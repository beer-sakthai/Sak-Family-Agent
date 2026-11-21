"""Unit tests for the 'sakthai gateway' Click CLI commands."""

from __future__ import annotations

from io import BytesIO
from typing import Any

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.server import RuntimeGatewayServer


@pytest.fixture
def test_server() -> RuntimeGatewayServer:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token="cli-test-token")
    server = RuntimeGatewayServer(config=cfg)
    server.start(background=True)
    yield server
    server.shutdown()


def test_cli_gateway_help() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["gateway", "--help"])
    assert result.exit_code == 0
    assert "Manage the OpenAI-compatible and REST API Runtime Gateway." in result.output
    assert "serve" in result.output
    assert "status" in result.output
    assert "models" in result.output
    assert "chat" in result.output


def test_cli_gateway_status(test_server: RuntimeGatewayServer) -> None:
    runner = CliRunner()
    url = f"http://127.0.0.1:{test_server.port}"

    # Formatted status
    res = runner.invoke(main, ["gateway", "status", "--url", url, "--token", "cli-test-token"])
    assert res.exit_code == 0
    assert "Gateway Status:    HEALTHY" in res.output

    # JSON status
    res_json = runner.invoke(
        main, ["gateway", "status", "--url", url, "--token", "cli-test-token", "--json"]
    )
    assert res_json.exit_code == 0
    assert '"status": "healthy"' in res_json.output


def test_cli_gateway_models(test_server: RuntimeGatewayServer) -> None:
    runner = CliRunner()
    url = f"http://127.0.0.1:{test_server.port}"

    # Formatted models
    res = runner.invoke(main, ["gateway", "models", "--url", url, "--token", "cli-test-token"])
    assert res.exit_code == 0
    assert "Models served by Gateway" in res.output
    assert "sakthai" in res.output

    # JSON models
    res_json = runner.invoke(
        main, ["gateway", "models", "--url", url, "--token", "cli-test-token", "--json"]
    )
    assert res_json.exit_code == 0
    assert '"object": "list"' in res_json.output


def test_cli_gateway_chat_non_streaming(test_server: RuntimeGatewayServer) -> None:
    runner = CliRunner()
    url = f"http://127.0.0.1:{test_server.port}"

    res = runner.invoke(
        main,
        [
            "gateway",
            "chat",
            "Hello Gateway!",
            "--url",
            url,
            "--model",
            "sakking",
            "--token",
            "cli-test-token",
        ],
    )
    assert res.exit_code == 0
    assert "SakKing" in res.output


def test_cli_gateway_chat_streaming(test_server: RuntimeGatewayServer) -> None:
    runner = CliRunner()
    url = f"http://127.0.0.1:{test_server.port}"

    res = runner.invoke(
        main,
        [
            "gateway",
            "chat",
            "Stream this message",
            "--url",
            url,
            "--model",
            "saksee",
            "--token",
            "cli-test-token",
            "--stream",
        ],
    )
    assert res.exit_code == 0
    assert "SakSee" in res.output


def test_cli_gateway_status_connection_error() -> None:
    runner = CliRunner()
    # Port 59999 should not have a server running
    res = runner.invoke(main, ["gateway", "status", "--url", "http://127.0.0.1:59999"])
    assert res.exit_code != 0
    assert "Failed to reach Gateway" in res.output


def test_cli_gateway_serve_lifecycle(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    called = False

    def mock_start(self: Any, background: bool = False) -> None:
        nonlocal called
        called = True
        raise KeyboardInterrupt()

    monkeypatch.setattr(RuntimeGatewayServer, "start", mock_start)

    res = runner.invoke(main, ["gateway", "serve", "--port", "8089", "--token", "abc"])
    assert res.exit_code == 0
    assert called
    assert "Launching SakThai Runtime Gateway" in res.output
    assert "Gateway stopped cleanly" in res.output


def test_cli_gateway_errors(
    test_server: RuntimeGatewayServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    runner = CliRunner()
    url = f"http://127.0.0.1:{test_server.port}"

    # Status bad status code
    from sakthai.cli import gateway as gw_mod

    monkeypatch.setattr(
        gw_mod, "_make_request", lambda *a, **kw: (500, {"error": "Server failure"})
    )
    res = runner.invoke(main, ["gateway", "status", "--url", url])
    assert res.exit_code != 0
    assert "Gateway returned status 500" in res.output

    # Models bad token
    res2 = runner.invoke(main, ["gateway", "models", "--url", url, "--token", "wrong-token"])
    assert res2.exit_code != 0

    # Chat bad token
    res3 = runner.invoke(main, ["gateway", "chat", "hi", "--url", url, "--token", "wrong-token"])
    assert res3.exit_code != 0

    # Chat streaming connection failure
    res4 = runner.invoke(
        main, ["gateway", "chat", "hi", "--url", "http://127.0.0.1:59999", "--stream"]
    )
    assert res4.exit_code != 0


def test_make_request_raw_text_and_http_error(test_server: RuntimeGatewayServer) -> None:
    from sakthai.cli.gateway import _make_request

    base = f"http://127.0.0.1:{test_server.port}"

    # Hit 404 endpoint -> HTTPError handled
    code, data = _make_request(f"{base}/nonexistent", token="cli-test-token")
    assert code == 404

    # Bad token -> HTTPError handled
    code2, data2 = _make_request(f"{base}/v1/models", token="invalid")
    assert code2 == 401


def test_cli_gateway_serve_open_access_logging(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()

    def mock_start(self: Any, background: bool = False) -> None:
        raise KeyboardInterrupt()

    monkeypatch.setattr(RuntimeGatewayServer, "start", mock_start)

    res = runner.invoke(main, ["gateway", "serve", "--port", "8091"])
    assert res.exit_code == 0
    assert "Authentication:  Disabled (Open Access)" in res.output


def test_cli_gateway_models_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    from sakthai.cli import gateway as gw_mod

    def failing_request(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Network down")

    monkeypatch.setattr(gw_mod, "_make_request", failing_request)
    res = runner.invoke(main, ["gateway", "models", "--url", "http://127.0.0.1:8080"])
    assert res.exit_code != 0
    assert "Error querying Gateway: Network down" in res.output


def test_cli_gateway_chat_empty_choices_and_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    from sakthai.cli import gateway as gw_mod

    # Return 200 with no choices list
    monkeypatch.setattr(gw_mod, "_make_request", lambda *a, **kw: (200, {"choices": []}))
    res = runner.invoke(main, ["gateway", "chat", "hi", "--url", "http://127.0.0.1:8080"])
    assert res.exit_code == 0
    assert '"choices": []' in res.output

    # Raise exception
    def failing_request(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("Chat timeout")

    monkeypatch.setattr(gw_mod, "_make_request", failing_request)
    res2 = runner.invoke(main, ["gateway", "chat", "hi", "--url", "http://127.0.0.1:8080"])
    assert res2.exit_code != 0
    assert "Error communicating with Gateway: Chat timeout" in res2.output


def test_cli_gateway_chat_streaming_chunk_handling(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = CliRunner()
    import urllib.request

    stream_content = [
        b"comment line\n",
        b"data: not-a-json\n",
        b'data: {"choices": []}\n',
        b'data: {"choices": [{"delta": {"content": "hello "}}]}\n',
        b'data: {"choices": [{"delta": {"content": "world"}}]}\n',
        b"data: [DONE]\n",
    ]

    class MockStreamResp:
        def __init__(self) -> None:
            self._lines = iter(stream_content)

        def __iter__(self) -> MockStreamResp:
            return self

        def __next__(self) -> bytes:
            return next(self._lines)

        def __enter__(self) -> MockStreamResp:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: MockStreamResp())

    res = runner.invoke(
        main,
        ["gateway", "chat", "hi", "--url", "http://127.0.0.1:8080", "--stream", "--token", "tok"],
    )
    assert res.exit_code == 0
    assert "hello world" in res.output


def test_make_request_decode_fallbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    import urllib.error
    import urllib.request

    from sakthai.cli.gateway import _make_request

    # 200 OK with non-JSON body
    class PlainTextResp:
        status = 200

        def read(self) -> bytes:
            return b"Plain text message"

        def __enter__(self) -> PlainTextResp:
            return self

        def __exit__(self, *args: Any) -> None:
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **kw: PlainTextResp())
    code, data = _make_request("http://127.0.0.1:8080")
    assert code == 200
    assert data == "Plain text message"

    # HTTPError with non-JSON body
    def raise_http_error(*a: Any, **kw: Any) -> Any:
        raise urllib.error.HTTPError(
            "http://127.0.0.1", 502, "Bad Gateway", {}, BytesIO(b"Bad Gateway HTML")
        )  # type: ignore[arg-type]

    monkeypatch.setattr(urllib.request, "urlopen", raise_http_error)
    code2, data2 = _make_request("http://127.0.0.1:8080")
    assert code2 == 502
    assert "Bad Gateway HTML" in str(data2)
