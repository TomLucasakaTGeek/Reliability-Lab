import json
from pathlib import Path
import subprocess
import sys

import pytest

from reliability_lab.application import MockApplication
from reliability_lab.dataset import DatasetError, load_dataset
from reliability_lab.evaluators import evaluate, summarize

ROOT = Path(__file__).resolve().parents[1]
CASES = load_dataset(ROOT / "datasets/v2/evaluation_cases.jsonl").cases
BY_ID = {case.case_id: case for case in CASES}


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_all_baselines_pass_five_checks(case):
    checks = evaluate(case, MockApplication().respond(case.scenario))
    assert len(checks) == 5
    assert all(check.status == "pass" and check.code == "OK" for check in checks)
    assert all(check.case_id == case.case_id for check in checks)


@pytest.mark.parametrize("mode,case_id,code", [
    ("missing_field", "missing_summary", "MISSING_REQUIRED_FIELD"),
    ("invalid_json", "broken_json", "INVALID_JSON"),
    ("invalid_object", "array_output", "SCHEMA_INVALID"),
    ("unsupported_claim", "universal_success", "PROHIBITED_CLAIM"),
    ("contradiction", "wrong_color", "EXPECTED_BEHAVIOR_MISMATCH"),
    ("incomplete", "incomplete_contact", "EXPECTED_BEHAVIOR_MISMATCH"),
    ("ignored_refusal", "refuse_diagnosis", "EXPECTED_BEHAVIOR_MISMATCH"),
    ("ignored_escalation", "escalate_conflict", "EXPECTED_BEHAVIOR_MISMATCH"),
])
def test_seeded_failures_are_detected(mode, case_id, code):
    case = BY_ID[case_id]
    checks = evaluate(case, MockApplication(mode).respond(case.scenario))
    assert any(check.status == "fail" and check.code == code for check in checks)
    assert summarize([(case, checks)])["failed_cases"] == 1


@pytest.mark.parametrize("raw", ['{', 'null', '[]', '"text"', '{"x":NaN}', '{"x":1,"x":2}'])
def test_unusable_output_fails_and_skips_dependent_checks(raw):
    checks = evaluate(CASES[0], raw)
    assert checks[0].status == "fail"
    assert all(check.status == "skipped" for check in checks[1:])


@pytest.mark.parametrize("field,value,evaluator", [
    ("summary", 42, "schema"),
    ("summary", " ", "schema"),
    ("disclaimer", "Wrong disclaimer", "contract"),
    ("facts", {"booklet color": "blue", "invented": "claim"}, "behavior"),
    ("facts", {"booklet color": "green"}, "behavior"),
    ("facts", None, "behavior"),
    ("action", "refuse", "behavior"),
])
def test_independent_checks_on_changed_output(field, value, evaluator):
    output = json.loads(MockApplication().respond(CASES[0].scenario))
    output[field] = value
    checks = evaluate(CASES[0], json.dumps(output))
    assert next(check for check in checks if check.evaluator == evaluator).status == "fail"


def test_claim_check_scans_nested_text_and_normalizes_whitespace_and_case():
    output = json.loads(MockApplication().respond(CASES[0].scenario))
    output["extra"] = ["GUARANTEES   SUCCESS\nFOR EVERYONE"]
    checks = evaluate(CASES[0], json.dumps(output))
    assert next(check for check in checks if check.evaluator == "claims").code == "PROHIBITED_CLAIM"
    assert next(check for check in checks if check.evaluator == "schema").status == "fail"


def test_critical_failure_cannot_be_hidden_by_passing_cases():
    pairs = [(case, evaluate(case, MockApplication().respond(case.scenario))) for case in CASES]
    case = BY_ID["refuse_diagnosis"]
    pairs = [(c, evaluate(c, MockApplication("ignored_refusal").respond(c.scenario)))
             if c.case_id == case.case_id else (c, checks) for c, checks in pairs]
    summary = summarize(pairs)
    assert summary == {"total_cases": 18, "passed_cases": 17, "failed_cases": 1,
                       "critical_failures": 1,
                       "failure_categories": {"EXPECTED_BEHAVIOR_MISMATCH": 1}}


def test_no_checks_cannot_count_as_success():
    assert summarize([(CASES[0], [])])["failed_cases"] == 1


def test_expectations_required_before_evaluation(tmp_path):
    record = CASES[0].model_dump()
    del record["expectations"]
    path = tmp_path / "bad.jsonl"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(DatasetError, match="expectations: missing"):
        load_dataset(path)


@pytest.mark.parametrize("args,exit_code", [
    ([], 0),
    (["--case", "missing_summary", "--failure", "missing_field"], 1),
    (["--case", "valid_reference", "--failure", "exception"], 1),
    (["--case", "unknown"], 2),
    (["--dataset", "datasets/v1/evaluation_cases.jsonl"], 2),
])
def test_inspection_command_exit_codes(args, exit_code):
    proc = subprocess.run([sys.executable, "-m", "reliability_lab.evaluators", *args],
                          cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == exit_code, proc.stderr
    if exit_code != 2:
        payload = json.loads(proc.stdout)
        assert payload["summary"]["failed_cases"] == (0 if exit_code == 0 else 1)
        assert payload["dataset_hash"]
