---
name: hf-hub-local-agents-with-llamacpp
author: SakThai
license: MIT
description: "Running local coding agents (Pi, OpenClaw, Hermes, OpenCode, llama-agent) with llama.cpp server backend using HF Hub models."
version: 1.0.0
tags: [huggingface, hf, agents, local, llama.cpp, GGUF, coding-agent, Pi, OpenClaw, Hermes, OpenCode, llama-agent]
---

# HF Hub Local Agents with llama.cpp

Run coding agents entirely on your own hardware using llama.cpp as the model server. The Hugging Face Hub provides the model discovery, hardware profiling, and one-click llama.cpp commands to bridge HF GGUF models with local agent frameworks.

## When to Use

- You want a Claude Code / Codex-like experience running locally with no cloud costs
- You need fully private, air-gapped coding agent workflows
- You want to experiment with different GGUF quants of models like Gemma, Qwen, Llama on your own hardware
- You're building agent toolchains that need local inference

## Supported Agent Frameworks

| Agent | Setup Mechanism | Config File |
|-------|----------------|-------------|
| **Pi** | `~/.pi/agent/models.json` | npm package, direct llama.cpp integration |
| **OpenClaw** | `openclaw onboard` CLI | Built-in CLI wizard |
| **Hermes Agent** | `~/.hermes/config.yaml` | YAML config with custom provider |
| **OpenCode** | `~/.config/opencode/opencode.json` | JSON provider config |
| **llama-agent** | C++ binary, no deps | CLI flags + cmake build |

## Architecture

```
┌─────────┐     OpenAI-compatible API     ┌──────────────────┐
│  Agent  │ ───────────────────────────▶  │  llama.cpp server │
│  (Pi,   │ ◀───────────────────────────  │  (local model)    │
│  Hermes,│      responses + tool calls    │  GGUF format     │
│  etc.)  │                                └──────────────────┘
     │
     ▼
  Your files,
  terminal, IDE
```

## Steps to Run

1. **Configure hardware**: Visit `huggingface.co/settings/hardware` and set your local hardware profile
2. **Select llama.cpp**: Enable llama.cpp as your inference engine in Local Apps settings
3. **Find a model**: Browse/buy llama.cpp-compatible GGUF models on HF
4. **Launch server**: `llama-server -hf ggml-org/gemma-4-26b-a4b-it-GGUF:Q4_K_M`
5. **Connect agent**: Configure agent to point at `http://localhost:8080/v1`

## Local Memory Search

Both Hermes Agent and OpenClaw support local embedding models for memory/semantic search via llama.cpp:

- Hermes: `session_search` in `~/.hermes/config.yaml` points at same local server
- OpenClaw: Uses `node-llama-cpp` to run `EmbeddingGemma-300M` locally

## Key Concepts

| Concept | Detail |
|---------|--------|
| **llama.cpp server** | OpenAI-compatible API server running GGUF models locally |
| **Hardware profiling** | HF settings page tells you which models fit your GPU/RAM |
| **Model autodownload** | `-hf` flag downloads GGUF model from HF automatically |
| **Vision support** | Pi supports vision by adding `"input": ["text", "image"]` to model config |
| **llama-agent** | All-in-one binary: agent loop built directly into llama.cpp — no Node/Python deps |

## Related Topics

- HF CLI Agent Mode
- HF MCP Server integration
- HF Agent Skills
- GGUF model quantization and selection
- Local Apps on HF Hub
