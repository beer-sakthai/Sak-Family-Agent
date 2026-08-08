# Vision Model Availability — Beer's Environment (2026-07-07)

## Current Model

- **Primary:** `deepseek-v4-flash` via `opencode-go` provider — **NO vision**
- **Fallback:** `deepseek-v4-flash-free` via `opencode` provider — **NO vision**
- **Vision fallback (auxiliary):** "Console Go" provider — **FAILING** (upstream errors, large images rejected)

## Which Models CAN See Images

Available through Beer's configured providers:

| Provider | Models with Vision | Status |
|----------|-------------------|--------|
| **OpenRouter** | `anthropic/claude-sonnet-4`, `openai/gpt-4o`, `google/gemini-2.5-flash`, `qwen/qwen-vl-plus` | Available but needs config change — commented out in `profiles/saksit/config.yaml` as fallback_model |
| **Nous Portal** | Various Nous/Hermes models | May have vision — depends on user's Portal account |
| **OpenAI Codex** | GPT-4o (via OAuth) | Not tested for vision in this environment |

The config has a commented-out fallback block:
```yaml
# fallback_model:
#   provider: openrouter
#   model: anthropic/claude-sonnet-4
```
Uncommenting this and switching `model.default` to a vision-capable model would enable `vision_analyze`.

## Workarounds When Vision Is Unavailable

1. **Send the image file as a media message** — Beer can see it on his end. Include `MEDIA:/path/to/image` in the response.
2. **Describe what you expect based on file name and context** — e.g., "Gemini_Generated_Image_* = AI artwork, Personal_AI_Agent_Ecosystem_Overview.png = diagram"
3. **Use Pillow pixel analysis** for basic color/edge/dimension data from local files.
4. **Ask Beer to describe it** — a simple "what's in this one?" works.

## File-Name Clues for Blind Image Work

| File Name Pattern | Likely Content |
|-------------------|----------------|
| `Gemini_Generated_Image_*.png` | AI-generated agent artwork, high-res (7-10MB) |
| `Personal_AI_Agent_Ecosystem_Overview.png` | Diagram of the 6-agent ecosystem (~4.5MB) |
| UUID-style name (`925100f1-799b-*.png`) | Agent cards or visuals from SakSit folder (~4-7MB) |
| `The_House_of_Sak.pdf` / `The_House_of_Sak` (Slides) | Presentation deck — not an image but can be exported |
