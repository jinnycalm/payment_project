from typing import Any, Dict, List

from psycopg2.extras import RealDictCursor

from server.database.connection import get_db_conn
from server.langgraph.models import AnalysisState


def search_user_cards(state: AnalysisState) -> List[Dict[str, Any]]:
    """DB에서 사용자의 카드 정보 조회"""
    print("--- 카드 정보 조회 중 ---")
    user_id = state["user_id"]
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)     # 결과를 딕셔너리 형태로 받기 위해(tuple -> dictionary)
            cursor.execute("""
                SELECT u.id AS user_card_id, c.card_id AS card_id, c.card_name, u.last_month_spent, u.issue_date, c.card_type, c.benefits_json
                    FROM user_card u LEFT JOIN card_master c 
                           ON u.card_id = c.id
                WHERE u.user_id = %s""", (user_id,))
            
            candidate_cards = [dict(row) for row in cursor.fetchall()]   # RealDictCursor[]~ -> 일반 딕셔너리 리스트로 변환
            
            print(f"✅ 조회된 카드 수: {len(candidate_cards)}개")
            return candidate_cards
    except Exception as e:
        print(f"❌ DB에서 사용자 카드 데이터 조회 실패: {e}")
        raise e


def fetch_offline_events_from_rag(state: AnalysisState) -> List[Dict[str, Any]]:
    """RAG를 사용하여 현장 결제 이벤트 정보 조회"""
    print("--- RAG 현장 이벤트 조회 중 ---")
   
    dummy_events = [
        {"pay_system": "네이버페이", "brand": state["store_name"], "benefit_detail": "결제 금액의 10% 페이백", "max_benefit": 2000, "source": "naver_events.md"}
    ]
    print(f"✅ RAG로 조회된 이벤트 수: {len(dummy_events)}개")
    return dummy_events