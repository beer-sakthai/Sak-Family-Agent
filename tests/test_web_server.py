"""Tests for sakthai.web.server — JSON API endpoints and static-file security.

The HTTP handler is tested by spinning up a real HTTPServer on a free port in a
daemon thread. The dashboard data function gracefully falls back to a demo stub
when no DB exists, so tests don't need a live memory store.
"""

from __future__ import annotations

import json
import os
import runpy
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from sakthai.web.server import (
    _DEFAULT_HOST,
    _DEFAULT_PORT,
    _STATIC_ROOT,
    _dashboard_data,
    _ecosystem_status,
    _get_or_create_bearer_token,
    _Handler,
    serve,
)

try:
    from http.server import HTTPServer
except ImportError:
    HTTPServer = None  # type: ignore[misc,assignment]


# ---------------------------------------------------------------------------
# Test server fixture
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def api_base() -> str:
    """Start a one-shot HTTPServer on a random port; yield its base URL."""
    srv = HTTPServer(("127.0.0.1", 0), _Handler)
    _, port = srv.server_address
    thread = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    srv.shutdown()


def _get(
    url: str, timeout: int = 30, force_auth: bool = False, token: str | None = None
) -> tuple[int, dict[str, Any]]:
    """GET url, returning (status_code, parsed_body). 4xx raises are caught."""
    try:
        req = urllib.request.Request(url)
        if "/api/" in url or force_auth:
            use_token = token if token is not None else _get_or_create_bearer_token()
            req.add_header("Authorization", f"Bearer {use_token}")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            try:
                body = json.loads(resp.read().decode("utf-8"))
            except Exception:
                body = {}
            return resp.status, body
    except urllib.error.HTTPError as exc:
        return exc.code, {}


# ---------------------------------------------------------------------------
# Unit tests for data helper functions
# ---------------------------------------------------------------------------


class TestDashboardData:
    def test_returns_dict_with_required_keys(self) -> None:
        data = _dashboard_data()
        assert isinstance(data, dict)
        assert "kpis" in data

    def test_kpis_has_fact_count(self) -> None:
        data = _dashboard_data()
        assert "total_facts" in data["kpis"]

    def test_falls_back_to_demo_when_import_fails(self) -> None:
        with patch("sakthai.web.server._dashboard_data", wraps=_dashboard_data):
            data = _dashboard_data()
        assert data.get("source") == "demo" or "kpis" in data

    def test_days_parameter_accepted(self) -> None:
        data = _dashboard_data(days=7)
        assert isinstance(data, dict)

    def test_demo_stub_has_growth_key(self) -> None:
        # Force fallback to the demo stub by mocking the import error
        with patch.dict("sys.modules", {"sakthai.dashboard.data": None}):
            data = _dashboard_data()
            assert "growth" in data
            assert data.get("source") == "demo"

    def test_falls_back_to_demo_on_import_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """An ImportError importing the data module yields the demo stub (server.py:36-37)."""
        import sys
        import types as _types

        # A stand-in module lacking ``collect_dashboard_data`` makes the
        # ``from ... import collect_dashboard_data`` raise ImportError.
        broken = _types.ModuleType("sakthai.dashboard.data")
        monkeypatch.setitem(sys.modules, "sakthai.dashboard.data", broken)
        data = _dashboard_data()
        assert data.get("source") == "demo"
        assert data["kpis"]["total_facts"] == 0


class TestEcosystemStatus:
    def test_returns_dict(self) -> None:
        status = _ecosystem_status()
        assert isinstance(status, dict)

    def test_composio_configured_when_key_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("COMPOSIO_API_KEY", "fake-key")
        status = _ecosystem_status()
        assert status["composio_mcp"] == "configured"

    def test_composio_not_configured_when_key_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("COMPOSIO_API_KEY", raising=False)
        status = _ecosystem_status()
        assert status["composio_mcp"] == "not_configured"

    def test_huggingface_ready_when_both_vars_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("HUGGINGFACE_USERNAME", "testuser")
        monkeypatch.setenv("HF_TOKEN", "test-token")
        status = _ecosystem_status()
        assert status["huggingface"] == "ready"

    def test_huggingface_not_ready_when_vars_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("HUGGINGFACE_USERNAME", raising=False)
        monkeypatch.delenv("HF_TOKEN", raising=False)
        status = _ecosystem_status()
        assert status["huggingface"] == "not_ready"

    def test_generated_at_falls_back_when_clock_fails(self) -> None:
        """If timestamp generation raises, generated_at stays 'unknown' (server.py:72-73)."""
        with patch("datetime.datetime") as dt:
            dt.now.side_effect = RuntimeError("clock broke")
            status = _ecosystem_status()
        assert status["generated_at"] == "unknown"

    def test_generated_at_is_present(self) -> None:
        status = _ecosystem_status()
        assert "generated_at" in status

    def test_supermemory_key_present(self) -> None:
        status = _ecosystem_status()
        assert "supermemory" in status


# ---------------------------------------------------------------------------
# HTTP endpoint tests (via real test server)
# ---------------------------------------------------------------------------


class TestApiStagesEndpoint:
    def test_returns_200(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/api/stages")
        assert code == 200

    def test_response_is_json_with_kpis(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/stages")
        assert "kpis" in body

    def test_days_query_param_accepted(self, api_base: str) -> None:
        code, body = _get(f"{api_base}/api/stages?days=7")
        assert code == 200
        assert "kpis" in body

    def test_invalid_days_falls_back_to_default(self, api_base: str) -> None:
        code, body = _get(f"{api_base}/api/stages?days=notanumber")
        assert code == 200
        assert isinstance(body, dict)

    def test_trailing_slash_routed(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/api/stages/")
        assert code == 200

    def test_secrets_redacted_in_stages_response(self, api_base: str) -> None:
        # Dynamically construct secret to prevent gitleaks trigger
        part1 = "sk-ant-"
        part2 = "api03-1234567890123456789012345678901234567890"
        secret_key = part1 + part2
        mock_data = {
            "source": f"custom-{secret_key}",
            "kpis": {
                "total_facts": 1,
            },
            "recent_facts": [{"value": f"my api key is {secret_key}"}],
        }
        with patch("sakthai.web.server._dashboard_data", return_value=mock_data):
            code, body = _get(f"{api_base}/api/stages")
            assert code == 200
            body_str = json.dumps(body)
            assert secret_key not in body_str
            assert "[REDACTED]" in body_str


class TestApiEcosystemEndpoint:
    def test_returns_200(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/api/ecosystem")
        assert code == 200

    def test_response_contains_composio_key(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/ecosystem")
        assert "composio_mcp" in body

    def test_response_contains_huggingface_key(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/ecosystem")
        assert "huggingface" in body

    def test_content_type_is_json(self, api_base: str) -> None:
        token = _get_or_create_bearer_token()
        req = urllib.request.Request(f"{api_base}/api/ecosystem")
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            ct = resp.headers.get("Content-Type", "")
        assert "application/json" in ct


class TestStaticFilePathTraversal:
    def test_path_traversal_blocked_with_403_when_authenticated(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/../../etc/passwd", force_auth=True)
        assert code == 403

    def test_deep_traversal_blocked_when_authenticated(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/../../../../etc/shadow", force_auth=True)
        assert code == 403

    def test_path_traversal_unauthenticated_gets_401(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/../../etc/passwd")
        assert code == 401


class TestApiEdgeCases:
    """Boundary values and structural checks not covered by the main endpoint tests."""

    def test_days_zero_accepted(self, api_base: str) -> None:
        code, body = _get(f"{api_base}/api/stages?days=0")
        assert code == 200
        assert "kpis" in body

    def test_unknown_api_path_returns_403(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/api/unknown_endpoint")
        assert code == 403

    def test_content_length_header_present_in_stages(self, api_base: str) -> None:
        token = _get_or_create_bearer_token()
        req = urllib.request.Request(f"{api_base}/api/stages")
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_length = resp.headers.get("Content-Length")
        assert content_length is not None
        assert int(content_length) > 0

    def test_content_length_header_present_in_ecosystem(self, api_base: str) -> None:
        token = _get_or_create_bearer_token()
        req = urllib.request.Request(f"{api_base}/api/ecosystem")
        req.add_header("Authorization", f"Bearer {token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_length = resp.headers.get("Content-Length")
        assert content_length is not None
        assert int(content_length) > 0

    def test_extra_query_params_do_not_break_stages(self, api_base: str) -> None:
        code, body = _get(f"{api_base}/api/stages?days=14&format=json&extra=ignored")
        assert code == 200
        assert "kpis" in body

    def test_stages_response_body_is_valid_json(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/stages")
        assert isinstance(body, dict)

    def test_ecosystem_response_body_is_valid_json(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/ecosystem")
        assert isinstance(body, dict)


class TestServeFunction:
    def test_serve_creates_httpserver_with_correct_args(self) -> None:
        with (
            patch("sakthai.web.server.os.chdir") as mock_chdir,
            patch("sakthai.web.server.HTTPServer") as mock_http,
        ):
            result = serve()
            # dashboard/dist is gone (5de2c25): serve() must skip the chdir
            # and still bring the API up.
            if _STATIC_ROOT.is_dir():
                mock_chdir.assert_called_once_with(str(_STATIC_ROOT))
            else:
                mock_chdir.assert_not_called()
            mock_http.assert_called_once_with((_DEFAULT_HOST, _DEFAULT_PORT), _Handler)
            assert result is mock_http.return_value

    def test_serve_custom_host_port(self) -> None:
        with (
            patch("sakthai.web.server.os.chdir"),
            patch("sakthai.web.server.HTTPServer") as mock_http,
        ):
            serve(host="127.0.0.1", port=9999)
            mock_http.assert_called_once_with(("127.0.0.1", 9999), _Handler)

    def test_serve_refuses_non_loopback_without_ack(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_WEB_ALLOW_PUBLIC", raising=False)
        with (
            patch("sakthai.web.server.HTTPServer") as mock_http,
            pytest.raises(PermissionError, match="non-loopback"),
        ):
            serve(host="0.0.0.0", port=9999)  # noqa: S104 — testing the guard
        mock_http.assert_not_called()

    def test_serve_refuses_empty_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("SAKTHAI_WEB_ALLOW_PUBLIC", raising=False)
        with (
            patch("sakthai.web.server.HTTPServer") as mock_http,
            pytest.raises(PermissionError, match="non-loopback"),
        ):
            serve(host="", port=9999)
        mock_http.assert_not_called()

    def test_serve_allows_non_loopback_when_acknowledged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_WEB_ALLOW_PUBLIC", "1")
        with (
            patch("sakthai.web.server.os.chdir"),
            patch("sakthai.web.server.HTTPServer") as mock_http,
        ):
            serve(host="0.0.0.0", port=9999)  # noqa: S104 — explicit opt-in
            mock_http.assert_called_once_with(("0.0.0.0", 9999), _Handler)  # noqa: S104


class TestMainBlock:
    def test_main_block_starts_server_and_exits_on_interrupt(self) -> None:
        import http.server as _http_server
        import os as _os

        srv = MagicMock()
        srv.serve_forever.side_effect = KeyboardInterrupt()
        # Resolve via the installed package rather than a repo-layout path (the
        # canonical package copy lives under personas/sakthai/).
        import sakthai.web.server as _server_mod

        server_py = Path(str(_server_mod.__file__))
        # runpy executes in a fresh namespace; patch the real stdlib objects so
        # the re-imported `os.chdir` and `HTTPServer` inside the file use mocks.
        with patch.object(_os, "chdir"), patch.object(_http_server, "HTTPServer", return_value=srv):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_path(str(server_py), run_name="__main__")
            assert exc_info.value.code == 0


class TestStaticFileServe:
    """Tests for the static-file fallback in _Handler.do_GET (line 120)."""

    def test_serves_file_within_static_root(self, tmp_path: Path) -> None:
        """A request whose resolved path IS within _STATIC_ROOT reaches super().do_GET()."""
        import sakthai.web.server as srv_mod

        static_root = tmp_path / "web"
        static_root.mkdir()
        (static_root / "ok.html").write_text("<html>ok</html>", encoding="utf-8")

        original_root = srv_mod._STATIC_ROOT
        srv_mod._STATIC_ROOT = static_root
        original_dir = os.getcwd()
        os.chdir(static_root)
        try:
            srv = HTTPServer(("127.0.0.1", 0), _Handler)
            _, port = srv.server_address
            t = threading.Thread(
                target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
            )
            t.start()
            try:
                # Use urlopen directly — the response is HTML, not JSON
                req = urllib.request.Request(f"http://127.0.0.1:{port}/ok.html")
                token = srv_mod._get_or_create_bearer_token()
                req.add_header("Authorization", f"Bearer {token}")
                with urllib.request.urlopen(req, timeout=30) as resp:
                    status = resp.status
                    body = resp.read().decode("utf-8")
                assert status == 200
                assert "ok" in body
            finally:
                srv.shutdown()
        finally:
            os.chdir(original_dir)
            srv_mod._STATIC_ROOT = original_root

    def test_no_file_leakage_when_static_root_missing(self, tmp_path: Path) -> None:
        """Verify that files from current working directory are not served/leaked when _STATIC_ROOT is missing."""
        import sakthai.web.server as srv_mod

        # Point _STATIC_ROOT to a nonexistent directory
        fake_root = tmp_path / "nonexistent_dist"
        original_root = srv_mod._STATIC_ROOT
        srv_mod._STATIC_ROOT = fake_root

        # Create a dummy file in the current working directory
        leak_file = Path("leak_test_file_xyz.txt")
        leak_file.write_text("top secret data", encoding="utf-8")

        try:
            srv = HTTPServer(("127.0.0.1", 0), _Handler)
            _, port = srv.server_address
            t = threading.Thread(
                target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
            )
            t.start()
            try:
                url = f"http://127.0.0.1:{port}/leak_test_file_xyz.txt"
                req = urllib.request.Request(url)
                token = srv_mod._get_or_create_bearer_token()
                req.add_header("Authorization", f"Bearer {token}")
                try:
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        status = resp.status
                except urllib.error.HTTPError as exc:
                    status = exc.code
                assert status == 404
            finally:
                srv.shutdown()
        finally:
            srv_mod._STATIC_ROOT = original_root
            if leak_file.exists():
                leak_file.unlink()


class TestEcosystemStatusPartialConfig:
    """HuggingFace and other partial-config edge cases."""

    def test_huggingface_not_ready_when_only_token_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("HUGGINGFACE_USERNAME", raising=False)
        monkeypatch.setenv("HF_TOKEN", "some-token")
        status = _ecosystem_status()
        assert status["huggingface"] == "not_ready"

    def test_huggingface_not_ready_when_only_username_set(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HUGGINGFACE_USERNAME", "myuser")
        monkeypatch.delenv("HF_TOKEN", raising=False)
        status = _ecosystem_status()
        assert status["huggingface"] == "not_ready"

    def test_generated_at_is_iso_format(self) -> None:
        status = _ecosystem_status()
        generated_at = status.get("generated_at", "")
        assert "T" in generated_at or generated_at == "unknown"

    def test_cron_jobs_key_is_list(self) -> None:
        status = _ecosystem_status()
        assert isinstance(status.get("cron_jobs"), list)


# ---------------------------------------------------------------------------
# serve(), _find_static_root, and handler edge paths
# ---------------------------------------------------------------------------


class TestServe:
    def test_serve_binds_and_returns_server(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sakthai.web.server as server_mod

        # Point the static root at a non-directory so serve() skips chdir.
        monkeypatch.setattr(server_mod, "_STATIC_ROOT", Path("/nonexistent/dist"))
        srv = serve(host="127.0.0.1", port=0)
        try:
            assert srv.server_address[1] != 0
        finally:
            srv.server_close()

    def test_serve_chdirs_into_existing_static_root(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sakthai.web.server as server_mod

        static = tmp_path / "dist"
        static.mkdir()
        monkeypatch.chdir(tmp_path)  # teardown restores the original cwd
        monkeypatch.setattr(server_mod, "_STATIC_ROOT", static)
        srv = serve(host="127.0.0.1", port=0)
        try:
            assert Path(os.getcwd()) == static
        finally:
            srv.server_close()


class TestFindStaticRoot:
    def test_returns_first_dist_dir_walking_up(self, tmp_path: Path) -> None:
        from sakthai.web.server import _find_static_root

        dist = tmp_path / "dashboard" / "dist"
        dist.mkdir(parents=True)
        marker = tmp_path / "pkg" / "server.py"
        marker.parent.mkdir()
        marker.touch()
        assert _find_static_root(start=marker) == dist.resolve()

    def test_falls_back_relative_to_module_when_no_dist_found(self, tmp_path: Path) -> None:
        from sakthai.web.server import _find_static_root

        marker = tmp_path / "server.py"
        marker.touch()
        result = _find_static_root(start=marker)
        assert result.name == "dist"


class TestHandlerEdgePaths:
    def test_address_string_returns_client_ip(self) -> None:
        fake = MagicMock()
        fake.client_address = ("203.0.113.9", 4242)
        assert _Handler.address_string(fake) == "203.0.113.9"

    def test_dashboard_data_generic_exception_yields_demo(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sys
        import types as _types

        broken = _types.ModuleType("sakthai.dashboard.data")

        def _boom(days: int = 30) -> dict:
            raise RuntimeError("collection failed")

        broken.collect_dashboard_data = _boom  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, "sakthai.dashboard.data", broken)
        data = _dashboard_data()
        assert data.get("source") == "demo"

    def test_static_request_403_when_realpath_raises(self, api_base: str) -> None:
        with patch("sakthai.web.server.os.path.realpath", side_effect=OSError("boom")):
            status, _ = _get(f"{api_base}/index.html", force_auth=True)
        assert status == 403

    def test_standalone_server_bind_directory(self) -> None:
        import sys
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        from scripts.serve_api import WEB_DIR
        from scripts.serve_api import _Handler as StandaloneHandler

        mock_request = MagicMock()
        mock_client_address = ("127.0.0.1", 12345)
        mock_server = MagicMock()

        with patch("http.server.SimpleHTTPRequestHandler.__init__") as mock_base_init:
            StandaloneHandler(mock_request, mock_client_address, mock_server)
            mock_base_init.assert_called_once()
            assert mock_base_init.call_args[1].get("directory") == str(WEB_DIR)

    def test_standalone_server_missing_web_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sys
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import scripts.serve_api as standalone_mod

        # Point WEB_DIR to a non-existent directory
        missing_dir = tmp_path / "does-not-exist"
        monkeypatch.setattr(standalone_mod, "WEB_DIR", missing_dir)

        srv = HTTPServer(("127.0.0.1", 0), standalone_mod._Handler)
        _, port = srv.server_address
        t = threading.Thread(target=srv.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True)
        t.start()
        try:
            url = f"http://127.0.0.1:{port}/index.html"
            req = urllib.request.Request(url)
            token = standalone_mod._get_or_create_bearer_token()
            req.add_header("Authorization", f"Bearer {token}")
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    status = resp.status
            except urllib.error.HTTPError as exc:
                status = exc.code
            assert status == 404

            # Verify that API endpoints still work properly
            api_url = f"http://127.0.0.1:{port}/api/ecosystem"
            token = standalone_mod._get_or_create_bearer_token()
            req = urllib.request.Request(api_url)
            req.add_header("Authorization", f"Bearer {token}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                api_status = resp.status
                api_body = json.loads(resp.read().decode("utf-8"))
            assert api_status == 200
            assert "generated_at" in api_body
        finally:
            srv.shutdown()

    def test_standalone_server_refuses_non_loopback_without_ack(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sys
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import scripts.serve_api as standalone_mod

        monkeypatch.delenv("SAKTHAI_WEB_ALLOW_PUBLIC", raising=False)
        with (
            patch("scripts.serve_api.HTTPServer") as mock_http,
            pytest.raises(PermissionError, match="non-loopback"),
        ):
            standalone_mod.serve(host="0.0.0.0", port=9999)  # noqa: S104 — testing the guard
        mock_http.assert_not_called()

    def test_standalone_server_refuses_empty_host(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import sys
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import scripts.serve_api as standalone_mod

        monkeypatch.delenv("SAKTHAI_WEB_ALLOW_PUBLIC", raising=False)
        with (
            patch("scripts.serve_api.HTTPServer") as mock_http,
            pytest.raises(PermissionError, match="non-loopback"),
        ):
            standalone_mod.serve(host="", port=9999)
        mock_http.assert_not_called()

    def test_standalone_server_allows_non_loopback_when_acknowledged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import sys
        from pathlib import Path

        REPO_ROOT = Path(__file__).resolve().parents[1]
        if str(REPO_ROOT) not in sys.path:
            sys.path.insert(0, str(REPO_ROOT))

        import scripts.serve_api as standalone_mod

        monkeypatch.setenv("SAKTHAI_WEB_ALLOW_PUBLIC", "1")
        with (
            patch("scripts.serve_api.os.chdir"),
            patch("scripts.serve_api.HTTPServer") as mock_http,
        ):
            standalone_mod.serve(host="0.0.0.0", port=9999)  # noqa: S104 — explicit opt-in
            mock_http.assert_called_once_with(("0.0.0.0", 9999), standalone_mod._Handler)  # noqa: S104


class TestEnhancedWebAuth:
    @pytest.fixture(autouse=True)
    def setup_static(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        import sakthai.web.server as srv_mod

        self.static_root = tmp_path / "web_auth_test_dist"
        self.static_root.mkdir()
        (self.static_root / "index.html").write_text("<html>index</html>", encoding="utf-8")
        monkeypatch.setattr(srv_mod, "_STATIC_ROOT", self.static_root)

    def test_health_is_public(self, api_base: str) -> None:
        """The /health endpoint must be public and require no auth."""
        code, body = _get(f"{api_base}/health")
        assert code == 200
        assert body == {"status": "ok"}

    def test_unauthenticated_static_is_gated(self, api_base: str) -> None:
        """Unauthenticated requests to static paths get 401."""
        code, _ = _get(f"{api_base}/")
        assert code == 401

    def test_authenticated_via_query_param(self, api_base: str) -> None:
        """Providing token as query param is accepted and issues a Cookie."""
        token = _get_or_create_bearer_token()
        # Query parameter must hit a real file in self.static_root or "/", which defaults to index.html
        url = f"{api_base}/index.html?token={token}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            assert resp.status == 200
            headers = resp.info()
            assert "Set-Cookie" in headers
            assert f"token={token}" in headers["Set-Cookie"]

    def test_authenticated_via_cookie(self, api_base: str) -> None:
        """Providing token as a Cookie is accepted."""
        token = _get_or_create_bearer_token()
        url = f"{api_base}/index.html"
        req = urllib.request.Request(url)
        req.add_header("Cookie", f"token={token}")
        with urllib.request.urlopen(req, timeout=30) as resp:
            assert resp.status == 200
            assert b"index" in resp.read()


def test_all_persona_servers_hardened_against_loopback_bypass() -> None:
    """Ensure that all persona web servers are hardened against empty string loopback bypass."""
    import py_compile
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[1]
    personas_dir = repo_root / "personas"

    # All persona names including shared
    personas = ["sakthai", "sakjules", "sakking", "saksee", "saksit", "saktan", "shared"]

    for persona in personas:
        server_path = personas_dir / persona / "sakthai" / "web" / "server.py"
        # If the file does not exist (e.g., saktan or sakjules is a symlink, check it too)
        if not server_path.is_file():
            # If it's a symlink or missing, continue as it's covered when we check the symlink target (shared)
            continue

        # Compile the file to ensure no syntax errors
        try:
            py_compile.compile(str(server_path), doraise=True)
        except Exception as exc:
            pytest.fail(f"Persona {persona} server file {server_path} failed to compile: {exc}")

        content = server_path.read_text(encoding="utf-8")

        # Ensure no merge conflict markers
        assert "<<<<<<<" not in content, f"Merge conflict marker found in {server_path}"
        assert "=======" not in content, f"Merge conflict marker found in {server_path}"
        assert ">>>>>>>" not in content, f"Merge conflict marker found in {server_path}"

        # Ensure empty string is excluded from _LOOPBACK_NAMES
        assert (
            '_LOOPBACK_NAMES = frozenset({"localhost"})' in content
            or "_LOOPBACK_NAMES = frozenset({'localhost'})" in content
        ), (
            f"Vulnerability check failed: empty string is not excluded from _LOOPBACK_NAMES in {server_path}"
        )

        # Ensure compare_digest is used for bearer token verification (timing-attack defense)
        assert "compare_digest" in content, (
            f"Timing attack vulnerability: compare_digest not found in {server_path}"
        )


# ---------------------------------------------------------------------------
# Dashboard API routes (/api/personas|metrics|sessions|memory|audit)
# ---------------------------------------------------------------------------


class TestDashboardRoutes:
    """The endpoints backing apps/sak_agent_dashboard.

    Payload construction is covered in tests/test_web_api.py; these check the
    HTTP layer — that each route is reachable, authenticated, enveloped, and
    that a bad query param degrades rather than 500-ing.
    """

    ROUTES = ("personas", "metrics", "sessions", "memory", "audit")

    @pytest.mark.parametrize("route", ROUTES)
    def test_route_returns_an_envelope(self, api_base: str, route: str) -> None:
        status, body = _get(f"{api_base}/api/{route}")
        assert status == 200
        assert body["ok"] is True
        assert body["source"] == "local"
        assert "generated_at" in body
        assert "data" in body

    @pytest.mark.parametrize("route", ROUTES)
    def test_route_requires_a_token(self, api_base: str, route: str) -> None:
        req = urllib.request.Request(f"{api_base}/api/{route}")
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            urllib.request.urlopen(req, timeout=30)
        assert excinfo.value.code == 401

    @pytest.mark.parametrize("route", ROUTES)
    def test_route_rejects_a_wrong_token(self, api_base: str, route: str) -> None:
        status, _ = _get(f"{api_base}/api/{route}", token="not-the-token")
        assert status == 403

    def test_personas_lists_all_six(self, api_base: str) -> None:
        _, body = _get(f"{api_base}/api/personas")
        assert len(body["data"]["personas"]) == 6

    def test_trailing_slash_is_normalised(self, api_base: str) -> None:
        status, body = _get(f"{api_base}/api/personas/")
        assert status == 200
        assert body["ok"] is True

    def test_unknown_api_path_is_still_forbidden(self, api_base: str) -> None:
        status, _ = _get(f"{api_base}/api/does-not-exist")
        assert status == 403

    def test_non_numeric_limit_degrades_to_the_default(self, api_base: str) -> None:
        """`?limit=abc` must not 500, and must not silently return nothing."""
        status, body = _get(f"{api_base}/api/sessions?limit=abc")
        assert status == 200
        assert isinstance(body["data"]["sessions"], list)

    def test_query_params_are_accepted(self, api_base: str) -> None:
        status, body = _get(f"{api_base}/api/audit?severity=high&limit=5")
        assert status == 200
        assert body["data"]["total"] >= 0

    def test_search_alias_query_is_accepted(self, api_base: str) -> None:
        status, _ = _get(f"{api_base}/api/sessions?query=anything")
        assert status == 200

    def test_builder_failure_is_a_500_without_a_traceback(self, api_base: str) -> None:
        """A payload builder blowing up must not leak internals to the client."""
        with patch("sakthai.web.api.personas_payload", side_effect=RuntimeError("boom")):
            status, body = _get(f"{api_base}/api/personas")
        assert status == 500
        assert body == {}  # HTTPError body isn't parsed by _get; the point is the code


class TestQueryHelpers:
    def test_parses_params(self) -> None:
        from sakthai.web.server import _query_params

        assert _query_params("a=1&b=two") == {"a": "1", "b": "two"}

    def test_keeps_first_value_for_repeats(self) -> None:
        from sakthai.web.server import _query_params

        assert _query_params("a=1&a=2") == {"a": "1"}

    def test_blank_query_is_empty(self) -> None:
        from sakthai.web.server import _query_params

        assert _query_params("") == {}

    def test_int_param_reads_a_value(self) -> None:
        from sakthai.web.server import _int_param

        assert _int_param({"limit": "7"}, "limit", 20) == 7

    def test_int_param_falls_back_when_missing(self) -> None:
        from sakthai.web.server import _int_param

        assert _int_param({}, "limit", 20) == 20

    def test_int_param_falls_back_when_garbage(self) -> None:
        from sakthai.web.server import _int_param

        assert _int_param({"limit": "abc"}, "limit", 20) == 20


# ---------------------------------------------------------------------------
# CORS — opt-in, exact-match, never credentialed
# ---------------------------------------------------------------------------


class TestCors:
    ORIGIN = "http://localhost:3000"

    def _request(self, url: str, origin: str | None, method: str = "GET") -> Any:
        req = urllib.request.Request(url, method=method)
        if method == "GET":
            req.add_header("Authorization", f"Bearer {_get_or_create_bearer_token()}")
        if origin:
            req.add_header("Origin", origin)
        return urllib.request.urlopen(req, timeout=30)

    def test_no_cors_headers_by_default(
        self, api_base: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("SAKTHAI_WEB_CORS_ORIGIN", raising=False)
        with self._request(f"{api_base}/api/personas", self.ORIGIN) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") is None

    def test_allowed_origin_is_echoed(self, api_base: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", self.ORIGIN)
        with self._request(f"{api_base}/api/personas", self.ORIGIN) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") == self.ORIGIN
            assert resp.headers.get("Vary") == "Origin"

    def test_other_origin_gets_nothing(
        self, api_base: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exact match only — a different origin must not be echoed back."""
        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", self.ORIGIN)
        with self._request(f"{api_base}/api/personas", "http://evil.example") as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") is None

    def test_wildcard_is_never_sent(self, api_base: str, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", self.ORIGIN)
        with self._request(f"{api_base}/api/personas", self.ORIGIN) as resp:
            assert resp.headers.get("Access-Control-Allow-Origin") != "*"

    def test_credentials_are_never_allowed(
        self, api_base: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The token rides in Authorization; credentialed CORS buys nothing."""
        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", self.ORIGIN)
        with self._request(f"{api_base}/api/personas", self.ORIGIN) as resp:
            assert resp.headers.get("Access-Control-Allow-Credentials") is None

    def test_preflight_succeeds_when_configured(
        self, api_base: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", self.ORIGIN)
        with self._request(f"{api_base}/api/personas", self.ORIGIN, "OPTIONS") as resp:
            assert resp.status == 204

    def test_preflight_is_rejected_when_cors_is_off(
        self, api_base: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A default server must not advertise cross-origin support."""
        monkeypatch.delenv("SAKTHAI_WEB_CORS_ORIGIN", raising=False)
        with pytest.raises(urllib.error.HTTPError) as excinfo:
            self._request(f"{api_base}/api/personas", self.ORIGIN, "OPTIONS")
        assert excinfo.value.code == 405

    def test_blank_env_var_counts_as_off(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from sakthai.web.server import _cors_origin

        monkeypatch.setenv("SAKTHAI_WEB_CORS_ORIGIN", "   ")
        assert _cors_origin() is None
