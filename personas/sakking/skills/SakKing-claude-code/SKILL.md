---
name: SakKing-claude-code
version: 1.0.0
description: Delegate autonomous coding, PR implementation, and refactoring tasks to Claude Code CLI.
category: coding
tags:
- claude
- cli
- code
- runner
- tdd
---

# SakKing Claude Code Delegation Protocol

## Overview

Delegates autonomous coding, debugging, and multi-turn refactoring tasks to Claude Code CLI (`@anthropic-ai/claude-code`) from SakKing's runner environment.

Operated by **SakKing** (`@sakking_agent_bot`), Deputy 1 and General Assistant/Runner of the House of Sak.

---

## 1. Operating Rules & Delegation Constraints

| Guardrail | Constraint |
|:---|:---|
| **Preferred Mode** | Non-interactive Print Mode (`-p`) with `--allowedTools` whitelist. |
| **Loop Bounding** | Always set `--max-turns <n>` (typically $\le 10$) to prevent runaway execution. |
| **Spend Cap** | Enforce `--max-budget-usd` or $0.00 local execution policy. |
| **Tool Whitelist** | Restrict tools strictly to required capabilities (`Read,Edit,Bash(git *)`). |
| **Interactive REPL** | Require `tmux` sessions for multi-turn sessions; automate workspace trust dialogs. |

---

## 2. Core Execution Patterns

### Pattern A: Automated One-Shot Coding Task (Print Mode)
```bash
claude -p "Refactor database query logic in personas/sakthai/memory/store.py" \
  --output-format json \
  --allowedTools "Read,Edit" \
  --max-turns 10 \
  --workdir /path/to/project
```

### Pattern B: Piped Code Review / Analysis
```bash
git diff HEAD~1 | claude -p "Review these changes for regression risks" --max-turns 1
```

### Pattern C: Structured JSON Output with Schema
```bash
claude -p "Extract exported functions in src/" \
  --output-format json \
  --json-schema '{"type":"object","properties":{"functions":{"type":"array"}}}' \
  --max-turns 5
```

---

## 3. Reference Documents

For comprehensive flag tables, tmux REPL scripts, dialog handling, and subagent schemas:
- [Claude Code CLI & Tmux Integration Guide](./references/cli-and-tmux-guide.md)
