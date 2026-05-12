from __future__ import annotations

import argparse
import sys

from escalation_analysis.graph import build_graph
from escalation_analysis.io import load_tickets, print_json
from escalation_analysis.jira import apply_label
from escalation_analysis.models import (
    AnalysisResult,
    JiraLabelUpdateResult,
    JiraTicket,
)


def configure_output_encoding() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


def run_with_debug(
    ticket: JiraTicket,
    *,
    use_llm: bool = False,
    model: str = "gpt-5-nano",
) -> AnalysisResult:
    app = build_graph(use_llm=use_llm, model=model)
    result: AnalysisResult | None = None

    print("Node transitions:")
    for update in app.stream({"ticket": ticket}, stream_mode="updates"):
        for node_name, node_update in update.items():
            print(f"\n[{node_name}]")
            print_json(node_update)

            if "result" in node_update:
                result = node_update["result"]

    if result is None:
        raise RuntimeError("Graph finished without producing an analysis result.")

    print("\nFinal result:")
    return result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze a Jira escalation ticket with LangGraph."
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Print each LangGraph node update before the final result.",
    )
    parser.add_argument(
        "--input",
        help=(
            "Path to a UTF-8 JSON file containing one Jira ticket or a records array. "
            "Defaults to tickets/sample_escalated_vm_metadata_corruption.json."
        ),
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Use an OpenAI model to classify the ticket instead of local rules.",
    )
    parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="OpenAI model name used with --llm. Defaults to gpt-5-nano.",
    )
    parser.add_argument(
        "--apply-label",
        action="store_true",
        help="Add the classified label to the Jira ticket.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the Jira label update that would be performed without calling Jira.",
    )
    args = parser.parse_args()
    if args.dry_run and not args.apply_label:
        parser.error("--dry-run requires --apply-label.")
    return args


def main() -> None:
    configure_output_encoding()
    args = parse_args()
    tickets = load_tickets(args.input)
    results = [
        analyze_ticket(ticket, debug=args.debug, use_llm=args.llm, model=args.model)
        for ticket in tickets
    ]

    if args.apply_label:
        update_results = [
            {
                "analysis": result,
                "jira_label_update": apply_label(result, dry_run=args.dry_run),
            }
            for result in results
        ]
        print_json(one_or_many(update_results))
    else:
        print_json(one_or_many(results))


def analyze_ticket(
    ticket: JiraTicket,
    *,
    debug: bool,
    use_llm: bool,
    model: str,
) -> AnalysisResult:
    if debug:
        return run_with_debug(ticket, use_llm=use_llm, model=model)

    app = build_graph(use_llm=use_llm, model=model)
    final_state = app.invoke({"ticket": ticket})
    return final_state["result"]


def one_or_many(
    items: list[AnalysisResult]
    | list[dict[str, AnalysisResult | JiraLabelUpdateResult]],
) -> AnalysisResult | dict[str, AnalysisResult | JiraLabelUpdateResult] | list[object]:
    if len(items) == 1:
        return items[0]
    return items


if __name__ == "__main__":
    main()
