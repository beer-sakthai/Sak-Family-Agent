# Cron Skills Wiring — jobs.json Inventory

**Fixed 2026-07-30.** Every agent-mode cron job must list its skills in `jobs.json`.
Without this, skill FIRST ACTION directives and Step 0 checks are invisible to the
running agent — the skill exists in the library but is never loaded.

## Current wiring (verified)

| Job | Schedule | Skills |
|-----|----------|--------|
| HF Auto Improve | every 1m | `cron-tool-workarounds`, `SakThai-hf-ecosystem-health-check` |
| HF Report & Plan | every 1m | `cron-tool-workarounds`, `SakThai-hf-ecosystem-health-check` |
| CI Health Check | every 1m | `cron-tool-workarounds` |
| HF Deep Learn | every 1m | `cron-tool-workarounds` |
| Social Growth | every 1m | `cron-tool-workarounds` |
| Assistant Excellence | every 1m | `cron-tool-workarounds` |
| Platform Algorithms | every 1m | `cron-tool-workarounds` |
| Brand Storytelling | every 1m | `cron-tool-workarounds` |
| Content Creation | every 1m | `cron-tool-workarounds` |
| weekly-planning | 0 9 * * 1 | `cron-tool-workarounds` |
| daily-standup | 0 9 * * 1-5 | `cron-tool-workarounds` |
| weekly-review | 0 17 * * 5 | `cron-tool-workarounds` |
| monthly-finance-review | 0 9 1 * * | `cron-tool-workarounds` |
| a2a-shard-worker | every 5m | `cron-tool-workarounds`, `sak-a2a-shard-worker` |

**3 no-skill jobs** (all `no_agent: true`, script-based):
cron-fleet-selfheal, a2a-bus-watchdog, fleet-health-check.

## How to verify

```bash
python3 -c "
import json
with open('/opt/data/profiles/sakthai/cron/jobs.json') as f:
    j = json.load(f)
for jb in j.get('jobs', []):
    if not jb.get('no_agent') and not jb.get('skills'):
        print(f'MISSING: {jb.get(\"name\",\"?\")}')
"
# Should print nothing.
```

## Adding a new cron job

Always include at least `cron-tool-workarounds` in the `"skills": []` array.
For ecosystem-scope jobs, also add `SakThai-hf-ecosystem-health-check`.
Without this wiring step, the job will waste 3–4 round trips per run rediscovering
blocked patterns that the skill already documents.
