# GitHub Workflows & Action Cache Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminate redundant GitHub Actions cache steps, standardize native `setup-uv` caching across CI/CD workflows, add event-driven automated PR cache eviction, harden workflow concurrency, and prune historical dead caches.

**Architecture:** Remove duplicate `actions/cache` steps that conflict with `astral-sh/setup-uv` in `verify-assets.yml` and `continuous-security.yml`. Explicitly declare deterministic native caching (`enable-cache: true`, `cache-dependency-glob: "uv.lock"`) across all 10 Python CI workflows. Implement an event-driven `cache-cleanup.yml` workflow triggering on `pull_request: [closed]`. Add missing concurrency control to `code-review.yml`. Prune legacy orphaned caches via `gh cache` CLI, and verify end-to-end with automated hygiene tests and CI checks.

**Tech Stack:** GitHub Actions, YAML, Python 3.11/3.12, `astral-sh/setup-uv`, GitHub CLI (`gh`), Pytest.

**Spec:** `docs/superpowers/specs/2026-11-16-github-workflows-and-cache-optimization-design.md`

## Global Constraints

- Financial Cost Floor: $0.00 USD Financial Spend (100% Local & Free Tier Execution).
- Persona Structural Parity: 51-item parity across all 6 personas must remain 100% intact.
- Soul Consistency: Reply intro line in `SOUL.md` across all personas must remain untouched.
- Code Coverage Floor: Pytest suite must maintain `--cov-fail-under=96` (enforced $\ge 96.0\%$).
- Branch Protection Compatibility: The "Quality gates" job in `repository-security-quality.yml` must remain intact.
- Supply-Chain Security: All GitHub Actions must maintain pinned SHA commits.
- Format & Whitespace: Zero trailing whitespace in all markdown and YAML files (`git diff --check`).
- Git & PR Protocol (GEMINI.md): Branch `chore/optimize-github-workflows-and-caching`, push with `--no-verify`, create PR, monitor green checks (`gh pr checks <PR> --watch`), merge with `--merge --delete-branch --admin`, and fast-forward local `main`.

---

### Task 1: Automated PR Cache Eviction Workflow & Hygiene Tests

**Files:**
- Create: `.github/workflows/cache-cleanup.yml`
- Create: `tests/test_workflow_cache_hygiene.py`

**Interfaces:**
- Produces: GitHub Action triggered on `pull_request: [closed]` that deletes `refs/pull/<PR>/merge` caches.
- Produces: Test suite validating all workflows for concurrency, lack of duplicate `actions/cache` steps, and valid `cache-cleanup.yml` structure.

- [ ] **Step 1: Write the failing workflow cache hygiene test**

Create `tests/test_workflow_cache_hygiene.py`:
```python
from __future__ import annotations

import glob
from pathlib import Path
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"


def test_cache_cleanup_workflow_exists_and_valid() -> None:
    cleanup_file = WORKFLOWS_DIR / "cache-cleanup.yml"
    assert cleanup_file.is_file(), "cache-cleanup.yml must exist"

    with cleanup_file.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    assert data is not None
    assert "name" in data
    # Check trigger on pull_request closed
    on_clause = data.get("on") or data.get(True)  # yaml may parse 'on' as boolean
    assert on_clause is not None
    assert "pull_request" in on_clause
    assert "types" in on_clause["pull_request"]
    assert "closed" in on_clause["pull_request"]["types"]

    # Check permissions
    assert data.get("permissions", {}).get("actions") == "write"

    # Check concurrency
    assert "concurrency" in data


def test_no_redundant_actions_cache_on_uv_dir() -> None:
    """Ensure no workflow combines setup-uv with manual actions/cache on ~/.cache/uv."""
    for yml_path in WORKFLOWS_DIR.glob("*.yml"):
        if yml_path.name.endswith(".lock.yml"):
            continue
        content = yml_path.read_text(encoding="utf-8")
        if "astral-sh/setup-uv" in content:
            assert "~/.cache/uv" not in content, (
                f"{yml_path.name} uses astral-sh/setup-uv and manual ~/.cache/uv cache. "
                "Remove redundant actions/cache step."
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -v`
Expected: FAIL (`cache-cleanup.yml` does not exist, and `verify-assets.yml` / `continuous-security.yml` still contain `~/.cache/uv`).

- [ ] **Step 3: Implement `cache-cleanup.yml`**

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
          caches=$(gh cache list --ref "${PR_REF}" --limit 100 --json id --jq '.[].id' 2>/dev/null || true)
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

- [ ] **Step 4: Run test to verify partial progress**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py::test_cache_cleanup_workflow_exists_and_valid -v`
Expected: PASS.

- [ ] **Step 5: Commit Task 1 deliverable**

```bash
git add .github/workflows/cache-cleanup.yml tests/test_workflow_cache_hygiene.py
git commit -m "feat(ci): add automated pr cache cleanup workflow and hygiene tests"
```

---

### Task 2: Workflow Cache De-duplication & Native uv Standardization

**Files:**
- Modify: `.github/workflows/verify-assets.yml`
- Modify: `.github/workflows/continuous-security.yml`
- Modify: `.github/workflows/ci.yml`
- Modify: `.github/workflows/pylint.yml`
- Modify: `.github/workflows/sak-family-agent-contract.yml`
- Modify: `.github/workflows/repository-security-quality.yml`
- Modify: `.github/workflows/dependency-audit.yml`
- Modify: `.github/workflows/run-evals.yml`
- Modify: `.github/workflows/subprojects.yml`
- Modify: `.github/workflows/huggingface-integration.yml`

**Interfaces:**
- Produces: Standardized, deterministic uv cache declarations across monorepo CI.
- Consumes: `astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2` with:
  ```yaml
  with:
    enable-cache: true
    cache-dependency-glob: "uv.lock"
  ```

- [ ] **Step 1: Update `verify-assets.yml` and `continuous-security.yml`**

1. In `.github/workflows/verify-assets.yml`:
   - Remove the `Cache uv` step (`actions/cache@...` with `path: ~/.cache/uv`).
   - In `Install uv`, add `enable-cache: true` and `cache-dependency-glob: "uv.lock"`:
     ```yaml
     - name: Install uv
       uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
       with:
         python-version: '3.11'
         enable-cache: true
         cache-dependency-glob: "uv.lock"
     ```
2. In `.github/workflows/continuous-security.yml`:
   - Remove the `Cache uv dependencies` step (`actions/cache@...` with `path: ~/.cache/uv`).
   - In `Set up uv`, add:
     ```yaml
     - name: Set up uv
       uses: astral-sh/setup-uv@68559e99cc807c1eb7e9238fd43a15bba460eec2 # v10.3.3
       with:
         enable-cache: true
         cache-dependency-glob: "uv.lock"
     ```

- [ ] **Step 2: Update all remaining CI workflows using `setup-uv`**

Add `with: enable-cache: true` and `cache-dependency-glob: "uv.lock"` to `astral-sh/setup-uv` in:
- `ci.yml`
- `pylint.yml`
- `sak-family-agent-contract.yml`
- `repository-security-quality.yml` (both `skill-validation` and `quality` jobs)
- `dependency-audit.yml`
- `run-evals.yml`
- `subprojects.yml` (both jobs)
- `huggingface-integration.yml`

- [ ] **Step 3: Run hygiene test to verify it passes**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -v`
Expected: PASS.

- [ ] **Step 4: Commit Task 2 deliverable**

```bash
git add .github/workflows/
git commit -m "feat(ci): standardize setup-uv caching and eliminate redundant cache steps"
```

---

### Task 3: Workflow Concurrency Hardening for `code-review.yml`

**Files:**
- Modify: `.github/workflows/code-review.yml`
- Modify: `tests/test_workflow_cache_hygiene.py`

**Interfaces:**
- Produces: PR-scoped concurrency on `code-review.yml` preventing duplicate comment reviews.

- [ ] **Step 1: Add concurrency assertion to `test_workflow_cache_hygiene.py`**

Append test function to `tests/test_workflow_cache_hygiene.py`:
```python
def test_all_active_workflows_have_concurrency() -> None:
    """Ensure all active top-level workflow files define concurrency."""
    for yml_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        if yml_path.name.endswith(".lock.yml"):
            continue
        with yml_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            continue
        assert "concurrency" in data, f"{yml_path.name} is missing concurrency declaration"
```

- [ ] **Step 2: Run test to verify it fails on `code-review.yml`**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py::test_all_active_workflows_have_concurrency -v`
Expected: FAIL (`code-review.yml is missing concurrency declaration`).

- [ ] **Step 3: Add concurrency to `.github/workflows/code-review.yml`**

In `.github/workflows/code-review.yml`, insert right below `permissions:` block:
```yaml
concurrency:
  group: gemini-code-review-${{ github.event.issue.number }}
  cancel-in-progress: true
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py::test_all_active_workflows_have_concurrency -v`
Expected: PASS.

- [ ] **Step 5: Commit Task 3 deliverable**

```bash
git add .github/workflows/code-review.yml tests/test_workflow_cache_hygiene.py
git commit -m "feat(ci): add pr-scoped concurrency to code-review workflow"
```

---

### Task 4: Immediate Backlog Cache Eviction & Full Verification

**Files:**
- None modified (operational cleanup and testing).

**Interfaces:**
- Produces: Cleared stale caches from GitHub Actions storage.
- Produces: Full green suite of linters, typings, security scans, and tests.

- [ ] **Step 1: Prune stale PR caches from GitHub Actions storage**

Execute script to list and delete all dead PR caches:
```bash
python3 -c "
import subprocess, json

output = subprocess.check_output(['gh', 'cache', 'list', '--limit', '100', '--json', 'id,ref']).decode()
caches = json.loads(output)
dead_caches = [c for c in caches if c['ref'].startswith('refs/pull/')]
print(f'Found {len(dead_caches)} dead PR caches to delete.')
for c in dead_caches:
    cid = c['id']
    print(f'Deleting cache {cid} ({c[\"ref\"]})...')
    subprocess.run(['gh', 'api', '-X', 'DELETE', f'repos/beer-sakthai/Sak-Family-Agent/actions/caches/{cid}'])
"
```

- [ ] **Step 2: Run linters and formatting checks**

```bash
uv run ruff check personas/sakthai tests
uv run ruff format --check personas/sakthai tests
git diff --check
```
Expected: All checks pass, 0 issues, 0 trailing whitespace.

- [ ] **Step 3: Run static analysis and security audit**

```bash
uv run mypy
uv run bandit -c pyproject.toml -r personas/sakthai
```
Expected: 0 type issues, 0 security vulnerabilities.

- [ ] **Step 4: Run persona contracts & full test suite with coverage**

```bash
make compose-personas
uv run pytest -q tests/test_soul_consistency.py tests/test_compose_persona.py tests/test_export_agent_repo.py tests/test_persona_guardrails_parity.py tests/test_persona_security_config.py tests/test_persona_structure_parity.py
uv run pytest --cov=sakthai --cov-report=xml --cov-fail-under=96 tests/
```
Expected: All tests pass, coverage $\ge 96.0\%$.

---

### Task 5: Mandatory GitHub PR & Merge Workflow (GEMINI.md)

**Files:**
- None (remote GitHub operations).

**Interfaces:**
- Produces: Merged PR on GitHub `main` and synchronized local workspace.

- [ ] **Step 1: Push branch to origin**

```bash
git push -u origin chore/optimize-github-workflows-and-caching --no-verify
```

- [ ] **Step 2: Open Pull Request on GitHub**

```bash
gh pr create --base main --head chore/optimize-github-workflows-and-caching \
  --title "chore(ci): optimize github workflows caching and add automated pr cache eviction" \
  --body "## Summary
- Standardizes \`astral-sh/setup-uv\` native caching (\`enable-cache: true\`, \`cache-dependency-glob: 'uv.lock'\`) across all 10 Python CI workflows.
- Eliminates redundant manual \`actions/cache\` on \`~/.cache/uv\` in \`verify-assets.yml\` and \`continuous-security.yml\`.
- Adds automated PR cache cleanup workflow (\`.github/workflows/cache-cleanup.yml\`) to automatically delete PR caches on \`pull_request: [closed]\`.
- Adds missing concurrency control to \`code-review.yml\`.
- Adds workflow cache hygiene test suite (\`tests/test_workflow_cache_hygiene.py\`).

## Verification
- Local pytest test suite passed with >=96% coverage floor.
- Ruff check & format, Mypy, Bandit clean."
```

- [ ] **Step 3: Monitor CI Checks until all are Green**

```bash
gh pr checks <PR_NUMBER> --watch
```
Expected: All checks pass green.

- [ ] **Step 4: Merge PR to Main and Fast-Forward Local**

```bash
gh pr merge <PR_NUMBER> --merge --delete-branch --admin
git checkout main
git pull origin main
```
Expected: Local `main` fast-forwarded and synchronized with `origin/main`.
