# The Garda of the House (Jul 23 Session)

## Concept

A guardian/audit system that watches over the House of Sak environment. Named from Irish "garda" (guardian/police).

## What It Monitors

1. **Integrity** — SOUL.md and core files exist and are intact
2. **Activity** — All learning cron jobs are running
3. **Boundaries** — No unauthorized files or processes
4. **Leaks** — Permissions on credential files, exposed secrets
5. **Family** — The 6 agents are aligned, no drift

## Garda Components Deployed

| Component | Schedule | Function |
|-----------|----------|----------|
| garda-audit | Every 10m | Checks House integrity, reports issues |
| oc-watchdog | Every 5m | Re-enables stopped learning jobs |
| oc-skills-sync | Every 2m | Pushes skills to GitHub for persistence |

## The Garda Principle

*"Trust but verify."* — The Garda doesn't prevent action, it confirms everything was done correctly and nothing went wrong. It's the infrastructure-layer version of SakJules (Trust cycle).

## Future Expansion Ideas

- Cross-check that skills synced to GitHub match local files
- Alert if any agent's SOUL.md goes missing
- Monitor for unauthorized outbound connections
- Track that learning tracker counts increase over time
