---
name: SakSit-social-media-posting-workflows
description: Post to Instagram, LinkedIn, Facebook via Composio.
category: social-media
author: SakSit Agent (beer-sakthai)
tags:
- Instagram
- LinkedIn
- Facebook
- social media
- Composio
- posting
- file-upload
created: 2026-07-05
updated: 2026-07-23
---

# Social-Media Posting Workflows 2026

> ⚠️ **Environment constraint:** This workflow requires Composio MCP tools. In this DeepSeek-V4-Flash (opencode-go) environment, Composio MCP is **not connected**. The content below remains the authoritative reference; actual posting requires a Composio-enabled Hermes session or manual platform use.

A practical playbook for planning a content series AND posting text+image to Instagram,
LinkedIn, and **Facebook** via Composio MCP, including file-upload workarounds, two-step
Instagram process, Facebook batch posting patterns, and manual-image fallbacks.

** referencing file-upload-debug.md for deeper debugging if API failures occur.

---

## Beer's Brief Request Decoder

Beer communicates in ultra-short fragmented messages — typically 3–6 words. A query like
`"Pictures 12 pic you post all?"` is standard. When you receive one:

1. **Assume it refers to something recently discussed** — last session's topic is the first place to look.
2. **Default to action, not discussion.** Beer's short messages are commands or yes/no questions, not open-ended conversation starters.
3. **Limit clarification to 1 message, ≤3 options.** If after 1–2 `session_search` calls there's no context, ask directly. Don't burn 5+ tool calls searching before responding.
4. **Use stored preferences silently.** IG ID, profile links, account details — already in memory, don't re-ask.
5. **"Record and save" means persist to both stores.** When Beer says "record and save the now" or similar, write a compact session summary to both supermemory and Hermes `memory`, then continue executing. Don't stop to ask what to record.
6. **Continuous execution mode.** Once Beer signals "go" / "do all" / "the whole set" — you are in continuous execution mode. Execute everything that can be done without more input. Only stop to deliver a structured status report when a task batch completes or a blocker genuinely needs his input. Do not end a turn with "what next?" — state the next logical step.
7. **Tone: positive vision vibe, hopeful, House of Sak-focused.** Beer confirmed content should centre the mission and the family, not the trauma. Lead with hope and a forward-looking vision. "Positive vision vibe" = uplifting, future-focused, dreams-not-trauma. Long-form is fine. The dark moment is context for the build, not the punchline. When asked to pick a tone, default to this hopeful/visionary framing.
8. **Every IG feed post = Story too.** When you post an image to the Instagram feed, always also create a Story with the same image. Use media_type="STORIES", no caption needed. This is non-negotiable — Beer explicitly set this rule.
9. **Zero cost, always, on everything.** Beer is homeless, no income, has a fiancé. Any paid API, service, or tool = stop, ask permission, report free alternatives. Never assume a service is free without verifying. All Composio-connected tools are free — use those.
10. **Sign DMs when replying on Beer's behalf.** When Beer says "reply" and you send a DM via `INSTAGRAM_SEND_TEXT_MESSAGE`, always make clear it was written by SakSit (his AI agent), not by Beer himself. Add a transparent signature in the message or as a follow-up. Never let the recipient think Beer typed it.
11. **Personal mental health content = Story-only by default.** When Beer shares about his own mental health (not the origin story, but "today is hard" type posts), default to IG Story only unless he specifies otherwise. These are personal moments, not campaign content.

### Common Decoding Table

### Common Decoding Table

| Beer says | Likely meaning |
|-----------|---------------|
| `"X pic you post all?"` / `"X pic post all?"` | "Did you post all X pictures?" |
| `"X pic about and prompt"` | "Generate X pictures and show me the prompts" |
| `"Content"` | Run the **content-source-check** skill — scan Drive + session history + memory before generating. Report findings, don't jump to production. |
| `"plan"` / `"social plan"` | "Build or show the content plan" — don't ask what plan |
| `"12 hours no weeks"` | "12-hour sprint, not 12-week campaign" |
| `"just post"` / `"post"` (after content is ready) | Execute immediately on ALL connected platforms (IG + LI + FB). Default to all three. Do not post one and wait. Beer's signal: "No Facebook?" means you missed it. Don't ask which platform. Don't read caption aloud. Over-asking frustrates Beer. Content approval on one platform = approval for all. |
| `"GO"` / `"trust X"` | Proceed with your best judgment on the current task |
| `"pro whole set"` / `"do all"` / `"the whole set"` / `"all those of your suggestion"` | **Execute ALL identified tasks simultaneously. Don't ask which to prioritize.** This is Beer's strongest execution signal — he wants every option in the plan executed in parallel. `"all those of your suggestion"` is a variant meaning "yes to all options proposed" — same behavior. |
| `"plan?"` (solo, opening message) | "What's our current state? Give me a concise status update." Not a request to build a new plan — audit what exists and report. |
| "record and save the now" / "record and save" | Persist session state to memory + supermemory + Google Drive, then continue executing. Drive backup is mandatory — upload SOUL.md, LEARNING_JOURNAL.md, and key session files. Don't ask where to save. |
| `"something in [platform] can [action] also"` | Beer is telling you about a native cross-platform feature. Act on it immediately — if a post went to Platform A and he says it can reach Platform B too, post the same content to Platform B using available tools. |
| `"don't wait keep do do do"` / `"keep do do do"` | Full-speed continuous execution. Do not pause between steps. Batch everything possible. Deliver partial progress rather than stalling. |

### Operating Principles

1. **Parallel execution over sequential selection.** When Beer says "the whole set" / "pro whole set" / "do all" / "all those of your suggestion" — execute every identified task simultaneously. Batch independent operations via `COMPOSIO_MULTI_EXECUTE_TOOL` and `delegate_task`. Never ask "which one first?" — do them all.
2. **Report blockers once, keep executing.** If one task in a batch fails, document it and continue executing the rest. Deliver a structured summary of what completed, what blocked, and what needs his input. Don't loop on a failing tool — switch to an alternative or note it and move on.
3. **Status report as delivery, not handoff.** After executing a batch of tasks, deliver a complete status summary. Don't end with "what next?" — state the next logical step based on outcomes.

### Pitfalls

- **Over-searching.** 5+ `session_search` calls before replying wastes tokens and delays response. If 1–2 don't hit, clarify directly.
- **Verbose clarification.** Keep to 1–2 sentences. Offer options as a compact table or short unordered list.
- **Re-asking stored facts.** Beer's account IDs, platform handles, and style preferences are in memory — use them silently.
- **Treating fragments as full sentences.** A Beer query is a stem — infer the verb from context. `"Pictures 12 pic you post all?"` ≈ `"Did you post all 12 pictures we discussed?"`
- **Asking which task to do first.** When Beer says "the whole set" / "pro all" / "do it all" / "all those of your suggestion" — execute EVERY option simultaneously. Do not re-ask for priority.
- **Stopping on a single blocker.** If one task in a batch fails, complete the rest and report the blocker separately. A partial delivery is better than a stalled turn. If the blocker has a workaround, flag it for Beer in the final report.

---

## Multi-Source Content Discovery (Pre-Posting Prep)

Run this BEFORE content planning whenever Beer says "plan" or before posting
to any platform. Scans every source where assets may already exist — saves you
from duplicating work sibling agents already did.

### When to trigger

- "plan [and] photo" / "draft a plan and photo"
- "check google drive" / "check google photos"
- "check [sibling agent]" / "check Sak Agent"
- Before any Instagram post — sibling agents often prep IG cards but never publish them

### Scan workflow (run these in parallel)

#### 1. GitHub Repo — `beer-sakthai/house-of-sak`

Use `GITHUB_GET_A_TREE` (owner="beer-sakthai", repo="house-of-sak", tree_sha="main", recursive=true)
to scan for pre-existing assets:

| What | Where | Meaning |
|------|-------|---------|
| `ig-card.png` | Root `/` or `diaries/saksee/` | Visual card prepped by sibling |
| `ig-caption.txt` | Root `/` or `diaries/saksee/` | Caption prepped by sibling |
| `og-image.png` | Root `/` | Generic visual — good IG fallback when specific card is already used |
| Sibling diary dirs | `diaries/saksee/`, `diaries/saktan/`, `diaries/sakjules/` | Work done by other agents (drafts, research, manifests) |
| Numbered drafts | `diaries/saksee/` (e.g. `03-why-we-do-it.md`) | Content series drafts that need cross-platform adaptation |

**Key insight:** Sibling agents (especially SakSee) often prepare Instagram
assets that get committed to the repo but **never actually published**. Always
check before creating new assets from scratch.

#### 2. Google Drive — Beer's photos

Use `GOOGLEDRIVE_FIND_FILE`:
```
q: "mimeType contains 'image/' and trashed = false"
orderBy: "modifiedTime desc"
```
Beer creates his own images — the most recent photo is usually what he wants
to use. Note file names, dates, and sizes.

#### 3. Google Drive — Video files

When Beer wants to post a video (e.g. to YouTube), search his Drive:
```
q: "mimeType contains 'video/' and trashed = false"
orderBy: "modifiedTime desc"
```
Video files (mp4, mov, webm) are usually AI-generated clips, screen recordings,
or produced House of Sak content. Report name, size in MB, and modified date.
Key files found (as of Jul 7):
- `The AI Agency Built in a Homeless Shelter.mp4` (5.3 MB)
- `The_Architecture_of_Survival__Inside_the_House_of_Sak.mp4` (35.7 MB)
- `The_Empathy_Engine.mp4` (44.9 MB)
- Various AI-generated sample clips (11–14 MB each)

#### 4. Google Drive — "Sak Agent" folder

Find via `GOOGLEDRIVE_FIND_FILE` with `q: "name contains 'Sak Agent'"`.
Contains:
- `The_House_of_Sak` — Google Slides presentation (19.5MB, modified Jul 6)
- `The_House_of_Sak.pdf` — PDF export (16.2MB, modified Jul 6)

This is Beer's presentation deck — potential source of visuals, slide content,
or story elements for social posts. Always note the modified date — Beer may
have updated it today.

#### 5. Supermemory connection check

Before presenting findings, verify supermemory is reachable:

1. Call `supermemory_profile()` or `supermemory_search()` with a test query
2. If **402 (credits exhausted)** → fall back to Hermes `memory` tool for all
   persistent storage in this session. The `memory` tool is the reliable fallback.
3. Save key findings to BOTH stores when supermemory is available; use `memory`
   exclusively when supermemory returns 402. Never skip saving.

**Pattern:** Supermemory = primary durable store. `memory` = fallback on 402.
Always try supermemory first, fall back silently, never abandon persistence.

#### 6. Present to Beer

Read back your findings:
- "Found existing IG card and caption from [sibling] — ready to use (Option A)"
- "Found [N] photos on Google Drive — most recent is [name] from [date] (Option B)"
- "Found a House of Sak presentation in Sak Agent folder"

### Pitfalls

- **Don't generate AI images for final posts.** Beer creates his own.
  `image_generate` is for concept drafts only.
- **Don't assume sibling-prepped assets were posted.** They're often committed
  but never published. The `raw.githubusercontent.com` URL for repo-hosted images
  is a ready-to-use Instagram media URL (no query params — Instagram rejects those).
- **DeepSeek has no vision.** You can't analyze images inline. Read the caption
  text and describe the image concept instead.
- **Google Drive signed URLs with query params fail on Instagram `image_url`.** Use Strategy C or D instead (s3key via image_file parameter).
- **Supermemory credits may be exhausted (402) mid-session.** Always verify
  supermemory is reachable before attempting a write. If 402, the `memory` tool
  is the reliable fallback — use it without hesitation. Never skip persistence
  because supermemory is down.

---

## Content Series Planning (Pre-Posting)

Use this section when Beer asks about a "social plan", "content plan", "schedule",
or "where is the plan" — i.e. the scheduling layer that sits before individual posts.

### When to trigger

Any of these phrases means run the planning workflow:
- "plan for social" / "social plan"
- "where is the plan" / "find the plan"
- "content calendar" / "posting schedule"
- "what should I post next" / "next post"

### Planning workflow

1. **Audit drafted content** — scan `house-of-sak/` for numbered drafts (`NN-title.md`).
   Also check memory/supermemory for any previously discussed but unsaved post ideas.

2. **Build the calendar** — for each draft, decide:
   - Platform(s): LinkedIn, Instagram, Reddit, Facebook?
   - Posting date — space posts 2–3 days apart minimum.
   - Format adaptation per platform (image size, caption length, hashtags).

3. **Populate `content-calendar-template.md`** — write real rows with titles, platforms,
   scheduled dates, and status. Replace the empty template with a working calendar.

4. **Read it back to Beer verbatim** — he cannot read on-screen. Say:
   - "Here's the plan: [Post 1 title] goes to [platform] on [date], [Post 2 title] to [platform] on [date]..."
   - Ask: "Does this schedule work?"

5. **Execute per schedule** — on each posting day, run the relevant posting workflow
   (Instagram or LinkedIn section below). Update the calendar status to ✅ Published
   with the live URL after each post.

6. **Update the calendar after every post** — don't wait; mark done immediately so
   the next session picks up the correct state.

### Pitfalls

- **Empty template = no plan.** If Beer asks for "the plan" and the calendar reference
  has no rows, you haven't done step 2–3 yet. Build the calendar immediately.
- **Don't ask "what plan?"** — Beer has said it exists or wants one. Audit house-of-sak/
  for draft content and build the calendar without asking him to repeat himself.
- **Read aloud every time.** Beer confirmed he cannot read on-screen. After building
  or updating the calendar, always read the full schedule back verbally.

### Content Story Progression (House of Sak)

Proven story sequence for Beer's brand content (validated through Post 1-4 execution):

| Phase | Post | Topic | Image Asset | Platform Mix |
|-------|------|-------|-------------|-------------|
| 1 | Origin | April 15 — the day it all started | `15AprilThatAllStart.png` | LI + IG + FB |
| 2 | Shelter | Building AI from a homeless shelter in Cork | `FromASHelterInCork.png` | LI + IG + FB |
| 3 | AI with Heart | Tools are cold, companions aren't | `AiCare.png` | IG + FB |
| 4 | Manifesto | Companions, not just tools — core message | `CompanionNotJustTools.png` | LI + IG + FB |
| 5 | Builder | Beer actually building, programming | `PhotoBeerWriteProGram.png` | IG + FB |
| 6 | The Family | 6 souls, one mission | `TheHouseOfSak6Souls1mission.png` | LI + IG + FB |

**Image asset mapping (as of Jul 8):** Beer uploaded these 6 named PNGs to Google Drive. Their filenames ARE the content brief. Each maps to one post in the progression. Additionally, 6 agent profile PNGs (SakKing/See/Sit/Tan/Thai/Jules-Profile.png) are available for individual agent spotlights.

**Key principle:** Each post works standalone but fits a sequence. Start vulnerable (origin), then context (shelter), then heart (AI with care), then philosophy (companions), then evidence (builder), then family (the House). Each image filename tells the story step.

### Sequential Posting via Cron (Spaced Series)

When Beer wants a series of posts at intervals (e.g. "30 min apart from each post"):

1. **Post the first item immediately** in the current session — never delay the first one for cron setup.
2. **Create a state JSON file** at `~/profiles/saksit/scripts/<series-name>-state.json` — see `references/agent-carousel-state-schema.md` for the exact schema. Track agents array (name, role, description, emoji, drive_file_id, per-platform posted flags), next_index (0-based), posted array, total.
3. **Create a cron job** with schedule=`"30m"`, repeat=`N-1`, deliver=`"origin"`, and a self-contained prompt that includes reading state, downloading fresh from Drive, posting to all 3 platforms, and updating state.
4. **CRITICAL**: Each cron tick must download a fresh image via `GOOGLEDRIVE_DOWNLOAD_FILE` — s3keys expire in ~1 hour. File IDs in Drive are permanent.
5. **State file update from cron:** `execute_code` is blocked for cron jobs (requires interactive approval mode). Use `write_file` to write the updated JSON state directly instead.

**Confirmed 2026-07-08:** All 6 agent profile posts across Instagram + LinkedIn + Facebook, 30 min apart, fully automated.

---



## Getting Started

When you need to post:

1. **If Beer said "just post" / "post" / approved the caption** — execute immediately on ALL platforms (IG + LI + FB). Do NOT re-ask for content.
2. **If no content exists yet** — draft from context (previous chat, Drive assets, topic mentioned). Deliver for review, don't ask "what should I write?"
3. **If image in Drive** — fetch via GOOGLEDRIVE_DOWNLOAD_FILE, use s3key pipeline. Don't ask where it is.
4. **If Beer sends his own image in chat** — use THAT image, not an AI-generated or Pillow version. Upload it to GitHub raw and use the URL. Beer will correct you if you substitute his image with a generated one.
5. **Ask ONCE max** — one question: "What's the post about?" Then draft.
6. **Multiple tones** — for emotional/creative topics, offer 2-3 tone versions (raw, poetic, riddle, Shakespeare). Default to "positive vision vibe" if unsure.

**"just post" overrides everything above.** If content was discussed, execute immediately.

---

## Instagram Posting

Instagram requires **two steps**:
1. Create a media container (`INSTAGRAM_POST_IG_USER_MEDIA`)
2. Publish the container (`INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`)

### Strategy A: Image has a public HTTPS URL

**Confirmed cross-platform (2026-07-29):** `raw.githubusercontent.com` URLs work for ALL three platforms — Instagram (feed + story), Facebook photo post, and LinkedIn text post (image via link). No s3key needed. Upload once to GitHub, use the same `image_url` across all platforms.

#### Step 1: Create container

```json
{
  "ig_user_id": "<numeric-id>",
  "caption": "...",
  "image_url": "https://example.com/image.jpg"
}
```

- `ig_user_id` = numeric Instagram ID (e.g. `27647006041564332`)
- `image_url` = **direct HTTPS**, no query strings
- `media_type` = **For standard image feed posts, omit `media_type` entirely** (auto-inferred as IMAGE). Only pass it for non-feed formats: `"STORIES"`, `"REELS"`, or `"CAROUSEL"`. **`"IMAGE"` and `"POST"` are both rejected** by the API — confirmed 2026-07-08.

#### Step 2: Publish

```json
{
  "ig_user_id": "<numeric-id>",
  "creation_id": "<container-id>",
  "max_wait_seconds": 30
}
```

Wait for container to reach `FINISHED` status before publishing.

---

### Strategy B: Image is local (COMPOSIO FILE UPLOAD PATTERN)

Composio’s Instagram tool expects `image_file.s3key`, which is an **internal reference** — not a filename.

**Correct workflow:**

1. **First**, register the image with LinkedIn (`LINKEDIN_REGISTER_IMAGE_UPLOAD`) — this creates a Composio reference
2. **Then**, use that reference in Instagram’s `image_file.s3key` field

**Sketch:**

```python
# 1. Register upload (gets upload information)
resp = COMPOSIO_MULTI_EXECUTE_TOOL(
  tools=[{"tool_slug": "LINKEDIN_REGISTER_IMAGE_UPLOAD", "arguments": {"owner_urn": "..."}}]
)
upload_url = resp["results"][0]["data"]["upload_url"]
asset_urn = resp["results"][0]["data"]["asset_urn"]

# 2. Upload bytes to upload_url (curl / direct PUT outside Composio)
# curl -X PUT -H "Content-Type: image/png" --data-binary @image.png "$upload_url"

# 3. Use asset_urn in Instagram call as file reference
```

**Note:** As of 2026-M07, there is **no direct local-file upload** for Instagram via Composio.
The workaround is to reuse LinkedIn’s upload infrastructure.

### Strategy C: Google Drive Image → Composio s3key → Instagram (CONFIRMED WORKING 2026-07-07)

When the image lives in Beer's Google Drive and you need to post it to Instagram without a clean public URL:

**Step 1 — Download from Drive:**
```json
{
  "tool_slug": "GOOGLEDRIVE_DOWNLOAD_FILE",
  "arguments": {"fileId": "<google-drive-file-id>"}
}
```
Returns `downloaded_file_content` with `name`, `mimetype`, and `s3url`.

**Step 2 — Extract the s3key from the s3url:**
The s3url has the format: `https://temp.<bucket>.r2.cloudflarestorage.com/<account-id>/<toolkit>/<tool-slug>/response/<hash>?X-Amz-...`
Extract the path after the bucket (`<account-id>/<toolkit>/<tool-slug>/response/<hash>`) — this IS the s3key.

In Python:
```python
from urllib.parse import urlparse
parsed = urlparse(s3url)
path = parsed.path  # e.g. /631637/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/a7307c1dd...
s3key = path.lstrip('/')  # 631637/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/a7307c1dd...
```

**Step 3 — Create Instagram container with image_file:**
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "<numeric-id>",
    "caption": "...",
    "image_file": {
      "name": "<filename.png>",
      "mimetype": "image/png",
      "s3key": "<extracted-s3key-from-step-2>"
    }
  }
}
```

**Step 4 — Publish:**
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
  "arguments": {
    "ig_user_id": "<numeric-id>",
    "creation_id": "<container-id-from-step-3>",
    "max_wait_seconds": 60
  }
}
```

**Key insight:** The s3url returned by `GOOGLEDRIVE_DOWNLOAD_FILE` is an S3 signed URL with query params (rejected by Instagram's `image_url`), but the path portion works as the `image_file.s3key` because the file was stored in Composio's internal S3. Instagram's tool then re-hosts it to a clean temporary URL internally.

**Pitfalls:**
- The s3url is time-limited (3600s expiry on the signed URL), but the s3key reference persists as long as Composio retains the file
- Not all Composio download tools return `downloaded_file_content` with usable s3url — `GOOGLEDRIVE_DOWNLOAD_FILE` does (confirmed)
- When extracting the s3key from the URL path, include everything after the leading `/` — the full path including the account prefix
### Strategy D: Any Image File → upload_local_file() s3key → Instagram (CONFIRMED WORKING 2026-07-07)

When the image file is accessible in the Composio workbench sandbox filesystem (downloaded via curl,
copied from Google Drive, etc.) and you need an s3key to use with Instagram's `image_file`:

**Step 1 — In the workbench, upload the file to Composio's S3 storage:**
```python
result, error = upload_local_file("/home/user/image.png")
# Returns: {"s3key": "project/.../pIsI6VHmzL7W", "s3_url": "https://backend.composio.dev/api/v3/sl/..."}
s3key = result["s3key"]  # Use this as image_file.s3key
```

**Step 2 — Create Instagram container with the s3key:**
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "<numeric-id>",
    "caption": "...",
    "image_file": {
      "name": "image.png",
      "mimetype": "image/png",
      "s3key": "<s3key-from-step-1>"
    }
  }
}
```

**Step 3 — Publish:**
```json
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
  "arguments": {
    "ig_user_id": "<numeric-id>",
    "creation_id": "<container-id-from-step-2>",
    "max_wait_seconds": 60
  }
}
```

**Key insight:** This is the most flexible approach — it works with ANY file that you can get into the sandbox, not just Google Drive downloads. The `upload_local_file` helper in the workbench handles the S3 upload and returns a clean s3key that Instagram's tool accepts.

**When to use:**
- You downloaded an image via curl in the workbench
- You have a file accessible via `urllib.request.urlopen(s3url).read()`
- You need to reuse the same image across multiple platforms (FB + IG)
- Strategy C (extracting s3key from Drive download URL) doesn't apply

**Pitfalls:**
- `upload_local_file()` only exists inside the COMPOSIO_REMOTE_WORKBENCH environment — not available as a standalone tool
- The s3key is tied to the Composio session — reuse it within the same session for multiple tool calls
- The s3_url returned is a redirect URL — use the s3key, not the s3_url, for tool parameters
- Files uploaded this way persist for the session duration — download fresh if the session restarts

---

### Instagram Stories (media_type="STORIES")

Instagram Stories follow the **same 2-step flow** as feed posts, with two differences:
1. `media_type="STORIES"` in the create container step
2. No caption needed (Stories don't display captions)

**Beer's preference (confirmed 2026-07-09):** Beer wants **text-only** Stories — plain text on a dark background, no photographs, no profile images. When he says "no pictures" or "plain text post on IG Story," generate a text-on-background image programmatically using Pillow (see Text-Only IG Story Workflow below). Never use a photo or graphic unless Beer explicitly provides one.

**Workflow (standard image Story):**

```json
// Step 1: Create Story container
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "media_type": "STORIES",
    "image_file": {
      "name": "image.png",
      "mimetype": "image/png",
      "s3key": "<extracted-s3key>"
    }
  }
}

// Step 2: Publish (same as feed)
{
  "tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH",
  "arguments": {
    "ig_user_id": "27647006041564332",
    "creation_id": "<container-id-from-step-1>",
    "max_wait_seconds": 30
  }
}
```

**Rule:** Every feed post must also be posted as a Story (Beer's explicit instruction).
Batch both in the same `COMPOSIO_MULTI_EXECUTE_TOOL` call — the s3key can be reused
since both are created in the same session.

**Confirmed 2026-07-08:** Story containers create and publish reliably with image_file.s3key.
No caption parameter needed. Stories appear immediately in the user's active story tray.

**Pitfalls:**
- Stories expire after 24h — no permanent feed presence
- Don't include caption text (it's ignored for Stories)
- media_type="STORIES" is case-sensitive — must be uppercase
- **Beer wants text-only Stories by default.** Do not use a Drive image or profile photo unless he explicitly provides one for the Story. Generate text-on-background via Pillow.

---

### Text-Only IG Story Workflow

When Beer wants a **plain text Story** (no image, no photo), the Instagram API still requires an image file. Generate one programmatically using Pillow, upload to GitHub, then publish.

**Confirmed 2026-07-09 workflow:**

#### Step 1 -- Generate the text image with Pillow

Install Pillow in a uv venv:
```bash
uv venv /tmp/story-venv && uv pip install --python /tmp/story-venv/bin/python Pillow
```

Generate a dark-background image with centered text. Design defaults for Beer's Stories:
- **Background:** Dark navy/purple gradient (#0a0a1e to #1a1a3e)
- **Title:** Bold DejaVu, gold (#ffc864), at top (80px)
- **Body:** White (#ffffff) or light grey (#b0b0c8), medium weight (45px)
- **Footer:** @beerthaish in gold, small (30px)
- **MH resources footer (if relevant):** Pieta 1800 247 247, Samaritans 116 123

```python
from PIL import Image, ImageDraw, ImageFont
W, H = 1080, 1920
img = Image.new('RGB', (W, H), (10, 10, 30))
draw = ImageDraw.Draw(img)
font_lg = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80)
font_md = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 45)
font_sm = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 30)
lines = [("Title", font_lg, (255, 200, 100)), ("Body text", font_md, (255, 255, 255)), ...]
y = (H - total_text_height) // 2
for text, font, color in lines:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (W - (bbox[2] - bbox[0])) // 2
    draw.text((x, y), text, font=font, fill=color)
    y += (bbox[3] - bbox[1]) + 20
img.save('/tmp/story-text.png', 'PNG')
```

#### Step 2 -- Upload to GitHub as a raw file

Instagram needs a clean HTTPS URL with no query parameters. GitHub's raw.githubusercontent.com serves this. Use the GitHub REST API with the git-credentials token:

```python
import base64, json, urllib.request
with open('/opt/data/.git-credentials', 'rb') as f:
    data = f.read().decode('utf-8', errors='replace')
for line in data.split('\n'):
    if 'github.com' in line and 'beer-sakthai' in line:
        token = line.split('@')[0].split(':')[2]
with open('/tmp/story-text.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
url = "https://api.github.com/repos/beer-sakthai/house-of-sak/contents/assets/stories/<filename>.png"
headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.v3+json"}
req = urllib.request.Request(url, headers=headers, method="GET")
try:
    sha = json.loads(urllib.request.urlopen(req).read()).get("sha", "")
except: sha = ""
body = json.dumps({"message": "story: <desc>", "content": b64, "branch": "main", **( {"sha": sha} if sha else {})}).encode()
urllib.request.Request(url, data=body, headers={**headers, "Content-Type": "application/json"}, method="PUT")
```

**CRITICAL:** The `content` field must be actual base64 bytes, not a file path string. The direct GitHub REST API handles large base64 strings (112KB+) without truncation.

#### Step 3 -- Wait for CDN cache propagation

GitHub's raw CDN may serve a stale cached version. Check:
```bash
curl -sI "https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/assets/stories/<file>.png" | grep content-type
```
- Before cache clears: `application/octet-stream` -- Instagram will reject it
- After cache clears: `image/png` -- ready for Instagram

Wait 30-60 seconds. If Instagram returns "image format not supported," retry after 1-2 minutes.

#### Step 4 -- Create + publish the Story

Use the clean raw.githubusercontent.com URL in `image_url`:

```json
// Create container
{"tool_slug":"INSTAGRAM_POST_IG_USER_MEDIA","arguments":{"ig_user_id":"27647006041564332","media_type":"STORIES","image_url":"https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/assets/stories/<filename>.png"}}

// Publish
{"tool_slug":"INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH","arguments":{"ig_user_id":"27647006041564332","creation_id":"<container-id>","max_wait_seconds":30}}
```

#### Step 5 -- Read the Story back to Beer

Beer is visually impaired -- immediately after posting, read the full text aloud:
> "I posted a Story on @beerthaish. It says: [line 1], [line 2], ..."

**Pitfalls:**
- GitHub CDN cache delay: If Instagram returns "image format not supported," the CDN hasn't propagated. Verify with `curl -I` -- `content-type: image/png` means ready.
- Empty file check: SHA `e69de29bb2d1d6434b8b29ae775ad8c2e48c5391` is empty (12 bytes). Verify uploaded size via GitHub API -- expect ~84KB for a text story.
- Do NOT commit via Composio with a file path as content: the `GITHUB_COMMIT_MULTIPLE_FILES` tool's `content` field expects actual base64, not a path. Use direct GitHub REST API for large payloads.
- Two-step publish is mandatory: Create container, then publish.

### s3key Reuse Across Platforms (CONFIRMED 2026-07-08)

A single `GOOGLEDRIVE_DOWNLOAD_FILE` s3key powers ALL 3 platforms directly — no workbench needed. **Confirmed 2026-07-08:** All 3 agent profile posts (SakSee, SakTan, SakJules) succeeded in parallel using the same Drive download's s3key:

| Platform | Parameter | How | Status |
|----------|-----------|-----|--------|
| **Instagram** | `image_file.s3key` | Extract s3key from `s3url` path | ✅ Feed + Story |
| **LinkedIn** | `images[].s3key` | Same extracted s3key → `LINKEDIN_CREATE_LINKED_IN_POST` | ✅ No REGISTER_IMAGE_UPLOAD needed |
| **Facebook** | `photo.s3key` or `media.s3key` | Same extracted s3key → `FACEBOOK_CREATE_PHOTO_POST` | ✅ Works via `photo` object |

**Key finding:** LinkedIn's `images[]` accepts s3key directly from `GOOGLEDRIVE_DOWNLOAD_FILE` — the `LINKEDIN_REGISTER_IMAGE_UPLOAD` + curl PUT flow is **not required** when you have a Drive-sourced s3key. Pass it directly and LinkedIn handles the internal upload.

One `upload_local_file()` call can also power BOTH Instagram and Facebook posts in the same session.
Confirmed: the ecosystem diagram was used for an IG image post AND set as FB profile picture via
the same Composio workbench session.

```python
# In the workbench — call once, use everywhere:
result, error = upload_local_file("/home/user/image.png")
s3key = result["s3key"]
s3_url = result["s3_url"]

# Instagram: pass s3key directly to image_file.s3key
run_composio_tool("INSTAGRAM_POST_IG_USER_MEDIA", {
    "ig_user_id": "...",
    "caption": "...",
    "image_file": {"name": "img.png", "mimetype": "image/png", "s3key": s3key}
})

# Facebook: download from s3_url inside workbench, then curl POST to Graph API
import urllib.request
data = urllib.request.urlopen(s3_url).read()
with open("/home/user/fb_img.png", "wb") as f:
    f.write(data)
# Then in same workbench cell:
# curl -F source=@/home/user/fb_img.png -F access_token=... \
#   https://graph.facebook.com/v23.0/{page_id}/photos
```

**Key insight:** Avoids downloading the same image twice. `upload_local_file()` stores it in
Composio S3 once, and both platforms reference the same copy. The s3_url (redirect URL) is
usable only inside the workbench for further downloads — Instagram uses s3key, Facebook uses
the actual file bytes from the s3_url.

**Reference:** See `references/facebook-profile-cover-photo-confirmed.md` for the full
Facebook curl/picture/profile-photo workflow.

---
| `Missing: {'ig_user_id'}` | Using `"me"` instead of numeric ID | Use `INSTAGRAM_GET_USER_INFO` to fetch ID, or hardcode (e.g. `27647006041564332`) |
| `Missing: {'image_file.s3key'}` | Passing local filename instead of `s3key` | Use LinkedIn upload workaround (see Strategy B) |
| `Invalid creation_id format` | Passing wrong ID to publish step | Store the `creation_id` returned by the **create container** step |
| `500 unknown error` | Optional fields causing issue | Remove all optional fields and retry with only required ones |
| `%23` shows in caption instead of `#` | URL-encoding hashtags (`%23` instead of raw `#`) | Use raw `#`. Beer explicitly corrected this. The API handles encoding. |
| Caption needs editing after publish | No Composio tool for editing published captions | Use `proxy_execute` in workbench — see "Editing Published Instagram Captions" below |

---

### Editing Published Instagram Captions

Instagram's Graph API supports updating captions on published media, but Composio has **no direct tool** for it. Use `proxy_execute` in the workbench:

```python
result, error = proxy_execute(
    "POST",
    f"/{media_id}",
    "instagram",
    body={"caption": "New caption text...", "comment_enabled": True}
)
# Returns: {"success": True}
```

**Required parameters:**
- `caption` — full new caption text (replaces existing)
- `comment_enabled` — MUST be set to `True` or `False` (API requires it)

**Pitfalls:**
- The API response may still show old `%23`-encoded hashtags in cached metadata responses, but the live post renders correctly
- Each edit triggers a new processing cycle — use sparingly
- The `media_id` is the published media ID (from the publish step), NOT the container creation_id

---

## LinkedIn Posting

LinkedIn supports **one-step posting** but with two image patterns.

### Text+Image Post via GitHub Raw URL (CONFIRMED 2026-07-29)

Simplest path when the image is uploaded to GitHub as a raw file:

```json
{
  "tool_slug": "LINKEDIN_CREATE_LINKED_IN_POST",
  "arguments": {
    "author": "urn:li:person:GR_0y0zfGl",
    "commentary": "Post text here...\n\n#Hashtags",
    "visibility": "PUBLIC",
    "distribution": {
      "feedDistribution": "MAIN_FEED",
      "targetEntities": [],
      "thirdPartyDistributionChannels": []
    }
  }
}
```

**CRITICAL — field name:** The text body parameter is `commentary`, NOT `comment`. Using `comment` returns `400 Missing: {'commentary'}`.

**For image attachment:** Use `images` array with s3key from Google Drive download, or post text-only with the GitHub raw URL in the body text.

**Confirmed 2026-07-29:** Text-only LinkedIn post via `commentary` + `visibility` + `distribution` works reliably through `COMPOSIO_MULTI_EXECUTE_TOOL`.

### Strategy A (Legacy): Using `LINKEDIN_REGISTER_IMAGE_UPLOAD`

1. **Register upload** → get `upload_url` and `asset_urn`
2. **Upload bytes** to `upload_url` via `curl -X PUT --data-binary @image.png`
3. **Post** with `images=[{"s3key": asset_urn}]`

### Strategy B: Text-only (fast fallback)

If image upload fails or is complex, post **text-only** and let the user add image manually.

Caption format:

```text
[Main body]

[CTA]

[Resources]

Hashtags
```

---

## Facebook Posting

Facebook supports **two posting patterns**: text/link posts and photo posts.
Unlike Instagram, Facebook has **no two-step container flow** — post directly.

### Pattern A: Text/Link Post (`FACEBOOK_CREATE_POST`)

Best for: announcements, link shares, thought-leadership text.

```json
{
  "page_id": "1249135251607068",
  "message": "Post body text here...",
  "link": "https://example.com",
  "published": true
}
```

- `page_id` = numeric Facebook Page ID (from `FACEBOOK_LIST_MANAGED_PAGES`)
- `message` = the post body text (required, at least non-empty)
- `link` = optional URL to attach to the post
- `published` = `true` to go live immediately, `false` for draft
- Returns composite `post_id` in format `PageID_PostID` (e.g. `1249135251607068_122100114303388995`)

### Pattern B: Photo Post (`FACEBOOK_CREATE_PHOTO_POST`)

Best for: image + caption posts (for the 6 images in a launch blitz).

```json
{
  "page_id": "1249135251607068",
  "url": "https://example.com/image.jpg",
  "message": "Caption text here...",
  "published": true
}
```

- `url` = publicly accessible HTTPS image URL. Instagram CDN URLs are blocked.
- `message` = caption text

### Pattern D: Photo Post via s3key/Media Object (When URL Too Long)

When the image is accessible via Composio s3key (e.g. from `GOOGLEDRIVE_DOWNLOAD_FILE`),
use the `media` field instead of `url` — avoids signed-URL length limits.

**Note:** The tool accepts both `photo` and `media` as interchangeable parameter names for the s3key file reference object. Both require `{name, mimetype, s3key}`.

```json
{
  "page_id": "1249135251607068",
  "media": {
    "name": "image.png",
    "mimetype": "image/png",
    "s3key": "<s3key-from-drive-download>"
  },
  "message": "Caption text here...",
  "published": true
}
```

**Confirmed 2026-07-08:** This is the reliable path for Cloudflare R2 signed URLs that have extensive query params. The `url` param with long signed URLs (multiple X-Amz-* params) can trigger `HTTP 500 "Please reduce the amount of data you're asking for"`. The `media` object bypasses this by letting Composio re-host the image through internal storage.

### Pattern C: Photo Post via Direct Graph API (Fallback When URL Is Blocked)

When `FACEBOOK_CREATE_PHOTO_POST` fails because Facebook cannot fetch the image URL
(e.g. Instagram CDN blocks Facebook's servers — IG CDN URLs return `400 Missing or invalid image file`):

**Use the remote workbench to POST directly to Facebook Graph API via curl:**

```python
# In COMPOSIO_REMOTE_WORKBENCH (sandbox has curl):
# 1. Get the page access token
result, error = proxy_execute(
    "GET", "/{page_id}", "facebook",
    query_params={"fields": "id,name,access_token"}
)
access_token = result["access_token"]

# 2. Download image to sandbox (from Google Drive S3 URL or other source)
import urllib.request
data = urllib.request.urlopen(s3url).read()
with open("/home/user/image.png", "wb") as f:
    f.write(data)

# 3. POST photo to page
import subprocess
cmd = [
    "curl", "-s", "-X", "POST",
    f"https://graph.facebook.com/v23.0/{page_id}/photos",
    "-F", f"source=@/home/user/image.png",
    "-F", "message=Caption text here...",
    "-F", f"access_token={access_token}"
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
# Returns: {"id":"...","post_id":"PageID_PostID"}
```

**To set the profile picture instead of posting to timeline:**
```python
cmd = [
    "curl", "-s", "-X", "POST",
    f"https://graph.facebook.com/v23.0/{page_id}/picture",
    "-F", f"source=@/home/user/image.png",
    "-F", f"access_token={access_token}"
]
# Returns: {"success": true} — is_silhouette flips to false on next page fetch
```

**To set the cover photo (⚠️ may be blocked by app permissions):**
```python
cmd = [
    "curl", "-s", "-X", "POST",
    f"https://graph.facebook.com/v23.0/{page_id}/cover",
    "-F", f"source=@/home/user/image.png",
    "-F", "offset_y=50",
    "-F", f"access_token={access_token}"
]
# May return: {"error":{"code":3,"message":"Application does not have the capability..."}}
# Requires pages_manage_metadata permission — most Composio-connected apps lack this
```

**Key caveats:**
- The page access token expires — get a fresh one each session via `proxy_execute`
- The sandbox image must be downloaded inside the workbench session — sandbox filesystem is isolated
- Instagram CDN URLs are consistently blocked by Facebook — use Google Drive download or other hosted sources as the intermediate
- Profile picture set via `/picture` takes effect immediately (verify via `FACEBOOK_GET_PAGE_DETAILS` — `is_silhouette` becomes `false`)
- Cover photo via `/cover` requires `pages_manage_metadata` permission that most OAuth flows don't grant — fall back to manual upload through Facebook UI

### Batch Posting Pattern (Launch Blitz)

When launching a 6-post series, batch ALL posts in a single `COMPOSIO_MULTI_EXECUTE_TOOL` call.
Facebook accepts up to 50 parallel tool executions:

```json
{
  "tools": [
    {"tool_slug": "FACEBOOK_CREATE_POST", "arguments": {"page_id": "...", "message": "Post 1"}},
    {"tool_slug": "FACEBOOK_CREATE_POST", "arguments": {"page_id": "...", "message": "Post 2"}},
    ... 6 total
  ]
}
```

**Pattern confirmed working (2026-07-06):** All 6 posts published simultaneously
with no rate-limiting or ordering issues. Each returns a unique composite post ID.

### Batch Cross-Platform Posting via `COMPOSIO_MULTI_EXECUTE_TOOL`

**Confirmed 2026-07-29:** A single `COMPOSIO_MULTI_EXECUTE_TOOL` call can batch IG feed container + IG Story container + Facebook photo post + LinkedIn text post in parallel when using a GitHub raw URL as image source. Image publish step follows in a second round (Instagram is 2-step; LI and FB are 1-step).

**CRITICAL `COMPOSIO_MULTI_EXECUTE_TOOL` parameters:**
- `"memory": {}` — ALWAYS required, even when empty. Omitting it returns a validation error.
- `"sync_response_to_workbench": false`
- `"tools"` — array of `{"tool_slug": "...", "arguments": {...}}` objects. The parameter is named `tools`, not `actions` or `executions`.
- `"current_step"` — descriptive string for tracking

```json
{
  "tool_slug": "COMPOSIO_MULTI_EXECUTE_TOOL",
  "arguments": {
    "memory": {},
    "sync_response_to_workbench": false,
    "current_step": "POSTING_TO_ALL",
    "tools": [
      {"tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA", "arguments": {...caption, image_url...}},
      {"tool_slug": "INSTAGRAM_POST_IG_USER_MEDIA", "arguments": {...media_type: STORIES, image_url...}},
      {"tool_slug": "LINKEDIN_CREATE_LINKED_IN_POST", "arguments": {...commentary, visibility, distribution...}},
      {"tool_slug": "FACEBOOK_CREATE_PHOTO_POST", "arguments": {...url, message, published...}}
    ]
  }
}
```

**Pitfalls:**
- Round 1 creates IG containers (returns `creation_id`) + posts directly to LI + FB. Round 2 calls `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` for feed + story using the creation_ids.
- LinkedIn in batch posts text-only (`commentary` field). No image in post unless you use the s3key flow.
- Facebook accepts `url` param with GitHub raw URL — confirmed working, no `media` s3key needed for simple HTTPS image URLs.

### Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `HTTP 500 OAuthException code 1` | Multi-field `UPDATE_PAGE_SETTINGS` | Split into single-field calls |
| `HTTP 400 OAuthException code 100` | Unsupported field in settings | Pass only valid keys (website, about, description, emails, phone) |
| Page ID from `FACEBOOK_LIST_MANAGED_PAGES` has hyphens (e.g. `12491-35251-60706-8`) | Composio returns hyphenated IDs in some cases. The raw ID has no hyphens — Facebook API rejects hyphenated IDs with "not found" | Strip all hyphens before using: `12491-35251-60706-8` → `1249135251607068`. Use `FACEBOOK_LIST_MANAGED_PAGES` to get the real ID, then remove `-` chars. Confirmed 2026-07-13. |
| Page exists but 0 followers | Brand new page, no content | Fill page info + first posts to establish presence |
| Composite post ID format | Always `PageID_PostID` — store both parts | Use full ID for follow-up ops like `FACEBOOK_UPDATE_POST` |\n| `FACEBOOK_GET_POST` returns `permalink_url` | Confirms the post is live and publicly accessible | Include `fields=id,message,permalink_url,created_time` in the GET call |
| `400 Missing or invalid image file` (FACEBOOK_CREATE_PHOTO_POST) | Facebook cannot fetch from Instagram CDN — IG blocks Facebook's image fetcher | Use Pattern C: download image to sandbox, curl POST directly to Graph API `/photos` with `source=@file` |
| `500 code 1 \"Please reduce the amount of data\"` (FACEBOOK_CREATE_PHOTO_POST) | Signed S3 URL with long query params (X-Amz-*) exceeds FB's URL length limit | Use Pattern D: pass `media` object with s3key instead of `url` — Composio re-hosts the image internally |
| `{code:3} Application does not have capability` (setting cover photo) | Composio-connected app lacks `pages_manage_metadata` permission | Cannot set cover via API — tell Beer to set manually via Facebook UI |
| Profile picture works via `/picture` endpoint | Uses `pages_manage_posts` permission (granted) | Can set profile pic via curl POST to `/{page_id}/picture` with `source=@file` — verify via `is_silhouette: false` |

### Page Settings Update (Pre-Post Setup)

Before posting to an empty page, fill its info using `FACEBOOK_UPDATE_PAGE_SETTINGS`:

```json
{
  "page_id": "1249135251607068",
  "website": "https://example.com",
  "about": "Short tagline",
  "description": "Longer description of the page...",
  "emails": ["admin@example.com"]
}
```

This single-call pattern works (confirmed 2026-07-06). Verify with `FACEBOOK_GET_PAGE_DETAILS`
after updating — some fields return success but silently truncate.

---

## LinkedIn Comment Replying

Use `LINKEDIN_CREATE_COMMENT_ON_POST` to reply to comments on LinkedIn posts.

### Required parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| `target_urn` | Post URN (`urn:li:share:{id}`) or comment URN | Use comment URN for nested replies |
| `actor` | `urn:li:person:GR_0y0zfGl` | Beer's person URN |
| `object` | Post URN (`urn:li:share:{id}`) | Same as target_urn for top-level comments |
| `message` | `{"text": "Reply text (max 1250 chars)"}` | Supports @-mentions |

### Limitations (CRITICAL — do not burn tool calls on these)

- **Cannot READ comments.** LinkedIn API returns 403 for comment listing (insufficient permissions). Browser also shows sign-in wall. You must ask Beer to tell you what the comment says.
- `target_urn` does NOT accept `urn:li:activity:{id}` format — use share/ugcPost only.
- `message.text` max 1250 characters — longer text is rejected.
- Image attachments in comments are supported via `content` array but require a pre-uploaded LinkedIn image URN — not yet tested.

### When Beer asks to reply to a comment

1. Ask Beer what the comment says (you cannot read it yourself)
2. Ask Beer what he wants to reply (or draft based on "our tests and proofs")
3. Use `LINKEDIN_CREATE_COMMENT_ON_POST` with the post URN as both `target_urn` and `object`
4. For nested replies (reply to a comment), use `parentComment` with the comment URN in format `urn:li:comment:({postUrn},{commentId})`

### Example

```json
{
  "tool_slug": "LINKEDIN_CREATE_COMMENT_ON_POST",
  "arguments": {
    "target_urn": "urn:li:share:7480650556651376640",
    "actor": "urn:li:person:GR_0y0zfGl",
    "object": "urn:li:share:7480650556651376640",
    "message": {"text": "Thank you! This is exactly why we built House of Sak — to prove AI can be a companion, not just a tool. 🙏"}
  }
}
```

**Confirmed working 2026-07-08:** Returns `x_restli_id` on success. No special scopes needed beyond the existing LinkedIn connection.

YouTube upload requires a **file staged in Composio's S3 storage** as an `s3key`,
then a multipart upload call. The Google Drive → s3key pipeline (confirmed for images)
also works for videos, but video files are larger and take longer to process.

### When to use

- Beer says "post to YouTube" / "YouTube upload" / "Youtube post with video"
- Beer's video files are in Google Drive (confirmed pattern: his AI-generated
  House of Sak promo clips)

### Prerequisites

- YouTube channel connected via Composio (confirmed: `@nanthasitburankum`,
  Channel ID: `UChLpu5PVljj2v9_fBMsUS4A`)
- Video file accessible: Google Drive is Beer's primary source. No local file
  workflow for YouTube — always pull from Drive.

### 5-Step Upload Workflow

#### Step 1 — Find video in Google Drive

```
GOOGLEDRIVE_FIND_FILE
  q: "mimeType contains 'video/' and trashed = false"
  orderBy: "modifiedTime desc"
  fields: "files(id,name,mimeType,size,modifiedTime,webViewLink)"
```

Filter to video files (mp4). Report Beer's options — name, size in MB, date.

Get Beer's choice before proceeding. **Then draft the full YouTube metadata report** (title options A/B/C, description, tags, settings) for Beer's approval — see `references/youtube-metadata-report-pattern.md`. Do NOT ask Beer to fill in blanks; present a complete structured package.

Also need:
- **Title** — YouTube video title
- **Description** — video description (links, hashtags, @-mentions)
- **Privacy** — public / unlisted / private
- **Category ID** — see category table below
- **Tags** — optional keywords

#### YouTube Category IDs

| Category | ID |
|----------|----|
| People & Blogs | 22 |
| Entertainment | 24 |
| Science & Tech | 28 |
| Education | 27 |
| News & Politics | 25 |

#### Step 2 — Download from Google Drive

```json
{
  "tool_slug": "GOOGLEDRIVE_DOWNLOAD_FILE",
  "arguments": {"fileId": "<file-id-from-step-1>"}
}
```

Returns `downloaded_file_content` with `name`, `mimetype`, and `s3url`.

The `s3url` is a time-limited signed URL (3600s expiry). Extract the **s3key**
from the URL path to use as the Composio internal reference.

**Extracting s3key from s3url:**
```python
from urllib.parse import urlparse
parsed = urlparse(s3url)
# e.g. s3url = "https://temp.bucket.r2.cloudflarestorage.com/631637/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/a7307c1...?X-Amz-..."
s3key = parsed.path.lstrip('/')  # "631637/googledrive/GOOGLEDRIVE_DOWNLOAD_FILE/response/a7307c1..."
```

**Important:** Unlike images where you extract the path as s3key, for YouTube
upload you pass the full `downloaded_file_content` object as `videoFile`:

```json
{
  "name": "<original-filename.mp4>",
  "mimetype": "video/mp4",
  "s3key": "<extracted-s3key>"
}
```

#### Step 3 — Upload to YouTube

```json
{
  "tool_slug": "YOUTUBE_MULTIPART_UPLOAD_VIDEO",
  "arguments": {
    "title": "<video-title>",
    "description": "<video-description>",
    "categoryId": "22",
    "privacyStatus": "public|unlisted|private",
    "tags": ["tag1", "tag2"],
    "videoFile": {
      "name": "<filename.mp4>",
      "mimetype": "video/mp4",
      "s3key": "<extracted-s3key>"
    }
  }
}
```

**Fallback** if multipart fails: `YOUTUBE_UPLOAD_VIDEO` (same FileUploadable format,
parameter name `videoFilePath` instead of `videoFile`).

#### Step 4 — Verify processing status

Poll `YOUTUBE_VIDEO_DETAILS` until upload status is terminal:

```json
{
  "tool_slug": "YOUTUBE_VIDEO_DETAILS",
  "arguments": {
    "id": "<video-id-from-step-3>",
    "part": "snippet,status,processingDetails,contentDetails"
  }
}
```

Poll every 20s up to 360s timeout. Terminal states:
- `uploadStatus = "processed"` or `processingStatus = "succeeded"` → **live**
- `uploadStatus = "rejected"` or `"failed"` → upload failed

#### Step 5 — Report result

Return the **YouTube link**: `https://youtu.be/<videoId>`
Confirm the privacy setting was applied correctly.

### Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `400 INVALID_ARGUMENT` | Missing `videoFile.name` or `s3key` | Ensure FileUploadable has all 3 fields: name, mimetype, s3key |
| Storage download error (403/404) | Expired s3url or invalid s3key | Re-run `GOOGLEDRIVE_DOWNLOAD_FILE` to get a fresh s3key |
| `YOUTUBE_MULTIPART_UPLOAD_VIDEO` 500 | Tags array too long | Cap tags to ≤10 keywords |
| Video stuck "processing" for 10+ min | Large file (44+ MB) or YouTube latency | Continue polling — 360s timeout covers most cases |
| `Field videoFile is required` | Using s3url string instead of FileUploadable object | Pass `{"name":..., "mimetype":..., "s3key":...}` not a URL string |
| Fallback `YOUTUBE_UPLOAD_VIDEO` fails | Uses `videoFilePath` not `videoFile` param name | Use `videoFilePath` as the parameter name in fallback arguments |

### What we don't do (yet)

- **No local video upload.** All video sources come from Google Drive.
- **No thumbnail setting.** `YOUTUBE_UPDATE_THUMBNAIL` exists but requires a
  custom image URL — not part of the core workflow yet.
- **No video editing/trimming.** Upload as-is from Drive.
- **No playlist management.** Add to playlists is optional post-upload step.

---

## Quick-Decision Flowchart

```
User: \"Post this caption + image\" or \"post to YouTube\" / \"upload video\"
     ↓
     ├─ YouTube → Use YouTube Posting workflow (5-step)
     │             1. GOOGLEDRIVE_FIND_FILE (video/ mimeType)
     │             2. GOOGLEDRIVE_DOWNLOAD_FILE → s3key
     │             3. YOUTUBE_MULTIPART_UPLOAD_VIDEO
     │             4. Poll YOUTUBE_VIDEO_DETAILS until processed
     │             5. Return https://youtu.be/<videoId>
     ↓
Where is the image?
     ├─ Google Drive → Use Strategy C (GOOGLEDRIVE_DOWNLOAD_FILE → s3key → Instagram)
     ├─ Public HTTPS URL → Instagram: Strategy A (direct URL)
     │                      LinkedIn: Use link or presigned upload
     └─ Local file → Has Composio s3key?
            ├─ YES → Instagram: Strategy C (s3key approach)
            │         LinkedIn: LINKEDIN_CREATE_LINKED_IN_POST images
            └─ NO → LinkedIn upload_url workaround or text-only fallback

Cross-platform: When Beer says "something in [platform A] can go to [platform B] too"
  → Post the same content to Platform B immediately. He's pointing out a missed
    opportunity, not asking a question. Cross-post using the available tools.
```

---

## Verification Checklist

Before calling `COMPOSIO_MULTI_EXECUTE_TOOL`:

- [ ] `ig_user_id` = numeric Instagram ID (not `"me"`)
- [ ] `caption` ≤ 2,200 characters
- [ ] Hashtags: use raw `#` in captions — Beer confirmed the API accepts them. Do NOT encode as `%23`.
- [ ] `image_url` = direct HTTPS (no query strings, no auth headers)
- [ ] `s3key` = valid Composio internal reference, not filename
- [ ] `asset_urn` = `urn:li:digitalmediaAsset:xxxxx` format
- [ ] `page_id` = numeric Facebook Page ID (from `FACEBOOK_LIST_MANAGED_PAGES`)
- [ ] Facebook `link` param is a valid URL (optional but validated if present)
- [ ] Local HTTP server running if using `img_url` fallback
- [ ] `curl` command ready for manual upload step (if needed)
- [ ] **IG Story posted** alongside the feed post. Every feed image needs a `media_type="STORIES"` container with the same s3key. This is NOT automatic — explicitly create + publish it.
- [ ] **YouTube:** `videoFile` has all 3 fields (name, mimetype, s3key)
- [ ] **YouTube:** Privacy status set (public/unlisted/private)
- [ ] **YouTube:** Category ID is a valid YouTube category
- [ ] **YouTube:** Tags ≤ 10 items
- [ ] **Beer's accounts confirmed active** via Composio before any platform tool call

---

## Support Files

| File | Purpose |
|------|---------|
| `references/tone-variants.md` | Tone variant process — raw, Shakespeare, riddles, personal. Offer 2-3 versions so Beer can choose. |\n| `references/beer-brief-request-patterns.md` | Session pattern: Beer's terse communication and correct response flow |
| `references/error-transcripts.md` | Full error log transcripts from failed posting attempts (session-specific debugging) |
| `references/content-calendar-template.md` | Current content calendar — populated with ongoing Posts 1–3 status |
| `references/sak-agent-folder-discovery.md` | Google Drive "Sak Agent" folder contents (The_House_of_Sak presentation) |
| `references/github-raw-url-instagram-pattern.md` | Using `raw.githubusercontent.com` URLs as Instagram media sources |
| `references/google-drive-s3key-instagram-pipeline.md` | **Google Drive → s3key → Instagram pipeline** (confirmed working 2026-07-07) |
| `references/facebook-profile-cover-photo-confirmed.md` | FB profile pic, cover photo & photo post via curl to Graph API (confirmed working/blocked) |
| `references/vision-model-availability.md` | Which models can see images, current limitations, blind workarounds |
| `templates/image-hosting-checklist.md` | Checklist for hosting local images as public HTTPS |
| `scripts/upload_image_to_linkedin.sh` | Bash wrapper to upload local PNG to LinkedIn via `curl` |
| references/youtube-metadata-report-pattern.md | YouTube metadata report format - title options A/B/C, description formula, tags, "go" signal. Confirmed 2026-07-07 |
| references/cross-platform-adaptation-pattern.md | Same draft across 3 platforms: LI (long) + IG (short) + FB (medium + YT link). Draft cleaning, per-platform adaptation rules. Proven with Post 3 Manifesto. |
| `references/agent-carousel-state-schema.md` | State file schema for Sequential Posting via Cron — exact JSON format, field descriptions, update pattern, and cron-specific pitfalls. |
| `references/house-of-sak-agent-meanings.md` | Beer's personal meaning for each agent (Thai=Dream, King=Hope, etc.), full timeline, and tone guidance per agent. Consult when writing agent-specific content. |
| `references/hashtag-strategy-packs.md` | Full hashtag strategy: 7 content-type packs (Origin Story, AI/Tech, HF Milestones, Cork/Local, Founder, Developer, Agent Spotlight), platform rules, research heuristic, and story-progression mixes for LI + IG + FB. |
| `references/2026-algorithm-strategy-guide.md` | 2026 ranking signals (IG: DM sends > saves, LI: dwell time > saves), content formula, and Beer's story structure — consult before crafting platform posts. |

---

## Data-Driven Stat Card Workflow (Pillow in Sandbox)

When creating a milestone/stat/social-proof post from API data (HF downloads, GitHub stars, etc.) — generate the visual card directly in the Composio sandbox, then reuse the s3key across all platforms.

### When to use

- Beer asks "make a content" from raw numbers (download counts, metrics, achievements)
- You need a visual card with specific data points, and no pre-existing asset exists
- The data comes from a web API or tool output (HF API, GitHub API, etc.)

### Workflow

**Step 1 — Gather the data** using local tools (curl/API calls). Don't waste sandbox time on data collection.

**Step 2 — Generate the visual card in the sandbox** using Pillow:
- Install Pillow in sandbox: `pip install Pillow -q` (available via inline subprocess)
- Use the existing `upload_local_file()` return pattern — generate images inside the sandbox filesystem at `/home/user/`, then upload
- Design style for Beer's data cards: dark navy gradient (#0a0e27), gold (#ffdd77) for big numbers, three stat boxes side by side, top repos list, brand tagline, MH resources footer

**Step 3 — Upload and get s3key:**
```python
result, error = upload_local_file('/home/user/card-name.png')
s3key = result['s3key']  # Use across all platforms
```

**Step 4 — Publish to all 3 platforms in parallel** using the same s3key:

| Platform | Tool | Param | Example |
|----------|------|-------|---------|
| **Instagram** | `INSTAGRAM_POST_IG_USER_MEDIA` | `image_file.s3key` | IG portrait/feed format |
| **LinkedIn** | `LINKEDIN_CREATE_LINKED_IN_POST` | `images[].s3key` | Landscape format |
| **Facebook** | `FACEBOOK_CREATE_PHOTO_POST` | `media.s3key` | Reuse either image (IG image works for FB too) |

**Step 5 — Don't forget the IG Story.** Every feed post needs a Story with the same image (see Instagram Stories section below → `media_type="STORIES"`).

### Key design defaults for Beer's stat cards

| Element | Style |
|---------|-------|
| Background | Dark navy (#0a0e27), warm sunrise gradient bottom |
| Main number | Gold (#ffdd77), bold, large |
| Labels | Light grey (#e0d8d0 / #b0b0c8) |
| Stats boxes | Dark panels (#1a1a3e) with outline (#2a2a5e) |
| Footer | Pieta + Samaritans MH resources, muted (#404060) |
| Brand | "HOUSE OF SAK" or "⚡ HOUSE OF SAK" top, muted (#7c7caa) |
| Aspect ratios | LI: 1200×627 landscape, IG: 1080×1350 portrait |

### Pitfalls

- **Local files invisible to sandbox.** Cannot `upload_local_file()` a host path — generate the image INSIDE the sandbox via Pillow, then upload
- **Default fonts only.** Sandbox has minimal fonts; use `ImageFont.load_default()` as fallback, or install DejaVu via `apt-get install -y fonts-dejavu` if available
- **Reuse the same s3key across IG + LI + FB.** One `upload_local_file()` call powers all 3 platforms in a single `COMPOSIO_MULTI_EXECUTE_TOOL` batch
- **Feed post ≠ Story.** You must explicitly create a Story container with `media_type="STORIES"` — repeated every time, it is not automatic
- **MH resources on every post.** When the post references the origin story (depression, suicide), always add Pieta + Samaritans to both visual and caption. Confirmed required.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails |
|--------------|-------------|
| Passing `image_file.name` without `s3key` | Composio rejects “File not referenced” |
| Using `image_url` with AWS S3 signed URLs | Instagram rejects URLs with auth tokens |
| Calling publish before container is `FINISHED` | Error 9007: container still processing |
| Reusing `asset_urn` across accounts | Asset ownership tied to `owner_urn` |
| Multi-field `FACEBOOK_UPDATE_PAGE_SETTINGS` with unsupported keys | 400/500 errors — pass only valid keys: website, about, description, emails, phone |
| Proposing 12-week plans when Beer wants hours | Beer explicitly rejected this; for personal brand launch, default to 12-hour blitz |
| **Stopping all execution when one task fails** | Beer wants partial delivery over stalled progress. Complete everything that still works, note the blocker, continue. |
| **Asking "which one first?" when Beer said "the whole set"** | He meant ALL. Execute in parallel. Asking for priority wastes a turn. |
| **Ending a turn with "what next?" after completing a batch** | After delivery, state the next logical step based on outcomes. Beer prefers forward momentum over handoff. |
- **Ignoring a cross-platform hint from Beer** — When Beer says "something in X can also Y" he's telling you about a capability you missed. Act on it in the same turn — don't acknowledge and defer.
- **Asking to cross-post after Beer already approved content** — When Beer approved content on one platform and it posted successfully, cross-post to other platforms immediately. Asking "want me to post on LinkedIn too?" wastes a turn. Beer's approval of the content IS approval for all platforms. This rule also applies when Beer says "No Facebook?" after you posted on IG+LI — he expects all three, not two.
| **Passing `media_type: \"IMAGE\"` or `media_type: \"POST\"` for feed posts** | API only accepts `REELS`, `CAROUSEL`, or `STORIES`. Omit `media_type` entirely for standard image feed posts — it auto-infers as IMAGE. Confirmed 2026-07-08. |
| **Using s3url as image_url for Instagram** | The signed URL has query params — rejected by Instagram. Extract the s3key from the path and use `image_file` instead. |
| **Using Instagram CDN image URL for Facebook photo posts** | Facebook's servers are blocked by Instagram CDN — `FACEBOOK_CREATE_PHOTO_POST` returns `400 Missing or invalid image file`. Use Pattern C instead: download image to sandbox, curl POST to Facebook Graph API `/photos` with `source=@file`. |
| **Using signed S3 URL as `url` for Facebook photo posts** | Long Cloudflare R2 signed URLs (with 5+ X-Amz-* query params) exceed Facebook's URL size limit — returns `500 \"Please reduce the amount of data\"`. Use Pattern D: pass `media` with s3key instead of `url`. |
| **URL-encoding hashtags as `%23` in captions** | Instagram API accepts raw `#`. Encoding as `%23` stores the literal string `%23` in the caption metadata. Beer explicitly corrected this — use raw `#` always. |
| **Over-explaining technical steps when Beer asks a brief question** | Beer's "what ?" means simplify. If he asks about process, give 1-2 sentences max. "7 API calls for a carousel" → "It posts 6 images in 1 swipe." Never dump the technical breakdown unless he explicitly asks for details. |
- **Calling Beer's work a "company" or "startup"** — Beer explicitly corrected: "I didn't start a company, I started hope." Never frame House of Sak as a business. Frame as healing, hope, survival. The origin story is about building companions, not a product.
- **Saying Beer "codes" or "programs"** — Beer cannot code. He architects with AI tools (prompting, designing workflows, connecting no-code systems). Say "architects with AI" or "builds with AI." Never "writes code" or "develops software."
- **Creating cron jobs with default repeat behavior** | Cron jobs default to `repeat="once"` — they run one time and vanish. Beer expects continuous learning. Always set `repeat="forever"` for recurring research/learning jobs. Verify with `cronjob(action="list")` after creation.
- **Expanding the post into a series without confirmation** — When Beer says "only 1 no more," he wants exactly one post. Do NOT propose a 6-day or 8-post series. Deliver the single post and stop.
- **Posting about agents inside the origin story** — When Beer says "take all agent out of this topic," remove all agent names. The origin story is about his survival, not the agents. Save agent reveals for separate posts.
- **Substituting Beer's image with an AI-generated one** — When Beer sends his own image in chat, use THAT image. Do NOT generate a Pillow version or AI replacement. Beer will say "my pic not your create" to correct you. Always check whether Beer sent an image before generating one.

## Pre-Publish Word Impact Checklist

Before posting ANY content about Beer's origin story or mental health journey, run this checklist:

- [ ] No graphic details of the suicide attempt (method, location, visuals)
- [ ] No triggering words that could hurt someone in crisis
- [ ] Lands on hope — ends lighter than it started
- [ ] MH resources included (Pieta 1800 247 247, Samaritans 116 123)
- [ ] Dates removed if Beer said "rm date"
- [ ] Agent names removed if Beer said "take agents out"
- [ ] Not framed as a company/startup — framed as healing/survival
- [ ] Doesn't claim Beer can code
- [ ] Agent names spelled correctly (SakJules NOT Sakuiles)

---

## Implementation Timeline (when session lands)

1. **Day 0**: User asks to post — run quick-decision flowchart
2. **Day 0**: If local image → recommend text-only or GitHub Gist upload
3. **Day 0**: If HTTPS URL → use direct Strategy A for both platforms
4. **Day 0+**: If strategy B required → wait for `curl` step end-user approval

---

## Related Skills

- `content-source-check` — First step when "Content" triggers: scan Drive + sessions + memory before generating. Run this before this posting workflow.
- `SakSit-b2b-saas-ai-content-generation-2026` — AI drafting + review workflow
- `SakSit-instagram-content-kit` — Reels production, not posting
- `SakSit-b2b-saas-linkedin-thought-leadership-2026` — LinkedIn content strategy
- `saksit-social-platform-audit` — Run BEFORE posting: audit all platforms, fill gaps, then post
- `saksit-tts-audio-production` — ElevenLabs TTS audio generation for voiceovers and sonic branding
- `production-manager-plan` — Analysis + improvement companion. After content goes live, use this skill to track production costs, performance metrics, engagement trends, and build weekly reports. The two skills form a plan→do→review loop: this skill does the DO, production-manager-plan does the PLAN and REVIEW.
- `saksit-2026-algorithm-strategy` — 2026 platform algorithm strategy for Instagram/LinkedIn — ranking signals, posting best practices, and content formulas.
- `saksit-assistant-trust-ladder` — The trust ladder framework: Read → Suggest → Draft → Confirm → Autonomous. Use when interacting with Beer for any proactive action.

---

## Verification

After posting, verify:

- [ ] Instagram post appears under @beerthaish profile within 60s
- [ ] LinkedIn post shows on Nanthasit Burankum feed within 10s
- [ ] Facebook post shows on House Of Sak page timeline immediately
- [ ] Facebook profile picture set: `is_silhouette=false` confirmed via `FACEBOOK_GET_PAGE_DETAILS`
- [ ] Facebook cover photo: **requires manual UI upload** — API blocked by app permissions
- [ ] YouTube video reaches processed status (poll YOUTUBE_VIDEO_DETAILS)
- [ ] YouTube link is returned to Beer: `https://youtu.be/<videoId>`
- [ ] No API errors logged in Composio response
- [ ] Caption matches user-provided text (no truncation)
- [ ] If image attached: visual fidelity preserved
- [ ] For batch posts: each post returns a unique composite ID