# Product Context: Sak-Family-Agent

## 1. Vision & Mission
**Sak-Family-Agent** is an autonomous multi-agent operating ecosystem comprising 6 specialized AI personas collaborating under strict deterministic guardrails, zero-copy memory vector mesh, persistent SQLite episodic memory, and continuous self-healing resilience.

---

## 2. The 6 Agent Personas

| Persona | Domain Role | Core Specialization | Primary Tools & Capabilities |
|---|---|---|---|
| **SakThai** 👑 | Chief Architect & Lead | System coordination, high-level planning, skill synthesis, final veto | `agent/loop`, MCP server, LLM provider routing, skills manager |
| **SakKing** 🛡️ | Kernel & Security Sentinel | AST guardrails, deterministic path validation, memory caching, deep audits | AST validator, security scanner, SQLite cache, policy gatekeeper |
| **SakSee** 👁️ | Vision & Quality Analyst | UI/UX inspection, Hugging Face space exploration, Playwright QA | Playwright automation, multimodal vision, artifact verification |
| **SakSit** ✍️ | Content & Communications | Technical documentation, social content kits, markdown publishing | Documentation builder, storytelling engine, diagrams |
| **SakJules** ⚡ | Automation & CI/CD Master | GitHub Actions, self-healing recovery, mutation testing, releases | CI fixer, mutation runner, DLQ supervisor, release drafter |
| **SakTan** 📊 | Governance & Financials | Token economics, budget analytics, billing models, compliance | Token tracker, billing ledger, audit logs, rate limiters |

---

## 3. Core Product Capabilities
1. **Autonomous Self-Healing Multi-Agent Recovery Protocol**: Runtime anomaly classification (`TRANSIENT`, `STATE_CORRUPT`, `FATAL`), dynamic circuit breakers, persistent SQLite dead-letter queue (DLQ), point-in-time state snapshot & rollback.
2. **Cross-Persona A2A Streaming & Consensus Mesh**: Structured chunk envelopes, domain-weighted quorum voting, real-time SSE streaming to Next.js War Room.
3. **Deterministic Security Guardrails**: ASCII control character rejection (`\x00-\x1f\x7f`), multi-prefix stripping, AST command injection blocker, PBKDF2 API key hashing.
4. **Episodic SQLite Memory & Vector Mesh**: WAL-mode thread-safe storage for facts, observations, and session episodes.
5. **Next.js 15 / React 19 Executive Dashboard**: Live telemetry feed, war room consensus inspector, DLQ console, and provider benchmark matrix.

---

## 4. Key Quality Metrics
- **Automated Tests:** 3,875+ unit, integration, and property-based tests.
- **Code Coverage Floor:** $\ge 96\%$ branch coverage across all core packages.
- **AST Compilation:** 100% clean compilation on all Python workspace files.
- **Package Parity:** Zero divergence between `personas/sakthai/sakthai` and `personas/shared/sakthai`.
