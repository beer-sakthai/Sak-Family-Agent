---
name: SakThai-hf-inference-client-openai
author: SakThai
license: MIT
description: "Deep reference on HF InferenceClient's OpenAI API compatibility — chat.completions.create, structured outputs (JSON Schema / regex), function calling, and streaming."
version: 1.0.0
category: mlops
tags: [huggingface, inference, client, openai, compatibility, structured-outputs, function-calling, json-schema, streaming]
platforms: [linux, macos, windows]
---

# HF Inference Client — OpenAI Compatibility & Structured Outputs

Deep reference on Hugging Face's `InferenceClient` and its OpenAI-compatible API surface — `client.chat.completions.create()`, structured outputs via `response_format` (JSON Schema / regex grammar), function calling, streaming, and the full parameter set.

## Capabilities

- Use `InferenceClient` as a drop-in OpenAI client replacement (change 2 lines of code)
- Enable structured outputs with `response_format={"type": "json_schema", "json_schema": {...}}`
- Use JSON mode for syntactically valid JSON without schema enforcement
- Call functions/tools via OpenAI-compatible `tools` and `tool_choice` parameters
- Stream responses token-by-token with `stream=True`
- Access all standard parameters: `temperature`, `top_p`, `max_tokens`, `stop`, `seed`, `logprobs`, `frequency_penalty`, `presence_penalty`
- Pass provider-specific parameters via `extra_body`
- Support all 17+ inference providers from a single unified API

## Key Files

| File | Purpose |
|------|---------|
| `SKILL.md` | This file — skill definition |
| `references/hf-learnings.md` | Learning log with deep-dive concepts |
