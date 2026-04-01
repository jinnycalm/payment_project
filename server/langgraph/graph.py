from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableParallel

from server.langgraph.models import AnalysisState
from server.langgraph.nodes.analysis import consolidate_analysis
from server.langgraph.nodes.data_gathering import (fetch_offline_events_from_rag, search_user_cards)
from server.langgraph.nodes.generation import (format_briefing, generate_final_ranking)

# --- Build Graph ---
def create_benefit_analysis_graph():
    workflow = StateGraph(AnalysisState)

    # Add nodes
    # 데이터 수집 단계 (병렬 실행)
    workflow.add_node("gather_data", RunnableParallel(
        candidate_cards=search_user_cards,
        offline_events=fetch_offline_events_from_rag
    ))
    # 분석 및 통합 단계
    workflow.add_node("consolidate_analysis", consolidate_analysis)
    # LLM 추천 및 순위 생성 단계
    workflow.add_node("generate_final_ranking", generate_final_ranking)
    # 최종 결과 포맷팅 단계
    workflow.add_node("format_briefing", format_briefing)

    # Set entry point
    workflow.set_entry_point("gather_data")

    # Add edges
    workflow.add_edge("gather_data", "consolidate_analysis")
    workflow.add_edge("consolidate_analysis", "generate_final_ranking")
    workflow.add_edge("generate_final_ranking", "format_briefing")
    workflow.add_edge("format_briefing", END)

    return workflow.compile()