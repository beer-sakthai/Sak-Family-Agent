---
name: SakThai-hf-jobs-api-deep-dive
author: SakThai
license: MIT
skill_type: reference
domain: hub
version: 1.0.0
created: 2026-07-25
updated: 2026-07-25
category: mlops
---

# Hugging Face Jobs API — Python SDK Deep Dive

## Description

Complete reference for the Hugging Face **Jobs** compute platform's Python SDK (`huggingface_hub` v1.24.0). Covers every API method, dataclass, and implementation detail for running, scheduling, monitoring, and managing compute jobs programmatically — including UV scripts, scheduled cron jobs, volume mounting, port exposure, SSH access, and the SSE-based log/metric streaming system.

Based on source code analysis of `_jobs_api.py` (573 lines) and `hf_api.py` methods (lines 11802–13200+).

## Files

- `references/hf-learnings.md` — Full research with source-level API reference, dataclass architecture, and usage patterns

## Related Skills

- `hf-jobs-complete-ecosystem-deep-dive` — CLI-focused job reference (topic #233)
- `hf-hub-buckets-api` — Storage Buckets for job volume mounting
- `hf-hub-webhooks-and-notifications-api` — Webhook-triggered jobs
- `hf-spaces-secrets-management` — Secret env vars for jobs
