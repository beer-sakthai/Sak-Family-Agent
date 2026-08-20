# Beer's Brief Request Patterns — Reference

Captured from session 2026-07-07.

## The Pattern

Beer's inbound messages are typically 3–6 words, fragmented, missing subjects/verbs,
and assume you share full context of what was recently discussed.

## Live Example: "Pictures 12 pic you post all?"

### What happened
- Beer asked this on July 7, 2026
- Agent spent **9 tool calls** searching session history, cron jobs, skills, files, and supermemory before responding
- Response offered 3 clarification options
- Beer replied with a skill-review instruction instead of answering the question

### What should have happened
- 1–2 session_search calls max (check yesterday's launch-blitz session)
- Recognize: yesterday's 12-hr blitz discussed 6 posts, Beer might now want 12
- Or: "Did you post all 12?" is a yes/no — answer based on what was actually posted
- If truly unclear: 1 clarification message with max 3 compact options
- Total tool calls: 2–3, not 9

## Live Example: "plan?" (July 7, 2026)

### What happened
- Beer opened with just "plan?"
- Agent responded with a status update + 4 options
- Beer replied: "im pro the whole set for we plan don't wait keep do do do thbf that"
  - Meaning: "I approve ALL options. Execute everything simultaneously. Don't ask which first."

### What this teaches
- "plan?" = state-of-play report, not a planning session
- "pro whole set" / "the whole set" / "do all" = execute every identified task in parallel
- Beer's strongest signal: he does not want prioritization questions — he wants everything done

## Root Cause

The SOUL.md and user profile already document Beer's terse style, but the agent
did not apply those preferences before spending tool calls — it searched for
external context instead of first checking its own stored knowledge of how Beer
communicates.

## Correction Applied

The `saksit-social-media-posting-workflows` SKILL.md now has a "Beer's Brief Request
Decoder" section as the first content section, encoding the correct response pattern
so future sessions find it immediately when loaded.
