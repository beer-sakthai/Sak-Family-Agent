---
name: SakKing-van-westendorp-price-research
description: >
  Design, run, and interpret a Van Westendorp Price Sensitivity Meter (PSM)
  to identify an acceptable price range and optimal price point before launching
  or repricing a SaaS product, feature module, or additive. Use when setting
  initial price for a new tier, validating WTP for a premium feature, entering
  a new segment, or diagnosing why an existing price isn't converting.
tags:
  - pricing
  - saas
  - market-research
  - monetization
  - pricing-research
---

# Van Westendorp Price Sensitivity Meter — Operational Skill

## When to Use This Skill

- Setting the initial price for a brand-new product, feature module, or tier
- Repricing an existing offer after a major packaging or value-metric change
- Entering a new market segment where price expectations may differ (e.g., SMB vs. enterprise)
- Diagnosing whether a low-conversion tier is suffering from a price-perception problem
- Calibrating an A/B test hypothesis before running a pricing experiment (link to `saas-pricing-experiment-design`)

---

## Core Concept

The Van Westendorp Price Sensitivity Meter (PSM) is a **survey-based research method** that isolates price as the variable and measures customer willingness-to-pay (WTP) through four simple questions.

It produces four key price points by plotting cumulative response curves:

| Price Point | What It Means | How It's Derived |
|-------------|---------------|------------------|
| **PMC** — Point of Marginal Cheapness | Price below which the product is seen as a bargain; above this, value starts to erode | Intersection of *Too Cheap* and *Cheap* curves |
| **PME** — Point of Marginal Expensiveness | Price above which the product is seen as expensive; below this, price friction starts to appear | Intersection of *Too Expensive* and *Expensive* curves |
| **OPP** — Optimal Price Point | The “sweet spot” where the market is happiest with the price/value balance | Intersection of *Too Cheap* and *Too Expensive* curves |
| **IPP** — Indifference Price Point | The price where equal numbers of customers find the product cheap vs. expensive | Intersection of *Cheap* and *Expensive* curves |

The **Acceptable Price Range (APR)** = between PMC and PME.

---

## Step 1 — Scope the Study

### Define the concept you are pricing
- Write a one-paragraph product description specific enough that respondents understand exactly what they are pricing.
- If testing a tier upgrade, specify the included features, limits, and target use case.
- If testing a new segment, name it explicitly (e.g., “mid-market manufacturing companies 200–1,000 employees”).

### Choose the respondent pool
- **Target actual buyers or power users** in the segment, not random consumers.
- If the segment is hard to reach, use existing customers for the research phase but weight results against new-market expectations.
- **Minimum sample per segment:** 200–400 for stable curves. N≈100 works directionally but with wide confidence bands. N<50 is unreliable.

---

## Step 2 — Write the Four Questions

Use a survey tool (Typeform, Google Forms, Qualtrics). The four questions must appear in this exact order to minimize anchoring:

1. **Too Cheap:** “At what price would you begin to doubt the quality of this product?”  
2. **Cheap:** “At what price would you consider this product a bargain (excellent value for the money)?”  
3. **Expensive:** “At what price would you consider this product expensive, but still worth considering?”  
4. **Too Expensive:** “At what price would you consider this product too expensive to purchase?”

### Question rules
- Ask for a **single numerical price**, not a range.
- Specify currency and whether the price is per user / per month / per year / flat fee.
- Include a “would not purchase at any price” note, but exclude those respondents from curve plotting (they are useful for churn risk insight only).
- Do **not** show competitor prices in the survey.

---

## Step 3 — Administer the Survey

### Recruitment channels
| Channel | Quality | Speed | Cost |
|---------|---------|-------|------|
| Warm existing customers | High signal | Fast | Low |
| Customer prospects in pipeline | High signal | Medium | Low |
| Panel vendor (e.g., Respondi, Cint) | Medium signal | Fast | Medium-High |
| LinkedIn / social paid ads | Low-to-medium signal | Slow | Variable |

### Fielding tips
- Offer a small incentive ($10–$25 gift card, entry into a raffle) to improve completion rates without distorting WTP.
- Screen for role and company size up front.
- Field for 7–14 days; survey fatigue in B2B panels is real after two weeks.

---

## Step 4 — Clean and Prepare the Data

1. Remove incomplete responses.
2. Remove respondents who answered “would not purchase at any price.”
3. Inspect for **straight-lining** (identical answers across all four questions — these are noise).
4. Winsorize top/bottom 1% outliers unless they are genuine enterprise-negotiated outliers.
5. Segment by buyer persona if sample size permits (e.g., Title, Company Size).

---

## Step 5 — Plot the Curves and Calculate Price Points

### Plotting
For each price point on the x-axis, plot the cumulative percentage of respondents who find the price at or below the stated threshold.

- **Too Cheap curve** = % who said price ≤ “too cheap”  
- **Cheap curve** = % who said price ≤ “cheap”  
- **Expensive curve** = % who said price ≤ “expensive”  
- **Too Expensive curve** = % who said price ≤ “too expensive”

### Finding the intersections
Use linear interpolation between the two closest recorded price points to the intersection.

| Price Point | Formula / Logic |
|-------------|-----------------|
| PMC | Intersection of Too Cheap and Cheap curves. Below this, quality is doubted; above it, the price looks like a bargain. |
| PME | Intersection of Too Expensive and Expensive curves. Above this, price is a barrier; below it, price is not a friction point. |
| OPP | Intersection of Too Cheap and Too Expensive curves. The market is most comfortable here. |
| IPP | Intersection of Cheap and Expensive curves. Neutral price perception. |

### Acceptable Price Range (APR)
```text
APR = PMC to PME
```
OPP should sit inside the APR. If OPP is outside, the curves are unstable and the study is likely underpowered or the concept is poorly defined.

---

## Step 6 — Interpret and Decide

### Interpreting the spread

| Spread Size | Interpretation | Typical Action |
|-------------|----------------|----------------|
| **Wide APR (OPP is ~2× lower bound)** | Market sees value but price sensitivity is scattered | Pick a tiered structure (Good/Better/Best) to capture spread; test the upper band via A/B |
| **Tight APR (PME < 1.3× PMC)** | Market has strong, narrow WTP | Price confidently at OPP; limited room for tiering; watch for value communication issues |
| **OPP >> current price** | Strong latent value — possible undervaluation | Test a price increase via `saas-pricing-experiment-design` |
| **OPP << current price** | Price is materially above WTP; conversion will suffer | Repackage or re-price before widening GTM spend |

### Segment-level checks
- If Enterprise OPP is 2× SMB OPP, you likely need **tiered packaging** or usage-based thresholds.
- If an internal segment (e.g., customers in EMEA) has a systematically lower OPP, investigate purchasing power parity or taxation expectations.

---

## Step 7 — Benchmark and Validate

### Internal benchmarks to check
- Current gross margin: ensure OPP allows for ≥75% gross margin after COGS (cloud, support, AI inference, third-party APIs).
- Current CAC payback: if OPP implies a much lower ACV, verify that LTV:CAC still works at that ARPU level.
- Blended historical pricing: if OPP is dramatically different from what the market has paid, expect a transition period.

### External benchmarks (post-2025)
- SaaS median gross margin ≈ 77% (with AI/API-heavy products trending lower before optimization).
- Annual contract with upfront payment typically commands 15–25% premium over monthly.
- Feature add-ons can be priced at 10–30% of base ACV if they are non-essential.

---

## Pitfalls

| Pitfall | Why It Happens | Fix |
|---------|----------------|-----|
| **Hypothetical bias** | Respondents state higher WTP than they actually spend when asked abstractly | Always context-rich product descriptions; follow up with “would you buy at OPP?” yes/no question and map to past purchase behavior |
| **Small N** | Curves are jagged and intersections shift wildly | Minimum 200 per key segment; if you must release with N<100, treat OPP as directional only |
| **Anchoring on current price** | If current price is in the survey or known, respondents anchor around it | Do not reveal your current pricing; use a new product name / codename |
| **Forgetting customer success / implementation cost** | OPP looks great but service delivery erodes margin | Add a “cost to deliver” column and subtract from OPP to get net margin |
| **Ignoring segment splits** | Blended OPP masks a high-WTP beta segment and a low-WTP mass segment | Analyze curves by segment; if segments are >20% of your target mix, size them separately |
| **Treating OPP as the only valid price** | OPP is a minimum-demand point, not a revenue-maximization point | Consider IPP (indifference) and PME (marginal expensiveness) as upper bounds for psychological pricing |

---

## Verification Checklist

Before using the output to set or repricing, confirm:

- [ ] Product concept description was reviewed by a non-participant for clarity
- [ ] At least 200 respondents reached per key segment (or n≥50 if directional only)
- [ ] Four questions asked in the exact Too Cheap → Cheap → Expensive → Too Expensive order
- [ ] Outliers and straight-liners removed; denominator documented
- [ ] Cumulative curves plotted and intersections interpolated (not eyeballed)
- [ ] OPP falls between PMC and PME (if not, the study is unstable)
- [ ] OPP checked against unit economics: gross margin, CAC payback, and LTV:CAC at the implied ARPU
- [ ] Results segmented by at least one material cut (e.g., title, company size, geography)
- [ ] A follow-up “would you buy at OPP?” validation question yielded ≥50% yes rate

---

## What This Skill Does NOT Cover

- Designing the tier architecture itself (see `saas-pricing-architecture`)
- Testing price changes statistically in production (see `saas-pricing-experiment-design`)
- Usage-based metering and per-unit cost modeling (see `usage-based-pricing-bill-shock-prevention`)
- Revenue recognition (ASC 606) implications of changing invoice terms
- Platform-specific survey distribution outside standard panel tools

---

## Related Skills

- `saas-pricing-architecture` — tier design, psychological levers, and value-metric selection (design before researching)
- `saas-pricing-experiment-design` — A/B testing price changes in production (test after researching)
- `saas-cac-payback-optimization` — validates whether the derived ARPU supports efficient growth
- `saas-growth-efficiency` — links pricing research outcomes to Magic Number, Burn Multiple, and Rule of 40
