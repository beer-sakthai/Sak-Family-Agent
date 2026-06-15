"""Tests for credential resolution in sakthai.auth.

All tests are hermetic: real environment credentials are cleared and the Claude
and Gemini config directories are redirected to throwaway tmp dirs, so nothing
here reads or depends on the developer's actual credentials.
"""

from __future__ import annotations

import json
import time
from collections.abc import Iterator
from pathlib import Path

import anthropic
import pytest

from sakthai import auth


@pytest.fixture(autouse=True)
def isolated_creds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """Clear real Anthropic env vars and point the CLI config dirs at tmp."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    claude = tmp_path / "claude"
    gemini = tmp_path / "gemini"
    claude.mkdir()
    gemini.mkdir()
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", str(claude))
    monkeypatch.setenv("GEMINI_HOME", str(gemini))
    yield tmp_path


def _future_ms() -> int:
    return int((time.time() + 3600) * 1000)


def _write_claude_token(token: str = "claude-tok", *, expires_at: int | None = None) -> None:
    creds = Path(auth._claude_dir()) / ".credentials.json"
    payload = {"claudeAiOauth": {"accessToken": token, "expiresAt": expires_at or _future_ms()}}
    creds.write_text(json.dumps(payload), encoding="utf-8")


def _write_gemini_token(token: str = "gemini-tok", *, expiry_date: int | None = None) -> None:
    creds = Path(auth._gemini_dir()) / "oauth_creds.json"
    payload = {"access_token": token, "expiry_date": expiry_date or _future_ms()}
    creds.write_text(json.dumps(payload), encoding="utf-8")


# -- _expired ------------------------------------------------------------


def test_expired_past_timestamp() -> None:
    assert auth._expired(1) is True


def test_expired_future_timestamp() -> None:
    assert auth._expired(_future_ms()) is False


def test_expired_zero_means_never() -> None:
    assert auth._expired(0) is False


@pytest.mark.parametrize("bad", [None, "not-a-number", object()])
def test_expired_non_numeric_is_false(bad: object) -> None:
    assert auth._expired(bad) is False


# -- _read_json ----------------------------------------------------------


def test_read_json_missing_file(tmp_path: Path) -> None:
    assert auth._read_json(tmp_path / "nope.json") is None


def test_read_json_invalid_json(tmp_path: Path) -> None:
    p = tmp_path / "bad.json"
    p.write_text("{not json", encoding="utf-8")
    assert auth._read_json(p) is None


def test_read_json_non_dict(tmp_path: Path) -> None:
    p = tmp_path / "list.json"
    p.write_text("[1, 2, 3]", encoding="utf-8")
    assert auth._read_json(p) is None


def test_read_json_valid_dict(tmp_path: Path) -> None:
    p = tmp_path / "ok.json"
    p.write_text('{"a": 1}', encoding="utf-8")
    assert auth._read_json(p) == {"a": 1}


# -- load_claude_cli_token ----------------------------------------------


def test_claude_token_missing_returns_none() -> None:
    assert auth.load_claude_cli_token() is None


def test_claude_token_valid() -> None:
    _write_claude_token("abc")
    assert auth.load_claude_cli_token() == "abc"


def test_claude_token_expired_returns_none() -> None:
    _write_claude_token("abc", expires_at=1)
    assert auth.load_claude_cli_token() is None


def test_claude_token_without_access_token_returns_none() -> None:
    creds = Path(auth._claude_dir()) / ".credentials.json"
    creds.write_text(json.dumps({"claudeAiOauth": {}}), encoding="utf-8")
    assert auth.load_claude_cli_token() is None


# -- load_gemini_cli_token ----------------------------------------------


def test_gemini_token_missing_returns_none() -> None:
    assert auth.load_gemini_cli_token() is None


def test_gemini_token_valid() -> None:
    _write_gemini_token("xyz")
    assert auth.load_gemini_cli_token() == "xyz"


def test_gemini_token_expired_returns_none() -> None:
    _write_gemini_token("xyz", expiry_date=1)
    assert auth.load_gemini_cli_token() is None


# -- resolve_anthropic_client -------------------------------------------


def test_resolve_prefers_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    client = auth.resolve_anthropic_client()
    assert isinstance(client, anthropic.Anthropic)


def test_resolve_uses_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "bearer-test")
    client = auth.resolve_anthropic_client()
    assert isinstance(client, anthropic.Anthropic)


def test_resolve_falls_back_to_claude_cli() -> None:
    _write_claude_token("cli-tok")
    client = auth.resolve_anthropic_client()
    assert isinstance(client, anthropic.Anthropic)


def test_resolve_raises_when_nothing_available() -> None:
    with pytest.raises(auth.AuthError):
        auth.resolve_anthropic_client()


# -- anthropic_credential_source ----------------------------------------


def test_source_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    assert auth.anthropic_credential_source() == "api_key"


def test_source_auth_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "bearer-test")
    assert auth.anthropic_credential_source() == "auth_token"


def test_source_claude_cli() -> None:
    _write_claude_token("cli-tok")
    assert auth.anthropic_credential_source() == "claude_cli"


def test_source_none_when_unset() -> None:
    assert auth.anthropic_credential_source() is None
