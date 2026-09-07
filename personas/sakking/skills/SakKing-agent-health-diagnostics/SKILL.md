---
name: SakThai-agent-health-diagnostics
author: SakThai
license: MIT
description: "Diagnose why a Hermes agent isn't responding — gateway status, provider health, Telegram connectivity, log analysis"
version: 1.0.0
metadata:
  hermes:
    tags: [diagnostics, health-check, gateway, telegram, provider, sibling-agents, troubleshooting]
    category: environment-automation
---

# Agent Health Diagnostics

Diagnose why a Hermes agent that shows as "running" (gateway up) is not actually responding to messages.

## Quick check order

When Beer says "X isn't replying", run these in order. Each step narrows the cause.

### 1. Gateway status
```bash
hermes -p <profile> gateway status
```
- If down → restart with `setsid hermes -p <profile> gateway run --replace`
- If running, note the PID

### 2. Process alive?
```bash
ps aux | grep <profile> | grep -v grep
```
- Gateway PID exists? Good.
- Are there related processes (plugins, MCP servers, dashboard)?

### 3. Telegram connectivity
Check `channel_directory.json` for the profile:
```bash
cat ~/profiles/<profile>/channel_directory.json
```
- Is `telegram` platform present?
- Is there a connected chat?

Then check gateway logs for disconnects:
```bash
tail -30 ~/profiles/<profile>/logs/gateway.log
grep -i "telegram.*reconnect\|telegram.*connected\|telegram.*heartbeat" ~/profiles/<profile>/logs/gateway.log
```
- **"Polling heartbeat probe failed"** + **"reconnecting"** + no **"resumed"** = Telegram disconnected
- The agent can receive/send nothing while disconnected
- The gateway will keep trying (up to 10 attempts) but may silently stay disconnected

### 4. Provider health
Check `config.yaml`:
```bash
cat ~/profiles/<profile>/config.yaml | grep -A5 "provider\|model\|fallback"
```
- Is the primary provider paid (ollama-cloud, openai, etc.)?
- Is there a fallback provider configured?

Check provider errors in `errors.log`:
```bash
tail -20 ~/profiles/<profile>/logs/errors.log
grep -i "402\|credit\|depleted\|timed out\|API call failed" ~/profiles/<profile>/logs/gateway.log
```

### 5. Cron jobs as signal
Check `cron/jobs.json` for patterns:
- **Multiple jobs failing with HTTP 402** = provider credits depleted — affects chat too
- **Jobs timing out** = provider overloaded or network issue
- **All jobs failing with same error** = systemic provider failure

### 6. Test model directly
```bash
cat ~/profiles/<profile>/config.yaml | grep "default:" | head -1
```
Try a direct API call if the tool is available.

## Common failure patterns

| Pattern | What it means | Fix |
|---------|--------------|-----|
| Gateway running, Telegram disconnected | Network blip, reconnect failed | Restart gateway |
| HTTP 402 "credits depleted" | Paid provider out of credits | Switch primary to free provider or top up |
| HTTP 402 + fallback not kicking in | Fallback only covers 429/503/connection failures — NOT 402 | Acknowledge: fallback doesn't handle credit depletion. Must switch provider manually |
| API call timed out | Provider overloaded or unreachable | Check provider status page, wait, or switch |
| Gateway running, no errors, no responses | Telegram webhook/polling broken | Check channel_directory, restart gateway |

## Critical pitfalls

- **"Gateway is running" ≠ "Gateway can respond"** — The gateway process can be alive while its Telegram connection is dead and its provider is depleted. Always check both.
- **Fallback providers do NOT handle HTTP 402** — Standard Hermes fallback triggers on rate limits (429), overload (529), service errors (503), and connection failures. Credit depletion (402) passes through unhandled.
- **Telegram reconnection can silently fail** — The reconnect loop tries up to 10 times with increasing backoff. If all 10 fail, the agent stays disconnected with no further retry until the gateway restarts. Look for "Polling resumed" as the success signal.
- **Gateway logs may be in `~/profiles/<profile>/logs/`** not in `~/profiles/<profile>/gateway/` — check both locations.
- **`hermes gateway status` shows profile state but doesn't test connectivity** — it only confirms the process is alive.

## References

- `references/saksee-jul26-402-telegram-disconnect.md` — Reproduction case: SakSee's dual failure (Telegram drop + Ollama Cloud credits depleted)
- `sak-family-handoff` — For delegating work to sibling agents once they're healthy again
