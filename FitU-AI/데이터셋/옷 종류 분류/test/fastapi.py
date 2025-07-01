import torch
import timm
import numpy as np
from PIL import Image, UnidentifiedImageError
import torchvision.transforms as transforms
from ultralytics import YOLO
import cv2
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List
import io
import tempfile
import requests
from enum import Enum
import boto3
from pydantic import BaseModel
import uuid

# 기본 경로 설정
BASE_DIR = Path.home() / "AI"
MODELS_DIR = BASE_DIR / "models"
API_DIR = BASE_DIR / "clothes_classification"

# .env 파일 로드
env_path = BASE_DIR / '.env'
load_dotenv(dotenv_path=env_path)

app = FastAPI()

class DetectionStatus(str, Enum):
    NO_CLOTHES = "no_clothes"  # 옷이 탐지되지 않음
    SINGLE_CLOTH = "single_cloth"  # 1개의 옷이 탐지됨
    MULTIPLE_CLOTHES = "multiple_clothes"  # 2개 이상의 옷이 탐지됨

class ClothesAnalysis(BaseModel):
    category: str  # top, bottom, onepiece
    subcategory: str  # 티셔츠, 셔츠, 청바지 등
    pattern: str  # 패턴 분석 결과
    tone: str  # 밝은 톤, 어두운 톤
    segmented_image_path: str  # 세그멘테이션된 이미지 경로

class ImageAnalysisResponse(BaseModel):
    status: DetectionStatus  # 옷 탐지 상태
    analyses: List[ClothesAnalysis]  # 분석 결과 목록

class ImageAnalysisRequest(BaseModel):
    s3_url: str

# 모델 로드 함수들
def load_classification_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model('efficientnetv2_s', pretrained=False, num_classes=3)
    model.load_state_dict(torch.load(MODELS_DIR / "classification_efficientnetv2_s.pt", map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model, DEVICE

def load_pattern_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load(MODELS_DIR / "clothes_pattern.pt", map_location=DEVICE)
    class_names = checkpoint['class_names']
    num_classes = len(class_names)
    
    model = timm.create_model('efficientnetv2_rw_s', pretrained=False, num_classes=num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(DEVICE)
    model.eval()
    return model, class_names, DEVICE

def load_segmentation_model(model_path):
    return YOLO(model_path)

def analyze_color_tone(image):
    """이미지의 색상 톤을 분석하는 함수"""
    # 흰색 배경(255, 255, 255)을 제외한 픽셀만 추출
    mask = ~np.all(image == 255, axis=2)
    clothing_pixels = image[mask]
    
    if len(clothing_pixels) == 0:
        return "분석 불가", 0
    
    # RGB 평균값 계산
    avg_rgb = np.mean(clothing_pixels, axis=0)
    
    # RGB를 HSV로 변환
    avg_rgb_normalized = avg_rgb / 255.0
    avg_rgb_normalized = avg_rgb_normalized.reshape(1, 1, 3)
    avg_hsv = cv2.cvtColor(avg_rgb_normalized.astype(np.float32), cv2.COLOR_RGB2HSV)
    value = avg_hsv[0, 0, 2] * 255  # 명도 값 (0-255)
    
    # 톤 분류
    if value > 128:
        tone = "밝은 톤"
    else:
        tone = "어두운 톤"
    
    return tone, value

def process_segmentation(image_path, model_path):
    # YOLO 모델 로드
    model = load_segmentation_model(model_path)
    
    # 예측 수행
    results = model(image_path)
    
    # 원본 이미지 읽기
    original_image = cv2.imread(image_path)
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)
    
    # 결과 처리
    for result in results:
        if result.masks is not None and len(result.masks) > 0:
            # 분류 결과 가져오기
            class_names = result.names
            boxes = result.boxes
            class_ids = boxes.cls.cpu().numpy()
            confidences = boxes.conf.cpu().numpy()
            
            # 마스크 데이터 가져오기
            masks = result.masks.data.cpu().numpy()
            
            # 모든 마스크를 하나로 합치기
            combined_mask = np.zeros_like(masks[0], dtype=np.uint8)
            for mask in masks:
                combined_mask = np.logical_or(combined_mask, mask)
            
            # 마스크의 픽셀 수 계산
            mask_pixel_count = np.sum(combined_mask)
            total_pixels = combined_mask.size
            mask_ratio = mask_pixel_count / total_pixels
            
            # 마스크가 전체 이미지의 1% 이상을 차지하는 경우에만 처리
            if mask_ratio > 0.10:
                # 마스크를 원본 이미지 크기로 리사이즈
                original_height, original_width = original_image.shape[:2]
                resized_mask = cv2.resize(combined_mask.astype(np.uint8), 
                                        (original_width, original_height), 
                                        interpolation=cv2.INTER_NEAREST)
                
                # 마스크를 3채널로 확장
                mask_3channel = np.stack([resized_mask] * 3, axis=-1)
                
                # 마스크 적용 (옷 부분만 남기고 나머지는 흰색으로)
                segmented_image = np.where(mask_3channel, original_image, 255)
                
                # 색상 톤 분석
                tone, value = analyze_color_tone(segmented_image)
                
                # 마스크의 경계 상자 찾기
                y_indices, x_indices = np.where(resized_mask)
                if len(y_indices) > 0 and len(x_indices) > 0:
                    y_min, y_max = y_indices.min(), y_indices.max()
                    x_min, x_max = x_indices.min(), x_indices.max()
                    
                    # 패딩 추가 (이미지 크기의 10%)
                    padding_y = int((y_max - y_min) * 0.1)
                    padding_x = int((x_max - x_min) * 0.1)
                    
                    # 패딩을 적용한 새로운 경계 상자 계산
                    y_min = max(0, y_min - padding_y)
                    y_max = min(original_height - 1, y_max + padding_y)
                    x_min = max(0, x_min - padding_x)
                    x_max = min(original_width - 1, x_max + padding_x)
                    
                    # 옷 부분만 크롭
                    cropped_image = segmented_image[y_min:y_max+1, x_min:x_max+1]
                    
                    # 640x640 흰색 배경 생성
                    final_image = np.ones((640, 640, 3), dtype=np.uint8) * 255
                    
                    # 크롭된 이미지의 크기 계산
                    h, w = cropped_image.shape[:2]
                    
                    # 이미지 비율 유지하면서 640x640에 맞게 리사이즈
                    scale = min(640/w, 640/h)
                    new_w, new_h = int(w * scale), int(h * scale)
                    resized_crop = cv2.resize(cropped_image, (new_w, new_h), interpolation=cv2.INTER_AREA)
                    
                    # 중앙에 배치
                    y_offset = (640 - new_h) // 2
                    x_offset = (640 - new_w) // 2
                    final_image[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_crop
                    
                    # 분류 결과 반환
                    detection_results = []
                    for class_id, confidence in zip(class_ids, confidences):
                        class_name = class_names[int(class_id)]
                        detection_results.append((class_name, float(confidence)))
                    
                    return final_image, detection_results, tone, value, True  # 마스크 비율이 1% 이상이면 True 반환
    return None, [], "분석 불가", 0, False  # 마스크가 없거나 비율이 1% 미만이면 False 반환

def predict_pattern(image, model, class_names, device):
    # 이미지 전처리
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                           std=[0.229, 0.224, 0.225])
    ])
    
    # 이미지 변환
    input_tensor = transform(image).unsqueeze(0).to(device)
    
    # 예측
    with torch.no_grad():
        output = model(input_tensor)
        probs = torch.softmax(output, dim=1)
        predicted = torch.argmax(output, dim=1)
        confidence = probs[0][predicted].item()
        predicted_class = class_names[predicted.item()]
    
    return predicted_class, confidence

def save_segmented_image(image: np.ndarray, category: str) -> str:
    """세그멘테이션된 이미지를 저장하고 경로를 반환"""
    filename = f"{category}.jpg"  # 카테고리별로 고정된 파일명 사용
    filepath = SEGMENTED_IMAGES_DIR / filename
    
    # 이미지 저장 (덮어쓰기)
    cv2.imwrite(str(filepath), cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
    return str(filepath.absolute())

def save_segmented_image_to_s3(image: np.ndarray, category: str) -> str:
    """세그멘테이션 이미지를 S3에 저장하고 퍼블릭 URL을 반환"""
    bucket_name = os.getenv("AWS_S3_BUCKET_NAME")
    region = os.getenv("AWS_S3_REGION", "ap-northeast-2")

    # 고유한 파일명 생성
    unique_id = str(uuid.uuid4())[:8]  # 예: 'a3f9d012'
    filename = f"{category}_{unique_id}.jpg"
    s3_key = f"clothes_results/{filename}"

    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        temp_path = tmp_file.name
        cv2.imwrite(temp_path, cv2.cvtColor(image, cv2.COLOR_RGB2BGR))

    s3 = boto3.client(
        's3',
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        region_name=region
    )

    try:
        s3.upload_file(
            temp_path,
            bucket_name,
            s3_key,
            ExtraArgs={'ContentType': 'image/jpeg'}
        )
    except Exception as e:
        raise RuntimeError(f"S3 업로드 실패: {str(e)}")
    finally:
        os.unlink(temp_path)

    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{s3_key}"

def download_image_from_url(url: str) -> Image.Image:
    """URL에서 이미지를 다운로드하여 PIL Image로 반환"""
    try:
        response = requests.get(url)
        response.raise_for_status()
        image = Image.open(io.BytesIO(response.content)).convert("RGB")
        return image
    except requests.RequestException as e:
        raise HTTPException(
            status_code=400,
            detail=f"이미지 다운로드 실패: {str(e)}"
        )
    except UnidentifiedImageError:
        raise HTTPException(
            status_code=400,
            detail="지원하지 않는 이미지 형식입니다."
        )

@app.post("/clothes/image-analysis")
async def analyze_clothes_image_from_s3(payload: ImageAnalysisRequest):
    s3_url = payload.s3_url
    """S3 URL을 통해 이미지를 분석하는 엔드포인트"""
    try:
        # URL에서 이미지 다운로드
        image = download_image_from_url(s3_url)
        
        # 이미지를 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            image.save(tmp_file.name)
            tmp_path = tmp_file.name
        
        try:
            # 1. 패턴 분류 수행
            pattern_model, class_names, pattern_device = load_pattern_model()
            pattern, pattern_confidence = predict_pattern(image, pattern_model, class_names, pattern_device)
            
            # 2. 분류 모델 로드 및 예측
            model, DEVICE = load_classification_model()
            transform = transforms.Compose([
                transforms.Resize((640, 640)),
                transforms.ToTensor(),
            ])
            
            input_tensor = transform(image).unsqueeze(0).to(DEVICE)
            
            with torch.no_grad():
                output = model(input_tensor)
                probs = torch.sigmoid(output).cpu().numpy()[0]
                preds = (probs > 0.5).astype(int)
            
            classes = ['top', 'bottom', 'onepiece']
            analyses = []
            valid_detections = 0  # 유효한 세그멘테이션 결과 개수
            
            # 3. 세그멘테이션 수행
            model_paths = {
                'top': str(MODELS_DIR / "top_yolo11seg_m.pt"),
                'bottom': str(MODELS_DIR / "bottom_yolo11seg_m.pt"),
                'onepiece': str(MODELS_DIR / "onepiece_yolo11seg_m.pt")
            }
            
            for cls, is_present, prob in zip(classes, preds, probs):
                if is_present and cls in model_paths:
                    try:
                        segmented_image, detection_results, tone, value, is_valid = process_segmentation(tmp_path, model_paths[cls])
                        
                        if segmented_image is None or not detection_results or not is_valid:
                            continue
                        
                        # 가장 높은 신뢰도를 가진 서브카테고리 선택
                        best_detection = max(detection_results, key=lambda x: x[1])
                        subcategory, _ = best_detection
                        
                        # 세그멘테이션 이미지 저장
                        segmented_image_path = save_segmented_image_to_s3(segmented_image, cls)
                        
                        # 분석 결과 추가
                        analyses.append(ClothesAnalysis(
                            category=cls,
                            subcategory=subcategory,
                            pattern=pattern,
                            tone=tone,
                            segmented_image_path=segmented_image_path
                        ))
                        valid_detections += 1
                            
                    except Exception as e:
                        print(f"{cls} 처리 중 오류 발생: {str(e)}")
                        continue
            
            # 상태 결정
            if valid_detections == 0:
                status = DetectionStatus.NO_CLOTHES
            elif valid_detections == 1:
                status = DetectionStatus.SINGLE_CLOTH
            else:
                status = DetectionStatus.MULTIPLE_CLOTHES
            
            return ImageAnalysisResponse(
                status=status,
                analyses=analyses
            )
            
        finally:
            # 임시 파일 삭제
            try:
                os.unlink(tmp_path)
            except Exception as e:
                print(f"임시 파일 삭제 실패: {str(e)}")
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"처리 중 예상치 못한 오류 발생: {str(e)}"
        ) 