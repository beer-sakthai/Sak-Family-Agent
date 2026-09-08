# Sak Agent Dashboard Live Telemetry & Controls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate Hermes charge telemetry (v6), household lifecycle controls (`Dream → Growth`), live workflow dispatch, and an agent health ping intercom into the Sak Agent Dashboard and web API.

**Architecture:** Extend the Python web contracts (`contracts.py`) as the single source of truth, compile types to Next.js (`contracts.generated.ts`), implement authenticated mutation & query endpoints in `web/api.py` and `web/server.py`, and build modular React 19 components in `apps/sak_agent_dashboard`.

**Tech Stack:** Python 3.11+, Pytest, Next.js 16 (App Router), React 19, TypeScript 6, Tailwind CSS 3 (semantic token roles), Vitest, Lucide Icons.

**Spec:** [`docs/superpowers/specs/2026-09-04-sak-agent-dashboard-telemetry-controls-design.md`](../specs/2026-09-04-sak-agent-dashboard-telemetry-controls-design.md)

## Global Constraints

- Python version: 3.11+
- Test coverage floor: strictly >= 96% (`--cov-fail-under=96`)
- Contracts source of truth: `personas/sakthai/sakthai/web/contracts.py`
- Zero type drift: `python3 scripts/gen_dashboard_types.py --check` must exit 0
- Styling: Semantic token classes (`bg-panel`, `text-fg-*`, `bg-hue-*-tint`, `border-hue-*-line`), never hardcoded hex codes
- Auth: Mutating POST endpoints strictly require `Authorization: Bearer <token>`
- Demo Mode: `lib/demo.ts` must provide mock data so the dashboard functions standalone without backend

---

### Task 1: Python Web Contracts & TypeScript Type Generator

**Files:**
- Modify: `personas/sakthai/sakthai/web/contracts.py`
- Modify: `scripts/gen_dashboard_types.py`
- Generate: `apps/sak_agent_dashboard/src/lib/contracts.generated.ts`
- Test: `tests/test_web_contracts.py`

**Interfaces:**
- Consumes: `PERSONA_NAMES` from `sakthai.config`
- Produces:
  - `ChargeState = Literal["Optimal", "Active", "Low", "Critical"]`
  - `ChargeReport`: `{ persona: str, level: int, state: ChargeState, updated_at: int | None }`
  - `ChargePayload`: `{ reports: list[ChargeReport], household_average: float }`
  - `CycleStageInfo`: `{ stage: str, number: int, goal: str, guidance: str, commands: list[str] }`
  - `CycleStatusPayload`: `{ current_stage: str, stages: list[CycleStageInfo], next_stage: str }`
  - `WorkflowRunRequest`: `{ workflow_name: str, persona: str, params: dict[str, str] }`
  - `WorkflowRunResult`: `{ run_id: str, workflow_name: str, persona: str, status: Literal["completed", "failed", "running"], started_at: int, completed_at: int | None, error: str | None }`
  - `AgentPingRequest`: `{ persona: str, message: str }`
  - `AgentPingResponse`: `{ persona: str, status: Literal["ok", "error"], latency_ms: float, reply: str }`
  - Extended `PersonaSummary`: includes `charge: ChargeReport | None` and `current_stage: str | None`

- [ ] **Step 1: Write the failing test for new contract types**

In `tests/test_web_contracts.py`:
```python
from sakthai.web.contracts import (
    ChargeReport,
    ChargePayload,
    CycleStageInfo,
    CycleStatusPayload,
    WorkflowRunRequest,
    WorkflowRunResult,
    AgentPingRequest,
    AgentPingResponse,
    PersonaSummary,
)


def test_new_contract_types_exist():
    assert "charge" in PersonaSummary.__annotations__
    assert "current_stage" in PersonaSummary.__annotations__
    assert "level" in ChargeReport.__annotations__
    assert "current_stage" in CycleStatusPayload.__annotations__
    assert "workflow_name" in WorkflowRunRequest.__annotations__
    assert "latency_ms" in AgentPingResponse.__annotations__
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_web_contracts.py -v`  
Expected: FAIL with `ImportError: cannot import name 'ChargeReport'`

- [ ] **Step 3: Implement contract definitions in `contracts.py` and update generator**

In `personas/sakthai/sakthai/web/contracts.py`:
Add `ChargeState`, `ChargeReport`, `ChargePayload`, `CycleStageInfo`, `CycleStatusPayload`, `WorkflowRunRequest`, `WorkflowRunResult`, `AgentPingRequest`, `AgentPingResponse`.
Add them to `__all__`.
Add `charge: ChargeReport | None` and `current_stage: str | None` to `PersonaSummary`.

Run: `python3 scripts/gen_dashboard_types.py`

- [ ] **Step 4: Run test to verify it passes and check generator**

Run: `uv run pytest tests/test_web_contracts.py -v`  
Run: `python3 scripts/gen_dashboard_types.py --check`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add personas/sakthai/sakthai/web/contracts.py scripts/gen_dashboard_types.py apps/sak_agent_dashboard/src/lib/contracts.generated.ts tests/test_web_contracts.py
git commit -m "feat(contracts): add telemetry and control types and regenerate TypeScript contracts"
```

---

### Task 2: Backend API Builders (`web/api.py`)

**Files:**
- Modify: `personas/sakthai/sakthai/web/api.py`
- Test: `tests/test_web_api.py`

**Interfaces:**
- Consumes: `MemoryStore`, `sakthai.cycle.stages`, `sakthai.cycle.state`, `sakthai.config.PERSONA_NAMES`
- Produces:
  - `build_cycle_payload(store: MemoryStore) -> CycleStatusPayload`
  - `advance_cycle_stage(store: MemoryStore) -> CycleStatusPayload`
  - `build_charge_reports(store: MemoryStore) -> ChargePayload`
  - `record_charge_report(store: MemoryStore, persona: str, level: int, state: ChargeState) -> ChargeReport`
  - `run_workflow_execution(workflow_name: str, persona: str, params: dict[str, str]) -> WorkflowRunResult`
  - `ping_agent(persona: str, message: str) -> AgentPingResponse`

- [ ] **Step 1: Write failing tests for builders in `tests/test_web_api.py`**

```python
def test_build_cycle_payload_and_advance(tmp_path):
    from sakthai.memory.store import MemoryStore
    from sakthai.web.api import build_cycle_payload, advance_cycle_stage
    store = MemoryStore(str(tmp_path / "memory.db"))
    payload = build_cycle_payload(store)
    assert payload["current_stage"] == "dream"
    assert len(payload["stages"]) == 6
    assert payload["next_stage"] == "hope"

    advanced = advance_cycle_stage(store)
    assert advanced["current_stage"] == "hope"
    assert advanced["next_stage"] == "care"


def test_build_and_record_charge(tmp_path):
    from sakthai.memory.store import MemoryStore
    from sakthai.web.api import build_charge_reports, record_charge_report
    store = MemoryStore(str(tmp_path / "memory.db"))
    record_charge_report(store, "sakjules", 85, "Optimal")
    charge_payload = build_charge_reports(store)
    jules_report = next(r for r in charge_payload["reports"] if r["persona"] == "sakjules")
    assert jules_report["level"] == 85
    assert jules_report["state"] == "Optimal"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_web_api.py -k "test_build_cycle_payload_and_advance or test_build_and_record_charge" -v`  
Expected: FAIL with `ImportError: cannot import name 'build_cycle_payload'`

- [ ] **Step 3: Implement builders in `web/api.py`**

In `personas/sakthai/sakthai/web/api.py`:
- Implement `build_cycle_payload` and `advance_cycle_stage` using `sakthai.cycle.state` and `sakthai.cycle.stages`.
- Implement `build_charge_reports` querying memory facts tagged `charge-report`.
- Implement `record_charge_report` persisting charge state fact.
- Implement `run_workflow_execution` and `ping_agent`.
- In `build_persona_summary`, populate `charge` and `current_stage`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_web_api.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add personas/sakthai/sakthai/web/api.py tests/test_web_api.py
git commit -m "feat(web/api): implement cycle, charge, workflow, and ping payload builders"
```

---

### Task 3: Backend HTTP Routing & Security (`web/server.py`)

**Files:**
- Modify: `personas/sakthai/sakthai/web/server.py`
- Test: `tests/test_web_server.py`

**Interfaces:**
- Consumes: Builders from `sakthai.web.api`, `SAKTHAI_API_TOKEN`
- Produces:
  - `GET /api/cycle`, `POST /api/cycle/advance`
  - `GET /api/charge`, `POST /api/charge/update`
  - `POST /api/workflows/run`
  - `POST /api/intercom/ping`

- [ ] **Step 1: Write failing tests for route dispatch and authentication**

In `tests/test_web_server.py`:
```python
def test_post_endpoints_require_auth(client):
    res = client.post("/api/cycle/advance")
    assert res.status_code == 401
    assert res.json() == {"error": "Unauthorized"}

    res = client.post("/api/charge/update", json={"persona": "sakjules", "level": 90, "state": "Optimal"})
    assert res.status_code == 401


def test_post_endpoints_succeed_with_auth(client, auth_headers):
    res = client.post("/api/cycle/advance", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["ok"] is True
    assert "data" in res.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_web_server.py -k "test_post_endpoints_require_auth" -v`  
Expected: FAIL with 404 Not Found

- [ ] **Step 3: Implement routes and Bearer auth checks in `web/server.py`**

In `personas/sakthai/sakthai/web/server.py`:
- Add handler functions `_handle_cycle`, `_handle_cycle_advance`, `_handle_charge`, `_handle_charge_update`, `_handle_workflow_run`, `_handle_intercom_ping`.
- Protect mutating handlers with `_require_auth(request)`.
- Validate persona names with `config.PERSONA_NAMES`.
- Validate workflow names with `^[a-zA-Z0-9_-]+$`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_web_server.py -v`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add personas/sakthai/sakthai/web/server.py tests/test_web_server.py
git commit -m "feat(web/server): add authenticated cycle, charge, workflow, and ping HTTP routes"
```

---

### Task 4: Frontend Data Layer & Source Implementations

**Files:**
- Modify: `apps/sak_agent_dashboard/src/lib/source.ts`
- Modify: `apps/sak_agent_dashboard/src/lib/sources/api.ts`
- Modify: `apps/sak_agent_dashboard/src/lib/sources/demo.ts`
- Modify: `apps/sak_agent_dashboard/src/lib/demo.ts`
- Create: `apps/sak_agent_dashboard/src/app/api/cycle/route.ts`
- Create: `apps/sak_agent_dashboard/src/app/api/charge/route.ts`
- Create: `apps/sak_agent_dashboard/src/app/api/intercom/route.ts`
- Create: `apps/sak_agent_dashboard/src/app/api/workflows/run/route.ts`

**Interfaces:**
- Consumes: `DashboardSource` in `lib/source.ts`
- Produces:
  - `getCycle(): Promise<CycleStatusPayload>`
  - `advanceCycle(): Promise<CycleStatusPayload>`
  - `getCharge(): Promise<ChargePayload>`
  - `updateCharge(persona: string, level: number): Promise<ChargeReport>`
  - `runWorkflow(request: WorkflowRunRequest): Promise<WorkflowRunResult>`
  - `pingAgent(request: AgentPingRequest): Promise<AgentPingResponse>`

- [ ] **Step 1: Write Vitest test for new source methods in `apps/sak_agent_dashboard`**

In `apps/sak_agent_dashboard/src/lib/source.test.ts`:
```typescript
import { describe, it, expect } from "vitest";
import { DemoSource } from "./sources/demo";

describe("DemoSource live telemetry methods", () => {
  it("returns mock cycle state and advances stage", async () => {
    const source = new DemoSource();
    const cycle = await source.getCycle();
    expect(cycle.current_stage).toBeDefined();
    expect(cycle.stages.length).toBe(6);

    const advanced = await source.advanceCycle();
    expect(advanced.current_stage).toBe(cycle.next_stage);
  });

  it("returns mock charge payload", async () => {
    const source = new DemoSource();
    const charge = await source.getCharge();
    expect(charge.reports.length).toBe(6);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sak_agent_dashboard && npx vitest run src/lib/source.test.ts`  
Expected: FAIL with TypeScript/Runtime error on `getCycle`

- [ ] **Step 3: Implement methods on `DashboardSource`, `ApiSource`, `DemoSource`, and Next.js route handlers**

Update `src/lib/source.ts`, `src/lib/sources/api.ts`, `src/lib/sources/demo.ts`, `src/lib/demo.ts`.
Create route handlers under `src/app/api/cycle/route.ts`, `src/app/api/charge/route.ts`, `src/app/api/intercom/route.ts`, `src/app/api/workflows/run/route.ts`.

- [ ] **Step 4: Run test to verify it passes**

Run: `cd apps/sak_agent_dashboard && npx vitest run src/lib/source.test.ts`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sak_agent_dashboard/src/lib/ apps/sak_agent_dashboard/src/app/api/
git commit -m "feat(dashboard/data): add cycle, charge, workflow, and intercom methods to data layer"
```

---

### Task 5: Frontend UI: Hermes Charge & Household Cycle Control Strip

**Files:**
- Create: `apps/sak_agent_dashboard/src/components/CycleControlStrip.tsx`
- Modify: `apps/sak_agent_dashboard/src/components/AgentCard.tsx`
- Modify: `apps/sak_agent_dashboard/src/components/PersonaDrawer.tsx`
- Modify: `apps/sak_agent_dashboard/src/components/AgentOverview.tsx`
- Test: `apps/sak_agent_dashboard/src/components/CycleControlStrip.test.tsx`

**Interfaces:**
- Consumes: `CycleStatusPayload`, `PersonaSummary` with `charge` and `current_stage`
- Produces: Interactive visual cycle stepper and charge badge meter.

- [ ] **Step 1: Write failing component test for `CycleControlStrip`**

In `apps/sak_agent_dashboard/src/components/CycleControlStrip.test.tsx`:
```typescript
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { CycleControlStrip } from "./CycleControlStrip";

describe("CycleControlStrip", () => {
  const mockCycle = {
    current_stage: "care",
    next_stage: "joy",
    stages: [
      { stage: "dream", number: 1, goal: "Define vision", guidance: "Explore", commands: ["memory show"] },
      { stage: "hope", number: 2, goal: "Engineer solution", guidance: "Propose", commands: ["learn"] },
      { stage: "care", number: 3, goal: "Audit correctness", guidance: "Refine", commands: ["learn"] },
      { stage: "joy", number: 4, goal: "Package & ship", guidance: "Focus CI", commands: ["memory stats"] },
      { stage: "trust", number: 5, goal: "Secure foundation", guidance: "Doctor", commands: ["doctor"] },
      { stage: "growth", number: 6, goal: "Learn & grow", guidance: "Consolidate", commands: ["memory consolidate"] },
    ],
  };

  it("renders all 6 stages with active care stage", () => {
    render(<CycleControlStrip cycle={mockCycle} onAdvance={vi.fn()} />);
    expect(screen.getByText("care")).toBeDefined();
    expect(screen.getByText("Audit correctness")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sak_agent_dashboard && npx vitest run src/components/CycleControlStrip.test.tsx`  
Expected: FAIL (component doesn't exist)

- [ ] **Step 3: Implement `CycleControlStrip.tsx` and integrate into `AgentOverview.tsx` and `AgentCard.tsx`**

Implement `CycleControlStrip.tsx`.
Update `AgentCard.tsx` to render the Hermes Charge meter and badge using token classes:
- Optimal: `bg-hue-emerald-tint/50 text-hue-emerald border-hue-emerald-line/40`
- Active: `bg-hue-cyan-tint/50 text-hue-cyan border-hue-cyan-line/40`
- Low: `bg-hue-amber-tint/50 text-hue-amber border-hue-amber-line/40`
- Critical: `bg-hue-rose-tint/50 text-hue-rose border-hue-rose-line/40`

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/sak_agent_dashboard && npx vitest run`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sak_agent_dashboard/src/components/CycleControlStrip.tsx apps/sak_agent_dashboard/src/components/CycleControlStrip.test.tsx apps/sak_agent_dashboard/src/components/AgentCard.tsx apps/sak_agent_dashboard/src/components/PersonaDrawer.tsx apps/sak_agent_dashboard/src/components/AgentOverview.tsx
git commit -m "feat(dashboard/ui): add CycleControlStrip and Hermes charge telemetry to AgentCard"
```

---

### Task 6: Frontend UI: Workflow Runner & Agent Intercom

**Files:**
- Create: `apps/sak_agent_dashboard/src/components/WorkflowRunnerModal.tsx`
- Create: `apps/sak_agent_dashboard/src/components/AgentIntercomModal.tsx`
- Modify: `apps/sak_agent_dashboard/src/components/WorkflowRuns.tsx`
- Test: `apps/sak_agent_dashboard/src/components/WorkflowRunnerModal.test.tsx`
- Test: `apps/sak_agent_dashboard/src/components/AgentIntercomModal.test.tsx`

**Interfaces:**
- Consumes: `runWorkflow` and `pingAgent` from data source
- Produces: Execution modal with status updates and Intercom dialog with latency metric.

- [ ] **Step 1: Write failing component tests**

In `apps/sak_agent_dashboard/src/components/WorkflowRunnerModal.test.tsx`:
```typescript
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";
import { WorkflowRunnerModal } from "./WorkflowRunnerModal";

describe("WorkflowRunnerModal", () => {
  it("renders workflow runner form", () => {
    render(<WorkflowRunnerModal isOpen={true} onClose={() => {}} onRun={async () => {}} />);
    expect(screen.getByText("Run Workflow")).toBeDefined();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd apps/sak_agent_dashboard && npx vitest run src/components/WorkflowRunnerModal.test.tsx`  
Expected: FAIL

- [ ] **Step 3: Implement `WorkflowRunnerModal.tsx` and `AgentIntercomModal.tsx`**

Implement the modals with status indicators, latency measuring, and connect to `WorkflowRuns.tsx` and `AgentCard.tsx`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd apps/sak_agent_dashboard && npx vitest run`  
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add apps/sak_agent_dashboard/src/components/WorkflowRunnerModal.tsx apps/sak_agent_dashboard/src/components/AgentIntercomModal.tsx apps/sak_agent_dashboard/src/components/*.test.tsx apps/sak_agent_dashboard/src/components/WorkflowRuns.tsx
git commit -m "feat(dashboard/ui): add WorkflowRunnerModal and AgentIntercomModal controls"
```

---

### Task 7: Full Repository Verification & CI Gate

**Files:** None modified (verification run)

- [ ] **Step 1: Verify TypeScript contract synchronization**

Run: `python3 scripts/gen_dashboard_types.py --check`  
Expected: clean exit 0

- [ ] **Step 2: Run Ruff lint and formatting check**

Run: `uv run ruff check personas/sakthai/sakthai tests && uv run ruff format --check personas/sakthai/sakthai tests`  
Expected: All checks passed!

- [ ] **Step 3: Run Mypy strict type checking**

Run: `uv run mypy personas/sakthai/sakthai`  
Expected: Success: no issues found

- [ ] **Step 4: Run Bandit security scanner**

Run: `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai`  
Expected: No issues identified

- [ ] **Step 5: Run full Pytest suite with coverage check**

Run: `uv run pytest --cov=sakthai --cov-fail-under=96 tests/`  
Expected: >= 96% coverage, all tests passing

- [ ] **Step 6: Run Next.js dashboard tests, linting, and typecheck**

Run: `cd apps/sak_agent_dashboard && npm run lint && npx tsc --noEmit && npm test`  
Expected: 0 errors, all tests pass
