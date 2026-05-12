from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

from escalation_analysis.models import AnalysisResult, JiraLabelUpdateResult


JIRA_API_PATH = "/rest/api/3/issue/{key}"
REQUEST_TIMEOUT_SECONDS = 20


def apply_label(
    result: AnalysisResult,
    *,
    dry_run: bool,
) -> JiraLabelUpdateResult:
    if dry_run:
        return JiraLabelUpdateResult(
            key=result.key,
            label=result.label,
            dry_run=True,
            applied=False,
            message="Dry run: Jira API was not called.",
        )

    base_url, email, api_token = load_jira_config()
    url = f"{base_url.rstrip('/')}{JIRA_API_PATH.format(key=result.key)}"
    payload = {"update": {"labels": [{"add": result.label}]}}

    response = requests.put(
        url,
        json=payload,
        auth=(email, api_token),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Failed to add Jira label. key={result.key} "
            f"status={response.status_code} response={response.text}"
        )

    return JiraLabelUpdateResult(
        key=result.key,
        label=result.label,
        dry_run=False,
        applied=True,
        message="Jira label was added.",
    )


def load_jira_config() -> tuple[str, str, str]:
    load_dotenv()
    base_url = os.environ.get("JIRA_BASE_URL")
    email = os.environ.get("JIRA_EMAIL")
    api_token = os.environ.get("JIRA_API_TOKEN")

    missing = [
        name
        for name, value in {
            "JIRA_BASE_URL": base_url,
            "JIRA_EMAIL": email,
            "JIRA_API_TOKEN": api_token,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Jira configuration. Set these environment variables: "
            + ", ".join(missing)
        )

    return base_url, email, api_token
