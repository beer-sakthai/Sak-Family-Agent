"""Filesystem paths, environment-variable names, and startup checks.

Every path and env-var name the package uses is defined here once. No other
module should hard-code a path or read an env var that has a home in this file.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

# Repository root and bundled resource directories.
REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
LIBRARY_DIR = REPO_ROOT / "library"

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
    "OLLAMA_HOST": "Ollama host URL (default: http://127.0.0.1:11434)",
    "SAKTHAI_GATEWAY_URL": "Base URL of an OpenAI-compatible AI gateway (OpenRouter, LiteLLM, Vercel, Cloudflare)",
    "SAKTHAI_GATEWAY_API_KEY": "API key/token for the AI gateway (default: nokey)",  # nosec B105 — description text
    "SAKTHAI_HOME": "Override the data directory (default: ~/.sakthai)",
    "SAKTHAI_READ_ALLOW": "Extra paths the read_file tool may read (os.pathsep-separated)",
    "SAKTHAI_MCP_TIMEOUT": "Seconds to wait for an external MCP server reply (default: 30)",
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


def memory_db_path() -> Path:
    """Path to the shared SQLite memory database."""
    return sakthai_home() / "memory.db"


def sessions_dir() -> Path:
    """Directory where agent session logs are written."""
    return sakthai_home() / "sessions"


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
        load_gemini_cli_token,
        openai_credential_source,
    )

    anthropic_source = anthropic_credential_source()
    openai_source = openai_credential_source()
    gateway_source = gateway_credential_source()
    return {
        "anthropic_source": anthropic_source,
        "anthropic_ok": anthropic_source is not None,
        "gemini_cli_oauth": load_gemini_cli_token() is not None,
        "openai_source": openai_source,
        "openai_ok": openai_source is not None,
        "gateway_source": gateway_source,
        "gateway_ok": gateway_source is not None,
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
