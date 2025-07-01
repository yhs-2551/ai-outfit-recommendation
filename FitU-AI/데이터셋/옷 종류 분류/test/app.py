import streamlit as st
import torch
import timm
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from ultralytics import YOLO
import cv2
import os
import tempfile
import requests
import base64
from datetime import datetime
import time
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (상위 디렉토리의 .env 파일 사용)
env_path = Path(__file__).parents[3] / '.env'
load_dotenv(dotenv_path=env_path)

# 캐시 설정
@st.cache_resource
def load_classification_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model('efficientnetv2_s', pretrained=False, num_classes=3)
    model.load_state_dict(torch.load("데이터셋/옷 종류 분류/model/classification_efficientnetv2_s.pt", map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model, DEVICE

@st.cache_resource
def load_pattern_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    checkpoint = torch.load('데이터셋\옷 종류 분류\model\clothes_pattern.pt', map_location=DEVICE)
    class_names = checkpoint['class_names']
    num_classes = len(class_names)
    
    model = timm.create_model('efficientnetv2_rw_s', pretrained=False, num_classes=num_classes)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.to(DEVICE)
    model.eval()
    return model, class_names, DEVICE

@st.cache_resource
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
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)  # BGR을 RGB로 변환
    
    # 결과 처리
    for result in results:
        if result.masks is not None:
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
            
            # 마스크를 원본 이미지 크기로 리사이즈
            original_height, original_width = original_image.shape[:2]
            resized_mask = cv2.resize(combined_mask.astype(np.uint8), 
                                    (original_width, original_height), 
                                    interpolation=cv2.INTER_NEAREST)
            
            # 마스크를 3채널로 확장
            mask_3channel = np.stack([resized_mask] * 3, axis=-1)
            
            # 마스크 적용 (옷 부분만 남기고 나머지는 흰색으로)
            segmented_image = np.where(mask_3channel, original_image, 255)
            
            # 색상 톤 분석 (세그멘테이션 직후, 이미지 변환 전에 수행)
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
                
                return final_image, detection_results, tone, value
    return None, [], "분석 불가", 0

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

# FASHN API 설정
API_KEY = os.getenv("FASHN_API_KEY")
if not API_KEY:
    st.error("FASHN API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    st.stop()
BASE_URL = "https://api.fashn.ai/v1"

def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

def process_virtual_tryon(model_image_path, garment_image_path, category):
    try:
        # 이미지를 Base64로 인코딩
        model_image_base64 = encode_image_to_base64(model_image_path)
        garment_image_base64 = encode_image_to_base64(garment_image_path)

        # API 요청 데이터 준비
        input_data = {
            "model_image": f"data:image/jpeg;base64,{model_image_base64}",
            "garment_image": f"data:image/jpeg;base64,{garment_image_base64}",
            "category": category
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        # 1. /run 엔드포인트로 요청
        run_response = requests.post(f"{BASE_URL}/run", json=input_data, headers=headers)
        run_data = run_response.json()
        
        if run_response.status_code != 200:
            return None, f"API 호출 실패: {run_data.get('error', '알 수 없는 에러')}"
            
        prediction_id = run_data.get("id")
        if not prediction_id:
            return None, "예측 ID를 받지 못했습니다"
            
        # 2. 상태 확인 및 결과 대기
        while True:
            status_response = requests.get(f"{BASE_URL}/status/{prediction_id}", headers=headers)
            if status_response.status_code != 200:
                return None, f"상태 확인 실패: {status_response.text}"
                
            status_data = status_response.json()

            if status_data["status"] == "completed":
                result_url = status_data["output"][0] if isinstance(status_data["output"], list) else status_data["output"]
                
                # 결과 이미지 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_dir = "데이터셋/옷 종류 분류/test/virtual_tryon_result"
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"result_{timestamp}.png")
                
                if download_image(result_url, output_path):
                    return output_path, None
                else:
                    return None, "이미지 다운로드 실패"

            elif status_data["status"] in ["starting", "in_queue", "processing"]:
                time.sleep(3)
            else:
                return None, f"예측 실패: {status_data.get('error')}"

    except Exception as e:
        return None, f"예상치 못한 에러가 발생했습니다: {e}"

def main():
    st.title("👔 의류 분류, 세그멘테이션 및 가상 피팅 시스템")
    
    # 모델 이미지 업로더
    st.subheader("👤 모델 이미지 업로드")
    model_image = st.file_uploader("모델 이미지를 업로드하세요", type=['jpg', 'jpeg', 'png'], key="model")
    
    # 의류 이미지 업로더
    st.subheader("👕 의류 이미지 업로드")
    garment_image = st.file_uploader("의류 이미지를 업로드하세요", type=['jpg', 'jpeg', 'png'], key="garment")
    
    if garment_image is not None:
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(garment_image.getvalue())
            tmp_path = tmp_file.name
        
        # 원본 이미지 표시
        st.subheader("📸 원본 이미지")
        st.image(garment_image, use_container_width=True)
        
        # 1. 패턴 분류 수행
        st.subheader("🎨 패턴 분류")
        pattern_model, class_names, pattern_device = load_pattern_model()
        image = Image.open(tmp_path).convert("RGB")
        pattern, confidence = predict_pattern(image, pattern_model, class_names, pattern_device)
        st.write(f"**예측된 패턴:** {pattern}")
        st.write(f"**신뢰도:** {confidence:.3f}")
        
        # 2. 분류 모델 로드 및 예측
        model, DEVICE = load_classification_model()

        # 이미지 전처리
        transform = transforms.Compose([
            transforms.Resize((640, 640)),
            transforms.ToTensor(),
        ])

        input_tensor = transform(image).unsqueeze(0).to(DEVICE)

        # 예측 수행
        with torch.no_grad():
            output = model(input_tensor)
            probs = torch.sigmoid(output).cpu().numpy()[0]
            preds = (probs > 0.5).astype(int)

        # 라벨 매핑
        classes = ['top', 'bottom', 'onepiece']
        results = [(cls, int(p), round(prob, 3)) for cls, p, prob in zip(classes, preds, probs)]

        # 결과 출력
        st.subheader("🔍 의류 유형 분류 결과")
        detected_classes = []
        for label, is_present, confidence in results:
            status = "✅ 있음" if is_present else "❌ 없음"
            st.write(f"{label:<10}: {status} (신뢰도: {confidence:.3f})")
            if is_present:
                detected_classes.append(label)

        # 3. 세그멘테이션 수행
        model_paths = {
            'top': "데이터셋/옷 종류 분류/model/top_yolo11seg_m.pt",
            'bottom': "데이터셋/옷 종류 분류/model/bottom_yolo11seg_m.pt",
            'onepiece': "데이터셋/옷 종류 분류/model/onepiece_yolo11seg_m.pt"
        }

        # 세그멘테이션 결과 표시
        if detected_classes:
            st.subheader("🎯 세그멘테이션 결과")
            cols = st.columns(len(detected_classes))
            
            segmented_images = []
            for idx, cls in enumerate(detected_classes):
                if cls in model_paths:
                    with cols[idx]:
                        st.write(f"**{cls}**")
                        segmented_image, detection_results, tone, value = process_segmentation(tmp_path, model_paths[cls])
                        if segmented_image is not None:
                            st.image(segmented_image, use_container_width=True)
                            segmented_images.append((cls, segmented_image))
                            
                            # 색상 톤 정보 표시
                            st.write(f"**색상 톤 분석:**")
                            st.write(f"- 톤: {tone}")
                            st.write(f"- 명도 값: {value:.1f}")
                            
                            if detection_results:
                                st.write("**YOLO 분류 결과:**")
                                for class_name, confidence in detection_results:
                                    st.write(f"- {class_name}: {confidence:.3f}")
            
            # 가상 피팅 섹션
            if model_image is not None and segmented_images:
                st.subheader("🎨 가상 피팅")
                
                # 모델 이미지 임시 저장
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as model_tmp:
                    model_tmp.write(model_image.getvalue())
                    model_tmp_path = model_tmp.name
                
                # 카테고리 매핑
                category_mapping = {
                    'top': 'tops',
                    'bottom': 'bottoms',
                    'onepiece': 'one-pieces'
                }
                
                # 각 세그멘테이션 결과에 대해 가상 피팅 수행
                for cls, seg_image in segmented_images:
                    st.write(f"**{cls} 가상 피팅 결과**")
                    
                    # 세그멘테이션 이미지 임시 저장
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as seg_tmp:
                        cv2.imwrite(seg_tmp.name, cv2.cvtColor(seg_image, cv2.COLOR_RGB2BGR))
                        seg_tmp_path = seg_tmp.name
                    
                    # 가상 피팅 수행 (카테고리 매핑 적용)
                    category = category_mapping.get(cls, 'auto')
                    result_path, error = process_virtual_tryon(model_tmp_path, seg_tmp_path, category)
                    
                    if result_path:
                        st.image(result_path, use_container_width=True)
                    else:
                        st.error(error)
                    
                    # 임시 파일 삭제
                    os.unlink(seg_tmp_path)
                
                # 모델 이미지 임시 파일 삭제
                os.unlink(model_tmp_path)
        
        # 임시 파일 삭제
        os.unlink(tmp_path)

if __name__ == "__main__":
    main() 