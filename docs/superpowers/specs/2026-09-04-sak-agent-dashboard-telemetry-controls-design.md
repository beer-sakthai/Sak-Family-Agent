# Design Specification: Sak Agent Dashboard Live Telemetry & Controls

**Date:** 2026-09-04  
**Author:** SakJules (Master of Automation & CI/CD)  
**Status:** Approved for Implementation Planning  
**Target Repository:** `Sak-Family-Agent`  
**Subsystems Affected:**
- Backend API Contracts: `personas/sakthai/sakthai/web/contracts.py`
- Contract Type Generator: `scripts/gen_dashboard_types.py`
- Backend API Builders & Server: `personas/sakthai/sakthai/web/api.py`, `personas/sakthai/sakthai/web/server.py`
- Dashboard Frontend: `apps/sak_agent_dashboard/src/` (Components, Lib, Contracts)
- Verification Suite: `tests/test_web_api.py`, `tests/test_web_server.py`, `apps/sak_agent_dashboard/src/components/*.test.tsx`

---

## 1. Overview & Objectives

The Sak-Family-Agent dashboard (`apps/sak_agent_dashboard`) provides a read-only analytics view over the SakThai agent family's runtime state. While it accurately renders historical session statistics, latency averages, and fact counts, operators currently lack:
1. **Hermes Charge Telemetry**: Visualizing each persona's operational charge (v6 Charge System: Optimal, Active, Low, Critical) and charge history from memory.
2. **Household Growth Cycle Visibility & Controls**: Seeing the current stage of the 6-stage lifecycle (`Dream → Hope → Care → Joy → Trust → Growth`), viewing stage guidance and suggested commands, and advancing the stage.
3. **Workflow Dispatch**: Initiating workflow runs with custom parameters and monitoring status directly from the web interface.
4. **Agent Intercom / Ping**: Sending lightweight latency and responsiveness health pings to any persona.

This specification defines the contract models, backend mutation and query endpoints, TypeScript contract synchronization, and interactive React UI components required to deliver these capabilities while strictly maintaining the 96% CI test coverage floor and zero-drift contract guarantees.

---

## 2. Architecture & Data Contracts

All data models originate in `personas/sakthai/sakthai/web/contracts.py` and compile directly to `apps/sak_agent_dashboard/src/lib/contracts.generated.ts` via `scripts/gen_dashboard_types.py`.

### 2.1 Hermes Charge (v6)

```python
ChargeState = Literal["Optimal", "Active", "Low", "Critical"]

class ChargeReport(TypedDict):
    """Hermes charge state for a persona recorded in memory."""
    persona: str
    level: int                   # Integer 0 to 100
    state: ChargeState           # Optimal (80-100), Active (50-79), Low (20-49), Critical (0-19)
    updated_at: int | None       # Epoch timestamp in seconds

class ChargePayload(TypedDict):
    """All persona charge states and household summary."""
    reports: list[ChargeReport]
    household_average: float
```

### 2.2 Household Growth Cycle (v8)

```python
class CycleStageInfo(TypedDict):
    """Metadata for each stage in the 6-stage cycle."""
    stage: str                   # 'dream', 'hope', 'care', 'joy', 'trust', 'growth'
    number: int                  # 1 to 6
    goal: str
    guidance: str
    commands: list[str]

class CycleStatusPayload(TypedDict):
    """Current cycle position and available stages."""
    current_stage: str
    stages: list[CycleStageInfo]
    next_stage: str
```

### 2.3 Workflow Run & Intercom Ping

```python
class WorkflowRunRequest(TypedDict):
    """Parameters for dispatching a workflow run."""
    workflow_name: str
    persona: str
    params: dict[str, str]

class WorkflowRunResult(TypedDict):
    """Execution status and metadata for a workflow run."""
    run_id: str
    workflow_name: str
    persona: str
    status: Literal["completed", "failed", "running"]
    started_at: int
    completed_at: int | None
    error: str | None

class AgentPingRequest(TypedDict):
    """Payload for checking agent connectivity."""
    persona: str
    message: str

class AgentPingResponse(TypedDict):
    """Response from an agent health ping."""
    persona: str
    status: Literal["ok", "error"]
    latency_ms: float
    reply: str
```

### 2.4 Extended `PersonaSummary`

```python
class PersonaSummary(TypedDict):
    # Existing fields
    name: str
    display_name: str
    provider: str
    model: str
    has_shard: bool
    fact_count: int
    observation_count: int
    runs: int
    errors: int
    avg_latency_ms: float
    input_tokens: int
    output_tokens: int
    last_run_at: int | None
    # New telemetry fields
    charge: ChargeReport | None
    current_stage: str | None
```

---

## 3. Backend Implementation (`web/api.py` & `web/server.py`)

### 3.1 Builders in `web/api.py`
- `build_cycle_payload(store: MemoryStore) -> CycleStatusPayload`: Reads `current_stage` fact from `store` (fallback to `Stage.DREAM`). Loads static metadata from `sakthai.cycle.stages.STAGES`.
- `advance_cycle_stage(store: MemoryStore) -> CycleStatusPayload`: Calls `sakthai.cycle.state.advance_stage(store)` and returns the fresh `CycleStatusPayload`.
- `build_charge_reports(store: MemoryStore) -> ChargePayload`: Queries facts tagged `charge-report` for each persona in `config.PERSONA_NAMES`. Calculates `household_average` and returns reports list.
- `record_charge_report(store: MemoryStore, persona: str, level: int, state: ChargeState) -> ChargeReport`: Appends new memory fact tagged `charge-report` with timestamp.
- `run_workflow_execution(workflow_name: str, persona: str, params: dict[str, str]) -> WorkflowRunResult`: Dispatches workflow runner and records run metadata.
- `ping_agent(persona: str, message: str) -> AgentPingResponse`: Performs health check, verifies provider availability, measures roundtrip latency, and returns reply.

### 3.2 Routing & Security in `web/server.py`
- Endpoints:
  - `GET /api/cycle` -> Open read
  - `POST /api/cycle/advance` -> Requires Bearer token
  - `GET /api/charge` -> Open read
  - `POST /api/charge/update` -> Requires Bearer token
  - `POST /api/workflows/run` -> Requires Bearer token
  - `POST /api/intercom/ping` -> Requires Bearer token
- Token Authentication: Validates `Authorization: Bearer <token>` against `SAKTHAI_API_TOKEN`. Rejects missing/invalid tokens with HTTP 401 Unauthorized.
- Input Validation: Sanitizes persona against `config.PERSONA_NAMES`, enforces alphanumeric workflow names (`^[a-zA-Z0-9_-]+$`), clamps charge levels between 0 and 100.

---

## 4. Frontend Implementation (`apps/sak_agent_dashboard`)

### 4.1 UI Components
1. **`AgentCard.tsx` & `PersonaDrawer.tsx`**:
   - Renders Hermes Charge v6 meter with role-based colors:
     - Optimal: `bg-hue-emerald-tint text-hue-emerald border-hue-emerald-line`
     - Active: `bg-hue-cyan-tint text-hue-cyan border-hue-cyan-line`
     - Low: `bg-hue-amber-tint text-hue-amber border-hue-amber-line`
     - Critical: `bg-hue-rose-tint text-hue-rose border-hue-rose-line`
   - Shows current cycle stage badge and Quick Ping button.
2. **`CycleControlStrip.tsx`**:
   - Displays 6-stage linear pipeline: `Dream → Hope → Care → Joy → Trust → Growth`.
   - Highlights active stage with glowing border and pulsing dot.
   - Shows guidance, goal, and recommended CLI command for the active stage.
   - Includes "Advance Stage" button with optimistic UI update and error rollback.
3. **`WorkflowRunnerModal.tsx`**:
   - Workflow and target persona selectors.
   - Dynamic parameter input fields.
   - Execution status display.
4. **`AgentIntercomModal.tsx`**:
   - Interactive prompt test with roundtrip latency counter in milliseconds.
5. **`lib/demo.ts`**:
   - Provides mock data for cycle status, charge reports, and simulated dispatches for standalone demo mode.

---

## 5. Verification & Testing Strategy

1. **Python Unit & Integration Tests**:
   - `tests/test_web_api.py`: Verify cycle builders, charge builders, workflow dispatch, and ping handlers.
   - `tests/test_web_server.py`: Verify HTTP status codes, routing, and Bearer token auth enforcement.
   - Coverage verification: Ensure coverage remains `>= 96%` (`--cov-fail-under=96`).
2. **Contract Type Generation**:
   - Run `python3 scripts/gen_dashboard_types.py`.
   - Confirm `git diff --exit-code apps/sak_agent_dashboard/src/lib/contracts.generated.ts` is clean.
3. **Frontend Tests & Linting**:
   - Vitest component tests for new UI controls.
   - Run `npm run lint`, `npx tsc --noEmit`, and `npm test` inside `apps/sak_agent_dashboard`.
