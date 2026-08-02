---
name: SakThai-hf-inference-providers-responses-api-deep-dive
version: 1.0.0
author: SakThai
license: MIT
category: mlops
---

# HF Inference Providers — Responses API & Remote MCP (Deep Dive)

## Overview
The **Responses API (beta)** is Hugging Face's unified OpenAI-compatible interface over Inference Providers, exposed at `https://router.huggingface.co/v1`. It provides a single endpoint for chat completion, tool calling, structured outputs, event-driven streaming, **Remote MCP tool execution**, and multi-provider routing — all billed through your HF account with free monthly credits ($0.10/mo for free users, $2/mo for PRO).

**Key differentiator:** The Responses API is the first HF offering that natively integrates Remote MCP servers as callable tools, letting models invoke server-hosted tools without you managing the MCP client infrastructure.

**Zero-cost:** Free monthly credits cover moderate usage (widgets, playground, API calls). No GPU or paid account needed. See `references/hf-learnings.md` for full architecture, routing strategies, MCP integration patterns, and provider comparison.

## Quick Start
```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.getenv("HF_TOKEN"),
)

response = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:groq",
    instructions="You are a helpful assistant.",
    input="Tell me a three-sentence bedtime story about a unicorn.",
)
print(response.output_text)
```

## Provider Routing
Append `:<provider>` or `:<policy>` to the model ID:
- `:fastest` — auto-picks lowest latency provider (default)
- `:cheapest` — lowest cost provider
- `:preferred` — follows your HF account's provider ordering
- Explicit — e.g. `:groq`, `:fireworks-ai`, `:together`, `:deepinfra`

## Key Features
| Feature | Pattern | Description |
|---------|---------|-------------|
| Plain text | `input="string"` | Single-turn response |
| Multimodal | `input=[{content: [input_text, input_image]}]` | Text + image input |
| Multi-turn | `input=[{role}, {role}]` | Full conversation history |
| Streaming | `stream=True` | Event-driven `response.*` events |
| Tool calling | `tools=[function_schemas]` | Model calls your functions |
| Structured outputs | `response_format=schema` | Guaranteed JSON compliance |
| Remote MCP | `tools=[{type:"mcp", server_url, allowed_tools}]` | Call server-hosted MCP tools |
| Reasoning effort | `reasoning={"effort": "low"\|"medium"\|"high"}` | Control reasoning depth |

## Remote MCP Integration
```python
response = client.responses.create(
    model="moonshotai/Kimi-K2-Instruct-0905:groq",
    input="how does tiktoken work?",
    tools=[{
        "type": "mcp",
        "server_label": "gitmcp",
        "server_url": "https://gitmcp.io/openai/tiktoken",
        "allowed_tools": ["search_tiktoken_documentation", "fetch_tiktoken_documentation"],
        "require_approval": "never",
    }],
)
```

## Multi-Provider Model Discovery
List models available via providers:
```bash
# All models served by any provider
curl -s https://router.huggingface.co/v1/models

# Filter by provider
curl -s https://huggingface.co/api/models?inference_provider=groq
curl -s https://huggingface.co/api/models?inference_provider=fireworks-ai

# Get model inference status
curl -s https://huggingface.co/api/models/google/gemma-3-27b-it?expand=inference
```
