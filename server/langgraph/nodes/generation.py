import json

from langchain_openai import ChatOpenAI

from server.langgraph.models import AnalysisState, FinalRanking

# LLM 모델을 초기화합니다.
llm = ChatOpenAI(model="gpt-4.1-mini")

def generate_final_ranking(state: AnalysisState) -> dict:
    """통합된 정보를 바탕으로 LLM이 최종 순위 생성"""
    print("\n--- LLM 최종 순위 생성 중 ---")
    
    structured_llm = llm.with_structured_output(FinalRanking)
    
    prompt = f"""
    당신은 최고의 카드 혜택 분석 전문가입니다. 아래 정보를 바탕으로 사용자에게 가장 유리한 결제 수단을 최대 3개까지 순위별로 추천해주세요. 
    결제 금액이 정해져 있지 않으므로, 할인율과 고정 할인 금액을 비교하여 조건부 추천을 할 수 있습니다. (예: '2만원 이상 결제 시 A카드가 유리, 미만 시 B카드가 유리')
    
    **규칙:**
    1. 각 추천 항목에 대해 '비판적 검토(critical_review)'를 반드시 포함해야 합니다. 예상되는 단점이나 주의사항(예: 실적 제외, 다른 혜택과 중복 불가 등)을 명확히 지적해주세요. 단점이 없다면 '특별한 단점 없음'으로 표기하세요.
    2. 최종 요약(summary)을 통해 왜 이 순위가 최선인지 사용자에게 친절하게 설명해주세요.
    3. `benefit_description` 필드에는 구체적인 할인율이나 금액 대신, 사용자에게 가장 와닿는 형태의 혜택 설명을 요약해서 제공해주세요.
    4. 입력 데이터에 매장명에 지점명(ex. 강남점)이 포함된 경우, 다음 순서로 처리한다(카드 혜택, 현장 결제 이벤트 모두 동일하게 적용):
        - 먼저 카드 혜택(및 현장 결제 이벤트)에 해당 지점명이 명시된 조건이 있는지 확인한다.
        - 지점명 관련 조건이 존재하면, 해당 조건을 기준으로 혜택을 판단한다.
        - 지점명 관련 조건이 없다면, 매장명에서 지점명을 제거하고 “순수 매장명” 기준으로 다시 혜택을 확인한다.
    5. 현장 결제 이벤트 관련 정보가 없다면 일단 넘어가세요.
    6. 혜택 적용 카테고리로 받은 값은 아래의 내용을 보고 그에 해당 하는 키워드로 바꿔 판단에 참고하세요.
        - 'FD6': FOOD ("음식점", "식당", "외식", "패밀리레스토랑"), 
        - 'CE7': CAFE_BAKERY ("카페", "스타벅스", "베이커리", "커피", "디저트", "투썸", "이디야", "파리바게뜨", "뚜레쥬르") ,
        - 'CS2': CONVENIENCE ("편의점", "CU", "GS25", "세븐일레븐", "이마트24"),
        - 'HP8', 'PM9': MEDICAL ("병원", "약국", "치과", "한의원", "의료", "건강검진"),
        - 'MT1': SHOPPING ("마트", "이마트", "홈플러스", "롯데마트", "백화점"),
        - 'AC5': EDUCATION ("학원", "교육", "학습지", "강의"),
        - 'PK6': PARKING_LOT ("주차장", "주차", "발레파킹"),
        - 'OL7': OIL ("주유", "GSCALTEX", "S-OIL", "현대오일뱅크", "SK에너지", "충전소"), 
        - 'SW8': TRANSPORTATION ("지하철", "KTX", "SRT"), 
        - 'CT1': CULTURE_ENTERTAINMENT ("영화", "CGV", "메가박스", "롯데시네마", "문화", "공연", "전시", "테마파크", "놀이공원"), 
        - "EX1": OTHER (기타시설)

    **입력 정보:**
    - 사용자 ID: {state['user_id']}
    - 결제 장소: {state['store_name']}
    - 혜택 적용 카테고리: {state['store_category']} 
    - 분석된 카드 혜택: {json.dumps(state['analyzed_cards'], indent=2, ensure_ascii=False)}
    - 현장 결제 이벤트: {json.dumps(state.get('offline_events', []), indent=2, ensure_ascii=False)} 
    """
    # llm이 이해하기 쉽게 json 형식으로 변환(indent로 사람이 보기 쉽게 표현, ensure_ascii로 한글 깨짐 방지)
    
    response = structured_llm.invoke(prompt) 
    
    print(f"✅ LLM이 추천하는 혜택 순위 생성 완료")
    return {"final_ranking": response.model_dump()}


def format_briefing(state: AnalysisState) -> dict:
    """구조화된 순위 결과를 사용자가 보기 좋은 문자열로 변환"""
    print("\n--- 최종 브리핑 포맷팅 중 ---")
    ranking_data = state["final_ranking"]
    briefing = f"✨ **'{state['store_name']}' 최적 결제 플랜** ✨\n\n"
    
    for rec in ranking_data['recommendations']:
        briefing += f"**🏆 {rec['rank']}순위: {rec['payment_method']}**\n"
        briefing += f"- 혜택 내용: **{rec['benefit_description']}**\n"
        briefing += f"- 추천 이유: {rec['positive_reason']}\n"
        briefing += f"- ⚠️ **체크포인트**: {rec['critical_review']}\n"
        briefing += f"- 근거: {rec['evidence']}\n\n\n"
    
    briefing += f"**💡 최종 요약**\n{ranking_data['summary']}"
    
    print(briefing)
    return {"final_briefing": briefing}