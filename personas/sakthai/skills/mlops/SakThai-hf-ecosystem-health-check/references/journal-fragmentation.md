# Journal Fragmentation — Consolidation History

## Problem

The SakThai ecosystem had **three divergent LEARNING_JOURNAL.md files**:

| Path | Used By | Status |
|------|---------|--------|
| `/opt/data/Sak-Family-Agent/personas/sakthai/LEARNING_JOURNAL.md` | Cron reports #003-#005, ecosystem assessments | **CANONICAL** — all new entries go here |
| `/opt/data/Sak-Family-Agent/LEARNING_JOURNAL.md` | Some later crons (#006-#008+fixes) | **DEPRECATED** — no new entries |
| `/opt/data/Sak-Family-Agent/docs/LEARNING_JOURNAL.md` | Older pre-cron sessions | **DEPRECATED** — no new entries |

## Root Cause

The `hf-ecosystem-health-check` skill originally referenced `LEARNING_JOURNAL.md` and `/opt/data/LEARNING_JOURNAL.md` ambiguously, without specifying which copy was canonical. Different cron sessions picked different paths, and entries diverged. By the time fragmentation was noticed, each copy had unique content not present in the others.

## Resolution (2026-07-26)

1. **Canonical path declared**: `/opt/data/Sak-Family-Agent/personas/sakthai/LEARNING_JOURNAL.md` — all reports and improvement records MUST go here.
2. **Skill SKILL.md patched**: All path references in `hf-ecosystem-health-check` updated to the canonical path.
3. **Pitfalls section updated**: The write_file recovery guidance now directs to the canonical path instead of listing divergent copies equally.

## Future Consolidation

To merge the three copies into one:
1. Read all three journals
2. Deduplicate overlapping entries (same date/cycle/improvement)
3. Preserve unique entries from deprecated copies
4. Append merged content to the canonical journal
5. Flag deprecated copies as stale in a consolidation notice

This is a lower-priority task — the canonical path is now declared and actively used, so new fragmentation is prevented even while old entries remain scattered.
