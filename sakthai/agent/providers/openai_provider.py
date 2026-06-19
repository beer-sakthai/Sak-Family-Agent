"""OpenAI-compatible / Ollama provider backend."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..tools import Tool
from ..usage import extract_usage
from .base import AgentError, Block, Response, block_field, logger, with_retry


def _to_openai_assistant_msg(content: list[dict[str, Any]]) -> dict[str, Any]:
    """Format assistant message blocks into OpenAI assistant message."""
    text_content = ""
    tool_calls = []
    for block in content:
        block_type = block_field(block, "type")
        if block_type == "text":
            text_content += block_field(block, "text")
        elif block_type == "tool_use":
            tool_calls.append(
                {
                    "id": block_field(block, "id"),
                    "type": "function",
                    "function": {
                        "name": block_field(block, "name"),
                        "arguments": json.dumps(block_field(block, "input", {})),
                    },
                }
            )
    item: dict[str, Any] = {"role": "assistant"}
    item["content"] = text_content or None
    if tool_calls:
        item["tool_calls"] = tool_calls
    return item


def _to_openai_other_msgs(role: str, content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format user or tool blocks into OpenAI message list."""
    msgs = []
    for block in content:
        block_type = block_field(block, "type")
        if block_type == "tool_result":
            msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": block_field(block, "tool_use_id"),
                    "content": block_field(block, "content"),
                }
            )
        else:
            text = block_field(block, "text")
            if text:
                msgs.append({"role": "user", "content": text})
    return msgs


def to_openai_messages(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Adapt the provider-agnostic message list to the OpenAI chat schema."""
    openai_msgs: list[dict[str, Any]] = [{"role": "system", "content": system}]

    for msg in messages:
        role = msg["role"]
        content = msg["content"]

        if isinstance(content, str):
            openai_msgs.append({"role": role, "content": content})
        elif isinstance(content, list):
            if role == "assistant":
                openai_msgs.append(_to_openai_assistant_msg(content))
            else:
                openai_msgs.extend(_to_openai_other_msgs(role, content))
    return openai_msgs


def _update_tool_calls_from_delta(
    tool_calls: dict[int, dict[str, Any]], delta_tool_calls: list[dict[str, Any]]
) -> None:
    """Update accumulated tool calls with fragments from a stream delta."""
    for tc in delta_tool_calls:
        idx = tc.get("index", 0)
        slot = tool_calls.setdefault(idx, {"id": "", "function": {"name": "", "arguments": ""}})
        if tc.get("id"):
            slot["id"] = tc["id"]
        fn = tc.get("function") or {}
        if fn.get("name"):
            slot["function"]["name"] = fn["name"]
        if fn.get("arguments"):
            slot["function"]["arguments"] += fn["arguments"]


def _process_stream_choice(
    choice: dict[str, Any],
    content_parts: list[str],
    tool_calls: dict[int, dict[str, Any]],
    on_token: Callable[[str], None],
) -> str | None:
    """Process a single choice from a stream chunk, updating state."""
    delta = choice.get("delta") or {}
    text = delta.get("content")
    if text:
        content_parts.append(text)
        on_token(text)

    delta_tool_calls = delta.get("tool_calls")
    if delta_tool_calls:
        _update_tool_calls_from_delta(tool_calls, delta_tool_calls)

    return choice.get("finish_reason")


def _stream_chat(
    client: Any, payload: dict[str, Any], on_token: Callable[[str], None]
) -> dict[str, Any]:
    """Consume an OpenAI-compatible SSE stream into a non-streaming response dict.

    Text deltas are forwarded to ``on_token`` as they arrive; tool-call fragments
    (which arrive split across chunks) are reassembled by index. The returned
    dict has the same shape as a normal chat-completion response so the caller's
    parsing is identical for both paths.
    """
    stream_payload = {**payload, "stream": True, "stream_options": {"include_usage": True}}
    content_parts: list[str] = []
    tool_calls: dict[int, dict[str, Any]] = {}
    finish_reason: str | None = None
    usage: dict[str, Any] = {}

    with client.stream("POST", "/chat/completions", json=stream_payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line or not line.startswith("data:"):
                continue
            data_str = line[len("data:") :].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except Exception:
                chunk = None
            if not isinstance(chunk, dict):
                continue
            if chunk.get("usage"):
                usage = chunk["usage"]
            for choice in chunk.get("choices") or []:
                fr = _process_stream_choice(choice, content_parts, tool_calls, on_token)
                if fr:
                    finish_reason = fr

    message: dict[str, Any] = {"content": "".join(content_parts) or None}
    if tool_calls:
        message["tool_calls"] = [tool_calls[i] for i in sorted(tool_calls)]
    return {"choices": [{"message": message, "finish_reason": finish_reason}], "usage": usage}


def _format_openai_tools(tools: tuple[Tool, ...]) -> list[dict[str, Any]]:
    """Convert internal Tool objects to OpenAI function schema."""
    return [
        {
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": t.input_schema,
            },
        }
        for t in tools
    ]


def _get_request_executor(
    client: Any,
    payload: dict[str, Any],
    on_token: Callable[[str], None] | None = None,
) -> Callable[[], dict[str, Any]]:
    """Determine and return the appropriate request execution function."""
    if on_token is not None and hasattr(client, "stream"):
        return lambda: _stream_chat(client, payload, on_token)

    if hasattr(client, "post"):

        def _do_post() -> dict[str, Any]:
            resp = client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

        return _do_post

    if hasattr(client, "chat") and hasattr(client.chat, "completions"):

        def _do_openai() -> dict[str, Any]:
            raw = client.chat.completions.create(**payload)
            return raw.model_dump()  # type: ignore[no-any-return]

        return _do_openai

    raise AgentError(f"Unsupported client type: {type(client)}")


def _parse_openai_tool_call(tc: dict[str, Any], iteration: int, idx: int) -> Block:
    """Parse a single OpenAI tool call into a tool_use Block."""
    fn = tc.get("function") or {}
    fn_name = fn.get("name")
    if not isinstance(fn_name, str):
        fn_name = ""

    fn_args_raw = fn.get("arguments") or "{}"
    if isinstance(fn_args_raw, str):
        try:
            fn_args = json.loads(fn_args_raw)
        except Exception:
            fn_args = {}
    else:
        fn_args = fn_args_raw

    tool_id = tc.get("id") or f"call_{fn_name}_{iteration}_{idx}"
    return Block("tool_use", id=tool_id, name=fn_name, input=dict(fn_args or {}))


def _map_openai_stop_reason(finish_reason: str | None, has_tool_call: bool) -> str:
    """Map OpenAI finish reason to provider-agnostic stop reason."""
    if has_tool_call:
        return "tool_use"
    if finish_reason == "length":
        return "max_tokens"
    return "end_turn"


def _parse_openai_response(data: dict[str, Any], iteration: int) -> Response:
    """Convert raw OpenAI response dictionary to a Response object."""
    choices = data.get("choices") or []
    if not choices:
        raise AgentError("OpenAI returned no choices.")

    choice = choices[0]
    message_data = choice.get("message") or {}
    content_text = message_data.get("content") or ""
    tool_calls_data = message_data.get("tool_calls") or []
    finish_reason = choice.get("finish_reason")

    blocks: list[Any] = []
    if content_text:
        blocks.append(Block("text", text=content_text))

    for idx, tc in enumerate(tool_calls_data):
        blocks.append(_parse_openai_tool_call(tc, iteration, idx))

    stop_reason = _map_openai_stop_reason(finish_reason, bool(tool_calls_data))

    return Response(stop_reason=stop_reason, content=blocks, usage=extract_usage(data))


def call_openai_compat(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    on_token: Callable[[str], None] | None = None,
) -> Response:
    """Make one OpenAI-compatible chat completion, normalised to :class:`Response`.

    When ``on_token`` is set and the client supports streaming (``client.stream``),
    the reply is consumed as Server-Sent Events and text deltas are forwarded to
    the callback; otherwise a single non-streaming request is made.
    """
    openai_tools = _format_openai_tools(tools)

    payload: dict[str, Any] = {
        "model": model,
        "messages": to_openai_messages(system, messages),
        "stream": False,
    }
    if openai_tools:
        payload["tools"] = openai_tools

    _do_request = _get_request_executor(client, payload, on_token)

    try:
        data = with_retry(_do_request)
    except Exception as exc:
        logger.error("OpenAI-compatible API call failed: %s", exc)
        raise AgentError(f"OpenAI-compatible API call failed: {exc}") from exc

    return _parse_openai_response(data, iteration)
