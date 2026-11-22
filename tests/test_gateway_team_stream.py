"""Unit and integration tests for Gateway team pipeline streaming."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any

import pytest

from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.router import GatewayRouter
from sakthai.gateway.server import RuntimeGatewayServer
from sakthai.team.gateway import GatewayTeamOrchestrator


def _http_request(
    url: str,
    method: str = "GET",
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> tuple[int, dict[str, Any] | str, dict[str, str]]:
    req_headers = {"Content-Type": "application/json"}
    if headers:
        req_headers.update(headers)
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:  # nosec B310
            resp_headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(raw), resp_headers
            except json.JSONDecodeError:
                return resp.status, raw, resp_headers
    except urllib.error.HTTPError as err:
        resp_headers = {k.lower(): v for k, v in err.headers.items()}
        raw = err.read().decode("utf-8")
        try:
            return err.code, json.loads(raw), resp_headers
        except Exception:
            return err.code, raw, resp_headers


def test_stream_pipeline_unknown_pipeline() -> None:
    orchestrator = GatewayTeamOrchestrator()
    events = list(orchestrator.stream_pipeline("nonexistent-pipeline", "Some task"))
    assert len(events) == 1
    assert events[0]["event"] == "pipeline_error"
    assert events[0]["ok"] is False
    assert "Unknown pipeline" in events[0]["error"]


def test_stream_pipeline_empty_task() -> None:
    orchestrator = GatewayTeamOrchestrator()
    events = list(orchestrator.stream_pipeline("code-review", "   "))
    assert len(events) == 1
    assert events[0]["event"] == "pipeline_error"
    assert events[0]["ok"] is False
    assert "non-empty string" in events[0]["error"]


def test_stream_pipeline_lifecycle() -> None:
    router = GatewayRouter()
    orchestrator = GatewayTeamOrchestrator(router=router)
    events = list(orchestrator.stream_pipeline("code-review", "Refactor user authentication"))

    event_types = [e["event"] for e in events]
    assert "pipeline_start" in event_types
    assert "step_start" in event_types
    assert "step_token" in event_types
    assert "step_complete" in event_types
    assert "pipeline_complete" in event_types

    # First event is pipeline_start
    start_event = events[0]
    assert start_event["event"] == "pipeline_start"
    assert start_event["pipeline"] == "code-review"
    assert start_event["total_steps"] == 3
    assert len(start_event["steps"]) == 3

    # Last event is pipeline_complete
    final_event = events[-1]
    assert final_event["event"] == "pipeline_complete"
    assert final_event["ok"] is True
    assert final_event["status"] == "completed"
    assert final_event["steps_completed"] == 3
    assert len(final_event["final_output"]) > 0


def test_router_handle_team_stream() -> None:
    router = GatewayRouter()
    chunks = list(router.handle_team_stream({"pipeline": "code-review", "task": "Review PR 101"}))
    assert len(chunks) >= 4
    # Check SSE format
    for chunk in chunks[:-1]:
        assert chunk.startswith("event: ")
        assert "\ndata: {" in chunk

    # Last chunk is [DONE]
    assert chunks[-1] == "event: done\ndata: [DONE]\n\n"


@pytest.fixture
def stream_server() -> RuntimeGatewayServer:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token="stream-secret-token")
    server = RuntimeGatewayServer(config=cfg)
    server.start(background=True)
    yield server
    server.shutdown()


def test_server_stream_pipeline_get(stream_server: RuntimeGatewayServer) -> None:
    port = stream_server.port
    url = (
        f"http://127.0.0.1:{port}/v1/team/pipelines/stream"
        "?pipeline=code-review&task=TestTask&token=stream-secret-token"
    )
    status, raw_resp, headers = _http_request(url, method="GET")
    assert status == 200
    assert "text/event-stream" in headers.get("content-type", "")
    assert isinstance(raw_resp, str)
    assert "event: pipeline_start" in raw_resp
    assert "event: pipeline_complete" in raw_resp
    assert "data: [DONE]" in raw_resp


def test_server_stream_pipeline_post(stream_server: RuntimeGatewayServer) -> None:
    port = stream_server.port
    url = f"http://127.0.0.1:{port}/v1/team/pipelines/stream"
    headers = {"Authorization": "Bearer stream-secret-token"}
    body = {"pipeline": "code-review", "task": "TestTask via POST"}
    status, raw_resp, resp_headers = _http_request(url, method="POST", body=body, headers=headers)
    assert status == 200
    assert "text/event-stream" in resp_headers.get("content-type", "")
    assert isinstance(raw_resp, str)
    assert "event: pipeline_start" in raw_resp
    assert "event: pipeline_complete" in raw_resp
