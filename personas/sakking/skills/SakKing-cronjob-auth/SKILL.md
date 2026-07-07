---
name: SakKing-cronjob-auth
category: hermes
description: Handle authentication, authorization, and credential safety for Hermes
  cron jobs
version: 1.0.0
platforms:
- linux
- macos
metadata:
  sakthai:
    tags:
    - hermes
    related_skills: []
    source: hermes:cronjob-auth
---

# Cronjob Auth

## Purpose

Handle authentication, authorization, and credential safety for Hermes cron jobs. Prevent silent failures from missing/invalid secrets, and give cron jobs a safe path to act on protected resources without exposing credentials.

## When to use

Load this skill when:
- A cron job logs `credentials`, `credentials not found`, `api key`, `auth`, `token`, `unauthorized`, `403`, or `401`
- A job needs to call an external API that requires a key/token
- You want to add auth to a new cron job safely
- User asks about cron security, credentials, or auth

## Credential rules

1. **Never hardcode secrets in prompts, SKILL.md, or cron prompts.**
2. **Never expose raw credentials in cron output or Telegram delivery.**
3. **Always read from `~/.hermes/.env` via the `env` tool or `grep` (redacted).**
4. **If a credential is missing:**
   - Log the missing var name (not the value)
   - Notify Beer with the exact env var needed
   - Do NOT auto-generate or auto-inject secrets

## Safe auth patterns for cron jobs

### Pattern A: Env-based (preferred)
Cron jobs that need API keys should read them from the Hermes env:
```bash
grep '^ANTHROPIC_API_KEY=' ~/.hermes/.env | cut -d= -f2- | head -c 8
```
Only check presence/length — never print the full value.

### Pattern B: HF token rotation
For Hugging Face operations:
```bash
grep '^HF_TOKEN=' ~/.hermes/.env | wc -c   # nonzero = present
```
If write scope is needed, verify the token includes `write` by checking the HF API:
```bash
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  https://huggingface.co/api/whoami-v2
```
`200` = valid; `401` = invalid/missing.

### Pattern C: Telegram delivery only when authorized
Cron jobs delivering to Telegram must target a verified chat ID from `~/.hermes/.env`:
```bash
grep '^TELEGRAM_ALLOWED_USERS=' ~/.hermes/.env
```
Never deliver to a chat ID not in this list.

### Pattern D: Web auth headers for Composio/MCP
If a cron calls Composio tools, the API key must be present:
```bash
grep '^COMPOSIO_API_KEY=' ~/.hermes/.env | wc -c
```
Missing = notify Beer; do not run the MCP tool without it.

## Diagnosis flow

When a cron reports auth failure:
1. **Identify the service** (HF, Telegram, Composio, OpenAI, etc.)
2. **Check the env var** exists in `~/.hermes/.env`
3. **Check the var is non-empty** (not just defined but blank)
4. **Test the credential** with a minimal API call (HEAD/WHOAMI)
5. **If invalid:** notify Beer with service + var name + test result
6. **If missing:** notify Beer with exact var name to set
7. **If valid but still failing:** check rate limits, IP allowlists, or token expiry

## Common fixes

| Symptom | Fix |
|---------|-----|
| `401 Unauthorized` | Token missing/expired — check env, re-auth if needed |
| `403 Forbidden` | Token lacks required scope (e.g., HF write) — re-issue token |
| `credentials not found` | Env var absent from `.env` — add it |
| `no usable Supermemory baseline` | Add `supermemory` + `memory` to `enabled_toolsets` |
| `tool not available` | Cron sandbox missing the tool — add to `enabled_toolsets` |

## Notification template

When notifying Beer about a credential issue:
```
Cron auth issue: <service>
Job: <job_name> (<job_id>)
Missing/invalid: <ENV_VAR>
Action needed: <what to set or re-authenticate>
```

## Constraints

- Do NOT store credentials in `~/.hermes/cron/output/` or skill files
- Do NOT modify another user’s `.env` without explicit permission
- Do NOT retry failed auth in a tight loop — backoff 5 minutes
- Do NOT expose partial keys (first 8 chars is OK for presence check; never more)
