import torch
import torch.nn as nn
import torchvision.models as models
from torch.utils.data import Dataset, DataLoader, random_split
from torchvision import transforms
from PIL import Image
import os
from tqdm import tqdm

# 현재 스크립트의 절대 경로를 기준으로 데이터셋 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
dataset_dir = current_dir  # 현재 디렉토리가 데이터셋 디렉토리

# EfficientNetV2-S 모델 정의 (M 대신 S 사용)
def create_model(num_classes):
    model = models.efficientnet_v2_s(pretrained=True)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model

# 데이터셋 클래스
class PatternDataset(Dataset):
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.classes = sorted([d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))])
        # etc 클래스 추가
        if 'etc' not in self.classes:
            self.classes.append('etc')
        self.class_to_idx = {cls_name: i for i, cls_name in enumerate(self.classes)}
        
        self.images = []
        for class_name in self.classes:
            if class_name == 'etc':  # etc 클래스는 건너뛰기
                continue
            class_dir = os.path.join(root_dir, class_name)
            for img_name in os.listdir(class_dir):
                if img_name.endswith(('.jpg', '.jpeg', '.png')):
                    self.images.append((os.path.join(class_dir, img_name), self.class_to_idx[class_name]))

    def __len__(self):
        return len(self.images)

    def __getitem__(self, idx):
        img_path, label = self.images[idx]
        image = Image.open(img_path).convert('RGB')
        image = transforms.ToTensor()(image)
        return image, label

# 데이터셋 로드
dataset = PatternDataset(dataset_dir)

# 9:1 비율로 학습/검증 데이터 분할
train_size = int(0.9 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

# 데이터로더 생성 (배치 사이즈 감소)
train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=16, shuffle=False)

# 모델 생성
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"\n사용 중인 장치: {device}")
if torch.cuda.is_available():
    print(f"GPU 모델: {torch.cuda.get_device_name(0)}")
    print(f"GPU 메모리: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
else:
    print("GPU를 사용할 수 없어 CPU로 실행됩니다.")

model = create_model(num_classes=len(dataset.classes)).to(device)

# 학습 설정
criterion = nn.CrossEntropyLoss()
optimizer = torch.optim.AdamW(model.parameters(), lr=0.001)
scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=10)

# GPU 메모리 관리를 위한 설정
torch.cuda.empty_cache()

# Early Stopping 클래스 추가
class EarlyStopping:
    def __init__(self, patience=10, min_delta=0):
        self.patience = patience
        self.min_delta = min_delta
        self.counter = 0
        self.best_loss = None
        self.early_stop = False
        
    def __call__(self, val_loss):
        if self.best_loss is None:
            self.best_loss = val_loss
        elif val_loss > self.best_loss - self.min_delta:
            self.counter += 1
            if self.counter >= self.patience:
                self.early_stop = True
        else:
            self.best_loss = val_loss
            self.counter = 0

# 예측 함수 추가
def predict_with_threshold(model, image, threshold=0.7):
    model.eval()
    with torch.no_grad():
        outputs = model(image.unsqueeze(0))
        probabilities = torch.softmax(outputs, dim=1)
        max_prob, predicted = torch.max(probabilities, 1)
        
        # 확률이 임계값보다 낮으면 etc 클래스로 분류
        if max_prob.item() < threshold:
            return len(dataset.classes) - 1  # etc 클래스 인덱스
        return predicted.item()

# 학습 함수 수정
def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    correct = 0
    total = 0
    
    pbar = tqdm(loader, desc='Training')
    for images, labels in pbar:
        images, labels = images.to(device), labels.to(device)
        
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        
        total_loss += loss.item()
        probabilities = torch.softmax(outputs, dim=1)
        max_probs, predicted = torch.max(probabilities, 1)
        
        # 확률이 임계값보다 낮은 경우 etc로 분류
        predicted[max_probs < 0.7] = len(dataset.classes) - 1
        
        total += labels.size(0)
        correct += predicted.eq(labels).sum().item()
        
        pbar.set_postfix({'loss': total_loss/total, 'acc': 100.*correct/total})
    
    return total_loss/len(loader), 100.*correct/total

# 검증 함수 수정
def validate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    correct = 0
    total = 0
    
    with torch.no_grad():
        for images, labels in tqdm(loader, desc='Validation'):
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            
            total_loss += loss.item()
            probabilities = torch.softmax(outputs, dim=1)
            max_probs, predicted = torch.max(probabilities, 1)
            
            # 확률이 임계값보다 낮은 경우 etc로 분류
            predicted[max_probs < 0.7] = len(dataset.classes) - 1
            
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
    
    return total_loss/len(loader), 100.*correct/total

# 학습 루프
num_epochs = 50
best_val_acc = 0
early_stopping = EarlyStopping(patience=10)

for epoch in range(num_epochs):
    print(f'\nEpoch {epoch+1}/{num_epochs}')
    
    # 학습
    train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
    print(f'Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}%')
    
    # 검증
    val_loss, val_acc = validate(model, val_loader, criterion, device)
    print(f'Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')
    
    # 학습률 조정
    scheduler.step()
    
    # 최고 성능 모델 저장
    if val_acc > best_val_acc:
        best_val_acc = val_acc
        torch.save(model.state_dict(), 'best_pattern_model.pth')
        print(f'New best model saved! (Val Acc: {val_acc:.2f}%)')
    
    # Early Stopping 체크
    early_stopping(val_loss)
    if early_stopping.early_stop:
        print(f'Early stopping triggered after {epoch+1} epochs')
        break

# ONNX 변환
def export_to_onnx(model, save_path):
    model.eval()
    dummy_input = torch.randn(1, 3, 224, 224).to(device)
    torch.onnx.export(
        model,
        dummy_input,
        save_path,
        export_params=True,
        opset_version=11,
        do_constant_folding=True,
        input_names=['input'],
        output_names=['output'],
        dynamic_axes={'input': {0: 'batch_size'},
                     'output': {0: 'batch_size'}}
    )

# 최종 모델을 ONNX로 변환
export_to_onnx(model, '데이터셋/옷 패턴 분류/01.원천데이터_2000장/배경 제거/pattern_classification_model.onnx')
print("모델이 ONNX 형식으로 저장되었습니다.")