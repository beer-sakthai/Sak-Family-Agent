# Skill Library — Initial Inventory (2026-07-09)

Discovered during the first full audit-and-plan session.

## Scope

| Metric | Count |
|--------|-------|
| SKILL.md files on disk | 189 |
| Total lines | 42,832 |
| Unique skill names (skills_list) | 178 |
| SakSit-branded (B2B SaaS marketing) | 86 |
| Actionable (all others) | ~103 |

## Categories

| Category | Count | Notes |
|----------|-------|-------|
| B2B SaaS Marketing | 86 | Reference/content skills, large files |
| Software Development | 18 | Playwright, debugging, TDD, etc. |
| Creative | 18 | p5js, excalidraw, comfyui, ascii-art, etc. |
| Productivity | 14 | Google Workspace, notion, airtable, etc. |
| Research | 8 | arxiv, blogwatcher, llm-wiki, etc. |
| MLOps | 7 | vLLM, llama.cpp, W&B, huggingface, etc. |
| GitHub | 6 | PR workflow, code review, issues, etc. |
| Social Media | 5 | Instagram, LinkedIn, X/Twitter |
| Autonomous AI Agents | 5 | claude-code, codex, opencode, hermes-agent, sakthai |
| Apple (macOS only) | 5 | Notes, Reminders, FindMy, iMessage, macOS |
| SakThai Cycles | 6 | Dream→Hope→Care→Joy→Trust→Growth (30-line stubs) |
| Media | 4 | gif-search, heartmula, songsee, youtube-content |
| DevOps | 2 | kanban-orchestrator, kanban-worker |
| Other (standalone) | ~8 | service-quoting, dogfood, openhue, etc. |

## Known Duplicates

- `huggingface-hub` / `SakSit-huggingface-hub` — identical except name
- `SakSit-playwright-html-report` / `SakSit-playwright-html-reports` — singular vs plural variant
- Potentially overlapping: `community-building` vs `community-led-growth`, `short-form-video` vs `short-form-video-marketing`, `interactive-content` vs `interactive-content-leadgen`, `sales-enablement` vs `sales-enablement-content` (needs manual review)

## Evolution Pipeline Status

| Item | Status |
|------|--------|
| Pipeline code location | `/opt/data/profiles/saksit/sak-family-agent/packages/agent-self-evolution/` |
| Python venv | Not installed (needs `uv venv + uv pip install -e ".[dev]"`) |
| Previous runs | One: `github-auth` on sakking — FAILED (constraint validation) |
| Default model | Must use OpenRouter (`claude-3-haiku`), not local Ollama |
| Budget | Zero — free tier OpenRouter only |

## Largest Skills

- `research-paper-writing`: 2,377 lines
- `hermes-agent`: 1,111 lines
- `saksit-social-media-posting-workflows`: 1,107 lines
- `claude-code`: 745 lines
- `claude-design`: 650 lines
- `comfyui`: 612 lines

## Smallest Skills

- 6 sakthai-cycle-* skills: 30 lines each (stubs)
- `SakSit-core-web-vitals-basics`: 46 lines
- `service-quoting`: 50 lines
- `nano-pdf`: 52 lines

---

*Updated Jul 25 / Jul 26, 2026 — structural test now reports **203 skills** on disk (+14 since initial inventory). Full library has grown by ~7.4% in 2+ weeks.*
