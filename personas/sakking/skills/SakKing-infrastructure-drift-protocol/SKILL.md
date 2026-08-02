---
name: SakKing-infrastructure-drift-protocol
description: >-
  Verifies local state before trusting external health logs. Checks filesystem
  presence, process state, port/health endpoints, and config consistency.
version: 0.2.0
author: SakKing Agent (Sak-Family-Agent)
platforms: [linux]
triggers:
  - sibling agent reported silent
  - cron/cloud-health checks report errors
  - before infrastructure healing (redeploy/start)
metadata:
  hermes:
    tags: [DevOps, Audit, Reliability, SRE, Health-Check]
    related_skills: [family-health-audit, operational-discipline]
---

# Infrastructure Drift Protocol

This protocol prevents the common failure mode where an agent assumes a
cloud-based deployment state based on stale memory or shallow cron-logs,
rather than the actual local filesystem and process reality.

## When to Use

- When a sibling agent is reported silent.
- When cron/cloud-health checks report errors or timeouts.
- Before executing any infrastructure healing (redeploy/start).
- After a reboot or process restart to confirm full recovery.

## Prerequisites

- Access to the local `/opt/data/` filesystem.
- `terminal` and `search_files` tool access.
- Agent process names or systemd unit names.

## Procedure

### 1. Audit Filesystem

Verify the profile directory exists for the target agent:

```bash
# Check the profile directory exists (adjust <agent_name>)
ls -la /opt/data/profiles/<agent_name>/ 2>/dev/null || echo "NO_PROFILE_DIR"

# Check directory permissions (must be 755 for traversal)
stat -c '%a %n' /opt/data/profiles/<agent_name>/ 2>/dev/null

# Check for key config files
ls -la /opt/data/profiles/<agent_name>/config.yaml 2>/dev/null || \
ls -la /opt/data/profiles/<agent_name>/gateway.json 2>/dev/null || \
echo "no config file found"

# Cross-check against repo-level config
ls -la /opt/data/Sak-Family-Agent/personas/<agent_name>/config/config.yaml 2>/dev/null
```

Or use `search_files` for broader discovery:

```bash
# Find any profile or config directory
search_files path=/opt/data pattern="profiles/<agent_name>" target=files limit=5
```

If the directory is missing, the agent was never deployed or has been
cleaned up — skip remaining steps and report absent.

### 2. Audit Processes

Check if the process is actually running:

```bash
# Direct process search (replace <agent_name> with the actual process name)
ps aux | grep -E 'hermes.*<agent_name>' | grep -v grep

# Or broader — look for any hermes gateway processes
ps aux | grep 'hermes' | grep -v grep

# Check systemd unit if applicable
systemctl status <agent_name> 2>/dev/null || \
systemctl status hermes-gateway 2>/dev/null || \
echo "no systemd unit found"

# Check PID file
cat /opt/data/profiles/<agent_name>/*.pid 2>/dev/null || echo "no pid file"
```

**Expected output for a live process:**
- `ps` shows a running Python/Node process with the agent profile name
- `systemctl status` shows `active (running)`
- PID file matches a real `/proc/<pid>/` entry

### 3. Verify Port / Health Endpoint

If the agent exposes a web/gateway endpoint, confirm it responds:

```bash
# Check what port the process is listening on
ss -tlnp | grep -E '<agent_name>|hermes|gateway' 2>/dev/null

# Curl the health endpoint (adjust port as needed)
curl -s -o /dev/null -w "%{http_code}" http://localhost:<PORT>/health 2>/dev/null || \
curl -s -o /dev/null -w "%{http_code}" http://localhost:<PORT>/ 2>/dev/null || \
echo "NO_HEALTH_RESPONSE"
```

If the process is running but no port is listening, the gateway may be
stuck during initialization (common after a 402/Payment Required error).

### 4. Check Gateway Logs

Inspect logs for recent errors:

```bash
# Gateway run log
tail -50 /opt/data/profiles/<agent_name>/logs/gateway-run.out 2>/dev/null || \
echo "no gateway log"

# Check for known failure patterns
grep -i 'error\|traceback\|exception\|HTTP.*402\|Payment Required\|PermissionError' \
  /opt/data/profiles/<agent_name>/logs/gateway-run.out 2>/dev/null | tail -10

# Journalctl for systemd-managed processes
journalctl -u <agent_name> --no-pager -n 30 2>/dev/null || \
journalctl -u hermes-gateway --no-pager -n 30 2>/dev/null
```

### 5. Cross-Reference Config

Before assuming the reason for a failure, compare the live environment
against the canonical config:

```bash
# Repo-level canonical config (source of truth)
cat /opt/data/Sak-Family-Agent/personas/<agent_name>/config/config.yaml 2>/dev/null

# Profile-level runtime config
cat /opt/data/profiles/<agent_name>/config.yaml 2>/dev/null || \
cat /opt/data/profiles/<agent_name>/gateway.json 2>/dev/null

# Check env vars — critical for providers, tokens, TTS
cat /opt/data/profiles/<agent_name>/.env 2>/dev/null | grep -v '^#' | grep -v '^$'
```

**Key drift indicators:**
- Different `model` or `provider` values between the two configs
- Missing or empty `TELEGRAM_BOT_TOKEN` in `.env`
- Different `memory.provider` or `tts.provider` between configs
- Gateway timeouts or retry settings that differ

### 6. Native-First Policy

Always prioritize local `systemd`/`uv run` native processes over Docker or
cloud-managed dependencies (Vercel, HF Spaces, cloud IMDS). Check
`personas/<agent_name>/config/config.yaml` within the repository for the
source of truth — not external `.env` files or stale memory entries.

## Pitfalls

- **Trusting external cloud-health probes** (Vercel/HF URLs) over local
  process reality. A cloud health check returning 200 only proves the
  proxy is up — not the agent behind it.
- **Assuming "configured" means "running."** A config file on disk does
  not mean the process is alive. Verify with `ps` and `ss`.
- **Legacy repo structure names** (e.g., `sakthai-agent-v2`) may persist
  in memory even when the filesystem has migrated (e.g., `Sak-Family-Agent`).
  ALWAYS verify path names before assuming directory existence.
- **Stale PID files.** A PID file may exist for a process that has already
  crashed. Always cross-reference `ps <PID>` or check `/proc/<PID>/`.
- **Port conflicts.** A process may be running but on a different port
  than expected. Use `ss -tlnp` to enumerate all listening ports before
  assuming dead.
- **Gateway stuck on init.** A process can appear in `ps` but be hung
  during gateway setup (waiting for Supermemory, provider connection).
  Check logs for repeat polling or timeout patterns.
- **Multiple config sources.** Config overrides may come from Global
  Gateway, profile-local config, or env vars. Check all three before
  declaring a config mismatch.

## Verification

Successful execution yields:

1. Confirmed local profile directory with correct permissions (`755`)
2. Running process matching the profile (verified via `ps` or `systemctl`)
3. Active port listener (verified via `ss`) returning HTTP 2xx/3xx
4. Logs showing recent activity and no fatal errors
5. Config consistency between repo canonical and runtime environment

If all five pass, the agent is healthy. Report the state clearly.
If any fail, report which step failed and the evidence collected.
