"""Pilot tests for the Textual chat app."""

from __future__ import annotations

import threading
from typing import Any

import pytest
from textual.containers import VerticalScroll
from textual.widgets import Input, Static

import sakthai.agent.tui as tui_mod
from sakthai.agent.loop import AgentResult
from sakthai.agent.tui import SakThaiApp
from sakthai.memory.store import MemoryStore


@pytest.fixture(autouse=True)
def _sandbox_home(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the app's chat-history file writes inside a tmp dir, not ~/.sakthai."""
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path / "home"))


def _app() -> SakThaiApp:
    return SakThaiApp(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="sakthai",
        provider="ollama",
        caveman=None,
        with_skills=(),
        store=MemoryStore(":memory:"),
    )


@pytest.mark.asyncio
async def test_app_mounts_core_widgets() -> None:
    app = _app()
    async with app.run_test() as pilot:
        assert pilot.app.query_one("#conversation", VerticalScroll) is not None
        assert pilot.app.query_one("#compose", Input) is not None
        assert pilot.app.query_one("#status", Static) is not None
    app.store.close()


@pytest.mark.asyncio
async def test_mount_renderable_adds_child_to_conversation() -> None:
    app = _app()
    async with app.run_test() as pilot:
        before = len(pilot.app.query_one("#conversation").children)
        pilot.app.mount_renderable("hello")
        await pilot.pause()
        after = len(pilot.app.query_one("#conversation").children)
        assert after == before + 1
    app.store.close()


async def _type_and_enter(pilot: object, text: str) -> None:
    app = pilot.app  # type: ignore[attr-defined]
    app.query_one("#compose", Input).value = text
    await pilot.press("enter")  # type: ignore[attr-defined]
    await pilot.pause()  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_help_command_mounts_a_panel_and_clears_input() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/help")
        assert len(pilot.app.query_one("#conversation").children) == 1
        assert pilot.app.query_one("#compose", Input).value == ""
    app.store.close()


@pytest.mark.asyncio
async def test_goal_command_sets_goal() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/goal ship it")
        assert pilot.app.goal == "ship it"
    app.store.close()


@pytest.mark.asyncio
async def test_clear_command_empties_conversation() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/help")
        await _type_and_enter(pilot, "/clear")
        assert len(pilot.app.query_one("#conversation").children) == 0
    app.store.close()


@pytest.mark.asyncio
async def test_exit_command_stops_the_app() -> None:
    app = _app()
    async with app.run_test() as pilot:
        await _type_and_enter(pilot, "/exit")
        await pilot.pause()
        assert not pilot.app.is_running
    app.store.close()


def _fake_run_agent_factory(reply: str, tool: bool = False):
    def _fake(task, **kwargs):  # noqa: ANN001, ANN003
        on_event = kwargs.get("on_event")
        on_token = kwargs.get("on_token")
        if tool and on_event:
            on_event("tool_call", {"name": "read_file", "input": {"p": 1}, "output_preview": "ok"})
        if on_token:
            for ch in reply:
                on_token(ch)
        return AgentResult(text=reply, iterations=1, stop_reason="end", messages=[{"role": "x"}])

    return _fake


@pytest.mark.asyncio
async def test_turn_streams_reply_and_records_history(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_factory("hello"))
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause(0.2)
        # user panel + reply widget both present
        assert len(pilot.app.query_one("#conversation").children) >= 2
        assert pilot.app.prior_messages == [{"role": "x"}]
    app.store.close()


@pytest.mark.asyncio
async def test_turn_mounts_tool_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_factory("done", tool=True))
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "use a tool"
        await pilot.press("enter")
        await pilot.pause(0.2)
        texts = [str(c.content) for c in pilot.app.query_one("#conversation").children]  # type: ignore[attr-defined]
        assert any("read_file" in t for t in texts)
    app.store.close()


@pytest.mark.asyncio
async def test_turn_error_is_shown(monkeypatch: pytest.MonkeyPatch) -> None:
    def _boom(task, **kwargs):  # noqa: ANN001, ANN003
        from sakthai.agent.loop import AgentError

        raise AgentError("nope")

    monkeypatch.setattr(tui_mod, "run_agent", _boom)
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause(0.2)
        texts = [str(c.content) for c in pilot.app.query_one("#conversation").children]  # type: ignore[attr-defined]
        assert any("nope" in t for t in texts)
    app.store.close()


def _fake_run_agent_gated(reply: str, gate: threading.Event, messages: list[dict[str, Any]]):
    """A fake ``run_agent`` that blocks on ``gate`` until the test releases it.

    Lets a test deterministically control when the in-flight OS thread
    completes, so races between cancellation/new turns and stale
    completions can be exercised without arbitrary sleeps.
    """

    def _fake(task, **kwargs):  # noqa: ANN001, ANN003
        gate.wait()
        on_token = kwargs.get("on_token")
        if on_token:
            for ch in reply:
                on_token(ch)
        return AgentResult(text=reply, iterations=1, stop_reason="end", messages=messages)

    return _fake


def _patch_completion_probe(app: SakThaiApp) -> threading.Event:
    """Wrap the UI-thread turn-completion targets so a test can deterministically
    observe when a worker thread's completion callback has actually run on the
    UI thread -- including *stale* completions that correctly no-op and would
    otherwise leave no externally observable trace to poll for.

    Textual's ``Worker``/``Task`` bookkeeping is not a reliable proxy for this:
    a cancelled worker's asyncio ``Task`` can resolve to ``CANCELLED`` almost
    immediately, well before the underlying OS thread (blocked in the fake,
    synchronous ``run_agent``) actually wakes up and runs its completion code.
    """
    done = threading.Event()
    original_success = app._apply_turn_success
    original_error = app._apply_turn_error

    def _success(reply: Any, result: Any) -> None:
        original_success(reply, result)
        done.set()

    def _error(reply: Any, exc: Any) -> None:
        original_error(reply, exc)
        done.set()

    app._apply_turn_success = _success  # type: ignore[method-assign]
    app._apply_turn_error = _error  # type: ignore[method-assign]
    return done


async def _wait_for_completion(pilot: Any, done: threading.Event, attempts: int = 200) -> None:
    for _ in range(attempts):
        if done.is_set():
            return
        await pilot.pause(0.01)
    raise AssertionError("timed out waiting for a background turn completion callback")


@pytest.mark.asyncio
async def test_cancel_while_in_flight_ignores_stale_completion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    gate = threading.Event()
    monkeypatch.setattr(
        tui_mod, "run_agent", _fake_run_agent_gated("late reply", gate, [{"role": "late"}])
    )
    app = _app()
    async with app.run_test() as pilot:
        done = _patch_completion_probe(app)

        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause()

        reply = app._active_reply
        assert reply is not None

        app.action_cancel_turn()
        await pilot.pause()

        # Cancelling with a turn in flight must show "cancelled" immediately
        # and must not touch conversation history.
        assert app._active_reply is None
        cancelled_render = str(reply.content)  # type: ignore[attr-defined]
        assert "cancel" in cancelled_render.lower()
        assert app.prior_messages == []

        # Release the blocked thread. Textual can't preempt it, so it now
        # runs its completion code -- which must no-op because `reply` is no
        # longer `self._active_reply`.
        gate.set()
        await _wait_for_completion(pilot, done)

        assert str(reply.content) == cancelled_render  # type: ignore[attr-defined]
        assert app.prior_messages == []
        assert app._active_reply is None
    app.store.close()


@pytest.mark.asyncio
async def test_idle_cancel_does_not_touch_delivered_reply(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_factory("hello"))
    app = _app()
    async with app.run_test() as pilot:
        app.query_one("#compose", Input).value = "hi"
        await pilot.press("enter")
        await pilot.pause(0.2)

        # The turn already completed: no active reply left to cancel.
        assert app._active_reply is None
        delivered = [
            child
            for child in app.query_one("#conversation").children
            if isinstance(child, tui_mod.ReplyView)
        ]
        assert len(delivered) == 1
        rendered_before = str(delivered[0].content)  # type: ignore[attr-defined]
        assert "cancel" not in rendered_before.lower()

        app.action_cancel_turn()
        await pilot.pause()

        assert str(delivered[0].content) == rendered_before  # type: ignore[attr-defined]
    app.store.close()


@pytest.mark.asyncio
async def test_compose_input_disabled_while_turn_active(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """I2: the compose input is disabled for the duration of a turn and
    re-enabled once it completes, so a real user can't double-submit."""
    gate = threading.Event()
    monkeypatch.setattr(tui_mod, "run_agent", _fake_run_agent_gated("done", gate, [{"role": "x"}]))
    app = _app()
    async with app.run_test() as pilot:
        done = _patch_completion_probe(app)
        compose = app.query_one("#compose", Input)

        compose.value = "hi"
        await pilot.press("enter")
        await pilot.pause()
        assert compose.disabled is True

        gate.set()
        await _wait_for_completion(pilot, done)
        await pilot.pause()
        assert compose.disabled is False
    app.store.close()


@pytest.mark.asyncio
async def test_double_submit_keeps_latest_turn_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Latest-turn-wins must hold even when two turns genuinely overlap.

    With I2, the compose Input is disabled (and loses focus) once a turn is
    active, so a real user driving the UI can no longer fire a second
    Input.Submitted while one is in flight -- that's the point of I2. To
    still exercise the underlying overlap-safety invariant (a stale worker's
    completion callback must no-op against a newer active turn), this test
    calls the app's internal ``_submit`` directly, which is what
    ``on_input_submitted`` would have called had the input allowed a second
    real submission. This mirrors how a lingering, un-killable worker thread
    from a previous turn could still race a fresh one at the store layer.
    """
    gate1 = threading.Event()
    gate2 = threading.Event()
    routes = {
        "turn one": (gate1, [{"role": "turn1"}]),
        "turn two": (gate2, [{"role": "turn2"}]),
    }

    def _fake(task, **kwargs):  # noqa: ANN001, ANN003
        gate, messages = routes[task]
        gate.wait()
        return AgentResult(text=task, iterations=1, stop_reason="end", messages=messages)

    monkeypatch.setattr(tui_mod, "run_agent", _fake)
    app = _app()
    async with app.run_test() as pilot:
        done = _patch_completion_probe(app)

        app._submit("turn one")
        await pilot.pause()

        app._submit("turn two")
        await pilot.pause()

        # Release the newer turn first, then the stale one -- ordering must
        # not matter: whichever turn is *current* wins, not whichever
        # finishes last.
        gate2.set()
        await _wait_for_completion(pilot, done)
        done.clear()
        assert app.prior_messages == [{"role": "turn2"}]

        gate1.set()
        await _wait_for_completion(pilot, done)

        assert app.prior_messages == [{"role": "turn2"}]
        assert app._active_reply is None
        assert app.query_one("#compose", Input).disabled is False
    app.store.close()
