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


def test_gemini_token_falls_back_to_antigravity_cli() -> None:
    ag_dir = Path(auth._gemini_dir()) / "antigravity-cli"
    ag_dir.mkdir(parents=True, exist_ok=True)
    token_file = ag_dir / "antigravity-oauth-token"
    future_iso = "2099-01-01T00:00:00.000Z"
    payload = {"token": {"access_token": "ag-tok", "expiry": future_iso}}
    token_file.write_text(json.dumps(payload), encoding="utf-8")

    assert auth.load_gemini_cli_token() == "ag-tok"


def test_gemini_token_antigravity_cli_expired_returns_none() -> None:
    ag_dir = Path(auth._gemini_dir()) / "antigravity-cli"
    ag_dir.mkdir(parents=True, exist_ok=True)
    token_file = ag_dir / "antigravity-oauth-token"
    past_iso = "2020-01-01T00:00:00.000Z"
    payload = {"token": {"access_token": "ag-tok", "expiry": past_iso}}
    token_file.write_text(json.dumps(payload), encoding="utf-8")

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


# -- resolve_openai_credentials / openai_credential_source -----------------


def test_resolve_openai_with_api_key_defaults_to_openai_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    base, key = auth.resolve_openai_credentials()
    assert base == "https://api.openai.com/v1"
    assert key == "sk-openai-test"


def test_resolve_openai_with_ollama_host_builds_v1_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    base, key = auth.resolve_openai_credentials()
    assert base == "http://127.0.0.1:11434/v1"
    assert key == "nokey"


def test_resolve_openai_with_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "http://my-proxy/v1")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    base, key = auth.resolve_openai_credentials()
    assert base == "http://my-proxy/v1"
    assert key == "nokey"


def test_resolve_openai_raises_without_any_credential(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    with pytest.raises(auth.AuthError, match="OPENAI_API_KEY"):
        auth.resolve_openai_credentials()


def test_openai_credential_source_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    assert auth.openai_credential_source() == "openai_api_key"


def test_openai_credential_source_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_BASE_URL", "http://proxy/v1")
    assert auth.openai_credential_source() == "openai_api_base"


def test_openai_credential_source_api_base(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.setenv("OPENAI_API_BASE", "http://proxy/v1")
    assert auth.openai_credential_source() == "openai_api_base"


def test_openai_credential_source_ollama_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    assert auth.openai_credential_source() == "ollama_host"


def test_openai_credential_source_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert auth.openai_credential_source() is None


# -- resolve_gateway_credentials / gateway_credential_source ---------------


def test_resolve_gateway_with_url_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "https://openrouter.ai/api/v1/")
    monkeypatch.setenv("SAKTHAI_GATEWAY_API_KEY", "sk-gw")
    base, key = auth.resolve_gateway_credentials()
    assert base == "https://openrouter.ai/api/v1"  # trailing slash stripped
    assert key == "sk-gw"


def test_resolve_gateway_defaults_key_to_nokey(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "http://localhost:4000/v1")
    monkeypatch.delenv("SAKTHAI_GATEWAY_API_KEY", raising=False)
    base, key = auth.resolve_gateway_credentials()
    assert base == "http://localhost:4000/v1"
    assert key == "nokey"


def test_resolve_gateway_raises_without_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_GATEWAY_URL", raising=False)
    with pytest.raises(auth.AuthError, match="SAKTHAI_GATEWAY_URL"):
        auth.resolve_gateway_credentials()


def test_gateway_credential_source_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "http://localhost:4000/v1")
    assert auth.gateway_credential_source() == "gateway_url"


def test_gateway_credential_source_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_GATEWAY_URL", raising=False)
    assert auth.gateway_credential_source() is None


# -- resolve_ollama_credentials ------------------------------------------


def test_resolve_ollama_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    base, key = auth.resolve_ollama_credentials()
    assert base == "http://127.0.0.1:11434/v1"
    assert key == "nokey"


def test_resolve_ollama_uses_custom_host_and_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OLLAMA_HOST", "http://gpu-box:9999")
    monkeypatch.setenv("OPENAI_API_KEY", "supplied-key")
    base, key = auth.resolve_ollama_credentials()
    assert base == "http://gpu-box:9999/v1"
    assert key == "supplied-key"


# -- resolve_local_credentials -------------------------------------------


def test_resolve_local_raises_without_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    with pytest.raises(auth.AuthError, match="OPENAI_BASE_URL"):
        auth.resolve_local_credentials()


def test_resolve_local_returns_openai_creds_with_base_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_BASE_URL", "http://localhost:8080/v1")
    monkeypatch.setenv("OPENAI_API_KEY", "local-key")
    base, key = auth.resolve_local_credentials()
    assert base == "http://localhost:8080/v1"
    assert key == "local-key"


# -- Antigravity CLI token (expiry parsing) --------------------------------


def _write_antigravity_token(token: str, *, expiry: object = None) -> None:
    ag_dir = Path(auth._gemini_dir()) / "antigravity-cli"
    ag_dir.mkdir(parents=True, exist_ok=True)
    token_info: dict[str, object] = {"access_token": token}
    if expiry is not None:
        token_info["expiry"] = expiry
    (ag_dir / "antigravity-oauth-token").write_text(
        json.dumps({"token": token_info}), encoding="utf-8"
    )


def test_antigravity_token_with_future_expiry_is_returned() -> None:
    from datetime import UTC, datetime, timedelta

    future = (datetime.now(UTC) + timedelta(hours=1)).isoformat()
    _write_antigravity_token("ag-tok", expiry=future)
    assert auth.load_gemini_cli_token() == "ag-tok"


def test_antigravity_token_with_past_expiry_is_rejected() -> None:
    from datetime import UTC, datetime, timedelta

    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    _write_antigravity_token("ag-tok", expiry=past)
    assert auth.load_gemini_cli_token() is None


def test_antigravity_token_with_unparseable_expiry_is_treated_as_valid() -> None:
    _write_antigravity_token("ag-tok", expiry="not-a-timestamp")
    assert auth.load_gemini_cli_token() == "ag-tok"


def test_antigravity_token_without_expiry_is_treated_as_valid() -> None:
    _write_antigravity_token("ag-tok")
    assert auth.load_gemini_cli_token() == "ag-tok"


def test_antigravity_token_with_naive_past_expiry_is_rejected() -> None:
    # A naive ISO timestamp exercises the astimezone() normalisation branch.
    _write_antigravity_token("ag-tok", expiry="2020-01-01T00:00:00")
    assert auth.load_gemini_cli_token() is None


# -- get_credential_source dispatcher ---------------------------------------


def test_get_credential_source_dispatches_per_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "k")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_BASE_URL", "http://127.0.0.1:1/v1")
    monkeypatch.setenv("SAKTHAI_GATEWAY_URL", "http://gw.example/v1")
    assert auth.get_credential_source("anthropic") == "api_key"
    assert auth.get_credential_source("google") == "api_key"
    assert auth.get_credential_source("openai") is not None
    assert auth.get_credential_source("gateway") is not None
    assert auth.get_credential_source("unknown-provider") is None
