# Security Policy

## Reporting a Vulnerability

Please do not open public issues for security vulnerabilities.

Email: **beer@example.com** (replace with your actual contact)
Subject: `[SECURITY] sakthai-agent-v2`

We will acknowledge within 3 business days and provide a fix timeline.

## Hardening rules

- No secrets in source or default configs.
- `.env` is gitignored; only `.env.example` is committed.
- CI runs `ruff`, `mypy`, `bandit`, `pytest`, and a secret scan.
- Dependencies are pinned in `uv.lock`; review before merging.
- API surfaces are read-only unless explicitly gated.
