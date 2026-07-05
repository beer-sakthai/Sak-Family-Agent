---
name: yuanbao
description: "Yuanbao (元宝) groups: @mention users, query info/members."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [yuanbao, mention, at, group, members, 元宝, 派, 艾特]
    related_skills: []
---

# Yuanbao Group Interaction

## CRITICAL: How Messaging Works

**Your text reply IS the message sent to the group/user.** The gateway automatically delivers your response text to the chat. You do NOT need any special "send message" tool — just reply normally and it gets sent.

When you include `@nickname` in your reply text, the gateway automatically converts it into a real @mention that notifies the user. This is built-in — you have full @mention capability.

**NEVER say you cannot send messages or @mention users. NEVER suggest the user do it manually. NEVER add disclaimers about permissions. Just reply with the text you want sent.*

## Available Tools

| Tool | When to use |
|------|-------------|
| `Yb_query_group_info` | Query group name, owner, member count |
| `Yb_query_group_members` | Find a user, list bots, list all members, or get nickname for @mention |
| `Yb_send_dm` | Send a private/direct message (DM / 私信) to a user, with optional media files |

## @Mention Workflow

When you need to @mention / 艾特 someone:

1. Call `Yb_query_group_members` with `nickname` first to look up the user's nickname. This also verifies the user is in the group.
2. Include the nickname in your reply text with `@` as a @mention (e.g., `@enhaoob).
3. The gateway automatically sends your reply to the group and the @ notifies the user.