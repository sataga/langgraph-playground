from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from escalation_analysis.models import AnalysisResult
from escalation_analysis.state import TicketAnalysisState


DEFAULT_MODEL = "gpt-5-nano"
LABELS = {
    "first_cs_improvable": "escalation:first_cs_improvable",
    "authority_blocked": "escalation:authority_blocked",
    "mixed": "escalation:mixed",
    "unclear": "escalation:needs_human_review",
}

SYSTEM_PROMPT = """You classify Jira tickets that were already escalated.

Classify why the escalation happened, not whether the ticket was escalated.

Return one category:
- first_cs_improvable: future similar tickets can likely be handled by First-CS through better checking, investigation, or judgement.
- authority_blocked: escalation was unavoidable because the agent lacked required permission, role, or admin access.
- mixed: both First-CS improvement opportunities and permission blockers are present.
- unclear: there is not enough evidence to decide.

Use only the provided ticket content. Do not infer from external documents.
All output values except category, label, and confidence must be written in Japanese.
Write reason in Japanese, even if the ticket is written in Japanese, English, or Korean.
Write each evidence item as a short Japanese summary.
Do not copy English or Korean source sentences into evidence.
Translate or paraphrase the relevant ticket content into Japanese.
Keep the reason short and concrete.
Set label to one of:
- escalation:first_cs_improvable
- escalation:authority_blocked
- escalation:mixed
- escalation:needs_human_review
"""


def build_llm(model: str = DEFAULT_MODEL):
    load_dotenv()
    if not os.environ.get("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env before using --llm.")
    return ChatOpenAI(model=model).with_structured_output(AnalysisResult)


def normalize_result(result: AnalysisResult) -> AnalysisResult:
    return result.model_copy(update={"label": LABELS[result.category]})


def analyze_with_llm(
    state: TicketAnalysisState,
    *,
    model: str = DEFAULT_MODEL,
) -> dict[str, AnalysisResult]:
    ticket = state["ticket"]
    evidence = state.get("evidence", [])
    llm = build_llm(model)

    result = llm.invoke(
        [
            ("system", SYSTEM_PROMPT),
            (
                "user",
                "\n".join(
                    [
                        "Analyze this Jira ticket.",
                        "Return reason and evidence in Japanese.",
                        "Do not copy non-Japanese source sentences into evidence.",
                        "",
                        f"Ticket JSON:\n{ticket.model_dump_json(indent=2)}",
                        "",
                        "Evidence extracted by the graph:",
                        *[f"- {item}" for item in evidence],
                    ]
                ),
            ),
        ]
    )

    if not isinstance(result, AnalysisResult):
        result = AnalysisResult.model_validate(result)

    return {"result": normalize_result(result)}
