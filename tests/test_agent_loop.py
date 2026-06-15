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
