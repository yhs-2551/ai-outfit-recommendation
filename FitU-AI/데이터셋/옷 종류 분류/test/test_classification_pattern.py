from PIL import Image
import torch
import torchvision.transforms as transforms
import timm

# 모델과 클래스 불러오기
checkpoint = torch.load('데이터셋\옷 패턴 분류\model/best_model_with_classes.pt', map_location='cpu')
class_names = checkpoint['class_names']
num_classes = len(class_names)

model = timm.create_model('efficientnetv2_rw_s', pretrained=False, num_classes=num_classes)
model.load_state_dict(checkpoint['model_state_dict'])
model.eval()

# 🔄 전처리 (학습과 동일해야 함)
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406],
                         std=[0.229, 0.224, 0.225])
])

# 테스트 이미지 로딩 및 전처리
img = Image.open("데이터셋\옷 패턴 분류/01.원천데이터_2000장\TS_상품_상의_dot/05_sou_2831_203777_160_model_05outer_06dot.jpg").convert("RGB")
input_tensor = transform(img).unsqueeze(0)  # [1, 3, 224, 224]

# 추론
with torch.no_grad():
    output = model(input_tensor)
    predicted = torch.argmax(output, dim=1)
    predicted_class = class_names[predicted.item()]

print(f"✅ 예측된 패턴 클래스: {predicted_class}")