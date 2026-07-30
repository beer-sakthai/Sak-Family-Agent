---
name: SakThai-telegram-media
author: SakThai
license: MIT
description: "Native Telegram media delivery using the MEDIA protocol — images, audio, video, and files"
version: 1.1.0
metadata:
  hermes:
    tags: [telegram, media, files, images, audio, video]
    category: communication
category: communication
---

# Telegram Media

## Sending files natively

Include `MEDIA:/absolute/path/to/file` anywhere in your response text:

| Extension | Renders as |
|-----------|-----------|
| `.png`, `.jpg`, `.jpeg`, `.webp` | Native photo |
| `.ogg` | Voice bubble |
| `.mp4` | Inline video |
| Any other | Downloadable file attachment |

## Image URLs

Markdown image syntax `![alt](url)` also renders as native photos on Telegram.

## Best practices

1. **Verify the file exists** before referencing it in MEDIA: — use `stat` or `read_file` first
2. **Use absolute paths** — relative paths may not resolve correctly
3. **Prefer OGG for voice notes** — Telegram native voice bubble format
4. **Audio files** — `.ogg` Opus-encoded gives the best native experience. Other formats (`.mp3`, `.wav`) send as file attachments
5. **File size limits** — Telegram has ~50 MB per file; for larger content, compress first
6. **Multiple files** — include multiple `MEDIA:` markers in sequence
7. **Don't describe the MEDIA** — just include the path; delivery is automatic

## Creating media for Telegram

- **TTS voice notes**: use `text_to_speech` tool — it outputs `.mp3` by default; convert to `.ogg` if voice bubble preferred
- **ASCII art**: generate with pyfiglet / cowsay, then pipe to PNG and send as photo
- **Screenshots**: use browser snapshot tools, then save to file and send
