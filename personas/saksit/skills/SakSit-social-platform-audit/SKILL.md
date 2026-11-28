---
name: SakSit-social-platform-audit
version: 1.1.0
description: Pre-posting social platform connectivity, profile completeness, and audience readiness audit protocol.
category: social-media
tags:
- audit
- content
- platform
- social
---

# Social Platform Audit Protocol

Standard operating procedure for scanning connected social toolkits, evaluating profile completeness, and assessing platform health before publishing.

## 1. Operating Invariants
- **Full Spectrum Inventory**: Never restrict audits to curated "top picks". Audit every connected platform (LinkedIn, Instagram, YouTube, X, Hugging Face) and present objective trade-offs.
- **Identity Grounding**: Query authenticated user profiles and permissions before recommending posting actions.
- **Actionable Gap Analysis**: Highlight missing profile elements (bios, website links, avatars) as concrete fix tasks.

## 2. Audit Workflow
1. **Discovery**: Query connected integrations and active OAuth credentials.
2. **Profile Completeness**: Evaluate avatar, bio, website URL, and verified links across all channels.
3. **Audience & Metric Baseline**: Record follower counts, engagement baselines, and historical reach.
4. **Channel Readiness Matrix**: Output a concise 3-column table (Platform | Status | Action Item).

## 3. References & Deep Dive Guides
- Platform-Specific Audits: [Hugging Face Profile](references/huggingface-profile-audit.md) | [YouTube Deep Dive](references/youtube-audit-deep-dive.md)
- Completeness Checklist: [Profile Completeness Audit](references/profile-completeness-audit.md)
- Case Studies & Historical Audits: [Real Audit 2026-07-06](references/real-audit-2026-07-06.md) | [Launch Blitz Plan](references/post-audit-launch-blitz.md)
- Storage & Patterns: [Drive Archive Pattern](references/archive-to-google-drive-example.md) | [Raw URL Pattern](references/github-raw-url-instagram-pattern.md)
