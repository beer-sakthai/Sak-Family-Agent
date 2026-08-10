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
# Query-parameter and cookie credential channels
# ---------------------------------------------------------------------------
# ``_is_authenticated`` accepts a token three ways: the Authorization header
# (covered above), a ``?token=``/``?bearer_token=`` query parameter, and a
# ``token=``/``bearer_token=`` cookie. Only the header was previously tested,
# leaving two thirds of the credential-accept surface — including its
# ``unquote`` handling and its ``compare_digest`` calls — with no coverage at
# all. ``_has_auth_attempt`` mirrors the same three channels to decide between
# a 401 (no credentials offered) and a 403 (credentials offered but wrong), and
# was untested for the same two channels.


def _get_raw(url: str, headers: dict[str, str], timeout: int = 5) -> tuple[int, bytes]:
    """GET url, returning (status_code, raw_body) without assuming JSON."""
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


@pytest.mark.parametrize("param", ["token", "bearer_token"])
def test_api_allowed_with_query_parameter_token(
    authed_server_base: tuple[str, str], param: str
) -> None:
    """Both accepted query-parameter names authenticate a valid token."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages?{param}={token}", {})
    assert status == 200
    assert "kpis" in body


@pytest.mark.parametrize("param", ["token", "bearer_token"])
def test_api_forbidden_with_wrong_query_parameter_token(
    authed_server_base: tuple[str, str], param: str
) -> None:
    """A wrong token in the query string is an auth *attempt*, so 403 not 401."""
    base_url, _ = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages?{param}=wrong_token_xyz", {})
    assert status == 403
    assert body["error"] == "Forbidden"


def test_api_query_parameter_token_is_url_decoded(authed_server_base: tuple[str, str]) -> None:
    """The query value is passed through ``unquote`` before comparison.

    Percent-encoding the underscores yields a value that only matches once
    decoded, so this fails if the ``unquote`` call is dropped.
    """
    base_url, token = authed_server_base
    encoded = token.replace("_", "%5F")
    assert encoded != token
    status, body = _get_with_headers(f"{base_url}/api/stages?token={encoded}", {})
    assert status == 200
    assert "kpis" in body


def test_api_unrelated_query_parameter_is_not_a_credential(
    authed_server_base: tuple[str, str],
) -> None:
    """Only 'token'/'bearer_token' count; another key is not an auth attempt."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages?auth={token}", {})
    assert status == 401
    assert body["error"] == "Unauthorized"


@pytest.mark.parametrize("name", ["token", "bearer_token"])
def test_api_allowed_with_cookie_token(authed_server_base: tuple[str, str], name: str) -> None:
    """Both accepted cookie names authenticate a valid token."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Cookie": f"{name}={token}"})
    assert status == 200
    assert "kpis" in body


def test_api_cookie_token_among_other_cookies(authed_server_base: tuple[str, str]) -> None:
    """The token cookie is found even when other cookies surround it."""
    base_url, token = authed_server_base
    cookie = f"session=abc; token={token}; theme=dark"
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Cookie": cookie})
    assert status == 200
    assert "kpis" in body


def test_api_forbidden_with_wrong_cookie_token(authed_server_base: tuple[str, str]) -> None:
    """A wrong token in a cookie is an auth attempt, so 403 not 401."""
    base_url, _ = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Cookie": "token=wrong_token_xyz"})
    assert status == 403
    assert body["error"] == "Forbidden"


def test_api_unrelated_cookie_is_not_a_credential(authed_server_base: tuple[str, str]) -> None:
    """A cookie that is not named token/bearer_token is not an auth attempt."""
    base_url, token = authed_server_base
    status, body = _get_with_headers(f"{base_url}/api/stages", {"Cookie": f"session={token}"})
    assert status == 401
    assert body["error"] == "Unauthorized"


def test_query_parameter_auth_sets_session_cookie(authed_server_base: tuple[str, str]) -> None:
    """Authenticating by query param sets a hardened cookie for follow-up requests.

    ``end_headers`` issues this so static assets load without repeating the
    token in every URL. The flags matter as much as the cookie: HttpOnly keeps
    it away from scripts and SameSite=Strict blocks cross-site replay.
    """
    base_url, token = authed_server_base
    req = urllib.request.Request(f"{base_url}/api/stages?token={token}")
    with urllib.request.urlopen(req, timeout=5) as resp:
        set_cookie = resp.headers.get("Set-Cookie")
    assert set_cookie is not None, "expected a Set-Cookie header after query-param auth"
    assert f"token={token}" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=Strict" in set_cookie


def test_header_auth_does_not_set_session_cookie(authed_server_base: tuple[str, str]) -> None:
    """Header auth needs no cookie, and must not mint one."""
    base_url, token = authed_server_base
    req = urllib.request.Request(
        f"{base_url}/api/stages", headers={"Authorization": f"Bearer {token}"}
    )
    with urllib.request.urlopen(req, timeout=5) as resp:
        assert resp.headers.get("Set-Cookie") is None


def test_wrong_query_token_does_not_set_cookie(authed_server_base: tuple[str, str]) -> None:
    """A failed query-param auth must never mint a session cookie."""
    base_url, _ = authed_server_base
    try:
        with urllib.request.urlopen(
            urllib.request.Request(f"{base_url}/api/stages?token=wrong_token_xyz"), timeout=5
        ) as resp:
            set_cookie = resp.headers.get("Set-Cookie")
    except urllib.error.HTTPError as exc:
        set_cookie = exc.headers.get("Set-Cookie")
    assert set_cookie is None


# --- Static (non-/api/) paths use the same three channels ------------------
# Static paths answer with a plaintext 401 rather than JSON, and were only ever
# exercised through the header channel.


def test_static_path_allowed_with_query_parameter_token(
    authed_server_base: tuple[str, str],
) -> None:
    """A valid query-param token gets past auth on a static path.

    ``_STATIC_ROOT`` does not exist in this repo, so the request falls through
    to a 404 — which is precisely the point: 404 proves authentication passed,
    where an unauthenticated request gets 401.
    """
    base_url, token = authed_server_base
    status, _ = _get_raw(f"{base_url}/index.html?token={token}", {})
    assert status == 404


def test_static_path_allowed_with_cookie_token(authed_server_base: tuple[str, str]) -> None:
    """A valid cookie token gets past auth on a static path."""
    base_url, token = authed_server_base
    status, _ = _get_raw(f"{base_url}/index.html", {"Cookie": f"token={token}"})
    assert status == 404


def test_static_path_unauthorized_without_token(authed_server_base: tuple[str, str]) -> None:
    """Static paths answer 401 in plaintext, not JSON."""
    base_url, _ = authed_server_base
    status, body = _get_raw(f"{base_url}/index.html", {})
    assert status == 401
    assert b"Unauthorized" in body


def test_static_path_unauthorized_with_wrong_cookie(authed_server_base: tuple[str, str]) -> None:
    """Static paths reject a wrong cookie token."""
    base_url, _ = authed_server_base
    status, body = _get_raw(f"{base_url}/index.html", {"Cookie": "token=wrong_token_xyz"})
    assert status == 401
    assert b"Unauthorized" in body


def test_health_endpoint_needs_no_credentials(authed_server_base: tuple[str, str]) -> None:
    """/health is the one deliberately unauthenticated path."""
    base_url, _ = authed_server_base
    status, body = _get_raw(f"{base_url}/health", {})
    assert status == 200
    assert json.loads(body)["status"] == "ok"


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
