from __future__ import annotations

from langchain_core._api.deprecation import suppress_langchain_deprecation_warning

from escalation_analysis.rules import (
    classify_escalation,
    extract_evidence,
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
            "classify_escalation",
            lambda state: analyze_with_llm(state, model=model),
        )
    else:
        graph.add_node("classify_escalation", classify_escalation)

    graph.add_edge("extract_evidence", "classify_escalation")
    graph.add_edge("classify_escalation", END)

    return graph.compile()
