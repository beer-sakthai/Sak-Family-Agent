# Skills Sync Duplication Issue

## Problem
The `cp -a ~/profiles/sakthai/skills/. .` step in cron jobs creates nested `skills/skills/` duplicates when the target git repo (`sakthai-skills-repo`) already has a `skills/` directory. This causes **ambiguous skill name** errors for any skill at the top level of `skills/` that also exists under `skills/skills/`.

## Affected skills
Currently only `environment-automation` is affected — it's an uncategorized top-level skill. Categorized skills (like `autonomous-ai-agents/hermes-agent`) don't collide because their paths differ.

## Root cause
The sync command copies the **contents** of `skills/` into the repo root. If the repo root already contains a `skills/` dir, then `skills/skills/` gets created:

```
cp -a ~/profiles/sakthai/skills/. .  # copies 'environment-automation/' into ./
                                    # which already has 'skills/' from prior sync
                                    # result: skills/skills/environment-automation/
```

## Fix
Switch the sync from `cp -a X/. .` to a targeted copy that skips the nested `skills/` dir, or use `rsync --exclude='skills/skills/'`:

```bash
cd /opt/data/sakthai-skills-repo
rsync -a --exclude='skills/skills/' ~/profiles/sakthai/skills/. .
# OR: remove the nested copy after cp
# rm -rf skills/skills/
```

## Prevention
Add a cleanup step after every git sync to remove the nested `skills/skills/` directory if it exists:

```bash
[ -d skills/skills ] && rm -rf skills/skills/
```
