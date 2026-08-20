# Kaggle Training Watchdog Pattern

Monitor a Kaggle kernel training run, auto-heal on error, report on complete.

## Overview

When training is triggered on Kaggle (via CLI push or manual start), set up a watchdog to monitor it. The watchdog runs on a cron schedule (every 2 min) and checks kernel status. On ERROR it re-pushes the kernel. On COMPLETE it downloads the output.

## Script Pattern

```bash
#!/bin/bash
KERNEL="username/kernel-slug"
STATE_FILE="/path/to/state.txt"
export KAGGLE_USERNAME="your-user"
export KAGGLE_API_TOKEN="your-KGAT-token"   # NOTE: KAGGLE_API_TOKEN not KAGGLE_KEY (CLI v2.2.3+)
# Old format that silently fails: export KAGGLE_KEY="...""

# Check current status
STATUS=$(kaggle kernels status "$KERNEL" 2>/dev/null | grep -oP '"\K[^"]+(?=")')

case "$STATUS" in
    *RUNNING*)
        echo "RUNNING" > "$STATE_FILE"
        # No output — silent monitoring
        ;;
    *COMPLETE*)
        echo "✅ Training complete!"
        kaggle kernels output "$KERNEL" -p /path/to/output
        rm -f "$STATE_FILE"
        ;;
    *ERROR*)
        echo "⚠️ Training error — re-pushing..."
        kaggle kernels push  # from kernel directory
        ;;
esac
```

## Key Behaviors

- **SILENT when all is well** — only report STATE CHANGES (was RUNNING → now COMPLETE, was WAITING → now RUNNING)
- **Heal on ERROR** — re-push the kernel from the local directory (this creates a new version which triggers a fresh run)
- **Download on COMPLETE** — pull logs/output immediately so results aren't lost
- **Idempotent state file** — prevents repeated notifications for the same state

## Cron Setup

```bash
# Create with cronjob tool
# no_agent=true means the script's stdout IS the delivery
cronjob(action='create', name='Kaggle Training Watchdog',
        schedule='2m', script='kaggle-watchdog.sh', no_agent=True)
```

## Pitfalls

- `kaggle kernels delete` is interactive (prompts yes/no) — never call from scripts
- Status string matching is fragile — Kaggle may change enum values. Use grep with `-oP '"\K[^"]+(?=")'` to extract the quoted status from CLI output
- The `kaggle kernels output` command may download to unexpected paths if run from a repo directory — always specify `-p` with an explicit output directory
- **Pushing a new version does NOT trigger execution.** Kaggle v2.x CLI uploads the code but the kernel sits idle until the scheduler runs it. To force immediate execution, change the kernel slug (create a new kernel). Kaggle auto-runs kernels on creation.
- **Version pushes after an error do not re-run.** If v5 errored, pushing v6 does not re-run it. A new slug is the only reliable trigger from CLI.
