---
name: SakKing-gtm-channel-mix-economics
title: GTM Channel Mix Economics
triggers:
  - GTM motion selection (PLG vs sales-led vs hybrid)
  - CAC by channel optimization
  - Marketing budget allocation across channels
  - Evaluating new channel launches
  - Diagnosing why blended CAC is rising
description: Optimize GTM channel mix by evaluating PLG, sales-led, and hybrid motion economics. Models marginal CAC by channel, enforces LTV:CAC and payback benchmarks, and allocates budget to maximize ARR at target efficiency. Use when choosing a GTM motion, scaling beyond seed stage, or when blended CAC increments outpace new ARR.
---

# GTM Channel Mix Economics

## Step-by-Step Workflow

### 1. Lock the ICP and ACV Band
GTM motion is primarily dictated by ACV, not product type.
- **PLG-first**: ACV < $10K. Self-serve trials/freemium, sales-assisted onboarding for expansion.
- **Sales-led**: ACV > $25K. Outbound/inbound with demos, proof-of-value, multi-threading required.
- **Hybrid**: $10K–$25K ACV band. Need product-led acquisition with sales-assisted closing, or vice versa.

**Action**: Define ACV median and 25th/75th percentiles before debating motion.

### 2. Build Channel-Level Unit Economics
Do not rely on blended CAC. Calculate per-channel:
- `Marketing S&M spend` + `Sales comp & tooling` + `Customer success onboarding cost`
- `New ARR attributed` (first-touch, last-touch, or multi-touch—pick one consistently)
- `CAC = Channel spend / New ARR`

**Formula: LTV:CAC**
```
Customer LTV = (ARPA × Gross Margin %) / Churn rate
LTV:CAC = Customer LTV / CAC
```
- Target LTV:CAC ≥ 3:1 for Series A+, ≥ 5:1 for mature SaaS.
- Watch the payback period: `CAC / (ARPA × Gross Margin %)`
- Target CAC payback ≤ 12 months (PLG), ≤ 18 months (sales-led).

### 3. Model Marginal CAC by Channel
First-dollar CAC is deceptive. After saturation, CAC rises sharply.

**Procedure**:
1. Plot cumulative spend against cumulative ARR for each channel over trailing 6 months.
2. Fit a curve: usually quadratic or logarithmic decay.
3. Identify inflection point where CAC per incremental dollar rises >20% over channel average.
4. Cap budget at the inflection point unless LTV:CAC remains ≥ 3:1.

**Formula: Marginal CAC**
```
Marginal CAC = (Channel spend(t) - Channel spend(t-1)) / (New ARR(t) - New ARR(t-1))
```
If marginal CAC > 2× blended CAC, pause incremental spend.

### 4. Allocate Budget by Channel Efficiency
Use a two-gate filter:
- **Gate 1 — Efficiency**: LTV:CAC ≥ 3:1 AND payback ≤ 18 months.
- **Gate 2 — Growth**: Channel must produce ≥ 10% new ARR of next year's target to justify management overhead.

Allocate budget to channels passing both gates in descending order of marginal efficiency until either:
- Blended LTV:CAC hits target, or
- All passing channels are saturated.

### 5. Validate Motion Consistency
**Pitfall: The Hybrid Trap**
A sales-led team bolting on a freemium product and calling it hybrid usually produces two disconnected metrics monsters: PLG vanity metrics (free signups) and sales-led CAC, with no shared funnel.

**Check**:
- Does every motion share the same CRM/funnel definitions?
- Are PLG upgrades and sales-led new logos measured in the same ARR pipeline?
- Is customer success segmented by motion, or does one team serve both with conflicting SLAs?

### 6. Revisit Quarterly with these Exact Reads
- CAC by channel (rolling 90-day)
- Marginal CAC by channel (quarter-over-quarter)
- LTV:CAC by channel
- Payback period by channel
- Channel mix % of new ARR
- Marginal read: Does the *next* $100K of spend in channel X generate ARR at target efficiency?

## Formulas Cheat Sheet

| Metric | Formula | Benchmark |
|--------|---------|-----------|
| CAC | Channel S&M / New ARR | PLG <$5K, Sales-led <$15K |
| LTV | (ARPA × GM%) / Churn | — |
| LTV:CAC | LTV / CAC | ≥ 3:1 |
| CAC Payback | CAC / (ARPA × GM%) | ≤ 18 mo |
| Marginal CAC | ΔSpend / ΔARR | ≤ 1.5× blended |
| SM Ratio | S&M / New ARR | < 0.7× for healthy |

## Pitfalls
- **Blended CAC concealment**: Organic + paid + channel mix can hide a dying channel.
- **Multi-touch attribution inflation**: Giving credit to late-stage clicks understates top-of-funnel channels.
- **Ignoring ramp time**: Sales-led CAC peaks in months 1–3 before converting; judge on 6-month rolling basis.
- **Seasonality**: Q4 budget flush distorts Q1 CAC; use trailing 4-quarter average.
- **ACV drift**: As ACV moves across motion bands, old motion economics become invalid—re-evaluate at each band crossing.

## Verification Step
Build a one-page "Channel Card" for each active channel showing:
1. Target ACV band
2. CAC, LTV:CAC, payback (current and 90-day trend)
3. Share of new ARR (current vs target)
4. Last reviewed date and next review trigger (e.g., CAC > target or share swings >5 pts)

If three or more channels are failing Gate 1, reduce channel count before adding more.
