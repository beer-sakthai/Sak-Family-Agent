"""OpenAI-compatible LLM provider implementation."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..tools import Tool
from ..usage import extract_usage
from .base import AgentError, Block, Response, block_field, logger, with_retry


def _convert_assistant_blocks(content: list[dict[str, Any]]) -> dict[str, Any]:
    """Convert assistant message blocks to OpenAI schema."""
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
    item: dict[str, Any] = {"role": "assistant", "content": text_content or None}
    if tool_calls:
        item["tool_calls"] = tool_calls
    return item


def _convert_other_blocks(role: str, content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert non-assistant message blocks to OpenAI schema."""
    openai_msgs = []
    for block in content:
        block_type = block_field(block, "type")
        if block_type == "tool_result":
            openai_msgs.append(
                {
                    "role": "tool",
                    "tool_call_id": block_field(block, "tool_use_id"),
                    "content": block_field(block, "content"),
                }
            )
        else:
            text = block_field(block, "text")
            if text:
                openai_msgs.append({"role": role, "content": text})
    return openai_msgs


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
                openai_msgs.append(_convert_assistant_blocks(content))
            else:
                openai_msgs.extend(_convert_other_blocks(role, content))
    return openai_msgs


def _process_stream_chunk(
    chunk: dict[str, Any],
    content_parts: list[str],
    tool_calls: dict[int, dict[str, Any]],
    on_token: Callable[[str], None],
) -> tuple[str | None, dict[str, Any]]:
    """Process a single SSE chunk from the OpenAI stream."""
    finish_reason: str | None = None
    usage: dict[str, Any] = chunk.get("usage") or {}

    for choice in chunk.get("choices") or []:
        delta = choice.get("delta") or {}
        text = delta.get("content")
        if text:
            content_parts.append(text)
            on_token(text)

        for tc in delta.get("tool_calls") or []:
            index = tc.get("index", 0)
            slot = tool_calls.setdefault(
                index, {"id": "", "function": {"name": "", "arguments": ""}}
            )
            if tc.get("id"):
                slot["id"] = tc["id"]
            fn = tc.get("function") or {}
            if fn.get("name"):
                slot["function"]["name"] = fn["name"]
            if fn.get("arguments"):
                slot["function"]["arguments"] += fn["arguments"]

        if choice.get("finish_reason"):
            finish_reason = choice["finish_reason"]

    return finish_reason, usage


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
                continue
            if not isinstance(chunk, dict):
                continue

            f_reason, u = _process_stream_chunk(chunk, content_parts, tool_calls, on_token)
            if f_reason:
                finish_reason = f_reason
            if u:
                usage = u

    message: dict[str, Any] = {"content": "".join(content_parts) or None}
    if tool_calls:
        message["tool_calls"] = [tool_calls[i] for i in sorted(tool_calls)]
    return {"choices": [{"message": message, "finish_reason": finish_reason}], "usage": usage}


def _prepare_openai_tools(tools: tuple[Tool, ...]) -> list[dict[str, Any]]:
    """Convert Tool objects to OpenAI function schemas."""
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


def _parse_tool_calls(tool_calls_data: list[dict[str, Any]], iteration: int) -> list[Block]:
    """Parse OpenAI tool calls into provider-agnostic Blocks."""
    blocks = []
    for idx, tc in enumerate(tool_calls_data):
        fn = tc.get("function") or {}
        fn_name = fn.get("name") or ""
        fn_args_raw = fn.get("arguments") or "{}"

        if isinstance(fn_args_raw, str):
            try:
                fn_args = json.loads(fn_args_raw)
            except Exception:
                fn_args = {}
        else:
            fn_args = fn_args_raw

        tool_id = tc.get("id") or f"call_{fn_name}_{iteration}_{idx}"
        blocks.append(Block("tool_use", id=tool_id, name=fn_name, input=dict(fn_args or {})))
    return blocks


def _get_stop_reason(finish_reason: str | None, has_tool_call: bool) -> str:
    """Determine the provider-agnostic stop reason."""
    if has_tool_call:
        return "tool_use"
    if finish_reason == "length":
        return "max_tokens"
    return "end_turn"


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
    openai_tools = _prepare_openai_tools(tools)
    payload: dict[str, Any] = {
        "model": model,
        "messages": to_openai_messages(system, messages),
        "stream": False,
    }
    if openai_tools:
        payload["tools"] = openai_tools

    _do_request: Callable[[], dict[str, Any]]
    if on_token is not None and hasattr(client, "stream"):

        def _do_request() -> dict[str, Any]:
            return _stream_chat(client, payload, on_token)

    elif hasattr(client, "post"):

        def _do_request() -> dict[str, Any]:
            resp = client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

    elif hasattr(client, "chat") and hasattr(client.chat, "completions"):

        def _do_request() -> dict[str, Any]:
            return client.chat.completions.create(**payload).model_dump()  # type: ignore[no-any-return]

    else:
        raise AgentError(f"Unsupported client type: {type(client)}")

    try:
        data = with_retry(_do_request)
    except Exception as exc:
        logger.error("OpenAI-compatible API call failed: %s", exc)
        raise AgentError(f"OpenAI-compatible API call failed: {exc}") from exc

    choices = data.get("choices") or []
    if not choices:
        raise AgentError("OpenAI returned no choices.")
    choice = choices[0]
    message_data = choice.get("message") or {}
    content_text = message_data.get("content") or ""
    tool_calls_data = message_data.get("tool_calls") or []

    blocks: list[Block] = []
    if content_text:
        blocks.append(Block("text", text=content_text))

    tool_blocks = _parse_tool_calls(tool_calls_data, iteration)
    blocks.extend(tool_blocks)

    stop_reason = _get_stop_reason(choice.get("finish_reason"), bool(tool_blocks))
    return Response(stop_reason=stop_reason, content=blocks, usage=extract_usage(data))
