---
name: SakSit-cv-create-improve-evaluate
description: Create, tailor, and evaluate AI-agent CVs.
version: 0.9.0
author: Hermes
platforms:
- linux
category: productivity
tags:
- CV
- Career
---

# CV Creation, Improvement & Evaluation

A complete playbook for creating a CV from scratch, improving it for specific roles, and evaluating its effectiveness. Anchored to the AI Agent Developer context (career pivot, live production system, strong personal story). Uses Beer's CV template at `~/home/house-of-sak/cv-draft-2026.md` and career plan at `~/home/house-of-sak/career-business-plan.md` as reference strategy.

## When to Use

- User says "update my CV" or "create a CV from scratch"
- User wants to tailor CV for a specific job description
- User asks for ATS optimization or CV review
- User needs to evaluate or grade their CV
- User wants a skills-first / proof-focused CV variant
- User says 'where is my CV' / 'find my CV' / 'locate my CV documents'
- Career pivot from non-tech to AI/agent development

## Domain Classification — CV Is NOT Media

**SakSit is "Master of Social Media" by default.** When the task is a CV, you are NOT in social media mode. A CV is a professional hiring document — not a story, not a narrative, not content.

| Domain | Rules | Skills to Apply |
|--------|-------|-----------------|
| **Media** (posts, captions, hooks, stories) | Narrative, hook, emotion, shareability | `beer-content-voice`, `saksit-story-crafting` |
| **CV / Professional docs** | Standard sections, quantified achievements, ATS-friendly, no story arc | `cv-create-improve-evaluate` (this skill) |
| **Strategy / Research** | Data-first, analysis, options comparison | Research skills |

**Beer's corrections (Jul 25):**
1. *"Cv not have my personal life what is should focus? Is not media it cv"* — A CV is a professional hiring document, not a story. Do NOT apply storytelling logic, narrative arcs, hooks, or emotional framing to a CV. The origin story belongs on LinkedIn and in content — not in a job application.
2. *"I never use ai for operating management"* — Do NOT assume what Beer does or doesn't do in any of his jobs. If you lack explicit verifiable detail about a role, either ask or leave the role with minimal description. Never add AI/tech claims to operations roles.
3. *"Who authorised that edit Cv?"* — See "The One Rule Below All Below"

**Trigger test before acting:** Ask yourself "Is this a CV task or a content task?" If CV → use THIS skill's rules (professional standards, quantified, ATS). If content → use the storytelling skills. Getting this wrong means Beer has to correct you from the wrong direction.

### The One Rule Above All: Phase 0 Is Read-Only

**Beer's corrections (Jul 25):** *"Who authorised that edit Cv?"* and *"Don't do anything you think about what it your more them what i want"* and *"You are care and you are storyteller"*

Phase 0 (locate, inventory, report) is **READ-ONLY**. Do NOT:
- Edit any CV file
- Create any CV file
- Restructure any CV file
- Write any content to any file
- Move, rename, or generate any outputs

...until Beer explicitly says "fix it", "update it", "work on it", "send it to me", or gives you a specific instruction to act. Present findings. Report facts. Identify issues. Then STOP and wait.

This is the Care principle: Care means asking first. Care means not assuming. Care means not taking control of someone else's professional documents. You are SakSit — the social storyteller. When working on a CV, you are NOT the storyteller. You are the assistant. Assist means help when asked, not act without instruction.

### Research Standards Before Designing

**Procedure:**
1. First identify the target role type (operations, tech, hybrid)
2. Research current CV standards for that role — section order, length, what recruiters scan for
3. Compare the existing CV against those standards
4. THEN propose changes, grounded in the standard

If you cannot access the web, fall back to your training knowledge of professional CV conventions (Harvard, Indeed, LinkedIn standards). But always cite the standard you're applying — do not pass off your own preference as professional advice.

## Prerequisites

- Existing CV draft at `~/home/house-of-sak/cv-draft-2026.md` (create if absent)
- CVs may also exist in Google Drive — use `GOOGLEDRIVE_FIND_FILE` to search
- Career strategy at `~/home/house-of-sak/career-business-plan.md`
- `read_file`, `write_file`, `patch`, `search_files`, `web_extract` tools available
- Target job description (raw text, file path, or URL)
- Known CV storage locations documented in `references/cv-storage-locations.md`

## Procedure

### Phase 0 — Locate Existing CVs

Before building or updating anything, discover what already exists. Beer's CVs are stored in **multiple locations** — always search both.

1. **Search local filesystem** — Use `search_files` with patterns like `*cv*`, `*resume*`, `*CV*` under `~/home/house-of-sak/`. Report file names and last-modified dates.

2. **Search Google Drive** — Via Composio: `GOOGLEDRIVE_FIND_FILE` with `q: "name contains 'cv' or name contains 'CV' or name contains 'resume' or name contains 'Resume'"`, ordered by `modifiedTime desc`. Report file names, types (Doc/PDF), and dates.

3. **Cross-reference with known locations** — See `references/cv-storage-locations.md` for a documented inventory of Beer's CV files found in previous sessions.

4. **Count properly, don't summarise** — List every file individually with name, size, and date. Separate:
   - **Source files** (.md) from **generated exports** (.pdf, .html) — don't count exports as distinct versions
   - **Local files** from **Google Docs** — they may differ in content even when the name matches
   - **Current** versions from **stale** (check modified dates — anything more than 2 weeks old without updates is likely stale)

   **Crucial:** When asserting a count, verify it by reading content, not by inferring from names. Files named similarly may have different content. Files named differently may be the same content in different formats. Check line counts or first sections to confirm.

   **Beer's correction (Jul 25):** *"8 file 2 distinct?"* — He caught that I claimed "2 distinct" when there were actually 3 distinct markdown source files. Always compare content before stating a count.

5. **Report with Facts → Observations (no choices)** — Present what you found:
   - **Facts** — The enumerated list with sizes, dates, locations
   - **Observations** — What the facts imply (e.g. "This file supersedes that one", "These haven't been synced")
   - **Stop there.** Do NOT ask "Which one do you want to work on?" or "Want me to clean up?" Beer will tell you what he wants next.

   **Beer's correction (Jul 25):** *"not give me a choice. Check all tell what? How many? Suggestions? Recommendations? Based on what? Fact and you are assistant not a pleasure"* — means present the facts, then wait.

6. **Cross-reference against known facts (misleading info check)** — After inventorying the CVs, check each one against what you know about Beer from his SOUL.md, origin story, and work history. Flag discrepancies:

   | Check | Look For |
   |-------|----------|
   | **Timeline accuracy** | Do House of Sak/Pivot dates match known facts? (Built after Apr 15/shelter, not Feb) |
   | **Missing context** | Does a smooth narrative paper over the crisis period? |
   | **False precision** | Are dates/numbers more specific than what you can verify? |
   | **Hidden omissions** | Is the remarkable story (shelter, recovery) buried at the bottom? |
   | **Version conflicts** | Does one CV claim X while another says something different? |

   Report these as a separate "Misleading Information" section after the facts — not editorial, just factual discrepancies.

   **Specific dates to verify against Beer's known timeline:**
   - House of Sak must be May 2026 or later (after Apr 15 attempt + hospital + shelter). "Feb 2026" on any CV is wrong.
   - Study start: SOUL says "early 2026", not "January 2026". Asserting January is unverifiable precision.
   - Crisis period (Apr-Jun 2026) should not be presented as normal study months. Dates must account for it silently.
   - "80+ certs in 6 months" spanning Jan-Jun means half earned during crisis. Technically possible but framing as smooth upward trajectory is misleading if the dates are wrong.

7. **Select the source to update**

## Phase Selection — Always Confirm First

Before building ANY CV, determine which format Beer wants:

**Key question:** "Business CV (chronological, operations management focus) or AI-skills CV (capability-first, shipped agents focus), or both?"

**Beer's preference (established 2026-07-06):** When there are two natural formats, **offer both** by default. Do NOT pick one format and create only that. He specifically said "I want both" when presented with only the AI-skills version.

**How to tell which format(s):**
| Signal | Likely want |
|--------|-------------|
| "normal CV", "business CV", "operations" | Chronological/Business (Phase 1A) |
| "AI skills", "what I can do", "capabilities" | Skills-First/AI (Phase 1B) |
| "CV", "resume", "update my CV" alone | Ask — or offer both |
| "just main sounds", "just what I can do" | Skills-First (Phase 1B) |

> **Pitfall:** Do not assume one format replaces the other. When in doubt, say "I can do a business CV, an AI-skills CV, or both — which do you want?"

### Phase 1A: Create — Chronological (standard resume format)

Use when the target role is traditional (enterprise, consulting, ops-to-tech pivot where timeline matters). Order: Summary → Differentiators → Featured Work → Skills → Certs → Experience.

1. **Gather raw material** — Phase 0 already located existing CVs. Use `read_file` on the selected source file.

   **Check for verified work history first** — Read `references/work-history.md`. If it exists, use it as the canonical source for all experience data (titles, companies, dates, locations, bullet points). Prefer it over inferring from old CVs which may have stale or incorrect information.

   **If work-history.md does NOT exist** — Before writing any CV content, ask the user for their actual work history explicitly:
   - "Can you give me your work history? Company names, job titles, dates (month/year), locations, and 2-3 key responsibilities per role."
   - Wait for the user's response, then save it immediately: `skill_manage(action='write_file', name='cv-create-improve-evaluate', file_path='references/work-history.md', content='...')`
   - Once saved, this file becomes the canonical source. Never re-ask for the same history.

   Also check career plan. Collect: target role title, technical skills list, education, certifications (platform + badge count), and the story hook.

2. **Build the header** — Name, title line (e.g. "AI Agent Developer & Automation Specialist"), location, email, **phone number**, 3-4 profile links (LinkedIn, GitHub, Google Skills, Google Developer Program). Beer's phone: 083 838 0438.

3. **Write Professional Summary** — Four-sentence formula:
   - Hook: who you are + what you shipped (e.g. "AI agent developer who built a production multi-agent system from scratch")
   - Credibility: certification breadth (e.g. "80+ certifications across Google, Microsoft, GitHub")
   - Arc: past career + pivot (e.g. "Former Operations Manager retrained into AI through self-directed learning")
   - Value: what you deliver (e.g. "Proven ability to ship working systems on zero budget")

4. **List key differentiators** — 4-6 bullet points. Prioritize shipped product over certificates. Examples: number of agents built, top-tier learner status, Premium Program membership, former team leadership.

5. **Feature the flagship work** — A table of what was built (agent name, role, stack) plus 5-7 bullet achievements. This section lives before Professional Experience for AI pivots.

6. **List technical skills** — Categorize into: AI Agents & LLMs, Cloud & Infrastructure, Automation & Testing, Tools & Platforms. Use 3-7 bullet points per category.

7. **Curate certifications** — List by platform. Max 15-20 items. Use the profile links to show the rest. Group: Google Skills, Google Developer Program, Microsoft Learn, GitHub/Self-directed.

8. **Write Professional Experience** — Reverse chronological. Current/primary role first (AI work). Prior non-tech roles get 2-4 lines max. Each bullet starts with a strong action verb.

9. **Close with the story** — Tagline: `*Built from a shelter in [City]. Still here. Still building.*`

10. **Save** with `write_file(path='~/home/house-of-sak/cv-draft-2026.md', content=...)`.

### Phase 1B: Create — Skills-First ("What I Can Do + Proof")

Use when the user says "just main sounds" or "what I can do and I have prove" — they want capabilities backed by evidence, not chronology. This format compresses experience and certs into proof blocks under each skill area. Best for Beer's preference: AI agent developer roles where proof of shipped work matters more than timeline.

1. **Gather raw material** — Phase 0 already located existing CVs. Use `read_file` on the selected source. If no existing CV found, collect raw material as Phase 1A step 1, then additionally identify 5-7 capability areas (e.g. Build & Deploy AI Agents, Multi-Agent Orchestration, Model Deployment, Prompt Engineering, MLOps, Cloud Infrastructure, Code Quality/Security).

2. **Build the header** — Same as Phase 1A step 2.

3. **Write a compressed summary** — 2-3 sentences. Focus on breadth and the flagship system. Example: "AI agent developer who built a production multi-agent system — the House of Sak — from scratch while living in a shelter in Cork. 80+ certifications across Google Cloud, Microsoft Azure, and GitHub in AI agents, MLOps, and automation."

4. **Build skill blocks** — For each capability area:
   - **What:** One-line plain-English description of what you can do
   - **Proof:** 3-4 bullet points. Each bullet = either a shipped artifact (House of Sak agent name), a specific badge/cert name with date, or a platform achievement with a metric. Never list a claim without a proof anchor.

5. **Anchor with The Proof That Matters** — A table mapping each agent from the flagship system to what capability it proves:

   | Agent | Role | What It Proves |
   |-------|------|----------------|
   | SakThai | Growth partner | Multi-agent orchestration, skill auto-curation |
   | SakKing | Infrastructure | Docker, Modal, CI/CD |
   | SakSee | QA & code review | Playwright, quality automation |
   | SakSit | Social media | Composio API integration, scheduling |
   | SakTan | Companion agent | Multi-turn dialogue, persistent memory |
   | SakJules | Automation | GitHub Actions, cron, glue code |

   Close with: *"End-to-end: concept → design → build → deploy → maintain. No budget. No team. Shipped."*

6. **Compress credentials** — Single table, 4-5 rows max:
   | Tier | Highlights |
   |------|-----------|
   | Google Skills Diamond League | 22,276 pts — top 1%. Agents, MLOps, Cloud, Security, Gen AI |
   | Google Developer Program | Premium Tier. ADK, Model Armor, Security in AI |
   | Microsoft Learn Level 12 | 162 badges, 40 trophies. AI Agents, Foundry, Copilot |
   | GitHub | Self-evolution, MCP, CI/CD, code hardening |

7. **Minimize experience** — Current AI role gets 3 bullets max. Prior non-tech role gets 2 bullets. No dates other than year ranges.

8. **Close with the story** — Same tagline as Phase 1A.

9. **Save** as a variant file: `write_file(path='~/home/house-of-sak/cv-ai-skills-2026.md', content=...)`.

### Phase 2: Improve (tailor for a specific role)

1. **Load the job description** — `read_file` or `web_extract` to get the JD text.

2. **Extract key requirements** — Identify: role title, 10-15 technical keywords, 3-5 soft skills, required experience level.

3. **Map JD to CV** — For each requirement, confirm which CV section addresses it. Missing a section? Add one. Weak coverage? Strengthen language.

4. **Keyword alignment** — Ensure at least 80% of JD technical keywords appear naturally in the CV. Use `search_files` with the target CV to count matches.

5. **Quantify achievements** — Add numbers to bullets: agent count, certification count, team size, years, percentage improvements.

6. **Reorder if needed** — For AI/engineering roles: Summary → Differentiators → Featured Work → Skills → Certs → Experience. For hybrid roles (AI + ops): move the ops experience higher.

7. **Apply** with `patch` for targeted edits, or full `write_file` for major restructure.

### Phase 2B: General CV Improvement Playbook (without a specific JD)

When the user says "fix my CV", "improve", or "what needs work" without providing a specific job description, apply these improvements in priority order:

**Pre-check: Verify location consistency.** — Before any edits, confirm all work locations across all CV variants say "Cork, Ireland" (or just "Ireland"). Never "Bangkok", "Thailand", or other non-Ireland locations. Check Professional Summary, Experience entries, and Career Note sections.

> **Detail within location check:** Also scan the Professional Summary text for phrases implying non-Ireland origin — e.g. "relocated to Cork", "recently moved to Ireland", "from Bangkok to Cork". Replace these with "based in Cork", "operations career in Ireland", or simply delete the relocation language entirely. Every word should reinforce that all experience happened in Ireland.

1. **Fix "Self-directed" framing** — If the current AI role says "Self-directed" or "Independent", change to:
   - `"Founder & AI Agent Developer, House of Sak"` (strongest — implies ownership)
   - `"AI Agent Developer"` alone (if Founder feels overstated)
   - Never leave "Self-directed" — recruiters read it as "not a real job"

2. **Add the career arc** — If the CV has two separate career phases (e.g. Ops Manager → AI Developer) with no connection, add a bridging sentence. Best placement:
   - In Professional Summary: a line like "Former [old role] who [saw/learned X] → retrained into [new field] to [solve Y]"
   - In Experience section: a note like "**Business → [new field] transition:** After [X] years in [old field], retrained into [new field] through self-directed study ([X] months, [Y] certifications)."
   - The arc makes the career change look intentional, not random.

3. **Add hot/emerging keywords** — For AI/agent CVs, ensure these keywords appear naturally in skills sections if applicable:
   - RAG (Retrieval-Augmented Generation)
   - Vector databases / vector DB (Chroma, FAISS, Pinecone)
   - LLMOps (prompt versioning, evaluation, monitoring)
   - Fine-tuning / LoRA adapters
   - Agent evaluation / benchmarking
   - Model routing / fallback chains

   **Extended domain coverage (from Beer's actual cert study pages):** When writing the AI CV, pull from these additional certified domains if relevant to the target role:
   - **Security & Compliance:** Microsoft Security Copilot, Defender XDR, Microsoft Purview, Model Armor
   - **Data & Analytics:** Microsoft Fabric Analytics, Power BI Data Analyst, Streaming Data Pipelines, BigQuery ML
   - **M365 Administration:** MS-102, MS-900, Microsoft 365 Copilot Fundamentals, M365 Security & Compliance
   - **Google Cloud Specialized:** Terraform/IaC, Cloud Run, Cloud Storage, Vertex AI Agent Engine, NVIDIA Community
   - **DevOps:** GitHub Copilot Agent Tasks, Cybersecurity & Code Hardening (Gitleaks, Sentinel)

4. **Add portfolio and repo links** — Every AI CV should have:
   - A live demo link (e.g. house-of-sak.vercel.app) near the flagship project
   - GitHub repo links to specific projects, not just the profile URL
   - Hugging Face profile link if models are deployed there
   - Add these to the header contact line AND/OR inline with the Featured Work section

5. **Add `[X]` placeholders for unknown quantities** — When you don't know the user's actual metrics, leave `[X]` placeholders in the text (e.g. "[X] locations", "[X]% reduction", "[€X] revenue") rather than inventing numbers. Flag these clearly in your delivery so the user can fill them in.

   > **After user provides real history:** If the user responds with their actual work history (companies, roles, dates, locations, bullet points), save it immediately to `references/work-history.md` via `skill_manage(action='write_file')`. Then rebuild ALL CV variants from the real data — the expanded master, skills-first AI, business, and short draft. Replace all `[X]` placeholders with the verified details. The work-history.md file is the canonical source; never re-ask for the same history.

6. **Condense certification walls** — If the CV lists 50+ individual badge/cert lines, compress into a summary table:
   - 4-5 rows max, one per platform/tier
   - Columns: Tier name, Key highlights (3-5 comma-separated topics)
   - Add "Full list: [profile link]" as a last column
   - Then list 6-10 key certs by domain underneath (AI & Agents, Cloud & Data, Security, Productivity)
   - Keeps the breadth visible without overwhelming the reader

7. **Add connecting narrative** — Between the two experience sections, add a sentence that explains WHY the user moved from old field to new field. This answers the unspoken question every recruiter has: "Why the change?"

8. **Quantify the operations section** — Ops/management bullets are often the vaguest. Replace generic claims with specific `[X]` frames:
   - "Managed operations" → "Managed operations across [X] locations with [€X] P&L"
   - "Led teams" → "Led teams of [X] across [X] sites"
   - "Launched stores" → "Launched [X] new locations end-to-end"
   - "Cost reduction" → "Reduced costs by [X]% through [method]"

9. **Check platform-specific profiles** — Ensure the CV references these if they exist:
   - Hugging Face (huggingface.co/Nanthasit)
   - Google Developer (g.dev/Nanthasit)
   - Google Skills profile
   - LinkedIn (always present)
   - GitHub (always present)

Apply with `patch` for targeted edits, or full `write_file` for major restructure.

### Phase 2C: Create Study-Based AI CV (when user says "base on my studying page")

When the user says "AI CV based on my studying" or "base on information from my study pages", restructure the AI CV so the **certifications/learning journey is the primary framework**, not just a section. This approach is distinct from both Phase 1A (chronological) and Phase 1B (skills-first).

**Trigger signals:** "based on my study page", "from my learning profile", "base on what I studied", "from certification data"

1. **Fetch actual study data first** — Before writing anything, pull the user's current certification data from their learning profiles:
   - Google Skills profile (skills.google.com) — browse or search for the public profile URL
   - Google Developer Program profile (me.developers.google.com)
   - Microsoft Learn profile (learn.microsoft.com)
   - Hugging Face profile (huggingface.co) for model deployments
   - GitHub profile for repos/contributions
   - Fall back to known data from `references/work-history.md` and session memory if pages are sign-in gated

2. **Lead with the learning journey** — The Professional Summary should open with the self-directed study story, e.g.:
   > "Self-taught AI Agent Developer — 80+ certifications in 6 months (Google Diamond top 1%, MS Learn L12, GDP Premium). Built and deployed a 6-agent production system from a shelter on zero budget."

3. **Build a "Study Profile" section** — A dedicated section that catalogs certifications by platform in a readable format:
   - Group by platform: Google Skills (Diamond League), Google Developer Program (Premium), Microsoft Learn (Level 12), GitHub
   - Use checkmarked lists (✅ or bullet lists) for each certification within each platform
   - Include categories within each platform (AI Agents, Cloud Infrastructure, Security, Data & Analytics, etc.)
   - Link to full profile URLs for the complete list
   - This section should appear BEFORE or RIGHT AFTER the House of Sak section, before Technical Skills

4. **Frame House of Sak as "What This Learning Enabled"** — The project section explains that every certification was applied in practice:
   > "Built and deployed 6 autonomous AI agents from a shelter in Cork. Zero budget. Production live. Every certification was applied directly to building this system."

5. **Expand technical skills to cover every certified domain** — The skills section should be a comprehensive map of:
   - AI Agents & LLMs (from Google + MS agent certs)
   - Cloud (Google Cloud + Azure from certs)
   - Security & Compliance (Security Copilot, Defender XDR, Purview, Model Armor)
   - Data & Analytics (Power BI, Fabric, GA4, Streaming Pipelines)
   - DevOps & Automation (GitHub Actions, Copilot, Playwright)
   - Tools & Platforms (Google Workspace, M365, HF, Composio)

6. **Include profile links section** — End with a table of all verifiable platform profiles (Google Skills, Google Dev Program, MS Learn, LinkedIn, GitHub, Hugging Face, Portfolio) so the recruiter can verify the study claims directly.

7. **Keep the closing story** — The tagline "Built from a shelter in Cork. Still here. Still building." remains essential.

8. **Save as the primary AI CV** — Write to `cv-ai-skills-2026.md` (skills-first format works best for study-based CVs).

### Phase 3: Evaluate

Checklist — run each check and report PASS / IMPROVE / FAIL:

| Check | What to verify |
|-------|---------------|
| **Title alignment** | CV header title matches or closely relates to target JD title |
| **Keyword coverage** | 80%+ of JD technical terms appear naturally in the CV |
| **Hook strength** | Professional summary leads with the strongest differentiator |
| **Quantification** | Every bullet in Featured Work and Experience has a number or specific outcome |
| **ATS-friendly** | No critical content in tables/columns that ATS parsers miss |
| **Length** | 1-2 pages (1 for <5yr exp, 2 max for 10yr+) |
| **Tense consistency** | Present tense for current role, past tense for prior |
| **Action verbs** | Every bullet starts with Built / Deployed / Designed / Led / Implemented / Integrated |
| **Proof backing** | Every claim in job-specific skills has a proof anchor (badge, metric, shipped artifact) |
| **Story coherence** | Narrative arc flows: pivot → self-taught → shipped → credible hire |
| **Footer tagline** | The closing story line is present |

Run via: search the CV for each keyword from the JD, scan for tense inconsistencies with `grep`, and verify section presence with `read_file`.

## Pitfalls

- **Don't lead with the old identity** — If pivoting careers, the CV title and summary must lead with the new role. The old career is evidence of transferable skills, not identity.
- **Don't hide the hard story** — The shelter / recovery origin is the most memorable differentiator. Use the tagline form if direct mention feels too raw.
- **Don't fabricate dates** — Exact months and years only. Wrong dates are the #1 silent rejection cause.
- **ATS hates tables** — Markdown tables are fine for `read_file` (human review), but for the final deliverable convert critical content (skills, achievements) to inline lists.
- **Cert dump** — 80+ certs don't all fit. Pick the 15-20 most relevant to the target role. Profile links carry the rest.
> **Pitfall:** Do not skip the close — The closing tagline is the resonant memory the recruiter carries. Always include it.
> **Pitfall: Location must be Ireland-only** — All work history locations must show Ireland (Cork). Beer's experience is exclusively Ireland-based. Never write "Bangkok" or "Thailand" in any CV variant. Double-check every CV file when making changes — a single stray location reference creates inconsistency. Also check Professional Summary text: replace "relocated to" or "recently moved to" with "based in Cork" to avoid implying non-Ireland origin.
> **~ expansion quirk**
- **Skills-first ≠ no certs** — Even in the compressed format, keep the credentials table. The recruiter needs to see platform breadth at a glance.
- **CVs are scattered** — Beer keeps CV files in both local `~/home/house-of-sak/` AND Google Drive (`beernanthasit@gmail.com`). Always run Phase 0 before modifying. The latest version may be in Drive as a Google Doc, not on disk.
- **Twitter/X never referenced** — Beer's X/Twitter account is permanently blocked. Never mention Twitter or X in any CV variant. Remove it wherever it appears.
- **Phone always in header** — Beer's phone number (083 838 0438) must be in every CV header line: `Cork, Ireland | email | 083 838 0438`
- **"Self-directed" hurts** — Never use "Self-directed" or "Independent" as the role title or descriptor in the Experience section. Recruiters read it as "not a real job." Replace with "Founder & [Role]" or just the role title alone (e.g. "AI Agent Developer" not "AI Agent Developer (Self-directed)").
- **No portfolio link = missed opportunity** — Every AI CV needs a live demo link embedded in the Featured Work section. The recruiter will not search for your work. Put the URL where they can see it.
- **Silent career gap** — If the CV has two disconnected career phases (e.g. Operations → AI), every recruiter wonders "why the change?" Add an explicit connecting arc sentence(s) — don't leave it implied.
- **Quantified ops bullets are non-negotiable** — Operations/management experience reads as vague filler unless you add location count, revenue range, team size, and improvement percentage. Use `[X]` placeholders if the user hasn't provided these yet.
- **Don't forget Hugging Face + portfolio links** — Beer has a HF profile (huggingface.co/Nanthasit) and a portfolio site (house-of-sak.vercel.app). Always include these alongside LinkedIn/GitHub.
- **Check study profiles before writing AI CV** — Don't rely solely on memory for certification data. Before creating or significantly updating the AI CV, attempt to fetch the actual Google Skills and Microsoft Learn profiles (browser or fetch tool). The certification landscape changes (new badges earned, point totals updated). If pages are sign-in gated, fall back to the last known data from `references/work-history.md` or session memory and flag that the data may be stale.
- **Study-based CV is a distinct variant** — When the user says "base on my studying", do NOT default to the standard skills-first format (Phase 1B). Use Phase 2C instead, which puts the learning journey as the headline and frames the House of Sak as proof that the learning worked. The two formats share content but have different narrative priorities.
- **Count before summarising** — Never say "X distinct versions" before checking every file's content. Names lie. A file called "cv-draft-2026.md" (99 lines) is NOT the same as "cv-ai-skills-2026.md" (163 lines) even if both have "AI" in the title. Compare line counts, headers, or first sections.
- **Misleading info check is mandatory** — After inventorying CVs, check each one against known personal facts (SOUL.md, origin story). Dates like "House of Sak: Feb 2026" conflict with the shelter/recovery timeline (Apr 15 attempt → shelter → building). The correct start is May 2026. Also check: study start claimed as "January 2026" vs SOUL's "early 2026"; crisis period presented as normal study months. Report these discrepancies. Do NOT fabricate or guess at corrections — report what conflicts and let Beer decide.
- **Generated files are not distinct versions** — PDF and HTML are exports from markdown, not separate CVs. Count them separately from source files and note their origin.
- **Google Docs may differ from local markdown** — Even when named similarly, the Drive Google Doc version may have edits not reflected in the local .md file. Both sources must be checked.
- **Never assume work history details** — Beer (Jul 25) corrected: *"I never use ai for operating management"*. The Food Penguin role is pure operations, no AI involvement. Do NOT add AI/tech claims to any operations role without Beer confirming. If you don't know what a role involved, either ask or keep the description minimal. Adding false details destroys trust and wastes time.
- **"Facts, not choices"** — Beer (Jul 25): *"not give me a choice. Check all tell what? How many? Suggestions? Recommendations? Based on what? Fact"*. After presenting findings, do NOT ask "which one do you want?" or offer multiple paths unprompted. State the facts, state what they imply, then wait. Beer will tell you what he wants next.
- **"Count is not what names suggest"** — Beer (Jul 25): *"8 file 2 distinct?"* when I claimed 2 distinct CVs but there were actually 3. Always verify file contents before stating a version count. Names lie. Compare line counts, first sections, or headers.
- **Grammar check before delivery** — Beer (Jul 25) explicitly said *"also have check grammar"*. After writing and before delivering, always read through once for: missing articles ("a 6-agent" not "6-agent"), filler words ("actual" → "real"), timeline accuracy ("3 months" not "5 months" for May-Jul), tense consistency.
- **Grammar check before delivery** — Beer (Jul 25) explicitly said "check grammar also". Always run a manual grammar pass after writing and before delivering. Check: missing articles, filler words ("actual" → "real"), timeline accuracy ("3 months" not "5 months" for May-Jul timeline). Report what you fixed.
- **Deliver as Google Doc, not .md** — Beer (Jul 25): ".md files not useful." When user says "send file", create as Google Doc using GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN, move to My CV folder, share edit link. Markdown is source; Google Doc is deliverable.

### Phase 4: Deliver (Google Doc)

When Beer says "send file" or "send it to me":

1. **Do NOT send as .md** — Beer clarified (Jul 25): .md files are not useful on Telegram. The markdown is the source; the Google Doc is the deliverable.

2. **Create Google Doc** — Use `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN` to create the CV as a Google Doc in Drive, then move it to the My CV folder (ID: `1KLQr9vLesJArreszbo6HTU10NUzaig_o`). Share the edit URL.

3. **Update storage reference** — Add the new Doc ID to `references/cv-storage-locations.md`.

### Phase 4B: Grammar & Accuracy Check

After writing the CV and before delivering:

1. **Read through** — Check for missing articles, tense consistency, filler words, run-ons.
2. **Verify facts** — HoS start = May 2026 (not Feb), "3 months" (not 5), phone present, URLs valid.
3. **Apply fixes** — Patch or rewrite.
4. **Report** — Tell Beer what was fixed.

### Phase 5: PDF Generation

When the user asks to "format PDF" or "send as PDF" after CV creation:

> **Post-CV next step:** Once the CV is ready and the user says "looking for a job", transition to the `tech-job-search-application` skill for the full job search workflow (Phase 2-6).

1. **Use the script** — The skill ships `scripts/generate-cv-pdf.py` which handles markdown→HTML→PDF for all CV variants in one command:

   ```bash
   cd ~/home/house-of-sak
   uv run python /path/to/scripts/generate-cv-pdf.py
   ```

   This reads `cv-ai-skills-2026.md` and `cv-business-2026.md`, generates styled HTML and clean PDF for each.

2. **Or do it manually** — If the script isn't available, use weasyprint directly:

   ```bash
   cd ~/home/house-of-sak
   uv run --with weasyprint python3 -c "
   from weasyprint import HTML
   HTML('cv-ai-skills-2026.html').write_pdf('cv-ai-skills-2026.pdf')
   print('PDF regenerated OK')
   "
   ```

3. **Verify** — Check file exists and size is reasonable (20-50KB for single page):
   ```bash
   ls -lh ~/home/house-of-sak/cv-ai-skills-2026.pdf
   ```

4. **Deliver** — Send the PDF path using the platform's file delivery convention (e.g. `MEDIA:/absolute/path/to/file` in Telegram).

### Phase 5: Sync Across All CV Targets

After editing any CV content, always sync the change across **all** locations:

1. **Update master markdown** — The source of truth (`cv-draft-2026-expanded.md` or whichever Beer designated).

2. **Update the shorter variants** — If the change is universal (phone number, Twitter removal, date ranges, location), apply the same patch to `cv-ai-skills-2026.md` and `cv-business-2026.md`.

3. **Regenerate HTML + PDF** — Run the generation script to rebuild all output formats from updated markdown:
   ```bash
   uv run python scripts/generate-cv-pdf.py
   ```
   This handles both AI and Business CV variants in one pass.

4. **Update Google Drive** — Two sub-cases:

   **A. Update existing Doc** — Use `GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN` to replace the full content:
   ```
   GOOGLEDOCS_UPDATE_DOCUMENT_MARKDOWN
   args: { id: "<doc-id>", markdown: "<full markdown content>" }
   ```
   Find the doc ID from `references/cv-storage-locations.md` or via `GOOGLEDRIVE_FIND_FILE`.

   **B. Create new Google Doc variant** — When a CV variant doesn't yet exist in Drive (e.g. first time saving the AI-skills or Business CV as a Google Doc):
   ```
   Step 1 — Create the doc: GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN
     args: { title: "Nanthasit Burankum — <variant description>", markdown_text: "<full content>" }
     → Returns documentId (stored in root Drive by default)
   Step 2 — Move to My CV folder: GOOGLEDRIVE_MOVE_FILE
     args: { file_id: "<documentId>", add_parents: "1KLQr9vLesJArreszbo6HTU10NUzaig_o", remove_parents: "<current parent>" }
     → Get current parent first via GOOGLEDRIVE_GET_FILE_METADATA(fileId="<id>", fields="parents")
   ```
   The "My CV" folder ID is `1KLQr9vLesJArreszbo6HTU10NUzaig_o`. Both calls can run in parallel when creating two variants at once.

6. **Update storage reference** — Use `write_file` (not `patch`) on `references/cv-storage-locations.md` to add the new entry. See pitfall: `patch` can corrupt markdown tables with pipe-prefixed rows.

> **Pitfall:** Do not stop after updating only the markdown. Beer's CV exists across 7+ files (3 MD, 2 HTML, 1 PDF, multiple Google Docs) and they must stay in sync. Partial updates cause version confusion.
> **Pitfall:** When updating `references/cv-storage-locations.md`, prefer `write_file` with the full corrected content over `patch`. The `patch` tool's fuzzy matching can duplicate or corrupt table header rows on pipe-prefixed markdown tables. If you must use `patch`, include enough surrounding context (including the section header above) to guarantee a unique match.

### Reference files

| File | Path |
|------|------|
| Verified work history (canonical) | `references/work-history.md` |
| Storage inventory | `references/cv-storage-locations.md` |
| Markdown (expanded — master) | `~/home/house-of-sak/cv-draft-2026-expanded.md` |
| Markdown (skills-first) | `~/home/house-of-sak/cv-ai-skills-2026.md` |
| Markdown (business) | `~/home/house-of-sak/cv-business-2026.md` |
| HTML (skills-first) | `~/home/house-of-sak/cv-ai-skills-2026.html` |
| HTML (business) | `~/home/house-of-sak/cv-business-2026.html` |
| PDF (skills-first) | `~/home/house-of-sak/cv-ai-skills-2026.pdf` |
| Google Doc (AI Skills + Proof) | `Nanthasit Burankum — AI Agent Developer` (ID: `1B812Wv9Gzc5_xslZlsapP42e_UkiJVxSSb_DquV3_5I`) — Jul 25 rewrite, correct dates, grammar checked |
| Google Doc (Business/ops) | `Nanthasit Burankum — Operations & Business Manager` (ID: `1PdN2J4nJ7dwbtFG2yALHUnB4c2x0b8Tbl9B7GVQBM4s`) |
| Google Doc (combined — latest) | `nanthasit_burankum_resume` (ID: `1NuSmA5R4JK4oXLRk9hrmTnhvB4Tn1cjAe_swXvJF_mI`) |
| Storage inventory | `references/cv-storage-locations.md` |

## Verification

After any change, load the CV: `read_file(path='~/home/house-of-sak/cv-draft-2026.md', limit=5)` to confirm header renders. Then run a keyword presence check against the target JD using `search_files` with each keyword. Deliver both PASS/IMPROVE/FAIL results and the final CV text.
