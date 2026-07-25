# HF Learnings: huggingface.js SDK

**Date:** 2026-07-25  
**Topic:** `hf-hub-js-sdk`  
**Author:** SakThai  
**Source:** Official docs at https://huggingface.co/docs/huggingface.js

## What I Learned

### The huggingface.js Monorepo

The Hugging Face JS libraries are published as 10 packages from a single monorepo at `github.com/huggingface/huggingface.js`. They form the official TypeScript/JavaScript SDK for interacting with the Hugging Face Hub and its ML models.

### Architecture

Unlike the Python `huggingface_hub` library which is one monolithic package, the JS SDK is intentionally modular — each concern is its own tiny npm package. This keeps bundle sizes small for browser usage and enables tree-shaking.

### Key Insight: Three-Tier Inference

The `@huggingface/inference` package abstracts three deployment models behind one `InferenceClient` class:
1. **Serverless Providers** (18+ partners via HF router) — free tier available
2. **Inference Endpoints** (dedicated, paid) — pass `endpointUrl` to constructor
3. **Local endpoints** (llama.cpp, Ollama, vLLM, TGI) — pass local URL as `endpointUrl`

This is cleaner than Python's `InferenceClient` vs `InferenceEndpoint` split.

### Provider Ecosystem (18 partners)

The provider system uses HF as a router by default (when using a HF token), or direct API calls (when using a third-party API key). The `provider` parameter controls routing. The partner list is growing and can be queried at `hf.co/api/partners/{provider}/models`.

### CLI Tools

Two packages ship CLI tools:
- `@huggingface/hub` → `npx @huggingface/hub upload` or global `hfjs` command
- `@huggingface/gguf` → `npx @huggingface/gguf` or global `gguf-view`

The `@huggingface/tiny-agents` package can also serve agents as OpenAI-compatible HTTP servers.

### Tiny Agents Pattern

A novel "agent as configuration" pattern: agents are defined declaratively in `agent.json` (model + MCP servers) and optionally hosted on the Hub as a dataset. This is distinct from smolagents (Python) — tiny-agents is JS-native, uses MCP for tools, and targets browser/CLI environments.

### Missing Documentation Areas

The `@huggingface/tasks` package at 52K bytes is mostly type definitions (no runtime code). The `@huggingface/dduf` package at v0.0.2 is very new. Documentation is sparse for `@huggingface/ollama-utils` and `@huggingface/space-header`.

### Versions (as of 2026-07-25)

| Package | Version | Published |
|---------|---------|-----------|
| inference | 4.13.23 | latest |
| hub | 2.13.3 | latest |
| gguf | 0.4.3 | latest |
| mcp-client | 0.2.3 | latest |
| tiny-agents | 0.3.4 | latest |
| tasks | 0.21.28 | latest |
| jinja | 0.5.9 | latest |
| dduf | 0.0.2 | latest |
| ollama-utils | 0.0.18 | latest |
| space-header | 1.0.4 | latest |

### How This Differs from Python SDK

| Aspect | Python (`huggingface_hub`) | JS (`@huggingface/*`) |
|--------|---------------------------|----------------------|
| Package style | Monolithic | Modular (10 packages) |
| Inference client | `InferenceClient` + `InferenceEndpoint` | Single `InferenceClient` |
| Cache management | Full `scan_cache`, `snapshot_download` | Basic `scanCacheDir`, `snapshotDownload` |
| Async | Synchronous + `asyncio` variants | All async (Promises) |
| Auth | Token, OAuth, App authentication | Token, OAuth (Sign in with HF) |
| Agent library | `smolagents` (Python-native) | `tiny-agents` (MCP-based, JS) |
| CLI | `huggingface-cli` | Per-package CLIs + global `hfjs` |
