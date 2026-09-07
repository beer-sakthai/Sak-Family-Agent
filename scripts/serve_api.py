"""SakThai dashboard/API server.

Serves:
- `/` → `web/index.html`
- `/api/stages` → dashboard data
- `/api/ecosystem` → ecosystem status

Run:
    python scripts/serve_api.py
"""

from __future__ import annotations

import ipaddress
import json
import logging
import os
import secrets
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

WEB_DIR = (Path(__file__).resolve().parent.parent / "dashboard" / "dist").resolve()
_HOST = "127.0.0.1"
_PORT = 3002
_LOOPBACK_NAMES = frozenset({"localhost"})


def _is_loopback_host(host: str) -> bool:
    """True if ``host`` is loopback-only (safe to bind without authentication)."""
    if host in _LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        # A non-literal hostname (other than localhost) may resolve anywhere.
        return False


_BEARER_TOKEN: str | None = None


def _get_or_create_bearer_token() -> str:
    """Retrieve or create an opaque 32-character hex bearer token in MemoryStore."""
    global _BEARER_TOKEN
    if _BEARER_TOKEN is not None:
        return _BEARER_TOKEN

    try:
        import sys
        from pathlib import Path

        REPO_ROOT = (Path(__file__).resolve().parent.parent).resolve()
        if str(REPO_ROOT / "personas" / "sakthai") not in sys.path:
            sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        from sakthai.config import register_secret
        from sakthai.memory.store import MemoryStore

        with MemoryStore() as store:
            fact = store.get_fact_by_key(kind="web_auth", key="bearer_token")
            if fact:
                _BEARER_TOKEN = fact.value
                register_secret(_BEARER_TOKEN)
                return _BEARER_TOKEN

            import secrets

            token = secrets.token_hex(16)
            store.delete_facts_by_key(kind="web_auth", key="bearer_token")
            store.add_fact(
                value=token,
                kind="web_auth",
                key="bearer_token",
                tags=["system", "no-export"],
            )
            register_secret(token)
            _BEARER_TOKEN = token
            return token
    except Exception as exc:
        logging.getLogger(__name__).warning(
            "Failed to get or create bearer token from MemoryStore: %s", exc
        )
        if _BEARER_TOKEN is None:
            import secrets

            _BEARER_TOKEN = secrets.token_hex(16)
        return _BEARER_TOKEN


def _dashboard_data(days: int = 30) -> dict[str, Any]:
    try:
        import sys

        REPO_ROOT = (Path(__file__).resolve().parent.parent).resolve()
        sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))
        sys.path.insert(0, str(REPO_ROOT))
        from sakthai.dashboard.data import collect_dashboard_data

        return collect_dashboard_data(days=days)
    except Exception as exc:  # noqa: BLE001
        logging.getLogger(__name__).warning("dashboard data failed: %s", exc)
        return {
            "generated_at": "demo",
            "source": "demo",
            "kpis": {
                "total_facts": 0,
                "total_facts_delta": 0,
                "total_observations": 0,
                "total_observations_delta": 0,
            },
            "growth": {"labels": [], "facts": [], "observations": []},
            "recent_facts": [],
            "top_observations": [],
            "categories": [],
        }


def _ecosystem_status() -> dict[str, Any]:
    return {
        "generated_at": "unknown",
        "composio_mcp": "unknown",
        "huggingface": "unknown",
        "cron_jobs": [],
        "supermemory": "unknown",
    }


class _Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Secure fallback: explicitly bind the static files directory to WEB_DIR
        # to prevent fallback file serving from the process's working directory.
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def address_string(self) -> str:
        return self.client_address[0]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        logging.getLogger(__name__).info(format, *args)

    def _has_auth_attempt(self) -> bool:
        """True if the request contains any authentication credentials."""
        if self.headers.get("Authorization"):
            return True
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            for item in query.split("&"):
                if "=" in item:
                    k, _ = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        return True
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, _ = item.strip().split("=", 1)
                    if k in ("token", "bearer_token"):
                        return True
        return False

    def _is_authenticated(self) -> bool:
        expected_token = _get_or_create_bearer_token()
        if not expected_token:
            return False

        # 1. Check Authorization header
        auth_header = self.headers.get("Authorization", "")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if secrets.compare_digest(token, expected_token):
                return True

        # 2. Check query parameter 'token' or 'bearer_token'
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            for item in query.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            return True

        # 3. Check Cookie header
        cookie_header = self.headers.get("Cookie", "")
        if cookie_header:
            for item in cookie_header.split(";"):
                if "=" in item:
                    k, v = item.strip().split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            return True

        return False

    def end_headers(self) -> None:
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; img-src 'self' data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
        )
        # If authenticated via query param, set cookie so subsequent static asset requests load seamlessly
        parsed = urlparse(self.path)
        query = parsed.query
        if query:
            expected_token = _get_or_create_bearer_token()
            for item in query.split("&"):
                if "=" in item:
                    k, v = item.split("=", 1)
                    if k in ("token", "bearer_token"):
                        val = unquote(v)
                        if secrets.compare_digest(val, expected_token):
                            self.send_header(
                                "Set-Cookie",
                                f"token={expected_token}; Path=/; HttpOnly; SameSite=Strict",
                            )
                            break
        super().end_headers()

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        try:
            from sakthai.config import redact_secrets

            raw_body = json.dumps(payload, indent=2, ensure_ascii=False)
            redacted_body = redact_secrets(raw_body)
        except Exception:
            raw_body = json.dumps(payload, indent=2, ensure_ascii=False)
            redacted_body = raw_body
        body = redacted_body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        logging.getLogger(__name__).info("GET request for path: %s", self.path)
        parsed = urlparse(self.path)
        path = parsed.path.rstrip("/") or "/"

        if path == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", "16")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
            return

        if path.startswith("/api/"):
            if not self._is_authenticated():
                auth_header = self.headers.get("Authorization", "")
                if auth_header and not auth_header.startswith("Bearer "):
                    self._json(
                        401,
                        {
                            "error": "Unauthorized",
                            "message": "Authorization header must be in 'Bearer <token>' format",
                        },
                    )
                    return

                if not self._has_auth_attempt():
                    self._json(
                        401, {"error": "Unauthorized", "message": "Missing Authorization header"}
                    )
                else:
                    self._json(403, {"error": "Forbidden", "message": "Invalid Bearer token"})
                return
        else:
            if not self._is_authenticated():
                self.send_response(401)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"Unauthorized: Missing or invalid bearer token")
                return

        if path == "/api/stages":
            try:
                qs = dict(item.split("=") for item in parsed.query.split("&") if "=" in item)
                days = int(qs.get("days", "30"))
            except Exception:
                days = 30
            self._json(200, _dashboard_data(days=days))
            return

        if path == "/api/ecosystem":
            self._json(200, _ecosystem_status())
            return

        if path.startswith("/api/"):
            self.send_error(403, "Forbidden")
            return

        # Serve static files from web/ (path-traversal safe). `serve()` chdir's
        # to WEB_DIR, so the stdlib handler resolves requests relative to it;
        # mirror that here, reject anything that canonicalises outside the root,
        # then delegate the actual read to SimpleHTTPRequestHandler (whose
        # translate_path performs its own safe path handling). The
        # realpath + startswith form is the sanitizer CodeQL recognizes.
        try:
            root = os.path.realpath(str(WEB_DIR))
            requested = unquote(parsed.path).lstrip("/\\")
            candidate = os.path.realpath(os.path.join(root, requested))
            if candidate != root and not candidate.startswith(root + os.sep):
                self.send_error(403, "Forbidden")
                return
        except Exception:
            self.send_error(403, "Forbidden")
            return

        # Explicitly verify the static files directory exists before serving.
        if not WEB_DIR.is_dir():
            self.send_error(404, "File not found")
            return

        return super().do_GET()


def serve(host: str = _HOST, port: int = _PORT) -> HTTPServer:
    # API endpoints require a Bearer token, but the loopback default is
    # defense-in-depth: personal memory should not be reachable off-host by
    # default. Require an explicit opt-in for any non-loopback bind.
    if not _is_loopback_host(host) and not os.environ.get("SAKTHAI_WEB_ALLOW_PUBLIC"):
        raise PermissionError(
            f"Refusing to bind the API to non-loopback host {host!r}. "
            "It serves personal memory; set SAKTHAI_WEB_ALLOW_PUBLIC=1 to "
            "override once you have placed authentication in front of it."
        )
    _get_or_create_bearer_token()  # Warm cache & register secret
    os.chdir(str(WEB_DIR))
    srv = HTTPServer((host, port), _Handler)
    logging.getLogger(__name__).info("SakThai API on http://%s:%d  static=%s", host, port, WEB_DIR)
    return srv


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    srv = serve()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        raise SystemExit(0) from None
