---
name: SakJules-command-development
version: 1.1.0
description: Design, structure, and author reusable slash commands and interactive prompts for agent automation workflows.
category: devops
tags:
- automation
- command
- development
---

# Command Development Protocol

Standards for authoring, configuring, and maintaining reusable slash commands (`.claude/commands/` or `.claude/skills/<name>/SKILL.md`).

## 1. Core Principles
- **Instructions for Agent, Not User**: Commands must be written as direct imperatives for the agent loop (e.g. "Audit target repository for SQL injection vulnerabilities and return unified diff"), not as explanatory dialogue directed to the user.
- **Single Source of Truth**: Modern commands standardize on `SKILL.md` format with YAML frontmatter.
- **Dynamic Context Injection**: Leverage `$ARGUMENTS`, file references (`@file`), and Bash execution (`!command`) to ingest dynamic session state cleanly.

## 2. Command Frontmatter Specification
```yaml
---
name: command-name
description: Purpose of command shown in CLI autocomplete
argument-schema:
  type: object
  properties:
    target: { type: string }
---
```

## 3. Best Practices & Invariants
- **Fail Gracefully**: Verify prerequisite environment variables and CLI tools before attempting execution.
- **Narrow Output Contract**: Require structured outputs (JSON or bulleted summaries) for predictable downstream parsing.
- **Zero Hallucination**: Require explicit verification commands before claiming status or readiness.

## 4. References & Guides
- **Frontmatter Reference**: [Frontmatter Schema & Options](references/frontmatter-reference.md)
- **Interactive Workflows**: [Interactive Prompts & AskUser](references/interactive-commands.md)
- **Advanced Patterns**: [Complex Multi-Step Workflows](references/advanced-workflows.md)
- **Testing & QA**: [Command Validation Strategies](references/testing-strategies.md)
- **Plugin Features**: [Plugin Features Reference](references/plugin-features-reference.md)
- **Documentation**: [Command Documentation Patterns](references/documentation-patterns.md)
- **Marketplace Rules**: [Distribution Guidelines](references/marketplace-considerations.md)
- **Examples**: [Simple Commands](examples/simple-commands.md) | [Plugin Commands](examples/plugin-commands.md)
