# 🏠 House of Sak — Master Report for SakSee
**From:** SakTan
**Date:** July 5, 2026
**Session:** Full day — 3 case studies + 118-business web scan

---

## 📋 Table of Contents

1. **The 3 Case Studies** — Aitheon, Bia Beirut, Cobh Print
2. **118-Business Web Scan** — Who needs House of Sak in Cork
3. **The Reusable Framework** — QA Shield Skill
4. **Key Learnings & Next Actions**

---

## 1. 🎯 THE 3 CASE STUDIES

---

### Case Study #1: Aitheon (aitheon.ie)

| Detail | Info |
|--------|------|
| **Type** | AI predictive maintenance startup |
| **Founders** | Oleksii Zhestkov & Barry O'Sullivan |
| **Platform** | Webflow + Cloudflare |
| **Contact** | info@aitheon.ie • +353 89 238 4071 |

**🔴 Critical Issues Found:**
1. **Lorem ipsum** on live /about-us page → kills credibility
2. **Missing OG image** → blank social share cards
3. **No JSON-LD structured data** → no rich search results
4. **Missing security headers** → X-Frame-Options, CSP, X-Content-Type-Options, Referrer-Policy
5. **No custom favicon** → Webflow defaults used

**✅ Quick Wins (1 hour total):**
1. Replace lorem ipsum with real text
2. Add og:image meta tag (use hero image)
3. Add Organization + Product + FAQ schema
4. Add X-Frame-Options and X-Content-Type-Options
5. Upload custom favicon

**🏆 Best House of Sak Fit:** QA Shield → fix gaps immediately. Agent Builder → FAQ chatbot for their pricing page.

**📄 File:** `house-of-sak/aitheon-trust-check-report.md`

---

### Case Study #2: Bia Beirut (biabeirut.ie)

| Detail | Info |
|--------|------|
| **Type** | Lebanese-Irish family food business |
| **Founders** | Rabih & Pamela Farah (2 people, founded 2024) |
| **Platform** | Webnode (PHP) |
| **Contact** | info@biabeirut.ie |
| **Reach** | SuperValu Food Academy + 2 farmers markets |

**🔴 Critical Issues Found:**
1. **`contact@example.com` placeholder email still on live site** 🚨
2. **Missing OG image** → blank social cards
3. **No JSON-LD** → no rich search
4. **Social links point to Webnode's accounts**, not theirs (FB/IG go to @webnode_ag)
5. **No caching** → repeat visitors load everything fresh

**✅ Quick Wins (1-2 hours):**
1. Remove placeholder email, use info@biabeirut.ie
2. Add OG image with hero photo of their spreads
3. Add FoodBusiness JSON-LD schema
4. Fix social links → link real TikTok @bia.beirut + set up proper FB Page
5. Delete 7+ "copy-of" duplicate pages from sitemap

**🏆 Best House of Sak Fit:** Social Pulse (they already have TikTok but no IG setup). Fast Prototype (rebuild from Webnode). Perfect emotional story for House of Sak brand.

**📄 File:** `house-of-sak/bia-beirut-trust-check-report.md`

---

### Case Study #3: Cobh Print & Marketing (cobhprintandmarketing.com)

| Detail | Info |
|--------|------|
| **Type** | Print & marketing company (serves local businesses) |
| **Location** | Newtown, Cobh, Co. Cork |
| **Platform** | Webador Lite (free tier — **SUSPENDED**) |
| **Contact** | cobhprintandmarketing@gmail.com • +353 87 0388 968 |
| **Clients** | Solar Clean, Cobh Tours, Cork Night Shop, GS Recovery, and more |

**🚨 Critical Finding — Website Suspended:**
- Returns **HTTP 451** — "Service suspended | Webador"
- Entire site is down. No content loads.
- Their real contact email is not even on their site (only support@webador.com)

**🏆 Best House of Sak Fit — Not a client play but a PARTNERSHIP:**
- They're in the same space as us (helping local businesses)
- **Referral partnership**: They send us clients needing web/QA; we send them clients needing print/marketing
- They also urgently need a new website themselves (ironic for a marketing company)

**📄 File:** `house-of-sak/cobh-print-trust-check-report.md`

---

## 2. 🔍 118-BUSINESS WEB SCAN

Source: Google Maps — 6 business categories in Cork (restaurants, barbers, shops, tradesmen, fitness, B&Bs)

### Web Presence Breakdown

| Status | Count | % |
|--------|-------|---|
| No website at all 🚨 | 19 | 16% |
| Facebook/Instagram only ⚠️ | 15 | 13% |
| Booking app / review site only ⚠️ | 7 | 6% |
| Has proper website | 71 | 60% |
| Chain brands | 5 | 4% |
| **Total needing House of Sak** | **41** | **35%** |

### 🏆 Top Targets (No Website, Highest Rated)

| Business | ⭐ | Category | Phone |
|----------|---|----------|-------|
| Tom Winters Barbers | 4.9 | Barbers | 083 091 4263 |
| Keith's Barbershop | 4.9 | Barbers | — |
| DJ.A Barber | 4.9 | Barbers | 083 436 1401 |
| Mechanical Flow Plumbing | 4.9 | Tradesmen | 083 413 4273 |
| Cafe Jane | 4.8 | Cafe | 021 241 0668 |
| Zizenia | 4.8 | Barbers | 021 422 2828 |
| Bluefig Boutique | 4.7 | Boutique | 021 487 7944 |
| City barbers | 4.7 | Barbers | 089 978 5975 |

### 🔥 Top Social-Only Targets

| Business | ⭐ | Current "Site" | Phone |
|----------|---|----------------|-------|
| HIVE Barbershop | 4.9 | Instagram only | 085 731 0993 |
| Woodview House B&B | 4.9 | Google Sites | 087 133 2740 |
| Coffee Scape | 4.8 | Instagram only | — |
| Bright Side | 4.8 | Instagram only | — |
| St Luke's Barber Shop | 4.8 | Facebook only | 021 241 1689 |

### 🤯 Key Insight: Barbers Cork

**13 of 19** zero-website businesses are barbershops. Average rating **4.7★**. Zero digital presence. Huge gap.

**📄 File:** `house-of-sak/cork-business-web-scan.md`

---

## 3. 🧩 REUSABLE FRAMEWORK

**Skill created:** `house-of-sak-qa-shield`

A 4-step executable audit framework that any agent can run:

```
Step 1 — Recon: 5 parallel curl/python3 commands (DNS, headers, meta, robots, emails)
Step 2 — Speed: load times across pages, image format check
Step 3 — Content: scrape key pages for placeholder content
Step 4 — Compile: fill report template with findings
```

**Template:** `house-of-sak/qa-shield-report-template.md` — 10-section markdown report

### Cross-Platform Pitfalls (from today's work)

| Platform | Sites Audited | Common Gaps |
|----------|-------------|-------------|
| **Webflow** | Aitheon | OG image, JSON-LD, security headers, favicon |
| **Webnode** | Bia Beirut | Placeholder emails, social links to platform, no cache |
| **Webador** | Cobh Print | Lapses/suspension, no custom email, minimal SEO |

---

## 4. 🎯 KEY LEARNINGS & NEXT STEPS

### What We Learned Today
1. **35% of Cork small businesses have no real website** — massive market
2. **Barbershops** are the most underserved category (13 of 19 zero-website)
3. **Web platform gaps are predictable** — same issues across Webflow/Webnode/Webador
4. **Cobh Print is a partnership goldmine** — not a client, a referral partner
5. **The QA Shield skill works** — full Trust Check in under 2 minutes per site

### Suggested Next Actions
1. [ ] Pick first outreach target and draft DM
2. [ ] Run Trust Checks on top barbershop targets
3. [ ] Draft Cobh Print partnership proposal
4. [ ] Build Social Pulse plan for Bia Beirut
5. [ ] Create a Cork Business Directory spreadsheet from scan data

---

---

## 5. 🎓 STUDENT STARTER KIT — New Offering

*Created after the main research session — additional offering for Cork student market.*

### Market Size
| University | Students |
|-----------|----------|
| UCC | 26,066 |
| MTU (Cork+Kerry) | 18,000+ |
| **Total Cork students** | **~44,000+** |

### The Offer — Student Starter Kit

| Tier | Price | What They Get |
|------|-------|--------------|
| **Starter** | €29 one-time | Portfolio site + brand kit + 1yr hosting |
| **Pro** | €79 one-time | Full kit + LinkedIn + CV + side project + unlimited revisions |
| **Partnership** | Bulk/Free | UCC/MTU career offices & incubators |

### What's Inside (Pro Kit)
1. Portfolio website (multi-page, recruiter-ready)
2. Personal brand kit (colours, fonts, banners)
3. LinkedIn optimisation (headline, about, banner)
4. Side project landing page (for Ignite/LEO pitches)
5. CV site + downloadable PDF
6. Free hosting for 1 year
7. Real human support on Telegram

### Why Students Need Us
- AI builders are generic (SitesPlaced, Killer, Grigora)
- Agencies are too expensive (Web Wizard, CEVEW = €€€)
- DIY tools leave them alone (Web60, Wix)
- **We're the middle: affordable + human + Cork-local**

### Revenue Projection (Conservative)
At 1% of 44,000 students = 880 students:
- Starter (440 × €29) = €12,760
- Pro (440 × €79) = €34,760
- **Total: ~€47,520**

### Files
- `house-of-sak/student-starter-kit.html` — Full rendered landing page
- `house-of-sak/student-starter-kit-offer.md` — Markdown offer summary

---

*All files live at `house-of-sak/` directory shared between agents. Full inventory:*

| File | What It Is |
|------|-----------|
| `master-report-for-saksee.md` | ★ **This file — start here** |
| `cork-outreach-candidates.md` | Initial deep research on 3 candidates |
| `aitheon-trust-check-report.md` | Case study 1 (Webflow) |
| `bia-beirut-trust-check-report.md` | Case study 2 (Webnode) |
| `cobh-print-trust-check-report.md` | Case study 3 (Webador — suspended) |
| `cork-business-web-scan.md` | 118 Cork businesses scanned |
| `qa-shield-report-template.md` | Reusable 10-section report template |
| `student-starter-kit.html` | 🆕 Student Starter Kit landing page |
| `student-starter-kit-offer.md` | 🆕 Student offer summary |