from PIL import Image
import torchvision.transforms as transforms
import torch
import timm
import numpy as np

# ⬇️ 이미지 경로 입력 (예: /content/datasets/top/your_image.jpg)
test_image_path = "데이터셋\옷 종류 분류/01.원천데이터\VS_상품_하의_onepiece(dress)_3000/01_sou_000956_004778_wear_03-1onepiece(dress)_woman.jpg"

# 🔺 1. 모델 로드
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = timm.create_model('efficientnetv2_s', pretrained=False, num_classes=3)
model.load_state_dict(torch.load("데이터셋\옷 종류 분류\model\classification_efficientnetv2_s.pt", map_location=DEVICE))
model.to(DEVICE)
model.eval()

# 🔺 2. 이미지 전처리
transform = transforms.Compose([
    transforms.Resize((640, 640)),
    transforms.ToTensor(),
])

image = Image.open(test_image_path).convert("RGB")
input_tensor = transform(image).unsqueeze(0).to(DEVICE)  # (1, 3, 640, 640)

# 🔺 3. 예측 수행
with torch.no_grad():
    output = model(input_tensor)
    probs = torch.sigmoid(output).cpu().numpy()[0]
    preds = (probs > 0.5).astype(int)

# 🔺 4. 라벨 매핑
classes = ['top', 'bottom', 'onepiece']
results = [(cls, int(p), round(prob, 3)) for cls, p, prob in zip(classes, preds, probs)]

# 🔺 5. 출력
print("🔍 예측 결과:")
for label, is_present, confidence in results:
    status = "✅ 있음" if is_present else "❌ 없음"
    print(f"{label:<10}: {status} (score: {confidence})")
