---
name: SakThai-hf-chat-ui-complete-reference
description: "Complete reference for Hugging Face Chat UI \u2014 the open-source SvelteKit chat\
  \ interface powering HuggingChat (hf.co/chat). Covers installation (local, Docker,\
  \ Helm), configuration (models, MCP tools, LLM Router, OpenID, theming, voice transcription,\
  \ r"
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

## MCP Tools

Chat UI integrates with **Model Context Protocol (MCP)** servers for tool calling, using OpenAI function calling under the hood.

### Server Configuration

```env
MCP_SERVERS=[{"name": "Web Search (Exa)", "url": "https://mcp.exa.ai/mcp"}, {"name": "Hugging Face MCP", "url": "https://hf.co/mcp"}]

# Forward signed-in user's HF token to MCP servers
MCP_FORWARD_HF_USER_TOKEN=true

# API key injected into mcp.exa.ai URLs
EXA_API_KEY=your_exa_key

# Tool call timeout (default: 120000ms = 2 minutes)
MCP_TOOL_TIMEOUT_MS=120000

# Allow HTTP on localhost/private LAN (dev only!)
MCP_ALLOW_INSECURE_URLS=false
```

### UI Interaction

- **MCP Servers panel**: Top-right menu or `+` menu in chat input
- **Health Check**: Test server connectivity
- **Tool cards**: Each server shows available tools
- **Execution**: When a model calls a tool, the UI shows a compact tool block with parameters, progress bar, and result
- **Per-model overrides**: Settings → Model → toggle "Tool calling (functions)" per model

### Integration Pattern

```
User message → Model (with function calling) → MCP server call → Tool result → Model generates response with tool output
```

## Authentication (OpenID Connect)

### Basic OpenID Setup

```env
OPENID_CONFIG={}
OPENID_CLIENT_ID=__CIMD__
OPENID_CLIENT_SECRET=
OPENID_SCOPES="openid profile inference-api read-mcp read-billing"
```

`__CIMD__` (Client ID Metadata Document) auto-creates an OAuth app when deployed to HF Spaces.

### Provider Configuration

```env
OPENID_PROVIDER_URL=https://huggingface.co
# For Google: OPENID_PROVIDER_URL=https://accounts.google.com
OPENID_NAME_CLAIM=name  # or "username" for some providers
OPENID_TOLERANCE=
OPENID_RESOURCE=
```

### Access Control

```env
# Allow only specific emails
ALLOWED_USER_EMAILS=["user@example.com"]

# Allow all users from specific domains
ALLOWED_USER_DOMAINS=["huggingface.co"]

# Auto-redirect to login
AUTOMATIC_LOGIN=false
```

### Cookie Configuration

```env
COOKIE_NAME=hf-chat
COOKIE_SAMESITE=lax     # "lax", "strict", "none", or empty
COOKIE_SECURE=true      # HTTPS only
COUPLE_SESSION_WITH_COOKIE_NAME=
```

## Theming & UI Customization

```env
PUBLIC_APP_NAME=ChatUI              # Title throughout the app
PUBLIC_APP_ASSETS=chatui            # Logo/favicon set: "chatui" or "huggingchat"
PUBLIC_APP_DESCRIPTION="Making the community's best AI chat models available to everyone."
PUBLIC_APP_DATA_SHARING=            # Enable data sharing opt-in toggle
PUBLIC_ORIGIN=                      # Public origin URL
PUBLIC_CAVEAT=                      # Text shown below chat input
PUBLIC_SHARE_PREFIX=                # Share URL prefix
PUBLIC_GOOGLE_ANALYTICS_ID=         # Google Analytics
PUBLIC_PLAUSIBLE_SCRIPT_URL=        # Plausible Analytics
PUBLIC_APPLE_APP_ID=                # Apple App ID for PWA

# Feature announcements (toast on home screen)
PUBLIC_FEATURE_ANNOUNCEMENTS=[{"title":"New Model","description":"Try it now","link":"/models/...","cta":"Go","maxDate":"2026-12-31"}]
```

## Voice Transcription

```env
# Model for voice-to-text
TRANSCRIPTION_MODEL=openai/whisper-large-v3-turbo

# Optional: custom transcription API base URL
TRANSCRIPTION_BASE_URL=https://router.huggingface.co/hf-inference/models
```

When `TRANSCRIPTION_MODEL` is set, the microphone button appears in the chat input.

## Rate Limits & Usage Controls

```env
USAGE_LIMITS={
  "conversations": 50,
  "messages": 1000,
  "assistants": 10,
  "messageLength": 10000,
  "messagesPerMinute": 30,
  "tools": 10
}
```

Defined in `src/lib/server/usageLimits.ts`.

## Metrics & Monitoring

```env
METRICS_ENABLED=false
METRICS_PORT=5565
LOG_LEVEL=info
```

Uses `prom-client` for Prometheus metrics on the metrics port.

### Generation Health Monitoring

```env
GENERATION_REAP_INTERVAL_MS=60000     # Sweep interval for dead generations
GENERATION_REAP_AFTER_MS=90000        # No heartbeat = presumed dead
GENERATION_HEARTBEAT_MS=10000         # Generation heartbeat interval
```

## Feature Flags

| Flag | Default | Description |
|------|---------|-------------|
| `LLM_SUMMARIZATION` | `true` | Generate conversation titles with LLMs |
| `ALLOW_IFRAME` | `true` | Allow embedding in iframes |
| `ENABLE_DATA_EXPORT` | `true` | Enable conversation data export |
| `ENABLE_CONFIG_MANAGER` | `true` | Enable config manager UI |
| `USE_USER_TOKEN` | `false` | Use user token for inference |

**Artifacts**: Per-model opt-in via `"supportsArtifacts": true` in MODELS overrides. Artifacts render model-generated apps/docs/diagrams in a side panel.

## Architecture

Chat UI is a **SvelteKit** app (Svelte 5 + SvelteKit 2) with the following code map:

```
src/
├── routes/             # SvelteKit pages + API endpoints
├── lib/
│   ├── server/
│   │   ├── textGeneration/  # OpenAI API integration (chat completions)
│   │   ├── endpoints/       # Model discovery & provider config
│   │   ├── mcp/             # MCP server management & tool execution
│   │   ├── llmRouter/       # Smart routing heuristics
│   │   └── migrations/      # MongoDB schema migrations
│   └── client/              # Client-side components
├── static/              # Static assets (logos, favicons)
└── scripts/             # CLI tools (config, populate, updateLocalEnv)
```

### Key Dependencies

| Package | Purpose |
|---------|---------|
| `@huggingface/hub` | HF Hub SDK for OAuth, Spaces, repo access |
| `@huggingface/inference` | HF InferenceClient |
| `@modelcontextprotocol/sdk` | MCP client for tool integration |
| `openai` | OpenAI API client for chat completions |
| `mongodb` | Database driver |
| `openid-client` | OpenID Connect authentication |
| `prom-client` | Prometheus metrics |
| `svelte` + `@sveltejs/kit` | Web framework (Svelte 5 + SvelteKit 2) |
| `tailwindcss` | CSS framework (Tailwind 4) |
| `vite` | Build tool (Vite 6) |
| `bits-ui` | UI component library |

### Key Design Decisions

1. **OpenAI-only API** — All model interactions use the OpenAI chat completions format. Any OpenAI-compatible endpoint works.
2. **MCP for tools** — Tool calling is handled exclusively via MCP servers, not custom integrations.
3. **Auto-discovery** — Models are listed from `{base_url}/models`; no manual model registration.
4. **Embedded MongoDB** — Falls back to `mongodb-memory-server` when no `MONGODB_URL` is set, enabling zero-infrastructure development.

## Deployment

### Production Build

```bash
npm run build
npm run preview
```

For production, set `MONGODB_URL` to a persistent MongoDB (Atlas free tier works) and use a process manager or container orchestration.

### Docker Production

```bash
docker build -t chat-ui .
docker run -d -p 3000:3000 \
  -e MONGODB_URL=mongodb://mongo:27017 \
  -e OPENAI_BASE_URL=https://router.huggingface.co/v1 \
  -e OPENAI_API_KEY=hf_*** \
  --name chat-ui-prod \
  chat-ui
```

### Hugging Face Space Deployment

Deploy as a Docker Space using the `ghcr.io/huggingface/chat-ui-db` image, or as a custom Space with the Node.js buildpack. Set `AUTOMATIC_LOGIN=true` and configure OpenID with `OPENID_CLIENT_ID=__CIMD__` for automatic OAuth app creation.

### Body Size Limit

```env
BODY_SIZE_LIMIT=15728640  # 15MB default, for file uploads
```

## Common Issues & Pitfalls

### 429 Rate Limiting

Chat UI makes one request per message. If using HF Inference Providers, be aware of free-tier rate limits. Consider adding `USE_USER_TOKEN=true` so each user's own token/rate limit is used.

### MongoDB Connection

- **Embedded mode**: Data persists in `./db`. Deleting this directory resets all data.
- **Atlas**: Add `0.0.0.0/0` to network access for development; use IP whitelist for production.
- **Connection strings**: Verify `MONGODB_URL` format — standard MongoDB URI format required.

### Model Not Appearing

- Verify the model is listed at `{OPENAI_BASE_URL}/models`
- Check that `OPENAI_API_KEY` has access to the model (gated models may need approval)
- For HF Router, gated models require the user/HF token to have accepted the terms

### MCP Tools Not Working

- Ensure the model supports function calling (`supportsTools: true`)
- Run Health Check on the MCP server from the UI
- Check `MCP_TOOL_TIMEOUT_MS` — increase if tools are slow
- For local MCP servers, set `MCP_ALLOW_INSECURE_URLS=true` (dev only)

### OpenID Login Issues

- Verify `OPENID_PROVIDER_URL` is correct (with `https://`)
- For Hugging Face OAuth: use `__CIMD__` as `OPENID_CLIENT_ID` when deploying to Spaces
- Check `ALLOWED_USER_EMAILS` / `ALLOWED_USER_DOMAINS` if users can't log in
- Set `AUTOMATIC_LOGIN=true` to require authentication on all routes

### Cookie/Session Issues

- Cross-origin deployments: set `COOKIE_SAMESITE=none` and `COOKIE_SECURE=true`
- Sub-path deployments: use `COUPLE_SESSION_WITH_COOKIE_NAME` to tie sessions to parent domain auth

---

*Researched July 2026 from Hugging Face Chat UI docs, GitHub repository (v0.20.0), and .env template.*
