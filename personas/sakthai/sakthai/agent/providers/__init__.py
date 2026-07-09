"""Provider backends for the agent loop.

Each provider lives in its own module and owns its API call, message adaptation,
and retry handling. This package also resolves *which* provider to use
(:func:`detect_provider`) and builds its client (:func:`build_client`), keeping
all provider-specific concerns out of the orchestration loop.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from ...auth import (
    AuthError,
    anthropic_credential_source,
    gateway_credential_source,
    local_credential_source,
    openai_credential_source,
    resolve_anthropic_client,
    resolve_local_credentials,
    resolve_ollama_credentials,
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

OPENAI_COMPAT_KEYWORDS = {
    "openai",
    "gpt-",
    "qwen",
    "llama",
    "deepseek",
    "mistral",
    "gemma",
}


def _detect_from_model_name(model: str) -> str | None:
    """Detect provider from model name hints."""
    model_lower = model.lower()
    if model_lower.startswith("gateway"):
        return "gateway"
    if model_lower.startswith("local/"):
        return "local"
    if "ollama" in model_lower:
        return "ollama"
    if "gemini" in model_lower:
        return "google"
    if any(keyword in model_lower for keyword in OPENAI_COMPAT_KEYWORDS):
        return "openai"
    return None


def _detect_from_client_type(client: Any) -> str | None:
    """Detect provider from the type of an injected client."""
    if client is None:
        return None
    module = client.__class__.__module__
    if "google.genai" in module:
        return "google"
    if "openai" in module:
        return "openai"
    # Any other client is assumed to be Anthropic-compatible.
    return "anthropic"


def _detect_from_credentials() -> str | None:
    """Detect provider by checking for available credentials."""
    if gateway_credential_source() is not None:
        return "gateway"
    if local_credential_source() is not None:
        return "local"
    if os.environ.get("OLLAMA_HOST"):
        return "ollama"
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "google"
    if openai_credential_source() is not None:
        return "openai"
    if anthropic_credential_source() is not None:
        return "anthropic"
    return None


def detect_provider(client: Any | None, model: str) -> str:
    """Choose a provider when the caller didn't.

    Detection runs in priority order: an explicit model-name hint
    (``gateway``/``local/``/``ollama``/``gemini``/OpenAI-compat keywords) wins
    first, then the type of an injected client, then whichever credential is
    configured. Falls back to ``anthropic`` when nothing else matches.
    """
    # The order of these checks defines the detection priority.
    checks: list[Callable[[], str | None]] = [
        lambda: _detect_from_model_name(model),
        lambda: _detect_from_client_type(client),
        _detect_from_credentials,
    ]

    for check in checks:
        if provider := check():
            return provider

    return "anthropic"


def _openai_compat_client(api_base: str, api_key: str) -> Any:
    """Build an httpx client for an OpenAI-compatible endpoint (OpenAI/Ollama/gateway)."""
    import httpx

    return httpx.Client(
        base_url=api_base,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        timeout=120.0,
    )


def _build_google_client() -> Any:
    """Build a Google Gemini client, trying API key then OAuth."""
    from google import genai

    # Try API key first
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if api_key:
        try:
            return genai.Client(api_key=api_key)
        except Exception as exc:
            raise AgentError(f"Failed to initialize Google Gemini client: {exc}") from exc

    # Fallback to Gemini CLI OAuth token
    import subprocess

    from google.oauth2.credentials import Credentials

    from ...auth import load_gemini_cli_token

    token = load_gemini_cli_token()
    if not token:
        raise AgentError(
            "Missing credentials for Google Gemini. Either set GEMINI_API_KEY / "
            "GOOGLE_API_KEY, or run `gemini auth login` to authenticate via the CLI."
        )

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        try:
            project = subprocess.check_output(
                ["gcloud", "config", "get-value", "project"],
                stderr=subprocess.DEVNULL,
                text=True,
            ).strip()
        except Exception:
            project = None

    if not project:
        raise AgentError(
            "Missing GCP Project ID. Please configure GOOGLE_CLOUD_PROJECT "
            "or set your active gcloud project with `gcloud config set project <id>`."
        )

    try:
        credentials = Credentials(token=token)
        return genai.Client(
            vertexai=True,
            project=project,
            location=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"),
            credentials=credentials,
        )
    except Exception as exc:
        raise AgentError(f"Failed to initialize Google Gemini client with OAuth: {exc}") from exc


def _build_openai_compat_client(provider: str) -> Any:
    """Build a client for OpenAI-compatible providers (OpenAI, Gateway)."""
    from ...auth import resolve_openai_credentials

    try:
        api_base, api_key = resolve_openai_credentials()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc
    return _openai_compat_client(api_base, api_key)


def _build_anthropic_client() -> Any:
    """Build an Anthropic client."""
    try:
        return resolve_anthropic_client()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc


def _build_ollama_client() -> Any:
    """Build a client for a local Ollama instance."""
    try:
        api_base, api_key = resolve_ollama_credentials()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc

    return _openai_compat_client(api_base, api_key)


def _build_local_client() -> Any:
    """Build a client for a custom local OpenAI-compatible model."""
    try:
        api_base, api_key = resolve_local_credentials()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc

    return _openai_compat_client(api_base, api_key)


def _build_gateway_client() -> Any:
    """Build a client for an OpenAI-compatible AI gateway."""
    from ...auth import resolve_gateway_credentials

    try:
        api_base, api_key = resolve_gateway_credentials()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc

    return _openai_compat_client(api_base, api_key)


def build_client(provider: str, client: Any | None) -> Any:
    """Construct the SDK client for ``provider``, or return an injected one.

    Missing or unusable credentials raise :class:`AgentError` with a clear
    message rather than a raw SDK traceback.
    """
    if client is not None:
        return client

    if provider == "google":
        return _build_google_client()
    if provider == "openai":
        return _build_openai_compat_client(provider)
    if provider == "gateway":
        return _build_gateway_client()
    if provider == "ollama":
        return _build_ollama_client()
    if provider == "local":
        return _build_local_client()

    # Default to Anthropic
    return _build_anthropic_client()
