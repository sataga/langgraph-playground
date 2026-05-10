from __future__ import annotations

from langchain_core._api.deprecation import suppress_langchain_deprecation_warning

from escalation_analysis.rules import (
    assign_label,
    extract_evidence,
    judge_category,
    score_authority_blocked,
    score_knowledge_gap,
)
from escalation_analysis.state import TicketAnalysisState

with suppress_langchain_deprecation_warning():
    from langgraph.graph import END, START, StateGraph


def build_graph(*, use_llm: bool = False, model: str = "gpt-5-nano"):
    graph = StateGraph(TicketAnalysisState)

    graph.add_node("extract_evidence", extract_evidence)
    graph.add_edge(START, "extract_evidence")

    if use_llm:
        from escalation_analysis.llm import analyze_with_llm

        graph.add_node(
            "analyze_with_llm",
            lambda state: analyze_with_llm(state, model=model),
        )
        graph.add_edge("extract_evidence", "analyze_with_llm")
        graph.add_edge("analyze_with_llm", END)
    else:
        graph.add_node("score_knowledge_gap", score_knowledge_gap)
        graph.add_node("score_authority_blocked", score_authority_blocked)
        graph.add_node("judge_category", judge_category)
        graph.add_node("assign_label", assign_label)

        graph.add_edge("extract_evidence", "score_knowledge_gap")
        graph.add_edge("score_knowledge_gap", "score_authority_blocked")
        graph.add_edge("score_authority_blocked", "judge_category")
        graph.add_edge("judge_category", "assign_label")
        graph.add_edge("assign_label", END)

    return graph.compile()
