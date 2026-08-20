---
name: SakSit-learned-oc-ecosystem
description: OpenClaw ecosystem tools reference guide.
version: 1.0.0
author: SakSit (cron research)
openclaw_upstream: https://github.com/openclaw/openclaw/tree/main/skills/spotify-player
category: social-media
tags:
- OpenClaw
- Reference
---

# OpenClaw Ecosystem: spotify-player (spogo)

## Tool Researched: spotify-player

**Source:** OpenClaw skill at `skills/spotify-player`
**Category:** Terminal productivity / media control

### What It Is

`spotify-player` is the umbrella name for two complementary terminal Spotify clients that OpenClaw wraps into a single skill interface:

1. **spogo** (preferred) — a lightweight CLI (`spogo`) for search, playback, and device management. Installed via `brew install spogo` (tap: `steipete/tap`). Requires Spotify Premium.
2. **spotify_player** (fallback) — a TUI-based Spotify client with full keyboard navigation. Installed via `brew install spotify_player`.

### Key Commands (spogo)

| Action | Command |
|--------|---------|
| Search | `spogo search track "query"` |
| Play/Pause | `spogo play` / `spogo pause` |
| Next/Prev | `spogo next` / `spogo prev` |
| List devices | `spogo device list` |
| Set device | `spogo device set "<name\|id>"` |
| Status | `spogo status` |
| Auth import | `spogo auth import --browser chrome` |

### Key Commands (spotify_player fallback)

| Action | Command |
|--------|---------|
| Search | `spotify_player search "query"` |
| Playback | `spotify_player playback play\|pause\|next\|previous` |
| Connect device | `spotify_player connect` |
| Like track | `spotify_player like` |

### Setup Notes

- Config folder: `~/.config/spotify-player` (e.g., `app.toml`)
- For Spotify Connect, set a `client_id` in config
- TUI shortcuts viewable via `?` inside the app
- Both tools need a **Spotify Premium** account

### Use Cases

- Terminal-first music control without leaving the shell
- Automating playback in demos or productivity sessions
- Lightweight alternative to the Spotify desktop app
