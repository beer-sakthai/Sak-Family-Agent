# HF Learnings: huggingface.js Deep Dive — Full Package Architecture & API Reference

**Date:** 2026-07-25
**Topic:** `hf-hub-js-sdk` (deep-dive v2)
**Author:** SakThai
**License:** MIT
**Sources:**
- Official docs: https://huggingface.co/docs/huggingface.js
- Hub API: https://huggingface.co/docs/huggingface.js/hub/README
- Inference: https://huggingface.co/docs/huggingface.js/inference/README
- Tiny Agents: https://huggingface.co/docs/huggingface.js/tiny-agents/README
- MCP Client: https://huggingface.co/docs/huggingface.js/mcp-client/README
- GGUF: https://huggingface.co/docs/huggingface.js/gguf/README
- GitHub: https://github.com/huggingface/huggingface.js
- Inference Providers docs: https://huggingface.co/docs/inference-providers/en/index
- Tiny Agents Hub Dataset: https://huggingface.co/datasets/tiny-agents/tiny-agents

---

## 1. Architecture Overview

The huggingface.js monorepo at `github.com/huggingface/huggingface.js` publishes **10 npm packages**. Unlike Python's `huggingface_hub` which is a single monolithic package, the JS SDK is intentionally **modular** — each concern is its own tiny package for tree-shaking and minimal bundle sizes.

### Package Dependency Graph

```
@huggingface/tasks (types, no runtime)
       |
       v
@huggingface/jinja (chat templates)
       |
       v
@huggingface/inference (inference client)
       |
       +---> @huggingface/hub (hub API client)
       |
       v
@huggingface/mcp-client (MCP client + agent)
       |
       v
@huggingface/tiny-agents (composable agents)
       
@huggingface/gguf (GGUF parser, standalone)
@huggingface/dduf (DDUF parser, standalone)
@huggingface/ollama-utils (Ollama compatibility, standalone)
@huggingface/space-header (reusable space header, standalone)
```

### Key Design Decision: Modularity over Monolith

| Aspect | Python SDK | JS SDK |
|--------|-----------|--------|
| Package style | Single `huggingface_hub` | 10 separate `@huggingface/*` packages |
| Tree-shaking | Not applicable | Built-in — import only what you need |
| Bundle size | 100s of KB | Minimal per-package (tasks=52KB types-only) |
| CLI | Single `huggingface-cli` | Per-package CLIs + global `hfjs` |
| Async model | Sync + asyncio | All async (Promises, async iterables) |
| Auth | Token, OAuth, App auth | Token, OAuth (Sign in with HF) |
| Agent framework | smolagents (Python) | tiny-agents (JS, MCP-based) |

---

## 2. @huggingface/inference — Complete Deep Dive

### Version: 4.13.23

The `InferenceClient` is a **unified interface** to three inference modes via a single constructor:

```
InferenceClient(token)
  ├── provider: "auto" → HF routers to 18+ Inference Providers
  ├── endpointUrl: "https://..." → dedicated Inference Endpoint or local server
  └── (no provider/endpoint) → Falls back to HF serverless inference
```

### Inference Providers (18+ Partners)

Current provider list (verified from docs):
Fal.ai, Featherless AI, Fireworks AI, HF Inference, Novita, Nscale, OVHcloud, Public AI, Replicate, Scaleway, Together, Baseten, Cohere, Cerebras, DeepInfra, Groq, Wavespeed.ai, Z.ai

**Provider resolution logic:**
1. Default `provider: "auto"` → HF checks user's preferred provider order at `hf.co/settings/inference-providers`
2. Explicit `provider: "together"` → routes directly to that provider
3. When using HF token → request goes through `https://huggingface.co` as proxy
4. When using 3rd-party API key → request goes directly to that provider's API

**Model discovery per provider:**
Each provider publishes its supported model list at:
```
https://huggingface.co/api/partners/{provider}/models
```
Example: `https://huggingface.co/api/partners/fireworks-ai/models`

### Key API Methods

#### Chat Completion (Primary LLM Interface)

```typescript
// Non-streaming
const response = await client.chatCompletion({
  model: "Qwen/Qwen3-32B",
  provider: "cerebras",
  messages: [{ role: "user", content: "Hello" }],
  max_tokens: 512,
  temperature: 0.1,
  // Optional: top_p, frequency_penalty, presence_penalty, stop, seed, tools
});

// Streaming — returns async iterable
for await (const chunk of client.chatCompletionStream({
  model: "Qwen/Qwen3-32B",
  provider: "cerebras",
  messages: [{ role: "user", content: "Hello" }],
  max_tokens: 512,
})) {
  if (chunk.choices?.[0]?.delta?.content) {
    process.stdout.write(chunk.choices[0].delta.content);
  }
}
```

#### Text Generation (Legacy/Non-Chat)

```typescript
const result = await client.textGeneration({
  model: "mistralai/Mixtral-8x7B-v0.1",
  provider: "together",
  inputs: "The answer to the universe is",
});

// Streaming
for await (const output of client.textGenerationStream({
  model: "mistralai/Mixtral-8x7B-v0.1",
  inputs: "repeat 'one two three'",
  parameters: { max_new_tokens: 250 },
})) {
  console.log(output.token.text, output.generated_text);
}
```

#### Vision & Multimodal

```typescript
// Text-to-Image
const image = await client.textToImage({
  provider: "replicate",
  model: "black-forest-labs/Flux.1-dev",
  inputs: "A black forest cake",
});

// Image-to-Text (captioning)
const caption = await client.imageToText({
  model: "Salesforce/blip-image-captioning-base",
  data: readFileSync("photo.jpg"),
});

// Visual Question Answering
const answer = await client.visualQuestionAnswering({
  model: "google/paligemma-3b-mix-224",
  inputs: {
    image: readFileSync("chart.png"),
    question: "What is the highest value?",
  },
});
```

#### Embeddings

```typescript
const embeddings = await client.featureExtraction({
  model: "sentence-transformers/distilbert-base-nli-mean-tokens",
  inputs: "That is a happy person",
});
```

### Error Handling Hierarchy

```
InferenceClientError (base)
├── InferenceClientInputError         — invalid/missing input params
├── InferenceClientProviderApiError   — provider API failure (has .request, .response)
├── InferenceClientHubApiError        — HF Hub API failure (has .request, .response)
└── InferenceClientProviderOutputError — malformed provider response format
```

Usage pattern:
```typescript
try {
  const result = await client.textGeneration({...});
} catch (error) {
  if (error instanceof InferenceClientProviderApiError) {
    console.error("Provider error:", error.message);
    console.error("Request:", error.request);
    console.error("Response:", error.response);
  } else if (error instanceof InferenceClientInputError) {
    console.error("Bad input:", error.message);
  } else if (error instanceof InferenceClientError) {
    console.error("HF inference error:", error);
  }
}
```

### Tree-Shaking Alternative

Instead of `new InferenceClient()`, import functions directly:
```typescript
import { textGeneration, chatCompletion } from "@huggingface/inference";

await textGeneration({
  accessToken: "hf_...",
  model: "gpt2",
  inputs: "Hello",
});
```

This enables bundlers to shake unused task functions from the final bundle — critical for browser/web apps.

### EndpointUrl Pattern

You can connect to any OpenAI-compatible local server:
```typescript
const client = new InferenceClient("no-token-needed", {
  endpointUrl: "http://localhost:8080/v1",
});
// Works with llama.cpp, vLLM, Ollama, TGI, LiteLLM
```

Or to a dedicated HF Inference Endpoint:
```typescript
const client = new InferenceClient("hf_...", {
  endpointUrl: "https://xyz.us-east-1.aws.endpoints.huggingface.cloud/llama-4-8b",
});
```

---

## 3. @huggingface/hub — Complete API Reference

### Version: 2.13.3

### All Exported Functions

**Repo CRUD:**
- `createRepo({ repo, accessToken, license? })` — also updates if exists
- `deleteRepo({ repo, accessToken })`
- `repoInfo({ name, type? })` — returns RepoEntry
- `modelInfo({ name })` — returns ModelEntry with config, metrics
- `spaceInfo({ name })` — returns SpaceEntry
- `datasetInfo({ name })` — returns DatasetEntry
- `checkRepoAccess({ repo, accessToken })` — verifies read/write access
- `whoAmI({ accessToken })` — returns { name, orgs, apps }

**Listing:**
- `listModels({ search?, owner?, sort?, direction?, limit? })` → AsyncIterable<ModelEntry>
- `listDatasets({ search?, owner?, limit? })` → AsyncIterable<DatasetEntry>
- `listSpaces({ search?, owner?, limit? })` → AsyncIterable<SpaceEntry>
- `listFiles({ repo, revision? })` → AsyncIterable<ListFileEntry>

**File Operations:**
- `uploadFiles({ repo, files, accessToken, revision? })` — batch upload
- `uploadFile({ repo, path, content, accessToken, revision? })` — single file
- `uploadFilesWithProgress({ repo, files, accessToken, revision? })` — streaming progress events
- `downloadFile({ repo, path, revision? })` → Response (streamable)
- `downloadFileToCacheDir({ repo, path, cacheDir })` — download with caching
- `snapshotDownload({ repo, revision?, cacheDir })` — full repo snapshot
- `deleteFile({ repo, path, accessToken })`
- `deleteFiles({ repo, paths, accessToken })`

**Advanced Operations:**
- `commit({ repo, operations, accessToken })` — multi-op atomic commit
  - Operations: CommitFile, CommitDeleteFile, CommitEditFile (prefix/suffix edits), CommitCopyFile
- `createBranch({ repo, branch, accessToken })` — even empty branches for clean uploads
- `copyFiles({ fromRepo, toRepo, files, accessToken })` — cross-repo file copy

**Cache:**
- `scanCacheDir({ cacheDir? })` → HFCacheInfo with CachedRepoInfo[]
- `downloadFileToCacheDir({ repo, path, cacheDir })` — cached download

**OAuth:**
- `oauthLoginUrl({ state, redirectUri })` → redirect URL for Sign in with HF
- `oauthHandleRedirectIfPresent()` → OAuthResult (token + user info)

**Auth Helpers:**
- `Credentials.fromAccessToken(token)` — create credentials object
- Various `AuthInfo` interfaces for token and OAuth

### Upload Patterns

The `uploadFiles` function accepts a versatile `files` array:

```typescript
await uploadFiles({
  repo: { type: "model", name: "myuser/my-model" },
  accessToken: "hf_...",
  files: [
    // 1. Inline content as Blob
    { path: "config.json", content: new Blob([JSON.stringify(config)]) },

    // 2. Local file via URL
    pathToFileURL("./pytorch_model.bin"),

    // 3. Entire directory via URL
    pathToFileURL("./tokenizer_files/"),

    // 4. Remote file by web URL
    new URL("https://huggingface.co/bert-base-uncased/resolve/main/tokenizer.json"),

    // 5. Remote with custom path
    { path: "myfile.bin", content: new URL("https://.../pytorch_model.bin") },

    // 6. Native File object (browser <input type="file">)
    // files[0] from <input type="file">
  ],
});
```

**Progress streaming:**
```typescript
for await (const event of await uploadFilesWithProgress({...})) {
  // event: { type: "progress" | "done", progress: number, ... }
  console.log(`Upload: ${event.progress}%`);
}
```

**Performance: Uploading large files is SHA-256 hashed inside a Worker** to avoid blocking the main thread. Lazy blob loading via URL objects avoids reading everything into memory.

### Commit with Edit Operations

```typescript
await commit({
  repo: { type: "model", name: "user/model" },
  accessToken: "hf_...",
  operations: [{
    type: "edit",
    originalContent: existingFile,
    edits: [{
      start: 0,
      end: 0,
      content: new Blob(["// added prefix\n"])
    }]
  }]
});
```

### CLI Tool

```bash
# Upload current directory
npx @huggingface/hub upload user/test-model .

# Upload with repo type
npx @huggingface/hub upload datasets/user/test-dataset .

# Create empty branch for clean history
npx @huggingface/hub branch create user/test-model release --empty

# Upload to specific revision
npx @huggingface/hub upload user/test-model . --revision release

# Global install for 'hfjs' command
npm install -g @huggingface/hub
hfjs upload user/test-model .
```

---

## 4. @huggingface/tiny-agents — Composable Agent Framework

### Version: 0.3.4

Tiny-agents is a **lightweight, MCP-powered agent framework** built on top of `@huggingface/inference`. Agents are defined declaratively as configuration (not code), shared on the Hub as datasets, and executed via CLI or programmatically.

### Agent Definition (agent.json)

Minimal:
```json
{
  "model": "Qwen/Qwen2.5-72B-Instruct",
  "provider": "novita",
  "servers": [
    {
      "type": "stdio",
      "command": "npx",
      "args": ["@playwright/mcp@latest"]
    }
  ]
}
```

With custom endpoint:
```json
{
  "model": "Qwen/Qwen3-32B",
  "endpointUrl": "http://localhost:1234/v1",
  "servers": [
    { "type": "stdio", "command": "npx", "args": ["@playwright/mcp@latest"] }
  ]
}
```

MCP server types supported:
- **stdio** — local subprocess
- **SSE** — Server-Sent Events over HTTP
- **HTTP** — direct HTTP MCP

Optional files:
- `PROMPT.md` or `AGENTS.md` — override the default system prompt
- `EXAMPLES.md` — sample prompts and use cases

### CLI Usage

```bash
# Run from Hub
npx @huggingface/tiny-agents run "julien-c/flux-schnell-generator"

# Run from local folder
npx @huggingface/tiny-agents run ./my-agent

# Serve as OpenAI-compatible HTTP server
npx @huggingface/tiny-agents serve "agent/id"
```

### Hub Collection

Agents are hosted at `https://huggingface.co/datasets/tiny-agents/tiny-agents`. Each agent is a subdirectory with `agent.json` and optional `PROMPT.md`. Community contributions via PR to that dataset repo.

### Programmatic Usage

```typescript
import { Agent } from '@huggingface/tiny-agents';

const agent = new Agent({
  provider: "auto",
  model: "Qwen/Qwen2.5-72B-Instruct",
  apiKey: "hf_...",
  servers: [
    {
      command: "npx",
      args: ["@playwright/mcp@latest"],
    },
  ],
});

await agent.loadTools();

// Stream responses
for await (const chunk of agent.run("What are the top 5 trending models?")) {
  if ("choices" in chunk) {
    const content = chunk.choices[0]?.delta?.content;
    if (content) console.log(content);
  }
}
```

### Architecture Insight

Tiny-agents is **not** a Python smolagents port. It's a fundamentally different approach:
- **smolagents** (Python): agents defined as code, tool calling via `@tool` decorators, Hugging Face Hub search as tool
- **tiny-agents** (JS): agents defined as JSON config, MCP servers as tools, shareable on Hub as datasets

This makes tiny-agents more portable (no code execution required to define an agent) and interoperable (MCP servers can be written in any language).

---

## 5. @huggingface/mcp-client

### Version: 0.2.3

A minimal MCP client built on top of `@huggingface/inference`. Includes a CLI agent that:
1. Connects to MCP servers (default: filesystem + Playwright)
2. Loads their tools
3. Uses the InferenceClient model to decide which tool to call
4. Returns structured responses

**Environment variables:**
- `HF_TOKEN` — inference auth
- `MODEL_ID` — model to use (default: `Qwen/Qwen2.5-72B-Instruct`)
- `PROVIDER` — inference provider (default: `together`)
- `ENDPOINT_URL` or `BASE_URL` — custom endpoint

```bash
cd packages/mcp-client
pnpm agent
```

---

## 6. @huggingface/gguf — Remote GGUF Parser

### Version: 0.4.3

Unlike Python GGUF readers that require local files, `@huggingface/gguf` works on **remotely hosted GGUF files** — it reads metadata directly from a URL without downloading the entire file (reads only header + KV metadata sections).

### Basic Usage

```typescript
import { GGMLQuantizationType, GGUFValueType, gguf } from "@huggingface/gguf";

const URL = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q2_K.gguf";

const { metadata, tensorInfos } = await gguf(URL);

console.log(metadata["general.architecture"]); // "llama"
console.log(tensorInfos[0]); // { name: "token_embd.weight", shape: [4096n, 32000n], dtype: GGMLQuantizationType.Q2_K }
```

### Typed Metadata

```typescript
const { typedMetadata } = await gguf(URL, { typedMetadata: true });

// Both value and its GGUF type
console.log(typedMetadata["general.architecture"].value);  // "llama"
console.log(typedMetadata["general.architecture"].type);   // GGUFValueType.STRING (8)
console.log(typedMetadata["llama.attention.head_count"].value); // 32
```

### Strict Typing by Architecture

Known metadata fields are **typed per architecture** — TypeScript knows that `llama.attention.head_count` is valid for llama models but `mamba.ssm.conv_kernel` is not:

```typescript
if (metadata["general.architecture"] === "llama") {
  console.log(metadata["llama.attention.head_count"]); // typed as number ✓
  console.log(metadata["mamba.ssm.conv_kernel"]);      // TypeScript error ✓
}
```

For custom/non-standard GGUF files, cast the output:
```typescript
const { metadata }: GGUFParseOutput<{ strict: false }> = await gguf(URL);
```

### Local File Support

```typescript
const { metadata } = await gguf('./my_model.gguf', { allowLocalFile: true });
// Not supported in browser environments
```

### CLI

```bash
# Online GGUF file (read-only, no download of entire file)
npx @huggingface/gguf https://huggingface.co/.../model.Q4_K_M.gguf

# Local file
npx @huggingface/gguf my_model.gguf

# Global install provides 'gguf-view'
npm i -g @huggingface/gguf
gguf-view my_model.gguf
```

---

## 7. Smaller Packages

### @huggingface/tasks (v0.21.28)
- **52KB on npm** — types-only, no runtime code
- Defines TypeScript types for: pipeline tasks (text-generation, text-to-image, etc.), model libraries (transformers, diffusers, etc.), dataset configs, metrics
- Used as typing dependency by `@huggingface/inference` and `@huggingface/hub`

### @huggingface/jinja (v0.5.9)
- Minimal JS Jinja templating engine
- Used for tokenizer `apply_chat_template()` in JS/Deno/Browser environments
- Single-file implementation, no external dependencies

### @huggingface/dduf (v0.0.2)
- Parser for DDUF (Diffusers Unified Format) files
- Very new (v0.0.2) — expect rapid development
- DDUF bundles model components (UNet, VAE, text encoder, scheduler config) into a single file

### @huggingface/ollama-utils (v0.0.18)
- Utilities for mapping Hub models to Ollama compatibility
- Creates Ollama Modelfile content, manages tags and manifests
- Bridges the gap between Hugging Face model repository and Ollama's format

### @huggingface/space-header (v1.0.4)
- Reusable Space `mini_header` web component
- Lets you embed the HF Spaces header/nav bar in non-HF-hosted apps
- Useful for white-label Spaces-like UIs

---

## 8. Performance & Browser Considerations

### Worker-based SHA-256 Hashing
When uploading large files, `@huggingface/hub` offloads SHA-256 computation to a **Web Worker** to avoid blocking the main thread. This is critical for browser-based uploads where blocking the UI degrades the user experience.

### Lazy Blob Loading
Files referenced as `URL` objects (local or remote) are not loaded into memory until the upload actually needs their bytes. This means:
- You can upload files larger than available RAM
- The entry array is cheap to construct (just URL references)
- The actually I/O happens in streaming chunks

### Bundle Size Optimization
- `@huggingface/tasks` at 52KB is types-only → tree-shaken to nothing at runtime
- Individual function imports (`import { textGeneration } from "@huggingface/inference"`) reduce bundle vs `new InferenceClient()`
- Avoid importing the entire `hub` package if you only need inference

### Environment Compatibility
- Node.js >= 18 (native fetch, Web Streams, Workers)
- Deno (native TypeScript support, URL imports)
- Bun (fast startup, Node compat)
- Modern browsers (Chrome, Firefox, Safari, Edge — all support ESM + Web Streams)
- No polyfills needed

---

## 9. OAuth Sign in with HF

The `@huggingface/hub` package provides OAuth integration for web apps:

```typescript
import { oauthLoginUrl, oauthHandleRedirectIfPresent } from "@huggingface/hub";

// Step 1: Get login URL
const url = oauthLoginUrl({
  state: crypto.randomUUID(),
  redirectUri: "https://myapp.com/callback",
});
// Redirect user to this URL

// Step 2: Handle callback (on redirect page)
const result = oauthHandleRedirectIfPresent();
if (result) {
  console.log("Logged in as:", result.userInfo.name);
  console.log("Access token:", result.accessToken);
  // Store token for subsequent @huggingface/inference and @huggingface/hub calls
}
```

This enables client-side web apps to authenticate users without a backend proxy.

---

## 10. Comparison: Python huggingface_hub vs JS @huggingface/*

| Capability | Python SDK | JS SDK |
|-----------|-----------|--------|
| **Package count** | 1 (huggingface_hub) | 10 (@huggingface/*) |
| **Inference client** | InferenceClient + InferenceEndpoint (separate) | Single InferenceClient (unified) |
| **Provider routing** | InferenceClient(provider=...) | InferenceClient with provider parameter |
| **Streaming** | Generator-based | Async iterable (for await...of) |
| **Cache scan** | scan_cache() returns dict | scanCacheDir() returns typed HFCacheInfo |
| **Snapshot download** | snapshot_download() | snapshotDownload() |
| **File upload** | upload_file(), upload_folder() | uploadFiles() with flexible content types |
| **Commit system** | create_commit() with CommitOperation | commit() with typed operations |
| **Agent library** | smolagents (Python code) | tiny-agents (JSON config + MCP) |
| **CLI** | huggingface-cli (many commands) | hfjs (upload + branch only), per-package CLIs |
| **GGUF reader** | llama.cpp Python binding | @huggingface/gguf (remote files!) |
| **Browser support** | Limited (not designed for browser) | First-class (ESM, Workers, OAuth) |
| **Error types** | HfHubHTTPError, etc. | 5-class InferenceClientError hierarchy |

---

## 11. Zero-Cost Pathways

- **@huggingface/inference**: Inference Providers have generous free tiers. No-cost for Prototype usage. Check per-provider limits.
- **@huggingface/hub**: All CRUD operations on public repos are free (rate-limited). File uploads count toward storage quota (free tier: ~5GB models, ~50GB datasets).
- **@huggingface/tiny-agents**: Free. Agents use Inference Providers under the hood.
- **@huggingface/gguf**: Free. Reads GGUF metadata from remote URLs without downloading the full file.
- **@huggingface/mcp-client**: Free. MCP servers are local processes.
- **OAuth**: Free for web apps.

**Paid features**: Dedicated Inference Endpoints, HF Storage Buckets beyond free tier.

---

## 12. Key Takeaways

1. **The JS SDK is not a port of the Python SDK** — it's a ground-up design optimized for browser, Deno, and ESM ecosystems. Modularity, tree-shaking, and modern JS patterns (async iterables, Workers, URL objects) are first-class.

2. **Single InferenceClient for all modes** — Whether serverless Provider, dedicated Endpoint, or local llama.cpp, the same class and same API methods work. This is cleaner than Python's split between `InferenceClient` and `InferenceEndpoint`.

3. **Remote GGUF parsing** — The ability to read GGUF metadata from a URL without downloading the full file is unique to the JS SDK. Python requires either the local file or the full download.

4. **Tiny Agents != smolagents** — Tiny Agents are configuration-based (JSON), shareable on Hub as datasets, and use MCP for tool integration. This is a fundamentally different, more portable approach than smolagents' code-as-agent paradigm.

5. **OAuth built-in** — First-class client-side OAuth for "Sign in with HF" means no backend needed for web app authentication.

6. **Error handling is granular** — 5 specific error types with `.request` and `.response` properties make debugging provider issues straightforward.

7. **Tree-shaking is intentional** — Individual function imports enable tiny bundle sizes for web apps. Not just a nice-to-have, but a design requirement.
