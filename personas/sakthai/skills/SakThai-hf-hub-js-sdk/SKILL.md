---
name: SakThai-hf-hub-js-sdk
author: SakThai
license: MIT
description: >
  Complete reference for the @huggingface/* TypeScript/JS SDK monorepo —
  inference, hub, gguf, mcp-client, tiny-agents, tasks, jinja, dduf,
  ollama-utils, and space-header packages.
version: 2.0.0
metadata:
  hermes:
    tags: [huggingface, javascript, typescript, sdk, inference, hub]
    category: software-development
category: mlops
---

# huggingface.js — Official Hugging Face TypeScript/JS SDK
**package:** @huggingface/* monorepo  
**version:** inference@4.13.23 | hub@2.13.3 | gguf@0.4.3 | mcp-client@0.2.3 | tiny-agents@0.3.4 | tasks@0.21.28 | jinja@0.5.9 | dduf@0.0.2 | ollama-utils@0.0.18 | space-header@1.0.4  
**npm:** `@huggingface/inference`, `@huggingface/hub`, `@huggingface/gguf`, `@huggingface/mcp-client`, `@huggingface/tiny-agents`, `@huggingface/tasks`, `@huggingface/jinja`, `@huggingface/dduf`, `@huggingface/ollama-utils`, `@huggingface/space-header`  
**docs:** https://huggingface.co/docs/huggingface.js  
**repo:** https://github.com/huggingface/huggingface.js  
**requires:** Node.js >= 18, Bun, or Deno (modern ESM, no polyfills)

## Packages Overview

| Package | Version | Purpose |
|---------|---------|---------|
| `@huggingface/inference` | 4.13.23 | Unified inference client for Providers, Inference Endpoints, and local servers |
| `@huggingface/hub` | 2.13.3 | Hub API client — create/delete repos, upload/download files, search, OAuth |
| `@huggingface/mcp-client` | 0.2.3 | MCP client with built-in Agent over InferenceClient |
| `@huggingface/tiny-agents` | 0.3.4 | Composable lightweight AI agents (hub-sourced or local) |
| `@huggingface/gguf` | 0.4.3 | GGUF parser for remotely hosted files |
| `@huggingface/dduf` | 0.0.2 | DDUF (Diffusers Unified Format) parser |
| `@huggingface/tasks` | 0.21.28 | Type definitions for Hub primitives (pipeline tasks, model libraries) |
| `@huggingface/jinja` | 0.5.9 | Minimal Jinja templating engine for ML chat templates |
| `@huggingface/ollama-utils` | 0.0.18 | Ollama compatibility utilities for Hub models |
| `@huggingface/space-header` | 1.0.4 | Reusable Space mini_header outside HF |

## Key Features

### 1. `@huggingface/inference`

**Unified client** for three inference modes:
- **Inference Providers** (serverless): 18+ providers including Together, Replicate, Fireworks, Groq, SambaNova, Cerebras, DeepInfra, Cohere, Baseten, etc.
- **Inference Endpoints** (dedicated): Connect to your own deployed endpoint
- **Local endpoints**: llama.cpp, vLLM, LiteLLM, TGI, Ollama via OpenAI-compatible API

Chat completion with streaming, text/image/audio generation, feature extraction, and more — all with full TypeScript types.

**Provider routing:** Pass `provider: "auto"` (default) or specify a provider name. Auto-routing picks the first available provider sorted by user preference on hf.co/settings/inference-providers.

**Error hierarchy:**
- `InferenceClientError` (base)
- `InferenceClientInputError` → invalid input
- `InferenceClientProviderApiError` → provider API failure (has `request` and `response` properties)
- `InferenceClientHubApiError` → HF Hub API failure
- `InferenceClientProviderOutputError` → malformed provider response

**Task support:** textGeneration, chatCompletion, featureExtraction, fillMask, summarization, questionAnswering, textClassification, tokenClassification, translation, zeroShotClassification, sentenceSimilarity, automaticSpeechRecognition, audioClassification, textToSpeech, audioToAudio, imageClassification, objectDetection, imageSegmentation, imageToText, textToImage, imageToImage, zeroShotImageClassification, visualQuestionAnswering, documentQuestionAnswering, tabularRegression, tabularClassification

**Tree-shaking:** Individual functions importable (e.g., `import { textGeneration } from "@huggingface/inference"`) for smaller bundles.

### 2. `@huggingface/hub`

Full Hub API client:
- `createRepo`, `deleteRepo`, `repoInfo`, `modelInfo`, `listModels`, `listFiles`
- `uploadFiles`, `uploadFile`, `uploadFilesWithProgress` (streaming progress)
- `downloadFile`, `downloadFileToCacheDir`, `snapshotDownload`
- `deleteFiles`, `deleteFile`
- `commit` with edit operations (prefix/suffix edits on files)
- `whoAmI`, `checkRepoAccess`
- `scanCacheDir` — inspect HF cache
- OAuth login (`oauthLoginUrl`, `oauthHandleRedirectIfPresent`)

**CLI mode:** `npx @huggingface/hub upload` and `npx @huggingface/hub branch create`. Global install provides `hfjs` command.

**Performance:** Upload large files inside a Worker to offload SHA-256. Lazy blob loading for remote/local files via `URL` objects.

### 3. `@huggingface/mcp-client`

MCP client built atop InferenceClient. Supports stdio, SSE, and HTTP MCP server transports. Includes a CLI agent that auto-loads tools from configured MCP servers.

### 4. `@huggingface/tiny-agents`

Lightweight composable agent framework:
- Define agents via `agent.json` (model, provider/servers, optional PROMPT.md/AGENTS.md)
- Hub-hosted agent collection at `hf.co/datasets/tiny-agents/tiny-agents`
- CLI: `npx @huggingface/tiny-agents run "agent/id"` or `serve "agent/id"` as OpenAI-compatible HTTP server
- Programmatic `new Agent({...})` with `agent.loadTools()` and `agent.run()`

### 5. `@huggingface/gguf`

GGUF parser for remote or local files:
- `gguf(url)` returns `{ metadata, tensorInfos }`
- `typedMetadata: true` provides GGUF data type info alongside values
- Strictly typed architecture-aware metadata (llama, mamba, whisper, etc.)
- CLI: `npx @huggingface/gguf my_model.gguf` (like gguf_dump.py)
- Global install provides `gguf-view` command

### 6. `@huggingface/tasks`

Source of truth for Hub primitives: pipeline tasks, model libraries, dataset types, metrics. Used as typing-only dependency by other packages.

### 7. `@huggingface/jinja`

Minimal JS implementation of Jinja templating, used for ML chat templates (e.g., tokenizer `apply_chat_template` in JS environments).

### 8. `@huggingface/dduf`

Parser for DDUF (Diffusers Unified Format) — the new format for Diffusers model bundles.

### 9. `@huggingface/ollama-utils`

Utilities for maintaining Ollama compatibility with Hub models — tags, manifests, model file generation.

### 10. `@huggingface/space-header`

Reusable Space mini_header component for use outside of HF.

## Installation

```bash
npm install @huggingface/inference @huggingface/hub @huggingface/gguf
```

**CDN:**
```html
<script type="module">
  import { InferenceClient } from 'https://cdn.jsdelivr.net/npm/@huggingface/inference@4.13.23/+esm';
</script>
```

**Deno:**
```ts
import { InferenceClient } from "https://esm.sh/@huggingface/inference";
```

## Quick Start

```ts
import { InferenceClient } from "@huggingface/inference";

const client = new InferenceClient("hf_...");

// Chat completion
const out = await client.chatCompletion({
  model: "Qwen/Qwen3-32B",
  provider: "cerebras",
  messages: [{ role: "user", content: "Hello!" }],
});

// Hub operations
import { createRepo, uploadFiles } from "@huggingface/hub";
await createRepo({ repo: { type: "model", name: "myuser/my-model" }, accessToken: "hf_..." });
```

## Key Considerations

- **Access tokens:** Always pass a token for inference. For browser/SPA, proxy through a backend to protect the token.
- **Zero-cost compatible:** Inference Providers have free tiers; Inference Endpoints are paid.
- **Modern JS only:** Uses native ESM — no polyfills, requires Node >= 18 / Bun / Deno.
- **OAuth:** `@huggingface/hub` supports Sign in with HF for client-side web apps.
