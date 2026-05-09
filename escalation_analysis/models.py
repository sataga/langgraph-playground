from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


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
