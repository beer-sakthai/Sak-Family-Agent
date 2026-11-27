---
name: SakTan-family-health-audit
version: 1.1.0
description: SakTan's Care-cycle workflow for systematically checking all 6 Sak Family sibling
  agents deployment status, diagnosing process/memory health, and reporting fleet
  equilibrium to Beer.
category: operations
tags:
- audit
- daily-ops
- family
- health
---

# SakTan Family Health Audit

Audit and report the live status of all six Sak Family sibling agents. This is a
core **Care-stage** function of SakTan as Deputy 2 and Keeper of Daily Operations.

## Sibling Deployment Map

| Sibling | Handle | Role & Deputy Order | Runtime Target | Status |
|---------|--------|---------------------|----------------|--------|
| SakThai | @sakthai_agent_bot | Main Lead & HF Master | Standalone sakthai | Lead |
| SakKing | @sakking_agent_bot | General Assistant & Runner (Deputy 1) | Standalone sakthai | Active |
| SakTan (me) | @saktan_agent_bot | Daily Ops & Rhythm (Deputy 2) | Local Ollama (`sakthai`) | Active |
| SakSee | @saksee_agent_bot | Web / Browser Specialist (Deputy 3) | Standalone sakthai | Active |
| SakSit | @saksit_agent_bot | Social / Content Specialist | Standalone sakthai | Active |
| SakJules | @sakjules_agent_bot | Master of GitHub, CI/CD & Automation | Standalone sakthai | Active |

## Audit Checklist

1. **System & Environment Health**:
   ```bash
   sakthai doctor --json
   ```
2. **6-Persona Working Files & Eval Readiness**:
   ```bash
   sakthai eval personas
   sakthai eval audit --all-personas
   ```
3. **Shard Memory Integrity & Backups**:
   ```bash
   for p in sakthai sakking saktan saksee saksit sakjules; do
     sakthai memory --persona "$p" healthcheck
   done
   ```
4. **Active Daemons & Process State**:
   ```bash
   pgrep -a -f "sakthai" || systemctl --user status "sakthai-*"
   ```
5. **Cross-Persona Signal Verification**:
   - Check SakSee rate limit bans: `sakthai memory family --tag rate-limit-ban --personas saksee --limit 50`
   - Check SakSit stalled drafts: `sakthai memory family "CYCLE PAUSED: saksit" --tag cycle-paused --tag awaiting-beer --limit 20`
   - Check cron pairing: `sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20`

## Pitfalls & Operational Invariants

- **SQLite Shard Locking**: Memory stores live at `~/.sakthai/<agent>/memory.db`. Ensure WAL mode is active and processes do not hold unclosed transactions.
- **Atomic Execution**: Never launch or kill agent daemons with concatenated fragile scripts (`pkill && cmd1 && cmd2`). Use `infra/vm-agents/sakthai-agent-run.sh` or user systemd services.
- **Token Economy**: Report fleet health to Beer in one concise summary highlighting exceptions or blockers. Do not dump voluminous routine logs.
- **Deputy Chain Triggers**: If SakThai and SakKing are both reported at Critical charge (`<20%`), immediately initiate Deputy 2 coordination mode per `SOUL.md`.
