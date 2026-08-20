# Jul 26 — Garda Monitor Fleet Expansion

Deployed 10 new no_agent Python monitor scripts as cron jobs.
Total Garda cron jobs: 5 original env-guard + 10 new + 1 self-heal + 1 weekly audit = 17.

## New Scripts Created

All at `/opt/data/profiles/saksit/scripts/`:

| Script | Lines | Purpose |
|--------|-------|---------|
| `monitor-network-audit.py` | 87 | Outbound connections, 3-agent check |
| `monitor-firewall.py` | 62 | Listening ports, unexpected services |
| `monitor-agent-health.py` | 84 | Process/SOUL.md/memory/session DB check |
| `monitor-log-scanner.py` | 54 | Gateway log error pattern detection |
| `monitor-system-resources.py` | 62 | Disk, memory, session DB, FDs |
| `monitor-skill-integrity.py` | 57 | SHA256 hash audit across 3 agents |
| `monitor-link-validator.py` | 53 | URL reachability from skill docs |
| `monitor-ci-status.py` | 65 | GitHub Actions status for 4 repos |
| `monitor-deps.py` | 48 | Required commands and env vars |
| `monitor-family-manifest.py` | 81 | Consolidated agent consistency check |

## Pitfall Documented

**Cron schedule update + resume required.** Discovered Jul 26:
`cronjob(action='update', schedule='5m', job_id='X')` changes the schedule but
after one run the job enters `state: completed` silently. Must call
`cronjob(action='resume', job_id='X')` after every schedule update to keep the
job repeating.

## Health Baseline

- agent-health: All 3 agents running continuously
- Session DB: saksit 137MB, sakthai 817MB, saksee 175MB
- Gateway logs: recurring auth_fail/timeout/api_error patterns (historical)
- Broken links: several external URLs in B2B SaaS reference skills
