# Technical Plan: Cross-Persona A2A Distributed Streaming & Consensus Mesh

## Overview
Implements a reactive streaming and voting mesh enabling real-time token/tool delta emission via Server-Sent Events (SSE) and domain-weighted quorum consensus resolution across the 6 Sak-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`).

## PRD Reference
- File: [`docs/prds/0002_prd_a2a_streaming_consensus_mesh.md`](file:///home/beern/Sak-Family-Agent/docs/prds/0002_prd_a2a_streaming_consensus_mesh.md)
- Feature: Cross-Persona A2A Distributed Streaming & Consensus Mesh

## Relevant Files

### Files to Modify
- `personas/sakthai/sakthai/agent/loop.py` - Connect streaming callback `on_token` to A2A Broker.
- `apps/sak_agent_dashboard/src/components/AgentWarRoomPanel.tsx` - Connect live SSE feed to UI cards.
- `apps/sak_agent_dashboard/src/lib/a2a/a2aEngine.ts` - Integrate consensus and streaming channels.

### Files to Create
- `personas/sakthai/sakthai/a2a/models.py` - Domain types for `StreamChunk`, `VoteBallot`, `ConsensusSession`.
- `personas/sakthai/sakthai/a2a/streaming.py` - SSE generator and in-memory pub/sub broker.
- `personas/sakthai/sakthai/a2a/consensus.py` - Domain-weighted quorum resolution engine.
- `apps/sak_agent_dashboard/src/app/api/a2a/stream/route.ts` - Next.js SSE streaming route handler.
- `apps/sak_agent_dashboard/src/app/api/a2a/vote/route.ts` - Consensus vote polling and ballot submission.
- `tests/test_a2a_streaming.py` - Hermetic tests for streaming generators and sequence buffers.
- `tests/test_a2a_consensus.py` - Unit tests for weighted quorum calculation and veto rules.

### Reference Files
- `personas/sakthai/sakthai/healing/supervisor.py` - Circuit breaker health query integration.
- `apps/sak_agent_dashboard/src/lib/a2a/serviceRegistry.ts` - Capability registry.

---

## Key Algorithms

### 1. Domain-Weighted Quorum Resolution
**Purpose:** Calculate consensus outcome based on domain weights and veto overrides.
**Steps:**
1. Check if SakThai (Lead) submitted a `VETO` $\to$ immediately resolve as `REJECTED`.
2. Compute weighted approvals: $\sum (w_i \cdot \text{vote}_i)$ where $w_i = 2.0$ for primary domain experts and $1.0$ for others.
3. Compare against quorum threshold (default: $60\%$ of total active persona weight).
4. If threshold reached $\to$ `APPROVED`; if timeout or majority reject $\to$ `REJECTED`.

---

## AI Guardrails Applied

### Resource Efficiency
- [x] Sequence-indexed chunk buffering (max 1,000 chunks in circular memory).
- [x] SSE keepalive comments (`: keepalive\n\n`) emitted every 15s.

### Error Handling
- [x] Client connection abort handler closes stream cleanly without memory leaks.
- [x] Degraded personas with tripped circuit breakers excluded from quorum denominator.

### Type Safety
- [x] Strict TypeScript interfaces in `apps/sak_agent_dashboard/src/lib/a2a/types.ts`.
- [x] Pydantic / dataclasses in Python `sakthai.a2a.models`.

---

## Phase 1: Data Layer & Models (Foundation)

Defines serializable schemas, chunk types, and ballot models in Python and TypeScript.

### Tasks
- [ ] 1.0 **Create Python A2A Domain Models**
  - [ ] 1.1 Create `personas/sakthai/sakthai/a2a/models.py`
  - [ ] 1.2 Implement `ChunkType` (`token`, `tool_call`, `tool_result`, `vote`)
  - [ ] 1.3 Implement `StreamChunk`, `VoteBallot`, `VoteChoice`, and `ConsensusSession` dataclasses
  - [ ] 1.4 Add `to_dict()` and `from_dict()` serialization helpers

- [ ] 2.0 **Update Dashboard TypeScript Types**
  - [ ] 2.1 Update `apps/sak_agent_dashboard/src/lib/a2a/types.ts` with streaming chunk definitions

### Verification Criteria
- [ ] `tests/test_a2a_models.py` passes 100%.
- [ ] TypeScript `pnpm typecheck` compiles cleanly.

- [ ] Task: Conductor - User Manual Verification 'Data Layer & Models'

---

## Phase 2: Core Streaming Broker & Consensus Engine

Builds the asynchronous pub/sub streaming generator and domain-weighted voting engine.

### Tasks
- [ ] 3.0 **Implement A2A Streaming Broker**
  - [ ] 3.1 Create `personas/sakthai/sakthai/a2a/streaming.py` with `A2AMeshBroker`
  - [ ] 3.2 Implement `subscribe()`, `publish_chunk()`, and `sse_generator()`
  - [ ] 3.3 Add monotonic sequence counter (`seq`) and sequence history buffer

- [ ] 4.0 **Implement Multi-Agent Consensus Engine**
  - [ ] 4.1 Create `personas/sakthai/sakthai/a2a/consensus.py` with `ConsensusEngine`
  - [ ] 4.2 Implement domain weighting matrix (Security/Ops: SakKing+SakJules 2.0x, Vision/Content: SakSee+SakSit 2.0x)
  - [ ] 4.3 Add SakThai tie-breaking veto logic and dynamic circuit-breaker quorum adjustment

### Verification Criteria
- [ ] `tests/test_a2a_streaming.py` and `tests/test_a2a_consensus.py` pass 100%.

- [ ] Task: Conductor - User Manual Verification 'Core Streaming & Consensus Engine'

---

## Phase 3: Dashboard SSE Route & War Room UI

Exposes real-time streaming and consensus polling to Next.js 15 App Router.

### Tasks
- [ ] 5.0 **Create Next.js SSE Route Handlers**
  - [ ] 5.1 Create `apps/sak_agent_dashboard/src/app/api/a2a/stream/route.ts`
  - [ ] 5.2 Create `apps/sak_agent_dashboard/src/app/api/a2a/vote/route.ts`

- [ ] 6.0 **Enhance Agent War Room Panel**
  - [ ] 6.1 Update `apps/sak_agent_dashboard/src/components/AgentWarRoomPanel.tsx`
  - [ ] 6.2 Render live token streams for all 6 personas
  - [ ] 6.3 Render real-time consensus voting meters

### Verification Criteria
- [ ] `pnpm typecheck` and `pnpm lint` in `apps/sak_agent_dashboard` pass with 0 errors.

- [ ] Task: Conductor - User Manual Verification 'Dashboard SSE Route & War Room UI'

---

## Phase 4: Review & Finalize

### Tasks
- [ ] 7.0 **Testing & Parity Check**
  - [ ] 7.1 Synchronize `personas/shared/sakthai/a2a/` for exact package parity
  - [ ] 7.2 Run `tests/test_shared_package_divergence.py` and `tests/test_repo_parses.py`

- [ ] 8.0 **Documentation**
  - [ ] 8.1 Update `conductor/tracks.md` status
  - [ ] 8.2 Add walkthrough and verification report

- [ ] Task: Conductor - User Manual Verification 'Review & Finalize'
