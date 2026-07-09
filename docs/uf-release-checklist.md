# UF Release Checklist

Use before every production cut to `main` or a published HF artifact.

## Pre-flight
- [ ] `git status` clean (no untracked `.env` or secrets)
- [ ] `git pull --rebase` latest `main`
- [ ] `pytest tests/ -q -m "not integration"` green
- [ ] `uv run ruff check personas/sakthai/sakthai tests` green
- [ ] `uv run ruff format --check personas/sakthai/sakthai tests` green
- [ ] `uv run mypy personas/sakthai/sakthai` green
- [ ] `uv run bandit -c pyproject.toml -r personas/sakthai/sakthai` green

## Secret / credential check
- [ ] `.env` is gitignored
- [ ] `git diff --cached --stat` shows no `.env` file
- [ ] No raw API keys, tokens, or passwords in source or committed config

## Version bump
- [ ] `pyproject.toml` version updated
- [ ] `CHANGELOG.md` updated (or `docs/releases/` note added)

## Tag and release
- [ ] `git tag vX.Y.Z && git push origin vX.Y.Z`
- [ ] GitHub Release note added (summary + migration notes)

## Post-release verification
- [ ] `sakthai doctor` runs clean on a fresh env
- [ ] `hermes mcp test composio` confirms HF connection end-to-end
- [ ] API surface (`/api/stages`, `/api/ecosystem`) responds without exposing secrets

## Rollback
- If something breaks: revert the tag, do not delete history; create a hotfix branch and re-cut.
