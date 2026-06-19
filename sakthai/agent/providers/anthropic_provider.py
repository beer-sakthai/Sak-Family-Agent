"""Anthropic (Claude) provider backend."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import anthropic

from .base import AgentError, logger, with_retry


def _get_request_executor(
    client: Any,
    model: str,
    max_tokens: int,
    system: str,
    tool_schemas: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    on_token: Callable[[str], None] | None = None,
) -> Callable[[], Any]:
    """Return a zero-arg callable that makes the Anthropic request."""

    def _create() -> Any:
        return client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tool_schemas,
            messages=messages,
        )

    def _stream() -> Any:
        with client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system,
            tools=tool_schemas,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                if text and on_token is not None:
                    on_token(text)
            return stream.get_final_message()

    return _stream if on_token is not None else _create


def call_anthropic(
    client: Any,
    model: str,
    max_tokens: int,
    system: str,
    tool_schemas: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    on_token: Callable[[str], None] | None = None,
) -> Any:
    """Make one Claude Messages API call, returning the raw SDK response.

    When ``on_token`` is provided, the response is streamed via
    ``client.messages.stream`` and each text delta is forwarded to the callback;
    the assembled final message is returned, identical in shape to the
    non-streaming ``messages.create`` response.
    """
    _do_request = _get_request_executor(
        client, model, max_tokens, system, tool_schemas, messages, on_token
    )

    try:
        return with_retry(_do_request)
    except (anthropic.APIError, OSError) as exc:
        logger.error("Anthropic API call failed: %s", exc)
        raise AgentError(f"Anthropic API call failed: {exc}") from exc
