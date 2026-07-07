---
name: sakthai-voice-delivery
category: voice
description: 'Deliver Telegram replies as matched voice notes — preferred voice is
  en-US-BrianMultilingualNeural (multilingual, Thai-capable US male). Covers edge-tts
  setup, MEDIA: file sending, Hermes TTS config, and browser-automation quirks on
  WSL.'
version: 1.0.0
platforms:
- linux
- macos
- wsl
metadata:
  sakthai:
    tags:
    - hermes
    - productivity
    related_skills: []
    source: hermes:voice-delivery
---

# Voice Delivery for Hermes Agent

Send Telegram replies as a short text message immediately followed by a matching BrianMultilingual voice note.

## When to Use

- Every Telegram chat reply to Beer (preferred channel).
- When the text is worth hearing but not worth reading at length.
- When the user explicitly asks for voice.
- When Thai or other non-English text is part of the reply — use BrianMultilingual so the accent stays consistent.

Skip voice on trivial acknowledgments ("ok", "done", "no") to save credits and tokens.

## Setup

### Edge TTS (free, no API key)

Requires `edge-tts` Python package. Install into a dedicated venv if the system Python has PEP 668 restrictions:

```bash
uv venv ~/.hermes/.venv-edges
uv pip install --python ~/.hermes/.venv-edges/bin/python edge-tts
```

Verify:
```bash
~/.hermes/.venv-edges/bin/edge-tts --voice en-US-BrianMultilingualNeural \
  --text "Hello" --write-media /tmp/smoke.mp3
ls -la /tmp/smoke.mp3
```

### Hermes TTS Config

Set the Hermes config so auto-voice uses the same voice:

```bash
hermes config set tts.provider edge
hermes config set tts.edge.voice en-US-BrianMultilingualNeural
```

Restart the gateway (`/restart`) for the config to take effect.

### Browser Automation on WSL (Playwright + Chrome)

On WSL/Ubuntu where Playwright's Chromium build may fail (e.g. `ubuntu26.04-x64`), use the system Chrome binary instead:

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page()
    page.goto('https://example.com')
    print(page.title())
    browser.close()
```

Invoke from the Hermes edge venv:
```bash
source /home/sakthai/.hermes/.venv-edges/bin/activate
python3 your_script.py
```

See `references/playwright-system-chrome.md` for the verified Ubuntu 26.04 workaround.

## Pattern

1. **Draft the short text** (3–5 lines, voice is the primary channel).
2. **Generate the voice note**:
   - Preferred: use Hermes `text_to_speech` with `provider: edge` and the configured BrianMultilingual voice.
   - Fallback: call the Edge TTS CLI directly:
     ```bash
     ~/.hermes/.venv-edges/bin/edge-tts \
       --voice en-US-BrianMultilingualNeural \
       --text "<short text>" \
       --write-media /home/sakthai/.hermes/audio_cache/<name>.mp3
     ```
3. **Send via MEDIA:** in the Telegram message, then call `send_message` with `MEDIA:<absolute_path>`.

## Repo/user conventions

- **Hermes proof surface:** when asked to verify a config or integration, prefer `hermes mcp test <name>` over `hermes chat -q` because the latter can hit upstream provider rate limits before the MCP path is even reached.
- **Terminal hygiene:** do not show terminal command dumps inside Telegram replies; report status, delta, and next action only.
- **TTS venv:** use `/home/sakthai/.hermes/.venv-edges` with the Python `edge-tts` CLI; mark the Node CLI `@andresaya/edge-tts` on PATH as deprecated for Hermes TTS.
- **Voice rule:** voice is primary when it adds value and reduces tokens; do not auto-voice trivial 1–3 line replies. For short non-value-additive replies, send text only. For longer substantive replies, keep text to 3–5 lines and add a BrianMultilingual voice note as the primary channel.
- **Thai / multilingual rule:** always use BrianMultilingual (or another MultilingualNeural voice) when the spoken text might include Thai or other non-English content; this preserves US-accent English while correctly rendering the foreign words.

## Voicenote delivery to Telegram

edge-tts generates MP3; Telegram voice bubbles require Opus in OGG. Convert with ffmpeg before sending as a voice note:

```bash
ffmpeg -y -i /tmp/voice.mp3 -c:a libopus -b:a 32k /tmp/voice.ogg
```

Send as voice bubble:
<!-- MEDIA:/tmp/voice.ogg -->
```
MEDIA:/tmp/voice.ogg
```

## Voice choice

Permanent default for Hermes: `en-US-BrianMultilingualNeural` (multilingual, Thai-capable). Do not keep asking which voice to use; if unsure, use Brian.

## Shortcut: send generic greeting to another recipient

When the user asks to "say hello" to named recipients they haven't registered:
1. Generate the voice note for that recipient's name.
2. Clarify recipient delivery destination in one short line.
3. If the user confirms delivery to an existing contact, send immediately.
4. Otherwise deliver to Beer's home channel (`telegram:8618306046`) and note that direct send requires the recipient's Telegram ID/username.

## Instagram destination defaults

Confirmed Instagram publishing account for Beer: `beerthaish` (IG User ID `27647006041564332`).

## Pitfalls
