# Cron Job Safety Checklist

## Before every commit in a cron job

1. **YAML validation**: Run `grep "^version:" && grep "^author:"` on edited SKILL.md to confirm frontmatter is intact
2. **Git hygiene**: `git pull --rebase origin main` before push (avoid conflicts)
3. **Skip on no-change**: Only commit if content actually changed (`git diff --stat` to check)
4. **Push retry**: If push fails (conflict), retry ONCE with pull + push, then abort
5. **Tracker integrity**: After updating tracker JSON, validate it's parseable and has no duplicates

## Pitfalls avoided by this checklist

- ❌ Broken YAML from botched edits → ✅ grep validation catches it
- ❌ Push rejection from diverged history → ✅ rebase before push
- ❌ Empty/no-op commits bloating history → ✅ skip-if-no-change
- ❌ Tracker corruption → ✅ JSON validation
