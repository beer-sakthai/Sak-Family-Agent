# CI Diagnosis Session Log — 2026-07-25

## Key patterns discovered

### 1. Pending commit status ≠ failure
When the commit status shows "pending" with no status checks listed, it often means workflows are still running — not that something is broken. Check the **check-runs API** (`/commits/<SHA>/check-runs`) for the real state, not just the commit status endpoint.

### 2. Empty commit doesn't trigger CI
Commits with only deleted files (`git rm --cached`) or empty commits may not trigger any workflow. To force a CI run, add a trivial whitespace change to a tracked file (e.g. README.md) or use `git commit --allow-empty -m "ci: trigger"`.

### 3. Stale persona references
After deleting a persona, CI fails with multiple test assertion errors. Use `grep -r "deleted_persona" personas/sakthai/sakthai/ tests/ personas/README.md` to find all stale references. Common files that need updating:
- `config.py` — PERSONA_NAMES tuple
- `agent/chat.py` — PERSONA_LABELS and PERSONA_COLORS dicts
- `tests/test_soul_consistency.py` — PERSONAS dict and parametrized tests
- `tests/test_persona_guardrails_parity.py` — PERSONAS list
- `tests/test_config_reports.py` — hardcoded persona tuples
- `tests/test_chat.py` — test name may reference old count
- `personas/README.md` — directory tree
- `personas/<persona>/SOUL.md` — sibling list

### 4. SKILLS_DIR config mismatch
When the root `skills/` dir is removed from git tracking, the config.py `SKILLS_DIR = REPO_ROOT / "skills"` still points to a path that may not exist in CI. Fix: update to `PERSONAS_DIR / "sakthai" / "skills"` and reorder lines so `PERSONAS_DIR` is defined before use.

### 5. HF Learn cron recreates root skills/ dir
The HF Learn cron prompt instructs the agent to `cp -a ~/profiles/sakthai/skills/. skills/` then `git add skills/`. This recreates the root skills/ dir on every run. Two permanent fixes:
- The `.gitignore` has `skills/` to prevent tracking
- The GitHub sync script (`github-sync.sh`) removes `skills/` before committing
- The config.py `SKILLS_DIR` points to `personas/sakthai/skills/` instead

### 6. CI Health Check cron is misleading
The cron job checks its OWN run status (whether it executed without errors), not the actual CI workflow results. A cron status of "ok" does NOT mean CI is green. Always query the check-runs API directly to verify real CI status.

## Methodology: Read log first, fix second

The correct diagnosis sequence is:
1. **Check** — query the check-runs API for the failing commit
2. **Read** — get the failing step's log output (try public API first, then web UI)
3. **Identify** — find the exact error message or assertion failure
4. **Root cause** — trace the error to its source (stale reference, config mismatch, missing file)
5. **Fix** — apply the targeted correction
6. **Verify** — run the test locally first, then push and confirm next CI run is green

Never guess the root cause. Never jump to a fix before reading the log.
