---
name: SakTan-ops-cron-fleet
version: 1.1.0
description: Manage the household scheduled job fleet across systemd timers, GitHub Actions,
  and memory-paired schedule requests.
category: operations
tags:
- automation
- cron
- daily-ops
- fleet
- ops
---

# Cron Fleet — House of Sak Scheduled Jobs

Govern and audit scheduled jobs across the House of Sak. SakTan owns the schedule
specification (`schedule-request`), while SakJules implements the automated execution
(`schedule-confirmed`).

## Operational Protocol

All scheduled automation follows the strict two-agent contract:
1. **SakTan specifies** *what*, *when*, and *why*:
   ```bash
   sakthai learn --persona saktan "SCHEDULE REQUEST: <job-name> | cron: <cron-expression> | why: <reason> | timestamp: <ISO>" \
     --kind observation --tag schedule-request --tag saktan
   ```
2. **SakJules provisions** the execution engine (systemd user timer or GitHub Action workflow) and responds:
   ```bash
   sakthai learn --persona sakjules "SCHEDULE CONFIRMED: <job-name> | target: <systemd|github-actions> | timer: <unit> | timestamp: <ISO>" \
     --kind observation --tag schedule-confirmed --tag sakjules
   ```
3. **SakTan verifies pairing** at every **Trust** cycle stage.

## Quick Reference: Local & Remote Fleet Inspection

### 1. Local Systemd Timers (VM & Developer Environment)
```bash
# List all active and pending timers
systemctl --user list-timers --all

# Check status of specific timer and its matching service
systemctl --user status "sakthai-*.timer"
systemctl --user status "sakthai-*.service"

# View recent timer executions and exit codes
journalctl --user -u "sakthai-*.service" -n 30 --no-pager
```

### 2. GitHub Actions Scheduled Workflows
```bash
# List all scheduled workflows in the repository
gh workflow list

# Check recent scheduled runs
gh run list --event schedule --limit 10
```

### 3. Memory Pairing Audit
```bash
# Verify all schedule requests have matching confirmations
sakthai memory family --tag schedule-request --personas saktan --limit 50
sakthai memory family --tag schedule-confirmed --personas sakjules --limit 50
```

## Fleet Watchdog Checklist

When auditing the fleet:
1. **Check for Unpaired Requests**: If a `schedule-request` lacks a `schedule-confirmed` from SakJules after 24 hours, flag it in the daily briefing.
2. **Check for Unapproved Cron Jobs**: SakJules must never deploy a cron job without a corresponding `schedule-request` from SakTan. Audit `.github/workflows/` and user systemd timers for unregistered schedules.
3. **Check Timer Execution Health**: Any service unit exiting with non-zero status must be investigated via `journalctl --user -u <service>`.
4. **Token & Spend Hygiene**: Ensure all scheduled runs operate at $0.00 spend using local Ollama or pinned free-tier inference. Report any scheduled pipeline that consumes paid tokens.
