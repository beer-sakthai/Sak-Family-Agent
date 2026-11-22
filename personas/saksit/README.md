# 📢 SakSit — Social, Brand & Content Specialist

**Social, Brand & Content Specialist of the House of Sak.**

SakSit drives developer communications, technical marketing, B2B SaaS thought leadership, release announcements, and narrative engagement across technical communities.

---

## ⚡ Core Responsibilities

- **Technical Storytelling**: Translates deep technical changes and monorepo architectures into clear, compelling engineering updates.
- **B2B SaaS Thought Leadership**: In-depth analysis on modern software patterns, agent architectures, and AI ecosystem shifts.
- **Multi-Platform Publishing**: Structured delivery for GitHub Releases, community forums, technical blogs, and developer hubs.
- **Brand Consistency**: Ensures voice, tone, and visual clarity across all family publications.
- **Evaluator-Optimizer Engine**: Multi-pass editorial refinement against tone and publication rubrics (`sakthai run --optimize`).
- **Remote MCP Knowledge Access**: Integrated Microsoft Learn and Gemini API Docs tools.

---

## Quick Start

```bash
# Sync dependencies
uv sync --all-extras

# Run SakSit on default model (DeepSeek-V4-Flash)
uv run sakthai run --persona saksit "Draft a release announcement for 6-agent resilience architecture"

# Run with bounded Evaluator-Optimizer refinement loop
uv run sakthai run --persona saksit --optimize "Refine release post for technical accuracy and tone"

# Run with interactive chat mode
uv run sakthai chat --persona saksit

# Run dynamic tool evaluation & telemetry benchmarks
uv run sakthai eval tools --bench --persona saksit

# Run self-evolution on a skill
./evolve_agent.sh --skill SakSit-linkedin-b2b-saas-thought-leadership-2026 --iterations 5
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
- `BACKPACK.md`: Domain toolbelt and skills inventory (45 overlay skills + 19 shared).
- `config/`: Configuration files (`config.yaml`, `workspace.yaml`, `mcp.json`).
- `evolution/`: Persona-owned self-evolution engine.

---

## License

MIT — © 2026 Beer SakThai / House of Sak
