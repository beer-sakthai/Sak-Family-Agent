# Cross-Platform Content Adaptation — Confirmed 2026-07-07

When a single story draft needs to go to **LinkedIn, Instagram, AND Facebook** (different formats, different audiences), use this adaptation pipeline.

## When to Use

- Draft exists in `diaries/saksee/` or `house-of-sak/` as markdown
- Beer says "go" / "do all" / "all those of your suggestion" — meaning publish everywhere
- The content is story-based (manifesto, origin, behind-the-scenes)

## Pattern Proven This Session

**Source:** `diaries/saksee/03-why-we-do-it.md` (3KB markdown)
**Results:** LinkedIn + Instagram + Facebook published within 5 minutes — 3 platforms, 1 story.

---

### Step 1: Clean the Draft

The draft comes from a sibling agent (SakSee) and may have formatting artifacts from the repo:

| Artifact | Fix |
|----------|-----|
| `*$*bold text**` | Replace `*$*` with `**` (extra `*` from base64 decoding) |
| Double trailing `**` in author line | Normalize to single `**` |
| Section headers with `#` but missing spaces | Keep markdown structure, convert to plain text for IG/FB |

**Tool:** `execute_code` with base64 decode to read, then `patch` or manual cleanup.

---

### Step 2: Adapt per Platform — 3-Platform Pipeline

#### LinkedIn Version (long-form)
- **Format:** Long-form text post (up to 3,000 chars)
- **Image:** Optional — text-only works well for heavy story content
- **Structure:** Keep original section headers as plain text → `## Section` → "Section"
- **CTA:** End with Pieta 1800 247 247 + Samaritans 116 123
- **Author sig:** Name, location, year
- **Achievement footer:** Append Beer's profile badges (HF, Google Skills Diamond, Dev Program Premium, MS Learn L12)
- **Visibility:** PUBLIC
- **Tool:** `LINKEDIN_CREATE_LINKED_IN_POST` with `author=urn:li:person:<id>` and `commentary`

**Confirmation:** Returns `urn:li:share:<id>`

#### Instagram Version (short + visual)
- **Format:** Photo post (image + caption)
- **Caption length:** Truncate to ~1,000–1,500 chars (keep the emotional arc, cut detail)
- **Structure:**
  - Hook (first 125 chars = visible before "more")
  - Body (3-4 short paragraphs)
  - CTA (MH resources)
  - Achievement footer
  - Hashtags (URL-encoded with `%23`)
- **Image options (priority order):**
  1. Pre-existing IG card from repo (`ig-card.png` or `ig-card-v2.png`) — first choice
  2. `og-image.png` from repo root — good fallback, clean visual
  3. Google Drive photo from Beer — if story needs a personal photo
- **Tool:** `INSTAGRAM_POST_IG_USER_MEDIA` → `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`

**Confirmation:** Returns published media ID; verify via `INSTAGRAM_GET_IG_USER_MEDIA`

#### Facebook Version (medium + link)
- **Format:** Text/link post — shorter than LI, slightly longer than IG. Include the YouTube video link as the anchor.
- **Structure:**
  - Hook (same opening as IG/LI — the ICU story)
  - Body (the 6 agents list — bullet-friendly on FB)
  - YouTube link (the same video from the blitz)
  - MH resources (Pieta + Samaritans)
  - Hashtags (raw `#` works on Facebook, unlike IG)
- **No image needed** — the YouTube link generates a preview card on Facebook
- **Tool:** `FACEBOOK_CREATE_POST` with `page_id`, `message`, `link`, `published: true`

**Confirmation:** `FACEBOOK_GET_POST` with `post_id` returns `permalink_url`.

**Note:** Unlike Instagram (2-step container flow), Facebook is **1-step** — the post goes live immediately with `published: true`.

---

### Step 3: Publish in Parallel

All API calls are **independent** — batch what you can:

```json
COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[
    {tool_slug: "LINKEDIN_CREATE_LINKED_IN_POST", arguments: {commentary, visibility}},
    {tool_slug: "FACEBOOK_CREATE_POST", arguments: {page_id, message, link, published: true}}
  ]
)
```

Then publish the IG container (second step after container creation).

---

## Key Differences Across 3 Platforms

| Dimension | LinkedIn | Instagram | Facebook |
|-----------|----------|-----------|----------|
| **Length** | Full (up to 3,000 chars) | Condensed (~1,000–1,500 chars) | Medium (~800–1,200 chars) |
| **Image** | Optional | Required | Not needed (link preview) |
| **Hashtags** | Optional, bottom | URL-encoded with `%23` | Raw `#` works |
| **MH Resources** | In post body footer | In caption body | In message body |
| **Tone** | Professional vulnerability | Raw, immediate | Community + personal |
| **Flow** | 1-step | 2-step (container → publish) | 1-step |
| **Key addition** | Achievement footer | Visual + hashtags | YouTube link as anchor |

## Post-3 Manifesto Example (this session)

**LinkedIn:** Full manifesto — 5 sections preserved, author sig, MH resources, PUBLIC visibility, achievement footer.
**Instagram:** Shortened to ~1,200 chars — hook (ICU), middle arc (building from nothing), closer (not going back), hashtags. Image used: `og-image.png` from repo.
**Facebook:** Medium-length — same hook, agent list as bullets, YouTube link as the post's link anchor, MH resources, raw hashtags. Published to House Of Sak page.

## Pitfalls

- **Don't post identical text to multiple platforms.** Each platform's audience expects a different format. Adapt tone AND length.
- **Hashtags on Instagram must be URL-encoded** (`#` → `%23`). Raw `#` in the caption breaks the API.
- **Check which repo image is available** — `ig-card.png` may already be used for a previous post. `og-image.png` is the fallback.
- **LinkedIn has a 3,000 char limit** on `commentary`. If the draft exceeds it, cut detail paragraphs, not the emotional core.
- **Instagram's daily quota is 100 API posts** (confirmed 2/100 used as of Jul 7). Check before posting.
- **Facebook page ID must be obtained via `FACEBOOK_LIST_MANAGED_PAGES` first.** House Of Sak page ID: `1249135251607068`. Hardcode after first lookup.
- **Facebook post returns composite ID** (`PageID_PostID` format) — store both parts for follow-up operations.
- **Cross-platform consistency:** The story arc (ICU → shelter → building → MH resources) must stay intact across all 3 versions. Cut details, never cut the emotional core.
