from typing import Any, Dict, List

from langchain_openai import OpenAIEmbeddings
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
    """RAG를 사용하여 Vector DB에서 현장 결제 이벤트 정보 조회"""
    print("--- RAG 현장 이벤트 조회 중 ---")
    store_name = state["store_name"]
    store_category = state["store_category"]

    # 카테고리 코드를 자연어 키워드로 변환 (RAG 쿼리 보강용)
    category_map = {
        "FD6": "음식점, 식당, 외식, 패밀리레스토랑",
        "CE7": "카페, 스타벅스, 베이커리, 커피, 디저트, 투썸, 이디야, 파리바게뜨, 뚜레쥬르",
        "CS2": "편의점, CU, GS25, 세븐일레븐, 이마트24",
        "HP8": "병원, 약국, 치과, 한의원, 의료, 건강검진",
        "PM9": "병원, 약국, 치과, 한의원, 의료, 건강검진",
        "MT1": "마트, 이마트, 홈플러스, 롯데마트",
        "AC5": "학원, 교육, 학습지, 강의, 서점, 도서, 유치원",
        "PK6": "주차장, 주차, 발레파킹",
        "OL7": "주유, GSCALTEX, S-OIL, 현대오일뱅크, SK에너지, 충전소",
        "SW8": "대중교통, 버스, 지하철, 택시, 철도, KTX, SRT, K-패스",
        "CT1": "영화, CGV, 메가박스, 롯데시네마, 문화, 공연, 전시, 테마파크, 놀이공원",
        "EX1": "기타 시설, 다이소, 올리브영 등"
    }
    mapping_category = category_map.get(store_category, "일반 매장")

    # 정확도 향상을 위한 브랜드명 추출
    brand_name = store_name.split()[0]

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        query_text = f"브랜드 '{brand_name}' 또는 매장명 '{store_name}' ({mapping_category}) 관련 현장 결제 이벤트"
        query_vector = embeddings.embed_query(query_text)
    
    except Exception as e:
        print(f"❌ 이벤트 RAG 임베딩 생성 실패: {e}")
        return []

    found_events = []
    try:
        with get_db_conn() as conn:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            brand_like_pattern = f'%{brand_name}%'
            
            cursor.execute("""
                SELECT content, metadata, 1 - (embedding <=> %s::vector) as similarity
                FROM naver_pay_vectors
                WHERE metadata::text LIKE %s
                ORDER BY embedding <=> %s::vector
                LIMIT 5
            """, (str(query_vector), brand_like_pattern, str(query_vector)))
            
            for row in cursor.fetchall():
                if row['similarity'] < 0.75:  # 유사도 임계값 이하인 결과는 무시
                    continue

                metadata = row.get('metadata', {})
                brands = metadata.get('brands', [])

                # 최종 결과 포맷팅
                found_events.append({
                    "pay_system": metadata.get("payment_method", "정보 없음"),
                    "brand": ", ".join(brands) if brands else "모든 매장",
                    "benefit_detail": row.get('content', '상세 정보 없음'),
                    "max_benefit": metadata.get("benefit_max"),
                    "source": "naver_pay_vectors"
                })
    except Exception as e:
        print(f"❌ 이벤트 RAG 벡터 검색 실패: {e}")

    print(f"✅ RAG로 조회된 이벤트 수: {len(found_events)}개")
    return found_events