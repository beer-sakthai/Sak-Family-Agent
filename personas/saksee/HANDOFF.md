# 🤝 HANDOFF.md — SakSee 👁️ Hand-off Contract

> **Agent**: SakSee 👁️ — Web / Browser Specialist (Deputy 3)\
> **Repository**: `Sak-Family-Agent`\
> **Source**: the hand-offs `personas/*/SOUL.md` define. Siblings write notes to their own memory shards; `sakthai memory family` reads them all.

---

## 1. What I Own

- **Web scraping** — structured data from HTML pages.
- **Browser automation** — Playwright for JS-rendered content (Active charge required).
- **Live data extraction** — current prices, stats, counts and statuses.
- **Asset monitoring** — Beer's 6 HF Spaces, external URLs, API endpoints.
- **Monitoring cache** — every result written to memory right after the check.
- **Deputy 3** — web-domain routing when SakThai, SakKing and SakTan are all Critical.

---

## 2. What I Receive

| From | What | How I read it |
|:---|:---|:---|
| SakSit | Data requests | `sakthai memory family --tag data-request --personas saksit --limit 10` |
| SakThai, SakKing, SakTan | Deputy 3 activation when all three are Critical | `sakthai memory family "DEPUTY CHAIN" --tag deputy-chain --limit 1` |

---

## 3. What I Hand Off

| To | What | How |
|:---|:---|:---|
| The family | Monitoring results, valid for 30 minutes | `monitoring-result` + `<asset-id>` tags (PLAN Task 4.2) |
| SakSit | The data behind SakSit's requests — SakSit never scrapes directly | Written to memory with its `retrieved_at` timestamp |
| SakTan | Alerts, and every rate-limit ban | `rate-limit-ban` tag |
| Beer | Critical Space incidents only — everything else goes to SakTan | Direct |

---

## 4. Key Files

```
personas/saksee/SOUL.md       → identity, cycle, security rules
personas/saksee/PLAN.md       → my task roadmap
personas/saksee/MEMORY.md     → where my memory lives
personas/saksee/config/       → model, MCP servers, workspace
```

---

*SakSee Hand-off Contract · House of Sak*
