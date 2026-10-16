"""UI-independent inspection and comparison of actual runner artifacts."""

from collections import Counter
import json
from pathlib import Path
import re


def aggregate(report: dict) -> dict:
    """Count completed records; in-flight evaluator observations stay separate."""
    cases = report["cases"]
    ids = [c["case_id"] for c in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate case IDs in artifact")
    done = [c for c in cases if c["passed"] is not None]
    categories = Counter()
    evaluators = {}
    for case in cases:
        if case["passed"] is not None:
            if type(case["passed"]) is not bool or not case["checks"]:
                raise ValueError("Invalid completed case")
            if case["passed"] != all(c["status"] == "pass" for c in case["checks"]):
                raise ValueError("Case outcome disagrees with evaluator records")
            categories.update({c["code"] for c in case["checks"] if c["status"] == "fail"})
        for check in case["checks"]:
            counts = evaluators.setdefault(check["evaluator"], {"pass": 0, "fail": 0, "skipped": 0})
            if check["status"] not in counts:
                raise ValueError("Unknown evaluator status")
            counts[check["status"]] += 1
    summary = {"total_cases": len(done), "passed_cases": sum(c["passed"] for c in done),
               "failed_cases": sum(not c["passed"] for c in done),
               "critical_failures": sum(not c["passed"] and c["severity"] == "critical" for c in done),
               "failure_categories": dict(categories)}
    if summary != report["summary"]:
        raise ValueError("Reported totals disagree with evaluation records")
    return {"summary": summary, "evaluators": evaluators, "failure_categories": dict(categories)}


def read_run(root: Path, run_id: str) -> dict:
    if not re.fullmatch(r"[0-9a-f]{32}", run_id):
        raise ValueError("Invalid run identifier")
    folder = root / run_id
    path = folder / "report.json"
    if not path.exists():
        path = folder / "live.json"
    if folder.is_symlink() or path.is_symlink():
        raise ValueError("Linked artifacts are not supported")
    try:
        report = json.loads(path.read_text(encoding="utf-8"))
        if report["run_id"] != run_id or not isinstance(report["trace"], list):
            raise ValueError("Artifact identity or trace is invalid")
        report["overview"] = aggregate(report)
        report.setdefault("state", "unknown")
        report.setdefault("updated_at", report.get("ended_at", report["started_at"]))
        return report
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Run artifact unavailable or invalid: {run_id}") from exc


def list_runs(root: Path) -> list[dict]:
    entries = []
    for folder in root.iterdir():
        if not re.fullmatch(r"[0-9a-f]{32}", folder.name) or not folder.is_dir():
            continue
        try:
            report = read_run(root, folder.name)
            entries.append({key: report.get(key) for key in
                            ("run_id", "started_at", "state", "dataset_id", "dataset_hash", "summary")})
        except ValueError as exc:
            entries.append({"run_id": folder.name, "state": "invalid", "error": str(exc)})
    return sorted(entries, key=lambda item: item.get("started_at") or "", reverse=True)


def compare_runs(before: dict, after: dict) -> dict:
    for report in (before, after):
        aggregate(report)
        if report.get("state") != "completed" or report.get("error") or any(c["passed"] is None for c in report["cases"]):
            raise ValueError("Comparison requires two completed runs without run-level errors")
    if before["run_id"] == after["run_id"]:
        raise ValueError("Choose two different runs")
    left = {c["case_id"]: c for c in before["cases"]}
    right = {c["case_id"]: c for c in after["cases"]}
    result = {key: [] for key in ("newly_failing", "recovered", "unchanged_failures", "unchanged_passes", "changed_cases")}
    for case_id in sorted(left.keys() & right.keys()):
        a, b = left[case_id], right[case_id]
        fields = ("scenario", "expectations", "severity", "category")
        if (before.get("schema_version") != after.get("schema_version") or
                before.get("provider_id") != after.get("provider_id") or
                any(a.get(key) != b.get(key) for key in fields)):
            result["changed_cases"].append(case_id)
            continue
        key = ("unchanged_passes" if b["passed"] else "newly_failing") if a["passed"] else (
            "recovered" if b["passed"] else "unchanged_failures")
        result[key].append(case_id)
    result.update(before=before["run_id"], after=after["run_id"],
                  dataset_changed=before["dataset_hash"] != after["dataset_hash"],
                  added_cases=sorted(right.keys() - left.keys()), removed_cases=sorted(left.keys() - right.keys()))
    return result
