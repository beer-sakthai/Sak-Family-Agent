---
name: ecommerce-unit-economics
title: E-Commerce Unit Economics — Tiered Contribution Margin Ladder
description: |
  Analyze DTC/e-commerce unit economics using the CM1/CM2/CM3 contribution margin ladder,
  sliced by SKU, channel, and customer cohort. Use when pricing products, evaluating marketing
  ROI, deciding whether to scale a channel, or diagnosing profitability leaks.
triggers:
  - "ecommerce unit economics"
  - "contribution margin"
  - "CM1 CM2 CM3"
  - "SKU profitability"
  - "DTC profitability"
  - "channel-level ROAS"
  - "customer cohort LTV"
inputs:
  - Order-level or SKU-level revenue, COGS, fulfillment, shipping, payment fees, returns, discounts
  - Channel-level marketing spend (paid social, search, affiliates)
  - Customer acquisition cost by cohort/channel
  - Fixed overhead pool (for coverage check)
outputs:
  - CM1/CM2/CM3 per SKU, per channel, per cohort
  - LTV:CAC ratio, payback period
  - Channel-level blended ROAS adjustment
  - Action list: scale, fix, or kill
---

# E-Commerce Unit Economics — Tiered Contribution Margin Ladder

## Why this skill
Gross margin alone hides the truth. A product can look “gross margin positive” while losing money on fulfillment, returns, or customer acquisition. The tiered ladder (CM1 → CM2 → CM3) isolates each cost layer so you can see exactly where value leaks — and fix the right lever.

## Core definitions

| Layer | Formula | What it reveals |
|-------|---------|-----------------|
| **CM1** | Revenue − COGS − Discounts − Payment Fees | Core product profitability (is the SKU a good make?) |
| **CM2** | CM1 − Fulfillment (picking/pack) − Outbound Shipping − Returns Reserve | Operational efficiency (can we fulfill it cheaply?) |
| **CM3** | CM2 − Variable Marketing (CAC) − Customer-level Promos | Growth economics (can we profitably acquire the customer?) |

**CM3 on a per-order basis × Order frequency ≈ contribution to fixed costs and profit.**

## Step-by-step workflow

### 1. Build the data foundation
Collect the last 90 days (or 2× your average payback period) of:
- Orders with SKU, quantity, revenue, discount, payment method/fee rate
- COGS by SKU (landed cost + duties)
- Fulfillment cost per order (warehouse/labor/3PL)
- Outbound shipping cost by order (carrier invoice or blended rate)
- Return rate by SKU and reason; reserve = return_rate × (shipping + handling + restocking)
- Marketing spend by channel and campaign; attribute to first-touch or last-click consistently
- Fixed overhead (rent, salaries, tech) for coverage check

### 2. Compute CM1/CM2/CM3
Map each cost to the hierarchy above in a spreadsheet or BI tool. Derive:

```
CM1% = CM1 / Revenue
CM2% = CM2 / Revenue
CM3% = CM3 / Revenue
```

Target thresholds (adjust for your model):
- CM1% ≥ 40–60% (depends on category)
- CM2% ≥ 25–40%
- CM3% ≥ 15–25%

If CM3 < 15%, you are only covering variable costs. Negative CM3 means you are losing money on every acquisition.

### 3. Slice by SKU
Flag SKUs with:
- CM1% in bottom third → renegotiate COGS or delist
- CM2% in bottom third → renegotiate 3PL, change packaging, or raise shipping threshold
- CM3% in bottom third → reduce paid spend or optimize creative

**Hierarchy of lethal combinations:**
- CM1 negative: kill or redesign the product
- CM1 positive but CM2 negative: fulfillment/shipping problem
- CM1+CM2 positive but CM3 negative: overpaying for acquisition

### 4. Slice by Marketing Channel
For each channel (TikTok, Meta, Google, Email, Affiliates):

```
Channel Adjusted ROAS =
  (Channel Revenue × Average Channel CM3%) / Channel Spend
```

A unified 3.0+ ROAS with negative CM3% is a trap — revenue without profit.

**Channel benchmarks (high variance by vertical):**
- Performance social (TikTok/Meta): CM3% often lower; scale only if >15%
- Search (Google): higher CM3% because intent is stronger; target >25%
- Email/Organic: treat as incremental; maintaining CM3% here funds paid growth

### 5. Slice by Customer Cohort
Group customers by acquisition channel and month. Track:
- **CAC paid in that cohort** (spend ÷ new customers)
- **Cohort LTV** = average CM3 per order × expected orders over lifetime
- **Cohort LTV:CAC** = target 3:1 minimum
- **CAC Payback Period** = CAC ÷ (CM3 per order × Orders per month)

If payback > 90 days, you need either higher CM3%, more frequency, or cheaper acquisition.

### 6. Prioritize Actions
Use a 2×2 matrix:

| | High CM3% | Low CM3% |
|---|---|---|
| **High Volume** | Scale | Fix unit economics before scaling |
| **Low Volume** | Protect / reinvest | Kill or restructure |

## Formulas cheat sheet

**Returns Reserve:**
```
Return Reserve % = (Returns $ / Net Sales $) for SKU or Channel
Dollar Reserve = Return Reserve % × (Avg Shipping + Avg Handling per return)
```

**Contribution to Fixed Costs (monthly):**
```
Contribution Pool = Σ (Units_sold × CM3 per unit)
Fixed Cost Coverage = Contribution Pool / Fixed Costs
Target: >1.0 within 12–18 months
```

**Channel Profitability (%):**
```
Channel CM3% = (Channel Revenue − Channel COGS − Fulfill − Ship − Returns − Channel CAC) / Channel Revenue
```

**Blended CAC:**
```
Blended CAC = Total Variable Marketing / Total New Customers
```

**Net Revenue Retention proxy (e-com):**
```
Repeat Purchase Rate = Customers with 2+ orders / Total customers
AOV Growth = Repeat AOV / First AOV
```

## Pitfalls

1. **Ignoring the right cost bucket.** Putting CAC in CM2 instead of CM3 masks growth losses.
2. **Averaging costs across heterogeneous SKUs.** A 50-SKU catalog should have 50 CM1 numbers, not one blended gross margin.
3. **Using blended ROAS only.** Channel-level CM3% is the truth; blended ROAS is the lie.
4. **Forgetting returns.** Use actual return rates, not “industry average.” A return-reserve understatement of 5 pp can flip CM2 to negative.
5. **Not cohorting customer economics.** Brand loyalty and repeat behavior differ by channel; averaging hides the worst acquisition channels.
6. **Ignoring payment-fee variances.** Card-not-present fees differ by payment method and processor; net them into CM1.
7. **Scaling on CM1 positivity.** CM1 positive but CM3 negative is a growth scam — you’re acquiring users you cannot profitably serve.

## Verification step

**The “Kill Test”:**
For any SKU + channel combination, compute CM3$. If CM3 < 0 for three consecutive months and no structural fix is planned, exit. If CM3 > 0 but below your threshold, require a written 90-day improvement roadmap.

**The “Fixed-Cost Coverage Test”:**
Compute Contribution Pool / Fixed Costs for the full catalog. If coverage < 0.6 and you have >12 months of runway data, you have a structural profitability problem — raise prices, cut unprofitable SKUs, or reduce CAC.

**The “Channel Truth Test”** (monthly):
Pick one channel. Take last 30 days of attributed revenue. Compute Channel CM3%. Compare to channel-reported ROAS. If ROAS implies profit but Channel CM3% says otherwise, your attribution model is wrong — fix the data first.

## Integration with other skills
- Use **ccc-operational-levers** to fix high DIO/DSO/DPO that depress cash despite positive CM3.
- Combine with **saas-retention-metrics** only when you add a subscription or membership layer.
- Use **b2b-pipeline-math-mql-to-close** if the same SKU set is sold through B2B wholesale.
