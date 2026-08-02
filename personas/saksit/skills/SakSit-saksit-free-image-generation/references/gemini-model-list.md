# Gemini Image-Capable Models (Discovered 2026-07-25)

Confirmed by querying `https://generativelanguage.googleapis.com/v1beta/models`
with the GOOGLE_API_KEY from `.env`.

## Image Generation Models (supports `generateContent` + IMAGE modality)

| Model ID | Notes |
|----------|-------|
| `nano-banana-pro-preview` | Canonical Nano Banana model. Has its own quota pool. |
| `gemini-2.5-flash-image` | GA stable, fast, 1K default. Workhorse model. |
| `gemini-3-pro-image-preview` | Nano Banana Pro. 4K, thinking mode, 14 ref images. |
| `gemini-3-pro-image` | Same as preview but production. Paid tier. |
| `gemini-3.1-flash-image` | Latest flash, free tier. |
| `gemini-3.1-flash-image-preview` | Preview of 3.1 flash. |
| `gemini-3.1-flash-lite-image` | Lite version of flash image. |
| `gemini-2.0-flash-exp-image-generation` | Experimental. No longer in model list (404). |

## Text + Vision Models (can see images, not generate)

| Model ID | Context |
|----------|---------|
| `gemini-2.5-flash` | 1M context |
| `gemini-2.5-pro` | 2M context |
| `gemini-3-pro-preview` | Latest pro |
| `gemini-3.1-pro-preview` | 3.1 pro |
| `gemini-3-flash-preview` | Latest flash |

## Quota notes

- All free-tier image models share a daily quota pool. When one returns 429,
  all will until reset (~midnight PST).
- `nano-banana-pro-preview` may have its own pool (untested separately).
- Paid tier (billing enabled) removes all quota limits.
