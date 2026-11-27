---
name: SakTan-ops-cron-job-catalog
version: 1.1.0
description: Catalog, manage, audit, and debug scheduled jobs across the House of Sak.
category: operations
tags:
- automation
- catalog
- cron
- cronjob
- daily-ops
- everything
- job
- ops
---

# Cron Job Catalog & Operational Guide

A centralized reference for designing, requesting, verifying, and debugging scheduled
jobs in the House of Sak. Covers cron expressions, systemd timers, GitHub Actions
schedules, memory pairing contracts, and failure remediation.

## When to Use

- Defining a new recurring household schedule or maintenance cadence.
- Auditing existing scheduled jobs for drift, timeouts, or failures.
- Designing zero-cost (\$0.00) automated runs on local Ollama or pinned free-tier models.
- Verifying the `schedule-request` and `schedule-confirmed` pairing protocol.

## Architecture & Delegation Boundary

1. **SakTan (Specification)**: Owns the schedule design, cadence requirements, and memory logging.
2. **SakJules (Implementation)**: Provisions GitHub Actions workflows, systemd unit files, or crontabs.
3. **Target Persona (Execution)**: Runs the automated task via `sak run --persona <name>` or specific script.

## 1. Defining a Schedule Request

To request a recurring job, write a tagged observation to SakTan's memory shard:

```bash
sakthai learn --persona saktan "SCHEDULE REQUEST: <job-name> | cron: <cron-expression> | why: <reason> | target-agent: <persona> | timestamp: <ISO>" \
  --kind observation --tag schedule-request --tag saktan
```

**Common Cron Cadences:**
- Daily Morning Briefing: `0 8 * * *` (Daily at 08:00)
- End-of-Day Closeout: `0 21 * * *` (Daily at 21:00)
- Weekly Review: `0 18 * * 0` (Sundays at 18:00)
- System Health Audit: `0 */4 * * *` (Every 4 hours)
- Cache Hygiene: `0 2 * * *` (Nightly at 02:00)

## 2. Implementation Patterns

### Pattern A: GitHub Actions Scheduled Workflow
Ideal for cloud-hosted verification, portfolio checks, and repository maintenance:
```yaml
name: Scheduled Task
on:
  schedule:
    - cron: '0 8 * * *'
  workflow_dispatch:

permissions:
  contents: read

jobs:
  run:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv run sak run "Task instruction" --persona saktan
```

### Pattern B: Systemd User Service & Timer
Ideal for local VM daemons, local Ollama execution, and offline scheduled tasks:
- Service (`~/.config/systemd/user/sakthai-daily.service`):
  ```ini
  [Unit]
  Description=SakThai Daily Operations Run
  After=network.target

  [Service]
  Type=oneshot
  WorkingDirectory=%h/beer-sakthai/Sak-Family-Agent
  ExecStart=/usr/local/bin/uv run sak run "Run daily briefing" --persona saktan
  StandardOutput=journal
  StandardError=journal
  ```
- Timer (`~/.config/systemd/user/sakthai-daily.timer`):
  ```ini
  [Unit]
  Description=Trigger SakThai Daily Operations

  [Timer]
  OnCalendar=*-*-* 08:00:00
  Persistent=true

  [Install]
  WantedBy=timers.target
  ```

## 3. Auditing & Troubleshooting

### Diagnostic Commands
```bash
# Check timer schedule and next trigger
systemctl --user list-timers --all | grep sakthai

# Inspect execution logs
journalctl --user -u "sakthai-*.service" -n 50 --no-pager

# Verify pairing in family memory
sakthai memory family --tag schedule-request --personas saktan --limit 20
sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20
```

### Common Issues & Remedies

| Issue | Cause | Fix |
|-------|-------|-----|
| Timer missed run | Machine suspended or service inactive | Enable `Persistent=true` in `[Timer]` section |
| Job fails on import | Environment drift or unpinned dependencies | Use `uv run --locked` in service `ExecStart` |
| Token / Quota error | Cloud API rate limit or depletion | Route scheduled tasks to local Ollama or free tier |
| Unconfirmed schedule | Request not picked up by SakJules | Flag in daily briefing for SakJules review |
