from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from escalation_analysis.graph import build_graph
from escalation_analysis.io import (
    load_analysis_results,
    load_tickets,
    print_json,
    write_json,
)
from escalation_analysis.jira import PROJECT_JQL, apply_label, fetch_tickets
from escalation_analysis.models import AnalysisResult, JiraLabelUpdateResult, JiraTicket


DEFAULT_JIRA_EXPORT_DIR = Path(__file__).resolve().parent / "jira_exports"
DEFAULT_ANALYSIS_RESULT_DIR = Path(__file__).resolve().parent / "analysis_results"
FILE_PREFIX = "escalation_analysis"
SAMPLE_INPUTS = {
    "vm_metadata_corruption": "samples/sample_escalated_vm_metadata_corruption.json",
    "first_cs_rebuild_missed": "samples/sample_escalated_first_cs_rebuild_missed.json",
    "batch": "samples/sample_escalated_batch.json",
}


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

    print(f"Node transitions for {ticket.key}:")
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
        description="Analyze Jira escalation tickets and apply planned labels."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    fetch_parser = subparsers.add_parser(
        "fetch",
        help="Fetch Jira tickets with predefined JQL and write input JSON.",
    )
    fetch_parser.add_argument(
        "--project",
        choices=[*PROJECT_JQL.keys(), "all"],
        required=True,
        help="Predefined project JQL to fetch. Use all to fetch every project.",
    )
    fetch_parser.add_argument(
        "--max-results",
        type=int,
        default=100,
        help="Maximum number of tickets to fetch. Defaults to 100.",
    )
    fetch_parser.add_argument(
        "--output",
        help=(
            "Path to write fetched ticket JSON. "
            "Defaults to jira_exports/escalation_analysis_YYYYMMDD_HHMMSS.json."
        ),
    )

    analysis_parser = subparsers.add_parser(
        "analysis",
        help="Analyze Jira ticket JSON and write planned label updates to a file.",
    )
    analysis_input_group = analysis_parser.add_mutually_exclusive_group()
    analysis_input_group.add_argument(
        "--input",
        help=(
            "Path to a UTF-8 JSON file containing one Jira ticket or a records array. "
            "Defaults to samples/sample_escalated_vm_metadata_corruption.json."
        ),
    )
    analysis_input_group.add_argument(
        "--sample",
        choices=list(SAMPLE_INPUTS),
        help="Built-in sample JSON to analyze.",
    )
    analysis_parser.add_argument(
        "--output",
        help=(
            "Path to write analysis results used by the apply command. "
            "Defaults to analysis_results/escalation_analysis_YYYYMMDD_HHMMSS.json."
        ),
    )
    analysis_parser.add_argument(
        "--debug",
        action="store_true",
        help="Print each LangGraph node update before writing results.",
    )
    analysis_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use an OpenAI model to classify the ticket instead of local rules.",
    )
    analysis_parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="OpenAI model name used with --llm. Defaults to gpt-5-nano.",
    )

    apply_parser = subparsers.add_parser(
        "apply",
        help="Apply Jira labels from an analysis result JSON file.",
    )
    apply_parser.add_argument(
        "--input",
        required=True,
        help="Path to a UTF-8 JSON file produced by the analysis command.",
    )

    args = parser.parse_args()
    if args.command == "fetch" and args.max_results < 1:
        parser.error("fetch --max-results must be greater than 0.")
    return args


def main() -> None:
    configure_output_encoding()
    args = parse_args()

    if args.command == "fetch":
        tickets = fetch_tickets(args.project, max_results=args.max_results)
        output_path = resolve_jira_export_path(args.output)
        payload = {
            "metadata": {
                "source": "jira",
                "analysis": FILE_PREFIX,
                "project": args.project,
                "record_count": len(tickets),
            },
            "records": tickets,
        }
        write_json(payload, output_path)
        print_json({"output": str(output_path), **payload})
        return

    if args.command == "analysis":
        results = analyze_updates(args)
        output_path = resolve_output_path(args.output)
        write_json(results, output_path)
        print_json({"output": str(output_path), "planned_updates": results})
        return

    if args.command == "apply":
        update_results = apply_updates(args.input)
        print_json(update_results)
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


def analyze_updates(args: argparse.Namespace) -> list[AnalysisResult]:
    input_path = SAMPLE_INPUTS[args.sample] if args.sample else args.input
    tickets = load_tickets(input_path)
    return [
        analyze_ticket(ticket, debug=args.debug, use_llm=args.llm, model=args.model)
        for ticket in tickets
    ]


def resolve_output_path(output_path: str | None) -> Path:
    if output_path:
        return Path(output_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_ANALYSIS_RESULT_DIR / f"{FILE_PREFIX}_{timestamp}.json"


def resolve_jira_export_path(output_path: str | None) -> Path:
    if output_path:
        return Path(output_path)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return DEFAULT_JIRA_EXPORT_DIR / f"{FILE_PREFIX}_{timestamp}.json"


def apply_updates(input_path: str) -> list[JiraLabelUpdateResult]:
    results = load_analysis_results(input_path)
    return [apply_label(result) for result in results]


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


if __name__ == "__main__":
    main()
