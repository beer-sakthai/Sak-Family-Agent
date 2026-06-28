---
name: saas-customer-concentration-risk
description: Diagnose customer concentration risk in SaaS/subscription businesses, calculate HHI and top-customer exposure, interpret thresholds that affect valuation/fundraising, and build a mitigation playbook. Use when preparing for a raise or exit, diagnosing why blended CAC is rising, or when a single customer churn would materially move revenue.
triggers:
  - customer concentration analysis
  - HHI revenue concentration
  - whale customer risk
  - exit due diligence concentration
  - top customer share SaaS
  - customer base diversification
---

# SaaS Customer Concentration Risk

## Why this matters

Customer concentration converts a high-multiple SaaS revenue model into a risk-adjusted cash-flow analysis. At PE/strategic due diligence, a single customer above ~10% of ARR triggers a special-purpose equity risk discount; above ~20% and deal teams often require churn-and-fill guarantees or walk away entirely. The relationship between concentration and valuation multiple is non-linear: each 5-point jump in top-customer concentration compresses multiples disproportionately, because the business becomes a custom-integration shop rather than a scalable platform.

---

## Step 1: Calculate the metrics

### Top-Customer Share
```
Top-Customer Share (%) = (ARR from #1 Customer / Total ARR) × 100
```

### Top-3 / Top-5 Concentration
```
Top-3 Share (%) = (Sum of ARR from top 3 customers / Total ARR) × 100
Top-5 Share (%) = (Sum of ARR from top 5 customers / Total ARR) × 100
```

### Revenue HHI (Herfindahl-Hirschman Index mapped to customers)
Map each customer's ARR share to a 0–1 share, square each share, then sum. Divide by N (number of customers) to normalize, or use the squared-sum directly:
```
Revenue HHI = Σ (Share_i)²
```
- HHI = 1.0 → one customer owns everything (perfect concentration)
- HHI = 1/N → perfectly balanced base
- For practical SaaS use, cap N at major-account tier boundaries or use annual cohorts.

### Gross Revenue Retention (GRR) Contribution Risk
Note the absolute ARR at risk from the top-customer cohort. A \$2M ARR customer at $120k/year needs ~17 years to breakeven on acquisition; a churn event destroys \$120k+ expansion upside.

---

## Step 2: Read the thresholds

| Top-Customer Share | Risk Zone | Valuation / M&A Impact |
|---|---|---|
| < 3% | Low | No material disclosure required for most deals |
| 3% – 7% | Moderate | Secondary buyer asks for optional churn study; lenders watch closely |
| 7% – 12% | High | Primary buyer demands churn-and-fill clause or earn-out; multiple compression 15–30% below median SaaS comps |
| 12% – 20% | Critical | Most PE pass without structural protections; many VCs require remediation before next round |
| > 20% | Existential | Acquisition values shift to DCF / asset-based; SaaS multiples rarely apply |

Top-3 share above 25% is a near-universal red flag across debt, equity, and strategic M&A.

---

## Step 3: Diagnose root causes

Ask which of the four typical drivers created the concentration:
1. **Land-and-expand leakage**: you land whales but fail to expand into mid-market.
2. **Channel capture**: a reseller or VAR owns the end relationship and funnels only their lwc accounts.
3. **Vertical monoculture**: you won a flagship marquee in one vertical and stopped selling into others.
4. **Pricing/product mismatch**: your packaging bundles features that appeal only to large orgs, pricing out the segment that would diversify the base.

Map each top customer to a cohort (vertical, channel, ACV tier) to confirm the pattern.

---

## Step 4: Build the mitigation playbook

Rank by speed of impact:

**Quick (0–3 months)**
- Add a formal "whale watch" dashboard: weekly churn probability + support-ticket velocity for top-5 accounts.
- Renegotiate multi-year contracts to include annual expansion milestones; if missed, discount converts to on-demand pricing that deters lock-in concentration.
- Introduce a mid-market self-serve or product-led tier below the enterprise bottom to capture new logos at lower ACV.

**Medium (3–9 months)**
- Hire or reassign one SDR/AM exclusively to a vertical that is currently <10% of ARR.
- Build a referral/partnership channel explicitly to convert non-whale advocates into new accounts.
- Price the product to create a "Good / Better / Best" tier with clear value metrics that scale by seat/usage, so large accounts naturally plateau at a higher tier but don't absorb disproportionate support/engineering attention.

**Long (9–18 months)**
- Engineering roadmap: remove technical dependencies on single-account custom code (audit shadow IT built for whales).
- Fundraising narrative: when raising, pre-negotiate 2–3 LOIs from target mid-market verticals to show remediation in progress.
- M&A prep: before a sale, hire a third-party to model "post-exit churn" on top accounts to price into the diligence model—this removes the buyer's fear premium.

---

## Step 5: Verification

Pick the current calendar quarter. Run:
1. Pull ARR by customer (net of discounts).
2. Compute Top-Customer Share, Top-3, Top-5, and Revenue HHI.
3. Plot against the thresholds above.
4. State in one sentence whether the risk is Low / Moderate / High / Critical / Existential.
5. If threshold is Moderate or above, identify exactly one quick action and one medium action with owners and completion dates.

If the business has ≥50 customers and a top-customer share <5%, the concentration risk is generally manageable and can be reported as "within standard range" to board/investors.
