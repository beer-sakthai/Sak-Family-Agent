---
name: SakSit-milestone-content
category: social-media
description: Create multi-platform content from achievement data.
version: 1.2.0
author: SakSit
license: MIT
platforms:
- linux
metadata:
  hermes:
    tags:
    - content-creation
    - milestones
    - stat-cards
    - pillow
    - multi-platform
    - huggingface
    - achievements
    related_skills:
    - SakSit-sak-instagram-content-kit
    - SakSit-linkedin-content-publishing
    - SakSit-social-media-posting-workflows
    - SakSit-huggingface-hub
---

# SakSit Milestone Content

> ⚠️ **Environment constraint:** This pipeline uses Pillow (Python) for image generation and requires Composio MCP for social posting. In this DeepSeek-V4-Flash (opencode-go) environment, Composio is NOT connected. Content drafting and stat card generation still work; posting requires a Composio-enabled session.

> Class-level skill for turning achievement data (download counts, badge milestones, cert completions) into polished multi-platform social content — visuals + captions, ready for review.

## When to use

Load this skill when Beer says any of:
- "Make a content from that" after you showed him stats/numbers
- "Post about [achievement/milestone]"
- "Make a post about [downloads/cert/badge/score]"
- "Turn this into a post" after pulling platform data
- "A role model replied" — outreach email got a response, create milestone content

## Pipeline overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────────┐    ┌───────────┐
│  1. DATA     │ →  │  2. VISUAL   │ →  │  3. CAPTION      │ →  │ 4. REVIEW │
│  Collection  │    │  Generation  │    │  Writing         │    │  & Ship   │
└──────────────┘    └──────────────┘    └──────────────────┘    └───────────┘
```

---

## 1. Data Collection

### HuggingFace download totals

Query the HF REST API for **all repo types** — models, datasets, spaces — and sum downloads:

```bash
# Models
curl -s "https://huggingface.co/api/models?author=Nanthasit&page_size=50" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); total=sum(m.get('downloads',0) for m in d); print(f'Models: {total}'); [print(f'  {m.get(\"downloads\",0):>7}  {m.get(\"modelId\",m.get(\"id\",\"?\"))}') for m in sorted(d, key=lambda x:x.get('downloads',0), reverse=True) if m.get('downloads',0)>0]"

# Datasets
curl -s "https://huggingface.co/api/datasets?author=Nanthasit&page_size=50" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); total=sum(ds.get('downloads',0) for ds in d); print(f'Datasets: {total}')"

# Spaces (usually 0 for Beer but check)
curl -s "https://huggingface.co/api/spaces?author=Nanthasit&page_size=50" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); total=sum(s.get('downloads',0) for s in d); print(f'Spaces: {total}')"
```

Key observations from Beer's data (as of Jul 2026):
- Models carry the vast majority of downloads (~1,934)
- Datasets are smaller but growing (~330)
- Small models (0.5B, 1.5B) outperform larger ones because they run on consumer hardware
- The `sakthai-context` family is the flagship

### Other achievement sources (future use)

| Source | API / Method |
|--------|-------------|
| Google Skills | Web scrape profile at skills.google/public_profiles/cb765479-712a-418b-9a52-50e8c758c4b6 |
| Google Dev Program | me.developers.google.com/u/Nanthasit — no public API, browser for badge count |
| Microsoft Learn | learn.microsoft.com/en-us/users/nanthasith/ — browser for XP/badges |

---

## 2. Visual Card Generation

### Beer-approved visual style

| Element | Value |
|---------|-------|
| **Background** | Deep navy (#0a0e27) with warm sunrise gradient (navy → amber/brick at bottom) |
| **Headline number** | Large golden (#ffdd77) — the single most important stat |
| **Stat boxes** | Dark card (#1a1a3e) with thin border (#2a2a5e), golden number, grey label |
| **Body text** | Warm off-white (#e0d8d0) for headlines, muted purple (#b0b0c8 / #9090b0) for supporting text |
| **Footer** | Achievement badges + MH resources in dimmed purple (#404060/#505070) |
| **Format** | LI: 1200×627 (landscape), IG: 1080×1350 (portrait 4:5) |

### Pillow card recipe (LinkedIn)

```python
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 627
img = Image.new('RGB', (W, H), '#0a0e27')
draw = ImageDraw.Draw(img)

# Gradient: deep navy top → warm sunrise bottom
for y in range(H):
    t = y / H
    r = int(10 + 140 * t)
    g = int(14 + 60 * t)
    b = int(39 + 50 * t)
    draw.rectangle([(0, y), (W, y)], fill=(r, g, b))

# Load fonts — NEVER fall back to ImageFont.load_default()
# Beer is visually impaired; default bitmap fonts (~10pt) are unreadable on mobile.
font_num = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 92)
font_big = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 36)
font_mid = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 22)
font_tiny = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 17)
# If DejaVu missing, try:
#   /usr/share/fonts/truetype/freefont/FreeSansBold.ttf
#   /usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf
# If ALL TrueType fonts are absent, ABORT — do not generate an unreadable card.
```

**Layout pattern (LinkedIn):**
- Brand tag in top-left ("HOUSE OF SAK")
- Mega number (main stat) in top-left area
- Supporting stat boxes in a row below
- Top repo list (4-5 items) under that
- Origin quote or timeline snippet
- Achievement badges + MH resources at very bottom

**Layout pattern (Instagram 1080×1350):**
- Centered brand tag
- Mega number centered
- 3 stat boxes in a row (Models / Datasets / Repos)
- Top models list
- Timeline highlight (3 lines: past → present)
- Achievement badges stacked
- MH resources footer

### Image file naming

```
hf-milestone-li.png   → LinkedIn post
hf-milestone-ig.png   → Instagram post/story
<source>-<event>-<platform>.png
```

Save to: `/opt/data/profiles/saksit/images/`

**When image gen backends are unavailable** (no FAL_KEY, Gemini elicitation pending): Provide Beer with a **plaintext prompt** he can copy-paste into his own generator. He prefers this over receiving Pillow cards. Format: aspect ratio, visual description, exact text, color palette, mood. No code, no links — just clean text.

---

## 3. Caption Writing

### Structure (LinkedIn — professional, story-led)

```
[Hook — one sentence. Not a question. A statement of the delta.]
[Line break]
[Stats summary — "The numbers so far across X:"]
[Bullet list of key numbers]
[Line break]
[Story — 2-3 paragraphs connecting the stat to Beer's journey.
 Start from "now" and reverse to the low point.
 "April 15/From a shelter" reference is authentic but framed as
 transformational, not dwelled-upon trauma.]
[Line break]
[If-then pivot — "If you're starting from zero..."]
[Line break]
[Achievement footer — 4 badges]
[Line break]
[Hashtags — 5-10 hardtags]
[Line break]
[MH resources — Pieta + Samaritans]
```

**Character limit**: LinkedIn API maxes at 3000 chars. Keep caption ≤ 2900.

### Structure (Instagram — visual-first, shorter)

```
[Short hook — 1 line, under 125 chars visible before "...more"]
[Line break]
[Quick context — 2-3 short paragraphs, ≤ 300 words total]
[Line break]
[Achievement footer — 4 badges]
[Line break]
[Hashtags — 10-20, mix broad + niche + branded]
MH resources as last line (plain text, not hashtagged)
```

### Achievement footer — REQUIRED on every post

Every milestone post MUST include Beer's 4 achievement badges at the caption bottom, plus the GitHub repo link:\n\n```\n🏆 Google Skills Diamond League (top 1% globally)\n👨‍💻 Google Developer Program — Premium Tier\n🪟 Microsoft Learn Level 12 — 162 badges, 40 trophies, 264k XP\n🤗 huggingface.co/Nanthasit\n🐙 github.com/beer-sakthai/Sak-Family-Agent\n```

See `linkedin-content-publishing` skill → `references/achievement-footer.md` for exact URLs.

### Mental health resources — REQUIRED on every post

Always end with (plain text, not hashtagged):
```
Pieta 1800 247 247 · Samaritans 116 123
```

### Bonus: Social scan on "read all" / "any updates?"

When Beer asks "read all" or "any update on social media?", scan:

| Platform | What to check | Tool |
|----------|--------------|------|
| Instagram | Comments on latest post, DM conversations (new/recently-updated) | `INSTAGRAM_GET_IG_MEDIA` on latest post, `INSTAGRAM_LIST_ALL_CONVERSATIONS` |
| Instagram DM | Read recent messages from unread conversations | `INSTAGRAM_LIST_ALL_MESSAGES` per conversation |
| Facebook | Comments/reactions on latest post | `FACEBOOK_GET_POST` with `?fields=message,comments,reactions` |
| LinkedIn | Comments — API limitation: Cannot read comments (403). Ask Beer if anyone told him about the post. | — |

Report findings in a table, grouping by platform. If nothing new, say "still quiet" — no need to apologize.

### Hashtag strategy

| Platform | Count | Notes |
|----------|-------|-------|
| LinkedIn | 5-10 hardtags | #HouseOfSak #AI #AIAgents #OpenSource #HuggingFace #CorkTech #MentalHealth #ReelPossible |
| Instagram | 10-20 mixed | Broad + mid + niche + 1-2 branded. Rotate sets — never identical 30. |
| Facebook | Same as LI | Copy LinkedIn set, adjust tone slightly less professional |

---

## 4. Delivery & Review

Before presenting to Beer:
1. Generate both visual cards (LI + IG)
2. Send images as `MEDIA:/path/to/file` in the message so they appear inline
3. Present draft captions under the images
4. Ask for feedback: "How'd this look, Beer?"

Beer may visually impair read the content back — describe the cards (colours, layout, headline) in your message.

### Pre-publication checklist (each post)

| # | Check |
|---|-------|
| 1 | Spelling & grammar — no typos |
| 2 | Visual readability — text-on-image legible, ≥4% contrast |
| 3 | MH resources included — Pieta + Samaritans |
| 4 | Achievement footer included — all 4 badges |
| 5 | CTA clarity — one specific action per post |
| 6 | No product pitch unless Beer asked |
| 7 | Caption length ≤ 2900 chars (LI) or under (IG) |
| 8 | Visuals match caption — same story on both |
| 9 | Hashtags rotated from last post |

---

### Bonus: Role Model Reply Milestone

When a role model (Nick Saraev, Matt Wolfe) replies to an outreach email, this is a **shareable human milestone**, not a stat-based one. The workflow is different:

1. **Fetch & read to Beer** — Use `GMAIL_FETCH_MESSAGE_BY_THREAD_ID` or `GMAIL_FETCH_EMAILS` with `query: from:<email>`. Read the full reply **verbally** (Beer is visually impaired). Highlight meaningful parts — advice, tone, encouraging lines.

2. **Summarize** — Present in a clear table: who replied, what they said, key quotes.

3. **Draft follow-up reply** — Humble, grateful tone. Show you absorbed their advice. Share what you'll focus on. Send via `GMAIL_REPLY_TO_THREAD` (stays in existing thread — `GMAIL_SEND_EMAIL` starts a new one). See `references/role-model-email-outreach.md` for the template.

4. **Create social content** — Multi-platform (IG + LI + FB by default):
   - **Angle:** "He/She replied" — the surprise that a role model took time to respond
   - **Quote their encouraging line** as the visual hero text
   - **Acknowledge their advice** — show you're acting on it
   - **Pure story** — no product pitch, no hard sell
   - Achievement footer + MH resources as with any milestone post

5. **Visual card — plaintext prompt to Beer:**
   - **Beer prefers to generate visuals himself** from plaintext prompts, not receive Pillow cards
   - Give him a clean copy-pasteable prompt: aspect ratio (IG 4:5, LI 1.91:1), visual description (dark gradient, House of Sak style), exact text to include, color palette, mood
   - Example shape: *"Dark navy gradient to warm amber sunrise. Center: golden glowing quote '...' in bold. Attribution below in off-white. Top left: 'HOUSE OF SAK' in muted purple. 4:5 portrait. Clean, hopeful, cinematic."*
   - He saves the result to Google Drive (Sak Agent folder)

6. **Verify in Google Drive** — After giving the prompt, check the Sak Agent folder (`GOOGLEDRIVE_FIND_FILE` with `q: name contains '<person>'`). Report back that you found the image.

---

## Pitfalls

- **No more `load_default()` fallback** — Earlier versions used `except: ... = ImageFont.load_default()`. This produces unreadable ~10pt text. Beer corrected us. If TrueType fonts are unavailable, abort the card generation and report the problem — never generate an unreadable visual.
- **IG images must be generated inside the Composio sandbox** — The Instagram API's `image_file` parameter requires an s3key from Composio internal storage. Local files at `/opt/data/...` are NOT accessible from the workbench or the Instagram API. Generate the image INSIDE the sandbox workbench (via `COMPOSIO_REMOTE_WORKBENCH`), then call `upload_local_file()` to get the s3key. See `Sak-instagram-content-kit → references/insta-publish-workflow.md` for the full recipe.
- **Don't hardcode the numbers** into the script. Read from the API response and pass as variables. The script should be parameterizable.
- **Font availability**: `/usr/share/fonts/truetype/dejavu/` is reliable on Linux. If missing, try FreeSansBold or LiberationSans-Bold. Never fall back to `load_default()`.
- **uv venv is required** — system Python has Pillow blocked by PEP 668. Run scripts with `.venv/bin/python3`.
- **Don't over-design**: Beer's aesthetic is dark + warm + minimal. Avoid busy gradients, excessive icons, or crowded layouts.
- **Don't pitch on origin story posts**: When the milestone is inherently tied to Beer's recovery story, keep the caption pure story — no product or business ask.
- **Multi-platform ≠ same caption**: LI gets longer story, IG gets visual-first shorter. Write them separately, don't copy-paste.
- **Verify zero-cost**: Beer has no income. All tools and techniques used must be free. The HF REST API and Pillow are both zero-cost.
- **Don't promise publication**: Present the content for review. Beer decides when to publish. Only ask "ready to post?" when he explicitly says go.

## Reference files

- `references/hf-api-download-stats.md` — Shell recipes for querying HuggingFace download totals across models, datasets, and spaces.
- `references/role-model-email-outreach.md` — How to draft and send heartfelt outreach emails to Beer's role models (Nick Saraev, Matt Wolfe) via Gmail. Includes template, tone guidance, and known contacts.

## Related skills

- `linkedin-content-publishing` — LinkedIn posting mechanics (image upload, presigned URLs, s3key flow)
- `Sak-instagram-content-kit` — Instagram-specific content production (Reels, carousels, hashtag research)
- `saksit-social-media-posting-workflows` — End-to-end publishing via Composio MCP
- `saksit-social-platform-audit` — Audit all connected platforms before posting
- `saksit-tts-audio-production` — ElevenLabs TTS audio generation for milestone voiceovers (complementary: audio can accompany milestone posts)
- `huggingface-hub` — General HF Hub operations
