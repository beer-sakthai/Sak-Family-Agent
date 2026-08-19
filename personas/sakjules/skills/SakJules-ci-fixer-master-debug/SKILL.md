---
name: SakJules-SakThai-ci-fixer-master-debug
description: Diagnose and fix GitHub Actions CI failures.
...
---

## ⚠️ Cardinal Rule — Diagnose First, Fix Second

**Never guess the root cause. Never jump to a fix before reading the log.**
Beer caught you guessing three times this session. The correct sequence is:

1. **Check** — query the **check-runs API** (`/commits/<SHA>/check-runs`), not just commit status
2. **Read** — get the failing step's output
3. **Identify** — find the exact error message
4. **Root cause** — trace the error to its source
5. **Fix** — apply the targeted correction
6. **Verify** — confirm next run is green

A "pending" commit status usually means workflows are **still running**, not failing. Always check the check-runs API for real status before acting.

# CI Fixer Master Debug

Diagnose CI failures in `beer-sakthai/Sak-Family-Agent` by reading workflow logs, identifying root causes, and applying targeted fixes. Covers the four most common failure patterns: test assertions, secret scanning, dependency changes, and false-positive test matching. Does NOT cover workflow YAML syntax errors.

## When to Use

- A CI run on `main` or a PR shows `failure` or `cancelled`.
- A workflow name (e.g. "CI", "Secret Scan") appears red in the GitHub Actions tab.
- You need to read a CI log but the API auth keeps failing.

## Prerequisites

- `git` CLI configured with push access to `beer-sakthai/Sak-Family-Agent`.
- GitHub token in `~/.git-credentials` (format: `https://x-access-token:PAT@github.com`).

## How to Run

1. Fetch the latest failing run via the GitHub REST API.
2. Inspect the job's `conclusion` and `steps` arrays to find the exact failure.
3. Extract the test output or gitleaks finding from the raw log.
4. Apply the matching fix below.
5. Commit and push; verify the next CI run turns green.

## Quick Reference

```bash
# List recent failing runs
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?status=failure&per_page=3"

# List jobs in a run
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/<RUN_ID>/jobs"

# Download raw logs (requires token auth)
curl -sL -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/<RUN_ID>/logs"
```

## Procedure

### 1. Identify the failing workflow

Use `web_extract` or `terminal` with curl to query the GitHub API:

```bash
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?status=failure&per_page=3" \
  | python3 -c "import sys,json; [print(f'{r[\"name\"]} — {r[\"conclusion\"]} ({r[\"created_at\"][:16]})') for r in json.load(sys.stdin).get('workflow_runs',[])]"
```

### 2. Drill into the failing job

From the run's job list, find the step that failed:

```bash
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/<RUN_ID>/jobs" \
  | python3 -c "import sys,json; j=json.load(sys.stdin)['jobs']; [print(f'❌ {s[\"name\"]}') for jj in j if jj['conclusion']=='failure' for s in jj['steps'] if s['conclusion']=='failure']"
```

### 3. Read the log (API auth pattern)

The GitHub download-logs endpoint redirects to a signed blob. Use the stored token:

```bash
TOKEN=$(cat ~/.git-credentials | grep -oP '(?<=x-access-token:)[^@]+(?=@github\.com)')
curl -sL -H "Authorization: token $TOKEN" \
  "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs/<RUN_ID>/logs" \
  | python3 -c "
import sys, urllib.request, json
d = json.load(sys.stdin)
# Steps may have their own 'logs_url' key in the job detail response
"
```

If the API returns 403/401, the token may lack the `actions:read` scope — use `gh auth status` or inspect `~/.git-credentials`.

### 4. Diagnose common failures

| Failure pattern | Root cause | Fix |
|---|---|---|
| `test_real_skill_catalog_validates_cleanly` — "missing SKILL.md" | Root-level `skills/` dir exists with dirs that have no SKILL.md. Even with `.gitignore`, if git already tracks files under skills/, they keep getting committed and breaking CI. | **Step 1:** `rm -rf skills/` (remove locally). **Step 2:** `git rm -r --cached skills/` (untrack from git history). **Step 3:** Verify `skills/` is in `.gitignore`. **Step 4:** Add to `github-sync.sh` to strip it before commit. Without Step 2, the dir keeps coming back. |
| All BFCL tests pass (false positive) | Substring match in grep: "get_weather" matches plain text "the weather". The model never actually called a tool — it just said the word "weather". | Check for exact tool call syntax (`<tool>`, `tool_call:`, `<search>`) not keywords. Multi-trial with format-specific checks. |
| Secret Scan — gitleaks finding | A credential (`HF_TOKEN`, `KGAT_*`, `sk-*`) exists in the git history or was committed with a recent change. | Check the gitleaks output for the file path. Use `git diff HEAD~1 -- <path>` to confirm. Purge the secret with `git rm --cached <file>` and a `.gitignore` entry, or use `git filter-branch` for history (last resort). |
| `Run tests with coverage` — "ModuleNotFoundError" | A new dependency was added but not pinned in `uv.lock`. CI runs `uv sync --all-extras` which uses the lockfile. | Run `uv lock` locally to regenerate the lockfile, commit the updated `uv.lock`. |
| `Run linters` — ruff or mypy violation | Code style or type error introduced by a recent commit. | Run `uv run ruff check .` and `uv run mypy personas/sakthai/sakthai` locally. Fix the reported line, commit. |

### 5. Apply the fix and revalidate

- Commit and push to `main` (or the PR branch).
- Wait for the next CI run (~1 min). Check with:

```bash
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=1&status=completed" \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['workflow_runs'][0]; print(f'{\"✅\" if r[\"conclusion\"]==\"success\" else \"❌\"} {r[\"name\"]}: {r[\"conclusion\"]}')"
```

### 6. Escalate if stuck

- If the log is inaccessible (403), try extracting the error message from the job's step output summary on the GitHub web UI (visible in the Actions tab without auth).
- If the issue is a false-positive gitleaks hit, update `.gitleaks.toml` with a regex or path allowlist entry and document why it is safe.

## Pitfalls

- The GitHub log-download endpoint returns a 302 redirect to a signed URL. The `-L` flag on curl follows it, but the signed URL may have its own auth requirements. If the download fails, inspect the run's web UI instead — the step output is visible without auth.
- `hypothesis` test-cache files in `.hypothesis/` can cause gitleaks false positives (auto-generated constants that look like credentials). Add `.hypothesis/` to `.gitignore` and remove from tracking with `git rm -r --cached .hypothesis/`.
- The `skills/` dir at repo root may be recreated by the GitHub-Auto-Sync cron job. The fix must be applied to BOTH the sync script AND `.gitignore`.

See `references/bfcl-testing-methodology.md` for the BFCL false-positive diagnosis, `references/ci-failure-patterns.md` for the full CI failure diagnosis, `references/ci-log-access.md` for log retrieval when API auth fails, `references/ci-diagnosis-methodology.md` for the step-by-step diagnosis protocol, `references/ci-verify-method.md` for the correct CI verification method (check-runs API, not commit status), and `references/ci-check-runs-methodology.md` for the correct CI status check method (check-runs API, not just commit status).

## Verification

Push the fix and confirm the next CI run for `beer-sakthai/Sak-Family-Agent` shows `success` for all workflows:

```bash
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/actions/runs?per_page=5&status=completed" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ ALL GREEN' if all(r['conclusion']=='success' for r in d['workflow_runs'][:5]) else '❌ STILL FAILING')"
```
