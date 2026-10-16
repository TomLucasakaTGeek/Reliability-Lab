"""Synchronous evaluation orchestration with durable traces and unique runs."""

from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from reliability_lab.application import Application, MockApplication
from reliability_lab.dataset import DatasetError, load_dataset
from reliability_lab.evaluators import CheckResult, evaluate, summarize
from reliability_lab.regression import demonstrate
from reliability_lab.reporting import save_reports, save_snapshot
from reliability_lab.tracing import TraceWriter, utc_now

DEMO_FAILURES = {
    "missing_summary": "missing_field", "broken_json": "invalid_json",
    "array_output": "invalid_object", "universal_success": "unsupported_claim",
    "wrong_color": "contradiction", "incomplete_contact": "incomplete",
    "refuse_diagnosis": "ignored_refusal", "escalate_conflict": "ignored_escalation",
}


def run(dataset_path: Path, output_root: Path, *, application: Application | None = None,
        case_id: str | None = None, failure: str = "none", demo: bool = False,
        regression: bool = False, step_delay: float = 0) -> tuple[dict, Path]:
    if not 0 <= step_delay <= 2:
        raise ValueError("step_delay must be between 0 and 2 seconds")
    run_id = uuid4().hex
    directory = output_root.resolve() / run_id
    directory.mkdir(parents=True, exist_ok=False)
    app = application or MockApplication(failure)
    report = {"report_version": "1.0", "run_id": run_id, "started_at": utc_now(),
              "provider_id": app.provider_id, "mode": "demo" if demo else "evaluation",
              "dataset_id": None, "dataset_hash": None, "schema_version": None,
              "cases": [], "summary": summarize([]), "error": None, "regression": None,
              "state": "running", "selected_count": None, "step_delay": step_delay,
              "artifacts_saved": False,
              "artifacts": {"json": "report.json", "html": "report.html", "trace": "traces.jsonl"}}
    pairs = []
    def publish(active: dict | None = None) -> None:
        save_snapshot(directory, {**report, "updated_at": utc_now(), "active": active,
                                  "trace": trace.events})

    trace = TraceWriter(directory / "traces.jsonl", run_id, app.provider_id,
                        on_update=publish, step_delay=step_delay)
    publish()
    try:
        with trace.step("load_dataset") as span:
            dataset = load_dataset(dataset_path)
            trace.dataset_hash = dataset.content_hash
            trace.dataset_id = dataset.dataset_id
            trace.schema_version = dataset.schema_version
            report.update(dataset_hash=dataset.content_hash, dataset_id=dataset.dataset_id,
                          schema_version=dataset.schema_version)
            span["record_count"] = len(dataset.cases)
        with trace.step("select_cases") as span:
            selected = [case for case in dataset.cases if case_id is None or case.case_id == case_id]
            if not selected:
                raise ValueError("No matching case ID")
            span["selected_count"] = len(selected)
            report["selected_count"] = len(selected)
        for case in selected:
            raw = None
            mode = DEMO_FAILURES.get(case.case_id, "none") if demo else failure
            provider = MockApplication(mode) if demo else app
            case_record = {"case_id": case.case_id, "category": case.category,
                           "severity": case.severity, "scenario": case.scenario,
                           "expectations": case.expectations.model_dump(), "raw_output": None,
                           "failure_mode": mode, "passed": None, "checks": []}
            report["cases"].append(case_record)
            try:
                with trace.step("application", case.case_id) as span:
                    span["failure_mode"] = mode
                    raw = provider.respond(case.scenario)
                    case_record["raw_output"] = raw
            except Exception as exc:
                checks = [CheckResult(case.case_id, "application", "fail", "APPLICATION_ERROR",
                                      "Application failed; see trace error type.", {"error_type": type(exc).__name__})]
            else:
                def observe(name, operation):
                    with trace.step(name, case.case_id) as span:
                        check = operation()
                        span["status"] = check.status
                        span["result"] = asdict(check)
                        case_record["checks"].append(asdict(check))
                        return check
                try:
                    checks = evaluate(case, raw, observe)
                except Exception as exc:
                    checks = [CheckResult(case.case_id, "engine", "fail", "EVALUATOR_ERROR",
                                          "Evaluator raised an exception; see trace.",
                                          {"error_type": type(exc).__name__})]
            pairs.append((case, checks))
            case_record.update(passed=all(c.status == "pass" for c in checks),
                               checks=[asdict(c) for c in checks])
            report["summary"] = summarize(pairs)
            publish()
        with trace.step("summarize") as span:
            report["summary"] = summarize(pairs)
            span["summary"] = report["summary"]
        if regression:
            with trace.step("regression_demo") as span:
                report["regression"] = demonstrate(directory / "regression")
                span["status"] = "pass" if report["regression"]["verified"] else "fail"
                span["phases"] = report["regression"]["phases"]
    except (DatasetError, ValueError) as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc) if isinstance(exc, DatasetError)
                           else "Invalid run configuration."}
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": "Run failed; exception text omitted. See traces."}
    report["exit_code"] = (2 if report["error"] else
                           1 if report["summary"]["failed_cases"] or
                           (report["regression"] and not report["regression"]["verified"]) else 0)
    report["ended_at"] = utc_now()
    # Persist after spans finish so the report embeds their measured durations.
    # Artifact writing is deliberately not self-referential: it is not a timed span.
    report["trace"] = trace.events
    report["state"] = "saving"
    publish()
    report["state"] = "error" if report["error"] else "completed"
    try:
        report["artifacts_saved"] = True
        save_reports(directory, report)
    except Exception as exc:
        report.update(state="error", exit_code=2, artifacts_saved=False,
                      error={"type": type(exc).__name__, "message": "Unable to save final reports."})
        publish()
        raise
    publish()
    return report, directory
