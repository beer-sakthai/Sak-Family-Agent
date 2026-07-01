---
name: saas-gross-margin-optimization
description: >
  Audit, classify, and optimize SaaS gross margin by correctly identifying COGS
  components, fixing misclassification, and applying levers to hit the 75%
  investor benchmark. Use when gross margin looks low, investors question unit
  economics, preparing for fundraising, building board KPI decks, or when the
  finance team cannot agree on what belongs in COGS vs OpEx.
---

# SaaS Gross Margin Optimization

## Trigger
- Board/investors ask why gross margin is below 70% (or falling as revenue scales).
- You need to size "true" unit economics before a pricing change, channel expansion, or M&A.
- Finance and engineering disagree on what costs are "direct" vs "indirect."
- Pre-fundraising: you want to present defensible, best-in-class unit economics.

## Workflow

### 1. Pull the raw P&L by expense line item
Export last 3–6 months of P&L (or T12) at the GL level. Do not rely on a pre-rolled "COGS" bucket—it is probably wrong.

### 2. Map every expense line into one of five SaaS COGS buckets or OpEx
**COGS buckets (direct cost of delivering the service to a customer):**
| Bucket | What belongs here | Typical % of total COGS |
|--------|-------------------|------------------------|
| Cloud Hosting & Infrastructure | AWS/GCP/Azure, CDN, managed DB, object storage, ingress/egress | 15–30% |
| Payment Processing | Stripe/Braintree/PayPal fees, merchant fees, interchange & scheme fees | 5–15% |
| Third-Party APIs & Software | APIs consumed per user/feature (Twilio, SendGrid, Plaid, mapping, AI inference), embedded SaaS licenses | 10–25% |
| Customer Support | Support staff salaries + benefits, support tooling (Zendesk, Intercom), onboarding CS for net-new logos only | 15–25% |
| Professional Services (direct delivery) | Implementation/onboarding hours directly tied to a specific customer contract; not product development | 5–15% |

**Everything else is OpEx:** R&D/engineering (unless contract-custom dev), sales & marketing, G&A, finance, legal, HR.

### 3. Calculate baseline gross margin
```
Gross Margin % = (ARR / CMRR − COGS) / (ARR / CMRR)
```
Use the same denominator for both revenue and COGS (e.g., strip out passthrough revenue that has no associated COGS).

### 4. Diagnose the "margin killers"
Common misclassifications that inflate COGS and depress GM:
- **R&D / Engineering salaries** accidentally booked to COGS (should be OpEx unless 100% customer-specific customization).
- **Dev tools** (GitHub, Datadog, Linear) booked to COGS (OpEx).
- **Sales commissions** or **success fees** booked to COGS (should be S&M).
- **G&A tools** (HRIS, legal software) in COGS.
- **Professional services creep**: CS or PS work that is "expansion" not "onboarding" should be COGS only if it is a contractual, directly billable pass-through cost tied to a specific revenue stream. Otherwise, move to S&M or CS OpEx.

### 5. Apply levers to compress COGS toward target
Prioritized levers for SaaS:
1. **Cloud cost optimization**: Right-size instances, reserved instances, spot fleets, idle resource cleanup. Target: reduce hosting by 10–20%.
2. **Payment processor negotiation**: Volume rebates, interchange optimization, or direct merchant account. Target: reduce fees by 10–20 bps.
3. **API cost management**: Batch calls, cache responses, negotiate enterprise tiers, replace low-value AI/API features with cheaper heuristics.
4. **Support cost per ticket**: Deflect via docs/self-serve, tiered support response SLAs, automation (chatbots). Target: hold support COGS flat as ARR grows.
5. **Professional services cap**: Move time-and-materials onboarding to fixed-fee productized packages or automate the first 80% of setup.

### 6. Recalculate and verify
After reclassification:
```
New Gross Margin % = (Revenue − Corrected COGS) / Revenue
```
Benchmark against stage:
- **Early-stage (<$1M ARR):** 60–75% is common due to high onboarding/PS costs.
- **Growth stage ($1M–$20M ARR):** 70–80% is the target; below 70% signals heavy customization or uncontrolled infra.
- **Scale stage (>$20M ARR):** 75–85% is achievable for pure-play SaaS.

If after reclassification and levers you are still below 70%, identify whether the business is actually a *services-heavy* or *AI-native* business (different unit economics apply—see `ai-native-unit-economics`).

## Formulas & Examples

**Example calculation:**
- ARR: $10M
- COGS (raw): $3.5M → 65% GM
- After reclassification: $2.8M (fixed misclassification + host optimization + API savings)
- New GM: 72%

**COGS intensity check:**
```
COGS as % of Revenue = COGS / Revenue
```
- Hosting alone >10% of revenue: investigate over-provisioning.
- Payment fees >3% of revenue: renegotiate or optimize routing.
- APIs >5% of revenue: audit per-user consumption and build cost into pricing tier.

**Inventory analogy (for marketplace/usage-based hybrid):** If your product has a direct cost per unit (e.g., SMS cost per message, compute cost per inference), model marginal COGS per unit to ensure no tier is underwater.

## Pitfalls
- **"We've always booked it this way":** Legacy chart of accounts errors are common in seed/series A. Reclassification is an audit, not an opinion.
- **Ignoring hidden professional services:** "Custom setup" hours often bleed from product engineering into COGS without a control loop.
- **Averaging across disparate revenue streams:** Marketplace or usage-based revenue with different marginal cost structures must be gross-profit-segmented, not blended.
- **Pushing COGS down at the expense of product quality:** Aggressively cutting support or onboarding can raise churn and CAC, destroying unit economics.
- **Treating gross margin as static:** Cloud and API costs evolve with usage; revisit quarterly.

## Verification Step
Run this sanity check before finalizing:
1. **Zero-based COGS rebuild:** Start from zero; add only lines that meet the five-bucket rules. The delta vs. reported COGS is your misclassification number.
2. **Per-unit COGS test:** For your largest revenue segment, compute COGS per $1 of revenue. It should align with the benchmark for your stage. If a segment deviates by >10 points, investigate.
3. **Trend check:** Plot 12-month GM%. It should improve or stabilize as ARR scales. A worsening trend at scale means COGS is growing faster than revenue—usually hosting or services creep.
