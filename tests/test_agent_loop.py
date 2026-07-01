"""Tests for the agent loop using a fake client (no network)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from sakthai.agent.loop import (
    AgentError,
    AgentResult,
    _detect_provider,
    _detect_untriggered_tool_call,
    _extract_text,
    _parse_slash_command,
    _save_session_log,
    _strip_code_fence,
    run_agent,
)
from sakthai.agent.registry import builtin_registry
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
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="echo", input={"msg": "hi"})],
            ),
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

    run_agent(
        "x",
        client=_CapClient(),
        store=store,
        provider="anthropic",
        skills=["demo-skill"],
    )
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


def test_run_agent_failed_setup_does_not_leak_active_flag(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run_agent call that fails during setup must not leave SAKTHAI_AGENT_ACTIVE
    set in the process environment.

    Regression: the flag used to be set before the try/finally that restores it,
    so any exception in provider detection / client build leaked "1" globally and
    permanently tripped the run_agent_loop recursion guard for the rest of the
    process. Here _build_client raises before the loop body; the flag must be
    absent afterwards and the recursion guard must not fire on a later call.
    """
    import os

    import sakthai.agent.loop as loop_mod
    from sakthai.agent.providers import AgentError
    from sakthai.agent.tools import tool_by_name

    monkeypatch.delenv("SAKTHAI_AGENT_ACTIVE", raising=False)

    def _boom(provider: str, client: object) -> object:
        raise AgentError("no credentials")

    monkeypatch.setattr(loop_mod, "_build_client", _boom)

    with pytest.raises(AgentError):
        run_agent("do something", store=store, provider="anthropic")

    assert "SAKTHAI_AGENT_ACTIVE" not in os.environ

    # The leaked flag would have made this raise "Indirect recursion detected".
    inner_client = FakeClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: inner_client)
    run_agent_loop_tool = tool_by_name("run_agent_loop")
    assert run_agent_loop_tool is not None
    result = run_agent_loop_tool.handler({"task": "later task", "provider": "anthropic"}, store)
    assert result == "ok"


def test_run_agent_loop_pruning(store: MemoryStore, monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod
    from sakthai.agent.tools import tool_by_name

    run_agent_loop_tool = tool_by_name("run_agent_loop")
    assert run_agent_loop_tool is not None

    inner_client = FakeClient(
        [
            _Resp(
                "tool_use",
                [
                    _Block(
                        type="tool_use",
                        id="t1",
                        name="learn",
                        input={"value": "fact-xyz"},
                    )
                ],
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
                [
                    _Block(
                        type="tool_use",
                        id="t2",
                        name="learn",
                        input={"value": "fact-abc"},
                    )
                ],
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


def test_with_retry_does_not_retry_non_retryable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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
    try:
        import google.genai  # noqa: F401
    except BaseException:
        pytest.skip("google-genai not importable in this environment (missing native libs)")
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


def test_preflight_runnable_with_anthropic_creds(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_preflight_gateway_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "gateway_credential_source", lambda: "gateway_url")
    monkeypatch.setattr(loop_mod, "_build_client", lambda *a, **kw: None)
    report = loop_mod.preflight(provider="gateway")
    assert report["provider"] == "gateway"
    assert report["credential_source"] == "gateway_url"
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


# -- 7.3 OpenAI-compatible streaming ------------------------------------


class _FakeSSEResponse:
    def __init__(self, lines: list[str]) -> None:
        self._lines = lines

    def __enter__(self) -> _FakeSSEResponse:
        return self

    def __exit__(self, *_a: object) -> bool:
        return False

    def raise_for_status(self) -> None:
        return None

    def iter_lines(self):  # type: ignore[no-untyped-def]
        return iter(self._lines)


class _FakeStreamHTTPX:
    """Fake httpx client whose .stream() replays one SSE line-set per call."""

    def __init__(self, line_sets: list[list[str]]) -> None:
        self._line_sets = line_sets
        self.stream_calls = 0

    def stream(self, method: str, url: str, json: Any = None) -> _FakeSSEResponse:
        lines = self._line_sets[self.stream_calls]
        self.stream_calls += 1
        return _FakeSSEResponse(lines)


def test_openai_streaming_emits_text_deltas(store: MemoryStore) -> None:
    lines = [
        'data: {"choices":[{"delta":{"content":"Hello "}}]}',
        'data: {"choices":[{"delta":{"content":"world"}}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"stop"}],'
        '"usage":{"prompt_tokens":3,"completion_tokens":2}}',
        "data: [DONE]",
    ]
    client = _FakeStreamHTTPX([lines])
    tokens: list[str] = []
    result = run_agent("x", client=client, store=store, provider="openai", on_token=tokens.append)
    assert tokens == ["Hello ", "world"]
    assert result.text == "Hello world"
    assert result.stop_reason == "end_turn"
    assert result.usage["input_tokens"] == 3
    assert result.usage["output_tokens"] == 2
    assert client.stream_calls == 1


# -- Gemini provider helpers ---------------------------------------------


def _install_fake_genai(monkeypatch: pytest.MonkeyPatch) -> object:
    """Inject a minimal google.genai stand-in into sys.modules.

    Returns the fake ``types`` namespace so tests can construct fake response
    objects without importing the real SDK.
    """
    import sys
    import types as _t

    class _Part:
        def __init__(
            self,
            text: str | None = None,
            function_call: object | None = None,
            function_response: object | None = None,
        ) -> None:
            self.text = text or ""
            self.function_calls = [function_call] if function_call is not None else []
            self.function_response = function_response

    class _FunctionCall:
        def __init__(self, name: str = "", args: dict | None = None) -> None:
            self.name = name
            self.args = args or {}

    class _FunctionResponse:
        def __init__(self, name: str = "", response: object = None) -> None:
            pass

    class _Content:
        def __init__(self, role: str = "", parts: list | None = None) -> None:
            self.role = role
            self.parts = parts or []

    class _Tool:
        def __init__(self, function_declarations: object = None) -> None:
            pass

    class _FunctionDeclaration:
        def __init__(
            self, name: str = "", description: str = "", parameters: object = None
        ) -> None:
            pass

    class _GenerateContentConfig:
        def __init__(self, system_instruction: str = "", tools: object = None) -> None:
            pass

    fake_types = _t.SimpleNamespace(
        Part=_Part,
        FunctionCall=_FunctionCall,
        FunctionResponse=_FunctionResponse,
        Content=_Content,
        Tool=_Tool,
        FunctionDeclaration=_FunctionDeclaration,
        GenerateContentConfig=_GenerateContentConfig,
    )
    fake_genai = _t.SimpleNamespace(types=fake_types)

    if "google" not in sys.modules:
        monkeypatch.setitem(sys.modules, "google", _t.SimpleNamespace(genai=fake_genai))
    monkeypatch.setitem(sys.modules, "google.genai", fake_genai)
    monkeypatch.setitem(sys.modules, "google.genai.types", fake_types)
    return fake_types


# -- call_gemini unit tests ----------------------------------------------


def test_call_gemini_text_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_types = _install_fake_genai(monkeypatch)

    from sakthai.agent.providers.gemini_provider import call_gemini
    from sakthai.agent.tools import BUILTIN_TOOLS

    class _UsageMeta:
        prompt_token_count = 4
        candidates_token_count = 8

    class _Candidate:
        finish_reason = "STOP"
        content = type("C", (), {"parts": [fake_types.Part(text="gemini reply")]})()  # type: ignore[attr-defined]

    class _FakeResponse:
        candidates = [_Candidate()]
        usage_metadata = _UsageMeta()

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(**_kw: object) -> _FakeResponse:
                return _FakeResponse()

    resp = call_gemini(
        _FakeClient(),
        "gemini-2.0-flash",
        "system prompt",
        BUILTIN_TOOLS,
        [{"role": "user", "content": "hello"}],
        1,
    )
    assert resp.stop_reason == "end_turn"
    assert any(b.type == "text" and "gemini reply" in b.text for b in resp.content)
    assert resp.usage["input_tokens"] == 4
    assert resp.usage["output_tokens"] == 8


def test_call_gemini_tool_use_response(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_types = _install_fake_genai(monkeypatch)

    from sakthai.agent.providers.gemini_provider import call_gemini
    from sakthai.agent.tools import BUILTIN_TOOLS

    fc = fake_types.FunctionCall(name="learn", args={"value": "from gemini"})  # type: ignore[attr-defined]

    class _UsageMeta:
        prompt_token_count = 5
        candidates_token_count = 3

    class _Candidate:
        finish_reason = "OTHER"
        content = type("C", (), {"parts": [fake_types.Part(function_call=fc)]})()  # type: ignore[attr-defined]

    class _FakeResponse:
        candidates = [_Candidate()]
        usage_metadata = _UsageMeta()

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(**_kw: object) -> _FakeResponse:
                return _FakeResponse()

    resp = call_gemini(
        _FakeClient(),
        "gemini-2.0-flash",
        "system",
        BUILTIN_TOOLS,
        [{"role": "user", "content": "save it"}],
        1,
    )
    assert resp.stop_reason == "tool_use"
    assert any(b.type == "tool_use" and b.name == "learn" for b in resp.content)
    tool_block = next(b for b in resp.content if b.type == "tool_use")
    assert tool_block.input == {"value": "from gemini"}


def test_call_gemini_no_candidates_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_genai(monkeypatch)

    from sakthai.agent.providers.base import AgentError
    from sakthai.agent.providers.gemini_provider import call_gemini
    from sakthai.agent.tools import BUILTIN_TOOLS

    class _UsageMeta:
        prompt_token_count = 0
        candidates_token_count = 0

    class _FakeResponse:
        candidates: list = []
        usage_metadata = _UsageMeta()

    class _FakeClient:
        class models:
            @staticmethod
            def generate_content(**_kw: object) -> _FakeResponse:
                return _FakeResponse()

    with pytest.raises(AgentError, match="no candidates"):
        call_gemini(
            _FakeClient(),
            "gemini-2.0-flash",
            "sys",
            BUILTIN_TOOLS,
            [{"role": "user", "content": "x"}],
            1,
        )


def test_gemini_loop_dispatches_via_run_agent(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod
    from sakthai.agent.providers.base import Block, Response

    fake_resp = Response("end_turn", [Block("text", text="gemini answer")])
    monkeypatch.setattr(loop_mod, "_call_gemini", lambda *_a, **_kw: fake_resp)

    result = run_agent("hi", client=object(), store=store, provider="google")
    assert result.text == "gemini answer"
    assert result.stop_reason == "end_turn"


# -- to_gemini_contents message adaptation -------------------------------


def test_to_gemini_contents_text_message(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_genai(monkeypatch)

    from sakthai.agent.providers.gemini_provider import to_gemini_contents

    messages = [{"role": "user", "content": "hello world"}]
    contents = to_gemini_contents(messages)
    assert len(contents) == 1
    assert contents[0].role == "user"
    assert len(contents[0].parts) == 1
    assert contents[0].parts[0].text == "hello world"


def test_to_gemini_contents_tool_result_role(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_genai(monkeypatch)

    from sakthai.agent.providers.gemini_provider import to_gemini_contents

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "content": "stored",
                    "is_error": False,
                }
            ],
        }
    ]
    contents = to_gemini_contents(messages)
    assert len(contents) == 1
    assert contents[0].role == "tool"


# -- providers/base.py helpers -------------------------------------------


def test_block_field_reads_dict_and_object() -> None:
    from sakthai.agent.providers.base import block_field

    assert block_field({"type": "text", "text": "hi"}, "type") == "text"
    assert block_field({}, "type", "default") == "default"

    class _Obj:
        type = "tool_use"

    assert block_field(_Obj(), "type") == "tool_use"
    assert block_field(_Obj(), "missing_attr", "fallback") == "fallback"


def test_find_tool_name_by_id() -> None:
    from sakthai.agent.providers.base import find_tool_name_by_id

    class _Block:
        def __init__(self, btype: str, bid: str = "", bname: str = "") -> None:
            self.type = btype
            self.id = bid
            self.name = bname

    messages = [
        {
            "role": "assistant",
            "content": [
                _Block("tool_use", bid="t1", bname="learn"),
                _Block("tool_use", bid="t2", bname="recall"),
            ],
        }
    ]
    assert find_tool_name_by_id(messages, "t1") == "learn"
    assert find_tool_name_by_id(messages, "t2") == "recall"
    assert find_tool_name_by_id(messages, "missing") == "unknown"


def test_openai_streaming_reassembles_tool_calls(store: MemoryStore) -> None:
    tool_lines = [
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,"id":"c1",'
        '"function":{"name":"learn","arguments":"{\\"val"}}]}}]}',
        'data: {"choices":[{"delta":{"tool_calls":[{"index":0,'
        '"function":{"arguments":"ue\\": \\"x\\"}"}}]}}]}',
        'data: {"choices":[{"delta":{},"finish_reason":"tool_calls"}]}',
        "data: [DONE]",
    ]
    end_lines = [
        'data: {"choices":[{"delta":{"content":"done"},"finish_reason":"stop"}]}',
        "data: [DONE]",
    ]
    client = _FakeStreamHTTPX([tool_lines, end_lines])
    result = run_agent(
        "x",
        client=client,
        store=store,
        provider="openai",
        on_token=lambda _t: None,
        max_iterations=2,
    )
    # The reassembled tool call (split across chunks) should have dispatched `learn`.
    assert any(c["name"] == "learn" for c in result.tool_calls)
    assert result.text == "done"


# -- session log persistence --------------------------------------------


def test_session_log_written_after_run(sakthai_home: Path, store: MemoryStore) -> None:
    import json

    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="result")])])
    run_agent("my task", client=client, store=store, provider="anthropic")
    logs = list((sakthai_home / "sessions").glob("*.json"))
    assert len(logs) == 1
    payload = json.loads(logs[0].read_text(encoding="utf-8"))
    assert payload["task"] == "my task"
    assert isinstance(payload["model"], str) and payload["model"]
    assert isinstance(payload["timestamp"], int) and payload["timestamp"] > 0
    assert isinstance(payload["messages"], list)


def test_session_log_result_schema(sakthai_home: Path, store: MemoryStore) -> None:
    import json

    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="hello")])])
    run_agent("task", client=client, store=store, provider="anthropic")
    logs = list((sakthai_home / "sessions").glob("*.json"))
    payload = json.loads(logs[0].read_text(encoding="utf-8"))
    result = payload["result"]
    assert result["text"] == "hello"
    assert result["iterations"] == 1
    assert result["stop_reason"] == "end_turn"
    assert isinstance(result["tool_calls"], list)


def test_session_log_usage_totals_match(sakthai_home: Path, store: MemoryStore) -> None:
    import json

    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    run_agent("task", client=client, store=store, provider="anthropic")
    logs = list((sakthai_home / "sessions").glob("*.json"))
    payload = json.loads(logs[0].read_text(encoding="utf-8"))
    usage = payload["usage"]
    assert usage["total_tokens"] == usage["input_tokens"] + usage["output_tokens"]


def test_session_log_written_with_tool_calls(sakthai_home: Path, store: MemoryStore) -> None:
    import json

    client = FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="learn", input={"value": "x"})],
            ),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    run_agent("learn x", client=client, store=store, provider="anthropic")
    logs = list((sakthai_home / "sessions").glob("*.json"))
    payload = json.loads(logs[0].read_text(encoding="utf-8"))
    tool_calls = payload["result"]["tool_calls"]
    assert any(c["name"] == "learn" for c in tool_calls)


def test_slash_command_parsing(sakthai_home: Path, store: MemoryStore) -> None:
    gemini_ext_dir = sakthai_home.parent / "gemini" / "extensions"
    cmd_dir = gemini_ext_dir / "my-plugin" / "commands"
    cmd_dir.mkdir(parents=True, exist_ok=True)
    (cmd_dir / "my-cmd.md").write_text(
        "---\ndescription: test desc\n---\n\nRule: Do the $ARGUMENTS thing.\n",
        encoding="utf-8",
    )

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            captured["task"] = str(kwargs.get("messages", [{}])[0].get("content", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent(
        "/my-plugin:my-cmd write a test",
        client=_CapClient(),
        store=store,
        provider="anthropic",
    )

    assert "Rule: Do the write a test thing." in captured["system"]
    assert captured["task"] == "write a test"


def test_fast_mode_injects_fast_track_instruction(store: MemoryStore) -> None:
    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent("x", client=_CapClient(), store=store, provider="anthropic", fast=True)
    assert "FAST-TRACK MODE" in captured["system"]


def test_tool_handler_exception_returned_as_error(store: MemoryStore) -> None:
    from sakthai.agent.tools import Tool

    def _boom(args: dict, _store: MemoryStore) -> str:
        raise RuntimeError("handler exploded")

    bad_tool = Tool(
        name="bad_tool",
        description="always fails",
        input_schema={"type": "object", "properties": {}},
        handler=_boom,
    )
    client = FakeClient(
        [
            _Resp(
                "tool_use",
                [_Block(type="tool_use", id="t1", name="bad_tool", input={})],
            ),
            _Resp("end_turn", [_Block(type="text", text="recovered")]),
        ]
    )
    result = run_agent(
        "x",
        client=client,
        store=store,
        provider="anthropic",
        tools=(bad_tool,),
    )
    # The error is surfaced back to the model (is_error flag set), not raised.
    assert result.text == "recovered"
    assert any(c["is_error"] for c in result.tool_calls)


def test_run_agent_creates_own_store_and_closes_it(sakthai_home: Path) -> None:
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    # No store= passed → run_agent creates and owns its MemoryStore.
    result = run_agent("hi", client=client, provider="anthropic")
    assert result.text == "ok"


def test_preflight_google_gemini_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setenv("GEMINI_API_KEY", "fake-gemini-key")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    report = loop_mod.preflight(provider="google")
    assert report["provider"] == "google"
    assert report["credential_source"] == "GEMINI_API_KEY"
    assert report["runnable"] is True


def test_preflight_google_google_api_key_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "fake-google-key")
    report = loop_mod.preflight(provider="google")
    assert report["credential_source"] == "GOOGLE_API_KEY"
    assert report["runnable"] is True


def test_preflight_google_no_creds(monkeypatch: pytest.MonkeyPatch) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    report = loop_mod.preflight(provider="google")
    assert report["credential_source"] is None
    assert report["runnable"] is False


def test_caveman_flag_injection(sakthai_home: Path, store: MemoryStore) -> None:
    gemini_ext_dir = sakthai_home.parent / "gemini" / "extensions"
    skill_dir = gemini_ext_dir / "caveman" / "skills" / "caveman"
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        "---\nname: caveman\ndescription: test caveman desc\n---\n\nRespond terse.\n",
        encoding="utf-8",
    )

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent(
        "x",
        client=_CapClient(),
        store=store,
        provider="anthropic",
        caveman="ultra",
    )

    assert "Respond terse." in captured["system"]
    assert "ACTIVE CAVEMAN LEVEL: ultra" in captured["system"]


# --- Phase 13.2: surface text-emitted (un-dispatched) tool calls -------------


@pytest.mark.parametrize(
    "text",
    [
        '{"name": "learn", "input": {"value": "x", "kind": "pref"}}',
        '{"tool": "learn", "arguments": {}}',
        '{"function": {"name": "learn"}, "arguments": {}}',
        '```json\n{"name": "learn", "parameters": {}}\n```',
        '[{"name": "learn", "input": {}}]',
    ],
)
def test_detect_untriggered_tool_call_positive(text: str) -> None:
    assert _detect_untriggered_tool_call(text, builtin_registry()) == "learn"


@pytest.mark.parametrize(
    "text",
    [
        "",
        "All done — I have learned that for you.",
        '{"name": "not_a_real_tool", "input": {}}',  # unknown tool
        '{"value": "just some json answer"}',  # no tool-name key
        "{not valid json",
    ],
)
def test_detect_untriggered_tool_call_negative(text: str) -> None:
    assert _detect_untriggered_tool_call(text, builtin_registry()) is None


def test_text_emitted_tool_call_warns_without_failing(store: MemoryStore) -> None:
    # Weak model ends the turn with a tool-call-shaped JSON blob as plain text.
    blob = '{"name": "learn", "input": {"value": "uses vim", "kind": "pref"}}'
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text=blob)])])
    events: list = []
    result = run_agent(
        "remember something",
        client=client,
        store=store,
        provider="anthropic",
        on_event=lambda k, p: events.append((k, p)),
    )

    # The run still reports success (it's model quality, not an app error)...
    assert result.stop_reason == "end_turn"
    assert result.text == blob
    # ...but the missed tool call is surfaced rather than silently swallowed.
    assert ("tool_call_in_text", {"name": "learn", "stop_reason": "end_turn"}) in events
    # And nothing was actually dispatched / stored.
    assert result.tool_calls == []
    assert store.list_facts() == []


def test_caveman_flag_not_found_logs_warning(
    sakthai_home: Path, store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "find_skill", lambda *_a: None)

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent("x", client=_CapClient(), store=store, provider="anthropic", caveman="ultra")
    # Caveman skill missing → warning logged, system prompt unchanged (no crash).
    assert "ACTIVE CAVEMAN LEVEL" not in captured.get("system", "")


def test_caveman_combined_with_existing_skills_block(
    sakthai_home: Path, store: MemoryStore
) -> None:
    # Place demo-skill and caveman skill under sakthai_home/extensions/ so
    # default_skill_roots() finds them without any monkeypatching.
    ext_dir = sakthai_home / "extensions"
    for name, body in [("demo-skill", "DEMO BLOCK."), ("caveman", "CAVEMAN RULES.")]:
        skill_dir = ext_dir / name
        skill_dir.mkdir(parents=True, exist_ok=True)
        (skill_dir / "SKILL.md").write_text(
            f"---\nname: {name}\ndescription: {name} desc\n---\n\n{body}\n",
            encoding="utf-8",
        )

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent(
        "x",
        client=_CapClient(),
        store=store,
        provider="anthropic",
        skills=["demo-skill"],
        caveman="ultra",
    )
    # Both the skill block and caveman instructions must appear together.
    assert "DEMO BLOCK." in captured["system"]
    assert "CAVEMAN RULES." in captured["system"]
    assert "ACTIVE CAVEMAN LEVEL: ultra" in captured["system"]


# -- _strip_code_fence ----------------------------------------------------


def test_strip_code_fence_no_closing_fence() -> None:
    text = '```json\n{"key": "value"}'
    result = _strip_code_fence(text)
    # No closing ``` — original (stripped) returned unchanged
    assert result == text.strip()


def test_strip_code_fence_with_closing_fence() -> None:
    text = '```json\n{"key": "value"}\n```'
    result = _strip_code_fence(text)
    assert result == '{"key": "value"}'


def test_strip_code_fence_no_fence_at_all() -> None:
    text = "plain text"
    assert _strip_code_fence(text) == "plain text"


# -- _detect_untriggered_tool_call: OpenAI-style --------------------------


def test_detect_untriggered_tool_call_openai_function_style() -> None:
    registry = builtin_registry()
    text = '{"function": {"name": "learn"}, "arguments": {"value": "x"}}'
    result = _detect_untriggered_tool_call(text, registry)
    assert result == "learn"


def test_detect_untriggered_tool_call_list_with_non_dict_element() -> None:
    registry = builtin_registry()
    # List containing a non-dict element followed by a valid tool call — exercises
    # the `if not isinstance(entry, dict): continue` branch.
    text = '[42, {"name": "recall"}]'
    result = _detect_untriggered_tool_call(text, registry)
    assert result == "recall"


# -- _parse_slash_command -------------------------------------------------


def test_parse_slash_command_finds_command_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    cmd_dir = tmp_path / "my-plugin" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "my-cmd.md").write_text("Do something with $ARGUMENTS", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    result = _parse_slash_command("/my-plugin:my-cmd some args")
    assert result is not None
    system_prompt, arguments = result
    assert "COMMAND INSTRUCTIONS" in system_prompt
    assert "some args" in system_prompt
    assert arguments == "some args"


def test_parse_slash_command_strips_yaml_frontmatter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    cmd_dir = tmp_path / "my-plugin" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "my-cmd.md").write_text(
        "---\ntitle: cmd\n---\nThe actual body content", encoding="utf-8"
    )
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    result = _parse_slash_command("/my-plugin:my-cmd")
    assert result is not None
    system_prompt, _ = result
    assert "The actual body content" in system_prompt
    assert "title: cmd" not in system_prompt


def test_parse_slash_command_returns_none_for_missing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])
    result = _parse_slash_command("/no-plugin:no-cmd")
    assert result is None


def test_parse_slash_command_finds_commands_dir_variant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    # Place command at root/commands/cmd.md (second variant, without plugin prefix dir)
    cmd_dir = tmp_path / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "my-cmd.md").write_text("Do $ARGUMENTS", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    result = _parse_slash_command("/any-plugin:my-cmd extra-args")
    assert result is not None
    system_prompt, arguments = result
    assert "COMMAND INSTRUCTIONS" in system_prompt
    assert arguments == "extra-args"


def test_parse_slash_command_found_in_extension_plugin_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Command at root/child/plugin_name/commands/cmd.md (lines 117-120 in loop.py)."""
    import sakthai.agent.loop as loop_mod

    child = tmp_path / "extension-bundle"
    cmd_dir = child / "my-plugin" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "my-cmd.md").write_text("Extension plugin-subdir body", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    result = _parse_slash_command("/my-plugin:my-cmd")
    assert result is not None
    system_prompt, _ = result
    assert "Extension plugin-subdir body" in system_prompt


def test_parse_slash_command_found_in_extension_commands_subdir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Command at root/child/commands/cmd.md (lines 121-124 in loop.py)."""
    import sakthai.agent.loop as loop_mod

    child = tmp_path / "extension-bundle"
    cmd_dir = child / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "my-cmd.md").write_text("Extension commands-subdir body", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    result = _parse_slash_command("/any-plugin:my-cmd")
    assert result is not None
    system_prompt, _ = result
    assert "Extension commands-subdir body" in system_prompt


def test_parse_slash_command_returns_none_on_read_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sakthai.agent.loop as loop_mod

    cmd_dir = tmp_path / "myplugin" / "commands"
    cmd_dir.mkdir(parents=True)
    cmd_file = cmd_dir / "mycmd.md"
    cmd_file.write_text("Body", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    with patch("pathlib.Path.read_text", side_effect=OSError("permission denied")):
        result = _parse_slash_command("/myplugin:mycmd")
    assert result is None


# -- _save_session_log ----------------------------------------------------


def test_save_session_log_handles_write_error(store: MemoryStore) -> None:
    result = AgentResult(text="done", iterations=1, stop_reason="end_turn", tool_calls=[], usage={})
    with patch("pathlib.Path.write_text", side_effect=OSError("disk full")):
        # Should not raise — failure is best-effort
        _save_session_log("test task", "claude-sonnet-4-6", [], result)


# -- provider/model defaults in run_agent ---------------------------------


def test_run_agent_renames_ollama_provider_to_openai(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """provider='ollama' is normalised to 'openai' before the client is built."""
    from sakthai.agent.providers.base import Response as _ProvResponse

    called: dict[str, bool] = {}

    import sakthai.agent.loop as loop_mod

    def _fake_openai_compat(
        client: object, model: str, *args: object, **kwargs: object
    ) -> _ProvResponse:
        called["openai"] = True
        return _ProvResponse("end_turn", [_Block(type="text", text="ok")])

    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: client)
    monkeypatch.setattr(loop_mod, "_call_openai_compat", _fake_openai_compat)
    run_agent("hi", client=FakeClient([]), store=store, provider="ollama")
    assert called.get("openai") is True


def test_run_agent_openai_defaults_model_to_gpt4o(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When provider='openai' and model=DEFAULT_MODEL (Anthropic) without OLLAMA_HOST,
    the model is reset to 'gpt-4o'."""
    from sakthai.agent.loop import DEFAULT_MODEL
    from sakthai.agent.providers.base import Response as _ProvResponse

    captured: dict[str, str] = {}

    import sakthai.agent.loop as loop_mod

    def _fake_openai_compat(
        client: object, model: str, *args: object, **kwargs: object
    ) -> _ProvResponse:
        captured["model"] = model
        return _ProvResponse("end_turn", [_Block(type="text", text="ok")])

    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: client)
    monkeypatch.setattr(loop_mod, "_call_openai_compat", _fake_openai_compat)
    run_agent("hi", client=FakeClient([]), store=store, provider="openai", model=DEFAULT_MODEL)
    assert captured["model"] == "gpt-4o"


def test_run_agent_openai_defaults_model_to_qwen_when_ollama_host(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When provider='openai', model=DEFAULT_MODEL, and OLLAMA_HOST is set,
    the model is reset to 'qwen2.5-coder:7b'."""
    from sakthai.agent.loop import DEFAULT_MODEL
    from sakthai.agent.providers.base import Response as _ProvResponse

    captured: dict[str, str] = {}

    import sakthai.agent.loop as loop_mod

    def _fake_openai_compat(
        client: object, model: str, *args: object, **kwargs: object
    ) -> _ProvResponse:
        captured["model"] = model
        return _ProvResponse("end_turn", [_Block(type="text", text="ok")])

    monkeypatch.setenv("OLLAMA_HOST", "http://127.0.0.1:11434")
    monkeypatch.setattr(loop_mod, "_build_client", lambda provider, client: client)
    monkeypatch.setattr(loop_mod, "_call_openai_compat", _fake_openai_compat)
    run_agent("hi", client=FakeClient([]), store=store, provider="openai", model=DEFAULT_MODEL)
    assert captured["model"] == "qwen2.5-coder:7b"


def test_run_agent_skills_and_command_system_are_merged(
    store: MemoryStore, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When both a skill and a slash-command are active, they're concatenated into
    skills_block (line 250 in loop.py)."""
    import sakthai.agent.loop as loop_mod
    import sakthai.skills as skills_mod

    # Skill
    skill_dir = tmp_path / "demo-skill"
    skill_dir.mkdir()
    (skill_dir / "SKILL.md").write_text(
        "---\nname: demo-skill\ndescription: d\n---\n\nSKILL BODY HERE.\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(skills_mod, "default_skill_roots", lambda: (tmp_path,))

    # Slash-command file
    cmd_dir = tmp_path / "myplugin" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "mycmd.md").write_text("COMMAND BODY HERE.", encoding="utf-8")
    monkeypatch.setattr(loop_mod, "default_skill_roots", lambda: [tmp_path])

    captured: dict[str, str] = {}

    class _CapMessages:
        def create(self, **kwargs: object) -> _Resp:
            captured["system"] = str(kwargs.get("system", ""))
            return _Resp("end_turn", [_Block(type="text", text="ok")])

    class _CapClient:
        def __init__(self) -> None:
            self.messages = _CapMessages()

    run_agent(
        "/myplugin:mycmd",
        client=_CapClient(),
        store=store,
        provider="anthropic",
        skills=["demo-skill"],
    )
    assert "SKILL BODY HERE." in captured["system"]
    assert "COMMAND BODY HERE." in captured["system"]
