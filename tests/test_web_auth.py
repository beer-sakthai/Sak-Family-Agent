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


# ---------------------------------------------------------------------------
# HEAD Authentication Tests
#
# `SimpleHTTPRequestHandler` ships its own `do_HEAD`. Inheriting it unchanged
# let an unauthenticated caller read the headers of any file under the static
# root -- existence, size and mtime -- and skipped the containment check that
# `do_GET` applies. Every case below is a regression test for that bypass.
# ---------------------------------------------------------------------------

HEAD_TOKEN = "head_test_bearer_token_1234"


@pytest.fixture
def static_server(tmp_path: Path):
    """Serve a temp static root, yielding (base_url, token, secret_filename)."""
    import sakthai.web.server as srv

    static_root = tmp_path / "dist"
    static_root.mkdir()
    (static_root / "bundle.js").write_text("console.log('secret bundle');\n")

    previous_token = srv._BEARER_TOKEN
    srv._BEARER_TOKEN = HEAD_TOKEN
    with patch.object(srv, "_STATIC_ROOT", static_root):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        _, port = server.server_address
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        thread.start()
        try:
            yield f"http://127.0.0.1:{port}", HEAD_TOKEN, "bundle.js"
        finally:
            server.shutdown()
            thread.join(timeout=5)
    srv._BEARER_TOKEN = previous_token


def _head(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str], bytes]:
    """HEAD url, returning (status_code, headers, body)."""
    req = urllib.request.Request(url, headers=headers or {}, method="HEAD")
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def test_head_static_requires_token(static_server: tuple[str, str, str]) -> None:
    """HEAD on a static file without a token is rejected, as GET already was."""
    base_url, _, name = static_server
    status, headers, _ = _head(f"{base_url}/{name}")
    assert status == 401
    # The bypass leaked the file's size; a rejection must not describe the file.
    assert headers.get("Content-Type", "").startswith("text/plain")


def test_head_does_not_leak_file_existence(static_server: tuple[str, str, str]) -> None:
    """A present and an absent path answer identically without a token.

    The inherited handler answered 200 for one and 404 for the other, which is
    enough to enumerate the static tree unauthenticated.
    """
    base_url, _, name = static_server
    present, _, _ = _head(f"{base_url}/{name}")
    absent, _, _ = _head(f"{base_url}/not-a-real-file.js")
    assert present == absent == 401


def test_head_api_requires_token(static_server: tuple[str, str, str]) -> None:
    """HEAD on an API route without a token is rejected."""
    base_url, _, _ = static_server
    status, _, _ = _head(f"{base_url}/api/stages")
    assert status == 401


def test_head_health_is_public(static_server: tuple[str, str, str]) -> None:
    """`/health` stays reachable without a token, matching GET."""
    base_url, _, _ = static_server
    status, _, _ = _head(f"{base_url}/health")
    assert status == 200


def test_head_static_allowed_with_token(static_server: tuple[str, str, str]) -> None:
    """A valid token still gets the static file's headers."""
    base_url, token, name = static_server
    status, headers, _ = _head(f"{base_url}/{name}", {"Authorization": f"Bearer {token}"})
    assert status == 200
    assert int(headers["Content-Length"]) > 0


def test_head_api_is_method_not_allowed_with_token(static_server: tuple[str, str, str]) -> None:
    """The JSON endpoints are GET-only; an authenticated HEAD gets 405."""
    base_url, token, _ = static_server
    status, _, _ = _head(f"{base_url}/api/stages", {"Authorization": f"Bearer {token}"})
    assert status == 405


def test_head_rejects_traversal_with_token(static_server: tuple[str, str, str]) -> None:
    """The static-root containment check applies to HEAD, not only GET."""
    base_url, token, _ = static_server
    status, _, _ = _head(f"{base_url}/../../../etc/passwd", {"Authorization": f"Bearer {token}"})
    assert status == 403


def test_head_response_carries_no_body(static_server: tuple[str, str, str]) -> None:
    """A HEAD response is headers only, whether it is rejected or served."""
    base_url, token, name = static_server
    _, _, rejected = _head(f"{base_url}/{name}")
    _, _, served = _head(f"{base_url}/{name}", {"Authorization": f"Bearer {token}"})
    assert rejected == b""
    assert served == b""


# ---------------------------------------------------------------------------
# Query-parameter and cookie authentication
#
# `_is_authenticated` accepts the token from three places, but only the
# `Authorization` header was covered. The other two are what let a browser load
# static assets after a `?token=` link, so they are exercised here directly.
# ---------------------------------------------------------------------------


def _raw_get(url: str, headers: dict[str, str] | None = None) -> tuple[int, dict[str, str]]:
    """GET url without parsing the body, returning (status_code, headers)."""
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, dict(resp.headers)
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers)


def test_query_param_token_authenticates(static_server: tuple[str, str, str]) -> None:
    """A `?token=` query parameter is accepted, as `Authorization` is."""
    base_url, token, name = static_server
    status, _ = _raw_get(f"{base_url}/{name}?token={token}")
    assert status == 200


def test_query_param_token_sets_cookie_from_server_token(
    static_server: tuple[str, str, str],
) -> None:
    """The Set-Cookie value comes from the stored token, never the request.

    Interpolating the user-supplied query value is what CodeQL flags as
    "construction of a cookie using user-supplied input".
    """
    base_url, token, name = static_server
    status, headers = _raw_get(f"{base_url}/{name}?bearer_token={token}")
    assert status == 200
    cookie = headers["Set-Cookie"]
    assert cookie.startswith(f"token={token};")
    assert "HttpOnly" in cookie
    assert "SameSite=Strict" in cookie


def test_cookie_token_authenticates(static_server: tuple[str, str, str]) -> None:
    """A `token=` cookie is accepted, so follow-up asset requests load."""
    base_url, token, name = static_server
    status, _ = _raw_get(f"{base_url}/{name}", {"Cookie": f"token={token}"})
    assert status == 200


def test_wrong_query_token_is_forbidden_not_unauthorized(
    static_server: tuple[str, str, str],
) -> None:
    """A wrong token in the query is a failed attempt (403), not a missing one."""
    base_url, _, _ = static_server
    status, _ = _raw_get(f"{base_url}/api/stages?token=not-the-right-token")
    assert status == 403


def test_wrong_cookie_token_is_forbidden_not_unauthorized(
    static_server: tuple[str, str, str],
) -> None:
    """Likewise for a wrong token presented as a cookie."""
    base_url, _, _ = static_server
    status, _ = _raw_get(f"{base_url}/api/stages", {"Cookie": "bearer_token=nope"})
    assert status == 403


def test_head_404s_when_static_root_missing(tmp_path: Path) -> None:
    """An authenticated HEAD with no built dashboard is a 404, not a traceback."""
    import sakthai.web.server as srv

    previous_token = srv._BEARER_TOKEN
    srv._BEARER_TOKEN = HEAD_TOKEN
    missing_root = tmp_path / "never-built"
    with patch.object(srv, "_STATIC_ROOT", missing_root):
        server = HTTPServer(("127.0.0.1", 0), _Handler)
        _, port = server.server_address
        thread = threading.Thread(
            target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        thread.start()
        try:
            status, _, _ = _head(
                f"http://127.0.0.1:{port}/index.html",
                {"Authorization": f"Bearer {HEAD_TOKEN}"},
            )
            assert status == 404
        finally:
            server.shutdown()
            thread.join(timeout=5)
    srv._BEARER_TOKEN = previous_token
