# Composio GitHub Push — Content Archive Fallback

When `git push` fails with no local auth (common in agent environments), use
the Composio GitHub toolkit to commit delivery artifacts (diaries, content plans,
post records) to the House of Sak repo.

## Prerequisite

- Active Composio GitHub connection (`COMPOSIO_SEARCH_TOOLS`)
- Account resolves to the correct GitHub user (e.g. `beer-sakthai`)

## One-Shot File Commit

```json
{
  "tool_slug": "GITHUB_COMMIT_MULTIPLE_FILES",
  "arguments": {
    "owner": "beer-sakthai",
    "repo": "house-of-sak",
    "branch": "main",
    "message": "descriptive commit message",
    "author": {"name": "Agent Name", "email": "beernanthasit@gmail.com"},
    "upserts": [
      {
        "path": "diaries/saksit/2026-07-06.md",
        "content": "# Diary content as string...",
        "encoding": "utf-8"
      }
    ]
  }
}
```

## Known Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| 404 "not found" | Target branch doesn't exist | Add `base_branch: "main"` |
| 403 "forbidden" | No write perms | Verify the GitHub account owns or has write access to the repo |
| Content mismatch | Variable interpolation failed | `execute_code` resolves variables before the API call |
| Local repo out of sync | API creates new commit SHA | `git fetch origin && git reset --hard origin/main` |

## Verification

Do NOT trust the tool's success message alone. Always verify:

```bash
curl -s https://raw.githubusercontent.com/beer-sakthai/house-of-sak/main/diaries/saksit/2026-07-06.md | head -5
```

## When This Happens

After any content production cycle (post planning, posting, diary writing):
1. File saved locally at `/opt/data/house-of-sak/diaries/<agent-name>/`
2. Try `git commit && git push` in the local repo
3. If push fails (no auth) → use this Composio fallback
4. Sync local repo: `git fetch origin && git reset --hard origin/main`
