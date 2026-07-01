"""Wire-contract tests for the OpenAI-compatible provider.

The other provider suites drive a ``MagicMock`` client whose ``raise_for_status``
and ``json`` are themselves mocks — so they prove the *parsing* code runs but
never exercise the real HTTP path: status handling, the transient-failure retry
policy, or the exact request payload that goes on the wire.

These tests close that gap by running ``call_openai_compat`` against a real
``httpx.Client`` backed by ``httpx.MockTransport``. The transport sees the
genuine serialized request and returns genuine ``httpx.Response`` objects, so
``resp.raise_for_status()`` and :func:`with_retry` behave exactly as in
production. Retry sleeps are zeroed so the suite stays fast.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

import sakthai.agent.providers.base as base
from sakthai.agent.providers.base import AgentError
from sakthai.agent.providers.openai_provider import call_openai_compat
from sakthai.agent.tools import Tool


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero the backoff so the 3-attempt retry policy doesn't actually sleep."""
    monkeypatch.setattr(base, "RETRY_WAIT_MULTIPLIER", 0.0)
    monkeypatch.setattr(base, "RETRY_WAIT_MAX", 0.0)


def _tool(name: str = "learn") -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {"value": {"type": "string"}}},
        handler=lambda args, store: "ok",
    )


def _client(handler: Any) -> httpx.Client:
    return httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test.local"
    )


def _ok_body(text: str = "hi") -> dict[str, Any]:
    return {
        "choices": [
            {"message": {"content": text, "tool_calls": []}, "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 3, "completion_tokens": 2},
    }


# -- request wire-shape ------------------------------------------------------


def test_request_payload_matches_openai_contract() -> None:
    """The serialized request hits /chat/completions with the expected body."""
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["method"] = request.method
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=_ok_body("done"))

    with _client(handler) as client:
        resp = call_openai_compat(
            client,
            model="gpt-test",
            system="you are helpful",
            tools=(_tool("learn"),),
            messages=[{"role": "user", "content": "hello"}],
            iteration=0,
        )

    assert seen["method"] == "POST"
    assert seen["url"].endswith("/chat/completions")
    body = seen["body"]
    assert body["model"] == "gpt-test"
    assert body["stream"] is False
    # System prompt is the first message; the user turn follows.
    assert body["messages"][0] == {"role": "system", "content": "you are helpful"}
    assert body["messages"][1] == {"role": "user", "content": "hello"}
    # Tools are emitted in OpenAI function-schema form.
    assert body["tools"][0]["type"] == "function"
    assert body["tools"][0]["function"]["name"] == "learn"
    # And the reply is normalised back into our Response shape.
    assert resp.stop_reason == "end_turn"
    assert resp.content[0].text == "done"


def test_request_omits_tools_key_when_no_tools() -> None:
    """With no tools, the payload carries no ``tools`` key at all."""
    seen: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json=_ok_body())

    with _client(handler) as client:
        call_openai_compat(
            client,
            model="m",
            system="s",
            tools=(),
            messages=[{"role": "user", "content": "x"}],
            iteration=0,
        )
    assert "tools" not in seen["body"]


# -- transient-failure retry policy ------------------------------------------


def test_retries_on_429_then_succeeds() -> None:
    """A 429 is retried; the second (200) attempt yields the response."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] == 1:
            return httpx.Response(429, json={"error": "rate limited"})
        return httpx.Response(200, json=_ok_body("recovered"))

    with _client(handler) as client:
        resp = call_openai_compat(
            client,
            model="m",
            system="s",
            tools=(),
            messages=[{"role": "user", "content": "x"}],
            iteration=0,
        )
    assert calls["n"] == 2
    assert resp.content[0].text == "recovered"


def test_retries_exhausted_on_persistent_500() -> None:
    """A persistent 500 is retried up to RETRY_ATTEMPTS, then surfaces as AgentError."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(500, json={"error": "boom"})

    with (
        _client(handler) as client,
        pytest.raises(AgentError, match="OpenAI-compatible API call failed"),
    ):
        call_openai_compat(
            client,
            model="m",
            system="s",
            tools=(),
            messages=[{"role": "user", "content": "x"}],
            iteration=0,
        )
    assert calls["n"] == base.RETRY_ATTEMPTS


def test_client_error_400_is_not_retried() -> None:
    """A 400 is a permanent error: one attempt, then AgentError (no retry)."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"error": "bad request"})

    with _client(handler) as client, pytest.raises(AgentError):
        call_openai_compat(
            client,
            model="m",
            system="s",
            tools=(),
            messages=[{"role": "user", "content": "x"}],
            iteration=0,
        )
    assert calls["n"] == 1


def test_malformed_json_body_surfaces_as_agent_error() -> None:
    """A 200 with a non-JSON body fails parsing and is wrapped, not retried."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(200, text="this is not json")

    with (
        _client(handler) as client,
        pytest.raises(AgentError, match="OpenAI-compatible API call failed"),
    ):
        call_openai_compat(
            client,
            model="m",
            system="s",
            tools=(),
            messages=[{"role": "user", "content": "x"}],
            iteration=0,
        )
    # JSON decode is a permanent failure — exactly one request was made.
    assert calls["n"] == 1
