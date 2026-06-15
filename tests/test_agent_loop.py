"""Tests for the agent loop using a fake client (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from sakthai.agent.loop import AgentError, _detect_provider, _extract_text, run_agent
from sakthai.memory.store import MemoryStore


class _Block:
    def __init__(self, **kwargs: object) -> None:
        self.type = ""
        self.text = ""
        self.id = ""
        self.name = ""
        self.input: dict = {}
        for key, value in kwargs.items():
            setattr(self, key, value)


class _Resp:
    def __init__(self, stop_reason: str, content: list) -> None:
        self.stop_reason = stop_reason
        self.content = content


class _Messages:
    def __init__(self, responses: list) -> None:
        self._responses = responses
        self.calls = 0

    def create(self, **kwargs: object) -> _Resp:
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


class FakeClient:
    def __init__(self, responses: list) -> None:
        self.messages = _Messages(responses)


def test_simple_text_response(store: MemoryStore) -> None:
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="hello")])])
    result = run_agent("hi", client=client, store=store, provider="anthropic")
    assert result.text == "hello"
    assert result.iterations == 1
    assert result.stop_reason == "end_turn"


def test_tool_use_then_finish(store: MemoryStore) -> None:
    client = FakeClient(
        [
            _Resp(
                "tool_use",
                [
                    _Block(
                        type="tool_use",
                        id="t1",
                        name="learn",
                        input={"value": "uses vim", "kind": "pref"},
                    )
                ],
            ),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    result = run_agent("remember", client=client, store=store, provider="anthropic")
    assert result.text == "done"
    assert result.iterations == 2
    assert [c["name"] for c in result.tool_calls] == ["learn"]
    assert store.list_facts()[0].value == "uses vim"


def test_unknown_tool_is_reported(store: MemoryStore) -> None:
    client = FakeClient(
        [
            _Resp("tool_use", [_Block(type="tool_use", id="t1", name="ghost", input={})]),
            _Resp("end_turn", [_Block(type="text", text="ok")]),
        ]
    )
    events: list = []
    result = run_agent(
        "x",
        client=client,
        store=store,
        provider="anthropic",
        on_event=lambda k, p: events.append((k, p)),
    )
    assert result.text == "ok"
    assert any(k == "tool_error" for k, _ in events)


def test_empty_task_raises(store: MemoryStore) -> None:
    with pytest.raises(AgentError):
        run_agent("   ", client=FakeClient([]), store=store, provider="anthropic")


def test_iteration_cap(store: MemoryStore) -> None:
    looping = _Resp("tool_use", [_Block(type="tool_use", id="t", name="recall", input={})])
    client = FakeClient([looping, looping, looping])
    with pytest.raises(AgentError, match="iteration cap"):
        run_agent("x", client=client, store=store, provider="anthropic", max_iterations=2)


def test_bad_max_seconds(store: MemoryStore) -> None:
    with pytest.raises(AgentError):
        run_agent("x", client=FakeClient([]), store=store, provider="anthropic", max_seconds=0)


def test_extract_text_joins_blocks() -> None:
    assert _extract_text([_Block(type="text", text="a"), _Block(type="text", text="b")]) == "a\nb"
    assert _extract_text([]) == ""


def test_detect_provider_for_gemini_model() -> None:
    assert _detect_provider(None, "gemini-2.0-flash") == "google"


def test_detect_provider_with_injected_client() -> None:
    assert _detect_provider(object(), "claude-opus-4-8") == "anthropic"


# -- stop / iteration logic ----------------------------------------------


def test_terminal_stop_max_tokens(store: MemoryStore) -> None:
    client = FakeClient([_Resp("max_tokens", [_Block(type="text", text="partial")])])
    result = run_agent("x", client=client, store=store, provider="anthropic")
    assert result.stop_reason == "max_tokens"
    assert result.text == "partial"
    assert result.iterations == 1


def test_unexpected_stop_reason_returns_marker(store: MemoryStore) -> None:
    client = FakeClient([_Resp("weird_reason", [])])
    result = run_agent("x", client=client, store=store, provider="anthropic")
    assert result.stop_reason == "weird_reason"
    assert "unexpected stop_reason" in result.text


def test_pause_turn_then_finish(store: MemoryStore) -> None:
    client = FakeClient(
        [
            _Resp("pause_turn", [_Block(type="text", text="thinking")]),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    result = run_agent("x", client=client, store=store, provider="anthropic")
    assert result.stop_reason == "end_turn"
    assert result.text == "done"
    assert result.iterations == 2


def test_deadline_trips_midloop(store: MemoryStore, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    # A tool_use first response forces a second iteration; by then the wall-clock
    # deadline has passed, so the loop must raise before calling the model again.
    client = FakeClient(
        [
            _Resp("tool_use", [_Block(type="tool_use", id="t1", name="recall", input={})]),
            _Resp("end_turn", [_Block(type="text", text="too late")]),
        ]
    )
    calls = {"n": 0}

    def fake_monotonic() -> float:
        calls["n"] += 1
        return 100.0 if calls["n"] <= 2 else 200.0  # deadline calc + iter1 pass, iter2 trips

    monkeypatch.setattr(loop_mod.time, "monotonic", fake_monotonic)
    with pytest.raises(AgentError, match="time budget exhausted"):
        run_agent("x", client=client, store=store, provider="anthropic", max_seconds=1.0)


def test_injected_custom_tool_is_dispatched(store: MemoryStore) -> None:
    # Regression: tools passed via `tools=` must be dispatchable, not just
    # advertised to the model. Before the registry, dispatch scanned only
    # BUILTIN_TOOLS, so a custom tool came back as "Unknown tool".
    from sakthai.agent.tools import Tool

    def _echo(args: dict, _store: MemoryStore) -> str:
        return f"echoed:{args.get('msg', '')}"

    echo = Tool(
        name="echo",
        description="echo back a message",
        input_schema={"type": "object", "properties": {"msg": {"type": "string"}}},
        handler=_echo,
    )
    client = FakeClient(
        [
            _Resp("tool_use", [_Block(type="tool_use", id="t1", name="echo", input={"msg": "hi"})]),
            _Resp("end_turn", [_Block(type="text", text="ok")]),
        ]
    )
    result = run_agent("x", client=client, store=store, provider="anthropic", tools=(echo,))
    assert result.stop_reason == "end_turn"
    assert any(c["name"] == "echo" and not c["is_error"] for c in result.tool_calls)


def test_skills_are_injected_into_system_prompt(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: d\n---\n\nALWAYS DO THE DEMO THING.\n",
        encoding="utf-8",
    )
    import sakthai.skills as skills_mod

    monkeypatch.setattr(skills_mod, "default_skill_roots", lambda: (tmp_path,))

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent("x", client=_CapClient(), store=store, provider="anthropic", skills=["demo-skill"])
    assert "ALWAYS DO THE DEMO THING." in captured["system"]


class FakeHttpxClient:
    def __init__(self, response_data: dict) -> None:
        self.response_data = response_data
        self.payloads: list = []

    def post(self, url: str, json: dict) -> Any:
        self.payloads.append((url, json))

        class FakeResponse:
            def __init__(self, data: dict) -> None:
                self.data = data

            def raise_for_status(self) -> None:
                pass

            def json(self) -> dict:
                return self.data

        return FakeResponse(self.response_data)


def test_detect_provider_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    import sakthai.auth

    monkeypatch.setattr(sakthai.auth, "load_claude_cli_token", lambda: None)
    monkeypatch.setattr(sakthai.auth, "load_gemini_cli_token", lambda: None)

    assert _detect_provider(None, "gpt-4o") == "openai"
    assert _detect_provider(None, "qwen2.5-coder") == "openai"
    assert _detect_provider(None, "llama-3") == "openai"
    assert _detect_provider(None, "deepseek-chat") == "openai"
    assert _detect_provider(None, "mistral-large") == "openai"

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    assert _detect_provider(None, "some-random-model") == "openai"


def test_openai_provider_basic(store: MemoryStore) -> None:
    response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "hello world from openai",
                },
                "finish_reason": "stop",
            }
        ]
    }
    client = FakeHttpxClient(response_data)
    result = run_agent("hi", client=client, store=store, provider="openai")
    assert result.text == "hello world from openai"
    assert result.iterations == 1
    assert result.stop_reason == "end_turn"


def test_openai_provider_tool_use(store: MemoryStore) -> None:
    first_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "let's learn a fact",
                    "tool_calls": [
                        {
                            "id": "t1",
                            "type": "function",
                            "function": {
                                "name": "learn",
                                "arguments": '{"value": "loves python", "kind": "pref"}',
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ]
    }
    second_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "fact saved successfully",
                },
                "finish_reason": "stop",
            }
        ]
    }

    class MultiResponseFakeHttpxClient:
        def __init__(self, responses: list) -> None:
            self.responses = responses
            self.calls = 0

        def post(self, url: str, json: dict) -> Any:
            resp_data = self.responses[self.calls]
            self.calls += 1

            class FakeResponse:
                def raise_for_status(self) -> None:
                    pass

                def json(self) -> dict:
                    return resp_data

            return FakeResponse()

    client = MultiResponseFakeHttpxClient([first_response, second_response])
    result = run_agent("save fact", client=client, store=store, provider="openai")
    assert result.text == "fact saved successfully"
    assert result.iterations == 2
    assert [c["name"] for c in result.tool_calls] == ["learn"]
    assert store.list_facts()[0].value == "loves python"


def test_run_agent_loop_tool(store: MemoryStore, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod
    from sakthai.agent.tools import tool_by_name

    run_agent_loop_tool = tool_by_name("run_agent_loop")
    assert run_agent_loop_tool is not None

    inner_client = FakeClient([_Resp("end_turn", [_Block(type="text", text="inner loop success")])])
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: inner_client)

    res = run_agent_loop_tool.handler(
        {"task": "do something complex", "provider": "anthropic"},
        store,
    )
    assert res == "inner loop success"


def test_run_agent_loop_recursion_guard(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    from sakthai.agent.tools import tool_by_name

    run_agent_loop_tool = tool_by_name("run_agent_loop")
    assert run_agent_loop_tool is not None

    monkeypatch.setenv("SAKTHAI_AGENT_ACTIVE", "1")

    with pytest.raises(ValueError, match="Indirect recursion detected"):
        run_agent_loop_tool.handler(
            {"task": "do nested task", "provider": "anthropic"},
            store,
        )


def test_run_agent_loop_pruning(store: MemoryStore, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod
    from sakthai.agent.tools import tool_by_name

    run_agent_loop_tool = tool_by_name("run_agent_loop")
    assert run_agent_loop_tool is not None

    inner_client = FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="learn", input={"value": "fact-xyz"})],
            ),
            _Resp("end_turn", [_Block(type="text", text="inner success")]),
        ]
    )
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: inner_client)

    res_pruned = run_agent_loop_tool.handler(
        {"task": "do pruning task", "provider": "anthropic", "prune_history": True},
        store,
    )
    assert res_pruned == "inner success"

    inner_client2 = FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t2", name="learn", input={"value": "fact-abc"})],
            ),
            _Resp("end_turn", [_Block(type="text", text="inner success 2")]),
        ]
    )
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: inner_client2)

    res_unpruned = run_agent_loop_tool.handler(
        {"task": "do unpruned task", "provider": "anthropic", "prune_history": False},
        store,
    )
    assert "inner success 2" in res_unpruned
    assert "Tool calls made in this loop:" in res_unpruned
    assert "- learn({'value': 'fact-abc'}) [success]" in res_unpruned


# ---------- retry behaviour tests (Phase 5.1) ----------


class _FailThenSucceedMessages:
    """Simulates a transient failure followed by a successful response."""

    def __init__(self, fail_exc: Exception, success_resp: _Resp) -> None:
        self._fail_exc = fail_exc
        self._success = success_resp
        self.calls = 0

    def create(self, **kwargs: object) -> _Resp:
        self.calls += 1
        if self.calls == 1:
            raise self._fail_exc
        return self._success


class _FailThenSucceedClient:
    def __init__(self, fail_exc: Exception, success_resp: _Resp) -> None:
        self.messages = _FailThenSucceedMessages(fail_exc, success_resp)


def test_anthropic_retry_on_rate_limit(store: MemoryStore) -> None:
    """Verify RateLimitError is retried and succeeds on 2nd attempt."""
    import anthropic as anth
    import httpx

    req = httpx.Request("POST", "https://api.anthropic.com")
    resp = httpx.Response(429, request=req)
    exc = anth.RateLimitError(
        message="rate limited",
        response=resp,
        body=None,
    )
    client = _FailThenSucceedClient(
        exc, _Resp("end_turn", [_Block(type="text", text="retry worked")])
    )
    result = run_agent("hi", client=client, store=store, provider="anthropic", max_iterations=1)
    assert result.text == "retry worked"
    assert client.messages.calls == 2  # 1 fail + 1 success


def test_anthropic_no_retry_on_bad_request(store: MemoryStore) -> None:
    """Verify BadRequestError (400) is NOT retried — fails immediately."""
    import anthropic as anth
    import httpx

    req = httpx.Request("POST", "https://api.anthropic.com")
    resp = httpx.Response(400, request=req)
    exc = anth.BadRequestError(
        message="bad request",
        response=resp,
        body=None,
    )
    client = _FailThenSucceedClient(
        exc, _Resp("end_turn", [_Block(type="text", text="should not reach")])
    )
    with pytest.raises(AgentError, match="Anthropic API call failed"):
        run_agent("hi", client=client, store=store, provider="anthropic", max_iterations=1)
    assert client.messages.calls == 1  # no retry


def test_anthropic_retry_on_connection_error(store: MemoryStore) -> None:
    """Verify OSError (connection failure) is retried."""
    client = _FailThenSucceedClient(
        OSError("Connection reset"),
        _Resp("end_turn", [_Block(type="text", text="reconnected")]),
    )
    result = run_agent("hi", client=client, store=store, provider="anthropic", max_iterations=1)
    assert result.text == "reconnected"
    assert client.messages.calls == 2


# -- 5.1 API retry with exponential backoff -----------------------------


class _StatusError(Exception):
    """Stand-in for an SDK error carrying an HTTP status_code."""

    def __init__(self, status_code: int) -> None:
        super().__init__(f"status {status_code}")
        self.status_code = status_code


def test_is_retryable_classifies_errors() -> None:
    import httpx

    from sakthai.agent.loop import _is_retryable

    assert _is_retryable(_StatusError(429)) is True
    assert _is_retryable(_StatusError(503)) is True
    assert _is_retryable(httpx.ConnectError("boom")) is True
    assert _is_retryable(_StatusError(400)) is False
    assert _is_retryable(_StatusError(404)) is False
    assert _is_retryable(ValueError("nope")) is False


def test_with_retry_recovers_after_transient(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod
    import sakthai.agent.providers.base as base

    monkeypatch.setattr(base, "RETRY_WAIT_MULTIPLIER", 0.0)
    monkeypatch.setattr(base, "RETRY_WAIT_MAX", 0.0)

    calls = {"n": 0}

    def flaky() -> str:
        calls["n"] += 1
        if calls["n"] < 2:
            raise _StatusError(503)
        return "ok"

    assert loop_mod._with_retry(flaky) == "ok"
    assert calls["n"] == 2


def test_with_retry_does_not_retry_non_retryable(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod
    import sakthai.agent.providers.base as base

    monkeypatch.setattr(base, "RETRY_WAIT_MULTIPLIER", 0.0)
    monkeypatch.setattr(base, "RETRY_WAIT_MAX", 0.0)

    calls = {"n": 0}

    def bad_request() -> str:
        calls["n"] += 1
        raise _StatusError(400)

    with pytest.raises(_StatusError):
        loop_mod._with_retry(bad_request)
    assert calls["n"] == 1


def test_anthropic_call_retries_then_succeeds(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.providers.base as base

    monkeypatch.setattr(base, "RETRY_WAIT_MULTIPLIER", 0.0)
    monkeypatch.setattr(base, "RETRY_WAIT_MAX", 0.0)

    class _FlakyMessages:
        def __init__(self) -> None:
            self.calls = 0

        def create(self, **_kwargs: object) -> _Resp:
            self.calls += 1
            if self.calls < 2:
                raise _StatusError(503)
            return _Resp("end_turn", [_Block(type="text", text="recovered")])

    class _FlakyClient:
        def __init__(self) -> None:
            self.messages = _FlakyMessages()

    client = _FlakyClient()
    result = run_agent("x", client=client, store=store, provider="anthropic")
    assert result.text == "recovered"
    assert client.messages.calls == 2


# ---------- usage tracking (Phase 5.2) ----------


class _RespWithUsage:
    def __init__(self, usage: Any) -> None:
        self.stop_reason = "end_turn"
        self.content = [_Block(type="text", text="hi")]
        self.usage = usage


def test_usage_tracker_accumulates() -> None:
    from sakthai.agent.usage import UsageTracker

    tracker = UsageTracker()
    tracker.record(input_tokens=10, output_tokens=20)
    tracker.record(input_tokens=5, output_tokens=10)
    assert tracker.to_dict() == {
        "input_tokens": 15,
        "output_tokens": 30,
        "total_tokens": 45,
    }


def test_extract_usage_anthropic() -> None:
    from sakthai.agent.usage import extract_usage

    resp = _RespWithUsage(usage=type("U", (), {"input_tokens": 7, "output_tokens": 13})())
    assert extract_usage(resp) == {"input_tokens": 7, "output_tokens": 13}


# ---------- provider construction / credentials validation (Phase 5.4) ----------


def test_provider_construction_no_creds_google(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    with pytest.raises(AgentError, match="Missing credentials for Google Gemini"):
        run_agent("hello", store=store, provider="google")


def test_provider_construction_no_creds_openai(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    with pytest.raises(AgentError, match="No OpenAI credentials found"):
        run_agent("hello", store=store, provider="openai")


def test_provider_construction_no_creds_anthropic(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    import sakthai.auth

    monkeypatch.setattr(sakthai.auth, "load_claude_cli_token", lambda: None)
    with pytest.raises(AgentError, match="No Anthropic credentials found"):
        run_agent("hello", store=store, provider="anthropic")


# -- 5.6 preflight (sakthai run --dry-run, no API call) -----------------


def test_preflight_runnable_with_anthropic_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "anthropic_credential_source", lambda: "api_key")
    report = loop_mod.preflight(provider="anthropic")
    assert report["provider"] == "anthropic"
    assert report["model"] == loop_mod.DEFAULT_MODEL
    assert report["credential_source"] == "api_key"
    assert report["runnable"] is True
    assert report["tool_count"] >= 1
    assert "learn" in report["tools"]


def test_preflight_not_runnable_without_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "anthropic_credential_source", lambda: None)
    report = loop_mod.preflight(provider="anthropic")
    assert report["runnable"] is False
    assert report["credential_source"] is None


def test_preflight_ollama_maps_to_openai(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    for var in ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OLLAMA_HOST", "http://localhost:11434")
    report = loop_mod.preflight(provider="ollama")
    assert report["provider"] == "openai"
    assert report["model"] == "qwen2.5-coder:7b"
    assert report["credential_source"] == "ollama_host"
    assert report["runnable"] is True


def test_preflight_makes_no_api_call(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    def boom(*_a: object, **_k: object) -> Any:
        raise AssertionError("preflight must not build a client")

    monkeypatch.setattr(loop_mod, "_build_client", boom)
    monkeypatch.setattr(loop_mod, "anthropic_credential_source", lambda: "api_key")
    report = loop_mod.preflight(provider="anthropic")
    assert report["runnable"] is True


# -- 7.1 streaming callback interface -----------------------------------


def test_run_agent_accepts_on_token(store: MemoryStore) -> None:
    # With on_token set, the anthropic backend streams via client.messages.stream.
    final = _Resp("end_turn", [_Block(type="text", text="hi")])
    client = _StreamClient(["hi"], final)
    tokens: list[str] = []
    result = run_agent(
        "x", client=client, store=store, provider="anthropic", on_token=tokens.append
    )
    assert result.text == "hi"
    assert tokens == ["hi"]


def test_provider_calls_accept_on_token() -> None:
    import inspect

    from sakthai.agent.providers import call_anthropic, call_gemini, call_openai_compat

    for fn in (call_anthropic, call_gemini, call_openai_compat):
        assert "on_token" in inspect.signature(fn).parameters


# -- 7.2 Anthropic streaming --------------------------------------------


class _FakeStream:
    def __init__(self, deltas: list[str], final: _Resp) -> None:
        self.text_stream = iter(deltas)
        self._final = final

    def __enter__(self) -> _FakeStream:
        return self

    def __exit__(self, *_a: object) -> bool:
        return False

    def get_final_message(self) -> _Resp:
        return self._final


class _StreamMessages:
    def __init__(self, deltas: list[str], final: _Resp) -> None:
        self._deltas = deltas
        self._final = final
        self.stream_calls = 0

    def stream(self, **_kwargs: object) -> _FakeStream:
        self.stream_calls += 1
        return _FakeStream(self._deltas, self._final)


class _StreamClient:
    def __init__(self, deltas: list[str], final: _Resp) -> None:
        self.messages = _StreamMessages(deltas, final)


def test_anthropic_streaming_emits_text_deltas(store: MemoryStore) -> None:
    final = _Resp("end_turn", [_Block(type="text", text="Hello world")])
    client = _StreamClient(["Hello ", "world"], final)
    tokens: list[str] = []
    result = run_agent(
        "x", client=client, store=store, provider="anthropic", on_token=tokens.append
    )
    assert tokens == ["Hello ", "world"]
    assert result.text == "Hello world"
    assert client.messages.stream_calls == 1


def test_anthropic_no_stream_when_no_on_token(store: MemoryStore) -> None:
    # Without on_token the non-streaming create() path is used (FakeClient has no .stream).
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="plain")])])
    result = run_agent("x", client=client, store=store, provider="anthropic")
    assert result.text == "plain"
