"""Validate a JSONL snapshot completely before exposing any cases."""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from pydantic import ValidationError

from reliability_lab.models import EvaluationCase


class DatasetError(ValueError):
    """The dataset cannot safely be used for evaluation."""


@dataclass(frozen=True)
class Dataset:
    dataset_id: str
    schema_version: str
    content_hash: str
    cases: tuple[EvaluationCase, ...]


def _unique_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON object key")
        result[key] = value
    return result


def load_dataset(path: str | Path) -> Dataset:
    """Read once, hash exact bytes, and reject the whole snapshot on any error.

    Blank lines are forbidden. Diagnostics omit record values so malformed
    input does not accidentally get copied into logs. No historical storage
    or semantic equivalence is implied by the byte-level hash.
    """
    source = Path(path)
    try:
        raw = source.read_bytes()
    except OSError as exc:
        raise DatasetError(f"{source}: cannot read dataset ({type(exc).__name__})") from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise DatasetError(f"{source}: expected UTF-8 at byte {exc.start}") from exc
    if not text.strip():
        raise DatasetError(f"{source}: dataset is empty")

    cases: list[EvaluationCase] = []
    seen: set[str] = set()
    issues: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        location = f"{source}: line {line_number}"
        try:
            record = json.loads(line, object_pairs_hook=_unique_keys)
        except (ValueError, RecursionError) as exc:
            issues.append(f"{location}: invalid JSON ({type(exc).__name__})")
            continue
        try:
            case = EvaluationCase.model_validate(record)
        except ValidationError as exc:
            for error in exc.errors(include_input=False, include_url=False):
                field = ".".join(str(part) for part in error["loc"]) or "record"
                issues.append(f"{location}: {field}: {error['type']}")
            continue
        if case.case_id in seen:
            issues.append(f"{location}: duplicate case_id")
        seen.add(case.case_id)
        if cases and case.dataset_id != cases[0].dataset_id:
            issues.append(f"{location}: dataset_id differs from first valid record")
        cases.append(case)
    if issues:
        raise DatasetError("Dataset validation failed:\n" + "\n".join(issues))
    return Dataset(
        dataset_id=cases[0].dataset_id,
        schema_version=cases[0].schema_version,
        content_hash=hashlib.sha256(raw).hexdigest(),
        cases=tuple(cases),
    )
