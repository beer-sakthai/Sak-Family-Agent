---
name: SakSit-linkedin-content-publishing
version: 1.0.0
description: Publish professional updates, architecture breakdowns, and media-rich posts to LinkedIn via REST API.
category: content-marketing
tags:
- content
- linkedin
- publishing
- social
---

# SakSit LinkedIn Content Publishing Protocol

## Overview

Executes professional content broadcasting, thought leadership essays, and technical architecture reveals to LinkedIn via the LinkedIn REST API (`v2/posts`) and Composio toolchain.

Operated by **SakSit** (`@saksit_agent_bot`), the Social & Content Specialist of the House of Sak.

---

## 1. Operating Rules & Core Constraints

| Rule | Requirement |
|:---|:---|
| **Editorial Hook** | Lead with a compelling 1-line hook or hard milestone metric; avoid generic throat-clearing. |
| **Media Attachments** | Use 1200x627 (landscape) or 1080x1080 (square) high-res visuals via presigned upload URLs. |
| **Mission Alignment** | Emphasize positive vision, engineering craftsmanship, and open-source democratization. |
| **Zero Cost Policy** | Free tier API tooling and approved local assets only; no paid distribution platforms. |
| **Pre-Publishing Review** | Stage content drafts for Beer's review or automated editorial score ($\ge 85$). |

---

## 2. Publishing Workflow

```
Draft Concept ──► Resolve Author URN (LINKEDIN_GET_MY_INFO)
                         │
                         ▼
          Format Copy (Hook + Body Whitespace + Achievement Footer)
                         │
                         ▼
          Upload Media (Presigned URL PUT) ──► Publish Post (v2/posts)
```

1. **Resolve Identity**: Query person URN (`urn:li:person:<id>`).
2. **Draft & Stage**: Structure commentary ($\le 3000$ characters) with clear paragraph breaks.
3. **Attach Media**: Initialize image upload, upload binary, and link `image_urn`.
4. **Publish**: Dispatch to `MAIN_FEED` with `PUBLIC` visibility.

---

## 3. Reference Documents

For API payload examples, presigned upload steps, and copy templates:
- [LinkedIn Publishing Playbook & API Workflow](./references/linkedin-publishing-playbook.md)
- [House of Sak Content Series](./references/house-of-sak-content-series.md)
- [Achievement Footer Standard](./references/achievement-footer.md)
- [LinkedIn vs Instagram Asset Differences](./references/linkedin-instagram-asset-differences.md)
