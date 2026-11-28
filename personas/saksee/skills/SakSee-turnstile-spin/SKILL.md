---
name: SakSee-turnstile-spin
version: 1.0.0
description: Set up Cloudflare Turnstile bot verification end-to-end across frontend embed, API endpoints, and canonical siteverify.
category: frontend
tags:
- automation
- spin
- turnstile
---

# SakSee Turnstile Spin Skill

## Overview

Turns the prompt "set up Turnstile" into a working end-to-end integration: widget creation, frontend snippet insertion, canonical server-side siteverify inside existing backend handlers, and automated validation.

Operated by **SakSee** (`@saksee_agent_bot`), the Web & Browser Specialist of the House of Sak.

---

## 1. Operating Rules & Core Constraints

| Rule | Enforcement |
|:---|:---|
| **Gate, Don't Replace** | Existing backend handlers remain intact; siteverify gates execution on `success === true`. |
| **No Secret Leaks** | Never echo, print, log, or commit `TURNSTILE_SECRET`. Pass via stdin or `.env`. |
| **Fail Closed** | If siteverify encounters network errors or non-2xx status, return HTTP 403 Forbidden. |
| **Single-Use Tokens** | Verify replay rejection; reset widget with `window.turnstile.reset(widgetId)` on SPA forms. |
| **Out-of-Scope Boundaries** | Do NOT add email delivery, database persistence, or custom proxies. |

---

## 2. Execution Flow Summary

```
Prompt ──► Auth & Scope Probe (auth-probe.sh) ──► Codebase Scan (Frontend/Backend)
                 │
                 ▼
          Insertion Plan (signup/login/contact) ──► Widget Creation / Existing Sitekey
                 │
                 ▼
          Wire Frontend (<cf-turnstile>) & Backend (siteverify) ──► Validation (validate.sh)
```

1. **Auth & Scope Probe**: Run `scripts/auth-probe.sh`. Require `Account.Turnstile:Edit` token.
2. **Scan Codebase**: Detect framework (Next.js, Express, Workers, Astro) and form endpoints.
3. **Widget Setup**: Create via approved Wrangler or `scripts/widget-create.sh`. Localhost (`localhost`, `127.0.0.1`) + production domain.
4. **Wire Backend**: Insert siteverify fetch targeting `https://challenges.cloudflare.com/turnstile/v0/siteverify`.
5. **Verify**: Run `scripts/validate.sh` and exercise replay rejection.

---

## 3. Reference Documents

For complete implementation templates, backend adapters, and migration guides, consult:
- [Turnstile Setup Flow & Code Reference](./references/turnstile-setup-flow.md)
