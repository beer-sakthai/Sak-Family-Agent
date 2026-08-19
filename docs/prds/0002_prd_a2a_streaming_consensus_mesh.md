# PRD 0002: Cross-Persona A2A Distributed Streaming & Consensus Mesh

## 1. Project Overview
The **Cross-Persona A2A Distributed Streaming & Consensus Mesh** enables real-time inter-agent token delta streaming, structured JSON-RPC 2.0 message delegation, and domain-weighted multi-agent consensus voting across all 6 Sak-Family personas (`SakThai`, `SakKing`, `SakSee`, `SakSit`, `SakJules`, `SakTan`).

---

## 2. Problem Statement
1. **Synchronous Blocking Handoffs**: Currently, multi-agent workflows execute sequentially without real-time token or thought streaming, causing human operators and downstream agents to wait until complete turns finish before seeing progress.
2. **Lack of Multi-Agent Consensus**: Complex decisions (such as deployment approvals, security gates, or architectural changes) lack a formalized voting protocol, leading to single-agent failure points.
3. **Dashboard Disconnection**: Next.js dashboard panels cannot observe live streaming token generation across multiple personas concurrently.

---

## 3. Goals
- **Real-Time Chunk Streaming**: Stream token deltas, tool calls, and intermediate reasoning steps across agents via Server-Sent Events (SSE) and async in-memory queues with monotonic `seq` indexing.
- **Domain-Weighted Quorum Consensus**: Implement a voting engine where specialized personas hold higher voting weights in their domains (Security: SakKing/SakJules 2.0x; Design: SakSee/SakSit 2.0x; Lead: SakThai holds tie-breaker veto).
- **Interactive War Room Console**: Provide a live Next.js 15 / React 19 visual interface for observing multi-agent thought streams, quorum votes, and inter-agent delegation.
- **Resilience Integration**: Connect directly to `SelfHealingSupervisor` to dynamically adjust quorum if an agent trips its circuit breaker.

---

## 4. Functional Requirements

### P0 (Must Have)
- [ ] **A2A Streaming Protocol & Broker (`personas/sakthai/sakthai/a2a/streaming.py`)**:
  - Emits structured chunk envelopes (`seq`, `chunk_type: token|tool_call|tool_result|vote`, `delta`, `persona`, `timestamp`).
  - Supports `Last-Event-ID` reconnection and `: keepalive\n\n` heartbeats every 15s.
- [ ] **Consensus Voting Engine (`personas/sakthai/sakthai/a2a/consensus.py`)**:
  - Collects signed ballots (`APPROVE`, `REJECT`, `ABSTAIN`) with domain-weighting calculation.
  - Resolves voting sessions with quorum thresholds and SakThai veto overrides.
- [ ] **Next.js Real-Time Stream Route (`apps/sak_agent_dashboard/src/app/api/a2a/stream/route.ts`)**:
  - SSE streaming endpoint with `ReadableStream` and connection abort signal handling.
- [ ] **War Room Streaming & Voting Panel (`apps/sak_agent_dashboard/src/components/AgentWarRoomPanel.tsx`)**:
  - Live token streaming cards for all 6 personas and consensus resolution meters.

---

## 5. Non-Goals
- Modifying underlying LLM model weights or internal token sampling kernels.
- Distributed physical network clustering across distinct remote machines outside local stdio / HTTP endpoints.
