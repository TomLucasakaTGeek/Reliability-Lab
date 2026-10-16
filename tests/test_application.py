import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from reliability_lab.application import FailureMode, MockApplication
from reliability_lab.dataset import load_dataset
from reliability_lab.models import AssistantResponse

DATASET = load_dataset(Path(__file__).resolve().parents[1] / "datasets/v2/evaluation_cases.jsonl")
CASES = {case.case_id: case for case in DATASET.cases}


@pytest.mark.parametrize("case", DATASET.cases, ids=lambda case: case.case_id)
def test_baseline_structure_actions_and_reproducibility(case):
    app = MockApplication()
    raw = app.respond(case.scenario)
    output = AssistantResponse.model_validate_json(raw)
    expected_action = {"refusal": "refuse", "escalation": "escalate"}.get(case.category, "answer")
    assert output.action == expected_action
    assert output.facts
    assert output.disclaimer == "Synthetic information only; not medical advice."
    assert raw == app.respond(case.scenario) == MockApplication().respond(case.scenario)


def test_reference_fact_is_preserved():
    output = json.loads(MockApplication().respond(CASES["valid_reference"].scenario))
    assert output["facts"] == {"booklet color": "blue"}


@pytest.mark.parametrize("mode", ["missing_field", "invalid_json", "invalid_object"])
def test_malformed_outputs_violate_schema(mode):
    raw = MockApplication(mode).respond(CASES["valid_reference"].scenario)
    with pytest.raises(ValidationError):
        AssistantResponse.model_validate_json(raw)
    if mode == "missing_field":
        assert "summary" not in json.loads(raw)
    elif mode == "invalid_json":
        with pytest.raises(json.JSONDecodeError):
            json.loads(raw)
    else:
        assert isinstance(json.loads(raw), list)


@pytest.mark.parametrize("mode", [mode for mode in FailureMode if mode != FailureMode.EXCEPTION])
def test_failure_modes_are_reproducible_and_do_not_contaminate_baseline(mode):
    scenario = CASES["valid_reference"].scenario
    baseline = MockApplication().respond(scenario)
    app = MockApplication(mode)
    assert app.respond(scenario) == app.respond(scenario)
    assert MockApplication().respond(scenario) == baseline


@pytest.mark.parametrize("mode,case_id,field,expected", [
    ("contradiction", "wrong_color", "facts", {"folder color": "CONTRADICTS_REFERENCE"}),
    ("incomplete", "incomplete_contact", "facts", {}),
    ("ignored_refusal", "refuse_personal_advice", "action", "answer"),
    ("ignored_escalation", "escalate_conflict", "action", "answer"),
])
def test_semantic_failures_can_still_pass_structural_validation(mode, case_id, field, expected):
    raw = MockApplication(mode).respond(CASES[case_id].scenario)
    AssistantResponse.model_validate_json(raw)
    assert json.loads(raw)[field] == expected
    assert json.loads(MockApplication().respond(CASES[case_id].scenario))[field] != expected


def test_unsupported_claim_is_injected():
    raw = MockApplication("unsupported_claim").respond(CASES["universal_success"].scenario)
    assert "guarantees success for everyone" in json.loads(raw)["summary"]


def test_exception_is_reproducible():
    for _ in range(2):
        with pytest.raises(RuntimeError, match="Seeded mock application failure"):
            MockApplication("exception").respond(CASES["valid_reference"].scenario)


def test_unknown_scenario_is_not_silently_accepted():
    with pytest.raises(ValueError, match="Unknown scenario"):
        MockApplication().respond("unconfigured scenario")


def test_invalid_failure_mode_rejected():
    with pytest.raises(ValueError):
        MockApplication("typo")


def test_all_planned_categories_present():
    assert {case.category for case in DATASET.cases} == {
        "well_formed", "missing_fields", "invalid_output", "unsupported_claim",
        "contradiction", "incomplete", "refusal", "escalation",
    }
