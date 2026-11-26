"""Tests for modern Gemini features (Gemini 4, Decisions API, Interactions API)."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from sakthai.agent.loop import _resolve_model_name
from sakthai.agent.providers.base import AgentError
from sakthai.agent.providers.gemini_provider import (
    FREE_TIER_GEMINI_MODELS,
    LEGACY_GEMINI_MODELS,
    PAID_ONLY_GEMINI_MODELS,
    call_gemini,
    call_gemini_decision,
    call_gemini_interaction,
    is_free_tier_model,
)


@pytest.fixture(autouse=True)
def _isolate_quota_sentinel(monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate quota sentinel to prevent daily request limit cascades in tests."""
    monkeypatch.setenv("SAKTHAI_QUOTA_SENTINEL", "0")


def test_legacy_gemini_models_mapping() -> None:
    """Verify legacy model substitution mapping contains expected migrations."""
    assert LEGACY_GEMINI_MODELS["gemini-2.5-flash"] == "gemini-4-hydrogen"
    assert LEGACY_GEMINI_MODELS["gemini-2.0-flash"] == "gemini-4-hydrogen"
    assert LEGACY_GEMINI_MODELS["gemini-1.5-flash"] == "gemini-4-hydrogen"
    assert LEGACY_GEMINI_MODELS["gemini-1.5-pro"] == "gemini-4-neon"
    assert LEGACY_GEMINI_MODELS["gemini-3.1-pro-preview"] == "gemini-4-neon"


def test_paid_only_gemini_models_set() -> None:
    """Verify paid-only models requiring billing accounts are identified."""
    assert "gemini-4-carbon" in PAID_ONLY_GEMINI_MODELS
    assert "gemini-4-neon" in PAID_ONLY_GEMINI_MODELS
    assert "gemini-4-hydrogen" not in PAID_ONLY_GEMINI_MODELS
    assert "gemini-3.5-flash-lite" not in PAID_ONLY_GEMINI_MODELS


def test_free_tier_gemini_models_and_helper() -> None:
    """Verify Free-Tier eligible models and is_free_tier_model helper."""
    assert "gemini-4-hydrogen" in FREE_TIER_GEMINI_MODELS
    assert "gemini-3.8-flash" in FREE_TIER_GEMINI_MODELS
    assert "gemini-3.5-flash-lite" in FREE_TIER_GEMINI_MODELS
    assert "gemini-decision-1" in FREE_TIER_GEMINI_MODELS
    assert "gemma-4-31b-it" in FREE_TIER_GEMINI_MODELS
    assert is_free_tier_model("gemini-4-hydrogen") is True
    assert is_free_tier_model("models/gemini-3.5-flash-lite") is True
    assert is_free_tier_model("gemini-4-carbon") is False


def test_gemini_free_only_fallback(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify GEMINI_FREE_ONLY safely redirects paid-only models to gemini-4-hydrogen."""
    monkeypatch.setenv("GEMINI_FREE_ONLY", "true")
    client = MagicMock()
    candidate = MagicMock()
    candidate.content.parts = [MagicMock(text="response text", function_calls=[])]
    candidate.finish_reason = "STOP"
    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata = None
    client.models.generate_content.return_value = response

    with (
        patch("sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]),
        caplog.at_level(logging.WARNING),
    ):
        res = call_gemini(client, "gemini-4-carbon", "system", (), [], 0)

    assert res.content[0].text == "response text"
    assert "is paid-only (0 free-tier quota) and GEMINI_FREE_ONLY is set" in caplog.text
    call_args = client.models.generate_content.call_args
    assert call_args.kwargs["model"] == "gemini-4-hydrogen"


def test_resolve_model_name_substitutes_legacy_models(caplog: pytest.LogCaptureFixture) -> None:
    """Verify deprecated Gemini models are automatically upgraded with warning."""
    with caplog.at_level(logging.WARNING):
        resolved_flash = _resolve_model_name("gemini-2.5-flash", "google")
        assert resolved_flash == "gemini-4-hydrogen"
        assert "is deprecated; auto-substituting" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        resolved_pro = _resolve_model_name("gemini-1.5-pro", "google")
        assert resolved_pro == "gemini-4-neon"
        assert "gemini-4-neon" in caplog.text


def test_resolve_model_name_defaults_google_to_neon_and_free_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify default Google model is gemini-4-neon, and GEMINI_FREE_ONLY falls back to hydrogen."""
    from sakthai.agent.loop import DEFAULT_MODEL

    monkeypatch.delenv("GEMINI_FREE_ONLY", raising=False)
    assert _resolve_model_name(DEFAULT_MODEL, "google") == "gemini-4-neon"

    monkeypatch.setenv("GEMINI_FREE_ONLY", "true")
    assert _resolve_model_name(DEFAULT_MODEL, "google") == "gemini-4-hydrogen"


def test_call_gemini_auto_substitutes_legacy_model(caplog: pytest.LogCaptureFixture) -> None:
    """Verify call_gemini updates legacy models to Gemini 4 equivalents."""
    client = MagicMock()
    candidate = MagicMock()
    candidate.content.parts = [MagicMock(text="response text", function_calls=[])]
    candidate.finish_reason = "STOP"
    response = MagicMock()
    response.candidates = [candidate]
    response.usage_metadata = None
    client.models.generate_content.return_value = response

    with (
        patch("sakthai.agent.providers.gemini_provider.to_gemini_contents", return_value=[]),
        caplog.at_level(logging.WARNING),
    ):
        res = call_gemini(client, "gemini-2.0-flash", "system instruction", (), [], 0)

    assert res.content[0].text == "response text"
    assert "auto-substituting 'gemini-4-hydrogen'" in caplog.text
    # Verify the client received the substituted model
    call_args = client.models.generate_content.call_args
    assert call_args.kwargs["model"] == "gemini-4-hydrogen"


def test_call_gemini_decision_success() -> None:
    """Verify call_gemini_decision delegates to decisions.create with correct args."""
    client = MagicMock()
    mock_result = MagicMock()
    client.decisions.create.return_value = mock_result

    questions = {
        "is_safe": {
            "type": "yes_no",
            "prompt": "Is this content safe?",
        }
    }
    result = call_gemini_decision(
        client=client,
        text_input="User input text",
        questions=questions,
        model="gemini-decision-1",
    )

    assert result == mock_result
    client.decisions.create.assert_called_once_with(
        model="gemini-decision-1",
        input="User input text",
        questions=questions,
    )


def test_call_gemini_decision_error_handling() -> None:
    """Verify call_gemini_decision wraps exceptions in AgentError."""
    client = MagicMock()
    client.decisions.create.side_effect = RuntimeError("Service unavailable")

    questions = {"is_valid": {"type": "yes_no", "prompt": "Is valid?"}}
    with pytest.raises(AgentError, match="Gemini Decisions API call failed"):
        call_gemini_decision(client, "some input", questions)


def test_call_gemini_interaction_success() -> None:
    """Verify call_gemini_interaction delegates to interactions.create with modern model."""
    client = MagicMock()
    mock_resp = MagicMock()
    client.interactions.create.return_value = mock_resp

    res = call_gemini_interaction(
        client=client,
        text_input="Plan a workflow",
        model="gemini-4-hydrogen",
        previous_interaction_id="int_123",
        stream=True,
    )

    assert res == mock_resp
    client.interactions.create.assert_called_once_with(
        model="gemini-4-hydrogen",
        input="Plan a workflow",
        previous_interaction_id="int_123",
        stream=True,
    )


def test_call_gemini_interaction_auto_substitutes_legacy() -> None:
    """Verify call_gemini_interaction auto-substitutes deprecated models."""
    client = MagicMock()
    mock_resp = MagicMock()
    client.interactions.create.return_value = mock_resp

    res = call_gemini_interaction(
        client=client,
        text_input="Hello",
        model="gemini-2.5-flash",
    )

    assert res == mock_resp
    client.interactions.create.assert_called_once_with(
        model="gemini-4-hydrogen",
        input="Hello",
    )


def test_call_gemini_interaction_error_handling() -> None:
    """Verify call_gemini_interaction wraps exceptions in AgentError."""
    client = MagicMock()
    client.interactions.create.side_effect = RuntimeError("Network timeout")

    with pytest.raises(AgentError, match="Gemini Interactions API call failed"):
        call_gemini_interaction(client, "test input")


def test_call_gemini_interaction_neon_free_only_fallback(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify call_gemini_interaction redirects gemini-4-neon to hydrogen under GEMINI_FREE_ONLY."""
    monkeypatch.setenv("GEMINI_FREE_ONLY", "true")
    client = MagicMock()
    mock_resp = MagicMock()
    client.interactions.create.return_value = mock_resp

    with caplog.at_level(logging.WARNING):
        res = call_gemini_interaction(
            client=client,
            text_input="Hello Neon",
            model="gemini-4-neon",
        )

    assert res == mock_resp
    assert "auto-falling back to 'gemini-4-hydrogen'" in caplog.text
    client.interactions.create.assert_called_once_with(
        model="gemini-4-hydrogen",
        input="Hello Neon",
    )
