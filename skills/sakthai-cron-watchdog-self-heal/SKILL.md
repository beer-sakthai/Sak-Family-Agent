---
name: sakthai-cron-watchdog-self-heal
category: hermes
description: Autonomous diagnosis + self-healing for the SakThai cron fleet
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    related_skills: []
    source: hermes:cron-watchdog-self-heal
---

# Cron Watchdog Self-Heal

## Purpose

Autonomous diagnosis + self-healing for the SakThai cron fleet. Keep each job running “prefectly”; when any job fails, find why and apply the safest known fix without interrupting healthy schedulers.

## Trigger

Load this skill when:
- A cron job reports `last_status != ok`
- A cron output mentions `error`, `fail`, `warn`, `missing`, `block`, `not available`, `traceback`, `exception`, or `credentials`
- A user says “check/fix the cron jobs”

## Procedure

### A. Enumerate all jobs

1. `cronjob action=list`
2. For each job: capture `job_id`, `name`, `last_status`, `last_delivery_error`, `enabled_toolsets`, `state`

### B. Forensics per job

1. Read `~/.hermes/cron/output/<job_id>/*.md` (newest first)
2. Flag the FIRST failure if there is one; older violations are informational only
3. Produce: `job_id | name | symptom | severity | candidate_fix`

Severity:
- `low` — log only, no auto-fix
- `medium` — auto-fix after verification
- `high` — auto-fix + notify Beer

### C. Symptom → Fix map

| Symptom | Cause | Fix |
|---------|-------|-----|
| `supermemory_store not available` / `no usable Supermemory baseline` | `enabled_toolsets` missing memory tools | `cronjob update` — add `supermemory` + `memory` |
| Playwright browser missing / OS not supported | No matching Playwright Chromium build | Use system Chrome with `channel='chrome'` |
| `429 rate limit` | Provider throttling | Pause 5m then resume; switch model if repeat |
| `credentials` / `credentials not found` | Config env var absent | Log + notify Beer — do NOT auto-inject |
| Timeout / killed / process failure | Schedule too aggressive | Raise interval; add retry/backoff |
| `ModuleNotFoundError: playwright` | Wrong Python env | Run venv ✓; if venv has no chromium build, use system Chrome |
| State = paused unexpectedly | Manual pause or prior failure | Resume + confirm `last_status == ok` next run |

### D. Apply + verify

1. Apply the fix via `cronjob update` (or `resume`/`pause`)
2. Wait for next tick — re-read the newest run file in `~/.hermes/cron/output/<job_id>/`
3. Confirm symptom is gone (`keyword_absent=True`)
4. One-shot success = `fixed`; still failing = `failed` → notify Beer with exact reason

### E. Logging

Append to `~/.hermes/cron/output/cron-watchdog.log`:
```
<ISO-8601> cron-watchdog <status> job=<id> issue=<symptom> fix=<action|none>
```
- `status`: `ok | warn | fixed | failed`
- Always one line per tick, no timestamps -> never logs
- Never append the same line twice in a row without a new failure

### F. Notify Beer

Notify (Telegram) only when:
- You actually performed a fix (`status=fix`), or
- A job is `high` severity

Telegram message format:
```
Cron fix: `<job_name>` (<job_id>) — <symptom> → <fix>
```

## Constraints

- Do NOT change prompts, deliverables, schedules, or third-party jobs
- Do NOT auto-inject credentials — flag them to Beer instead
- If unsure about the fix, mark `warn` and explain what you think
- Preserve `last_run` history and `*.md` artifacts — do not delete

## Replay guard

If context contains `REPLAY_DETECTED:<job_id>`, skip that job this tick and continue with the next one.

## Verification

Before marking `fixed`:
1. Re-read the newest run file after applying the fix
2. Confirm the failure keyword is absent
3. Confirm the new `last_status` is `ok`
4. Only then mark `fixed`
