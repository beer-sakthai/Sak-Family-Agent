# GitHub API Research Pattern

Use when researching open-source projects (their docs, SECURITY.md, architecture, config) via terminal curl.

## Two Endpoints

| Data | URL Pattern | Notes |
|------|-------------|-------|
| Repo metadata | `https://api.github.com/repos/{owner}/{repo}` | Stars, topics, description, license |
| File contents | `https://api.github.com/repos/{owner}/{repo}/contents/{path}` | Returns JSON with `download_url` for files, `type: "dir"` for directories |
| Raw file | `https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}` | Direct file download, no JSON wrapper |
| Search repos | `https://api.github.com/search/repositories?q={query}` | Supports filtering by topic, stars, etc. |
| Directory listing | `https://api.github.com/repos/{owner}/{repo}/contents/` | Lists all files/dirs at root |
| Docs directory | `https://api.github.com/repos/{owner}/{repo}/contents/docs` | Lists all doc files |

## Example Workflow

```bash
# 1. Get repo info
curl -sL "https://api.github.com/repos/openclaw/openclaw" \
  -H "Accept: application/vnd.github.v3+json" \
  -o /tmp/repo.json

# 2. List docs directory
curl -sL "https://api.github.com/repos/openclaw/openclaw/contents/docs" \
  -H "Accept: application/vnd.github.v3+json" \
  -o /tmp/docs.json

# 3. Read a specific file directly
curl -sL "https://raw.githubusercontent.com/openclaw/openclaw/main/SECURITY.md" \
  -o /tmp/security.md
```

## Headers

- Always set `Accept: application/vnd.github.v3+json` for API calls
- Set `User-Agent: HermesBot` (GitHub requires a user-agent)
- No auth needed for public repos (rate limit: 60 req/hr unauthenticated)
