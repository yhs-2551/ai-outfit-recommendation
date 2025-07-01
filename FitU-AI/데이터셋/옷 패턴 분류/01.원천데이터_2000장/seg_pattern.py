import cv2
import numpy as np
from ultralytics import YOLO
import torch
import os
from pathlib import Path

# GPU 사용 가능 여부 확인 및 강제 설정
if torch.cuda.is_available():
    device = '0'  # CUDA 장치 인덱스 (0은 첫 번째 GPU)
    print(f"CUDA 사용 가능: {torch.cuda.get_device_name(0)}")
else:
    device = 'cpu'
    print("CUDA 사용 불가능, CPU 사용")

print(f"사용 중인 장치: {device}")

# 1. 모델 로드 (onnx 경로와 task="segment" 지정)
model = YOLO("데이터셋\옷 종류 분류\clothes_type_large.onnx", task="segment")

# 2. 클래스 이름 (data.yaml의 names와 동일하게)
class_names = [
    'blouse', 'bottom', 'cardigan', 'coat', 'jacket', 'jumper',
    'onepiece-dress', 'onepiece-jumpsuite', 'shirt', 'sweater', 't-shirt', 'vest'
]

# 3. 랜덤 컬러 팔레트 생성
np.random.seed(42)
colors = {i: tuple(np.random.randint(0, 255, 3).tolist()) for i in range(len(class_names))}

def segment_clothes(image):
    # device 매개변수 추가하여 GPU 사용
    results = model.predict(image, imgsz=640, device=device)[0]
    seg_map = np.zeros(image.shape[:2], dtype=np.uint8)

    if results.masks is not None and results.boxes.cls is not None:
        masks = results.masks.data.cpu().numpy()  # (N, H_mask, W_mask)
        class_ids = results.boxes.cls.cpu().numpy().astype(int)  # (N,)

        for i, mask in enumerate(masks):
            class_id = class_ids[i]
            # 남녀 구분 없이 통합된 클래스 ID로 변환
            unified_class_id = class_id // 2
            # mask를 원본 이미지 크기로 리사이즈
            mask_resized = cv2.resize(mask, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_NEAREST)
            seg_map[mask_resized > 0.5] = unified_class_id

    return seg_map

def overlay_segmentation(seg_map, original_img, alpha=0.5):
    h, w = seg_map.shape
    # 배경만 흰색, 나머지는 원본 이미지 그대로
    overlay = original_img.copy()
    background_mask = (seg_map == 0)
    overlay[background_mask] = (255, 255, 255)
    
    # 세그멘테이션된 옷의 바운딩 박스 찾기
    non_bg_mask = (seg_map > 0).astype(np.uint8) * 255
    contours, _ = cv2.findContours(non_bg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # 모든 컨투어를 포함하는 바운딩 박스 찾기
        x_min, y_min, x_max, y_max = float('inf'), float('inf'), 0, 0
        for cnt in contours:
            x, y, w_box, h_box = cv2.boundingRect(cnt)
            x_min = min(x_min, x)
            y_min = min(y_min, y)
            x_max = max(x_max, x + w_box)
            y_max = max(y_max, y + h_box)
        
        # 옷 영역 추출
        clothes_region = overlay[y_min:y_max, x_min:x_max]
        
        # 640x640 흰색 배경 이미지 생성
        result_img = np.ones((640, 640, 3), dtype=np.uint8) * 255
        
        # 옷 영역의 크기 계산
        clothes_h, clothes_w = clothes_region.shape[:2]
        
        # 옷 영역의 크기에 따라 적절한 스케일 결정
        target_area_ratio = clothes_w * clothes_h / (640 * 640)
        
        if target_area_ratio < 0.3:  # 옷이 작은 경우 확대
            target_size = 0.7  # 전체 이미지의 70%를 차지하도록
        elif target_area_ratio > 0.8:  # 옷이 큰 경우
            target_size = 0.9  # 전체 이미지의 90%를 차지하도록
        else:  # 적당한 크기
            target_size = 0.8  # 전체 이미지의 80%를 차지하도록
        
        # 목표 크기를 기준으로 스케일 계산
        scale_w = (640 * target_size) / clothes_w
        scale_h = (640 * target_size) / clothes_h
        scale = min(scale_w, scale_h)  # 비율 유지를 위해 작은 값 선택
        
        new_w, new_h = int(clothes_w * scale), int(clothes_h * scale)
        
        if new_w > 0 and new_h > 0:  # 크기가 유효한 경우에만 리사이즈
            resized_clothes = cv2.resize(clothes_region, (new_w, new_h))
            
            # 중앙에 배치
            x_offset = (640 - new_w) // 2
            y_offset = (640 - new_h) // 2
            
            result_img[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized_clothes
        
        return result_img
    
    # 컨투어가 없는 경우 원본 이미지를 640x640으로 리사이즈하여 반환
    return cv2.resize(overlay, (640, 640))

def process_directory(input_dir, output_dir):
    # 출력 디렉토리가 없으면 생성
    os.makedirs(output_dir, exist_ok=True)
    
    # 입력 디렉토리에서 모든 이미지 파일 찾기
    image_extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(Path(input_dir).glob(f'*{ext}')))
    
    # 중복 제거
    image_files = list(set(str(p) for p in image_files))
    image_files = [Path(p) for p in image_files]
    
    total_files = len(image_files)
    print(f"총 {total_files}개의 이미지 파일을 처리합니다.")
    
    for idx, img_path in enumerate(image_files, 1):
        try:
            # 이미지 읽기
            img = cv2.imread(str(img_path))
            if img is None:
                print(f"이미지를 읽을 수 없습니다: {img_path}")
                continue
                
            # 세그멘테이션 실행
            seg_map = segment_clothes(img)
            result = overlay_segmentation(seg_map, img)
            
            # 결과 저장
            output_path = os.path.join(output_dir, img_path.name)
            cv2.imwrite(output_path, result)
            
            print(f"처리 완료 ({idx}/{total_files}): {img_path.name}")
            
        except Exception as e:
            print(f"이미지 처리 중 오류 발생 ({img_path}): {str(e)}")
    
    print("모든 이미지 처리가 완료되었습니다!")

# 메인 실행 코드
if __name__ == "__main__":
    input_directory = r"데이터셋\옷 패턴 분류\01.원천데이터_2000장\TS_상품_상의_symbol"
    output_directory = r"데이터셋\옷 패턴 분류\01.원천데이터_2000장\symbol"
    process_directory(input_directory, output_directory) 