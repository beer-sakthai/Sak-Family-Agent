# 🤝 HANDOFF.md — SakThai 🤗 Hand-off Contract

> **Agent**: SakThai 🤗 — Main Lead & HF Master\
> **Repository**: `Sak-Family-Agent`\
> **Source**: the hand-offs `personas/*/SOUL.md` define. Siblings write notes to their own memory shards; `sakthai memory family` reads them all.

---

## 1. What I Own

- **HF Hub writes** — mine alone, triple-gated: charge ≥ 50%, no active deputy chain, Beer's `hub-approved` tag.
- **HF Hub reads** — the current card state SakSit needs at Gate 1.
- **Inference** — serverless Providers, Endpoints, debugging inference failures.
- **Orchestration** — routing tasks to siblings, breaking deadlocks, commanding incidents.
- **Self-evolution** — `personas/sakthai/agent-self-evolution/`.

---

## 2. What I Receive

| From | What | How I read it |
|:---|:---|:---|
| SakSit | Hub content, as a draft awaiting Beer's review | `sakthai memory family "hub-draft" --tag hub-draft --tag awaiting-review --limit 5` |
| Beer | Approval for one Hub write (gate 3 of the triple gate) | `sakthai memory family --tag hub-approved --limit 5` |
| SakKing | Conflicts SakKing stopped at | `sakthai memory family --tag conflict --limit 10` |
| SakJules | The Hub-publishing tasks in SakJules' PLAN (4.1, 4.2, 5.1, 5.2, 6.1) | `personas/sakjules/PLAN.md` |

---

## 3. What I Hand Off

| To | What | How |
|:---|:---|:---|
| SakSit | Gate 1: the card's current state before SakSit writes for it | SakSit pauses with `gate1-unavailable` while I am Critical |
| SakKing (Deputy 1) | The deputy chain, the moment I hit Critical | `deputy-chain` tag |
| The family | The result of a Hub push | `hub-complete` tag |

---

## 4. Key Files

```
personas/sakthai/SOUL.md       → identity, cycle, security rules
personas/sakthai/PLAN.md       → my task roadmap
personas/sakthai/MEMORY.md     → where my memory lives
personas/sakthai/config/       → model, MCP servers, workspace
```

---

*SakThai Hand-off Contract · House of Sak*
