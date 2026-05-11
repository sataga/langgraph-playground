from __future__ import annotations

from typing import NotRequired, TypedDict

from escalation_analysis.models import AnalysisResult, Category, JiraTicket


class TicketAnalysisState(TypedDict):
    ticket: JiraTicket
    evidence: NotRequired[list[str]]
    first_cs_improvable_score: NotRequired[int]
    first_cs_improvable_findings: NotRequired[list[str]]
    authority_score: NotRequired[int]
    authority_findings: NotRequired[list[str]]
    category: NotRequired[Category]
    confidence: NotRequired[float]
    judgement_reason: NotRequired[str]
    result: NotRequired[AnalysisResult]
