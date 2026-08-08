# Nano Banana — Discovery 2026-07-25

> **Note (2026-08-01):** a real Google API key was found embedded in this file during a later migration and has been redacted below. Treat it as potentially already exposed and rotate it if it is still live.

## What it is

`nano-banana-pro-preview` is a **real Google Gemini model** for image generation.
Also branded as `gemini-3-pro-image-preview` = **"Nano Banana Pro"** in Composio's
tool descriptions.

## Where it was found

Listed in the Google Gemini API model catalog:
```bash
GET https://generativelanguage.googleapis.com/v1beta/models?key=$GOOGLE_API_KEY
```
Response includes:
```
models/nano-banana-pro-preview  methods=['generateContent', 'countTokens', 'batchGenerateContent']
models/gemini-3-pro-image       methods=['generateContent', 'countTokens', 'batchGenerateContent']
models/gemini-3-pro-image-preview methods=['generateContent', 'countTokens', 'batchGenerateContent']
models/gemini-3.1-flash-image   methods=['generateContent', 'countTokens', 'batchGenerateContent']
```

## What it means

"Nano Banana" is **not a prompt modifier** — it's an actual model name. The phrase
"Nano Banana (Gemini 2.5 Flash Preview Image)" that Beer wanted added to prompts
was referencing this model family.

## Access paths tested

| Path | Status | Blocked by |
|------|--------|-----------|
| `google-genai` SDK direct | ⚠️ Free tier exhausted daily | Quota reset ~midnight PST |
| Composio GEMINI_GENERATE_IMAGE | ❌ Enhanced Controls | Toggle OFF at composio.dev |
| OpenRouter `google/gemini-2.5-flash-image` | ⚠️ 82 credits | Add funds |

## Key

`GOOGLE_API_KEY=[REDACTED]` stored in
`/opt/data/profiles/saksit/.env`.
