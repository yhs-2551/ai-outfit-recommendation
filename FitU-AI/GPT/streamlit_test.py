import streamlit as st
import json
import os
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 로드 (상위 디렉토리의 .env 파일 사용)
env_path = Path(__file__).parents[1] / '.env'
load_dotenv(dotenv_path=env_path)
api_key = os.getenv("OPENAI_API_KEY")

DATA_PATH = "GPT/closet_100.json"

CLOTHING_TYPES = [
    'blouse', 'activewear', 'jeans', 'pants', 'shorts', 'skirt', 'slacks', 'cardigan', 'coat', 'jacket', 'jumper',
    'onepiece(dress)', 'onepiece(jumpsuite)', 'shirt', 'sweater', 't-shirt', 'vest'
]
PATTERNS = [
    'animal', 'artifact', 'check', 'dot', 'etc', 'etcnature',
    'geometric', 'plants', 'stripe', 'symbol'
]
TONES = ['어두운 계열', '밝은 계열', '고려하지 않음']
CATEGORY_MAP = {
    'blouse': 'top', 'cardigan': 'top', 'coat': 'top', 'jacket': 'top', 'jumper': 'top',
    'shirt': 'top', 'sweater': 'top', 't-shirt': 'top', 'vest': 'top',
    'activewear': 'bottom', 'jeans': 'bottom', 'pants': 'bottom', 'shorts': 'bottom', 'skirt': 'bottom', 'slacks': 'bottom',
    'onepiece(dress)': 'onepiece', 'onepiece(jumpsuite)': 'onepiece'
}

def load_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

llm = ChatOpenAI(model_name="gpt-4o-mini", temperature=0.5)

def ask_gpt_for_filtering_criteria(situation, gender):
    prompt = f"""
    상황: {situation}
    성별: {gender}

    아래 조건을 만족하는 옷 조합을 3개 추천해주세요:

    1. 조합은 다음 중 하나여야 합니다:
      - (top + bottom) 조합
      - onepiece 단독 조합 (여성인 경우에만)

    2. top + bottom 조합을 선택했다면 top과 bottom이 각각 1벌씩 있어야 합니다.
    3. onepiece를 선택했다면 top과 bottom을 동시에 선택하면 안 됩니다.
    4. 남성인 경우 onepiece 조합은 추천하지 마세요.

    옷 종류 목록은 다음과 같습니다:
    - top: blouse, cardigan, coat, jacket, jumper, shirt, sweater, t-shirt, vest
    - bottom: activewear, jeans, pants, shorts, skirt, slacks
    - onepiece: onepiece(dress), onepiece(jumpsuite) (여성인 경우에만)

    응답 형식 예시:
    1. top: shirt, bottom: jeans
    2. top: sweater, bottom: slacks
    3. top: t-shirt, bottom: shorts
    """
    messages = [
        SystemMessage(content="당신은 패션 스타일리스트입니다."),
        HumanMessage(content=prompt)
    ]
    return llm.invoke(messages).content

def ask_gpt_for_best_clothing_sets(situation, outfit_sets, recommended_combinations):
    prompt_lines = [f"{i+1}. {s}" for i, s in enumerate(outfit_sets)]
    prompt = f"""
    상황: {situation}

    아래는 추천받은 3개의 옷 조합입니다:
    {recommended_combinations}

    그리고 아래는 옷장에 있는 실제 옷들입니다:
    {chr(10).join(prompt_lines)}

    각 추천 조합에 대해, 상황에 맞게 옷장에서 가장 적절한 옷을 하나씩 선택해주세요.
    선택한 옷에 대해 왜 그 옷이 상황에 적절한지 설명해주세요.

    응답은 반드시 아래 형식으로만 작성해주세요. 추가 설명이나 결론은 작성하지 마세요:

    조합 1: <첫 번째 추천 조합>
    선택한 옷: <옷장에서 선택한 옷 ID 또는 "해당 조합에 맞는 옷이 없습니다">
    이유: <이유>

    조합 2: <두 번째 추천 조합>
    선택한 옷: <옷장에서 선택한 옷 ID 또는 "해당 조합에 맞는 옷이 없습니다">
    이유: <이유>

    조합 3: <세 번째 추천 조합>
    선택한 옷: <옷장에서 선택한 옷 ID 또는 "해당 조합에 맞는 옷이 없습니다">
    이유: <이유>
    """
    messages = [
        SystemMessage(content="당신은 패션 코디 전문가입니다."),
        HumanMessage(content=prompt)
    ]
    return llm.invoke(messages).content

st.title("AI 옷 추천 시스템")

st.header("👕 옷 추가하기")
col1, col2, col3 = st.columns(3)
with col1:
    new_type = st.selectbox("옷 종류", CLOTHING_TYPES)
with col2:
    new_pattern = st.selectbox("패턴", PATTERNS)
with col3:
    new_tone = st.selectbox("톤", TONES)

if st.button("+ 옷장에 추가"):
    data = load_data()
    new_item = {
        "clothing_id": f"CLT_{len(data):06d}",
        "file_name": f"random_{len(data):03d}.jpg",
        "attributes": {
            "type": new_type,
            "type_id": CLOTHING_TYPES.index(new_type),
            "category": CATEGORY_MAP[new_type],
            "pattern": new_pattern,
            "pattern_id": PATTERNS.index(new_pattern),
            "tone": new_tone,
            "tone_id": TONES.index(new_tone)
        },
        "timestamp": datetime.now().isoformat(),
        "source": "user_upload"
    }
    data.append(new_item)
    save_data(data)
    st.success("옷이 옷장에 추가되었습니다!")

st.header("📌 상황 입력 & 옷 추천")
col1, col2 = st.columns(2)
with col1:
    situation = st.text_input("어떤 상황인가요? (예: 장례식, 면접, 여행 등)")
with col2:
    gender = st.selectbox("성별을 선택해주세요", ["남성", "여성"])

if st.button("👗 옷 추천받기") and situation:
    data = load_data()
    recommended_combinations = ask_gpt_for_filtering_criteria(situation, gender)
    st.text("[GPT 추천 옷 조합 기준]")
    st.code(recommended_combinations)

    outfit_sets = []
    for line in recommended_combinations.splitlines():
        if 'onepiece' in line.lower() and gender == "여성":
            for op in CLOTHING_TYPES:
                if CATEGORY_MAP[op] == 'onepiece' and op in line:
                    match = [item for item in data if item['attributes']['type'] == op]
                    for m in match:
                        outfit_sets.append(f"{m['clothing_id']} ({m['attributes']['type']})")
        elif 'top' in line.lower() and 'bottom' in line.lower():
            for top in CLOTHING_TYPES:
                if CATEGORY_MAP[top] == 'top' and top in line:
                    for bottom in CLOTHING_TYPES:
                        if CATEGORY_MAP[bottom] == 'bottom' and bottom in line:
                            top_matches = [item for item in data if item['attributes']['type'] == top]
                            bottom_matches = [item for item in data if item['attributes']['type'] == bottom]
                            for t in top_matches:
                                for b in bottom_matches:
                                    outfit_sets.append(f"{t['clothing_id']} ({t['attributes']['type']}) + {b['clothing_id']} ({b['attributes']['type']})")

    if not outfit_sets:
        st.warning("조건에 맞는 옷 조합이 없습니다.")
    else:
        final_response = ask_gpt_for_best_clothing_sets(situation, outfit_sets, recommended_combinations)
        st.text("[추천 결과]")
        st.code(final_response)
