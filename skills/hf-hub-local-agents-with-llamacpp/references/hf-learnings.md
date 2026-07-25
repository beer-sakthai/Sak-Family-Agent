# HF Learnings — Local Agents with llama.cpp

## 2026-07-25: hf-hub-local-agents-with-llamacpp — Hugging Face Hub Local Agents with llama.cpp (Topic #324)

### Summary
Deep dive into the HF Hub's "Local Agents with llama.cpp" documentation. The Hub now provides a complete workflow for connecting local coding agents to GGUF models via llama.cpp server. Covers Pi, OpenClaw, Hermes Agent, OpenCode, and llama.cpp's native agent binary (llama-agent). The key innovation is the hardware profiling system at `huggingface.co/settings/hardware` that tells you which models fit your local GPU/RAM, then provides one-click `llama-server -hf ...` commands to download and serve any GGUF model.

### Key Findings

| Aspect | Detail |
|--------|--------|
| **Architecture** | Two components: llama.cpp server (OpenAI-compatible API on localhost:8080) + agent process that sends prompts and executes tool calls |
| **Hardware setup** | Configure at huggingface.co/settings/hardware — sets hardware profile for model compatibility |
| **Model discovery** | "Use this model" → llama.cpp → exact server command with HF autodownload via `-hf` flag |
| **Pi agent** | `npm install -g @mariozechner/pi-coding-agent` + configure `~/.pi/agent/models.json` with llama-cpp provider |
| **Vision in Pi** | Add `"input": ["text", "image"]` to model entry for vision-capable GGUF models |
| **OpenClaw** | `openclaw onboard` with custom-api-key, custom-base-url pointing at localhost:8080 |
| **OpenClaw local memory** | Uses `node-llama-cpp` to serve EmbeddingGemma-300M locally for semantic search |
| **Hermes Agent** | Config in `~/.hermes/config.yaml` with custom provider, plus `session_search` for local embeddings |
| **OpenCode** | JSON config at `~/.config/opencode/opencode.json` with llama.cpp provider block |
| **llama-agent** | C++ binary built from source — zero deps, tool calls happen in-process (no HTTP overhead), supports subagents, MCP, HTTP API server mode |
| **Auth** | No API key needed for local: `api_key: "llama.cpp"` or `"no-key-required"` or `"none"` |
| **Memory search** | Separate embedding model served on same llama.cpp endpoint or via node-llama-cpp |

### Agent Configuration Reference

**Pi** (`~/.pi/agent/models.json`):
```json
{
  "providers": {
    "llama-cpp": {
      "baseUrl": "http://localhost:8080/v1",
      "api": "openai-completions",
      "apiKey": "none",
      "models": [
        { "id": "ggml-org-gemma-4-26b-4b-gguf" }
      ]
    }
  }
}
```

**Hermes Agent** (`~/.hermes/config.yaml`):
```yaml
model:
  provider: custom
  default: ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M
  base_url: http://127.0.0.1:8080/v1
  api_key: llama.cpp
custom_providers:
  - name: Local (127.0.0.1:8080)
    base_url: http://127.0.0.1:8080/v1
    api_key: llama.cpp
    model: ggml-org/gemma-4-26B-A4B-it-GGUF:Q4_K_M
```

**OpenCode** (`~/.config/opencode/opencode.json`):
```json
{
  "provider": {
    "llama.cpp": {
      "npm": "@ai-sdk/openai-compatible",
      "name": "llama-server (local)",
      "options": {
        "baseURL": "http://127.0.0.1:8080/v1"
      },
      "models": {
        "gemma-4-26b-4b-it": {
          "name": "Gemma 4 (local)",
          "limit": { "context": 128000, "output": 8192 }
        }
      }
    }
  }
}
```

### llama-agent Binary
Unique in the ecosystem: builds agent loop directly into llama.cpp as a single binary:
```
git clone https://github.com/gary149/llama-agent.git
cd llama-agent
cmake -B build
cmake --build build --target llama-agent
./build/bin/llama-agent -hf ggml-org/gemma-4-26b-a4b-it-GGUF:Q4_K_M
```
No Node.js, no Python. Tool calls are in-process (no HTTP network overhead between model and agent). Supports subagents, MCP servers, and HTTP API server mode.

### OpenClaw Local Memory Setup
```bash
npm i node-llama-cpp
openclaw config set agents.defaults.memorySearch.provider local
openclaw config set agents.defaults.memorySearch.local.modelPath \
  "hf:ggml-org/embeddinggemma-300m-qat-q8_0-GGUF/embeddinggemma-300m-qat-Q8_0.gguf"
openclaw gateway restart
openclaw memory status
```

### Hermes Agent Local Memory Setup (`~/.hermes/config.yaml`):
```yaml
auxiliary:
  session_search:
    base_url: "http://127.0.0.1:8080/v1"
    api_key: "no-key-required"
    model: "local-llama"
    timeout: 90
    max_concurrency: 1
```

### Sources
- https://huggingface.co/docs/hub/en/agents-local
- https://huggingface.co/docs/hub/en/agents
- https://huggingface.co/settings/hardware

### Skill Created
`hf-hub-local-agents-with-llamacpp/` — comprehensive reference covering 5 local agent frameworks with exact config files for each, architecture deep-dive, and local memory search patterns.
