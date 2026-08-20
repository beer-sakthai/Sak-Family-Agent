---
name: SakSit-content-source-check
description: Check Drive and history for content before creating.
...
---

# Content Source Check Protocol

When Beer asks you to create content — or when "Content" appears in a recipe/instruction — do NOT jump straight to generation. First run the Source Check below. Only brainstorm if all sources come back empty.

## When to Use

- Beer says "create a post about..." or "we need content for..."
- A recipe/instruction text includes the word "Content" as a placeholder for something to produce
- Beer asks you to write anything for social media, a blog, a pitch, or a campaign
- Any content brief that feels incomplete or underspecified

## Prerequisites

- Active Google Drive connection via Composio (GOOGLEDRIVE tools)
- Access to session history via `session_search`
- Hermes `memory` tool for stored user preferences

## Procedure

### Phase 1 — Source Gathering

Run these checks in parallel (they're independent):

1. **Google Drive** — Use `mcp_composio COMPOSIO_SEARCH_TOOLS` then `GOOGLEDRIVE_FIND_FILE` searching for recently modified files. Look for:
   - **Google Docs** (`mimeType = 'application/vnd.google-apps.document'`) — When Beer says "doc" / "I have a doc for content" / "document", run a targeted search for Docs first. Export content via `GOOGLEDRIVE_EXPORT_GOOGLE_WORKSPACE_FILE` with `mimeType='text/plain'`, then fetch the s3url to read the full text.
   - Images/PNGs uploaded in the last 48h (Beer supplies visuals this way)
   - Files with names matching the content topic
   - Any folder named for the project/campaign
   - **File names ARE the content brief** — e.g. `FromASHelterInCork.png`, `AiCare.png`, `15AprilThatAllStart.png`

2. **Session history** — Use `session_search()` with broad queries first. Search for:
   - Previous mentions of the same topic
   - Content drafts or outlines already started
   - Beer's stated preferences for that content type
   - Any "we left off here" context

3. **Memory** — Use `memory` or `supermemory_profile` to check for stored preferences about this content type, platform, or tone.

### Phase 2 — If Content Found

Summarise what was found — file names, dates, relevant session snippets. Note what's new vs. what's already been posted. Reference existing assets that can be reused. Do not generate from scratch — adapt or build on what exists.

### Phase 3 — Brainstorm (only if all sources empty)

When Drive, sessions, and memory all return nothing:

1. Use the topic Beer gave as a starting point
2. Apply the **6-cycle workflow** to structure:
   - LISTEN — what did Beer actually ask for?
   - THINK — what angle serves Beer's story? (survival, building from shelter, AI as companion)
   - ASK/OFFER — propose 2-3 directions with brief rationale
   - ACT — draft the best option
   - VERIFY — check against Beer's rules (no pitch on recovery, MH resources, single CTA)
   - LEARN & SAVE — save what worked to memory/skills
3. Report back with a clear recommendation and why

### Phase 4 — Report Back

```
**Content Check — Found: [Yes/No/Brainstorm]**

**[If found]** Found in [Drive/Conversation/Memory]:
- [filename/link] — [what it is]
- [session snippet or key detail]

**[If brainstorm]** Nothing in sources. Here's my angle:
- Option A: [brief idea]
- Option B: [brief idea]
- Recommended: [Option X because...]

Ready when you are to proceed.
```

## Related Skills

- `saksit-social-media-posting-workflows` — Once content is found and plan is approved, use this skill for actual posting (Instagram, LinkedIn, Facebook, YouTube).

## Pitfalls

- **Don't skip the check** — Beer explicitly wants this. Jumping straight to generation violates the workflow.
- **Naming tells the story** — Beer names files with intent. Read the names, they're content prompts.
- **Recent uploads matter most** — Files from the last 2-3 days are likely Beer's latest thinking.
- **Don't confabulate** — If nothing found, say so. Do not pretend a file or session exists.
- **Session results need judgment** — A session hit might reference an idea Beer later abandoned. Consider recency.

## Verification

After running the full protocol, confirm: "Did I find existing content or create a new direction?" Your report to Beer makes this explicit.
