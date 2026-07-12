"""Tests for the agent loop's failure-handling seams.

Covers the paths that only matter when something goes wrong: guardrail
denials around tool execution, a model that signals tool_use without
sending tool_use blocks, session-log write failures, and the
``SAKTHAI_AGENT_ACTIVE`` environment restore.
"""

from __future__ import annotations

import os
from typing import Any

import pytest

from sakthai.agent.guardrails import (
    GuardrailAction,
    GuardrailPolicy,
    GuardrailResult,
)
from sakthai.agent.loop import (
    DEFAULT_MODEL,
    AgentResult,
    _execute_tool_with_guardrails,
    _preview,
    _resolve_model_name,
    _save_session_log,
    run_agent,
)
from sakthai.agent.tools import Tool
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


# ---------------------------------------------------------------------------
# _resolve_model_name / _preview helpers
# ---------------------------------------------------------------------------


def test_resolve_model_name_passes_through_explicit_model() -> None:
    assert _resolve_model_name("my-custom-model", "openai") == "my-custom-model"


def test_resolve_model_name_keeps_default_for_anthropic() -> None:
    assert _resolve_model_name(DEFAULT_MODEL, "anthropic") == DEFAULT_MODEL


def test_preview_truncates_long_text_with_ellipsis() -> None:
    text = "word " * 100
    preview = _preview(text, limit=20)
    assert len(preview) == 20
    assert preview.endswith("…")


def test_preview_collapses_whitespace_without_truncating_short_text() -> None:
    assert _preview("a  b\n\tc") == "a b c"


# ---------------------------------------------------------------------------
# _execute_tool_with_guardrails denial paths
# ---------------------------------------------------------------------------


def _recording_tool(calls: list[dict[str, Any]]) -> Tool:
    def handler(args: dict[str, Any], _store: MemoryStore) -> str:
        calls.append(args)
        return "tool ran"

    return Tool("demo", "desc", {}, handler)


def test_pre_execution_deny_blocks_tool_and_returns_reason(store: MemoryStore) -> None:
    calls: list[dict[str, Any]] = []
    policy = GuardrailPolicy(
        pre_rules=[lambda _t, _a, _s: GuardrailResult(GuardrailAction.DENY, reason="nope")],
        post_rules=[],
    )
    output, is_error = _execute_tool_with_guardrails(_recording_tool(calls), {}, store, policy)
    assert is_error
    assert output == "nope"
    assert calls == []


def test_pre_execution_deny_without_reason_uses_default_message(store: MemoryStore) -> None:
    policy = GuardrailPolicy(
        pre_rules=[lambda _t, _a, _s: GuardrailResult(GuardrailAction.DENY)],
        post_rules=[],
    )
    output, is_error = _execute_tool_with_guardrails(_recording_tool([]), {}, store, policy)
    assert is_error
    assert "denied by a pre-execution guardrail" in output


def test_pre_execution_modified_args_are_passed_to_the_tool(store: MemoryStore) -> None:
    calls: list[dict[str, Any]] = []
    policy = GuardrailPolicy(
        pre_rules=[
            lambda _t, a, _s: GuardrailResult(
                GuardrailAction.ALLOW, modified_args={**a, "extra": True}
            )
        ],
        post_rules=[],
    )
    output, is_error = _execute_tool_with_guardrails(
        _recording_tool(calls), {"x": 1}, store, policy
    )
    assert not is_error
    assert output == "tool ran"
    assert calls == [{"x": 1, "extra": True}]


def test_post_execution_deny_replaces_output_with_reason(store: MemoryStore) -> None:
    policy = GuardrailPolicy(
        pre_rules=[],
        post_rules=[
            lambda _t, _a, _o, _e, _s: GuardrailResult(GuardrailAction.ALLOW),
            lambda _t, _a, _o, _e, _s: GuardrailResult(GuardrailAction.DENY, reason="leaked"),
        ],
    )
    output, is_error = _execute_tool_with_guardrails(_recording_tool([]), {}, store, policy)
    assert is_error
    assert output == "leaked"


def test_post_execution_deny_without_reason_uses_default_message(store: MemoryStore) -> None:
    policy = GuardrailPolicy(
        pre_rules=[],
        post_rules=[lambda _t, _a, _o, _e, _s: GuardrailResult(GuardrailAction.DENY)],
    )
    output, is_error = _execute_tool_with_guardrails(_recording_tool([]), {}, store, policy)
    assert is_error
    assert "denied by a post-execution guardrail" in output


# ---------------------------------------------------------------------------
# run_agent edge behavior
# ---------------------------------------------------------------------------


def test_tool_use_stop_reason_without_tool_use_blocks_is_a_pause(store: MemoryStore) -> None:
    client = FakeClient(
        [
            _Resp("tool_use", [_Block(type="text", text="thinking out loud")]),
            _Resp("end_turn", [_Block(type="text", text="done")]),
        ]
    )
    result = run_agent("hi", client=client, store=store, provider="anthropic")
    assert result.text == "done"
    assert result.iterations == 2
    assert result.tool_calls == []


def test_agent_active_env_var_is_restored_after_run(
    store: MemoryStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SAKTHAI_AGENT_ACTIVE", "outer-run")
    client = FakeClient([_Resp("end_turn", [_Block(type="text", text="ok")])])
    run_agent("hi", client=client, store=store, provider="anthropic")
    assert os.environ["SAKTHAI_AGENT_ACTIVE"] == "outer-run"


# ---------------------------------------------------------------------------
# _save_session_log is best-effort
# ---------------------------------------------------------------------------


def test_save_session_log_failure_is_swallowed_and_logged(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    import sakthai.agent.loop as loop_mod

    def _boom() -> None:
        raise RuntimeError("disk full")

    monkeypatch.setattr(loop_mod, "sessions_dir", _boom)
    result = AgentResult(
        text="t", iterations=1, stop_reason="end_turn", tool_calls=[], usage={}, messages=[]
    )
    with caplog.at_level("WARNING", logger="sakthai.agent.loop"):
        _save_session_log("task", "model", [], result)
    assert "Failed to save session log" in caplog.text
