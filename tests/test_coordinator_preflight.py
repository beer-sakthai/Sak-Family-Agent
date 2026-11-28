"""Tests for SakKing intent preflight specialist delegation envelope."""

from __future__ import annotations

from sakthai.agent.coordinator import SakKingIntentPreflight, classify_intent_envelope


def test_classify_intent_envelope_hf_specialist() -> None:
    task = "Please inspect the Hugging Face model card and check safetensors weights"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "sakthai"
    assert env["should_delegate"] is True
    assert "Hugging Face" in env["specialist_domain"]
    assert env["confidence"] >= 0.5
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_browser_specialist() -> None:
    task = "Use playwright to scrape and inspect element on the login page"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "saksee"
    assert env["should_delegate"] is True
    assert "Web Browsing" in env["specialist_domain"]
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_cicd_specialist() -> None:
    task = "Audit the GitHub action workflow for PR review and check bandit lint"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "sakjules"
    assert env["should_delegate"] is True
    assert "CI/CD" in env["specialist_domain"]
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_social_specialist() -> None:
    task = "Draft a LinkedIn post and announce the milestone content via xurl"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "saksit"
    assert env["should_delegate"] is True
    assert "Social Media" in env["specialist_domain"]
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_ops_specialist() -> None:
    task = "Perform WAL checkpoint, vacuum memory databases, and verify daemon heartbeat"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "saktan"
    assert env["should_delegate"] is True
    assert "Daily Operations" in env["specialist_domain"]
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_sakking_default() -> None:
    task = "Calculate the fibonacci sequence of 20 and print result"
    env = classify_intent_envelope(task)
    assert env["recommended_persona"] == "sakking"
    assert env["should_delegate"] is False
    assert env["specialist_domain"] == "General Execution & Technical Implementation"
    assert env["latency_ms"] < 3000.0


def test_classify_intent_envelope_forced_persona() -> None:
    task = "Do something"
    env = classify_intent_envelope(task, forced_persona="saksee")
    assert env["recommended_persona"] == "saksee"
    assert env["should_delegate"] is True
    assert env["confidence"] == 1.0


def test_sakking_intent_preflight_class() -> None:
    preflight = SakKingIntentPreflight(timeout_seconds=3.0)
    res = preflight.evaluate("Open browser and visit python.org")
    assert res["recommended_persona"] == "saksee"
    assert res["should_delegate"] is True
    assert res["latency_ms"] < 3000.0
