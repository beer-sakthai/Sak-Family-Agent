"""Tests for benchmark parsing fallbacks."""

import sys
from pathlib import Path

# Add the project root to sys.path to import the benchmark script
sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.bench_dashboard_json import DummyFact, baseline_parse, batch_parse  # noqa: E402


def test_baseline_parse_fallback() -> None:
    # Arrange
    malformed_facts = [
        DummyFact(id=1, kind="revenue", key="Client_1", value="bad json", created_at=0, tags=[]),
        DummyFact(id=2, kind="revenue", key=None, value="[", created_at=0, tags=[]),
    ]

    # Act
    result = baseline_parse(malformed_facts)

    # Assert
    assert len(result) == 2
    assert result[0] == {
        "client": "Client_1",
        "amount": 0.0,
        "type": "setup",
        "date": "",
    }
    assert result[1] == {
        "client": "Unknown",
        "amount": 0.0,
        "type": "setup",
        "date": "",
    }


def test_batch_parse_fallback() -> None:
    # Arrange
    malformed_facts = [
        DummyFact(id=1, kind="revenue", key="Client_1", value="bad json", created_at=0, tags=[]),
        DummyFact(id=2, kind="revenue", key=None, value="[", created_at=0, tags=[]),
    ]

    # Act
    result = batch_parse(malformed_facts)

    # Assert
    assert len(result) == 2
    assert result[0] == {
        "client": "Client_1",
        "amount": 0.0,
        "type": "setup",
        "date": "",
    }
    assert result[1] == {
        "client": "Unknown",
        "amount": 0.0,
        "type": "setup",
        "date": "",
    }


def test_parse_valid_json() -> None:
    # Arrange
    facts = [
        DummyFact(
            id=1,
            kind="revenue",
            key="Client_1",
            value='{"client": "Client_1", "amount": 100.0, "type": "monthly", "date": "2025-01-15"}',
            created_at=0,
            tags=[],
        ),
    ]

    # Act
    baseline_result = baseline_parse(facts)
    batch_result = batch_parse(facts)

    # Assert
    assert baseline_result == batch_result
    assert len(baseline_result) == 1
    assert baseline_result[0] == {
        "client": "Client_1",
        "amount": 100.0,
        "type": "monthly",
        "date": "2025-01-15",
    }
