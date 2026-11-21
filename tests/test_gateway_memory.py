"""Unit tests for Gateway Phases 1-4: Memory, Voice/Duplex, Team Orchestration, and Benchmarks."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from sakthai.cli import main
from sakthai.client.gateway import GatewayClient
from sakthai.gateway.bench import GatewayTelemetryTracker, run_gateway_benchmark
from sakthai.gateway.config import GatewayConfig
from sakthai.gateway.memory import GatewayMemoryManager, _default_store_factory
from sakthai.gateway.router import GatewayRouter
from sakthai.gateway.server import RuntimeGatewayServer
from sakthai.gateway.voice import GatewayVoiceHandler
from sakthai.memory.store import MemoryStore
from sakthai.team.gateway import GatewayTeamOrchestrator

# ---------------------------------------------------------------------------
# Phase 1: Automated Memory & Episodic Context Middleware
# ---------------------------------------------------------------------------


def test_default_store_factory() -> None:
    with _default_store_factory("sakthai") as store:
        assert isinstance(store, MemoryStore)


def test_memory_manager_get_memory_context_and_record_turn(tmp_path: Any) -> None:
    db_path = tmp_path / "memory.db"

    def store_factory(persona: str = "sakthai") -> MemoryStore:
        return MemoryStore(db_path=db_path)

    mgr = GatewayMemoryManager(store_factory=store_factory)

    # Empty store returns empty context
    assert mgr.get_memory_context("sakthai", query="hello") == ""

    # Populate store with facts (keyed and keyless) and observations
    with store_factory("sakthai") as store:
        store.add_fact("Beer", key="user_name", kind="profile")
        store.add_fact("Keyless note", key=None, kind="note")
        store.add_observation("User loves automation and zero cost local models", weight=1.0)

    # Search matching query
    ctx = mgr.get_memory_context("sakthai", query="Beer", limit=5)
    assert "Persistent Memory Context for Sakthai" in ctx
    assert "user_name = Beer" in ctx

    # Search non-matching query falls back to recent facts/observations
    ctx_fallback = mgr.get_memory_context("sakthai", query="xyz_nonexistent_123", limit=5)
    assert "user_name = Beer" in ctx_fallback
    assert "Keyless note" in ctx_fallback
    assert "User loves automation" in ctx_fallback

    # Empty query also falls back cleanly
    ctx_empty_query = mgr.get_memory_context("sakthai", query="", limit=5)
    assert "user_name = Beer" in ctx_empty_query

    # Record turn
    assert mgr.record_turn("sakthai", "How is the CI?", "All 52 checks are green!") is True
    assert mgr.record_turn("sakthai", "   ", "response") is False
    assert mgr.record_turn("sakthai", "prompt", "") is False

    # Verify recorded turn appears in stats
    stats = mgr.get_memory_stats("sakthai", limit=10)
    assert stats["ok"] is True
    assert stats["persona"] == "sakthai"
    assert stats["facts_count"] == 2
    assert stats["observations_count"] == 2
    summaries = [o["summary"] for o in stats["observations"]]
    assert any("How is the CI?" in s for s in summaries)


def test_memory_manager_handles_exceptions_gracefully() -> None:
    def failing_factory(persona: str = "sakthai") -> Any:
        raise RuntimeError("Database locked")

    mgr = GatewayMemoryManager(store_factory=failing_factory)
    assert mgr.get_memory_context("sakthai", "test") == ""
    assert mgr.record_turn("sakthai", "hello", "world") is False
    stats = mgr.get_memory_stats("sakthai")
    assert stats["ok"] is False
    assert "Database locked" in stats["error"]


def test_router_chat_completion_memory_injection_and_recording(tmp_path: Any) -> None:
    db_path = tmp_path / "router_mem.db"

    def store_factory(persona: str = "sakjules") -> MemoryStore:
        return MemoryStore(db_path=db_path)

    with store_factory("sakjules") as store:
        store.add_fact("Manual merge only by Beer", key="ci_policy", kind="rule")

    mgr = GatewayMemoryManager(store_factory=store_factory)
    captured_messages: list[dict[str, Any]] = []

    def custom_executor(**kwargs: Any) -> str:
        captured_messages.extend(kwargs["messages"])
        return "Understood, following CI policy."

    router = GatewayRouter(
        config=GatewayConfig(default_persona="sakjules"),
        chat_executor=custom_executor,
        memory_manager=mgr,
    )

    # 1. With existing system message
    body = {
        "model": "sakjules",
        "messages": [
            {"role": "system", "content": "You are SakJules."},
            {"role": "user", "content": "What is our ci_policy?"},
        ],
    }
    res, is_stream = router.handle_chat_completion(body)
    assert is_stream is False
    assert isinstance(res, dict)
    assert len(captured_messages) == 2
    assert "Manual merge only by Beer" in captured_messages[0]["content"]

    # Check turn was recorded
    stats = router.handle_persona_memory("sakjules")
    assert stats["ok"] is True
    assert stats["observations_count"] == 1

    # 2. Without existing system message (inserts new system message at index 0)
    captured_messages.clear()
    body2 = {
        "model": "sakjules",
        "messages": [
            {"role": "user", "content": "Check ci_policy"},
        ],
    }
    router.handle_chat_completion(body2)
    assert len(captured_messages) == 2
    assert captured_messages[0]["role"] == "system"
    assert "Manual merge only by Beer" in captured_messages[0]["content"]

    # 3. With x-sakthai-disable-memory header
    captured_messages.clear()
    router.handle_chat_completion(
        body2,
        headers={"x-sakthai-disable-memory": "true", "x-sakthai-memory-limit": "invalid"},
    )
    assert len(captured_messages) == 1
    assert captured_messages[0]["role"] == "user"

    # 4. Streaming completion records turn on finish
    body_stream = {
        "model": "sakjules",
        "stream": True,
        "messages": [{"role": "user", "content": "Stream test query"}],
    }
    gen, is_stream = router.handle_chat_completion(body_stream)
    assert is_stream is True
    chunks = list(gen)
    assert any("[DONE]" in c for c in chunks)
    stats_after = router.handle_persona_memory("sakjules")
    assert stats_after["observations_count"] >= 2


def test_router_handle_persona_memory_unknown_persona() -> None:
    router = GatewayRouter()
    res = router.handle_persona_memory("unknown_agent")
    assert res["ok"] is False
    assert "Unknown persona" in res["error"]


def test_router_stream_sse_on_done_exception_logged() -> None:
    router = GatewayRouter()

    def bad_callback(text: str) -> None:
        raise ValueError("Callback failure")

    def token_gen() -> Any:
        yield "Hello"

    chunks = list(router._stream_sse("id-1", 123, "sakthai", token_gen(), on_done=bad_callback))
    assert any("[DONE]" in c for c in chunks)


# ---------------------------------------------------------------------------
# Phase 2: Real-Time WebSocket Duplex Streaming & Voice Audio Mode
# ---------------------------------------------------------------------------


def test_voice_handler_profiles_and_duplex_events() -> None:
    router = GatewayRouter()
    vh = GatewayVoiceHandler(router=router)

    profiles = vh.list_voice_profiles()
    assert profiles["count"] == 6
    assert "sakjules" in profiles["profiles"]

    p_jules = vh.get_voice_profile("SAKJULES")
    assert p_jules["voice_id"] == "sakjules-ci-precision"

    p_fallback = vh.get_voice_profile("unknown")
    assert p_fallback["persona"] == "sakthai"

    # 1. ping event
    frames_ping = list(vh.handle_duplex_event({"type": "ping", "session_id": "s1"}))
    assert len(frames_ping) == 1
    assert frames_ping[0]["type"] == "pong"
    assert frames_ping[0]["session_id"] == "s1"

    # 2. voice_config event
    frames_cfg = list(vh.handle_duplex_event({"type": "voice_config", "persona": "saksit"}))
    assert len(frames_cfg) == 1
    assert frames_cfg[0]["type"] == "voice_profile"
    assert frames_cfg[0]["persona"] == "saksit"

    # 3. audio_chunk without transcript
    frames_audio_only = list(
        vh.handle_duplex_event({"type": "audio_chunk", "data": "AAAA", "persona": "sakking"})
    )
    assert len(frames_audio_only) == 1
    assert frames_audio_only[0]["type"] == "audio_ack"
    assert frames_audio_only[0]["bytes_received"] == 4

    # 4. audio_chunk with transcript -> triggers full response
    frames_audio_tx = list(
        vh.handle_duplex_event(
            {
                "type": "audio_chunk",
                "data": "BBBB",
                "transcript": "Hello voice",
                "persona": "saksee",
            }
        )
    )
    types = [f["type"] for f in frames_audio_tx]
    assert "audio_ack" in types
    assert "start" in types
    assert "delta" in types
    assert "done" in types

    # 5. message event with unknown persona falls back to default_persona
    frames_msg = router.handle_duplex_event(
        {"type": "message", "content": "Hello duplex", "persona": "invalid_persona"}
    )
    assert frames_msg[0]["type"] == "start"
    assert frames_msg[-1]["type"] == "done"
    assert "Hello duplex" in frames_msg[-1]["content"]

    # 6. message event with empty content -> error frame
    frames_err = list(vh.handle_duplex_event({"type": "message", "content": "   "}))
    assert len(frames_err) == 1
    assert frames_err[0]["type"] == "error"

    # 7. router.handle_voice_profiles
    assert router.handle_voice_profiles()["count"] == 6


def test_voice_handler_ignores_malformed_sse_lines() -> None:
    router = MagicMock()
    router.config.default_persona = "sakthai"

    def custom_sse() -> Any:
        yield "comment line without data prefix"
        yield "data: {invalid json"
        yield 'data: {"choices": [{"delta": {"content": "Hi"}}]}'
        yield "data: [DONE]"

    router.handle_chat_completion.return_value = (custom_sse(), True)
    vh = GatewayVoiceHandler(router=router)
    frames = list(vh.handle_duplex_event({"type": "message", "content": "test"}))
    deltas = [f["content"] for f in frames if f["type"] == "delta"]
    assert deltas == ["Hi"]


# ---------------------------------------------------------------------------
# Phase 3: Distributed Multi-Agent Team Orchestration via Gateway
# ---------------------------------------------------------------------------


def test_team_orchestrator_list_and_execute_local() -> None:
    router = GatewayRouter()
    orch = GatewayTeamOrchestrator(router=router)

    catalog = orch.list_pipelines()
    assert catalog["count"] == 5
    names = {p["name"] for p in catalog["pipelines"]}
    assert "feature-delivery" in names
    assert "daily-sync" in names

    # Invalid pipeline
    err_unknown = orch.execute_pipeline("nonexistent-pipeline", "Do something")
    assert err_unknown["ok"] is False
    assert "Unknown pipeline" in err_unknown["error"]

    # Empty task
    err_task = orch.execute_pipeline("daily-sync", "   ")
    assert err_task["ok"] is False
    assert "Field 'task' is required" in err_task["error"]

    # Local execution of daily-sync (1 step) and code-review (3 steps)
    res_sync = orch.execute_pipeline("daily-sync", "Check family shards")
    assert res_sync["ok"] is True
    assert res_sync["status"] == "completed"
    assert res_sync["steps_completed"] == 1
    assert res_sync["steps"][0]["dispatch_mode"] == "local-gateway"

    res_review = router.handle_team_run({"pipeline": "code-review", "task": "Review PR #2016"})
    assert res_review["ok"] is True
    assert res_review["steps_completed"] == 3
    assert router.handle_team_pipelines()["count"] == 5


def test_team_orchestrator_remote_client_and_error_handling() -> None:
    mock_client = MagicMock()
    mock_client.base_url = "http://remote-node:8080"
    mock_client.chat_completions.return_value = {
        "choices": [{"message": {"content": "Remote step output"}}]
    }

    orch = GatewayTeamOrchestrator(client=mock_client)
    res = orch.execute_pipeline("daily-sync", "Remote sync task")
    assert res["ok"] is True
    assert res["steps"][0]["dispatch_mode"] == "remote:http://remote-node:8080"
    assert res["final_output"] == "Remote step output"

    # Test step failure handling
    mock_client.chat_completions.side_effect = RuntimeError("Remote gateway unreachable")
    res_fail = orch.execute_pipeline("daily-sync", "Failing task")
    assert res_fail["ok"] is False
    assert res_fail["status"] == "failed"
    assert res_fail["failed_step"] == "sync"
    assert "Remote gateway unreachable" in res_fail["steps"][0]["error"]


def test_team_orchestrator_missing_template_key_and_gateway_url_instantiation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from sakthai.team.models import PipelineDefinition, PipelineStep

    # Test missing key fallback in prompt template
    bad_step = PipelineStep(
        name="broken_tpl",
        persona="sakthai",
        prompt_template="Missing key {nonexistent_placeholder}",
        output_key="out",
    )
    custom_pipe = PipelineDefinition(
        name="custom-broken",
        description="Test missing key",
        steps=(bad_step,),
    )
    monkeypatch.setitem(
        __import__("sakthai.team.gateway", fromlist=["BUILTIN_PIPELINES"]).BUILTIN_PIPELINES,
        "custom-broken",
        custom_pipe,
    )

    # Also test non-dict return from router
    mock_router = MagicMock()
    mock_router.handle_chat_completion.return_value = ("Plain string fallback", False)

    orch = GatewayTeamOrchestrator(router=mock_router)
    res = orch.execute_pipeline("custom-broken", "My task")
    assert res["ok"] is True
    assert res["final_output"] == "Plain string fallback"


# ---------------------------------------------------------------------------
# Phase 4: High-Concurrency Benchmarks & Telemetry Tracker
# ---------------------------------------------------------------------------


def test_telemetry_tracker_and_benchmark_runner() -> None:
    tracker = GatewayTelemetryTracker(max_samples=100)
    snap_empty = tracker.snapshot()
    assert snap_empty["total_requests"] == 0
    assert snap_empty["latency_ms"]["p50"] == 0.0

    tracker.record_request(12.5, ttft_ms=4.2, tokens=25)
    tracker.record_request(25.0, ttft_ms=8.1, tokens=50, error=True, blocked=True)
    snap = tracker.snapshot()
    assert snap["total_requests"] == 2
    assert snap["total_tokens"] == 75
    assert snap["total_errors"] == 1
    assert snap["guardrail_blocks"] == 1
    assert snap["latency_ms"]["p50"] > 0
    assert snap["ttft_ms"]["p50"] > 0

    # Streaming benchmark
    router = GatewayRouter()
    res_stream = run_gateway_benchmark(
        router=router, concurrency=4, num_requests=8, persona="sakjules", stream=True
    )
    assert res_stream["ok"] is True
    assert res_stream["requests"] == 8
    assert res_stream["concurrency"] == 4
    assert res_stream["total_tokens"] >= 8
    assert res_stream["latency_ms"]["p95"] > 0

    # Non-streaming benchmark via router.handle_benchmark
    res_nostream = router.handle_benchmark(
        {"concurrency": 2, "requests": 4, "persona": "sakking", "stream": False}
    )
    assert res_nostream["ok"] is True
    assert res_nostream["stream"] is False
    assert res_nostream["requests"] == 4

    # Failing benchmark worker
    bad_router = MagicMock()
    bad_router.handle_chat_completion.side_effect = RuntimeError("Worker crash")
    res_err = run_gateway_benchmark(router=bad_router, concurrency=2, num_requests=3)
    assert res_err["ok"] is False
    assert res_err["errors"] == 3


def test_cli_gateway_bench_command() -> None:
    runner = CliRunner()
    res_text = runner.invoke(main, ["gateway", "bench", "-c", "2", "-n", "4", "-p", "sakjules"])
    assert res_text.exit_code == 0
    assert "SakThai Gateway Benchmark" in res_text.output
    assert "Throughput" in res_text.output

    res_json = runner.invoke(
        main, ["gateway", "bench", "-c", "2", "-n", "4", "--no-stream", "--json"]
    )
    assert res_json.exit_code == 0
    assert '"requests": 4' in res_json.output


# ---------------------------------------------------------------------------
# End-to-End Live HTTP Server & GatewayClient SDK Verification
# ---------------------------------------------------------------------------


def test_server_and_client_new_endpoints_e2e() -> None:
    cfg = GatewayConfig(host="127.0.0.1", port=0, bearer_token="test-e2e-token")
    server = RuntimeGatewayServer(config=cfg)
    server.start()
    try:
        base_url = f"http://127.0.0.1:{server.port}"
        with GatewayClient(base_url=base_url, api_token="test-e2e-token") as client:
            # 1. Persona memory endpoint
            mem = client.get_persona_memory("sakjules")
            assert mem["ok"] is True
            assert mem["persona"] == "sakjules"

            # 2. Voice profiles endpoint
            voices = client.list_voice_profiles()
            assert voices["count"] == 6

            # 3. Duplex WebSocket endpoint
            ws_res = client.send_duplex_event(
                {"type": "message", "content": "Live duplex test", "persona": "sakjules"}
            )
            assert ws_res["ok"] is True
            assert any(f["type"] == "done" for f in ws_res["frames"])

            # 4. Team pipelines GET & POST
            pipes = client.list_team_pipelines()
            assert pipes["count"] == 5

            run_res = client.run_team_pipeline(
                "daily-sync", "Verify live server pipeline", gateway_url=None
            )
            assert run_res["ok"] is True
            assert run_res["status"] == "completed"

            # Also test remote gateway_url parameter on run_team_pipeline
            run_remote = client.run_team_pipeline(
                "daily-sync", "Verify remote url pass-through", gateway_url=base_url
            )
            assert "ok" in run_remote

            # 5. Benchmark endpoint
            bench_res = client.run_benchmark(concurrency=2, requests=4, persona="sakjules")
            assert bench_res["ok"] is True
            assert bench_res["requests"] == 4
    finally:
        server.shutdown()
