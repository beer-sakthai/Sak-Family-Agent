---
name: SakJules-continuous-learning-loop
version: 1.1.0
description: Operational protocol for continuous background research, deduplicated insight extraction, and multi-tier knowledge persistence.
category: devops
tags:
- automation
- continuous
- learning
- loop
---

# Continuous Learning Loop Protocol

Standard procedure for recurring background research pipelines that evolve agent skills and durable memory without message fatigue.

## 1. Operating Invariants
- **Loop Closure**: Research that does not modify agent behavior, configuration, or documentation is noise. Every loop must write to durable storage.
- **Deduplication First**: Always inspect `LEARNING_JOURNAL.md` before initiating search queries. Novelty is mandatory.
- **Double-Dip Persistence**: Every validated learning must update both the audit log (`LEARNING_JOURNAL.md`) and the relevant operational artifact (`SKILL.md`, `SOUL.md`, or `references/`).
- **Silent Background Delivery**: Learning crons run with `deliver: local` to prevent user inbox spam.

## 2. Execution Flow
1. **Trigger**: Cron job wakes up on scheduled cadence ($\ge 30$ min interval).
2. **Deduplication Check**: Scan local journal for overlapping concepts.
3. **Retrieval**: Extract 1–2 high-signal, actionable insights from targeted documentation or search.
4. **Persist & Mutate**: Update target skill file and append structured entry to journal.
5. **Verify**: Ensure updated YAML/Markdown files validate cleanly.

## 3. References & Artifacts
- Detailed scheduling matrix, delivery modes, and persistence rules: [Learning Loop Rules](references/learning-loop-rules.md)
- Research patterns & fallback recipes: [DDG Lite Search](references/ddg-lite-search-fallback.md) | [GitHub API Research](references/github-api-research-pattern.md) | [Viral Frameworks](references/viral-content-frameworks-jul23.md)
