# GitHub Actions Workflows & Analytics Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve critical active workflow defects, eliminate illegal syntax and bash execution bugs, modernize repository AI/Copilot guidelines, align checkout action pins, expand PR labeling taxonomy, and add StepSecurity Harden-Runner runtime telemetry to core pipelines.

**Architecture:** Systematic remediation across GitHub Actions workflow files and configuration manifests in `.github/`, verified by automated regression tests in `tests/test_workflow_cache_hygiene.py` and `tests/test_marketplace_actions.py`, and validated via `scripts/audit_repo_security.py` and `scripts/audit_workflow_concurrency.py`.

**Tech Stack:** GitHub Actions, YAML, Python 3.11+, Pytest, Bash, StepSecurity Harden-Runner, Zizmor.

**Spec:** [docs/sak-family-agent-github-actions-guide.md](file:///home/antigravity/beer-sakthai/Sak-Family-Agent/docs/sak-family-agent-github-actions-guide.md) & [docs/marketplace-actions-catalog.md](file:///home/antigravity/beer-sakthai/Sak-Family-Agent/docs/marketplace-actions-catalog.md)

## Global Constraints

- Monorepo package layout: `personas/sakthai/` is the installed package; no root-level `sakthai/` or `skills/`.
- All third-party action references must be pinned to full 40-character immutable commit SHAs with human-readable comments.
- Zero scalar permissions: top-level and job-level permissions must be declared as explicit YAML mappings.
- Minimum 96.0% test coverage floor enforced by `--cov-fail-under=96`.
- Auto-merge is strictly forbidden by repository policy (PRs must remain open for Beer's manual review).

## Review Focus

- `reconstruction.yml` bash escaping: ensuring backticks in echo commands do not evaluate git commit SHAs as shell commands.
- `reconstruction.yml` find syntax: ensuring trailing backslashes in multi-line find commands do not leave orphaned arguments.
- Local composite action paths: ensuring `uses: ./.github/actions/...` is used rather than invalid syntax like `uses: $/.github/...`.
- Action pin consistency: ensuring `actions/checkout` is harmonized to `@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1` everywhere.
- Test suite regressions: ensuring `test_workflow_cache_hygiene.py` and `test_marketplace_actions.py` pass without warning or failure.

---

### Task 1: Fix Syntax & Escaping Defects in `reconstruction.yml` and `bot-check-action.yml`

**Files:**
- Modify: `.github/workflows/reconstruction.yml:40-45, 90-100`
- Modify: `.github/workflows/bot-check-action.yml:39-44`
- Test: `tests/test_workflow_cache_hygiene.py`

**Interfaces:**
- Consumes: `.github/actions/check-automation-permissions` composite action
- Produces: Cleanly executing reconstruction audit and bot check workflows

- [ ] **Step 1: Write regression test verifying composite action path and bash escaping syntax**

Add tests in `tests/test_workflow_cache_hygiene.py` asserting no workflow contains `uses: $/.github` and asserting that `reconstruction.yml` contains valid `find` and `git rev-parse` escaping without bare command substitutions.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_reconstruction_syntax_and_composite_paths" -v`
Expected: FAIL with assertion error.

- [ ] **Step 3: Fix syntax and escaping in `reconstruction.yml` and `bot-check-action.yml`**

In `.github/workflows/reconstruction.yml`:
- Change `uses: $/.github/actions/check-automation-permissions` to `uses: ./.github/actions/check-automation-permissions`.
- Fix line 92 to `echo "Commit: \`$(git rev-parse HEAD)\`"`.
- Fix line 95 to avoid trailing backslash argument error:
  ```bash
  find .github/workflows -maxdepth 1 -type f \
    \( -name '*.yml' -o -name '*.yaml' -o -name '*.md' \) -printf '%f\n' | sort
  ```
In `.github/workflows/bot-check-action.yml`:
- Change `uses: $/.github/actions/check-automation-permissions` to `uses: ./.github/actions/check-automation-permissions`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_reconstruction_syntax_and_composite_paths" -v`
Expected: PASS.

- [ ] **Step 5: Verify bash block execution locally**

Run:
```bash
bash -c '
set -euo pipefail
mkdir -p /tmp/test-reconstruct
python3 scripts/audit_workflow_concurrency.py --workflow-dir .github/workflows --output /tmp/test-reconstruct/audit.md
echo "Commit: \`$(git rev-parse HEAD)\`"
find .github/workflows -maxdepth 1 -type f \( -name "*.yml" -o -name "*.yaml" -o -name "*.md" \) -printf "%f\n" | sort | head -n 5
'
```
Expected: Clean execution without `command not found` or `find: paths must precede expression`.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/reconstruction.yml .github/workflows/bot-check-action.yml tests/test_workflow_cache_hygiene.py
git commit -m "fix(workflows): resolve reconstruction.yml and bot-check-action syntax and escaping defects"
```

---

### Task 2: Remove Orphaned `.github/action.yml`

**Files:**
- Delete: `.github/action.yml`
- Test: `tests/test_workflow_cache_hygiene.py`

**Interfaces:**
- Consumes: None (no workflow invokes `uses: ./.github`)
- Produces: Clean root `.github/` without phantom Docker actions missing Dockerfiles

- [ ] **Step 1: Write test asserting `.github/action.yml` does not exist or has matching Dockerfile**

Add test in `tests/test_workflow_cache_hygiene.py` checking that any action declaring `using: docker` with `image: Dockerfile` has an existing Dockerfile in its directory.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_docker_actions_have_dockerfile" -v`
Expected: FAIL.

- [ ] **Step 3: Remove orphaned `.github/action.yml`**

Remove `.github/action.yml`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_docker_actions_have_dockerfile" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git rm .github/action.yml
git add tests/test_workflow_cache_hygiene.py
git commit -m "fix(actions): remove orphaned root .github/action.yml missing Dockerfile"
```

---

### Task 3: Modernize `.github/copilot-instructions.md`

**Files:**
- Modify: `.github/copilot-instructions.md`
- Test: `tests/test_repo_hygiene.py`

**Interfaces:**
- Consumes: Monorepo layout rules from `AGENTS.md`
- Produces: Authoritative, accurate assistant instructions for Copilot and AI agents

- [ ] **Step 1: Write test validating `.github/copilot-instructions.md` against repository invariants**

Add test checking that `copilot-instructions.md` contains `personas/sakthai`, `--cov-fail-under=96`, and does not reference stale `sakthai-agent-v2` or `fail_under = 85`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_repo_hygiene.py -k "test_copilot_instructions_alignment" -v`
Expected: FAIL.

- [ ] **Step 3: Update `.github/copilot-instructions.md`**

Rewrite `.github/copilot-instructions.md` to reflect:
- Project title: House of Sak (`Sak-Family-Agent`)
- Package paths: `personas/sakthai/` (editable-installed)
- Quality commands: `uv run --locked ruff check personas/sakthai tests`, `uv run --locked mypy personas/sakthai`, `uv run --locked pytest --cov=sakthai --cov-fail-under=96 tests/`
- Coverage floor: 96%
- Memory: `~/.sakthai/<persona>/memory.db` per-persona shards
- Skills: `personas/<name>/skills/` and `personas/shared/skills/`

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_repo_hygiene.py -k "test_copilot_instructions_alignment" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/copilot-instructions.md tests/test_repo_hygiene.py
git commit -m "docs(copilot): modernize copilot-instructions.md for monorepo paths and 96% coverage"
```

---

### Task 4: Expand `.github/labeler.yml` and Update `.github/conflict-resolver.yml`

**Files:**
- Modify: `.github/labeler.yml`
- Modify: `.github/conflict-resolver.yml:28-34`
- Test: `tests/test_pr_workflows.py`

**Interfaces:**
- Consumes: PR file change paths
- Produces: Precise PR category labels and valid conflict resolution rules

- [ ] **Step 1: Write test verifying `.github/labeler.yml` rules and `.github/conflict-resolver.yml` paths**

Add test in `tests/test_pr_workflows.py` ensuring `labeler.yml` contains rules for `core_python`, `dashboard`, `personas`, and `tests`, and ensuring `conflict-resolver.yml` references existing path patterns.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pr_workflows.py -k "test_labeler_and_conflict_resolver_configs" -v`
Expected: FAIL.

- [ ] **Step 3: Update `labeler.yml` and `conflict-resolver.yml`**

In `.github/labeler.yml`:
- Add `core_python`, `dashboard`, `personas`, `tests`, `security`, `dependencies`.
In `.github/conflict-resolver.yml`:
- Replace `src/**/*.test.ts` with `apps/sak_agent_dashboard/**/*.test.tsx` and `tests/**/*.py`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_pr_workflows.py -k "test_labeler_and_conflict_resolver_configs" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/labeler.yml .github/conflict-resolver.yml tests/test_pr_workflows.py
git commit -m "chore(github): expand labeler taxonomy and update conflict-resolver paths"
```

---

### Task 5: Align `actions/checkout` Commit SHAs to `v7.0.1`

**Files:**
- Modify: `.github/workflows/contrast-ai-smartfix.yml:28`
- Modify: `.github/workflows/pr-rules-checker.yml:29`
- Modify: `.github/workflows/microsoft-security-devops.yml:33`
- Modify: `.github/workflows/awesome-lint.yml:27`
- Test: `tests/test_marketplace_actions.py`

**Interfaces:**
- Consumes: `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`
- Produces: 100% SHA consistency across all 189 workflows

- [ ] **Step 1: Write test verifying all `actions/checkout` uses use canonical SHA**

Add test in `tests/test_marketplace_actions.py` ensuring that every `actions/checkout` reference across `.github/workflows/*.yml` uses `3d3c42e5aac5ba805825da76410c181273ba90b1`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_marketplace_actions.py -k "test_all_checkout_actions_use_canonical_sha" -v`
Expected: FAIL with 4 non-canonical instances.

- [ ] **Step 3: Update the 4 workflows to `actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1`**

Update `contrast-ai-smartfix.yml`, `pr-rules-checker.yml`, `microsoft-security-devops.yml`, and `awesome-lint.yml`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_marketplace_actions.py -k "test_all_checkout_actions_use_canonical_sha" -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/contrast-ai-smartfix.yml .github/workflows/pr-rules-checker.yml .github/workflows/microsoft-security-devops.yml .github/workflows/awesome-lint.yml tests/test_marketplace_actions.py
git commit -m "chore(ci): standardize actions/checkout to v7.0.1 across all workflows"
```

---

### Task 6: Add StepSecurity Harden-Runner & Timeouts to Core Pipelines

**Files:**
- Modify: `.github/workflows/ci.yml:34-40`
- Modify: `.github/workflows/apps.yml:47-51`
- Modify: `.github/workflows/wiki-sync.yml:28-33`
- Modify: `.github/workflows/semantic-tagging.yml:27-32`
- Modify: `.github/workflows/code-review.yml:15-20`
- Modify: `.github/workflows/no-free-usage.yml:15-20`
- Test: `tests/test_workflow_cache_hygiene.py`

**Interfaces:**
- Consumes: `step-security/harden-runner@aebdcf6156ab6691adf63218240e476564a1ed4c # v2.23.0`
- Produces: Outbound network telemetry and runtime egress protection for core pipelines

- [ ] **Step 1: Write test verifying core workflows have Harden-Runner and explicit timeouts**

Add test in `tests/test_workflow_cache_hygiene.py` verifying that `ci.yml:test`, `apps.yml:dashboard`, `wiki-sync.yml:sync`, and `semantic-tagging.yml:tag` initialize `step-security/harden-runner` as their first step, and that `code-review.yml` and `no-free-usage.yml` declare explicit `timeout-minutes`.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_core_workflows_have_harden_runner_and_timeouts" -v`
Expected: FAIL.

- [ ] **Step 3: Update `ci.yml`, `apps.yml`, `wiki-sync.yml`, `semantic-tagging.yml`, `code-review.yml`, and `no-free-usage.yml`**

- In `ci.yml:test`: add Harden Runner step before checkout.
- In `apps.yml:dashboard`: add Harden Runner step before checkout.
- In `wiki-sync.yml:sync`: add Harden Runner step before checkout.
- In `semantic-tagging.yml:tag`: add Harden Runner step before checkout.
- In `code-review.yml:gemini-code-review`: add `timeout-minutes: 10`.
- In `no-free-usage.yml:check-engagement`: add `timeout-minutes: 5`.

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_workflow_cache_hygiene.py -k "test_core_workflows_have_harden_runner_and_timeouts" -v`
Expected: PASS.

- [ ] **Step 5: Run full repository security and concurrency audits**

Run:
```bash
python3 scripts/audit_repo_security.py
python3 scripts/audit_workflow_concurrency.py
uv run --with zizmor==1.30.1 zizmor --config .github/zizmor.yml .github/workflows
```
Expected: All audits pass with 0 errors.

- [ ] **Step 6: Commit**

```bash
git add .github/workflows/ci.yml .github/workflows/apps.yml .github/workflows/wiki-sync.yml .github/workflows/semantic-tagging.yml .github/workflows/code-review.yml .github/workflows/no-free-usage.yml tests/test_workflow_cache_hygiene.py
git commit -m "feat(security): add Harden-Runner and explicit timeouts to core pipelines"
```
