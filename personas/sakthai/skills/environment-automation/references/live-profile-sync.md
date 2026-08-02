# Live Profile ↔ GitHub Sync Convention

**Rule:** Always improve the **live profile first**, verify it works, then backup to GitHub. Never the reverse.

The live Hermes profile at `~/profiles/sakthai/skills/` is what the agent actually loads at runtime. The GitHub repo at `beer-sakthai/sakthai-skills` is a backup/organized copy.

## Direction

```
✅ CORRECT:  improve live → verify → commit GitHub
❌ WRONG:    improve GitHub → sync to live (invisible work)
```

When you improve something in the GitHub repo (new content, fixes, enrichment) and forget to sync back to the live profile, the agent never sees those improvements. The agent runs from `~/profiles/sakthai/skills/`, not from GitHub.

## Sync commands

### Live → GitHub (backup)
```bash
cp -a ~/profiles/sakthai/skills/. /opt/data/sakthai-skills-repo/skills/
cd /opt/data/sakthai-skills-repo
git add -A && git commit -m "sync skills $(date +%Y-%m-%d)" && git push
```

### GitHub → Live (restore)
```bash
cp -a /opt/data/sakthai-skills-repo/skills/. ~/profiles/sakthai/skills/
```

## Pitfalls

- The GitHub repo uses `SakThai-*` prefixed flat names; the live profile uses short categorized names (`mlops/hf-*`). Content copy works; directory renames do not.
- The HF Learn cron copies live → GitHub every tick. If you manually edit GitHub, the cron overwrites from live on the next tick.
- Always verify after sync: `skill_view(name="skill-name")` should load without errors.
