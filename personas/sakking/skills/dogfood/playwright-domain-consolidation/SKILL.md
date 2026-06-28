---
name: playwright-domain-consolidation
description: Group Playwright skills by domain instead of keeping one-offs scattered. Use when asked to consolidate, dedupe, or reorganize playwright skills into network, visual, performance, and security buckets. Also use when a domain check reports MISSING for a known domain group.
---

# Playwright Domain Consolidation

Reduce Playwright skill sprawl by organizing related skills into stable domain buckets.

## Fixed domain groups

Use exactly these names when creating or checking consolidated skills:

- playwright-network-testing
- playwright-visual-testing
- playwright-performance
- playwright-security-hardening

## When to use

- A cron check, Supermemory recall, or user request reports Playwright skills as MISSING.
- Playwright skill count is high and skills are duplicative by topic.
- Restoring a broken or incomplete Playwright skill tree after merges.

## Steps

1. List current playwright-related skills by path or name.
2. Identify which domain buckets exist and which are missing.
3. If a bucket exists but is empty or absent, recreate it:
   - create the skill directory
   - write SKILL.md with domain-specific guidance using existing knowledge from neighboring playwright skills
4. If related skills duplicate each other, merge content into the domain bucket and mark the old skills retired or absorbed if the skill layout supports it.
5. Verify presence on disk; report completion.

## Reporting format

MISSING: [list of missing domains]
CREATED: [list of newly created domain skills]
VERIFIED: [list of existing domain skills now confirmed on disk]
COMPLETED: true or false

## Notes

- Keep changes local to the skill tree unless the user asks to modify code or tests.
- Do not rename working domain buckets after creation; consistency matters for later cron checks.