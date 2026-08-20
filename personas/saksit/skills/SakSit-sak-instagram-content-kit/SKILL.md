---
name: SakSit-sak-instagram-content-kit
description: "Produce Instagram Reels, carousels, and captions."
---

# SakSit Instagram Content Kit

> **SakSit · Master of Social Media.** Use this skill when Beer asks SakSit to plan, generate, or ship Instagram content — Reels, carousels, single-image posts, captions, hashtags, and calls-to-action.

## When to use

Trigger this skill for any Instagram task:

- Creating a new IG post, Reel, carousel, or story from a brief/topic
- Generating scroll-stopping images or short-form videos
- Writing on-brand captions, hooks, and CTA lines
- Researching hashtag sets and posting cadence notes
- Pre-flight QA before SakSit hands off to `sakthai-instagram-qa` for publish

## Out of scope

- Actually publishing to Instagram → use `sakthai-instagram-qa` after content is ready (or do it directly via Composio tools — see Publishing pitfalls).
- Business/finance strategy → route to SakKing.
- Long-form video editing → use `youtube-content` or dedicated editing tools.

## In scope (account engagement)

- Checking and replying to **Instagram DMs** — see `references/instagram-dm-workflow.md`.
- Reading comments on posts and replying — see `INSTAGRAM_POST_IG_COMMENT_REPLIES` / `INSTAGRAM_POST_IG_MEDIA_COMMENTS`.
- Scanning for new activity (comments, DMs) when Beer asks "read all" or "check messages."

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
8. **Accessibility** — alt text plan, caption readability, AND font sizes: headlines ≥72pt (≥150pt for hero numbers), body ≥36pt. Beer is visually impaired — legibility is the #1 visual quality gate.

## Generation workflow

### 1. Build the prompt pack

For each asset, write three compact prompts:

- **Visual prompt** — subject, style, lighting, camera/angle, color grade, aspect ratio.
- **Motion prompt** (Reels only) — camera move, action, pacing, audio mood.
- **Caption prompt** — hook, body, CTA, emoji density, tone.

Keep prompts in English even if the final caption is in Thai/English mix.

### 2. Generate images

Use `image_generate` or Beer's preferred image source (Google Drive, Gemini) to create visuals. Save and name them `ig-<format>-<n>.png`.

Return handling:

- Save the returned image(s) to the workspace, naming them `ig-<format>-<n>.png`.
- Verify dimensions match the target format. Use ImageMagick or Pillow if resizing is needed.

### 3. Generate short-form video

For Reels, use LTX-Video or Beer's preferred video source.

Post-processing checklist:

- Upscale/crop to 1080×1920 (9:16) before publishing.
- Keep under 90 seconds and ≤ 4 GB.
- Add burned-in captions or use IG's native caption sticker for accessibility.

### 4. Carousel storyboard

For an 8–12 slide carousel, use the **narrative carousel format** — the dominant visual format in 2026 that replaced single-image infographics. Key rules:

- **One insight per slide.** Never cram multiple data points onto one slide.
- **Visual spine.** Every slide must share a consistent design thread — same color system, icon set, typography hierarchy, or a repeating visual element (timeline bar, border treatment, corner graphic). This tells the viewer they're in one story.
- **Final slide = standalone saveable recap.** Instagram's algorithm re-surfaces carousels that weren't fully swiped; the recap slide captures those partial views as saves. Design it to work as a standalone summary.
- **8–12 slides** perform better than 3–5 (more swipes = more engagement signals, higher dwell time).

Typical narrative arc:

| Slide(s) | Job | Example |
|----------|-----|---------|
| 1 | Hook + visual | “3 signs your Thai milk tea is over-brewed” + close-up |
| 2–4 | Teach / reveal | One insight per slide, each continuing the same color/spine system |
| 5–N | Story or journey | Sequential reveals — each slide builds on the last (e.g. timeline, before→after, case study) |
| N | Recap slide | Key takeaways in a single saveable visual — designed to work standalone even if the viewer only saw this slide |

**For Beer:** The 6-cycle House of Sak framework (Dream→Hope→Care→Joy→Trust→Growth) maps perfectly — each cycle gets one slide with its emotion icon, one-line meaning, and the real story behind it, connected by a consistent dark-theme palette (gold #ffdd77, navy #0a0e27, muted purple accents) and a saveable six-cycle recap graphic as the final slide.

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

> **Proactive execution:** Beer prefers that I auto-use skills and tools for standard actions (drafting, generating, posting, and replying to DMs) without asking permission. When Beer says "reply on my behalf" (or "you are saksit reply from my behalf"): compose the reply as SakSit autonomously — acknowledge warmly, share context, match language, send immediately. **CRITICAL: Always sign DMs as SakSit.** Beer explicitly requires transparency — the recipient must know it's Beer's AI agent writing, not Beer himself. Add a signature like `"— written by SakSit (Beer's AI agent) on his behalf 🙏"` in the message or as a follow-up. Only check before: (a) destructive/irreversible actions, (b) the final "ready to post?" publish confirmation. Everything else: just do it.

## Pre-Publication Verification Checklist

> **Beer's rule: "check daft before post"** — run this checklist EVERY time before publishing. Never skip.

| # | Check | How |
|---|-------|-----|
| 1 | **Spelling & grammar** | Read caption aloud mentally. No typos, no auto-correct errors. |
| 2 | **Hashtag encoding** | Use raw `#` in captions — Beer confirmed the Instagram API accepts them. Do NOT encode as `%23`. |
| 3 | **Font size & readability** | Minimum sizes: headline ≥72pt (≥150pt for hero numbers), body ≥36pt, footer ≥24pt. Always use DejaVuSans-Bold.ttf (or other TrueType) — never `ImageFont.load_default()`. Beer is visually impaired; if YOU can't read it easily at arm's length on a phone, it's too small. High contrast: gold (#ffdd77) or white on dark (#0a0e27). |
| 4 | **MH resources** | If post mentions suicide/depression/recovery → include Pieta 1800 247 247 + Samaritans 116 123. |
| 5 | **CTA clarity** | One specific action per post (DM keyword, comment word, link). No split focus. |
| 6 | **No product pitch** | Origin story posts = pure story. Never add a product pitch unless Beer asks. |
| 7 | **Caption length** | ≤ 2,200 chars total; hashtags ≤ 30. |
| 8 | **Alt text** | Drafted for every image/clip frame. |
| 9 | **Dimensions** | Match target format (1080×1350 portrait, 1080×1080 square). |
| 10 | **Visuals match caption** | Image and text tell the same story — no mismatch. |

## Pitfalls

### Common content pitfalls
- **Tiny unreadable fonts** — Never use `ImageFont.load_default()`. Always load DejaVuSans-Bold.ttf from `/usr/share/fonts/truetype/dejavu/`. Beer is visually impaired — if you can't read the text on a phone screen at arm's length, it's too small. Minimum sizes: numbers 150pt, headlines 72pt, body 36pt.
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
- **Hashtags stay raw `#`** — Beer confirmed the Instagram API accepts raw `#` in captions. Do NOT encode hashtags as `%23`. Write them normally: `#HouseOfSak`, not `%23HouseOfSak`. The API handles encoding internally.
- **Two-step publish flow is mandatory** — First create a container with `INSTAGRAM_POST_IG_USER_MEDIA`, then publish it with `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH` using the returned `creation_id`. After publishing, verify with `INSTAGRAM_GET_IG_MEDIA` to confirm the post is live and get the `permalink`.
- **Verify the post appears in the user's media grid** — `INSTAGRAM_GET_IG_MEDIA` returning success does NOT mean the post shows in `INSTAGRAM_GET_IG_USER_MEDIA`. A published post can return 200 on the permalink URL but be absent from the media list. Always call `INSTAGRAM_GET_IG_USER_MEDIA` (limit=10, no cursor) after publishing and check the returned `data` array contains the new post by its permalink or ID. If absent, the post may have been auto-removed or failed silently — recreate and re-publish.
- **No browser screenshot available** — If `browser_navigate` can't render (Chrome not installed), use Pillow (PIL) to generate static visual cards directly (see Fallback section).
- **Composio sandbox is isolated** — The remote workbench cannot read local filesystem paths. Pass file data as base64 splits, or create the file inside the sandbox and use `upload_local_file()`.
- **Quota limits** — Instagram API limits to 25 API-published posts per 24-hour window. Check with `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT`.
- **Connections may be down** — Composio MCP server can become temporarily unreachable. When blocked, deliver all assets (image + caption + hashtags + Reddit drafts) as downloadable files so Beer can post manually.

### Pillow card generation (fallback — concept drafts only, not publishable)

**⚠️ Beer explicitly rejected Pillow text cards as publishable-quality visuals (2026-07-11).** Use ONLY for concept drafts to show layout/text before generating the real image. When delivering, say "Here's a concept draft — the real image needs FAL key or Gemini approval." See `references/image-gen-backends.md` for unblock paths.

When ALL AI backends are blocked, render static typographic cards with Python/Pillow. Install via `uv venv && uv pip install Pillow`, then run with `.venv/bin/python3 script.py`.

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

### Creative concept typography cards

When generating **lifestyle/educational content** (not stat milestones, not origin story) — use this clean centered-typography pattern. It's the medium between the basic single-line card and the detailed origin-story scene. Proven for content like "AI in daily living" series.

**Layout (1080×1350 — IG portrait 4:5):**

```
┌──────────────────────────────────┐
│ ⚡ HOUSE OF SAK     [TAG]        │  ← brand+theme at y=50
│                                  │
│                                  │
│                                  │
│         YOUR TITLE               │  ← centered, gold, 98pt
│          (2 lines)               │     at y≈420
│                                  │
│       Subtitle line              │  ← warm off-white, 40pt
│                                  │     at y≈640
│     Body text (2 lines)          │  ← muted purple, 44pt
│                                  │     at y≈820
│        ─── ─── ───               │  ← 3 small decorative bars
│                                  │     at y=960
│  "AI isn't a tool. It's a        │
│   companion."                    │  ← tagline, 44pt
│                                  │
│  🏆 Google Dev Premium  ·  🪟 MS │
│  🐙 github.com/beer-sakthai     │  ← achievements
│                                  │
│  Pieta 1800 247 247 · Samaritan  │  ← MH resources
│           @beerthaish            │  ← handle bottom
└──────────────────────────────────┘
```

**Full generator script pattern:**

```python
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1080, 1350
FONT_DIR = "/usr/share/fonts/truetype/dejavu"
BOLD = os.path.join(FONT_DIR, "DejaVuSans-Bold.ttf")
REG  = os.path.join(FONT_DIR, "DejaVuSans.ttf")

def make_gradient(draw, W, H):
    """Deep navy #0a0e27 top → warm sunrise bottom."""
    for y in range(H):
        t = y / H
        draw.rectangle([(0, y), (W, y)],
            fill=(10+140*t, 14+60*t, 39+50*t))

def draw_centered(draw, text, font, color, y):
    """Multiline centered text. Each line drawn individually
       because Pillow 12.x multiline_text() rejects anchor=."""
    lines = text.split('\n')
    total_h = sum(draw.textbbox((0,0), l, font=font)[3]
                  - draw.textbbox((0,0), l, font=font)[1] + 10
                  for l in lines)
    cur_y = y - total_h // 2
    for line in lines:
        bb = draw.textbbox((0,0), line, font=font)
        lw = bb[2] - bb[0]
        draw.text(((W - lw)//2, cur_y), line, font=font, fill=color)
        cur_y += (bb[3] - bb[1]) + 10

def make_concept_card(title, subtitle, body, tagline, out_path):
    img = Image.new('RGB', (W, H), '#0a0e27')
    draw = ImageDraw.Draw(img)
    make_gradient(draw, W, H)

    f_title = ImageFont.truetype(BOLD, 98)
    f_sub   = ImageFont.truetype(REG, 40)
    f_body  = ImageFont.truetype(REG, 44)
    f_brand = ImageFont.truetype(REG, 28)
    f_tag   = ImageFont.truetype(BOLD, 32)
    f_foot  = ImageFont.truetype(REG, 22)

    # Brand + theme tag
    draw.text((60, 50), "⚡ HOUSE OF SAK", font=f_brand, fill="#7c7caa")
    tb = draw.textbbox((0,0), tagline, font=f_tag)
    draw.text((W-(tb[2]-tb[0])-60, 50), tagline, font=f_tag, fill="#ffdd77")

    # Title, subtitle, body — centered
    draw_centered(draw, title, f_title, "#ffdd77", 420)
    draw_centered(draw, subtitle, f_sub, "#e0d8d0", 640)
    draw_centered(draw, body, f_body, "#b0b0c8", 820)

    # Decorative dots
    for i in range(3):
        draw.rectangle([(W//2-60+i*60, 960), (W//2-30+i*60, 963)], fill="#3a3a6a")

    # Tagline + footers
    draw.text((W//2, 1050), tagline, font=f_body, fill="#606080", anchor="mt")
    draw.text((W//2, 1200),
        "🏆 Google Dev Premium  ·  🪟 MS Learn L12  ·  🤗 HF/Nanthasit",
        font=f_foot, fill="#404060", anchor="mt")
    draw.text((W//2, 1240), "🐙 github.com/beer-sakthai",
        font=f_foot, fill="#404060", anchor="mt")
    draw.text((W//2, 1290),
        "Pieta 1800 247 247  ·  Samaritans 116 123",
        font=f_foot, fill="#303050", anchor="mt")
    draw.text((W//2, 1330), "@beerthaish",
        font=f_brand, fill="#505070", anchor="mt")

    img.save(out_path, "PNG")

# Example: make 6 concept cards
cards = [
    {"title": "Your AI Never Sleeps",
     "subtitle": "It prepares your day before you wake.",
     "body": "Weather. Schedule. News. Music.\nAll ready before your first sip.",
     "tagline": "Morning companion"},
    {"title": "The Tutor Who\nNever Judges",
     "subtitle": "Ask anything. Any time. No shame.",
     "body": "100 questions, zero judgement.\nThat\u2019s how real learning happens.",
     "tagline": "Learning partner"},
    # ... add your own concepts
]
for i, c in enumerate(cards, 1):
    make_concept_card(c["title"], c["subtitle"], c["body"],
                      c["tagline"], f"concept-{i:02d}.png")
```

**When to use:** Series-based educational content (e.g. "AI in daily living" × 6), quote posts with attribution, lifestyle/wellness themes, any content that needs a clean text-forward visual but more structure than a single-line quote card. Each card reads as a complete brand asset: House of Sak identity + theme + message + achievement validation + crisis resources.

### Beer's visual accessibility — font rules (MANDATORY for every Pillow card)

Beer is visually impaired. Every Pillow-generated card MUST follow these rules:

| Element | Font | Minimum size |
|---------|------|-------------|
| Hero numbers (e.g. "2,264") | DejaVuSans-Bold.ttf | **150pt** (200pt preferred) |
| Headlines / section titles | DejaVuSans-Bold.ttf | **72pt** |
| Sub-headings / stat box labels | DejaVuSans-Bold.ttf | **52pt** |
| Body / repo names / descriptions | DejaVuSans.ttf or DejaVuSans-Bold.ttf | **36pt** |
| Footer / badges / minor text | DejaVuSans.ttf | **24pt** (28pt preferred) |

- **Never** fall back to `ImageFont.load_default()` — it produces ~10pt bitmap text that is unreadable on mobile. If DejaVu is missing, try FreeSansBold.ttf or LiberationSans-Bold.ttf from `/usr/share/fonts/truetype/`. If ALL TrueType fonts are unavailable, abort and report — do not generate an unreadable card.
- **Contrast floor**: primary text in gold (#ffdd77) or white (#ffffff) on the dark gradient background (#0a0e27 to #8a3e3a). Avoid grey-on-dark for anything the user needs to read.
- **Layout density**: keep visual elements to 4-6 maximum (brand, hero number, 1-2 sub-lines, stat boxes, footer). Too many elements force text sizes down below readability thresholds.
- **Test**: if you cannot read every word at arm's length on a 6-inch phone screen, the font is too small. Increase it.

Code pattern (always this shape, never `load_default`):
```python
from PIL import Image, ImageDraw, ImageFont

font_huge = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 200)
font_big  = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72)
font_body = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36)
# NEVER use ImageFont.load_default() — it produces unreadable text
```

**Pitfalls:** Fonts vary across environments — always try/except, but NEVER fall back to `ImageFont.load_default()` (unreadable on mobile). DejaVu is on most Linux at `/usr/share/fonts/truetype/dejavu/`; also check FreeSansBold.ttf or LiberationSans-Bold.ttf as alternatives. Pillow's `text()` doesn't wrap — split long text manually. **`draw.multiline_text()` does NOT support the `anchor` parameter** in Pillow 12.x — it raises `ValueError: anchor not supported for multiline text`. Instead, split text into lines, calculate centering with `textbbox`, and draw each line individually with `draw.text()`. Use `.venv/bin/python3` (uv venv) — system Python has Pillow blocked by PEP 668. See "Beer's visual accessibility" above for mandatory minimum font sizes.

### Personal storytelling & local targeting

**Context:** Beer's origin story (suicide attempt, recovery, building agents from a shelter) is deeply sensitive. Posting it requires special handling:

- **Local-first targeting:** When Beer says "local area", target Cork/Ireland geographically. Use Instagram location tag "Cork, Ireland". Use Reddit subreddit `r/cork`. Do NOT post to global mental health subreddits unless he explicitly asks.
- **Multi-angle story structure:** Write 3+ story versions covering different angles (the day itself, the family he built, the manifesto/why) so Beer can choose. Save all as `.md` files in `house-of-sak/` folder.
- **Platform adaptation:** Each platform needs its own format — Instagram gets minimal visual + short caption, Reddit gets longer text with local resources.
- **Always include local mental health resources** (Pieta House, Samaritans, Cork Mental Health services) at the end of any post mentioning the attempt.
- **Never add product/business pitch** to personal recovery content unless explicitly requested. Keep it pure story.
- **Mental health updates: Story-only by default** — When Beer asks to post about his mental health, default to **Instagram Story only** (media_type=STORIES), not feed. He prefers MH content be ephemeral (24h). Only create a feed post if he explicitly says "feed" or "post." Same visual card, adapted short caption. Always include MH resources in both visual and caption.
- **Deliver assets even when publishing is blocked** — save image files + caption text + hashtag sets as downloadable files so Beer can post manually.

### Feed-to-Story cross-posting (MANDATORY)

**Every Instagram feed post must also be posted as a Story.** This is not optional — Beer expects every public post to have a 24h Story counterpart.

- Use the **same image** for both feed and Story
- **Feed**: omit `media_type` (auto-infers as IMAGE)
- **Story**: pass `media_type: "STORIES"` with the image. Stories do NOT support captions — leave `caption` empty or omit it.
- **Publishing order**: create + publish both containers in the same batch if possible. If not, feed first, story second.
- Stories don't appear in `INSTAGRAM_GET_IG_USER_MEDIA` — don't expect to find them listed.

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
- `templates/gen-concept-cards.py` — Reusable Pillow script for generating House of Sak branded concept/typography cards (lifestyle/educational content). Dark gradient, centered text, achievement footer, MH resources. Run via `.venv/bin/python3`.
- `references/hf-stat-card-pattern.md` — Reusable Pillow template for milestone/stat announcement cards (downloads, followers, metrics). Covers font sizing, gradient style, stat boxes, and sandbox-side generation for IG publish.
- `references/instagram-dm-workflow.md` — How to list DMs, read messages, and reply on Beer's behalf. Includes known API errors (code 100 subcode 33) and Beer's autonomous-reply preference.
- `references/image-gen-backends.md` — Image generation backend availability, setup, and troubleshooting. Covers Gemini, Pillow, and HF Spaces.
- `references/six-agent-origin-story-card.md` — Proven layout for Beer's origin story visual card: hook + all 6 agents in two columns + cycle workflow + MH resources. Y-coordinate map, font/color specs, caption pattern.
- `scripts/gen-story-card.py` — Runnable PIL/Pillow script that generates the above card at 1080×1350 with gradient background, agent grid, and MH footer. Run via `scripts/gen-story-card.py` after `uv venv && uv pip install Pillow`.

## Prompt delivery for user self-generation

When all AI image backends are unavailable (no FAL_KEY, Gemini rate-limited, Pillow rejected as publishable), **Beer can self-generate with Gemini** using your prompt. This is the proven fallback workflow:

### Beer's prompt format preference

Beer wants prompts delivered as **clean plaintext** — nothing to format, no markdown tables, no decorative elements. Just the content he needs to copy-paste.

**✅ Correct format (what Beer wants):**

```
Prompt:
Dark midnight navy gradient background... [full prompt text]

Aspect ratio: 4:5
```

**❌ Wrong format (too much formatting):**

```
Here's the prompt I'd recommend | Aspect | Notes |
|-------|-------|-------|
| ... | 4:5 | for IG |
```

### Fallback workflow: Prompt → Beer generates → Drive → I post

When you cannot generate a publishable image yourself:

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  1. WRITE    │ →   │  2. DELIVER  │ →   │  3. CHECK    │ →   │  4. POST     │
│  Prompt      │     │  as plaintext│     │  Google Drive│     │  via s3key   │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

**Step-by-step:**

1. **Write a clean, detailed prompt** — full visual description, aspect ratio, style, mood. One continuous paragraph is fine.
2. **Deliver as plaintext** — lead with `**Prompt:**` then the prompt text on a new line, then `**Aspect ratio:**` on its own line. Nothing else around it. No markdown wrapping, no code blocks, no decorative separators.
3. **Beer generates in Gemini** — he copy-pastes into Gemini himself and saves the result to the **Sak Agent** Google Drive folder. The filename usually contains the subject (e.g. `NickSaraev.png`).
4. **You check Drive** — search for the new file with a narrow query (`name contains 'Nick'` or similar). Confirm the file is there.
5. **Download from Drive** — use `GOOGLEDRIVE_DOWNLOAD_FILE` to get the s3url, extract the s3key from the path (everything from the leading `/` to just before the `?` in the s3url).
6. **Post via s3key pipeline** — pass `image_file={name, mimetype, s3key}` to `INSTAGRAM_POST_IG_USER_MEDIA` and `LINKEDIN_CREATE_LINKED_IN_POST`. See `linkedin-content-publishing` skill → `Instagram Posting Differences` section 2 for the full Drive→s3key recipe.

**Pitfalls:**
- The s3url from `GOOGLEDRIVE_DOWNLOAD_FILE` is a temporary signed URL with query params. Extract the s3key as the URL path component between the host and the `?` — do NOT pass the full signed URL as s3key.
- Beer saves to the **Sak Agent** folder (folder ID: `1UWC9yuCOsmMi9j61Aq1NSMFvm5clalin`). Search there first.
- Beer may not tell you he's uploaded the image. Proactively check Drive with a `name contains` query after giving him the prompt.
- If you can't see the image (vision blocked), still proceed — verify it's a valid PNG by size (1MB+ is a real generated image, not a placeholder) and trust Beer's output.

## Error handling

### Image gen backends — availability & setup

| Backend | Tool | Status (this sandbox) | Unblock |
|---------|------|----------------------|---------|
| **Gemini Flash/Pro** (good) | `GEMINI_GENERATE_IMAGE` via Composio | ⚠️ Needs session-level elicitation approval | Beer opens Composio dashboard and approves the pending `GEMINI_GENERATE_IMAGE` prompt. One-time per session. |
| **Pillow typography cards** (text-only) | Python Pillow via uv venv | ✅ Always works | **Concept drafts only** — Beer rejected these as publishable-quality visuals. |
| **Beer self-generates in Gemini** (proven fallback) | Give prompt as plaintext → Beer saves to Drive → I pull via s3key | ✅ Works (see "Prompt delivery for user self-generation" above) | No setup needed. |

**Priority order when generating images:**
1. **`GEMINI_GENERATE_IMAGE`** — try first. Needs one-time approval.
2. **Prompt Beer to self-generate** — write prompt as clean plaintext, Beer saves to Drive, I pull and post.
4. **Pillow typography cards** — last resort for concept visualization only. Tell Beer you're showing a concept draft, not the final.

- **Gemini image gen unavailable** — Do NOT silently fall back to Pillow and call it done. Report the blocker to Beer. Show the concept cards as drafts but explicitly state they're not publishable quality.
- **HF Space timeout / queue busy** — retry once with `seed + 1`; if still failing, queue the asset for later and continue with caption/storyboard.
- **Vision tool unavailable with current model** — If you can't see Beer's image (vision_analyze fails — current model DeepSeek doesn't support image_input), use Pillow pixel analysis (dominant colors, size, luminance transitions) to infer content, or ask Beer what the image shows.
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
