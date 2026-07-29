---
name: SakSee-hermes-agent-skill-authoring
description: Author SKILL.md files with proper frontmatter and structure.
category: software-development
tags: [skill, authoring, documentation]
---

# Hermes Agent Skill Authoring

Author well-structured SKILL.md files.

## Frontmatter Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | ✅ | Lowercase, hyphens |
| `description` | ✅ | One-line summary |
| `category` | ✅ | Domain category |
| `tags` | ❌ | Search keywords |
| `prerequisites` | ❌ | Required tools/packages |

## Body Structure

```markdown
# Title

## When to Use

## Steps

### 1. Step Name

```code

### 2. ...

## Pitfalls

### Pitfall 1
```

## Principles

- Write for reuse
- Include exact commands
- Note all known pitfalls
- Keep it actionable
