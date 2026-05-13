from __future__ import annotations

import argparse
import sys

from escalation_analysis.graph import build_graph
from escalation_analysis.io import (
    load_analysis_results,
    load_tickets,
    print_json,
    write_json,
)
from escalation_analysis.jira import apply_label
from escalation_analysis.models import AnalysisResult, JiraLabelUpdateResult, JiraTicket


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

    read_parser = subparsers.add_parser(
        "read",
        help="Analyze Jira ticket JSON and write planned label updates to a file.",
    )
    read_parser.add_argument(
        "--input",
        help=(
            "Path to a UTF-8 JSON file containing one Jira ticket or a records array. "
            "Defaults to tickets/sample_escalated_vm_metadata_corruption.json."
        ),
    )
    read_parser.add_argument(
        "--output",
        required=True,
        help="Path to write analysis results used by the write command.",
    )
    read_parser.add_argument(
        "--debug",
        action="store_true",
        help="Print each LangGraph node update before writing results.",
    )
    read_parser.add_argument(
        "--llm",
        action="store_true",
        help="Use an OpenAI model to classify the ticket instead of local rules.",
    )
    read_parser.add_argument(
        "--model",
        default="gpt-5-nano",
        help="OpenAI model name used with --llm. Defaults to gpt-5-nano.",
    )

    write_parser = subparsers.add_parser(
        "write",
        help="Apply Jira labels from an analysis result JSON file.",
    )
    write_parser.add_argument(
        "--input",
        required=True,
        help="Path to a UTF-8 JSON file produced by the read command.",
    )

    return parser.parse_args()


def main() -> None:
    configure_output_encoding()
    args = parse_args()

    if args.command == "read":
        results = read_updates(args)
        write_json(results, args.output)
        print_json({"output": args.output, "planned_updates": results})
        return

    if args.command == "write":
        update_results = write_updates(args.input)
        print_json(update_results)
        return

    raise RuntimeError(f"Unsupported command: {args.command}")


def read_updates(args: argparse.Namespace) -> list[AnalysisResult]:
    tickets = load_tickets(args.input)
    return [
        analyze_ticket(ticket, debug=args.debug, use_llm=args.llm, model=args.model)
        for ticket in tickets
    ]


def write_updates(input_path: str) -> list[JiraLabelUpdateResult]:
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
