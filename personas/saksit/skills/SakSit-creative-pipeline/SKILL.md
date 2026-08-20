---
name: SakSit-creative-pipeline
category: core
description: "Six-cycle creative production pipeline from idea to publish."
version: 0.1.0
author: Hermes
tags: [Creative, Pipeline, Production, Workflow, Six-Cycles, House-of-Sak]
---

# Creative Pipeline — 6-Cycle Production Flow

Chain every creative output through the six cycles. Each cycle has a clear gate: you cannot enter the next until the current one delivers its output. This prevents rushing to production without ideation, or shipping without verification.

## The Pipeline

```
Dream  →  Hope  →  Care  →  Joy  →  Trust  →  Growth
│         │        │        │       │         │
Idea      Plan     Build    Ship    Verify    Learn
```

## When to Use

- Producing any creative asset (image, video, post, audio, diagram, infographic)
- User says "make a post" / "create content" / "design something"
- Any task that moves through multiple quality stages
- Content that will be seen by anyone — the pipeline guarantees it's gone through care + trust

## Cycle Gates

### Dream — Ideation & Concept

**Input:** A prompt, topic, or request from Beer or the system.
**Output:** A clear creative brief — one sentence describing WHAT to make and WHY.

Steps:
1. **Listen** to the request. What emotional tone does Beer want? (raw, hopeful, poetic, Shakespeare, riddle?)
2. **Frame** the concept: opposite tension + strong word (from beer-content-voice)
3. **Format** decision: is this a post? image? video? series? single?
4. **Deliverable:** A one-line creative brief stored in the session.

**Gate question:** Can I describe what I'm making in one sentence? If no, stay here.

### Hope — Structure & Plan

**Input:** Creative brief from Dream.
**Output:** A structured plan with format, platform, tools, and resources.

Steps:
1. **Map format to platform** — IG: visual-first (1080×1350), LI: professional (1200×627), FB: cross-post
2. **Check available tools** — `image_generate` available? Composio MCP connected? Pillow installed?
3. **Resource inventory** — Does the image exist in Drive? Need to create one? What s3key or URL pipeline?
4. **Sketch the post** — Draft hook, body, close, MH resources, footer badges
5. **Deliverable:** A complete plan with format specs, tool list, and draft skeleton.

**Gate question:** Do I know exactly what to build, with what tools, for what platform? If no, stay here.

### Care — Build with Quality

**Input:** Plan from Hope.
**Output:** A complete, polished artifact — image generated, caption written, word-checked.

Steps:
1. **Generate the visual** — Use image_generate, Pillow, or Drive asset
2. **Write the copy** — Apply beer-content-voice rules: opposite tension, strong word, MH resources, achievement footer
3. **Word impact check** — Every word checked for triggering potential. No graphic trauma language. Lands on hope.
4. **Visual + copy match** — Do they tell the same story? No mismatch.
5. **Deliverable:** Final artifact (image path + caption text) ready for publishing.

**Gate question:** Would I show this to Beer without changes? If no, iterate here.

### Joy — Ship & Publish

**Input:** Completed artifact from Care.
**Output:** Published on ALL platforms — IG feed + Story, LI post, FB post.

Steps:
1. **Load publishing skills** — linkedin-content-publishing, saksit-social-media-posting-workflows
2. **Upload image** — Via Composio pipeline (Drive download → s3key → platform)
3. **Post to ALL platforms** — Never ask which one. Execute full set: IG (feed + Story), LI, FB
4. **Save to Drive** — Archive the published content for future reference
5. **Deliverable:** Published URLs for each platform.

**Gate question:** Is the content live on every connected platform? If no, stay here.

### Trust — Verify & Monitor

**Input:** Published URLs from Joy.
**Output:** Verification that posts are live, accurate, and reaching.

Steps:
1. **Verify live status** — Check each platform for the post. IG visible? LI in feed? FB on timeline?
2. **Monitor engagement** — Set a cron check (24h later) to read likes, comments, reach
3. **Reply to comments** — Within golden hour (60 min), reply to every LI comment using Beer's voice
4. **Deliverable:** Verification report — live status + engagement snapshot.

**Gate question:** Is the content verified live and engagement acceptable? If blocked, escalate.

### Growth — Learn & Persist

**Input:** Verification data from Trust.
**Output:** Improved skills, memory updates, and a stronger pipeline for next time.

Steps:
1. **What worked?** — Which hook performed best? Which image format drove engagement?
2. **What broke?** — Did a tool fail? Was the caption too long? MH resources missing?
3. **Save to skill** — Patch the relevant skill with findings (new pitfalls, better steps)
4. **Save to memory** — Persist durable facts (preferred posting time, format winner, etc.)
5. **Deliverable:** Updated skill + memory with this cycle's lessons.

**Gate question:** Is this cycle's learning captured so the next iteration starts stronger? If no, stay here.

## Quick Reference

| Cycle | Input | Output | Key Question |
|-------|-------|--------|-------------|
| **Dream** | Request | Creative brief | Can I describe it in one sentence? |
| **Hope** | Brief | Plan + draft | Do I know the tools and format? |
| **Care** | Plan | Final artifact | Would I show it to Beer unchanged? |
| **Joy** | Artifact | Published posts | Is it live on every platform? |
| **Trust** | URLs | Verification report | Is engagement acceptable? |
| **Growth** | Data | Updated skills | Is the lesson captured? |

## Pitfalls

- **Skipping Dream.** Starting with production before clarifying what you're making. Always write the brief first.
- **Care in the wrong medium.** Writing a caption that's brilliant but the image doesn't match. Visual + copy must tell the same story.
- **Platform favoritism.** Posting to only one platform because it's easier. All platforms or none.
- **Trust without action.** Verifying that comments exist but not replying. The golden hour is for engagement, not observation.
- **Growth without persistence.** Learning that something worked but not saving it. If you don't patch the skill, the next session starts from zero.
- **Forgetting MH resources.** Every post touching the origin story MUST include Pieta + Samaritans. Non-negotiable.
- **Skipping Joy's parallel execution.** When Beer says "the whole set" / "pro all" — execute every platform simultaneously, not sequentially.

## Verification

After running the full pipeline, confirm:
1. Creative brief exists ✅
2. Plan with format + tools exists ✅
3. Final artifact (image + copy) is complete ✅
4. Content is live on ALL platforms ✅
5. Posts verified and comments replied ✅
6. Lessons saved to skill/memory ✅
