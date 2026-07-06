---
name: SakKing-plg-funnel-economics
title: PLG Funnel Economics — Free-to-Paid Conversion, Activation, and Virality
description: |
  Diagnose and optimize product-led growth funnels: free-tier sizing, activation events,
  PQL scoring, free→paid conversion rate benchmarks by ACV band, reverse-trial vs
  freemium mechanics, K-factor virality, and hybrid PLG-to-sales handover thresholds.
  Use when designing a free tier, diagnosing low paid conversion, evaluating a reverse
  trial, deciding when to layer sales-assist onto self-serve, or re-pricing free
  capacity caps.
triggers:
  - "PLG conversion"
  - "freemium to paid"
  - "free tier design"
  - "activation rate"
  - "PQL"
  - "reverse trial"
  - "K-factor"
  - "virality loop"
inputs:
  - Free signup volume (monthly)
  - Activation event definition and current activation rate
  - Free → Paid conversion rate (last 90 days)
  - ARPA / ACV at upgrade
  - Self-serve CAC (hosting, support, infrastructure-per-free-user)
  - Viral coefficient or invite rate per user
  - Sales-assisted opportunity count sourced from PQLs
outputs:
  - Funnel-stage conversion rates (signup → active → PQL → paid → expanded)
  - Free-tier unit economics (cost-to-serve, payback, viral vs organic)
  - Activation event diagnostic
  - PQL scoring rubric
  - Decision on freemium vs reverse trial vs opt-in free
  - Hybrid handover threshold (when to layer sales-assist)
  - K-factor target and virality lever map
---

# PLG Funnel Economics

## Why this skill

A PLG business has a *funnel inside the product*, not just outside it (in marketing). Every free signup is a unit of inventory with three competing claims on it: (1) a real customer trying to get value, (2) a future paying customer who hasn't triggered the right behavior yet, and (3) cost. Get the funnel wrong and you grow MAUs at 80% margins but pay 100% of them.

This skill covers the *internal* mechanics of a PLG funnel that the existing
`gtm-channel-mix-economics` and `saas-pricing-architecture` skills touch but
do not operationalize.

---

## Core Concept: The PLG Funnel Has 6 Stages, Not 2

```
Signup → Activated → Engaged → PQL → Paid → Expanded
```

Most companies only measure two of these (Signup and Paid). Between them is
where 80% of the conversion lift lives.

### Stage Definitions

| Stage | Definition | Typical ACV <$5K PLG Benchmark | Typical ACV $5K–$25K Hybrid | Notes |
|---|---|---|---|---|
| **Signup** | Account created | 100% baseline | 100% baseline | Vanity metric alone; ignore. |
| **Activated** | Hit the activation event (see §3) | 20–40% | 30–50% | Largest single drop-off in the funnel. |
| **Engaged** | Used core feature ≥3× in 14 days | 40–60% of activated | 50–70% of activated | Predicts 90-day retention. |
| **PQL** | Triggered buying-intent signal (see §4) | 10–25% of engaged | 15–30% of engaged | The hand-off point to sales-assist. |
| **Paid** | Converted to a paid plan | 5–15% of PQL | 20–40% of PQL | Hybrid > PLG here because of human assist. |
| **Expanded** | Upsold or multiplied seats | 20–35% annually | 30–50% annually | The expansion-revenue motion. |

**Free → Paid conversion benchmarks (90-day window):**

| Free-model | Median Free→Paid | Top quartile | Trap |
|---|---|---|---|
| **Pure freemium** (always free tier exists) | 2–5% | 7–12% | Free tier cannibalizes paid if feature overlap is too high |
| **Opt-in free trial** (14–30 day) | 8–15% | 15–25% | Trial users churn hard at day 14 unless activated |
| **Reverse trial** (full feature N days, then downgrade) | 12–22% | 20–35% | Best for products where value is felt in <7 days |
| **Hybrid free + sales-assist on PQLs** | 25–45% | 40–60% | PQLs vs non-PQLs gated separately |

These are assembly-level medians; your numbers will vary by category, ICP fit, and time-to-value.

---

## Step 1 — Choose the Free Model

### Decision tree

```
Is time-to-value < 7 days for the user to feel an "aha"?
├── YES → Reverse trial (full features for 14 days, then downgrade)
│         Best for: productivity tools, dev tools, AI tools
└── NO  → Does usage of free tier create word-of-mouth / shared value?
          ├── YES → Freemium (free tier is forever)
          │         Best for: collaboration, data network effects
          └── NO  → Opt-in free trial (credit-card-free, 14–30 days)
                    Best for: vertical SaaS, workflow tools with setup cost
```

### Why these choices matter
- **Reverse trial** converts higher *per user* but produces lower signup volume because no permanent free tier exists.
- **Freemium** produces higher signup volume but the paid-conversion rate is lower; you need viral mechanics and a low cost-to-serve.
- **Opt-in trial** produces moderate volume and moderate conversion; safest default when uncertain.

**Rule of thumb:** Cost-to-serve per free user per month must be ≤ 10% of paid ARPA or you'll lose money on the funnelfloor even at top-quartile conversion.

---

## Step 2 — Size the Free Tier (Capacity)

Free-tier design has three levers, in order of impact:

### Lever A — What sits behind the paywall (features)
- **Lock integration depth**, not core utility. Slack locks message history; Notion locks guest access; Linear locks sub-issue count.
- **Never lock the "aha."** If users can't understand why your product matters on the free plan, they'll never convert.

### Lever B — Usage caps
- Set caps at **2× the median payer's usage**, not the median free user's usage. This puts free users in a position to feel "I would hit this within 60 days."
- **Make the next step visible.** A flat ceiling without a clear upgrade CTA feels punitive.

### Lever C — Time cap (trial only)
- 14 days for low-complexity, 30 days for setup-heavy.
- Always checkpoint on day 7 with a "you've used X of Y" nudge.

**Anti-pattern:** Locking on a feature that's easy to live without (e.g., removing the export button). This depresses free signup conversion for negligible paid lift.

---

## Step 3 — Define and Instrument the Activation Event

The activation event is a *behavior*, not a milestone. It must satisfy three criteria:

1. **Decisive** — once a user hits it, retention at day 30 jumps by ≥2× vs users who didn't.
2. **Early** — should occur within the first 1–3 sessions, ideally < 10 minutes from signup.
3. **Unique to your value** — would a user do this on a competitor? If yes, it's not decisive enough.

### How to find the right activation event
1. Take your day-30 retained cohort.
2. List every action taken in the first session.
3. Find the single action with the highest correlation to retention (odds ratio or logistic regression).
4. Test instrumentation: when a user does this, cohort retention jumps.
5. Reduce friction on that action until median time-to-activation is < 10 minutes.

**Examples:**
- Slack: sent ≥1 message to a teammate outside the company (collaborative aha)
- Notion: created a page AND invited a teammate
- Linear: created a team AND added ≥3 issues
- Figma: created a file AND invited a collaborator

**Common wrong activation events:** "Logged in twice." "Created account." "Viewed dashboard." These describe signup, not value.

---

## Step 4 — Score PQLs (Product-Qualified Leads)

A PQL is **a user whose in-product behavior signals buying intent**, not a marketing qualified lead. The standard scoring rubric:

| Signal | Weight | Rationale |
|---|---:|---|
| Repeatedly hit a usage cap (≥2× in 14 days) | 30 | Highest signal — they're literally blocked from getting more value |
| Invited ≥3 teammates (collaboration expansion) | 20 | Solo users rarely convert; teams do |
| Connected an integration (signals workflow fit) | 15 | Indicates they've decided this is part of their stack |
| Used a feature only available on paid tier (read-only trial) | 15 | Saw the door, wants in |
| Account from target-ICP domain (firmographic match) | 10 | Not sufficient alone; signal multiplier |
| Renewal-equivalent behavior (returned ≥14 days unprompted) | 10 | Indicates habit |

**Threshold:** A PQL score ≥ 60 is hand-off-ready. Score 30–59 is nurture (in-app upsells, lifecycle emails). Score <30 is ignore.

**Pitfall:** Don't score on signup alone. A user signing up from a Fortune 500 domain is not yet a PQL — they need to also hit the activation event.

---

## Step 5 — Run the Hybrid Handover (PLG → Sales-Assist)

When does it make sense to layer a sales team on PLG? Use the formula:

```
Sales-assist is justified when:

Payback period from a sales-assisted PQL ≤ 50% of ARPA / 12
         AND
PQL volume ≥ 20 per week per AE
         AND
Free-tier paid conversion (self-serve only) ≤ 8%
```

If those three conditions don't all hold, more sales headcount will *hurt* the unit economics (because sales-assist adds CAC faster than it lifts conversion).

**Handover mechanics:**
1. PQL score ≥ 60 triggers a CRM record creation.
2. AE gets a 24-hour SLA to send a *contextual* outreach (referencing the in-product behavior).
3. The PQL keeps the in-app premium feature access until 14 days post-discount; if no deal closes, they downgrade.
4. AE comp should be **lighter** than for traditional inbound MQLs (typically 60–70% of base) because the lead pre-qualified itself.

---

## Step 6 — Design and Measure Virality (K-Factor)

The K-factor is the average number of new users each existing user brings in.

```
K = i × c
where:
  i = invites sent per user (lifetime)
  c = conversion rate of each invite (signup → activated)
```

- K < 0.5: organic-only growth. PLG works but is paid-traffic-dependent.
- K 0.5–1.0: balanced. PLG is self-sustaining but not exponential.
- K > 1.0: viral. Each acquired user generates the next. (Realistic only at scale with strong network effects.)

### Levers to lift K-factor
1. **Make invites effortless and useful to the inviter.** Linear's "share view" creates a visible collaborator, not just an email.
2. **Make invites branded.** Slack's email invites carry the sender's name and the team name — recipient sees the social graph.
3. **Reciprocity loops.** Notion's "comment requires login" forces the recipient to sign up.
4. **Pair with collaboration features** (multiplayer, shared docs) — invites aren't a side feature, they're the *product*.

**Pitfall:** Counting every invite, not every accepted-and-activated invite. Sending 5 invites/year where 2 convert is K=10; sending 20 invites where 1 converts is K=20/100=0.10. The denominator matters.

---

## Step 7 — Free-Tier Unit Economics

### Cost-to-serve per free user
```
Cost-to-serve = (Hosting + Support + Infra-per-free-user) / Free MAU
```

If your ARPA is $50/mo and cost-to-serve is $8 per free user per month, you've spent 16% of ARPA on a non-paying user. At 3% conversion, your free-tier *blended* contribution margin = $50 × 0.97 (no pay) − $8 = −$5.76. **You're losing money on every free signup.**

Fix:
- Reduce hosting footprint (tiered logging, off-instance storage for dormant free users)
- Reduce support cost (in-app education, AI chat deflection)
- Cap free MAUs per domain (5 seats per free workspace)
- Lift the activation bar (require collaboration before accepting a free account)

### Free-tier payback period
```
Free-Tier Payback = Cost-to-Serve (per free user, lifetime)
                  / (Conversion Rate × ARPA × Gross Margin %)
```

If payback > 18 months for PLG or > 24 months for hybrid, the free tier is structurally money-losing — even with healthy top-line conversion.

---

## Pitfalls

1. **Calling Active Users a vanity metric without checking cost-to-serve.** 1M MAUs at $4/user cost-to-serve means you're burning $4M/year for a 3% conversion lift.
2. **Locking the wrong feature.** Removing the "aha" feature tears the funnel.
3. **Activation event that's really signup.** Confirm via day-30 retention lift before committing.
4. **PQLs scored on firmographic only.** A Fortune 500 user who never activated is not a lead.
5. **Sales-assist added before PQL volume supports it.** One AE drowning in 20 PQLs/week will spin; better to wait until 50/week.
6. **Reverse trial with no downgrade path.** Users hit "trial expired" with no visible "what was I using" — high churn spike at day 15.
7. **Counting invites, not activated invitations.** Vanity K-factors damage the cost basis.
8. **Skipping the hybrid test.** Some products are pure self-serve forever (e.g., developer tools); others never are. Test the bridge before scaling either.
9. **No usage-cap repeat signal.** If your cap is high enough that organic users don't hit it, your PQL signal is weak.
10. **Confusing PLG with "no sales team."** Hybrid > pure PLG for ACVs above $10K. Plan the handover in advance.

---

## Verification Step — The Quarterly PLG Scorecard

Build a one-page dashboard:

| Metric | Last Q | Target | Trend (4Q) |
|---|---:|---:|---|
| Signups/month | — | — | ↗ |
| Activation rate (% of signup hitting event) | — | 30%+ | — |
| 14-day retention of activated users | — | 60%+ | — |
| PQLs created/month | — | — | — |
| Free→Paid conversion (90-day window) | — | 4%+ (freemium) / 15%+ (trial) | — |
| Cost-to-serve / free user / month | — | <10% ARPA | — |
| K-factor (rolling 90-day) | — | >0.5 | — |
| % of paid ARR sourced from PQL handover | — | track only | — |
| Sales-assisted PQL→Closed-Won rate | — | >25% | — |
| Free-tier payback period (months) | — | <18 | — |

**Reconciliation rule:** If `cost-to-serve × free MAU / paid conversion × ARPA × GM%` ≠ payback — there's a data-model mismatch (likely ghost accounts or untracked usage). Audit before reporting.

---

## Integration With Other Skills

- **gtm-channel-mix-economics** — PLG is one channel; this skill treats PLG as a *self-contained funnel*, not a line item in channel mix.
- **saas-pricing-architecture** — The free tier is a tier. Pricing principles (decoy, anchoring, charm) apply to *where* the free tier sits in the visual hierarchy.
- **saas-retention-metrics** — Activation event and 14/30-day retention are upstream of NRR and GRR.
- **saas-growth-efficiency** — Free-tier customers distort Burn Multiple and Magic Number; subtract their CAC or treat as acquisition R&D.
- **b2b-pipeline-math-mql-to-close** — PQLs become SQLs in the standard B2B funnel; the handover point is handoff-quality-dependent.
- **cohort-analysis-operational-framework** — Run free→paid conversion cohort analysis by signup quarter to detect decay in the funnel itself.
- **land-and-expand-playbook** — Free tier is the "land"; expansion to team plan / higher tier is the "expand."
