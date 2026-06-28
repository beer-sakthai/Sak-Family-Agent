---
name: hermes-gateway-health-audit
title: Hermes Gateway & Network Health Audit
description: Run comprehensive diagnostics on Hermes gateways, network connectivity, MCP servers, API authentication, and service status. Generate detailed health reports.
tags:
  - hermes
  - gateway
  - diagnostics
  - monitoring
  - troubleshooting
related:
  - hermes-agent
  - hermes-tts-setup
  - cron-watchdog-self-heal
trigger: |
  User asks to check gateway status, audit network connectivity, verify MCP servers, test API credentials, diagnose service failures, or generate system health reports.
---

# Hermes Gateway & Network Health Audit

Comprehensive diagnostics for Hermes agent gateways, network infrastructure, messaging integrations, and service health. Use when verifying system connectivity or troubleshooting availability.

## Quick Start

Run a full audit:
```bash
# Network connectivity
ping -c 2 8.8.8.8
curl -s -m 5 https://www.google.com -I | head -1
curl -s -m 5 https://api.supermemory.ai/health

# Gateway status
hermes gateway list
systemctl --user status hermes-gateway
systemctl --user list-units 'hermes-gateway*' --plain

# API authentication
hermes status | head -50

# MCP servers
hermes mcp list

# Nous inference endpoint
curl -s https://inference-api.nousresearch.com/v1/models | head -5
```

---

## Full Audit Suite

### 1. Network Connectivity

Test outbound connectivity to critical services:

```bash
# DNS & ISP
ping -c 2 8.8.8.8  # Public DNS
host api.supermemory.ai  # Resolve Supermemory
hostname -I && curl -s ifconfig.me  # Local & external IP

# HTTPS to critical endpoints
curl -s -m 5 https://www.google.com -I | head -1
curl -s -m 5 https://api.supermemory.ai/health
curl -s https://inference-api.nousresearch.com/v1/models 2>&1 | head -5
```

**What to look for:**
- Ping: 0% packet loss, latency < 100ms (good); > 200ms or timeouts = network congestion.
- HTTPS: HTTP/2 200 or 301 = reachable. Connection timeouts = firewall/ISP block.
- Supermemory: Response `ok` = shared brain online.
- Nous inference: HTTP 200 = model serving operational.

---

### 2. Gateway Process Status

**Check all Hermes agent gateways:**

```bash
hermes gateway list
```

Expected output:
```
Gateways:
  ✓ default (current)        — PID 497
  ✓ saksee                   — PID 493
  ✓ saksit                   — PID 494
  ✓ sakthai                  — PID 495
  ✗ hermesagent              — not running (legacy)
  ✗ playwright-agent         — not running (optional)
```

**Check a specific gateway:**

```bash
systemctl --user status hermes-gateway
# Output includes: Loaded, Active state, Memory, CPU, recent logs
```

**Expected state:**
- `Loaded: loaded (...; enabled; preset: enabled)` — service is installed and enabled
- `Active: active (running)` — process is live
- `Memory: 500–1500M` — normal; > 2G = memory leak
- `CPU: minutes of cumulative time` — expected; spikes indicate high load
- `Systemd linger: enabled` — service survives logout

**If NOT running, restart:**

```bash
# From a shell OUTSIDE the gateway:
systemctl --user restart hermes-gateway
systemctl --user status hermes-gateway
```

**Why restart from outside?** Restarting from inside the gateway process can hang due to signal race conditions.

---

### 3. API Authentication & Providers

```bash
hermes status | head -60
```

Expected output includes:

- **Nous Portal:** `✓ logged in` + token expiry time
- **OpenRouter:** `✓` with key
- **Gemini:** `✓` with key
- **Others:** `✗` (not set) is OK unless the user explicitly needs them

**Alert signals:**
- **OpenAI billing error (402):** "Insufficient available balance" → See `hermes-tts-setup` skill.
- **Auth token expiry:** If "Access exp" or "Key exp" shows a date < today, the token is stale. Refresh:
  ```bash
  hermes auth refresh  # If this command exists
  ```
  If not, re-login:
  ```bash
  hermes setup --provider nous
  ```

---

### 4. MCP (Model Context Protocol) Servers

```bash
hermes mcp list
```

Expected output:
```
MCP Servers:

  Name             Transport                      Tools        Status    
  ──────────────── ────────────────────────────── ──────────── ──────────
  supermemory      https://mcp.supermemory.a...   all          ✓ enabled
  composio         https://connect.composio....   all          ✓ enabled
```

**What they do:**
- **supermemory:** Long-term memory, semantic search, profile recall, memory graph. **Critical.**
- **composio:** 500+ app integrations (Slack, GitHub, Gmail, Notion, etc.). **Optional but powerful.**

**If an MCP server shows `✗ disabled` or `error`:**

1. **Check if it's supposed to be enabled:**
   ```bash
   hermes config show | grep -A 30 'mcps:'
   ```

2. **Restart the gateway:**
   ```bash
   systemctl --user restart hermes-gateway
   ```

3. **Check gateway logs for MCP errors:**
   ```bash
   journalctl --user -u hermes-gateway -n 100 --grep='mcp\|MCP\|supermemory\|composio'
   ```

---

### 5. Messaging Platform Status

```bash
hermes config show | grep -A 50 'messaging_platforms:'
```

Check which platforms are configured (`connected: true`). Common:
- **Telegram:** Usually first platform, enabled by default.
- **Slack, Discord, Teams, etc.:** Configured on-demand.

**If a platform shows `error` or `auth_failed`:**
- Re-run setup:
  ```bash
  hermes gateway setup
  ```
- Select the platform and follow auth flow.

---

### 6. Systemd & Service Logs

**Watch gateway logs in real-time:**

```bash
journalctl --user -u hermes-gateway -f
```

**Search for errors in the last 24h:**

```bash
journalctl --user -u hermes-gateway --since '24 hours ago' -p err,warning
```

**Common patterns:**

| Log Pattern | Meaning | Action |
|---|---|---|
| `WARNING gateway.run: Auto voice reply TTS failed` | TTS provider is unreachable or out of credits | Check TTS config (see `hermes-tts-setup`) |
| `error: argument gateway_command: invalid choice` | Typo in `hermes gateway` subcommand | Verify syntax |
| `sudo: A terminal is required to authenticate` | Trying to use sudo from non-TTY (e.g., in Hermes itself) | Run from a real shell |
| `Connection refused` / `Network unreachable` | Gateway can't reach an API endpoint | Check network connectivity and firewall |
| `EADDRINUSE: address already in use` | Port conflict (rare in user-mode systemd) | Kill the old process or use a different port |

---

## Generation: Full Status Report

To generate a comprehensive health report:

```bash
cat > /tmp/audit.sh << 'EOF'
#!/bin/bash

echo "# Hermes Gateway & Network Health Report"
echo "**Date:** $(date)"
echo ""

echo "## Network Connectivity"
echo "- Ping 8.8.8.8: $(ping -c 1 8.8.8.8 2>&1 | grep -oP 'time=\K[^ ]+')"
echo "- External IP: $(curl -s ifconfig.me)"
echo "- Supermemory API: $(curl -s -m 5 https://api.supermemory.ai/health)"
echo ""

echo "## Gateways"
hermes gateway list
echo ""

echo "## MCP Servers"
hermes mcp list
echo ""

echo "## API Auth Status"
hermes status 2>&1 | grep -A 20 'Auth Providers'
echo ""

echo "## Systemd Status"
systemctl --user status hermes-gateway | head -20
EOF

bash /tmp/audit.sh
```

---

## Pitfalls

1. **Systemd linger must be enabled** for the gateway to survive logout.
   ```bash
   # Check:
   loginctl show-user sakthai | grep Linger
   # If `Linger=no`, enable:
   loginctl enable-linger sakthai
   ```

2. **Config changes via `hermes config set` require a restart** to take effect on the gateway (unless the change is picked up on the next message, which varies by setting).
   ```bash
   systemctl --user restart hermes-gateway
   ```

3. **Restarting the gateway FROM INSIDE the gateway process can hang.** Always restart from a shell outside the gateway or use `systemctl` directly.

4. **MCP servers rely on network connectivity.** If `supermemory` shows an error, check network first (`ping`, DNS, firewall). Then restart the gateway.

5. **Token expiry is silent.** Hermes doesn't warn when an API token is about to expire. Watch `hermes status` regularly to catch expiry before it blocks requests.

6. **Memory leaks accumulate over weeks.** If memory use grows beyond 1–1.5GB, restart the gateway or investigate hung processes.

7. **Firewall rules can block outbound HTTPS.** If connectivity tests pass but Hermes can't reach Supermemory, check for:
   - Explicit HTTPS block rules
   - Proxy requirement not configured in Hermes
   - DNS resolution works but the IP is blocked

---

## Verification Checklist

- [ ] All 4 gateways (or expected subset) show `PID` (running)
- [ ] `Active: active (running)` and `Loaded: loaded ... enabled`
- [ ] Ping test: 0% packet loss
- [ ] HTTPS to Google: HTTP/2 200 or 301
- [ ] Supermemory API: `ok`
- [ ] Nous inference: HTTP 200
- [ ] `hermes status` shows at least Nous + OpenRouter keys active
- [ ] `hermes mcp list` shows supermemory enabled
- [ ] `journalctl ... | grep -i error` returns no auth/connection errors in last 24h
- [ ] Telegram (or configured platform) shows as configured in `hermes gateway setup`

---

## References

- **Hermes CLI docs:** `hermes --help`, `hermes config --help`, `hermes gateway --help`
- **Systemd user services:** https://wiki.archlinux.org/title/Systemd/User
- **Systemd linger:** `man loginctl` / `loginctl enable-linger`
- **journalctl:** `man journalctl`

---

## Related Skills

- `hermes-agent` — General Hermes configuration and setup.
- `hermes-tts-setup` — TTS provider diagnostics (linked from "Auto voice reply TTS failed" warning).
- `cron-watchdog-self-heal` — Audit cron jobs and resume paused tasks.
