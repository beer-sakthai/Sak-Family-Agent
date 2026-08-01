---
name: SakSit-image-generate-persist
category: creative
description: Generate an image, persist it, and register it for reuse.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Image, Generation, Persistence, Reuse, Download]
related_skills:
  - SakSit-api-troubleshoot-solutions
  - SakSit-free-image-generation
---

# SakSit Image Generate & Persist

Generate an image with `image_generate`, download the result to a permanent
location, and register it so any future session can find and reuse it.

This skill does NOT cover posting images to social platforms — that is
`linkedin-content-publishing`, `saksit-social-media-posting-workflows`, etc.

## When to Use

- Beer asks "create picture", "make image", "generate visual"
- You need an image asset that should survive beyond the current session
- You want to save a generated image to Google Drive for Beer's records
- You need to find a previously generated image by description or date

## Prerequisites

- `image_generate` tool (uses configured backend — FAL.ai/FLUX 2 in this env)
- Write access to `~/profiles/saksit/images/` (local persistent storage)
- OPTIONAL: Google Drive connection via Composio for off-machine backup
- OPTIONAL: GitHub `beer-sakthai/house-of-sak` repo for public raw URLs

**Environment note:** In DeepSeek-V4-Flash (opencode-go), `image_generate` may
require `FAL_KEY`. If unset, silently try fallback chains before reporting failure.

## Beer's rule: Execute, don't ask

Jul25 corrections — Beer's actual words this session:
- "Find the way make a choice i don't care get it for me"
- "Use funking Gemini"
- "Do it create it and do what you tell me"
- "Bit you try it first"

These mean: **stop presenting options, stop asking permission, pick one path,
execute it.** If it fails, silently try the next. Only ask Beer to toggle
settings / add credits / visit a URL after ALL automated paths are exhausted.
"Bit you try it first" = try every automated path before asking Beer to act.

## Nano Banana prompt

Beer requires every Gemini image prompt to start with
**"Nano Banana (Gemini 2.5 Flash Preview Image)."**
Applies ONLY to Gemini calls — not FAL/FLUX or Pillow.

## Fallback chain (try in order, silently, without narration)

1. **`image_generate`** (FAL/FLUX 2) — needs FAL_KEY in env.
2. **Gemini via google-genai** — read `GOOGLE_API_KEY` from `.env` files,
   use `/opt/data/.venv/bin/python3`. Watch for: 429 free-tier exhausted.
3. **Gemini via Composio direct curl** — check `MCP_COMPOSIO_API_KEY`,
   POST JSON-RPC 2.0 to `connect.composio.dev/mcp`. Enhanced Controls may block.
4. **Gemini via OpenRouter** — read `OPENROUTER_API_KEY`, model
   `google/gemini-2.5-flash-image`. Watch for: 402 insufficient credits.
5. **Pillow programmatic** — draw with Python Pillow. Always works.
6. **Only after all 5 fail** — ask Beer one action (toggle/credits/key).

## Quick Reference

| Step | Tool | Output |
|------|------|--------|
| Generate | `image_generate(prompt, aspect_ratio)` | Local file path or URL |
| Download | `terminal(curl/fetch)` if URL | Local `.png` file |
| Persist | Copy to `~/profiles/saksit/images/` | Permanent local copy |
| Backup | `terminal(gdrive upload)` or API | Google Drive copy |
| Register | `supermemory_store(content="image:...")` | Semantic-searchable record |
| Reuse | `supermemory_search(query="image:...")` | File path + description |

## Procedure

### 1. Generate the image

Use the `image_generate` tool or one of the fallback paths above.

| Aspect Ratio | Parameter | Use Case |
|--------------|-----------|----------|
| 16:9 landscape | `landscape` | LinkedIn, YouTube thumbnails |
| 9:16 portrait | `portrait` | Instagram Stories/Reels |
| 1:1 square | `square` | Instagram feed |

### 2. Download / localise the image

If `image_generate` returns a **local path** (e.g. `/tmp/...`), it is already
local. If it returns a **URL**, download via `terminal(curl -sLo ...)`.

### 3. Persist to permanent local storage

Copy to `~/profiles/saksit/images/<topic>-<context>-<style>.png`.

### 4. (Optional) Backup to Google Drive

Via Composio `GOOGLEDRIVE_UPLOAD_FROM_URL` or GitHub API push to `house-of-sak`.

### 5. Register the image for future discovery

Save to **Supermemory** AND Hermes `memory`:

```text
supermemory_store(content="image: <filename>.png — <description>")
memory(action="add", target="memory", content="Generated image: <path> — <description>")
```

### 6. Find a previously generated image

1. `supermemory_search(query="image: <topic>")`
2. `search_files(pattern="*.png", path="~/profiles/saksit/images/")`
3. Verify: `terminal(command="ls <path>")`
4. Deliver via `MEDIA:<path>`

## Pitfalls

- **Do not report failure after 1 path fails.** Try all 5 paths in the fallback
  chain before telling Beer an image can't be made.
- **Gemini quota exhausted.** All image models share a free-tier daily limit.
- **Enhanced Controls (Composio).** Needs toggle at composio.dev settings.
- **OpenRouter credits.** Only ~82 tokens remain (needs ~8192 for an image).
- **FAL_KEY not found.** Not present in any .env file. Create at fal.ai.
- **File name collision.** Check existing files before writing.
- **No embedded vision.** Cannot visually inspect output — rely on prompt.
- **Supermemory may 402.** Fall back to Hermes `memory` tool.

## Verification

```text
terminal(command="ls -la ~/profiles/saksit/images/<filename>.png")
supermemory_search(query="image: <filename>")
```
