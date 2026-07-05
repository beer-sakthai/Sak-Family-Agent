---
name: Sak-instagram-content-kit
category: social-media
description: 'End-to-end Instagram content production for SakSit: Reels (9:16), carousels, single-image posts, captions, hashtags, CTAs, and generation via FLUX.1-schnell and LTX-Video on Hugging Face Spaces.'
version: 1.0.0
author: Hermes Agent / SakSit
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  sakthai:
    tags:
    - social-media
    - instagram
    - content-creation
    - reels
    - carousels
    - flux
    - ltx-video
    - huggingface-spaces
    - caption
    - hashtag
    related_skills:
    - sakthai-instagram-qa
    - huggingface-hub
    - baoyu-infographic
    - gif-search
---

# SakSit Instagram Content Kit

> **SakSit · Master of Social Media.** Use this skill when Beer asks SakSit to plan, generate, or ship Instagram content — Reels, carousels, single-image posts, captions, hashtag packs, and calls-to-action. Image/video generation runs through FLUX.1-schnell and LTX-Video via the Hugging Face Spaces MCP server.

## When to use

Trigger this skill for any Instagram task:

- Creating a new IG post, Reel, carousel, or story from a brief/topic
- Generating scroll-stopping images or short-form videos
- Writing on-brand captions, hooks, and CTA lines
- Researching hashtag sets and posting cadence notes
- Pre-flight QA before SakSit hands off to `sakthai-instagram-qa` for publish

## Out of scope

- Actually publishing to Instagram → use `sakthai-instagram-qa` after content is ready.
- Business/finance strategy → route to SakKing.
- Long-form video editing → use `youtube-content` or dedicated editing tools.

## Instagram formats covered

| Format | Ratio | Safe zone / specs | Best for |
|--------|-------|-------------------|----------|
| **Reels / Stories** | 9:16 | 1080×1920; keep text inside 1080×1420 top-safe area; max 90s for Reels, 60s for Stories | Motion hooks, tutorials, behind-the-scenes |
| **Carousels** | 1:1 or 4:5 | 1080×1080 (1:1) or 1080×1350 (4:5); up to 10 slides | Tips, before/after, step-by-step, product features |
| **Single-image posts** | 1:1, 4:5, or 1.91:1 | 1080 px on short edge; 4:5 is most vertical real estate | Announcements, quotes, product shots |

## Pre-generation brief checklist

Before generating anything, capture these points (ask if missing):

1. **Goal** — awareness, engagement, traffic, saves, DMs?
2. **Topic / key message** — one sentence max.
3. **Audience** — who should stop scrolling?
4. **Mood / aesthetic** — e.g. cinematic, lo-fi, neon, clean studio, vintage.
5. **Format** — Reel, carousel, or single image.
6. **Text on creative** — headline, watermark, none?
7. **CTA** — what should the viewer do?
8. **Accessibility** — alt text plan and caption readability.

## Generation workflow

### 1. Build the prompt pack

For each asset, write three compact prompts:

- **Visual prompt** — subject, style, lighting, camera/angle, color grade, aspect ratio.
- **Motion prompt** (Reels only) — camera move, action, pacing, audio mood.
- **Caption prompt** — hook, body, CTA, emoji density, tone.

Keep prompts in English for FLUX/LTX even if the final caption is in Thai/English mix.

### 2. Generate still images with FLUX.1-schnell

SakSit's MCP server `hf-media` exposes `black-forest-labs/FLUX.1-schnell`.
Typical call pattern (tool names may be `<server>__<tool>`; inspect the tool list):

```text
tool: hf-media__FLUX_1_schnell  (or tool-mapped equivalent)
arguments:
  prompt: "A cinematic product shot of a glass iced Thai milk tea on a marble counter, morning light, soft shadows, pastel cafe background, 4:5 aspect ratio, clean negative space at top for text"
  width: 1080
  height: 1350
  num_inference_steps: 4
  guidance_scale: 3.5
  seed: 42
```

Return handling:

- Save the returned image(s) to the workspace, naming them `ig-<format>-<n>.png`.
- Verify dimensions match the target format. Use ImageMagick or Pillow if resizing is needed.

### 3. Generate short-form video with LTX-Video

For Reels, call `Lightricks/LTX-Video` via the same `hf-media` MCP server:

```text
tool: hf-media__LTX_Video  (or tool-mapped equivalent)
arguments:
  prompt: "Cinematic handheld shot, barista pouring Thai milk tea over ice, slow motion, warm morning light, cozy cafe bokeh background, vertical 9:16"
  width: 480
  height: 848
  num_frames: 121
  fps: 24
  guidance_scale: 3.0
  num_inference_steps: 30
  seed: 42
```

Post-processing checklist:

- Upscale/crop to 1080×1920 (9:16) before publishing.
- Keep under 90 seconds and ≤ 4 GB.
- Add burned-in captions or use IG's native caption sticker for accessibility.

### 4. Carousel storyboard

For a 5–7 slide carousel, generate the first image, then request stylistically matching follow-ups or describe each slide consistently in a batch prompt. Typical arc:

| Slide | Job | Example |
|-------|-----|---------|
| 1 | Hook + visual | “3 signs your Thai milk tea is over-brewed” + close-up |
| 2–4 | Teach / reveal | One tip per slide, same style |
| 5 | CTA slide | “Save this. Which tip helped you? 👇” |

Export each slide as 1080×1350 PNG. Zip as `ig-carousel-<topic>.zip` if delivering files.

### 5. Write caption + hashtags + CTA

Use this formula:

```text
[HOOK — line 1, no emoji, < 125 chars visible before “…more”]
[LINE BREAK]
[Body — 2–5 short paragraphs, max one emoji per paragraph]
[LINE BREAK]
[CTA]
[LINE BREAK]
[Hashtags — 10–25, mix of big + niche, in Thai/English as needed]
```

Example hook bank:

- “Most people brew Thai tea wrong. Here is the fix:”
- “Stop scrolling if you love Thai milk tea ☕️”
- “Save this before your next cafe run.”

CTA bank:

- “Double tap if you agree 👇”
- “Tag a friend who needs this.”
- “DM me ‘TEA’ for the full guide.”

Hashtag research heuristic:

- 3–5 broad tags (≥1M posts): `#thaitea` `#milktea` `#thaifood`
- 5–10 mid tags (100K–1M): `#thaicafe` `#icedtea` `#homecafe`
- 5–10 niche tags (<100K): `#cha yen` `#thaimilktealover` `#brewingtips`
- 1–2 branded tags: `#beerthaish` `#saksitmade` (if approved)

Avoid banned/oversaturated spam tags and never copy the exact same 30 tags to every post.

## Post-publishing verbal delivery

Beer may not be able to read the on-screen Instagram content himself. **After any post is published (or delivered as files), immediately read the full content back to him in chat:**

1. Read the **visual card text** aloud — describe what the image shows (colours, layout, headline, sub-line).
2. Read the **caption** verbatim — hook, body, CTA, hashtags.
3. Read the **alt text** if one was drafted.
4. Ask "Does that match what you wanted?" — wait for confirmation before moving on.

This is not optional. If Beer says "you post IG for me and can't read," it means I failed to deliver the content back to him verbally. Every post must be followed by a verbal playback. Do NOT wait for him to ask — read the content back proactively the moment after publishing or file delivery.

## Pre-Publication Verification Checklist

> **Beer's rule: "check daft before post"** — run this checklist EVERY time before publishing. Never skip.

| # | Check | How |
|---|-------|-----|
| 1 | **Spelling & grammar** | Read caption aloud mentally. No typos, no auto-correct errors. |
| 2 | **Hashtag encoding** | `#` in caption MUST be `%23` for Instagram API. Raw `#` causes 400 errors. |
| 3 | **Visual readability** | Text-on-image legible? ≥ 4% contrast? No text in bottom 15%? |
| 4 | **MH resources** | If post mentions suicide/depression/recovery → include Pieta 1800 247 247 + Samaritans 116 123. |
| 5 | **CTA clarity** | One specific action per post (DM keyword, comment word, link). No split focus. |
| 6 | **No product pitch** | Origin story posts = pure story. Never add a product pitch unless Beer asks. |
| 7 | **Caption length** | ≤ 2,200 chars total; hashtags ≤ 30. |
| 8 | **Alt text** | Drafted for every image/clip frame. |
| 9 | **Dimensions** | Match target format (1080×1350 portrait, 1080×1080 square). |
| 10 | **Visuals match caption** | Image and text tell the same story — no mismatch. |

## Pitfalls

### Common content pitfalls
- **Wrong ratio** — FLUX often returns square by default; always specify width/height and crop if needed.
- **Tiny text / cut-off text** — keep critical text in top 60% of 9:16; never put captions at the very bottom edge.
- **Hashtag dumping** — 30 identical tags every post flags the algorithm; rotate.
- **Weak CTA** — every post should ask for one specific action.
- **Ignoring accessibility** — add alt text and burned-in captions on Reels.
- **Long Reels** — front-load the hook in the first 1–2 seconds; trim slow intros.
- **Copyright risk** — do not generate logos, celebrities, or trademarked products without clearance.

### Publishing pitfalls (Composio / Instagram API)
- **Image upload via s3key (preferred over public URL)** — Use `image_file` parameter with `{name, mimetype, s3key}` instead of `image_url`. Generate the image inside the Composio workbench sandbox (not on the local host — the sandbox cannot reach the local filesystem). Call `upload_local_file()` from the workbench to get an s3key, then pass that s3key to `INSTAGRAM_POST_IG_USER_MEDIA`. See `references/insta-publish-workflow.md` for the full step-by-step recipe.
- **Permalink returning 200 does NOT mean visible** — A published post can return HTTP 200 on its permalink URL but be absent from `INSTAGRAM_GET_IG_USER_MEDIA`. Always call `INSTAGRAM_GET_IG_USER_MEDIA` (limit=10, no cursor) after publishing and check the returned `data` array contains the new post by its permalink or ID. If absent, the post may have been auto-removed or never actually published — recreate and re-publish.
- **Image URL fallback** — If you must use `image_url` instead of s3key, the URL must be a stable, directly-fetchable image with proper Content-Type. AWS S3 signed URLs with query parameters are NOT supported. Upload via the workbench's `upload_local_file()` which gives both an s3key (for `image_file`) and an s3_url (redirect-based, for manual verification).
- **File host selection matters** — Not all file hosts work with Instagram's API. See `references/insta-file-hosting.md` for tested services and their quirks.
- **Caption must be URL-encoded** — Instagram expects the caption to be URL-encoded. Use `urllib.parse.quote()` to encode the full caption before passing it. Hashtags (`#`) MUST be encoded as `%23` — the raw `#` character causes the API to reject the post.
- **Two-step publish flow is mandatory** — First create a container with `INSTAGRAM_POST_IG_USER_MEDIA`, then publish it with `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` using the returned `creation_id`. After publishing, verify with `INSTAGRAM_GET_IG_MEDIA` to confirm the post is live and get the `permalink`.
- **Verify the post appears in the user's media grid** — `INSTAGRAM_GET_IG_MEDIA` returning success does NOT mean the post shows in `INSTAGRAM_GET_IG_USER_MEDIA`. A published post can return 200 on the permalink URL but be absent from the media list. Always call `INSTAGRAM_GET_IG_USER_MEDIA` (limit=10, no cursor) after publishing and check the returned `data` array contains the new post by its permalink or ID. If absent, the post may have been auto-removed or failed silently — recreate and re-publish.
- **No browser screenshot available** — If `browser_navigate` can't render (Chrome not installed), use Pillow (PIL) to generate static visual cards directly (see Fallback section).
- **Composio sandbox is isolated** — The remote workbench cannot read local filesystem paths. Pass file data as base64 splits, or create the file inside the sandbox and use `upload_local_file()`.
- **Quota limits** — Instagram API limits to 25 API-published posts per 24-hour window. Check with `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT`.
- **Connections may be down** — Composio MCP server can become temporarily unreachable. When blocked, deliver all assets (image + caption + hashtags + Reddit drafts) as downloadable files so Beer can post manually.

### Pillow card generation (fallback — no HF Spaces, no browser)

When HF Spaces are queued or unavailable AND browser screenshot tools are not installed, render static typographic cards directly with Python/Pillow. Install via `uv venv && uv pip install Pillow`, then run with `.venv/bin/python3 script.py`.

**Basic text card:**
```python
from PIL import Image, ImageDraw, ImageFont
img = Image.new('RGB', (1080, 1080), '#0a0a0a')
draw = ImageDraw.Draw(img)
try:
    font_lg = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
except OSError:
    font_lg = ImageFont.load_default()
draw.text((540, y), 'Main Text', fill='#ffffff', font=font_lg, anchor='mt')
img.save('ig-card.png', 'PNG')
```

**Storytelling visual card (Beer's origin story style):**
```python
W, H = 1080, 1350  # Instagram portrait 4:5
img = Image.new('RGB', (W, H), '#0a0e27')
draw = ImageDraw.Draw(img)

# Gradient: deep navy top → warm sunrise bottom
for y in range(H):
    t = y / H
    draw.rectangle([(0, y), (W, y)], fill=(10+140*t, 14+60*t, 39+50*t))

# Window frame with morning light
wx, wy, ww, wh = W//4, H//6, W//2, H*5//10
draw.rectangle([(wx, wy), (wx+ww, wy+wh)], fill='#1a1a2e', outline='#2a2a4e', width=4)
draw.line([(wx+ww//2, wy), (wx+ww//2, wy+wh)], fill='#2a2a4e', width=4)
draw.line([(wx, wy+wh//2), (wx+ww, wy+wh//2)], fill='#2a2a4e', width=4)
# Warm glow through window
for y_i in range(wy, wy+wh):
    alpha = max(0, 1 - abs((y_i-wy)/wh - 0.5)*2)
    draw.line([(wx+4, y_i), (wx+ww-4, y_i)], fill=(220, 150+int(30*alpha), 80))

# Silhouette figure looking out
cx, cy = wx+ww//2, wy+wh//2
draw.ellipse([(cx-25, cy-65), (cx+25, cy-15)], fill='#0a0e27')
draw.polygon([(cx-50, cy+60), (cx-30, cy-15), (cx+30, cy-15), (cx+50, cy+60)], fill='#0a0e27')

# Code lines on wall
for i, line in enumerate(["python sakthai.py --morning-call",
    "if agent.says('today matters'):", "    await user.take_step()",
    "cron.add_job('9:00', call_agent)"]):
    draw.text((60, H-320+i*36), line, fill='#4a4a7a' if i%2==0 else '#3a3a6a', font_size=20)

# Headline
draw.text((W//2, H-260), "Today Matters", fill='#ffdd77',
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 80), anchor='mt')

# Subhead + byline
draw.text((W//2, H-160), '"Your first AI agent isn\'t a chatbot"', fill='#b0b0c8',
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 28), anchor='mt')
draw.text((W//2, H-110), "— House of Sak · Cork, Ireland —", fill='#707090',
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22), anchor='mt')

# Mental health resources footer
draw.text((W//2, H-40), "Pieta ❤ 1800 247 247  |  Samaritans 116 123",
    fill='#505070', font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 20), anchor='mt')

img.save('ig-story-card.png', 'PNG')
```

**When to use:** Static typographic cards, quote posts, minimal announcement visuals. The storytelling pattern above is the preferred visual style for Beer's origin story / House of Sak posts — dark navy gradients, warm sunrise glow, window silhouettes, code on walls, "Today Matters" headline, mental health resources footer.

**Pitfalls:** Fonts vary across environments — always try/except. DejaVu is on most Linux at `/usr/share/fonts/truetype/dejavu/`. Pillow's `text()` doesn't wrap — split long text manually. Use `.venv/bin/python3` (uv venv) — system Python has Pillow blocked by PEP 668.

### Personal storytelling & local targeting

**Context:** Beer's origin story (suicide attempt, recovery, building agents from a shelter) is deeply sensitive. Posting it requires special handling:

- **Local-first targeting:** When Beer says "local area", target Cork/Ireland geographically. Use Instagram location tag "Cork, Ireland". Use Reddit subreddit `r/cork`. Do NOT post to global mental health subreddits unless he explicitly asks.
- **Multi-angle story structure:** Write 3+ story versions covering different angles (the day itself, the family he built, the manifesto/why) so Beer can choose. Save all as `.md` files in `house-of-sak/` folder.
- **Platform adaptation:** Each platform needs its own format — Instagram gets minimal visual + short caption, Reddit gets longer text with local resources.
- **Always include local mental health resources** (Pieta House, Samaritans, Cork Mental Health services) at the end of any post mentioning the attempt.
- **Never add product/business pitch** to personal recovery content unless explicitly requested. Keep it pure story.
- **Deliver assets even when publishing is blocked** — save image files + caption text + hashtag sets as downloadable files so Beer can post manually.

## Cross-Platform Posting (Instagram + Reddit)

When Beer asks to post content to **both Instagram and Reddit** (especially local subreddits like `r/cork`):

1. **Generate a unified story collection** — 3+ narrative angles saved as `.md` files in `house-of-sak/` folder
2. **Adapt per platform:**
   - **Instagram** — 1:1 visual card (`ig-card.png`) + short caption (~200-400 words) with Cork location tag
   - **Reddit** — longer text post (300-500 words) with full raw story + local mental health resources at the end
3. **Publishing order:** Post to Instagram first (via API), then provide Reddit draft as a file for copy-paste
4. **No product pitch** in recovery content unless explicitly requested

## Cross-Platform Posting (Instagram + LinkedIn)

When Beer asks to post content to **both Instagram and LinkedIn** (common pattern — "both" in chat):

1. **Write one unified caption** that merges all angles (story + thought-leadership + local community) into a single comprehensive post. Beer prefers this over serial content.
2. **Adapt per platform:**
   - **Instagram** — 1080×1350 portrait visual card + shorter caption (hook, body, CTA, hashtags). Visual-first.
   - **LinkedIn** — 1200×627 landscape visual card (or same image resized) + longer caption (up to 3000 chars). More professional tone, same authentic voice.
3. **Hashtag sets differ** per platform — Instagram gets 10-25, LinkedIn gets 3-5. Never copy the same set.
4. **Publishing order:** Instagram first (via API), then LinkedIn. Both captions must be verbally reviewed by Beer before publishing.
5. **Run the Pre-Publication Verification Checklist** on BOTH posts before publishing either one.

## References

This skill ships with supporting reference material:

- `references/personal-storytelling.md` — Story structure frameworks and platform-specific adaptation notes for Beer's origin story content.
- `references/insta-file-hosting.md` — Tested public file hosting services for Instagram API image uploads.
- `references/insta-publish-workflow.md` — Complete step-by-step for the s3key approach: generate image in workbench sandbox → upload to Composio S3 → pass s3key to Instagram tool → publish.

## Error handling

- **HF Space timeout / queue busy** — retry once with `seed + 1`; if still failing, queue the asset for later and continue with caption/storyboard.
- **NSFW / safety filter** — rephrase the prompt to remove suggestive or violent language; avoid realistic gore/nudity requests.
- **Malformed output / wrong tool name** — inspect the live tool list with `sakthai tools` and map the exact `<server>__<tool>` name.
- **Seed reproducibility** — record the seed in the deliverable metadata so the same asset can be regenerated.

## Deliverable template

Return content in this structure:

```markdown
## SakSit Instagram Content Kit — <Topic>

**Format:** Reel / Carousel / Single-image
**Dimensions:** 1080×...  
**Seed:** ...

### Assets
- `ig-reel-1.mp4` — <description>
- `ig-carousel-1.png` …

### Caption
<caption text>

### Hashtags
<tag block>

### CTA
<one-line CTA>

### Alt text
<alt text for each image/clip>
```

## Related skills

- `sakthai-instagram-qa` — final quality gate and publishing.
- `huggingface-hub` — downloading/uploading models, Spaces, or assets.
- `baoyu-infographic` — dense carousel or infographic layouts.
- `gif-search` — reaction/loop content for stories.
