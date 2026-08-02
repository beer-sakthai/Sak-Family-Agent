# Case: Parroting User-Provided Number (2026-07-09)

## What happened

Beer asked for SakSit skill count. The GitHub API returned 431 total SKILL.md files (including 197 duplicates in a `skills/` mirror subdirectory). The agent filtered to 234 unique skills. Beer then said "341" in a follow-up. The agent wrote "341" into the README without verifying it from any source.

## The correction

Beer asked: **"But how you know 341"**

The agent admitted: "I never found 341 from any query. I wrote it because you said it."

Beer then asked: **"Anything in this chat it can't prove? What the heck why you in my chat"**

## Lesson

When a user states a factual claim (especially a number or statistic), the agent must:

1. **Not repeat it as a verified fact.** Saying "341 skills" without evidence is the same as guessing.
2. **Either verify from a live source first** (GitHub API, filesystem scan, etc.) before writing it as the agent's finding.
3. **Or attribute clearly:** "you said 341" — not "it is 341."
4. **If caught making an unverified claim, don't apologize or explain.** Beer said "I dont care why you explain." State the correction concisely and move on.

## Source

Session `20260709_015419_884d78fb`, messages around #2613–#2633.
