---
name: cron-watchdog-self-heal
description: Audit the Hermes cron fleet, resume safe paused jobs, and repair missing toolsets so playbooks like supermemory/memory aren't blocked. Use when asked to monitor cron, self-heal cron jobs, or fix missing-tool errors.
---

# Cron Watchdog Self-Heal

Watch and repair the Hermes cron fleet safely: resume jobs that are only conditionally paused, and add missing toolsets that gate expected behavior.

## When to use

- A cron job failed because a tool was unavailable and the error indicates a missing toolset.
- User asks for a cron check, fleet audit, or auto-resume of paused jobs.
- Reviewing a cron job's scheduled behavior and needed permissions.

## Fixed rules for cron health

### 1. List first
Always call cronjob(action='list') before changing anything. Treat this as the current source of truth.

### 2. Resume condition
Resume only a job when:
- enabled is true
- state is paused or scheduled normally
- paused is false
- paused_reason is empty or absent
Never resume a job that carries an explicit paused_reason.

### 3. Toolset repair
Add missing toolsets only when the missing tool is required for the job's intended behavior. Preferred additions for observability/memory jobs:
- supermemory
- memory
Use cronjob(action='update', job_id=..., enabled_toolsets=...) to add without changing model, prompt, or schedule.

### 4. No silent schedule changes
Do not:
- change schedule
- change prompt template
- change model or provider
- change delivery target
Those remain exactly as-is unless the user explicitly requests it.

### 5. Reporting format
Return a compact report in chat:
- RESUMED: [job names or none]
- UPDATED_TOOLSETS: [job names]
- HEALTHY: [count]

Mention any job that could not be repaired and why.

## Example

1. cronjob(action='list')
2. For paused job with no paused_reason:
   cronjob(action='resume', job_id='...')
3. For job that needs memory access:
   cronjob(action='update', job_id='...', enabled_toolsets=['supermemory','memory'])
4. Summarize in chat using the reporting format above.
