from fastapi import APIRouter
from server.models.map import MapInfo
from server.langgraph.graph import create_benefit_analysis_graph
from server.langgraph.models import AnalysisState

router = APIRouter()

benefit_analysis_graph = create_benefit_analysis_graph()

@router.post("/analyze")
async def analyze_benefit(place: MapInfo):
    print(f"선택한 매장명: {place.get('place_name')}, 카테고리 코드: {place.get('category_group_code')}")
    
    # TODO: 실제 서비스에서는 인증 시스템(예: JWT 토큰)을 통해 user_id를 가져와야함.
    initial_state = AnalysisState(
        user_id="1",  # 임시 사용자 ID
        store_name=place.get('place_name'),
        store_category=place.get('category_group_code'), # 카카오 API의 카테고리 코드를 사용
    )
    
    final_state = benefit_analysis_graph.invoke(initial_state)

    return {
        "status": "success",
        "message": f"'{place.get('place_name')}' 매장에 대한 분석이 완료되었습니다.",
        "data": final_state.get("final_briefing") 
    }
