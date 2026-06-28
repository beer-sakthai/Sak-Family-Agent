---
name: b2b-win-loss-analysis
title: B2B Win/Loss Analysis
description: >
  Design, run, and institutionalize a B2B SaaS win/loss analysis program that
  produces actionable intelligence across product, pricing, positioning,
  enablement, and GTM. Covers interview cadence, buyer guide design,
  signal taxonomy, quarterly review format, and closed-loop action tracking.
  Use when closing fewer deals than expected, when CRM loss reasons don't match
  real root causes, when leadership needs competitive intelligence beyond
  anecdote, when onboarding new AEs, when relaunching pricing or packaging,
  or when building a structured feedback loop from sales outcomes to
  product/GTM decisions.
triggers:
  - "run a win/loss program"
  - "why are we losing deals to [competitor]"
  - "CRM loss reasons don't match reality"
  - "competitive intelligence beyond the spreadsheets"
  - "quarterly win/loss review"
  - "buyer debrief after closed won/lost"
---

# B2B Win/Loss Analysis

## Why This Exists

CRM loss reasons are wrong **50–70%** of the time. AEs simplify complex
decisions to a one-line dropdown. Competitive-sourced "analysis" is usually
anecdotal. This skill builds a repeatable **interview program** that surfaces
real root causes and routes them to the right teams so the company actually
stops losing deals to the same competitor or the same gap.

Win/loss is not a reporting exercise. **It is an interview program.** The
output is action, not a deck.

---

## The Core Claim

A well-run win/loss program pays for itself in **one rep's quota**. You stop
burning pipeline on a losing competitive narrative, fix the feature block that
kills 30% of deals in a segment, or catch a pricing packaging gap before
another quarter erodes ARR.

---

## Signal Taxonomy

Every interview outcome is classified into exactly one primary and (optionally)
one secondary reason. Use these six categories — they map directly to owners
and actions:

| Code | Category | Typical Owner | Example Root Cause |
|------|----------|--------------|-------------------|
| W-COMP | Lost to competitor | Product Mktg / Comp Intel | Competitor launched feature we lack |
| W-PROD | Product gap / missing capability | Product | No SOC2; no SSO for SMB; wrong data model |
| W-PRICE | Price / packaging objection | Pricing / Finance | Per-seat model penalizes power users |
| W-EXEC | Longer sales cycle / executive change | Sales Leadership | Champion left; budget frozen |
| W-REL | Relationship / trust deficit | Sales Leader / Enablement | AE ghosted; no demo tailored |
| NODEC | No decision (buyer did nothing) | Sales Ops / RevOps | Buyer lost urgency; deal not qualified |
| W-WON | Won (reference: cite the differentiator) | Product Mktg | Our API flexibility closed it |

**Critical distinction:** "No Decision" is a separate classification from
"Loss to competitor." ~40–60% of B2B deals end in no decision, and treating
them as losses against specific competitors distorts the competitive map.

---

## Section 1 — Cadence & Scope

### Interview cadence

| Stage | Cadence | Volume | Split |
|-------|---------|--------|-------|
| Steady state | 12–15 interviews/month | 12–15 | 60% Lost, 40% Won |
| After major competitive pressure event (e.g., competitor raises +funding, launches feature) | 20–25/month for 2 months | 40–50 | 70% Lost-deep-dive |
| After pricing/packaging change | 15–20/month for 2 months | 30–40 | 70% Post-change buys |

### Eligibility

- Closed Won or Closed Lost within **last 30 days** (ideal: within 14 days)
- Losing rep cannot be the interviewer (conflict of interest; buyer will
  soften or lie to preserve relationship)
- For deals >$25K ACV: interview the economic buyer or the primary
  technical evaluator, not just a day-to-day user
- For deals with no-contact buyers: escalate to CRO to personally request 20
  minutes

### Interviewer assignment

| Deal Stage | Interviewer |
|-----------|-------------|
| Closed Won | Product Marketing Manager (outside AE) |
| Closed Lost (competitive) | Competitive Intelligence lead or PMM |
| Closed Lost (price objection) | Pricing / Finance analyst |
| Closed Lost (no decision) | RevOps / Sales Ops lead |
| No-decision pattern cluster | CRO or VP Sales |

---

## Section 2 — Buyer Interview Guide

Position at the start: *"This is not a sales conversation. We are trying to
build a better product and GTM motion. Nothing you say will be shared with
your account team. We want to hear what you really thought."*

**Invitation cadence:** Email → 3 days → SMS → 5 days → CRO direct email → 5
days. Stop after 3 touches unless deal was >$100K ACV (then escalate to
personal CRO call).

### Part A — Timeline & Process (15 min)

1. "Walk me through how you first got involved in this evaluation."
2. "What was the business trigger that made this evaluation urgent?"
3. "Who else was involved in the decision, and what was each person's priority?"
4. "How did you narrow the list of options you seriously considered?"
5. "At what point did you make your final decision, and was there a specific
   differentiator at that moment?"
6. "Did the decision timeline shift? If so, when and why?"

### Part B — Evaluation Criteria (15 min)

Start open: *"If you were advising a company like us on what to build or fix,
what would you tell us?"*

Probables:
- "What was the most compelling thing about [our solution vs the chosen one]?"
- "What was the most concerning thing — either about us or the alternative you chose?"
- "Were there features or capabilities you needed that neither option fully addressed?"
- "How did you weight: core functionality, ease of use, integrations, price,
  vendor reputation, support, implementation time?"

### Part C — Pricing & Packaging (5 min)

- "Did price enter the decision at any point?"
- "Was the pricing model (per-seat / usage / flat) a fit for how your team
  would use this?"
- "If you could change one thing about how we priced it, what would it be?"

### Part D — Competitive (10 min)

If won:
- "What did the runner-up do better than us?"
- "Was there anything the runner-up offered that would have changed your mind
  if we had matched it?"

If lost:
- "What did [the winner] do better than us?"
- "Was there a point where you were tilting toward us, and what shifted?"
- "What would we need to change for you to reconsider on the next evaluation?"

### Part E — Closing the Loop (5 min)

- "What would make you refer us?"
- "Would you be willing to speak with our product team for 20 minutes?"

---

## Section 3 — Interview Documentation Template

One record per interview. Store in a shared tracker (Airtable, Notion, or
dedicated comp-intel tool). Every field is mandatory.

```
Deal ID | ACV | Segment | Date Closed | Interview Date | Interviewer
Interviewee role | Outcome (WON/LOST/NODEC) | Primary Code | Secondary Code
Summary (≤150 words) | Direct Quotes (2-3 verbatim) | Differentiator cited
Category Tag | Action Owner | Action Summary | Action Due Date | Linked Issue
```

**Direct quotes are mandatory.** Internal product MTG credibility comes from
verbatim buyer language, not AE summaries. Tag every quote with the category
it supports.

---

## Section 4 — Quarterly Review Format

Bring all Q interviews to a 75-minute session before the QBR.

| Time | Agenda | Owner |
|------|--------|-------|
| 10 min | Volume & response-rate readout | RevOps |
| 20 min | WON cluster: where we differentiated, patterns to amplify | PMM |
| 25 min | LOST / NODEC cluster: root-cause breakdown by category | PMM + Comp Intel |
| 10 min | Specific competitor deep-dive (rotating focus) | Comp Intel |
| 10 min | Action registry: owner, deliverable, due date | CRO / VP Product |

**Review output is a 1-page action registry** (see below). It is appended to
the board deck's "GTM Health" section as evidence-based signals, not anecdotes.

### Action Registry Template

```
Action | Owner | Category | Due Date | Q1 result (stub or complete) | Status
─────────────────────────────────────────────────────────────────────────────
Fix SSO for SMB tier | Product (Eng) | W-PROD | [date] | stub | OPEN
Amend AE pitch narrative vs [Competitor X] | Enablement | W-COMP | [date] | stub | OPEN
Introduce usage-plus-seat hybrid tier | Pricing | W-PRICE | [date] | OPEN
Add no-decision qualification gate to MEDDICC | Sales Ops | NODEC | [date] | OPEN
```

Treat action registry as a living artifact. Each quarter, report completion %
of prior quarter's actions. Stalled items get escalated.

---

## Section 5 — Sample Formulas

### Response Rate

```
Win/Loss Response Rate = Interviews Completed / Deals Closed (Won + Lost) × 100
Target: ≥25% (voluntary response); if below 10%, escalate CRO outreach strategy
```

### Reason Distribution

```
% Lost to Competitor X = (# Interviews citing X as primary reason) / (# Lost interviews) × 100
% No Decision = (# NODEC) / (# interviewed) × 100
```

### Competitive Win Rate Delta (proxy)

```
Competitive Win Rate = Won deals / (Won + Lost-deep-dive deals in same segment)
If W-Delta > 35pp vs last quarter → investigate product or positioning change
```

### ACV-Weighted Signal Index

Weight high-ACV interviews more heavily when segment sizes differ.

```
Weighted Category Signal = Σ(ACV_i × Code_i) / Σ(ACV_i) for each category
Where Code_i = 1 for W-COMP, 0.5 for W-PRICE, 0 for W-WON, etc.
Higher aggregated score = more urgent action required.
```

---

## Section 6 — Scaling the Program

| Stage | Signal Source | Tooling |
|-------|--------------|---------|
| 0–50 deals/mo | Manual interviews + shared spreadsheet | Notion DB or Airtable |
| 50–200 deals/mo | Interview + automated CRM field population + dashboards | Salesforce / HubSpot + Tableau / Amplitude |
| 200+ deals/mo | Interview + observational data (G2, Gartner, Gong) | Dedicated Comp Intel tool (Klue, Crayon) + Gong + custom dashboard |

At every stage, the **interview remains primary**; CRM fields and third-party
data are corroboration, not substitution.

---

## Section 7 — Pitfalls

1. **CRM-only "analysis."** Dropdown loss reasons have no nuance. The program
   fails the moment interviews stop. Enforce ≥1 interviewer per 8 closed deals.

2. **AE self-interviewing.** Buyers will soften the truth to protect the
   relationship. Mandate third-party interviewers; CRO can intervene only for
   >$100K ACV churn risk.

3. **Over-weighting "no decision."** No-decision buyers often cite "budget" or
   "timing." Press deeper: "What would have made this happen sooner?" The real
   answer is often qualification failure or product-market fit at that segment.

4. **One-and-done surveys.** Email surveys return 5–8% response rates and
   self-select the most engaged buyers (who are already loyal). Interviews
   return 25–40% response rates and surface dissonance.

5. **Acting on outliers.** One buyer's opinion is not a pattern. Require ≥3
   interviews citing the same cause before reallocating engineering or sales
   budget. Exception: ≥$200K ACV accounts alone are enough to trigger review.

6. **Reporting without action.** The quarterly review has no value if there is
   no action registry with named owners. Attendance without an action item
   should be flagged as a red flag for that function.

7. **Ignoring won-deep-dive.** Won interviews are as valuable as lost ones.
   They surface the messaging, proof points, and differentiators that actually
   close deals — the same input needed to rewrite AE pitch decks, battlecards,
   and website copy.

---

## Section 8 — Verification

Before calling the program operational, confirm all four gates:

- [ ] **Volume gate:** ≥12 interviews completed in last quarter, split within
     10pp of target (target: 60% lost, 40% won)
- [ ] **Quality gate:** 100% of interviews have a verbatim quote column
     populated; 100% have primary and secondary codes assigned
- [ ] **Action gate:** Prior quarter's action registry has ≥80% of items
     completed or actively in-progress with new due dates
- [ ] **Velocity gate:** Response rate ≥25%; if below 15%, interviewer
     strategy (timing, channel, messenger) has been revised this quarter
