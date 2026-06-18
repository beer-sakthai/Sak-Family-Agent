import json
import io
import csv
from sakthai.memory.store import snapshot_to_jsonl, snapshot_to_csv, CSV_COLUMNS

def test_snapshot_to_jsonl_empty():
    assert snapshot_to_jsonl({}) == ""
    assert snapshot_to_jsonl({"facts": [], "observations": []}) == ""

def test_snapshot_to_jsonl_facts_only():
    snapshot = {
        "facts": [
            {"id": 1, "value": "fact 1"},
            {"id": 2, "value": "fact 2"}
        ]
    }
    result = snapshot_to_jsonl(snapshot)
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0]) == {"type": "fact", "id": 1, "value": "fact 1"}
    assert json.loads(lines[1]) == {"type": "fact", "id": 2, "value": "fact 2"}
    assert result.endswith("\n")

def test_snapshot_to_jsonl_observations_only():
    snapshot = {
        "observations": [
            {"id": 101, "summary": "obs 1"},
        ]
    }
    result = snapshot_to_jsonl(snapshot)
    lines = result.strip().split("\n")
    assert len(lines) == 1
    assert json.loads(lines[0]) == {"type": "observation", "id": 101, "summary": "obs 1"}

def test_snapshot_to_jsonl_mixed():
    snapshot = {
        "facts": [{"id": 1, "value": "f1"}],
        "observations": [{"id": 101, "summary": "o1"}]
    }
    result = snapshot_to_jsonl(snapshot)
    lines = result.strip().split("\n")
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "fact"
    assert json.loads(lines[1])["type"] == "observation"

def test_snapshot_to_jsonl_unicode():
    snapshot = {
        "facts": [{"id": 1, "value": "ภาษาไทย"}]
    }
    result = snapshot_to_jsonl(snapshot)
    assert "ภาษาไทย" in result
    # ensure_ascii=False should keep it as is
    assert "\\u" not in result

def test_snapshot_to_csv_empty():
    result = snapshot_to_csv({})
    reader = csv.DictReader(io.StringIO(result))
    assert reader.fieldnames == CSV_COLUMNS
    assert list(reader) == []

def test_snapshot_to_csv_mixed():
    snapshot = {
        "facts": [
            {"id": 1, "kind": "info", "value": "f1", "tags": ["tag1", "tag2"]}
        ],
        "observations": [
            {"id": 101, "summary": "o1"}
        ]
    }
    result = snapshot_to_csv(snapshot)
    reader = csv.DictReader(io.StringIO(result))
    rows = list(reader)
    assert len(rows) == 2

    assert rows[0]["type"] == "fact"
    assert rows[0]["id"] == "1"
    assert rows[0]["tags"] == "tag1,tag2"

    assert rows[1]["type"] == "observation"
    assert rows[1]["id"] == "101"
    assert rows[1]["summary"] == "o1"

def test_snapshot_to_csv_extras_ignored():
    snapshot = {
        "facts": [
            {"id": 1, "unknown_field": "val"}
        ]
    }
    result = snapshot_to_csv(snapshot)
    assert "unknown_field" not in result
