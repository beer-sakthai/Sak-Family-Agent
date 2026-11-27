# 🤖 SakJules — GitHub, CI/CD & Automation Specialist

**Master of Automation, GitHub & CI/CD Pipelines of the House of Sak.**

SakJules manages GitHub operations, PR attestation, repository security pipelines, and continuous integration self-healing across the House of Sak monorepo.

---

## ⚡ Core Responsibilities

- **CI Auto-Healing (`scripts/ci_auto_heal.py`)**: Deterministic log parsing, classification (lint, format, typing, transient network), targeted remediation, and automatic test loops.
- **Supply-Chain & Workflow Security**: SHA-256 action pinning, step-security hardening, zizmor audit enforcement, and secret leak scanning.
- **Branch & Cache Maintenance**: Automated PR cache cleanup on pull request closure (`cache-cleanup.yml`), stale ref sweeping, and pruning merged remote feature branches.
- **Interactive TUI & Risk Gates**: Full Textual terminal with two-phase tool logging and `ConfirmModalScreen` risk permission gates (`sak chat --tui`).
- **Gemini 4 Neon & Free-Tier Quota Sentinel**: Flagship **Gemini 4 Neon** (`gemini-4-neon`) support with guarded API rate limiting, Pacific Time resets (`~/.sakthai/quota_sentinel.db`), and adaptive free-tier fallback (`gemini-4-hydrogen` → `gemini-3.5-flash-lite` → `gemini-decision-1` under `GEMINI_FREE_ONLY=true`).
- **Autonomous Evolution**: Drives repository health maintenance, daily syncs, and prompt/tool evolution.
- **Evaluator-Optimizer & Graders**: CI auto-heal loop, supply-chain verification, and CodeGrader/ModelGrader assertions (`sakthai run --optimize`).
- **Remote MCP Security Stack**: StepSecurity remote SSE integration, Microsoft Learn, and Gemini API Docs.

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakJules on default model (DeepSeek-V4.1-Flash)
uv run sakthai run --persona sakjules "Run automated CI health diagnostics and audit supply-chain pins"

# Run with bounded Evaluator-Optimizer refinement loop
uv run sakthai run --persona sakjules --optimize "Verify and harden workflow action pins"

# Run with interactive chat mode (terminal or full-screen TUI)
uv run sakthai chat --persona sakjules
uv run sak chat --tui --persona sakjules

# Check Free-Tier Quota Sentinel status and token limits
uv run sakthai quota status

# Run CI auto-healing utility locally
uv run python scripts/ci_auto_heal.py --run-tests

# Run dynamic tool evaluation & telemetry benchmarks
uv run sakthai eval tools --bench --persona sakjules

# Run self-evolution on a skill
./evolve_agent.sh --skill SakJules-github-actions-dev --iterations 5
```

---

## Self-Evolution & GEPA Architecture

```
Read current skill/prompt/tool ──► Generate eval dataset
                                        │
                                        ▼
                                   GEPA Optimizer ◄── Execution traces
                                        │                    ▲
                                        ▼                    │
                                   Candidate variants ──► Evaluate
                                        │
                                   Constraint gates (tests, size limits, benchmarks)
                                        │
                                        ▼
                                   Best variant ──► PR against agent repo
```

Every evolved variant must pass:
1. **Full test suite** — `uv run pytest tests/ -q` must pass 100% with $\ge 96.0\%$ coverage.
2. **Size limits** — Skills $\le 15\text{ KB}$, tool descriptions $\le 500\text{ chars}$.
3. **Parity preservation** — Maintains 51-item structural parity and canonical path invariants.
4. **Human review** — Proposed enhancements go through PR review before merging.

---

## Core Working Files

- `SOUL.md`: Identity, charge system v6, and 100-point self-evaluation v9 rubric.
- `PLAN.md`: Task decomposition and multi-agent routing protocols.
- `CYCLE.md`: 6-stage growth cycle (Dream $\rightarrow$ Hope $\rightarrow$ Care $\rightarrow$ Joy $\rightarrow$ Trust $\rightarrow$ Growth).
- `MEMORY.md`: Active memory and durable learnings.
- `HANDOFF.md`: Cross-persona handoff contracts.
- `BACKPACK.md`: Domain toolbelt and skills inventory (48 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
