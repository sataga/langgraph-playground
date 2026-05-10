from __future__ import annotations

from escalation_analysis.models import AnalysisResult, Category
from escalation_analysis.state import TicketAnalysisState


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
    texts = [
        ticket.summary,
        ticket.description,
        *(comment.body for comment in ticket.comments),
    ]
    evidence = [text for text in texts if text.strip()]
    return {"evidence": evidence}


def score_knowledge_gap(state: TicketAnalysisState) -> dict[str, int]:
    ticket = state["ticket"]
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()
    score = sum(1 for keyword in KNOWLEDGE_KEYWORDS if keyword in evidence_text)
    if ticket.no_document:
        score += 1
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
