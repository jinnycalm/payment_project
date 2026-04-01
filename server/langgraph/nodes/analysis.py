import datetime
from typing import Any, Dict, List

from langchain_openai import OpenAIEmbeddings
from psycopg2.extras import RealDictCursor

from server.database.connection import get_db_conn
from server.langgraph.models import AnalysisState, CardAnalysisResult


def valid_benefit(card: Dict[str, Any], store_category: str) -> List[Dict[str, Any]]:
    """카드 한 개에 대해, 주어진 결제 정보에 적용 가능한 모든 혜택을 찾아 요약"""
    benefits_json = card.get("benefits_json", {})
    if not benefits_json:
        return []

    card_name = card.get("card_name")
    last_month_spent = card.get("last_month_spent", 0)

    category_map = {
        'FD6': "FOOD", 'CE7': "CAFE_BAKERY", 'CS2': "CONVENIENCE",
        'HP8': "MEDICAL", 'PM9': "MEDICAL", 'MT1': "SHOPPING",
        'AC5': "EDUCATION", 'PK6': "PARKING_LOT", 'OL7': "OIL", 
        'SW8': "TRANSPORTATION", 'CT1': "CULTURE_ENTERTAINMENT", "EX1": "OTHER"
    }
    target_category = category_map.get(store_category, "OTHER")  # 사용자가 선택한 업종

    print(f"💳 {card_name} 혜택 분석")
    found_benefits = []         # 해당 업종과 실적 조건을 충족하는 혜택들을 모두 찾아서 요약

    for benefit in benefits_json.get("benefits", []):
        if benefit.get("category") != target_category:
            continue

        conditions = benefit.get("conditions", {})
        min_performance = conditions.get("min_performance", 0)      # 실적 조건
        
        if last_month_spent < min_performance:
            continue                # 해당 업종이 다른 혜택 안에도 있을 수 있어서
        
        benefit_summary = {}
        benefit_type = benefit.get("type")          # PERCENT_DISCOUNT, FIXED_DISCOUNT, FREE_ACCESS, FEE_WAIVER 등
        benefit_value = benefit.get("value")        # 할인되는 금액, 횟수, 퍼센트
        unit = benefit.get("unit")                  # WON, PERCENT, COUNT 등
        
        desc = "혜택 확인 불가"     # default
        if benefit_type == "PERCENT_DISCOUNT":
            desc = f"{benefit_value}% 할인"
        elif benefit_type == "KRW_DISCOUNT":
            desc = f"{benefit_value}원 할인"
        elif benefit_type == "CASHBACK":
            desc = f"{benefit_value}{'%' if unit == 'PERCENT' else '원'} 캐시백"
        elif benefit_type == "POINT_ACCUMULATION":
            desc = f"{benefit_value}{'%' if unit == 'PERCENT' else '점'} 적립"
        elif benefit_type == "FREE_ACCESS":
            desc = f"무료 이용 {benefit_value}회"
        elif benefit_type == "FEE_WAIVER":
            desc = f"수수료 {benefit_value}% 면제"

        if conditions.get("per_transaction_cap"):       # 건당 최대 할인 금액
            desc += f" (건당 최대 {conditions['per_transaction_cap']:,}원)"

        benefit_summary['description'] = desc
        benefit_summary['benefit_id'] = benefit.get('benefit_id')       # 혜택 제공명(ex. 수수료 우대)
        
        merchants = benefit.get("merchant", [])
        if merchants:
            benefit_summary['applicable_merchants'] = ", ".join(merchants)
        
        limits = benefit.get("limits", {})      # 1구간은 얼마, 2구간은 얼마
        limit_desc_parts = []           # 구간 별 혜택 한도
        LIMIT_TYPES = ["monthly_performance_tiers", "monthly", "yearly"]

        for key in LIMIT_TYPES:
            value = limits.get(key)
            # 값이 없거나 None이면 다음 키로 넘어감
            if value is None:
                continue
            
            if key == "monthly_performance_tiers":
                # 리스트 형태인 '실적별 한도' 처리
                tiers = [f"{t['tier_min']//10000}만원↑ 월 {t['limit']:,}원" for t in value]
                limit_desc_parts.append(f"실적별: {', '.join(tiers)}")
                
            elif key == "monthly":
                # 숫자 형태인 '월간 한도' 처리
                limit_desc_parts.append(f"월간: {value:,}원")
                
            elif key == "yearly":
                # 숫자 형태인 '연간 한도' 처리
                limit_desc_parts.append(f"연간: {value:,}원")

            # 4. 최종 결과 합치기
            if limit_desc_parts:
                benefit_summary['limit_info'] = " / ".join(limit_desc_parts)
            else:
                benefit_summary['limit_info'] = "한도 제한 없음"

        performance_impact = benefit.get("performance_impact", {})      # 결제건이 실적에 미치는 영향
        perf_comment = performance_impact.get("comment")
        if not perf_comment:
            counts = performance_impact.get("counts_toward_performance", True)
            all_or_nothing = performance_impact.get("is_all_or_nothing_exclusion", False)

            if not counts:
                if all_or_nothing:
                    perf_comment = "할인 적용 시 결제 건 전체 실적 제외"
                else:
                    perf_comment = "할인 적용된 금액만 실적 제외"
            else:
                perf_comment = "실적에 포함됨"
        benefit_summary['performance_impact'] = perf_comment
        print(f"✨{card_name}의 {target_category} 혜택 정리: {benefit_summary}")
        found_benefits.append(benefit_summary)

    return found_benefits

def cross_check_with_rag(card: Dict[str, Any], store_name: str, store_category: str) -> Dict[str, Any]:
    """pgvector를 이용해 혜택과 주의사항을 RAG로 교차 검증"""
    benefits_json = card.get("benefits_json", {})
    critical_warning = benefits_json.get("critical_warning", "특별한 주의사항 없음.")
    
    # 1. 임베딩 모델 초기화 및 쿼리 벡터 생성
    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        query_text = f"카드명: {card.get('card_name')} | 상세: {store_name} 혜택 조건, 실적 제외 대상 및 주의사항"
        query_vector = embeddings.embed_query(query_text)
        
    except Exception as e:
        print(f"❌ 임베딩 생성 실패: {e}")
        # 임베딩 실패 시 기본 정보만 반환
        return {
            "is_rules_verified_by_rag": False,
            "rag_validation_details": f"기본 주의사항: {critical_warning} (RAG 검증 실패: {e})"
        }
    
    print(f"\n🕵️ '{store_name}'에 대한 '{card.get('card_name')}' RAG 검증 진행")
    vector_search_result = ""
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # 2. pgvector를 사용한 벡터 유사도 검색 실행
            cursor.execute("""
                SELECT content, 1 - (embedding <=> %s::vector) as similarity
                FROM card_benefit_vectors
                WHERE card_id = %s 
                ORDER BY embedding <=> %s::vector
                LIMIT 1
            """, (str(query_vector), str(card.get('card_id')), str(query_vector)))
            
            row = cursor.fetchone()
            
            # 유사도가 특정 임계값(예: 0.75) 이상일 때만 유의미한 정보로 간주
            if row and row['similarity'] > 0.75:
                vector_search_result = dict(row).get('content', '')
                print(f"🔍 RAG 검증: '{store_name}'에 대한 약관 유사도 {row['similarity']:.2f}의 내용 발견")
            else:
                print(f"🔍 RAG 검증: '{store_name}'에 대한 연관성 높은 약관 내용 없음")

    except Exception as e:
        print(f"❌ RAG 벡터 검색 실패: {e}")

    final_details = f"기본 주의사항: {critical_warning}"
    if vector_search_result:
        # 사용자가 이해하기 쉽게 포맷팅
        final_details += f" | ⚡ 추가 확인사항: {vector_search_result}"

    return {
        "is_rules_verified_by_rag": True, # RAG 검증 시도는 항상 했으므로 True, 내용은 details에 포함
        "rag_validation_details": final_details
    }

def check_benefit_limits(user_card_id: int, user_card_name:str, applicable_benefits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """DB에서 월별/연별 한도 사용량을 조회하여 실제 남은 한도 확인"""
    if not applicable_benefits:
        print(f"\n😢 {user_card_name} 카드로는 적용될 혜택이 없습니다.")
        return [] # 적용될 혜택이 없으면 빈 리스트 반환

    # 현재 월을 'YYYY-MM' 형식으로 가져옵니다.
    current_month = datetime.datetime.now().strftime('%Y-%m')

    benefit_ids = [b['benefit_id'] for b in applicable_benefits if 'benefit_id' in b]
    if not benefit_ids:
        print("\n😢 혜택 id가 없어서 조회가 불가능합니다.")
        return applicable_benefits # 혜택 ID가 없으면 한도 제한 없이 통과

    try:
        with get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            # 여러 benefit_id에 대해 한 번에 조회
            cursor.execute("""
                SELECT benefit_id, remaining_limit, remaining_count
                FROM monthly_benefit_usage
                WHERE user_card_id = %s
                  AND base_month = %s
                  AND benefit_id = ANY(%s)
            """, (user_card_id, current_month, benefit_ids))
            
            # RealDictRow 객체를 완벽한 dict 타입으로 캐스팅하며 benefit_id를 key로 매핑
            usage_records = {rec['benefit_id']: dict(rec) for rec in cursor.fetchall()}
            valid_benefits = []
            
            for benefit in applicable_benefits:
                benefit_id = benefit.get('benefit_id')
                if benefit_id in usage_records:           # 사용자가 혜택을 사용하지 않았으면 해당 테이블에 값이 없음
                    record = usage_records[benefit_id]
                    remaining_limit = record.get('remaining_limit')
                    remaining_count = record.get('remaining_count')

                    # 1. 한도 소진 여부 판단
                    is_limit_exhausted = (
                        (remaining_limit is not None and remaining_limit <= 0) or
                        (remaining_count is not None and remaining_count <= 0)
                    )

                    if is_limit_exhausted:
                        print(f"⚠️ {user_card_id}의 {benefit_id} 혜택 한도 초과")
                        continue  # 한도가 소진된 혜택은 스킵

                    # 2. LLM 분석용 데이터 주입
                    if remaining_limit is not None:
                        benefit['current_remaining_limit'] = remaining_limit

                    if remaining_count is not None:
                        benefit['current_remaining_count'] = remaining_count
                else:
                    benefit['current_remaining_info'] = "이번 달 사용 이력 없음 (최대 한도 보유)"
                
                valid_benefits.append(benefit)
            
            print(f"\n✅ 한도 확인 완료: {user_card_name} (유효한 혜택 {len(valid_benefits)}개)")
            print("-----------------------------------------")
            return valid_benefits

    except Exception as e:
        print(f"❌ DB에서 월별 혜택 한도 조회 실패: {e}")
        # 예외 발생 시 안전하게 한도가 없다고 가정하여 False 반환
        return []

def consolidate_analysis(state: AnalysisState) -> dict:
    """카드별 규칙(실적,한도), RAG 검증을 수행하고 분석 결과 통합"""
    print("\n--- 분석 결과 통합 및 RAG 검증 중 ---")

    analyzed_cards = []
    for card in state["candidate_cards"]:
        # 1. 적용 가능한 혜택 찾기
        applicable_benefits = valid_benefit(card, state["store_category"])
        
        # 2. RAG를 통한 교차 검증
        rag_check = cross_check_with_rag(card, state["store_name"], state["store_category"])
        
        # 3. DB에서 실시간 한도 조회
        valid_applicable_benefits = check_benefit_limits(card['user_card_id'], card['card_name'], applicable_benefits)

        # 4. 최종 분석 결과 종합
        is_benefit_applicable_overall = len(applicable_benefits) > 0        
        is_limit_remaining_overall = len(valid_applicable_benefits) > 0
        final_eligibility = is_benefit_applicable_overall and is_limit_remaining_overall and rag_check['is_rules_verified_by_rag']

        result = CardAnalysisResult(
            card_id=card['card_id'],
            card_name=card['card_name'],
            card_type=card.get('card_type', 'credit'),
            is_benefit_applicable=is_benefit_applicable_overall,
            is_limit_remaining=is_limit_remaining_overall,
            is_rules_verified_by_rag=rag_check['is_rules_verified_by_rag'],
            rag_validation_details=rag_check['rag_validation_details'],
            applicable_benefits=valid_applicable_benefits,
            final_eligibility=final_eligibility
        )
        analyzed_cards.append(result.model_dump())      # Pydantic 모델을 딕셔너리로 변환하여 저장
    
    print(f"=> ✅ 분석 결과 통합 완료: {len(analyzed_cards)}개 카드 분석됨")
    return {"analyzed_cards": analyzed_cards}