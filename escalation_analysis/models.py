from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


Category = Literal["first_cs_improvable", "authority_blocked", "mixed", "unclear"]


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
    reason: str = Field(
        description="Short Japanese explanation for the classification result."
    )
    evidence: list[str] = Field(
        description=(
            "Japanese evidence summaries. Translate or paraphrase ticket content into "
            "Japanese instead of copying non-Japanese source text."
        )
    )
