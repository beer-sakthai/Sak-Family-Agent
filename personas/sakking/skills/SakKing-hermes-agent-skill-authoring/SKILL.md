---
name: SakKing-hermes-agent-skill-authoring
version: 1.0.0
description: Author in-repo SKILL.md files for SakKing with valid frontmatter, 10-factor schema rubric, and size constraints.
category: productivity
tags:
- agent
- authoring
- cli
- runner
- skill
---

# SakKing Skill Authoring Guidelines (In-Repo)

## Overview

Skills provide reusable procedural domain knowledge for the Sak Family agents. In this repository, skills are maintained as canonical Markdown documents with YAML frontmatter following the 10-factor schema rubric.

---

## 1. Where Skills Live

| Type | Path | Purpose |
|:---|:---|:---|
| **SakKing Overlay** | `personas/sakking/skills/<Skill-Name>/SKILL.md` | Persona-specific runner and engineering skills |
| **Shared Household** | `personas/shared/skills/<Skill-Name>/SKILL.md` | Cross-persona universal workflows (e.g., `Sak-auto-cycle-loop`) |

---

## 2. Required Frontmatter Specification

Every `SKILL.md` must start on line 1 with `---` and contain:

```yaml
---
name: SakKing-<kebab-case-topic>
version: 1.0.0
description: Actionable, concise summary of what this skill does and when to invoke it (<= 1024 characters).
category: <coding|productivity|devops|data|ai|security>
tags:
- runner
- cli
- <relevant-tag>
---
```

### Invariants:
1. **Name Prefix**: Must match `SakKing-` (or `Sak-` for shared skills).
2. **Size Constraint**: Total file size must remain $\le 15$ KB.
3. **No Legacy Metadata**: Do not use `metadata.hermes` or obsolete nesting blocks.
4. **Body Content**: Must contain substantial, actionable Markdown instructions (not empty stubs).

---

## 3. Skill Validation & Composition Commands

```bash
# Validate SakKing skill schema and 10-factor rubric:
sak eval skills --persona sakking --detailed

# Verify skill tree composition across shared + overlay:
python3 scripts/compose_persona.py sakking --out /tmp/sakking_composed --check personas/sakking/skills

# Run full persona test suite including skill invariants:
uv run pytest tests/test_skills_organization_parity.py -q
```
