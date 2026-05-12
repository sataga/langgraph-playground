from __future__ import annotations

from typing import NotRequired, TypedDict

from escalation_analysis.models import AnalysisResult, JiraTicket


class TicketAnalysisState(TypedDict):
    ticket: JiraTicket
    evidence: NotRequired[list[str]]
    result: NotRequired[AnalysisResult]
