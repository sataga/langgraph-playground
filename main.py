from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Literal, NotRequired, TypedDict

from langchain_core._api.deprecation import suppress_langchain_deprecation_warning
from pydantic import BaseModel, Field

with suppress_langchain_deprecation_warning():
    from langgraph.graph import END, START, StateGraph


Category = Literal["knowledge_gap", "authority_blocked", "mixed", "unclear"]


class JiraTicket(BaseModel):
    key: str
    summary: str
    description: str
    comments: list[str] = Field(default_factory=list)
    escalated: bool = False


class AnalysisResult(BaseModel):
    category: Category
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[str]


class TicketAnalysisState(TypedDict):
    ticket: JiraTicket
    evidence: NotRequired[list[str]]
    knowledge_score: NotRequired[int]
    authority_score: NotRequired[int]
    category: NotRequired[Category]
    confidence: NotRequired[float]
    result: NotRequired[AnalysisResult]


DUMMY_TICKET = JiraTicket(
    key="HELP-123",
    summary="Unable to reset customer MFA",
    description=(
        "The support agent escalated the ticket after finding that MFA reset "
        "requires an administrator role."
    ),
    comments=[
        "Checked the runbook and confirmed the documented reset steps.",
        "The reset button is disabled for the support role.",
        "Escalating to an administrator because elevated permission is required.",
    ],
    escalated=True,
)


KNOWLEDGE_KEYWORDS = [
    "runbook not checked",
    "did not check",
    "unknown procedure",
    "missed document",
    "investigation missing",
]

AUTHORITY_KEYWORDS = [
    "administrator",
    "permission",
    "role",
    "access",
    "approval",
    "disabled",
]


def extract_evidence(state: TicketAnalysisState) -> dict[str, list[str]]:
    ticket = state["ticket"]
    texts = [ticket.summary, ticket.description, *ticket.comments]
    evidence = [text for text in texts if text.strip()]
    return {"evidence": evidence}


def score_knowledge_gap(state: TicketAnalysisState) -> dict[str, int]:
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()
    score = sum(1 for keyword in KNOWLEDGE_KEYWORDS if keyword in evidence_text)
    return {"knowledge_score": score}


def score_authority_blocked(state: TicketAnalysisState) -> dict[str, int]:
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()
    score = sum(1 for keyword in AUTHORITY_KEYWORDS if keyword in evidence_text)
    return {"authority_score": score}


def judge_category(state: TicketAnalysisState) -> dict[str, Category | float]:
    knowledge_score = state.get("knowledge_score", 0)
    authority_score = state.get("authority_score", 0)

    if knowledge_score == 0 and authority_score == 0:
        return {"category": "unclear", "confidence": 0.2}

    if knowledge_score > 0 and authority_score > 0:
        return {"category": "mixed", "confidence": 0.6}

    if authority_score > knowledge_score:
        return {"category": "authority_blocked", "confidence": 0.85}

    return {"category": "knowledge_gap", "confidence": 0.85}


def assign_label(state: TicketAnalysisState) -> dict[str, AnalysisResult]:
    category = state.get("category", "unclear")
    labels = {
        "knowledge_gap": "escalation:knowledge_gap",
        "authority_blocked": "escalation:authority_blocked",
        "mixed": "escalation:mixed",
        "unclear": "escalation:needs_human_review",
    }
    reasons = {
        "knowledge_gap": "The evidence suggests the issue could likely have been resolved with better research or existing documentation.",
        "authority_blocked": "The evidence suggests escalation was unavoidable because the agent lacked required permission or role.",
        "mixed": "The evidence contains both knowledge-gap and permission-related signals.",
        "unclear": "There is not enough evidence to classify the escalation confidently.",
    }

    result = AnalysisResult(
        category=category,
        label=labels[category],
        confidence=state.get("confidence", 0.0),
        reason=reasons[category],
        evidence=state.get("evidence", []),
    )
    return {"result": result}


def build_graph():
    graph = StateGraph(TicketAnalysisState)

    graph.add_node("extract_evidence", extract_evidence)
    graph.add_node("score_knowledge_gap", score_knowledge_gap)
    graph.add_node("score_authority_blocked", score_authority_blocked)
    graph.add_node("judge_category", judge_category)
    graph.add_node("assign_label", assign_label)

    graph.add_edge(START, "extract_evidence")
    graph.add_edge("extract_evidence", "score_knowledge_gap")
    graph.add_edge("score_knowledge_gap", "score_authority_blocked")
    graph.add_edge("score_authority_blocked", "judge_category")
    graph.add_edge("judge_category", "assign_label")
    graph.add_edge("assign_label", END)

    return graph.compile()


def to_jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump()
    if isinstance(value, dict):
        return {key: to_jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [to_jsonable(item) for item in value]
    return value


def print_json(value: Any) -> None:
    print(json.dumps(to_jsonable(value), indent=2, ensure_ascii=False))


def load_ticket(input_path: str | None) -> JiraTicket:
    if input_path is None:
        return DUMMY_TICKET

    path = Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JiraTicket.model_validate(payload)


def run_with_debug(ticket: JiraTicket) -> AnalysisResult:
    app = build_graph()
    result: AnalysisResult | None = None

    print("Node transitions:")
    for update in app.stream({"ticket": ticket}, stream_mode="updates"):
        for node_name, node_update in update.items():
            print(f"\n[{node_name}]")
            print_json(node_update)

            if "result" in node_update:
                result = node_update["result"]

    if result is None:
        raise RuntimeError("Graph finished without producing an analysis result.")

    print("\nFinal result:")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a dummy Jira escalation ticket with LangGraph."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print each LangGraph node update before the final result.",
    )
    parser.add_argument(
        "--input",
        help="Path to a UTF-8 JSON file containing one Jira ticket.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ticket = load_ticket(args.input)

    if args.debug:
        result = run_with_debug(ticket)
    else:
        app = build_graph()
        final_state = app.invoke({"ticket": ticket})
        result = final_state["result"]

    print_json(result)


if __name__ == "__main__":
    main()
