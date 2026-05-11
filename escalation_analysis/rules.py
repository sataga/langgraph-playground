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
    "unknown procedure": "手順の理解不足を示す記述があります。",
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


def extract_evidence(state: TicketAnalysisState) -> dict[str, list[str]]:
    ticket = state["ticket"]
    texts = [
        ticket.summary,
        ticket.description,
        *(comment.body for comment in ticket.comments),
    ]
    evidence = [text for text in texts if text.strip()]
    return {"evidence": evidence}


def score_first_cs_improvable(state: TicketAnalysisState) -> dict[str, int | list[str]]:
    ticket = state["ticket"]
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()
    score = sum(
        1 for keyword in FIRST_CS_IMPROVABLE_KEYWORDS if keyword in evidence_text
    )
    findings = [
        finding
        for keyword, finding in FIRST_CS_IMPROVABLE_FINDINGS.items()
        if keyword in evidence_text
    ]
    if ticket.no_document:
        score += 1
        findings.append("参照できるドキュメントがないことを示すフラグがあります。")
    return {
        "first_cs_improvable_score": score,
        "first_cs_improvable_findings": findings,
    }


def score_authority_blocked(state: TicketAnalysisState) -> dict[str, int | list[str]]:
    evidence = state.get("evidence", [])
    evidence_text = " ".join(evidence).lower()
    score = sum(1 for keyword in AUTHORITY_KEYWORDS if keyword in evidence_text)
    findings = [
        finding
        for keyword, finding in AUTHORITY_FINDINGS.items()
        if keyword in evidence_text
    ]
    return {"authority_score": score, "authority_findings": findings}


def judge_category(state: TicketAnalysisState) -> dict[str, Category | float | str]:
    first_cs_score = state.get("first_cs_improvable_score", 0)
    authority_score = state.get("authority_score", 0)

    if first_cs_score == 0 and authority_score == 0:
        return {
            "category": "unclear",
            "confidence": 0.2,
            "judgement_reason": "権限不足または First-CS 改善余地を示す十分な根拠が見つかりませんでした。",
        }

    if first_cs_score > 0 and authority_score > 0:
        return {
            "category": "mixed",
            "confidence": 0.6,
            "judgement_reason": "権限不足を示す根拠と First-CS 側で改善できる可能性を示す根拠の両方があります。",
        }

    if authority_score > first_cs_score:
        return {
            "category": "authority_blocked",
            "confidence": 0.85,
            "judgement_reason": "一次受付では実行できない権限・ロール・管理者操作が必要だった可能性が高いです。",
        }

    return {
        "category": "first_cs_improvable",
        "confidence": 0.85,
        "judgement_reason": "権限不足による不可避なエスカレーションではなく、First-CS の確認・判断改善で次回対応できる可能性があります。",
    }


def assign_label(state: TicketAnalysisState) -> dict[str, AnalysisResult]:
    category = state.get("category", "unclear")
    labels = {
        "first_cs_improvable": "escalation:first_cs_improvable",
        "authority_blocked": "escalation:authority_blocked",
        "mixed": "escalation:mixed",
        "unclear": "escalation:needs_human_review",
    }
    reasons = {
        "first_cs_improvable": "権限不足による不可避なエスカレーションではなく、First-CS の確認・判断改善で次回対応できる可能性があります。",
        "authority_blocked": "一次受付では実行できない権限・ロール・管理者操作が必要だった可能性が高いです。",
        "mixed": "権限不足を示す根拠と First-CS 側で改善できる可能性を示す根拠の両方があります。",
        "unclear": "分類に必要な根拠が不足しているため、人による確認が必要です。",
    }
    findings = [
        *state.get("authority_findings", []),
        *state.get("first_cs_improvable_findings", []),
    ]
    if not findings:
        findings = ["分類に使える明確な根拠は抽出できませんでした。"]

    result = AnalysisResult(
        category=category,
        label=labels[category],
        confidence=state.get("confidence", 0.0),
        reason=state.get("judgement_reason", reasons[category]),
        evidence=findings,
    )
    return {"result": result}
