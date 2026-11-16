# Sak Family Agent — Master Plan Index

> **Dream → Hope → Care → Joy → Trust → Growth**

This is the master index. Navigate from here. Always update sub-plans in-place;
never duplicate content across files.

---

## 🗂️ Where Things Live

| What you're looking for | Where to find it |
|---|---|
| **Business strategy & monetization plan** | [`product/PLAN.md`](./product/PLAN.md) |
| **Session notes & brainstorms** | [`product/sessions/`](./product/sessions/) |
| **Team identity, Charge & Principles** | [`docs/SOUL.md`](./docs/SOUL.md) |
| **Memory tools & agent guide** | [`docs/SAKTHAI.md`](./docs/SAKTHAI.md) |
| **Beer's profile & core values** | [`docs/USER.md`](./docs/USER.md) |
| **Agent operating rules** | [`docs/OPERATING_CONTRACT.md`](./docs/OPERATING_CONTRACT.md) |
| **Architecture & capabilities** | [`docs/architecture.md`](./docs/architecture.md) · [`docs/capabilities.md`](./docs/capabilities.md) |
| **Python source** | [`personas/sakthai/sakthai/`](./personas/sakthai/sakthai/) — the installed package |
| **Agent personas** | [`personas/`](./personas/) |
| **Skills** | [`personas/*/skills/`](./personas/) (per-persona overlays) · [`personas/shared/skills/`](./personas/shared/skills/) · [`library/`](./library/) (31 curated) |
| **Helper scripts** | [`scripts/`](./scripts/) |
| **Tests** | [`tests/`](./tests/) |
| **Web dashboard** | [`apps/sak_agent_dashboard/`](./apps/sak_agent_dashboard/) — Next.js frontend; HTTP API in [`personas/sakthai/sakthai/web/`](./personas/sakthai/sakthai/web/) |
| **Assets / images** | `assets/` — on disk but untracked; see [`docs/repo-audit-2026-08-08.md`](./docs/repo-audit-2026-08-08.md) |

---

## 🚦 Open & Uncompleted Tasks (Consolidated Master Backlog)

All completed historical tasks (`✅ Done` / `[x]`) have been removed from the active plan files and consolidated here so only uncompleted work remains in one place.

### 1. Security & Repository Settings (Needs Beer / Maintainer Action)
- [x] 2026-11-16 **Repository quality review** — corrected the README's canonical package path and added a regression test for the documented validation commands.
- [x] 2026-11-16 **Legacy and infrastructure Ruff cleanup** — removed the remaining findings in the workflow framework, infrastructure, services, and training utilities without changing behavior.
- [x] 2026-11-16 **GitHub Agentic Workflows & Gemini Reviewer fixes** — Merged PR #1860 and PR #1861 to `main`, applied `copilot-requests: write` token auth and Gemini excluded-only PR guard, and closed the 8 open `[aw]` issues (`#1837`, `#1839`, `#1850`, `#1851`, `#1852`, `#1853`, `#1854`, `#1859`).
- [x] 2026-11-16 **6-Persona Evaluation & Readiness Pipeline** — Added 4-layer evaluation across all 6 personas (`sakthai eval personas`, `sakthai eval summary --persona / --all-personas`, `saktan` v9 rubric in `SOUL.md`, 6-persona `lm-eval` soul-following dataset/regex, and `diagnose_personas.py` working-files check).
- [x] 2026-11-16 **6-Persona Working & Analysis Files Alignment** — Audited and synchronized all 8 markdown/analysis files (`SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, `BACKPACK.md`, `AGENTS.md`, `README.md`) across `personas/<agent>/` with actual on-disk skill counts (`285/63/139/45/68/9` + `19` shared), primary skills (`Sak-ocr-and-documents`), canonical paths (`personas/sakthai/`, `personas/<agent>/evolution/`), and Hermes lead profile (`sakthai` on `~/.hermes`).
- [x] 2026-11-16 **Remove Hermes framework — personas run standalone via `sakthai`** — Deleted `infra/hermes-agents/`, stripped Hermes runtime dependencies from all 6 personas (`SOUL.md`, `PLAN.md`, `CYCLE.md`, `MEMORY.md`, `HANDOFF.md`, `BACKPACK.md`, `AGENTS.md`, `README.md`), updated self-evolution packages and configs to clean security baselines, updated scripts and CI workflows, and verified full 6-persona diagnostic and test suite pass (PR #1865).
- [ ] **Revoke historical leaked credentials** ([`security/SECURITY_FIXES_PLAN.md`](./security/SECURITY_FIXES_PLAN.md) Fix #1) — Revoke the historical Composio consumer key, Mistral API key, and Kaggle API token in their provider dashboards and re-test dependent integrations (Fix #2 Web API Bearer Auth is already `[x]` done).
- [ ] **GitHub Repository Settings — Required Status Check De-duplication** — Drop `Quality gates` from `main`'s required status checks in GitHub repo settings so the duplicate `quality` job in `.github/workflows/repository-security-quality.yml` can be removed (`ci.yml` already runs ruff, mypy, bandit, and pytest on Python 3.11 and 3.12).
- [ ] **GitHub Repository Settings — Scorecard Non-Commit Checks** — `Branch-Protection`, `Code-Review` (requires a second human reviewer), and `CII-Best-Practices` ([`docs/cii-best-practices-answers.md`](./docs/cii-best-practices-answers.md)) require repository/external settings changes by Beer.
- [ ] **Triaged Workflow Decisions** — Decide whether to retire or replace `sonarcloud.yml` (archived upstream action) and `ossar.yml`.

### 2. Hugging Face Ecosystem ([`docs/hf-cards-improvement-plan.md`](./docs/hf-cards-improvement-plan.md))
- [ ] **Private `Nanthasit/sakthai-embedding` repo decision** — Decide whether to keep `sakthai-embedding` (English) permanently private or publish a deprecation notice redirecting to `sakthai-embedding-multilingual`.
- [ ] **Automated card-promotion cron check** — Ensure no external promotion script overwrites the lean 11-model / 8-dataset / 3-Space card template on `sakthai-combined-v6`.

### 3. Product & Monetization ([`product/PLAN.md`](./product/PLAN.md))
- [ ] **ServiceQuoteBot Customer Outreach** — Deploy first live pilot instance for Beer's target local service business customer.
- [ ] **Revenue & Lead Tracking** — Set up conversion and monthly recurring revenue (MRR) tracking once the pilot is live.

### 4. Agent Self-Evolution Pipeline ([`personas/shared/agent-self-evolution/PLAN.md`](./personas/shared/agent-self-evolution/PLAN.md))
*(Phases 1 & 2 — Skill Evolution and Tool Description Optimization — are `[x]` complete)*
- [ ] **Phase 3: System Prompt Evolution** (`evolution/prompts/`) — Build section-as-DSPy-parameter wrapper for the 5 evolvable `prompt_builder.py` sections (`DEFAULT_AGENT_IDENTITY`, `MEMORY_GUIDANCE`, `SESSION_SEARCH_GUIDANCE`, `SKILLS_GUIDANCE`, `PLATFORM_HINTS`) and behavioral evaluator.
- [ ] **Phase 4: Code Evolution via Darwinian Evolver** (`evolution/code/`) — Build `GitBasedOrganism` wrapper and composite pytest + benchmark fitness function for tool implementation code.
- [ ] **Phase 5: Continuous Self-Improvement Loop** (`evolution/monitor/`) — Build performance monitor, auto-triage ranker, and scheduled optimization trigger.

### 5. Agent Workflow Framework Backlog ([`apps/agent_workflow_framework/docs/superpowers/plans/2026-09-22-framework-improvement-plan.md`](./apps/agent_workflow_framework/docs/superpowers/plans/2026-09-22-framework-improvement-plan.md))
*(P1 — Packaging & Import Ergonomics (`pyproject.toml`) and P1 — Evaluation Isolation (`--storage-dir` + `verify.py` isolation) are `[x]` complete)*
- [x] 2026-11-16 **P2 — Observability & Failure Contracts** — Add tests for malformed persisted history, duplicate run IDs, invalid retry values, and callback exceptions. (PR #1868)
- [ ] **P2 — Execution Resilience** — Add cancellation and timeout semantics for long-running workflow steps.
- [ ] **P3 — Benchmark Quality** — Add parallel fan-out/retry baselines and machine-readable JSON summary output to `verify.py`.

### 6. Per-Persona Open Operational Tasks (`personas/*/PLAN.md`)
- [ ] **SakThai** ([`personas/sakthai/PLAN.md`](./personas/sakthai/PLAN.md)) — Live `HF_TOKEN` preflight; family pre-task memory read; Gate 1 `sakthai hf info <repo_id>` for SakSit; triple-gated Hub writes (`hub-approved`); family status & conflict resolution; Growth stage `CYCLE EVAL: sakthai`.
- [ ] **SakKing** ([`personas/sakking/PLAN.md`](./personas/sakking/PLAN.md)) — Live `HF_TOKEN` preflight; family pre-task memory read; Deputy 1 readiness check (`DEPUTY CHAIN`).
- [ ] **SakSee** ([`personas/saksee/PLAN.md`](./personas/saksee/PLAN.md)) — Live `HF_TOKEN` preflight; Chrome DevTools MCP (`chrome-devtools-mcp@1.10.1`) & Playwright (`@playwright/mcp@0.0.83`) checks; live web extraction with mandatory `retrieved_at` ISO timestamp and `monitoring-result` memory cache write; Growth stage `CYCLE EVAL: saksee`.
- [ ] **SakSit** ([`personas/saksit/PLAN.md`](./personas/saksit/PLAN.md)) — Live `HF_TOKEN` preflight; family pre-task memory read; draft PR #1636 family update (`hub-draft` + `awaiting-review`); refresh model card copy after SakThai Gate 1; request live numbers via `data-request` tag from SakSee.
- [ ] **SakJules** ([`personas/sakjules/PLAN.md`](./personas/sakjules/PLAN.md)) — Live `HF_TOKEN` preflight; verify open PRs (`gh pr list`) and implement SakTan's `schedule-request` tags (`schedule-confirmed`); run full quality gate (`ruff`, `mypy`, `bandit`, `pytest`); Growth stage `CYCLE EVAL: sakjules`.
- [ ] **SakTan** ([`personas/saktan/PLAN.md`](./personas/saktan/PLAN.md)) — Local Ollama (`sakthai` model) preflight; family pre-task memory read; `memory healthcheck` & `backup`; Beer's daily briefing, close-the-day, and weekly review; SakSee `rate-limit-ban` tally; SakSit >7d stalled Joy check; SakJules `schedule-confirmed` verification.

## 📋 Sub-Plans

| Plan | Location | Status |
|---|---|---|
| Whole-Repo Refactor Plan | [`docs/superpowers/plans/2026-11-13-whole-repo-refactor.md`](./docs/superpowers/plans/2026-11-13-whole-repo-refactor.md) | 🟢 Complete (2026-11-13) — All 5 TDD tasks verified |
| Product & Monetization | [`product/PLAN.md`](./product/PLAN.md) | 🟡 Active — 2 outreach/revenue tasks open |
| Security Fixes | [`security/SECURITY_FIXES_PLAN.md`](./security/SECURITY_FIXES_PLAN.md) | 🔴 HIGH — Fix #1 (Credential revocation) open; Fix #2 done |
| Personas (×6) | [`personas/*/PLAN.md`](./personas/) | 🟡 Active — operational tasks open |
| Agent Self-Evolution | [`personas/shared/agent-self-evolution/PLAN.md`](./personas/shared/agent-self-evolution/PLAN.md) | 🟡 Active — Phases 3–5 open (Phases 1–2 done) |
| HF Ecosystem Improvement | [`docs/hf-cards-improvement-plan.md`](./docs/hf-cards-improvement-plan.md) | 🟡 Active — private `sakthai-embedding` decision open |
| Workflow Framework Backlog | [`apps/agent_workflow_framework/docs/superpowers/plans/2026-09-22-framework-improvement-plan.md`](./apps/agent_workflow_framework/docs/superpowers/plans/2026-09-22-framework-improvement-plan.md) | 🟡 Active — P2–P3 open (P1 done) |

## 🔧 Runtime Notes

Runtime and deployment details are tracked in the implementation docs and the
workspace runtime config under `infra/`.

### Source files

- `docs/agent-diagnosis.md` for the standalone run checklist and runtime notes.
- `personas/` for the persona profiles and runtime config.
- `product/TODO.md` for the product delivery checklist.

---

## 🔑 Working Rules

1. **Plan first.** Update this file or the relevant sub-plan before acting.
2. **Surgical edits.** Change only what the task needs; preserve surrounding style.
3. **No duplication.** One source of truth per topic — link, don't copy.
4. **Protect Beer first.** No-cost, low-risk solutions always preferred.
