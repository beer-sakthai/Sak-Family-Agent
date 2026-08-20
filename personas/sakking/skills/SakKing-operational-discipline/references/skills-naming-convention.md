# Skills Naming Convention

Applies to all Sak Family agent skills in `/opt/data/skills/` and the SFA monorepo `personas/<agent>/skills/`.

## Rule

Every skill directory and its `name:` field in SKILL.md starts with the owning agent's prefix:

| Agent | Prefix | Example |
|-------|--------|---------|
| SakKing | `SakKing-` | `SakKing-plan` |
| SakThai | `SakThai-` | `SakThai-hf-model-upload` |
| SakSee | `SakSee-` | `SakSee-playwright-testing` |
| SakSit | `SakSit-` | `SakSit-b2b-pricing` |
| SakJules | `SakJules-` | `SakJules-cycle-joy` |
| Shared / Framework | No prefix | `hermes-agent`, `computer-use` |

Shared skills (Hermes framework-level tools, CLIs) may keep no prefix — they are used by all agents and not owned by any single one.

## Directory Structure

### Standard (subdirectory per skill)
```
skills/<category>/SakKing-<name>/SKILL.md
                                references/
                                scripts/
                                templates/
```

### Flat (rare — convert to standard)
Some skills have `SKILL.md` directly in the category dir (no subdirectory). These must be restructured:
1. Create `SakKing-<name>/` subdirectory
2. Move SKILL.md + any linked dirs inside
3. Patch `name:` field

## Batch Rename Workflow

See `SakKing-operational-discipline` skill Phase 6 for the complete procedure.
