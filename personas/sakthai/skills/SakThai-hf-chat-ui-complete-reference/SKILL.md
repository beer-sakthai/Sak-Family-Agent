---
name: SakThai-hf-chat-ui-complete-reference
version: 1.0.0
description: Complete reference for Hugging Face Chat UI — the open-source SvelteKit
  chat interface powering HuggingChat (hf.co/chat). Covers installation (local, Docker,
  Helm), configuration (models, MCP tools, LLM Router, OpenID, theming, voice transcription,
  r
category: mlops
tags:
- chat
- complete
- hf
- huggingface
- reference
- ui
---

# Chat UI — Complete Reference

**Chat UI** is Hugging Face's open-source chat interface for LLMs, built with SvelteKit + MongoDB + Tailwind CSS. It powers [HuggingChat at hf.co/chat](https://huggingface.co/chat) and is fully self-hostable. Version 0.20.0 (July 2026).

## Table of Contents

1. [Quickstart](#quickstart)
2. [Installation](#installation)
3. [Configuration Overview](#configuration-overview)
4. [Model Configuration](#model-configuration)
5. [LLM Router](#llm-router)
6. [MCP Tools](#mcp-tools)
7. [Authentication (OpenID Connect)](#authentication-openid-connect)
8. [Theming & UI Customization](#theming--ui-customization)
9. [Voice Transcription](#voice-transcription)
10. [Rate Limits & Usage Controls](#rate-limits--usage-controls)
11. [Metrics & Monitoring](#metrics--monitoring)
12. [Feature Flags](#feature-flags)
13. [Architecture](#architecture)
14. [Deployment](#deployment)
15. [Common Issues & Pitfalls](#common-issues--pitfalls)

---

## Quickstart

The fastest way to run Chat UI locally with Hugging Face Inference Providers:

```bash
# 1. Create .env.local
cat > .env.local << 'EOF'
OPENAI_BASE_URL=https://router.huggingface.co/v1
OPENAI_API_KEY=hf_xxxxxxxxxxxxxxxxxxxx
EOF

# 2. Install and run
git clone https://github.com/huggingface/chat-ui
cd chat-ui
npm install
npm run dev -- --open
```

Models are **auto-discovered** from `{OPENAI_BASE_URL}/models` — no manual model list needed.

## Installation

### Local (Node.js)

Requirements: Node.js 18+, npm 9+

```bash
git clone https://github.com/huggingface/chat-ui
cd chat-ui
cp .env .env.local   # edit with your config
npm install
npm run dev           # dev server on http://localhost:5173
npm run build         # production build
npm run preview       # preview production build
```

### Docker (bundled MongoDB)

The `chat-ui-db` image includes MongoDB inside the container:

```bash
docker run \
  -p 3000:3000 \
  -e OPENAI_BASE_URL=https://router.huggingface.co/v1 \
  -e OPENAI_API_KEY=hf_*** \
  -v chat-ui-data:/data \
  ghcr.io/huggingface/chat-ui-db:latest
```

All environment variables from `.env.local` work as `-e` flags.

### Docker (separate MongoDB)

```bash
# Start MongoDB
docker run -d -p 27017:27017 --name mongo-chatui mongo:latest

# Build and run Chat UI
docker build -t chat-ui .
docker run -p 3000:3000 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  -e OPENAI_BASE_URL=https://router.huggingface.co/v1 \
  -e OPENAI_API_KEY=hf_*** \
  chat-ui
```

### Helm (Kubernetes)

Available in the repo's Helm chart. See the Helm installation docs for values.yaml configuration.

## Configuration Overview

Chat UI is configured exclusively through **environment variables**. Defaults are in `.env`; override in `.env.local` or system environment.

> **Quick lookup:** `references/dotenv-reference.md` has the complete `.env` variable table with defaults, types, and descriptions — every variable in one place.

### Required

| Variable | Description |
|----------|-------------|
| `OPENAI_BASE_URL` | OpenAI-compatible API endpoint |
| `OPENAI_API_KEY` | Auth token (HF token, OpenAI key, or provider key) |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `MONGODB_URL` | (embedded) | MongoDB connection string. **Unset = embedded MongoDB** (persists to `./db`) |
| `MONGODB_DB_NAME` | `chat-ui` | Database name |
| `MONGODB_DIRECT_CONNECTION` | `false` | Force direct connection mode |

> **Zero-cost dev**: When `MONGODB_URL` is unset, Chat UI uses an in-process embedded MongoDB via `mongodb-memory-server`. Data persists to `./db`. Perfect for local development without external infra.

### Provider Compatibility

| Provider | `OPENAI_BASE_URL` | Key |
|----------|-------------------|-----|
| Hugging Face Router | `https://router.huggingface.co/v1` | `hf_xxx` |
| llama.cpp | `http://127.0.0.1:8080/v1` | any string |
| Ollama | `http://127.0.0.1:11434/v1` | `ollama` |
| OpenRouter | `https://openrouter.ai/api/v1` | `sk-or-v1-...` |
| Poe | `https://api.poe.com/v1` | `pk_...` |

## Model Configuration

### Auto-Discovery

Models are fetched from `{OPENAI_BASE_URL}/models`. Each model's metadata (multimodal, tool support, etc.) is read from the provider's response.

### Model Overrides (MODELS env var)

Override model metadata with a JSON5 array:

```env
MODELS=`[
  {
    "id": "meta-llama/Llama-3.3-70B-Instruct",
    "name": "Llama 3.3 70B",
    "multimodal": false,
    "supportsTools": true,
    "supportsArtifacts": true
  }
]`
```

Fields: `id`, `name`, `multimodal`, `supportsTools`, `supportsArtifacts`.

### Task Model

Optional model for internal tasks (title summarization, etc.):

```env
TASK_MODEL=meta-llama/Llama-3.3-70B-Instruct
```

If unset, the current conversation model is used.

### User Token Forwarding

```env
USE_USER_TOKEN=true
```

When enabled, the signed-in user's HF token is used for inference calls instead of the server's `OPENAI_API_KEY`.

## LLM Router

The LLM Router provides a smart **virtual model** (default name: "Omni") that routes each request to the optimal model based on content type.

### Basic Setup

```env
# Path to routes policy JSON file
LLM_ROUTER_ROUTES_PATH=config/routes.chat.json

# Model fallback when all routes fail
LLM_ROUTER_FALLBACK_MODEL=meta-llama/Llama-3.3-70B-Instruct
```

### Route Types

The router recognizes three route names from the policy file:

| Route | Trigger | Config Variable |
|-------|---------|-----------------|
| `default` | Regular text chat | `LLM_ROUTER_DEFAULT_ROUTE` (default: `default`) |
| `multimodal` | Image input | `LLM_ROUTER_MULTIMODAL_MODEL` |
| `agentic` | MCP tools enabled | `LLM_ROUTER_TOOLS_MODEL` |

### Route Policy File Format

```json
[
  {
    "name": "default",
    "description": "Fast general-purpose model",
    "primary_model": "meta-llama/Llama-3.3-70B-Instruct",
    "fallback_models": ["meta-llama/Llama-3.1-8B-Instruct"]
  },
  {
    "name": "multimodal",
    "description": "Vision-capable model",
    "primary_model": "meta-llama/Llama-3.2-11B-Vision-Instruct"
  },
  {
    "name": "agentic",
    "description": "Tool-capable model",
    "primary_model": "meta-llama/Llama-3.3-70B-Instruct"
  }
]
```

### Shortcut Env Vars (bypass policy file)

```env
# Multimodal shortcut
LLM_ROUTER_ENABLE_MULTIMODAL=true
LLM_ROUTER_MULTIMODAL_MODEL=meta-llama/Llama-3.2-11B-Vision-Instruct

# Tools shortcut
LLM_ROUTER_ENABLE_TOOLS=true
LLM_ROUTER_TOOLS_MODEL=meta-llama/Llama-3.3-70B-Instruct
```

When these shortcuts are enabled and the relevant condition is met (image attached / MCP server on), the router bypasses the policy file entirely.

### UI Customization

```env
PUBLIC_LLM_ROUTER_DISPLAY_NAME=Omni
PUBLIC_LLM_ROUTER_LOGO_URL=
PUBLIC_LLM_ROUTER_ALIAS_ID=omni
```

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [Chat UI MCP Tools, OpenID Connect & Router Architecture](./references/chat-ui-mcp-and-auth.md).
