import operator
from typing import Any, Dict, List, Annotated, TypedDict

from pydantic import BaseModel, Field


# --- Pydantic 모델 정의 ---
class CardAnalysisResult(BaseModel):
    """하나의 카드에 대한 모든 분석 결과를 통합하는 모델 (consolidate_analysis 노드의 출력)"""
    card_id: int
    card_name: str
    card_type: str = Field(description="카드 타입 ('credit' 또는 'check')")
    is_benefit_applicable: bool = Field(description="적용 가능한 혜택이 있는지")
    is_limit_remaining: bool = Field(description="월간/연간 혜택 한도 잔여 여부 (유효한 혜택이 하나라도 남아있는지 여부)")
    is_rules_verified_by_rag: bool = Field(description="RAG를 통해 약관상 예외 조항이 없음을 확인했는지 여부")
    rag_validation_details: str = Field(description="RAG 검증 시 발견된 주의사항 또는 확인 내용")
    applicable_benefits: List[Dict[str, Any]] = Field(description="해당 가맹점에서 적용 가능하며 한도도 남아있는 혜택 목록과 상세 조건")
    final_eligibility: bool = Field(description="모든 조건을 종합했을 때 최종 혜택 적용 가능 여부")

class Recommendation(BaseModel):
    """LLM이 생성하는 개별 추천 항목 모델"""
    rank: int = Field(description="혜택 순위")
    payment_method: str = Field(description="추천하는 결제 수단 이름 (예: 'KB 토심이 카드' 또는 '네이버페이 현장결제')")
    benefit_description: str = Field(description="예상 혜택에 대한 설명. 금액이 특정되지 않을 경우, 할인율이나 조건을 명시. 예: '10% 할인', '2만원 이상 결제 시 20% 할인이 2000원 할인보다 유리'")
    positive_reason: str = Field(description="이 결제 수단을 추천하는 긍정적인 이유")
    critical_review: str = Field(description="놓칠 수 있는 단점이나 주의사항 (비판적 전략). 예를 들어, '이 혜택을 받으면 실적에서 제외됩니다.' 또는 '다른 혜택과 중복 적용되지 않습니다.' 등. 단점이 없다면 '특별한 단점 없음'으로 명시.")
    evidence: str = Field(description="이 추천의 근거가 된 데이터나 분석 내용 요약")

class FinalRanking(BaseModel):
    """LLM의 최종 판단 결과를 구조화하는 최상위 모델 (generate_final_ranking 노드의 출력)"""
    recommendations: List[Recommendation] = Field(description="순위화된 추천 목록 (최대 3개)")
    summary: str = Field(description="사용자를 위한 최종 요약 및 조언")


# --- State 정의 ---
class AnalysisState(TypedDict):
    """혜택 분석 워크플로우 상태 정의"""
    # --- 입력 (Input) ---
    user_id: str
    store_name: str # location_name과 동일
    store_category: str # raw_category와 동일 (카카오 API 원본 문자열)

    # --- 중간 데이터 (Intermediate Data) ---
    # 1. DB에서 조회한 사용자의 카드 후보 목록 (search_user_cards 노드 결과)
    candidate_cards: List[Dict[str, Any]]

    # 2. 현장 결제 이벤트 (crawl_offline_events 노드 결과)
    offline_events: Annotated[List[Dict[str, Any]], operator.add]

    # 3. 카드별 분석 결과 (consolidate_analysis 노드 결과)
    analyzed_cards: List[Dict[str, Any]]

    # --- 최종 출력 (Final Output) ---
    # 4. LLM이 생성한 최종 순위 및 분석 결과 (generate_final_ranking 노드 결과)
    final_ranking: Dict[str, Any]

    # 5. 사용자에게 보여줄 최종 브리핑 문자열 (format_briefing 노드 결과)
    final_briefing: str