---
name: sakthai-media-playback
category: media
description: Find and deliver playable media links for requested tracks, playlists,
  or sleep/relaxation content across desktop and mobile.
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    - media
    related_skills: []
    source: hermes:media-playback
---

# Media playback: links and device delivery

Use when the user asks to play media on a specific service or device, or wants a track/playlist sent for playback. This skill does not cover generating media, only finding and delivering playable media links.

## Preferred flow
1. Search only when the user does not provide a track or link.
2. If the user mentions a service by name, use that service’s direct link format.
3. On desktop, open the link in Chrome when playback is requested.
4. On mobile, deliver a direct link via Telegram because I cannot control the phone.

## Constraints
- I cannot control the user’s phone apps.
- I cannot launch Spotify/YouTube/Ryzm inside the phone from this session.
- For cross-device playback, treat Telegram as the transfer surface.

## Reference files
- `references/spotify_quick_links.md` — sleep/relaxation tracks already used with this user.
