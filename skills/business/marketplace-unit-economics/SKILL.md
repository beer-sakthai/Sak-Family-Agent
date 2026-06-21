---
name: marketplace-unit-economics
title: Marketplace Unit Economics — Two-Sided Value & Liquidity Model
description: |
  Analyze marketplace and platform businesses using GMV, take rate, liquidity, and
  two-sided unit economics. Use when evaluating a marketplace startup, diagnosing
  why GMV is growing but revenue is not, sizing take-rate expansion, or benchmarking
  against Series A/peer metrics. Distinct from DTC e-commerce: here value is
  created by matching, not margin on goods.
triggers:
  - "marketplace unit economics"
  - - "take rate"
  - - "GMV"
  - - "liquidity metrics"
  - - "search to fill"
  - - "fill rate"
  - - "two-sided CAC"
  - - "platform unit economics"
  - - "seller acquisition cost"
  - - "buyer acquisition cost"
inputs:
  - Gross Merchandise Value (GMV) and Net Revenue by month
  - Take rate history and by vertical/segment
  - Buyer and seller counts, transactions, and AOV by side
  - Marketing spend by acquisition channel, split by buyer-side vs seller-side
  - Transaction volume: search-to-fill, fill rate, time-to-fill, repeat rates
  - Disintermediation signals (off-platform follow-on transaction rate)
  - Variable costs: payment processing, trust & safety, support
outputs:
  - Net Revenue / GMV bridge and take rate trends
  - Two-sided CAC and LTV by cohort
  - Liquidity health score and constraining-side diagnosis
  - Action list: raise take rate, fix liquidity, or shift acquisition spend
---

# Marketplace Unit Economics — Two-Sided Value & Liquidity Model

## Why this skill
Marketplaces fail for two reasons: dead liquidity (buyers find nothing, sellers find no buyers) and broken unit economics (you lose money on every transaction). This skill diagnoses both. Unlike DTC unit economics (SKU → contribution margin), marketplace economics starts with **GMV** and then layers take rate, matching efficiency, and two-sided acquisition costs.

## Core definitions

| Metric | Formula | What it reveals |
|--------|---------|-----------------|
| **GMV** | Σ (Transaction quantity × Transaction price) | Total value flowing through the platform |
| **Take Rate** | Net Revenue / GMV | Platform cut; stability and expansion potential |
| **Net Revenue** | GMV × Take Rate − Returns/Refunds − Discounts | Actual realized revenue |
| **Search-to-Fill** | Filled transactions / Buyer searches | Demand-side liquidity |
| **Fill Rate** | Filled transactions / Listed supply hours | Supply-side liquidity |
| **Time-to-Fill** | Avg hours from listing to transaction | Efficiency of matching |
| **Supplier Utilization** | Sold inventory-hours / Total listed inventory-hours | Seller economics |
| **Buyer-side CAC** | Buyer acquisition spend / New buyers | Demand-side efficiency |
| **Seller-side CAC** | Seller acquisition spend / New sellers | Supply-side efficiency |
| **Buyer LTV** | Gross profit per buyer over lifetime | Demand-side value |
| **Seller LTV** | Gross profit per seller over lifetime | Supply-side value |
| **Disintermediation Rate** | Off-platform follow-on transactions / Total transactions | Trust and lock-in health |

**Critical distinction:** A marketplace growing GMV 3× while take rate falls from 15% to 10% may be shrinking net revenue. Always model the **GMV → Net Revenue bridge**.

## Step-by-step workflow

### 1. Build the GMV-to-Net-Revenue bridge
For each month and by major segment (vertical, geography, business model):
- Start with GMV
- Subtract: refunds, disputes, chargebacks, promotional discounts funded by platform
- Multiply residual by effective take rate
- Result = Net Revenue

**Diagnostic:** If GMV is up 20% but Net Revenue is flat, check whether take rate compression (volume discounts, fee waivers, mix shift to low-rate categories) is offsetting growth.

### 2. Measure and benchmark liquidity
Compute for both buyer and seller sides:

**Demand side:**
- **Search-to-Fill Rate** = Completed transactions / Total search sessions
- **Buyer repeat rate** = Buyers with ≥2 transactions / Total buyers

**Supply side:**
- **Fill Rate** = Transactions / Unique active listings (per day or per week)
- **Supplier Utilization** = Filled slots / Total listed slots
- **Seller repeat rate** = Sellers with ≥2 transactions / Total sellers

**Benchmarks (seed / Series A depending on vertical):**
- Two-sided marketplaces: search-to-fill > 25% indicates healthy demand-side liquidity
- B2B marketplaces: liquidity score > 60% (blended demand + supply signals)
- Home services / local: fill rates > 15–20%
- E-commerce platforms (Amazon/eBay model): supplier utilization > 20%

**Diagnostic:** If one side is strong but the other is weak, the marketplace is half-broken. Buyers leave when they find nothing; sellers leave when they make nothing.

### 3. Two-sided unit economics
Compute unit economics **by side**, not blended.

**Unit economics structure:**

```
Buyer Unit:
  Buyer Revenue = ∑ (Transactions × Take Rate on that transaction)
  Buyer CAC = Buyer acquisition spend ÷ New buyers
  Buyer Gross Profit = Buyer Revenue − Variable costs (payment fees, support)
  Buyer LTV:CAC = Target > 3:1 for durable platforms

Seller Unit:
  Seller Revenue = ∑ (Transactions × Take Rate)
  Seller CAC = Seller acquisition spend ÷ New sellers
  Seller Gross Profit = Seller Revenue − Variable seller costs (disputes, fraud)
  Seller LTV:CAC = Seller-side efficiency
```

**Constraint model:**
The marketplace’s growth rate is constrained by the **slower side** of the network effect. If seller CAC is 3× buyer CAC and seller repeat rate is low, adding more buyers wastes money.

**Action:** Allocate acquisition spend so that marginal LTV:CAC is equalized across sides. If buyer LTV:CAC = 5:1 and seller LTV:CAC = 1.5:1, shift budget to seller acquisition until the marginal return equalizes.

### 4. Diagnose disintermediation risk
Track attempts or signals of off-platform behavior:
- Direct messages exchanged on platform
- Post-transaction reviews mentioning "contacted directly"
- Duplicate payment requests or invoice divergence

**Disintermediation tolerance:** Generally <10–15% of follow-on transactions. Above that, platform value is questionable.

### 5. Model take-rate expansion scenarios
Take rate is rarely static. Build scenarios:

- **Status quo:** current blended take rate
- **Value capture:** move transactions from flat-fee to percentage, introduce premium placement, checkout add-ons
- **Risk:** raising take rate → seller churn or disintermediation → GMV loss

**Formula for take-rate sensitivity:**
```
ΔNet Revenue = (GMV_new × TR_new) − (GMV_new × Churn_seller% × TR_elasticity) − (GMV_old × TR_old)
```
Keep a watch list of high-volume sellers who drive disproportionate GMV; losing them costs more than headline churn % suggests.

### 6. Verify with the “Liquidity-Unit-Economic” dashboard
Build a simple monthly view:

| Driver | This Month | Last Month | Change |
|--------|-----------|-----------|--------|
| GMV | | | |
| Take Rate | | | |
| Net Revenue | | | |
| Search-to-Fill | | | |
| Fill Rate | | | |
| Buyer CAC | | | |
| Seller CAC | | | |
| Buyer LTV:CAC | | | |
| Seller LTV:CAC | | | |
| Disintermediation Rate | | | |

## Formulas cheat sheet

**Take Rate by segment:**
```
Take Rate = Net Revenue from segment / GMV from segment
Blended Take Rate = Total Net Revenue / Total GMV
```

**GMV per buyer / seller:**
```
GMV per Buyer = Total GMV / Total active buyers
GMV per Seller = Total GMV / Total active sellers
```

**Contribution to Variable Costs:**
```
Platform Gross Profit = Net Revenue − (Payment processing + Trust & Safety + Variable support)
Platform Gross Margin % = Platform Gross Profit / Net Revenue
```

**Liquidity score (simplified blended):**
```
Liquidity Score = 0.5 × (Search-to-Fill %) + 0.3 × (Fill Rate %) + 0.2 × (Seller Utilization %)
(Weight by your vertical’s constraint)
```

**Take-rate expansion breakeven:**
```
New Take Rate needed = (Fixed Cost + Target Profit) / (GMV × (1 − Expected seller churn %))
```

## Pitfalls

1. **Optimizing GMV instead of Net Revenue.** GMV is vanity; Net Revenue is sanity. A 30% GMV boost with a 5pp take-rate drop can leave you with less revenue and higher support costs.
2. **Ignoring single-sided CAC.** Many marketplaces only track buyer-side metrics. Seller-side unit economics often look worse and constrain growth.
3. **Blending two-sided LTV.** Buyer LTV (repeat purchases) and seller LTV (repeat listings) have very different dynamics and cost structures.
4. **Discounting churn elasticity on take-rate hikes.** A 1pp take-rate increase may cause 2–4pp seller churn in elastic segments; model it.
5. **Treating all GMV equally.** A GMV dollar from sellers paying 20% take rate is worth more than one paying 5%.
6. **Ignoring mix shift.** Growth in low-rate categories (e.g., commoditized goods) drags blended take rate down even if stated fees are unchanged.
7. **Liquidity theater.** High searches + low fill rate = frustrated buyers. High listings + zero views = frustrated sellers. Both churn.
8. **No disintermediation tracking.** If you don’t measure it, you can’t defend your take rate.

## Verification step

**The “Side-Constraint Test”:**
Ask: which side of the marketplace is the binding constraint to GMV growth?
- If **demand-constrained** (fill rate high, search-to-fill low), your growth dollars belong on buyer acquisition and onboarding.
- If **supply-constrained** (search-to-fill high, fill rate low), your growth dollars belong on seller acquisition and activation.
- If **neither is constrained** (both strong), growth requires **take-rate expansion** or **new verticals / geographies**, not more spend.

**The “Take-Rate Pit” Test:**
If blended take rate has fallen >2pp over the last 6 months while GMV grew >20%, and gross profit dollars are flat or declining, you have a **growth-equals-profit-leakage** problem. Do not celebrate GMV headlines.

**The “Liquidity Health Check” (monthly):**
Run the six liquidity metrics above. If any critical-side metric is in the bottom quartile of your peer segment (from the benchmarks table), flag a 90-day liquidity improvement plan before scaling acquisition.

## Integration with other skills
- Pair with **ecommerce-unit-economics** when your marketplace adds a 1P (inventory) store; channel-level CM3 analysis applies to owned inventory, not GMV.
- Use **saas-pricing-architecture** for take-rate tiering and value-based pricing negotiations with high-volume sellers.
- Combine with **revops-sales-velocity-and-pipeline-coverage** if your marketplace charges enterprise contracts or commit-based subscription fees on top of transaction take rates.
- Use **market-sizing-frameworks** to estimate addressable GMV for new vertical launches.
