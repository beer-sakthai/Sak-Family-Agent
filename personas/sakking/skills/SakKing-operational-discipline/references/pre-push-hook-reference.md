# Pre-Push Hook Setup

## What it does
Enforces Beer's Zero-Exposure policy at the git layer — blocks non-interactive pushes to remote unless explicitly allowed.

## Installation

The hook lives at `.githooks/pre-push` in the SFA repo. Activate it:

```bash
cd /opt/data/Sak-Family-Agent
chmod +x .githooks/pre-push
git config core.hooksPath .githooks
```

Verify: `git config core.hooksPath` must return `.githooks`.

## How it works

| Scenario | Behavior |
|----------|----------|
| **Non-interactive push** (cron/CI/agent) | Blocked — prints warning + exits 1 |
| **Non-interactive with `HERMES_PUSH_ALLOW=1`** | Allowed (use when Beer said push) |
| **Interactive push** (user at keyboard) | Allowed with reminder warning |
| **`git push --no-verify`** | Bypasses hook entirely (hard override) |

## CI gitleaks gate

Separate from the hook — `secret-scan.yml` runs on every push + PR using `gitleaks/gitleaks-action@v3` with full history scan. Catches secrets that bypass the hook.
