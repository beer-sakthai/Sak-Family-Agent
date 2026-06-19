"""OpenAI-compatible / Ollama provider backend."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..tools import Tool
from ..usage import extract_usage
from .base import AgentError, Block, Response, block_field, logger, with_retry


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
                openai_msgs.append(_format_assistant_message(content))
            else:
                openai_msgs.extend(_format_user_or_tool_messages(role, content))
    return openai_msgs


def _format_assistant_message(content: list[dict[str, Any]]) -> dict[str, Any]:
    """Format an assistant message from blocks."""
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


def _format_user_or_tool_messages(role: str, content: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Format user or tool messages from blocks."""
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
                msgs.append({"role": role, "content": text})
    return msgs


def _stream_chat(
    client: Any, payload: dict[str, Any], on_token: Callable[[str], None]
) -> dict[str, Any]:
    """Consume an OpenAI-compatible SSE stream into a non-streaming response dict."""
    stream_payload = {**payload, "stream": True, "stream_options": {"include_usage": True}}
    content_parts: list[str] = []
    tool_calls: dict[int, dict[str, Any]] = {}
    finish_reason: str | None = None
    usage: dict[str, Any] = {}

    with client.stream("POST", "/chat/completions", json=stream_payload) as resp:
        resp.raise_for_status()
        for line in resp.iter_lines():
            if not line.startswith("data:"):
                continue
            data_str = line[len("data:") :].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
            except Exception:
                continue

            if chunk.get("usage"):
                usage = chunk["usage"]

            for choice in chunk.get("choices") or []:
                delta = choice.get("delta") or {}
                if text := delta.get("content"):
                    content_parts.append(text)
                    on_token(text)

                for tc in delta.get("tool_calls") or []:
                    _process_tool_call_chunk(tool_calls, tc)

                if choice.get("finish_reason"):
                    finish_reason = choice["finish_reason"]

    message: dict[str, Any] = {"content": "".join(content_parts) or None}
    if tool_calls:
        message["tool_calls"] = [tool_calls[i] for i in sorted(tool_calls)]
    return {"choices": [{"message": message, "finish_reason": finish_reason}], "usage": usage}


def _process_tool_call_chunk(tool_calls: dict[int, dict[str, Any]], tc: dict[str, Any]) -> None:
    """Update reassembled tool calls from a stream chunk."""
    idx = tc.get("index", 0)
    slot = tool_calls.setdefault(idx, {"id": "", "function": {"name": "", "arguments": ""}})
    if tc.get("id"):
        slot["id"] = tc["id"]
    fn = tc.get("function") or {}
    if fn.get("name"):
        slot["function"]["name"] = fn["name"]
    if fn.get("arguments"):
        slot["function"]["arguments"] += fn["arguments"]


def call_openai_compat(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    on_token: Callable[[str], None] | None = None,
) -> Response:
    """Make one OpenAI-compatible chat completion, normalised to :class:`Response`."""
    payload = _prepare_payload(model, system, messages, tools)
    executor = _get_request_executor(client, payload, on_token)

    try:
        data = with_retry(executor)
    except Exception as exc:
        logger.error("OpenAI-compatible API call failed: %s", exc)
        raise AgentError(f"OpenAI-compatible API call failed: {exc}") from exc

    return _parse_response(data, iteration)


def _prepare_payload(
    model: str, system: str, messages: list[dict[str, Any]], tools: tuple[Tool, ...]
) -> dict[str, Any]:
    """Construct the API request payload."""
    payload: dict[str, Any] = {
        "model": model,
        "messages": to_openai_messages(system, messages),
        "stream": False,
    }
    if tools:
        payload["tools"] = [
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
    return payload


def _get_request_executor(
    client: Any, payload: dict[str, Any], on_token: Callable[[str], None] | None
) -> Callable[[], dict[str, Any]]:
    """Determine how to call the client and return a callable executor."""
    if on_token is not None and hasattr(client, "stream"):
        return lambda: _stream_chat(client, payload, on_token)

    if hasattr(client, "post"):

        def _do_post() -> dict[str, Any]:
            resp = client.post("/chat/completions", json=payload)
            resp.raise_for_status()
            return resp.json()  # type: ignore[no-any-return]

        return _do_post

    if hasattr(client, "chat") and hasattr(client.chat, "completions"):

        def _do_sdk() -> dict[str, Any]:
            raw = client.chat.completions.create(**payload)
            return raw.model_dump()  # type: ignore[no-any-return]

        return _do_sdk

    raise AgentError(f"Unsupported client type: {type(client)}")


def _parse_response(data: dict[str, Any], iteration: int) -> Response:
    """Convert OpenAI API response into a Response object."""
    choices = data.get("choices") or []
    if not choices:
        raise AgentError("OpenAI returned no choices.")

    choice = choices[0]
    message_data = choice.get("message") or {}
    content_text = message_data.get("content") or ""
    tool_calls_data = message_data.get("tool_calls") or []
    finish_reason = choice.get("finish_reason")

    blocks: list[Block] = []
    if content_text:
        blocks.append(Block("text", text=content_text))

    has_tool_call = False
    for idx, tc in enumerate(tool_calls_data):
        has_tool_call = True
        blocks.append(_parse_tool_call(tc, iteration, idx))

    stop_reason = "end_turn"
    if has_tool_call:
        stop_reason = "tool_use"
    elif finish_reason == "length":
        stop_reason = "max_tokens"

    return Response(stop_reason=stop_reason, content=blocks, usage=extract_usage(data))


def _parse_tool_call(tc: dict[str, Any], iteration: int, idx: int) -> Block:
    """Parse a single tool call from the API response."""
    fn = tc.get("function") or {}
    name = fn.get("name") or ""
    args_raw = fn.get("arguments") or "{}"

    if isinstance(args_raw, str):
        try:
            args = json.loads(args_raw)
        except Exception:
            args = {}
    else:
        args = args_raw

    tool_id = tc.get("id") or f"call_{name}_{iteration}_{idx}"
    return Block("tool_use", id=tool_id, name=name, input=dict(args or {}))
