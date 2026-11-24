"""Branch coverage for `GatewayTeamOrchestrator` in `sakthai.team.gateway`.

`tests/test_gateway_team_stream.py` and `tests/test_gateway_memory.py` drive the
happy paths through a real `GatewayRouter`. These tests cover what they leave
out: the remote-client token stream, a `gateway_url`-built client, prompt
templates that reference a missing key, the SSE parser's tolerance of bad
chunks, non-dict router results, and step failure mid-stream. Every remote call
goes through an `httpx.MockTransport`, so nothing leaves the process.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest

import sakthai.team.gateway as team_gateway
from sakthai.client.gateway import GatewayClient
from sakthai.gateway.router import GatewayRouter
from sakthai.team.gateway import GatewayTeamOrchestrator
from sakthai.team.models import PipelineDefinition, PipelineStep


def _completion(content: str) -> dict[str, Any]:
    return {"choices": [{"message": {"role": "assistant", "content": content}}]}


def _sse(content: str) -> str:
    return "data: " + json.dumps({"choices": [{"delta": {"content": content}}]}) + "\n\n"


def _mock_client(
    base_url: str,
    handler: Callable[[httpx.Request], httpx.Response],
    api_token: str | None = None,
) -> GatewayClient:
    """A real `GatewayClient` whose HTTP layer is an in-process mock transport."""
    http = httpx.Client(transport=httpx.MockTransport(handler), base_url=base_url)
    client = GatewayClient(base_url=base_url, api_token=api_token, httpx_client=http)
    # An injected httpx client does not inherit GatewayClient's headers; mirror
    # them so the handler sees exactly what the real client would send.
    http.headers.update(client.headers)
    return client


def _router_returning(*results: Any) -> MagicMock:
    router = MagicMock(spec=GatewayRouter)
    router.handle_chat_completion.side_effect = list(results)
    return router


def _events_of(events: list[dict[str, Any]], kind: str) -> list[dict[str, Any]]:
    return [e for e in events if e["event"] == kind]


@pytest.fixture
def missing_key_pipeline(monkeypatch: pytest.MonkeyPatch) -> str:
    """Register a one-step pipeline whose template names a key the context lacks."""
    name = "missing-key-test"
    pipeline = PipelineDefinition(
        name=name,
        description="Template references an undefined placeholder",
        steps=(
            PipelineStep(
                name="only",
                persona="sakthai",
                prompt_template="Summarise {undefined_key} please",
                output_key="summary",
            ),
        ),
    )
    monkeypatch.setitem(team_gateway.BUILTIN_PIPELINES, name, pipeline)
    return name


# ---------------------------------------------------------------------------
# stream_pipeline: remote dispatch
# ---------------------------------------------------------------------------


def test_stream_remote_client_emits_word_tokens() -> None:
    seen: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(json.loads(request.content))
        return httpx.Response(200, json=_completion("alpha beta gamma"))

    client = _mock_client("http://remote.test", handler)
    orch = GatewayTeamOrchestrator(client=client)

    events = list(orch.stream_pipeline("daily-sync", "  Check the shards  "))

    assert [e["event"] for e in events] == [
        "pipeline_start",
        "step_start",
        "step_token",
        "step_token",
        "step_token",
        "step_complete",
        "pipeline_complete",
    ]
    assert [e["token"] for e in _events_of(events, "step_token")] == ["alpha ", "beta ", "gamma"]
    assert events[0]["task"] == "Check the shards"

    complete = _events_of(events, "step_complete")[0]
    assert complete["output"] == "alpha beta gamma"

    final = events[-1]
    assert final["ok"] is True
    assert final["status"] == "completed"
    assert final["steps"][0]["dispatch_mode"] == "remote:http://remote.test"
    assert final["final_output"] == "alpha beta gamma"

    assert len(seen) == 1
    assert seen[0]["model"] == "sakthai"
    assert "Check the shards" in seen[0]["messages"][0]["content"]


def test_stream_gateway_url_builds_a_remote_client(monkeypatch: pytest.MonkeyPatch) -> None:
    auth_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        auth_headers.append(request.headers.get("authorization"))
        return httpx.Response(200, json=_completion("remote ok"))

    built: list[tuple[str | None, str | None]] = []

    def factory(base_url: str | None = None, api_token: str | None = None) -> GatewayClient:
        built.append((base_url, api_token))
        assert base_url is not None
        return _mock_client(base_url, handler, api_token=api_token)

    monkeypatch.setattr(team_gateway, "GatewayClient", factory)
    router = _router_returning()  # must never be consulted
    orch = GatewayTeamOrchestrator(router=router)

    events = list(
        orch.stream_pipeline(
            "daily-sync", "Sync", gateway_url="http://gw.test:9000", api_token="tok-123"
        )
    )

    assert built == [("http://gw.test:9000", "tok-123")]
    assert auth_headers == ["Bearer tok-123"]
    router.handle_chat_completion.assert_not_called()
    final = events[-1]
    assert final["ok"] is True
    assert final["steps"][0]["dispatch_mode"] == "remote:http://gw.test:9000"
    assert final["final_output"] == "remote ok"


def test_stream_explicit_client_wins_over_gateway_url(monkeypatch: pytest.MonkeyPatch) -> None:
    def factory(*args: Any, **kwargs: Any) -> GatewayClient:
        raise AssertionError("GatewayClient must not be built when a client is injected")

    monkeypatch.setattr(team_gateway, "GatewayClient", factory)
    client = _mock_client(
        "http://injected.test", lambda request: httpx.Response(200, json=_completion("hi"))
    )
    orch = GatewayTeamOrchestrator(client=client)

    events = list(orch.stream_pipeline("daily-sync", "Sync", gateway_url="http://ignored.test"))

    assert events[-1]["steps"][0]["dispatch_mode"] == "remote:http://injected.test"


def test_stream_remote_error_fails_the_step() -> None:
    client = _mock_client(
        "http://down.test", lambda request: httpx.Response(503, text="service unavailable")
    )
    orch = GatewayTeamOrchestrator(client=client)

    events = list(orch.stream_pipeline("code-review", "Review PR"))

    assert [e["event"] for e in events] == [
        "pipeline_start",
        "step_start",
        "step_failed",
        "pipeline_complete",
    ]
    failed = events[2]
    assert failed["step_name"] == "scope"
    assert "Gateway error 503" in failed["error"]
    final = events[-1]
    assert final["ok"] is False
    assert final["status"] == "failed"
    assert final["failed_step"] == "scope"
    assert final["steps_completed"] == 0
    assert "Gateway error 503" in final["error"]


# ---------------------------------------------------------------------------
# stream_pipeline: local router dispatch
# ---------------------------------------------------------------------------


def test_stream_sse_parser_skips_malformed_chunks() -> None:
    def chunks() -> Iterator[str]:
        yield _sse("Hel")
        yield "event: progress\n"  # not a data line
        yield "data: {not json}\n\n"  # JSONDecodeError
        yield 'data: {"choices": []}\n\n'  # IndexError
        yield 'data: {"choices": null}\n\n'  # TypeError
        yield _sse("")  # empty content is not a token
        yield _sse("lo") + _sse(" world")  # two events in one chunk
        yield "data: [DONE]\n\n"

    router = _router_returning((chunks(), True))
    orch = GatewayTeamOrchestrator(router=router)

    events = list(orch.stream_pipeline("daily-sync", "Sync"))

    assert [e["token"] for e in _events_of(events, "step_token")] == ["Hel", "lo", " world"]
    complete = _events_of(events, "step_complete")[0]
    assert complete["output"] == "Hello world"
    final = events[-1]
    assert final["ok"] is True
    assert final["steps"][0]["dispatch_mode"] == "local-gateway"
    sent = router.handle_chat_completion.call_args.args[0]
    assert sent["stream"] is True
    assert sent["model"] == "sakthai"


@pytest.mark.parametrize(
    ("result", "expected"),
    [
        ((_completion("dict output"), False), "dict output"),
        (("plain text reply", False), "plain text reply"),
        ((12345, True), "12345"),
    ],
    ids=["dict", "string", "stream-flag-but-not-iterable"],
)
def test_stream_non_streaming_router_results(result: tuple[Any, bool], expected: str) -> None:
    router = _router_returning(result)
    orch = GatewayTeamOrchestrator(router=router)

    events = list(orch.stream_pipeline("daily-sync", "Sync"))

    assert _events_of(events, "step_token") == []
    assert _events_of(events, "step_complete")[0]["output"] == expected
    assert events[-1]["final_output"] == expected


def test_stream_failure_after_a_completed_step() -> None:
    router = _router_returning(
        (_completion("scope done"), False),
        RuntimeError("router exploded"),
    )
    orch = GatewayTeamOrchestrator(router=router)

    events = list(orch.stream_pipeline("code-review", "Review PR 7"))

    kinds = [e["event"] for e in events]
    assert kinds == [
        "pipeline_start",
        "step_start",
        "step_complete",
        "step_start",
        "step_failed",
        "pipeline_complete",
    ]
    # The second step's prompt was built from the first step's output.
    assert "scope done" in events[3]["input_prompt"]
    failed = events[4]
    assert failed["step_index"] == 1
    assert failed["step_name"] == "review"
    assert failed["error"] == "router exploded"
    final = events[-1]
    assert final["ok"] is False
    assert final["failed_step"] == "review"
    assert final["steps_completed"] == 1
    assert final["error"] == "router exploded"
    assert router.handle_chat_completion.call_count == 2


def test_stream_template_with_missing_key_falls_back(missing_key_pipeline: str) -> None:
    router = _router_returning((_completion("fallback ok"), False))
    orch = GatewayTeamOrchestrator(router=router)

    events = list(orch.stream_pipeline(missing_key_pipeline, "the real task"))

    step_start = _events_of(events, "step_start")[0]
    assert step_start["input_prompt"] == "Summarise {undefined_key} please\n\nTask: the real task"
    sent = router.handle_chat_completion.call_args.args[0]
    assert sent["messages"][0]["content"] == step_start["input_prompt"]
    assert events[-1]["ok"] is True
    assert events[-1]["final_output"] == "fallback ok"


# ---------------------------------------------------------------------------
# execute_pipeline: the same seams, non-streaming
# ---------------------------------------------------------------------------


def test_execute_template_with_missing_key_falls_back(missing_key_pipeline: str) -> None:
    router = _router_returning((_completion("exec ok"), False))
    orch = GatewayTeamOrchestrator(router=router)

    res = orch.execute_pipeline(missing_key_pipeline, "exec task")

    sent = router.handle_chat_completion.call_args.args[0]
    assert sent["stream"] is False
    assert sent["messages"][0]["content"] == "Summarise {undefined_key} please\n\nTask: exec task"
    assert res["ok"] is True
    assert res["final_output"] == "exec ok"


def test_execute_non_dict_router_result_is_stringified() -> None:
    router = _router_returning(("raw string result", False))
    orch = GatewayTeamOrchestrator(router=router)

    res = orch.execute_pipeline("daily-sync", "Sync")

    assert res["ok"] is True
    assert res["steps"][0]["dispatch_mode"] == "local-gateway"
    assert res["final_output"] == "raw string result"


def test_execute_gateway_url_builds_a_remote_client(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers.get("authorization") == "Bearer exec-token"
        return httpx.Response(200, json=_completion("exec remote"))

    def factory(base_url: str | None = None, api_token: str | None = None) -> GatewayClient:
        assert base_url is not None
        return _mock_client(base_url, handler, api_token=api_token)

    monkeypatch.setattr(team_gateway, "GatewayClient", factory)
    orch = GatewayTeamOrchestrator(router=_router_returning())

    res = orch.execute_pipeline(
        "daily-sync", "Sync", gateway_url="http://exec.test", api_token="exec-token"
    )

    assert res["ok"] is True
    assert res["steps"][0]["dispatch_mode"] == "remote:http://exec.test"
    assert res["final_output"] == "exec remote"
