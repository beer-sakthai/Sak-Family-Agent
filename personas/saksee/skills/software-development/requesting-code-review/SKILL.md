---
name: requesting-code-review
description: Pre-commit review: security scan, quality gates, auto-fix.
category: software-development
tags: [review, security, quality]
---

# Code Review Request

Pre-commit review workflow.

## Before Requesting

1. **Self-review** — check your own diff
2. **Run checks** — lint, type check, tests
3. **Security scan** — secrets, injections, dependencies

## The Review

Checklist:
- [ ] Correctness — does it do what it's supposed to?
- [ ] Edge cases — empty states, errors, boundaries
- [ ] Security — no secrets, injection risks, over-permissioned
- [ ] Performance — N+1 queries, large payloads
- [ ] Style — consistent with codebase

## After Review

Apply fixes from review comments, re-run checks, merge.
