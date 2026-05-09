from __future__ import annotations

from typing import NotRequired, TypedDict

from escalation_analysis.models import AnalysisResult, Category, JiraTicket


class TicketAnalysisState(TypedDict):
    ticket: JiraTicket
    evidence: NotRequired[list[str]]
    knowledge_score: NotRequired[int]
    authority_score: NotRequired[int]
    category: NotRequired[Category]
    confidence: NotRequired[float]
    result: NotRequired[AnalysisResult]
