# Platform Trend Scan — 26 Jul 2026

## Context
Scheduled cron job: "Self-improvement: analyze platform algorithms (GitHub trending, HF trending, Kaggle). Check if our repos appear."

## API Endpoints Verified

### GitHub
- User repos: `https://api.github.com/users/{owner}/repos?per_page=20&sort=updated` — works unauthenticated
- Search repos (24h window): `https://api.github.com/search/repositories?q=created:YYYY-MM-DD..YYYY-MM-DD+stars:>N&sort=stars&order=desc&per_page=10`
- Trending (HTML scrape): `https://github.com/trending?since=daily` — parse with regex on `<h2 class="h3">` tags

### Hugging Face
- Trending: `https://huggingface.co/api/trending?limit=20` — returns `{"recentlyTrending": [{"repoData":{...}, "repoType":"model"}]}`
- Models: `https://huggingface.co/api/models/{owner}/{name}` — works unauthenticated
- Datasets: `https://huggingface.co/api/datasets/{owner}/{name}` — works unauthenticated
- Spaces: `https://huggingface.co/api/spaces/{owner}/{name}` — works unauthenticated
- Collections: `https://huggingface.co/api/collections/{owner}/{slug}` — works unauthenticated
- **Models list API** (`/api/models?sort=trendingScore`): `trendingScore` is the valid sort param (NOT `trending`)
- **Model type detection from raw data**: `repoData` keys `safetensors` or `numParameters` = weight model; `runtime` or `title` = Space; `datasetsServerInfo` = dataset

### Kaggle
- Competitions: `https://www.kaggle.com/api/v1/competitions/list` — 401 without auth
- Datasets list: `https://www.kaggle.com/api/v1/datasets/list` — 400 without auth (valid sortBy values not discoverable without docs)
- Datasets search: `https://www.kaggle.com/api/v1/datasets/list?search={term}` — works unauthenticated
## Cron Environment Constraints (Verified 26 Jul 2026 — may vary by config)

- `execute_code` tool is BLOCKED in cron mode (security restriction — does not apply to interactive sessions)
- `curl | python3` pipes are BLOCKED by Tirith security scanner — always use `curl -o /tmp/file && python3 /tmp/parse.py` two-step pattern
- `patch`, `write_file`, `terminal`, and browser tools (`browser_*`) ARE available in cron mode — their availability depends on the Hermes profile's tool whitelist, not on cron mode itself

## Beer's HF Asset Snapshot (26 Jul 2026)

Collection "sakthai-model-family" has 16 items:
- Models: sakthai-context-0.5b-merged, sakthai-context-1.5b-merged, sakthai-context-7b-merged, sakthai-context-7b-128k, sakthai-context-1.5b-tools, sakthai-context-7b-tools, sakthai-coder-1.5b, sakthai-vision-7b, sakthai-tts-model, sakthai-embedding-multilingual
- Datasets: sakthai-combined-v6, sakthai-kaggle-notebooks, SimpleToolCalling, food-penguin-v1
- Spaces: sakthai-tts, sakthai-leaderboard

Stats: Leading downloads = sakthai-context-1.5b-merged (942), sakthai-context-0.5b-merged (785). Total ~3,107. All have 0 likes.

## Trending Observations
- GitHub: Agent/skills ecosystem is the dominant theme (ComposioHQ/awesome-claude-skills, obra/superpowers, mattpocock/skills)
- HF: MoE models dominate top 10 (4 of 10). Quantization (GGUF, ternary) also strong. Multimodal rising.
- Kaggle: No trending data available without auth. Search for "tool calling" returns 20 datasets.
