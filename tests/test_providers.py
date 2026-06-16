"""Unit tests for sakthai/agent/providers/*.

Covers base helpers, Anthropic, Gemini, and OpenAI-compat providers in
isolation — no real network traffic, no credentials required.
"""

from __future__ import annotations

import importlib
import json
import sys
from types import SimpleNamespace
from typing import Any
from unittest.mock import MagicMock

import anthropic
import httpx
import pytest

from sakthai.agent.providers.base import (
    RETRYABLE_STATUS,
    AgentError,
    Block,
    Response,
    block_field,
    find_tool_name_by_id,
    is_retryable,
    with_retry,
)

# ---------------------------------------------------------------------------
# base.py — Block / Response
# ---------------------------------------------------------------------------


class TestBlock:
    def test_defaults(self) -> None:
        b = Block("text")
        assert b.type == "text"
        assert b.text == ""
        assert b.id == ""
        assert b.name == ""
        assert b.input == {}

    def test_explicit_fields(self) -> None:
        b = Block("tool_use", id="t1", name="learn", input={"k": "v"})
        assert b.type == "tool_use"
        assert b.id == "t1"
        assert b.name == "learn"
        assert b.input == {"k": "v"}

    def test_none_input_becomes_empty_dict(self) -> None:
        b = Block("tool_use", input=None)
        assert b.input == {}


class TestResponse:
    def test_defaults(self) -> None:
        r = Response("end_turn", [])
        assert r.stop_reason == "end_turn"
        assert r.content == []
        assert r.usage["input_tokens"] == 0
        assert r.usage["output_tokens"] == 0
        assert r.usage["total_tokens"] == 0

    def test_usage_forwarded(self) -> None:
        r = Response(
            "tool_use", [], usage={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}
        )
        assert r.usage["total_tokens"] == 15


# ---------------------------------------------------------------------------
# base.py — block_field
# ---------------------------------------------------------------------------


class TestBlockField:
    def test_dict_access(self) -> None:
        assert block_field({"type": "text", "text": "hi"}, "type") == "text"
        assert block_field({"type": "text", "text": "hi"}, "text") == "hi"

    def test_dict_missing_uses_default(self) -> None:
        assert block_field({}, "name", "default") == "default"

    def test_object_access(self) -> None:
        obj = SimpleNamespace(type="tool_use", name="recall")
        assert block_field(obj, "type") == "tool_use"
        assert block_field(obj, "name") == "recall"

    def test_object_missing_uses_default(self) -> None:
        obj = SimpleNamespace(type="text")
        assert block_field(obj, "id", "xyz") == "xyz"

    def test_falsy_value_not_replaced_by_default(self) -> None:
        assert block_field({"count": 0}, "count", 99) == 0


# ---------------------------------------------------------------------------
# base.py — find_tool_name_by_id
# ---------------------------------------------------------------------------


class TestFindToolNameById:
    def _make_messages(self) -> list[dict[str, Any]]:
        return [
            {
                "role": "assistant",
                "content": [
                    {"type": "tool_use", "id": "t1", "name": "learn"},
                    {"type": "tool_use", "id": "t2", "name": "recall"},
                ],
            }
        ]

    def test_finds_by_id(self) -> None:
        msgs = self._make_messages()
        assert find_tool_name_by_id(msgs, "t1") == "learn"
        assert find_tool_name_by_id(msgs, "t2") == "recall"

    def test_unknown_id_returns_unknown(self) -> None:
        msgs = self._make_messages()
        assert find_tool_name_by_id(msgs, "t99") == "unknown"

    def test_empty_messages(self) -> None:
        assert find_tool_name_by_id([], "t1") == "unknown"

    def test_string_content_skipped(self) -> None:
        msgs = [{"role": "user", "content": "hello"}]
        assert find_tool_name_by_id(msgs, "t1") == "unknown"

    def test_object_blocks_work(self) -> None:
        block = SimpleNamespace(type="tool_use", id="t3", name="search")
        msgs = [{"role": "assistant", "content": [block]}]
        assert find_tool_name_by_id(msgs, "t3") == "search"

    def test_block_with_empty_name_returns_unknown(self) -> None:
        msgs = [{"role": "assistant", "content": [{"type": "tool_use", "id": "t4", "name": ""}]}]
        assert find_tool_name_by_id(msgs, "t4") == "unknown"


# ---------------------------------------------------------------------------
# base.py — is_retryable
# ---------------------------------------------------------------------------


class TestIsRetryable:
    def test_api_connection_error_retryable(self) -> None:
        exc = anthropic.APIConnectionError(request=MagicMock())
        assert is_retryable(exc) is True

    def test_httpx_transport_error_retryable(self) -> None:
        assert is_retryable(httpx.TransportError("timeout")) is True

    def test_os_error_retryable(self) -> None:
        assert is_retryable(OSError("broken pipe")) is True

    @pytest.mark.parametrize("status", sorted(RETRYABLE_STATUS))
    def test_anthropic_status_code_retryable(self, status: int) -> None:
        exc = MagicMock(spec=Exception)
        exc.status_code = status
        assert is_retryable(exc) is True

    def test_google_genai_code_retryable(self) -> None:
        exc = MagicMock(spec=Exception)
        del exc.status_code  # ensure attribute access falls through
        exc.status_code = None
        exc.code = 429
        assert is_retryable(exc) is True

    def test_httpx_response_status_retryable(self) -> None:
        exc = MagicMock(spec=Exception)
        exc.status_code = None
        exc.code = None
        exc.response = SimpleNamespace(status_code=503)
        assert is_retryable(exc) is True

    def test_non_retryable_status(self) -> None:
        exc = MagicMock(spec=Exception)
        exc.status_code = 400
        assert is_retryable(exc) is False

    def test_value_error_not_retryable(self) -> None:
        assert is_retryable(ValueError("bad input")) is False

    def test_404_not_retryable(self) -> None:
        exc = MagicMock(spec=Exception)
        exc.status_code = 404
        assert is_retryable(exc) is False


# ---------------------------------------------------------------------------
# base.py — with_retry
# ---------------------------------------------------------------------------


class TestWithRetry:
    def test_succeeds_on_first_try(self) -> None:
        calls: list[int] = []

        def fn() -> str:
            calls.append(1)
            return "ok"

        result = with_retry(fn)
        assert result == "ok"
        assert len(calls) == 1

    def test_non_retryable_propagates_immediately(self) -> None:
        calls: list[int] = []

        def fn() -> None:
            calls.append(1)
            raise ValueError("bad")

        with pytest.raises(ValueError, match="bad"):
            with_retry(fn)
        assert len(calls) == 1  # no retries for non-retryable

    def test_retryable_error_reraises_after_attempts(self) -> None:
        """With patched wait=0 so the test doesn't actually sleep."""
        import sakthai.agent.providers.base as base_mod

        original_attempts = base_mod.RETRY_ATTEMPTS
        base_mod.RETRY_ATTEMPTS = 2

        calls: list[int] = []

        def fn() -> None:
            calls.append(1)
            raise OSError("network")

        try:
            with pytest.raises(OSError):
                with_retry(fn)
        finally:
            base_mod.RETRY_ATTEMPTS = original_attempts

        assert len(calls) == 2


# ---------------------------------------------------------------------------
# anthropic_provider.py — call_anthropic
# ---------------------------------------------------------------------------


class TestCallAnthropic:
    def _fake_client(self, response: Any) -> Any:
        messages = MagicMock()
        messages.create.return_value = response
        client = MagicMock()
        client.messages = messages
        return client

    def _make_raw_response(self, stop_reason: str = "end_turn", text: str = "hello") -> Any:
        block = SimpleNamespace(type="text", text=text)
        return SimpleNamespace(stop_reason=stop_reason, content=[block])

    def test_non_streaming_returns_raw_response(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        raw = self._make_raw_response()
        client = self._fake_client(raw)
        result = call_anthropic(
            client, "claude-3", 1024, "sys", [], [{"role": "user", "content": "hi"}]
        )
        assert result is raw
        client.messages.create.assert_called_once()

    def test_non_streaming_passes_correct_params(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        raw = self._make_raw_response()
        client = self._fake_client(raw)
        call_anthropic(
            client,
            "claude-opus",
            2048,
            "system prompt",
            [{"name": "learn"}],
            [{"role": "user", "content": "hi"}],
        )
        kwargs = client.messages.create.call_args.kwargs
        assert kwargs["model"] == "claude-opus"
        assert kwargs["max_tokens"] == 2048
        assert kwargs["system"] == "system prompt"
        assert kwargs["tools"] == [{"name": "learn"}]

    def test_streaming_calls_on_token_and_returns_final(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        final_msg = self._make_raw_response(text="streamed")
        stream = MagicMock()
        stream.__enter__ = MagicMock(return_value=stream)
        stream.__exit__ = MagicMock(return_value=False)
        stream.text_stream = iter(["stre", "amed"])
        stream.get_final_message.return_value = final_msg

        client = MagicMock()
        client.messages.stream.return_value = stream

        tokens: list[str] = []
        result = call_anthropic(
            client,
            "claude-3",
            1024,
            "sys",
            [],
            [{"role": "user", "content": "hi"}],
            on_token=tokens.append,
        )
        assert result is final_msg
        assert tokens == ["stre", "amed"]

    def test_streaming_skips_empty_token(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        final_msg = self._make_raw_response()
        stream = MagicMock()
        stream.__enter__ = MagicMock(return_value=stream)
        stream.__exit__ = MagicMock(return_value=False)
        stream.text_stream = iter(["", "hello", ""])
        stream.get_final_message.return_value = final_msg

        client = MagicMock()
        client.messages.stream.return_value = stream

        tokens: list[str] = []
        call_anthropic(client, "claude-3", 1024, "sys", [], [], on_token=tokens.append)
        assert tokens == ["hello"]

    def test_api_error_raises_agent_error(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        client = MagicMock()
        client.messages.create.side_effect = anthropic.APIStatusError(
            "rate limit",
            response=MagicMock(status_code=400),
            body={},
        )

        with pytest.raises(AgentError, match="Anthropic API call failed"):
            call_anthropic(client, "claude-3", 1024, "sys", [], [])

    def test_os_error_raises_agent_error(self) -> None:
        from sakthai.agent.providers.anthropic_provider import call_anthropic

        client = MagicMock()
        client.messages.create.side_effect = OSError("broken pipe")

        with pytest.raises(AgentError, match="Anthropic API call failed"):
            call_anthropic(client, "claude-3", 1024, "sys", [], [])


# ---------------------------------------------------------------------------
# gemini_provider.py — to_gemini_contents & call_gemini (mocked google.genai)
# ---------------------------------------------------------------------------


def _install_fake_genai() -> MagicMock:
    """Insert a minimal fake google.genai into sys.modules so the provider can import it."""
    fake_types = MagicMock()

    def Part(**kwargs: Any) -> Any:
        return SimpleNamespace(**kwargs)

    def Content(**kwargs: Any) -> Any:
        return SimpleNamespace(**kwargs)

    def FunctionCall(**kwargs: Any) -> Any:
        return SimpleNamespace(**kwargs)

    def FunctionResponse(**kwargs: Any) -> Any:
        return SimpleNamespace(**kwargs)

    fake_types.Part = Part
    fake_types.Content = Content
    fake_types.FunctionCall = FunctionCall
    fake_types.FunctionResponse = FunctionResponse
    fake_types.Tool = MagicMock
    fake_types.FunctionDeclaration = MagicMock
    fake_types.GenerateContentConfig = MagicMock

    fake_genai = MagicMock()
    fake_genai.types = fake_types

    sys.modules["google"] = MagicMock()
    sys.modules["google.genai"] = fake_genai
    sys.modules["google.genai.types"] = fake_types
    return fake_genai


class TestToGeminiContents:
    def setup_method(self) -> None:
        self._fake_genai = _install_fake_genai()

    def _convert(self, messages: list[dict[str, Any]]) -> list[Any]:
        # Re-import after patching to pick up the mocked module
        import sakthai.agent.providers.gemini_provider as mod

        importlib.reload(mod)
        return mod.to_gemini_contents(messages)

    def test_string_content_user_message(self) -> None:
        result = self._convert([{"role": "user", "content": "hello"}])
        assert len(result) == 1
        assert result[0].role == "user"
        assert len(result[0].parts) == 1
        assert result[0].parts[0].text == "hello"

    def test_assistant_text_block(self) -> None:
        messages = [{"role": "assistant", "content": [{"type": "text", "text": "world"}]}]
        result = self._convert(messages)
        assert result[0].role == "model"
        assert result[0].parts[0].text == "world"

    def test_tool_use_block(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "t1", "name": "recall", "input": {"n": 5}}],
            }
        ]
        result = self._convert(messages)
        assert result[0].role == "model"
        part = result[0].parts[0]
        assert hasattr(part, "function_call")

    def test_tool_result_gets_tool_role(self) -> None:
        # First message establishes the tool_use id
        prior = [
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "t1", "name": "recall", "input": {}}],
            }
        ]
        tool_result_msg = {
            "role": "user",
            "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "result text"}],
        }
        messages = prior + [tool_result_msg]
        result = self._convert(messages)
        # last entry should have role "tool"
        assert result[-1].role == "tool"

    def test_empty_messages(self) -> None:
        result = self._convert([])
        assert result == []


class TestCallGemini:
    def setup_method(self) -> None:
        _install_fake_genai()

    def _make_tool(self, name: str = "recall") -> Any:
        from sakthai.agent.tools import Tool

        def handler(args: dict[str, Any], store: Any) -> str:
            return "ok"

        return Tool(
            name=name,
            description="desc",
            input_schema={"type": "object", "properties": {}},
            handler=handler,
        )

    def _make_candidate(
        self,
        text: str = "",
        function_calls: list[Any] | None = None,
        finish_reason: str = "STOP",
    ) -> Any:
        parts = []
        if text:
            parts.append(SimpleNamespace(text=text, function_calls=None))
        if function_calls:
            parts.append(SimpleNamespace(text=None, function_calls=function_calls))
        content = SimpleNamespace(parts=parts)
        return SimpleNamespace(content=content, finish_reason=finish_reason)

    def _call(self, candidates: list[Any]) -> Response:
        import sakthai.agent.providers.gemini_provider as mod

        importlib.reload(mod)

        raw = SimpleNamespace(candidates=candidates, usage_metadata=None)
        client = MagicMock()
        client.models.generate_content.return_value = raw

        return mod.call_gemini(
            client,
            "gemini-pro",
            "system",
            (self._make_tool(),),
            [{"role": "user", "content": "hi"}],
            iteration=0,
        )

    def test_text_response(self) -> None:
        resp = self._call([self._make_candidate(text="hello")])
        assert resp.stop_reason == "end_turn"
        assert len(resp.content) == 1
        assert resp.content[0].type == "text"
        assert resp.content[0].text == "hello"

    def test_no_candidates_raises_agent_error(self) -> None:
        import sakthai.agent.providers.gemini_provider as mod

        importlib.reload(mod)

        raw = SimpleNamespace(candidates=[], usage_metadata=None)
        client = MagicMock()
        client.models.generate_content.return_value = raw

        with pytest.raises(AgentError, match="no candidates"):
            mod.call_gemini(client, "gemini-pro", "sys", (), [], iteration=0)

    def test_function_call_stop_reason(self) -> None:
        fc = SimpleNamespace(name="recall", args={"n": 3})
        resp = self._call([self._make_candidate(function_calls=[fc])])
        assert resp.stop_reason == "tool_use"
        assert resp.content[0].type == "tool_use"
        assert resp.content[0].name == "recall"
        assert resp.content[0].input == {"n": 3}

    def test_max_tokens_finish_reason(self) -> None:
        resp = self._call([self._make_candidate(text="cut", finish_reason="MAX_TOKENS")])
        assert resp.stop_reason == "max_tokens"

    def test_api_failure_raises_agent_error(self) -> None:
        import sakthai.agent.providers.gemini_provider as mod

        importlib.reload(mod)

        client = MagicMock()
        client.models.generate_content.side_effect = RuntimeError("network")

        with pytest.raises(AgentError, match="Gemini API call failed"):
            mod.call_gemini(client, "gemini-pro", "sys", (), [], iteration=0)

    def test_generated_tool_use_id_contains_iteration(self) -> None:
        import sakthai.agent.providers.gemini_provider as mod

        importlib.reload(mod)

        fc = SimpleNamespace(name="recall", args={"n": 1})
        candidate = self._make_candidate(function_calls=[fc])
        raw = SimpleNamespace(candidates=[candidate], usage_metadata=None)
        client = MagicMock()
        client.models.generate_content.return_value = raw

        resp = mod.call_gemini(client, "gemini-pro", "sys", (), [], iteration=7)
        assert "7" in resp.content[0].id


# ---------------------------------------------------------------------------
# openai_provider.py — to_openai_messages
# ---------------------------------------------------------------------------


class TestToOpenAIMessages:
    def _convert(self, system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        from sakthai.agent.providers.openai_provider import to_openai_messages

        return to_openai_messages(system, messages)

    def test_system_message_prepended(self) -> None:
        result = self._convert("sys", [])
        assert result[0] == {"role": "system", "content": "sys"}

    def test_user_string_message(self) -> None:
        result = self._convert("sys", [{"role": "user", "content": "hello"}])
        assert result[1] == {"role": "user", "content": "hello"}

    def test_assistant_text_block(self) -> None:
        messages = [{"role": "assistant", "content": [{"type": "text", "text": "reply"}]}]
        result = self._convert("s", messages)
        msg = result[1]
        assert msg["role"] == "assistant"
        assert msg["content"] == "reply"
        assert "tool_calls" not in msg

    def test_assistant_tool_use_block(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "t1", "name": "recall", "input": {"n": 5}}],
            }
        ]
        result = self._convert("s", messages)
        msg = result[1]
        assert msg["role"] == "assistant"
        assert len(msg["tool_calls"]) == 1
        tc = msg["tool_calls"][0]
        assert tc["id"] == "t1"
        assert tc["type"] == "function"
        assert tc["function"]["name"] == "recall"
        assert json.loads(tc["function"]["arguments"]) == {"n": 5}

    def test_assistant_text_and_tool_use_combined(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": [
                    {"type": "text", "text": "sure, "},
                    {"type": "tool_use", "id": "t2", "name": "learn", "input": {}},
                ],
            }
        ]
        result = self._convert("s", messages)
        msg = result[1]
        assert msg["content"] == "sure, "
        assert len(msg["tool_calls"]) == 1

    def test_tool_result_block(self) -> None:
        messages = [
            {
                "role": "user",
                "content": [{"type": "tool_result", "tool_use_id": "t1", "content": "fact stored"}],
            }
        ]
        result = self._convert("s", messages)
        msg = result[1]
        assert msg["role"] == "tool"
        assert msg["tool_call_id"] == "t1"
        assert msg["content"] == "fact stored"

    def test_user_text_block_in_list_content(self) -> None:
        messages = [{"role": "user", "content": [{"type": "text", "text": "follow up"}]}]
        result = self._convert("s", messages)
        assert result[1] == {"role": "user", "content": "follow up"}

    def test_assistant_no_content_yields_none(self) -> None:
        messages = [
            {
                "role": "assistant",
                "content": [{"type": "tool_use", "id": "t3", "name": "x", "input": {}}],
            }
        ]
        result = self._convert("s", messages)
        assert result[1]["content"] is None


# ---------------------------------------------------------------------------
# openai_provider.py — _stream_chat
# ---------------------------------------------------------------------------


def _make_sse_stream(chunks: list[dict[str, Any]]) -> MagicMock:
    """Build a fake httpx streaming context manager from SSE data chunks."""
    lines = []
    for chunk in chunks:
        lines.append(f"data: {json.dumps(chunk)}")
    lines.append("data: [DONE]")

    resp = MagicMock()
    resp.iter_lines.return_value = iter(lines)
    resp.raise_for_status = MagicMock()

    client = MagicMock()
    client.stream.return_value.__enter__ = MagicMock(return_value=resp)
    client.stream.return_value.__exit__ = MagicMock(return_value=False)
    return client


class TestStreamChat:
    def _call(self, chunks: list[dict[str, Any]], on_token: Any = None) -> dict[str, Any]:
        from sakthai.agent.providers.openai_provider import _stream_chat

        if on_token is None:
            on_token = lambda t: None  # noqa: E731

        client = _make_sse_stream(chunks)
        return _stream_chat(client, {"model": "gpt-4"}, on_token)

    def test_text_content_reassembled(self) -> None:
        chunks = [
            {"choices": [{"delta": {"content": "hel"}, "finish_reason": None}], "usage": None},
            {"choices": [{"delta": {"content": "lo"}, "finish_reason": "stop"}], "usage": None},
            {"usage": {"prompt_tokens": 5, "completion_tokens": 2}},
        ]
        tokens: list[str] = []
        result = self._call(chunks, on_token=tokens.append)
        assert result["choices"][0]["message"]["content"] == "hello"
        assert tokens == ["hel", "lo"]

    def test_tool_call_reassembled_across_chunks(self) -> None:
        chunks = [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": "tc1",
                                    "function": {"name": "recall", "arguments": ""},
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ]
            },
            {
                "choices": [
                    {
                        "delta": {"tool_calls": [{"index": 0, "function": {"arguments": '{"n"'}}]},
                        "finish_reason": None,
                    }
                ]
            },
            {
                "choices": [
                    {
                        "delta": {"tool_calls": [{"index": 0, "function": {"arguments": ": 5}"}}]},
                        "finish_reason": "tool_calls",
                    }
                ]
            },
        ]
        result = self._call(chunks)
        tc = result["choices"][0]["message"]["tool_calls"][0]
        assert tc["id"] == "tc1"
        assert tc["function"]["name"] == "recall"
        assert json.loads(tc["function"]["arguments"]) == {"n": 5}

    def test_usage_extracted(self) -> None:
        chunks = [
            {"choices": [{"delta": {"content": "x"}, "finish_reason": "stop"}]},
            {"usage": {"prompt_tokens": 10, "completion_tokens": 3}},
        ]
        result = self._call(chunks)
        assert result["usage"]["prompt_tokens"] == 10

    def test_malformed_json_line_skipped(self) -> None:
        from sakthai.agent.providers.openai_provider import _stream_chat

        resp = MagicMock()
        resp.iter_lines.return_value = iter(
            [
                "data: not-json",
                "data: [DONE]",
            ]
        )
        resp.raise_for_status = MagicMock()
        client = MagicMock()
        client.stream.return_value.__enter__ = MagicMock(return_value=resp)
        client.stream.return_value.__exit__ = MagicMock(return_value=False)

        result = _stream_chat(client, {}, lambda t: None)
        assert result["choices"][0]["message"]["content"] is None

    def test_non_data_lines_skipped(self) -> None:
        from sakthai.agent.providers.openai_provider import _stream_chat

        resp = MagicMock()
        resp.iter_lines.return_value = iter(
            [
                "",
                ": keep-alive",
                "data: [DONE]",
            ]
        )
        resp.raise_for_status = MagicMock()
        client = MagicMock()
        client.stream.return_value.__enter__ = MagicMock(return_value=resp)
        client.stream.return_value.__exit__ = MagicMock(return_value=False)

        result = _stream_chat(client, {}, lambda t: None)
        assert result["choices"][0]["message"]["content"] is None

    def test_no_tool_calls_in_message_when_none_received(self) -> None:
        chunks = [
            {"choices": [{"delta": {"content": "ok"}, "finish_reason": "stop"}]},
        ]
        result = self._call(chunks)
        assert "tool_calls" not in result["choices"][0]["message"]

    def test_multiple_tool_calls_ordered_by_index(self) -> None:
        chunks = [
            {
                "choices": [
                    {
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 1,
                                    "id": "b",
                                    "function": {"name": "b", "arguments": "{}"},
                                },
                                {
                                    "index": 0,
                                    "id": "a",
                                    "function": {"name": "a", "arguments": "{}"},
                                },
                            ]
                        },
                        "finish_reason": "tool_calls",
                    }
                ]
            }
        ]
        result = self._call(chunks)
        tcs = result["choices"][0]["message"]["tool_calls"]
        assert tcs[0]["id"] == "a"
        assert tcs[1]["id"] == "b"


# ---------------------------------------------------------------------------
# openai_provider.py — call_openai_compat
# ---------------------------------------------------------------------------


class TestCallOpenAICompat:
    def _make_tool(self, name: str = "recall") -> Any:
        from sakthai.agent.tools import Tool

        def handler(args: dict[str, Any], store: Any) -> str:
            return "ok"

        return Tool(
            name=name,
            description="desc",
            input_schema={"type": "object", "properties": {}},
            handler=handler,
        )

    def _post_client(self, response_data: dict[str, Any]) -> MagicMock:
        resp = MagicMock()
        resp.raise_for_status = MagicMock()
        resp.json.return_value = response_data

        client = MagicMock(spec=["post"])
        client.post.return_value = resp
        return client

    def _make_response_data(
        self,
        text: str = "reply",
        finish_reason: str = "stop",
        tool_calls: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        message: dict[str, Any] = {"content": text, "tool_calls": tool_calls or []}
        return {"choices": [{"message": message, "finish_reason": finish_reason}], "usage": {}}

    def test_text_response_end_turn(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        client = self._post_client(self._make_response_data("hello", "stop"))
        result = call_openai_compat(client, "gpt-4", "sys", (self._make_tool(),), [], iteration=0)
        assert result.stop_reason == "end_turn"
        assert result.content[0].text == "hello"

    def test_tool_call_response(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        tc = {"id": "tc1", "function": {"name": "recall", "arguments": '{"n": 5}'}}
        data = self._make_response_data("", "tool_calls", tool_calls=[tc])
        client = self._post_client(data)
        result = call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)
        assert result.stop_reason == "tool_use"
        assert result.content[0].type == "tool_use"
        assert result.content[0].name == "recall"
        assert result.content[0].input == {"n": 5}

    def test_malformed_tool_call_json_defaults_to_empty(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        tc = {"id": "tc2", "function": {"name": "learn", "arguments": "not-json"}}
        data = self._make_response_data("", "tool_calls", tool_calls=[tc])
        client = self._post_client(data)
        result = call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)
        assert result.content[0].input == {}

    def test_finish_reason_length_maps_to_max_tokens(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        client = self._post_client(self._make_response_data("cut", "length"))
        result = call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)
        assert result.stop_reason == "max_tokens"

    def test_empty_choices_raises_agent_error(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        client = self._post_client({"choices": [], "usage": {}})
        with pytest.raises(AgentError, match="no choices"):
            call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)

    def test_generated_tool_id_when_missing(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        tc: dict[str, Any] = {"function": {"name": "recall", "arguments": "{}"}}
        data = self._make_response_data("", "tool_calls", tool_calls=[tc])
        client = self._post_client(data)
        result = call_openai_compat(client, "gpt-4", "sys", (), [], iteration=3)
        assert "recall" in result.content[0].id
        assert "3" in result.content[0].id

    def test_unsupported_client_raises_agent_error(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        bad_client = object()
        with pytest.raises(AgentError, match="Unsupported client"):
            call_openai_compat(bad_client, "gpt-4", "sys", (), [], iteration=0)

    def test_api_error_raises_agent_error(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        client = MagicMock(spec=["post"])
        client.post.side_effect = OSError("connection refused")
        with pytest.raises(AgentError, match="OpenAI-compatible API call failed"):
            call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)

    def test_streaming_path_chosen_when_on_token_and_stream(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        chunks = [
            {"choices": [{"delta": {"content": "hi"}, "finish_reason": "stop"}]},
        ]
        client = _make_sse_stream(chunks)

        tokens: list[str] = []
        result = call_openai_compat(
            client, "gpt-4", "sys", (), [], iteration=0, on_token=tokens.append
        )
        assert result.stop_reason == "end_turn"
        assert tokens == ["hi"]

    def test_tools_serialised_into_payload(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        tool = self._make_tool("recall")
        client = self._post_client(self._make_response_data())
        call_openai_compat(client, "gpt-4", "sys", (tool,), [], iteration=0)
        payload = client.post.call_args.kwargs["json"]
        assert payload["tools"][0]["function"]["name"] == "recall"

    def test_no_tools_omits_tools_key(self) -> None:
        from sakthai.agent.providers.openai_provider import call_openai_compat

        client = self._post_client(self._make_response_data())
        call_openai_compat(client, "gpt-4", "sys", (), [], iteration=0)
        payload = client.post.call_args.kwargs["json"]
        assert "tools" not in payload
