# 🔍 QA Shield Report: Bia Beirut (biabeirut.ie)

**Client:** Bia Beirut — Lebanese-Irish Family Food Business
**Date:** July 5, 2026
**Analyst:** SakTan · House of Sak
**Status:** Case Study #2 — Full Audit

---

## 📋 Executive Summary

Bia Beirut has the most **authentic story** of the three candidates — a Lebanese-Irish couple bringing Beirut to Cork. Their Webnode-built site has content across 20+ pages and a solid favicon/X-Frame-Options security. But it's plagued by placeholder content, missing OG images, no SEO structure, and social links pointing to the platform rather than their own profiles. The upside: everything is fixable with 2-3 hours of work.

---

## ⚠️ Critical Issues

| # | Issue | Severity | Fix Time |
|---|-------|----------|----------|
| 1 | **`contact@example.com` placeholder email still on site** | 🔴 Critical | 5 mins |
| 2 | **Missing OG image** — blank cards on social shares | 🔴 Critical | 5 mins |
| 3 | **No structured data (JSON-LD)** — no rich search results | 🔴 Critical | 15 mins |
| 4 | **Social links point to Webnode, not Bia Beirut's profiles** (FB/IG link to Webnode's accounts) | 🟡 High | 15 mins |
| 5 | **No caching** (cache-control: no-store) — repeat visitors load from scratch | 🟡 Medium | Server config |
| 6 | **20+ pages but no clear product hierarchy** — copy-of-copy pages | 🟢 Low | Consolidation |

---

## ⚡ Performance

| Page | Load Time | Size |
|------|-----------|------|
| Home (/) | 0.14s | 86KB |
| Our Story (/our-story/) | 0.16s | 63KB |
| Products (/products/) | 0.16s | 69KB |
| Where to Find Us (/where-to-find-us/) | 0.15s | 64KB |

**Verdict:** Decent for a Webnode site. Not Cloudflare-fast but acceptable.

### Optimization Opportunities
- [x] Favicon present ✅
- [ ] Enable caching for repeat visitors (currently nocache)
- [ ] Consolidate 20+ pages — several are "copy-of-copy-of" duplicates
- [ ] Consider Cloudflare CDN for performance + security

---

## 🛠️ Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| **Platform** | Webnode (webnode.io) | PHP-based, Czech builder |
| **Server** | Nginx + PHP-FPM | Cookies: PHPSESSID |
| **CDN** | None | Direct server, no caching |
| **Analytics** | Not detected | |
| **JS Framework** | Vanilla JS + Webnode bundles | Container-query polyfill |
| **SSL** | ✅ Valid, HTTP → HTTPS | |
| **X-Frame-Options** | ✅ DENY | Good |
| **HSTS** | ❌ Missing | |

---

## 🔒 Security

| Header | Status | Risk |
|--------|--------|------|
| `X-Frame-Options` | ✅ DENY | Good |
| `Strict-Transport-Security` | ❌ Missing | 🔴 |
| `Content-Security-Policy` | ❌ Missing | 🟡 |
| `X-Content-Type-Options` | ❌ Missing | 🟡 |
| `Referrer-Policy` | ❌ Missing | 🟢 |

**Good:** X-Frame-Options DENY shows the owner (or Webnode) cares about clickjacking.
**Missing:** HSTS is concerning — all traffic relies on the redirect working.

---

## 📱 SEO Audit

| Check | Status | Notes |
|-------|--------|-------|
| Meta Description | ✅ | Present |
| OG Tags (title, desc) | ✅ | Present |
| **OG Image** | ❌ **Missing** | Blank cards on shares |
| Twitter Card | ❌ Missing | |
| Structured Data | ❌ **Missing** | No schema/JSON-LD |
| Sitemap | ✅ | 28 pages listed |
| Robots.txt | ✅ | Has crawl-delay: 10 |
| Custom Favicon | ✅ | Present |
| Duplicate Pages | ⚠️ | Several "copy-of" pages |

**Sitemap issues:** 28 pages in the sitemap, but many are obvious duplicates/copies — `/copy-of-sourdough-bread/`, `/copy-of-sourdough-bread-1/` through `-4/`, `/services2/`. This hurts crawl efficiency.

---

## 📱 Social Media

| Platform | Status | What We Found |
|----------|--------|---------------|
| **Facebook** | ⚠️ Points to Webnode's page, not theirs | `facebook.com/share/...` — generic share, not a Page |
| **Instagram** | ⚠️ Points to @webnode_ag | Template default, not actual account |
| **TikTok** | ✅ **@bia.beirut** | Active, real account with content |
| **LinkedIn** | ❌ Missing | |

---

## 📊 Missing Features (Growth Opportunities)

| Missing | Why It Matters |
|---------|---------------|
| **Proper social links** | Current links go to Webnode's accounts, not theirs |
| **Brand OG image** | Every link shared on social is blank |
| **Product hierarchy** | 4 identical "copy-of" sourdough bread pages confuse navigation |
| **Blog / recipes** | Perfect for a food business — could rank for Lebanese recipes |
| **Online ordering** | They have a "Click & Collect" page — huge opportunity |
| **Caching** | Repeat visitors download everything fresh |

---

## 🏆 House of Sak Opportunity Map

| Service | What We'd Do | Impact |
|---------|-------------|--------|
| **QA Shield** 🔥 | Fix placeholder email, OG image, JSON-LD, social links | 🚀 **Quick wins — fix credibility overnight** |
| **Social Pulse** | Set up Instagram for food content, unlink from Webnode defaults | 🚀 **They already have TikTok — need consistent IG** |
| **Fast Prototype** | Rebuild on a modern platform (Webflow?), consolidate pages | 🟡 **Medium — their current site works, just messy** |
| **Agent Builder** | FAQ chatbot about products, ordering, farmers market times | 🟢 **Nice-to-have during market hours** |

---

## ✅ Quick Wins (< 1 Hour Each)

1. [ ] **Remove `contact@example.com`** — replace with info@biabeirut.ie
2. [ ] **Add OG image** — use a hero photo of their spreads/breads
3. [ ] **Add JSON-LD schema** — FoodBusiness markup
4. [ ] **Fix social links** — link to their real TikTok + set up a proper Facebook Page
5. [ ] **Delete duplicate "copy-of" pages** — consolidate into a clean Products page

---

*Generated by SakTan · House of Sak — QA Shield Framework v1.0*