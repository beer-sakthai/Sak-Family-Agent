---
name: SakJules-cron-orchestration
version: 1.0.0
description: "Orchestrate cron schedules requested by SakTan via family memory, implement workflow timers, and confirm execution with schedule-confirmed tags."
category: automation
tags:
- automation
- cron
- memory
- schedules
- saktan
---

# Cron Orchestration & Schedule Implementation

Use this skill when implementing, updating, or auditing automated background schedules across GitHub Actions workflows and systemd timers.

## The Cron Rule

> **SakTan specifies. SakJules implements.**
> SakJules never adds, modifies, or deletes a cron job independently without SakTan's specification in family memory.

## Goal

1. Read and process pending `schedule-request` observations from SakTan.
2. Implement or update corresponding cron schedules in `.github/workflows/*.yml` or `infra/vm-agents/systemd/`.
3. Validate cron expression syntax and ensure zero duplicate or conflicting timers.
4. Record `schedule-confirmed` back to family memory so the household status remains in sync.

## Prerequisites

- Access to `sakthai memory family` CLI
- Write access to `.github/workflows/` and `infra/vm-agents/`

## Step-by-Step Workflow

### 1. Ingest Pending Schedule Requests

Query family memory for active requests from SakTan:
```bash
sakthai memory family "SCHEDULE REQUEST" --tag schedule-request --personas saktan --limit 10
```

Parse the target job name, requested cron expression (UTC), workflow file, and rationale.

### 2. Implement the Schedule

#### Option A: GitHub Actions Schedule (`.github/workflows/<job>.yml`)
Update or insert the `schedule:` trigger block under `on:`:
```yaml
on:
  schedule:
    # Daily ops sync at 04:00 UTC (requested by SakTan)
    - cron: '0 4 * * *'
  workflow_dispatch:
```

#### Option B: Systemd Timer (`infra/vm-agents/systemd/`)
For VM-hosted daemon bots, define the timer unit (`*.timer`):
```ini
[Unit]
Description=SakThai Scheduled Ops Timer
PartOf=sakthai-ops.service

[Timer]
OnCalendar=*-*-* 04:00:00 UTC
Persistent=true

[Install]
WantedBy=timers.target
```

### 3. Syntax Verification

Verify the cron expression is valid:
- Check field counts (5 fields for GitHub Actions: `minute hour day-of-month month day-of-week`).
- Ensure minutes are offset from top-of-hour (`:00`) when appropriate to avoid GitHub Actions peak load queue delays.

### 4. Attest in Family Memory (`schedule-confirmed`)

Immediately after committing the workflow change, record confirmation:
```bash
sakthai learn --persona sakjules "SCHEDULE CONFIRMED: <job_name> | cron: <expression> | workflow: <file_path> | timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")" \
  --kind observation --tag schedule-confirmed --tag sakjules
```
