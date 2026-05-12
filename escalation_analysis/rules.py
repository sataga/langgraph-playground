from __future__ import annotations

from escalation_analysis.models import AnalysisResult, Category
from escalation_analysis.state import TicketAnalysisState


FIRST_CS_IMPROVABLE_KEYWORDS = [
    "runbook not checked",
    "without checking",
    "did not check",
    "before checking",
    "unknown procedure",
    "missed document",
    "investigation missing",
    "should have been attempted",
    "existing rebuild runbook",
]

FIRST_CS_IMPROVABLE_FINDINGS = {
    "runbook not checked": "既存の runbook を確認していない記述があります。",
    "without checking": "必要な確認を行わずにエスカレーションした可能性があります。",
    "did not check": "必要な確認を行っていない記述があります。",
    "before checking": "確認前にエスカレーションした記述があります。",
    "unknown procedure": "手順理解の不足を示す記述があります。",
    "missed document": "参照すべきドキュメントを見落とした可能性があります。",
    "investigation missing": "一次受付での調査不足を示す記述があります。",
    "should have been attempted": "一次受付で試すべき手順があった記述があります。",
    "existing rebuild runbook": "既存の rebuild runbook で対応できた可能性があります。",
}

AUTHORITY_KEYWORDS = [
    "administrator",
    "permission",
    "role",
    "access",
    "approval",
    "disabled",
]

AUTHORITY_FINDINGS = {
    "administrator": "管理者権限が必要であることを示す記述があります。",
    "permission": "必要な権限が不足していることを示す記述があります。",
    "role": "一次受付のロールでは対応できないことを示す記述があります。",
    "access": "必要なアクセス権が不足していることを示す記述があります。",
    "approval": "承認が必要で一次受付だけでは進められない可能性があります。",
    "disabled": "一次受付の権限では操作できない状態であることを示す記述があります。",
}

LABELS = {
    "first_cs_improvable": "escalation:first_cs_improvable",
    "authority_blocked": "escalation:authority_blocked",
    "mixed": "escalation:mixed",
    "unclear": "escalation:needs_human_review",
}

CATEGORY_REASONS = {
    "first_cs_improvable": (
        "権限不足による不可避なエスカレーションではなく、"
        "First-CS の確認や判断を改善できる可能性が高いです。"
    ),
    "authority_blocked": (
        "一次受付では実行できない権限、ロール、管理者操作が必要だった可能性が高いです。"
    ),
    "mixed": (
        "権限不足を示す根拠と First-CS 側で改善できる可能性を示す根拠の両方があります。"
    ),
    "unclear": "分類に必要な根拠が不足しているため、人による確認が必要です。",
}


def extract_evidence(state: TicketAnalysisState) -> dict[str, list[str]]:
    ticket = state["ticket"]
    texts = [
        ticket.summary,
        ticket.description,
        *(comment.body for comment in ticket.comments),
    ]
    evidence = [text for text in texts if text.strip()]
    return {"evidence": evidence}


def classify_escalation(state: TicketAnalysisState) -> dict[str, AnalysisResult]:
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()

    first_cs_score, first_cs_findings = score_keywords(
        evidence_text,
        FIRST_CS_IMPROVABLE_KEYWORDS,
        FIRST_CS_IMPROVABLE_FINDINGS,
    )
    authority_score, authority_findings = score_keywords(
        evidence_text,
        AUTHORITY_KEYWORDS,
        AUTHORITY_FINDINGS,
    )

    if state["ticket"].no_document:
        first_cs_score += 1
        first_cs_findings.append("参照できるドキュメントがないことを示すフラグがあります。")

    category, confidence = choose_category(first_cs_score, authority_score)
    findings = [*authority_findings, *first_cs_findings]
    if not findings:
        findings = ["分類に使える明確な根拠は抽出できませんでした。"]

    result = AnalysisResult(
        key=state["ticket"].key,
        category=category,
        label=LABELS[category],
        confidence=confidence,
        reason=CATEGORY_REASONS[category],
        evidence=findings,
    )
    return {"result": result}


def score_keywords(
    evidence_text: str,
    keywords: list[str],
    findings_by_keyword: dict[str, str],
) -> tuple[int, list[str]]:
    score = sum(1 for keyword in keywords if keyword in evidence_text)
    findings = [
        finding
        for keyword, finding in findings_by_keyword.items()
        if keyword in evidence_text
    ]
    return score, findings


def choose_category(first_cs_score: int, authority_score: int) -> tuple[Category, float]:
    if first_cs_score == 0 and authority_score == 0:
        return "unclear", 0.2

    if first_cs_score > 0 and authority_score > 0:
        return "mixed", 0.6

    if authority_score > first_cs_score:
        return "authority_blocked", 0.85

    return "first_cs_improvable", 0.85
