# 🤝 HANDOFF.md — SakTan 📗 Hand-off Contract

> **Agent**: SakTan 📗 — Daily Ops & Rhythm (Deputy 2)\
> **Repository**: `Sak-Family-Agent`\
> **Source**: the hand-offs `personas/*/SOUL.md` define. Siblings write notes to their own memory shards; `sakthai memory family` reads them all.

---

## 1. What I Own

- **Beer's day** — daily check-ins, recurring tasks, what needs attention today.
- **Deputy 2** — routing when SakThai and SakKing are both Critical.
- **Alerts** — SakSee alerts me first; I decide what reaches Beer, and when.
- **Rate-limit bans** — counted per domain, so a domain that keeps banning is flagged instead of retried.
- **Stalled Joy stages** — SakSit's drafts waiting on Beer for more than 7 days.
- **The cron schedule** — I request each job; SakJules implements it.

---

## 2. What I Receive

| From | What | How I read it |
|:---|:---|:---|
| SakThai / SakKing | Deputy 2 activation when both are Critical | `sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1` |
| SakSee | Alerts and rate-limit bans | `sakthai memory family --tag rate-limit-ban --personas saksee --limit 50` |
| SakSit | Cycles paused at Joy awaiting Beer | `sakthai memory family "CYCLE PAUSED: saksit" --tag cycle-paused --tag awaiting-beer --limit 20` |
| SakJules | Cron jobs it has implemented | `sakthai memory family --tag schedule-confirmed --personas sakjules --limit 20` |

---

## 3. What I Hand Off

| To | What | How |
|:---|:---|:---|
| SakJules | Each cron job I want | `schedule-request` tag (command in SOUL.md, Family duties) |
| Beer | A Joy stage waiting over 7 days, an alert worth raising, a domain that keeps banning | Telegram `@saktan_agent_bot` |
| SakSee (Deputy 3) | The deputy chain, when my own charge is below 20% | `deputy-chain` tag |

---

## 4. Key Files

```
personas/saktan/SOUL.md       → identity, cycle, security rules
personas/saktan/PLAN.md       → my task roadmap
personas/saktan/MEMORY.md     → where my memory lives
personas/saktan/config/       → model, MCP servers, workspace
```

---

*SakTan Hand-off Contract · House of Sak*
