---
name: SakSit-tech-job-search-application
description: Guide tech/AI job search, application, and follow-up.
version: 0.2.0
author: Hermes
platforms:
- linux
category: productivity
tags:
- Career
- Job-Search
---

# Tech/AI Job Search & Application Workflow

A complete playbook for helping a user find, tailor, and apply to tech/AI roles — especially career pivots with non-traditional backgrounds (shipped portfolio > formal credentials). Covers the full lifecycle: understanding targets, searching (with fallbacks when automation is blocked), tailoring CVs, drafting cover letters, and tracking applications.

Designed for **zero-cost constraint**: all job boards, alerts, and tools must be free. No paid APIs for job aggregation.

## When to Use

- User says "looking for a job", "need to find work", "apply to roles"
- User says "help me find jobs in [city/region]"
- User says "tailor my CV for this role" or "draft a cover letter"
- User needs a job application tracker or follow-up reminders
- Career pivot — user has a strong portfolio story but non-traditional background

## Prerequisites

- CV files exist at `~/home/house-of-sak/` — run `cv-create-improve-evaluate` Phase 0 first if unsure
- Google Drive search access via `GOOGLEDRIVE_FIND_FILE` (Composio) for CV location
- Browser access for manual-approach fallback or linkedin.com
- User's LinkedIn, Indeed, and IrishJobs accounts (user logs in manually)

## Phase 1: Clarify Target

Before searching, confirm:

1. **Role type** — AI Agent Developer, AI Engineer, Automation Specialist, Hybrid (AI + Ops), Solutions Engineer, etc.
2. **Location** — City, remote preference, willingness to relocate
3. **Seniority** — Entry (pivot), mid, senior — calibrate expectations
4. **Constraints** — Zero-cost only. Visually impaired user — read all listings back.

Output: clear target profile used to shape all subsequent phases.

### ⚠️ User-preference: what "content" means

When you've offered to help with a specific application (tailor CV + draft cover letter) and the user replies "Content", they mean **application content** — the CV and cover letter for that specific role. NOT LinkedIn posts, social media content, or thought-leadership drafts.

**Default path:** Tailor CV → draft cover letter → read both back to user. Only pivot to LinkedIn/social content if the user explicitly says "post", "LinkedIn post", or "publish".

**Correction signal to learn from:** Beer said "Check your drift again" when I jumped to LinkedIn post drafts after he said "Content" in response to an offer to help with a specific job application.

## Phase 2: Attempt Automated Search

**Important:** Major job sites (LinkedIn, Indeed, IrishJobs, Google) have aggressive bot detection. Automated search often fails. Don't spend more than 2-3 attempts.

### Approach 1: COMPOSIO_SEARCH_WEB (if available)
```python
# Via Composio — may require Exa API approval in Composio dashboard
# Error pattern: "No response to elicitation prompt within the allowed time"
# or "Elicitation is unavailable for this session. Approve this tool"
# → This means COMPOSIO_SEARCH_WEB needs dashboard approval. Don't retry.
```

### Approach 2: Browser tool (BROWSER_TOOL_CREATE_TASK)
May work for some sites but most job portals block headless browsers. Google/Startpage/DuckDuckGo all present CAPTCHAs.

### Approach 3: Terminal via curl
Python-based approaches (duckduckgo_search, requests) are rate-limited from shared IPs. Google blocks curl with CAPTCHA challenges.

**Fallback trigger:** If the FIRST approach fails with a bot-detection/captcha/elicitation error, skip directly to Phase 3. Do not try 2+ approaches — every major job portal (LinkedIn, Indeed, IrishJobs, Google Jobs, Bing Jobs, DuckDuckGo) uses the same bot-detection infrastructure. A single failure pattern (captcha, consent wall, Cloudflare challenge) means all others will fail the same way. Save the tokens.

### Step 0 — Check existing leads first

Before searching fresh, check for previously found job leads. Beer has past session output files:
- `~/home/house-of-sak/job-search-results-*.md` — previously found matches with fit ratings
- `~/home/house-of-sak/job-search-deep-dive.md` — career strategy with target role rankings
- `~/home/house-of-sak/week1-job-search-planner.html` — actionable week-by-week plan
- `references/known-job-leads-2026.md` (in this skill) — compiled leads, keywords, image assets

Also use `session_search` to find past job-related conversations. A lead from a prior session (e.g. Joveo AI AI Agent Engineer) may still be open and is higher-value than a fresh search.

## Phase 3: Fallback — Manual Direction

When automated search is blocked, guide the user to search themselves. This is the primary reliable path for job search.

### Step 1 — Provide exact search URLs and keywords
Give the user ready-to-click links:

| Platform | URL Pattern | Keywords |
|----------|-------------|----------|
| LinkedIn Jobs | https://www.linkedin.com/jobs/search?keywords=KEYWORDS&location=Cork%2C%20Ireland | "AI Agent", "AI Engineer", "Automation", "MLOps" |
| Indeed.ie | https://ie.indeed.com/jobs?q=KEYWORDS&l=Cork | Same |
| IrishJobs.ie | https://www.irishjobs.ie/Jobs/Results?Keywords=KEYWORDS&Location=Cork | Same |
| Jobs.ie | https://www.jobs.ie/Jobs.aspx?keywords=KEYWORDS&location=Cork | Same |

### Step 2 — Job alert setup
Instruct user to:
1. Visit each site → search → click "Create job alert" / "Get email alerts"
2. Use 3-4 keyword variations per platform
3. Set frequency to daily

### Step 3 — LinkedIn networking
Guide user to:
1. Update headline + About section to include role keywords
2. Search "recruiter Cork" + "recruiter Ireland AI" → connect with 10+
3. Follow company pages: Apple Cork, Dell Cork, Proofpoint, Teamwork, Zendesk, Salesforce Dublin, Intercom
4. Connection message template: *"Hi [Name], I'm an AI Agent Developer based in Cork. I built 6 production AI agents from a shelter here. Always looking to connect with people in Irish tech."*

### Step 4 — Re-engage from existing leads
Check for previously found job leads (session_search, local files) before starting fresh. Existing leads may still be open.

## Phase 4: Tailor CV for Role

Delegate to `cv-create-improve-evaluate` skill Phase 2 and Phase 3.

1. User provides job description (paste text, URL, or file path)
2. Run extract → map → align → quantify → reorder workflow
3. Read the tailored CV back to the user
4. Offer to export as PDF via cv-create-improve-evaluate Phase 4

## Phase 5: Draft Cover Letter

Generate a 3-4 paragraph cover letter:

```
Paragraph 1 — Hook: Who you are + what you shipped
  "I built 6 production AI agents from scratch — while living in a shelter in Cork."

Paragraph 2 — Fit: Why this role matches your skills
  Map 2-3 JD requirements to specific House of Sak agents or certifications.

Paragraph 3 — Differentiator: What sets you apart
  Google Skills Diamond League (top 1%), Premium Developer Program, 80+ certs, 7+ years ops management.

Paragraph 4 — Close: Call to action
  "I'd love to show you a live demo of the House of Sak in action."
```

Keep each paragraph 2-4 sentences. End with contact info and links.

## Phase 6: Track Applications

Create or update a tracking document:

```
| Company | Role | Date Applied | Status | Notes |
|---------|------|-------------|--------|-------|
| Joveo AI | AI Agent Engineer | 2026-07-09 | Applied | Used SakThai demo |
```

Store at `~/home/house-of-sak/job-application-tracker.md`. Offer Google Sheets sync if user requests.

## Pitfalls

- **Bot detection is the norm, not the exception.** All major job sites (LinkedIn, Indeed, IrishJobs, Google Jobs) block automated access. Plan for Phase 3 (manual direction) from the start.
- **COMPOSIO_SEARCH_WEB elicitation error** — "Elicitation is unavailable for this session. Approve this tool in the Composio dashboard." This means the Exa search tool was not approved in the dashboard's tool settings. Until it's approved, COMPOSIO_SEARCH_WEB will always fail. Don't retry; use manual fallback.
- **COMPOSIO_REMOTE_WORKBENCH web_search helper** — Depends on the same Exa API as COMPOSIO_SEARCH_WEB. Will also fail if elicitation is not approved.
- **Zero-cost constraint** — Do NOT suggest paid services (LinkedIn Premium, Indeed Resume, paid job alerts, CV writing services). Always include free alternatives.
- **Visually impaired user** — Read all job listings, CV changes, and guidance back verbatim. Don't say "check the link" — read the content.
- **DuckDuckGo search library** — Rate-limited from shared/cloud IPs. If it returns 0 results, try again later or use a different approach. Not reliable for job search.
- **Existing leads first** — Check session_search and local files for previously found job matches before starting a fresh search. A lead found in a prior session may still be open.
- **Don't over-tailor** — 1 CV version per role type (AI Agent Dev / Hybrid / Ops) is enough. Tailor per-application sparingly (keywords + summary). Full rewrite per role is unsustainable.

## Verification

After any Phase 4-6 action, confirm with user:
- "I read you the tailored CV — does it sound right?"
- "The cover letter is drafted — want me to read it back?"
- "The tracker is updated — want me to read the current entries?"
