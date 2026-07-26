---
name: SakKing-saas-price-increase-execution-playbook
title: SaaS Price Increase Execution Playbook
description: Design, communicate, and execute SaaS price increases on existing customers with controlled churn impact. Covers grandfathering strategy, cohort sequencing, communication cadence, churn impact modeling, and live post-rollout monitoring. Use when leadership has decided to raise prices, when margin expansion is needed, when product value has materially increased, or when preparing a board discussion on pricing power.
tags: [pricing, gtm, churn, nrr, revenue, b2b-saas]
---

# SaaS Price Increase Execution Playbook

> **Trigger:** You need to raise prices on existing customers — not design a new pricing tier or run an experiment, but execute a live price change across the installed base with minimal churn and maximal net revenue uplift.

---

## 1. Baseline Assessment (Week -4 to -2)

Before announcing anything, establish hard benchmarks:

| Metric | Formula | Target Baseline |
|--------|---------|-----------------|
| NRR | (Open ARR + Expansion - Contraction - Churn) / Open ARR | ≥ 110% |
| Gross churn rate | Churned ARR / Open ARR | < 3.5% monthly |
| Concentration | Top-10 customers / Total ARR | < 25% |
| Days-to-renewal | Average days remaining on current contract | Segment by risk |

**Decision gate:** If gross churn > 4.5% or NRR < 100%, delay the increase until retention is stable.

---

## 2. Segmentation and Cohort Design (Week -2)

Split the installed base into **risk tiers** based on:
1. Contract renewal date (in-term vs renewing soon)
2. Usage health score (active / at-risk / dormant)
3. Strategic value (referenceable, partnership, champion)
4. Price sensitivity history (past discount usage, deal desk friction)

**Cohort sequencing recommendation:**
- **Pilot tier (20% of ARR):** healthiest accounts renewing in next 60–90 days. Test messaging, objections, and actual churn lift.
- **Fast-follow (40%):** healthy accounts mid-term. Announce 4–6 weeks after pilot.
- **Protect tier (30%):** at-risk but not churning. Hold until post-pilot data validates acceptable churn lift.
- **Grandfather tier (10%):** strategic accounts, annual contracts >$100k ACV, or reference customers. Offer 6–12 month grace period or permanent grandfathering in exchange for multi-year renewal.

**Pricing action per cohort:**
| Cohort | Action |
|--------|--------|
| Pilot | Full increase at renewal |
| Fast-follow | Full increase at renewal or in-term with notice |
| Protect | Increase at next renewal only |
| Grandfather | Hold or increase only on multi-year extension |

---

## 3. Grandfathering Strategy (Week -2)

Grandfathering is a **cost of retention**, not charity. Model it:

- **Full grandfather:** zero increase. Cost = (New price - Old price) × ARR. Use only for accounts where churn risk > 30%.
- **Time-boxed grandfather:** hold existing price for 6–12 months, then full increase. Useful for accounts coming up for renewal inside the pilot window.
- **Hybrid grandfather:** hold base price but remove legacy discounts or move to current tier structure. Often captures 60% of uplift with <20% of churn risk.
- **Feature grandfather vs price grandfather:** keep price but sunset a premium feature. Often cheaper if feature costs are << margin.

**Rule:** Every grandfathered dollar must be mapped to either (a) multi-year lock-in value, (b) reference/referral value, or (c) high probability of organically churning anyway.

---

## 4. Communication Playbook (Week -1 to Execution)

### Timeline
| Timing | Action |
|--------|--------|
| T-30 days (in-term) or T-90 days (renewing) | Personalized email from account owner / CSM |
| T-14 days | Follow-up with executive summary and FAQ |
| T-7 days | Final reminder with link to accept new terms |
| T-0 | Billing switches; grace period flags trigger if not accepted |
| T+7 | Dunning / suspension workflow if still pending |

### Message structure
1. **Lead with new value:** product updates, roadmap items, security improvements, support enhancements since last purchase.
2. **State the change clearly:** percentage increase, effective date, new price.
3. **Acknowledge the ask:** "We know price changes require review."
4. **Provide a path:** accept now, discuss at renewal, or escalate to CS leadership.
5. **FAQ block:** "Why now?", "Will this happen again?", "What if this is a bad time?"

**Tone:** confident, grateful, not apologetic. Avoid "unfortunately we must raise prices."

---

## 5. Churn Impact Modeling (Week -2)

Use **cohort-matched historical data** to estimate lift:

```
Predicted churn increase = min(
  Historical lift from prior price changes (if any),
  0.5 × (New price / Old price - 1)
)
```

**Industry benchmarks (use with caution — calibrate to your data):**
- 10–15% price increase every 18 months
- Typical gross churn lift: +2.0 to +2.5 percentage points
- Net revenue uplift: +9% to +11% (after churn drag)
- Accounts that churn post-increase were ~3× more likely to have had support tickets in prior 90 days

**Segment the model:**
- Low-touch / low-ARPU: higher churn sensitivity
- Enterprise / multi-year: lower sensitivity if bundled with added services
- Usage-trending-down: treat as soft churn regardless of price

---

## 6. Rollout Execution and Monitoring (Week 0 to +8)

### Week 0: Launch
- CSM standup with role-play on objections: "We're over budget", "Competitor X is cheaper", "No new features justify this."
- Enable talk track: pivot to renewal value summary, not feature-by-feature defense.

### Weekly Dashboard (first 8 weeks)

| Metric | Alert Threshold |
|--------|-----------------|
| Acceptance rate | < 85% within 14 days |
| Churn rate (increase cohort) | > +4pp vs prior 30-day baseline |
| Net revenue uplift (realized) | < 6% by week 4 |
| Escalation volume | > 10% of cohort opening CS tickets |
| downgrade / contraction requests | > 5% of cohort |

**Playbook responses:**
- Acceptance < 85%: extend grace period by 7 days; release simplified accept flow.
- Churn > +4pp: pause next cohort; diagnose root cause by segment.
- Escalation spike: update CSM talk track and FAQ with real objections.

### Week 4 and Week 8 Retro
- Actual vs modeled churn lift by segment
- Revenue uplift realized
- Objection themes from CSM conversations
- Update internal playbook and set date for next price review

---

## 7. Pricing Power Signal (Board / Investor View)

After execution, communicate pricing power as a structured metric:

```
Pricing Power Index = (NRR - GRR) - (Expansion-only NRR - 100%)
```

Simplified: **Gross NRR - 100% = combined volume + price effect.**

If price contributed > 60% of that spread, you have proven pricing power. This is a board-level KPI distinct from growth.

---

## 8. Common Pitfalls

1. **"We'll just raise the listed price and grandfather selectively."** 
   - Misfire: customers discover new pricing via public website or sales quotes before being told. Perceived deception drives 2× churn.
2. **Timing increases during contract renewal windows without notice.**
   - Surprise renewals with a 20% hike feel punitive; allow 90+ days notice for in-term increases.
3. **Ignoring in-term customers.**
   - Only raising at renewal front-loads churn into renewal season and misses ~40% of ARR in in-term contracts.
4. **No internal alignment before external communication.**
   - Sales, CS, and support must hear the playbook simultaneously. If an account exec promises a discount to "calm things down," you've corrupted the test.
5. **Under-investing in pilot.**
   - Skipping pilot because "we have no prior increases" means you have no error rate calibration. Run the pilot even if it's 30 days and 50 accounts.
6. **Annualize the uplift too early.**
   - Price increases look like a revenue spike in the month of conversion; normalize to monthly ARR impact, not total invoiced dollars.

---

## 9. Verification Step (Success Criteria)

Six months post-execution:

- [ ] Realized NRR uplift ≥ modeled net revenue uplift (benchmark: ≥ +8%)
- [ ] Churn in increase cohort returned to baseline within 90 days of last increase
- [ ] No material drop in NPS / CSAT in affected cohorts (≤ 5 points)
- [ ] Sales cycle time for renewals in increased cohort did not increase > 20%
- [ ] Updated internal pricing cadence: next increase scheduled 12–18 months out

If all boxes pass, institutionalize the playbook. If ≥ 3 boxes fail, revert grandfathering and redesign before next attempt.
