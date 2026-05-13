from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from escalation_analysis.models import AnalysisResult, JiraTicket


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


def write_json(value: Any, output_path: str) -> None:
    path = Path(output_path)
    payload = json.dumps(to_jsonable(value), indent=2, ensure_ascii=False)
    path.write_text(payload + "\n", encoding="utf-8")


def load_ticket(input_path: str | None) -> JiraTicket:
    path = DEFAULT_TICKET_PATH if input_path is None else Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    return JiraTicket.model_validate(payload)


def load_tickets(input_path: str | None) -> list[JiraTicket]:
    path = DEFAULT_TICKET_PATH if input_path is None else Path(input_path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "records" in payload:
        return [JiraTicket.model_validate(record) for record in payload["records"]]
    return [JiraTicket.model_validate(payload)]


def load_analysis_results(input_path: str) -> list[AnalysisResult]:
    payload = json.loads(Path(input_path).read_text(encoding="utf-8"))
    if isinstance(payload, dict) and "planned_updates" in payload:
        payload = payload["planned_updates"]
    if isinstance(payload, list):
        return [AnalysisResult.model_validate(item) for item in payload]
    return [AnalysisResult.model_validate(payload)]
