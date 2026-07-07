---
name: SakKing-cron-fleet
description: "Manage a Hermes cron fleet across multiple profiles — list, audit, re-enable, and remediate scheduled jobs."
version: "1.0.0"
author: Beer (beer-sakthai) + Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [hermes, cron, jobs, scheduler, fleet, multi-profile, watchdog, automation]
    related_skills: [hermes-agent, sakthai]
---

# Cron Fleet — Multi-Profile Scheduled Jobs

Drive `hermes cron` across **all profiles** in a Hermes installation. This skill
covers fleet-wide audits, the self-heal pattern, and profile-scoped job management.

> **Base CLI** lives in the bundled `hermes-agent` skill (CLI Reference → Cron Jobs).
> This skill adds the multi-profile fleet patterns and watchdog workflow.

## Quick Ref

```bash
hermes cron list            # active jobs only
hermes cron list --all      # includes disabled / completed jobs
hermes cron resume <id>     # re-enable a disabled job
hermes cron pause <id>      # disable a job
hermes cron run <id>        # trigger next tick immediately
hermes cron remove <id>     # delete permanently
```

**Invocation note.** There is no standalone `cronjob` binary. All cron
operations go through the `hermes cron` CLI (from the `terminal` tool,
or via the `cronjob` toolset in live sessions that expose it). Set
`HERMES_HOME` to target a specific profile.

## Profiles & Fleet Context

Each Hermes profile has its own `$HERMES_HOME` and therefore its own cron
fleet. To manage a profile from the outside:

```bash
export HERMES_HOME=/home/sakthai/.hermes/profiles/<name>
hermes cron list --all
```

Common profiles on this machine:
- `default` (`~/.hermes`) — Hermes bot
- `sakthai` (`~/.hermes/profiles/sakthai`) — Saksee bot
- `hermesagent` (`~/.hermes/profiles/hermesagent`) — SakThai bot
- `saksit` (`~/.hermes/profiles/saksit`) — SakSit bot

## Fleet Watchdog Pattern

When asked to audit the entire fleet:

1. **Enumerate every profile.** Check each known `$HERMES_HOME`.
2. **List all jobs** with `hermes cron list --all` per profile.
3. **Self-heal disabled-ok jobs.** In JSON, `enabled: false` +
   `last_status: "ok"` means the job was healthy before being paused.
   In CLI, these may appear as `[completed]`. Re-enable with:
   ```bash
   hermes cron resume <job_id>
   ```
4. **Report chronic errors.** Jobs with `last_status: "error"` or a
   non-null `last_delivery_error` need human review. Do NOT auto-re-enable
   these — output the job ID, name, and the error signal.
5. **Silent when healthy.** If every profile is green and no actions were
   taken, emit exactly `[SILENT]` to suppress delivery.

## State Quirks

| JSON field | CLI display | Notes |
|------------|-------------|-------|
| `enabled: false` | `[completed]` | Completed one-shots or paused jobs |
| `enabled: true` | `[active]` | Running normally |
| `last_status: "ok"` | `ok` | Last run succeeded |
| `last_status: "error"` | `error` | Last run failed |
| `non-null last_delivery_error` | *(visible in JSON)* | Delivery failure — separate from run status |
| `last_status: null` | *(not shown)* | Job never ran (newly created) — not an error |

`hermes cron list` (no `--all`) filters to `[active]` jobs only. Use `--all`
to include disabled and completed jobs.

## Self-Heal Watchdog Template

When asked to create a self-healing watchdog, use this prompt for a cron
job that runs every 5m:

```
You are a cron fleet watchdog. Every tick:

1. Run `hermes cron list --all` across every known profile and inspect all jobs.
   - If you need richer metadata (last_delivery_error, exact timestamps), fall
     back to the Python API: `python3 -c "from cron.jobs import list_jobs; print(list_jobs(include_disabled=True))"`.
2. For any job that is `enabled: false` AND has `last_status: 'ok'`
   (i.e., it was working before being disabled), re-enable it:
   `hermes cron resume <job_id>`.
3. For jobs with `last_status: 'error'` or a non-null delivery error,
   **do NOT** auto-re-enable. Instead, emit a concise report listing
   the job ID, name, and the error signal.
4. Output `[SILENT]` when no actions were taken and the fleet is healthy.
```

Key constraints:
- Schedule: `every 5m`, repeat: forever.
- The watchdog must stay quiet when there is nothing to report.
- Do not recursively schedule more cron jobs from inside the watchdog.
- There is no standalone `cronjob` binary; all cron operations go through the
  `hermes cron` CLI.
- `hermes cron list` (no `--all`) filters to `[active]` jobs only. Use `--all`
  to include disabled and completed jobs.
- The CLI display omits `last_delivery_error`; to inspect it, read
  `$HERMES_HOME/cron/jobs.json` directly or use the Python API above.

## Repo / Source

Source lives at `~/.hermes/hermes-agent/cron/`. The JSON store is at
`$HERMES_HOME/cron/jobs.json`.

## References

- Fleet watchdog pattern & cron cross-profile notes: `references/fleet-watchdog.md`
- Source code layout: `~/.hermes/hermes-agent/cron/`
