# Repository Reorganization — Root-Level Skill Cleanup

## Signal

When a monorepo (like Sak-Family-Agent) has root-level directories that duplicate content under `personas/<name>/skills/`. The AGENTS.md file defines the canonical structure — use it as the authority.

## Assessment Steps

1. **Read AGENTS.md** — The repo's own rules define expected structure. In Sak-Family-Agent: "there is no root-level `skills/`; Persona overlays and skills are under `personas/<name>/skills/`."
2. **Compare root vs personas** — Check if root skill dirs (mlops/, github/, research/, etc.) are duplicated under `personas/<name>/skills/`.
3. **Check git tracking** — Use `git ls-files mlops/SKILL.md` to confirm if the root-level files ARE tracked (not just local copies).
4. **Check .gitignore** — Some runtime files may be gitignored. Don't try to delete gitignored directories from tracking.

## Execution

```bash
# 1. Identify duplicates
ls -d */  # at root — note all skill dirs
curl -s "https://api.github.com/repos/org/repo/contents/personas/sakthai/skills" | python3 -c "..."

# 2. Verify they're tracked
git ls-files mlops/SKILL.md  # returns path if tracked

# 3. Remove from filesystem AND git
rm -rf mlops/ github/ research/  # etc.
git rm -r mlops/ github/ research/  # staged deletion

# 4. Commit with clear message
git commit -m "refactor: remove N duplicate root skill dirs (content exists under personas/)"

# 5. Push
git push
```

## Pitfalls

- **Do NOT use `--cached`** unless you want to untrack without deleting. Use plain `git rm -r`.
- **Check `.gitignore first`** — some dirs may be gitignored. `rm -rf` them from disk but `--cached` is wrong for non-tracked files.
- **Beware of `git add -A`** after rm — it will pick up `.hypothesis/`, `__pycache__/`, and other junk. Add these to `.gitignore` BEFORE committing:
  ```
  __pycache__/
  *.pyc
  .hypothesis/
  ```
- **CI will fail** if leftover dirs (like `skills/email/` with no SKILL.md) trigger validation tests. Run `pytest tests/` locally after cleanup.
- **Secret scans (gitleaks)** may fail if `.hypothesis/` files contain auto-generated constants that look like secrets. Best to gitignore them.
- **Verify on GitHub API** after push — CDN may cache old state. Check via `https://api.github.com/repos/org/repo/contents/` not the web UI.

## Results (2026-07-25)

Sak-Family-Agent: removed 30 root-level skill dirs (691 files, 220,245 lines). All content confirmed under `personas/sakthai/skills/`. CI passing.
