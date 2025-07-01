from ultralytics import YOLO
import streamlit as st
import cv2
import numpy as np
from PIL import Image


st.title("사람 탐지 시스템")

# Load a COCO-pretrained YOLO model
model = YOLO("데이터셋\옷 종류 분류\model\yolo12s.pt", task='detect')

# 파일 업로더
uploaded_file = st.file_uploader("이미지를 선택하세요", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # 이미지를 numpy 배열로 변환
    image = Image.open(uploaded_file)
    image_np = np.array(image)
    
    # 이미지 크기 가져오기
    image_height, image_width = image_np.shape[:2]
    
    # BGR로 변환 (OpenCV 형식)
    image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
    
    # 추론 실행
    results = model(image_np)
    
    # 결과 표시
    for result in results:
        # person 클래스만 필터링
        person_boxes = []
        for box in result.boxes:
            if result.names[int(box.cls)] == 'person':
                person_boxes.append(box)
        
        # 결과 이미지 생성 (person 클래스만 표시)
        annotated_frame = result.plot(boxes=person_boxes)
        
        # BGR에서 RGB로 변환
        annotated_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
        
        # 결과 이미지 표시
        st.image(annotated_frame, caption="탐지 결과", use_container_width=True)
        
        # 사람 탐지 결과 표시
        if len(person_boxes) > 0:
            st.success(f"사람이 {len(person_boxes)}명 탐지되었습니다! 👤")
            
            # 각 사람의 바운딩 박스 크기 확인
            for i, box in enumerate(person_boxes):
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                box_width = x2 - x1
                box_height = y2 - y1
                
                # 이미지 크기 대비 바운딩 박스 크기 비율 계산
                width_ratio = box_width / image_width
                height_ratio = box_height / image_height
                
                # 바운딩 박스가 너무 작은 경우 (이미지 크기의 50% 미만)
                if width_ratio < 0.5 or height_ratio < 0.5:
                    st.warning(f"사람 #{i+1}이(가) 너무 멀리 있습니다. 카메라에 더 가까이 와주세요! 📸")
        else:
            st.warning("사람이 탐지되지 않았습니다. ❌")