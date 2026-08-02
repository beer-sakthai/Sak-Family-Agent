---
name: SakSit-social-platform-audit
description: "Audit all connected social platforms before posting."
---

# Social Platform Audit — Pre-Posting

> ⚠️ **Environment constraint:** This audit requires Composio MCP tools. In the current DeepSeek-V4-Flash (opencode-go) environment, Composio MCP is **not connected** — this skill serves as reference documentation. A live audit requires a Composio-enabled Hermes session.

Before ANY content planning or posting, audit every connected platform.
Beer explicitly rejects curated "top picks" — he wants the full landscape,
every platform audited with pros/cons, then we choose together.

## When to Run

- "plan for social" / "social plan"
- "what platforms can we post to"
- "what can you do in/on [platform]"
- "post this to social media"
- Any mention of posting without specifying a platform
- Any mention of a specific platform's capabilities (YouTube, Instagram, etc.)

## Audit Workflow

### Step 1 — Scan ALL platforms

Use `COMPOSIO_SEARCH_TOOLS` to discover every connected social toolkit:

```
session: {generate_id: true}
queries: [{
  use_case: "list all connected social media apps and available tools for posting content"
}]
```

Parse the `toolkit_connection_statuses` from the response. Note each toolkit name,
its active/inactive status, and the account/user info.

> **Do NOT filter or rank yet.** Complete inventory first.

### Step 2 — Pull identity data from EVERY platform in parallel

Use `COMPOSIO_MULTI_EXECUTE_TOOL` to query identity endpoints simultaneously.
Batch all independent calls into a single multi-execute:

| Platform | Tool | What you get |
| Platform | Tool | What you get |
| LinkedIn | `LINKEDIN_GET_MY_INFO` | Name, URN, profile picture |
| Instagram | `INSTAGRAM_GET_USER_INFO` (ig_user_id="me") | Username, followers, follows, account type, media count |
| Facebook | `FACEBOOK_LIST_MANAGED_PAGES` | Page names, IDs, categories, permissions |
| YouTube | `YOUTUBE_GET_CHANNEL_STATISTICS` (id or forHandle with part="snippet,statistics,brandingSettings") | Sub count, video count, view count, description, branding settings, avatar |
| Reddit | (from search response) | Username, karma, account age |
| Hugging Face | `https://huggingface.co/api/whoami-v2` (HTTP GET with HF_TOKEN) OR browser_navigate to profile page | Name, bio (if any), websiteUrl, orgs, signup links (GitHub/LI/Twitter) |
| Gmail | `GMAIL_FETCH_EMAILS` (query="is:unread", max_results=10) | Total messages, unread count, recent subject lines — reveals newsletter overload, missed DMs, pending replies |

Also check rate limits where available:
```
INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT
Returns quota_usage vs quota_total — know your cap before planning
```

### Step 3 — Build pros/cons for EACH platform with REAL data

For every platform found, answer two questions:

| Question | What to check |
|----------|---------------|
| ✅ **What's working?** | Followers count, permissions level, daily quota remaining, content type fit |
| ❌ **What's blocking?** | Karma too low, missing tools, URL constraints (e.g. no S3 signed URLs), rate limits hit, account too fresh |

**Common constraints found in real audits:**
- **Reddit:** Account may have 1 karma — functionally unusable in most subreddits, AutoModerator silently removes posts
- **Instagram:** Requires public HTTPS URLs **without query strings** — AWS S3 signed URLs fail, needs direct image URLs. **Fix:** host images on GitHub and use `raw.githubusercontent.com` (no query params, Instagram accepts it). See `saksit-social-media-posting-workflows` → `references/github-raw-url-instagram-pattern.md`
- **LinkedIn:** `distribution` field is REQUIRED in post body via the Composio tool — missing it returns 422
- **Facebook:** Text/link posts only in basic `FACEBOOK_CREATE_POST` — photo/video needs separate endpoints
- **YouTube:** Can READ (search, stats, comments, captions) but CANNOT upload videos or edit channel metadata through current Composio tools — `YOUTUBE_UPDATE_CHANNEL` exists but only for description/keywords, not video upload
- **Hugging Face:** Can READ profile data via `huggingface.co/api/whoami-v2` with HF_TOKEN auth but CANNOT update bio/details through any API — all profile edits must be done manually at `hf.co/settings/profile` (CloudFront blocks automated browsers)

### Step 4 — Tier platforms into priority order

| Tier | Meaning | Criteria |
|------|---------|----------|
| **Tier 1 — Ship Now** | Fewest barriers, best ROI | No karma gates, generous limits, existing audience |
| **Tier 2 — Build First** | Real audience but needs prep | Has followers but tool/URL constraints to solve |
| **Tier 3 — Cross-Post** | Exists but cold start | Page exists but zero followers shown |
| **Tier 4 — Later** | Not usable yet | Account too new, too low karma, restricted |

### Step 5 — Present the full picture

Read back the complete audit — every platform, its pros/cons, and your
tiering rationale. Let Beer choose which platform to post to and what
content before executing.

## Step 6 — Archive to Google Drive (on user request)

After the audit, if the user asks to "save for later" or "remember my links":

1. **Compile the links** into a clean table with platform name, URL, and status
2. **Create a Google Doc** via `GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN`:
   - Title: `Social Media Links - [Brand Name]`
   - Include a Markdown table with all platforms, clickable URLs, and connection status
   - Add timestamp and any relevant notes (vanity URLs not set, follower counts, empty fields)
3. **Return the doc link** to the user so they can access it anytime

**Google Doc creation flow:**
```markdown
# Social Media Links — [Brand Name]

Last updated: [date]

| Platform | Link | Status |
|----------|------|--------|
| **LinkedIn** | https://linkedin.com/in/vanityname/ | Connected |
| **YouTube** | https://youtube.com/@handle | Connected |
| ... | ... | ... |

### Notes
- Any missing vanity URLs, low followers, or actionable gaps
```

**Pitfall:** Don't dump raw JSON or API response data into the doc. Curate it — platform name, clickable link, status badge. The doc is for Beer to lookup later, not for debugging.

## Step 7 — Post-Audit Setup (fill what's empty)

After the audit and archive, if the user wants to **actually fill in the gaps**:

### Facebook Page — settings (most actionable)
The Facebook page is typically the most updatable. Use `FACEBOOK_UPDATE_PAGE_SETTINGS`:
- `website`: The business URL
- `about`: Short tagline (e.g., "AI-powered brand agency")
- `description`: Longer description
- `emails`: Contact email array
- `phone`: Contact number

**Flow:**
1. Ask the user what website URL + bio they want
2. Update via `FACEBOOK_UPDATE_PAGE_SETTINGS(page_id=..., website=..., about=...)`
3. Verify by re-reading with `FACEBOOK_GET_PAGE_DETAILS`

### YouTube Channel — description (if YOUTUBE_UPDATE_CHANNEL available)
- Channel description with keywords
- But note: cannot upload videos via current Composio tools

### Other platforms (manual-only)
- Instagram, LinkedIn, Hugging Face profile edits are **manual only** (no API endpoint via Composio)
- Tell the user clearly: "This one needs to be done manually at [URL]" with the specific link

**Pitfall:** When image generation fails (missing FAL_KEY, etc.), **do not stop**. Write the image prompts as text descriptions and deliver them inline. Beer explicitly requests "6 pic about and prompt" — the concept descriptions + prompt text pairs ARE the deliverable when images can't be rendered. See `references/post-audit-launch-blitz.md` for the exact format.

## Step 8 — Post-Audit Launch Blitz (when Beer wants action)

After audit + archive + setup, Beer may ask for an **immediate action plan**. When he says "make list, plan, step, timeframe":

**Default to hours, not weeks.** Beer explicitly rejected a 12-week plan and demanded a 12-hour blitz.

Follow the pattern in `references/post-audit-launch-blitz.md`:

1. H1 — Fix all profiles (website, bio, images)
2. H2-3 — Generate 6 brand images (or write prompts as fallback)
3. H4-5 — Write 6 post copies (Origin, Sak Family, How-To, BTS, Client, Reflection)
4. H6-8 — Publish to Facebook, Instagram, LinkedIn
5. H9-10 — Video asset prep + YouTube metadata
6. H11 — Cross-post + schedule second loop
7. H12 — Verify everything, deliver links

**6 content buckets** for the post loop: Origin Story, Sak Family, How-To, Behind the Scenes, Client Work, Reflection. Each gets one image + one caption. Loop 2x (immediate publish + scheduled repost).

This is an execution blitz, not a strategy phase. Move fast.

**Pitfall:** Update one field at a time on Facebook — multi-field writes can 500. Use separate calls per field if a combined call fails.

## Example: Real Session Flow (2026-07-06)

What happened in a real session:
1. **Audit** → Found Facebook (empty page, 0 followers), YouTube (0 subs, 0 videos)
2. **Archive** → Saved all platform links to a Google Doc titled "Social Media Links - House of Sak"
3. **Setup** → User wanted to add website to Facebook page (deferred to next session)

The Google Doc pattern worked well: structured table, clickable links, status badges, notes for actionable gaps. Use this as the template for archive requests.

## Pitfalls

1. **Don't assume a connection works because the toolkit shows active.**
   Reddit may be connected but have 1 karma — you can't post in useful subreddits.
   Always check the actual account state, not just the connection status.

2. **Don't give "top 3".** Beer has explicitly rejected this. Show EVERY platform.

3. **Don't skip Instagram rate limits.** 25 API posts/day limit is enforced.
   Always check `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT` before planning.

4. **Don't skip the identity pull.** A connected toolkit might resolve to an
   unexpected identity — wrong Facebook page, personal vs business account,
   wrong Instagram account. Verify before planning content.

5. **"don't sure don't forget but learn from that"** — when uncertain about a
   platform's capabilities, check rather than guess. Recording what you learned
   (in memory, diary, or this skill) IS the output. The audit teaches you the
   landscape; capture that knowledge.

6. **Default to hours, not weeks, for Beer's personal brand.** When Beer asks
   "make a plan" for House of Sak / his personal profiles, propose a 12-hour
   blitz, not a 12-week quarter plan. He rejected 12 weeks explicitly. The
   hours timeline is for personal brand; B2B SaaS clients still get weeks/months.

7. **Instagram DM conversations may return errors for stale threads.**
   When checking INSTAGRAM_LIST_ALL_CONVERSATIONS, some conversation IDs may
   fail with `error code=100, subcode=33: Unsupported get request` — these are
   stale/bot conversations that no longer exist. Bundle ALL conversation reads
   in a single COMPOSIO_MULTI_EXECUTE_TOOL call and check per-result. Don't
   stop the workflow because one thread failed — only real active conversations
   return messages successfully.

8. **ElevenLabs connection troubleshooting — "elicitation" errors.**
   When ElevenLabs tools return `"Elicitation is unavailable for this session.
   Approve this tool in the Composio dashboard."` or later `"No response to
   elicitation prompt within the allowed time."`, the existing connection may
   show as "active" but the tools still fail. **The reliable fix is to create a
   fresh connection**, not just ask the user to approve in the dashboard:

   ```
   COMPOSIO_MANAGE_CONNECTIONS → action="add", alias="elevenlabs-<purpose>", name="elevenlabs"
   → Returns a redirect_url auth link
   → Share link with user, call COMPOSIO_WAIT_FOR_CONNECTIONS([elevenlabs])
   → Retry tools once connection becomes ACTIVE
   ```

   Error progression:
   - Before auth: `"Elicitation is unavailable for this session. Approve this tool in the Composio dashboard."`
   - After auth link created but not completed: `"No response to elicitation prompt within the allowed time."`
   - After successful reconnect: tools work normally.

   Subscription info returns on the free tier: `tier: "free", character_count: 0/10000,
   character_refresh_period: "monthly_period"`. 23 premade voices are available
   (including Brian-Deep, Harry-FierceWarrior, George-Storyteller, Sir Michael Caine™).

   **Pitfall:** Don't retry more than twice — the auth link is time-limited (~10 min).
   Generate a fresh link with COMPOSIO_MANAGE_CONNECTIONS if the previous one expired.

9. **Manus AI integration has task tools but no credit-check endpoint.**
   Manus (manus.im) is available via Composio with tools MANUS_CREATE_TASK,
   MANUS_GET_TASK, MANUS_LIST_TASKS, MANUS_CREATE_PROJECT, MANUS_LIST_PROJECTS.
   There is NO credit-balance/quota-check endpoint in the API. If the user asks
   about credits, explain this limitation — check credits via the Manus web
   dashboard.

## Example Output

This is what a real audit looks like (from 2026-07-06):

```
Platforms found: 5
├── LinkedIn → Tier 1 (Ship Now) — Nanthasit Burankum, full access
├── Instagram → Tier 2 (Build First) — @beerthaish, 906 followers, 0/100 quota
├── Facebook  → Tier 3 (Cross-Post) — House Of Sak Page, full manage, 0 followers
├── YouTube   → Tier 3 (Prep) — @nanthasitburankum, 0 subs, 0 videos, needs content
└── Reddit    → Tier 4 (Later) — u/Then-Chest-8704, 1 karma, not ready
```

## Related Skills

- `saksit-social-media-posting-workflows` — posting execution (run AFTER this audit)
- `Sak-instagram-content-kit` — Instagram content production
- `linkedin-content-publishing` — LinkedIn-specific posting details
- `saksit-milestone-content` — milestone visual + caption pipeline
- `saksit-tts-audio-production` — TTS audio for social content
- `saksit-social-platform-audit` — (self: first step before any posting)

## Support Files

| File | Purpose |
|------|---------|
| `references/real-audit-2026-07-06.md` | Complete real-audit output from the first-ever full platform audit |
| `references/youtube-audit-deep-dive.md` | YouTube-specific deep-dive: search, stats, competitor research, strategy |
| `references/profile-completeness-audit.md` | Profile completeness matrix: what fields are filled vs missing across ALL platforms, with update-tool availability |
| `references/huggingface-profile-audit.md` | Hugging Face profile constraints: read-only API, no update endpoint, all edits manual |
| `references/archive-to-google-drive-example.md` | Session example: archiving social media links to a Google Doc after audit — Markdown template, input structure, pitfalls |
| `references/post-audit-launch-blitz.md` | **2026-07-06 session.** 12-hour launch blitz pattern for Beer's personal brand — hour-by-hour plan, 6 content buckets, image-gen fallback to prompts, timeline preference (hours not weeks) |
