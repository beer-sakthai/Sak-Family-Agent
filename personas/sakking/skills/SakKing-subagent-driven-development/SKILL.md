---
name: SakKing-subagent-driven-development
version: 1.0.0
description: Execute implementation plans by dispatching isolated implementer and reviewer subagents per task.
category: agent-runner
tags:
- cli
- development
- driven
- subagent
- runner
---

# SakKing Subagent-Driven Development Protocol

## Overview

Executes implementation plans through depth-bounded, isolated subagent dispatch. Dispatches a fresh implementer subagent per task, followed by spec compliance and code quality reviews, and concluding with a whole-branch synthesis.

Operated by **SakKing** (`@sakking_agent_bot`), Deputy 1 and General Assistant/Runner of the House of Sak.

---

## 1. Operating Rules & Core Principles

| Principle | Rule |
|:---|:---|
| **Context Isolation** | Never dump session history into subagents; construct minimal, targeted task prompts. |
| **Depth Bounding** | Enforce `DEFAULT_MAX_DELEGATION_DEPTH = 2`; prevent nested subagent runaway. |
| **Two-Stage Review** | Each task requires both a Spec Compliance review and a Code Quality check before sign-off. |
| **Continuous Execution** | Do not stop between independent tasks unless blocked by unresolvable ambiguity. |
| **Plan Synchronization** | Mark tasks `[ ]` $\to$ `[/]` $\to$ `[x] YYYY-MM-DD` in `PLAN.md` immediately. |

---

## 2. Dispatch Workflow

```
[Plan Task] ──► Dispatch Implementer Subagent (TDD + Targeted Files)
                     │
                     ▼
          Spec Compliance Review Subagent ──► Code Quality Review Subagent
                     │                                   │
                     ▼                                   ▼
             (Approved / Revisions)              (Ruff, Mypy, Tests)
                     │
                     ▼
          Mark Task Complete in PLAN.md ──► Advance to Next Task
```

1. **Craft Implementer Prompt**: Include exact task spec, target files, and test commands.
2. **Execute & Test**: Subagent writes tests, implements changes, and verifies exit code 0.
3. **Review**: Verify spec compliance and run quality checks (`ruff`, `mypy`, `pytest`).
4. **Final Whole-Branch Review**: Broad architectural audit before opening PR.

---

## 3. Reference Documents

For complete implementer, reviewer, and fixer prompt templates and ledger formats:
- [Subagent Workflow Templates & Prompts](./references/subagent-workflow-templates.md)
