---
name: SakTan-instagram-content-kit
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

## Verification before handoff

1. Dimensions match the chosen format.
2. Visual and caption tell the same story; no mismatch.
3. No unverified claims, prices, dates, or medical/legal advice.
4. Text-on-image is legible (≥ 4% contrast, safe zone respected).
5. Caption length ≤ 2,200 chars; hashtags ≤ 30.
6. Alt text is drafted for every image/clip frame.
7. Generated faces/hands look acceptable; if broken, re-roll with seed +1.

## Common pitfalls

- **Wrong ratio** — FLUX often returns square by default; always specify width/height and crop if needed.
- **Tiny text / cut-off text** — keep critical text in top 60% of 9:16; never put captions at the very bottom edge.
- **Hashtag dumping** — 30 identical tags every post flags the algorithm; rotate.
- **Weak CTA** — every post should ask for one specific action.
- **Ignoring accessibility** — add alt text and burned-in captions on Reels.
- **Long Reels** — front-load the hook in the first 1–2 seconds; trim slow intros.
- **Copyright risk** — do not generate logos, celebrities, or trademarked products without clearance.

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
