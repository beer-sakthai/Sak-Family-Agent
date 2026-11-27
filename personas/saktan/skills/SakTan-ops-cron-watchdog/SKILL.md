---
name: SakTan-ops-cron-watchdog
version: 1.1.0
description: Auto-resume paused or failed scheduled jobs and daemons across the household fleet.
category: operations
tags:
- automation
- cron
- daily-ops
- heal
- ops
- self
- watchdog
---

# Scheduled Job Watchdog & Self-Healing

Automatically detects, audits, and self-heals scheduled jobs, daemons, and systemd
timers that have stopped, encountered transient failures, or entered inactive states.

## When to Use

- System status check reports "scheduled jobs or daemons stopped firing".
- Routine Care-stage fleet diagnostic run.
- Verifying systemd user services after an environment reboot or update.

## Procedure

1. **Inspect Active & Inactive Timers**:
   ```bash
   systemctl --user list-timers --all
   ```
2. **Detect Failed Units**:
   ```bash
   systemctl --user --failed
   ```
3. **Inspect Failure Details**:
   For any failed unit, inspect recent journal output:
   ```bash
   journalctl --user -u "<unit>.service" -n 25 --no-pager
   ```
4. **Self-Healing Actions**:
   - For transient failure (network timeout, temporary file lock):
     ```bash
     systemctl --user reset-failed "<unit>.service"
     systemctl --user restart "<unit>.service"
     ```
   - For timer disabled or stopped:
     ```bash
     systemctl --user enable --now "<unit>.timer"
     ```
5. **Log Healed Units**:
   Write observation to SakTan's memory shard:
   ```bash
   sakthai learn --persona saktan "WATCHDOG HEAL: <unit> | action: restart | reason: <transient-error>" \
     --kind observation --tag watchdog-heal --tag saktan
   ```
6. **Report Summary**:
   Deliver a single-line update to Beer if any units were healed. Emit nothing if all units are healthy.

## Pitfalls

- **Do Not Loop-Heal Persistent Failures**: If a service fails immediately upon restart due to missing credentials, do not repeatedly restart it. Report the root cause to Beer.
- **Check Shard Locks Before Restarting**: If an agent process crashed, verify its SQLite shard (`~/.sakthai/<persona>/memory.db`) is intact via `sakthai memory --persona <p> healthcheck`.
