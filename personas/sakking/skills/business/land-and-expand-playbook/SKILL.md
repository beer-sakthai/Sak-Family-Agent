---
name: land-and-expand-playbook
title: Land and Expand Playbook
description: Operator-level guide for executing B2B SaaS land-and-expand motion to grow ACV within existing accounts. Covers expansion vectors, account scoring, timing benchmarks, product design requirements, and GTM alignment. Use when NRR is <110%, expansion pipeline is stalled, or when building systematic account growth.
triggers:
  - NRR below 110% with weak expansion pipeline
  - Landed accounts not progressing beyond starter tier after 90 days
  - Need predictable expansion revenue without proportionally increasing new sales
  - Evaluating product design for expansion enablement
  - Designing CSM responsibilities around growth, not just retention
---

# Land and Expand Playbook

Land-and-expand turns small initial deals into large, multi-year relationships. It is the highest-margin growth motion in B2B SaaS because it leverages existing trust, implementation work, and operational dependencies.

---

## Step-by-Step Workflow

### 1. Segment Accounts by Expansion Potential

Not every account can expand. Score every active account on three axes:

**Expansion Potential Score (0–10):**
- **Company trajectory** (headcount growth, funding, M&A): 0–3
- **Product usage depth** (feature adoption rate, power-user count): 0–3
- **Budget authority proximity** (does the champion control budget? Can you reach economic buyer?): 0–2
- **Competitive pressure / switching cost** (integrations built, data stored, workflows configured): 0–2

**Action**: Every 90 days, re-score accounts with >20% active utilization and >6 months tenure. Target accounts scoring 7+ for proactive expansion.

---

### 2. Map the Three Expansion Vectors

Assign each potential expansion to one of three vectors. Do not mix them in the same campaign.

**Vector A — Seat Expansion**
- Upsell from team/unit licenses to department or enterprise-wide agreements.
- Trigger: Headcount growth >20% YoY, request for additional seats, feature limits reached on current plan.
- Typical ACV lift: 1.5×–5×.

**Vector B — Module / Feature Expansion**
- Sell adjacent products, premium modules, or advanced capabilities.
- Trigger: Repeated support tickets for manual workarounds, feature requests that map to paid modules, completion of core workflow automation.
- Typical ACV lift: 1.3×–3×.

**Vector C — Upmarket / Platform Expansion**
- Move the account to enterprise tier with custom contracts, dedicated support, or platform access.
- Trigger: Compliance/security requirements (SOC 2, HIPAA), integration with broader tech stack, executive sponsorship change.
- Typical ACV lift: 3×–10×+.

---

### 3. Set Timing Benchmarks

**Critical time windows** (from original contract start date):
- **Days 1–30**: Onboarding. Goal: achieve time-to-first-value (TTFV) under 14 days.
- **Days 31–90**: Adoption. Goal: ≥2 weekly active users per licensed seat and ≥1 core workflow automated.
- **Days 91–180**: Expansion window opens. First upsell conversation should happen by day 100–120, before renewal discussions begin.
- **Days 181–365**: Renewal + multi-year negotiation. Expansion pitch joins renewal; never let renewal happen without expansion option on the table.

If no expansion motion is active by day 90, the account is at high risk of flat renewal or churn.

---

### 4. Build the Expansion Pipeline Separately

Track expansion ARR separately from new ARR.

**Metrics to build:**
- `Expansion Pipeline = Sum of qualified expansion opportunities by close date`
- `Expansion Win Rate = Closed-won expansion / Total expansion opportunities`
- `Expansion ACV Growth = (Expanded ACV - Original ACV) / Original ACV`

**Target benchmarks** (directional, not absolute):
- Expansion Win Rate: 25–40%
- Average days from expansion opportunity creation to close: 45–75 days
- Expansion as % of total new ARR: 30–50% for healthy growth-stage SaaS

---

### 5. Design the Product for Expansion

Expansion is a product problem masquerading as a sales problem.

**Required product design choices:**
- **Granular permissions**: Allow new departments/teams to be added without re-onboarding or security review delays.
- **Usage-based metering**: Built-in analytics showing which features are underutilized so CSMs can coach adoption.
- **Integration hooks**: Pre-built connectors to adjacent tools your customers use (so expansion modules feel native, not bolted).
- **Self-service upgrade path**: Seat additions and module upgrades should be purchasable inside the product for accounts under a defined ACV threshold (e.g., <$50K).

If expansion requires a 4-week custom contract every time, you will lose 60–80% of potential upgrades.

---

### 6. Align CSM Comp and Incentives

**Danger**: If CSMs are measured only on retention/churn prevention, they will avoid pushing expansion for fear of upsetting the customer.

**Correct incentive structure:**
- **Base**: 70–80% on retention/health score (GRR target, product usage health).
- **Variable**: 20–30% on expansion pipeline creation and closed-won expansion.
- **Team goal**: NRR target that blends retention and expansion outcomes.

Include a minimum "expansion touches" activity metric if the team is new to proactive growth (e.g., 3 qualified expansion conversations per account per quarter).

---

### 7. Execute the Expansion Cadence

**Quarterly rhythm for accounts >90 days old:**

- **Week 1**: Re-score accounts; identify top 20% by expansion potential.
- **Week 2**: CS/AM conducts "growth review" — not a renewal conversation, but a business-outcomes review: "What are your goals for H2? Where is the tool falling short?"
- **Week 3**: Present tailored expansion proposal with ROI calculator.
- **Week 4**: Legal/security review if enterprise tier; or self-service checkout if low-friction.

For lower-touch accounts (PLG), automate expansion nudges:
- In-app messages when seat limit reached or feature usage hits 80% of plan cap.
- Email sequences triggered by usage milestones.
- Pricing page with "upgrade" sticky banner when usage threshold breached.

---

## Formulas and Examples

### Simple LTV Upside from Expansion
```
Original ACV: $24,000 (24 seats × $1,000)
Expansion vector: +12 seats + advanced analytics module ($500/mo)
Expanded ACV: $48,000

ACV Growth Rate = ($48,000 - $24,000) / $24,000 = 100%
Multi-year value lift = $24,000 × 3 years = $72,000 incremental LTV
```

### CAC Payback Benefit
If original CAC was $6,000 and expansion cost is only $1,000 (no new S&M spend):
```
Effective CAC for expanded account = $6,000 / $48,000 = 12.5% of ACV
Original CAC ratio = $6,000 / $24,000 = 25% of ACV
```
Expansion doubles capital efficiency without new customer acquisition.

### Expansion Ratio Check
```
Expansion Ratio = Expansion MRR in quarter / Churned MRR in quarter

Target: >1.0
Healthy: 1.3–4.0
World-class: 4.0+
```
If expansion ratio is <1.0, the business is only "growing" by adding new customers faster than it loses old ones—expensive and fragile.

---

## Pitfalls

- **Expansion at renewal only**: Pushing upsells only during renewal negotiations signals price-gouging. Build expansion into the product journey.
- **Ignoring seat sprawl**: Allowing informal seat sharing or shadow-IT usage without tracking caps expansion revenue. Enforce license limits.
- **Premature enterprise push**: Moving accounts to enterprise tier before they have compliance/scale needs creates churn. Match expansion to existential customer needs.
- **CSM overloading**: If one CSM manages 100+ accounts, they cannot run structured expansion programs. Cap at 30–50 for proactive growth.
- **Product bloat**: Adding modules to drive expansion without addressing core value weakens retention—fix the core first.
- **Forgetting negative expansion**: Contraction and churn of large accounts more than offset small expansions. Monitor both.

---

## Verification Step

Run this monthly:
1. Pull accounts open >90 days.
2. Calculate % of those accounts with expansion revenue in trailing 90 days.
3. Calculate average days from contract start to first expansion.
4. Compare actual expansion revenue vs. what potential scoring model predicted.

If predicted expansion was >$400K and actual is <$200K, inspect whether:
- Product lacks upgrade triggers (usage data not surfaced to CSMs)?
- CSMs lack incentive (comp plan misaligned)?
- Timing is off (expansion offered too early or too late)?

Diagnose and adjust the vector/timing/incentive before next quarter.
