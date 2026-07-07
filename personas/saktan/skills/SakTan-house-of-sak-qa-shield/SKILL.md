---
name: SakTan-house-of-sak-qa-shield
description: "Full Trust Check / QA Shield audit framework for House of Sak. Run parallel checks on any website: tech stack, performance, security headers, SEO, accessibility, social presence, and content quality. Produces a structured report template."
---

# House of Sak — QA Shield / Trust Check Framework

A tested, repeatable process for auditing any business website as part of House of
Sak outreach. Born from the **aitheon.ie** case study (July 5, 2026).

---

## Prerequisites

- Terminal access (curl, python3, dig if available)
- Target website URL
- `house-of-sak-report/` directory exists under project root

---

## Step 0: Prospecting — Finding Who Needs Us

Before auditing a single site, find the businesses that actually need what we do. Use Google Maps Search + Yelp to discover candidates, then classify their web presence.

### 0.1 — Category-based Google Maps sweep

Query multiple business categories in your target area. Batch 6 categories at once using COMPOSIO_MULTI_EXECUTE_TOOL with COMPOSIO_SEARCH_GOOGLE_MAPS:

```
"restaurants and cafes in [City] [Country]"
"hair salons and barbers in [City] [Country]"
"independent shops and boutiques in [City] [Country]"
"plumbers electricians tradesmen in [City] [Country]"
"fitness gyms yoga studios in [City] [Country]"
"hotels B&Bs accommodation in [City] [Country]"
```

### 0.2 — Classify web presence

For each business returned, classify their `website` field:

| Classification | Meaning | Priority |
|---------------|---------|----------|
| **none** | No website field at all | 🔴 High |
| **facebook_only** | Website is a Facebook page URL | 🟡 Medium |
| **instagram_only** | Website is an Instagram URL | 🟡 Medium |
| **booking_app** | Square, Booksy, Nearcut, etc. | 🟡 Medium |
| **booking_site** | Booking.com, hotelb1, Kross.travel | 🟡 Medium |
| **url_shortener** | shorturl.at, bit.ly (suspect) | 🟡 Medium |
| **google_site** | sites.google.com | 🟡 Medium |
| **review_site** | travelreview.io, etc. | 🟢 Low |
| **chain_brand** | Large national chain, not local | 🟢 Ignore |
| **proper_site** | Real custom domain with content | ✅ Skip |

Use a Python helper in COMPOSIO_REMOTE_WORKBENCH to classify at scale — check domain against known platform keywords.

### 0.3 — Output candidate list

Compile high+medium priority candidates into a lead table: business name, category, phone, address, rating, reviews, current web presence type.

### 0.4 — Key prospecting insight: barbershops

From the Cork 118-business scan (July 2026): **13 of 19** zero-website businesses were barbershops. Average rating **4.7★**. This pattern repeats in most local markets — trades that run on word-of-mouth are the most underserved.

---

## Step 1: Initial Recon (Parallel — 5 commands)

Run these in one terminal batch call for maximum speed:

### 1.1 — HTTP status + redirect + server
```bash
curl -s -o /dev/null -w "%{http_code} %{redirect_url} %{url_effective} %{content_type}\n" "https://$TARGET"
```

### 1.2 — SSL + Security headers
```bash
curl -sI "https://$TARGET" | grep -iE 'strict-transport|content-security|x-frame|x-content|x-xss|referrer|permissions|cache'
```

### 1.3 — Meta extraction from source
```bash
curl -s "https://$TARGET" | python3 -c "
import sys, re
html = sys.stdin.read()
for m in re.findall(r'<meta[^>]+>', html): print(m.group())
h1s = re.findall(r'<h1[^>]*>(.*?)</h1>', html, re.DOTALL)
for h in h1s: print('H1:', re.sub(r'<[^>]+>','',h).strip())
print('og:image:', bool(re.search(r'og:image', html)))
print('twitter:image:', bool(re.search(r'twitter:image', html)))
ld = re.findall(r'type=\"application/ld\+json\"[^>]*>(.*?)</script>', html, re.DOTALL)
print('JSON-LD count:', len(ld))
print('Lorem ipsum:', 'FOUND' if re.search(r'Lorem\s+ipsum', html, re.I) else 'None')
styles = re.findall(r'<style[^>]*>(.*?)</style>', html, re.DOTALL)
print(f'Inline CSS: {sum(len(s) for s in styles)} chars')
print(f'HTML size: {len(html)} bytes')
"
```

### 1.4 — Robots + Sitemap
```bash
curl -s "https://$TARGET/robots.txt" | head -20
curl -s "https://$TARGET/sitemap.xml" | head -40
```

### 1.5 — Email + Social links
```bash
curl -s "https://$TARGET" | python3 -c "
import sys, re
html = sys.stdin.read()
emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', html)
print('Emails:', set(emails))
socials = re.findall(r'(linkedin\.com|twitter\.com|x\.com|facebook\.com|instagram\.com|github\.com)[^\"\'< ]+', html)
print('Social links:', set(socials))
"
```

---

## Step 2: Speed & Performance

### 2.1 — Load times across pages
```bash
for url in https://\$TARGET/ https://\$TARGET/about https://\$TARGET/contact; do
  echo -n "\$url -> "
  curl -s -o /dev/null -w "Time: %{time_total}s, Size: %{size_download}bytes\n" "\$url"
done
```

### 2.2 — Image optimization check
```bash
curl -s "https://\$TARGET" | python3 -c "
import sys, re
html = sys.stdin.read()
imgs = re.findall(r'<img[^>]+src=\"([^\"]+)\"', html)
for img in imgs:
    tag = 'WebP/AVIF' if '.webp' in img or '.avif' in img else 'May optimize'
    print(f'{tag}: {img[:80]}')
"
```

---

## Step 3: Content & Pages

```bash
for page in / /about /pricing /contact /how-it-works /services; do
  echo "=== \$page ==="
  curl -s "https://\$TARGET\$page" | python3 -c "
import sys, re
html = sys.stdin.read()
text = re.sub(r'<[^>]+>', ' ', html)
text = re.sub(r'\s+', ' ', text).strip()
print(text[:300])
"
done
```

---

## Step 4: Compile the Report

Fill in the template at `house-of-sak-report/qa-shield-report-template.md` with:

1. **Executive Summary** — 3-line overview
2. **Critical Issues** — Table: severity, finding, fix time
3. **Performance** — Load times, image optimization, JS/CSS size
4. **Tech Stack** — Platform, CDN, analytics, frameworks
5. **Security Headers** — Check each header, flag missing
6. **SEO Audit** — Meta tags, OG, schema, sitemap, robots, favicon
7. **Accessibility** — Preliminary check
8. **Missing Features** — Case studies, blog, social links, chat
9. **Opportunity Map** — Which House of Sak services fit best
10. **Quick Wins** — 5 things they can fix in 1 hour

---

## Pitfalls

- **Google PageSpeed API** has daily quota — don't rely on it
- **dig** not always available on host — skip DNS checks
- **wappalyzer/builtwith** likely not installed — use source analysis
- **LinkedIn** returns HTTP 999 (rate-limited) — not a failure signal
- **Webflow sites** — always have CF cache, jQuery bundles, no CSP by default
- **Webnode sites** (biabeirut.ie) — PHP-based, PHPSESSID cookies, no caching, often have platform-default social links and placeholder emails
- **Webador sites** (cobhprintandmarketing.com) — free-tier builder, sites often suspended/lapsed, common for very small businesses
- Always check for **Lorem ipsum** — more common than you'd think
- Always check for **contact@example.com** — placeholder email left on live site
- **HTTP 451** means the page is unavailable (suspended/blocked) — don't retry, report it
- **Non-www vs www** — some sites only work on the www subdomain; always test both
- **Platform-default social links** — Webnode/Webador sites often have links pointing to the platform's own social accounts, not the client's
- **"copy-of" pages in sitemap** — common in builder sites where users duplicate pages instead of organizing

## Cross-Platform Reference

| Platform | Typical Tech | Common Gaps |
|----------|-------------|-------------|
| **Webflow** | Cloudflare CDN, AWS Lambda, jQuery, GA4 | OG image, JSON-LD, security headers, favicon |
| **Webnode** | PHP, Nginx, PHPSESSID, no CDN | Placeholder content, platform social links, no caching, no HSTS |
| **Webador** | Nginx, Lite plan, free domain | Frequent lapses/suspension, no custom email, minimal SEO |

---

## Verification

After writing the report, confirm:
- [ ] Critical issues section has severity labels
- [ ] Opportunity map links to House of Sak services
- [ ] Quick wins are actionable (< 1 hour each)
- [ ] Report saved to `house-of-sak-report/` directory

---

## Cross-Agent Handoff

When another sibling agent (SakSee, SakSit, SakJules) needs context from this session:

1. **Compile a master report** — `house-of-sak-report/master-report-for-[agent].md`
   - Concatenate summaries of all case studies this session
   - Include web presence breakdown stats
   - Link to individual report files for depth

2. **Save to shared filesystem** — the `house-of-sak-report/` directory is accessible by all agents on the same host. No cross-agent messaging tools exist — file handoff is the pattern.

3. **Signal completion** — tell the user the file is ready. They forward the signal to the target agent.

Master report structure:
- Executive summary of the session
- Each case study: 5-line summary, critical findings, quick wins
- Any market scan data
- Reusable assets created (skills, templates)
- Suggested next actions

---

## Reference Files

This skill includes reference data from real Cork market scans:

| File | Content |
|------|---------|
| `references/cork-market-scan-2026-07.md` | 118-business scan by category — phone, rating, web presence for every lead |
| `references/student-market-research.md` | Cork student market size, competition analysis, Student Starter Kit offer |

See these for example output format and real market data.

---

## Workflow Insights (from session on 2026-07-05)

1. **"Process" means execute immediately** — when the user says "yes process" or "process", they want action, not more questions. Skip the confirmation loop and go.
2. **Webflow sites** — fast but miss OG images, schema, security headers, favicon. Low-hanging fruit.
3. **Tech startups** have pricing pages worth scraping — reveals their budget tier.
4. **Lorem ipsum** on live pages is embarrassingly common — easy win.
5. **Parallel terminal calls** = full recon in <30 seconds.
6. **Opportunity map** is the most valuable section — bridges audit to pitch.
7. **Barbershops** are the single most underserved category in any local market.
8. **Cross-agent handoff** works via shared filesystem + master report compilation — not messaging tools.