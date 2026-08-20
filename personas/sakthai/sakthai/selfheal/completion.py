"""One-shot text completion over the package's existing provider abstraction.

The self-healing pipeline needs two single-turn model calls — a diagnosis and a
PR walkthrough — not a tool-using agent loop. Rather than stand up a second
provider stack, this module reuses ``agent.providers`` and collapses it to the
shape those two calls actually need::

    completion(system, user) -> str

Everything downstream depends on that alias, never on a provider SDK, which is
what lets the whole pipeline be tested with a two-line stub.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from ..agent.providers import (
    build_client,
    call_anthropic,
    call_gemini,
    call_openai_compat,
    detect_provider,
)
from ..agent.providers.base import block_field

Completion = Callable[[str, str], str]

DEFAULT_MAX_TOKENS = 4_000


def _extract_text(content: Any) -> str:
    """Join the text blocks of a normalised (or raw Anthropic) response."""
    parts: list[str] = []
    for block in content or []:
        if block_field(block, "type") == "text":
            parts.append(str(block_field(block, "text")))
    return "\n".join(part for part in parts if part).strip()


def build_completion(
    *,
    provider: str | None = None,
    model: str,
    client: Any | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
) -> Completion:
    """Build a one-shot completion callable for ``model``.

    ``client`` is injectable for tests and for callers that already hold one;
    when it is ``None`` the provider is detected and its client built the same
    way the agent loop does it.
    """
    resolved_provider = provider or detect_provider(client, model)
    sdk_client = build_client(resolved_provider, client)

    def complete(system: str, user: str) -> str:
        messages: list[dict[str, Any]] = [{"role": "user", "content": user}]
        if resolved_provider == "google":
            response = call_gemini(sdk_client, model, system, (), messages, 0)
            return _extract_text(response.content)
        if resolved_provider == "anthropic":
            raw = call_anthropic(sdk_client, model, max_tokens, system, [], messages)
            return _extract_text(getattr(raw, "content", []))
        response = call_openai_compat(sdk_client, model, system, (), messages, 0)
        return _extract_text(response.content)

    return complete
