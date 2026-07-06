"""Shared building blocks for the provider backends.

Holds the pieces every provider needs: the normalised response types
(:class:`Block` / :class:`Response`), the transient-failure retry policy, and a
couple of message-adaptation helpers. Provider modules depend on this module;
this module depends on no other agent module, so there is no import cycle.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

import anthropic
import httpx
import tenacity

logger = logging.getLogger("sakthai.agent.providers")


class AgentError(RuntimeError):
    """Raised when a run cannot proceed (missing credential, API failure, …)."""


class Block:
    """Normalised content block (text or tool_use) across providers."""

    def __init__(
        self,
        block_type: str,
        *,
        text: str = "",
        id: str = "",
        name: str = "",
        input: dict[str, Any] | None = None,
    ) -> None:
        self.type = block_type
        self.text = text
        self.id = id
        self.name = name
        self.input = input or {}


class Response:
    """Normalised model response: a stop_reason plus a list of content blocks."""

    def __init__(
        self,
        stop_reason: str,
        content: list[Any],
        usage: dict[str, int] | None = None,
    ) -> None:
        self.stop_reason = stop_reason
        self.content = content
        self.usage = usage or {"input_tokens": 0, "output_tokens": 0}


# -- transient-failure retry policy -------------------------------------

# Wait constants are module-level so tests can zero them out to avoid real sleeps.
RETRY_ATTEMPTS = 3
RETRY_WAIT_MULTIPLIER = 0.5
RETRY_WAIT_MAX = 8.0
RETRYABLE_STATUS = frozenset({408, 409, 429, 500, 502, 503, 504})


def is_retryable(exc: BaseException) -> bool:
    """True for transient API failures worth retrying (rate limit, 5xx, network)."""
    if isinstance(exc, anthropic.APIConnectionError | httpx.TransportError | OSError):
        return True
    # HTTP status surfaced differently across SDKs: anthropic uses ``status_code``,
    # google-genai uses ``code``, httpx exposes it on ``response``.
    status: Any = getattr(exc, "status_code", None)
    if status is None:
        status = getattr(exc, "code", None)
    if status is None:
        status = getattr(getattr(exc, "response", None), "status_code", None)
    return isinstance(status, int) and status in RETRYABLE_STATUS


def with_retry(fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
    """Call ``fn`` with exponential-backoff retries on transient failures.

    Non-retryable errors (bad request, auth, not found) propagate on the first
    attempt; the original exception is re-raised once attempts are exhausted.
    """
    retryer = tenacity.Retrying(
        retry=tenacity.retry_if_exception(is_retryable),
        stop=tenacity.stop_after_attempt(RETRY_ATTEMPTS),
        wait=tenacity.wait_exponential(multiplier=RETRY_WAIT_MULTIPLIER, max=RETRY_WAIT_MAX),
        reraise=True,
    )
    return retryer(fn, *args, **kwargs)


# -- message-adaptation helpers (shared by openai + gemini) -------------


def block_field(block: Any, field_name: str, default: Any = "") -> Any:
    """Read a field from a block whether it is a dict or an attribute object."""
    if isinstance(block, dict):
        return block.get(field_name, default)
    return getattr(block, field_name, default)


def find_tool_name_by_id(messages: list[dict[str, Any]], tool_use_id: str) -> str:
    """Look up the tool name that produced ``tool_use_id`` in prior messages."""
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if block_field(block, "type") != "tool_use":
                continue
            if block_field(block, "id") == tool_use_id:
                return block_field(block, "name") or "unknown"
    return "unknown"
