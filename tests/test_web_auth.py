"""Tests for web API bearer token authentication."""

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
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return exc.code, body


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
