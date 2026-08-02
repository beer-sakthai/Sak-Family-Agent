---
name: SakSit-free-image-generation
category: creative
description: Free image generation via Gemini and Canva.
version: 1.3.0
author: SakSit
tags:
- image-generation
- gemini
- composio
- huggingface-spaces
- free
- fallback
related_skills:
- SakSit-linkedin-content-publishing
- SakSit-social-media-posting-workflows
- SakSit-sak-instagram-content-kit
- SakSit-huggingface-hub-management
---

# SakSit Free Image Generation

Class-level skill for generating images at zero cost when the primary image_generate tool is unavailable. Two free paths, try in order:

| Priority | Path | Tool | Auth Needed | Limits |
|----------|------|------|:----------:|:------:|
| **🅰️ Try first** | **Gemini Image Gen via Composio** | `GEMINI_GENERATE_IMAGE` | ✅ None | 🆓 1,500+ req/day free tier |
| **🅱️ Secondary** | **Canva Design Export via Composio** | `CANVA_CREATE_CANVA_DESIGN_WITH_OPTIONAL_ASSET` + `CANVA_POST_EXPORTS` | ✅ Connected | 🆓 Free tier, unlimited exports |
| **🅲 Direct** | **Gemini via google-genai** | `google.genai` Python SDK | ✅ None | 🆓 Free tier, daily quota |
| **🅳 Fallback** | **Pillow programmatic** | Python Pillow | None | Unlimited |

Use Gemini first — it has generous free quotas and requires no setup. Fall back to Canva export when Gemini is blocked.

## Environment: DeepSeek-V4-Flash (opencode-go)

This environment runs **DeepSeek-V4-Flash** via opencode-go.

**Tool availability:**

| Path | Status | How to access |
|------|--------|---------------|
| `image_generate` (FAL/FLUX 2) | Needs `FAL_KEY` | Set `FAL_KEY` env var (free at fal.ai) |
| Gemini via Composio | ✅ Works via direct curl | `MCP_COMPOSIO_API_KEY` in env → curl `connect.composio.dev/mcp` (see Option C) |
| Canva via Composio | ✅ Works via direct curl | Same as above |
| Hugging Face Inference | Token exhausted (403) | Not available |

**Effective rule:** Check `FAL_KEY` first for `image_generate`. If missing, check `MCP_COMPOSIO_API_KEY` env var. If set, use **direct curl to Composio MCP** (Option C below) to call `GEMINI_GENERATE_IMAGE`. Do NOT report "no way to generate images" without checking `MCP_COMPOSIO_API_KEY` first.

## When to load

Use this skill when:
- image_generate fails with FAL_KEY environment variable is not set
- Beer says make pics or create images and FAL is down
- An infographic, card, or visual needs to be generated with no paid option available
- Beer expresses impatience (do it what you waiting, use easy dont need a key) — take this as a signal to act immediately on the free path without asking
- **Beer sends an image and says "for content"** — the image IS the content specification. Don't ask what he wants; build it. Recognize that he used the image to communicate the layout/copy/aesthetic, so (a) extract or infer the visual spec from it, (b) generate the image, (c) deliver. If you can't read the image (vision down), ask him to describe it concisely rather than trying to analyze it for minutes.

## Beer's rule: Just do it

When an image generation path exists, execute it immediately. Do NOT:
- Explain why other options failed
- Explore paid alternatives first
- Wait for confirmation
- Present multiple options for Beer to choose from (pick one, do it)

Beer Jul25 corrections (embed these in every execution):
- "Find the way make a choice i don't care get it for me" = find ONE working
  path, use it, deliver the image. If there's a blocker, present ONE fix link.
- "Use funking Gemini" = stop debugging, start executing.
- "Bit you try it first" = try every automated path before asking Beer to act.
- "Do it create it and do what you tell me" = stop explaining, produce output.
- **Check sources before making claims.** "Check in X omg check first" means
  verify against the actual Hub/repo/API before stating what a model can do.

## Option A: Gemini Image Gen via Composio (Primary)

Use the `GEMINI_GENERATE_IMAGE` tool through the Composio MCP. No authentication needed — the Gemini toolkit is available without setup.

### Models

| Model | Quality | Speed | Best For |
|-------|---------|-------|----------|
| `gemini-3-pro-image-preview` (Nano Banana Pro) | ⭐⭐⭐ 4K, thinking mode | Medium | Final assets |
| `gemini-2.5-flash-image` | ⭐⭐ 1K | Fast | Most tasks — GA stable |
| `gemini-2.0-flash-exp-image-generation` | ⭐⭐ | Fastest | Quick tests (no aspect ratio param) |
| `nano-banana-pro-preview` | ⭐⭐⭐ | Medium | Canonical Nano Banana model ID |

Note: **`nano-banana-pro-preview` is a real Google model**, confirmed via
Google's model list API. It is the canonical model ID for what Composio calls
"Nano Banana Pro" (`gemini-3-pro-image-preview` is an alias). When an image
model returns quota exhausted, also try `nano-banana-pro-preview` — they may
have separate quota pools. See `references/gemini-model-list.md` for the full
model catalog discovered in this environment.

### Aspect Ratios

1:1, 4:5, 3:4, 16:9, 9:16, 2:3, 3:2, 4:3, 5:4, 21:9

### Image Sizes

`1K`, `2K`, or `4K` (gemini-3-pro only). Default 1K is sufficient for most social media.

### Basic invocation

```text
tool: GEMINI_GENERATE_IMAGE
arguments:
  model: "gemini-2.5-flash-image"     # or gemini-3-pro-image-preview
  prompt: "Your detailed image description here"
  aspect_ratio: "4:5"                 # IG portrait
  image_size: "1K"
```

### Safety settings (if prompt gets blocked)

```json
"safety_settings": [
  {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
  {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
]
```

### Pitfalls (Gemini)

- Concurrency >3 returns HTTP 429 — keep ≤3 parallel calls, use exponential backoff
- 4K images cost more tokens; set `image_size: "1K"` for faster results
- Hosted image URLs expire — persist via GOOGLEDRIVE_UPLOAD_FROM_URL if needed long-term
- Trademarked or explicit content triggers PROHIBITED_CONTENT (400) — rephrase neutrally
- The Gemini toolkit in Composio says "does not require authentication" — it works immediately
- **Enhanced Controls blocker:** If Gemini returns "Enhanced Controls is not supported" (or times out with no clear error), see `references/enhanced-controls-blocker.md` — Beer must disable Enhanced Controls at dashboard.composio.dev/org/connect/settings

## Option B: Canva Design Export via Composio (Secondary)

Use when Gemini image gen returns Enhanced Controls errors or you need to export an existing Canva design as a downloadable image. Canva creates blank canvases and exports them — it does NOT add text/elements programmatically (old API limitation).

### Workflow

```
CANVA_CREATE_CANVA_DESIGN_WITH_OPTIONAL_ASSET → CANVA_POST_EXPORTS (export job) → CANVA_GET_DESIGN_EXPORT_JOB_RESULT (poll → URLs)
```

### 1. Create a blank design (or list existing ones)

```text
# New design with custom dimensions (e.g. 1080×1350 Instagram portrait)
tool: CANVA_CREATE_CANVA_DESIGN_WITH_OPTIONAL_ASSET
arguments:
  title: "My Design Name"
  design_type:
    type: custom
    width: 1080
    height: 1350

# Or list existing designs Beer already has content in
tool: CANVA_LIST_USER_DESIGNS
```

### 2. Start an export job

```text
tool: CANVA_POST_EXPORTS
arguments:
  design_id: "DAQxxx"        # ID from step 1
  format:
    type: png                # png, jpg, pdf, pptx, gif, mp4
```

Returns a `job.id` (e.g. `"7e7403c1-..."`).

### 3. Poll until success

```text
tool: CANVA_GET_DESIGN_EXPORT_JOB_RESULT
arguments:
  exportId: "7e7403c1-..."   # from step 2
```

When `status` is `"success"`, extract `urls[0]` — the downloadable PNG/JPG URL.

### Limits & Notes

| Item | Detail |
|------|--------|
| Max dimensions | 40–8000px for custom designs |
| Export formats | PNG, JPG, PDF, PPTX, GIF, MP4 |
| JPG quality | Required (1–100) for JPG exports |
| Download expiry | URLs expire after 24h–30d depending on method |
| Pro features | Transparent BG, lossy PNG require Pro plan |
| Content addition | ⚠️ Cannot add text/elements to designs via API. Use existing manually-made designs or upload image assets first. |

### Pitfalls (Canva)

- `CANVA_CREATE_CANVA_DESIGN_WITH_OPTIONAL_ASSET` is **deprecated** in newer Canva API; use `CANVA_POST_DESIGNS` if available
- Blank designs export as blank images — only useful if you upload assets first or use existing designs
- Beer has 25+ existing Canva designs (Facebook Covers, presentations) that can be exported directly
- Export supports specific page numbers (1-indexed) for multi-page designs
- MP4 export requires a quality enum (`horizontal_1080p`, `vertical_1080p`, etc.)

## Option C: Direct curl to Composio MCP (when Hermes MCP is disconnected)

When Hermes has no Composio MCP server configured, check for `MCP_COMPOSIO_API_KEY` in the environment. If set, you can call Composio tools directly via curl + SSE — no Hermes MCP needed.

### Discovery

```text
terminal(command="echo 'MCP_COMPOSIO_API_KEY length: ' ${#MCP_COMPOSIO_API_KEY}")
```

If non-zero, Composio is reachable at `https://connect.composio.dev/mcp`.

### Calling a tool

Send a JSON-RPC 2.0 POST with SSE response. The server returns `data:` lines:

```text
terminal(command=curl -s -X POST "https://connect.composio.dev/mcp" \
  -H "x-consumer-api-key: $MCP_COMPOSIO_API_KEY" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"GEMINI_GENERATE_IMAGE","arguments":{"model":"gemini-2.5-flash-image","prompt":"<your prompt>","aspect_ratio":"4:5","image_size":"1K"}},"id":1}'
)
```

Parse the `data:` JSON lines to extract the result. For SSE responses, the `result.content[0].text` field contains the tool output as a JSON string.

### Workflow pattern

1. Search for tools: `COMPOSIO_SEARCH_TOOLS` — sends `method: "tools/call", params: {name: "COMPOSIO_SEARCH_TOOLS", arguments: {...}}`
2. Get schema if needed: `COMPOSIO_GET_TOOL_SCHEMAS`
3. Execute: `COMPOSIO_MULTI_EXECUTE_TOOL` or the specific app tool directly
4. For single app tools (like GEMINI_GENERATE_IMAGE), the tool_slug is the tool name directly

### Active connections (from search results)

The following toolkits are already connected (no auth needed): canva, clickup, elevenlabs, exa, facebook, figma, github, gitlab, gmail, google_analytics, googlecalendar, googledocs, googledrive, googlemeet, googlephotos, googlesheets, googleslides, googletasks, hugging_face, instagram, kaggle, linkedin, make, manus, microsoft_teams, one_drive, outlook, render, vercel, youtube. Gemini says "does not require authentication" but Enhanced Controls blocks it.

Limitations: 3-min timeout per workbench cell, SSE streaming (not plain JSON), tools have a 1-index output array.

### Pitfalls

- The `session_id` pattern: use `COMPOSIO_SEARCH_TOOLS` with `session: {generate_id: true}` for new workflows, pass the returned `session_id` to subsequent calls
- For `COMPOSIO_MULTI_EXECUTE_TOOL`, `sync_response_to_workbench` and `current_step` are required parameters
- `GEMINI_GENERATE_IMAGE` may hit **Enhanced Controls** even when connection is active — see troubleshooting section below

Gemini image generation through Composio may fail with:

```
Enhanced Controls is not supported for this session...
Please go to https://dashboard.composio.dev/org/connect/settings
and disable enhanced controls to continue.
```

**Fix:** Ask Beer to visit dashboard.composio.dev/org/connect/settings and toggle **Enhanced Controls** OFF.

This error appears both in `COMPOSIO_MULTI_EXECUTE_TOOL` (as a timeout: "No response to elicitation prompt within the allowed time") and in `COMPOSIO_REMOTE_WORKBENCH` (as a clear 400 error). If you see the timeout, investigate via the workbench to get the real error message.

The `DATABRICKS_SETTINGS_ENHANCED_SECURITY_MONITORING_UPDATE` tool in Composio is for Databricks, NOT the general Enhanced Controls toggle — it will NOT fix this issue.

## Option D: Gemini Direct via google-genai Python SDK

When Composio MCP is unavailable or Enhanced Controls is blocked, call Gemini's
API directly using the `google-genai` package installed at `/opt/data/.venv/`.

### Prerequisites

- `GOOGLE_API_KEY` — read from `.env` files (NOT from `auth.json`, which has
  sealed fingerprints):
  ```
  grep GOOGLE_API_KEY /opt/data/profiles/saksit/.env
  grep GOOGLE_API_KEY /opt/data/.env
  ```

### Invocation

```python
import os
os.environ["GOOGLE_API_KEY"] = "KEY_FROM_ENV_FILE"
from google import genai
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
prompt = "Nano Banana (Gemini 2.5 Flash Preview Image). <description>"
response = client.models.generate_content(
    model="gemini-2.5-flash-image",
    contents=prompt,
    config={"response_modalities": ["IMAGE"]}
)
# Extract image from:
data = response.candidates[0].content.parts[0].inline_data.data
with open("output.png", "wb") as f:
    f.write(data)
```

Use the venv's Python: `/opt/data/.venv/bin/python3`

### Models

| Model | Found in this env | Cost | Notes |
|-------|-------------------|------|-------|
| `nano-banana-pro-preview` | ✅ Quota exhausted | Free tier | Canonical Nano Banana — try first |
| `gemini-2.5-flash-image` | ✅ Quota exhausted | Free tier | GA stable, fast |
| `gemini-3-pro-image` | Quota exhausted | Paid | Also called gemini-3-pro-image-preview |
| `gemini-3.1-flash-image` | Quota exhausted | Free tier | Latest flash |

### Pitfalls

- **Free tier quota: daily limit.** All image models returned 429 (exhausted)
  in this environment. Check by trying any model — if all return 429, the key
  has no remaining daily quota.
- **Requires `/opt/data/.venv/bin/python3`** — the system `python3` does NOT have
  `google-genai` installed.
- The "Nano Banana" prefix must be in the prompt for Gemini calls.

## Option E: Pillow Programmatic (Guaranteed Fallback)

When ALL other paths fail (no keys, no quotas, no access), generate the image
with Python Pillow. This ALWAYS works — no keys, no API, no quotas.

### Pattern

Use the venv's Python with `Pillow`:

```python
from PIL import Image, ImageDraw, ImageFont
import math, random

W, H = 1080, 1350  # portrait
img = Image.new('RGB', (W, H), (10, 10, 30))
draw = ImageDraw.Draw(img)

# Gradient background
for y in range(H):
    r = int(10 + 5 * (y/H))
    g = int(10 + 3 * (y/H))
    b = int(30 + 15 * (y/H))
    draw.line([(0, y), (W, y)], fill=(r, g, b))

# Add particles, shapes, text as needed
# Load fonts from /usr/share/fonts/truetype/dejavu/

img.save('output.png', 'PNG')
```

### Design defaults for Beer's visuals

| Element | Style |
|---------|-------|
| Background | Dark navy (#0a0e27) at top → warm sunrise (#2a1a1a) at bottom, vertical gradient |
| Gradient detail | `for y in range(H): t = y/H; r = int(10+(42-10)*t); g = int(14+(26-14)*t); b = int(39+(26-39)*t)` |
| Decorative | 120-150 star particles, random positions, dim blue-white (60-180 brightness) |
| Top text | "⚡ HOUSE OF SAK" in muted silver (~RGB 165,160,180) |
| Headline | "I had nothing. So I built everything." in gold #ffdd77 (255,221,119), with subtle black glow offset |
| Subtitle | "Six cycles. Six companions. One healing journey." in warm white (240,235,228) |
| Divider | Thin gold line (255,221,119) fading to darker gold edges, ~400px wide |
| Agent section | 6 agents in 2-column grid (3 rows), each with colored orb + name + cycle label |
| Agent colors | SakThai=blue, SakKing=purple, SakSit=orange, SakTan=green, SakJules=pink, SakSee=sky |
| Footer MH | "Pieta 1800 247 247 \| Samaritans 116 123" in dim grey (135,130,145) |
| Handle | `@beerthaish` in light grey (195,190,200) at bottom |
| Dimensions | 1080×1350 (4:5 Instagram portrait) |
| Note | Does NOT use icons/emojis from the cycle table — uses colored circles as agent indicators |

📄 **Template available** at `templates/house-of-sak-card.py` — a complete, working
Pillow script that generates this exact card. Copy, modify prompts/text/colors,
and run as-is. It produces an Instagram 4:5 portrait with all elements above.

### Pitfalls

- **🐛 The system `python3` likely has NO Pillow.** The `.venv` at
  `/opt/data/.venv/` does NOT have Pillow either (it lacks pip entirely).
  **DO NOT assume either path works.** Instead, create a throwaway venv:
  ```bash
  python3 -m venv /tmp/pillow-venv && /tmp/pillow-venv/bin/pip install Pillow
  ```
  Then use `/tmp/pillow-venv/bin/python3 your_script.py`.
  ✓ The created `/tmp/pillow-venv` persisted in this session and can be
    reused on subsequent calls within the same session.
- `uv pip install Pillow --system` may appear to succeed but the system
  Python won't find it (PEP 668 isolation). Don't rely on it — use the
  fresh-venv approach above.
- Fonts are limited to DejaVu in the sandbox available at
  `/usr/share/fonts/truetype/dejavu/`. Use `ImageFont.truetype(...)`
  and reference `DejaVuSans.ttf` (regular), `DejaVuSans-Bold.ttf` (bold),
  or `DejaVuSans-Oblique.ttf` (italic).

## 🤖 Manus: Paid Alternative (for reference)

Manus (via Composio) can create images from natural language prompts — it produced an Instagram graphic (dark purple bg, gold text, 6 stars) for House of Sak. However it uses **paid credits** (1,255 total used across 5 tasks). Only use if Beer explicitly approves the cost.

| Manus agent_profiles | Use case |
|---------------------|----------|
| `manus-1.6-lite-agent` | Simple image/text tasks, lower credit cost |
| `manus-1.6-lite-adaptive` | Complex multi-step tasks with repo access |
| `manus-1.6-max` | Heavy workloads (highest cost) |

Task flow: `MANUS_CREATE_TASK` → `MANUS_GET_TASK` (poll until `status: "completed"`).

Manus is NOT zero-cost. Do not default to Manus — only use when Beer asks for it.

## Aspect Ratio Reference

| Desired | width x height | Use Case |
|---------|---------------|----------|
| 16:9 landscape | 1344 x 768 | LinkedIn, YouTube thumbnails |
| 9:16 portrait | 768 x 1344 | Instagram Stories/Reels |
| 1:1 square | 1024 x 1024 | Instagram feed |
| 4:3 | 1152 x 864 | Presentations |
| 3:2 | 1200 x 800 | Blog headers |

## Pitfalls

- **HF gated model access**: model_info() returns public data even for gated repos you dont have access to. Use list_repo_files() to verify actual download access. See references/hf-gated-model-api-pitfalls.md.
- **Nano Banana prompt**: Beer requires every Gemini image prompt to start with "Nano Banana (Gemini 2.5 Flash Preview Image)." See `references/nano-banana-prompt.md` — use for Gemini calls only, not for FAL/FLUX.
- **When Beer sends his OWN image for content**: upload it to GitHub raw and post it directly. Do NOT generate a new version with Pillow or AI unless you can't handle his image (wrong format, too small, etc.). He will say "my pic not your create" if you substitute.
- **Full failure chain when you can't see Beer's image**: vision_analyze fails → try pixel analysis with Pillow → try browser view → ask Beer what it shows. If all image gen paths fail too (no FAL_KEY, Gemini quota exhausted, Enhanced Controls blocked), use Pillow to programmatically generate what he described. Report what worked and what didn't.
