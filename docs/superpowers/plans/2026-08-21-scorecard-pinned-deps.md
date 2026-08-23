# Scorecard Pinned-Dependency Remediation — 2026-08-21

Status: COMPLETE (2026-08-21)

## Goal

Clear the actionable OpenSSF Scorecard code-scanning alerts on `main` for
`PinnedDependenciesID`, and document the rest as accepted risk or an upstream
limitation. This plan covers the **code PR** only; repo-settings hardening
(branch protection, CII badge) is tracked separately below.

## Findings (from code-scanning API, 2026-08-21)

23 open Scorecard alerts on `main` (commit `aa2c523`):

- 1 critical: `DangerousWorkflowID` — `self-healing-ci.yml:83` untrusted checkout
  (already guarded by fork check + pinned by `test_workflow_hygiene.py`) → accepted risk
- 18 medium: `PinnedDependenciesID`
  - 2 × `apps/sak_agent_dashboard/Dockerfile` — `node:22.22.2-slim` not pinned by digest
  - 16 × gh-aw `.lock.yml` — `npm install -g @google/gemini-cli@0.55.1` not pinned by hash
    (**NOT source-fixable**: line is injected by gh-aw at compile time, not in any `.md`)
  - 1 × root `Dockerfile:46` — `pip install -e "."` (local editable install) → accepted risk
- 1 high: `CodeReviewID` (0/7 approved changesets) — repo policy matter
- 1 high: `BranchProtectionID` (main not maximal) — repo settings matter
- 1 medium: `SASTID` (26/30 commits covered) — partial coverage
- 1 low: `CIIBestPracticesID` (badge InProgress)

## What was done

### Code PR — merged as #1082 (`a220a4f2`, 2026-08-21)

Pin the base image by digest in the dashboard Dockerfile:

- `apps/sak_agent_dashboard/Dockerfile`
  - `FROM node:22.22.2-slim AS builder`
    → `FROM node:22.22.2-slim@sha256:9f6d5975c7dca860947d3915877f85607946403fc55349f39b4bc3688448bb6e AS builder`
  - `FROM node:22.22.2-slim AS runner`
    → same digest appended

Digest verified against the Docker Hub registry API (matches the
`docker-content-digest` header for `node:22.22.2-slim`).
Closes Scorecard alerts #21560/#21561.

Also added an accepted-risk note to `docs/gh-aw-engines.md` documenting the
16 gh-aw `gemini-cli` npm alerts as an upstream (non-source-fixable) limitation.

Verification: `uv run pytest tests/test_workflow_hygiene.py
tests/test_repo_parses.py tests/test_persona_guardrails_parity.py` →
**1341 passed, 14 skipped**.

### Repo settings — applied 2026-08-21

`main` branch protection hardened (was entirely unprotected):

- 1 required approving review, dismiss stale reviews, require last-push approval
- enforce admins, block force pushes, block deletions
- require conversation resolution
- required checks: `test (3.11)`, `test (3.12)`, `build (3.11)`, `build (3.12)`, `gitleaks`

## Accepted risk (documented, not fixed)

- gh-aw `npm install -g @google/gemini-cli` (16 alerts): injected by the gh-aw
  compiler from engine config; no author-side knob in the `.md` sources; npm
  global installs do not accept `pkg@sha256:` for registry packages. Documented
  in `docs/gh-aw-engines.md` as an upstream limitation.
- Root `Dockerfile:46` `pip install --no-cache-dir -e "."`: local editable
  install of the package itself; not a third-party download, so hash-pinning is
  inapplicable.
- `self-healing-ci.yml` untrusted checkout: guarded by
  `head_repository.full_name == github.repository` and covered by the fork-guard
  test in `tests/test_workflow_hygiene.py`.
- `CodeReviewID` / `SASTID` / `CIIBestPracticesID`: repo policy / badge matters,
  not code fixes.
