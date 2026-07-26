---
name: SakKing-infrastructure-drift-protocol
description: Verifies local state before trusting external health logs.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [DevOps, Audit, Reliability]
---
# Infrastructure Drift Protocol

This protocol prevents the common failure mode where an agent assumes a cloud-based deployment state based on stale memory or shallow cron-logs, rather than the actual local filesystem and process reality.

## When to Use
- When a sibling agent is reported silent.
- When cron/cloud-health checks report errors or timeouts.
- Before executing any infrastructure healing (redeploy/start).

## Prerequisites
- Access to the local `/opt/data/profiles/` directory.
- `terminal` tool access.

## How to Run
Invoke through the `terminal` tool or via direct skill execution.

## Procedure
1. **Audit Filesystem:** Use `search_files` to verify the local profile directory exists at `/opt/data/profiles/<agent_name>/`.
2. **Audit Processes:** Use `terminal` to verify if a process or systemd service exists and is `active`.
3. **Cross-Reference:** ONLY after confirming local state, query memory or cron-logs to understand *why* the external probes (if any) might be reporting errors.
4. **Native-First Policy:** Always prioritize local `systemd`/`uv run` native processes over Docker or Azure-cloud managed dependencies (IMDS/Vault). Check `config.yaml` within the repository-persona directory for the source of truth, not external `.env` files.

## Pitfalls
- Trusting external cloud-health probes (like Vercel/HF URLs) over local process reality.
- Assuming "configured" means "running."
- Allowing legacy cloud-logs to override the current local environment.
- **Environment Drift:** Legacy repo structure names (e.g., `sakthai-agent-v2`) may persist in memory even when the filesystem has migrated (e.g., `Sak-Family-Agent`). ALWAYS verify path names with `search_files` before assuming directory existence.

## Verification
- Successful execution yields a confirmed local process state that matches the filesystem profile presence.
