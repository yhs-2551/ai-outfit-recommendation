from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import re
import base64
import requests
import tempfile
import time
import boto3
import uuid
import asyncio
import aiohttp
from typing import List, Dict, Any

# .env 로드
env_path = Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

# GPT 초기화
llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5, api_key=api_key)

# FastAPI 앱 초기화
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# DB 접속 정보
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# 옷 종류 및 카테고리 정의
CLOTHING_TYPES = {
    'TOP': [
        'BLOUSE',    # 블라우스
        'CARDIGAN',  # 가디건
        'COAT',      # 코트
        'JACKET',    # 자켓
        'JUMPER',    # 점퍼
        'SHIRT',     # 셔츠
        'SWEATER',   # 스웨터
        'TSHIRT',    # 티셔츠
        'VEST'       # 베스트
    ],
    'BOTTOM': [
        'ACTIVEWEAR',  # 편한 활동복
        'JEANS',       # 청바지
        'PANTS',       # 일반 바지
        'SHORTS',      # 반바지
        'SKIRT',       # 치마
        'SLACKS'       # 슬랙스
    ],
    'ONEPIECE': [
        'DRESS',     # 드레스
        'JUMPSUIT'   # 점프수트
    ]
}

# 카테고리 매핑 (옷장 DB 구조에 맞춤)
CATEGORY_MAP = {
    'TOP': ['BLOUSE', 'CARDIGAN', 'COAT', 'JACKET', 'JUMPER', 'SHIRT', 'SWEATER', 'TSHIRT', 'VEST'],
    'BOTTOM': ['ACTIVEWEAR', 'JEANS', 'PANTS', 'SHORTS', 'SKIRT', 'SLACKS'],
    'ONEPIECE': ['DRESS', 'JUMPSUIT']
}

# 패턴 매핑
PATTERN_MAP = {
    'ANIMAL': '동물',
    'ARTIFACT': '아티팩트',
    'CHECK': '체크',
    'DOT': '도트',
    'ETC': '기타',
    'NATURE': '자연',
    'GEOMETRIC': '기하학',
    'PLANT': '식물',
    'STRIPE': '줄무늬',
    'SYMBOL': '심볼'
}

# 톤 매핑
TONE_MAP = {
    "LIGHT": "밝은 계열",
    "DARK": "어두운 계열",
    "NOT_CONSIDERED": "고려하지 않음"
}

# 요청 바디 스키마
class RecommendationRequest(BaseModel):
    user_id: str
    situation: str
    targetTime: str
    targetPlace: str
    highTemperature: int
    lowTemperature: int
    rainPercent: int
    status: str
    showClosetOnly: bool

# 옷장의 옷 종류만 가져오는 함수 (첫 번째 프롬프트용)
def load_clothing_types_from_db(user_id: str):
    try:
        session = SessionLocal()
        query = text("""
            SELECT DISTINCT
                type,
                category
            FROM clothes
            WHERE user_id = :user_id
        """)
        
        print(f"SQL 쿼리 실행: user_id = {user_id}")  # 디버깅용 로그
        result = session.execute(query, {"user_id": user_id}).fetchall()
        print(f"SQL 쿼리 결과: {result}")  # 디버깅용 로그
        
        items = []
        for row in result:
            type_name = row[0].strip().upper()  # 일반 카테고리 (TOP, BOTTOM, ONEPIECE)
            category = row[1].strip().upper()   # 상세 카테고리 (BLOUSE, JEANS 등)
            
            # type이 일반 카테고리이고 category가 해당 type의 상세 카테고리인 경우
            if type_name in CATEGORY_MAP and category in CATEGORY_MAP[type_name]:
                items.append({
                    "type": type_name,
                    "category": category
                })
        
        print(f"처리된 옷장 데이터: {items}")  # 디버깅용 로그
        return items
    except Exception as e:
        print(f"데이터베이스 조회 중 오류 발생: {e}")
        return []
    finally:
        session.close()

# 옷의 상세 정보를 가져오는 함수 (두 번째 프롬프트용)
def load_clothing_details_from_db(user_id: str):
    try:
        session = SessionLocal()
        query = text("""
            SELECT 
                id,
                type,
                category,
                pattern,
                color,
                image_url
            FROM clothes
            WHERE user_id = :user_id
        """)
        
        result = session.execute(query, {"user_id": user_id}).fetchall()
        
        items = []
        for row in result:
            clothing_id = str(row[0])  # 데이터베이스 ID를 그대로 사용
            type_name = row[1].strip().upper()  # 일반 카테고리 (TOP, BOTTOM, ONEPIECE)
            category = row[2].strip().upper()   # 상세 카테고리 (BLOUSE, JEANS 등)
            pattern = row[3].strip().upper()
            tone = TONE_MAP.get(row[4].strip().upper(), "고려하지 않음")
            image_url = row[5].strip()

            if not image_url or not image_url.startswith('http'):
                continue

            items.append({
                "clothing_id": clothing_id,
                "attributes": {
                    "type": type_name,
                    "category": category,
                    "pattern": pattern,
                    "tone": tone,
                    "image_url": image_url
                }
            })
        return items
    except Exception as e:
        print(f"데이터베이스 조회 중 오류 발생: {e}")
        return []
    finally:
        session.close()

# 사용자 정보 로드 함수 추가
def load_user_data(user_id: str):
    try:
        session = SessionLocal()
        query = text("""
            SELECT 
                id,
                gender,
                age,
                height,
                weight,
                skin_tone,
                body_image_url
            FROM users
            WHERE id = :user_id
        """)
        
        result = session.execute(query, {"user_id": user_id}).fetchone()
        
        if result:
            return {
                "id": result[0],
                "gender": result[1],
                "age": result[2],
                "height": result[3],
                "weight": result[4],
                "skin_tone": result[5],
                "body_image_url": result[6]
            }
        return None
    except Exception as e:
        print(f"사용자 데이터 조회 중 오류 발생: {e}")
        return None
    finally:
        session.close()

# GPT에 추천 조합 요청 (사용자 정보 반영)
def ask_gpt_for_filtering_criteria(situation, user_data, available_types, target_time, target_place, high_temp, low_temp, rain_percent, status):
    gender = "여성" if user_data["gender"] == "FEMALE" else "남성"
    skin_tone = {
        "COOL": "쿨톤",
        "WARM": "웜톤",
        "NEUTRAL": "뉴트럴톤"
    }.get(user_data["skin_tone"], "뉴트럴톤")
    
    prompt = f"""
    상황: {situation}
    성별: {gender}
    나이: {user_data["age"]}세
    키: {user_data["height"]}cm
    체중: {user_data["weight"]}kg
    피부톤: {skin_tone}
    시간: {target_time}
    장소: {target_place}
    기온: {high_temp}°C ~ {low_temp}°C
    강수확률: {rain_percent}%
    날씨상태: {status}

    위 상황과 사용자의 신체 정보를 고려하여 가장 적합한 옷 조합을 3개 추천해주세요.

    1. 조합은 다음 중 하나여야 합니다:
      - (TOP + BOTTOM) 조합
      - ONEPIECE 단독 조합 (여성인 경우에만)

    2. TOP + BOTTOM 조합을 선택했다면 TOP과 BOTTOM이 각각 1벌씩 있어야 합니다.
    3. ONEPIECE를 선택했다면 TOP과 BOTTOM을 동시에 선택하면 안 됩니다.
    4. 남성인 경우 ONEPIECE 조합은 추천하지 마세요.
    5. 사용자의 피부톤({skin_tone})에 어울리는 색상을 고려해주세요.

    옷장에 있는 옷 종류 목록은 다음과 같습니다:
    {available_types}

    위 목록에 있는 옷 종류만 사용해서 추천해주세요.
    날씨와 시간, 장소를 고려하여 적절한 옷을 선택해주세요.

    반드시 아래 형식으로만 응답해주세요. 다른 설명이나 추가 텍스트는 포함하지 마세요.

    1. TOP: [옷종류], BOTTOM: [옷종류]
    2. TOP: [옷종류], BOTTOM: [옷종류]
    3. TOP: [옷종류], BOTTOM: [옷종류]

    또는 여성인 경우:

    1. TOP: [옷종류], BOTTOM: [옷종류]
    2. TOP: [옷종류], BOTTOM: [옷종류]
    3. ONEPIECE: [옷종류]

    예시:
    1. TOP: SHIRT, BOTTOM: JEANS
    2. TOP: SWEATER, BOTTOM: SLACKS
    3. TOP: TSHIRT, BOTTOM: SHORTS
    """
    messages = [
        SystemMessage(content="당신은 패션 스타일리스트입니다. 반드시 영문으로만 응답하고, 주어진 형식에 정확히 맞춰서만 응답해주세요."),
        HumanMessage(content=prompt)
    ]
    return llm.invoke(messages).content

# GPT에 일반적인 옷 추천 요청 (사용자 정보 반영)
def ask_gpt_for_general_recommendation(situation, user_data, target_time, target_place, high_temp, low_temp, rain_percent, status):
    gender = "여성" if user_data["gender"] == "FEMALE" else "남성"
    skin_tone = {
        "COOL": "쿨톤",
        "WARM": "웜톤",
        "NEUTRAL": "뉴트럴톤"
    }.get(user_data["skin_tone"], "뉴트럴톤")
    
    prompt = f"""
    상황: {situation}
    성별: {gender}
    나이: {user_data["age"]}세
    키: {user_data["height"]}cm
    체중: {user_data["weight"]}kg
    피부톤: {skin_tone}
    시간: {target_time}
    장소: {target_place}
    기온: {high_temp}°C ~ {low_temp}°C
    강수확률: {rain_percent}%
    날씨상태: {status}

    위 상황과 사용자의 신체 정보를 고려하여 가장 적합한 옷 조합을 3개 추천해주세요.
    실제 옷장에 없는 옷도 추천해도 됩니다.

    1. 조합은 다음 중 하나여야 합니다:
      - (TOP + BOTTOM) 조합
      - ONEPIECE 단독 조합 (여성인 경우에만)

    2. TOP + BOTTOM 조합을 선택했다면 TOP과 BOTTOM이 각각 1벌씩 있어야 합니다.
    3. ONEPIECE를 선택했다면 TOP과 BOTTOM을 동시에 선택하면 안 됩니다.
    4. 남성인 경우 ONEPIECE 조합은 추천하지 마세요.
    5. 사용자의 피부톤({skin_tone})에 어울리는 색상을 고려해주세요.

    옷 종류 목록은 다음과 같습니다:
    - TOP: BLOUSE, CARDIGAN, COAT, JACKET, JUMPER, SHIRT, SWEATER, TSHIRT, VEST
    - BOTTOM: ACTIVEWEAR, JEANS, PANTS, SHORTS, SKIRT, SLACKS
    - ONEPIECE: DRESS, JUMPSUIT

    반드시 아래 형식으로만 응답해주세요. 다른 설명이나 추가 텍스트는 포함하지 마세요:

    1. TOP: [옷종류], BOTTOM: [옷종류]
    2. TOP: [옷종류], BOTTOM: [옷종류]
    3. TOP: [옷종류], BOTTOM: [옷종류]

    또는 여성인 경우:

    1. TOP: [옷종류], BOTTOM: [옷종류]
    2. TOP: [옷종류], BOTTOM: [옷종류]
    3. ONEPIECE: [옷종류]

    예시:
    1. TOP: SHIRT, BOTTOM: JEANS
    2. TOP: SWEATER, BOTTOM: SLACKS
    3. TOP: TSHIRT, BOTTOM: SHORTS
    """
    messages = [
        SystemMessage(content="당신은 패션 스타일리스트입니다. 반드시 영문으로만 응답하고, 주어진 형식에 정확히 맞춰서만 응답해주세요."),
        HumanMessage(content=prompt)
    ]
    return llm.invoke(messages).content

# GPT에 옷장 기반 최종 추천 요청 (사용자 정보 반영)
def ask_gpt_for_best_clothing_sets(situation, outfit_sets, recommended_combinations, is_closet_only, user_data, target_time, target_place, high_temp, low_temp, rain_percent, status):
    gender = "여성" if user_data["gender"] == "FEMALE" else "남성"
    skin_tone = {
        "COOL": "쿨톤",
        "WARM": "웜톤",
        "NEUTRAL": "뉴트럴톤"
    }.get(user_data["skin_tone"], "뉴트럴톤")
    
    prompt_lines = [f"{i+1}. {s}" for i, s in enumerate(outfit_sets)]
    
    if is_closet_only:
        prompt = f"""
        상황: {situation}
        성별: {gender}
        나이: {user_data["age"]}세
        키: {user_data["height"]}cm
        체중: {user_data["weight"]}kg
        피부톤: {skin_tone}
        시간: {target_time}
        장소: {target_place}
        기온: {high_temp}°C ~ {low_temp}°C
        강수확률: {rain_percent}%
        날씨상태: {status}

        아래는 추천받은 3개의 옷 조합입니다:
        {recommended_combinations}

        그리고 아래는 옷장에 있는 실제 옷들입니다:
        {chr(10).join(prompt_lines)}

        각 추천 조합에 대해, 위의 모든 상황과 사용자의 신체 정보를 고려하여 옷장에서 가장 적절한 옷을 하나씩 선택해주세요.
        선택한 옷에 대해 왜 그 옷이 상황과 사용자에게 적절한지 설명해주세요.

        응답은 반드시 아래 형식으로만 작성해주세요. 추가 설명이나 결론은 작성하지 마세요:

        요약: [상황, 시간, 장소, 날씨를 포함한 한 줄 요약]

        조합 1: <첫 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리>
        이유: <이유>

        조합 2: <두 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리>
        이유: <이유>

        조합 3: <세 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리>
        이유: <이유>

        예시:
        조합 1: TOP: BLOUSE, BOTTOM: JEANS
        선택한 옷: CLT_000070 (BLOUSE) + CLT_000077 (JEANS)
        이유: CLT_000070 블라우스는 쿨톤 피부에 잘 어울리는 색상이고, CLT_000077 청바지는 편안하면서도 스타일리시한 조합을 제공합니다.
        """
    else:
        prompt = f"""
        상황: {situation}
        성별: {gender}
        나이: {user_data["age"]}세
        키: {user_data["height"]}cm
        체중: {user_data["weight"]}kg
        피부톤: {skin_tone}
        시간: {target_time}
        장소: {target_place}
        기온: {high_temp}°C ~ {low_temp}°C
        강수확률: {rain_percent}%
        날씨상태: {status}

        아래는 추천받은 3개의 옷 조합입니다:
        {recommended_combinations}

        그리고 아래는 옷장에 있는 실제 옷들입니다:
        {chr(10).join(prompt_lines)}

        각 추천 조합에 대해, 다음 규칙을 따라 응답해주세요:
        1. 옷장에 있는 옷이면 해당 옷의 ID를 사용하고, 없는 옷이면 "추천: [옷 종류]" 형식으로 표시
        2. 각 조합이 위의 모든 상황과 사용자의 신체 정보에 적절한 이유를 설명해주세요
        3. 옷장에 없는 옷을 추천한 경우, 왜 그 옷이 필요한지 설명해주세요

        응답은 반드시 아래 형식으로만 작성해주세요. 추가 설명이나 결론은 작성하지 마세요:

        요약: [상황, 시간, 장소, 날씨를 포함한 한 줄 요약]

        조합 1: <첫 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리 또는 "추천: [옷 종류]">
        이유: <이유>

        조합 2: <두 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리 또는 "추천: [옷 종류]">
        이유: <이유>

        조합 3: <세 번째 추천 조합>
        선택한 옷: <옷장에서 선택한 옷 ID와 카테고리 또는 "추천: [옷 종류]">
        이유: <이유>

        예시:
        조합 1: TOP: BLOUSE, BOTTOM: JEANS
        선택한 옷: CLT_000070 (BLOUSE) + CLT_000077 (JEANS)
        이유: CLT_000070 블라우스는 쿨톤 피부에 잘 어울리는 색상이고, CLT_000077 청바지는 편안하면서도 스타일리시한 조합을 제공합니다.
        """

    messages = [
        SystemMessage(content="당신은 패션 코디 전문가입니다."),
        HumanMessage(content=prompt)
    ]
    return llm.invoke(messages).content

# GPT 응답 파싱 함수
def parse_gpt_result(text: str):
    result = []
    
    # 요약 추출
    summary_match = re.search(r"요약: (.+?)(?=\n\n|$)", text)
    summary = summary_match.group(1) if summary_match else ""
    
    # 조합 추출
    pattern = re.compile(r"조합 \d+: .+?\n선택한 옷: .+?\n이유: .+?(?=(?:\n조합 \d+:|$))", re.DOTALL)
    matches = pattern.findall(text)

    for match in matches:
        lines = match.strip().split("\n")
        if len(lines) >= 3:
            combination = lines[0].strip()
            selected = lines[1].strip()
            reason = lines[2].strip()
            
            # "선택한 옷: " 접두사 제거
            if selected.startswith("선택한 옷: "):
                selected = selected[7:]
            
            # "이유: " 접두사 제거
            if reason.startswith("이유: "):
                reason = reason[4:]
            
            result.append({
                "combination": combination,
                "selected": selected,
                "reason": reason
            })
    
    return {
        "summary": summary,
        "outfits": result
    }

# FASHN API 설정
API_KEY = os.getenv("FASHN_API_KEY")
if not API_KEY:
    raise ValueError("FASHN API 키가 설정되지 않았습니다. .env 파일을 확인해주세요.")
BASE_URL = "https://api.fashn.ai/v1"

# AWS S3 설정
s3_client = boto3.client('s3')
BUCKET_NAME = 'amzn-s3-fitu-bucket'
RESULT_FOLDER = 'FASHNAI_result/'

def encode_image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            # 바이너리 데이터를 Base64로 인코딩
            binary_data = image_file.read()
            # base64.b64encode는 자동으로 패딩을 처리합니다
            encoded = base64.b64encode(binary_data)
            return encoded.decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Base64 인코딩 실패: {e}")
        raise

def download_image(url, save_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(save_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

def save_image_to_s3(image_url: str, user_id: str) -> str:
    try:
        # 이미지 다운로드
        response = requests.get(image_url)
        if response.status_code != 200:
            return None, "이미지 다운로드 실패"

        # S3에 저장할 파일명 생성 (user_id와 timestamp를 포함)
        timestamp = int(time.time())
        file_name = f"{RESULT_FOLDER}{user_id}_{timestamp}_{uuid.uuid4()}.jpg"

        # S3에 이미지 업로드
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=response.content,
            ContentType='image/jpeg'
        )

        # S3 URL 생성
        s3_url = f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{file_name}"
        return s3_url, None

    except Exception as e:
        return None, f"S3 저장 중 오류 발생: {str(e)}"

async def process_virtual_tryon_async(model_image_path, garment_image_path, category, user_id):
    try:
        print(f"\n[DEBUG] 가상 피팅 시작 - 카테고리: {category}")
        print(f"[DEBUG] 모델 이미지 경로: {model_image_path}")
        print(f"[DEBUG] 의류 이미지 경로: {garment_image_path}")

        # 이미지를 Base64로 인코딩
        model_image_base64 = encode_image_to_base64(model_image_path)
        garment_image_base64 = encode_image_to_base64(garment_image_path)
        print("[DEBUG] 이미지 Base64 인코딩 완료")

        # 카테고리 매핑
        category_mapping = {
            "tops": "tops",
            "bottoms": "bottoms",
            "one-pieces": "one-pieces"
        }
        
        mapped_category = category_mapping.get(category, "auto")
        print(f"[DEBUG] 매핑된 카테고리: {mapped_category}")

        # API 요청 데이터 준비
        input_data = {
            "model_image": f"data:image/jpeg;base64,{model_image_base64}",
            "garment_image": f"data:image/jpeg;base64,{garment_image_base64}",
            "category": mapped_category,
            # "mode": "quality",
            "mode": "performance",
            "garment_photo_type": "auto",
            "num_samples": 1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        print("[DEBUG] FASHN API 호출 시작")
        # Base64 이미지 데이터는 길이만 표시
        debug_input_data = input_data.copy()
        debug_input_data["model_image"] = f"data:image/jpeg;base64,[{len(model_image_base64)} bytes]"
        debug_input_data["garment_image"] = f"data:image/jpeg;base64,[{len(garment_image_base64)} bytes]"
        print(f"[DEBUG] API 요청 데이터: {debug_input_data}")
        print(f"[DEBUG] API 요청 헤더: {headers}")

        async with aiohttp.ClientSession() as session:
            # 1. /run 엔드포인트로 요청
            async with session.post(f"{BASE_URL}/run", json=input_data, headers=headers) as run_response:
                if run_response.status != 200:
                    error_data = await run_response.json()
                    print(f"[ERROR] API 호출 실패: {error_data}")
                    return None, f"API 호출 실패: {error_data.get('error', '알 수 없는 에러')}"
                
                run_data = await run_response.json()
                prediction_id = run_data.get("id")
                if not prediction_id:
                    print("[ERROR] 예측 ID를 받지 못함")
                    return None, "예측 ID를 받지 못했습니다"
                
                print(f"[DEBUG] 예측 ID: {prediction_id}")
                
                # 2. 상태 확인 및 결과 대기
                while True:
                    async with session.get(f"{BASE_URL}/status/{prediction_id}", headers=headers) as status_response:
                        if status_response.status != 200:
                            error_text = await status_response.text()
                            print(f"[ERROR] 상태 확인 실패: {error_text}")
                            return None, f"상태 확인 실패: {error_text}"
                        
                        status_data = await status_response.json()
                        print(f"[DEBUG] 현재 상태: {status_data['status']}")

                        if status_data["status"] == "completed":
                            result_url = status_data["output"][0] if isinstance(status_data["output"], list) else status_data["output"]
                            print(f"[DEBUG] 결과 URL: {result_url}")
                            
                            # S3에 이미지 저장
                            s3_url, error = save_image_to_s3(result_url, user_id)
                            if error:
                                print(f"[ERROR] S3 저장 실패: {error}")
                                return None, error
                                
                            print(f"[DEBUG] S3 저장 완료: {s3_url}")
                            return s3_url, None

                        elif status_data["status"] in ["starting", "in_queue", "processing"]:
                            print("[DEBUG] 처리 중... 3초 대기")
                            await asyncio.sleep(3)
                        else:
                            print(f"[ERROR] 예측 실패: {status_data.get('error')}")
                            return None, f"예측 실패: {status_data.get('error')}"

    except Exception as e:
        print(f"[ERROR] 예상치 못한 에러: {e}")
        return None, f"예상치 못한 에러가 발생했습니다: {e}"

async def apply_virtual_tryon_async(user_data, outfit_combination):
    try:
        print("\n[DEBUG] 가상 피팅 시작")
        print(f"[DEBUG] 사용자 ID: {user_data['id']}")
        print(f"[DEBUG] 성별: {user_data['gender']}")

        # 사용자 이미지 URL 확인 및 기본 모델 이미지 설정
        model_image_url = user_data["body_image_url"]
        if not model_image_url:
            if user_data["gender"] == "FEMALE":
                model_image_url = "https://amzn-s3-fitu-bucket.s3.ap-northeast-2.amazonaws.com/basic_model/ChatGPT_image_woman.png"
            else:
                model_image_url = "https://amzn-s3-fitu-bucket.s3.ap-northeast-2.amazonaws.com/basic_model/ChatGPT_Image_man.png"
        print(f"[DEBUG] 모델 이미지 URL: {model_image_url}")

        # 모델 이미지 다운로드
        async with aiohttp.ClientSession() as session:
            async with session.get(model_image_url) as response:
                if response.status != 200:
                    print(f"[ERROR] 모델 이미지 다운로드 실패: {response.status}")
                    return None, "모델 이미지를 다운로드할 수 없습니다."

                body_image_content = await response.read()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(body_image_content)
            model_image_path = tmp_file.name
        print(f"[DEBUG] 모델 이미지 저장 완료: {model_image_path}")

        # 옷 조합 분석
        combination = outfit_combination["combination"]
        selected = outfit_combination["selected"]
        print(f"[DEBUG] 처리할 옷 조합: {combination}")
        print(f"[DEBUG] 선택된 옷: {selected}")

        # 옷장에 없는 옷을 추천한 경우
        if selected.startswith("추천:"):
            print("[DEBUG] 옷장에 없는 옷 추천됨")
            return None, "옷장에 없는 옷은 가상 피팅을 할 수 없습니다."

        if "DRESS" in combination or "JUMPSUIT" in combination:
            # 원피스인 경우
            clothing_id = selected.split(" ")[0]  # CLT_000001 형식의 ID
            print(f"[DEBUG] 원피스 ID: {clothing_id}")
            
            # DB에서 해당 옷의 image_url 가져오기
            session = SessionLocal()
            query = text("""
                SELECT image_url 
                FROM clothes 
                WHERE id = :id AND user_id = :user_id
            """)
            result = session.execute(query, {
                "id": int(clothing_id.split("_")[1]),
                "user_id": user_data["id"]
            }).fetchone()
            session.close()
            
            if not result or not result[0]:
                print(f"[ERROR] 의류 이미지를 찾을 수 없음: {clothing_id}")
                return None, f"의류 이미지를 찾을 수 없습니다. (ID: {clothing_id})"
                
            garment_url = result[0]
            print(f"[DEBUG] 원피스 이미지 URL: {garment_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(garment_url) as response:
                    if response.status != 200:
                        print(f"[ERROR] 의류 이미지 다운로드 실패: {response.status}")
                        return None, f"의류 이미지를 다운로드할 수 없습니다. (URL: {garment_url}, Status: {response.status})"

                    garment_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(garment_content)
                garment_image_path = tmp_file.name
            print(f"[DEBUG] 의류 이미지 저장 완료: {garment_image_path}")

            print("[DEBUG] 원피스 가상 피팅 시작 (one-pieces 카테고리 사용)")
            result_url, error = await process_virtual_tryon_async(model_image_path, garment_image_path, "one-pieces", user_data["id"])
            
            # 임시 파일 삭제
            os.unlink(garment_image_path)
            os.unlink(model_image_path)
            print("[DEBUG] 임시 파일 삭제 완료")
            
            return result_url, error

        else:
            # 상의 + 하의 조합인 경우
            top_id, bottom_id = selected.split(" + ")
            top_id = top_id.split(" ")[0]  # ID만 추출 (예: 61)
            bottom_id = bottom_id.split(" ")[0]  # ID만 추출 (예: 62)
            print(f"[DEBUG] 상의 ID: {top_id}, 하의 ID: {bottom_id}")

            # DB에서 해당 옷들의 image_url 가져오기
            session = SessionLocal()
            query = text("""
                SELECT id, image_url 
                FROM clothes 
                WHERE id IN (:top_id, :bottom_id) 
                AND user_id = :user_id
            """)
            result = session.execute(query, {
                "top_id": int(top_id),
                "bottom_id": int(bottom_id),
                "user_id": user_data["id"]
            }).fetchall()
            session.close()
            
            if len(result) != 2:
                print(f"[ERROR] 의류 이미지를 찾을 수 없음: 상의={top_id}, 하의={bottom_id}")
                return None, f"의류 이미지를 찾을 수 없습니다. (상의: {top_id}, 하의: {bottom_id})"

            # 결과를 id를 기준으로 정렬하여 top과 bottom 매칭
            result_dict = {row[0]: row[1] for row in result}
            top_url = result_dict.get(int(top_id))
            bottom_url = result_dict.get(int(bottom_id))

            if not top_url or not bottom_url:
                print(f"[ERROR] 의류 URL 누락: 상의={top_url}, 하의={bottom_url}")
                return None, f"의류 이미지를 찾을 수 없습니다. (상의 URL: {top_url}, 하의 URL: {bottom_url})"

            print(f"[DEBUG] 상의 이미지 URL: {top_url}")
            print(f"[DEBUG] 하의 이미지 URL: {bottom_url}")

            # 하의 먼저 적용
            async with aiohttp.ClientSession() as session:
                async with session.get(bottom_url) as response:
                    if response.status != 200:
                        print(f"[ERROR] 하의 이미지 다운로드 실패: {response.status}")
                        return None, f"하의 이미지를 다운로드할 수 없습니다. (URL: {bottom_url}, Status: {response.status})"

                    bottom_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(bottom_content)
                bottom_image_path = tmp_file.name
            print(f"[DEBUG] 하의 이미지 저장 완료: {bottom_image_path}")

            print("[DEBUG] 하의 가상 피팅 시작 (bottoms 카테고리 사용)")
            intermediate_url, error = await process_virtual_tryon_async(model_image_path, bottom_image_path, "bottoms", user_data["id"])
            if error:
                print(f"[ERROR] 하의 가상 피팅 실패: {error}")
                os.unlink(bottom_image_path)
                os.unlink(model_image_path)
                return None, error

            # 중간 결과 이미지 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(intermediate_url) as response:
                    if response.status != 200:
                        print(f"[ERROR] 중간 결과 이미지 다운로드 실패: {response.status}")
                        return None, f"중간 결과 이미지를 다운로드할 수 없습니다. (URL: {intermediate_url}, Status: {response.status})"

                    intermediate_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(intermediate_content)
                intermediate_image_path = tmp_file.name
            print(f"[DEBUG] 중간 결과 이미지 저장 완료: {intermediate_image_path}")

            # 상의 이미지 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(top_url) as response:
                    if response.status != 200:
                        print(f"[ERROR] 상의 이미지 다운로드 실패: {response.status}")
                        return None, f"상의 이미지를 다운로드할 수 없습니다. (URL: {top_url}, Status: {response.status})"

                    top_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(top_content)
                top_image_path = tmp_file.name
            print(f"[DEBUG] 상의 이미지 저장 완료: {top_image_path}")

            print("[DEBUG] 상의 가상 피팅 시작 (tops 카테고리 사용)")
            final_url, error = await process_virtual_tryon_async(intermediate_image_path, top_image_path, "tops", user_data["id"])

            # 임시 파일 삭제
            os.unlink(bottom_image_path)
            os.unlink(intermediate_image_path)
            os.unlink(top_image_path)
            os.unlink(model_image_path)
            print("[DEBUG] 임시 파일 삭제 완료")

            return final_url, error

    except Exception as e:
        print(f"[ERROR] 가상 피팅 처리 중 예상치 못한 에러: {e}")
        return None, f"가상 피팅 처리 중 오류 발생: {e}"

# 옷장에서 조합 매칭 (상세 정보 필요)
def match_outfit_combinations(data, recommended_combinations, user_data, available_types):
    outfit_sets = []
    for line in recommended_combinations.splitlines():
        if 'onepiece' in line.lower() and user_data["gender"] == "FEMALE":
            # ONEPIECE 매칭
            for op in available_types['ONEPIECE']:
                if op in line.upper():
                    # ONEPIECE 카테고리의 해당 상세 타입(DRESS/JUMPSUIT) 매칭
                    matches = [item for item in data if item['attributes']['type'] == 'ONEPIECE' and item['attributes']['category'] == op]
                    for match in matches:
                        outfit_sets.append(f"{match['clothing_id']} ({match['attributes']['category']})")
                        
        elif 'top' in line.lower() and 'bottom' in line.lower():
            # TOP과 BOTTOM 타입 추출
            top_type = None
            bottom_type = None
            
            # TOP 상세 카테고리 매칭
            for top in available_types['TOP']:
                if top in line.upper():
                    top_type = top
                    break
                    
            # BOTTOM 상세 카테고리 매칭
            for bottom in available_types['BOTTOM']:
                if bottom in line.upper():
                    bottom_type = bottom
                    break
            
            if top_type and bottom_type:
                # TOP 매칭
                top_matches = [item for item in data if item['attributes']['type'] == 'TOP' and item['attributes']['category'] == top_type]
                # BOTTOM 매칭
                bottom_matches = [item for item in data if item['attributes']['type'] == 'BOTTOM' and item['attributes']['category'] == bottom_type]
                
                if top_matches and bottom_matches:
                    for t in top_matches:
                        for b in bottom_matches:
                            outfit_sets.append(f"{t['clothing_id']} ({t['attributes']['category']}) + {b['clothing_id']} ({b['attributes']['category']})")
    
    print(f"매칭된 옷 조합: {outfit_sets}")  # 디버깅용 로그
    return outfit_sets

# 메인 API 엔드포인트
@app.post("/vision/recommendation")
async def recommend(request: RecommendationRequest):
    user_data = load_user_data(request.user_id)
    
    if not user_data:
        return {
            "header": {
                "resultCode": "01",
                "resultMsg": "USER_NOT_FOUND"
            },
            "body": {
                "result": []
            }
        }
    
    # 옷장에 있는 옷 종류만 추출 (중복 제거)
    data = load_clothing_types_from_db(request.user_id)
    print(f"옷장 데이터: {data}")
    
    available_types = {
        'TOP': set(),
        'BOTTOM': set(),
        'ONEPIECE': set()
    }
    
    for item in data:
        type_name = item['type']  # 일반 카테고리 (TOP, BOTTOM, ONEPIECE)
        category = item['category']  # 상세 카테고리 (BLOUSE, JEANS 등)
        available_types[type_name].add(category)
    
    print(f"가용 옷 종류: {available_types}")
    
    if request.showClosetOnly:
        # 프롬프트용 문자열 생성
        available_types_str = ""
        for category, types in available_types.items():
            if types:  # 해당 카테고리에 옷이 있는 경우만 추가
                available_types_str += f"- {category}: {', '.join(sorted(types))}\n"
        
        print(f"생성된 프롬프트 문자열: {available_types_str}")
        
        # 옷장 데이터만 사용하는 경우
        if not available_types_str:  # 옷장 데이터가 없는 경우
            return {
                "header": {
                    "resultCode": "01",
                    "resultMsg": "NO_CLOTHES"
                },
                "body": {
                    "result": []
                }
            }
            
        recommended_combinations = ask_gpt_for_filtering_criteria(
            request.situation,
            user_data,
            available_types_str,
            request.targetTime,
            request.targetPlace,
            request.highTemperature,
            request.lowTemperature,
            request.rainPercent,
            request.status
        )
    else:
        # 일반적인 추천을 포함하는 경우
        recommended_combinations = ask_gpt_for_general_recommendation(
            request.situation,
            user_data,
            request.targetTime,
            request.targetPlace,
            request.highTemperature,
            request.lowTemperature,
            request.rainPercent,
            request.status
        )

    # 옷장에서 조합 매칭
    data = load_clothing_details_from_db(request.user_id)
    outfit_sets = match_outfit_combinations(data, recommended_combinations, user_data, available_types)
    
    if not outfit_sets and request.showClosetOnly:
        return {
            "header": {
                "resultCode": "01",
                "resultMsg": "NO_MATCH"
            },
            "body": {
                "result": []
            }
        }

    final_response = ask_gpt_for_best_clothing_sets(
        request.situation,
        outfit_sets,
        recommended_combinations,
        request.showClosetOnly,
        user_data,
        request.targetTime,
        request.targetPlace,
        request.highTemperature,
        request.lowTemperature,
        request.rainPercent,
        request.status
    )
    structured_result = parse_gpt_result(final_response)

    # 각 조합에 대해 가상 피팅을 비동기로 수행
    tasks = []
    for outfit in structured_result["outfits"]:
        if not request.showClosetOnly and "추천:" in outfit["selected"]:
            outfit["virtualTryonImage"] = None
            outfit["virtualTryonError"] = "옷장에 없는 옷은 가상 피팅을 할 수 없습니다."
            continue
            
        if outfit["selected"] != "해당 조합에 맞는 옷이 없습니다":
            tasks.append(apply_virtual_tryon_async(user_data, outfit))

    # 모든 가상 피팅 작업을 동시에 실행
    results = await asyncio.gather(*tasks)

    # 결과를 각 outfit에 할당
    for outfit, (tryon_url, error) in zip(structured_result["outfits"], results):
        if error:
            outfit["virtualTryonImage"] = None
            outfit["virtualTryonError"] = error
        else:
            outfit["virtualTryonImage"] = tryon_url
            outfit["virtualTryonError"] = None

    return {
        "header": {
            "resultCode": "00",
            "resultMsg": "SUCCESS"
        },
        "body": {
            "summary": structured_result["summary"],
            "result": structured_result["outfits"]
        }
    } 