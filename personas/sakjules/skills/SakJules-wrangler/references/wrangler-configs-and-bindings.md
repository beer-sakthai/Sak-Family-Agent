# Wrangler Configuration & Bindings Reference Guide

Comprehensive syntax, bindings, and command recipes for Cloudflare Workers CLI (`wrangler`).

## 1. Minimal `wrangler.jsonc`
```jsonc
{
  "$schema": "./node_modules/wrangler/config-schema.json",
  "name": "my-worker",
  "main": "src/index.ts",
  "compatibility_date": "2026-01-01",
  "compatibility_flags": ["nodejs_compat"]
}
```

## 2. Resource Bindings

### KV Namespaces
```jsonc
"kv_namespaces": [
  { "binding": "KV_STORE", "id": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" }
]
```

### D1 Databases
```jsonc
"d1_databases": [
  { "binding": "DB", "database_name": "prod-db", "database_id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" }
]
```

### R2 Buckets
```jsonc
"r2_buckets": [
  { "binding": "BUCKET", "bucket_name": "prod-assets" }
]
```

### Vectorize Indexes & Workers AI
```jsonc
"vectorize": [
  { "binding": "VECTOR_INDEX", "index_name": "kb-embeddings" }
],
"ai": {
  "binding": "AI"
}
```

### Queues & Workflows
```jsonc
"queues": {
  "producers": [{ "binding": "TASK_QUEUE", "queue": "task-processing" }],
  "consumers": [{ "queue": "task-processing", "max_batch_size": 10 }]
}
```

## 3. Essential CLI Commands
| Task | Command |
|---|---|
| Local dev | `wrangler dev` |
| Remote deploy | `wrangler deploy` |
| Dry run | `wrangler deploy --dry-run` |
| TypeScript types | `wrangler types` |
| Tail live logs | `wrangler tail` |
| Auth check | `wrangler whoami` |
| D1 migrations | `wrangler d1 migrations apply DB` |
| Secret storage | `wrangler secret put <KEY>` |
