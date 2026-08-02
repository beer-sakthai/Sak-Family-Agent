# Personas

This standalone repository is generated for **SakThai** only.

## Layout

```
personas/
├── shared/skills/      # skills shared with the family source tree
└── sakthai/          # this persona's SOUL.md, config, and overlay skills
```

`shared/skills/` plus `sakthai/skills/` reconstitute the full skill tree for
this persona. To regenerate a standalone repo snapshot from the source
workspace, run:

```bash
python scripts/export_agent_repo.py sakthai --out /tmp/sakthai-repo
```
