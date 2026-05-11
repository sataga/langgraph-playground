from __future__ import annotations

import argparse
import sys

from escalation_analysis.graph import build_graph
from escalation_analysis.io import load_ticket, print_json
from escalation_analysis.models import AnalysisResult, JiraTicket


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
            "Path to a UTF-8 JSON file containing one Jira ticket. "
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
    return parser.parse_args()


def main() -> None:
    configure_output_encoding()
    args = parse_args()
    ticket = load_ticket(args.input)

    if args.debug:
        result = run_with_debug(ticket, use_llm=args.llm, model=args.model)
    else:
        app = build_graph(use_llm=args.llm, model=args.model)
        final_state = app.invoke({"ticket": ticket})
        result = final_state["result"]

    print_json(result)


if __name__ == "__main__":
    main()
