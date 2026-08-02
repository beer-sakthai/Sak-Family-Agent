# Image Generation Backends — Availability & Setup

Current state as of July 2026 in the Hermes/SakSit sandbox environment.

## Backend Comparison

| Backend | Quality | Cost | Setup | This Sandbox |
|---------|---------|------|-------|-------------|
| **Gemini Flash/Pro via Composio** | ⭐⭐ good | **🆓 Free within Gemini quotas** | **✅ No auth needed** | **✅ Available now** |
| Pillow text cards | ⭐ text-only typography | Zero | `uv pip install Pillow` | ✅ Always works |

---

## Gemini via Composio (✅ Available — try first)

Gemini is already connected to Composio (`GEMINI_GENERATE_IMAGE`). **No authentication or approval needed** — the toolkit says "does not require authentication" and is ready to use immediately. This is the preferred free image generation path.

### Quick start

```text
tool: GEMINI_GENERATE_IMAGE
arguments:
  model: "gemini-2.5-flash-image"
  prompt: "Your detailed visual description"
  aspect_ratio: "4:5"        # or 1:1, 16:9, 9:16, etc.
  image_size: "1K"           # or 2K, 4K (gemini-3-pro only)
```

### Models and specs

| Model | Quality | Speed | Features |
|-------|---------|-------|----------|
| `gemini-3-pro-image-preview` | Best (4K) | Medium | Thinking mode, 14 ref images |
| `gemini-2.5-flash-image` | Good (1K) | Fast | GA stable, recommended first try |
| `gemini-2.0-flash-exp-image-generation` | Fair | Fastest | Experimental, no aspect ratio param |

### Aspect ratios
1:1, 4:5, 3:4, 16:9, 9:16, 2:3, 3:2, 4:3, 5:4, 21:9

### Safety settings (if prompt gets blocked)
```json
"model": "gemini-2.5-flash-image",
"safety_settings": [
  {"category":"HARM_CATEGORY_HARASSMENT","threshold":"BLOCK_NONE"},
  {"category":"HARM_CATEGORY_HATE_SPEECH","threshold":"BLOCK_NONE"},
  {"category":"HARM_CATEGORY_SEXUALLY_EXPLICIT","threshold":"BLOCK_NONE"},
  {"category":"HARM_CATEGORY_DANGEROUS_CONTENT","threshold":"BLOCK_NONE"}
]
```

### Pitfalls
- Concurrency >3 returns HTTP 429 — keep ≤3 parallel calls, exponential backoff
- 4K images cost more tokens; set `image_size: "1K"` for faster results
- Hosted URLs expire — persist via `GOOGLEDRIVE_UPLOAD_FROM_URL` if needed
- Trademarked content triggers PROHIBITED_CONTENT (400) — rephrase neutrally

---

## Pillow Typography Cards (Last resort — concept drafts only)

Beer explicitly rejected these as publishable-quality visuals (July 11 session).
Use ONLY for:
- Concept drafts to show layout/idea before generating the real image
- Quick mockups for Beer to review the text/structure
- When ALL other backends are blocked AND Beer knows these are drafts

| **Mark them clearly:** When delivering Pillow cards, say "Here's the concept draft — not publishable quality."

## HF Spaces (Unavailable)

`api-inference.huggingface.co` does not resolve DNS from this sandbox.
Do not attempt.

## Quick decision flow

```
Beer wants images
    ↓
Gemini Composio available? → YES → Use GEMINI_GENERATE_IMAGE (free, immediate)
    ↓ NO / blocked
Show Pillow concept drafts + tell Beer to use Gemini instead
```
