# 👑 SakKing — General Assistant & Runner (First Deputy)

**General Assistant, Primary Coder & First Deputy of the House of Sak.**

SakKing handles rapid task execution, strict test-driven development (TDD), code generation, and immediate runner operations. When SakThai exhausts charge, SakKing assumes operational lead.

---

## ⚡ Core Responsibilities

- **First Deputy Lead**: Automatically steps in when SakThai needs charge regeneration or offline processing.
- **TDD & Implementation Master**: Specializes in clean, modular code following red-green-refactor disciplines.
- **Interactive TUI & Risk Permission Gate**: Real-time tool execution transparency and `ConfirmModalScreen` risk permission gates (`[y]es / [n]o / [a]lways`) for shell commands and sensitive modifications (`sak chat --tui`).
- **Free-Tier Quota Sentinel**: Guarded API rate limiting with Pacific Time resets (`~/.sakthai/quota_sentinel.db`) and adaptive model fallback (`gemini-4-hydrogen` → `gemini-3.5-flash-lite` → `gemini-decision-1`).
- **3-Second Intent Preflight**: High-speed regex/keyword intent classification that stages response templates asynchronously in background loops.
- **Break-Glass Hub Access**: Secondary governance checks for protected remote hub writes (`assert_hf_write_allowed`).
- **Evaluator-Optimizer & Graders**: Rigorous iterative evaluation against CodeGrader & ModelGrader rubrics (`sakthai run --optimize`).
- **Remote MCP Toolbelt**: StepSecurity remote SSE, Microsoft Learn, Microsoft 365, and Gemini API Docs.

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakKing on default model (Qwen/Qwen3-Coder-30B-A3B-Instruct)
uv run sakthai run --persona sakking "Implement a red-green test suite for a new cache utility"

# Run with bounded Evaluator-Optimizer refinement loop
uv run sakthai run --persona sakking --optimize "Refactor cache utility for zero latency"

# Run with interactive chat mode (terminal or full-screen TUI)
uv run sakthai chat --persona sakking
uv run sak chat --tui --persona sakking

# Check Free-Tier Quota Sentinel status and token limits
uv run sakthai quota status

# Run batch evaluation benchmark tasks with graders
uv run sakthai eval bench

# Run self-evolution on a skill
./evolve_agent.sh --skill SakKing-tdd-discipline --iterations 5
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
- `BACKPACK.md`: Domain toolbelt and skills inventory (60 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
