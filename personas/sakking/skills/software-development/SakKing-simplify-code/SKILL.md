---
name: SakKing-simplify-code
description: Parallel 3-agent cleanup of recent code changes.
category: software-development
tags: [refactoring, cleanup, code-quality]
---

# Simplify Code

Use when asked to clean up / refactor code.

## Process

1. Identify the code area to simplify
2. Spawn 3 parallel subagents via `delegate_task`:
   - Agent 1: Remove dead code / unused imports
   - Agent 2: Extract repeated logic into functions
   - Agent 3: Apply consistent naming and style
3. Review and merge the results
4. Test that nothing broke
