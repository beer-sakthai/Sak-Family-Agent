---
name: SakSee-business-landing-page
description: "Transform a business repo (README, services, pricing, docs) into a polished, story-driven single-page HTML landing site with nav, animations, trust signals, and CTA."
---

# Business Landing Page

## Overview

Use this skill when the user wants to turn a business/info repo — README, services docs, pricing table, crisis/info docs — into a **single, polished, production-ready HTML landing page**. This is NOT a throwaway mockup (use `sketch` for that). This is the page you put live.

## When to Use

- The user says "polish the house of sak page" or "make a landing page for my business"
- You have a repo full of markdown docs (README, SERVICES.md, pricing, crisis info)
- The user needs a single HTML file they can deploy immediately
- Content exists but needs to become a cohesive web presence

## When NOT to Use

- User wants 2-3 variants to compare — use `sketch`
- User wants a design-only artifact without production concerns — use `claude-design`
- User wants a diagram or infographic — use `excalidraw` or `architecture-diagram`
- User wants a full multi-page site with backend — this is single-page only

## Core Method

### 1. Intake — Read the Source Material

Read every relevant file in the business repo:

```
read_file("path/to/README.md")
read_file("path/to/SERVICES.md")   # pricing, packages
read_file("path/to/PLAN.md")       # business strategy
read_file("path/to/CRISIS.md")     # emergency info
read_file("path/to/ABOUT.md")      # founder story
```

Extract:
- **Brand identity**: name, tagline, tone, colors if specified
- **Origin story**: the founder's narrative — this is your emotional hook
- **The team/agents**: who delivers — each needs a name, role, emoji
- **Services**: package name, description, price range, delivery time, what's included/not
- **Process**: how clients engage (inquiry → quote → build → deliver → pay)
- **Trust signals**: crisis info, testimonials, social proof
- **CTA channels**: Telegram, Instagram, LinkedIn, email — how clients reach you

### 2. Structure the Page Sections

Standard structure (adjust based on what the repo has). When services carry significant detail (features, use cases, deliverables), prefer the expanded pattern:

```
1. NAV          — Sticky bar: links to each section + CTA button
2. HERO         — Tagline, headline, badge ("X agents online"), CTA buttons
3. STORY        — Origin narrative with stat cards (numbers that impress)
4. AGENTS/TEAM  — Grid of who delivers (name, role, emoji, description)
5. PROCESS      — "How It Works" steps (3-4 steps)
6. WHY US       — Optional trust section: 6 cards about values (pay-after-delivery, no jargon, etc.)
7. SERVICES     — Pricing grid with price ranges, agent attribution, feature lists
8. FAQ          — Optional accordion: common questions about process, pricing, trust
9. TESTIMONIAL  — Quote section (founder quote or client placeholder)
10. CTA/CONTACT — Channel cards (Telegram, Instagram, LinkedIn)
11. FOOTER      — Attribution + crisis/emergency numbers (if applicable)
```

### 3. Design Patterns

**Color scheme:**
- Dark theme (`#0a0a0b` bg, `#e8e8ed` text) works for tech/agent stories
- Use a single accent color (purple `#8b5cf6`, cyan `#06b6d4`, green `#22c55e`)
- Subtle grid background via `body::before` with 3% opacity accent lines
- Surface/raised cards at `#121214` and `#1a1a1e`

**Typography:**
- Headings: `Inter` at 800 weight, tight tracking (`letter-spacing: -3px`)
- Body: `Inter` at 400 weight
- Prices/metrics: `JetBrains Mono` monospace for credibility
- Import: `@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');`

**Animations:**
- Scroll-reveal with IntersectionObserver (0-dependency, lightweight)
- Card hover lifts (`translateY(-4px)`) + border accent
- Hero badge pulsing dot
- Scroll hint at bottom of hero (optional)

**Responsive breakpoints:**
- `@media (max-width: 768px)`: single-column grids, smaller headings, hamburger nav
- `@media (max-width: 480px)`: stacked CTAs, single-column stats

**Content Strategy:**
- Showcase authentic origin stories to build emotional connection
- Feature case studies and reports for social proof
- Link to detailed documentation for transparency
- Include methodology explanations to build trust

### 4. Polish Checklist

- [ ] **Sticky nav** with smooth scroll (`html { scroll-behavior: smooth }`), closed on mobile link click
- [ ] **Hamburger menu** for mobile (toggle class `open` on nav-links)
- [ ] **OG meta tags** (og:title, og:description, og:type, og:url) + Twitter card
- [ ] **Favicon** via SVG data URI (`data:image/svg+xml,...`)
- [ ] **Scroll-reveal** — every section gets `class="reveal"`, IntersectionObserver adds `class="visible"`
- [ ] **Stat cards** with auto-calculated day counter (e.g. "82 Days Since April 15")
- [ ] **Service cards** with "powered by AgentName" attribution line
- [ ] **Bundle/highlight card** with accent border and gradient background
- [ ] **Expanded service cards** (Pattern B): feature lists, use-case box, deliverable line, per-service CTA
- [ ] **"Why Us" trust section** — 6 cards covering: pay-after-delivery, AI+human, no jargon, small biz focus, fast iteration, pricing for people who struggle
- [ ] **FAQ accordion** with toggle function — 6-8 questions covering pay process, revisions, agents, communication, examples, international, custom projects, origin story
- [ ] **CTA section** with clickable channel cards (Telegram, Instagram, LinkedIn)
- [ ] **"No upfront payment" badge** — repeated in process step 4, services section footer, and CTA
- [ ] **Crisis footer** (optional, for mental-health-adjacent businesses): emergency numbers in red-bordered container

### 5. Pricing Display Patterns

Two patterns depending on how much detail each service has.

**Pattern A — Compact (3+ per row, minimal info per card):**

```html
<div class="service-card">
  <span class="icon">🛡️</span>
  <h3>Service Name</h3>
  <p>Short description of what's included and who it's for.</p>
  <span class="price">€200–€500</span>
  <span class="price-note">per project · 3–7 days</span>
  <div class="powered-by">powered by <span>AgentName</span></div>
</div>
```

Bundle card gets `service-highlight` class with accent border + subtle gradient.

**Pattern B — Expanded (two-column: details + pricing sidebar) — use when each service has feature lists, use cases, deliverables:**

```html
<div class="service-card">
  <div class="left-col">
    <span class="icon">🛡️</span>
    <h3>Service Name — Tagline</h3>
    <div class="tag">Powered by AgentName</div>
    <p class="description">2-3 sentence overview of what the service delivers and who it helps.</p>

    <div class="use-case">
      <strong>Perfect for:</strong> Comma-separated list of use cases (e.g. Small e-commerce stores, SaaS dashboards, booking platforms)
    </div>

    <ul class="features">
      <li>Feature bullet 1 — actionable, specific</li>
      <li>Feature bullet 2</li>
      <li>Feature bullet 3</li>
      <li>Feature bullet 4</li>
      <li>Feature bullet 5</li>
      <li>Feature bullet 6</li>
    </ul>

    <p class="description"><strong>Deliverable:</strong> What the client receives at the end — specific and concrete.</p>
  </div>
  <div class="right-col">
    <div class="price">€200–€500</div>
    <span class="price-note">per project</span>
    <div class="delivery">
      <div class="label">Delivery</div>
      <div class="value">3–7 days</div>
    </div>
    <div class="powered-by">powered by <span>AgentName</span></div>
    <a href="#contact" class="cta-service">Book a Free Scope</a>
  </div>
</div>
```

**Extended CSS for Pattern B:**

```css
.service-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 40px;
  margin-bottom: 32px;
  transition: all 0.2s;
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 32px;
  align-items: start;
}
.service-card:hover { border-color: var(--accent); }

.service-card .tag {
  display: inline-block; font-size: 12px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 1px; color: var(--accent);
  margin-bottom: 12px;
}
.service-card .description {
  font-size: 14px; color: var(--text2); line-height: 1.7; margin-bottom: 20px;
}
.service-card .features { list-style: none; margin-bottom: 20px; }
.service-card .features li {
  font-size: 14px; color: var(--text2); padding: 4px 0;
  display: flex; align-items: flex-start; gap: 10px;
}
.service-card .features li::before {
  content: "\2192"; color: var(--accent); font-weight: 600; flex-shrink: 0;
}
.service-card .use-case {
  font-size: 13px; color: var(--text2); opacity: 0.8;
  padding: 12px 16px; background: var(--bg);
  border-radius: 10px; border: 1px solid var(--border); margin-bottom: 16px;
}
.service-card .right-col {
  background: var(--bg); border: 1px solid var(--border);
  border-radius: 16px; padding: 28px; text-align: center;
}
.service-card .delivery {
  margin: 16px 0; padding: 12px 0;
  border-top: 1px solid var(--border); border-bottom: 1px solid var(--border);
}
.service-card .delivery .label {
  font-size: 11px; text-transform: uppercase; letter-spacing: 1px;
  color: var(--text2); opacity: 0.6;
}
.service-card .delivery .value {
  font-family: 'JetBrains Mono', monospace; font-size: 16px; font-weight: 600;
  color: var(--text); margin-top: 4px;
}
.service-card .cta-service {
  display: inline-block; margin-top: 16px; padding: 10px 24px;
  background: var(--accent); color: white; border-radius: 10px;
  font-size: 14px; font-weight: 600; text-decoration: none;
  transition: background 0.2s;
}
.service-card .cta-service:hover { background: var(--accent2); }

@media (max-width: 900px) {
  .service-card { grid-template-columns: 1fr; }
  .service-card .right-col { order: -1; }
}
```

**Deciding which pattern to use:**

| Signal | Use |
|--------|-----|
| 5+ services, minimal one-liner per service | Pattern A (compact grid) |
| 3-6 services, each with distinct features and use cases | Pattern B (expanded two-column) |
| User specifically asks for detailed service info | Pattern B |
| User says "keep it simple" or "just the basics" | Pattern A |

### 6. FAQ Accordion Pattern

When adding an FAQ section, use this accordion pattern. It stays closed by default, opens on click, and auto-closes other items (single-open behavior).

**HTML structure:**

```html
<section class="faq-section" id="faq">
  <div class="container">
    <h2 class="reveal">Frequently Asked Questions</h2>
    <p class="subtitle reveal">Subtitle text.</p>
    <div class="faq-list">
      <div class="faq-item reveal">
        <button class="faq-question" onclick="toggleFaq(this)">
          Question text?
          <span class="arrow">▾</span>
        </button>
        <div class="faq-answer">Answer paragraph. Links and formatting supported.</div>
      </div>
      <!-- Repeat for each question -->
    </div>
  </div>
</section>
```

**CSS:**

```css
.faq-section { padding: 120px 0; background: var(--surface); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
.faq-section h2 { font-size: 42px; font-weight: 700; letter-spacing: -1.5px; margin-bottom: 16px; }
.faq-section .subtitle { color: var(--text2); font-size: 18px; margin-bottom: 64px; }
.faq-list { max-width: 800px; margin: 0 auto; display: flex; flex-direction: column; gap: 12px; }
.faq-item { background: var(--bg); border: 1px solid var(--border); border-radius: 14px; overflow: hidden; transition: border-color 0.2s; }
.faq-item:hover, .faq-item.open { border-color: var(--accent); }
.faq-question {
  width: 100%; padding: 20px 24px; background: none; border: none;
  color: var(--text); font-size: 16px; font-weight: 500; font-family: inherit;
  text-align: left; cursor: pointer; display: flex;
  justify-content: space-between; align-items: center; gap: 16px;
}
.faq-question .arrow { transition: transform 0.3s; font-size: 14px; color: var(--text2); flex-shrink: 0; }
.faq-item.open .faq-question .arrow { transform: rotate(180deg); }
.faq-answer { max-height: 0; overflow: hidden; transition: max-height 0.3s ease, padding 0.3s ease; padding: 0 24px; font-size: 14px; color: var(--text2); line-height: 1.7; }
.faq-item.open .faq-answer { max-height: 400px; padding: 0 24px 20px; }
```

**JS toggle function:**

```javascript
function toggleFaq(btn) {
  const item = btn.parentElement;
  const isOpen = item.classList.contains('open');
  // close all
  document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
  // open clicked
  if (!isOpen) item.classList.add('open');
}
```

**Standard FAQ topics for a services landing page:**

1. "How does 'pay after delivery' work?" — explain scope → build → inspect → pay
2. "What if I need revisions?" — every service includes revisions, iterative process
3. "Who are the [agents/team]?" — clarify automation vs human oversight
4. "How do I communicate during a project?" — fastest channel, update cadence
5. "Can I see examples of past work?" — link to live sites and open-source repos
6. "Do you work with people outside [country]?" — international, payment methods
7. "What if my project is outside these service descriptions?" — scope custom work
8. "What's the story behind the brand?" — the origin narrative in Q&A form

### 7. Transparent Pricing Breakdown Section

When the user says "tell customers why our prices are this way" or "we should explain our pricing to customers," add a dedicated transparency section after services (before FAQ). This answers the implicit question "why so cheap?" and pre-empts trust objections.

**Placement:** Between the Services section and the FAQ section.

**Section type:** Reuse `why-section` / `why-grid` classes from the "Why Us" pattern.

**Capture pillar pattern** (5-6 cards covering these angles):

| Icon | Title | Message |
|------|-------|---------|
| ⏱ | Time × Complexity | Scope-based pricing — every project is different, quoted after free scope |
| 📊 | Below Agency Rates | 30–50% lower than agency rates due to lean operations |
| 🏠 | No Overhead | No office rent, no employees, no investors — built from shelter |
| 🤖 | Agent Speed | AI agents deliver faster — days instead of weeks, savings passed to client |
| 🎯 | Scoped Per Client | Free scope, firm quote, no hidden fees |
| ❤️ | Built for People Who Struggle | Purpose-driven pricing — not maximising profit |

**Closing line pattern:** "We're not trying to maximise profit. We're trying to prove that people who have nothing can still build something worth paying for."

**HTML example:**
```html
<section class="why-section" id="pricing">
  <div class="container">
    <h2 class="reveal">How We Price</h2>
    <p class="subtitle reveal">Our prices aren't pulled from thin air. Here's exactly what they're based on — because you deserve to know.</p>
    <div class="why-grid">
      <!-- 5-6 why-card items using same .why-card CSS -->
    </div>
  </div>
</section>
```

**CSS:** Reuses `.why-section`, `.why-grid`, `.why-card` — no new styles needed.

### 9. "Why Us" Trust Section Pattern

Place this between Process and Services when the business has strong differentiating values to communicate.

**HTML:**

```html
<section class="why-section" id="why">
  <h2 class="reveal">Why [Brand Name]?</h2>
  <p class="subtitle reveal">One-liner about what makes you different.</p>
  <div class="why-grid">
    <div class="why-card reveal">
      <span class="icon">💰</span>
      <h3>Value 1</h3>
      <p>2-3 line explanation of this value.</p>
    </div>
    <!-- Repeat for 6 cards covering: pay-after-delivery, AI+human approach, no jargon, affordable pricing, fast turnaround, empathy for the target audience -->
  </div>
</section>
```

**CSS:**

```css
.why-section { padding: 120px 0; background: var(--surface); border-top: 1px solid var(--border); border-bottom: 1px solid var(--border); }
### 13. Script (add at end of body)

```javascript
const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));

// Close mobile nav on link click
document.querySelectorAll('.nav-links a').forEach(a => {
  a.addEventListener('click', () => {
    document.querySelector('.nav-links').classList.remove('open');
  });
});

// FAQ toggle function
function toggleFaq(btn) {
  const item = btn.parentElement;
  const isOpen = item.classList.contains('open');
  // close all
  document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
  // open clicked
  if (!isOpen) item.classList.add('open');
}
```

### 14. Showcasing Authentic Content

When the business has authentic stories, case studies, or detailed documentation, consider adding a dedicated section to showcase this content. This builds trust and provides social proof.

**HTML structure for a "Stories & Reports" section:**

```html
<section class="stories-section" id="stories">
  <div class="container">
    <h2 class="reveal">Stories & Reports</h2>
    <p class="subtitle reveal">The origin story behind our work</p>

    <div class="stories-grid">
      <div class="story-card reveal">
        <span class="icon">📖</span>
        <h3>Origin Story</h3>
        <p>Brief description of the story and why it matters.</p>
        <a href="link-to-full-story" target="_blank" rel="noopener" class="btn btn-outline" style="margin-top: 16px;">Read Story</a>
      </div>

      <div class="story-card reveal">
        <span class="icon">📊</span>
        <h3>Case Study</h3>
        <p>Description of the case study and results achieved.</p>
        <a href="link-to-case-study" target="_blank" rel="noopener" class="btn btn-outline" style="margin-top: 16px;">Read Report</a>
      </div>

      <div class="story-card reveal">
        <span class="icon">🔄</span>
        <h3>Methodology</h3>
        <p>Explanation of your approach and why it works.</p>
        <a href="link-to-methodology" class="btn btn-outline" style="margin-top: 16px;">Learn More</a>
      </div>
    </div>

    <div class="reveal" style="text-align:center;margin-top:48px;padding:24px;border:1px solid var(--border);border-radius:16px;background:var(--surface);">
      <p style="color:var(--text2);margin:0;">
        <strong style="color:var(--text);">Radical Transparency:</strong> All our documentation is available in our 
        <a href="link-to-repository" target="_blank" rel="noopener" style="color:var(--accent);">repository</a>. 
        You can see everything we've built and how we've built it.
      </p>
    </div>
  </div>
</section>
```

**CSS for the stories section:**

```css
  /* ── STORIES & REPORTS ── */
  .stories-section {
    padding: 120px 0;
    background: var(--surface);
    border-top: 1px solid var(--border);
    border-bottom: 1px solid var(--border);
  }

  .stories-section h2 {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -1.5px;
    margin-bottom: 16px;
  }

  .stories-section .subtitle {
    color: var(--text2);
    font-size: 18px;
    margin-bottom: 64px;
    text-align: center;
  }

  .stories-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 24px;
    margin-bottom: 48px;
  }

  .story-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 32px;
    transition: all 0.2s;
    text-align: center;
  }

  .story-card:hover {
    border-color: var(--accent);
    transform: translateY(-4px);
  }

  .story-card .icon {
    font-size: 48px;
    margin-bottom: 16px;
    display: block;
  }

  .story-card h3 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 12px;
  }

  .story-card p {
    font-size: 14px;
    color: var(--text2);
    line-height: 1.7;
    margin-bottom: 16px;
  }

  @media (max-width: 768px) {
    .stories-section h2 {
      font-size: 32px;
    }
    
    .stories-grid {
      grid-template-columns: 1fr;
    }
  }
```

**Benefits of showcasing authentic content:**
1. **Builds Trust** - Real stories and case studies demonstrate credibility
2. **Provides Social Proof** - Evidence of actual results achieved
3. **Increases Transparency** - Showing your work builds confidence
4. **Improves SEO** - More content and links improve search visibility
5. **Creates Emotional Connection** - Stories help visitors relate to your brand

### 15. Content Organization

When implementing a Stories & Reports section, organize your content effectively:

**Directory Structure:**
```
diaries/
  _summaries/
    all-reports-summary.md
    stories-and-reports-summary.md
  saksee/
    01-the-day-i-died.md
    02-the-house-of-sak.md
    the-view-from-growth.md
  saktan/
    family-analysis-report.md
    aitheon-trust-check-report.md
    bia-beirut-trust-check-report.md
    cobh-print-trust-check-report.md
```

**Summary Files:**
Create summary files that provide easy access to all documentation:
- `all-reports-summary.md` - Comprehensive overview of all reports
- `stories-and-reports-summary.md` - Focused summary of featured content

This organization makes it easy for visitors to find relevant content and for search engines to index your documentation.

### 11. No-Upfront Payment Badge

For businesses offering deferred payment, add a trust badge that repeats the message in key sections:

**After Process steps:**
```html
<div class="reveal" style="text-align:center;margin-top:48px;">
  <div style="display:inline-flex;align-items:center;gap:8px;background:var(--surface);border:1px solid var(--border);border-radius:100px;padding:8px 20px;font-size:13px;color:var(--text2);">
    <span style="color:var(--green);">✓</span> No upfront payment for first-time clients
  </div>
</div>
```

**After services list:**
```html
<div class="reveal" style="text-align:center;margin-top:48px;padding:24px;border:1px solid var(--border);border-radius:16px;background:var(--surface);">
  <p style="color:var(--text2);font-size:14px;font-style:italic;margin:0;">
    💡 <strong style="color:var(--text);">No upfront payment</strong> for first-time clients.
    We deliver, you inspect, then you pay.<br>
    <span style="font-size:13px;color:var(--text2);opacity:0.7;">All prices in EUR.</span>
  </p>
</div>
```

### 12. Deployment Prep

Before deployment, the page is ready to go static:
- **0 dependencies** — pure HTML/CSS/JS, no build step
- One file — deploy by uploading `index.html` to any static host
- Google Fonts loads from CDN — works offline after first cache

For deployment you need credentials (one-time setup):
- **GitHub Pages**: `gh auth login` → create repo → push → enable Pages
- **Vercel**: `npx vercel deploy` (opens browser for login first time)
- **Netlify**: `npx netlify deploy --prod` (opens browser for login first time)

## Common Pitfalls

1. **Over-engineering.** A business landing page doesn't need React, Tailwind CDN, or 15 animations. Pure CSS/JS keeps it deployable anywhere with zero setup.
2. **Missing the story.** The origin story is the emotional hook — don't bury it below the fold. Lead with it.
3. **No CTA.** Every section should flow toward the contact CTA. If the user reads the whole page and doesn't know how to reach you, the page failed.
4. **Pricing without attribution.** Clients want to know WHO delivers. Tag each service to the agent/team member.
5. **Forgetting trust signals.** Crisis numbers, "no upfront payment", transparent scope boundaries — these build trust for small-biz clients.
6. **Broken mobile nav.** Test the hamburger toggle and smooth scroll on mobile viewport before calling it done.
7. **No OG tags.** The page needs to look good when shared on social media — always add `og:` meta tags.
8. **Shallow service descriptions.** When the user asks "improve the detail about our services," they want feature lists, use cases, deliverables, and delivery timelines — not just a one-liner per service. Always expand at least to Pattern B when detail is requested.
9. **Missing FAQ.** Businesses with non-traditional pricing (pay after delivery, AI-powered, single founder) raise questions. Anticipate them: payment process, revisions, who's behind the agents, international clients, custom work scope. A missing FAQ loses trust.
10. **No "Why Us" section.** When competing on price or values, a dedicated trust section between Process and Services pre-empts objections before the user reads pricing.
11. **FAQ not implementing single-open accordion.** If multiple FAQ items can be open simultaneously, the page grows uncomfortably tall. Always close all before toggling the clicked one.
12. **No authentic content.** Failing to showcase real stories, case studies, or documentation misses an opportunity to build trust and provide social proof.
13. **Deployment issues.** Git authentication problems can prevent deployment. Have a fallback strategy using direct API calls (see House of Sak implementation for example).

## Verification

- [ ] All sections load and are readable
- [ ] Scroll-reveal animations trigger properly (no sections stuck invisible)
- [ ] Mobile hamburger menu opens/closes
- [ ] Smooth scroll anchors land at correct sections
- [ ] Pricing and service names match the source repo exactly
- [ ] Expanded service cards (Pattern B): features list has 5-7 items, use-case box present, deliverable line included
- [ ] FAQ accordion: clicking one question closes others, all answers legible
- [ ] "Why Us" section: 6 cards covering key differentiators
- [ ] "Stories & Reports" section: showcases authentic content with links to source material
- [ ] Contact channels are real and functional
- [ ] Crisis numbers are accurate (if included)
- [ ] OG meta tags present in `<head>`
- [ ] Favicon visible in browser tab
- [ ] `wc -l` is reasonable for a single-page site (800–1400 lines typical; expanded pattern can reach 1400+)
- [ ] Deployment works via both git and API fallback methods