import hashlib
import json
from pathlib import Path

import pytest

from reliability_lab.dataset import DatasetError, load_dataset

SAMPLE = Path(__file__).resolve().parents[1] / "datasets/v2/evaluation_cases.jsonl"


@pytest.fixture
def record():
    return json.loads(SAMPLE.read_text(encoding="utf-8").splitlines()[0])


def write_records(tmp_path, *records):
    path = tmp_path / "cases.jsonl"
    path.write_text("\n".join(json.dumps(record) for record in records) + "\n", encoding="utf-8")
    return path


def test_sample_loads_with_snapshot_metadata():
    dataset = load_dataset(SAMPLE)
    assert len(dataset.cases) == 18
    assert dataset.dataset_id == "fictional-care-v2"
    assert dataset.schema_version == "2.0"
    assert dataset.content_hash == hashlib.sha256(SAMPLE.read_bytes()).hexdigest()


@pytest.mark.parametrize("field,value,error", [
    ("schema_version", "3.0", "literal_error"),
    ("severity", "urgent", "literal_error"),
    ("category", "unknown", "literal_error"),
    ("scenario", "  ", "string_too_short"),
    ("scenario", 123, "string_type"),
    ("case_id", "Invalid ID", "string_pattern_mismatch"),
    ("criteria", [], "too_short"),
    ("criteria", [" "], "string_too_short"),
    ("surprise", "field", "extra_forbidden"),
])
def test_invalid_fields(tmp_path, record, field, value, error):
    record[field] = value
    with pytest.raises(DatasetError, match=rf"line 1: {field}.*{error}"):
        load_dataset(write_records(tmp_path, record))


def test_missing_field_reports_line_without_input(tmp_path, record):
    del record["expected_behavior"]
    record["scenario"] = "SENSITIVE_SENTINEL"
    with pytest.raises(DatasetError) as caught:
        load_dataset(write_records(tmp_path, record))
    assert "line 1: expected_behavior: missing" in str(caught.value)
    assert "SENSITIVE_SENTINEL" not in str(caught.value)


@pytest.mark.parametrize("content", ["", " \n", "{broken", "\n{}", "[]", "null", '{"case_id":"a","case_id":"b"}'])
def test_malformed_records(tmp_path, content):
    path = tmp_path / "bad.jsonl"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(DatasetError):
        load_dataset(path)


def test_duplicate_id_rejected(tmp_path, record):
    with pytest.raises(DatasetError, match="line 2: duplicate case_id"):
        load_dataset(write_records(tmp_path, record, record))


def test_mixed_dataset_ids_rejected(tmp_path, record):
    other = {**record, "case_id": "another", "dataset_id": "different"}
    with pytest.raises(DatasetError, match="line 2: dataset_id differs"):
        load_dataset(write_records(tmp_path, record, other))


def test_hash_is_stable_and_detects_byte_changes(tmp_path, record):
    path = write_records(tmp_path, record)
    original = load_dataset(path)
    assert original.content_hash == load_dataset(path).content_hash
    path.write_bytes(path.read_bytes().replace(b"blue", b"green"))
    assert original.content_hash != load_dataset(path).content_hash


def test_all_errors_reported_no_partial_dataset(tmp_path, record):
    path = write_records(tmp_path, record, {}, {})
    with pytest.raises(DatasetError) as caught:
        load_dataset(path)
    assert "line 2:" in str(caught.value)
    assert "line 3:" in str(caught.value)


def test_invalid_encoding(tmp_path):
    path = tmp_path / "bad.jsonl"
    path.write_bytes(b"\xff")
    with pytest.raises(DatasetError, match="expected UTF-8 at byte 0"):
        load_dataset(path)


def test_missing_file(tmp_path):
    with pytest.raises(DatasetError, match="cannot read dataset"):
        load_dataset(tmp_path / "missing.jsonl")
