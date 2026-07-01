"""Retry-*wiring* tests for the provider backends.

``test_providers_base.py`` already proves ``with_retry`` / ``is_retryable`` work
in isolation, and the existing provider suites cover immediate failures and
retry *exhaustion*. The gap these tests close is the recovery path actually being
wired through each provider function: a transient error at the client/HTTP
boundary must trigger a real retry that then *succeeds*, and a non-retryable HTTP
status must fail fast without retrying. (The Gemini backend uses the identical
``with_retry(client.models.generate_content, ...)`` wiring; google-genai is not
reliably importable in this hermetic environment, so it is exercised by the
shared base-level tests rather than duplicated here.)
"""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

import sakthai.agent.providers.base as base_mod
from sakthai.agent.providers.anthropic_provider import call_anthropic
from sakthai.agent.providers.base import AgentError
from sakthai.agent.providers.openai_provider import call_openai_compat


@pytest.fixture(autouse=True)
def _fast_retries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero the backoff and allow a couple of attempts so retries don't sleep."""
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MULTIPLIER", 0)
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MAX", 0)
    monkeypatch.setattr(base_mod, "RETRY_ATTEMPTS", 3)


def _ok_resp() -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {"content": "recovered", "tool_calls": []},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1},
    }


def _good_post_response() -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = _ok_resp()
    resp.raise_for_status.return_value = None
    return resp


# -- openai-compatible (httpx .post path) ----------------------------------


def test_openai_retries_transient_connection_error_then_succeeds() -> None:
    client = MagicMock(spec=["post"])
    client.post.side_effect = [
        httpx.ConnectError("connection refused"),
        _good_post_response(),
    ]

    result = call_openai_compat(
        client, "gpt-4o", "sys", (), [{"role": "user", "content": "hi"}], 1
    )

    assert result.content[0].text == "recovered"
    assert client.post.call_count == 2  # retried once, then succeeded


def test_openai_retries_retryable_http_status_then_succeeds() -> None:
    bad = MagicMock()
    bad.raise_for_status.side_effect = httpx.HTTPStatusError(
        "503", request=MagicMock(), response=MagicMock(status_code=503)
    )
    client = MagicMock(spec=["post"])
    client.post.side_effect = [bad, _good_post_response()]

    result = call_openai_compat(
        client, "gpt-4o", "sys", (), [{"role": "user", "content": "hi"}], 1
    )

    assert result.content[0].text == "recovered"
    assert client.post.call_count == 2


def test_openai_does_not_retry_non_retryable_http_status() -> None:
    bad = MagicMock()
    bad.raise_for_status.side_effect = httpx.HTTPStatusError(
        "400", request=MagicMock(), response=MagicMock(status_code=400)
    )
    client = MagicMock(spec=["post"])
    client.post.side_effect = [bad, _good_post_response()]

    with pytest.raises(AgentError, match="OpenAI-compatible API call failed"):
        call_openai_compat(
            client, "gpt-4o", "sys", (), [{"role": "user", "content": "hi"}], 1
        )

    assert client.post.call_count == 1  # 4xx is fatal: no retry


# -- anthropic -------------------------------------------------------------


def _anthropic_ok() -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = "recovered"
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    resp.usage = MagicMock(input_tokens=1, output_tokens=1)
    return resp


def test_anthropic_retries_transient_then_succeeds() -> None:
    client = MagicMock()
    client.messages.create.side_effect = [OSError("broken pipe"), _anthropic_ok()]

    result = call_anthropic(client, "claude-3-5-sonnet-20241022", 1024, "sys", [], [])

    assert result.content[0].text == "recovered"
    assert client.messages.create.call_count == 2
