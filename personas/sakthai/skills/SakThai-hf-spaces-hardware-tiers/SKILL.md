---
name: SakThai-hf-spaces-hardware-tiers
description: 'HuggingFace Spaces hardware tiers: CPU, GPU, and accelerators'
---

# HF Spaces Hardware Tiers

Complete reference for all Hugging Face Spaces hardware options — CPU tiers, GPU accelerators, ZeroGPU, pricing, billing, and best practices for selecting the right hardware for your use case.

## Key Endpoints / APIs

- **Set hardware programmatically:** `POST /api/spaces/{namespace}/{repo}/hardware` with `{"flavor": "t4-small", "sleepTime": 3600}`
- **Get available hardware:** `GET /api/spaces/{namespace}/{repo}` — response includes hardware flavor in `runtime` field
- **Set replicas:** `POST /api/spaces/{namespace}/{repo}/replicas` with `{"replicas": 2}`
- **Stream logs/events/metrics:** `GET /api/spaces/{namespace}/{repo}/logs/{build|run}`, `/events`, `/metrics` (SSE, authenticated)
- **Pause:** Via hub settings UI or `/api/spaces/{namespace}/{repo}/settings` with `pause: true`

## Zero-Cost Considerations

- **CPU Basic** is always free — 2 vCPU, 16 GB RAM, 50 GB disk
- **ZeroGPU** is free but requires PRO plan ($9/mo) — dynamic Nvidia RTX Pro 6000 Blackwell, up to 96 GB VRAM, 8× higher quota with PRO
- **Static Spaces** (HTML/JS only) are always free for everyone
- **Community GPU Grants** available for side projects — apply from Space settings
- **Pausing stops billing** — only Starting/Running states are billed
- **Custom sleep time** can be set on paid hardware to auto-pause when idle

## Framework Setup

See references/hf-learnings.md for complete deep dive.
