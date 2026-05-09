from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from escalation_analysis.models import JiraTicket


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
