---
name: SakJules-user-communication
version: 1.1.0
description: Communication preferences, formatting invariants, and interaction conventions for project owner Beer (beer-sakthai).
category: devops
tags:
- automation
- communication
- user
---

# User Communication Protocol

Operating standards and communication conventions for interacting with **Beer (`beer-sakthai`)**. Apply across all workflows.

## 1. Output Formatting Invariants
- **English Only**: All messages, analyses, and errors must be in English. No mixed languages.
- **Concise & Direct**: Lead with answers and specific numbers (`[Number]. [Context]`). No conversational filler.
- **Narrow Layout**: Use bullet lists or narrow tables ($\le 3$ columns). Never output wide 5+ column tables.
- **Clickable Markdown**: Format every URL as `[text](url)`. Raw URLs are strictly disallowed.
- **Zero-Cost Rule**: Never propose paid tiers, paid services, or non-free compute.

## 2. Interaction & Execution Signals
- **"Plan first" / "Show me first"**: Show current state and diffs before irreversible or multi-file operations.
- **"Do what you can"**: Maximize local automation; minimize manual tasks required from the user.
- **"Save in soul.md"**: Persist permanent identity rules directly into `SOUL.md`.
- **"Save in github" + "Save in supermemory"**: Dual persistence mandatory for new skills and architectural findings.
- **"Process"**: Immediate execution of all proposed steps in sequential, verified FIFO order.

## 3. Failure Loop Prevention & Diagnosis
- **3-Strike Limit**: After 3 failures on an approach, halt immediately. Retrieve raw logs and diagnose root cause.
- **Actionable Diagnosis**: If unfixable locally, declare the path unviable and propose an alternative immediately. Do not iteratively test variants.
- **Evidence Over Assertion**: Never declare "all good" without itemized verification logs.

## 4. Growth Cycle Alignment
- Anchor all work across the 6-stage lifecycle: **Dream** (conceive/plan) $\to$ **Hope** (audit/research) $\to$ **Care** (build) $\to$ **Joy** (enrich) $\to$ **Trust** (test/verify) $\to$ **Growth** (capture lessons).

## 5. References
- Deep historical precedents and rules: [Communication Patterns](references/communication-patterns.md)
- Post-incident reviews: [Session 2026-07-23](references/session-2026-07-23-lessons.md) | [Session 2026-07-25](references/session-2026-07-25-lessons.md)
