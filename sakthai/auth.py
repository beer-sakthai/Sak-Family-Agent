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
from pathlib import Path
from typing import Any

import anthropic


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
    return str(token)


def load_gemini_cli_token() -> str | None:
    """Return the Gemini CLI OAuth access token, or None if missing/expired."""
    data = _read_json(_gemini_dir() / "oauth_creds.json")
    if not data:
        return None
    token = data.get("access_token")
    if not token or _expired(data.get("expiry_date", 0)):
        return None
    return str(token)


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
