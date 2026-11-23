# House of Sak Documentation (`docs/`)

Official technical documentation and architectural reference for **House of Sak** (`Sak-Family-Agent`).

> For the interactive, categorized GitHub Wiki version, see [**Home.md**](./Home.md) and [**_Sidebar.md**](./_Sidebar.md).

---

## 🏛️ Core Architecture & Reference Guides

- [**Home.md**](./Home.md) — The comprehensive Knowledge Hub homepage with visual banner, persona matrix, and quickstart commands.
- [**architecture.md**](./architecture.md) — Layered architecture across `personas/sakthai/`, Next.js dashboard, SQLite memory, safety guardrails, and MCP subsystem.
- [**capabilities.md**](./capabilities.md) — Complete tool inventory, memory operations, providers, dashboard CLI, and unified platform capabilities.
- [**plugins.md**](./plugins.md) — MCP server + skills extensibility model and configuration schemas.
- [**integrations.md**](./integrations.md) — Multi-agent connections, external services over MCP, and no-cost local recipes.
- [**runtimes.md**](./runtimes.md) — CLI, Textual TUI (`sak chat --tui`) with two-phase tool logging and risk permission modal, agent loop, OpenAI-compatible Runtime Gateway with SSE pipeline streaming, Memory Shard Studio, Free-Tier Quota Sentinel, stdio MCP server, and local models (Ollama / OpenAI-compatible).
- [**inter-agent-communication-protocol.md**](./inter-agent-communication-protocol.md) — JSON schema contracts and inter-agent handoffs.
- [**replication.md**](./replication.md) — Multi-agent memory shard synchronization and backup strategies.
- [**workspace.md**](./workspace.md) — Developer environment setup and toolchain resolution.

---

## 👥 Personas & The Sacred Soul Cycle

- [**SOUL.md**](./SOUL.md) — Shared team identity, emotional charge model, and operating principles.
- [**family-agents-character-guide.md**](./family-agents-character-guide.md) — Deep character guides and voice profiles for all six personas.
- [**OPERATING_CONTRACT.md**](./OPERATING_CONTRACT.md) — Cross-agent operating rules and resource boundaries.
- [**USER.md**](./USER.md) — Beer's user profile, priorities, and core values.
- **Soul Cycle**: [Dream.md](./cycle/Dream.md) → [Hope.md](./cycle/Hope.md) → [Care.md](./cycle/Care.md) → [Joy.md](./cycle/Joy.md) → [Trust.md](./cycle/Trust.md) → [Growth.md](./cycle/Growth.md).

---

## 🛡️ Security & CI/CD Automation

- [**SECURITY.md**](./SECURITY.md) — Vulnerability reporting and repository security standards.
- [**manage-your-dependency-security.md**](./manage-your-dependency-security.md) — GitHub supply chain security, Dependabot, and Dependency Review Action architecture.
- [**marketplace-actions-catalog.md**](./marketplace-actions-catalog.md) — Verified catalog of immutable SHA-pinned GitHub Actions.
- [**stepsecurity-integration.md**](./stepsecurity-integration.md) — Harden-Runner runtime protection and outbound network telemetry.
- [**scorecard-accepted-risks.md**](./scorecard-accepted-risks.md) — OpenSSF Scorecard assessment and accepted risk documentation.
- [**sak-family-agent-github-actions-guide.md**](./sak-family-agent-github-actions-guide.md) — Architectural guide for all GitHub Actions workflows across the repository.
- [**manual-workflow-approval.md**](./manual-workflow-approval.md) — Human-in-the-loop manual approval gates.
- [**pr-preview-guide.md**](./pr-preview-guide.md) — Dynamic PR preview deployments for docs and dashboard.

---

## 📐 Formal Specifications & Plans

Formal architecture designs and implementation plans authored via Superpowers:
- [2026-11-16 Agent Personas Resilience Architecture Spec](./superpowers/specs/2026-11-16-agent-personas-resilience-architecture-design.md)
- [2026-11-16 GitHub Workflows & Cache Optimization Spec](./superpowers/specs/2026-11-16-github-workflows-and-cache-optimization-design.md)
- [2026-11-16 Agent Personas Resilience Implementation Plan](./superpowers/plans/2026-11-16-agent-personas-resilience.md)
- [2026-11-16 GitHub Workflows & Cache Optimization Plan](./superpowers/plans/2026-11-16-github-workflows-and-cache-optimization.md)
- [2026-11-16 Update Every README Implementation Plan](./superpowers/plans/2026-11-16-update-every-readme.md)
- [2026-11-13 Whole Repo Refactor Plan](./superpowers/plans/2026-11-13-whole-repo-refactor.md)
