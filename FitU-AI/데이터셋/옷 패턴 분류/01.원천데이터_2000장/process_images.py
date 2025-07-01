import os
import torch
import timm
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from ultralytics import YOLO
import cv2
from tqdm import tqdm

def load_classification_model():
    DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = timm.create_model('efficientnetv2_s', pretrained=False, num_classes=3)
    model.load_state_dict(torch.load("데이터셋/옷 종류 분류/model/classification_efficientnetv2_s.pt", map_location=DEVICE))
    model.to(DEVICE)
    model.eval()
    return model, DEVICE

def load_segmentation_model(model_path):
    return YOLO(model_path)

def process_image(image_path, classification_model, device, segmentation_model):
    # 이미지 전처리
    transform = transforms.Compose([
        transforms.Resize((640, 640)),
        transforms.ToTensor(),
    ])

    # 분류 수행
    image = Image.open(image_path).convert("RGB")
    input_tensor = transform(image).unsqueeze(0).to(device)

    with torch.no_grad():
        output = classification_model(input_tensor)
        probs = torch.sigmoid(output).cpu().numpy()[0]
        preds = (probs > 0.5).astype(int)

    # 라벨 매핑
    classes = ['top', 'bottom', 'onepiece']
    results = [(cls, int(p), round(prob, 3)) for cls, p, prob in zip(classes, preds, probs)]
    
    # 가장 높은 신뢰도를 가진 클래스 선택
    detected_class = None
    max_confidence = 0
    for label, is_present, confidence in results:
        if is_present and confidence > max_confidence:
            detected_class = label
            max_confidence = confidence

    if detected_class is None:
        return None

    # 세그멘테이션 수행
    results = segmentation_model(image_path)
    
    # 원본 이미지 읽기
    original_image = cv2.imread(image_path)
    original_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2RGB)

    # 결과 처리
    for result in results:
        if result.masks is not None:
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
                
                return final_image
    return None

def main():
    # 입력 및 출력 디렉토리 설정
    input_dir = r"D:\엔비디아 ai\Project\Clothing_Styling\데이터셋\옷 패턴 분류\01.원천데이터_2000장\TS_상품_상의_animal"
    output_dir = r"D:\엔비디아 ai\Project\Clothing_Styling\데이터셋\옷 패턴 분류\01.원천데이터_2000장\배경 제거\animal"
    
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 모델 로드
    classification_model, device = load_classification_model()
    segmentation_model = load_segmentation_model("데이터셋/옷 종류 분류/model/top_yolo11seg_m.pt")
    
    # 이미지 처리
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    
    for image_file in tqdm(image_files, desc="이미지 처리 중"):
        input_path = os.path.join(input_dir, image_file)
        output_path = os.path.join(output_dir, image_file)
        
        # 이미지 처리
        processed_image = process_image(input_path, classification_model, device, segmentation_model)
        
        if processed_image is not None:
            # BGR로 변환하여 저장
            processed_image_bgr = cv2.cvtColor(processed_image, cv2.COLOR_RGB2BGR)
            cv2.imwrite(output_path, processed_image_bgr)

if __name__ == "__main__":
    main() 