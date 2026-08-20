"""Tests for web API bearer token authentication."""

from __future__ import annotations

import http.client
import json
import threading
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
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
    _redact_query_token,
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


def test_token_is_read_back_from_the_store_on_a_cold_start(temp_db: Path) -> None:
    """The second call in the test above never touches SQLite.

    ``_get_or_create_bearer_token`` returns the module-level ``_BEARER_TOKEN``
    cache before opening the store, so calling it twice in one process only
    exercises the *creation* path — the read-back branch stayed in the
    coverage miss list. That branch is what runs on every restart, and
    persisting the token across restarts is the whole point of storing it as a
    fact, so clear the cache to force a genuine cold start.
    """
    with (
        patch("sakthai.memory.store.memory_db_path", return_value=temp_db),
        patch("sakthai.config.memory_db_path", return_value=temp_db),
    ):
        import sakthai.web.server as srv

        srv._BEARER_TOKEN = None
        created = _get_or_create_bearer_token()

        # Simulate a process restart: same DB, empty cache.
        srv._BEARER_TOKEN = None
        recovered = _get_or_create_bearer_token()

        assert recovered == created, "token was regenerated instead of read back from the store"

        # And exactly one token fact exists — a cold start must not append a
        # second row alongside the one it just read.
        with MemoryStore(temp_db) as store:
            facts = store.list_facts(limit=100)
        token_facts = [f for f in facts if f.kind == "web_auth" and f.key == "bearer_token"]
        assert [f.value for f in token_facts] == [created]


def test_token_generation_falls_back_when_the_store_is_unreachable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A broken store must not leave the server with an empty token — that
    would make ``_is_authenticated`` reject every request rather than fail
    safe on a usable one."""
    import sakthai.web.server as srv

    monkeypatch.setattr(srv, "_BEARER_TOKEN", None)

    def _boom(*_args: object, **_kwargs: object) -> None:
        raise OSError("database is locked")

    monkeypatch.setattr("sakthai.memory.store.MemoryStore.__init__", _boom)

    token = _get_or_create_bearer_token()
    assert len(token) == 32

    monkeypatch.setattr(srv, "_BEARER_TOKEN", None)


def test_empty_expected_token_denies_authentication(monkeypatch: pytest.MonkeyPatch) -> None:
    """If token resolution ever yields an empty string, every request must be
    rejected — never treated as "no auth configured, let it through"."""
    import sakthai.web.server as srv

    monkeypatch.setattr(srv, "_get_or_create_bearer_token", lambda: "")

    handler = _Handler.__new__(_Handler)
    handler.headers = {}
    handler.path = "/api/stages"

    assert handler._is_authenticated() is False


@pytest.mark.parametrize(
    ("host", "expected"),
    [
        ("localhost", True),
        ("127.0.0.1", True),
        ("127.0.0.53", True),
        ("::1", True),
        ("0.0.0.0", False),
        ("192.168.1.10", False),
        ("example.com", False),
        ("", False),
    ],
)
def test_loopback_host_detection(host: str, expected: bool) -> None:
    """Drives the non-loopback bind refusal. ``localhost`` is matched by name
    and the rest by address; anything that does not parse as an IP is treated
    as public, since a hostname may resolve anywhere."""
    from sakthai.web.server import _is_loopback_host

    assert _is_loopback_host(host) is expected


# ---------------------------------------------------------------------------
# HTTP Authentication Tests
# ---------------------------------------------------------------------------


@contextmanager
def _background_server() -> Iterator[HTTPServer]:
    """Serve ``_Handler`` on an ephemeral loopback port for the duration of the block.

    ``shutdown()`` alone only stops the ``serve_forever`` loop — it leaves the
    listening socket open, so the FD survives until the garbage collector
    finalizes it. That finalization raises ``ResourceWarning`` from whatever
    test happens to be running at the time rather than from the fixture that
    leaked it, so the teardown must close the socket explicitly.
    """
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(
        target=server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.fixture(scope="module")
def authed_server_base() -> Iterator[tuple[str, str]]:
    """Start an authenticated HTTPServer and return (base_url, token)."""
    # Force generate a custom token for testing
    import sakthai.web.server as srv

    # Restored on teardown: `_BEARER_TOKEN` is process-global, so leaving the
    # test value behind makes any later test that reads it order-dependent.
    previous_token = srv._BEARER_TOKEN
    srv._BEARER_TOKEN = "test_bearer_token_12345678"

    try:
        with _background_server() as server:
            _, port = server.server_address
            yield f"http://127.0.0.1:{port}", "test_bearer_token_12345678"
    finally:
        srv._BEARER_TOKEN = previous_token


def test_background_server_teardown_closes_the_listening_socket() -> None:
    """Pin the teardown contract, not just "the block exited".

    A teardown that calls only ``shutdown()`` still passes every request-level
    assertion in this module — the leak surfaces later, as a ResourceWarning
    charged to an unrelated test — so assert the FD itself is released.
    """
    with _background_server() as server:
        assert server.socket.fileno() != -1

    assert server.socket.fileno() == -1, "listening socket outlived the server context"


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


# --- HEAD is gated exactly like GET ----------------------------------------
# ``SimpleHTTPRequestHandler`` ships its own ``do_HEAD``. Inheriting it unchanged
# served HEAD straight out of ``send_head()``, skipping the bearer-token check
# *and* the static-root containment check that ``do_GET`` performs: an
# unauthenticated HEAD disclosed the existence, size and mtime of files under the
# static root, and followed symlinks out of it that an authenticated GET rejects
# with 403. These pin the gate on the verb, not just on GET.


def _request(
    method: str, url: str, headers: dict[str, str], timeout: int = 5
) -> tuple[int, dict[str, str], bytes]:
    """Issue an arbitrary-method request, returning (status, headers, body)."""
    parts = urllib.parse.urlsplit(url)
    conn = http.client.HTTPConnection(parts.hostname or "", parts.port or 80, timeout=timeout)
    try:
        target = parts.path + (f"?{parts.query}" if parts.query else "")
        conn.request(method, target, headers=headers)
        resp = conn.getresponse()
        return resp.status, dict(resp.getheaders()), resp.read()
    finally:
        conn.close()


def test_head_on_static_path_is_unauthorized_without_a_token(
    authed_server_base: tuple[str, str],
) -> None:
    """The core bypass: HEAD must not be served where GET answers 401."""
    base_url, _ = authed_server_base
    status, _, _ = _request("HEAD", f"{base_url}/index.html", {})
    assert status == 401


def test_head_on_api_path_is_unauthorized_without_a_token(
    authed_server_base: tuple[str, str],
) -> None:
    """HEAD on an API endpoint is gated identically to GET."""
    base_url, _ = authed_server_base
    status, _, _ = _request("HEAD", f"{base_url}/api/stages", {})
    assert status == 401


def test_head_matches_get_status_across_paths_and_credentials(
    authed_server_base: tuple[str, str],
) -> None:
    """Pin the invariant itself: HEAD and GET agree on status for every case.

    Asserting the *agreement* rather than a hardcoded list is what stops the two
    verbs drifting apart again if routing changes.
    """
    base_url, token = authed_server_base
    good = {"Authorization": f"Bearer {token}"}
    bad = {"Authorization": "Bearer wrong_token_xyz"}
    for path, headers in [
        ("/health", {}),
        ("/api/stages", good),
        ("/api/stages", {}),
        ("/api/stages", bad),
        ("/api/ecosystem", good),
        ("/index.html", good),
        ("/index.html", {}),
    ]:
        get_status, _, _ = _request("GET", f"{base_url}{path}", headers)
        head_status, _, _ = _request("HEAD", f"{base_url}{path}", headers)
        assert head_status == get_status, f"HEAD/GET disagree on {path} (auth={bool(headers)})"


def test_head_sends_no_body_but_keeps_content_length(
    authed_server_base: tuple[str, str],
) -> None:
    """HEAD must advertise the length GET would send while writing no body."""
    base_url, token = authed_server_base
    good = {"Authorization": f"Bearer {token}"}
    get_status, _, get_body = _request("GET", f"{base_url}/api/stages", good)
    head_status, head_headers, head_body = _request("HEAD", f"{base_url}/api/stages", good)
    assert (get_status, head_status) == (200, 200)
    assert head_body == b""
    assert head_headers["Content-Length"] == str(len(get_body))


def test_unauthenticated_head_discloses_no_file_metadata(tmp_path: Path) -> None:
    """With a real static root present, HEAD leaks neither existence nor size.

    The module-level ``_STATIC_ROOT`` does not exist in this repo, so the leak
    only shows up once a built dashboard is on disk — which is exactly the
    deployed configuration.
    """
    import sakthai.web.server as srv

    static_root = tmp_path / "dist"
    static_root.mkdir()
    (static_root / "asset.js").write_text("console.log('sensitive')")

    previous_root, previous_token = srv._STATIC_ROOT, srv._BEARER_TOKEN
    srv._STATIC_ROOT = static_root
    srv._BEARER_TOKEN = "test_bearer_token_12345678"
    try:
        with _background_server() as server:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            present, present_headers, _ = _request("HEAD", f"{base_url}/asset.js", {})
            missing, _, _ = _request("HEAD", f"{base_url}/nope.js", {})

        assert present == 401
        # The response must not carry the asset's real size...
        assert present_headers.get("Content-Length") != str(len("console.log('sensitive')"))
        # ...nor let a present file be told apart from an absent one.
        assert present == missing
    finally:
        srv._STATIC_ROOT, srv._BEARER_TOKEN = previous_root, previous_token


def test_head_cannot_follow_a_symlink_out_of_the_static_root(tmp_path: Path) -> None:
    """HEAD is subject to the same containment check as GET.

    An authenticated GET answers 403 for a symlink escaping the static root; an
    unauthenticated HEAD used to answer 200 for the same target.
    """
    import sakthai.web.server as srv

    static_root = tmp_path / "dist"
    static_root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("escaped the static root")
    (static_root / "link.txt").symlink_to(outside)

    previous_root, previous_token = srv._STATIC_ROOT, srv._BEARER_TOKEN
    srv._STATIC_ROOT = static_root
    srv._BEARER_TOKEN = "test_bearer_token_12345678"
    try:
        with _background_server() as server:
            base_url = f"http://127.0.0.1:{server.server_address[1]}"
            good = {"Authorization": "Bearer test_bearer_token_12345678"}
            authed_get, _, _ = _request("GET", f"{base_url}/link.txt", good)
            authed_head, _, _ = _request("HEAD", f"{base_url}/link.txt", good)
            anon_head, _, _ = _request("HEAD", f"{base_url}/link.txt", {})

        assert authed_get == 403
        assert authed_head == 403
        assert anon_head == 401
    finally:
        srv._STATIC_ROOT, srv._BEARER_TOKEN = previous_root, previous_token


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


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("GET /api/stages?token=deadbeef HTTP/1.1", "GET /api/stages?token=[REDACTED] HTTP/1.1"),
        (
            "GET /?bearer_token=abc123&days=7 HTTP/1.1",
            "GET /?bearer_token=[REDACTED]&days=7 HTTP/1.1",
        ),
        ("GET /?TOKEN=Secret9 HTTP/1.1", "GET /?TOKEN=[REDACTED] HTTP/1.1"),
        # No token: left untouched.
        ("GET /health HTTP/1.1", "GET /health HTTP/1.1"),
    ],
)
def test_redact_query_token_masks_credentials(raw: str, expected: str) -> None:
    """The bearer token in a request line is masked by parameter name."""
    assert _redact_query_token(raw) == expected


def test_log_message_never_emits_the_token() -> None:
    """The real _Handler.log_message must strip ?token=<secret> before logging."""
    # Build a bare handler instance without running BaseHTTPRequestHandler's
    # socket-bound __init__ — log_message needs no request state.
    handler = _Handler.__new__(_Handler)
    secret = "s3cr3t-bearer-value"
    with patch("sakthai.web.server.logger") as mock_logger:
        handler.log_message('"%s" %s %s', f"GET /api/stages?token={secret} HTTP/1.1", "200", "512")
    assert mock_logger.info.called, "log_message should have logged a line"
    # The token must appear in none of the arguments handed to the logger.
    logged = " ".join(str(a) for call in mock_logger.info.call_args_list for a in call.args)
    assert secret not in logged
    assert "token=[REDACTED]" in logged
