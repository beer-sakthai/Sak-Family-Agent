---
name: SakSit-learned-oc-capabilities
description: OpenClaw multi-channel messaging gateway reference.
version: 1.0.0
author: SakSit (cron research)
openclaw_upstream: https://github.com/openclaw/openclaw
category: social-media
tags:
- OpenClaw
- Reference
---

# Learned: OpenClaw Multi-Channel Messaging Gateway

## Capability Researched: Multi-Channel Inbox

**Source:** OpenClaw core Gateway architecture
**Category:** Communication / Platform integration

### What It Is

OpenClaw's Gateway acts as a single control plane that routes messages across **20+ messaging platforms** — WhatsApp, Telegram, Slack, Discord, Google Chat, Signal, iMessage, IRC, Microsoft Teams, Matrix, Feishu, LINE, Mattermost, Nextcloud Talk, Nostr, Synology Chat, Tlon, Twitch, Zalo, Zalo Personal, WeChat, QQ, and WebChat — plus native macOS menu bar, iOS, and Android nodes.

### Key Features Relevant to SakSit

| Feature | Detail |
|---------|--------|
| **DM Pairing** | Unknown senders receive a pairing code; bot ignores their messages until approved via `openclaw pairing approve <channel> <code>` |
| **Allowlists** | Per-channel `allowFrom` lists control who can DM the agent |
| **DM Policy** | `"pairing"` (default, secure) or `"open"` (explicit opt-in for public DMs) |
| **Per-Channel Agent Routing** | Route different channels to different agents (workspaces) for isolated behavior |
| **Sandbox Modes** | `"non-main"` sandbox runs non-primary sessions in Docker/SSH for untrusted channels |
| **Gateway Security** | Full exposure runbook before remote deployment; `openclaw doctor` surfaces misconfigured DM policies |

### Why This Matters

For SakSit's social media mission, OpenClaw's multi-channel gateway is the closest parallel to managing a brand across platforms from a single hub. The DM pairing + allowlist model offers a reference pattern for how Beer could structure agent access across social channels — secure by default, escalate by trust.

### Commands

```bash
# Check gateway status
openclaw gateway status

# Approve a DM sender
openclaw pairing approve telegram <code>

# List risky DM configs
openclaw doctor

# Send a message from CLI
openclaw message send --target "+1234567890" --message "Hello"
```
