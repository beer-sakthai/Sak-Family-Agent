# Multi-Agent Telegram & Live Chat Routing Gateway Plan

## Overview
A high-performance routing gateway and cross-persona session manager that intelligently routes incoming user prompts, Telegram messages, and API chat requests across the 6 Sak-Family personas (SakThai, SakKing, SakSee, SakSit, SakJules, SakTan) based on SOUL capabilities, query intent, tool requirements, and persona charge levels.

---

## Global Constraints & Invariants
1. **Persona Isolation & SOUL Compliance:** Every response generated must respect the persona's SOUL identity, charge state, and opening one-liner role declaration.
2. **Deterministic Intent Classifier:** Intent classification must use high-speed heuristic keyword scoring with LLM fallback, avoiding external network bottlenecks.
3. **Session Persistence:** Memory and conversation turns must be stored in SQLite memory store (`sakthai.memory`) with sliding window truncation.
4. **Zero Package Drift:** All modules added to `personas/sakthai/sakthai/` must be 100% mirrored in `personas/shared/sakthai/` to maintain 0% drift in `test_shared_package_divergence.py`.
5. **Strict Type Safety & Lint Cleanliness:** Strict `mypy` on `personas/sakthai/sakthai` and `ruff check` must pass with 0 errors.

---

## Task Breakdown

### Task 1: Core Gateway Router & Intent Classifier
- **Module:** `personas/sakthai/sakthai/agent/gateway_router.py`
- **Capabilities:**
  - `classify_intent(query: str) -> IntentClassification`: Detects categories (`coding`, `research`, `vision_presentation`, `creative_writing`, `automation_ci`, `ops_daily`).
  - `route_to_persona(query: str, charge_state: dict[str, int] | None = None) -> PersonaRouteResult`: Scores personas based on SOUL capabilities, intent match, and charge status.
  - Persona fallback chain: SakThai (Core Reasoning) -> SakKing (Architecture/Vision) -> SakSee (Research/Slides) -> SakSit (Copy/Story) -> SakJules (CI/DevOps) -> SakTan (Daily Ops).

### Task 2: Session & State Memory Bridge
- **Module:** `personas/sakthai/sakthai/agent/session_gateway.py`
- **Capabilities:**
  - `GatewaySession`: Manages multi-turn conversation state, active persona assignment, handoff history, and charge depletion/recharge.
  - `SessionManager`: Thread-safe session registry with persistence to SQLite or memory store, LRU eviction, and session cleanup.
  - `handle_handoff(session: GatewaySession, new_persona: str, reason: str) -> HandoffRecord`: Manages explicit or dynamic agent-to-agent delegation.

### Task 3: Telegram & REST Webhook Ingestor
- **Module:** `personas/sakthai/sakthai/telegram/gateway_bot.py` & `personas/sakthai/sakthai/web/gateway_api.py`
- **Capabilities:**
  - Telegram bot dispatcher handling commands (`/start`, `/persona <name>`, `/charge`, `/reset`) and routing text/voice queries to the active persona session.
  - REST endpoint `POST /api/gateway/chat` returning streaming SSE chunks with real-time routing metadata (`target_persona`, `intent_score`, `charge_level`).

### Task 4: Comprehensive Test Suite & Parity Sync
- **Tests:** `tests/test_gateway_router.py` & `tests/test_session_gateway.py`
- **Verification:** Unit and integration tests covering intent routing accuracy, session state preservation, persona handoffs, edge cases, and 100% byte-parity sync to `personas/shared/sakthai/`.

### Task 5: Dashboard Gateway Monitor Panel
- **Module:** `apps/sak_agent_dashboard/src/components/GatewayRouterPanel.tsx`
- **Capabilities:**
  - Real-time routing telemetry feed, intent score breakdown, persona load distribution, and live interactive test console.
  - Vitest unit tests in `apps/sak_agent_dashboard/src/tests/gateway_panel.test.tsx`.
