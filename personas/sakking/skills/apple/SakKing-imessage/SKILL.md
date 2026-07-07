---
name: SakKing-imessage
description: "Send and read iMessages via terminal using messages-cli."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [iMessage, Apple, messaging, macOS]
prerequisites:
  commands: [messages-cli]
---

# iMessage

Send and read iMessages from the terminal using `messages-cli`.

## Prerequisites

- macOS
- Install: `brew install messages-cli`
- Grant accessibility permissions when prompted

## Quick Reference

```bash
# Send a message
messages-cli send "+1234567890" "Hello from terminal"

# Send to a contact
messages-cli send "John" "Meeting at 3pm"

# Read recent messages
messages-cli recent

# List conversations
messages-cli conversations

# Read messages from a specific conversation
messages-cli read "John" --limit 10
```

## Attachments

```bash
messages-cli send "John" --attachment /path/to/photo.jpg
```