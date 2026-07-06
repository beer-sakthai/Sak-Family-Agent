---
name: SakKing-market-sizing-frameworks
title: Market Sizing Frameworks
description: Size markets rigorously using Bottom-Up, Top-Down, and Value Theory methods, then triangulate to get a defensible TAM/SAM/SOM. Use this when building pitch decks, planning GTM launch geography, evaluating M&A targets, or answering "how big is this opportunity?"
tags: [strategy, fundraising, gtm, forecasting, tamsamsom]
---

# Market Sizing Frameworks

## When to use

Use this skill whenever you need a defensible, investor-grade market size: fundraising pitches, board strategy sessions, GTM market prioritization, M&A target screening, or business case validation.

**Never** use a single method alone. The job is to triangulate.

---

## Step-by-step workflow

### 1. Define the three segments clearly (TAM / SAM / SOM)

| Segment | Definition | Typical use |
|---------|-----------|-------------|
| **TAM** (Total Addressable Market) | All potential revenue if 100% market share were achieved across the entire relevant universe, using your product/service. | Sets the vision. |
| **SAM** (Serviceable Addressable Market) | The portion of TAM you can realistically reach given your current business model, geography, distribution, and pricing. | Proves relevance. |
| **SOM** (Serviceable Obtainable Market) | The share of SAM you can capture in 3–5 years given execution constraints, competition, and channel capacity. | Drives near-term financial plan. |

**Rule of thumb for sizing depth:**  
- TAM can be aggressive / visionary.  
- SAM must be grounded in real filters (regions you ship to, verticals you serve, price points you charge).  
- SOM is a sales-plan output, not a Hail Mary — base it on historical win rates in similar segments.

### 2. Apply the three methods in parallel

#### Method A — Bottom-Up (Most Reliable)

Build the market from your unit economics outward.

**Formula variants:**
```
TAM = (# of target customers) × (average annual revenue per customer)
SAM = (# of reachable target customers within your model/geo) × (ARPU)
SOM = (# of customers you can realistically acquire in 3–5 years) × (ARPU)
```

**Data sources:**
- Internal CRM or pipeline data for actual win rates and deal sizes.
- Public company filings for comparable ARPU / market share.
- Industry reports for total number of target customers (e.g., US Bureau of Labor Statistics for business counts, government census data, trade association reports).
- LinkedIn Sales Navigator / Apollo / ZoomInfo for account-level counts.

**Example (B2B SaaS, vertical SaaS for restaurants):**
- Total restaurants in target markets: 500,000
- Average annual contract: $1,200
- **TAM** = 500,000 × $1,200 = $600M
- Restaurants with 10+ locations (your sweet spot): 40,000
- **SAM** = 40,000 × $1,200 = $48M
- Realistic 5-year capture at 8% market share in SAM: 3,200 customers
- **SOM** = 3,200 × $1,200 = $3.84M ARR

#### Method B — Top-Down (For Validation)

Start with macro market data and filter down to your niche.

**Formula variants:**
```
TAM = (Total vertical market revenue) × (relevant % your product category represents)
SAM = TAM × (geo filter) × (business-model filter) × (price-access filter)
SOM = SAM × (realistic competitor-adjusted share)
```

**Data sources:**
- Gartner, IDC, Forrester, Statista, IBISWorld.
- Government statistics (Census, BLS, Eurostat).
- Trade association annual reports.

**Example:**
- Global restaurant POS software market: $4.2B (IDC)
- Your category (cloud-native vertical SaaS for full-service chains): ~15% of total POS spend.
- **TAM** = $4.2B × 15% = $630M
- North America only: 35% of global TAM → $220.5M
- Your price tier captures 20% of NA spendable budget → **SAM** = $44.1M
- Realistic 5-year share after competitor adjustment: 8% → **SOM** = $3.5M (consistent with Bottom-Up)

#### Method C — Value Theory (Sometimes Called "Willingness to Pay")

Size the market by the value you create for customers, then estimate penetration.

**Formula:**
```
TAM = (# of target customers) × (value captured per customer) × (willingness-to-pay %)
```

**Data sources:**
- Customer interviews / conjoint analysis.
- Proxy pricing of functionally equivalent alternatives (e.g., labor cost saved, compliance fine avoided, revenue uplift generated).
- Case studies with quantified ROI.

**Example:**
- Target: 500,000 restaurants.
- Your product saves $200/month in labor / waste per restaurant.
- Willingness to pay is typically 10–30% of value captured; use 20% ($40/month or $480/year).
- **TAM** = 500,000 × $480 ≈ $240M (useful sanity check; typically smaller than other methods).

### 3. Triangulate and reconcile

```
Triangulation sanity check:
- Bottom-Up vs Top-Down should agree within 2–3×.
- If they diverge by more than 3×, investigate:
  • Are you counting the same customer universe?
  • Are ARPU and market revenue defined consistently (ACV vs. annual product revenue)?
  • Did you accidentally include/exclude a geography or vertical?
- Value Theory usually produces a lower, "willingness-to-pay–capped" ceiling. If it's wildly higher, your value assumptions are probably wrong.
```

**Reconciliation approach:**
1. Reconcile TAM first. If methods span, e.g., $240M (Value) to $630M (Top-Down), use the weighted mid-range but disclose the range.
2. SAM and SOM should track from the reconciled TAM through the same filters.
3. State the method bias: "Bottom-Up tends to undercount emerging use-cases; Top-Down can overcount if the bundled market includes legacy solutions."

---

## Formulas cheat sheet

| Method | Best for | Typical sources | Key assumption |
|--------|---------|----------------|----------------|
| Bottom-Up | Operational / sales planning | CRM, account lists, unit economics | Count of target customers is accurate |
| Top-Down | Investor narrative, category validation | IDC, Gartner, gov stats | Macro segment definitions map to your product |
| Value Theory | Pricing power, max willingness to pay | Customer ROI data, conjoint | Customers capture and pay for the full value |

---

## Pitfalls

- **Double-counting customers** across TAM layers. Each customer belongs to exactly one segment.
- **Using list price instead of effective ARPU.** Discounts, packaging, and churn drag realizations below sticker.
- **Confusing TAM with SOM.** TAM is the vision; SOM is the plan. Nobody ships to TAM in year one.
- **Anchoring on one method.** If Bottom-Up gives $3M SOM and Top-Down gives $30M, you haven't made a mistake — you've found a question worth resolving.
- **Ignoring competitor share.** SAM is total reachable; SOM requires a realistic share-of-wallet estimate after accounting for incumbents.
- **Over-filtering SAM** to make the story sound bigger. If you slice to a niche, justify why that niche is the right beachhead.

---

## Verification step

Before finalizing market sizes, run this checklist:

- [ ] Can I list 3–5 comparable data sources for the Top-Down number?
- [ ] Can I trace the Bottom-Up customer count to a credible list (CRM, public registry, or industry report)?
- [ ] Is my SOM internally consistent with my sales hiring plan and historical conversion rates?
- [ ] Have I disclosed the assumption set so someone else can reproduce the math?
- [ ] Does the Value Theory number sit between (or explain deviation from) the other two methods?

If any box is unchecked, the market size is not yet board-ready.
