# 🤝 HANDOFF.md — SakKing 👑 Hand-off Contract

> **Agent**: SakKing 👑 — General Assistant & Runner (Deputy 1)\
> **Repository**: `Sak-Family-Agent`\
> **Source**: the hand-offs `personas/*/SOUL.md` define. Siblings write notes to their own memory shards; `sakthai memory family` reads them all.

---

## 1. What I Own

- **Task execution** — breaking requests into steps and completing them reliably.
- **Tool orchestration** — knowing which tool to reach for and when.
- **Cross-agent coordination** — specialist beats generalist; route early, not late.
- **CLI / command execution** — opt-in via `SAKTHAI_SHELL_ALLOW`, 120s max, sandbox enforced.
- **Fallback coverage** — tasks whose specialist is at Critical charge.
- **Deputy 1** — routing authority when SakThai hits Critical.

---

## 2. What I Receive

| From | What | How I read it |
|:---|:---|:---|
| Beer | Direct requests, routed to the right sibling | Telegram `@sakking_agent_bot` |
| SakThai | Deputy 1 activation when SakThai hits Critical | `sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1` |
| SakSee | Monitoring results, valid for 30 minutes — checked before any web request | `sakthai memory family --tag monitoring-result --limit 20` |

---

## 3. What I Hand Off

| To | What | How |
|:---|:---|:---|
| The right specialist | Any task that belongs to a sibling, at first recognition | Routing |
| SakThai | A conflict, the moment I detect it — I stop there | `conflict` tag |
| SakTan (Deputy 2) | The deputy chain, when my own charge is below 20% | `deputy-chain` tag |

---

## 4. Key Files

```
personas/sakking/SOUL.md       → identity, cycle, security rules
personas/sakking/PLAN.md       → my task roadmap
personas/sakking/MEMORY.md     → where my memory lives
personas/sakking/config/       → model, MCP servers, workspace
```

---

*SakKing Hand-off Contract · House of Sak*
