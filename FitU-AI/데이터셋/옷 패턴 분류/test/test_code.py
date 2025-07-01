import onnxruntime as ort
import numpy as np
import cv2
import matplotlib.pyplot as plt

# 이미지 불러오기
img_path = "데이터셋/옷 패턴 분류/01.원천데이터_2000장/TS_상품_상의_etcnature/05_sou_4409_317444_310_clothes_02top(others)_04etc nature.jpg"
with open(img_path, 'rb') as f:
    img_array = np.asarray(bytearray(f.read()), dtype=np.uint8)
original_img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
image = cv2.cvtColor(original_img, cv2.COLOR_BGR2RGB)
input_size = 640

# 이미지 리사이즈 + 패딩
def letterbox(im, new_shape=640, color=(114, 114, 114)):
    shape = im.shape[:2]  # current shape [height, width]
    r = min(new_shape / shape[0], new_shape / shape[1])
    new_unpad = (int(round(shape[1] * r)), int(round(shape[0] * r)))
    dw, dh = new_shape - new_unpad[0], new_shape - new_unpad[1]
    dw /= 2
    dh /= 2
    im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)
    top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
    left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
    im = cv2.copyMakeBorder(im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
    return im, r, (dw, dh)

resized_img, ratio, dwdh = letterbox(image, new_shape=input_size)
input_tensor = resized_img.transpose(2, 0, 1)[np.newaxis, :, :, :].astype(np.float32) / 255.0

# ONNX 세션 생성
session = ort.InferenceSession("데이터셋/옷 패턴 분류/clothes_pattern.onnx", providers=["CUDAExecutionProvider", "CPUExecutionProvider"])
input_name = session.get_inputs()[0].name

# 추론
outputs = session.run(None, {input_name: input_tensor})

# outputs: [detection, mask]
dets, mask = outputs[0], outputs[1]  # dets: [1, N, 116], mask: [1, 32, 160, 160]

# 클래스명 리스트 (폴더명 기반)
class_names = [
    'symbol', 'stripe', 'plants', 'geometric', 'etcnature', 'etc',
    'dot', 'check', 'artifact', 'animal'
]

def process_segmentation(dets, mask, image, class_names):
    boxes = dets[0][:, :4]
    scores = dets[0][:, 4]
    classes = dets[0][:, 5].astype(int)
    
    # 세그멘테이션 맵 생성 (배경: 0, 객체: 클래스 ID)
    seg_map = np.zeros(image.shape[:2], dtype=np.uint8)
    
    for i, (box, score, cls) in enumerate(zip(boxes, scores, classes)):
        if score < 0.4:
            continue
            
        # 마스크 추출 및 후처리
        if i >= mask[0].shape[0]:
            continue
            
        mask_pred = mask[0][i]  # 해당 객체의 마스크
        mask_pred = cv2.resize(mask_pred, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_LINEAR)
        mask_pred = (mask_pred > 0.5).astype(np.uint8)
        
        # 마스크 영역에 클래스 ID 할당
        seg_map[mask_pred == 1] = cls + 1  # 배경은 0, 클래스는 1부터 시작
    
    return seg_map

def overlay_segmentation(seg_map, original_img):
    # 배경만 흰색, 나머지는 원본 이미지 그대로
    overlay = original_img.copy()
    background_mask = (seg_map == 0)
    overlay[background_mask] = (255, 255, 255)
    
    # 클래스명 표시 (배경 제외)
    for class_id in np.unique(seg_map):
        if class_id == 0:
            continue  # 배경은 라벨 표시하지 않음
        
        if class_id - 1 < len(class_names):  # 클래스 ID는 1부터 시작하므로 -1
            mask = (seg_map == class_id).astype(np.uint8)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for cnt in contours:
                if cv2.contourArea(cnt) > 500:  # 작은 영역 무시
                    x, y, w_box, h_box = cv2.boundingRect(cnt)
                    label = class_names[class_id - 1]
                    cv2.putText(overlay, f'{label}', (x, y - 5), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2, cv2.LINE_AA)
    
    return overlay

# 세그멘테이션 처리 및 결과 저장
seg_map = process_segmentation(dets, mask, original_img, class_names)
result = overlay_segmentation(seg_map, original_img)

# 결과 이미지 저장
cv2.imwrite('데이터셋/옷 패턴 분류/test/result.png', result)
print('결과 이미지가 result.png로 저장되었습니다.')
