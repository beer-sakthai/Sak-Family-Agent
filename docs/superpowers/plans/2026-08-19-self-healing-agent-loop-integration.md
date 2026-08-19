# Self-Healing Agent-Loop Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire the existing `SelfHealingSupervisor` into `run_agent()` so the runtime actually intercepts provider and tool failures, buffers them to the DLQ, isolates degraded providers via the circuit breaker, and rolls back memory on state-corrupting errors — and expose it behind a `sakthai run --heal` / `SAKTHAI_SELF_HEAL` opt-in.

**Architecture:** Add an injectable `supervisor: SelfHealingSupervisor | None` parameter to `run_agent()` (default `None` → behavior unchanged, existing tests stay green). When present, the loop creates one pre-run memory checkpoint, wraps the provider turn (`_agent_turn`) so a raised exception is routed through `supervisor.handle_execution_failure()`, and threads a small `_HealState` context through the tool-dispatch chain so a tool-handler exception is routed the same way. Every supervisor call is wrapped in a fail-safe helper that logs and returns `None` if the supervisor itself raises, so healing can never hard-crash the primary runtime. The CLI gains a `--heal` flag (and `SAKTHAI_SELF_HEAL` env) that constructs a default supervisor and passes it through.

**Tech Stack:** Python 3.11/3.12, SQLite3 WAL, dataclasses, Click, Pytest (hermetic, no network), Ruff, mypy strict.

**Spec:** [`docs/prds/0001_prd_self_healing_recovery_protocol.md`](docs/prds/0001_prd_self_healing_recovery_protocol.md) — this plan implements the PRD's P0 "Anomaly & Failure Detection Engine" interception requirement (§6 Must Have) and the §7 "Fail-Safe Operation" invariant. The `healing/` modules themselves (models, DLQ, circuit breaker, snapshot, supervisor) and the dashboard recovery API/panel are already implemented and committed on `feat/self-healing-recovery-protocol`; the missing piece is that nothing in `agent/loop.py` calls the supervisor.

## Scope

**Already done on the branch (do not re-implement):** `healing/models.py`, `healing/dlq.py`, `healing/circuit_breaker.py`, `healing/snapshot.py`, `healing/supervisor.py`; `tests/test_healing_*.py`; the dashboard `apps/sak_agent_dashboard/src/app/api/recovery/route.ts` + `components/dashboard/panels/IncidentDLQPanel.tsx`; shared-package parity of the `healing/` tree. Verified: `agent/loop.py` contains zero references to `healing` — the supervisor is never invoked.

**In scope (this plan):** the agent-loop + CLI integration that makes the supervisor run, plus its loop-level tests and the parity mirror.

**Out of scope (separate plans):** Telegram incident alerts (PRD §6 P1), SSE telemetry broadcast (PRD §6 P1), prompt-fallback model degradation (PRD §6 P2), MTTR analytics (§6 P2). The dashboard panel already exists; wiring it to live supervisor state is a follow-up.

## Global Constraints

- Python 3.11 and 3.12 compatibility; `mypy` strict over the package (only `sakthai.telegram.*` is exempt — keep all new code strict-clean).
- Zero network I/O in unit tests; all DLQ/snapshot tests use hermetic SQLite under `tmp_path`. Any test that constructs a default `SelfHealingSupervisor()` (which writes `recovery.db`/`snapshots/` under `SAKTHAI_HOME`) must `monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))` first.
- 96% branch coverage floor across the new code paths.
- **Byte-parity is mandatory.** `tests/test_shared_package_divergence.py` has `KNOWN_DIVERGENCES = {}` and `CANONICAL_ONLY = {}` — every `.py` file under `personas/sakthai/sakthai` must be byte-identical to its `personas/shared/sakthai` counterpart. Any edit to `agent/loop.py` or `cli/agent.py` MUST be mirrored into the shared copy in the same task, or `test_no_new_divergence` fails CI.
- Secret redaction stays where it is: `_execute_tool` already runs `redact_secrets` on tool output, and `DeadLetterQueue.enqueue` already redacts payload/error/stack — do not double-redact or bypass.
- **Fail-safe (PRD §7):** the self-healing subsystem must never hard-crash the primary runtime. Every call into the supervisor from `run_agent` goes through a try/except helper; if the supervisor raises, the original runtime exception propagates as if healing were absent.
- **Baseline before Task 1:** the working tree currently has uncommitted modifications to `personas/{sakthai,shared}/sakthai/healing/*.py` and `tests/test_healing_*.py`. Commit or stash them first so each task below produces a clean, reviewable diff:
  ```bash
  uv run pytest tests/test_healing_*.py -q
  git commit -am "feat(healing): finalize recovery module refinements"
  ```
  If that suite is not green, fix it before starting — this plan builds on a green healing suite.

## File Structure

| File | Responsibility |
|------|----------------|
| `personas/sakthai/sakthai/agent/loop.py` (modify) | Add `_HealState` dataclass, `_handle_healing_failure()` fail-safe helper, `supervisor` param to `run_agent`, pre-run checkpoint, provider-turn interception, and `heal` threading through the tool-dispatch chain. |
| `personas/sakthai/sakthai/cli/agent.py` (modify) | Add `--heal` flag + `SAKTHAI_SELF_HEAL` env, construct a default `SelfHealingSupervisor`, pass it to `run_agent`. |
| `personas/shared/sakthai/agent/loop.py` (mirror) | Byte-identical copy of the canonical `loop.py` after Task 1+2. |
| `personas/shared/sakthai/cli/agent.py` (mirror) | Byte-identical copy of the canonical `cli/agent.py` after Task 3. |
| `tests/test_healing_agent_loop.py` (create) | Loop-level tests: provider-failure interception, tool-failure interception, fail-safe. |
| `tests/test_cli_heal.py` (create) | CLI test: `--heal` constructs and passes a non-None supervisor. |
| `tests/test_shared_package_divergence.py` (unchanged) | The parity gate; must stay green after Task 4. |

**Interfaces (consumed from the already-merged `healing/` package — do not change these):**
- `SelfHealingSupervisor(dlq: DeadLetterQueue | None = None, snapshot_mgr: MemorySnapshotManager | None = None)`
- `supervisor.handle_execution_failure(persona: str, action: str, payload: dict, error: Exception, store: Any | None = None, checkpoint_id: str | None = None) -> RecoveryResult`
- `supervisor.snapshot_mgr.create_checkpoint(store: Any, label: str = "task_checkpoint") -> str` (returns `""` on failure)
- `supervisor.get_circuit_breaker(persona: str) -> DynamicCircuitBreaker`; `.allow_execution() -> bool`; `.failure_count: int`; `.state -> CircuitState`
- `RecoveryResult.action_taken: str`, `.remediated: bool`, `.severity: ErrorSeverity` (`.value` is `"transient"|"state_corrupt"|"fatal"`), `.dlq_id: str | None`, `.rolled_back: bool`

---

### Task 1: Provider-turn interception + pre-run checkpoint in `run_agent`

**Files:**
- Modify: `personas/sakthai/sakthai/agent/loop.py` (imports near line 34; new dataclass+helper near `AgentResult` ~line 85; `run_agent` signature ~line 416; body inside the `try:` at ~line 497 and around the `_agent_turn` call at ~line 513)
- Test: `tests/test_healing_agent_loop.py` (create)

**Interfaces:**
- Consumes: `SelfHealingSupervisor`, `RecoveryResult` from `sakthai.healing.supervisor`; `MemoryStore` (already imported).
- Produces: `run_agent(..., supervisor: SelfHealingSupervisor | None = None) -> AgentResult`; module-level `_HealState`, `_handle_healing_failure()`. Later tasks rely on `_HealState` being threaded into the tool-dispatch chain (Task 2).

- [ ] **Step 1: Write the failing test for provider-failure interception**

Create `tests/test_healing_agent_loop.py`:

```python
"""Loop-level tests for self-healing agent-loop integration (no network)."""

from __future__ import annotations

from typing import Any

import pytest

from sakthai.agent import loop as loop
from sakthai.agent.loop import run_agent
from sakthai.healing.dlq import DeadLetterQueue
from sakthai.healing.snapshot import MemorySnapshotManager
from sakthai.healing.supervisor import SelfHealingSupervisor
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
    def __init__(self) -> None:
        self.calls = 0

    def create(self, **kwargs: object) -> _Resp:
        self.calls += 1
        raise Exception("HTTP 429 Too Many Requests")


class FakeClient:
    def __init__(self) -> None:
        self.messages = _Messages()


def _supervisor(tmp_path) -> SelfHealingSupervisor:
    return SelfHealingSupervisor(
        dlq=DeadLetterQueue(db_path=tmp_path / "rec.db"),
        snapshot_mgr=MemorySnapshotManager(backup_dir=tmp_path / "snaps"),
    )


def test_run_agent_heals_provider_failure(store: MemoryStore, tmp_path, monkeypatch) -> None:
    # Bypass the provider retry layer deterministically (repo-sanctioned patch point).
    def _raise_429(*args: Any, **kwargs: Any) -> Any:
        raise Exception("HTTP 429 Too Many Requests")

    monkeypatch.setattr(loop, "_call_anthropic", _raise_429)

    sup = _supervisor(tmp_path)
    result = run_agent(
        "do thing",
        client=FakeClient(),
        store=store,
        provider="anthropic",
        supervisor=sup,
    )

    # The loop aborts gracefully once the breaker opens (3 consecutive failures).
    assert result.stop_reason == "healed"
    assert len(sup.dlq.list_pending(limit=20)) >= 1
    assert sup.get_circuit_breaker("sakthai").failure_count >= 3


def test_run_agent_without_supervisor_is_unchanged(store: MemoryStore, tmp_path, monkeypatch) -> None:
    def _raise_429(*args: Any, **kwargs: Any) -> Any:
        raise Exception("HTTP 429 Too Many Requests")

    monkeypatch.setattr(loop, "_call_anthropic", _raise_429)

    # No supervisor -> pre-existing behavior: the provider error propagates.
    with pytest.raises(Exception, match="429"):
        run_agent("do thing", client=FakeClient(), store=store, provider="anthropic")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_healing_agent_loop.py -q`
Expected: FAIL — `TypeError: run_agent() got an unexpected keyword argument 'supervisor'` (or import/attribute error).

- [ ] **Step 3: Implement the provider-turn interception**

In `personas/sakthai/sakthai/agent/loop.py`:

(a) Add the healing import with the other `from ..` imports (after `from ..auth import get_credential_source`):

```python
from ..healing.supervisor import RecoveryResult, SelfHealingSupervisor
```

(b) Add the `_HealState` dataclass and the fail-safe helper immediately after the `AgentResult` dataclass (after line ~83):

```python
@dataclass
class _HealState:
    """Per-run healing context: the supervisor plus the pre-run memory checkpoint."""

    supervisor: SelfHealingSupervisor
    persona: str
    checkpoint_id: str | None = None


def _handle_healing_failure(
    heal: _HealState,
    store: MemoryStore,
    *,
    action: str,
    payload: dict[str, Any],
    error: Exception,
) -> RecoveryResult | None:
    """Route a runtime failure through the supervisor.

    Returns ``None`` if the supervisor itself raised, so the caller can fall back
    to the pre-healing behavior (re-raise the original error) — fail-safe per PRD §7.
    """
    try:
        return heal.supervisor.handle_execution_failure(
            persona=heal.persona,
            action=action,
            payload=payload,
            error=error,
            store=store,
            checkpoint_id=heal.checkpoint_id,
        )
    except Exception as exc:  # noqa: BLE001 — healing must not crash the run
        logger.error("Self-healing supervisor raised handling %r: %s", action, exc)
        return None
```

(c) Add the `supervisor` parameter to `run_agent` (append after `persona: str | None = None,` in the signature):

```python
    supervisor: SelfHealingSupervisor | None = None,
```

(d) Build the `_HealState` (with pre-run checkpoint) inside the `try:` block, just before `for iteration in range(1, max_iterations + 1):`:

```python
        heal: _HealState | None = None
        if supervisor is not None:
            persona_key = persona or "sakthai"
            try:
                checkpoint_id = supervisor.snapshot_mgr.create_checkpoint(
                    store, label="run_agent"
                )
            except Exception as exc:  # noqa: BLE001 — fail-safe
                logger.warning("Healing checkpoint failed (continuing without): %s", exc)
                checkpoint_id = None
            heal = _HealState(
                supervisor=supervisor, persona=persona_key, checkpoint_id=checkpoint_id
            )
```

(e) Wrap the `_agent_turn(...)` call (the block currently at ~lines 513–525) in a try/except that routes provider failures through healing:

```python
            try:
                response = _agent_turn(
                    provider,
                    client,
                    model,
                    system,
                    tools,
                    messages,
                    iteration,
                    on_token,
                    max_tokens,
                    tool_schemas,
                    usage_tracker,
                )
            except Exception as exc:
                if heal is None:
                    raise
                recovery = _handle_healing_failure(
                    heal,
                    store,
                    action="provider_turn",
                    payload={"iteration": iteration},
                    error=exc,
                )
                if recovery is None:
                    raise  # supervisor broke; preserve the original runtime error
                notify(
                    "heal",
                    {
                        "action": recovery.action_taken,
                        "severity": recovery.severity.value,
                        "dlq_id": recovery.dlq_id,
                    },
                )
                # Transient and the breaker still admits calls: let the model retry.
                if (
                    recovery.severity.value == "transient"
                    and heal.supervisor.get_circuit_breaker(heal.persona).allow_execution()
                ):
                    messages.append(
                        {
                            "role": "assistant",
                            "content": f"[recovery] provider call failed ({recovery.severity.value}); retrying.",
                        }
                    )
                    continue
                final_text = (
                    f"[recovery] agent run aborted after self-healing: {recovery.action_taken}"
                )
                result = AgentResult(
                    text=final_text,
                    iterations=iteration,
                    stop_reason="healed",
                    tool_calls=tool_calls,
                    usage=usage_tracker.to_dict(),
                    messages=[*messages],
                )
                _save_session_log(task, model, messages, result)
                _record_run_eval(iteration, "healed", had_error=True)
                return result
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_healing_agent_loop.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Lint + type-check the changed module**

Run: `uv run ruff check personas/sakthai/sakthai/agent/loop.py tests/test_healing_agent_loop.py && uv run mypy personas/sakthai/sakthai/agent/loop.py`
Expected: clean (ruff 0 errors; mypy strict clean).

- [ ] **Step 6: Commit**

```bash
git add personas/sakthai/sakthai/agent/loop.py tests/test_healing_agent_loop.py
git commit -m "feat(healing): intercept provider failures in run_agent via SelfHealingSupervisor"
```

---

### Task 2: Tool-execution interception

**Files:**
- Modify: `personas/sakthai/sakthai/agent/loop.py` (`_execute_tool` ~line 217, `_execute_tool_with_guardrails` ~line 230, `_process_tool_uses` ~line 289, `_dispatch_tool_calls` ~line 336, and the `_dispatch_tool_calls` call site in `run_agent` ~line 571)
- Test: `tests/test_healing_agent_loop.py` (append)

**Interfaces:**
- Consumes: `_HealState`, `_handle_healing_failure` from Task 1.
- Produces: `heal: _HealState | None = None` parameter on `_execute_tool`, `_execute_tool_with_guardrails`, `_process_tool_uses`, `_dispatch_tool_calls`.

- [ ] **Step 1: Write the failing test for tool-failure interception**

Append to `tests/test_healing_agent_loop.py`:

```python
from sakthai.agent.tools import Tool


def test_run_agent_heals_tool_failure(store: MemoryStore, tmp_path) -> None:
    def _boom(args: dict[str, Any], _store: MemoryStore) -> str:
        raise RuntimeError("tool crashed")

    boom = Tool(
        name="boom",
        description="always fails",
        input_schema={"type": "object", "properties": {}},
        handler=_boom,
    )

    client = FakeClient(
        [
            _Resp("tool_use", [_Block(type="tool_use", id="t1", name="boom", input={})]),
            _Resp("end_turn", [_Block(type="text", text="recovered")]),
        ]
    )
    # FakeClient needs a responses list for the tool path; rebuild it with one:
    class _OKMessages:
        def __init__(self, responses: list) -> None:
            self._responses = responses
            self.calls = 0

        def create(self, **kwargs: object) -> _Resp:
            resp = self._responses[self.calls]
            self.calls += 1
            return resp

    class _FakeClient:
        def __init__(self, responses: list) -> None:
            self.messages = _OKMessages(responses)

    sup = _supervisor(tmp_path)
    result = run_agent(
        "run boom",
        client=_FakeClient(
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

    # The loop continued after the healed tool failure and reached the final answer.
    assert result.text == "recovered"
    pending = sup.dlq.list_pending(limit=10)
    assert len(pending) == 1
    assert pending[0].action == "boom"
    assert sup.get_circuit_breaker("sakthai").failure_count == 1
```

(Replace the earlier `FakeClient`/`_Messages` used in Task 1 with the responses-list form above, or keep both — the tool test uses `_FakeClient` with two responses. Use whichever name is consistent in the file; the principle is a responses-list fake client.)

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_healing_agent_loop.py::test_run_agent_heals_tool_failure -q`
Expected: FAIL — the tool error is swallowed by `_execute_tool` and reported to the model, but `sup.dlq` is empty because the supervisor is never called from the tool path.

- [ ] **Step 3: Thread `heal` through the tool-dispatch chain and route tool failures**

In `personas/sakthai/sakthai/agent/loop.py`:

(a) `_execute_tool` — add `heal: _HealState | None = None` and route the exception:

```python
def _execute_tool(
    tool: Tool, args: dict[str, Any], store: MemoryStore, heal: _HealState | None = None
) -> tuple[str, bool]:
    """Run a tool, returning (output, is_error). Errors are reported, not raised."""
    try:
        output = tool.handler(args, store)
        return redact_secrets(output), False
    except Exception as exc:  # noqa: BLE001 — surfaced back to the model
        logger.debug("Tool %r raised %s: %s", tool.name, type(exc).__name__, exc)
        if heal is not None:
            _handle_healing_failure(
                heal, store, action=tool.name, payload=args, error=exc
            )
        return redact_secrets(f"{type(exc).__name__}: {exc}"), True
```

(b) `_execute_tool_with_guardrails` — add `heal: _HealState | None = None` and pass it to `_execute_tool`:

```python
def _execute_tool_with_guardrails(
    tool: Tool,
    args: dict[str, Any],
    store: MemoryStore,
    policy: GuardrailPolicy,
    heal: _HealState | None = None,
) -> tuple[str, bool]:
    ...
    output, is_error = _execute_tool(tool, final_args, store, heal)
    ...
```

(c) `_process_tool_uses` — add `heal: _HealState | None = None` and pass it to `_execute_tool_with_guardrails`:

```python
def _process_tool_uses(
    tool_uses: list[Any],
    registry: ToolRegistry,
    store: MemoryStore,
    notify: Callable[[str, dict[str, Any]], None],
    tool_calls: list[dict[str, Any]],
    policy: GuardrailPolicy,
    heal: _HealState | None = None,
) -> list[dict[str, Any]]:
    ...
    output, is_error = _execute_tool_with_guardrails(tool, args, store, policy, heal)
    ...
```

(d) `_dispatch_tool_calls` — add `heal: _HealState | None = None` and pass it to `_process_tool_uses`:

```python
def _dispatch_tool_calls(
    response: Any,
    messages: list[dict[str, Any]],
    registry: ToolRegistry,
    store: MemoryStore,
    notify: Callable[[str, dict[str, Any]], None],
    tool_calls: list[dict[str, Any]],
    policy: GuardrailPolicy,
    heal: _HealState | None = None,
) -> None:
    ...
    results = _process_tool_uses(tool_uses, registry, store, notify, tool_calls, policy, heal)
    ...
```

(e) The call site in `run_agent` (currently `_dispatch_tool_calls(response, messages, registry, store, notify, tool_calls, policy)`) — append `heal`:

```python
            _dispatch_tool_calls(response, messages, registry, store, notify, tool_calls, policy, heal)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_healing_agent_loop.py -q`
Expected: PASS (all tests in the file).

- [ ] **Step 5: Lint + type-check**

Run: `uv run ruff check personas/sakthai/sakthai/agent/loop.py tests/test_healing_agent_loop.py && uv run mypy personas/sakthai/sakthai/agent/loop.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add personas/sakthai/sakthai/agent/loop.py tests/test_healing_agent_loop.py
git commit -m "feat(healing): route tool-handler failures through SelfHealingSupervisor"
```

---

### Task 3: CLI `--heal` flag + `SAKTHAI_SELF_HEAL` env

**Files:**
- Modify: `personas/sakthai/sakthai/cli/agent.py` (add `--heal` option ~after `--persona`; add `heal` param to `run()`; construct + pass supervisor in the `run_agent` call ~line 321)
- Test: `tests/test_cli_heal.py` (create)

**Interfaces:**
- Consumes: `SelfHealingSupervisor` from `sakthai.healing.supervisor`; `run_agent`'s new `supervisor` param (Task 1).
- Produces: `sakthai run --heal TASK` and `SAKTHAI_SELF_HEAL=1 sakthai run TASK` construct a default supervisor and pass it to `run_agent`.

- [ ] **Step 1: Write the failing test for the `--heal` flag**

Create `tests/test_cli_heal.py`:

```python
"""CLI tests for the --heal flag on `sakthai run`."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from sakthai.cli import agent as cli_agent
from sakthai.agent.loop import AgentResult


def test_run_heal_flag_constructs_supervisor(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))  # hermetic recovery.db/snapshots

    captured: dict = {}

    def _spy_run_agent(*args, **kwargs) -> AgentResult:
        captured["supervisor"] = kwargs.get("supervisor")
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn")

    monkeypatch.setattr(cli_agent, "run_agent", _spy_run_agent)

    runner = CliRunner()
    result = runner.invoke(cli_agent.run, ["--heal", "--no-mcp", "do thing"])

    assert result.exit_code == 0, result.output
    assert captured["supervisor"] is not None


def test_run_without_heal_passes_no_supervisor(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path))

    captured: dict = {}

    def _spy_run_agent(*args, **kwargs) -> AgentResult:
        captured["supervisor"] = kwargs.get("supervisor")
        return AgentResult(text="ok", iterations=1, stop_reason="end_turn")

    monkeypatch.setattr(cli_agent, "run_agent", _spy_run_agent)

    runner = CliRunner()
    result = runner.invoke(cli_agent.run, ["--no-mcp", "do thing"])

    assert result.exit_code == 0, result.output
    assert captured["supervisor"] is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli_heal.py -q`
Expected: FAIL — `--heal` is not a recognized option (`no such option: --heal`).

- [ ] **Step 3: Add the `--heal` flag and wire the supervisor**

In `personas/sakthai/sakthai/cli/agent.py`:

(a) Add the option after the `--persona` option block (before `def run(`):

```python
@click.option(
    "--heal",
    is_flag=True,
    help=(
        "Enable the self-healing supervisor: intercept provider/tool failures, "
        "buffer them to the DLQ (~/.sakthai/recovery.db), isolate degraded "
        "providers via a per-persona circuit breaker, and roll back memory on "
        "state-corrupting errors."
    ),
)
```

(b) Add `heal: bool,` to the `run(...)` parameter list (after `persona: str | None,`).

(c) Construct the supervisor and pass it to `run_agent`. Just before the `try:` block that calls `run_agent` (after `system_prompt_prefix = ...`), add:

```python
    heal_enabled = heal or bool(os.environ.get("SAKTHAI_SELF_HEAL"))
    supervisor = None
    if heal_enabled:
        from ..healing.supervisor import SelfHealingSupervisor

        supervisor = SelfHealingSupervisor()
```

(d) In the `run_agent(...)` call inside the `try:` block, add `supervisor=supervisor,` (after `persona=persona,`).

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_cli_heal.py -q`
Expected: PASS (2 tests).

- [ ] **Step 5: Lint + type-check**

Run: `uv run ruff check personas/sakthai/sakthai/cli/agent.py tests/test_cli_heal.py && uv run mypy personas/sakthai/sakthai/cli/agent.py`
Expected: clean.

- [ ] **Step 6: Commit**

```bash
git add personas/sakthai/sakthai/cli/agent.py tests/test_cli_heal.py
git commit -m "feat(cli): add --heal flag and SAKTHAI_SELF_HEAL env to sakthai run"
```

---

### Task 4: Mirror the changes to the shared package (byte-parity)

**Files:**
- Modify: `personas/shared/sakthai/agent/loop.py` (byte-identical to canonical after Tasks 1+2)
- Modify: `personas/shared/sakthai/cli/agent.py` (byte-identical to canonical after Task 3)
- Verify: `tests/test_shared_package_divergence.py` (unchanged — must pass)

**Interfaces:**
- Consumes: the canonical `loop.py` and `cli/agent.py` as the source of truth.
- Produces: zero divergence between `personas/sakthai/sakthai` and `personas/shared/sakthai` for these two files, so symlinked personas (SakJules, SakTan) get the same self-healing behavior.

- [ ] **Step 1: Confirm the current divergence is non-empty for these two files**

Run: `uv run pytest tests/test_shared_package_divergence.py -q`
Expected: FAIL — `test_no_new_divergence` reports `agent/loop.py` and `cli/agent.py` as unexpected divergences (the canonical copy now has healing wiring; the shared copy does not).

- [ ] **Step 2: Mirror the canonical files into the shared copy**

Copy the two files byte-for-byte (the shared tree is byte-parity by policy; do not edit the shared copy independently):

```bash
cp personas/sakthai/sakthai/agent/loop.py personas/shared/sakthai/agent/loop.py
cp personas/sakthai/sakthai/cli/agent.py personas/shared/sakthai/cli/agent.py
```

- [ ] **Step 3: Verify byte-parity holds**

Run: `uv run pytest tests/test_shared_package_divergence.py -q`
Expected: PASS — `KNOWN_DIVERGENCES` is empty and the two trees now match for these files.

- [ ] **Step 4: Run the guardrails-parity test too (sanity)**

Run: `uv run pytest tests/test_persona_guardrails_parity.py -q`
Expected: PASS (unchanged — guardrails were not touched).

- [ ] **Step 5: Commit**

```bash
git add personas/shared/sakthai/agent/loop.py personas/shared/sakthai/cli/agent.py
git commit -m "feat(healing): sync agent-loop self-healing integration to shared package"
```

---

### Task 5: Fail-safe test + full gate

**Files:**
- Test: `tests/test_healing_agent_loop.py` (append the fail-safe test)
- Verify: the whole suite stays green and the coverage floor holds.

**Interfaces:**
- Consumes: `_handle_healing_failure`'s `None`-on-supervisor-error contract (Task 1).
- Produces: a regression test proving the PRD §7 fail-safe invariant — a broken supervisor does not hard-crash the run or leak its own error.

- [ ] **Step 1: Write the fail-safe test**

Append to `tests/test_healing_agent_loop.py`:

```python
def test_healing_supervisor_failure_is_failsafe(
    store: MemoryStore, tmp_path, monkeypatch
) -> None:
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
```

- [ ] **Step 2: Run the fail-safe test**

Run: `uv run pytest tests/test_healing_agent_loop.py::test_healing_supervisor_failure_is_failsafe -q`
Expected: PASS.

- [ ] **Step 3: Run the full healing + loop + CLI + parity suite**

Run: `uv run pytest tests/test_healing_*.py tests/test_healing_agent_loop.py tests/test_cli_heal.py tests/test_shared_package_divergence.py tests/test_persona_guardrails_parity.py tests/test_agent_loop.py -q`
Expected: PASS (all).

- [ ] **Step 4: Run the repo-wide lint + type-check + full test gate (mirrors ci.yml)**

Run:
```bash
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest tests/ -q
```
Expected: ruff/mypy/bandit clean; pytest passes with coverage at or above the 96% branch floor.

- [ ] **Step 5: Commit**

```bash
git add tests/test_healing_agent_loop.py
git commit -m "test(healing): prove supervisor failure is fail-safe and gate full suite"
```

---

## Self-Review

**1. Spec coverage.** PRD §6 P0 "Anomaly & Failure Detection Engine — intercepts uncaught exceptions in agent tool calls, provider invocations" → Task 1 (provider) + Task 2 (tool). "Classifies errors into TRANSIENT/STATE_CORRUPT/FATAL" → consumed via `classify_exception` inside `handle_execution_failure` (already implemented). "Persistent DLQ" → enqueued by `handle_execution_failure` on every intercepted failure. "Atomic Memory Snapshot & Rollback" → pre-run checkpoint in Task 1, rollback on STATE_CORRUPT inside `handle_execution_failure`. "Dynamic Circuit Breaker" → `get_circuit_breaker` per persona, consulted in the Task 1 retry/abort decision. PRD §7 "Fail-Safe Operation" → Task 5. PRD §7 "Secret Redaction" → already enforced in `_execute_tool`/`DeadLetterQueue.enqueue`; this plan adds no new persistence. **Gaps:** PRD §6 P1 dashboard live-state wiring, Telegram/SSE alerts, §6 P2 prompt fallback and MTTR analytics — explicitly out of scope (separate plans).

**2. Placeholder scan.** No "TBD"/"TODO"/"add error handling". Every code step contains the actual code. The one spot that says "Use whichever name is consistent in the file" (Task 2 Step 1) is a directive to reconcile the two fake-client variants, not a placeholder — the executor picks the responses-list form and keeps the file consistent.

**3. Type consistency.** `_HealState` (Task 1) is referenced as `_HealState | None` in Tasks 1 and 2 with identical spelling. `supervisor: SelfHealingSupervisor | None = None` on `run_agent` (Task 1) matches the CLI pass-through `supervisor=supervisor` (Task 3). `RecoveryResult.severity.value` and `get_circuit_breaker(...).allow_execution()` match the merged `healing/` signatures verified against `main`. `_handle_healing_failure` returns `RecoveryResult | None` and both call sites check `is None` identically.