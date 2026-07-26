---
name: SakKing-saas-expansion-revenue-decomposition
title: SaaS Expansion Revenue Decomposition & Diagnostic
description: Diagnose what is *actually* driving NRR and GRR by breaking expansion revenue into seat growth, tier upgrades, usage overages, price increases, and new-product cross-sell. Use this when expansion looks healthy but growth is still inefficient, when you need to design product/pricing roadmaps, or when board/investors ask "where is NRR coming from?"
---

## Trigger
- Board/investor asks "what is driving our NRR?" and the answer "expansion" is too vague
- NRR is above benchmark but profitability/efficiency is poor
- Product or pricing team needs to prioritize which expansion vector to invest in
- Sales/CS team is hitting expansion targets but net retention is flat or declining
- You suspect expansion is masking underlying churn or pricing problems

## Step-by-Step Workflow

1. **Define the cohort and period** — Use a fixed cohort (e.g., MRR at start of Q). Avoid mixing new and old book business.
2. **Calculate GRR and NRR** (from existing `saas-retention-metrics` skill). Record base GRR and NRR.
3. **Build the Expansion Waterfall** — For the cohort, categorize every dollar of new MRR into one of five buckets:
   - Seat Growth: More users/licenses at the same tier/plan
   - Tier Upgrade: Same seats moving to a higher-priced tier/plan
   - Usage Overages: Additional spend driven by consumption above contract minimums
   - Price Increase: Existing plan price goes up (not due to seat or tier change)
   - New Product Cross-Sell: First-time purchase of a different product/module from the same company
4. **Calculate decomposition ratios** — Each bucket as % of starting MRR and % of total expansion.
5. **Diagnose the health mix** — Compare your bucket mix to healthy benchmarks and flag risks.
6. **Map to operational levers** — For each bucket, note whether to double down, optimize, or investigate.

## Formulas

### Base Metrics
- `GRR = (Start MRR - Churned MRR - Contraction MRR) / Start MRR`
- `NRR = GRR + (Expansion MRR / Start MRR)`

### Expansion Waterfall
```
Start MRR
- Churned MRR
- Contraction MRR
+ Seat Growth MRR
+ Tier Upgrade MRR
+ Usage Overage MRR
+ Price Increase MRR
+ New Product Cross-Sell MRR
= End MRR
```

Check: `Expansion MRR = Seat Growth + Tier Upgrade + Usage Overage + Price Increase + New Product Cross-Sell`

### Decomposition Ratios
- `Seat Growth / Start MRR`
- `Tier Upgrade / Start MRR`
- `Usage Overage / Start MRR`
- `Price Increase / Start MRR`
- `New Product / Start MRR`

### Expansion Mix
- `Seat Growth % of Expansion = Seat Growth / Expansion MRR`
- (Repeat for each bucket)

## Benchmarks & Diagnostic Signals

| Expansion Source | Healthy Range (% of total expansion) | Diagnostic Signal |
|---|---|---|
| Seat Growth | 25–45% | High seat growth can signal strong adoption but also poor self-serve optimization or lack of tiering. |
| Tier Upgrade | 20–35% | Healthy tier upgrades indicate good packaging and value communication. Very low (<10%) = packaging is wrong or CS isn't executing. |
| Usage Overages | 10–25% | Reasonable overages show product stickiness. Above 40% = pricing tiers are misaligned (too low minimums) or usage isn't forecasted. |
| Price Increase | 0–15% | Any price increase on existing contracts is pricing power. Above 20% = you may be losing price-sensitive customers who don't churn immediately but delay renewal. |
| New Product Cross-Sell | 10–20% | Strong indicator of platform strategy. Above 25% in early growth = you may be over-investing in product breadth before core retention is solid. |

**Warning patterns:**
- >60% of expansion from seat growth alone → product-led tiers are weak; customers buy horizontally instead of vertically.
- >40% from usage overages → pricing tiers don't capture value; consider raising minimums.
- 0% from price increases → you've never raised prices; lost pricing power.
- >50% from new product cross-sell → core product retention may be weak; expansion is propping up NRR artificially.

## Operational Levers by Source

| Source | When to Double Down | When to Optimize/Fix |
|---|---|---|
| **Seat Growth** | Seats are added within 30 days of purchase; high virality/net promoter score | Seats added slowly (>90 days); customers buying more seats to justify sunk cost |
| **Tier Upgrade** | Upgrade path is clear (1-click, auto-prompts) and win-rate >20% | Upgrade requires manual approval, long sales cycles, or >60% of customers stay on entry tier |
| **Usage Overages** | Customers regularly exceed minimums and don't complain | Overages are surprise invoices causing pushback, or 80%+ of revenue is overage (unpredictable) |
| **Price Increase** | Increases are paired with added value (features, support) | Increases are pure price hikes with no value add; renewal rates drop |
| **New Product Cross-Sell** | Cross-sell is automated via usage triggers; same customer has 2+ products | Cross-sell requires heavy touch; same customer has product but low adoption |

## Worked Example

A company with $100K starting MRR cohort has:
- Churned: $5K
- Contraction: $3K
- Expansion: $22K (Seat: $10K, Tier: $5K, Overages: $4K, Price Increase: $1K, New Product: $2K)

Calculations:
- GRR = (100 - 5 - 3) / 100 = 92%
- NRR = (92 + 22) / 100 = 114%
- Seat Growth % of expansion = 10/22 = 45.5% (above healthy 25-45%; flag)
- Tier Upgrade = 22.7% (healthy)
- Usage Overage = 18.2% (healthy)

Diagnosis: NRR is 114%, which looks good. But seat growth is 45.5% of expansion, suggesting weak tiering and packaging. Action: audit entry-tier limits, add upgrade prompts, and test a decoy tier.

## Pitfalls

- **Attribution ambiguity**: A single expansion event (e.g., adding 5 seats AND moving up a tier) should be split between Seat Growth and Tier Upgrade based on the price differential. Don't double-count.
- **Cohort timing**: Expansion must be from the *same cohort* (starting customers), not new logos. Adding new logos inflates NRR incorrectly.
- **Multi-year contracts**: Expansion inside a multi-year contract is still expansion; recognize it in the period it occurs, not deferred to end of term.
- **M&A or lump-sum deals**: Exclude these from decomposition unless they are true organic expansion from the same customer.
- **Confusing GRR with NRR**: GRR is the health check for core product retention. If GRR is <85%, NRR is misleading regardless of expansion volume.

## Verification Step

Reconcile the waterfall to the billing system cohort report:

```
Start Cohort MRR                = $M
+ Seat Growth                   = $S
+ Tier Upgrade                  = $T
+ Usage Overage                 = $U
+ Price Increase                = $P
+ New Product Cross-Sell        = $X
- Churned MRR                   = $C
- Contraction MRR               = $D
= Ending Cohort MRR (from billing system)

Check:
(M + S + T + U + P + X - C - D) must equal Ending Cohort MRR exactly.
If not, expansion categories are misclassified or missing.
```
