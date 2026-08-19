---
name: SakThai-hf-inference-client-serverless-inference-patterns
description: "Complete reference on Hugging Face Inference Providers serverless inference patterns\
  \ \u2014 the Routes API, OpenAI-compatible endpoint, provider selection policies,\
  \ structured outputs, function calling, streaming, pricing tiers, and zero-cost\
  \ strategies. "
---

# HF Inference Providers — Serverless Inference Patterns

Comprehensive reference on serverless inference through Hugging Face's Inference Providers system: a unified proxy layer that routes requests to 18+ AI providers. Covers the modern **Responses API (beta)**, the OpenAI-compatible chat completions endpoint, provider selection policies, structured outputs, function calling, streaming, pricing, and zero-cost strategies.

## Key Topics

| Topic | Description |
|-------|-------------|
| **Responses API** | New unified interface with event streaming, tools, MCP support |
| **OpenAI-Compatible Endpoint** | `router.huggingface.co/v1` — drop-in replacement for OpenAI SDK |
| **Provider Selection** | `:fastest`, `:cheapest`, `:preferred` policies or explicit providers |
| **Structured Outputs** | Guaranteed JSON Schema compliance via `text.format` |
| **Function Calling** | OpenAI-compatible function/tool calling with `tool_choice` control |
| **Streaming** | Server-Sent Events via `stream: true` |
| **Pricing** | Free tier ($0.10/mo), PRO ($2.00/mo), Custom Provider Key option |
| **Zero-Cost Strategies** | Free models, credit conservation, caching patterns |

See `references/hf-learnings.md` for the complete research document.
