---
name: b2b-forecast-call-discipline
description: Run defensible, unbossed weekly/quarterly forecast calls with proper category hygiene, slip detection, and confidence-weighted roll-ups for B2B SaaS. Use when a CRO/RevOps leader needs to convert pipeline into a board-trustworthy commit number and stop forecast shopping by reps.
category: business
---

# B2B SaaS Forecast Call Discipline

The forecast call is the single highest-leverage operating ritual in revenue leadership. Done badly it produces a fantasy number the board re-baselines around and a CRO who overpromises. Done well it surfaces real risk early, holds reps to evidence-not-aspiration accounting, and gives the CRO a number they can defend in any board meeting.

## When to use this skill

- CRO / VP Sales / RevOps leader runs a weekly cadence and the number keeps drifting late in quarter.
- Board / CEO keeps asking "why didn't we hit commit?"
- Reps move deals between categories with no justification (forecast shopping).
- Pipeline headed into quarter-close is opaque or stale.
- New VP Sales or first CRO hire inheriting a politically broken forecasting motion.
- Two consecutive quarters of >=15% miss-to-commit from stated forecast at same horizon.

## Core mental model

**A forecast is an act of evidence, not aspiration.**
Every category commitment should be defensible in 30 seconds to a hostile CFO. If the AE cannot make that case, the category is wrong.

Three numbers every call:

- **Commit** — what you will hit barring a surprise. Only held + best-evidence late-stage deals.
- **Best case / Most likely** — probability-weighted realistic outcome. (Pick one term per company and enforce — ambiguity here is itself a hygiene failure.)
- **Upside** — pull-in candidates with a real reason, not "may close" hope.

Slip math and stale-pipeline math run alongside the category discussion, not inside it.

## Exact workflow

### Pre-call (T-24h)

1. Pull a category snapshot by rep, segment, and deal age: commit, best case, upside, omitted, closed-won YTD.
2. Flag every commit deal that has been in commit for >14 days without stage advancement (= sandbag risk).
3. Compute **gap-to-commit** by segment: `(Commit target − Hard commit) / Commit target`. Any segment gap >15% two weeks before quarter close IS the entire call agenda.

### The call itself (45 min, weekly cadence)

4. **Open with five numbers, not narrative.** 5 minutes, top of screen:
   - (a) Total commit vs target
   - (b) Slip-back ratio last week
   - (c) Stale commit deals (in commit >14d, no advance)
   - (d) % of pipeline aged >30 days
   - (e) Gap-to-commit by segment
   These are the Battery Ventures "5 metrics every forecast call opens with" — they signal health before any single deal is discussed.
5. **Walk commits first.** Every AE defends every commit deal in 30 seconds: stage, next step, decision-maker, decision date, what would pull it out. If the AE cannot defend, the deal moves to best case or is omitted on the spot.
6. **Force-rank stale commit deals.** Any deal at the same stage for >2x your median stage age gets the binary "commit or demote?" — no neutrality allowed.
7. **New commits require an artifact.** Verbal commits without one of {email confirmation, scheduled demo, security review started, contract-out clause drafted} are not commit. Verbal-only "I think we're going to close" is automatically best case.
8. **Slip-back audit last 4 weeks.** Show the % of deals that were in commit two weeks ago and slipped. If >40% of last week's commit dollar slipped, next week's commit will underdeliver by a similar magnitude. Common pattern: AEs protect their commit slot with Volume-of-Commit deals; slip-back exposes the lie.
9. **Capture help-asks with a named owner.** Every commit deal flagged "needs help" gets a specific owner assigned on the spot (CRO, VP Product, CEO for enterprise). No anonymous asks — unowned asks never close.
10. **CRO states THE number with explicit confidence.** "1.05M commit, 80% confidence." If confidence <70% and you are <3 weeks to close, escalate to the CEO and board that same day — do not absorb the risk privately.

### Post-call (within 24h)

11. Publish the rolled-up commit, best case, upside, gap-to-commit by segment, and list of help-needed deals with named owners — to RevOps and leadership — one page, not a deck.
12. Move demoted deals in CRM (Salesforce stage or category picklist). Spoken category != CRM category is the single fastest trust-killer in forecasting. Re-run the roll-up from CRM, not from notes.

## Formulas

- **Gap to commit** = `(Commit target − Hard commit) / Commit target`. Always compute by segment; aggregate hides the segment in trouble.
- **Slip-back ratio** = `# deals in commit last week that slipped this week / total deals in commit last week`. Target: <25%. >40% = regime is broken, not the call.
- **Category hygiene index** = `% of forecasted $$ in CRM that matches spoken forecast category`. Target: ≥90%. <80% = the call is theatre.
- **Forecast accuracy (forward, like-for-like)** = `|Actual − Commit stated at the same forecast horizon| / Commit stated at that horizon`. Measure at the same point in the prior quarter (e.g. "what did we call at T-3 weeks?") to avoid end-of-quarter optimism bias.
- **Roll-up confidence (CFO-defensible)** = `Σ (deal_value × rep_assigned_confidence) / Σ deal_value`, then **floor at the lowest-confidence large-deal segment**. One 95%-confident rep cannot offset a 50%-confident enterprise rep holding 30% of the quarter.

## Pitfalls

- **Hidden commit.** AEs pack weak deals into commit "to be safe" — they collapse at end of quarter. Cure: artifact rule (point 7) + stale-cohort force-rank (point 6).
- **Forecast shopping.** Rep moves the same deal between categories across weeks so it stays in the forecast. Cure: category-change audit, every change requires a one-line CRM reason visible to manager.
- **Pollyanna CRO.** CRO inflates commit because the board wants a bigger number. Cure: confidence stated explicitly (point 10), and review accuracy at next quarter's board meeting against the confidence band you stated.
- **Stale-pipeline lies.** "$4M in pipeline, 60% in stage 4" means nothing if those deals are 90 days old. Pipeline age outranks stage label — always.
- **One-number reporting.** Reporting only "we'll hit $1M" hides the segment in trouble. Always report commit / best case / upside AND gap-to-commit by segment.
- **Sandbag quarter-end bargain.** Last 5 days of quarter, AEs "discover" pipeline they held back. If discovered deals >>10% of commit, your forecast was wrong all quarter — treat as data for next quarter's prep, not a surprise.

## Forecast category definitions (print, pin to wall, enforce verbatim)

| Category | Definition | Include test (all three must hold) |
| --- | --- | --- |
| **Commit** | Closing is a will-happen, not a may-happen. AE will be embarrassed if it slips. | Decision-maker identified AND contract drafted/verbal price accepted AND close date within 14 days AND last activity <7 days |
| **Best case** | Probable (>=50%) but missing one critical item. | At least one of: missing champion, missing economic buyer, missing technical validation |
| **Upside / Pipeline** | Possible (<50%). Not a coaching failure if it slips. | Validated need AND decision-maker identified OR champion engaged |

Naming varies — "best case" vs "most likely" vs "realistic." Pick one at first call and never rename again.

## Verification step (next 4 weeks, then monthly)

Run a weekly **forecast self-audit**:

- Compare last week's commit to this week's actual.
- Compute slip-back ratio, gap-to-commit by segment, and category-hygiene index (spoken vs CRM).
- After 4 weeks you should see: slip-back trending <30%, category-hygiene index >85%, and forecast accuracy on commit within ±10%.

If you don't, the cure is not more process — it is 1:1 coaching on the worst 2 reps. Typically 80% of the over-commit comes from 20% of AEs. Treat it as a coaching queue, not a process redesign.

## Companion skills

- Use `revops-sales-velocity-and-pipeline-coverage` for the pipeline-coverage math that feeds the gap-to-commit calculation.
- Use `b2b-pipeline-math-mql-to-close` for the upstream conversion math that determines whether the forecast gap is a pipeline-creation problem or a closing problem.
- Use `board-deck-kpi-narrative-framing` for packaging the forecast accuracy story into the board narrative.
