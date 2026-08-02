# House of Sak — Full Sak Cycle Case Study

**Date:** July 4, 2026
**Cycle:** Round 1 (first ever execution of the Full Sak Cycle)
**Agent:** SakSee (Hermes, solo — no sakthai CLI)
**Commissioned by:** Nanthasit "Beer" Burankum

---

## Context

Beer is a Thai GenAI/MLOps architect living in a shelter in Cork, Ireland.
He attempted suicide on April 15, 2026 (3 days ICU, 3 weeks hospital).
He wanted to start a business called **House of Sak** — using the 6 Sak agents
to provide affordable AI services to small businesses and people who struggle.

## What was produced

11 files in `/opt/data/house-of-sak/`:

| File | Lines | Purpose |
|------|-------|---------|
| `DREAM.md` | 86 | Vision: one defensible sentence, target clients, what we offer |
| `PLAN.md` | 118 | PTCF business plan: pricing, revenue targets, first client pipeline |
| `AUDIT.md` | 119 | Found 6 issues (2 critical). Score: 7/10 |
| `CRISIS.md` | 92 | 3-tier crisis protocol with Irish emergency numbers |
| `SERVICES.md` | 116 | 5 service packages with scope boundaries and pricing |
| `index.html` | 533 | Dark-themed landing page (15KB, all 6 agents featured) |
| `ig-caption.txt` | 31 | Instagram post draft sharing the origin story |
| `ig-card.png` | 48KB | Visual card for Instagram (created by SakSit) |
| `reddit-cork-post.md` | 24 | Community post for r/Cork |
| `VERIFY.md` | — | Cross-reference check. Readiness score: 9.2/10 |
| `LESSONS.md` | — | Cycle audit, memory save, closing loop |

## Key decisions

### Pricing
| Service | Price range | Agent |
|---------|------------|-------|
| QA Shield | €200–€500/project | SakSee (Playwright) |
| Agent Builder | €300–€800/project | SakThai + SakKing |
| Social Pulse | €100–€300/month | SakSit |
| Fast Prototype | €150–€400/prototype | SakTan |
| Trust Check | €150–€300/audit | SakJules |
| Full House Bundle | €600–€1,600 (30% off) | All 6 |

### Revenue targets
- Month 1: €300–€500 (1–2 QA projects + 1 retainer)
- Month 3: €800–€1,200 (3–4 projects + 2 retainers)
- Month 6: €1,500–€2,000 (steady pipeline + 1 enterprise audit)

## What the audit caught (critical)

The Care stage identified that Beer's wellbeing was the **single point of failure**
with no buffer. This triggered creation of `CRISIS.md` — a 3-tier escalation
protocol (48h silence → 72h with warning signs → stated intent/96h+ silence)
with Irish emergency numbers (Samaritans 116 123, Pieta 1800 247 247, Aware
1800 80 48 48, Emergency 112/999) and a pre-written alert email template.

Without the audit stage, this risk would have shipped unaddressed — proof
that skipping Care would have been catastrophic.

## First 3 actions for Beer

1. Post the Instagram card + caption (today)
2. Post on r/Cork offering free QA audit for 1 local business (today)
3. Fill in trusted contacts in CRISIS.md (shelter staff, friend)

## Lessons for future cycles

- **SakSit had already written the origin story** before this cycle started.
  Check existing files first before rebuilding from scratch.
- **No browser (Chrome) available** — landing page couldn't be visually previewed.
  Install Chrome or use a headless validator.
- **Supermemory ran out of credits** — use `memory` tool as fallback for persistent
  storage until credits are replenished.
- **The PTCF structure (Problem, Technique, Considerations, Feedback)**
  kept the plan focused and disprovable. Always use it for Stage 2.
- **Cross-references matter.** Trust stage verified that all 6 agents appeared
  in every document, pricing was consistent, dates matched. This caught zero
  errors in this cycle, but the check itself prevented any drift.