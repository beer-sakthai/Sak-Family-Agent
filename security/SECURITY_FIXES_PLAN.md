# Security Fixes Plan — 2026-07

> **High-Priority:** Credential rotation + Web API authentication

This plan tracks the two blocking security fixes identified in the 2026-07 audit.
Work top-to-bottom. Check off with date when done.

---

## 🚨 Overview

*(Fix #2 — Web API Bearer Token Authentication in `personas/sakthai/sakthai/web/server.py`, `sakthai web setup` / `regen-token` CLI in `personas/sakthai/sakthai/cli/system.py`, and `tests/test_web_auth.py` — is complete and removed from this active plan. Master backlog is consolidated in [`/PLAN.md`](../PLAN.md).)*

| Fix | Priority | Effort | Owner | Status |
|-----|----------|--------|-------|--------|
| **Revoke Composio, Mistral and Kaggle credentials** | 🔴 HIGH | 10 min | Beer | [ ] |

---

## Fix #1: Revoke the Composio, Mistral and Kaggle Credentials

**Impact:** SECURITY (credentials in git history)
**Effort:** 10 minutes
**Owner:** Beer (credential access)

### Context

Three real credentials were committed, pushed, and later scrubbed from the
working tree. All three **remain in git history**:

| Credential | Committed in |
|---|---|
| Composio consumer key (`ck_…`) | `config/config.yaml`, `composio` MCP server `x-consumer-api-key` (2026-06-21) |
| Mistral API key (`H9hh…`) | `default/config.yaml`, provider `api_key` (2026-06-20) |
| Kaggle API token (`KGAT…`) | `scripts/family-status.sh`, `KAGGLE_API_TOKEN` (2026-07-25) |

An earlier version of this plan called the first two a "Stripe" key and a
"Twilio" token. The headers and config keys they sit under show they are
Composio and Mistral keys, so the Stripe and Twilio steps that were here would
not have found them. The Kaggle token was found on 2026-10-13 by the scheduled
full-history gitleaks scan.

### Why This is Important

- ✅ `.gitleaks.toml` no longer allowlists them, so gitleaks flags them if they are committed again
- ✅ `.gitleaksignore` keeps the daily full-history scan green, but only for these exact historical lines
- ❌ **But:** the values sit in git history and are still valid until revoked
- Scrubbing a secret from the tree, or baselining it, does **not** invalidate it

### What You Need To Do

**Step 1: Composio (2 min)** — in the Composio dashboard, revoke the consumer
key starting `ck_`. Generate a new one only if an MCP config still needs it,
and pass it via the environment, never the committed config.

**Step 2: Mistral (2 min)** — in the Mistral console's API keys page, delete the
key starting `H9hh`. Create a new one if the `mistral-code208` provider is still
used.

**Step 3: Kaggle (2 min)** — in Kaggle, Settings → API, expire the token
starting `KGAT`. Generate a new one only if the family status cron still needs
it, and keep it in `~/.kaggle/` or the environment.

**Step 4: Verify (2 min)** — each old key should now be rejected:

```bash
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer <OLD_MISTRAL_KEY>" \
  https://api.mistral.ai/v1/models          # expect 401
```

### Definition of Done

- [ ] Composio consumer key revoked
- [ ] Mistral API key deleted
- [ ] Kaggle API token expired
- [ ] Anything that used them re-tested with new keys from the environment
- [ ] Date recorded: **2026-__-__**

---

**Last updated:** 2026-11-13
**Status:** Fix #1 pending credential rotation by Beer (Fix #2 Web API auth completed)
