"""Provider backends for the agent loop.

Each provider lives in its own module and owns its API call, message adaptation,
and retry handling. This package also resolves *which* provider to use
(:func:`detect_provider`) and builds its client (:func:`build_client`), keeping
all provider-specific concerns out of the orchestration loop.
"""

from __future__ import annotations

import os
from typing import Any

from ...auth import (
    AuthError,
    anthropic_credential_source,
    openai_credential_source,
    resolve_anthropic_client,
)
from .anthropic_provider import call_anthropic
from .base import (
    AgentError,
    Block,
    Response,
    block_field,
    find_tool_name_by_id,
    is_retryable,
    with_retry,
)
from .gemini_provider import call_gemini, to_gemini_contents
from .openai_provider import call_openai_compat, to_openai_messages

__all__ = [
    "AgentError",
    "Block",
    "Response",
    "block_field",
    "build_client",
    "call_anthropic",
    "call_gemini",
    "call_openai_compat",
    "detect_provider",
    "find_tool_name_by_id",
    "is_retryable",
    "to_gemini_contents",
    "to_openai_messages",
    "with_retry",
]


def detect_provider(client: Any | None, model: str) -> str:
    """Choose a provider when the caller didn't.

    A Gemini model name or google-genai client → ``google``;
    an openai client or `openai`/`ollama`/`gpt` in model name → ``openai``;
    any other injected client → ``anthropic``;
    otherwise pick whichever credential is present: anthropic → google → openai.
    """
    client_module = client.__class__.__module__ if client is not None else ""
    if "google.genai" in client_module or "gemini" in model.lower():
        return "google"
    if "openai" in client_module:
        return "openai"
    if any(
        keyword in model.lower()
        for keyword in ("openai", "ollama", "gpt-", "qwen", "llama", "deepseek", "mistral", "gemma")
    ):
        return "openai"
    if client is not None:
        return "anthropic"
    if anthropic_credential_source() is not None:
        return "anthropic"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "google"
    if openai_credential_source() is not None:
        return "openai"
    return "anthropic"


def build_client(provider: str, client: Any | None) -> Any:
    """Construct the SDK client for ``provider``, or return an injected one.

    Missing or unusable credentials raise :class:`AgentError` with a clear
    message rather than a raw SDK traceback.
    """
    if client is not None:
        return client
    if provider == "google":
        from google import genai

        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise AgentError(
                "Missing credentials for Google Gemini "
                "(GEMINI_API_KEY or GOOGLE_API_KEY must be set)."
            )
        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:
            raise AgentError(f"Failed to initialize Google Gemini client: {exc}") from exc
    if provider == "openai":
        import httpx

        from ...auth import resolve_openai_credentials

        try:
            api_base, api_key = resolve_openai_credentials()
        except AuthError as exc:
            raise AgentError(str(exc)) from exc
        return httpx.Client(
            base_url=api_base,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
    try:
        return resolve_anthropic_client()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc
