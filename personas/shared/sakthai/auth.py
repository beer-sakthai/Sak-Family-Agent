"""Credential resolution for the Anthropic and Google providers.

Anthropic (:func:`resolve_anthropic_client`) tries, in order:

1. ``ANTHROPIC_API_KEY``   — classic API key (X-Api-Key header)
2. ``ANTHROPIC_AUTH_TOKEN`` — Bearer token
3. the Claude CLI OAuth token in ``~/.claude/.credentials.json``

Google (:func:`load_gemini_cli_token`) reads the Gemini CLI OAuth token from
``~/.gemini/oauth_creds.json`` and returns the raw access-token string.
"""

from __future__ import annotations

import json
import os
import time
from datetime import UTC
from pathlib import Path
from typing import Any

import anthropic

from .config import register_secret


class AuthError(RuntimeError):
    """Raised when no usable credential can be found."""


def _claude_dir() -> Path:
    return Path(os.environ.get("CLAUDE_CONFIG_DIR", Path.home() / ".claude"))


def _gemini_dir() -> Path:
    return Path(os.environ.get("GEMINI_HOME", Path.home() / ".gemini"))


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _expired(expiry_ms: Any) -> bool:
    """True when an epoch-milliseconds expiry has already passed."""
    try:
        ms = int(expiry_ms)
    except (TypeError, ValueError):
        return False
    return ms > 0 and time.time() * 1000 >= ms


def load_claude_cli_token() -> str | None:
    """Return the Claude CLI OAuth access token, or None if missing/expired."""
    data = _read_json(_claude_dir() / ".credentials.json")
    if not data:
        return None
    oauth = data.get("claudeAiOauth") or {}
    token = oauth.get("accessToken")
    if not token or _expired(oauth.get("expiresAt", 0)):
        return None
    res = str(token)
    register_secret(res)
    return res


def load_gemini_cli_token() -> str | None:
    """Return the Gemini/Antigravity CLI OAuth access token, or None if missing/expired."""
    data = _read_json(_gemini_dir() / "oauth_creds.json")
    if data:
        token = data.get("access_token")
        if token and not _expired(data.get("expiry_date", 0)):
            res = str(token)
            register_secret(res)
            return res

    ag_data = _read_json(_gemini_dir() / "antigravity-cli" / "antigravity-oauth-token")
    if ag_data:
        token_info = ag_data.get("token") or {}
        token = token_info.get("access_token")
        if token:
            expiry = token_info.get("expiry")
            if expiry and isinstance(expiry, str):
                from datetime import datetime

                try:
                    dt = datetime.fromisoformat(expiry)
                    expired = datetime.now(UTC) >= dt.astimezone(UTC)
                except Exception:
                    expired = False
            else:
                expired = False

            if not expired:
                res = str(token)
                register_secret(res)
                return res

    return None


def gemini_credential_source() -> str | None:
    """Return a short label for the active Gemini credential, or None."""
    if os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY"):
        return "api_key"
    if load_gemini_cli_token() is not None:
        return "gemini_cli"
    return None


def resolve_anthropic_client(**kwargs: Any) -> anthropic.Anthropic:
    """Build an Anthropic client from the best available credential.

    Raises :class:`AuthError` when nothing usable is found.
    """
    if os.environ.get("ANTHROPIC_API_KEY"):
        return anthropic.Anthropic(**kwargs)

    token = os.environ.get("ANTHROPIC_AUTH_TOKEN") or load_claude_cli_token()
    if token:
        return anthropic.Anthropic(auth_token=token, **kwargs)

    raise AuthError(
        "No Anthropic credentials found. Set ANTHROPIC_API_KEY, sign in with "
        "Claude Code (`claude login`), or set ANTHROPIC_AUTH_TOKEN."
    )


def anthropic_credential_source() -> str | None:
    """Return a short label for the active Anthropic credential, or None."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api_key"
    if os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        return "auth_token"
    if load_claude_cli_token() is not None:
        return "claude_cli"
    return None


def resolve_openai_credentials() -> tuple[str, str]:
    """Resolve the base URL and API key for OpenAI / Ollama compatible calls.

    Raises :class:`AuthError` when no usable credential is found.

    Returns:
        (base_url, api_key)

    Resolves base_url to:
    1. OPENAI_BASE_URL or OPENAI_API_BASE if set.
    2. OLLAMA_HOST + "/v1" if OLLAMA_HOST is set.
    3. Otherwise "https://api.openai.com/v1" (only if OPENAI_API_KEY is set).

    Resolves api_key to:
    1. OPENAI_API_KEY if set.
    2. Otherwise "nokey".
    """
    from .config import ollama_host, openai_api_base

    if not openai_credential_source():
        raise AuthError(
            "No OpenAI credentials found. Please set OPENAI_API_KEY, "
            "OPENAI_BASE_URL, or OLLAMA_HOST."
        )

    api_base = openai_api_base()
    if not api_base:
        if os.environ.get("OLLAMA_HOST"):
            api_base = f"{ollama_host()}/v1"
        else:
            api_base = "https://api.openai.com/v1"

    api_key = os.environ.get("OPENAI_API_KEY") or "nokey"
    return api_base, api_key


def openai_credential_source() -> str | None:
    """Return a short label for the active OpenAI/Ollama credential, or None."""
    if os.environ.get("OPENAI_API_KEY"):
        return "openai_api_key"
    if os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE"):
        return "openai_api_base"
    if os.environ.get("OLLAMA_HOST"):
        return "ollama_host"
    return None


def resolve_ollama_credentials() -> tuple[str, str]:
    """Resolve the base URL and API key for a local Ollama instance.

    Returns ``(base_url, api_key)`` where ``base_url`` is ``ollama_host()`` with a
    ``/v1`` suffix (default ``http://127.0.0.1:11434/v1``) and ``api_key`` is
    ``OPENAI_API_KEY`` or ``"nokey"`` — Ollama ignores the key but the
    OpenAI-compatible client still requires a non-empty value.
    """
    from .config import ollama_host

    api_key = os.environ.get("OPENAI_API_KEY") or "nokey"
    return f"{ollama_host()}/v1", api_key


def resolve_local_credentials() -> tuple[str, str]:
    """Resolve the base URL and API key for a custom local OpenAI-compatible model.

    A "local" endpoint is any self-hosted OpenAI-compatible server addressed via
    ``OPENAI_BASE_URL`` / ``OPENAI_API_BASE``. This reuses the OpenAI resolver but
    requires an explicit base URL, so it never silently targets the public OpenAI
    API. Raises :class:`AuthError` when no base URL is configured.
    """
    from .config import openai_api_base

    if not openai_api_base():
        raise AuthError(
            "No local model endpoint configured. Set OPENAI_BASE_URL "
            "(or OPENAI_API_BASE) to your local OpenAI-compatible server."
        )
    return resolve_openai_credentials()


def resolve_gateway_credentials() -> tuple[str, str]:
    """Resolve the base URL and API key for an OpenAI-compatible AI gateway.

    Returns:
        (base_url, api_key)

    A "gateway" is any OpenAI-compatible HTTP endpoint that fronts one or more
    upstream models — OpenRouter, LiteLLM, the Vercel AI Gateway, Cloudflare AI
    Gateway, and so on. It is configured independently of the ``OPENAI_*`` and
    ``OLLAMA_*`` variables so a gateway and a direct OpenAI key can coexist
    without one shadowing the other.

    Resolves base_url from ``SAKTHAI_GATEWAY_URL`` (required) and api_key from
    ``SAKTHAI_GATEWAY_API_KEY``, falling back to ``"nokey"`` for keyless
    gateways. Raises :class:`AuthError` when no gateway URL is configured.
    """
    from .config import gateway_base_url

    base_url = gateway_base_url()
    if not base_url:
        raise AuthError(
            "No AI gateway configured. Set SAKTHAI_GATEWAY_URL to an "
            "OpenAI-compatible gateway endpoint (e.g. https://openrouter.ai/api/v1)."
        )
    api_key = os.environ.get("SAKTHAI_GATEWAY_API_KEY") or "nokey"
    return base_url.rstrip("/"), api_key


def local_credential_source() -> str | None:
    """Return a label for a distinct local-model credential, or None.

    Reserved for a future dedicated local-model config surface. It returns None
    today so the ``local`` provider is reachable only when selected explicitly
    (``provider="local"`` or a ``local/…`` model name) and never shadows the
    ``openai`` credential auto-detection.
    """
    return None


def gateway_credential_source() -> str | None:
    """Return a short label for the active AI gateway config, or None."""
    if os.environ.get("SAKTHAI_GATEWAY_URL"):
        return "gateway_url"
    return None


def get_credential_source(provider: str) -> str | None:
    """Return a short label for the active credential for the given provider."""
    if provider == "google":
        return gemini_credential_source()
    if provider == "openai":
        return openai_credential_source()
    if provider == "gateway":
        return gateway_credential_source()
    if provider == "anthropic":
        return anthropic_credential_source()
    return None
