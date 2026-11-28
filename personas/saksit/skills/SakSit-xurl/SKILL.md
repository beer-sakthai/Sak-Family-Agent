---
name: SakSit-xurl
version: 1.1.0
description: Official X (Twitter) API integration protocol via the xurl CLI for publishing, searching, and timeline monitoring.
category: social-media
tags:
- content
- social-media
- twitter
- xurl
---

# xurl CLI Protocol

Standard operating procedure for interacting with the X (Twitter) developer platform using the official `xurl` binary.

## 1. Security Invariants
- **Secret Isolation**: Never inspect, read, or print `~/.xurl` contents to LLM context.
- **No Inline Credentials**: Prohibit inline credential flags (`--bearer-token`, `--consumer-secret`). All auth must rely on existing local token configuration.
- **Check Status Safely**: Always verify session validity via `xurl auth status`.

## 2. Core Publishing Flow
1. **Preflight**: Verify `xurl auth status` indicates an active, valid token.
2. **Drafting**: Ensure post text conforms to character budgets ($\le 280$ chars or long-form threshold).
3. **Execution**: Post content using `xurl post "..."`.
4. **Verification**: Confirm returned JSON payload contains a valid tweet ID.

## 3. References & Command Recipes
- Detailed command matrix, media upload instructions, and raw v2 endpoint schemas: [xurl Commands & Auth Guide](references/xurl-commands-and-auth.md)
