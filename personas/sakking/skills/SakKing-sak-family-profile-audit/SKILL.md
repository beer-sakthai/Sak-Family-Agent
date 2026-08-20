---
name: SakKing-sak-family-profile-audit
description: Audit agent profiles for infrastructure and deployment state.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [DevOps, Audit, Agent Management]
---
# Sak Family Profile Audit

This skill systematically audits the local `/opt/data/profiles/` directory to identify the infrastructure state of each Sak Family agent. It distinguishes between agent presence (profile directory) and active deployment status (systemd/process).

## When to Use
- When diagnosing why a sibling agent is silent.
- Before initiating any redeployment or healing.
- When the cron/cloud-health checks provide ambiguous or stale data.

## Prerequisites
- Access to the `/opt/data/profiles/` directory.
- `terminal` tool for process and systemd service inspection.

## How to Run
Invoke through the `terminal` tool.

## Procedure
1. **List Profiles:** Run `search_files(pattern="profiles/*", target="files")` to confirm active agent directories.
2. **Audit State:** For each profile, inspect the `gateway_state.json` and logs.
3. **Verify Process:** Use `terminal` with `ps aux` or `systemctl` to verify if a process or service is active.

## Pitfalls
- A directory in `profiles/` does not guarantee a running process.
- Do not rely on cloud-service probes; verify local processes first.
- If cron failures occur, verify if the cron job is an orphaned artifact of a previous architecture (e.g., Azure VM-based) before attempting a fix. Infrastructure-drift (e.g., Vercel vs. Local Systemd/Docker) is a common root cause for "broken" health checks.

## Verification
- A successful audit will produce a status table mapping agent names to their confirmed local process status.

## Git Authentication Pitfall
- If you experience authentication failures during repository interaction, verify your identity configuration locally: `git config --local user.name` and `git config --local user.email`.
- Since the environment may lack `gh` CLI for automated auth, use the `Credential Helper` approach:
  1. Configure credentials for the current session: `git config --global credential.helper store`
  2. Use a GitHub Personal Access Token (PAT) with `repo` scope when prompted for the password, not your standard account password.
  3. Ensure the repository URL is correct: `git remote -v` should point to `https://github.com/beer-sakthai/Sak-Family-Agent.git`.
