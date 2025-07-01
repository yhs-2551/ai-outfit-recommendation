import torch
import torch.nn as nn
import torchvision.models as models
from torchvision import transforms
from PIL import Image
import os

class PatternClassifier:
    def __init__(self, model_path):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.transform = transforms.Compose([
            transforms.ToTensor(),  # 학습 코드와 동일하게 ToTensor만 사용
        ])
        self.classes = ['animal', 'artifact', 'etcnature', 'dot', 'check', 'geometric', 'plants', 'stripe', 'symbol', 'etc', 'unknown']
        self.model = self.load_model(model_path)
        
    def load_model(self, model_path):
        model = models.efficientnet_v2_s(pretrained=False)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(self.classes))
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model.eval()  # 평가 모드로 설정
        return model.to(self.device)
    
    def predict(self, image_path, threshold=0.7):
        # 이미지 로드 및 전처리
        image = Image.open(image_path).convert('RGB')
        image = image.resize((224, 224))  # EfficientNetV2-s의 기본 입력 크기
        image_tensor = self.transform(image).unsqueeze(0).to(self.device)
        
        # 예측
        with torch.no_grad():
            outputs = self.model(image_tensor)
            probabilities = torch.softmax(outputs, dim=1)
            max_prob, predicted = torch.max(probabilities, 1)
            
            # 확률이 임계값보다 낮으면 etc로 분류
            if max_prob.item() < threshold:
                return 'etc', max_prob.item()
            return self.classes[predicted.item()], max_prob.item()

def main():
    # 모델 경로 설정
    model_path = '데이터셋/옷 패턴 분류/01.원천데이터_2000장/best_pattern_model.pth'
    
    # 분류기 초기화
    classifier = PatternClassifier(model_path)
    
    # 테스트할 이미지 경로 (경로 구분자를 슬래시로 통일)
    test_image_path = '데이터셋\옷 패턴 분류/01.원천데이터_2000장\배경 제거\dot\수정됨_05_sou_3528_253978_330_model_04-1onepiece(dress)_06dot.jpg'
    
    # 예측
    predicted_class, confidence = classifier.predict(test_image_path)
    
    print(f"\n테스트 결과:")
    print(f"이미지: {os.path.basename(test_image_path)}")
    print(f"예측 클래스: {predicted_class}")
    print(f"신뢰도: {confidence*100:.2f}%")

if __name__ == "__main__":
    main()