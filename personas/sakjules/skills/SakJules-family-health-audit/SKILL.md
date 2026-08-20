---
name: SakJules-SakKing-family-health-audit
description: ">-   SakKings workflow for systematically checking all Sak Family sibling agents   deployment status, diagnosing why they arent replying, and reporting the   family health state to Beer. Covers the Care-cycle audit of the fleet."
---

# SakKing Family Health Audit

Audit and report the live status of all Sak Family sibling agents. This is a
**Care-cycle** function.

## Sibling deployment map

| Sibling | Telegram Handle | Deployment Target | Status |
|---------|----------------|-------------------|--------|
| SakKing (me) | @sakthai_agent_v2_bot | Hermes Gateway | Live |
| SakThai | @sakthai_v1_bot | Local Hermes Profile | Check |
| SakSee | @saksee_bot | Local Hermes Profile | Check |
| SakSit | @saksit_agent_bot | Local Hermes Profile | Check |
| SakTan | @saktan_agent_bot | Local Hermes Profile | Check |
| SakJules | @SakJules_Agent_bot | Local Hermes Profile | Live |

## Audit checklist

1. Check local process state: `ps aux | grep hermes`
2. Check gateway logs: `/opt/data/profiles/<agent>/logs/gateway-run.out`
3. Verify environment variables: inspect `/opt/data/profiles/<agent>/.env` for required tokens
4. Check for 'HTTP 402 Payment Required' errors in logs — this indicates a Supermemory billing block that will prevent gateway initialization.
5. Check directory permissions: Ensure `/opt/data/profiles/<agent>/` has `755` permissions for directory traversal.

## Pitfalls
- **Configuration Drift:** Runtime models may diverge from local `config.yaml` due to Global Gateway overrides. Check `/opt/data/gateway/config.yaml` and verify active process env vars if runtime model behaves unexpectedly.
- **Sequential Startup:** Never chain gateway starts (e.g., `pkill && cmd1 && cmd2`). The chain is brittle and hangs if any process blocks. Start each agent atomically as an individual background process.
- **Supermemory 402 Payment Required:** If an agent attempts to ingest data into Supermemory and hits an HTTP 402, the agent loop will crash. Check `gateway-run.out` for `urllib.error.HTTPError: HTTP Error 402: Payment Required`. This blocks memory operations and initialization.
- **Permission Errors:** Gateway failure due to `PermissionError` (Errno 13) on `config.yaml` or `auth.json` is a frequent cause of "silent" agents. Verify file permissions (`644`) AND directory permissions (`755`) for the parent profile directory (`/opt/data/profiles/<agent>/`) to allow process traversal.
- **Token Configuration:** Env files are at `/opt/data/profiles/<agent>/.env`. Check these directly for `TELEGRAM_BOT_TOKEN` and other required variables. If updating, edit the `.env` file for the target agent.
