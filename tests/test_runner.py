import json
from pathlib import Path
import subprocess
import sys

import pytest

from reliability_lab import runner

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets/v2/evaluation_cases.jsonl"


def test_run_creates_truthful_reports_and_case_linked_spans(tmp_path):
    report, directory = runner.run(DATA, tmp_path)
    assert report["exit_code"] == 0
    assert report["summary"]["passed_cases"] == 18
    assert json.loads((directory / "report.json").read_text(encoding="utf-8")) == report
    assert (directory / "report.html").exists()
    trace = [json.loads(line) for line in (directory / "traces.jsonl").read_text().splitlines()]
    assert trace == report["trace"]
    assert len({e["span_id"] for e in trace}) == len(trace)
    assert all(e["run_id"] == report["run_id"] and e["dataset_hash"] == report["dataset_hash"] for e in trace)
    case_events = [e for e in trace if e["case_id"] == "valid_reference"]
    assert [e["step"] for e in case_events] == ["application", "schema", "required_fields", "contract", "claims", "behavior"]
    assert all(e["duration_ms"] >= 0 and e["ended_at"] >= e["started_at"] for e in trace)
    assert all("token_usage" not in e for e in trace)


def test_failed_check_links_to_trace_and_critical_summary(tmp_path):
    report, _ = runner.run(DATA, tmp_path, case_id="refuse_diagnosis", failure="ignored_refusal")
    assert report["exit_code"] == 1
    assert report["summary"]["critical_failures"] == 1
    failed = [event for event in report["trace"] if event["status"] == "fail"]
    assert len(failed) == 1
    assert failed[0]["case_id"] == "refuse_diagnosis"
    assert failed[0]["result"]["code"] == "EXPECTED_BEHAVIOR_MISMATCH"


def test_provider_exception_is_recorded_without_secret_message(tmp_path):
    class Broken:
        provider_id = "test-provider"

        def respond(self, scenario):
            raise RuntimeError("SECRET_TOKEN_DO_NOT_RECORD")

    report, directory = runner.run(DATA, tmp_path, application=Broken(), case_id="valid_reference")
    assert report["exit_code"] == 1
    event = next(e for e in report["trace"] if e["step"] == "application")
    assert event["status"] == "error"
    assert event["error_type"] == "RuntimeError"
    assert "SECRET_TOKEN" not in (directory / "report.json").read_text()
    assert "SECRET_TOKEN" not in (directory / "traces.jsonl").read_text()


def test_invalid_dataset_produces_error_report_and_trace(tmp_path):
    data = tmp_path / "invalid.jsonl"
    data.write_text('{"scenario":"PRIVATE_VALUE"}', encoding="utf-8")
    report, directory = runner.run(data, tmp_path / "runs")
    assert report["exit_code"] == 2
    assert report["summary"]["total_cases"] == 0
    assert "line 1" in report["error"]["message"]
    assert report["trace"][0]["step"] == "load_dataset"
    assert report["trace"][0]["status"] == "error"
    assert "PRIVATE_VALUE" not in (directory / "report.json").read_text()


def test_evaluator_crash_fails_case(tmp_path, monkeypatch):
    def broken(*args):
        raise RuntimeError("private evaluator message")
    monkeypatch.setattr("reliability_lab.evaluators.behavior_check", broken)
    report, _ = runner.run(DATA, tmp_path, case_id="valid_reference")
    assert report["exit_code"] == 1
    assert report["cases"][0]["checks"][0]["code"] == "EVALUATOR_ERROR"
    assert any(e["step"] == "behavior" and e["status"] == "error" for e in report["trace"])


def test_runs_never_overwrite_prior_artifacts(tmp_path):
    first, first_dir = runner.run(DATA, tmp_path, case_id="valid_reference")
    original = (first_dir / "report.json").read_bytes()
    second, second_dir = runner.run(DATA, tmp_path, case_id="valid_reference")
    assert first["run_id"] != second["run_id"]
    assert first_dir != second_dir
    assert (first_dir / "report.json").read_bytes() == original


@pytest.mark.parametrize("arguments,code", [
    (["--case", "valid_reference"], 0),
    (["--case", "missing_summary", "--failure", "missing_field"], 1),
    (["--case", "unknown"], 2),
])
def test_unified_cli_from_another_directory(tmp_path, arguments, code):
    process = subprocess.run([sys.executable, "-m", "reliability_lab", "run", "--output",
                              str(tmp_path / "runs"), *arguments], cwd=tmp_path,
                             capture_output=True, text=True)
    assert process.returncode == code, process.stderr
    assert "Visual report:" in process.stdout


def test_artifact_write_error_is_not_reported_as_success(tmp_path):
    output = tmp_path / "file"
    output.write_text("not a directory")
    process = subprocess.run([sys.executable, "-m", "reliability_lab", "--output", str(output)],
                             capture_output=True, text=True)
    assert process.returncode == 2
    assert "Unable to finish saving" in process.stderr
    assert "Visual report:" not in process.stdout


def test_packaged_dataset_matches_editable_source():
    assert DATA.read_bytes() == (ROOT / "src/reliability_lab/data/evaluation_cases.jsonl").read_bytes()
