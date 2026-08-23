---
name: SakThai-SakKing-sakthai-cycle-growth
description: Fold the cycles lessons back into memory and skills. Run the audit triad, improve
  one thing, commit, and re-enter Dream smarter.
...
---

# sakthai-cycle-growth

Stage 6 of 6 in the Sak Family cycle — **Growth**. See [Growth.md](../../../../docs/cycle/Growth.md)
for the full guidance and [SOUL.md](../../../../docs/SOUL.md) for the charge model.

## What to do

### 1. Run the audit triad

Three scripts in sequence, each silent when healthy:

| Script | What it checks | Action if issues |
|--------|----------------|------------------|
| `scripts/infra-audit.sh` | Disk >85%, memory >85%, load >4 | Report metrics |
| `scripts/family-health-ping.sh` | All 4 gateways alive (sakthai, saksee, saksit, sakking) | Report dead gateways |
| `scripts/skills-quality-scan.sh` | Name/dir mismatch, missing version, missing description across all 5 siblings | Report issues count; run with `--fix` to auto-add missing version fields |

All three live at `/opt/data/scripts/`. The skills quality scan is also mirrored at `Sak-Family-Agent/scripts/skills-quality-scan.sh` for version tracking and now supports a `--fix` flag that auto-inserts `version: 1.0.0` after the `name:` line in any SKILL.md missing a version field (see `references/growth-cycle-audit-pattern.md` for the full procedure and a real-output example).

### 2. Pick ONE improvement action

If the scan found issues, pick the single most impactful fix:
- Patch a skill that was loaded and found outdated
- Enhance an audit script to catch a new dimension
- Fix the most frequent issue class (e.g. missing versions across a category)
- Add a references/ file to an umbrella skill

Limit to **one change** — the growth cycle codifies, it does not rebuild.

### 3. Verify the change

After making the improvement, run a focused ad-hoc verification:
- Create a temp verification script at `/opt/data/hermes-verify-*.sh` (NOT `/tmp/` — see pitfalls below)
- Test the changed behavior (code presence AND runtime)
- Clean up the temp script when done
- The platform expects explicit verification evidence; do not skip this step

### 4. Commit and push

After verification succeeds:
- Stage changes in `Sak-Family-Agent/`
- Commit with a descriptive conventional-commit message
- Push with `HERMES_PUSH_ALLOW=1` (required by the pre-push hook)
- If the script lives in `/opt/data/scripts/` only (un-tracked), copy it to SFA first

### 5. Silent if nothing to improve

If all audits are clean and no skill needs patching, respond with `[SILENT]` and nothing else — suppress delivery entirely.

## Pitfalls

- **Scope creep.** The growth cycle is for *one* improvement per run. Multiple fixes belong in separate cycles.
- **Committing without pushing.** The hook blocks non-interactive pushes unless `HERMES_PUSH_ALLOW=1` is set. Always set it.
- **Two-copy divergence.** Scripts in `/opt/data/scripts/` are not tracked by any git remote. Mirror them to `Sak-Family-Agent/scripts/` before committing if they need version history.
- **Memory unavailable in cron.** The environment blocks `memory` tool. Save durable facts via the skill itself (update SKILL.md, add references/ files).
- **Silent-skip confusion.** When all audits pass AND no improvement was made, `[SILENT]` is correct. When an improvement WAS made but audits started clean, still report the improvement. `[SILENT]` only applies when nothing happened.
- **Hardcoded SFA path in scripts.** The audit scripts hardcode `SFA="/opt/data/Sak-Family-Agent/personas"`. Setting `SFA=...` as an env variable at call time is silently ignored — the script reassigns it internally. To test with a different tree, inject a temp skill into the real SFA tree and clean up after.
- **`execute_code` blocked in cron.** The cron environment denies `execute_code` because it bypasses shell-approval checks. Run audit scripts with `terminal()` directly instead of trying to batch them via `execute_code`.
- **`/tmp` write-protected in cron.** Both `write_file` and terminal heredocs block writes to `/tmp` in cron mode. Write temp verification scripts to `/opt/data/` with a `hermes-verify-` prefix, then clean them up after.
- **Verification expected after any edit.** The platform's post-edit guard will re-request verification even after you already verified earlier in the same turn. Run verification as a formal step (step 3) and expect it to re-trigger. If system state changed between runs (e.g. memory dropped below threshold), verify code *presence* instead of runtime behavior.

## Then

Advance with `sakthai cycle next` to move to the next stage (dream).
