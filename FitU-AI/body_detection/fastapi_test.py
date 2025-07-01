from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from ultralytics import YOLO
import numpy as np
import cv2
from PIL import Image
import requests
import io

app = FastAPI()
model = YOLO("../models/yolo12s.pt", task="detect")

# 요청 바디 모델 정의
class ImageRequest(BaseModel):
    s3_url: str

@app.post("/user/profile/image-analysis")
async def analyze_profile_image(request: ImageRequest):
    try:
        response = requests.get(request.s3_url)
        response.raise_for_status()
    except Exception as e:
        return JSONResponse(status_code=400, content={"warnings": ["이미지를 불러올 수 없습니다."], "error": str(e)})

    image = Image.open(io.BytesIO(response.content)).convert("RGB")
    image_np = np.array(image)
    image_height, image_width = image_np.shape[:2]
    image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

    results = model(image_bgr)

    warnings = []

    for result in results:
        person_boxes = [
            box for box in result.boxes
            if result.names[int(box.cls)] == 'person'
        ]
        person_count = len(person_boxes)

        if person_count == 0:
            warnings.append("사람이 탐지되지 않았습니다.")
        elif person_count > 1:
            warnings.append(f"한 명만 나와야 합니다. 현재 인원: {person_count}")
        elif person_count == 1:
            box = person_boxes[0]
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            box_height = y2 - y1
            height_ratio = box_height / image_height

            if height_ratio < 0.5:
                warnings.append("인물이 너무 멀리 있습니다. 가까이 와주세요.")

    return JSONResponse(content={"warnings": warnings})