"""Gateway provider adapter for the SakThai agent loop.

Connects the agent loop to the local or remote Runtime Gateway, adapting tool schemas,
system prompts, and response envelopes.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..tools import Tool
from .base import Response
from .openai_provider import call_openai_compat


def call_gateway(
    client: Any,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int = 0,
    on_token: Callable[[str], None] | None = None,
) -> Response:
    """Execute a chat completion request against the Runtime Gateway."""
    return call_openai_compat(
        client=client,
        model=model,
        system=system,
        tools=tools,
        messages=messages,
        iteration=iteration,
        on_token=on_token,
    )
