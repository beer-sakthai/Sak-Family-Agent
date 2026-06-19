"""Tests for sakthai.agent.providers.anthropic_provider."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

import sakthai.agent.providers.base as base_mod
from sakthai.agent.providers.anthropic_provider import call_anthropic
from sakthai.agent.providers.base import AgentError


def _zero_wait(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MULTIPLIER", 0)
    monkeypatch.setattr(base_mod, "RETRY_WAIT_MAX", 0)
    monkeypatch.setattr(base_mod, "RETRY_ATTEMPTS", 1)


def _fake_sdk_response(stop_reason: str = "end_turn", text: str = "hello") -> MagicMock:
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = stop_reason
    resp.content = [block]
    resp.usage = MagicMock(input_tokens=5, output_tokens=3)
    return resp


# -- call_anthropic (non-streaming) ----------------------------------------


def test_call_anthropic_returns_raw_sdk_response() -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_sdk_response()
    result = call_anthropic(client, "claude-3-5-sonnet-20241022", 1024, "system", [], [])
    assert result.stop_reason == "end_turn"
    client.messages.create.assert_called_once()


def test_call_anthropic_passes_all_args() -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_sdk_response()
    tools = [{"name": "learn", "description": "d", "input_schema": {}}]
    msgs = [{"role": "user", "content": "hi"}]
    call_anthropic(client, "claude-3-5-haiku-20241022", 512, "my system", tools, msgs)
    kw = client.messages.create.call_args.kwargs
    assert kw["model"] == "claude-3-5-haiku-20241022"
    assert kw["max_tokens"] == 512
    assert kw["system"] == "my system"
    assert kw["tools"] == tools
    assert kw["messages"] == msgs


# -- call_anthropic (streaming) --------------------------------------------


def test_call_anthropic_streaming_forwards_tokens() -> None:
    final_msg = _fake_sdk_response(text="streamed result")

    stream = MagicMock()
    stream.text_stream = ["hel", "lo ", "world"]
    stream.get_final_message.return_value = final_msg

    stream_cm = MagicMock()
    stream_cm.__enter__ = MagicMock(return_value=stream)
    stream_cm.__exit__ = MagicMock(return_value=False)

    client = MagicMock()
    client.messages.stream.return_value = stream_cm

    tokens: list[str] = []
    result = call_anthropic(client, "m", 100, "sys", [], [], on_token=tokens.append)

    assert tokens == ["hel", "lo ", "world"]
    assert result is final_msg
    client.messages.stream.assert_called_once()
    client.messages.create.assert_not_called()


def test_call_anthropic_streaming_uses_stream_not_create() -> None:
    final_msg = _fake_sdk_response()
    stream = MagicMock()
    stream.text_stream = []
    stream.get_final_message.return_value = final_msg
    stream_cm = MagicMock()
    stream_cm.__enter__ = MagicMock(return_value=stream)
    stream_cm.__exit__ = MagicMock(return_value=False)
    client = MagicMock()
    client.messages.stream.return_value = stream_cm

    call_anthropic(client, "m", 100, "sys", [], [], on_token=lambda _: None)

    client.messages.stream.assert_called_once()
    client.messages.create.assert_not_called()


def test_call_anthropic_non_streaming_uses_create_not_stream() -> None:
    client = MagicMock()
    client.messages.create.return_value = _fake_sdk_response()

    call_anthropic(client, "m", 100, "sys", [], [], on_token=None)

    client.messages.create.assert_called_once()
    client.messages.stream.assert_not_called()


# -- error handling --------------------------------------------------------


def test_call_anthropic_api_error_raises_agent_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    client = MagicMock()
    client.messages.create.side_effect = OSError("network failure")
    with pytest.raises(AgentError, match="Anthropic API call failed"):
        call_anthropic(client, "m", 100, "sys", [], [])


def test_call_anthropic_oserror_wraps_as_agent_error(monkeypatch: pytest.MonkeyPatch) -> None:
    _zero_wait(monkeypatch)
    client = MagicMock()
    client.messages.create.side_effect = OSError("broken pipe")
    with pytest.raises(AgentError):
        call_anthropic(client, "m", 100, "sys", [], [])
