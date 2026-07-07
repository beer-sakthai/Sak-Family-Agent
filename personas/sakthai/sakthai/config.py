"""Filesystem paths, environment-variable names, and startup checks.

Every path and env-var name the package uses is defined here once. No other
module should hard-code a path or read an env var that has a home in this file.
"""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

# A regex for common API key prefixes (sk-, rk-, pk-, ghp-, hf-), Google keys (AIza),
# and Telegram bot tokens (123456789:ABC...).
# Handles both underscore (sk_) and hyphen (sk-) used by Anthropic, OpenAI, and HF.
SECRET_PATTERN = r"\b(?:(?:sk|rk|pk|ghp|hf)[-_][a-zA-Z0-9\-_]{20,}|AIza[0-9A-Za-z\-_]{34,}|[0-9]{8,12}:[a-zA-Z0-9_-]{35})\b"  # nosec B105
_SECRET_RE = re.compile(SECRET_PATTERN)

# Repository root and bundled resource directories. The package no longer sits
# directly under the repo root (its canonical copy lives at
# personas/sakthai/sakthai), so walk up from the package to the nearest
# directory holding pyproject.toml — correct both in this monorepo and in an
# exported standalone agent repo where the package sits at the root again.


def _find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    return start


REPO_ROOT = _find_repo_root(Path(__file__).resolve().parent.parent)
SKILLS_DIR = REPO_ROOT / "skills"
LIBRARY_DIR = REPO_ROOT / "library"
PERSONAS_DIR = REPO_ROOT / "personas"

# Environment variables, grouped by how the readiness check treats them.
REQUIRED_ENV_VARS: dict[str, str] = {
    "ANTHROPIC_API_KEY": "Claude API key for `sakthai run` (or sign in with `claude login`)",
}

OPTIONAL_ENV_VARS: dict[str, str] = {
    "ANTHROPIC_AUTH_TOKEN": "Bearer token alternative to ANTHROPIC_API_KEY",  # nosec B105 — description text
    "GEMINI_API_KEY": "Gemini API key — alternative provider",
    "GOOGLE_API_KEY": "Google API key — alternative provider",
    "OPENAI_API_KEY": "OpenAI API key — alternative provider",
    "OPENAI_API_BASE": "OpenAI API base URL (or use OPENAI_BASE_URL)",
    "OPENAI_BASE_URL": "OpenAI API base URL",
    "SAKTHAI_FAST": "Enable fast-track mode for Telegram/systemd launches",
    "SAKTHAI_MODEL": "Default model for Telegram/systemd launches",
    "SAKTHAI_NO_MCP": "Skip external MCP servers for Telegram/systemd launches",
    "SAKTHAI_PROVIDER": "Default provider for Telegram/systemd launches",
    "SAKTHAI_SYSTEM_PROMPT": "Inline system prompt prefix for a persona",
    "SAKTHAI_SYSTEM_PROMPT_FILE": "Path to a persona file prepended to the system prompt",
    "SAKTHAI_WITH_SKILLS": "Comma-separated skill names injected into the system prompt",
    "OLLAMA_HOST": "Ollama host URL (default: http://127.0.0.1:11434)",
    "SAKTHAI_GATEWAY_URL": "Base URL of an OpenAI-compatible AI gateway (OpenRouter, LiteLLM, Vercel, Cloudflare)",
    "SAKTHAI_GATEWAY_API_KEY": "API key/token for the AI gateway (default: nokey)",  # nosec B105 — description text
    "SAKTHAI_HOME": "Override the data directory (default: ~/.sakthai)",
    "SAKTHAI_READ_ALLOW": "Extra paths the read_file tool may read (os.pathsep-separated)",
    "SAKTHAI_MCP_CONFIG": "Path to a per-persona mcp.json whose servers override the defaults",
    "SAKTHAI_MCP_TIMEOUT": "Seconds to wait for an external MCP server reply (default: 30)",
    "TELEGRAM_ALLOWED_USER_IDS": "Comma- or space-separated Telegram user IDs allowed to use the bot",
    "TELEGRAM_BOT_TOKEN": "Telegram bot token used by the Telegram gateway",
    "SAKKING_HOME": "Override the SakKing data directory (default: ~/.sakking) for skill sync",
    "SAKTHAI_EVAL_LOG": "Override the local model eval/MLOps log path (default: SAKTHAI_HOME/eval.jsonl)",
}

# Seconds to wait for an external MCP server's reply, before SAKTHAI_MCP_TIMEOUT.
DEFAULT_MCP_TIMEOUT = 30.0


def sakthai_home() -> Path:
    """Return the data directory, honouring the SAKTHAI_HOME override."""
    override = os.environ.get("SAKTHAI_HOME")
    return Path(override) if override else Path.home() / ".sakthai"


def gemini_extensions_dir() -> Path:
    """Return the Gemini CLI extensions directory, honouring SAKTHAI_HOME/GEMINI_HOME."""
    override = os.environ.get("GEMINI_HOME")
    if override:
        return Path(override) / "extensions"
    sakthai_override = os.environ.get("SAKTHAI_HOME")
    if sakthai_override:
        return Path(sakthai_override).parent / "gemini" / "extensions"
    return Path("~/.gemini/extensions").expanduser()


def sakking_home() -> Path:
    """Return the SakKing data directory, honouring the SAKKING_HOME override."""
    override = os.environ.get("SAKKING_HOME")
    return Path(override) if override else Path.home() / ".sakking"


def mcp_config_override() -> Path | None:
    """Per-persona MCP manifest path from SAKTHAI_MCP_CONFIG, if set.

    Lets each persona (or a single ``sakthai run``) load an extra ``mcp.json``
    whose servers take precedence over the shared defaults — e.g.
    ``personas/saksee/config/mcp.json`` for Playwright + Chrome DevTools.
    """
    override = os.environ.get("SAKTHAI_MCP_CONFIG")
    return Path(override) if override else None


def sakking_skills_dir() -> Path:
    """Directory where SakKing stores its (bundled and learned) skills."""
    return sakking_home() / "skills"


def memory_db_path() -> Path:
    """Path to the shared SQLite memory database."""
    return sakthai_home() / "memory.db"


def sessions_dir() -> Path:
    """Directory where agent session logs are written."""
    return sakthai_home() / "sessions"


def eval_log_path() -> Path:
    """Path to the local model eval/MLOps JSONL log, honouring SAKTHAI_EVAL_LOG."""
    override = os.environ.get("SAKTHAI_EVAL_LOG")
    return Path(override) if override else sakthai_home() / "eval.jsonl"


def ollama_host() -> str:
    """Return the Ollama host URL, defaulting to http://127.0.0.1:11434.

    The IPv4 literal is used rather than ``localhost`` on purpose: on hosts where
    ``localhost`` resolves to IPv6 ``::1`` while Ollama binds IPv4 only, the agent
    loop would otherwise fail with ``[Errno 111] Connection refused`` even though
    the server is up. ``127.0.0.1`` works everywhere ``localhost`` does.
    """
    return os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def mcp_timeout() -> float:
    """Seconds to wait for an external MCP server reply (SAKTHAI_MCP_TIMEOUT).

    Falls back to ``DEFAULT_MCP_TIMEOUT`` when the var is unset, unparseable, or
    non-positive — a bad value should not silently disable the read deadline.
    """
    raw = os.environ.get("SAKTHAI_MCP_TIMEOUT")
    if not raw:
        return DEFAULT_MCP_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_MCP_TIMEOUT
    return value if value > 0 else DEFAULT_MCP_TIMEOUT


def openai_api_base() -> str | None:
    """Return the OpenAI API base URL, honoring OPENAI_BASE_URL or OPENAI_API_BASE."""
    return os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE")


def gateway_base_url() -> str | None:
    """Return the AI-gateway base URL, honoring SAKTHAI_GATEWAY_URL."""
    return os.environ.get("SAKTHAI_GATEWAY_URL")


def sakthai_default_provider() -> str | None:
    """Return the default provider override for Telegram/systemd launches."""
    value = os.environ.get("SAKTHAI_PROVIDER", "").strip()
    return value or None


def sakthai_default_model() -> str | None:
    """Return the default model override for Telegram/systemd launches."""
    value = os.environ.get("SAKTHAI_MODEL", "").strip()
    return value or None


def sakthai_fast_mode() -> bool:
    """Return whether Telegram/systemd launches should use fast-track mode."""
    return os.environ.get("SAKTHAI_FAST", "").strip().lower() in {"1", "true", "yes", "on"}


def sakthai_skip_mcp() -> bool:
    """Return whether Telegram/systemd launches should skip external MCP servers."""
    return os.environ.get("SAKTHAI_NO_MCP", "").strip().lower() in {"1", "true", "yes", "on"}


def sakthai_system_prompt_prefix() -> str | None:
    """Return an inline or file-backed system prompt prefix for agent launches."""
    inline = os.environ.get("SAKTHAI_SYSTEM_PROMPT", "")
    if inline.strip():
        return inline
    prompt_file = os.environ.get("SAKTHAI_SYSTEM_PROMPT_FILE", "").strip()
    if not prompt_file:
        return None
    try:
        return Path(prompt_file).read_text(encoding="utf-8").strip()
    except Exception:
        return None


def sakthai_with_skills() -> list[str]:
    """Return comma-separated skills injected into Telegram/systemd launches."""
    raw = os.environ.get("SAKTHAI_WITH_SKILLS", "")
    return [item.strip() for item in raw.replace(",", " ").split() if item.strip()]


def telegram_bot_token() -> str | None:
    """Return the Telegram bot token, or None when not configured."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    return token.strip() if token and token.strip() else None


def telegram_allowed_user_ids() -> list[int]:
    """Return the Telegram user IDs allowed to use the bot.

    The env var accepts comma, space, or newline separated integers. Invalid
    tokens are ignored rather than crashing startup.
    """
    raw = os.environ.get("TELEGRAM_ALLOWED_USER_IDS", "")
    if not raw.strip():
        return []
    values: list[int] = []
    for chunk in raw.replace(",", " ").split():
        try:
            values.append(int(chunk))
        except ValueError:
            continue
    return values


def telegram_session_db_path(chat_id: int | str) -> Path:
    """Return the persistent memory DB path for one Telegram chat session."""
    return sakthai_home() / "telegram" / str(chat_id) / "memory.db"


def _paths_report() -> dict[str, Any]:
    home = sakthai_home()
    db = memory_db_path()
    return {
        "sakthai_home": str(home),
        "sakthai_home_exists": home.is_dir(),
        "memory_db": str(db),
        "memory_db_exists": db.is_file(),
        "skills_dir": str(SKILLS_DIR),
        "skills_dir_exists": SKILLS_DIR.is_dir(),
    }


def _env_report() -> dict[str, dict[str, Any]]:
    report: dict[str, dict[str, Any]] = {}
    for name, desc in {**REQUIRED_ENV_VARS, **OPTIONAL_ENV_VARS}.items():
        report[name] = {
            "set": bool(os.environ.get(name)),
            "required": name in REQUIRED_ENV_VARS,
            "description": desc,
        }
    return report


def _count_rows(db: Path) -> tuple[int | None, int | None, str | None]:
    """Return (facts, observations, error) by querying the DB read-only."""
    try:
        conn = sqlite3.connect(str(db), timeout=3)
        try:
            facts = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
            obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            return int(facts), int(obs), None
        finally:
            conn.close()
    except Exception as exc:  # corrupt / locked / missing tables
        return None, None, str(exc)


def _memory_report() -> dict[str, Any]:
    db = memory_db_path()
    if not db.is_file():
        return {
            "db_exists": False,
            "db_writable": False,
            "fact_count": None,
            "observation_count": None,
            "error": None,
        }
    facts, obs, error = _count_rows(db)
    return {
        "db_exists": True,
        "db_writable": error is None and os.access(db, os.W_OK),
        "fact_count": facts,
        "observation_count": obs,
        "error": error,
    }


def _skills_report() -> dict[str, Any]:
    count = 0
    if SKILLS_DIR.is_dir():
        count = sum(1 for child in SKILLS_DIR.iterdir() if child.is_dir())
    return {"dir_exists": SKILLS_DIR.is_dir(), "skill_count": count}


def _auth_report() -> dict[str, Any]:
    # Imported lazily so config.py has no hard dependency on the anthropic SDK.
    from .auth import (
        anthropic_credential_source,
        gateway_credential_source,
        gemini_credential_source,
        load_gemini_cli_token,
        openai_credential_source,
    )

    anthropic_source = anthropic_credential_source()
    openai_source = openai_credential_source()
    gemini_source = gemini_credential_source()
    gateway_source = gateway_credential_source()
    return {
        "anthropic_source": anthropic_source,
        "anthropic_ok": anthropic_source is not None,
        "gemini_cli_oauth": load_gemini_cli_token() is not None,
        "openai_source": openai_source,
        "openai_ok": openai_source is not None,
        "gateway_source": gateway_source,
        "gateway_ok": gateway_source is not None,
        "gemini_source": gemini_source,
        "gemini_ok": gemini_source is not None,
    }


def _is_ready(report: dict[str, Any]) -> bool:
    # Readiness means the memory store is usable. The DB is created lazily on
    # first use, so "doesn't exist yet" still counts as ready; only an existing
    # but non-writable DB blocks. Credentials and skills are reported separately
    # and don't gate readiness (offline tools need no key; skills are optional).
    mem = report["memory"]
    return not mem["db_exists"] or bool(mem["db_writable"])


def check_env() -> dict[str, Any]:
    """Gather every startup prerequisite into one structured report.

    Top-level keys: ``paths``, ``env``, ``memory``, ``skills``, ``auth``, and
    ``ready`` (True only when the core components are functional).
    """
    report: dict[str, Any] = {
        "paths": _paths_report(),
        "env": _env_report(),
        "memory": _memory_report(),
        "skills": _skills_report(),
        "auth": _auth_report(),
    }
    report["ready"] = _is_ready(report)
    return report


# Extra values to be redacted (e.g. tokens loaded from disk), populated via register_secret.
_EXTRA_SECRETS: set[str] = set()


def register_secret(secret: str) -> None:
    """Register a value to be masked by redact_secrets.

    Used by the auth layer to register tokens loaded from disk so they are
    redacted even if they aren't in the environment.
    """
    if isinstance(secret, str) and len(secret) > 5:
        _EXTRA_SECRETS.add(secret)


def redact_secrets(text: str) -> str:
    """Redact sensitive environment variable values and registered secrets from text."""
    if not isinstance(text, str) or not text:
        return text

    # First, redact based on known exact values (highest precision).
    secret_keys = [
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENAI_API_KEY",
        "SAKTHAI_GATEWAY_API_KEY",
        "TELEGRAM_BOT_TOKEN",
        "HF_TOKEN",
        "COMPOSIO_API_KEY",
    ]

    secrets: set[str] = set(_EXTRA_SECRETS)
    for key in secret_keys:
        if val := os.environ.get(key):
            secrets.add(val)

    if secrets:
        # Sort by length descending to ensure longer secrets (e.g. session tokens)
        # are redacted before their potential substrings (e.g. parts of keys).
        for val in sorted(secrets, key=len, reverse=True):
            if len(val) > 5:
                text = text.replace(val, "[REDACTED]")

    # Second, redact based on common patterns (defense-in-depth).
    text = _SECRET_RE.sub("[REDACTED]", text)

    return text
