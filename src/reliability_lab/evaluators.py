"""Independent deterministic checks; no model judging or aggregate scores."""

from dataclasses import asdict, dataclass
from collections.abc import Callable, Iterator
import json
from typing import Literal

from pydantic import ValidationError

from reliability_lab.models import AssistantResponse, EvaluationCase


@dataclass(frozen=True)
class CheckResult:
    case_id: str
    evaluator: str
    status: Literal["pass", "fail", "skipped"]
    code: str
    explanation: str
    evidence: object = None


def result(case: EvaluationCase, evaluator: str, passed: bool, code: str,
           explanation: str, evidence: object = None) -> CheckResult:
    return CheckResult(case.case_id, evaluator, "pass" if passed else "fail",
                       "OK" if passed else code, explanation, evidence)


def schema_check(case: EvaluationCase, value: object) -> CheckResult:
    try:
        AssistantResponse.model_validate(value)
    except ValidationError as exc:
        evidence = [{"field": list(e["loc"]), "type": e["type"]}
                    for e in exc.errors(include_input=False, include_url=False)]
        return result(case, "schema", False, "SCHEMA_INVALID", "Output violates the response schema.", evidence)
    return result(case, "schema", True, "", "Output matches the response schema.")


def required_fields_check(case: EvaluationCase, value: dict) -> CheckResult:
    missing = sorted(set(AssistantResponse.model_fields) - value.keys())
    return result(case, "required_fields", not missing, "MISSING_REQUIRED_FIELD",
                  "All required keys must be present.", missing)


def contract_check(case: EvaluationCase, value: dict) -> CheckResult:
    actual = value.get("disclaimer")
    return result(case, "contract", actual == case.expectations.disclaimer,
                  "DISCLAIMER_MISMATCH", "Disclaimer must match the explicit output contract.",
                  {"expected": case.expectations.disclaimer, "actual": actual})


def _strings(value: object) -> Iterator[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _strings(item)


def claims_check(case: EvaluationCase, value: dict) -> CheckResult:
    texts = [" ".join(text.casefold().split()) for text in _strings(value)]
    matches = [phrase for phrase in case.expectations.prohibited_phrases
               if any(" ".join(phrase.casefold().split()) in text for text in texts)]
    return result(case, "claims", not matches, "PROHIBITED_CLAIM",
                  "No configured prohibited phrase may appear in output text.", matches)


def behavior_check(case: EvaluationCase, value: dict) -> CheckResult:
    expected = case.expectations
    issues = {}
    if value.get("action") != expected.action:
        issues["action"] = {"expected": expected.action, "actual": value.get("action")}
    facts = value.get("facts")
    if facts != expected.facts:
        issues["facts"] = {"expected": expected.facts, "actual": facts}
    return result(case, "behavior", not issues, "EXPECTED_BEHAVIOR_MISMATCH",
                  "Action and complete facts object must exactly match the reference.", issues)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate JSON key")
        value[key] = item
    return value


def _reject_constant(value: str) -> None:
    raise ValueError("Nonstandard JSON constant")


def evaluate(case: EvaluationCase, raw: str,
             observe: Callable[[str, Callable[[], CheckResult]], CheckResult] | None = None
             ) -> list[CheckResult]:
    """Parse once; invalid prerequisites produce explicit skipped checks."""
    value = None

    def schema() -> CheckResult:
        nonlocal value
        try:
            value = json.loads(raw, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        except (ValueError, TypeError, RecursionError):
            return result(case, "schema", False, "INVALID_JSON", "Response must be strict JSON with unique keys.")
        return schema_check(case, value)

    invoke = observe or (lambda name, operation: operation())
    results = [invoke("schema", schema)]
    for name, check in [("required_fields", required_fields_check), ("contract", contract_check),
                        ("claims", claims_check), ("behavior", behavior_check)]:
        def operation(check=check, name=name) -> CheckResult:
            if not isinstance(value, dict):
                return CheckResult(case.case_id, name, "skipped", "PREREQUISITE_FAILED",
                                   "Check requires a parsed JSON object.")
            return check(case, value)
        results.append(invoke(name, operation))
    return results


def summarize(cases: list[tuple[EvaluationCase, list[CheckResult]]]) -> dict:
    """Every check must pass; any skipped check also prevents a passing case."""
    failed = critical = 0
    categories: dict[str, int] = {}
    for case, checks in cases:
        passed = bool(checks) and all(check.status == "pass" for check in checks)
        failed += not passed
        critical += not passed and case.severity == "critical"
        for code in {check.code for check in checks if check.status == "fail"}:
            categories[code] = categories.get(code, 0) + 1
    return {"total_cases": len(cases), "passed_cases": len(cases) - failed,
            "failed_cases": failed, "critical_failures": critical,
            "failure_categories": categories}


def main() -> None:
    import argparse
    from reliability_lab.application import FailureMode, MockApplication
    from reliability_lab.dataset import DatasetError, load_dataset

    parser = argparse.ArgumentParser(description="Inspect deterministic checks (no saved report or traces)")
    parser.add_argument("--dataset", default="datasets/v2/evaluation_cases.jsonl")
    parser.add_argument("--case", help="Only evaluate this case ID")
    parser.add_argument("--failure", choices=list(FailureMode), default="none")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.dataset)
    except DatasetError as exc:
        parser.exit(2, f"{exc}\n")
    cases = [case for case in dataset.cases if not args.case or case.case_id == args.case]
    if not cases:
        parser.exit(2, "No matching cases.\n")
    app = MockApplication(args.failure)
    evaluated = []
    for case in cases:
        try:
            raw = app.respond(case.scenario)
        except Exception as exc:
            checks = [CheckResult(case.case_id, "application", "fail", "APPLICATION_ERROR",
                                  "Application execution failed.", {"error_type": type(exc).__name__})]
        else:
            checks = evaluate(case, raw)
        evaluated.append((case, checks))
    summary = summarize(evaluated)
    print(json.dumps({"dataset_id": dataset.dataset_id, "dataset_hash": dataset.content_hash,
                      "schema_version": dataset.schema_version, "provider_id": app.provider_id,
                      "summary": summary,
                      "checks": [asdict(check) for _, checks in evaluated for check in checks]}, indent=2))
    raise SystemExit(1 if summary["failed_cases"] else 0)


if __name__ == "__main__":
    main()
