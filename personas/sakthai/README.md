# 🧬 SakThai — Lead Persona & Agent Self-Evolution

**Main Lead & Hugging Face Master of the House of Sak.**

SakThai coordinates the six-agent family, manages Hugging Face Hub deployments, spaces, and datasets, and drives reflective self-evolution for agent skills, prompts, and tooling.

---

## ⚡ Core Responsibilities

- **Lead Coordination**: Orchestrates family workflows and delegates to deputies (SakKing, SakTan, SakSee) via distributed Gateway pipelines (`/v1/team/pipelines/stream`).
- **Hugging Face Hub Master**: Secure model/dataset upload, sync, and inference with break-glass safety protocol (`assert_hf_write_allowed`).
- **Gemini 4 Neon & Free-Tier Quota Sentinel**: Flagship **Gemini 4 Neon** (`gemini-4-neon`) support with guarded API rate limiting, Pacific Time resets (`~/.sakthai/quota_sentinel.db`), and adaptive free-tier fallback (`gemini-4-hydrogen` → `gemini-3.5-flash-lite` → `gemini-decision-1` under `GEMINI_FREE_ONLY=true`).
- **Interactive TUI & Risk Gates**: Full Textual terminal with two-phase tool logging and `ConfirmModalScreen` risk permission gates (`sak chat --tui`).
- **Progressive Skill Hydration**: Manifest-driven lazy loading of specialized functional clusters (`get_skill_domain_manifests`).
- **Self-Evolution Engine**: Reflective evolutionary optimization using DSPy + GEPA (Genetic-Pareto Prompt Evolution).
- **Evaluator-Optimizer Engine**: Iterative candidate generation and multi-dimensional rubric scoring (`sakthai run --optimize`).
- **Remote MCP Integrations**: High-speed Streamable HTTP and stdio servers (Microsoft 365, Microsoft Learn, Gemini API Docs).

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakThai on default model (DeepSeek-V4.1-Flash)
uv run sakthai run --persona sakthai "Analyze trending Hugging Face spaces and datasets"

# Run with bounded Evaluator-Optimizer refinement loop
uv run sakthai run --persona sakthai --optimize "Synthesize latest ML findings"

# Run with interactive chat mode (terminal or full-screen TUI)
uv run sakthai chat --persona sakthai
uv run sak chat --tui --persona sakthai

# Check Free-Tier Quota Sentinel status and token limits
uv run sakthai quota status

# Run dynamic tool evaluation & telemetry benchmarks
uv run sakthai eval tools --bench --persona sakthai

# Run self-evolution on a skill
./evolve_agent.sh --skill SakThai-coding-security --iterations 5
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
- `BACKPACK.md`: Domain toolbelt and skills inventory (170 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
