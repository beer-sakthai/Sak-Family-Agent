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
- [x] 2026-11-16 **Scorecard Pinned-Dependencies Remediation across 6 Personas** — Remediate unpinned pip install fallback in setup_venv across personas/*/evolve_agent.sh, mandate uv, add regression test in test_persona_structure_parity.py, and resolve Code Scanning alerts #21698-#21703.
- [x] 2026-11-16 **6-Persona Skills Refactoring & Standardization** — Refactored and standardized all 629 skills across the 6 Sak Family personas and shared skills: purged legacy Hermes metadata (0 remaining), populated categories and keyword tags (100% compliant), hydrated the 7 empty Hugging Face skills with operational runbooks, canonicalized SakKing's `SakKing-coding-tdd` primary skill, and enforced structural invariants in tests with 96.76% coverage.
- [x] 2026-11-16 **6-Agent Skills Consolidation to 480 Skills & Search Taxonomy** — Consolidated 149 fragmented skills across SakThai (285->170) and SakSee (139->105), reallocated 17 operational/monitoring/cron skills to SakTan (9->26), standardized all skill names to searchable `Sak<Agent>-<domain>-<topic>` convention, updated all persona working files, and verified with automated invariant tests.
- [x] 2026-11-16 **Spec-Kit (.specify) Operationalization & Household Constitution Ratification** — Ratified .specify/memory/constitution.md with House of Sak architectural invariants (96% coverage floor, editable-install module resolution, persona boundaries, security gates), expanded .specify/integration.json for multi-agent support (copilot, claude, gemini), and added automated invariant tests in test_specify_constitution.py.
- [x] 2026-11-16 **Comprehensive MCP Enhancements (Core Protocol & Ergonomics)** — Implemented dual-format manifest parsing (`mcpServers` dict + `servers` list), tool allowlist filtering, remote HTTP/SSE transport support (`RemoteMCPClient`), MCP resources/prompts protocol support in `server.py`, and `sakthai mcp` developer CLI subcommands (`list`, `ping`, `tools`).
- [x] 2026-11-16 **Bandit B310 Code Scanning Remediation in HF Portfolio Health Script** — Enforce scheme validation (http/https only) and safe URL opening with Bandit suppression (#21720) in `scripts/hf-portfolio-health.py`, add unit tests, and verify ruff, bandit, and test suite pass clean.
- [x] 2026-11-16 **Scorecard Security & Token-Permissions Remediation** — Remediate top-level actions write permission in cache-cleanup.yml, unpinned pip install in agent-self-evolution.yml, bootstrap.sh scripts, and Dockerfile.sandbox, add regression tests, and verify all linters and tests pass clean.
- [x] 2026-11-16 **CI & Cache Hygiene Regression Fixes** — Update test_workflow_cache_hygiene.py to support job-level actions write permissions in cache-cleanup.yml, fix pytest execution in agent-self-evolution.yml, and verify CI turns completely green.
- [x] 2026-11-16 **Enforce locked uv environments across root workflows (PR #1885)** — Mandate `uv sync --locked` and `uv run --locked` across root CI workflows, make pre-commit hook check lock non-mutatingly, and add regression tests.
- [x] 2026-11-16 **Replace scalar workflow permissions with mappings (PR #1886)** — Replace scalar read-all/write-all declarations in cache-cleanup.yml and scorecard.yml with explicit mappings, and add automated regression checks.
- [x] 2026-11-16 **Audit & Remediate GitHub Code Scanning Alerts** — Audited code scanning dashboard across all tools (CodeQL, Bandit, Trivy/OSSAR, Scorecard); confirmed 0 Bandit vulnerabilities, triaged Scorecard SASTID alert #15465 (score 9/10 due to historical commit window) as accepted risk, verified 0 open alerts remaining across the repository.
- [x] 2026-11-16 **Six-Agent Registry, Visual Architecture Diagram & Inter-Agent Ecosystem Initialization** — Integrate safe repository initialization workflow script and roadmap, establish inter-agent communication protocol and JSON schema, catalog family character guides and soul-templates, and generate visual architecture diagram of the six-agent registry and specialist routing matrix.
- [x] 2026-11-16 **Manual Workflow Approval Gate Infrastructure** — Integrate SHA-pinned manual approval action (trstringer/manual-approval) with Harden-Runner, configure manual workflow gating in manual.yml and reusable manual-approval-gate.yml, document human-in-the-loop operational gates, and add automated regression checks.
- [x] 2026-11-16 **PR Preview Action Integration (`rossjrw/pr-preview-action`)** — Integrate SHA-pinned PR preview action for documentation and dashboard previews, configure secure permissions, add StepSecurity Harden-Runner, document preview deployment flow, and add automated regression checks.
- [x] 2026-11-16 **Marketplace Automation Actions Integration & Security Catalog** — Integrate and pin 7 verified GitHub Marketplace actions with immutable commit SHAs, configure automated workflows (wiki sync, PR comment trigger, markdown autodocs, deployments), document supply-chain invariants in docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-16 **Marketplace Actions Wave 2 Expansion (Release & Benchmark Actions)** — Integrate and pin 5 additional verified GitHub Marketplace actions (bakunyo/git-pr-release-action, hngprojects/pr-deploy, benchmark-action/github-action-benchmark, ghalactic/github-release-from-tag, jamesgeorge007/github-activity-readme) with immutable commit SHAs, configure automated workflows, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-16 **Marketplace Actions Wave 3 Expansion (Renovate, Multi-Linter & App Token Actions)** — Integrate and pin 3 additional verified GitHub Marketplace actions (renovatebot/github-action, wearerequired/lint-action, actions/create-github-app-token) with immutable commit SHAs, configure automated workflows, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 4 (Fastify Dependabot Auto-Merge Action)** — Integrate and pin fastify/github-action-merge-dependabot@v3.15.0 (73ec4cbb5e56df5591eae286972d5b2201ffe90f) with immutable commit SHA, configure automated dependabot auto-merge workflow, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 5 (PR Lint & PR Label Checker Actions)** — Integrate and pin seferov/pr-lint-action@v2.0.0 (cbef81c153f36262fbcd92fe97d6c6b8736d891d) and Optimal-AI/PR-Label-Checker@1.0.3 (48d46fe6336aedcbb836ca580e86f195f9d14b01) with immutable commit SHAs, configure automated workflows, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 6 (Workflow Orchestration, Runner Cleaner & API Testing Actions)** — Integrate and pin 11 new marketplace actions (stepci/stepci, benc-uk/workflow-dispatch, BetaHuhn/repo-file-sync-action, convictional/trigger-workflow-and-wait, technote-space/workflow-conclusion-action, saadmk11/github-actions-version-updater, rokibhasansagar/slimhub_actions, the-actions-org/workflow-dispatch, ahmadnassri/action-workflow-queue, varunsridharan/action-github-workflow-sync, technote-space/auto-cancel-redundant-workflow) plus re-verify existing trstringer/manual-approval with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 7 (Workflow Wait, Audit, Immortality, Status & PR Helper Actions)** — Integrate and pin 10 new marketplace actions (workflow-run-wait, gitflow-workflow-action, setup-github-licensed, github-workflow-immortality, github-actions-usage-audit, workflow-status-action, dispatch-workflow, checkbox-workflow-action, simple-comment-pr, wait-for-workflow) with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 8 (Git Flow, Gemini AI Code Review & CI Dokumentor Actions)** — Integrate and pin 5 new marketplace actions (git-flow-workflow, gemini-actions, ci-dokumentor, code-review-by-gemini-ai, gemini-code-review) with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 9 (Git Auto-Commit, Dependabot Auto-Merge, Autofix, Review & Issue Automations)** — Integrate and pin 8 new marketplace actions (stefanzweifel/git-auto-commit-action, ahmadnassri/action-dependabot-auto-merge, autofix-ci/action, necojackarc/auto-request-review, wow-actions/auto-assign, lucasbento/auto-close-issues, reitermarkus/automerge, mschilde/auto-label-merge-conflicts) plus re-verify existing fastify/github-action-merge-dependabot with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 10 (Pipeline Healer, PR Auditor, AI Guard & Ecosystem Automations)** — Integrate and pin 15 new marketplace actions (JAI0705/DevOps_Pipeline_healer_agent, Shawnchee/the-auditor, johnmanjiro13/auto-reviewer-assign, 3lvia/gh-actions-docs, desbo/merge-pr-action, casassg/auto-merge-bot, BaharaJr/merge-pr, devjoes/pr-automation, nicklegan/github-repo-self-approve-action, pratikmallya/autolabeler-codeowners, Bhupesh-V/update-pr-reminder-action, salehhashemi1992/ai-code-guard, wow-actions/add-badges, LucasRuy/sync-branch-action, vargiuscuola/genshdoc) plus re-verify existing mschilde/auto-label-merge-conflicts with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Marketplace Actions Wave 11 (Safe Dependabot, Fetch Metadata, Automerge & Dependabot Workflow Automations)** — Integrate and pin 6 new marketplace actions (DiogoRibeiro7/safe-dependabot, onebalaban/DependabotHelper, invi5H/dependabot-automerge, GavinMeierSonos/dependabot-action, dependabot/fetch-metadata, goatandsheep/dependabot-issue-action) plus re-verify existing Wave 10 marketplace actions with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
- [x] 2026-11-17 **Audit, Fix & Harden GitHub Actions Workflows** — Remediate failing and fragile workflows across the repository: fix PR preview git checkout on PR close, wiki-sync remote repository preflight, auto-label-merge-conflicts Dockerfile node:22-alpine commit SHA update, wow-actions/add-badges JSON badges input, casassg/auto-merge-bot GITHUB_TOKEN & event gating, auto-reviewer-assign and autolabeler-codeowners pull_request event triggers, auto-close-issues payload guard, gitflow-lifecycle GITHUB_TOKEN env, git-pr-release branch preflight, continuous-benchmark fallback output.json, activity-readme section markers, and zizmor dangerous-trigger suppressions (PR #1919).
- [x] 2026-11-17 **Marketplace Actions Wave 12 (Enable Automerge for Dependabot, Automatic Contrib PRs, Auto-Update & Generate Roadmap)** — Integrate and pin 4 new marketplace actions (halostatue/dependabot-automerge, github/automatic-contrib-prs, chinthakagodawita/autoupdate, inat-get/action-is-roadmap) with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner and robust GitHub Actions expressions, expand docs/marketplace-actions-catalog.md, and add regression tests (PR #1921).
- [x] 2026-11-17 **House of Sak Workflow Suite Implementation** — Implement automated semantic version tagging (semantic-tagging.yml, scripts/semantic_tagger.py), GitHub Wiki sync (wiki-sync.yml, scripts/sync_wiki.py), and persona PR codenames (pr-codename.yml, scripts/generate_pr_codename.py) with 100% test coverage and Zizmor security compliance.
- [x] 2026-11-17 **Marketplace Actions Wave 13 (Rational Test Server, Actions Documenter, Wiki Page Maintenance & Actions Auto-Docs)** — Integrate and pin 4 new marketplace actions (IBM/devopsauto-testserver-actions, gizumon/github-actions-documenter, umonkey/github-wiki-tools, pndurette/gh-actions-auto-docs) with immutable commit SHAs, configure automated workflows with StepSecurity Harden-Runner, expand docs/marketplace-actions-catalog.md, and add regression tests.
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
