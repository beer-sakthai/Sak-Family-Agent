---
name: saas-pricing-governance-and-exception-management
description: Design, implement, and operate a pricing governance system that protects margin while keeping sales velocity healthy. Covers maturity tiers, discount approval matrices, price exception policies, CPQ/CRM instrumentation, and operational guardrails. Use when discounting is creeping up, deal desk is a bottleneck, leadership wants visibility into "approved" vs "rogue" pricing, or when scaling from founder-led sales to a structured GTM org.
---

# SaaS Pricing Governance & Exception Management

## Trigger
Use this when:
- Average discount rate is rising without a corresponding revenue or win-rate justification
- Finance/RevOps cannot reconstruct how a deal was priced
- Sales reps bypass standard quotes with "contractor" or "amendment" workarounds
- You are scaling headcount and can no longer rely on founder intuition for pricing decisions
- Board/investors are asking for pricing discipline ahead of a raise or exit

## Workflow

### 1. Assess Pricing Governance Maturity
Score 0–5 on each axis:
- **Visibility**: Can you see every quote, discount, and final contract price in real time?
- **Consistency**: Do reps of similar tenure/cluster get similar discount authority?
- **Speed**: Does an average deal approval take <24 hours?
- **Compliance**: Are unauthorized discounts (>X% or outside authority) flagged automatically?

**Maturity stages:**
- 0–6: Ad-hoc / Founder-led
- 7–12: Disciplined / Tiered approvals
- 13–16: Predictive / Exception-based
- 17–20: Strategic / Compounding

### 2. Design Discount Authority Bands
Define who can approve what, anchored to **net price change %** and **absolute $ value**.

| Role | Authority Band | Typical Condition |
|------|---------------|-------------------|
| AE  | 0–10% / $0–5k | Standard quick close |
| SD / AM | 10–25% / $5k–25k | Competitive displacement, multi-year |
| Sales Manager | 25–40% / $25k–100k | Strategic logo, procurement pressure |
| VP Sales / Deal Desk | 40–60% / $100k+ | Market-share plays |
| CFO / GC | >60% or >$500k | Board-approved carve-outs |

**Tie bands to:**
- ACV segment (Enterprise gets wider bands than SMB)
- Product/package profitability (gross margin floor per tier)
- Competition score (only allow >20% if competitor named + proven)

### 3. Set the Gross Margin Floor and Discount Ceiling
**Formula per deal:**
```
approved = (
  target_gross_margin >= min_margin_floor
  AND discount_pct <= role_authority_band
)
```
**Typical floors by motion:**
- PLG / Self-serve: 75% GM
- Sales-led SMB: 65% GM
- Mid-market: 60% GM
- Enterprise: 50% GM (often negative due to professional services / SLAs)

Discounts beyond the floor must go to CFO/GC with a written business case and an **arr payback timeline**.

### 4. Enforce the Exception Policy
Create four exception buckets:
1. **Standard** — inside authority, auto-approve in CPQ
2. **Elevated** — out of authority by amount, manager review within 4 hours
3. **Strategic** — out of authority by %, requires cross-functional sign-off (Sales, Finance, Product) within 24 hours
4. **Carve-out** — board reserve; track in a separate log and review quarterly

**Rule:** Any deal discounted >30% off list must be tagged with:
- Competitor (or "no competition")
- Procurement timeline
- Expansion vector (land and expand potential)
- Win/loss probability adjustment

### 5. Instrument the Quote-to-Cash Stack
**Requirements:**
- CPQ / quoting tool enforces floor and ceiling; blocks non-compliant quotes before PDF generation
- CRM syncs final price, discount %, approver, and exception code
- Weekly report: exception rate by rep, segment, reason code
- Monthly leak audit: compare quoted list price vs signed price by ACV decile

If you lack a CPQ, build a **two-control** system:
- Control A: Sales Manager reviews all >15% deals in a shared Slack/Teams channel
- Control B: Finance pulls contract values monthly and flags outliers

### 6. Train, Shadow, and Calibrate
- Quarterly "pricing war games" where AEs role-play deals and calibrate what justifies a discount
- Win/loss review includes a "price" column; when price is the reason for loss, the discount authority should have been higher (or the packaging fixed)
- Compensation: cap commissionable base at **92% of net ARR** so reps bear margin risk, not just gross ARR risk

### 7. Iterate Quarterly
Metrics to track:
- **Exception rate**: % of deals requiring elevation/strategic sign-off (target: <15%)
- **Discount leakage**: (quoted price − signed price) / quoted price by segment (target: declining QoQ)
- **Sales cycle length**: approval latency impact (target: <20% of cycle)
- **Win rate by discount band**: if >35% discount wins 70% of deals, your list price is wrong
- **NRR by exception bucket**: strategic carve-outs should outgrow standard deals

Publish a one-page governance scorecard to the RevOps channel and copy the CFO.

## Pitfalls
- **Matching speed to control**: Too many approval gates for SMB kills velocity; tier bands by segment.
- **Ignoring packaging**: If every enterprise deal needs a 40% exception, your packaging or value metric is wrong — fix tiers, don't just raise exceptions.
- **Compounding discounts in multi-year deals**: A Year-1 20% discount carried into Year-2 without re-approval leaks 20% forever.
- **No sunset**: Carve-outs must expire; otherwise they become the new floor.
- **Deal desk as police vs. advisor**: Frame the team as "dealmaker" not "dealblocker"; compensation should reflect margin recovery, not just approval volume.

## Verification
**Monthly Discount Leakage Audit:**
1. Pull all signed contracts from the prior month.
2. Calculate quoted list price vs net signed price by ACV decile and product tier.
3. Flag any account where net discount > authority band without an exception code.
4. Present results to sales leadership with a one-slide heat map.

**Pass criteria:** Unauthorized discount rate ≤ 2% of total signed ARR; exception approval lead time ≤ 24 hours for 95% of deals.
