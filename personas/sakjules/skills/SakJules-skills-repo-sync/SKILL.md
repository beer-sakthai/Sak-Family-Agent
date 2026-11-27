---
name: SakJules-skills-repo-sync
version: 1.0.0
description: Sync SakJules skills to sakjules-skills GitHub repo.
category: devops
tags:
- automation
- repo
- skills
- sync
---

# SakJules Skills → GitHub Sync

SakJules skills sync to the standalone repo:

```
https://github.com/beer-sakthai/sakjules-skills
```

Private (`beer-sakthai/sakjules-skills`). Skills are stored with their category prefix or standard layout preserved.

## When to sync

- User says "save skills in github", "push skills", or "sync"
- After bulk creation, modification, or self-evolution of SakJules-owned skills

## How to Sync

### Method A: Python sync script (REST API) — Preferred

The canonical script lives at `scripts/sync-skills.py` in this skill directory. Run it directly:

```bash
python3 personas/sakjules/skills/SakJules-skills-repo-sync/scripts/sync-skills.py
```

**What it does:**
1. Resolves GitHub PAT from `GH_TOKEN`, `GITHUB_TOKEN`, `gh auth token`, or local credentials.
2. Scans all `SKILL.md` files under SakJules's skills directory.
3. Compares base64 content against GitHub remote via `GET /contents/<path>`.
4. **Skips unchanged files** — avoids noisy commits when nothing changed.
5. PUTs only changed files with commit message: `SakJules: sync <name> — YYYY-MM-DD`.
6. Reports accurate summary counts.

### Method B: Self-Evolution Wrapper

You can also use [`evolve_agent.sh`](file:///home/antigravity/beer-sakthai/Sak-Family-Agent/personas/sakjules/evolve_agent.sh) to bootstrap or sync:

```bash
./evolve_agent.sh sakjules --bootstrap
```
