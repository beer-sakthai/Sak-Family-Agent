---
name: saas-pricing-experiment-design
description: >
  Design, run, and roll out statistically valid pricing experiments for SaaS products.
  Covers hypothesis framing, sample-size math, test types (new-user, geo, holdout),
  duration calculations, revenue-impact analysis, and rollout decisions.
  Use when testing a price increase, launching a new tier, optimizing a decoy
  structure, or asking \"should we change our price?\" with data rather than instinct.
tags:
  - pricing
  - saas
  - experimentation
  - gtm
  - monetization
  - statistics
---

# SaaS Pricing Experiment Design & Execution

## When to Use This Skill

- Testing a price increase on new signups before forcing it on the entire base
- Validating a new tier structure or decoy layout before a full redesign
- Optimizing charm vs. rounded pricing at specific price points
- Deciding between usage-based anchor thresholds
- Running a value-metric shift (e.g., seats → projects) and pricing impact is uncertain
- Diagnosing whether a price change (past or proposed) caused true demand shifts

---

## Core Precept

> **A bad pricing decision made slowly with data beats a good pricing decision made fast with gut.** Pricing experiments are not about proving you are right — they are about measuring customer price elasticity with controlled variance so you can release winners and kill losers before they damage the entire installed base.

---

## Step 1 — Write a Quantifiable Hypothesis

A pricing hypothesis must contain a **predictor** and a **measurable outcome**.

**Format:**
```
If we [change X] for [audience Y], then [metric Z] will move [direction]
because [behavioral mechanism].
```

**Good examples:**
- "If we raise Pro from $49 to $59 for new signups, then 30-day net revenue per visitor will increase by ≥8% because price-elasticity in our mid-market segment is −1.4 and conversion dip will be offset by higher ARPU."
- "If we move the 'Most Popular' badge from Pro to Advanced for new visitors, then Advanced adoption will rise to 40% because decoy engineering makes Advanced look like better value."

**Bad examples:**
- "If we raise prices, we'll make more money." (not falsifiable, no magnitude claim)
- "Customers love our product, so they'll pay more." (no mechanism, no metric)

**Rule:** If you cannot state the expected magnitude and direction before the test starts, the test is fishing, not science.

---

## Step 2 — Choose the Right Test Type

| Test Type | Use Case | How It Works | Key Constraint |
|-----------|----------|--------------|----------------|
| **New-user test** (front-door A/B) | Price point / tier layout changes | New visitors randomized by cookie or account ID into price variants at signup | No leakage; new users only, never existing |
| **Geo test** | Broader GTM or packaging changes | Entire IP ranges or regions locked into a variant; long-running | Must be large enough region; network effects can dilute |
| **Holdout test** | Rollout validation | Treat a control group that continues to see old price while experiment group sees new | Ethical only if price is lower for control; otherwise use new-user test |
| **Path-level test** | Test a single page or call-to-action | Only the pricing page / checkout free trial CTA is variant-ized; downstream conversion measured | Confounds if upstream traffic composition shifts |

**Default recommendation:** Start with new-user tests. They are cleanest, fastest, and ethically safest.

---

## Step 3 — Calculate Sample Size and Duration

### Sample Size Formula (two-proportion z-test for conversion)

```
n = 16 × σ² / Δ²
```

Simplified for binary conversion with equal allocation:

```
For each variant:
n = (Z_{α/2} + Z_{β})² × p × (1-p) / (Δ)²
```

Where:
- **p** = expected baseline conversion rate (use last 30 days)
- **Δ** = minimum detectable effect (MDE) you care about (e.g., 5% relative)
- **Z_{α/2}** = 1.96 for α=0.05 (5% false positive rate)
- **Z_{β}** = 0.84 for power=0.80 (80% chance of detecting true effect)

**Rule of thumb approximations:**
- p = 3%, MDE = 0.25pp absolute → n ≈ 58,000 per arm
- p = 5%, MDE = 0.50pp absolute → n ≈ 24,000 per arm
- p = 10%, MDE = 1.0pp absolute → n ≈ 14,000 per arm

**Conversion to calendar days:**
```
Days = (n per variant × number of variants) / daily_new_users
```

**Minimum run time:** 2 full billing cycles (usually 2–4 weeks for monthly, 2 months for annual) to capture upgrade/churn signals.

**Sample-size calculators:** Use Evan's Awesome A/B Tools (www.evanmiller.org/ab-testing/) or the Python snippet in `scripts/sample_size_calc.py`.

---

## Step 4 — Define Primary and Secondary Metrics

Never run a pricing experiment with conversion alone. Pricing changes affect revenue through multiple channels.

| Metric | Why It Matters | Threshold for Rollout |
|--------|----------------|----------------------|
| **Net Revenue Per Visitor (NRPV)** = conversion × ARPU | Direct revenue impact; stops chasing fake wins | ≥ +5% with 95% CI |
| **Conversion Rate** | Top-of-funnel demand signal | Not worse than −10% relative |
| **Upgrade / Downgrade rate** (30d, 90d) | Tier migration after initial purchase | Positive net migration or neutral |
| **90-day churn (new cohort)** | Price sensitivity lag signal | Not worse than baseline +1pp absolute |
| **Time to payback** (if trial/HQL motion) | Cash efficiency check | Within 10% of baseline |

**Primary metric = NRPV.** All other metrics are secondary/guardrail.

---

## Step 5 — Design for Clean Variance

### Randomization
- Hash `account_id` or `email_domain` modulo variant count at signup.
- Never bucket by time-of-day or IP geolocation alone unless you are running a geo test.

### Guardrails During the Test
1. **Do not change the product** during the test. A feature launch is a confound.
2. **Do not change traffic sources** — a sudden surge from a discount site can skew one variant.
3. **Do not change support messaging** — a chat-bot copy change can bump conversion.
4. **Monitor daily** for Simpson's Paradox (overall looks good but segments invert).
5. **Keep control arm unexposed** to the new price until rollout decision is final.

### Novelty Effect Watch
Price tests often show a "honeymoon" bump in early days due to attention, then normalize. Always look at rolling 7-day windows rather than cumulative early readings.

---

## Step 6 — Analyze and Decide

### Statistical Significance vs. Business Significance

A p-value < 0.05 means "this result is unlikely due to chance." It does NOT mean "implement now."

**Decision matrix:**

| Result | 90% CI on NRPV | 95% confidence | Decision |
|--------|----------------|----------------|----------|
| Strong win | Lower bound > +8% | Yes | Roll out to 100% immediately |
| Marginal win | Lower bound +2% to +8% | Yes | Roll out to 50% with continued monitoring, full rollout in 30 days if sustained |
| Inconclusive | CI crosses 0 | No | Kill experiment; cannot declare winner; return to hypothesis |
| Harm signal | Lower bound < −5% | Yes | Kill immediately; document learnings; do not blame the price team |

**Confidence intervals matter more than point estimates.** A +15% lift with CI [−2%, +32%] is not a win — it is an inconclusive result that happened to look good by chance.

### Revenue Impact Formula

```
Weekly Revenue Lift = (NRPV_experiment − NRPV_control) × total_new_visitors_per_week
Annualized Lift = Weekly Revenue Lift × 52
```

Example:
- Control NRPV = $4.20
- Experiment NRPV = $4.58 (+9.0%)
- Lower bound of 90% CI = +6.2%
- Weekly new visitors = 3,200
- Weekly lift = $4.58 × 3,200 − $4.20 × 3,200 = $1,216
- Annualized = $63,232
- If the only change is a $10/month price bump on one tier → experiment cost is minimal
- **Rollout justified.**

---

## Step 7 — Rollout / Kill Protocol

### If Rolling Out
1. Announce to CS team 48h before; prepare objection handlers.
2. Offer grandfathered legacy rate to existing customers for 12 months (do NOT force current base onto new price without transition).
3. Push annual contracts at the new rate with a "lock in before next increase" framing.
4. Monitor NRPV and churn weekly for 4 weeks post-full-rollout; expect a 1–2 week dip as bots/scrapers drop off, then stabilize.
5. Re-measure cohort churn at 90 days against experiment projection.

### If Killing
1. Document the exact hypothesis, expected effect, and observed result.
2. Check whether the failure was a pricing problem or an execution problem (wrong audience, wrong segment, confounded by product change).
3. Archive the data; do not rerun the exact same test later — the market has shifted.

---

## Common Pitfalls

| Pitfall | Why It Hurts | Fix |
|---------|--------------|-----|
| Testing existing customers at new prices | Breaks trust, creates PR/churn risk, contractual violations | Always test on new-user acquisition unless running a controlled holdout |
| Changing price without changing value perception | Demand drops and you lose signal on whether price or packaging is the issue | Pair price tests with packaging tests or hold page context constant |
| Running too short | Misses churn signal; captures early-stage traffic bias | Minimum 2 billing cycles; longer for annual plans |
| Multiple variants without correction | Family-wise error rate explodes; ~30% chance one variant looks winning by noise | Bonferroni correction or stick to 2 variants (control vs. one challenger) |
| Optimizing for conversion only | Higher price with lower conversion can still win on NRPV | Primary metric is always NRPV or equivalent revenue-per-visitor |
| Force-rolling out to existing base | Churn spike from sticker shock; CS overload | Grandfather existing contracts; only apply to net-new |
| Ignoring segment-level variance | Enterprise segment may tolerate +20%, SMB only tolerates +5% | Segment results post-hoc; plan tier-specific rollout |

---

## Verification Checklist

Before calling the experiment complete and making a decision, confirm:

- [ ] Primary hypothesis stated before the test with expected magnitude
- [ ] Sample size calculated and target N achieved for each variant
- [ ] Run duration ≥ 2 billing cycles and ≥ 14 calendar days
- [ ] No product/feature/promotion changes during the test window
- [ ] Primary metric (NRPV) measured with 90% CI not crossing zero
- [ ] Guardrail metrics (churn, downgrade) within pre-agreed bands
- [ ] Omnibus test (overall NRPV) checked; segment-level checks performed
- [ ] Decision mapped to roll-out/kill criteria from Step 7 before revealing the winner

---

## What This Skill Does NOT Cover

- Designing the tier architecture or psychological nudge itself (see `saas-pricing-architecture`)
- Usage-based metering and per-unit cost modeling
- Geographic FX adjustments or localized pricing strategy
- Revenue recognition (ASC 606) implications of deferred invoicing changes
- Platform-specific setup for Stripe Billing, Chargebee, or Paddle experiments (methodology only)

---

## Related Skills

- `saas-pricing-architecture` — tier design, psychological levers, and value-metric selection (design before testing)
- `saas-retention-metrics` — churn and cohort post-analysis to validate long-term pricing impact
- `b2b-pipeline-math-mql-to-close` — if your pricing test affects sales-assisted conversion paths
- `plg-funnel-economics` — for product-led motions where pricing page is a critical activation step
