from __future__ import annotations

import os

import requests
from dotenv import load_dotenv

from escalation_analysis.models import AnalysisResult, JiraLabelUpdateResult, JiraTicket


JIRA_API_PATH = "/rest/api/latest/issue/{key}"
JIRA_SEARCH_API_PATH = "/rest/api/latest/search"
REQUEST_TIMEOUT_SECONDS = 20
JIRA_SEARCH_FIELDS = [
    "assignee",
    "comment",
    "components",
    "created",
    "description",
    "issuetype",
    "labels",
    "resolutiondate",
    "summary",
]
PROJECT_JQL = {
    "project_a": "project = PROJECT_A AND labels = ESCL_PROJECT_A ORDER BY created DESC",
    "project_b": "project = PROJECT_B AND labels = ESCL_PROJECT_B ORDER BY created DESC",
    "project_c": "project = PROJECT_C AND labels = ESCL_PROJECT_C ORDER BY created DESC",
}


def apply_label(
    result: AnalysisResult,
) -> JiraLabelUpdateResult:
    base_url, personal_access_token = load_jira_config()
    url = f"{base_url.rstrip('/')}{JIRA_API_PATH.format(key=result.key)}"
    payload = {"update": {"labels": [{"add": result.label}]}}

    response = requests.put(
        url,
        json=payload,
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {personal_access_token}",
            "Content-Type": "application/json",
        },
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
        applied=True,
        message="Jira label was added.",
    )


def fetch_tickets(
    project: str,
    *,
    max_results: int,
) -> list[JiraTicket]:
    selected_projects = list(PROJECT_JQL) if project == "all" else [project]
    tickets: list[JiraTicket] = []
    for project_name in selected_projects:
        remaining = max_results - len(tickets)
        if remaining <= 0:
            break
        tickets.extend(fetch_tickets_by_jql(PROJECT_JQL[project_name], remaining))
    return tickets


def fetch_tickets_by_jql(jql: str, max_results: int) -> list[JiraTicket]:
    base_url, personal_access_token = load_jira_config()
    url = f"{base_url.rstrip('/')}{JIRA_SEARCH_API_PATH}"
    start_at = 0
    tickets: list[JiraTicket] = []

    while True:
        page_size = min(max_results - len(tickets), 100)
        if page_size <= 0:
            break

        response = requests.get(
            url,
            headers={
                "Accept": "application/json",
                "Authorization": f"Bearer {personal_access_token}",
            },
            params={
                "jql": jql,
                "startAt": start_at,
                "maxResults": page_size,
                "fields": ",".join(JIRA_SEARCH_FIELDS),
            },
            timeout=REQUEST_TIMEOUT_SECONDS,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                "Failed to search Jira tickets. "
                f"status={response.status_code} response={response.text}"
            )

        payload = response.json()
        issues = payload.get("issues", [])
        tickets.extend(jira_issue_to_ticket(issue, base_url) for issue in issues)

        start_at += len(issues)
        total = int(payload.get("total", start_at))
        if not issues or start_at >= total:
            break

    return tickets


def jira_issue_to_ticket(issue: dict, base_url: str) -> JiraTicket:
    fields = issue.get("fields", {})
    comments = [
        {
            "body": comment.get("body") or "",
            "created": comment.get("created") or "",
        }
        for comment in fields.get("comment", {}).get("comments", [])
    ]
    assignee = fields.get("assignee") or {}
    issue_type = fields.get("issuetype") or {}

    return JiraTicket(
        components=[
            component.get("name", "")
            for component in fields.get("components", [])
            if component.get("name")
        ],
        key=issue["key"],
        url=f"{base_url.rstrip('/')}/browse/{issue['key']}",
        created=fields.get("created") or "",
        closed=fields.get("resolutiondate"),
        summary=fields.get("summary") or "",
        description=fields.get("description") or "",
        labels=fields.get("labels") or [],
        category=issue_type.get("name") or "",
        assignee=assignee.get("displayName") or "",
        escalation=True,
        no_document=False,
        comments=comments,
        comment_stats={"total_comments": len(comments)},
    )


def load_jira_config() -> tuple[str, str]:
    load_dotenv()
    base_url = os.environ.get("JIRA_BASE_URL")
    personal_access_token = os.environ.get("JIRA_ACCESS_TOKEN")

    missing = [
        name
        for name, value in {
            "JIRA_BASE_URL": base_url,
            "JIRA_ACCESS_TOKEN": personal_access_token,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(
            "Missing Jira configuration. Set these environment variables: "
            + ", ".join(missing)
        )

    return base_url, personal_access_token
