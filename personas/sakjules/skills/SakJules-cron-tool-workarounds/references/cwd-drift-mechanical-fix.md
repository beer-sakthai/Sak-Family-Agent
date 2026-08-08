# CWD Drift — Learned: `workdir` Field Is Cosmetic

> **Why this was written:** To document the discovery that the `workdir` field in `jobs.json` is **not honored** by the Hermes cron runtime. Setting `workdir: /opt/data` on all 17 jobs does NOT change the working directory of spawned cron sessions.

## Discovery (2026-07-30, 10:48 UTC)

All 17 sakthai cron jobs had `workdir: /opt/data` set. Yet the "Assistant Excellence" cron session at 10:48 launched in `/opt/data/Sak-Family-Agent` — proving the field has no effect on the spawned process's CWD.

**The claim that "setting workdir prevents it permanently" (v1.36 of cron-tool-workarounds) was false.** Verified by live observation.

## The Actual Fix

There is no config-level mechanical fix. The only reliable defense is the guard documented in `cron-tool-workarounds` SKILL.md:

```bash
# First action in every cron session:
pwd
ls COMPARISON_SENTINEL 2>/dev/null || echo "CWD mismatch — use absolute paths"
```

Where `COMPARISON_SENTINEL` is a known file at the expected absolute path (e.g. `/opt/data/LEARNING_JOURNAL.md`).

## What Was Done (record of the attempted fix)

The prior patch (setting `workdir: /opt/data` on all jobs) **was executed** — `jobs.json` does contain the field for all jobs, confirmed by runtime inspection. But the fix was ineffective because the runtime ignores the field.

```bash
# Verify current state (all jobs have workdir set, but it doesn't matter)
python3 -c "
import json
with open('/opt/data/profiles/sakthai/cron/jobs.json') as f:
    j = json.load(f)
total = len(j.get('jobs', []))
with_wd = sum(1 for jb in j.get('jobs', []) if jb.get('workdir') is not None)
print(f'{with_wd}/{total} jobs have workdir set (cosmetic — no effect)')
"
```

## Lesson

A "mechanical fix" that targets the wrong layer is not a fix at all. The `workdir` field in the cron config is a data field — it describes intent, not behavior. The actual CWD is set by whatever process spawns the cron session (the gateway daemon), and that process does not consult `workdir`.

**Future approach:** If CWD drift is to be eliminated at the infrastructure level, the fix must target the gateway daemon or the shell init scripts — not the cron jobs.json config. Until then, the pwd guard + absolute paths is the only reliable workaround.
