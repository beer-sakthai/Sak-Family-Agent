# PRD: Self-Healing Multi-Agent Recovery Protocol

## 1. Project Overview

The **Self-Healing Multi-Agent Recovery Protocol** is an autonomous resilience framework designed for the 6-persona multi-agent ecosystem (SakThai, SakKing, SakSee, SakSit, SakJules, SakTan). It detects agent execution anomalies, LLM API timeouts, tool calling crashes, and corrupted memory states in real-time, executing automatic remediation strategies—including dead-letter queue (DLQ) replay, dynamic circuit-breaker isolation, and atomic SQLite state snapshot rollback—without requiring manual operator intervention.

---

## 2. Problem Statement

In autonomous multi-agent pipelines:
1. **Cascading Failures**: When an upstream agent (e.g. SakSee scouting web assets) encounters an unhandled exception or upstream rate limit (HTTP 429), dependent downstream agents (SakSit drafting code, SakKing running audits) fail sequentially or hang indefinitely.
2. **Corrupted Episodic State**: Partial pipeline crashes leave orphan facts or inconsistent multi-turn session state in SQLite memory databases.
3. **Silent Thread Degradation**: Deadlocked worker threads or memory leaks lead to silent agent stalls without automated alerts or dead-letter diagnostics.
4. **Lack of Operational Visibility**: Human operators lack a unified control plane to inspect failed agent payloads, replay dropped messages, or trigger emergency fallback recovery.

---

## 3. Goals

- **Autonomous Error Interception**: Automatically catch, categorize, and isolate runtime exceptions (transient network errors, schema mismatches, guardrail rejections, rate limits) across all 6 personas.
- **Dead-Letter Queue (DLQ) & Intelligent Replay**: Buffer unrecoverable task payloads in a persistent DLQ with exponential backoff and jittered self-healing retry policies.
- **State Snapshot & Transactional Rollback**: Provide point-in-time state checkpointing and automatic rollback for SQLite memory stores (`memory.db`) upon pipeline failure.
- **Circuit Breaker Isolation**: Automatically quarantine degraded LLM providers or failing external tools before they exhaust agent token budgets or cause cascade failures.
- **Visual Recovery Console & Incident Feed**: Expose a real-time Next.js dashboard panel to monitor persona health, inspect DLQ envelopes, trigger manual replays, and broadcast incident alerts to Telegram.

---

## 4. Non-Goals (Out of Scope)

- Modifying core LLM weights or running fine-tuning jobs on failed prompts during runtime.
- Managing low-level hardware or OS kernel restarts outside Python process boundaries.
- Re-architecting legacy single-persona CLI commands (`sakthai run`) into fully distributed microservices.

---

## 5. User Stories

- **As an Autonomous Agent Orchestrator**, I want unhandled tool exceptions to be safely trapped and routed to a Dead-Letter Queue so that the pipeline can continue executing without crashing the entire session.
- **As a System Administrator**, I want a visual Incident & DLQ Inspector on the dashboard so that I can audit failed execution payloads, see error stack traces, and click "Replay" once upstream services recover.
- **As a Persona Execution Engine**, I want state mutations to be committed atomically so that if a multi-step task aborts midway, corrupted facts are rolled back to the pre-execution snapshot.
- **As a DevOps Engineer (SakJules)**, I want Telegram incident alerts to notify me when an agent's circuit breaker trips into `OPEN` state.

---

## 6. Functional Requirements

### Must Have (P0)

- [ ] **Anomaly & Failure Detection Engine (`SelfHealingSupervisor`)**:
  - Intercepts uncaught exceptions in agent tool calls, provider invocations, and workflow step execution.
  - Classifies errors into `TRANSIENT` (retryable), `STATE_CORRUPT` (rollback required), and `FATAL` (quarantine required).
- [ ] **Persistent Dead-Letter Queue (DLQ)**:
  - SQLite/JSON-backed persistent store for failed payloads with metadata (timestamp, persona, error type, retry count, execution context).
  - Exponential backoff policy with maximum 3 automated retry attempts.
- [ ] **Atomic Memory Snapshot & Rollback**:
  - Pre-execution memory checkpoints for critical workflow stages.
  - Rollback capability to restore `facts` and `observations` tables upon critical aborts.
- [ ] **Dynamic Circuit Breaker**:
  - Monitors provider latency and consecutive failure rates.
  - Transitions across `CLOSED` → `OPEN` → `HALF-OPEN` with configurable cooldown intervals (default: 30s).
- [ ] **Next.js Self-Healing Management API**:
  - `/api/recovery/incidents`: GET active incidents, POST replay/resolve actions.
  - `/api/recovery/dlq`: GET DLQ items, POST manual retry or purge.

### Should Have (P1)

- [ ] **Self-Healing Dashboard Panel (`SelfHealingConsole.tsx`)**:
  - Persona Health Status Badges (Healthy, Degraded, Quarantined).
  - DLQ Item Inspector with syntax-highlighted payload viewer and "Replay Now" button.
  - Circuit Breaker toggle switches and live metrics (trip count, error rate).
- [ ] **Real-time Incident Alerts & Telemetry**:
  - SSE telemetry broadcast (`incident_alert`, `self_heal_success`, `circuit_open`).
  - Telegram webhook notification for CRITICAL severity incidents.

### Nice to Have (P2)

- [ ] **Automated Prompt Fallback & Model Degradation**:
  - Gracefully fallback from high-cost models (e.g. `gemini-2.5-pro`) to lightweight models (`gemini-2.5-flash-lite`) when rate limits occur.
- [ ] **Historical Incident Trends & Mean Time to Recovery (MTTR) Analytics**.

---

## 7. Business Invariants

- **Zero Data Inconsistency**: A rolled-back task must never leave dangling facts or orphaned partial records in the SQLite database.
- **Bounded Retry Loops**: No task in the DLQ shall ever be automatically retried more than 3 times (preventing infinite retry storms and token drain).
- **Secret Redaction**: All error logs, stack traces, and DLQ payloads must be scrubbed using `redact_secrets()` before persistence or transmission.
- **Fail-Safe Operation**: If the self-healing subsystem itself encounters an internal exception, it must log the failure and allow the primary runtime to degrade gracefully rather than hard-crashing.

---

## 8. Data Sensitivities

- **API Keys & Credentials**: All `OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, and bearer tokens must be stripped from DLQ stack traces and payloads.
- **User PII**: Personal conversations and private messages stored in session contexts must be masked before displaying in the visual console.

---

## 9. Failure States

| Failure Scenario | Expected Behavior |
|:---|:---|
| **LLM Provider Rate Limit (HTTP 429)** | Circuit breaker trips to `OPEN`, enqueues request to DLQ with exponential backoff (initial 2s, factor 2x), and alerts dashboard. |
| **Tool Execution Crash (Python Exception)** | Traps exception, captures execution snapshot, saves item to DLQ, and yields graceful error message without killing agent runner. |
| **Corrupted SQLite State / Disk Lock** | Write coalescer triggers memory rollback to last known checkpoint and retries in single-writer WAL mode. |
| **DLQ Store Disk Full / Unwritable** | Drops down to bounded in-memory ring buffer (100 items max) and logs urgent emergency diagnostic event. |

---

## 10. Technical Considerations

- **Backend Runtime**: Python 3.11+ async worker with SQLite WAL storage (`~/.sakthai/recovery.db`).
- **Dashboard Runtime**: Next.js 14 (App Router), TypeScript 5.x, TailwindCSS, Lucide Icons, Vitest.
- **Telemetry Protocol**: Server-Sent Events (SSE) via `telemetryBus.ts`.
- **Concurrency Protection**: Thread-safe mutexes for circuit breaker state and in-memory queue management.

---

## 11. UX/Design Considerations

- **Theme Compliance**: Dark-slate aesthetic matching `sak_agent_dashboard` (`bg-slate-900/80`, glassmorphism, accent cyan/emerald/rose badges).
- **Visual State Transitions**:
  - Green pulsing badge for `HEALTHY`.
  - Amber badge with countdown for `CIRCUIT OPEN (RECOVERING in 18s)`.
  - Red badge with badge counter for `DLQ PENDING (3 items)`.
- **Zero-Latency Controls**: Optimistic UI updates when clicking "Replay DLQ Task" or "Reset Circuit".

---

## 12. Success Metrics

- **Zero Unhandled Agent Crashes**: 100% of uncaught agent runtime exceptions captured and routed to DLQ.
- **Automated Recovery Rate**: ≥ 85% of transient network/rate-limit errors successfully self-healed on automated replay.
- **MTTR (Mean Time to Recovery)**: < 15 seconds for automated circuit-breaker resets and DLQ retries.
- **Test Coverage**: ≥ 90% unit test coverage for `SelfHealingSupervisor`, `DeadLetterQueue`, and `CircuitBreaker`.

---

## 13. Open Questions

- [ ] Should manual DLQ replay require administrative API token authorization or inherit standard session bearer authentication? *(Recommendation: Standard session bearer auth)*.
- [ ] Should Telegram incident alerts batch notifications when multiple agents trip simultaneously to prevent spam? *(Recommendation: 5-second rate-limiting window)*.
