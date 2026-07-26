---
title: Fundraising Dilution and Pro-Forma Cap Table Modeling
name: SakKing-fundraising-dilution-cap-table-modeling
description: |
  Model dilution, build pro-forma cap tables, choose between SAFEs/convertible notes/priced rounds,
  and diagnose cap table health before a fundraising round. Use when preparing for a raise,
  evaluating a term sheet, sizing an ESOP pool, stacking convertible instruments, or when
  founders ask "how much do I really own after this round?"
triggers:
  - "SAFE vs convertible note"
  - "pre-money vs post-money"
  - "pro-forma cap table"
  - "term sheet evaluation"
  - "dilution calculator"
  - "liquidation preference"
  - "ESOP pool"
  - "option pool sizing"
inputs:
  - Current shares outstanding (founders, previous investors, exercised options)
  - SAFEs / convertible notes (amount, cap, discount, interest, issue date)
  - Target investment amount and proposed pre-money valuation
  - Desired ESOP pool % (post-money or pre-money)
  - Exit value assumptions (for waterfall test)
outputs:
  - Pro-forma cap table (% and shares)
  - Founder ownership post-close
  - New investor ownership and implied price per share
  - Dilution impact of each instrument (waterfall)
  - ESOP sizing recommendation (pre vs post money)
  - Liquidation preference exit waterfall
---

# Fundraising Dilution and Pro-Forma Cap Table Modeling

## Why this skill
Founders routinely confuse pre-money with post-money, mis-model SAFE dilution, and discover too late that their cap table is broken. This skill turns cap table math from a spreadsheet hobby into a repeatable diagnostic with hard guardrails. It covers instrument selection, pro-forma construction, dilution math, ESOP sizing, and a quick liquidation preference sanity check.

---

## Step 1 — Snapshot the Current Cap Table

Before any round, lock a clean cap table snapshot (optionally use Carta, Pulley, or a spreadsheet). You need:

- **Common shares outstanding** (founders + previous rounds, all issued)
- **Options exercised** (should be in common)
- **Options reserved but unissued** (in the option pool)
- **SAFEs / convertible notes**: amount, valuation cap, discount rate, interest rate, and issue date
- **Outstanding warrants**

**Output:** A table with current ownership percentages on a fully-diluted basis (including all reserved options).

---

## Step 2 — Choose the Right Instrument (Decision Tree)

```text
Is valuation agreed and is a priced round feasible (legal cost < 1% of check)?
├── YES → Priced round (Series Seed / A / B). Cleanest cap table.
└── NO  → Convertible instrument. Choose by round maturity:
          ├── Pre-seed / friends & family → YC SAFE (post-money, no cap or moderate cap)
          ├── Angel/early seed → Convertible note (discount + cap, interest, maturity)
          └── Bridge before priced round → SAFE or note with a clear cap tied to next round
```

**Rules of thumb:**
- Use a **post-money SAFE** when possible. It clearly separates the new-money pool from existing shareholders, so only the new investor is diluted by the SAFE amount.
- Use a **convertible note** only when you need a maturity date/interest mechanism (e.g., bridge loans) or when the investor insists on downside protection via a note.
- Avoid **pre-money SAFEs** unless you fully understand how they stack; they dilute founders *and* the new investor.

---

## Step 3 — Master Pre-Money vs Post-Money

This is where 80% of cap table fights happen.

| Concept | Formula |
|---|---|
| **Pre-money valuation** | `V_pre` |
| **Investment amount** | `I` |
| **Post-money valuation** | `V_post = V_pre + I` |
| **New investor ownership** | `I / V_post` |
| **Previous owner collective dilution factor** | `V_pre / V_post` |

**Example:**
- Pre-money: $6M
- Investment: $1.5M
- Post-money: $7.5M
- New investor owns: $1.5M / $7.5M = **20%**
- Previous shareholders collectively own: $6M / $7.5M = **80%**

---

## Step 4 — Build the Pro-Forma Cap Table (Single Round + Post-Money ESOP)

**Scenario:**
- Founder: 10,000,000 common shares
- Investment: $1.5M at $6M pre-money
- ESOP: create 10% pool post-money

**Calculation:**
1. Post-money valuation = $6M + $1.5M = $7.5M
2. New investor owns: $1.5M / $7.5M = 20%
3. ESOP owns: 10% (post-money)
4. Founder owns: 1 − 20% − 10% = **70%**

**Shares:**
- Founder's 10M shares = 70% of post-money total.
- Post-money total shares = 10M / 0.70 = 14,285,714
- Investor shares = 20% × 14,285,714 = 2,857,143
  - Price per share = $1.5M / 2,857,143 = $0.525
- ESOP shares = 10% × 14,285,714 = 1,428,571
- Pre-money shares (founder + pre-existing ESOP) = 14,285,714 − 2,857,143 = 11,428,571
- Pre-money valuation check: 11,428,571 × $0.525 = $6.0M ✓

**ESOP pre- vs post-money:**
- **Post-money** (above example): dilutes founder *and* new investor. Cheaper for founder.
- **Pre-money**: pool is carved out of founder shares *before* pricing. Founder keeps less, but new investor is unaffected by the pool size.
- **Rule**: Always model both. If investors demand pre-money, require a higher pre-money valuation to offset founder dilution.

---

## Step 5 — Model SAFEs / Notes into the Pro-Forma

**Scenario:**
- Founder: 10M shares
- Post-money SAFE: $300K at $4M cap
- Priced round: $1M at $5M pre-money
- ESOP: 10% post-money

**Algorithm:**
1. **Convert the SAFE first.** A post-money SAFE at a $4M cap with a $300K investment gets:
   - Ownership immediately post-SAFE = $0.3M / $4M = **7.5%**
   - The founder is diluted from 100% to 92.5% *before* the priced round.
   - In share terms: if total post-SAFE shares = S, SAFE holds 0.075S, founder holds 0.925S.

2. **Bring in the priced round.**
   - New investor gets $1M / ($5M + $1M) = **16.67%** of post-money.
   - ESOP = 10% of post-money.
   - Founder = 1 − 0.0833 (pre-SAFE? No) — wait, the founder was already diluted to 92.5% by the SAFE. Now everyone after the SAFE is diluted by the new round and ESOP.

   - Actually simpler: treat the SAFE as a separate class with a fixed share count and fixed %, then run the priced round pro-rata across all post-SAFE holders.

   Let's do it share-first:
   - Assume 10M founder shares = 92.5% after SAFE. Total post-SAFE shares = 10M / 0.925 = 10.81M.
   - SAFE shares = 0.811M (7.5%).
   - Now priced round + ESOP target = 26.67% of final company.
   - Final shares = 10.81M / (1 − 0.2667) = 14.73M.
   - Investor shares = 16.67% × 14.73M = 2.455M. Price = $1M / 2.455M = $0.407.
   - ESOP shares = 1.473M.
   - Founder final % = 10M / 14.73M = **67.9%**.
   - SAFE final % = 0.811M / 14.73M = **5.5%**.

**Key insight:** A $300K post-money SAFE at a $4M cap costs the founder ~11.6 percentage points (100% → 67.9%) in this scenario, not just the 7.5% the SAFE document implies, because the priced round and ESOP dilute the SAFE too.

---

## Step 6 — Liquidation Preference Sanity Check

Run an exit waterfall at $0, $5M, $20M, and $50M for the pro-forma cap table.

**Assumptions:** $1.5M priced investment (1x preference), no participation.

| Exit value | Preferred (1x) | Common pool | Founder take (if 67.9% of common) |
|---|---:|---:|---:|
| $5M | $1.5M | $3.5M | $2.38M |
| $20M | $1.5M | $18.5M | $12.56M |
| $50M | $1.5M | $48.5M | $32.92M |

If investors have **participating preferred** (1x participating):
| Exit $20M | Preferred (1x + pro-rata) | Common pool | Founder take |
|---|---:|---:|---:|
| Participating | $1.5M + 20% × $18.5M = $5.2M | $14.8M | $10.05M |

If investors have **2x participating**:
| Exit $20M | Preferred (2x + pro-rata) | Common pool | Founder take |
|---|---:|---:|---:|
| 2x participating | $3.0M + 20% × $17M = $6.4M | $13.6M | $9.23M |

**Diagnostic:** At a 2x exit ($15M post-money), founder takes drop by ~25% floor vs. non-participating. At sub-$5M exits, founder can receive $0 even with 68% common ownership if preferences stack.

---

## Step 7 — Verification Step (Cap Table Health Check)

Before signing or modeling further, run these checks:

1. **Percentage Sum**: All classes (common, preferred, options, SAFEs converting) sum to exactly 100%.
2. **Dollar Consistency**: `price_per_share × total_post_shares ≈ post_money_valuation`.
3. **Founder Reality Check**: Print founder ownership % *and* effective control % (if voting differs).
4. **SAFE Shadow Check**: List every SAFE/note as if it converted today. Does the pro-forma still show > 50% common ownership for founders at the current valuation?
5. **Exit Waterfall**: If the company sells for 2x the post-money, do founders walk away with > 0? With participating preferred at >1x, sometimes they get nothing.

---

## Pitfalls

1. **Pre-money / post-money confusion**: A $5M *post-money* SAFE and a $5M *pre-money* priced round are completely different. In the first, the company is worth $5M after the money; in the second, it's worth $5M before.
2. **Ignoring the "option pool increase" mechanic**: If the term sheet requires a post-money ESOP, it dilutes *everyone* (founder + new investor). If it requires pre-money, it dilutes only founders.
3. **Pro-rata not modeled**: Early investors often have pro-rata rights. If they participate in the next round, their % stays flat and new investors/founders get diluted more.
4. **Discount + cap interaction**: A note with a 20% discount and a $4M cap converts at the *lower* implied price, not both. Model `min(cap, price × (1 − discount))`.
5. **Interest on notes**: A 6–8% interest rate over 12–24 months adds 0.5–1.5% to the amount, which translates directly to shares.
6. **Valuation cap vs. interest cap**: Some term sheets have an interest *cap* on notes (non-compounding), others compound. Read carefully.
7. **Founder shares with vesting**: If founder shares are subject to repurchase/vesting, "fully diluted" should distinguish between issued-and-outstanding vs. vested. Investors care about both.
8. **Multiple liquidation preferences**: Stacking 1x preferences across rounds is normal. Stacking >1x (e.g., 2x) is dangerous and can wipe founders out in sub-$50M exits.

---

## Formulas Cheat Sheet

| Formula | Use |
|---|---|
| `V_post = V_pre + I` | Post-money valuation |
| `Investor % = I / V_post` | New investor ownership |
| `SAFE post-money % = investment / cap` | Post-money SAFE ownership pre-next-round |
| `Founder % post round + ESOP = 1 − investor% − ESOP%` | Founder ownership after single priced round |
| `Conversion price = min(priced_price × (1 − discount), cap_price)` | SAFE/note share price |
| `Shadow shares = amount / conversion_price` | Shares issued to instrument |
| `ESOP post-money` = pool is created from new shares → **everyone dilutes** | — |
| `Non-participating exit = max(liquidation, ownership × exit)` | Preferred economic choice |
| `Participating exit = liquidation + (ownership × (exit − senior_liquidation))` | Preferred with participation |

---

## Use Cases

- **Pre-raise readiness**: "Is my cap table fundable?" → model a $3M Series Seed pro-forma and check founder ownership.
- **Term sheet review**: "Is this SAFE fair?" → compare post-money ownership % vs. a priced round at same valuation.
- **Bridge planning**: "Should I raise a note now?" → model the dilution at a $8M Series A and compare note vs. SAFE.
- **ESOP negotiation**: "Do we give up a bigger pool?" → quantify exactly how much founder ownership costs in terms of basis points per percent pool.
