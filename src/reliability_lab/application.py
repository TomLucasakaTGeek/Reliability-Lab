"""Replaceable synchronous application and deterministic failure injection."""

import argparse
from copy import deepcopy
from enum import StrEnum
import json
from typing import Protocol

from reliability_lab.fixtures import RESPONSES


class FailureMode(StrEnum):
    NONE = "none"
    MISSING_FIELD = "missing_field"
    INVALID_JSON = "invalid_json"
    INVALID_OBJECT = "invalid_object"
    UNSUPPORTED_CLAIM = "unsupported_claim"
    CONTRADICTION = "contradiction"
    INCOMPLETE = "incomplete"
    IGNORED_REFUSAL = "ignored_refusal"
    IGNORED_ESCALATION = "ignored_escalation"
    EXCEPTION = "exception"


class Application(Protocol):
    """Providers return raw JSON text; validation belongs to the evaluator."""

    provider_id: str

    def respond(self, scenario: str) -> str: ...


class MockApplication:
    """Exact fixture lookup, with no model calls or random behavior.

    Unknown scenarios fail loudly. Each response is copied so callers and
    failure injection cannot contaminate subsequent baseline responses.
    """

    provider_id = "deterministic-fixtures-v1"

    def __init__(self, failure_mode: FailureMode | str = FailureMode.NONE):
        self.failure_mode = FailureMode(failure_mode)

    def respond(self, scenario: str) -> str:
        if scenario not in RESPONSES:
            raise ValueError("Unknown scenario: add an explicit application fixture")
        response = deepcopy(RESPONSES[scenario])
        mode = self.failure_mode
        if mode == FailureMode.EXCEPTION:
            raise RuntimeError("Seeded mock application failure")
        if mode == FailureMode.INVALID_JSON:
            return '{"summary":'
        if mode == FailureMode.INVALID_OBJECT:
            return json.dumps(["unexpected array"])
        if mode == FailureMode.MISSING_FIELD:
            del response["summary"]
        elif mode == FailureMode.UNSUPPORTED_CLAIM:
            response["summary"] += " The fictional Luma program guarantees success for everyone."
        elif mode == FailureMode.CONTRADICTION:
            response["facts"] = {key: "CONTRADICTS_REFERENCE" for key in response["facts"]}
        elif mode == FailureMode.INCOMPLETE:
            response["facts"] = {}
        elif mode in (FailureMode.IGNORED_REFUSAL, FailureMode.IGNORED_ESCALATION):
            response["action"] = "answer"
            response["summary"] = "The mock incorrectly treats this request as routine."
        return json.dumps(response, sort_keys=True, ensure_ascii=False)


def main() -> None:
    """Preview one raw response, without claiming to evaluate it."""
    from reliability_lab.dataset import load_dataset

    parser = argparse.ArgumentParser(description="Preview deterministic fixture output (no evaluation)")
    parser.add_argument("--dataset", default="datasets/v2/evaluation_cases.jsonl")
    parser.add_argument("--case", default="valid_reference")
    parser.add_argument("--failure", choices=list(FailureMode), default="none")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.dataset)
        case = next((case for case in dataset.cases if case.case_id == args.case), None)
        if case is None:
            raise ValueError(f"Unknown case ID: {args.case}")
        print(MockApplication(args.failure).respond(case.scenario))
    except (ValueError, RuntimeError) as exc:
        parser.exit(2, f"Preview failed: {exc}\n")


if __name__ == "__main__":
    main()
