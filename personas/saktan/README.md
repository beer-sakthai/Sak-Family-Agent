# ⏰ SakTan — Daily Ops, System Rhythm & Infrastructure Lead (Second Deputy)

**Daily Ops, System Rhythm & Infrastructure Lead of the House of Sak.**

SakTan operates as the relentless heartbeat of the House of Sak, overseeing continuous local operations, daemon watchdogs, health monitoring, and system equilibrium. Operating 100% locally via Ollama, SakTan incurs zero external API spend.

---

## ⚡ Core Responsibilities

- **Second Deputy Lead**: Steps in immediately when SakThai and SakKing coordinate off-cycle maintenance.
- **Guarded Algorithmic Fallback**: Automated fallback configured in `config/config.yaml` to revert to deterministic provisioning plans when LLM providers encounter quota or latency barriers.
- **Zero-Cost Local Execution**: Runs entirely on local Ollama (`127.0.0.1:11434`), ensuring complete offline independence and privacy.
- **Workspace & System Hygiene**: Monitors directory structures, stale locks, transient files, and system health status.

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakTan on local Ollama model (zero external cost)
uv run sakthai run --persona saktan "Perform daily system and workspace status check"

# Run with interactive chat mode
uv run sakthai chat --persona saktan

# Run self-evolution on a skill
./evolve_agent.sh --skill SakTan-daily-workspace-status --iterations 5
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
- `BACKPACK.md`: Domain toolbelt and skills inventory (26 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
