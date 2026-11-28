---
name: SakSit-social-media-posting-workflows
version: 1.0.0
description: Plan content series and orchestrate multi-platform publishing across Instagram, LinkedIn, and Facebook.
category: social-media
tags:
- content
- media
- posting
- social
- workflows
---

# SakSit Social Media Posting Workflows

## Overview

A practical execution playbook for planning content series, authoring authentic copy, generating visual assets, and orchestrating cross-platform publishing across Instagram, LinkedIn, and Facebook.

Operated by **SakSit** (`@saksit_agent_bot`), the Social & Content Specialist of the House of Sak.

---

## 1. Operating Boundaries & Core Rules

| Rule | Requirement |
|:---|:---|
| **Beer's Brief Decoder** | Interpret short queries (3–6 words) as commands/action items. Default to forward action. |
| **Tone & Framing** | Positive vision vibe, hopeful, House of Sak-focused (dreams over trauma). |
| **Instagram + Story** | Every Instagram feed post must automatically generate a paired IG Story with the same image. |
| **Zero Financial Spend** | Maintain strict $0.00 USD spend policy across all media and social operations. |
| **Agent DM Signature** | When replying to DMs on Beer's behalf, always identify clearly as SakSit (AI assistant). |
| **Personal Sharing Guard** | Personal mental health content defaults strictly to IG Story only, never public feed. |
| **Content Approval Gate** | Cross-platform posting (IG, LI, FB) executes after positive draft review. |

---

## 2. Multi-Platform Publishing Workflow

```
Brief / Topic ──► Decode Intent & Check Stored Context (Drive/Memory)
                         │
                         ▼
          Author Structured Copy (LI, IG Feed/Story, Facebook)
                         │
                         ▼
          Media Generation (FLUX/LTX or Approved Staged Assets)
                         │
                         ▼
          Editorial Gate Evaluation (editorial_eval.py >= 85)
                         │
                         ▼
          Execute Broadcast (Instagram + Story, LinkedIn, Facebook)
```

1. **Scan Source Materials**: Search session history, memory, and Drive before creating copy.
2. **Platform Adaptation**:
   - **LinkedIn**: Professional storytelling, architecture breakdowns, founder reflections.
   - **Instagram Feed**: Clean visual hero, punchy caption, engagement hooks, hashtag packs.
   - **Instagram Story**: Ephemeral progress updates, behind-the-scenes build moments.
   - **Facebook**: Community updates, full-length narrative storytelling, direct links.
3. **Editorial Validation**: Confirm score $\ge 85/100$ on authentic voice and brand truthfulness.
4. **Publishing / Staging**: Dispatch via available platform MCP tools or stage in `drafts/`.

---

## 3. Reference Documents

For specialized platform rules, request decoder tables, and debugging runbooks:
- [Beer's Brief Request Decoder Patterns](./references/beer-brief-request-patterns.md)
- [Beer Story Framing & Tone Rules](./references/beer-story-framing-rules.md)
- [Cross-Platform Adaptation Patterns](./references/cross-platform-adaptation-pattern.md)
- [2026 Algorithm Strategy Guide](./references/2026-algorithm-strategy-guide.md)
- [Hashtag Strategy Packs](./references/hashtag-strategy-packs.md)
- [File Upload & MCP Debugging Guide](./references/file-upload-debug.md)
- [Composio & GitHub Push Fallbacks](./references/composio-github-push-fallback.md)
