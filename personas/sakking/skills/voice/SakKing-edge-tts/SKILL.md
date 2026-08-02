---
name: SakKing-edge-tts
description: "Generate voice notes via local Edge TTS for Hermes/Saksee. Use edge-tts CLI with en-US-EmmaMultilingualNeural, convert to Telegram OGG/Opus, and deliver as voice bubbles."
version: 1.0.0
author: SakSee
license: MIT
tags: [tts, voice, telegram, edge, edge-tts, communication]
---

# Edge TTS Voice Notes

## Overview

Generate short voice notes from text using the **free Edge TTS** CLI on this host.
No API key or paid provider is needed.

## Voice / pronunciation
- **Use only:** `en-US-EmmaMultilingualNeural`
- Do not substitute other voices unless Beer explicitly requests a change.
- Keep utterances short (< 30s) for Telegram friendliness.

## Required tools
- **CLI:** `edge-tts` (installed at `/home/sakthai/.npm-global/bin/edge-tts`)
- **Audio:** `ffmpeg` for converting MP3 → OGG Opus (Telegram voice bubble format)

## One-shot generation flow
1. Generate MP3 with Edge:
   ```bash
   mkdir -p /home/sakthai/.hermes/profiles/saksee/audio_cache
   edge-tts synthesize \
     --text "Hello Beer, this is Saksee." \
     --voice en-US-EmmaMultilingualNeural \
     --output /home/sakthai/.hermes/profiles/saksee/audio_cache/note.mp3
   ```
2. Convert to OGG Opus for Telegram:
   ```bash
   ffmpeg -y -i /home/sakthai/.hermes/profiles/saksee/audio_cache/note.mp3 \
     -c:a libopus -b:a 32k -ar 24000 -ac 1 \
     /home/sakthai/.hermes/profiles/saksee/audio_cache/note.ogg
   ```
3. Reference in reply with `MEDIA:/abs/path` to deliver as a voice bubble.

## Safety / privacy
- Do not narrate secrets, tokens, or private identifiers in voice output.
- If a generated file already exists, either overwrite or write to a timestamped path.

## Reliability notes
- Built-in OpenAI TTS is blocked here by a provider billing 402. Use Edge only.
- If `edge-tts` is missing, fall back to text-only and disable voice delivery for the rest of the session.
- For long outputs, split into 2–3 short clips instead of one long MP3.

## Pitfall: double `.mp3` extension
`edge-tts synthesize --output note.mp3` creates `note.mp3.mp3`. Either pass a path
without extension, pass `.ogg` directly, or rename afterward. The MP3 in
`/home/sakthai/.hermes/profiles/saksee/audio_cache/` should then be converted to
OGG Opus for Telegram voice delivery.