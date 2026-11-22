# House of Sak — GitHub Workflows & Action Cache Optimization Specification

> **Date**: 2026-11-16
> **Status**: Approved
> **Target Repository**: `Sak-Family-Agent`
> **Monorepo Root**: `/home/sak/Sak-Family-Agent`
> **Cost Policy**: $0.00 USD Financial Spend (100% Local & Free Tier Execution)

---

## 1. Problem Statement & Motivation

The `Sak-Family-Agent` repository orchestrates extensive CI/CD validation across 36 active GitHub Actions workflows. Over time, workflow caching and execution hygiene developed specific structural bottlenecks:

1. **Redundant & Conflicting Caches**:
   - `verify-assets.yml` and `continuous-security.yml` configure a manual `actions/cache` step pointing to `~/.cache/uv`.
   - Concurrently, `astral-sh/setup-uv` manages its own cache directory at `/home/runner/work/_temp/setup-uv-cache` and generates native `setup-uv-2-...` cache keys.
   - This creates duplicate cache uploads, key conflicts, and unnecessary post-job cache save overhead.
2. **Implicit uv Cache Configuration**:
   - Across 8 other CI workflows (`ci.yml`, `pylint.yml`, `sak-family-agent-contract.yml`, `repository-security-quality.yml`, `dependency-audit.yml`, `run-evals.yml`, `subprojects.yml`, `huggingface-integration.yml`), `astral-sh/setup-uv` is invoked without explicit `enable-cache` and `cache-dependency-glob` declarations.
3. **Severe Cache Accumulation & Storage Bloat**:
   - GitHub Actions storage currently holds **280 caches occupying over ~4.6 GB** of the repository's 10 GB quota.
   - A large fraction consists of stale `codeql-overlay` and `setup-uv` caches belonging to historical or merged pull requests (`refs/pull/*/merge`). GitHub does not delete PR caches when a PR merges or closes until the 7-day TTL or 10 GB LRU limit evicts them.
4. **Missing Concurrency Control**:
   - `code-review.yml` (triggered on `issue_comment`) is the sole active workflow lacking a `concurrency` block, leading to racing parallel runs on rapid successive comments.

---

## 2. Architectural Goals & Success Metrics

1. **Zero Redundancy**: Eliminate manual `actions/cache` steps that duplicate `setup-uv` native caching.
2. **Deterministic uv Caching**: Standardize `astral-sh/setup-uv` across all 10 Python CI workflows with explicit `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
3. **Event-Driven PR Cache Eviction**: Add a self-healing, automated workflow (`cache-cleanup.yml`) that triggers on `pull_request: [closed]` to purge all caches under `refs/pull/<PR>/merge`.
4. **Backlog Pruning**: Immediately prune existing dead caches, reclaiming ~4.6 GB of storage.
5. **Workflow Concurrency**: Add PR-scoped concurrency with `cancel-in-progress: true` to `code-review.yml`.
6. **Strict Invariant & Quality Preservation**:
   - 100% passing tests (`uv run pytest --cov=sakthai --cov-fail-under=96 tests/`).
   - 0 errors across `ruff check`, `ruff format`, `mypy`, `bandit`, and `zizmor`.
   - Zero financial spend ($0.00 USD).

---

## 3. Detailed Technical Design

### 3.1 Workflow Cache De-duplication & Native uv Standardization

#### A. Files to Update
- `.github/workflows/verify-assets.yml`:
  - Remove redundant `actions/cache` step (`Cache uv`).
  - Configure `astral-sh/setup-uv` with `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
- `.github/workflows/continuous-security.yml`:
  - Remove redundant `actions/cache` step (`Cache uv dependencies`).
  - Configure `astral-sh/setup-uv` with `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
- `.github/workflows/ci.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"` to `astral-sh/setup-uv`.
- `.github/workflows/pylint.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"` to `astral-sh/setup-uv`.
- `.github/workflows/sak-family-agent-contract.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"` to `astral-sh/setup-uv`.
- `.github/workflows/repository-security-quality.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"` to both jobs (`skill-validation` and `quality`).
- `.github/workflows/dependency-audit.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
- `.github/workflows/run-evals.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.
- `.github/workflows/subprojects.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"` across its uv setup steps.
- `.github/workflows/huggingface-integration.yml`:
  - Add `enable-cache: true` and `cache-dependency-glob: "uv.lock"`.

### 3.2 Missing Concurrency Control (`code-review.yml`)

Add concurrency control immediately below `permissions`:
```yaml
concurrency:
  group: gemini-code-review-${{ github.event.issue.number }}
  cancel-in-progress: true
```

### 3.3 Event-Driven PR Cache Eviction (`cache-cleanup.yml`)

Create `.github/workflows/cache-cleanup.yml`:
```yaml
name: Cleanup PR Caches

on:
  pull_request:
    types: [closed]

permissions:
  actions: write
  contents: read

concurrency:
  group: cache-cleanup-${{ github.event.pull_request.number }}
  cancel-in-progress: false

jobs:
  cleanup-cache:
    name: Purge closed PR caches
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - name: Delete caches for PR
        env:
          GH_TOKEN: ${{ github.token }}
          PR_REF: refs/pull/${{ github.event.pull_request.number }}/merge
        run: |
          echo "Listing caches belonging to ${PR_REF}..."
          caches=$(gh cache list --ref "${PR_REF}" --limit 100 --json id --jq '.[].id' || true)
          if [ -z "${caches}" ]; then
            echo "No caches found for ${PR_REF}."
            exit 0
          fi
          for cache_id in ${caches}; do
            echo "Deleting cache ID: ${cache_id}"
            gh api -X DELETE "repos/${GITHUB_REPOSITORY}/actions/caches/${cache_id}" || true
          done
          echo "Cache cleanup for ${PR_REF} completed."
```

### 3.4 Immediate Stale Cache Backlog Pruning

Run a controlled sweep using the GitHub CLI:
1. Identify all caches associated with closed/merged PR refs (`refs/pull/*/merge`).
2. Delete each dead cache via `gh api -X DELETE "repos/beer-sakthai/Sak-Family-Agent/actions/caches/<id>"`.
3. Verify reduction in total cache count and storage usage via `gh cache list`.

---

## 4. Safety & Invariant Guarantees

1. **Branch Protection Compatibility**:
   - The "Quality gates" job in `repository-security-quality.yml` remains untouched in naming and execution, satisfying required status checks on `main`.
2. **Contract Compatibility**:
   - `sak-family-agent-contract.yml` steps (`make compose-personas`, `export_agent_repo.py`, etc.) are preserved.
3. **Zero Security Regressions**:
   - Step security runner hardening (`step-security/harden-runner`) remains pinned with sha256 digests.
   - All input expansions are isolated to environment variables (`actions/code-injection` protection).
   - Zero online audits required (`zizmor --no-online-audits` clean).

---

## 5. Verification & Testing Plan

1. **Local Syntax & Supply-Chain Validation**:
   - `uv run ruff check personas/sakthai tests`
   - `uv run ruff format --check personas/sakthai tests`
   - `uv run mypy`
   - `uv run bandit -c pyproject.toml -r personas/sakthai`
   - Verify workflow files with `git diff --check` to prevent any trailing whitespace errors.
2. **Full Test Suite & Coverage**:
   - `uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/`
   - Verify that test suite passes with coverage $\ge 96.0\%$.
3. **Persona Contract Tests**:
   - `uv run pytest -q tests/test_soul_consistency.py tests/test_compose_persona.py tests/test_export_agent_repo.py tests/test_persona_guardrails_parity.py tests/test_persona_security_config.py tests/test_persona_structure_parity.py`

---

## 6. Mandatory PR & Merge Protocol (GEMINI.md)

1. **Push Branch**: `git push origin chore/optimize-github-workflows-and-caching --no-verify`
2. **Open PR**: `gh pr create` with structured summary.
3. **Monitor CI**: `gh pr checks <PR_NUMBER> --watch` until all ~21 checks pass green.
4. **Merge**: `gh pr merge <PR_NUMBER> --merge --delete-branch --admin` and fast-forward local `main`.
