---
name: SakKing-cli-workflow-pitfalls
description: "CLI-specific pitfalls and workarounds for SakKing Agent workflows."
---

# SakKing CLI Workflow Pitfalls

This skill documents specific pitfalls and their workarounds when executing SakKing Agent workflows in a command-line interface (CLI) environment.

## Pitfall: CLI Agent Hand-off (send_message unavailable)

When operating in a CLI environment, direct inter-agent messaging (e.g., using a `send_message` tool to notify other agents) is not available.

**Workaround:**

To hand off a `PLAN.md` or other instructions to a target agent (e.g., SakJules), write the `PLAN.md` directly into the target agent's persona directory (e.g., `/opt/data/Sak-Family-Agent/personas/<agent_name>/PLAN.md`). After writing the file, explicitly notify the *user* that the plan has been placed for the target agent.

## Pitfall: Documentation Drift (Live Filesystem vs. Static Docs)

Static documentation (e.g., `CLAUDE.md`, `AGENTS.md`) may become outdated and not accurately reflect the live filesystem state. This can lead to incorrect assumptions about repository existence, structure, or content.

**Workaround:**

Always prioritize `search_files` and `terminal` output (e.g., `git status`, `ls -d`) when verifying the actual existence, Git status, or content of repositories and files. The live filesystem state takes precedence over potentially outdated documentation. Conduct a thorough environment audit using skills like `SakKing-environment-audit` to confirm the current state before proceeding with actions based on documentation.