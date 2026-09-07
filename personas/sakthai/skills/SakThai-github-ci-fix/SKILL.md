---
name: SakThai-github-ci-fix
author: Hermes
description: Diagnose and repair GitHub Actions CI failures.
version: 0.1.0
tags:
  - CI/CD
  - GitHub
  - Debugging
  - Python
---

# GitHub CI Fix

Diagnoses and repairs failed GitHub Actions workflows in a Python monorepo. Reads the CI log to find the exact failure, runs the same commands locally with `terminal` to reproduce, applies the fix with `patch`/`write_file`, and re-runs until green. Does NOT rewrite workflows or alter CI configuration — only fixes the code or data the CI is testing.

## When to Use

- A CI check (ruff, mypy, pytest, bandit, pylint, gitleaks) shows red.
- The commit status says "failed" but the log is not immediately visible.
- A workflow errored on a push or PR and the user says "fix CI."
- A scheduled workflow (verify-assets, secret-scan) failed and needs attention.

## Prerequisites

- Repository cloned under `/opt/data` with write access.
- `gh` CLI installed and authenticated (`gh auth status`).
- For the Sak-Family-Agent repo: Python venv with `uv sync --all-extras` done.

## How to Run

1. Find the failing run with `gh run list` or the check-runs API.
2. Get the log with `gh run view <id> --log`.
3. Read the log, identify the failing step (ruff, mypy, pytest, bandit, gitleaks, pylint).
4. Reproduce locally with the same command the workflow uses.
5. Fix the issue and verify locally.
6. Commit and push.

## Quick Reference

```
# Find failing workflows
gh run list --branch main --status failure --limit 5
gh run view <run-id> --log

# Local reproduction (Sak-Family-Agent)
uv sync --all-extras
uv run ruff check personas/sakthai/sakthai tests
uv run ruff format --check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai
uv run pytest --cov=sakthai tests/

# Secret scan
gitleaks detect --source . -v

# Pylint
pylint --fail-under=7.0 $(git ls-files | grep -E '^(personas/sakthai/sakthai|tests|scripts)/.*\\.py$')
```

## Procedure

### 1. Identify the failing run

Use `terminal` to list recent failures:

```bash
gh run list --branch main --status failure --limit 5
```

If `gh` is unavailable, use the GitHub check-runs API instead:

```bash
curl -s -H "Authorization: Bearer $GITHUB_TOKEN" \
  https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/main/check-runs \
  | python3 -c "import json,sys; [print(c['name'],c['conclusion']) for c in json.load(sys.stdin)['check_runs']]"
```

### 2. Read the CI log

```bash
gh run view <run-id> --log
```

Search for the failing step name in the log output. Common targets:

| Workflow | Failing step | Error pattern |
|----------|-------------|---------------|
| CI | Run linters | `ruff` formatting/check errors |
| CI | Run static analysis | `mypy` type errors, `bandit` security warnings |
| CI | Run tests with coverage | `pytest` assertion errors, import failures |
| Pylint | Analysing code with pylint | Pylint score below threshold |
| Secret Scan | Run gitleaks | Credential or key detected in history |
| verify-assets | Run verification script | URL returned non-200 |

### 3. Reproduce locally

Run the exact command from the workflow. For the main CI workflow (`ci.yml`):

```bash
# Install deps
cd /opt/data/Sak-Family-Agent
uv sync --all-extras

# Lint check
uv run ruff check personas/sakthai/sakthai tests

# Format check  
uv run ruff format --check personas/sakthai/sakthai tests

# Static analysis
uv run mypy personas/sakthai/sakthai
uv run bandit -c pyproject.toml -r personas/sakthai/sakthai

# Tests
uv run pytest --cov=sakthai --cov-report=xml tests/
```

### 4. Fix the issue

- **Ruff errors**: Run `uv run ruff check --fix personas/sakthai/sakthai tests` to auto-fix. Then `uv run ruff format personas/sakthai/sakthai tests` to format.
- **Mypy errors**: Use `read_file` to inspect the offending file, then `patch` to fix type annotations.
- **Pytest failures**: Read the test output to find the assertion that failed. Fix the test or the code it tests.
- **Bandit warnings**: Use `# nosec` only if the warning is a false positive (rare). Prefer fixing the security issue.
- **Gitleaks findings**: Add a GitLeaks allowlist entry in `.gitleaks.toml` if the finding is a test fixture or documentation. Otherwise rotate the leaked secret.

### 5. Verify and push

```bash
# Re-run CI commands to confirm fix
uv run ruff check personas/sakthai/sakthai tests
uv run mypy personas/sakthai/sakthai
uv run pytest --cov=sakthai tests/ -x  # stop on first failure

# Commit and push
git add -A
git commit -m "fix: resolve CI failure — <brief description>"
git push
```

## Pitfalls

- **Do NOT rewrite workflow files** — the CI pipeline is the authority. Fix the code, not the test.
- **`cd` to the repo first** — git refuses to operate in unowned dirs (`git config --global --add safe.directory '*'` or use `git -c safe.directory='*'`).
- **Workflow dispatch workflows** (like verify-assets) never run on push. Run them locally instead.
- **Gitleaks full history** — `fetch-depth: 0` means gitleaks scans all commits, not just HEAD. A leaked secret in an old commit will still fail. Use `git log --all --oneline | head` to find the offending commit.
- **Pipeline caching** — `uv sync` caches deps. If the CI uses a stale cache, run `uv sync --reinstall` to force fresh installs.

## Verification

After pushing, verify CI goes green:

```bash
gh run list --branch main --limit 1
```

Or check via API:

```bash
curl -s https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/main/check-runs \
  | python3 -c "import json,sys; cr=json.load(sys.stdin)['check_runs']; [print(f'{\"✅\" if c[\"conclusion\"]==\"success\" else \"❌\"} {c[\"name\"]}: {c[\"conclusion\"]}') for c in cr]"
```
