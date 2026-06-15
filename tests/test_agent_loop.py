"""Tests for the agent loop using a fake client (no network)."""

from __future__ import annotations

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
