# CI Diagnosis Methodology

Session: 2026-07-25 — Lessons learned from debugging CI status.

## The Mistake

When Beer asked "It's green?" the commit status showed "pending". 
Assumed it was "just a delay" without reading the actual checks.

## The Fix — Use check-runs API, not commit status

```bash
# DON'T — this can show "pending" even when CI is running
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/<SHA>/status"

# DO — this shows every check with exact status
curl -sL "https://api.github.com/repos/beer-sakthai/Sak-Family-Agent/commits/<SHA>/check-runs"
```

The check-runs API returns per-check details:
- `status`: `queued`, `in_progress`, `completed`
- `conclusion`: `success`, `failure`, `null` (while running)

## The Correct Sequence

1. Query check-runs API for latest commit
2. Count completed vs in-progress
3. If any are `failure`, find the failing step and read its log
4. Only then apply a fix

## Token Extraction

The GitHub token in `.git-credentials` uses `x-access-token` format:

```
https://x-access-token:github_pat_XXXX@github.com
```

Extract with:
```bash
GH_TOKEN=$(cat ~/.git-credentials | grep -oP '(?<=x-access-token:)[^@]+(?=@github\.com)')
```
