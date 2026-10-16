"""One command for baseline evaluation or the complete seeded demonstration."""

import argparse
from pathlib import Path
import sys
import webbrowser

from reliability_lab.application import FailureMode
from reliability_lab.runner import run


def main() -> int:
    parser = argparse.ArgumentParser(description="ReliabilityLab: run, trace, inspect, and replay")
    parser.add_argument("command", nargs="?", choices=["run", "demo", "watch"], default="run")
    parser.add_argument("--dataset", type=Path, default=Path(__file__).with_name("data") / "evaluation_cases.jsonl")
    parser.add_argument("--output", type=Path, default=Path("runs"))
    parser.add_argument("--case")
    parser.add_argument("--port", type=int, default=8765, help="Local dashboard port (watch)")
    parser.add_argument("--step-delay", type=float, default=0,
                        help="Optional 0–2 second presentation pause before each measured step")
    parser.add_argument("--failure", choices=list(FailureMode), default="none")
    parser.add_argument("--open", action="store_true", help="Open the saved visual report in your browser")
    args = parser.parse_args()
    if not 0 <= args.step_delay <= 2:
        parser.error("--step-delay must be between 0 and 2 seconds")
    if args.command == "watch":
        from reliability_lab.live import serve
        try:
            serve(args.output, args.port, open_browser=args.open)
        except (OSError, ValueError) as exc:
            print(f"Cannot start live dashboard ({type(exc).__name__}); check the port.", file=sys.stderr)
            return 2
        return 0
    if args.command == "demo" and (args.case or args.failure != "none"):
        parser.error("demo selects its own cases and faults; use run for custom failures")
    print("Running: load dataset -> application -> five checks -> summary" +
          (" -> regression experiment" if args.command == "demo" else "") + " -> save reports", flush=True)
    try:
        report, directory = run(args.dataset, args.output, case_id=args.case, failure=args.failure,
                                demo=args.command == "demo", regression=args.command == "demo",
                                step_delay=args.step_delay)
    except Exception as exc:
        print(f"Unable to finish saving run artifacts ({type(exc).__name__}). Check output permissions."
              " Partial traces may remain in the output directory.", file=sys.stderr)
        return 2
    summary = report["summary"]
    print(f"Run: {report['run_id']}\nDataset SHA-256: {report['dataset_hash']}")
    print(f"Cases: {summary['total_cases']} | Passed: {summary['passed_cases']} | "
          f"Failed: {summary['failed_cases']} | Critical failures: {summary['critical_failures']}")
    print(f"Failure categories: {summary['failure_categories']}")
    if report["error"]:
        print(report["error"]["message"], file=sys.stderr)
    if report["regression"]:
        print("Regression red/green/red verified:", report["regression"]["verified"])
    print(f"Visual report: {directory / 'report.html'}\nJSON report: {directory / 'report.json'}\n"
          f"Traces: {directory / 'traces.jsonl'}")
    if args.open:
        if not webbrowser.open((directory / "report.html").as_uri()):
            print("Browser did not open automatically; open the visual report path above.")
    return report["exit_code"]
