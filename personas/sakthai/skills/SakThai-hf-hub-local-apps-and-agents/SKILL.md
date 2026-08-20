---
name: SakThai-hf-hub-local-apps-and-agents
author: SakThai
license: MIT
description: "Complete reference for running Hugging Face Hub models locally via Local Apps (llama.cpp, Ollama, Jan, LM Studio) and connecting local coding agents (Pi, OpenClaw, Hermes, OpenCode, llama-agent). Covers hardware profiling, the `-hf` flag architecture, cache management, zero-cost patterns, and troubleshooting."
version: 2.0.0
tags: [huggingface, hf, agents, local, llama.cpp, GGUF, coding-agent, Pi, OpenClaw, Hermes, OpenCode, llama-agent, Ollama, LM-Studio, Jan, local-apps]
related_skills:
  - hf-hub-hardware-profile
  - hf-gguf-llama-cpp
  - hf-hub-local-apps
  - hf-transformers-gguf-integration-v2
---

# HF Hub Local Apps & Agents

Run Hugging Face models on your own hardware with one-click commands from the Hub. This skill covers both **Local Apps** (the HF Hub ecosystem for local deployment) and **Local Agents** (coding agents that connect to local inference servers).

## Local Apps Ecosystem

The Hugging Face Hub provides **four supported local apps** for running models locally:

| App | Command | API Port | GPU | Best For |
|-----|---------|----------|-----|----------|
| **llama.cpp** | `llama-server -hf user/repo:quant` | `:8080` | Manual build flags | Performance, agents, shared HF cache |
| **Ollama** | `ollama run hf.co/user/repo:quant` | `:11434` | Auto-detected | Easy multi-model switching |
| **LM Studio** | GUI launch from HF model page | `:1234` | Auto-detected | GUI, developer tools |
| **Jan** | GUI launch from HF model page | `:1337` | Auto-detected | ChatGPT-like experience, RAG |

## Architecture

```
HF Hub Model Page → "Use this model" → llama.cpp/Ollama/Jan/LM Studio
                                               ↓
                                  Local Inference Server
                                  (OpenAI-compatible API)
                                               ↓
                                    Agent (Pi, Hermes, etc.)
```

## Key Features

- **Hardware Profiling**: `huggingface.co/settings/hardware` — set your GPU/RAM, HF tells you which models fit
- **Shared HF Cache**: llama.cpp `-hf` downloads go to `~/.cache/huggingface/hub/` — shared with transformers
- **One-click commands**: Model cards auto-generate `llama-server -hf ...` or `ollama run hf.co/...` commands
- **Zero-cost**: No cloud API bills — runs entirely on your hardware

## Quick Start

```bash
# 1. Configure hardware at huggingface.co/settings/hardware
# 2. Enable local apps at huggingface.co/settings/local-apps
# 3. Find a model with GGUF support
# 4. Copy the command from "Use this model" → llama.cpp

llama-server -hf ggml-org/gemma-3-1b-it-GGUF
# → OpenAI-compatible API at http://localhost:8080/v1
```

## Agent Integration

| Agent | Config File | Key Setting |
|-------|-------------|-------------|
| **Pi** | `~/.pi/agent/models.json` | `baseUrl: http://localhost:8080/v1` |
| **Hermes** | `~/.hermes/config.yaml` | `provider: custom`, `base_url: http://127.0.0.1:8080/v1` |
| **OpenCode** | `~/.config/opencode/opencode.json` | `baseURL: http://127.0.0.1:8080/v1` |
| **llama-agent** | CLI flags | `-hf user/repo:quant` (C++, zero deps) |
| **OpenClaw** | `openclaw onboard` | Select custom-api-key, point at `localhost:8080` |

See `references/hf-learnings.md` for the full deep-dive (~400 lines) covering:
- Hardware profiling architecture
- `-hf` flag internals (shared cache, auto-download, resume)
- Cross-app comparison matrix
- Agent framework comparison
- Zero-cost patterns for limited hardware
- Troubleshooting guide
- Building custom local apps
