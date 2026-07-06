# 🔍 QA Shield Report: Aitheon (aitheon.ie)

**Client:** Aitheon — AI Predictive Maintenance
**Date:** July 5, 2026
**Analyst:** SakTan · House of Sak
**Status:** Case Study #1 — Full Audit

---

## 📋 Executive Summary

Aitheon is a promising Cork-based AI startup. Their Webflow site is fast, clean, and well-structured — but misses several critical elements that cost them trust, leads, and organic visibility. Below is every finding, ranked by impact.

---

## ⚠️ Critical Issues

### 1. Lorem Ipsum Placeholder on Live Site
**Found on:** `/about-us` page
**Impact:** ❌ **High** — This is the first thing potential clients see when learning about Aitheon. Placeholder text signals "unfinished business" and kills credibility.

```
Lorem ipsum dolor sit amet, consectetur adipiscing elit,
sed do eiusmod tempor incididunt...
```

**Fix:** Replace with actual content about the team's mission, values, and founding story.

### 2. Missing OpenGraph Image
**Impact:** ❌ **High** — When someone shares an Aitheon link on LinkedIn, Twitter, WhatsApp, or Slack — **no image appears**. Just a blank card.

**Fix:** Add `og:image` and `twitter:image` meta tags pointing to the existing hero image (or a branded share card).

### 3. No Structured Data (JSON-LD / Schema.org)
**Impact:** ❌ **High** — No schema markup means Google can't show rich results (star ratings, pricing, FAQ snippets, corporate info) in search.

**Fix:** Add `Organization` + `Product` schema with pricing data, and FAQ schema for the `/pricing` page Q&A section (already exists as plain text!).

### 4. Missing Critical Security Headers
| Header | Status | Risk |
|--------|--------|------|
| `Strict-Transport-Security` | ✅ max-age=31536000 | Good |
| `X-Frame-Options` | ❌ Missing | **Clickjacking risk** |
| `X-Content-Type-Options` | ❌ Missing | **MIME-sniffing risk** |
| `Content-Security-Policy` | ❌ Missing | **XSS risk** |
| `Referrer-Policy` | ❌ Missing | **Info leakage risk** |
| `Permissions-Policy` | ❌ Missing | **Feature abuse risk** |

For a company selling AI-powered industrial safety, having missing security headers is a credibility gap.

---

## ⚡ Performance

Thanks to Cloudflare CDN, the site is **fast**:

| Page | Load Time | Size |
|------|-----------|------|
| Home (/) | 0.05s | 39KB |
| About (/about-us) | 0.07s | 25KB |
| Pricing (/pricing) | 0.05s | 41KB |
| Contact (/contact-us) | 0.04s | 24KB |

**Note:** Google PageSpeed API daily quota was exceeded — cannot give Lighthouse scores programmatically. Recommended: run `pagespeed.web.dev` manually for mobile + desktop scores.

### Optimization Opportunities:
- **No critical CSS inlined** (only 119 chars inline) → First paint waits for CSS bundles
- **jQuery 3.5.1 CDN** — adds 87KB to every page load. Modern vanilla JS would be faster
- **7 JS bundle files** from Webflow — consolidation could reduce round-trips
- **Images use WebP/AVIF** ✅ via Webflow's CDN — good

---

## 🛠️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Platform** | Webflow | Visual builder, AWS Lambda hosting |
| **CDN** | Cloudflare | DDoS protection, SSL termination, caching |
| **Analytics** | Google Analytics 4 (G-HGBJ6EMFX8) | Standard setup |
| **JS Framework** | jQuery 3.5.1 | Outdated — replace with vanilla JS |
| **Webflow JS** | v6.6.617 | Schunk framework (4 chunks) |
| **SSL** | ✅ Valid, HTTPS forced, HSTS enabled |
| **Images** | WebP / AVIF via Webflow CDN ✅ |

### Pricing Structure (scraped)
| Plan | Price | Coverage |
|------|-------|----------|
| Free Trial | Free | 1 machine, 30 days |
| Starter | €60–180/machine/month | Up to 5 machines |
| Business | €75–200/machine/month | Up to 15 machines |
| Enterprise | Custom | Unlimited machines |
| Maritime | Custom | Ships, tankers, vessels |

**Contact:** `info@aitheon.ie` • `+353 89 238 4071`

---

## 📱 SEO Audit

| Check | Status | Notes |
|-------|--------|-------|
| Meta Description | ✅ | "Aitheon helps manufacturers prevent machine breakdowns..." |
| OG Tags (title, desc) | ✅ | Present |
| OG Image | ❌ **Missing** | Blank cards on social shares |
| Twitter Card | ✅ | summary_large_image |
| Structured Data | ❌ **Missing** | No schema.org/JSON-LD |
| Sitemap.xml | ✅ | 8 pages listed |
| Robots.txt | ✅ | Points to sitemap |
| Google Search Console | ✅ | Verified |
| Custom Favicon | ❌ **Missing** | Using Webflow defaults |
| Canonical URLs | ✅ | Likely set by Webflow |
| H1 Tags | ✅ | One per page with clear value props |

---

## ♿ Accessibility Check

(Full check requires browser tools — preliminary findings based on source analysis)

| Check | Verdict |
|-------|---------|
| Viewport meta tag | ✅ Present |
| Alt text on images | ⚠️ Not verified per-image |
| Color contrast | ⚠️ Cannot check programmatically |
| ARIA landmarks | ⚠️ Webflow default (limited) |
| Tab order | ⚠️ Cannot check programmatically |
| Skip navigation | ❌ Likely missing |

**Recommendation:** Run a WAVE or axe DevTools audit manually.

---

## 📊 Missing Features (Growth Opportunities)

| What's Missing | Why It Matters |
|----------------|---------------|
| **Case studies / testimonials** | No social proof — visitors can't see who already uses Aitheon |
| **Blog / content section** | No SEO content to attract organic traffic for "predictive maintenance Ireland" |
| **Social media links** | No LinkedIn, Twitter, or Instagram anywhere on the site |
| **Live chat / chatbot** | No instant engagement — interested visitors must fill a form and wait |
| **Video / explainer** | No product demo or walkthrough for a technical product |

---

## 🏆 Opportunities to Help Aitheon

Based on the Trust Check, here's where House of Sak could step in:

| Service | What We'd Do | Impact |
|---------|-------------|--------|
| **QA Shield** | Fix structured data, OG image, security headers, lorem ipsum | 🚀 High — quick wins that build trust immediately |
| **Agent Builder** | Live chat AI assistant for pricing/FAQ questions (they already have an FAQ section) | 🚀 High — answer customer questions 24/7 |
| **Security Audit** | Full security headers configuration, CSP setup | 🟡 Medium — important for an IoT/AI company |
| **Social Pulse** | Set up LinkedIn presence, blog content for SEO | 🟢 Long-term growth |

---

## ✅ Quick Wins (Can Fix in 1 Hour)

1. **Remove lorem ipsum** from the about page → Replace with real text
2. **Add og:image** meta tag → Use existing hero image
3. **Add JSON-LD schema** → Organization + Product + FAQ
4. **Add missing security headers** → X-Frame-Options, X-Content-Type-Options
5. **Upload custom favicon** → Brand it

---

*Generated by SakTan · House of Sak — Trust Check Framework v1.0*