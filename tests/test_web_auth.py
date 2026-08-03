"""Tests for Web API authentication and manage commands."""

from __future__ import annotations

import json
import os
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.memory.store import MemoryStore
from sakthai.web.server import (
    _Handler,
    _get_or_create_bearer_token,
)

try:
    from http.server import HTTPServer
except ImportError:
    HTTPServer = None


@pytest.fixture
def clean_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Isolate tests under a temporary sakthai home directory."""
    home = tmp_path / "sakthai_home"
    home.mkdir()
    monkeypatch.setenv("SAKTHAI_HOME", str(home))
    return home


def _get(url: str, headers: dict[str, str] | None = None, timeout: int = 5) -> tuple[int, dict[str, Any]]:
    """GET url with optional headers, returning (status_code, parsed_body)."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            body = json.loads(exc.read().decode("utf-8"))
        except Exception:
            body = {}
        return exc.code, body


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
