<<<<<<< HEAD
"""Tests for Web API authentication and manage commands."""
=======
"""Tests for web API bearer token authentication."""
>>>>>>> origin/main

from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from http.server import HTTPServer
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from click.testing import CliRunner

<<<<<<< HEAD
from sakthai.cli import main
from sakthai.web.server import (
    _Handler,
    _get_or_create_bearer_token,
)

@pytest.fixture
def clean_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate tests under a temporary sakthai home directory."""
    home = tmp_path / "sakthai_home"
    home.mkdir()
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    return home


def _get(
    url: str,
    headers: dict[str, str] | None = None,
    timeout: int = 5,
) -> tuple[int, dict[str, Any]]:
    """GET url with optional headers, returning (status_code, parsed_body)."""
    req = urllib.request.Request(url, headers=headers or {})
=======
from sakthai.cli.system import web as web_cli
from sakthai.memory.store import MemoryStore
from sakthai.web.server import (
    _get_or_create_bearer_token,
    _Handler,
)


@pytest.fixture
def temp_db(tmp_path: Path) -> Path:
    """Return path to a temporary memory DB file."""
    return tmp_path / "temp_memory.db"


def test_token_creation_and_persistence(temp_db: Path) -> None:
    """Verify that a bearer token is created in the DB and persists on sub-sequent calls."""
    with (
        patch("sakthai.memory.store.memory_db_path", return_value=temp_db),
        patch("sakthai.config.memory_db_path", return_value=temp_db),
    ):
        import sakthai.web.server as srv

        srv._BEARER_TOKEN = None

        # Fetch/Create token
        token1 = _get_or_create_bearer_token()
        assert len(token1) == 32  # 16 bytes in hex

        # Retrieve again - should be identical
        token2 = _get_or_create_bearer_token()
        assert token1 == token2

        # Verify fact exists in DB
        with MemoryStore(temp_db) as store:
            fact = store.get_fact_by_key(kind="web_auth", key="bearer_token")
            assert fact is not None
            assert fact.value == token1
            assert "no-export" in fact.tags


# ---------------------------------------------------------------------------
# HTTP Authentication Tests
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def authed_server_base() -> tuple[str, str]:
    """Start an authenticated HTTPServer and return (base_url, token)."""
    # Force generate a custom token for testing
    import sakthai.web.server as srv

    srv._BEARER_TOKEN = "test_bearer_token_12345678"

    server = HTTPServer(("127.0.0.1", 0), _Handler)
    _, port = server.server_address
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()

    yield f"http://127.0.0.1:{port}", "test_bearer_token_12345678"
    server.shutdown()


def _get_with_headers(
    url: str, headers: dict[str, str], timeout: int = 5
) -> tuple[int, dict[str, Any]]:
    """GET url with headers, returning (status_code, parsed_body)."""
    req = urllib.request.Request(url, headers=headers)
>>>>>>> origin/main
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return exc.code, body


<<<<<<< HEAD
def test_token_creation_and_persistence(clean_home: Path) -> None:
    # On first run, it should generate a secure token and save it to facts
    db_path = clean_home / "memory.db"
    with patch("sakthai.memory.store.memory_db_path", return_value=db_path):
        token1 = _get_or_create_bearer_token()
        assert len(token1) == 32  # 16 bytes = 32 hex chars

        # On second run, it should load the same token from DB
        token2 = _get_or_create_bearer_token()
        assert token1 == token2


def test_token_env_override(clean_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_WEB_TOKEN", "override_token_value_123")
    token = _get_or_create_bearer_token()
    assert token == "override_token_value_123"


def test_api_rejection_and_acceptance(clean_home: Path) -> None:
    db_path = clean_home / "memory.db"
    with patch("sakthai.memory.store.memory_db_path", return_value=db_path):
        token = _get_or_create_bearer_token()

        srv = HTTPServer(("127.0.0.1", 0), _Handler)
        srv.bearer_token = token
        _, port = srv.server_address
        thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        thread.start()

        try:
            base_url = f"http://127.0.0.1:{port}"

            # 1. No Authorization header -> 401 Unauthorized
            code, body = _get(f"{base_url}/api/stages")
            assert code == 401
            assert "Unauthorized" in body.get("error", "")

            # 2. Invalid Bearer Token -> 403 Forbidden
            code, body = _get(f"{base_url}/api/stages", headers={"Authorization": "Bearer badtoken"})
            assert code == 403
            assert "Forbidden" in body.get("error", "")

            # 3. Valid Bearer Token -> 200 OK
            code, body = _get(f"{base_url}/api/stages", headers={"Authorization": f"Bearer {token}"})
            assert code == 200
            assert "kpis" in body
        finally:
            srv.shutdown()


def test_cli_web_setup_and_regen(clean_home: Path) -> None:
    runner = CliRunner()
    db_path = clean_home / "memory.db"

    with patch("sakthai.memory.store.memory_db_path", return_value=db_path):
        # 1. Setup - should generate a new token
        res = runner.invoke(main, ["web", "setup"])
        assert res.exit_code == 0
        assert "Web API token generated and saved" in res.output

        # Extract token from output
        lines = res.output.splitlines()
        token_line = [l for l in lines if "Web API token" in l][0]
        token = token_line.split()[-1]
        assert len(token) == 32

        # 2. Setup again - should load existing token
        res2 = runner.invoke(main, ["web", "setup"])
        assert res2.exit_code == 0
        assert f"Web API token: {token}" in res2.output

        # 3. Regen token (with confirmation)
        res3 = runner.invoke(main, ["web", "regen-token"], input="y\n")
        assert res3.exit_code == 0
        assert "Web API token regenerated and saved" in res3.output

        # Verify old token doesn't exist anymore and new is saved
        res4 = runner.invoke(main, ["web", "setup"])
        assert token not in res4.output
=======
def test_api_unauthorized_when_no_token(authed_server_base: tuple[str, str]) -> None:
    """Requesting an API endpoint without authorization header yields 401."""
    base_url, _ = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {})
    assert status == 401
    assert body["error"] == "Unauthorized"
    assert "Missing" in body["message"]


def test_api_unauthorized_when_bad_format(authed_server_base: tuple[str, str]) -> None:
    """Requesting with malformed authorization header format yields 401."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Authorization": f"Token {token}"})
    assert status == 401
    assert "format" in body["message"]


def test_api_forbidden_when_invalid_token(authed_server_base: tuple[str, str]) -> None:
    """Requesting with incorrect token yields 403."""
    base_url, _ = authed_server_base
    status, body = _get_with_headers(
        f"{base_url}/api/stages", {"Authorization": "Bearer wrong_token_xyz"}
    )
    assert status == 403
    assert body["error"] == "Forbidden"
    assert "Invalid" in body["message"]


def test_api_allowed_with_correct_token(authed_server_base: tuple[str, str]) -> None:
    """Requesting with the correct token yields 200."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Authorization": f"Bearer {token}"})
    assert status == 200
    assert "kpis" in body


# ---------------------------------------------------------------------------
# CLI Commands Tests
# ---------------------------------------------------------------------------


def test_cli_web_setup(temp_db: Path) -> None:
    """Verify that 'sakthai web setup' initializes and displays the token."""
    runner = CliRunner()
    with (
        patch("sakthai.memory.store.memory_db_path", return_value=temp_db),
        patch("sakthai.config.memory_db_path", return_value=temp_db),
    ):
        import sakthai.web.server as srv

        srv._BEARER_TOKEN = None

        result = runner.invoke(web_cli, ["setup"])
        assert result.exit_code == 0
        assert "configured" in result.output
        assert "Token:" in result.output


def test_cli_web_regen_token(temp_db: Path) -> None:
    """Verify that 'sakthai web regen-token' regenerates the token in DB and invalidates previous cache."""
    runner = CliRunner()
    with (
        patch("sakthai.memory.store.memory_db_path", return_value=temp_db),
        patch("sakthai.config.memory_db_path", return_value=temp_db),
    ):
        import sakthai.web.server as srv

        srv._BEARER_TOKEN = None

        # Setup initial token
        token1 = _get_or_create_bearer_token()

        # Regenerate token (answering Yes to prompt)
        result = runner.invoke(web_cli, ["regen-token"], input="y\n")
        print("RESULT OUTPUT IS:", result.output)
        assert result.exit_code == 0
        assert "Regenerated" in result.output

        # Cache should now be updated to the new token
        token2 = srv._BEARER_TOKEN
        assert token2 is not None
        assert token1 != token2

        # Verify new token matches DB
        with MemoryStore(temp_db) as store:
            fact = store.get_fact_by_key(kind="web_auth", key="bearer_token")
            assert fact is not None
            assert fact.value == token2
>>>>>>> origin/main
