# Post-Audit Launch Blitz — 12-Hour Pattern

**Source:** Session 2026-07-06 — Beer rejected a 12-week plan for "12 Hours plan, and all content and all video"

## When to Use

After a full audit reveals empty/bare platforms, and Beer asks for an action plan. If he says "make a plan," default to **hours, not weeks** for his personal brand launch. Weeks/quarters are for B2B SaaS clients; hours are for House of Sak.

## Trigger Phrases

- "make list, plan, step, timeframe" → propose 12-hour blitz, not 12-week quarter plan
- "all content and all video" → full blitz, every platform simultaneously
- "6 pic about and prompt" → user wants image prompts delivered as text + concept descriptions

## The 12-Hour Blitz Structure

```
H1  — Fix all profiles (website, bio, description, images)
H2-3 — Generate brand visuals (6 images for posts)
H4-5 — Write 6 post copies (one per content bucket)
H6-8 — Publish across platforms (Facebook + Instagram + LinkedIn)
H9-10 — Video content (generate assets, title, description)
H11 — Cross-post + schedule second loop
H12 — Verify everything + analytics baseline
```

### Hour-by-Hour Detail

| Hour | What | Tools |
|------|------|-------|
| **H1** | Fix ALL empty profiles in parallel — Facebook page (website, about, desc), Instagram bio link, YouTube channel description | FACEBOOK_UPDATE_PAGE_SETTINGS, manual instructions for Instagram/LinkedIn |
| **H2-3** | Generate brand visual assets — 6 images via Gemini or prompts | image_generate / fallback to prompt writing |
| **H4-5** | Write 6 post copies — one per content bucket (Origin, Sak Family, How-To, BTS, Client, Reflection) | Write to file then platform-publish |
| **H6-8** | Publish — Facebook (FACEBOOK_CREATE_PHOTO_POST or FACEBOOK_CREATE_POST), Instagram (create container + publish), LinkedIn (LINKEDIN_CREATE_POST) | Composio multi-execute (batch all 6 Facebook posts in one call) |
| **H9-10** | Video — generate title card image, write description, set up YouTube metadata (cannot upload via API — note this clearly) | Gemini + YOUTUBE_UPDATE_VIDEO (metadata only) |
| **H11** | Cross-post — LinkedIn → Facebook mirror, set scheduled times for second loop of 6 posts | FACEBOOK_CREATE_POST schedule |
| **H12** | Polish — verify all pages updated, re-read FACEBOOK_GET_PAGE_DETAILS, deliver final links to Beer | GET calls on all platforms |

## Content Buckets (6 Post Loop x 2)

| # | Topic | Platform |
|---|-------|----------|
| 1 | **Origin Story** — April 15, recovery, building from ICU | LinkedIn + YouTube |
| 2 | **Sak Family** — Meet the 6 agents | Instagram + Facebook |
| 3 | **How-To** — AI tools, agent building tips | YouTube + LinkedIn |
| 4 | **Behind the Scenes** — Beer's workshop, Cork | Instagram Stories |
| 5 | **Client Work** — House of Sak case studies | LinkedIn + Facebook |
| 6 | **Reflection** — Mental health, resilience | LinkedIn + Instagram |

## Image Generation Fallback Pattern

When image generation fails (no FAL_KEY, missing credentials, etc.):

1. **Write 6 detailed prompts** — one per content bucket
2. **Format each prompt as a pair:** concept description + the exact prompt text
3. **STYLE RULE: "mix over" — Beer's preference.** Not generic AI-art. Every prompt should blend 2-3 styles:
   - Anime / manga aesthetic (Cowboy Bebop, Studio Ghibli)
   - Dark / cyberpunk tech (neon, Blade Runner, Tron)
   - Documentary realness (film grain, Fujifilm colours, real Cork settings)
   - Cinematic (emotional lighting, depth, story in the frame)

   **What Beer rejected:** "don't use from gemini so bad" — no generic "cinematic digital art" prompts.
   **What Beer wants:** "mix over" — edgy, mixed-style, with actual soul and specific references.

4. **Deliver inline** in the chat so Beer can copy-paste into Midjourney / DALL-E / any gen tool

Example format from real session (updated — "mix over" style):

```
### 1️⃣ Origin Story
> **Visual:** A figure sitting up in a dark hospital room, IV drip in one hand, laptop glowing neon blue on their lap. Transparent digital ghost-like agents floating around. Rain on the window. Neon pink and deep indigo light. Cowboy Bebop meets Blade Runner.
> **Prompt:** "A figure sitting up in a dark hospital room, IV drip in one hand, laptop glowing neon blue on their lap. Transparent digital ghost-like agents float around the bed — one with a crown, one with glowing eyes. Rain streaks down the window. Neon pink and deep indigo light. Cowboy Bebop meets Blade Runner. 4K, cinematic, emotional."

### 2️⃣ Sak Family
> **Visual:** A round table in a dimly lit hall, 6 floating holographic figures — crowned king, all-seeing eye, speech bubble, lotus, sun, star. Each pulses with a different neon colour. Dark wood and warm light. Studio Ghibli meets Tron.
> **Prompt:** "A round table in a dimly lit hall, 6 floating holographic figures — a crowned king, all-seeing eye, speech bubble, lotus flower, sun, and a star. Each pulses with a different neon colour. The room is dark wood and warm light. Studio Ghibli meets Tron. Rich shadows, luminous details."

### 3️⃣ How-To / Building
> **Visual:** Bird's-eye view of a messy desk — mechanical keyboard, coffee rings, sticky notes, code on screen. Grey Irish daylight through window. Documentary style, slightly desaturated, film grain.
> **Prompt:** "Bird's-eye view of a messy desk — two monitors, mechanical keyboard, coffee ring stains, sticky notes everywhere. Code reflects on the screen. A pair of hands typing. Real Cork apartment lighting — grey Irish daylight through the window. Raw, unfiltered, documentary style. Slightly desaturated, film grain."

### 4️⃣ Behind the Scenes
> **Visual:** A corner of a small room. Second-hand desk, plants on windowsill, fairy lights, Thai snacks shelf. Early morning sun. Fujifilm colour recipe, 35mm feel. Homesick but hopeful.
> **Prompt:** "A corner of a small room in Cork. Second-hand desk, plants on the windowsill, fairy lights, a shelf with Thai snacks and instant noodles. Laptop open on a video call. Early morning sun coming through. Aesthetic but real. Homesick but hopeful. Fujifilm colour recipe. 35mm feel."

### 5️⃣ House of Sak Brand
> **Visual:** A simple geometric doorframe floating in a dark void. Code and circuits on one side, warm golden light and a hand reaching through on the other. Purple and teal gradients. Minimalist. Apple keynote meets sci-fi movie poster.
> **Prompt:** "A simple geometric doorframe floating in a dark void. On one side: code and circuits. On the other: warm golden light and a hand reaching through. Purple and teal gradients. Clean lines, minimalist. Apple keynote meets sci-fi movie poster."

### 6️⃣ Reflection
> **Visual:** Storm clouds breaking apart over the Atlantic, Cork coast. Golden sunset through clouds. A person standing on a cliff. Shot on old film camera, slightly overexposed sky. Peace. Alive.
> **Prompt:** "A person standing on a cliff overlooking the Atlantic, Cork coast. Storm clouds breaking apart, golden sunset breaking through. Wind in their hair. No dramatic poses — just standing. Real, contemplative, alive. Shot on an old film camera. Slightly overexposed sky. Peace."
```

**Rule:** Never just say "image gen failed." Always provide the prompts as the fallback. Beer explicitly asks for "6 pic about and prompt send it to me" — the prompts ARE the deliverable when images can't be generated.

## Pitfalls

1. **Don't propose 12-week plans for personal brand.** Beer rejected this explicitly. Default to hours.
2. **When image gen fails, prompts are the fallback, not silence.** Write them out — one per concept, with visual description + prompt text.
3. **Don't write generic "cinematic digital art" prompts.** Beer called this "gemini" — too generic. Every prompt must mix 2-3 specific style references (anime + cyberpunk, documentary + film, minimalist + sci-fi).
4. **YouTube upload is blocked via Composio.** Say this upfront in hour 9-10: "I can prep the metadata but you'll need to upload the file at youtube.com/upload."
5. **Don't over-engineer the plan.** 12-hour blitz means straight execution, not research phases.
6. **"6 pics and prompt" equals 6 distinct images with 6 distinct prompts.** Not a single prompt repeated. Every image covers a different content bucket.

## Related

- `saksit-social-platform-audit/references/real-audit-2026-07-06.md` — the audit that preceded this session's blitz
- `saksit-social-platform-audit/references/archive-to-google-drive-example.md` — pattern for saving results to Google Drive after the blitz
- `saksit-social-media-posting-workflows` — posting execution (run AFTER the blitz)
