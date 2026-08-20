---
name: SakSit-api-troubleshoot-solutions
category: core
description: Diagnose blocked APIs and find working solutions.
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Diagnostic, API, Credentials, Troubleshooting, Solutions]
---

# API Troubleshoot & Solutions

Systematically diagnose a blocked API or service: find credentials, test every
path, identify the real blocker, and present all working solutions. This skill
does NOT fix the issue — it maps the solution space so you and the user can
pick the fastest unblock path.

## When to Use

- An API/tool returns "quota exhausted", "rate limited", or "unauthorized".
- The user says "check," "test," "evaluate," "diagnose," or "full report."
- A service works for some paths but not the one you need.
- The user asked for something and you hit a paywall/block/limit.
- You need to find credentials in the environment.
- The user is frustrated ("find the way", "make a choice", "get it for me").

## Prerequisites

- Access to the environment (`terminal`, `env`, file system)
- `auth.json` in the Hermes profile directory (credential metadata)
- `.env` files in the profile or repo root (plaintext keys)
- If the service uses a plugin/tool, check its config
- `memory` and `supermemory` for prior credential knowledge

## Quick Reference

| Step | What | Tools |
|------|------|-------|
| 1 | Scan env vars | `terminal(env \| grep API_KEY)` |
| 2 | Read auth.json | `terminal("cat auth.json \| python3 -c ...")` |
| 3 | Find .env files | `search_files(pattern="*.env", path=".")` |
| 4 | Test each key | `terminal(curl or Python SDK)` |
| 5 | Report full table | Summarize path → status → blocker → fix |

## Procedure

### 1. Scan the environment for credentials

Check env vars first (fastest path):

```text
terminal(command="env | grep -i 'key\\|token\\|secret\\|api'")
```

Check the Hermes credential store:

```text
terminal(command="python3 -c \"import json; d=json.load(open('/opt/data/profiles/saksit/auth.json')); [print(f'{p}: {c[0].get(\\\"source\\\",\\\"?\\\")} status={c[0].get(\\\"last_status\\\",\\\"?\\\")}') for p,cl in d.get('credential_pool',{}).items() if cl for c in [cl if isinstance(cl,list) else [cl]]]\"")
```

Find all `.env` files:

```text
search_files(pattern=".env*", path="/opt/data", target="files")
```

Read the keys from the active profile's `.env`:

```text
terminal(command="grep -E 'API_KEY|TOKEN|SECRET' /opt/data/profiles/saksit/.env")
```

### 2. Test the primary path

Use the intended tool first and capture the exact error:

```text
# If image generation:
image_generate(prompt="test", aspect_ratio="square")
# If Composio MCP:
terminal(command="curl -s -X POST 'https://connect.composio.dev/mcp' ...")
# If direct API:
terminal(command="curl -s 'https://api.example.com/endpoint' -H 'Authorization: Bearer $KEY'")
```

### 3. Map all alternative paths

For each credential found, identify every possible route:

| Source | How to call | What it needs |
|--------|-------------|--------------|
| GOOGLE_API_KEY | Python `google-genai` SDK | Quota / billing |
| OPENROUTER_API_KEY | OpenRouter REST API | Credits balance |
| MCP_COMPOSIO_API_KEY | Composio MCP via curl | Enhanced Controls toggle |
| FAL_KEY | image_generate tool | Key must exist in env |
| HF_TOKEN | HF Inference API | Token must be valid |

Test each path systematically:

```text
terminal(command="export KEY=actual_value; python3 -c \"... try API call ...\"")
```

### 4. Identify the real blocker

Categorize every error into one of:

| Error Type | Meaning | Fix |
|-----------|---------|-----|
| **401 / 403** | Auth bad or forbidden | Wrong key, expired token, IP block |
| **429 / RESOURCE_EXHAUSTED** | Quota hit | Wait for reset, add billing, or switch path |
| **Enhanced Controls** | Composio session setting | Toggle OFF at dashboard.composio.dev |
| **402** | Insufficient credits | Add funds (OpenRouter, FAL) |
| **404** | Not found / wrong endpoint | Check URL, model name, API version |
| **Connection refused / DNS** | Network blocked | Different env or proxy |

### 5. Report in a structured table

Present every path with: path name, status (✅/⚠️/❌), what it needs, and the
specific fix. Include exact key prefixes and lengths (not full keys). End with
the three fastest unblocks ranked by effort.

### 6. Deliver a working fallback (if possible)

If all AI/API paths are blocked, check for programmatic fallbacks:

- **Pillow** (Python imaging library) — draw images manually
- **Template-based** — compose from existing assets
- **Text-only** — skip the asset and deliver what can be delivered

## Pitfalls

- **Keys in `.env` may be masked in terminal output.** The env var value itself
  may show as truncated (`sk-bri...Nprb`). Read `.env` directly with `grep` or
  `cat` to get the full plaintext value.
- **auth.json uses sealed `secret_fingerprint`** — the actual key is hashed and
  stored in Hermes' encrypted secret store, not readable directly. Get the key
  from `.env` files instead.
- **Free tier quotas reset daily** (usually midnight PST). If all models show
  429 RESOURCE_EXHAUSTED, wait a day or add billing.
- **"Enhanced Controls" is a Composio session setting** that requires the user
  to toggle it OFF at dashboard.composio.dev/org/connect/settings. There is no
  API to toggle it programmatically.
- **OpenRouter credits != tokens.** 82 tokens of credit may mean $0.000082 —
  insufficient for image generation (~8192 output tokens needed).
- **Don't stop at one failure.** If path A is blocked, test paths B, C, D.
  Report what DOES work, not just what doesn't.
- **Don't expose full keys in chat output.** Show prefix + length only
  (e.g. `sk-or-...168a`).
- **When user is frustrated "find the way", "make a choice", "get it for me" — don't present ranked options and ask for a pick.** Execute the fastest unblock path immediately. Beer's style: he wants action, not analysis. If path A works and needs a toggle, toggle it. If path B needs a free API key, find it. Default to doing over discussing.
- **When asked "can X model do Y" — don't answer from general knowledge.** Check the actual API or model card first. For Hugging Face models: query the API for `pipeline_tag`, `config.json`, and `README.md` in the same turn. For Gemini models: list available models via `GET /v1beta/models`. Beer's exact correction: "Check in hugging face omg check first."

## Verification

The diagnostic is complete when you can answer all four questions:

```text
1. What credentials exist?     (list every key with prefix + length)
2. What paths are available?   (list every API/SDK/CLI route)
3. What is blocking each path? (specific error for each)
4. What is the fastest fix?    (ranked by user effort — 1 click > sign in > add billing > wait)
```
