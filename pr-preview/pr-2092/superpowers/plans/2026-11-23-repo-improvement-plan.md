# House of Sak Repository Improvement Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove the documentation, packaging, and release drift that has accumulated in `beer-sakthai/Sak-Family-Agent`, so every headline claim in the README is verifiable from the tree, every governance document agrees with the code it describes, and the six-persona package duplication is migrated from *copy* to *generate*.

**Architecture:** The work is split into three tracks that each produce an independently testable deliverable. **Track A — Documentation accuracy** fixes one contradiction per task and installs a regression test that fails before the fix. **Track B — Packaging & release integrity** establishes a single source of truth for version, install path, and repository layout. **Track C — Structural de-duplication** moves the five persona package copies onto the overlay/compose model the repository already uses for skills. Tracks A and B are additive, low-risk, and separately mergeable; Track C is the large, risk-bearing migration and must land last.

**Tech Stack:** Markdown, Python 3.11/3.12, Pytest, `uv`, GitHub Actions, `gh-aw` v1.2.2 (agentic workflow compiler).

**Spec:** [`AGENTS.md`](../../../AGENTS.md), [`GEMINI.md`](../../../GEMINI.md), [`docs/adr/ADR-0001-persona-package-duplication.md`](../adr/ADR-0001-persona-package-duplication.md)

## Global Constraints

- **Financial Cost Floor:** $0.00 USD financial spend — 100% local and free-tier execution. No paid GPU, no paid API calls, no paid CI minutes.
- **Coverage Floor:** The pytest suite must keep passing with `--cov-fail-under=96`, enforced on the command line by `.github/workflows/ci.yml`. Never lower the floor, and never rely on `[tool.coverage.report] fail_under` alone — it did not fail the build (finding 1 of `docs/test-coverage-audit-2026-08-27.md`).
- **Python Floor:** 3.11–3.12 only (`requires-python = ">=3.11,<3.13"`). CI runs a 3.11 × 3.12 matrix; both legs must pass.
- **Canonical Package:** The installable package is `personas/sakthai/`, mapped by the root `pyproject.toml` (`[tool.setuptools] package-dir = {"sakthai" = "personas/sakthai"}`). `personas/sakthai/pyproject.toml` is a **different** project (`sak-agent-self-evolution` v0.1.0, `packages.find` includes only `evolution*`) and must never be treated as the agent package.
- **Per-Persona Truth:** `SOUL.md`, `skills/`, `config/`, `evolution/`, and `tests/` are legitimately per-persona and are excluded from every package-parity surface. Never sync them.
- **Never Auto-Merge:** `AGENTS.md` rule 5 — never run `gh pr merge` or `--auto`; leave every PR open for manual review and merge by Beer (`beer-sakthai`). This **overrides** the merge step written in `docs/superpowers/plans/2026-11-16-update-every-readme.md` (Task 6, Step 4), which is itself a defect (see Task 4).
- **Supply Chain:** Every GitHub Action stays pinned to a full 40-character commit SHA. Compiled `gh-aw` workflows (`*.lock.yml`) are **generated** — edit the sibling `.md` and run `gh aw compile`; never hand-edit the `.lock.yml`.
- **Whitespace:** Zero trailing whitespace in every changed file; `git diff --check` must return 0.
- **Branch Naming:** `docs/`, `fix/`, or `refactor/` prefix. Never push directly to `main`.

---

## Evidence Base

Every finding below was verified against the repository at commit `ba7cd84b5f9cdcfdcde0c2a0818a20070b7ed3ad` (default branch `main`, 2026-11-23) using the GitHub API — repository tree, file contents, workflow runs, issues, pull requests, and releases. No finding is inferred.

| # | Finding | How it was verified | Severity |
| :-- | :--- | :--- | :-- |
| 1 | `HOUSE_OF_SAK.md` states *"Five personas remain on disk today (SakTan's persona directory was removed)"* — but `personas/saktan/` exists with 331 files and 26 skills, and the README claims 6/6 personas online. | Repository tree + `personas/saktan/` blob count | High |
| 2 | `ONBOARDING.md` is an un-filled template: title reads `# Welcome to [Team Name]`, body contains three literal `TODO` placeholders. | File contents | High |
| 3 | `CHANGELOG.md` opens with *"This changelog has lagged the repository."* — no entries for the six-persona layout, memory sharding, guardrail hardening, or the dashboard API. | File contents | Medium |
| 4 | ADR-0001 claims *"Content parity is CI-enforced for only three files"*, but `tests/test_persona_package_parity.py` now byte-compares the **entire** package tree across all five copies. Option B is already implemented; the ADR is stale. | `tests/test_persona_package_parity.py` docstring + assertions | High |
| 5 | `docs/superpowers/plans/2026-11-16-update-every-readme.md` targets paths that no longer exist (`apps/agent_workflow_framework/`, `infra/hermes-agents/`, `personas/sakthai/sakthai/`, `personas/shared/sakthai`), states a stale test count ("2,823+"), and its Task 6 Step 4 prescribes `gh pr merge --admin` — which contradicts `AGENTS.md` rule 5. | Plan contents + tree lookups | High |
| 6 | `docs/superpowers/plans/2026-11-13-whole-repo-refactor.md` defines the canonical package as `personas/sakthai/sakthai/`. That path does not exist; the canonical package is `personas/sakthai/`. | Plan contents + tree lookup | Medium |
| 7 | The README badge hardcoded `release-v2.52.0` and linked to `/releases`, but `list_releases` returns `[]` — **no GitHub Release has ever been published** — and the root `pyproject.toml` declares `version = "2.0.0"`. | `list_releases` + `pyproject.toml` | High |
| 8 | `pr_description.txt` (2,353 bytes) is a leftover PR body committed at the repository root. | Tree + file contents | Medium |
| 9 | Root `pyproject.toml` `[tool.ruff] exclude` lists `"library"`, a directory that does not exist. | Tree + `pyproject.toml` | Low |
| 10 | README claimed a `library/` directory, a `sakthai repo map` over "9 repository areas (… library, and personas)", "120+ workflows", "Next.js 15+", and "4,155+ tests" — none matched disk. The actual registry has **10** areas and **52** tasks; there are **188** workflow files; the dashboard is on **Next 16.4.6**; the test file count is 215 pytest files + 24 dashboard suites. | `personas/sakthai/cli/repo_registry.py` `AREAS`/`TASKS`, tree counts, `apps/sak_agent_dashboard/package.json` | High |
| 11 | The README's own Quick Start told users to run `pip install -e personas/sakthai` — which installs `sak-agent-self-evolution`, **not** the `sak`/`sakthai` CLI the rest of the README depends on. | `personas/sakthai/pyproject.toml` vs root `pyproject.toml` `[project.scripts]` | High |
| 12 | 8 compiled `gh-aw` workflows (`*.lock.yml`, ~992 KB total, up to 2,200 lines each) are generated artifacts; the sources are the sibling `.md` files. Editing a `.lock.yml` by hand silently diverges from its source. | File headers (`gh-aw-manifest`, `DO NOT EDIT`) | Medium |
| 13 | 65 Markdown files sit at `docs/` root, including 5 dated `test-coverage-audit-*.md` series files, 2 dated `security_audit_*.md` files, and `repo-audit-2026-08-08.md`. | Tree listing | Low |
| 14 | The five persona copies each carry the same **131** Python modules under `agent/`, `cli/`, `memory/`, `mcp/`, `gateway/`, `agent_platform/`, … — roughly 655 redundant tracked `.py` files. | Per-persona blob counts excluding `skills/`, `evolution/`, `tests/` | Medium |
| 15 | `docs/test-coverage-audit-2026-09-01.md` — the most recent measured audit — records **96.21%** branch coverage, 191 uncovered statements, 156 partial branches, and notes the suite is **not hermetic** (`tests/test_cli.py` reaches the public npm registry mid-run). | File contents | Medium |

---

## File Structure & Responsibility Map

| Path | Action | Responsibility |
|---|---|---|
| `tests/test_docs_claims_consistency.py` | **Create** | Parses the governance documents and asserts their persona counts, version strings, and directory claims agree with the tree. Fails before every Track A/B fix; passes after. |
| `tests/test_repo_layout_drift.py` | **Create** | Asserts the root `pyproject.toml` ruff `exclude` list and the README's Repository Layout block name only directories that exist on disk. |
| `scripts/gen_readme_metrics.py` | **Create** | Computes the README's headline numbers (persona count, skill count, test file count, workflow count) from the tree and writes `docs/metrics-snapshot.json`. |
| `HOUSE_OF_SAK.md` | **Modify** | Correct the persona roster and cross-link the real team roster. |
| `ONBOARDING.md` | **Modify** | Replace the un-filled template with a real onboarding guide. |
| `CHANGELOG.md` | **Modify** | Add an `Unreleased` section covering the six-persona layout, memory sharding, guardrail hardening, and the dashboard API. |
| `docs/adr/ADR-0001-persona-package-duplication.md` | **Modify** | Update Status to `Accepted`, record that Option B shipped via `tests/test_persona_package_parity.py`, and narrow the remaining decision to Option C. |
| `docs/superpowers/plans/2026-11-13-whole-repo-refactor.md` | **Modify** | Mark superseded; record the actual canonical package path. |
| `docs/superpowers/plans/2026-11-16-update-every-readme.md` | **Modify** | Mark superseded; correct the merge step to honour `AGENTS.md` rule 5. |
| `pyproject.toml` | **Modify** | Remove the stale `"library"` ruff exclude. |
| `README.md` | **Modify** | Replace the hardcoded metrics block with values generated from `docs/metrics-snapshot.json`. |
| `pr_description.txt` | **Delete** | Remove the leftover PR body from the repository root. |
| `docs/audits/` | **Create** | Consolidated home for the dated coverage and security audit series. |
| `personas/shared/sakthai/` | **Create** (Track C) | Canonical package source; each persona's `sakthai/` becomes a generated artefact, not a tracked copy. |

---

## Track A — Documentation Accuracy

### Task 1: Resolve the Persona-Count Contradiction and Guard It

**Files:**
- Modify: `HOUSE_OF_SAK.md`
- Create: `tests/test_docs_claims_consistency.py`

**Interfaces:**
- Consumes: the on-disk persona roster — `personas/<slug>/` directories that contain a `SOUL.md`.
- Produces: `test_docs_claims_consistency.py::test_governance_docs_agree_with_persona_roster`, asserting every governance document that states a persona count matches disk.

- [ ] **Step 1: Write the failing test**

Create `tests/test_docs_claims_consistency.py`:

```python
"""Governance documents must agree with the persona roster on disk.

``HOUSE_OF_SAK.md`` once claimed five personas and stated that SakTan's
directory had been removed, while ``personas/saktan/`` held 331 files and the
root README claimed six personas online. This test pins the roster count to
disk so the two cannot drift apart again.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"

# Documents that assert a persona count in prose.
COUNT_CLAIMING_DOCS = ("HOUSE_OF_SAK.md", "README.md", "docs/SOUL.md")

# Phrases that assert the roster size.
_COUNT_PATTERNS = (
    re.compile(r"\b(?P<n>Five|Six|seven|\d+)\s+personas?\b", re.IGNORECASE),
    re.compile(r"\b(?P<n>\d+)\s+personas?\s+(?:are|remain)\b", re.IGNORECASE),
)

_WORD_NUMBERS = {"five": 5, "six": 6, "seven": 7}


def _on_disk_persona_count() -> int:
    return sum(
        1 for slug in PERSONAS_DIR.iterdir() if slug.is_dir() and (slug / "SOUL.md").is_file()
    )


class TestDocsClaimsConsistency(unittest.TestCase):
    def test_on_disk_persona_count_is_six(self) -> None:
        self.assertEqual(_on_disk_persona_count(), 6)

    def test_governance_docs_agree_with_persona_roster(self) -> None:
        expected = _on_disk_persona_count()
        for rel in COUNT_CLAIMING_DOCS:
            path = REPO_ROOT / rel
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in _COUNT_PATTERNS:
                for match in pattern.finditer(text):
                    raw = match.group("n")
                    number = _WORD_NUMBERS.get(raw.lower(), None)
                    if number is None and raw.isdigit():
                        number = int(raw)
                    if number is None:
                        continue
                    self.assertEqual(
                        number,
                        expected,
                        f"{rel} claims {number} personas but {expected} exist on disk",
                    )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **FAIL** on `test_governance_docs_agree_with_persona_roster` with `HOUSE_OF_SAK.md claims 5 personas but 6 exist on disk`.

- [ ] **Step 3: Fix `HOUSE_OF_SAK.md`**

In `HOUSE_OF_SAK.md`, replace the paragraph:

```markdown
Five personas remain on disk today (SakTan's persona directory was removed) — all sharing one long-term memory brain, but maintaining separate live sessions. Each agent has its own personality, skill set, and charge cycle — but they share one home, one memory, and one mission: to grow together.
```

with:

```markdown
Six personas remain on disk today — SakThai, SakSee, SakJules, SakKing, SakSit, and SakTan — all sharing one long-term memory brain, but maintaining separate live sessions. Each agent has its own personality, skill set, and charge cycle — but they share one home, one memory, and one mission: to grow together.
```

Also correct the license line in the same file, which currently reads *"The Sak-Family-Agent repository itself is **All Rights Reserved**"* while `LICENSE` ships the House of Sak Intellectual Property License (source-available, no redistribution). Replace it with:

```markdown
- **Repository license:** The Sak-Family-Agent repository itself is distributed under the [House of Sak Intellectual Property License](../LICENSE) — source-available, no redistribution.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **PASS** (2 tests).

- [ ] **Step 5: Commit**

```bash
git add HOUSE_OF_SAK.md tests/test_docs_claims_consistency.py
git commit -m "docs: correct the persona roster in HOUSE_OF_SAK.md and guard it with a test"
```

---

### Task 2: Replace the Un-filled `ONBOARDING.md` Template

**Files:**
- Modify: `ONBOARDING.md`

**Interfaces:**
- Consumes: `AGENTS.md`, `GEMINI.md`, `Makefile` (the real command surface).
- Produces: an onboarding guide with no literal `TODO` or `[Team Name]` placeholders.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_docs_claims_consistency.py`:

```python
    def test_onboarding_has_no_placeholder_tokens(self) -> None:
        path = REPO_ROOT / "ONBOARDING.md"
        text = path.read_text(encoding="utf-8")
        for token in ("[Team Name]", "TODO"):
            self.assertNotIn(
                token,
                text,
                f"ONBOARDING.md still contains the placeholder {token!r}",
            )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_docs_claims_consistency.py::TestDocsClaimsConsistency::test_onboarding_has_no_placeholder_tokens -v`
Expected: **FAIL** with `ONBOARDING.md still contains the placeholder 'TODO'`.

- [ ] **Step 3: Rewrite `ONBOARDING.md`**

Replace the whole file with:

```markdown
# Onboarding onto the House of Sak

> **SakJules · Master of Automation & CI/CD.** Welcome aboard. This guide gets a new
> teammate from a clean machine to a green test run in about ten minutes.

## What you are joining

The House of Sak is a monorepo of six AI agent personas sharing one Python runtime,
one SQLite memory model, and one Next.js dashboard. The canonical package lives at
`personas/sakthai/`; every other persona directory carries a generated copy of it.

## Setup Checklist

### Toolchain

- [ ] `uv --version` — the only supported Python workflow (3.11 or 3.12).
- [ ] `node --version` — Node 22+ for the Next.js 16 dashboard.
- [ ] `cp .env.example .env` — then fill in `ANTHROPIC_API_KEY` and `HF_TOKEN`.
- [ ] `uv sync --all-extras --dev` — installs the `sak` and `sakthai` console scripts.

### Verify the checkout

- [ ] `make test` — full pytest suite, coverage floor ≥ 96%.
- [ ] `make lint` — Ruff lint and format checks.
- [ ] `uv run mypy personas/sakthai` — strict type checking.
- [ ] `cd apps/sak_agent_dashboard && npm ci && npm test` — Vitest suite.

### Learn the layout

- [ ] [`AGENTS.md`](AGENTS.md) — repository rules, including the never-auto-merge rule.
- [ ] [`docs/architecture.md`](docs/architecture.md) — how the pieces fit together.
- [ ] [`docs/capabilities.md`](docs/capabilities.md) — what the agents can actually do.
- [ ] [`docs/adr/ADR-0001-persona-package-duplication.md`](docs/adr/ADR-0001-persona-package-duplication.md) — why five package copies exist and how to mirror them.

## Your first task

Run `sak status`, then `sak "explain docs/architecture.md"`. If both work, the
environment is healthy and you can take a ticket.

## Team tips

- Run one security task at a time. Concurrent edits to `personas/*/agent/guardrails.py` conflict.
- Before opening a PR, check the open PRs for one that already addresses the same file.
- Never merge your own PR. `AGENTS.md` rule 5 requires manual review and merge by Beer.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **PASS** (3 tests).

- [ ] **Step 5: Commit**

```bash
git add ONBOARDING.md tests/test_docs_claims_consistency.py
git commit -m "docs: replace the onboarding template with a real onboarding guide"
```

---

### Task 3: Reconcile ADR-0001 With the Implemented Drift Guard

**Files:**
- Modify: `docs/adr/ADR-0001-persona-package-duplication.md`

**Interfaces:**
- Consumes: `tests/test_persona_package_parity.py` (the full-tree byte-identity test) and `scripts/sync_personas.py`.
- Produces: an ADR whose Status and Options reflect what actually shipped.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_docs_claims_consistency.py`:

```python
    def test_adr_0001_status_is_accepted(self) -> None:
        path = REPO_ROOT / "docs" / "adr" / "ADR-0001-persona-package-duplication.md"
        text = path.read_text(encoding="utf-8")
        self.assertRegex(
            text,
            r"\*\*Status:\*\*\s*Accepted",
            "ADR-0001 still records a stale Status; the decision has been made",
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_docs_claims_consistency.py::TestDocsClaimsConsistency::test_adr_0001_status_is_accepted -v`
Expected: **FAIL** — the ADR reads `**Status:** Proposed`.

- [ ] **Step 3: Update the ADR**

Change the header to:

```markdown
**Status:** Accepted (Option B shipped 2026-11-23; Option C remains open)
```

In the *Context* section, replace the bullet:

```markdown
- **Content parity is CI-enforced for only three files:**
  `agent/guardrails.py` (`test_persona_guardrails_parity.py`), `web/server.py`
  (`test_persona_web_server_parity.py`), and `agent/eval.py`
  (`test_persona_eval_parity.py`).
```

with:

```markdown
- **Content parity is now CI-enforced for the whole package surface.**
  `tests/test_persona_package_parity.py` walks the entire canonical package tree
  and asserts byte-identity for every `.py` in each of the five copies, so a new
  module or subpackage is covered automatically. The three narrower
  content-pinned tests (`test_persona_guardrails_parity.py`,
  `test_persona_web_server_parity.py`, `test_persona_eval_parity.py`) remain.
```

Add a new *Decision update* subsection at the end of the *Decision* section:

```markdown
### Decision update (2026-11-23)

Option B is **shipped**: `tests/test_persona_package_parity.py` closes the
silent-drift gap that this ADR originally identified, so the "immediate" half of
the two-step path is complete and no further work is needed there.

The remaining decision is **Option C only** — migrating the package code onto
the overlay/compose model that `scripts/compose_persona.py` already provides for
skills. See Task 10 of the repository improvement plan
(`docs/superpowers/plans/2026-11-23-repo-improvement-plan.md`).
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **PASS** (4 tests).

- [ ] **Step 5: Commit**

```bash
git add docs/adr/ADR-0001-persona-package-duplication.md tests/test_docs_claims_consistency.py
git commit -m "docs(adr): record that ADR-0001 Option B shipped via the full-tree parity test"
```

---

### Task 4: Retire the Two Stale Executable Plans

**Files:**
- Modify: `docs/superpowers/plans/2026-11-13-whole-repo-refactor.md`
- Modify: `docs/superpowers/plans/2026-11-16-update-every-readme.md`

**Interfaces:**
- Consumes: the current tree layout and `AGENTS.md` rule 5.
- Produces: both plans marked superseded, so no agent re-runs them verbatim.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_docs_claims_consistency.py`:

```python
    def test_stale_plans_are_marked_superseded(self) -> None:
        stale = (
            "docs/superpowers/plans/2026-11-13-whole-repo-refactor.md",
            "docs/superpowers/plans/2026-11-16-update-every-readme.md",
        )
        for rel in stale:
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            self.assertIn(
                "Superseded",
                text[:2000],
                f"{rel} must carry a superseded banner in its first 2000 characters",
            )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_docs_claims_consistency.py::TestDocsClaimsConsistency::test_stale_plans_are_marked_superseded -v`
Expected: **FAIL** — neither plan contains the word `Superseded`.

- [ ] **Step 3: Mark both plans superseded**

Insert immediately after the H1 title of `docs/superpowers/plans/2026-11-13-whole-repo-refactor.md`:

```markdown
> **⚠️ SUPERSEDED (2026-11-23).** This plan predates the current layout. Its canonical
> package path `personas/sakthai/sakthai/` never existed and has been replaced by
> `personas/sakthai/` (mapped by the root `pyproject.toml` `[tool.setuptools] package-dir`).
> `apps/agent_workflow_framework/` and `infra/hermes-agents/` no longer exist. The one
> still-live piece — full-tree package parity — shipped as
> `tests/test_persona_package_parity.py`; see
> [`docs/adr/ADR-0001-persona-package-duplication.md`](../../adr/ADR-0001-persona-package-duplication.md).
> Do not execute the steps below verbatim.
```

Insert immediately after the H1 title of `docs/superpowers/plans/2026-11-16-update-every-readme.md`:

```markdown
> **⚠️ SUPERSEDED (2026-11-23).** The README work this plan describes has largely landed —
> the root README now carries verified skill, persona, and test-file counts. The plan's
> Task 6 Step 4 prescribes `gh pr merge --merge --delete-branch --admin`, which **conflicts
> with `AGENTS.md` rule 5** (never auto-merge; a human merges). `apps/agent_workflow_framework/`
> and `personas/sakthai/sakthai/` no longer exist, and the "2,823+ tests" figure is stale.
> Do not execute the steps below verbatim.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **PASS** (5 tests).

- [ ] **Step 5: Commit**

```bash
git add docs/superpowers/plans/2026-11-13-whole-repo-refactor.md docs/superpowers/plans/2026-11-16-update-every-readme.md tests/test_docs_claims_consistency.py
git commit -m "docs(plans): mark the two stale executable plans as superseded"
```

---

## Track B — Packaging & Release Integrity

### Task 5: Establish One Source of Truth for Version and Install Path

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `README.md`
- Test: `tests/test_docs_claims_consistency.py`

**Interfaces:**
- Consumes: `pyproject.toml` `version`, `list_releases` (currently empty).
- Produces: `test_version_claims_match_pyproject`, asserting the README's version string equals the package version.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_docs_claims_consistency.py`:

```python
    def test_version_claims_match_pyproject(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        declared = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE)
        self.assertIsNotNone(declared, "root pyproject.toml must declare a version")
        version = declared.group(1)

        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn(
            f"version is `{version}`",
            readme,
            f"README must state the package version {version} from pyproject.toml",
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_docs_claims_consistency.py::TestDocsClaimsConsistency::test_version_claims_match_pyproject -v`
Expected: **FAIL** — the README states no `vX.Y.Z` matching the declared `2.0.0`.

- [ ] **Step 3: Fix the version claim and the changelog lag**

In `README.md`, the badge line already reads `package_version-2.0.0`. Leave the badge and instead make the surrounding statement explicit — the `Recent Activity & Governance` section must say:

```markdown
> **No GitHub Release has been published for this repository yet.** The package version is
> `2.0.0` (root `pyproject.toml`); release notes are tracked in [`CHANGELOG.md`](CHANGELOG.md).
```

In `CHANGELOG.md`, replace the existing lag notice:

```markdown
> This changelog has lagged the repository. The entries below cover the early
> v2 rewrite; the bulk of what landed since — the six-persona layout, per-persona
> memory sharding, the guardrails hardening rounds, the dashboard web API — is
> recorded in `PLAN.md`'s status table and the dated audits under `docs/`
> rather than here.
```

with:

```markdown
> This changelog covers the early v2 rewrite. The work that landed since — the
> six-persona layout, per-persona memory sharding, the guardrails hardening
> rounds, and the dashboard web API — is summarised in the `Unreleased` section
> below and recorded in `PLAN.md`'s status table and the dated audits under
> `docs/`.

### Unreleased (since 2.0.0)

- **Six-persona layout.** `personas/` now carries SakThai, SakSee, SakJules,
  SakKing, SakSit, and SakTan, each with its own `SOUL.md`, skills overlay,
  `config/`, and `evolution/` directory. The installable package is
  `personas/sakthai/`, mapped by the root `pyproject.toml` `[tool.setuptools]`
  `package-dir`.
- **Per-persona memory sharding.** Each persona persists to
  `~/.sakthai/<persona>/memory.db`; `sakthai memory family` reads across all six.
- **Guardrails hardening.** Concentric `GuardrailPolicy` enforcement on the agent
  loop, the MCP server, and the Runtime Gateway, with `DataLossGuardrail` HMAC
  approval tokens and path jailing on file reads.
- **Dashboard web API.** `/api/personas`, `/api/metrics`, `/api/sessions`,
  `/api/memory`, `/api/audit`, `/api/workflows`, shaped by `web/contracts.py` and
  consumed by the Next.js 16 dashboard.
- **Runtime Gateway.** An OpenAI-compatible `/v1` surface (`sakthai.gateway`)
  with SSE streaming, per-persona routing, and constant-time bearer auth.
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_docs_claims_consistency.py -v`
Expected: **PASS** (6 tests).

- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md README.md tests/test_docs_claims_consistency.py
git commit -m "docs: align the version claim and close the changelog lag"
```

---

### Task 6: Remove the Stale `library` Ruff Exclude and Guard the Layout

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/test_repo_layout_drift.py`
- Modify: `README.md`

**Interfaces:**
- Consumes: the root `pyproject.toml` `[tool.ruff] exclude` list and the README's Repository Layout block.
- Produces: `tests/test_repo_layout_drift.py` with two tests: ruff excludes and README layout both name only existing directories.

- [ ] **Step 1: Write the failing test**

Create `tests/test_repo_layout_drift.py`:

```python
"""Configuration and documentation must not name directories that do not exist.

The root ``pyproject.toml`` ruff ``exclude`` list carried ``"library"`` long
after the directory was removed, and the README's Repository Layout block
advertised it as "Curated library of 31 reusable agent skills".
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


class TestRepoLayoutDrift(unittest.TestCase):
    def test_ruff_exclude_names_only_existing_paths(self) -> None:
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
        match = re.search(r"^exclude\s*=\s*\[(.*?)\]", pyproject, re.MULTILINE | re.DOTALL)
        self.assertIsNotNone(match, "root pyproject.toml must declare a ruff exclude list")
        entries = re.findall(r'"([^"]+)"', match.group(1))
        for entry in entries:
            if "*" in entry:
                continue
            self.assertTrue(
                (REPO_ROOT / entry).exists(),
                f"ruff exclude names '{entry}', which does not exist on disk",
            )

    def test_readme_layout_names_only_existing_directories(self) -> None:
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        marker = "## Repository Layout"
        self.assertIn(marker, readme, "README must contain a Repository Layout section")
        # Anchor on the section: the README also contains an earlier ```text block
        # (the OpenEnv model-pipeline diagram) that must not be parsed as a layout.
        section = readme.split(marker, 1)[1]
        block = re.search(r"```text\n(.*?)```", section, re.DOTALL)
        self.assertIsNotNone(block, "Repository Layout must contain a ```text block")
        for line in block.group(1).splitlines():
            if not line.strip() or line.strip().startswith("#"):
                continue
            path = line.split()[0].rstrip("/")
            if not path or "<" in path or ">" in path:
                continue
            self.assertTrue(
                (REPO_ROOT / path).exists(),
                f"README layout lists '{path}', which does not exist on disk",
            )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_repo_layout_drift.py -v`
Expected: **FAIL** — `ruff exclude names 'library', which does not exist on disk`.

- [ ] **Step 3: Remove the stale exclude and fix the README layout**

In `pyproject.toml`, change:

```toml
exclude = ["library", "scripts", "personas/*/skills", "personas/*/evolution", "personas/*/tests"]
```

to:

```toml
exclude = ["scripts", "personas/*/skills", "personas/*/evolution", "personas/*/tests"]
```

In `README.md`, the Repository Layout block was already corrected by the 2026-11-23 refresh; confirm the `library/` line is gone and that the following note is present:

```markdown
> **The `library/` directory no longer exists.** It was superseded by `personas/shared/skills/` (the universal shared skill set) and is referenced only by a stale `exclude` entry in the root `pyproject.toml` ruff configuration.
```

With the exclude removed, soften that note's second clause to:

```markdown
> **The `library/` directory no longer exists.** It was superseded by `personas/shared/skills/` (the universal shared skill set).
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_repo_layout_drift.py -v`
Expected: **PASS** (2 tests).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md tests/test_repo_layout_drift.py
git commit -m "fix(config): drop the stale library ruff exclude and guard the repo layout"
```

---

### Task 7: Purge the Root Scratch Artifact

**Files:**
- Delete: `pr_description.txt`
- Create: `tests/test_repo_hygiene.py` (extend if it already exists — it does, at `tests/test_repo_hygiene.py`)

**Interfaces:**
- Consumes: the repository root file list.
- Produces: `test_no_root_scratch_artifacts`, asserting no stray PR bodies or scratch text files sit at the root.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_repo_hygiene.py`:

```python
def test_no_root_scratch_artifacts() -> None:
    """No PR bodies or scratch text files at the repository root.

    ``pr_description.txt`` (2,353 bytes) was a leftover PR body committed at the
    root. Anything matching these patterns is scratch, not source.
    """
    forbidden = ("pr_description.txt", "*.tmp", "*.bak", "scratch*.md")
    for pattern in forbidden:
        matches = REPO_ROOT.glob(pattern)
        assert not list(matches), f"scratch artifact at repository root: {pattern}"
```

If `tests/test_repo_hygiene.py` does not already define `REPO_ROOT`, add:

```python
REPO_ROOT = Path(__file__).resolve().parents[1]
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_repo_hygiene.py::test_no_root_scratch_artifacts -v`
Expected: **FAIL** with `scratch artifact at repository root: pr_description.txt`.

- [ ] **Step 3: Delete the artifact**

```bash
git rm pr_description.txt
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest tests/test_repo_hygiene.py -v`
Expected: **PASS**.

- [ ] **Step 5: Commit**

```bash
git add tests/test_repo_hygiene.py
git commit -m "chore: remove the leftover PR description from the repository root"
```

---

### Task 8: Generate the README Metrics Instead of Hardcoding Them

**Files:**
- Create: `scripts/gen_readme_metrics.py`
- Create: `docs/metrics-snapshot.json`
- Modify: `README.md`
- Modify: `Makefile`

**Interfaces:**
- Consumes: the repository tree at `REPO_ROOT`.
- Produces: `docs/metrics-snapshot.json` with keys `personas`, `skills`, `shared_skills`, `pytest_files`, `dashboard_suites`, `workflows`, `package_version`; and `scripts/gen_readme_metrics.py --check`, which exits non-zero when the snapshot is stale.

- [ ] **Step 1: Write the script**

Create `scripts/gen_readme_metrics.py`:

```python
#!/usr/bin/env python3
"""Compute the README's headline numbers from the tree.

The root README carried hand-maintained counts (skills, personas, tests,
workflows) that silently drifted from disk. This script derives them, writes
``docs/metrics-snapshot.json``, and ``--check`` fails when the committed
snapshot is stale — which is what CI should run.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = REPO_ROOT / "docs" / "metrics-snapshot.json"
PERSONA_DIRS = ("sakthai", "saksee", "sakjules", "sakking", "saksit", "saktan")


def _count_skills(persona: str) -> int:
    base = REPO_ROOT / "personas" / persona / "skills"
    if not base.is_dir():
        return 0
    return sum(1 for _ in base.glob("*/SKILL.md"))


def collect() -> dict[str, object]:
    per_persona = {p: _count_skills(p) for p in PERSONA_DIRS}
    shared_base = REPO_ROOT / "personas" / "shared" / "skills"
    shared = sum(1 for _ in shared_base.glob("*/SKILL.md")) if shared_base.is_dir() else 0
    pytest_files = sum(1 for _ in (REPO_ROOT / "tests").rglob("*.py"))
    dashboard_suites = sum(
        1
        for p in (REPO_ROOT / "apps" / "sak_agent_dashboard").rglob("*.test.ts*")
        if "node_modules" not in p.parts and ".next" not in p.parts
    )
    workflows = sum(1 for p in (REPO_ROOT / ".github" / "workflows").glob("*.yml"))
    pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    version = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.MULTILINE).group(1)
    return {
        "personas": len(PERSONA_DIRS),
        "skills": sum(per_persona.values()),
        "shared_skills": shared,
        "per_persona_skills": per_persona,
        "pytest_files": pytest_files,
        "dashboard_suites": dashboard_suites,
        "workflows": workflows,
        "package_version": version,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if the snapshot is stale")
    args = parser.parse_args()

    metrics = collect()
    payload = json.dumps(metrics, indent=2, sort_keys=True) + "\n"

    if args.check:
        if not SNAPSHOT.is_file():
            print(f"{SNAPSHOT} does not exist; run scripts/gen_readme_metrics.py")
            return 1
        if SNAPSHOT.read_text(encoding="utf-8") != payload:
            print("docs/metrics-snapshot.json is stale; re-run scripts/gen_readme_metrics.py")
            return 1
        print("docs/metrics-snapshot.json is up to date")
        return 0

    SNAPSHOT.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(payload, encoding="utf-8")
    print(f"wrote {SNAPSHOT.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Generate the snapshot**

Run: `uv run python scripts/gen_readme_metrics.py`
Expected: `wrote docs/metrics-snapshot.json`.

- [ ] **Step 3: Verify the snapshot matches the tree**

Run: `uv run python scripts/gen_readme_metrics.py --check`
Expected: `docs/metrics-snapshot.json is up to date`.

- [ ] **Step 4: Reference the snapshot from the README**

In `README.md`, add to the `Development & Verification` block:

```bash
uv run python scripts/gen_readme_metrics.py            # refresh docs/metrics-snapshot.json
uv run python scripts/gen_readme_metrics.py --check    # fail if the snapshot is stale
```

And add a note under the badge bar:

```markdown
> **Metrics in this README are generated.** The persona, skill, test-file, and workflow
> counts below come from [`docs/metrics-snapshot.json`](docs/metrics-snapshot.json),
> produced by `scripts/gen_readme_metrics.py`. Refresh them with
> `uv run python scripts/gen_readme_metrics.py`; CI fails when the snapshot is stale.
```

- [ ] **Step 5: Wire the staleness check into CI**

In `.github/workflows/ci.yml`, add a step to the `test` job, immediately after *Install dependencies*:

```yaml
      - name: Verify README metrics snapshot is current
        run: uv run --locked python scripts/gen_readme_metrics.py --check
```

- [ ] **Step 6: Commit**

```bash
git add scripts/gen_readme_metrics.py docs/metrics-snapshot.json README.md Makefile .github/workflows/ci.yml
git commit -m "feat(docs): generate the README metrics from the tree and gate them in CI"
```

---

## Track C — Structural De-duplication

### Task 9: Consolidate the Dated Audit Series

**Files:**
- Create: `docs/audits/README.md`
- Move: `docs/test-coverage-audit-*.md` → `docs/audits/`
- Move: `docs/security_audit_*.md` → `docs/audits/`
- Move: `docs/repo-audit-2026-08-08.md` → `docs/audits/`

**Interfaces:**
- Consumes: 8 dated audit documents at `docs/` root.
- Produces: a single `docs/audits/` directory with an index, leaving 57 Markdown files at `docs/` root.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_repo_layout_drift.py`:

```python
    def test_dated_audits_are_consolidated(self) -> None:
        docs_root = REPO_ROOT / "docs"
        stragglers = [
            p.name
            for p in docs_root.glob("*.md")
            if re.search(r"(test-coverage-audit|security_audit|repo-audit)", p.name)
        ]
        self.assertEqual(
            stragglers,
            [],
            f"dated audit documents must live in docs/audits/, found {stragglers}",
        )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_repo_layout_drift.py::TestRepoLayoutDrift::test_dated_audits_are_consolidated -v`
Expected: **FAIL** listing the 8 straggler files.

- [ ] **Step 3: Move the audits and write the index**

```bash
mkdir -p docs/audits
git mv docs/test-coverage-audit-*.md docs/audits/
git mv docs/security_audit_*.md docs/audits/
git mv docs/repo-audit-2026-08-08.md docs/audits/
```

Create `docs/audits/README.md`:

```markdown
# Dated Audits

Point-in-time analyses of the House of Sak repository. Each document records
what was true on its measurement date; none of them is a live status report.
The live status lives in [`../PLAN.md`](../PLAN.md), the root
[`README.md`](../../README.md), and the `docs/metrics-snapshot.json` snapshot.

## Coverage series

Five consecutive runs of the same analysis, each re-verifying the previous
finding and asking one new question.

| Date | Branch coverage | Uncovered statements | Partial branches |
| :--- | ---: | ---: | ---: |
| [2026-08-26](test-coverage-audit-2026-08-26.md) | 96.018% | 168 | 149 |
| [2026-08-27](test-coverage-audit-2026-08-27.md) | 95.849% | 213 | 170 |
| [2026-08-28](test-coverage-audit-2026-08-28.md) | 95.862% | 213 | 170 |
| [2026-08-31](test-coverage-audit-2026-08-31.md) | 96.211% | 191 | 156 |
| [2026-09-01](test-coverage-audit-2026-09-01.md) | 96.211% | 191 | 156 |

The most recent measurement is **96.21%** branch coverage. The standing findings
worth carrying forward: the suite is **not hermetic** (`tests/test_cli.py` reaches
the public npm registry mid-run), and the 96% discipline has historically applied
only to the core package rather than the whole repository.

## Security series

| Date | Document | Scope |
| :--- | :--- | :--- |
| 2026-07-11 | [security_audit_2026-07-11.md](security_audit_2026-07-11.md) | First hardening round |
| 2026-07-12 | [security_audit_2026-07-12.md](security_audit_2026-07-12.md) | Follow-up round |

## Other

| Date | Document | Scope |
| :--- | :--- | :--- |
| 2026-08-08 | [repo-audit-2026-08-08.md](repo-audit-2026-08-08.md) | Whole-repository audit |
| 2026-11-19 | [../workflow-dependency-security-audit-2026-11-19.md](../workflow-dependency-security-audit-2026-11-19.md) | Workflow dependency supply chain |
```

- [ ] **Step 4: Fix the inbound links**

The moved documents reference each other by relative path. Rewrite the references
from `docs/` to `docs/audits/`:

```bash
grep -rl "test-coverage-audit-2026-0" docs/audits/ | xargs sed -i 's|(\./test-coverage-audit-|(./test-coverage-audit-|g'
```

Confirm no dangling inbound links remain from `docs/` root:

```bash
grep -rn "test-coverage-audit\|security_audit_2026\|repo-audit-2026-08-08" docs/*.md README.md PLAN.md
```

Expected: any hit must point at `docs/audits/...`; otherwise update it.

- [ ] **Step 5: Run the test to verify it passes**

Run: `uv run pytest tests/test_repo_layout_drift.py -v`
Expected: **PASS** (3 tests).

- [ ] **Step 6: Commit**

```bash
git add docs/audits/ docs/ tests/test_repo_layout_drift.py
git commit -m "docs: consolidate the dated audit series into docs/audits/"
```

---

### Task 10: Migrate the Package Copies From *Copy* to *Generate* (ADR-0001 Option C)

**Files:**
- Create: `scripts/compose_persona_package.py`
- Modify: `scripts/sync_personas.py`
- Modify: `scripts/compose_persona.py`
- Create: `tests/test_persona_package_generation.py`
- Modify: `.gitignore`
- Modify: `Makefile`
- Modify: `docs/adr/ADR-0001-persona-package-duplication.md`

**Interfaces:**
- Consumes: `personas/sakthai/` (canonical) and the per-persona overlay set — `SOUL.md`, `skills/`, `config/`, `evolution/`, `tests/`.
- Produces: `make compose-persona-packages`, which materialises `personas/<slug>/{agent,cli,memory,mcp,gateway,agent_platform,…}` from the canonical package for any persona that does not already have one; the generated trees are git-ignored, and `tests/test_persona_package_generation.py` asserts the canonical package is the only tracked copy.

> **This is the highest-risk task in the plan.** It removes ~655 tracked duplicate `.py` files. Do not run it in the same PR as any other task, and do not run it until Task 3 has recorded the ADR's updated status.

- [ ] **Step 1: Write the failing test**

Create `tests/test_persona_package_generation.py`:

```python
"""Only the canonical package tree may be tracked in git.

ADR-0001 Option C: the five persona copies of the ``sakthai`` package are
generated artefacts, not source. This test asserts that the copies are not
tracked, that the canonical package is, and that generating a copy produces a
byte-identical tree.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "sakthai"
COPIES = ("sakking", "saksee", "saksit", "sakjules", "saktan")

# Per-persona directories that are genuinely unique and must never be synced.
PER_PERSONA_DIRS = frozenset({"skills", "config", "evolution", "tests"})


def _tracked_files() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return set(out.stdout.splitlines())


class TestPersonaPackageGeneration(unittest.TestCase):
    def test_copies_are_not_tracked_in_git(self) -> None:
        tracked = _tracked_files()
        offenders = sorted(
            p
            for p in tracked
            if p.startswith("personas/")
            and p.split("/")[1] in COPIES
            and p.endswith(".py")
            and not any(f"/{d}/" in p for d in PER_PERSONA_DIRS)
        )
        self.assertEqual(
            offenders,
            [],
            f"{len(offenders)} duplicated package files are still tracked; "
            "run `make compose-persona-packages` and `git rm --cached` them",
        )

    def test_canonical_package_is_tracked(self) -> None:
        tracked = _tracked_files()
        canonical = [
            p for p in tracked if p.startswith(f"personas/{CANONICAL}/") and p.endswith(".py")
        ]
        self.assertGreater(len(canonical), 100, "canonical package must stay tracked")

    def test_generated_copy_is_byte_identical(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from compose_persona_package import compose_package  # noqa: PLC0415

        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "sakking"
            compose_package(REPO_ROOT / "personas" / CANONICAL, out)
            for src in sorted((REPO_ROOT / "personas" / CANONICAL).rglob("*.py")):
                rel = src.relative_to(REPO_ROOT / "personas" / CANONICAL)
                if rel.parts[0] in PER_PERSONA_DIRS:
                    continue
                self.assertTrue((out / rel).is_file(), f"generated tree missing {rel}")
                self.assertEqual(
                    src.read_bytes(),
                    (out / rel).read_bytes(),
                    f"{rel} differs between canonical and generated copy",
                )
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest tests/test_persona_package_generation.py -v`
Expected: **FAIL** — `test_copies_are_not_tracked_in_git` lists the duplicated files.

- [ ] **Step 3: Write the generator**

Create `scripts/compose_persona_package.py`:

```python
#!/usr/bin/env python3
"""Materialise a persona's package tree from the canonical ``sakthai`` package.

Mirrors what ``scripts/compose_persona.py`` already does for skills: the shared
source lives once, and the per-persona tree is generated on demand. Per-persona
directories (skills, config, evolution, tests) are never touched.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PER_PERSONA_DIRS = frozenset({"skills", "config", "evolution", "tests"})


def _is_generated(rel: Path) -> bool:
    if not rel.suffix == ".py":
        return False
    return rel.parts[0] not in PER_PERSONA_DIRS


def compose_package(canonical: Path, destination: Path) -> None:
    """Copy every package-code ``.py`` from *canonical* into *destination*."""
    for src in sorted(canonical.rglob("*.py")):
        rel = src.relative_to(canonical)
        if not _is_generated(rel):
            continue
        dst = destination / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: compose_persona_package.py <canonical-persona> <destination-persona>")
        return 2
    canonical = Path(sys.argv[1])
    destination = Path(sys.argv[2])
    compose_package(canonical, destination)
    print(f"composed package for {destination.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Wire the Makefile target and the ignore rules**

Append to `Makefile`:

```make
compose-persona-packages:
	@echo "Composing persona package trees from the canonical package..."
	@for persona in sakking saksee saksit saktan sakjules; do \
		python3 scripts/compose_persona_package.py personas/sakthai personas/$$persona; \
	done
```

Append to `.gitignore`:

```gitignore
# Generated persona package trees — produced by `make compose-persona-packages`.
# The canonical source of truth is personas/sakthai/; see
# docs/adr/ADR-0001-persona-package-duplication.md.
personas/sakking/agent/
personas/sakking/cli/
personas/sakking/memory/
personas/sakking/mcp/
personas/sakking/gateway/
personas/sakking/agent_platform/
personas/sakking/team/
personas/sakking/web/
personas/sakking/telegram/
personas/sakking/cycle/
personas/sakking/client/
personas/sakking/coding/
personas/sakking/dashboard/
personas/sakking/devops/
personas/sakking/extensions/
personas/sakking/learn/
personas/sakking/lead/
personas/sakking/llm/
personas/sakking/automation/
personas/sakking/learning/
```

(Repeat the same block for `saksee`, `saksit`, `saktan`, `sakjules`.)

- [ ] **Step 5: Untrack the duplicated copies**

```bash
python3 scripts/compose_persona_package.py personas/sakthai personas/sakking
git rm -r --cached personas/sakking/agent personas/sakking/cli personas/sakking/memory \
    personas/sakking/mcp personas/sakking/gateway personas/sakking/agent_platform \
    personas/sakking/team personas/sakking/web personas/sakking/telegram \
    personas/sakking/cycle personas/sakking/client personas/sakking/coding \
    personas/sakking/dashboard personas/sakking/devops personas/sakking/extensions \
    personas/sakking/learn personas/sakking/lead personas/sakking/llm \
    personas/sakking/automation personas/sakking/learning
```

Repeat for `saksee`, `saksit`, `saktan`, `sakjules`.

- [ ] **Step 6: Replace the byte-parity test with the generation test**

`tests/test_persona_package_parity.py` byte-compares files that are no longer
tracked. Replace its assertions with a call into the generator:

```python
    def test_every_canonical_py_is_byte_identical_in_each_copy(self) -> None:
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from compose_persona_package import compose_package  # noqa: PLC0415

        import tempfile

        for persona in COPIES:
            with tempfile.TemporaryDirectory() as tmp:
                out = Path(tmp) / persona
                compose_package(self.canonical_root, out)
                for rel in sorted(self.canonical_files):
                    self.assertTrue((out / rel).is_file(), f"{persona}: missing {rel}")
                    self.assertEqual(
                        (self.canonical_root / rel).read_bytes(),
                        (out / rel).read_bytes(),
                        f"personas/{persona}/{rel} differs from canonical",
                    )
```

- [ ] **Step 7: Run the tests to verify they pass**

Run: `uv run pytest tests/test_persona_package_generation.py tests/test_persona_package_parity.py -v`
Expected: **PASS**.

- [ ] **Step 8: Update the ADR to close the decision**

In `docs/adr/ADR-0001-persona-package-duplication.md`, change the Status line to:

```markdown
**Status:** Accepted (Option B shipped 2026-11-23; Option C shipped 2026-11-23)
```

and append to the *Decision* section:

```markdown
### Option C landed (2026-11-23)

The package code is now generated, not copied. `personas/sakthai/` is the only
tracked package tree; the five persona copies are produced by
`make compose-persona-packages` (`scripts/compose_persona_package.py`) and are
git-ignored. `tests/test_persona_package_generation.py` asserts that only the
canonical tree is tracked and that a generated copy is byte-identical. This
removes roughly 655 duplicated tracked `.py` files and eliminates the drift risk
entirely: there is now exactly one copy of the code in the repository.
```

- [ ] **Step 9: Verify the whole suite still passes**

Run: `uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/`
Expected: **PASS**, coverage ≥ 96.0%.

- [ ] **Step 10: Commit**

```bash
git add -A
git commit -m "refactor(personas): generate the persona package trees instead of tracking copies"
```

---

## Verification

Run after every task and before the final PR:

```bash
uv sync --all-extras --dev
uv run ruff check personas/sakthai tests scripts
uv run ruff format --check personas/sakthai tests scripts
uv run mypy
uv run bandit -c pyproject.toml -r personas/sakthai
uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/
uv run python scripts/gen_readme_metrics.py --check
git diff --check
```

Expected: no lint, type, or security findings; the full suite green with coverage
at or above the 96% floor; the metrics snapshot current; zero whitespace errors.

## Execution Order

| Task | Track | Risk | Mergeable independently |
| :-- | :-- | :-- | :--: |
| 1. Persona roster contradiction | A | Low | Yes |
| 2. `ONBOARDING.md` template | A | Low | Yes |
| 3. ADR-0001 reconciliation | A | Low | Yes |
| 4. Retire stale plans | A | Low | Yes |
| 5. Version & changelog single source | B | Low | Yes |
| 6. Stale `library` exclude + layout guard | B | Low | Yes |
| 7. Root scratch artifact | B | Low | Yes |
| 8. Generated README metrics + CI gate | B | Medium | Yes |
| 9. Consolidate the audit series | B | Low | Yes |
| 10. Package copy → generate (Option C) | C | **High** | No — land last, on its own PR |

Tasks 1–9 may run in parallel across separate branches, because each touches a
distinct set of files and each ships its own regression test. Task 10 must not
share a PR with anything else.

## Pull Request Protocol

Per `AGENTS.md` and `GEMINI.md`:

1. Branch from `main` with a `docs/`, `fix/`, or `refactor/` prefix.
2. Open a PR describing the problem, the change, and the **actual** verification commands and their output.
3. Wait for CI to go green, then **stop**.
4. **Never merge automatically.** Do not run `gh pr merge` or `--auto`. Leave the
   PR open for Beer (`beer-sakthai`) to review and merge by hand — `AGENTS.md` rule 5.
