# Self-Healing Multi-Agent Recovery Protocol Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an autonomous resilience and recovery framework that intercepts agent execution failures, isolates failing providers via dynamic circuit breakers, buffers failed task payloads in a persistent Dead-Letter Queue (DLQ), and performs atomic SQLite memory rollbacks across all 6 Sak-Family personas.

**Architecture:** Intercept runtime exceptions within the agent execution loop (`agent/loop.py`) using a centralized `SelfHealingSupervisor`. The supervisor classifies errors into `TRANSIENT`, `STATE_CORRUPT`, and `FATAL`, dispatches state rollbacks via `MemorySnapshotManager`, isolates degraded providers using `CircuitBreaker`, queues failed payloads into a persistent SQLite-backed `DeadLetterQueue`, and exposes live incident inspection and one-click replay to the Next.js dashboard.

**Tech Stack:** Python 3.11/3.12, SQLite3 WAL mode, Pydantic/dataclasses, Next.js 15, React 19, TypeScript, Pytest, Tailwind CSS.

**Spec:** [`docs/prds/0001_prd_self_healing_recovery_protocol.md`](file:///home/beern/Sak-Family-Agent/docs/prds/0001_prd_self_healing_recovery_protocol.md)

## Global Constraints

- Python 3.11 and 3.12 compatibility; strictly enforce `mypy` strict type-checking.
- Zero network I/O in unit tests; all memory and DLQ tests must run in hermetic SQLite fixtures (`:memory:` or isolated temp DB).
- Path resolution must use `_resolve_and_validate_path` with ASCII control character rejection.
- Maintain 96% branch coverage floor across all new recovery modules.
- Preserve byte parity between `personas/sakthai/sakthai` and `personas/shared/sakthai` in `test_shared_package_divergence.py`.

---

### Task 1: Incident Data Models & Failure Classifier

**Files:**
- Create: `personas/sakthai/sakthai/healing/models.py`
- Modify: `personas/sakthai/sakthai/healing/__init__.py`
- Test: `tests/test_healing_models.py`

**Interfaces:**
- Consumes: Standard Python `dataclasses` and `enum`.
- Produces: `ErrorSeverity` enum (`TRANSIENT`, `STATE_CORRUPT`, `FATAL`), `CircuitState` enum (`CLOSED`, `OPEN`, `HALF_OPEN`), `IncidentEnvelope` dataclass, `DLQItem` dataclass.

- [ ] **Step 1: Write the failing test for incident models and error classification**
- [ ] **Step 2: Run test to verify it fails (`uv run pytest tests/test_healing_models.py -q`)**
- [ ] **Step 3: Implement `personas/sakthai/sakthai/healing/models.py`**
- [ ] **Step 4: Run test to verify it passes (`uv run pytest tests/test_healing_models.py -q`)**
- [ ] **Step 5: Commit `feat(healing): add incident models and exception classifier`**

---

### Task 2: Persistent Dead-Letter Queue (DLQ) Engine

**Files:**
- Modify: `personas/sakthai/sakthai/healing/dlq.py`
- Test: `tests/test_healing_dlq.py`

**Interfaces:**
- Consumes: `DLQItem`, `IncidentEnvelope` from `sakthai.healing.models`.
- Produces: `DeadLetterQueue` class with `enqueue(item)`, `peek(limit)`, `dequeue(dlq_id)`, `record_retry_attempt(dlq_id)`, `list_dead(limit)`.

- [ ] **Step 1: Write the failing test for SQLite-backed DLQ**
- [ ] **Step 2: Run test to verify it fails (`uv run pytest tests/test_healing_dlq.py -q`)**
- [ ] **Step 3: Implement `personas/sakthai/sakthai/healing/dlq.py`**
- [ ] **Step 4: Run test to verify it passes (`uv run pytest tests/test_healing_dlq.py -q`)**
- [ ] **Step 5: Commit `feat(healing): implement persistent SQLite dead-letter queue engine`**

---

### Task 3: Dynamic Multi-Persona Circuit Breaker

**Files:**
- Create: `personas/sakthai/sakthai/healing/circuit_breaker.py`
- Test: `tests/test_healing_circuit_breaker.py`

**Interfaces:**
- Consumes: `CircuitState` from `sakthai.healing.models`.
- Produces: `DynamicCircuitBreaker` class with `record_success()`, `record_failure()`, `allow_execution()`, `state`, `reset()`.

- [ ] **Step 1: Write failing tests for DynamicCircuitBreaker**
- [ ] **Step 2: Run test to verify it fails (`uv run pytest tests/test_healing_circuit_breaker.py -q`)**
- [ ] **Step 3: Implement `personas/sakthai/sakthai/healing/circuit_breaker.py`**
- [ ] **Step 4: Run test to verify it passes (`uv run pytest tests/test_healing_circuit_breaker.py -q`)**
- [ ] **Step 5: Commit `feat(healing): add dynamic circuit breaker for persona failure isolation`**

---

### Task 4: Point-in-Time SQLite Memory Snapshot & Rollback

**Files:**
- Modify: `personas/sakthai/sakthai/healing/snapshot.py`
- Test: `tests/test_healing_snapshot.py`

**Interfaces:**
- Consumes: SQLite database connection or file path.
- Produces: `MemorySnapshotManager` with `create_checkpoint(db_path, label)`, `rollback(db_path, checkpoint_id)`, `list_checkpoints()`.

- [ ] **Step 1: Write failing tests for MemorySnapshotManager**
- [ ] **Step 2: Run test to verify it fails (`uv run pytest tests/test_healing_snapshot.py -q`)**
- [ ] **Step 3: Implement `personas/sakthai/sakthai/healing/snapshot.py`**
- [ ] **Step 4: Run test to verify it passes (`uv run pytest tests/test_healing_snapshot.py -q`)**
- [ ] **Step 5: Commit `feat(healing): implement point-in-time SQLite memory snapshot and rollback manager`**

---

### Task 5: Self-Healing Supervisor Orchestration & Agent Loop Integration

**Files:**
- Modify: `personas/sakthai/sakthai/healing/supervisor.py`
- Modify: `personas/sakthai/sakthai/agent/loop.py`
- Test: `tests/test_healing_supervisor.py`

**Interfaces:**
- Consumes: `DynamicCircuitBreaker`, `DeadLetterQueue`, `MemorySnapshotManager`, `IncidentEnvelope`.
- Produces: `SelfHealingSupervisor.handle_exception()`, `SelfHealingSupervisor.get_circuit_breaker()`.

- [ ] **Step 1: Write failing tests for SelfHealingSupervisor orchestration**
- [ ] **Step 2: Run test to verify it fails (`uv run pytest tests/test_healing_supervisor.py -q`)**
- [ ] **Step 3: Implement `personas/sakthai/sakthai/healing/supervisor.py`**
- [ ] **Step 4: Run test to verify it passes (`uv run pytest tests/test_healing_supervisor.py -q`)**
- [ ] **Step 5: Commit `feat(healing): orchestrate exception interception and DLQ routing in supervisor`**

---

### Task 6: Next.js Dashboard API & Live Incident Inspector

**Files:**
- Create: `apps/sak_agent_dashboard/src/components/dashboard/panels/IncidentDLQPanel.tsx`
- Modify: `apps/sak_agent_dashboard/src/app/api/recovery/route.ts`
- Test: `apps/sak_agent_dashboard` TypeScript & lint validation.

**Interfaces:**
- Consumes: Next.js API `/api/recovery` (GET incidents/DLQ, POST replay).
- Produces: Visual Incident & Dead-Letter Queue management panel with real-time status and Replay trigger.

- [ ] **Step 1: Implement `apps/sak_agent_dashboard/src/app/api/recovery/route.ts`**
- [ ] **Step 2: Create `apps/sak_agent_dashboard/src/components/dashboard/panels/IncidentDLQPanel.tsx`**
- [ ] **Step 3: Run Next.js dashboard typecheck and lint (`pnpm lint && pnpm typecheck`)**
- [ ] **Step 4: Commit `feat(dashboard): add IncidentDLQPanel and recovery API route`**

---

### Task 7: Full Resilience Integration Suite & Parity Check

**Files:**
- Create: `tests/test_healing_integration.py`
- Modify: `personas/shared/sakthai/` (sync parity)
- Test: `tests/test_shared_package_divergence.py`

**Interfaces:**
- Tests the complete lifecycle: Exception trigger $\to$ Circuit breaker trip $\to$ DLQ buffering $\to$ Memory rollback $\to$ Replay.

- [ ] **Step 1: Write end-to-end resilience integration test**
- [ ] **Step 2: Run test to verify it passes (`uv run pytest tests/test_healing_integration.py tests/test_shared_package_divergence.py -q`)**
- [ ] **Step 3: Commit `test(healing): add end-to-end multi-agent resilience integration test`**
