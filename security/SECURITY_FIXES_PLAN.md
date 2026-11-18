# Security Fixes Plan — 2026-07

> **High-Priority:** Credential rotation + Web API authentication

This plan tracks the two blocking security fixes identified in the 2026-07 audit.
Work top-to-bottom. Check off with date when done.

---

## 🚨 Overview

*(Fix #2 — Web API Bearer Token Authentication in `personas/sakthai/sakthai/web/server.py`, `sakthai web setup` / `regen-token` CLI in `personas/sakthai/sakthai/cli/system.py`, and `tests/test_web_auth.py` — is complete and removed from this active plan. Master backlog is consolidated in [`/PLAN.md`](../PLAN.md).)*

| Fix | Priority | Effort | Owner | Status |
|-----|----------|--------|-------|--------|
| **Revoke Composio, Mistral and Kaggle credentials** | 🔴 HIGH | 10 min | Beer | [x] 2026-11-18 |

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
- ✅ Automated hygiene test `tests/test_credential_hygiene.py` continuously guards against token leakage
- ❌ **Historical context:** the values sat in git history until revoked and rotated

### What Was Done & Verified

**Step 1: Composio** — in the Composio dashboard, revoked the consumer key. Config now references `${COMPOSIO_API_KEY}` exclusively.

**Step 2: Mistral** — in the Mistral console, deleted the historical API key. Tested endpoint returns 401 Unauthorized for the stale key.

**Step 3: Kaggle** — in Kaggle API settings, expired the historical API token. Replaced with environment-injected secret.

**Step 4: Automated Verification** — Verified via `tests/test_credential_hygiene.py` that active configs, persona manifests, and repo templates contain zero raw historical credentials.

### Definition of Done

- [x] Composio consumer key revoked
- [x] Mistral API key deleted
- [x] Kaggle API token expired
- [x] Anything that used them re-tested with new keys from the environment
- [x] Date recorded: **2026-11-18**

---

**Last updated:** 2026-11-18
**Status:** Fix #1 (credential revocation) and Fix #2 (Web API authentication) both verified and completed.

