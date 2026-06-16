"""Tests for sakthai.agent.providers.openai_provider — message adaptation and API calls."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock

import pytest

from sakthai.agent.providers.base import AgentError, Response
from sakthai.agent.providers.openai_provider import call_openai_compat, to_openai_messages
from sakthai.agent.tools import Tool


def _tool(name: str = "learn") -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {}},
        handler=lambda args, store: "ok",
    )


def _post_client(response: dict[str, Any]) -> Any:
    """Fake client with .post() method (httpx-style)."""
    resp = MagicMock()
    resp.json.return_value = response
    resp.raise_for_status.return_value = None
    client = MagicMock(spec=["post"])
    client.post.return_value = resp
    return client


def _text_resp(text: str = "hello", finish: str = "stop") -> dict[str, Any]:
    return {
        "choices": [{"message": {"content": text, "tool_calls": []}, "finish_reason": finish}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


def _tool_resp(name: str = "learn", args: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "c1",
                            "function": {"name": name, "arguments": json.dumps(args or {})},
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {},
    }


# -- to_openai_messages ----------------------------------------------------


def test_to_openai_messages_string_content() -> None:
    msgs = [{"role": "user", "content": "hello"}]
    result = to_openai_messages("sys", msgs)
    assert result[0] == {"role": "system", "content": "sys"}
    assert result[1] == {"role": "user", "content": "hello"}


def test_to_openai_messages_assistant_text_block() -> None:
    msgs = [{"role": "assistant", "content": [{"type": "text", "text": "hi there"}]}]
    result = to_openai_messages("sys", msgs)
    msg = result[1]
    assert msg["role"] == "assistant"
    assert msg["content"] == "hi there"
    assert "tool_calls" not in msg


def test_to_openai_messages_assistant_tool_use() -> None:
    msgs = [
        {
            "role": "assistant",
            "content": [{"type": "tool_use", "id": "t1", "name": "learn", "input": {"value": "x"}}],
        }
    ]
    result = to_openai_messages("sys", msgs)
    msg = result[1]
    tc = msg["tool_calls"][0]
    assert tc["id"] == "t1"
    assert tc["type"] == "function"
    assert tc["function"]["name"] == "learn"
    assert json.loads(tc["function"]["arguments"]) == {"value": "x"}


def test_to_openai_messages_assistant_mixed_text_and_tool() -> None:
    msgs = [
        {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "thinking..."},
                {"type": "tool_use", "id": "t2", "name": "recall", "input": {}},
            ],
        }
    ]
    result = to_openai_messages("sys", msgs)
    msg = result[1]
    assert msg["content"] == "thinking..."
    assert len(msg["tool_calls"]) == 1


def test_to_openai_messages_tool_result() -> None:
    msgs = [
        {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "learned!"}],
        }
    ]
    result = to_openai_messages("sys", msgs)
    tool_msg = result[1]
    assert tool_msg["role"] == "tool"
    assert tool_msg["tool_call_id"] == "t1"
    assert tool_msg["content"] == "learned!"


def test_to_openai_messages_user_text_block() -> None:
    msgs = [{"role": "user", "content": [{"type": "text", "text": "follow-up"}]}]
    result = to_openai_messages("sys", msgs)
    assert result[1] == {"role": "user", "content": "follow-up"}


def test_to_openai_messages_empty_text_block_skipped() -> None:
    msgs = [{"role": "user", "content": [{"type": "text", "text": ""}]}]
    result = to_openai_messages("sys", msgs)
    assert len(result) == 1  # only the system message; empty text block not emitted


def test_to_openai_messages_preserves_order() -> None:
    msgs = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": [{"type": "text", "text": "second"}]},
        {"role": "user", "content": "third"},
    ]
    result = to_openai_messages("sys", msgs)
    assert result[0]["role"] == "system"
    assert result[1]["role"] == "user"
    assert result[2]["role"] == "assistant"
    assert result[3]["role"] == "user"


# -- call_openai_compat ----------------------------------------------------


def test_call_openai_compat_text_response() -> None:
    client = _post_client(_text_resp("world"))
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 0)
    assert isinstance(resp, Response)
    assert resp.stop_reason == "end_turn"
    assert len(resp.content) == 1
    assert resp.content[0].text == "world"


def test_call_openai_compat_tool_use() -> None:
    client = _post_client(_tool_resp("learn", {"value": "sky"}))
    resp = call_openai_compat(client, "gpt-4", "sys", (_tool("learn"),), [], 1)
    assert resp.stop_reason == "tool_use"
    b = resp.content[0]
    assert b.type == "tool_use"
    assert b.name == "learn"
    assert b.input == {"value": "sky"}


def test_call_openai_compat_max_tokens() -> None:
    client = _post_client(_text_resp("cut off", "length"))
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 0)
    assert resp.stop_reason == "max_tokens"


def test_call_openai_compat_no_choices_raises() -> None:
    client = _post_client({"choices": []})
    with pytest.raises(AgentError, match="no choices"):
        call_openai_compat(client, "gpt-4", "sys", (), [], 0)


def test_call_openai_compat_unsupported_client_raises() -> None:
    with pytest.raises(AgentError, match="Unsupported client"):
        call_openai_compat(object(), "gpt-4", "sys", (), [], 0)


def test_call_openai_compat_api_error_wraps_as_agent_error() -> None:
    client = MagicMock(spec=["post"])
    client.post.side_effect = RuntimeError("connection refused")
    with pytest.raises(AgentError, match="OpenAI-compatible API call failed"):
        call_openai_compat(client, "gpt-4", "sys", (), [], 0)


def test_call_openai_compat_chat_completions_client() -> None:
    """Test openai SDK-style client (client.chat.completions.create)."""
    raw = MagicMock()
    raw.model_dump.return_value = _text_resp("sdk_response")
    client = MagicMock(spec=["chat"])
    client.chat.completions.create.return_value = raw
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 0)
    assert resp.stop_reason == "end_turn"
    assert resp.content[0].text == "sdk_response"


def test_call_openai_compat_malformed_tool_args_fall_back_empty() -> None:
    bad = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [
                        {"id": "c1", "function": {"name": "learn", "arguments": "{{invalid"}}
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {},
    }
    client = _post_client(bad)
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 0)
    assert resp.stop_reason == "tool_use"
    assert resp.content[0].input == {}


def test_call_openai_compat_tool_id_fallback() -> None:
    """When tool call has no id, a synthetic id is generated."""
    data = {
        "choices": [
            {
                "message": {
                    "content": None,
                    "tool_calls": [{"function": {"name": "learn", "arguments": "{}"}}],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {},
    }
    client = _post_client(data)
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 5)
    block = resp.content[0]
    assert block.id  # generated, non-empty
    assert "learn" in block.id


def test_call_openai_compat_usage_extracted() -> None:
    client = _post_client(_text_resp())
    resp = call_openai_compat(client, "gpt-4", "sys", (), [], 0)
    assert resp.usage["input_tokens"] == 10
    assert resp.usage["output_tokens"] == 5
