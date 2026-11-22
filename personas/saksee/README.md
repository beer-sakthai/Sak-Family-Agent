# 👁️ SakSee — Web, Browser & Creative Specialist

**Web, Browser & Creative Specialist of the House of Sak.**

SakSee specializes in headless browser automation, complex DOM inspection, multi-platform creative media generation, and resilient data extraction across dynamic web applications.

---

## ⚡ Core Responsibilities

- **3-Tier Web Scraping Escalation**: Standardized escalation framework (`SakSee-web-scraping`):
  - *Tier 1*: Fast HTTP client (httpx/requests) with zero overhead.
  - *Tier 2*: Headless browser (Playwright) handling client-rendered SPAs, sessions, and cookies.
  - *Tier 3*: Stealth browser with human-in-the-loop review for protected endpoints.
- **Live Pipeline Visualizer & Memory Studio**: Next.js SVG DAG canvas implementation, token streaming terminal, and Memory Shard Studio interfaces (`apps/sak_agent_dashboard`).
- **Interactive TUI & Risk Gates**: Full Textual terminal with two-phase tool logging and `ConfirmModalScreen` risk permission gates (`sak chat --tui`).
- **Free-Tier Quota Sentinel**: Guarded API rate limiting with Pacific Time resets (`~/.sakthai/quota_sentinel.db`) and adaptive model fallback (`gemini-4-hydrogen` → `gemini-3.5-flash-lite` → `gemini-decision-1`).
- **Creative & Visual Generation**: Manim programmatic mathematical animations, Remotion video authoring, ComfyUI workflows, and ASCII visual art.
- **Frontend & UI Prototyping**: Modern React, Vite, Shadcn-UI, and Tailwind design implementation.
- **Third Deputy Lead**: Coordinates web research and visual assets across family workflows.
- **Evaluator-Optimizer Engine**: Bounded visual and technical refinement loop (`sakthai run --optimize`).
- **Remote MCP Documentation**: Microsoft Learn and Gemini API Docs integration via Streamable HTTP.

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakSee on default model (DeepSeek-V4.1-Flash)
uv run sakthai run --persona saksee "Inspect documentation and extract API schemas"

# Run with bounded Evaluator-Optimizer refinement loop
uv run sakthai run --persona saksee --optimize "Design an accessible frontend component"

# Run with interactive chat mode (terminal or full-screen TUI)
uv run sakthai chat --persona saksee
uv run sak chat --tui --persona saksee

# Check Free-Tier Quota Sentinel status and token limits
uv run sakthai quota status

# Run dynamic tool evaluation & telemetry benchmarks
uv run sakthai eval tools --bench --persona saksee

# Run self-evolution on a skill
./evolve_agent.sh --skill SakSee-web-scraping --iterations 5
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
- `BACKPACK.md`: Domain toolbelt and skills inventory (106 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
