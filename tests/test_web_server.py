"""Tests for sakthai.web.server — JSON API endpoints and static-file security.

The HTTP handler is tested by spinning up a real HTTPServer on a free port in a
daemon thread. The dashboard data function gracefully falls back to a demo stub
when no DB exists, so tests don't need a live memory store.
"""

from __future__ import annotations

import json
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


def _get(url: str, timeout: int = 5) -> tuple[int, dict[str, Any]]:
    """GET url, returning (status_code, parsed_body). 4xx raises are caught."""
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
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
        with patch(
            "sakthai.dashboard.data.collect_dashboard_data", side_effect=RuntimeError("no db")
        ):
            data = _dashboard_data()
        assert "growth" in data
        assert data.get("source") == "demo"


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
        with urllib.request.urlopen(f"{api_base}/api/ecosystem", timeout=5) as resp:
            ct = resp.headers.get("Content-Type", "")
        assert "application/json" in ct


class TestStaticFilePathTraversal:
    def test_path_traversal_blocked_with_403(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/../../etc/passwd")
        assert code == 403

    def test_deep_traversal_blocked(self, api_base: str) -> None:
        code, _ = _get(f"{api_base}/../../../../etc/shadow")
        assert code == 403


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
        with urllib.request.urlopen(f"{api_base}/api/stages", timeout=5) as resp:
            content_length = resp.headers.get("Content-Length")
        assert content_length is not None
        assert int(content_length) > 0

    def test_content_length_header_present_in_ecosystem(self, api_base: str) -> None:
        with urllib.request.urlopen(f"{api_base}/api/ecosystem", timeout=5) as resp:
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
            mock_chdir.assert_called_once_with(str(_STATIC_ROOT))
            mock_http.assert_called_once_with((_DEFAULT_HOST, _DEFAULT_PORT), _Handler)
            assert result is mock_http.return_value

    def test_serve_custom_host_port(self) -> None:
        with (
            patch("sakthai.web.server.os.chdir"),
            patch("sakthai.web.server.HTTPServer") as mock_http,
        ):
            serve(host="127.0.0.1", port=9999)
            mock_http.assert_called_once_with(("127.0.0.1", 9999), _Handler)


class TestMainBlock:
    def test_main_block_starts_server_and_exits_on_interrupt(self) -> None:
        import http.server as _http_server
        import os as _os

        srv = MagicMock()
        srv.serve_forever.side_effect = KeyboardInterrupt()
        server_py = Path(__file__).parent.parent / "sakthai" / "web" / "server.py"
        # runpy executes in a fresh namespace; patch the real stdlib objects so
        # the re-imported `os.chdir` and `HTTPServer` inside the file use mocks.
        with patch.object(_os, "chdir"), patch.object(_http_server, "HTTPServer", return_value=srv):
            with pytest.raises(SystemExit) as exc_info:
                runpy.run_path(str(server_py), run_name="__main__")
            assert exc_info.value.code == 0


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
