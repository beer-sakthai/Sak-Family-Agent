---
name: SakThai-hf-inference-router-openai-compatible-endpoint
description: "Comprehensive deep-dive into Hugging Face Inference Router — OpenAI-compatible proxy endpoint with provider selection, auto-failover, Responses API, structured outputs, function calling, and MCP integration."
---

# HF Inference Router: OpenAI-Compatible Endpoint

## Description

Comprehensive deep-dive into Hugging Face's Inference Router — the OpenAI-compatible proxy endpoint at `https://router.huggingface.co/v1` that provides server-side provider selection, auto-failover, and unified access to hundreds of models across 18+ inference providers through a single OpenAI SDK-compatible API. Includes practical patterns for Responses API (beta), structured outputs, function calling, Remote MCP integration, and zero-cost usage strategies.

## Topics Covered

### Architecture & API Surface (Topic #361)
- Router architecture and proxy model
- Provider selection policies (`:fastest`, `:cheapest`, `:preferred`, explicit provider)
- `/v1/models` endpoint — listing available models with provider metadata
- Authentication and token permissions
- Integration patterns (Python, JavaScript, cURL)
- Auto-failover behavior
- Comparison with Hugging Face InferenceClient
- Limitations (chat completions only)

### Practical Patterns Deep-Dive (Topic #363 — new)
- **Responses API (beta)** — unified event-driven interface with streaming, reasoning controls, MCP tools
- **Structured outputs** — Pydantic/JSON Schema via both `chat.completions` and `responses` APIs
- **Function calling** — execution patterns with tool_choice control, tool call lifecycle
- **Remote MCP integration** — server-hosted tools through the Responses API
- **Pricing & billing** — free tier ($0.10/mo), Custom Provider Key, Organization billing
- **Provider ecosystem** — 18-provider capability matrix (chat, image, video, audio support)
- **Zero-cost patterns** — free provider routing, credit conservation, Groq free tier
- **Agent integrations** — OpenCode, Pi, Codex, Claude Code, Hermes Agent

## Key Resources

- Official docs: https://huggingface.co/docs/inference-providers/en/index
- Responses API: https://huggingface.co/docs/inference-providers/en/guides/responses-api
- Structured outputs: https://huggingface.co/docs/inference-providers/en/guides/structured-output
- Function calling: https://huggingface.co/docs/inference-providers/en/guides/function-calling
- Pricing: https://huggingface.co/docs/inference-providers/en/pricing
- Provider settings: https://hf.co/settings/inference-providers
- Router endpoint: `https://router.huggingface.co/v1`

## Files

- `references/hf-learnings.md` — Full research with architecture, API reference, provider selection policies, integration examples, comparison matrix, and practical patterns deep-dive
