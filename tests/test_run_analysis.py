from copy import deepcopy
import json
from pathlib import Path

import pytest

from reliability_lab.run_analysis import aggregate, compare_runs, list_runs, read_run
from reliability_lab.runner import run

DATA = Path(__file__).resolve().parents[1] / "datasets/v2/evaluation_cases.jsonl"


def test_real_failure_fix_and_reintroduction(tmp_path):
    before, _ = run(DATA, tmp_path, case_id="refuse_diagnosis", failure="ignored_refusal")
    after, _ = run(DATA, tmp_path, case_id="refuse_diagnosis")
    reintroduced, _ = run(DATA, tmp_path, case_id="refuse_diagnosis", failure="ignored_refusal")
    result = compare_runs(read_run(tmp_path, before["run_id"]), read_run(tmp_path, after["run_id"]))
    assert result["recovered"] == ["refuse_diagnosis"]
    assert not result["newly_failing"] and not result["dataset_changed"]
    assert compare_runs(after, reintroduced)["newly_failing"] == ["refuse_diagnosis"]
    assert compare_runs(before, reintroduced)["unchanged_failures"] == ["refuse_diagnosis"]
    overview = aggregate(before)
    assert overview["evaluators"]["behavior"] == {"pass": 0, "fail": 1, "skipped": 0}
    assert overview["summary"]["critical_failures"] == 1
    assert len(list_runs(tmp_path)) == 3


def test_changed_or_missing_cases_are_not_fixes(tmp_path):
    before, _ = run(DATA, tmp_path, case_id="refuse_diagnosis", failure="ignored_refusal")
    after, _ = run(DATA, tmp_path)
    assert len(compare_runs(before, after)["added_cases"]) == 17
    changed = deepcopy(after)
    changed["dataset_hash"] = "different-content"
    next(c for c in changed["cases"] if c["case_id"] == "refuse_diagnosis")["expectations"]["action"] = "answer"
    result = compare_runs(before, changed)
    assert result["dataset_changed"]
    assert result["changed_cases"] == ["refuse_diagnosis"]
    assert result["recovered"] == []
    result = compare_runs(after, before)
    assert len(result["removed_cases"]) == 17


def test_invalid_missing_incomplete_and_inconsistent_artifacts(tmp_path):
    assert list_runs(tmp_path) == []
    with pytest.raises(ValueError):
        read_run(tmp_path, "../report.json")
    with pytest.raises(ValueError):
        read_run(tmp_path, "f" * 32)
    before, folder = run(DATA, tmp_path, case_id="valid_reference")
    after, _ = run(DATA, tmp_path, case_id="valid_reference")
    assert compare_runs(before, after)["unchanged_passes"] == ["valid_reference"]
    with pytest.raises(ValueError, match="different"):
        compare_runs(before, before)
    after["state"] = "running"
    with pytest.raises(ValueError, match="completed"):
        compare_runs(before, after)
    before["summary"]["total_cases"] = 99
    with pytest.raises(ValueError, match="totals"):
        aggregate(before)
    (folder / "report.json").write_text(json.dumps(before))
    assert next(c for c in list_runs(tmp_path) if c["run_id"] == before["run_id"])["state"] == "invalid"


def test_categories_count_cases_not_duplicate_checks(tmp_path):
    report, _ = run(DATA, tmp_path, case_id="refuse_diagnosis", failure="ignored_refusal")
    report["cases"][0]["checks"].append(deepcopy(report["cases"][0]["checks"][-1]))
    assert aggregate(report)["failure_categories"] == {"EXPECTED_BEHAVIOR_MISMATCH": 1}


def test_invalid_dataset_diagnostics_are_inspectable(tmp_path):
    dataset = tmp_path / "invalid.jsonl"
    dataset.write_text('{"invalid": true}\n')
    report, _ = run(dataset, tmp_path)
    saved = read_run(tmp_path, report["run_id"])
    assert saved["state"] == "error" and saved["error"]["type"] == "DatasetError"
    assert saved["overview"]["summary"]["total_cases"] == 0
    assert saved["dataset_hash"] is None
