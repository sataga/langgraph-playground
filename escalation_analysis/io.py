from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from escalation_analysis.models import JiraTicket


DEFAULT_TICKET_PATH = Path("tickets/sample_escalated_vm_metadata_corruption.json")


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
    path = DEFAULT_TICKET_PATH if input_path is None else Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JiraTicket.model_validate(payload)
