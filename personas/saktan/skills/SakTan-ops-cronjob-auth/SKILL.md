---
name: SakTan-ops-cronjob-auth
version: 1.1.0
description: Handle authentication, authorization, and credential safety for scheduled jobs.
category: operations
tags:
- auth
- automation
- cronjob
- daily-ops
- ops
---

# Scheduled Job Auth & Credential Safety

## Purpose

Handle authentication, authorization, and credential safety for scheduled automation.
Prevent silent failures from missing or invalid credentials, and ensure scheduled jobs
operate safely without ever leaking secrets.

## When to Use

- A scheduled job reports `401 Unauthorized`, `403 Forbidden`, or missing token errors.
- Configuring environment variables for a newly provisioned systemd timer or GitHub Action.
- Auditing scheduled jobs to ensure compliance with Security Rule 1 (Secrets Stay Secret).

## Credential Safety Invariants

1. **Secrets Stay Secret**: Never hardcode API keys, tokens, or passwords in prompts, SKILL.md files, timer definitions, or workflow files.
2. **Never Expose Raw Credentials**: Sanitize and redact all outputs before logging to disk, writing to SQLite memory, or sending Telegram messages.
3. **Validate Presence Hermetically**: Check that environment variables exist and are non-empty without printing their values:
   ```bash
   # Test presence only:
   [ -n "$HF_TOKEN" ] && echo "HF_TOKEN: configured" || echo "HF_TOKEN: missing"
   ```
4. **Missing Secrets**: Log the missing variable name only; alert Beer with the exact variable needed without auto-injecting placeholder secrets.

## Safe Auth Patterns

### Pattern A: Environment-Scoped Provisioning (Preferred)
Scheduled tasks run under `uv run` inherit credentials from their parent process, `.env` file, or systemd user environment:
```ini
# In ~/.config/systemd/user/sakthai-<job>.service
[Service]
EnvironmentFile=%h/.sakthai/.env
ExecStart=/usr/local/bin/uv run sak run "<prompt>" --persona saktan
```

### Pattern B: Telegram Authorization & User ID Whitelist
Automated notifications must only send messages to authorized users configured in `TELEGRAM_ALLOWED_USER_IDS`:
```bash
# Verify allowed recipients are defined:
grep '^TELEGRAM_ALLOWED_USER_IDS=' ~/.sakthai/.env
```
Never dispatch messages to unverified chat IDs.

### Pattern C: Hugging Face Read/Write Scope Verification
When an automated task requires Hugging Face Hub access:
```bash
# Verify token validity without echoing the token:
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $HF_TOKEN" \
  https://huggingface.co/api/whoami-v2
```
`200` = valid; `401` = invalid/expired; `403` = insufficient permissions.

## Diagnosis Flow for Scheduled Failures

1. **Identify the Service**: HF Hub, Telegram gateway, Microsoft Graph / 365, or local Ollama.
2. **Check Variable Presence**: Inspect `.env` or systemd environment for the required variable name.
3. **Verify Local Endpoints**: For Ollama ($0 spend), ensure `http://127.0.0.1:11434` responds.
4. **Notify Beer**: If a secret is missing or revoked, provide a concise notification stating the affected job and required variable name.

## Common Fixes

| Symptom | Cause | Remedy |
|---------|-------|--------|
| `401 Unauthorized` | Token expired or invalid | Refresh token in `.env` |
| `403 Forbidden` | Insufficient token scope | Verify token role / permissions |
| `Connection refused` | Local daemon offline | Start Ollama service (`systemctl start ollama`) |
| Secret leaked in log | Unredacted tool output | Scrub log immediately, rotate compromised token |
