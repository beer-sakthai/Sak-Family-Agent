# SakThai-Agent v2 — User Guide

## Install

```bash
git clone <repo-url>
cd sakthai-agent-v2
cp .env.example .env
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

Required env in `.env`:
- `ANTHROPIC_API_KEY`

Optional:
- `OPENAI_API_KEY` / `OPENAI_API_BASE`
- `GOOGLE_API_KEY`
- `TELEGRAM_BOT_TOKEN` / `TELEGRAM_CHAT_ID`
- `HF_TOKEN`
- `COMPOSIO_API_KEY`

## Start the API server

```bash
python scripts/serve_api.py
```

Then open:
- Dashboard: http://localhost:3002/
- API stages: http://localhost:3002/api/stages
- API ecosystem: http://localhost:3002/api/ecosystem

## Run the agent

```bash
sakthai doctor
sakthai setup
sakthai run "Hello"
```

## Memory

```bash
sakthai memory show
sakthai memory stats
sakthai memory export backup.jsonl
```

## Troubleshooting

**Port 3002 already in use**
Kill the old server or pick another port in `scripts/serve_api.py`.

**Memory store locked**
Close other SakThai processes and retry.

**API returns demo fallback**
Memory DB is empty or unreadable — factors/observations will show zeros; agent logs will show the source.

**TTS**
The optional Edge TTS helper should be invoked only when it adds value; do not force voice on every reply.

## Support

- Repo issues: github.com/<org>/sakthai-agent-v2
- Security policy: `SECURITY.md`
