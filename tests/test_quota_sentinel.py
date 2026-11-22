"""Comprehensive tests for Quota Sentinel, adaptive rate limiting, and model cascading."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import pytest
from click.testing import CliRunner

from sakthai.agent.providers.gemini_provider import (
    call_gemini,
    call_gemini_decision,
    call_gemini_interaction,
)
from sakthai.agent.quota import (
    QuotaSentinel,
    QuotaSentinelStore,
    format_time_remaining,
    get_model_quota_spec,
    get_pacific_date_str,
    reset_quota_sentinel,
    seconds_until_pacific_midnight,
)
from sakthai.cli import main


@pytest.fixture(autouse=True)
def clean_quota_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Isolate quota sentinel store and reset singletons."""
    test_db = tmp_path / "test_quota.db"
    monkeypatch.setenv("SAKTHAI_QUOTA_DB", str(test_db))
    monkeypatch.setenv("SAKTHAI_QUOTA_SENTINEL", "1")
    reset_quota_sentinel()
    yield
    reset_quota_sentinel()


# --- Pacific Time Helpers ---


def test_pacific_date_str() -> None:
    dt = datetime(2026, 11, 22, 5, 30, tzinfo=ZoneInfo("America/Los_Angeles"))
    assert get_pacific_date_str(dt) == "2026-11-22"

    dt_utc = datetime(2026, 11, 22, 7, 30, tzinfo=ZoneInfo("UTC"))  # 23:30 prev day PST
    assert get_pacific_date_str(dt_utc) == "2026-11-21"


def test_seconds_until_pacific_midnight() -> None:
    dt = datetime(2026, 11, 22, 23, 0, 0, tzinfo=ZoneInfo("America/Los_Angeles"))
    sec = seconds_until_pacific_midnight(dt)
    assert sec == 3600.0

    rem_human = format_time_remaining(sec)
    assert rem_human == "1h 00m"


# --- Baseline Specs & Overrides ---


def test_model_quota_spec_defaults() -> None:
    spec = get_model_quota_spec("gemini-4-hydrogen")
    assert spec.rpd_limit == 20
    assert spec.rpm_limit == 5
    assert spec.fallback_model == "gemini-3.5-flash-lite"

    spec_lite = get_model_quota_spec("models/gemini-3.5-flash-lite")
    assert spec_lite.rpd_limit == 500
    assert spec_lite.rpm_limit == 15

    spec_decision = get_model_quota_spec("gemini-decision-1")
    assert spec_decision.rpd_limit == 10_000
    assert spec_decision.rpm_limit == 200

    spec_unknown = get_model_quota_spec("custom-model-x")
    assert spec_unknown.rpd_limit == 20
    assert spec_unknown.category == "Custom / Unknown"


def test_model_quota_spec_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_QUOTA_RPD_GEMINI_4_HYDROGEN", "100")
    monkeypatch.setenv("GEMINI_QUOTA_RPM_GEMINI_4_HYDROGEN", "25")
    spec = get_model_quota_spec("gemini-4-hydrogen")
    assert spec.rpd_limit == 100
    assert spec.rpm_limit == 25


# --- QuotaSentinelStore SQLite & Sliding Window ---


def test_quota_sentinel_store_recording(tmp_path: Path) -> None:
    db_path = tmp_path / "quota.db"
    store = QuotaSentinelStore(db_path=db_path)

    now = 1000.0
    store.record_request(
        "gemini-4-hydrogen",
        input_tokens=100,
        output_tokens=50,
        timestamp=now,
        date_str="2026-11-22",
    )
    store.record_request(
        "gemini-4-hydrogen",
        input_tokens=200,
        output_tokens=100,
        timestamp=now + 10.0,
        date_str="2026-11-22",
    )

    daily = store.get_daily_usage(model="gemini-4-hydrogen", date_str="2026-11-22")
    assert daily["gemini-4-hydrogen"]["request_count"] == 2
    assert daily["gemini-4-hydrogen"]["input_tokens"] == 300
    assert daily["gemini-4-hydrogen"]["output_tokens"] == 150

    rpm, tpm = store.get_sliding_window_usage("gemini-4-hydrogen", now=now + 15.0)
    assert rpm == 2
    assert tpm == 450

    # Pruned after 60 seconds
    rpm_later, tpm_later = store.get_sliding_window_usage("gemini-4-hydrogen", now=now + 65.0)
    assert rpm_later == 1
    assert tpm_later == 300


# --- QuotaSentinel Cascading & Throttling ---


def test_sentinel_cascades_on_rpd_exhaustion(tmp_path: Path) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "cascading.db")
    sentinel = QuotaSentinel(store=store)

    # gemini-4-hydrogen default limit is 20
    for _ in range(20):
        sentinel.postflight("gemini-4-hydrogen", input_tokens=10, output_tokens=10)

    # Calling gemini-4-hydrogen now should cascade to gemini-3.5-flash-lite
    target_model, wait_sec = sentinel.preflight("gemini-4-hydrogen")
    assert target_model == "gemini-3.5-flash-lite"
    assert wait_sec == 0.0


def test_sentinel_sliding_window_rpm_backoff(tmp_path: Path) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "rpm.db")
    sentinel = QuotaSentinel(store=store)

    base_time = 1000.0
    # gemini-4-hydrogen rpm limit is 5
    for i in range(5):
        store.record_request("gemini-4-hydrogen", timestamp=base_time + (i * 2))

    # Preflight at base_time + 10s: rpm cap hit (5 requests). Oldest was at base_time.
    # Expected wait: 60 - (1010 - 1000) + 0.1 = 50.1 seconds
    target_model, wait_sec = sentinel.preflight("gemini-4-hydrogen", now=base_time + 10.0)
    assert target_model == "gemini-4-hydrogen"
    assert pytest.approx(wait_sec, 0.2) == 50.1


def test_sentinel_bypassed_when_disabled(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("SAKTHAI_QUOTA_SENTINEL", "0")
    store = QuotaSentinelStore(db_path=tmp_path / "disabled.db")
    sentinel = QuotaSentinel(store=store)

    for _ in range(25):
        store.record_request("gemini-4-hydrogen")

    target_model, wait_sec = sentinel.preflight("gemini-4-hydrogen")
    assert target_model == "gemini-4-hydrogen"
    assert wait_sec == 0.0


# --- Provider Integration Tests ---


def test_call_gemini_quota_sentinel_hook(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "provider.db")
    sentinel = QuotaSentinel(store=store)
    monkeypatch.setattr("sakthai.agent.quota.sentinel._sentinel_instance", sentinel)

    mock_client = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [MagicMock(text="Hello world", function_calls=None)]
    mock_response = MagicMock(candidates=[mock_candidate], usage_metadata=None)
    mock_client.models.generate_content.return_value = mock_response

    resp = call_gemini(
        client=mock_client,
        model="gemini-4-hydrogen",
        system="You are helpful.",
        tools=(),
        messages=[{"role": "user", "content": "hi"}],
        iteration=0,
    )

    assert resp.content[0].text == "Hello world"
    daily = store.get_daily_usage(model="gemini-4-hydrogen")
    assert daily["gemini-4-hydrogen"]["request_count"] == 1


def test_call_gemini_cascades_when_quota_exhausted(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "cascaded_provider.db")
    sentinel = QuotaSentinel(store=store)
    monkeypatch.setattr("sakthai.agent.quota.sentinel._sentinel_instance", sentinel)

    # Exhaust gemini-4-hydrogen limit
    for _ in range(20):
        store.record_request("gemini-4-hydrogen")

    mock_client = MagicMock()
    mock_candidate = MagicMock()
    mock_candidate.finish_reason = "STOP"
    mock_candidate.content.parts = [MagicMock(text="Cascaded response", function_calls=None)]
    mock_response = MagicMock(candidates=[mock_candidate], usage_metadata=None)
    mock_client.models.generate_content.return_value = mock_response

    call_gemini(
        client=mock_client,
        model="gemini-4-hydrogen",
        system="You are helpful.",
        tools=(),
        messages=[{"role": "user", "content": "hi"}],
        iteration=0,
    )

    # Verify generate_content was called with fallback model
    call_kwargs = mock_client.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-3.5-flash-lite"
    daily = store.get_daily_usage(model="gemini-3.5-flash-lite")
    assert daily["gemini-3.5-flash-lite"]["request_count"] == 1


def test_call_gemini_decision_and_interaction_quota_hooks(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "other_providers.db")
    sentinel = QuotaSentinel(store=store)
    monkeypatch.setattr("sakthai.agent.quota.sentinel._sentinel_instance", sentinel)

    mock_client = MagicMock()
    mock_client.decisions.create.return_value = {"score": 1.0}
    mock_client.interactions.create.return_value = MagicMock(id="interaction_123")

    call_gemini_decision(mock_client, "Input text", {"q1": {}})
    daily_decision = store.get_daily_usage(model="gemini-decision-1")
    assert daily_decision["gemini-decision-1"]["request_count"] == 1

    call_gemini_interaction(mock_client, "Interactive chat")
    daily_hydrogen = store.get_daily_usage(model="gemini-4-hydrogen")
    assert daily_hydrogen["gemini-4-hydrogen"]["request_count"] == 1


# --- CLI Tests ---


def test_cli_quota_status_text(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "cli.db")
    store.record_request("gemini-4-hydrogen", input_tokens=1000, output_tokens=500)
    sentinel = QuotaSentinel(store=store)
    monkeypatch.setattr("sakthai.agent.quota.sentinel._sentinel_instance", sentinel)

    runner = CliRunner()
    result = runner.invoke(main, ["quota", "status"])
    assert result.exit_code == 0
    assert "Google AI Studio Quota Sentinel" in result.output
    assert "gemini-4-hydrogen" in result.output
    assert "gemini-3.5-flash-lite" in result.output
    assert "Active Mode: Free-Tier Auto-Cascading Enabled" in result.output


def test_cli_quota_status_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = QuotaSentinelStore(db_path=tmp_path / "cli_json.db")
    store.record_request("gemini-4-hydrogen", input_tokens=1000, output_tokens=500)
    sentinel = QuotaSentinel(store=store)
    monkeypatch.setattr("sakthai.agent.quota.sentinel._sentinel_instance", sentinel)

    runner = CliRunner()
    result = runner.invoke(main, ["quota", "status", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.output)
    assert data["sentinel_enabled"] is True
    assert "reset_in_seconds" in data
    assert any(m["model_id"] == "gemini-4-hydrogen" and m["rpd_used"] == 1 for m in data["models"])
