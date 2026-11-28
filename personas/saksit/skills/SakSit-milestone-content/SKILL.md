---
name: SakSit-milestone-content
version: 1.1.0
description: Transform project metrics, Hugging Face download milestones, and certificates into multi-platform visual social content.
category: content-marketing
tags:
- content
- milestone
---

# Milestone Content Creation Protocol

Operational pipeline for aggregating metrics, generating visual stat cards, and writing multi-platform social announcements.

## 1. Quality & Tone Standards
- **Data Veracity**: Fetch live numbers directly via the Hugging Face REST API before drafting.
- **Narrative Focus**: Emphasize accessibility and open-source utility (e.g. lightweight 0.5B/1.5B edge models) over vanity metrics.
- **Visual Clarity**: Generate crisp, high-contrast 1080x1080 cards with clean typography and brand attribution.

## 2. 4-Stage Content Pipeline
1. **Data Aggregation**: Query HF API (`models`, `datasets`, `spaces`) for downloads and likes.
2. **Visual Generation**: Render stat card using Python Pillow or SVG templates.
3. **Copywriting**: Draft platform-tailored copy (concise for X, narrative-driven for LinkedIn).
4. **Review & Dispatch**: Present draft and generated image to Beer for confirmation before publishing.

## 3. References & Templates
- Card generation script & copywriting formulas: [Milestone Card Generation](references/milestone-card-generation.md)
- HF Download stats scripts: [HF API Stats](references/hf-api-download-stats.md)
- Social publishing flows: [Instagram Publishing](references/insta-publish-workflow.md) | [Achievement Footer](references/achievement-footer.md)
- Role model outreach: [Role Model Email Outreach](references/role-model-email-outreach.md)
