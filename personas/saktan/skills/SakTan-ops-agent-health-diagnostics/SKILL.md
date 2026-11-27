---
name: SakTan-ops-agent-health-diagnostics
version: 1.1.0
description: Diagnose why a Sak Family agent isn't responding — gateway status, provider
  health, Telegram connectivity, log analysis
category: operations
tags:
- agent
- cli
- daily-ops
- diagnostics
- gateway
- health
- health-check
- ops
- provider
- sibling-agents
- telegram
- troubleshooting
---

# Agent Health Diagnostics

Diagnose why a Sak Family agent that shows as "running" is not actually responding to messages.

## Quick Check Order

When Beer says "Agent X isn't replying", run these in order. Each step narrows the cause.

### 1. Process & Daemon State
```bash
# Check if the agent daemon or runner is active
pgrep -a -f "sakthai.*<persona>" || systemctl --user status "sakthai-<persona>"
```
- If down → restart via `systemctl --user restart sakthai-<persona>` or `infra/vm-agents/sakthai-agent-run.sh`
- If running, note the PID and memory consumption

### 2. Dry-Run Health Preflight
```bash
# Execute dry-run to confirm persona config, model, and skill resolution
sakthai run "ping" --persona <persona> --no-mcp --dry-run
```
- If configuration errors are shown, check `personas/<persona>/config/config.yaml`
- Confirm provider credentials and fallback settings

### 3. Telegram Connectivity & Gateway Logs
Check gateway / systemd logs for Telegram polling errors:
```bash
journalctl --user -u "sakthai-<persona>" -n 50 --no-pager
# Or inspect agent runtime log:
tail -50 ~/.sakthai/<persona>/agent.log
```
- Look for **"Polling heartbeat probe failed"**, **"reconnecting"**, or `Conflict: terminated by other getUpdates request` (indicates multiple bot instances using the same token).
- Look for HTTP 401 Unauthorized (token revoked) or HTTP 403 Forbidden.

### 4. Provider & Quota Health
Check `config.yaml` in the persona tree:
```bash
cat personas/<persona>/config/config.yaml
```
- For local models (Ollama): verify `curl -s http://127.0.0.1:11434/api/tags`
- For Hugging Face router models: check quota limits via `sakthai quota status`
- Check for HTTP 429 (Rate Limit) or 503 (Overloaded) in logs

### 5. Memory Shard Integrity
Verify SQLite memory shard is not locked or corrupted:
```bash
sakthai memory --persona <persona> healthcheck
```

## Common Failure Patterns

| Pattern | What It Means | Fix |
|---------|---------------|-----|
| Process alive, Telegram disconnected | Webhook/polling collision or network drop | Restart service, check single bot token |
| HTTP 429 Rate Limit | Provider quota exhausted | Fail over to local Ollama or backup provider |
| SQLite `database is locked` | Zombie process holding WAL lock | Terminate orphaned process, run `sakthai memory --persona <p> healthcheck` |
| Import / Package error | Environment drift | Run `uv sync --locked` |

## Critical Pitfalls

- **"Process is running" ≠ "Agent can respond"** — The Python process may be alive while the Telegram polling loop has disconnected or blocked on a hung socket.
- **Bot Token Collision** — Never run a local test instance of `sakthai telegram` using the production bot token while the VM agent service is active; Telegram will reject both with HTTP 409 conflicts.
- **Fail Closed Security** — If Tirith or data loss guardrails block a tool call, the agent halts by design. Check stdout for security intercept notices.
