import os
from PIL import Image
import numpy as np

def delete_white_images(directory_path, threshold=0.95):
    deleted_count = 0
    
    # 디렉토리 내의 모든 이미지 파일 처리
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            image_path = os.path.join(directory_path, filename)
            
            try:
                # 이미지 열기
                with Image.open(image_path) as img:
                    # 이미지를 numpy 배열로 변환
                    img_array = np.array(img)
                    
                    # 흰색 픽셀의 비율 계산 (RGB 모두 240 이상인 경우를 흰색으로 간주)
                    white_pixels = np.sum(np.all(img_array > 240, axis=2))
                    total_pixels = img_array.shape[0] * img_array.shape[1]
                    white_ratio = white_pixels / total_pixels
                    
                    # 흰색 비율이 threshold 이상이면 삭제
                    if white_ratio > threshold:
                        os.remove(image_path)
                        print(f"삭제됨: {filename} (흰색 비율: {white_ratio:.2%})")
                        deleted_count += 1
                        
            except Exception as e:
                print(f"에러 발생 ({filename}): {e}")
                continue
    
    print(f"\n처리 완료!")
    print(f"총 {deleted_count}개의 이미지가 삭제되었습니다.")

if __name__ == "__main__":
    # 이미지가 있는 디렉토리 경로
    directory_path = "데이터셋/옷 패턴 분류/01.원천데이터_2000장/symbol"
    
    # 실행
    delete_white_images(directory_path) 