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
import openai
from PIL import Image
import io

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

# 카테고리 한글 매핑 추가
CATEGORY_KOREAN_MAP = {
    'BLOUSE': '블라우스',
    'CARDIGAN': '가디건',
    'COAT': '코트',
    'JACKET': '자켓',
    'JUMPER': '점퍼',
    'SHIRT': '셔츠',
    'SWEATER': '스웨터',
    'TSHIRT': '티셔츠',
    'VEST': '베스트',
    'ACTIVEWEAR': '활동복',
    'JEANS': '청바지',
    'PANTS': '바지',
    'SHORTS': '반바지',
    'SKIRT': '치마',
    'SLACKS': '슬랙스',
    'DRESS': '드레스',
    'JUMPSUIT': '점프수트'
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

def get_session():
    """DB 세션 생성"""
    return SessionLocal()

def load_clothing_types_from_db(user_id: str):
    """옷장의 옷 종류만 가져오는 함수"""
    try:
        session = get_session()
        query = text("""
            SELECT DISTINCT type, category
            FROM clothes
            WHERE user_id = :user_id
        """)
        
        result = session.execute(query, {"user_id": user_id}).fetchall()
        
        items = []
        for row in result:
            type_name = row[0].strip().upper()
            category = row[1].strip().upper()
            
            if type_name in CATEGORY_MAP and category in CATEGORY_MAP[type_name]:
                items.append({"type": type_name, "category": category})
        
        return items
    except Exception as e:
        print(f"[ERROR] 데이터베이스 조회 중 오류 발생: {e}")
        return []
    finally:
        session.close()

def load_clothing_details_from_db(user_id: str):
    """옷의 상세 정보를 가져오는 함수"""
    try:
        session = get_session()
        query = text("""
            SELECT id, type, category, pattern, color, image_url
            FROM clothes
            WHERE user_id = :user_id
        """)
        
        result = session.execute(query, {"user_id": user_id}).fetchall()
        
        items = []
        for row in result:
            type_name = row[1].strip().upper()
            category = row[2].strip().upper()
            tone = TONE_MAP.get(row[4].strip().upper(), "고려하지 않음")
            image_url = row[5].strip()

            if not image_url or not image_url.startswith('http'):
                continue

            items.append({
                "clothing_id": str(row[0]),
                "attributes": {
                    "type": type_name,
                    "category": category,
                    "pattern": row[3].strip().upper(),
                    "tone": tone,
                    "image_url": image_url
                }
            })
        
        return items
    except Exception as e:
        print(f"[ERROR] 데이터베이스 조회 중 오류 발생: {e}")
        return []
    finally:
        session.close()

def load_user_data(user_id: str):
    """사용자 정보 로드 함수"""
    try:
        session = get_session()
        query = text("""
            SELECT id, gender, age, height, weight, skin_tone, body_image_url
            FROM users
            WHERE id = :user_id
        """)
        
        result = session.execute(query, {"user_id": user_id}).fetchone()
        
        if result:
            user_data = {
                "id": result[0], "gender": result[1], "age": result[2],
                "height": result[3], "weight": result[4], "skin_tone": result[5],
                "body_image_url": result[6]
            }
            return user_data
        else:
            return None
    except Exception as e:
        print(f"[ERROR] 사용자 데이터 조회 중 오류 발생: {e}")
        return None
    finally:
        session.close()

def get_season_guide(avg_temp):
    """기온에 따른 계절 가이드 반환"""
    if avg_temp >= 25:
        return {
            "guide": "여름철 (더운 날씨) - 얇고 시원한 소재의 옷을 추천합니다.",
            "top": "TSHIRT, SHIRT (얇은 소재), BLOUSE (얇은 소재)",
            "bottom": "SHORTS, PANTS (얇은 소재), SKIRT (얇은 소재)",
            "onepiece": "DRESS (얇은 소재), JUMPSUIT (얇은 소재)"
        }
    elif avg_temp >= 15:
        return {
            "guide": "봄/가을철 (선선한 날씨) - 적당한 두께의 옷을 추천합니다.",
            "top": "SHIRT, BLOUSE, CARDIGAN, SWEATER, JACKET (얇은 겉옷)",
            "bottom": "JEANS, PANTS, SKIRT, SLACKS",
            "onepiece": "DRESS, JUMPSUIT"
        }
    else:
        return {
            "guide": "겨울철 (추운 날씨) - 두꺼운 소재의 옷을 추천합니다.",
            "top": "COAT, JACKET (두꺼운 겉옷), SWEATER, CARDIGAN, JUMPER",
            "bottom": "JEANS, PANTS, SLACKS (두꺼운 소재)",
            "onepiece": "DRESS (두꺼운 소재), JUMPSUIT (두꺼운 소재)"
        }

def create_gpt_prompt(situation, user_data, available_types_str, target_time, target_place, 
                     high_temp, low_temp, rain_percent, status, is_closet_only=True):
    """GPT 프롬프트 생성 함수"""
    gender = "여성" if user_data["gender"] == "FEMALE" else "남성"
    skin_tone = {
        "COOL": "쿨톤", "WARM": "웜톤", "NEUTRAL": "뉴트럴톤"
    }.get(user_data["skin_tone"], "뉴트럴톤")
    
    avg_temp = (high_temp + low_temp) / 2
    season_info = get_season_guide(avg_temp)
    
    closet_info = f"""
    옷장에 있는 옷 종류 목록은 다음과 같습니다:
    {available_types_str}
    위 목록에 있는 옷 종류만 사용해서 추천해주세요.
    """ if is_closet_only else """
    옷 종류 목록은 다음과 같습니다:
    - TOP: BLOUSE, CARDIGAN, COAT, JACKET, JUMPER, SHIRT, SWEATER, TSHIRT, VEST
    - BOTTOM: ACTIVEWEAR, JEANS, PANTS, SHORTS, SKIRT, SLACKS
    - ONEPIECE: DRESS, JUMPSUIT
    """
    
    return f"""
    상황: {situation}
    성별: {gender}
    나이: {user_data["age"]}세
    키: {user_data["height"]}cm
    체중: {user_data["weight"]}kg
    피부톤: {skin_tone}
    시간: {target_time}
    장소: {target_place}
    기온: {high_temp}°C ~ {low_temp}°C (평균 {avg_temp:.1f}°C)
    강수확률: {rain_percent}%
    날씨상태: {status}
    
    **계절별 옷 추천 가이드:**
    {season_info["guide"]}
    
    **기온별 옷 선택 기준:**
    - 25°C 이상 (여름): 얇은 소재, 반팔, 반바지, 시원한 원피스
    - 15-24°C (봄/가을): 적당한 두께, 긴팔, 얇은 겉옷, 긴바지
    - 15°C 미만 (겨울): 두꺼운 소재, 코트, 패딩, 니트, 두꺼운 바지

    **현재 기온({avg_temp:.1f}°C)에 적합한 카테고리별 추천:**
    - TOP: {season_info["top"]}
    - BOTTOM: {season_info["bottom"]}
    - ONEPIECE: {season_info["onepiece"]}

    위 상황과 사용자의 신체 정보를 고려하여 가장 적합한 옷 조합을 3개 추천해주세요.

    1. 조합은 다음 중 하나여야 합니다:
      - (TOP + BOTTOM) 조합
      - ONEPIECE 단독 조합 (여성인 경우에만)

    2. TOP + BOTTOM 조합을 선택했다면 TOP과 BOTTOM이 각각 1벌씩 있어야 합니다.
    3. ONEPIECE를 선택했다면 TOP과 BOTTOM을 동시에 선택하면 안 됩니다.
    4. **남성인 경우 3개 조합 모두 TOP + BOTTOM 조합으로 추천해주세요. ONEPIECE는 추천하지 마세요.**
    5. 여성이라도 꼭 ONEPIECE 조합을 추천할 필요는 없습니다.
    6. 사용자의 피부톤({skin_tone})에 어울리는 색상을 고려해주세요.
    7. **반드시 기온({avg_temp:.1f}°C)에 맞는 계절의 옷을 선택해주세요.**
    8. **위에서 제시한 카테고리별 추천을 우선적으로 고려해주세요.**

    {closet_info}
    날씨와 시간, 장소를 고려하여 적절한 옷을 선택해주세요.

    응답은 반드시 아래 형식으로만 작성해주세요. 추가 설명이나 결론은 작성하지 마세요:

    조합 1: TOP: [옷종류], BOTTOM: [옷종류]
    조합 2: TOP: [옷종류], BOTTOM: [옷종류]
    조합 3: TOP: [옷종류], BOTTOM: [옷종류]
    """

def ask_gpt_for_recommendation(situation, user_data, available_types_str, target_time, target_place, 
                              high_temp, low_temp, rain_percent, status, is_closet_only=True):
    """GPT에 추천 요청"""
    prompt = create_gpt_prompt(situation, user_data, available_types_str, target_time, target_place,
                              high_temp, low_temp, rain_percent, status, is_closet_only)
    
    messages = [
        SystemMessage(content="당신은 패션 스타일리스트입니다. 반드시 영문으로만 응답하고, 주어진 형식에 정확히 맞춰서만 응답해주세요."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages).content
    return response

def ask_gpt_for_best_clothing_sets(situation, organized_clothes, recommended_combinations, is_closet_only, 
                                  user_data, target_time, target_place, high_temp, low_temp, rain_percent, status):
    """GPT에 옷장 기반 최종 추천 요청"""
    gender = "여성" if user_data["gender"] == "FEMALE" else "남성"
    skin_tone = {
        "COOL": "쿨톤", "WARM": "웜톤", "NEUTRAL": "뉴트럴톤"
    }.get(user_data["skin_tone"], "뉴트럴톤")
    
    avg_temp = (high_temp + low_temp) / 2
    season_info = get_season_guide(avg_temp)
    
    # 카테고리별 옷 리스트를 문자열로 변환
    clothing_list_str = ""
    for clothing_type, categories in organized_clothes.items():
        if categories:
            clothing_list_str += f"\n{clothing_type}:\n"
            for category, items in categories.items():
                clothing_list_str += f"  {category}:\n"
                for item in items:
                    clothing_list_str += f"    - {item['id']} ({item['category']}, {item['pattern']}, {item['tone']})\n"
    
    closet_rule = """
        각 추천 조합에 대해, 위의 모든 상황과 사용자의 신체 정보를 고려하여 옷장에서 가장 적절한 옷을 하나씩 선택해주세요.
        **특히 기온({avg_temp:.1f}°C)에 맞는 계절의 옷을 우선적으로 선택해주세요.**
        
        **추천 이유 작성 가이드:**
        각 조합의 이유는 다음 요소들을 포함하여 상세하고 구체적으로 설명해주세요:
        - **날씨 적합성**: 현재 기온({avg_temp:.1f}°C)과 날씨 상태({status})에 어떻게 적합한지
        - **상황 적합성**: {situation} 상황에서 왜 이 조합이 적절한지
        - **시간대 고려**: {target_time} 시간대에 맞는 스타일링 포인트
        - **장소 적합성**: {target_place} 장소에서의 이미지와 분위기
        - **신체 정보 활용**: {gender}, {user_data["age"]}세, 키 {user_data["height"]}cm, 체중 {user_data["weight"]}kg에 맞는 스타일링
        - **피부톤 고려**: {skin_tone} 피부톤에 어울리는 색상과 스타일
        - **실용성**: 편안함, 활동성, 관리의 용이성 등
        - **스타일링 효과**: 전체적인 이미지와 분위기 연출
        
        선택한 옷에 대해 왜 그 옷이 상황과 사용자에게 적절한지 상세히 설명해주세요.
    """ if is_closet_only else """
        각 추천 조합에 대해, 다음 규칙을 따라 응답해주세요:
        1. 옷장에 있는 옷이면 해당 옷의 ID를 사용하고, 없는 옷이면 "추천: [옷종류] ([패턴], [톤])" 형식으로 표시
        2. **상의+하의 조합에서는 상의와 하의를 각각 독립적으로 선택할 수 있습니다.** 
           - 둘 다 옷장에 있는 옷: "003 (CARDIGAN) + 004 (JEANS)"
           - 둘 다 옷장에 없는 옷: "추천: TSHIRT (STRIPE, DARK) + 추천: PANTS (PLAIN, LIGHT)"
           - 상의만 옷장에 없는 옷: "추천: BLOUSE (PLAIN, LIGHT) + 004 (JEANS)"
           - 하의만 옷장에 없는 옷: "003 (CARDIGAN) + 추천: SKIRT (DOT, LIGHT)"
        3. 패턴은 다음 중 하나를 선택: PLAIN, STRIPE, CHECK, DOT, ANIMAL, ARTIFACT, ETC, NATURE, GEOMETRIC, PLANT, SYMBOL
        4. 톤은 다음 중 하나를 선택: LIGHT, DARK, NOT_CONSIDERED
        5. 각 조합이 위의 모든 상황과 사용자의 신체 정보에 적절한 이유를 상세히 설명해주세요
        6. **특히 기온({avg_temp:.1f}°C)에 맞는 계절의 옷을 우선적으로 선택해주세요.**
        7. 옷장에 없는 옷을 추천한 경우, 왜 그 옷이 필요한지 구체적으로 설명해주세요
        8. **피부톤({skin_tone})에 어울리는 패턴과 톤을 고려해주세요.**
        
        **추천 이유 작성 가이드:**
        각 조합의 이유는 다음 요소들을 포함하여 상세하고 구체적으로 설명해주세요:
        - **날씨 적합성**: 현재 기온({avg_temp:.1f}°C)과 날씨 상태({status})에 어떻게 적합한지
        - **상황 적합성**: {situation} 상황에서 왜 이 조합이 적절한지
        - **시간대 고려**: {target_time} 시간대에 맞는 스타일링 포인트
        - **장소 적합성**: {target_place} 장소에서의 이미지와 분위기
        - **신체 정보 활용**: {gender}, {user_data["age"]}세, 키 {user_data["height"]}cm, 체중 {user_data["weight"]}kg에 맞는 스타일링
        - **피부톤 고려**: {skin_tone} 피부톤에 어울리는 색상과 스타일
        - **실용성**: 편안함, 활동성, 관리의 용이성 등
        - **스타일링 효과**: 전체적인 이미지와 분위기 연출
    """
    
    prompt = f"""
    상황: {situation}
    성별: {gender}
    나이: {user_data["age"]}세
    키: {user_data["height"]}cm
    체중: {user_data["weight"]}kg
    피부톤: {skin_tone}
    시간: {target_time}
    장소: {target_place}
    기온: {high_temp}°C ~ {low_temp}°C (평균 {avg_temp:.1f}°C)
    강수확률: {rain_percent}%
    날씨상태: {status}
    
    **계절별 옷 추천 가이드:**
    {season_info["guide"]}

    아래는 추천받은 3개의 옷 조합입니다:
    {recommended_combinations}

    그리고 아래는 옷장에 있는 옷들입니다:
    {clothing_list_str}

    {closet_rule}

    응답은 반드시 아래 형식으로만 작성해주세요. 추가 설명이나 결론은 작성하지 마세요:

    요약: 20XX년 X월 X일에 [장소]에서 [상황]을 위한 스타일링

    조합 1: TOP: [옷종류], BOTTOM: [옷종류]
    선택한 옷: [옷ID] ([옷종류]) + [옷ID] ([옷종류])
    이유: [상세하고 구체적인 이유 - 위 가이드에 따라 작성]

    조합 2: TOP: [옷종류], BOTTOM: [옷종류]
    선택한 옷: [옷ID] ([옷종류]) + [옷ID] ([옷종류])
    이유: [상세하고 구체적인 이유 - 위 가이드에 따라 작성]

    조합 3: TOP: [옷종류], BOTTOM: [옷종류]
    선택한 옷: [옷ID] ([옷종류]) + [옷ID] ([옷종류])
    이유: [상세하고 구체적인 이유 - 위 가이드에 따라 작성]
    """

    messages = [
        SystemMessage(content="당신은 패션 코디 전문가입니다."),
        HumanMessage(content=prompt)
    ]
    
    response = llm.invoke(messages).content
    return response

def parse_gpt_result(text: str):
    """GPT 응답 파싱 함수"""
    result = []
    
    # 요약 추출
    summary_match = re.search(r"요약: (.+?)(?=\n\n|$)", text)
    summary = summary_match.group(1) if summary_match else ""
    
    # 조합 추출
    pattern = re.compile(r"조합 \d+: .+?\n선택한 옷: .+?\n이유: .+?(?=(?:\n조합 \d+:|$))", re.DOTALL)
    matches = pattern.findall(text)

    for i, match in enumerate(matches):
        lines = match.strip().split("\n")
        if len(lines) >= 3:
            combination = lines[0].strip()
            selected = lines[1].strip().replace("선택한 옷: ", "")
            reason = lines[2].strip().replace("이유: ", "")
            
            # 조합 정보를 한국어로 변환
            korean_combination = convert_combination_to_korean(combination)
            
            result.append({
                "combination": korean_combination,
                "selected": selected,
                "reason": reason
            })
    
    return {"summary": summary, "outfits": result}

def convert_combination_to_korean(combination: str) -> str:
    """조합 정보를 한국어로 변환"""
    if "TOP:" in combination and "BOTTOM:" in combination:
        # TOP + BOTTOM 조합
        top_match = re.search(r"TOP: (\w+)", combination)
        bottom_match = re.search(r"BOTTOM: (\w+)", combination)
        
        if top_match and bottom_match:
            top_category = top_match.group(1)
            bottom_category = bottom_match.group(1)
            
            top_korean = CATEGORY_KOREAN_MAP.get(top_category, top_category)
            bottom_korean = CATEGORY_KOREAN_MAP.get(bottom_category, bottom_category)
            
            result = f"상의: {top_korean}, 하의: {bottom_korean}"
            return result
            
    elif "ONEPIECE:" in combination:
        # ONEPIECE 조합
        onepiece_match = re.search(r"ONEPIECE: (\w+)", combination)
        if onepiece_match:
            onepiece_category = onepiece_match.group(1)
            onepiece_korean = CATEGORY_KOREAN_MAP.get(onepiece_category, onepiece_category)
            
            result = f"원피스: {onepiece_korean}"
            return result
    
    # 변환할 수 없는 경우 원본 반환
    return combination

def get_clothing_links(selected_clothing, clothing_data, virtual_clothing_urls=None):
    """옷 ID에서 링크 정보를 찾는 함수"""
    links = []
    
    # 상의 + 하의 조합인 경우 (혼합 조합 처리)
    if " + " in selected_clothing:
        top_part, bottom_part = selected_clothing.split(" + ")
        
        # 상의 처리
        if top_part.startswith("추천:"):
            # 상의는 가상 옷
            if virtual_clothing_urls:
                top_type = re.sub(r'\s*\([^)]+\)', '', top_part).replace("추천: ", "").strip()
                for virtual_item in virtual_clothing_urls:
                    if virtual_item["type"] == top_type:
                        link_info = {
                            "id": None,  # 가상 옷이므로 ID 없음
                            "category": top_type,
                            "image_url": virtual_item["url"]
                        }
                        links.append(link_info)
                        break
        else:
            # 상의는 옷장 옷
            top_id = top_part.split(" ")[0]
            for item in clothing_data:
                if item['clothing_id'] == top_id:
                    link_info = {
                        "id": top_id,
                        "category": item['attributes']['category'],
                        "image_url": item['attributes']['image_url']
                    }
                    links.append(link_info)
                    break
        
        # 하의 처리
        if bottom_part.startswith("추천:"):
            # 하의는 가상 옷
            if virtual_clothing_urls:
                bottom_type = re.sub(r'\s*\([^)]+\)', '', bottom_part).replace("추천: ", "").strip()
                for virtual_item in virtual_clothing_urls:
                    if virtual_item["type"] == bottom_type:
                        link_info = {
                            "id": None,  # 가상 옷이므로 ID 없음
                            "category": bottom_type,
                            "image_url": virtual_item["url"]
                        }
                        links.append(link_info)
                        break
        else:
            # 하의는 옷장 옷
            bottom_id = bottom_part.split(" ")[0]
            for item in clothing_data:
                if item['clothing_id'] == bottom_id:
                    link_info = {
                        "id": bottom_id,
                        "category": item['attributes']['category'],
                        "image_url": item['attributes']['image_url']
                    }
                    links.append(link_info)
                    break
        
        return links
    
    # 단일 옷인 경우 (원피스 또는 단일 가상 옷)
    if selected_clothing.startswith("추천:"):
        # 가상 옷인 경우
        if virtual_clothing_urls:
            clothing_type = re.sub(r'\s*\([^)]+\)', '', selected_clothing).replace("추천: ", "").strip()
            for virtual_item in virtual_clothing_urls:
                if virtual_item["type"] == clothing_type:
                    link_info = {
                        "id": None,  # 가상 옷이므로 ID 없음
                        "category": clothing_type,
                        "image_url": virtual_item["url"]
                    }
                    links.append(link_info)
                    break
        return links
    
    # 원피스인 경우 (옷장 옷)
    clothing_id = selected_clothing.split(" ")[0]
    for item in clothing_data:
        if item['clothing_id'] == clothing_id:
            link_info = {
                "id": clothing_id,
                "category": item['attributes']['category'],
                "image_url": item['attributes']['image_url']
            }
            links.append(link_info)
            break
    
    return links

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
    """이미지를 Base64로 인코딩"""
    try:
        with open(image_path, "rb") as image_file:
            binary_data = image_file.read()
            encoded = base64.b64encode(binary_data)
            return encoded.decode('utf-8')
    except Exception as e:
        print(f"[ERROR] Base64 인코딩 실패: {e}")
        raise

def resize_image_for_fashn(image_path, max_size=640):
    """FASHN API용으로 이미지 크기 조정"""
    try:
        with Image.open(image_path) as img:
            # 이미지가 RGB 모드가 아니면 변환
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 원본 크기
            width, height = img.size
            
            # 비율 유지하면서 크기 조정
            if width > height:
                new_width = max_size
                new_height = int(height * (max_size / width))
            else:
                new_height = max_size
                new_width = int(width * (max_size / height))
            
            # 이미지 리사이즈
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # 임시 파일로 저장
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                resized_img.save(tmp_file.name, 'JPEG', quality=85, optimize=True)
                return tmp_file.name
                
    except Exception as e:
        print(f"[ERROR] 이미지 리사이즈 실패: {e}")
        return image_path  # 실패시 원본 반환

def save_image_to_s3(image_url: str, user_id: str, folder: str = RESULT_FOLDER) -> tuple:
    """이미지를 S3에 저장"""
    try:
        response = requests.get(image_url)
        if response.status_code != 200:
            return None, "이미지 다운로드 실패"

        timestamp = int(time.time())
        file_name = f"{folder}{user_id}_{timestamp}_{uuid.uuid4()}.jpg"

        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=file_name,
            Body=response.content,
            ContentType='image/jpeg'
        )

        s3_url = f"https://{BUCKET_NAME}.s3.ap-northeast-2.amazonaws.com/{file_name}"
        return s3_url, None

    except Exception as e:
        return None, f"S3 저장 중 오류 발생: {str(e)}"

async def process_virtual_tryon_async(model_image_path, garment_image_path, category, user_id):
    """가상 피팅 처리"""
    try:
        print(f"[INFO] FASHN API 가상 피팅 시작 - 카테고리: {category}")
        
        # 이미지 리사이즈 (FASHN API 제한에 맞춤)
        resized_model_path = resize_image_for_fashn(model_image_path)
        resized_garment_path = resize_image_for_fashn(garment_image_path)
        
        model_image_base64 = encode_image_to_base64(resized_model_path)
        garment_image_base64 = encode_image_to_base64(resized_garment_path)

        # 카테고리 매핑
        category_mapping = {"tops": "tops", "bottoms": "bottoms", "one-pieces": "one-pieces"}
        mapped_category = category_mapping.get(category, "auto")

        # API 요청 데이터 준비
        input_data = {
            "model_image": f"data:image/jpeg;base64,{model_image_base64}",
            "garment_image": f"data:image/jpeg;base64,{garment_image_base64}",
            "category": mapped_category,
            "mode": "quality",
            "garment_photo_type": "auto",
            "num_samples": 1
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }

        async with aiohttp.ClientSession() as session:
            # 1. /run 엔드포인트로 요청
            async with session.post(f"{BASE_URL}/run", json=input_data, headers=headers) as run_response:
                if run_response.status != 200:
                    error_text = await run_response.text()
                    return None, f"API 호출 실패: {run_response.status}, message='{error_text}', url='{run_response.url}'"
                
                run_data = await run_response.json()
                prediction_id = run_data.get("id")
                if not prediction_id:
                    return None, "예측 ID를 받지 못했습니다"
                
                # 2. 상태 확인 및 결과 대기
                while True:
                    async with session.get(f"{BASE_URL}/status/{prediction_id}", headers=headers) as status_response:
                        if status_response.status != 200:
                            error_text = await status_response.text()
                            return None, f"상태 확인 실패: {error_text}"
                        
                        status_data = await status_response.json()

                        if status_data["status"] == "completed":
                            result_url = status_data["output"][0] if isinstance(status_data["output"], list) else status_data["output"]
                            
                            # S3에 이미지 저장
                            s3_url, error = save_image_to_s3(result_url, user_id)
                            if error:
                                return None, error
                                
                            print(f"[INFO] FASHN API 가상 피팅 완료 - 카테고리: {category}")
                            return s3_url, None

                        elif status_data["status"] in ["starting", "in_queue", "processing"]:
                            await asyncio.sleep(3)
                        else:
                            return None, f"예측 실패: {status_data.get('error')}"

        # 임시 리사이즈된 이미지 파일들 삭제
        if resized_model_path != model_image_path:
            try:
                os.unlink(resized_model_path)
            except:
                pass
        if resized_garment_path != garment_image_path:
            try:
                os.unlink(resized_garment_path)
            except:
                pass

    except Exception as e:
        return None, f"예상치 못한 에러가 발생했습니다: {e}"

# OpenAI 설정 추가
openai.api_key = os.getenv("OPENAI_API_KEY")

async def generate_virtual_clothing_with_dalle(clothing_type, description, user_id):
    """DALL-E로 가상 옷 생성 (비동기)"""
    try:
        print(f"[INFO] DALL-E 가상 옷 생성 시작 - {clothing_type}")
        
        # 패턴과 톤 정보 추출
        pattern = "PLAIN"  # 기본값
        tone = "LIGHT"     # 기본값
        
        # "추천: TSHIRT (STRIPE, DARK)" 형식에서 패턴과 톤 추출
        pattern_match = re.search(r'\(([^,]+),\s*([^)]+)\)', clothing_type)
        if pattern_match:
            pattern = pattern_match.group(1).strip()
            tone = pattern_match.group(2).strip()
            # 순수 옷 종류만 추출
            clothing_type = re.sub(r'\s*\([^)]+\)', '', clothing_type).replace("추천: ", "").strip()
        
        # 패턴별 프롬프트 매핑
        pattern_prompts = {
            "PLAIN": "solid color, minimal design",
            "STRIPE": "striped pattern, clean lines",
            "CHECK": "checkered pattern, classic design",
            "DOT": "polka dot pattern, playful design",
            "ANIMAL": "animal print pattern, bold design",
            "ARTIFACT": "geometric artifact pattern, artistic design",
            "ETC": "unique pattern, distinctive design",
            "NATURE": "nature-inspired pattern, organic design",
            "GEOMETRIC": "geometric pattern, modern design",
            "PLANT": "floral pattern, botanical design",
            "SYMBOL": "symbolic pattern, meaningful design"
        }
        
        # 톤별 색상 매핑
        tone_colors = {
            "LIGHT": "light colors, pastel tones, soft hues",
            "DARK": "dark colors, deep tones, rich hues",
            "NOT_CONSIDERED": "neutral colors, balanced tones"
        }
        
        # 옷 종류별 프롬프트 생성
        clothing_prompts = {
            "BLOUSE": "elegant blouse, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "SHIRT": "classic shirt, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "TSHIRT": "stylish t-shirt, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "SWEATER": "comfortable sweater, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "CARDIGAN": "elegant cardigan, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "JACKET": "stylish jacket, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "COAT": "elegant coat, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "JEANS": "classic jeans, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic denim texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "PANTS": "elegant pants, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "SKIRT": "stylish skirt, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "DRESS": "elegant dress, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment",
            "JUMPSUIT": "stylish jumpsuit, top view, perfectly straight, laid flat, fully spread out, no folds, no wrinkles, no creases, centered, on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment"
        }
        
        base_prompt = clothing_prompts.get(clothing_type, f"{clothing_type.lower()} laid flat on pure white background, professional product photography, high quality, realistic fabric texture, photorealistic, not illustration, not drawing, real clothing, no person, just the garment")
        pattern_prompt = pattern_prompts.get(pattern, "solid color, minimal design")
        tone_prompt = tone_colors.get(tone, "neutral colors, balanced tones")
        
        # 상세 설명 추가
        full_prompt = f"{base_prompt}, {pattern_prompt}, {tone_prompt}, {description}"
        
        # OpenAI 1.0.0+ API 형식으로 수정
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = await client.images.generate(
            model="dall-e-3",
            prompt=full_prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        
        generated_image_url = response.data[0].url
        print(f"[INFO] DALL-E 가상 옷 생성 완료 - {clothing_type} ({pattern}, {tone})")
        
        # 생성된 이미지를 S3에 저장
        s3_url, error = save_image_to_s3(generated_image_url, f"{user_id}_virtual_{clothing_type}", "New_clothes_gpt/")
        if error:
            return None, f"가상 옷 이미지 저장 실패: {error}"
            
        return s3_url, None
        
    except Exception as e:
        return None, f"DALL-E 가상 옷 생성 실패: {e}"

async def generate_virtual_clothing_batch(clothing_items, user_data, situation):
    """여러 가상 옷을 동시에 생성"""
    tasks = []
    for item in clothing_items:
        if item.startswith("추천:"):
            clothing_type = re.sub(r'\s*\([^)]+\)', '', item).replace("추천: ", "").strip()
            description = f"elegant {clothing_type.lower()}, suitable for {situation} occasion"
            task = generate_virtual_clothing_with_dalle(item, description, user_data["id"])
            tasks.append((item, task))
    
    if not tasks:
        return {}
    
    print(f"[INFO] {len(tasks)}개의 가상 옷 생성 시작")
    results = {}
    
    # 모든 가상 옷 생성을 동시에 실행
    task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
    
    for i, (original_item, _) in enumerate(tasks):
        result = task_results[i]
        if isinstance(result, Exception):
            print(f"[ERROR] 가상 옷 생성 실패: {result}")
            results[original_item] = None
        else:
            url, error = result
            if error:
                print(f"[ERROR] 가상 옷 생성 실패: {error}")
                results[original_item] = None
            else:
                clothing_type = re.sub(r'\s*\([^)]+\)', '', original_item).replace("추천: ", "").strip()
                results[original_item] = {"type": clothing_type, "url": url}
    
    print(f"[INFO] 가상 옷 생성 완료 - {len([r for r in results.values() if r is not None])}개 성공")
    return results

async def apply_virtual_tryon_with_generated_clothing(user_data, outfit_combination, show_closet_only, virtual_clothing_results=None):
    """가상 옷 생성과 가상 피팅 적용 (개선된 비동기 버전)"""
    try:
        print(f"[INFO] 가상 옷 생성 및 피팅 시작 - 조합: {outfit_combination['combination']}")
        
        # 사용자 이미지 URL 확인 및 기본 모델 이미지 설정
        model_image_url = user_data["body_image_url"]
        if not model_image_url:
            if user_data["gender"] == "FEMALE":
                model_image_url = "https://amzn-s3-fitu-bucket.s3.ap-northeast-2.amazonaws.com/basic_model/ChatGPT_image_woman.png"
            else:
                model_image_url = "https://amzn-s3-fitu-bucket.s3.ap-northeast-2.amazonaws.com/basic_model/ChatGPT_Image_man.png"

        # 모델 이미지 다운로드
        async with aiohttp.ClientSession() as session:
            async with session.get(model_image_url) as response:
                if response.status != 200:
                    return None, "모델 이미지를 다운로드할 수 없습니다."
                body_image_content = await response.read()

        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
            tmp_file.write(body_image_content)
            model_image_path = tmp_file.name

        # 옷 조합 분석
        combination = outfit_combination["combination"]
        selected = outfit_combination["selected"]

        # 옷장에 없는 옷을 추천한 경우 (showClosetOnly가 false일 때만)
        if selected.startswith("추천:") or (" + " in selected and any(part.startswith("추천:") for part in selected.split(" + "))):
            if not show_closet_only:
                # 상의 + 하의 조합인 경우
                if " + " in selected:
                    top_part, bottom_part = selected.split(" + ")
                    virtual_clothing = []  # 가상 옷 URL 수집
                    
                    # 상의 처리
                    if top_part.startswith("추천:"):
                        # 상의는 가상 옷 (이미 생성된 결과 사용)
                        if virtual_clothing_results and top_part in virtual_clothing_results and virtual_clothing_results[top_part]:
                            top_url = virtual_clothing_results[top_part]["url"]
                            virtual_clothing.append(virtual_clothing_results[top_part])
                            top_is_virtual = True
                        else:
                            os.unlink(model_image_path)
                            return None, f"상의 가상 옷 생성에 실패했습니다: {top_part}"
                    else:
                        # 상의는 옷장 옷
                        top_id = top_part.split(" ")[0]
                        session = get_session()
                        query = text("SELECT image_url FROM clothes WHERE id = :id AND user_id = :user_id")
                        result = session.execute(query, {"id": int(top_id), "user_id": user_data["id"]}).fetchone()
                        session.close()
                        
                        if not result or not result[0]:
                            os.unlink(model_image_path)
                            return None, f"상의 이미지를 찾을 수 없습니다. (ID: {top_id})"
                        
                        top_url = result[0]
                        top_is_virtual = False
                    
                    # 하의 처리
                    if bottom_part.startswith("추천:"):
                        # 하의는 가상 옷 (이미 생성된 결과 사용)
                        if virtual_clothing_results and bottom_part in virtual_clothing_results and virtual_clothing_results[bottom_part]:
                            bottom_url = virtual_clothing_results[bottom_part]["url"]
                            virtual_clothing.append(virtual_clothing_results[bottom_part])
                            bottom_is_virtual = True
                        else:
                            os.unlink(model_image_path)
                            return None, f"하의 가상 옷 생성에 실패했습니다: {bottom_part}"
                    else:
                        # 하의는 옷장 옷
                        bottom_id = bottom_part.split(" ")[0]
                        session = get_session()
                        query = text("SELECT image_url FROM clothes WHERE id = :id AND user_id = :user_id")
                        result = session.execute(query, {"id": int(bottom_id), "user_id": user_data["id"]}).fetchone()
                        session.close()
                        
                        if not result or not result[0]:
                            os.unlink(model_image_path)
                            return None, f"하의 이미지를 찾을 수 없습니다. (ID: {bottom_id})"
                        
                        bottom_url = result[0]
                        bottom_is_virtual = False
                    
                    # 하의 먼저 적용
                    async with aiohttp.ClientSession() as session:
                        async with session.get(bottom_url) as response:
                            if response.status != 200:
                                return None, "하의 이미지를 다운로드할 수 없습니다."
                            bottom_content = await response.read()

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(bottom_content)
                        bottom_image_path = tmp_file.name

                    intermediate_url, error = await process_virtual_tryon_async(model_image_path, bottom_image_path, "bottoms", user_data["id"])
                    if error:
                        os.unlink(bottom_image_path)
                        os.unlink(model_image_path)
                        return None, error

                    # 중간 결과 이미지 다운로드
                    async with aiohttp.ClientSession() as session:
                        async with session.get(intermediate_url) as response:
                            if response.status != 200:
                                return None, "중간 결과 이미지를 다운로드할 수 없습니다."
                            intermediate_content = await response.read()

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(intermediate_content)
                        intermediate_image_path = tmp_file.name

                    # 상의 이미지 다운로드
                    async with aiohttp.ClientSession() as session:
                        async with session.get(top_url) as response:
                            if response.status != 200:
                                return None, "상의 이미지를 다운로드할 수 없습니다."
                            top_content = await response.read()

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(top_content)
                        top_image_path = tmp_file.name

                    final_url, error = await process_virtual_tryon_async(intermediate_image_path, top_image_path, "tops", user_data["id"])

                    # 임시 파일 삭제
                    os.unlink(bottom_image_path)
                    os.unlink(intermediate_image_path)
                    os.unlink(top_image_path)
                    os.unlink(model_image_path)

                    print(f"[INFO] 가상 옷 생성 및 피팅 완료 - 혼합 조합")
                    # 가상 옷 URL과 가상 피팅 결과 URL을 함께 반환
                    return {
                        "tryon_url": final_url,
                        "error": error,
                        "virtual_clothing": virtual_clothing
                    }
                    
                else:
                    # 단일 가상 옷인 경우 (원피스)
                    if virtual_clothing_results and selected in virtual_clothing_results and virtual_clothing_results[selected]:
                        virtual_clothing_url = virtual_clothing_results[selected]["url"]
                        clothing_type = virtual_clothing_results[selected]["type"]
                    else:
                        os.unlink(model_image_path)
                        return None, f"가상 옷 생성에 실패했습니다: {selected}"
                    
                    # 가상 옷 이미지 다운로드
                    async with aiohttp.ClientSession() as session:
                        async with session.get(virtual_clothing_url) as response:
                            if response.status != 200:
                                return None, "가상 옷 이미지를 다운로드할 수 없습니다."
                            clothing_content = await response.read()

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                        tmp_file.write(clothing_content)
                        clothing_image_path = tmp_file.name

                    # 가상 피팅 실행
                    if "DRESS" in clothing_type or "JUMPSUIT" in clothing_type:
                        result_url, error = await process_virtual_tryon_async(model_image_path, clothing_image_path, "one-pieces", user_data["id"])
                    else:
                        result_url, error = await process_virtual_tryon_async(model_image_path, clothing_image_path, "tops", user_data["id"])

                    # 임시 파일 삭제
                    os.unlink(clothing_image_path)
                    os.unlink(model_image_path)

                    print(f"[INFO] 가상 옷 생성 및 피팅 완료 - {clothing_type}")
                    # 가상 옷 URL과 가상 피팅 결과 URL을 함께 반환
                    return {
                        "tryon_url": result_url,
                        "error": error,
                        "virtual_clothing": [
                            {"type": clothing_type, "url": virtual_clothing_url}
                        ]
                    }
            else:
                return None, "옷장에 없는 옷은 가상 피팅을 할 수 없습니다."

        # [N/A] 값인 경우
        if selected == "[N/A]":
            return None, "해당 조합에 맞는 옷이 없습니다."

        # 원피스 판별
        is_onepiece = False
        if "DRESS" in combination or "JUMPSUIT" in combination:
            is_onepiece = True
        elif "ONEPIECE" in combination:
            is_onepiece = True
        elif " + " not in selected and ("DRESS" in selected or "JUMPSUIT" in selected):
            is_onepiece = True

        if is_onepiece:
            # 원피스인 경우
            clothing_id = selected.split(" ")[0]
            
            # DB에서 해당 옷의 image_url 가져오기
            session = get_session()
            query = text("""
                SELECT image_url 
                FROM clothes 
                WHERE id = :id AND user_id = :user_id
            """)
            result = session.execute(query, {
                "id": int(clothing_id),
                "user_id": user_data["id"]
            }).fetchone()
            session.close()
            
            if not result or not result[0]:
                return None, f"의류 이미지를 찾을 수 없습니다. (ID: {clothing_id})"
                
            garment_url = result[0]
            
            async with aiohttp.ClientSession() as session:
                async with session.get(garment_url) as response:
                    if response.status != 200:
                        return None, f"의류 이미지를 다운로드할 수 없습니다."

                    garment_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(garment_content)
                garment_image_path = tmp_file.name

            result_url, error = await process_virtual_tryon_async(model_image_path, garment_image_path, "one-pieces", user_data["id"])
            
            # 임시 파일 삭제
            os.unlink(garment_image_path)
            os.unlink(model_image_path)
            
            print(f"[INFO] 가상 피팅 조합 처리 완료 - 원피스")
            return result_url, error

        else:
            # 상의 + 하의 조합인 경우
            if " + " not in selected:
                return None, "상의+하의 조합 형식이 올바르지 않습니다."
                
            top_part, bottom_part = selected.split(" + ")
            top_id = top_part.split(" ")[0]
            bottom_id = bottom_part.split(" ")[0]

            # DB에서 해당 옷들의 image_url 가져오기
            session = get_session()
            query = text("SELECT id, image_url FROM clothes WHERE id IN (:top_id, :bottom_id) AND user_id = :user_id")
            result = session.execute(query, {
                "top_id": int(top_id),
                "bottom_id": int(bottom_id),
                "user_id": user_data["id"]
            }).fetchall()
            session.close()
            
            if len(result) != 2:
                return None, f"의류 이미지를 찾을 수 없습니다."

            result_dict = {row[0]: row[1] for row in result}
            top_url = result_dict.get(int(top_id))
            bottom_url = result_dict.get(int(bottom_id))

            if not top_url or not bottom_url:
                return None, f"의류 이미지를 찾을 수 없습니다."

            # 하의 먼저 적용
            async with aiohttp.ClientSession() as session:
                async with session.get(bottom_url) as response:
                    if response.status != 200:
                        return None, f"하의 이미지를 다운로드할 수 없습니다."
                    bottom_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(bottom_content)
                bottom_image_path = tmp_file.name

            intermediate_url, error = await process_virtual_tryon_async(model_image_path, bottom_image_path, "bottoms", user_data["id"])
            if error:
                os.unlink(bottom_image_path)
                os.unlink(model_image_path)
                return None, error

            # 중간 결과 이미지 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(intermediate_url) as response:
                    if response.status != 200:
                        return None, f"중간 결과 이미지를 다운로드할 수 없습니다."
                    intermediate_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(intermediate_content)
                intermediate_image_path = tmp_file.name

            # 상의 이미지 다운로드
            async with aiohttp.ClientSession() as session:
                async with session.get(top_url) as response:
                    if response.status != 200:
                        return None, f"상의 이미지를 다운로드할 수 없습니다."
                    top_content = await response.read()

            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                tmp_file.write(top_content)
                top_image_path = tmp_file.name

            final_url, error = await process_virtual_tryon_async(intermediate_image_path, top_image_path, "tops", user_data["id"])

            # 임시 파일 삭제
            os.unlink(bottom_image_path)
            os.unlink(intermediate_image_path)
            os.unlink(top_image_path)
            os.unlink(model_image_path)

            print(f"[INFO] 가상 피팅 조합 처리 완료 - 상의+하의")
            return final_url, error

    except Exception as e:
        return None, f"가상 피팅 처리 중 오류 발생: {e}"

def match_outfit_combinations(data, recommended_combinations, user_data, available_types):
    """옷장에서 조합 매칭"""
    outfit_sets = []
    for line in recommended_combinations.splitlines():
        if 'onepiece' in line.lower() and user_data["gender"] == "FEMALE":
            for op in available_types['ONEPIECE']:
                if op in line.upper():
                    matches = [item for item in data if item['attributes']['type'] == 'ONEPIECE' and item['attributes']['category'] == op]
                    for match in matches:
                        outfit_sets.append(f"{match['clothing_id']} ({match['attributes']['category']})")
                        
        elif 'top' in line.lower() and 'bottom' in line.lower():
            top_type = None
            bottom_type = None
            
            for top in available_types['TOP']:
                if top in line.upper():
                    top_type = top
                    break
                    
            for bottom in available_types['BOTTOM']:
                if bottom in line.upper():
                    bottom_type = bottom
                    break
            
            if top_type and bottom_type:
                top_matches = [item for item in data if item['attributes']['type'] == 'TOP' and item['attributes']['category'] == top_type]
                bottom_matches = [item for item in data if item['attributes']['type'] == 'BOTTOM' and item['attributes']['category'] == bottom_type]
                
                if top_matches and bottom_matches:
                    for t in top_matches:
                        for b in bottom_matches:
                            combination = f"{t['clothing_id']} ({t['attributes']['category']}) + {b['clothing_id']} ({b['attributes']['category']})"
                            outfit_sets.append(combination)
    
    return outfit_sets

def organize_clothing_by_category(data):
    """옷장의 옷들을 카테고리별로 분류"""
    organized_clothes = {
        'TOP': {},
        'BOTTOM': {},
        'ONEPIECE': {}
    }
    
    for item in data:
        clothing_type = item['attributes']['type']
        category = item['attributes']['category']
        clothing_id = item['clothing_id']
        
        if clothing_type not in organized_clothes:
            continue
            
        if category not in organized_clothes[clothing_type]:
            organized_clothes[clothing_type][category] = []
            
        organized_clothes[clothing_type][category].append({
            'id': clothing_id,
            'category': category,
            'pattern': item['attributes']['pattern'],
            'tone': item['attributes']['tone']
        })
    
    return organized_clothes

def filter_clothing_by_recommendations(organized_clothes, recommended_combinations):
    """추천받은 조합에 맞는 카테고리만 필터링"""
    needed_categories = set()
    
    for line in recommended_combinations.splitlines():
        line = line.strip()
        if not line or not line.startswith('조합'):
            continue
            
        # TOP + BOTTOM 조합 추출
        if 'TOP:' in line and 'BOTTOM:' in line:
            top_match = re.search(r'TOP:\s*(\w+)', line)
            bottom_match = re.search(r'BOTTOM:\s*(\w+)', line)
            
            if top_match:
                needed_categories.add(top_match.group(1))
            if bottom_match:
                needed_categories.add(bottom_match.group(1))
                
        # ONEPIECE 조합 추출
        elif 'ONEPIECE:' in line:
            onepiece_match = re.search(r'ONEPIECE:\s*(\w+)', line)
            if onepiece_match:
                needed_categories.add(onepiece_match.group(1))
    
    # 필요한 카테고리만 필터링
    filtered_clothes = {
        'TOP': {},
        'BOTTOM': {},
        'ONEPIECE': {}
    }
    
    for clothing_type, categories in organized_clothes.items():
        for category, items in categories.items():
            if category in needed_categories:
                filtered_clothes[clothing_type][category] = items
    
    return filtered_clothes

# 메인 API 엔드포인트
@app.post("/vision/recommendation")
async def recommend(request: RecommendationRequest):
    print(f"[INFO] 추천 API 호출 시작 - user_id: {request.user_id}")
    
    user_data = load_user_data(request.user_id)
    
    if not user_data:
        return {
            "header": {"resultCode": "01", "resultMsg": "USER_NOT_FOUND"},
            "body": {"result": []}
        }
    
    # 옷장에 있는 옷 종류만 추출
    data = load_clothing_types_from_db(request.user_id)
    
    available_types = {'TOP': set(), 'BOTTOM': set(), 'ONEPIECE': set()}
    
    for item in data:
        type_name = item['type']
        category = item['category']
        available_types[type_name].add(category)
    
    if request.showClosetOnly:
        # 프롬프트용 문자열 생성
        available_types_str = ""
        for category, types in available_types.items():
            if types:
                available_types_str += f"- {category}: {', '.join(sorted(types))}\n"
        
        if not available_types_str:
            return {
                "header": {"resultCode": "01", "resultMsg": "NO_CLOTHES"},
                "body": {"result": []}
            }
            
        print("[INFO] GPT 옷장 기반 추천 시작")
        recommended_combinations = ask_gpt_for_recommendation(
            request.situation, user_data, available_types_str, request.targetTime,
            request.targetPlace, request.highTemperature, request.lowTemperature,
            request.rainPercent, request.status, True
        )
        print("[INFO] GPT 옷장 기반 추천 완료")
    else:
        print("[INFO] GPT 일반 추천 시작")
        recommended_combinations = ask_gpt_for_recommendation(
            request.situation, user_data, "", request.targetTime,
            request.targetPlace, request.highTemperature, request.lowTemperature,
            request.rainPercent, request.status, False
        )
        print("[INFO] GPT 일반 추천 완료")

    # 옷장에서 조합 매칭
    data = load_clothing_details_from_db(request.user_id)
    organized_clothes = organize_clothing_by_category(data)
    
    # 추천받은 조합에 맞는 카테고리만 필터링
    filtered_clothes = filter_clothing_by_recommendations(organized_clothes, recommended_combinations)
    
    if not any(filtered_clothes.values()) and request.showClosetOnly:
        return {
            "header": {"resultCode": "01", "resultMsg": "NO_MATCH"},
            "body": {"result": []}
        }

    print("[INFO] GPT 최종 옷장 매칭 시작")
    final_response = ask_gpt_for_best_clothing_sets(
        request.situation, filtered_clothes, recommended_combinations, request.showClosetOnly,
        user_data, request.targetTime, request.targetPlace, request.highTemperature,
        request.lowTemperature, request.rainPercent, request.status
    )
    print("[INFO] GPT 최종 옷장 매칭 완료")
    
    structured_result = parse_gpt_result(final_response)
    
    # 가상 옷이 필요한 조합들 수집
    virtual_clothing_items = []
    for outfit in structured_result["outfits"]:
        if outfit["selected"] != "해당 조합에 맞는 옷이 없습니다" and outfit["selected"] != "[N/A]":
            if not request.showClosetOnly:
                # 상의 + 하의 조합인 경우
                if " + " in outfit["selected"]:
                    top_part, bottom_part = outfit["selected"].split(" + ")
                    if top_part.startswith("추천:"):
                        virtual_clothing_items.append(top_part)
                    if bottom_part.startswith("추천:"):
                        virtual_clothing_items.append(bottom_part)
                else:
                    # 단일 가상 옷인 경우
                    if outfit["selected"].startswith("추천:"):
                        virtual_clothing_items.append(outfit["selected"])
    
    # 중복 제거
    virtual_clothing_items = list(set(virtual_clothing_items))
    
    # 1단계: 가상 옷 생성 (비동기)
    virtual_clothing_results = {}
    if virtual_clothing_items and not request.showClosetOnly:
        print(f"[INFO] 가상 옷 생성 시작 - {len(virtual_clothing_items)}개")
        virtual_clothing_results = await generate_virtual_clothing_batch(virtual_clothing_items, user_data, request.situation)
        print("[INFO] 가상 옷 생성 완료")
    
    # 2단계: 가상 피팅 (비동기)
    tasks = []
    for i, outfit in enumerate(structured_result["outfits"]):
        if outfit["selected"] != "해당 조합에 맞는 옷이 없습니다" and outfit["selected"] != "[N/A]":
            tasks.append(apply_virtual_tryon_with_generated_clothing(user_data, outfit, request.showClosetOnly, virtual_clothing_results))
        else:
            outfit["virtualTryonImage"] = None
            outfit["virtualTryonError"] = "해당 조합에 맞는 옷이 없습니다."

    # 모든 가상 피팅 작업을 동시에 실행
    if tasks:
        print(f"[INFO] 가상 피팅 시작 - {len(tasks)}개 조합")
        results = await asyncio.gather(*tasks)
        print("[INFO] 가상 피팅 완료")
    else:
        results = []

    # 결과를 각 outfit에 할당
    task_index = 0
    virtual_clothing_urls = []  # 가상 옷 URL 수집
    
    for i, outfit in enumerate(structured_result["outfits"]):
        if outfit.get("virtualTryonImage") is None and outfit.get("virtualTryonError") is None:
            if task_index < len(results):
                tryon_result = results[task_index]
                
                # 가상 옷인 경우와 일반 옷인 경우를 구분하여 처리
                if isinstance(tryon_result, dict) and "virtual_clothing" in tryon_result:
                    # 가상 옷 생성된 경우
                    if tryon_result["error"]:
                        outfit["virtualTryonImage"] = None
                        outfit["virtualTryonError"] = tryon_result["error"]
                    else:
                        outfit["virtualTryonImage"] = tryon_result["tryon_url"]
                        outfit["virtualTryonError"] = None
                        # 가상 옷 URL 수집
                        virtual_clothing_urls.extend(tryon_result["virtual_clothing"])
                else:
                    # 일반 옷장 옷인 경우 (기존 방식)
                    tryon_url, error = tryon_result
                    if error:
                        outfit["virtualTryonImage"] = None
                        outfit["virtualTryonError"] = error
                    else:
                        outfit["virtualTryonImage"] = tryon_url
                        outfit["virtualTryonError"] = None
                
                task_index += 1
        
        # 옷의 링크 정보 추가
        outfit["clothing_links"] = get_clothing_links(outfit["selected"], data, virtual_clothing_urls)

    print(f"[INFO] 추천 API 호출 완료 - {len(structured_result['outfits'])}개 조합 생성")
    return {
        "header": {"resultCode": "00", "resultMsg": "SUCCESS"},
        "body": {
            "summary": structured_result["summary"],
            "weather": f"{request.status}, {int((request.highTemperature + request.lowTemperature) / 2)}°C, 강수확률: {request.rainPercent}%",
            "result": structured_result["outfits"]
        }
    }