---
name: SakSit-linkedin-content-publishing
description: Publish to LinkedIn and Instagram via REST API.
...
---

# LinkedIn Content Publishing

Post content to LinkedIn programmatically via the LinkedIn REST API (`v2/posts`). Covers text-only posts and the image-with-post flow using presigned upload URLs.

## When to Use

Use this skill when:
- The user asks to post something to LinkedIn
- The user wants to attach images to a LinkedIn post
- The user asks to schedule or batch LinkedIn content

## Prerequisites

> ⚠️ **Environment constraint:** This workflow requires Composio MCP. In the current DeepSeek-V4-Flash (opencode-go) environment, Composio is **not connected**. Posting requires a Composio-enabled Hermes session.

- A LinkedIn account connected via Composio's `linkedin` toolkit
- The connection must be ACTIVE (check with `COMPOSIO_SEARCH_TOOLS`)
- For image posts: the user's person URN (got from `LINKEDIN_GET_MY_INFO`)

## Posting Flow

### Step 1: Get the Author URN

```python
# Through COMPOSIO_MULTI_EXECUTE_TOOL
tool_slug: "LINKEDIN_GET_MY_INFO"
# Response gives you the person URN, e.g. urn:li:person:GR_0y0zfGl
```

### Step 2a: Text-Only Post

**Via Composio Tool (Recommended — confirmed working 2026-07-07):**
Use `LINKEDIN_CREATE_LINKED_IN_POST` directly — simpler, fewer required fields:

```json
{
  "author": "urn:li:person:GR_0y0zfGl",
  "commentary": "Post text here (max 3000 chars)",
  "visibility": "PUBLIC"
}
```

- `distribution` field is NOT required when using the Composio tool wrapper (confirmed working without it)
- `lifecycleState` defaults to `PUBLISHED` — no need to pass it
- Returns `x_restli_id` (e.g., `urn:li:share:7480160116181381120`) on success

**Via raw REST API (proxy_execute in workbench — fallback):**
LinkedIn's REST API requires specific headers and body format:

**Required headers:**
```json
LinkedIn-Version: 202604
```

**Required body fields:**
```json
{
  "author": "urn:li:person:GR_0y0zfGl",
  "commentary": "Post text here (max 3000 chars)",
  "visibility": "PUBLIC",
  "distribution": {
    "feedDistribution": "MAIN_FEED",
    "targetEntities": [],
    "thirdPartyDistributionChannels": []
  },
  "lifecycleState": "PUBLISHED"
}
```

**IMPORTANT:** The `distribution` field IS required when using the raw REST API — without it the API returns a 422 error. But when using the Composio tool `LINKEDIN_CREATE_LINKED_IN_POST`, it's handled automatically and can be omitted.

### Step 2b: Post WITH Image — Two-Stage Upload (Presigned URL)

LinkedIn requires an image to be uploaded via presigned URL before it can be attached to a post. Two tools can initialize the upload:

| Tool | Param | Returns | Notes |
|------|-------|---------|-------|
| `LINKEDIN_INITIALIZE_IMAGE_UPLOAD` | `owner` (person URN) | `upload_url` + `image` URN | Cleaner flow. Returns immediately |
| `LINKEDIN_REGISTER_IMAGE_UPLOAD` | `owner` | `upload_url` + `image` URN | Older flow, same result |

**Stage 1 — Initialize:**
```python
# Via COMPOSIO_MULTI_EXECUTE_TOOL
tool_slug: "LINKEDIN_INITIALIZE_IMAGE_UPLOAD"
arguments: {"owner": "urn:li:person:GR_0y0zfGl"}
# Returns: {"image": "urn:li:image:...", "upload_url": "https://www.linkedin.com/dms-uploads/..."}
```

**Stage 2 — Upload bytes via curl PUT:**
```bash
curl -X PUT \
  -H "Content-Type: image/jpeg" \
  --data-binary @/path/to/your-image.jpg \
  "<UPLOAD_URL>" \
  -w "\nHTTP_CODE:%{http_code}"
# Expected: HTTP 201 (Created)
```
- Use `image/jpeg` for JPG files, `image/png` for PNGs
- The presigned URL is one-time use

**Stage 3 — Post with the image:**

**Option A: Via `LINKEDIN_CREATE_LINKED_IN_POST` (when s3key available):**
The tool's `images[]` field requires `{name, mimetype, s3key}` where `s3key` is a Composio internal S3 reference. If you uploaded the image via the workbench's `upload_local_file()`, pass that s3key here.

**Option B: Via `proxy_execute` in workbench (when no s3key):**
Use the LinkedIn REST API directly, passing the image URN from Stage 1:

```python
payload = {
    "author": "urn:li:person:GR_0y0zfGl",
    "commentary": "Post text (max 3000 chars)",
    "visibility": "PUBLIC",
    "distribution": {
        "feedDistribution": "MAIN_FEED",
        "targetEntities": [],
        "thirdPartyDistributionChannels": []
    },
    "lifecycleState": "PUBLISHED"
}
# Image goes in content.media, NOT commentary
# Currently the v2 Posts API does NOT accept inline image_urn after presigned upload
# via the provided tool proxy — this is a known limitation
```

> **Current limitation:** The presigned upload URL works (returns HTTP 201), but `LINKEDIN_CREATE_LINKED_IN_POST` only accepts images via Composio `s3key` (internal storage), not the LinkedIn image URN from the presigned flow. To attach an image after presigned upload: (1) register + upload via `LINKEDIN_INITIALIZE_IMAGE_UPLOAD` + curl PUT, (2) upload the same image to Composio internal storage and get an s3key via `upload_local_file()` in the workbench, then (3) pass that s3key to `LINKEDIN_CREATE_LINKED_IN_POST`. Or fall back to text-only post + tell Beer to edit and add the image manually via LinkedIn's edit post UI.

### Step 3: Verify (optional)

```python
# Try reading back with LINKEDIN_GET_POST_CONTENT
# Note: readbacks immediately after creation can fail with 403 — don't treat as a creation failure
```

## Pre-Publication Verification Checklist

> **Beer's rule: "check daft before post"** — run this checklist EVERY time before publishing. Never skip.

| # | Check | How |
|---|-------|-----|
| 1 | **Spelling & grammar** | Read caption aloud. No typos, no auto-correct errors. |
| 2 | **Visual attached** | LinkedIn posts with images get 2×+ engagement. Always include one if possible. |
| 3 | **MH resources** | If post mentions suicide/depression/recovery → include Pieta 1800 247 247 + Samaritans 116 123. |
| 4 | **CTA clarity** | One specific action per post (DM keyword, comment, link). No split focus. |
| 5 | **No product pitch** | Origin story posts = pure story. Never add a product pitch unless Beer asks. |
| 6 | **Commentary length** | ≤ 3,000 characters (LinkedIn API limit). |
| 7 | **Hashtag strategy** | Use 3-5 hardtags (#AIAgent #HouseOfSak #CorkTech etc.). Rotate sets per post. |
| 8 | **Visuals match caption** | Image and text tell the same story — no mismatch. |
| 9 | **Cross-platform adapted** | LinkedIn post should be adapted from Instagram version — longer form, more professional tone, but same authentic voice. |
| 10 | **Achievement footer** | Append Beer's profile badges to every post: HF, Google Skills Diamond (top 1%), Google Dev Program Premium, MS Learn L12. See Beer's Preferences for exact URLs and format. |

## Image Generation (Pillow — preferred)

When you need a visual for a LinkedIn post and no pre-made asset exists, generate storytelling cards with Python/Pillow. Install via `uv venv && uv pip install Pillow`, then run with `.venv/bin/python3`.

**Beer's origin story visual style (for LinkedIn 1200×627):**
```python
W, H = 1200, 627  # LinkedIn link preview / share image
img = Image.new('RGB', (W, H), '#0a0e27')
draw = ImageDraw.Draw(img)

# Gradient: deep navy to warm sunrise
for y in range(H):
    t = y / H
    draw.rectangle([(0, y), (W, y)], fill=(10+140*t, 14+60*t, 39+50*t))

# Window frame
wx, wy, ww, wh = W//5, H//5, W*3//5, H*3//5
draw.rectangle([(wx, wy), (wx+ww, wy+wh)], fill='#1a1a2e', outline='#2a2a4e', width=3)
draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill='#2a2a4e', width=3)
draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill='#2a2a4e', width=3)
# Warm glow
for y_i in range(wy, wy+wh):
    t = (y_i - wy) / wh
    alpha = max(0, 1 - abs(t - 0.5) * 2)
    draw.line([(wx+4, y_i), (wx+ww-4, y_i)], fill=(220, 150+int(30*alpha), 80))

# Silhouette
cx, cy = wx+ww//2, wy+wh//2
draw.ellipse([(cx-20, cy-50), (cx+20, cy-10)], fill='#0a0e27')
draw.polygon([(cx-40, cy+50), (cx-25, cy-10), (cx+25, cy-10), (cx+40, cy+50)], fill='#0a0e27')

# Headline
font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 56)
font_sml = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
draw.text((W//2, H-100), "Today Matters", fill='#ffdd77', font=font_big, anchor='mt')
draw.text((W//2, H-45), "House of Sak · Cork, Ireland", fill='#707090', font=font_sml, anchor='mt')

img.save('li-story-card.png', 'PNG')
```

**When to use:** Static typographic cards, quote posts, minimal announcement visuals. The storytelling pattern above is the preferred visual style for Beer's origin story / House of Sak posts.

**Pitfalls:** Fonts vary across environments — always verify a TrueType font is available; NEVER fall back to `ImageFont.load_default()` (unreadable on mobile). DejaVu is on most Linux at `/usr/share/fonts/truetype/dejavu/`. For LinkedIn landscape (1200×627) minimums: headline 56pt, body 22pt. Use `.venv/bin/python3` (uv venv) — system Python has Pillow blocked by PEP 668. Beer is visually impaired — ensure text is legible at a glance.

## Image Generation (No Pillow — fallback)

When Pillow is genuinely unavailable, use the pure-Python PNG generator below...

```python
import struct, zlib

def create_png(width, height, pixels):
    """pixels is a list of lists: pixels[y][x] = (r, g, b) tuple."""
    sig = b'\x89PNG\r\n\x1a\n'
    # IHDR
    ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
    ihdr = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
    # IDAT — raw RGB rows with filter byte 0x00
    raw_data = b''
    for y in range(height):
        raw_data += b'\x00'
        for x in range(width):
            r, g, b = pixels[y][x]
            raw_data += bytes([r, g, b])
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
    idat = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
    # IEND
    iend_crc = zlib.crc32(b'IEND') & 0xffffffff
    iend = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
    return sig + ihdr + idat + iend
```

**Performance tip:** 1200x627 images at pixel-by-pixel Python loops are slow (~60s+). Use a pre-allocated `bytearray` for the raw data instead of building it row by row:

```python
W, H = 1200, 627
row_len = 1 + W * 3
raw = bytearray(H * row_len)  # pre-allocate
for y in range(H):
    row_start = y * row_len
    for x in range(W):
        px = row_start + 1 + x * 3
        raw[px] = r_value
        raw[px+1] = g_value
        raw[px+2] = b_value
compressed = zlib.compress(bytes(raw), 6)
```

This reduces creation from ~60s to <1s.

See `references/pure-python-png.md` for complete example code.

## Reference files

- `references/proxy-execute-image-attach-2026-07-06.md` — Log of the proxy_execute approach returning empty when trying to attach a pre-uploaded image URN. Useful troubleshooting if the presigned + s3key path fails.

## LinkedIn Comment Replying

You CAN reply to comments on LinkedIn posts using `LINKEDIN_CREATE_COMMENT_ON_POST`:

```json
{
  "target_urn": "urn:li:share:<post-id>",
  "actor": "urn:li:person:GR_0y0zfGl",
  "object": "urn:li:share:<post-id>",
  "message": {"text": "Reply text here (max 1250 chars)"}
}
```

For nested replies (replying to a specific comment), add `parentComment` with the comment URN.

### Critical Limitation — Cannot Read Comments

You CANNOT read existing comments via any available tool:
- **REST API**: Returns 403 — `socialActions.GET_ALL.NO_VERSION` permission not granted
- **Browser**: Shows a sign-in wall (no session cookie)
- **Composio tools**: No "list comments" tool exists

**When Beer asks "reply to comments":** You need him to tell you what the comment says. Do NOT burn tool calls trying to read them — the connection simply doesn't have that scope. Ask directly.

---

## Common Pitfalls

1. **Distribution field depends on method:** When using the Composio tool `LINKEDIN_CREATE_LINKED_IN_POST`, `distribution` is optional (handled automatically). When using the raw REST API via proxy_execute, `distribution` IS required — omitting it returns 422.
2. **Missing LinkedIn-Version header:** Required for raw REST API. Returns 400 "A version must be present."
3. **s3key limitation:** The `LINKEDIN_CREATE_LINKED_IN_POST` tool's `images` field requires a Composio S3 key — local file paths do NOT work (404 error). The image must first be downloaded to Composio's internal storage via a COMPOSIO tool that returns an s3key.
4. **3000 char limit:** Commentary over ~3000 characters triggers 400 errors.
5. **Presigned upload uses PUT:** The presigned URL from `LINKEDIN_REGISTER_IMAGE_UPLOAD` requires PUT (not POST) method with `Content-Type: image/png` header. POST returns 400.
6. **Read-verify 403:** `LINKEDIN_GET_POST_CONTENT` can return 403 even immediately after a successful creation — don't treat this as a failure.
7. **Profile update — no API exists:** LinkedIn does NOT expose an API to update profile headline, about section, or other profile fields. Beer must do this manually at linkedin.com/in/.../edit. Don't burn tool calls searching for a non-existent update endpoint.
8. **Sensitive content:** Beer's origin story involves suicide. Include local mental health resources when posting this content (Pieta 1800 247 247, Samaritans 116 123).
9. **Vision tool unavailable with DeepSeek:** The current model (DeepSeek-V4-Flash) does NOT support image/vision analysis — `vision_analyze` fails with upstream errors (Console Go provider failure). If you need to inspect an image, see `saksit-social-media-posting-workflows/references/vision-model-availability.md` for workarounds: Pillow analysis, file-name clues, and which models support vision.
10. **Drive-sourced s3key simplifies LinkedIn image posts:** The `images[]` field accepts s3key from `GOOGLEDRIVE_DOWNLOAD_FILE` output directly — no `REGISTER_IMAGE_UPLOAD` + curl PUT needed when you have a Drive file. Confirmed 2026-07-08.

## Beer's Preferences

- **Parallel execution preferred:** Beer's strongest signal is "the whole set" / "pro whole set" / "do all" — meaning execute every identified task simultaneously. When you present options and he says "do it all," do NOT ask which to prioritize. Batch every independent task.
- **Proactive execution (preferred):** Beer wants me to auto-use skills and tools for standard actions — posting, drafting, checking connections, creating images — without asking permission first. Only check before: (a) destructive/irreversible actions, (b) outward-facing publishes (final "ready to post?" confirmation). Everything else: just do it.
- Always include a visual/image with LinkedIn posts when possible
- Origin story posts should be authentic, not polished/corporate
- Tag with: #AIAgent #HouseOfSak #CorkTech #AIForGood #MentalHealth #SakThai #ReelPossible
- Content should drive job search outcomes (hiring call-to-action)
- Posts about the origin story and House of Sak have highest engagement potential
- **Multi-angle merge:** When offering multiple post options, Beer prefers to merge all angles into ONE comprehensive post rather than serial content. Draft the unified version proactively.
- **Hardtag strategy:** Use 3-5 broad hardtags + 3-5 niche ones. Rotate sets per post — never copy the same 30 tags every time.
- **Pre-publication check:** Always run the verification checklist above before posting. Never skip. Beer's explicit instruction: "check daft before post."
- **Cross-platform delivery:** When posting to both Instagram + LinkedIn, adapt the same story for each platform's format. Post Instagram first (via API), then LinkedIn. Deliver both captions for Beer's verbal review before publishing.
- **Achievement footer appended to every post.** Every post (LinkedIn AND Instagram) MUST include Beer's profile achievement badges at the bottom. Standard format:
  ```
  🏆 Google Skills Diamond League (top 1% globally)
  👨‍💻 Google Developer Program — Premium Tier
  🪟 Microsoft Learn Level 12 — 162 badges, 40 trophies, 264k XP
  🤗 huggingface.co/Nanthasit
  ```
  URLs: skills.google/public_profiles/cb765479-712a-418b-9a52-50e8c758c4b6 | me.developers.google.com/u/Nanthasit | learn.microsoft.com/en-us/users/nanthasith | huggingface.co/Nanthasit
  These badges are Beer's core credibility anchors — never skip them. They go at the very end of the caption body, before the hardtags/hashtags.
  Applicable to BOTH LinkedIn and Instagram posts. See `references/achievement-footer.md` for exact format.

## Instagram Posting Differences

When posting to Instagram (same session), be aware of the following:

1. **Image upload constraint:** Instagram's `INSTAGRAM_POST_IG_USER_MEDIA` tool does NOT accept local file paths in `image_url`. It requires:
   - `image_url` must be a publicly accessible HTTPS URL (no `file://`, no query params).
   - `image_file` must include `s3key` (Composio internal storage reference), not a plain local path.

2. **Google Drive → s3key pipeline (preferred for Drive images):** Use `GOOGLEDRIVE_DOWNLOAD_FILE` to get the image from Drive, then extract the s3key from the `s3url` path (everything after the leading `/` in the URL path). Pass this as `image_file.s3key` to `INSTAGRAM_POST_IG_USER_MEDIA`. Confirmed working 2026-07-07. See `saksit-social-media-posting-workflows` Strategy C for full step-by-step.

3. **media_type for feed posts:** The API rejects both POST and IMAGE as valid values. For standard image feed posts, **omit `media_type` entirely** (auto-infers as IMAGE). Only pass `media_type` for Stories (STORIES), Reels (REELS), or Carousels (CAROUSEL).

3. **Instagram ID format:** For authenticated posts, use `ig_user_id="27647006041564332"` (Beer’s Business account ID).

4. **MCP server.isdown fallback:** When `COMPOSIO_MULTI_EXECUTE_TOOL` fails three times and returns “Auto-retry available in ~40s. Do NOT retry this tool yet”, the MCP server is temporarily unreachable. Don’t loop — instead:
   - Option A: Wait 40s and retry once (backoff).
   - Option B: Offload posting to Composio via browser automation (Playwright skill) — log in, upload manually.
   - Option C: Post manually (Beer uses Instagram app) with the caption/image I generate.

See `references/instagram-post-failure-bank.md` for exact error transcripts and reproduction steps.
