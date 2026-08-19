"""Loop-level tests for self-healing agent-loop integration (no network)."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.agent import loop as loop
from sakthai.agent.loop import run_agent
from sakthai.agent.tools import Tool
from sakthai.healing.dlq import DeadLetterQueue
from sakthai.healing.snapshot import MemorySnapshotManager
from sakthai.healing.supervisor import SelfHealingSupervisor
from sakthai.memory.store import MemoryStore


class _Block:
    """Minimal stand-in for a provider content block."""

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
        # Providers attach a usage dict; the loop reads it for anthropic via
        # extract_usage, and directly for google/openai. Keep it empty/zeroed.
        self.usage: dict[str, int] = {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }


class _Messages:
    def __init__(self, responses: list) -> None:
        self._responses = responses
        self.calls = 0

    def create(self, **kwargs: object) -> _Resp:
        if self.calls >= len(self._responses):
            raise Exception("HTTP 429 Too Many Requests")
        resp = self._responses[self.calls]
        self.calls += 1
        return resp


class FakeClient:
    """Responses-list fake client. ``client.messages.create`` returns the next
    canned response; once exhausted it raises (so provider-failure tests that
    patch ``_call_anthropic`` never reach it anyway)."""

    def __init__(self, responses: list | None = None) -> None:
        self.messages = _Messages(responses or [])


def _supervisor(tmp_path) -> SelfHealingSupervisor:
    return SelfHealingSupervisor(
        dlq=DeadLetterQueue(db_path=tmp_path / "rec.db"),
        snapshot_mgr=MemorySnapshotManager(backup_dir=tmp_path / "snaps"),
    )


def _raise_429(*args: Any, **kwargs: Any) -> Any:
    raise Exception("HTTP 429 Too Many Requests")


def test_run_agent_heals_provider_failure(store: MemoryStore, tmp_path, monkeypatch) -> None:
    # Bypass the provider retry layer deterministically (repo-sanctioned patch point).
    monkeypatch.setattr(loop, "_call_anthropic", _raise_429)

    sup = _supervisor(tmp_path)
    result = run_agent(
        "do thing",
        client=FakeClient([]),
        store=store,
        provider="anthropic",
        supervisor=sup,
    )

    # The loop aborts gracefully once the per-persona breaker opens (3 failures).
    assert result.stop_reason == "healed"
    assert len(sup.dlq.list_pending(limit=20)) >= 1
    assert sup.get_circuit_breaker("sakthai").failure_count >= 3


def test_run_agent_without_supervisor_is_unchanged(
    store: MemoryStore, tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(loop, "_call_anthropic", _raise_429)

    # No supervisor -> pre-existing behavior: the provider error propagates.
    with pytest.raises(Exception, match="429"):
        run_agent("do thing", client=FakeClient([]), store=store, provider="anthropic")


def test_run_agent_heals_tool_failure(store: MemoryStore, tmp_path) -> None:
    """A tool handler that raises is routed through the supervisor and the run continues."""

    def _boom(args: dict[str, Any], _store: MemoryStore) -> str:
        raise RuntimeError("tool crashed")

    boom = Tool(
        name="boom",
        description="always fails",
        input_schema={"type": "object", "properties": {}},
        handler=_boom,
    )

    sup = _supervisor(tmp_path)
    result = run_agent(
        "run boom",
        client=FakeClient(
            [
                _Resp("tool_use", [_Block(type="tool_use", id="t1", name="boom", input={})]),
                _Resp("end_turn", [_Block(type="text", text="recovered")]),
            ]
        ),
        store=store,
        provider="anthropic",
        tools=(boom,),
        supervisor=sup,
    )

    # The loop continued past the healed tool failure to the final answer.
    assert result.text == "recovered"
    pending = sup.dlq.list_pending(limit=10)
    assert len(pending) == 1
    assert pending[0].action == "boom"
    assert sup.get_circuit_breaker("sakthai").failure_count == 1


def test_healing_supervisor_failure_is_failsafe(store: MemoryStore, tmp_path, monkeypatch) -> None:
    """A supervisor that raises must not crash the run or mask the original error."""

    class _BrokenSupervisor(SelfHealingSupervisor):
        def handle_execution_failure(self, *args, **kwargs):  # type: ignore[override]
            raise RuntimeError("supervisor itself broke")

    def _raise_429(*args: Any, **kwargs: Any) -> Any:
        raise Exception("HTTP 429 Too Many Requests")

    monkeypatch.setattr(loop, "_call_anthropic", _raise_429)

    sup = _BrokenSupervisor(
        dlq=DeadLetterQueue(db_path=tmp_path / "rec.db"),
        snapshot_mgr=MemorySnapshotManager(backup_dir=tmp_path / "snaps"),
    )
    # The original provider error propagates; the supervisor's own error does not.
    with pytest.raises(Exception) as exc_info:
        run_agent(
            "do thing",
            client=FakeClient(),
            store=store,
            provider="anthropic",
            supervisor=sup,
        )
    assert "429" in str(exc_info.value)
    assert "supervisor itself broke" not in str(exc_info.value)
