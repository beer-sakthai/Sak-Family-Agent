# Monorepo-Wide Mermaid Visual Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate rich, standardized, syntax-valid Mermaid visual architecture diagrams across all primary domain and persona `README.md` files in the House of Sak monorepo, providing immediate visual clarity on agent routing, 3-tier escalation, dual-runner execution, CI/CD auto-healing, and dashboard integration.

**Architecture:** 
- Target files:
  1. `personas/README.md` (6-Persona Multi-Agent Routing Topology)
  2. `personas/sakthai/README.md` (Lead & MLOps Architecture)
  3. `personas/sakking/README.md` (Dual-Runner Execution Engine)
  4. `personas/saksee/README.md` (3-Tier Web Escalation & Reaper)
  5. `personas/saksit/README.md` (Content Generation & Editorial Quality Lifecycle)
  6. `personas/saktan/README.md` (Daily Ops, Rhythm & SQLite Compaction Engine)
  7. `personas/sakjules/README.md` (CI/CD Auto-Healing & DevSecOps Pipeline)
  8. `apps/sak_agent_dashboard/README.md` (Next.js 16 Frontend & Gateway SSE Architecture)
  9. `services/teams-copilot-mcp/README.md` (Teams Copilot MCP Protocol Architecture)
  10. `infra/pw-poc/README.md` (Playwright Infrastructure & Reaper Flow)
  11. `docs/README.md` (Documentation Knowledge Graph)

**Tech Stack:** GitHub Flavored Markdown, Mermaid (`flowchart`, `graph`), Pytest, Ruff.

**Invariants:**
- Every Mermaid diagram must use supported syntax: `flowchart TD`, `flowchart LR`, `graph TD`, or `sequenceDiagram`.
- All node labels with special characters (parentheses, slashes, brackets) must be properly quoted (e.g. `["Label (Text)"]`).
- No trailing whitespace (`git diff --check` must return 0).
- Strict adherence to persona invariants in `tests/test_soul_consistency.py` and `tests/test_repo_hygiene.py` (canonical paths `personas/sakthai/`, no `hermes`, no doubled paths).
- Coverage and linting remain 100% clean.

---

### Task 1: Setup SDD Workspace & Ledger

**Files:**
- Create: `.superpowers/sdd/2026-11-27-mermaid-doc-all-readmes/progress.md`
- Test: `git status`

- [x] **Step 1: Initialize SDD workspace and ledger**
Run workspace initializer and create progress ledger.

---

### Task 2: Personas Hub & 6 Persona README Mermaid Diagrams

**Files:**
- Modify: `personas/README.md`
- Modify: `personas/sakthai/README.md`
- Modify: `personas/sakking/README.md`
- Modify: `personas/saksee/README.md`
- Modify: `personas/saksit/README.md`
- Modify: `personas/saktan/README.md`
- Modify: `personas/sakjules/README.md`
- Test: `uv run pytest tests/test_soul_consistency.py -v`

- [x] **Step 1: Add 6-Persona Routing Topology to `personas/README.md`**
- [x] **Step 2: Add Lead & MLOps Architecture to `personas/sakthai/README.md`**
- [x] **Step 3: Add Dual-Runner Execution Engine to `personas/sakking/README.md`**
- [x] **Step 4: Add 3-Tier Web Escalation & Reaper to `personas/saksee/README.md`**
- [x] **Step 5: Add Editorial Quality Lifecycle to `personas/saksit/README.md`**
- [x] **Step 6: Add Daily Rhythm & Ops Engine to `personas/saktan/README.md`**
- [x] **Step 7: Add CI/CD Auto-Healing Pipeline to `personas/sakjules/README.md`**
- [x] **Step 8: Verify soul consistency and zero whitespace**

---

### Task 3: Apps, Services, Infra & Docs README Mermaid Diagrams

**Files:**
- Modify: `apps/sak_agent_dashboard/README.md`
- Modify: `services/teams-copilot-mcp/README.md`
- Modify: `infra/pw-poc/README.md`
- Modify: `docs/README.md`
- Test: `uv run pytest tests/test_repo_hygiene.py -v`
- Test: `make lint`

- [x] **Step 1: Add Next.js 16 & Gateway SSE Architecture to `apps/sak_agent_dashboard/README.md`**
- [x] **Step 2: Add Teams Copilot MCP Protocol Flow to `services/teams-copilot-mcp/README.md`**
- [x] **Step 3: Add Playwright Infrastructure to `infra/pw-poc/README.md`**
- [x] **Step 4: Add Documentation Knowledge Graph to `docs/README.md`**
- [x] **Step 5: Verify repo hygiene, lint, and formatting**

---

### Task 4: Final Quality Gates, Commit & Push to PR #2117

**Files:**
- Modify: `PLAN.md`
- Test: `make lint`
- Test: `uv run mypy personas/sakthai`
- Test: `uv run bandit -c pyproject.toml -r personas/sakthai -q`
- Test: `python3 scripts/sync_personas.py --check`
- Test: `uv run pytest tests/test_soul_consistency.py tests/test_repo_hygiene.py tests/test_cli_output_contract.py -v`

- [x] **Step 1: Execute all quality gate checks**
- [x] **Step 2: Update PLAN.md Section 20**
- [x] **Step 3: Commit and push changes to branch `docs/update-every-readme-in-repo`**
- [x] **Step 4: Verify PR #2117 status**
