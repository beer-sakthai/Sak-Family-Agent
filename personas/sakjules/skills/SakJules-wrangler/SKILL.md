---
name: SakJules-wrangler
version: 1.1.0
description: Cloudflare Workers CLI protocol for building, configuring, and deploying serverless applications, D1, KV, and R2 bindings.
category: devops
tags:
- automation
- cloudflare
- serverless
- wrangler
---

# Wrangler CLI Protocol

Operational guide for configuring, developing, and deploying Cloudflare Workers and bindings via `wrangler`.

## 1. Prerequisites & Version Requirements
- Ensure Wrangler is installed: `wrangler --version` (Requires v4.x+).
- Install if absent: `npm install -D wrangler@latest`.
- Verify authentication status: `wrangler whoami`.

## 2. Invariants & Best Practices
- **JSONC Over TOML**: Standardize on `wrangler.jsonc` with schema verification (`$schema`).
- **Compatibility Date**: Maintain a recent `compatibility_date` (within 30 days) and include `nodejs_compat` where required.
- **Type Generation**: Always regenerate TypeScript types after modifying bindings: `wrangler types`.
- **Preflight Dry Run**: Validate syntax before production release: `wrangler deploy --dry-run`.

## 3. Workflow Lifecycle
1. **Initialize/Edit**: Update worker script and `wrangler.jsonc`.
2. **Local Simulation**: `wrangler dev` (bindings run locally by default).
3. **Type Check**: Execute `wrangler types` and build validation.
4. **Deploy & Observability**: Execute `wrangler deploy`, then inspect live logs via `wrangler tail`.

## 4. References & Schemas
- Complete bindings, D1 migrations, and queue configs: [Wrangler Configs & Bindings](references/wrangler-configs-and-bindings.md)
