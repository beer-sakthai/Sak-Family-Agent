---
name: sakthai-instagram-qa
category: social
description: Provide a verified, repeatable workflow for checking Instagram content
  quality before publishing
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    related_skills: []
    source: hermes:instagram-qa
---

# Instagram Business Content QA

## Purpose

Provide a verified, repeatable workflow for checking Instagram content
quality before publishing. Prevents wrong/misleading info from being posted.

## Applicable accounts

- `beerthaish` (Instagram Business/Creator)
- IG user id: `27647006041564332`

## Pre-publish checklist

1. **Verify caption text**
   - spell-check proper nouns and place names
   - grammar: contractions, punctuation
   - ensure no unverified claims, dates, or stats

2. **Verify media**
   - ensure the image/video matches the caption
   - check that any UI text in screenshots is legible and correct
   - confirm no confidential data/chats are exposed unintentionally

3. **Confirm before send**
   - show a preview/caption summary to the user
   - wait for explicit approval before publish

## Verified endpoints

Use only these approved Instagram tools:

- `INSTAGRAM_GET_USER_INFO`
- `INSTAGRAM_GET_IG_USER_STORIES`
- `INSTAGRAM_GET_IG_MEDIA`
- `INSTAGRAM_POST_IG_USER_MEDIA`
- `INSTAGRAM_POST_IG_USER_MEDIA_PUBLISH`
- `INSTAGRAM_GET_IG_USER_CONTENT_PUBLISHING_LIMIT`

## Session context

Session id: `sell`

## Error handling

- If a publish fails with status 9007, verify container status first
- If quota limit reached, inform user before retrying
- If caption or media seems wrong, block publish and report issues

## Notes

This skill should be used for every IG post and story workflow.
