from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["knowledge_gap", "authority_blocked", "mixed", "unclear"]


class TicketComment(BaseModel):
    body: str
    created: str = ""


class JiraTicket(BaseModel):
    component: list[str] = Field(default_factory=list)
    key: str
    url: str = ""
    created: str = ""
    closed: str | None = None
    summary: str
    description: str
    labels: list[str] = Field(default_factory=list)
    category: str = ""
    assignee: str = ""
    escalation: bool = False
    no_document: bool = False
    comments: list[TicketComment] = Field(default_factory=list)
    comment_stats: dict[str, float | int] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    category: Category
    label: str
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str
    evidence: list[str]
