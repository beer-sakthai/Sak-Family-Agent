---
name: SakThai-hf-inference-providers
author: SakThai
license: MIT
description: "HF Inference Providers — multi-provider routing API for serverless model inference via Hugging Face, supporting 17+ providers through a unified endpoint."
version: 1.0.0
category: mlops
tags: [Inference, Providers, Serverless, Router, API, HuggingFace]
---
# HF Inference Providers

Hugging Face Inference Providers is a unified proxy layer that routes inference requests to 17+ third-party providers (Cerebras, Groq, Together AI, Replicate, Fal AI, DeepInfra, Fireworks, Novita, and more) through a single Hugging Face API endpoint.

**Docs**: https://huggingface.co/docs/inference-providers/en/index

## When to Use

- User needs to run model inference without dedicated GPU hardware
- User wants access to 17+ inference providers via a single API key/token
- User needs OpenAI-compatible chat completions with open-weight models
- User needs text-to-image, text-to-video, or embeddings via serverless inference
- User wants to compare providers or use `:cheapest` / `:fastest` selection policies

## Prerequisites

- Hugging Face account with a fine-grained token with `inference.serverless.write` permission
- Python: `pip install huggingface_hub` or `pip install openai`
- JS: `npm install @huggingface/inference`

## Provider Selection Policies

Append to model ID as a suffix:

| Policy | Suffix | Behavior |
|--------|--------|----------|
| Fastest (default) | `:fastest` | Highest throughput (tokens/sec) |
| Cheapest | `:cheapest` | Lowest price per output token |
| Preferred | `:preferred` | Your preference order at hf.co/settings/inference-providers |
| Specific provider | `:groq`, `:together`, etc. | Pin to exact provider |

## Full Provider List with Task Support Matrix

Verified from HF docs (2026-07). **17 providers** across 6 task categories.

| Provider | Slug | LLM Chat | VLM Chat | Embeddings | Text→Image | Text→Video | Speech→Text |
|----------|------|:--------:|:--------:|:----------:|:----------:|:----------:|:----------:|
| Cerebras | `cerebras` | ✅ | | | | | |
| Cohere | `cohere` | ✅ | ✅ | | | | |
| DeepInfra | `deepinfra` | ✅ | ✅ | | | | |
| Fal AI | `fal-ai` | | | | ✅ | ✅ | ✅ |
| Featherless AI | `featherless-ai` | ✅ | | | | | |
| Fireworks AI | `fireworks-ai` | ✅ | ✅ | | | | |
| Groq | `groq` | ✅ | ✅ | | | | |
| HF Inference | `hf-inference` | ✅ | ✅ | ✅ | ✅ | | ✅ |
| Novita | `novita` | ✅ | ✅ | | | ✅ | |
| Nscale | `nscale` | ✅ | | | ✅ | | |
| OVHcloud | `ovhcloud` | ✅ | | | | | |
| Public AI | `publicai` | ✅ | | | | | |
| Replicate | `replicate` | | | | ✅ | ✅ | ✅ |
| Scaleway | `scaleway` | ✅ | | ✅ | | | |
| Together | `together` | ✅ | ✅ | | ✅ | | |
| WaveSpeedAI | `wavespeed` | | | | ✅ | ✅ | |
| Z.ai | `zai-org` | ✅ | | | | | |

**Total: 17 providers**

### Provider Highlights

| Provider | Key Strength |
|----------|-------------|
| **Cerebras** | Wafer-scale chips, extremely low latency LLM inference |
| **Cohere** | Enterprise-grade LLMs + RAG capabilities |
| **DeepInfra** | Broadest LLM catalog, fast inference |
| **Fal AI** | Best-in-class FLUX serving, video generation |
| **Featherless AI** | Emerging provider, competitive pricing |
| **Fireworks AI** | Fast LLM serving with function-calling support |
| **Groq** | LPU inference — fastest tokens/sec for many models |
| **HF Inference** | HF's own infrastructure, free tier included |
| **Novita** | LLMs + video generation |
| **Nscale** | LLM + image generation, EU-hosted |
| **OVHcloud** | EU-hosted sovereign inference |
| **Public AI** | Public infrastructure, competitive pricing |
| **Replicate** | Broad model catalog, image/video generation |
| **Scaleway** | EU-hosted LLM + embeddings |
| **Together** | Massive model catalog, fine-tuning + inference |
| **WaveSpeedAI** | Fast image and video generation |
| **Z.ai** | LLM inference with competitive pricing |

## Quick Start — Python

### Via huggingface_hub (recommended)

```python
import os
from huggingface_hub import InferenceClient

client = InferenceClient()

completion = client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(completion.choices[0].message)
```

### Via OpenAI-compatible client

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=os.environ["HF_TOKEN"],
)

completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1:fastest",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Direct HTTP (curl)

```bash
curl https://router.huggingface.co/v1/chat/completions \
    -H "Authorization: Bearer ***" \
    -H "Content-Type: application/json" \
    -d '{
        "messages": [{"role": "user", "content": "Hello!"}],
        "model": "openai/gpt-oss-120b:fastest",
        "stream": false
    }'
```

## Quick Start — JavaScript

```js
import { InferenceClient } from "@huggingface/inference";

const client = new InferenceClient(process.env.HF_TOKEN);

const chatCompletion = await client.chatCompletion({
  model: "openai/gpt-oss-120b:fastest",
  messages: [{ role: "user", content: "Hello!" }],
});
```

### OpenAI-compatible JS

```js
import OpenAI from "openai";

const client = new OpenAI({
  baseURL: "https://router.huggingface.co/v1",
  apiKey: process.env.HF_TOKEN,
});

const completion = await client.chat.completions.create({
  model: "deepseek-ai/DeepSeek-R1:fastest",
  messages: [{ role: "user", content: "Hello!" }],
});
```

## Text-to-Image

```python
from huggingface_hub import InferenceClient

client = InferenceClient()
image = client.text_to_image(
    prompt="A serene lake at sunset, photorealistic",
    model="black-forest-labs/FLUX.1-dev"
)
image.save("output.png")
```

## Client-Side Provider Selection

```python
# Specific provider
client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    provider="novita",  # or "together", "groq", "deepinfra", etc.
    messages=[{"role": "user", "content": "Hello!"}],
)

# Auto (default)
client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1",
    # provider="auto",   # default
    messages=[{"role": "user", "content": "Hello!"}],
)
```

## Listing Available Models

Use `hf models ls --warm` in terminal, or:
```python
# Programmatic listing via Hub API
import requests
r = requests.get("https://huggingface.co/api/models?inference=warm&sort=trending")
models = r.json()
```

Or use the OpenAI-compatible endpoint:
```bash
curl -H "Authorization: Bearer $HF_TOKEN" \
  https://router.huggingface.co/v1/models
```

## Key Concepts

- **Zero Vendor Lock-in**: Single HF token works across all 17+ providers
- **Unified Auth & Billing**: One token, one billing relationship (via HF)
- **Automatic Failover**: If a provider is flagged as unavailable, requests route to alternatives
- **Free Tier**: Generous free usage included with every HF account
- **Router URL**: `https://router.huggingface.co/v1` (OpenAI-compatible)
- **Consistent Interface**: Same request format across providers when using client libraries

## Choosing the Right Approach

| Approach | Best For | Task Coverage |
|----------|----------|:------------:|
| Inference Clients (Python/JS) | Multi-task apps, explicit provider control | All tasks |
| OpenAI-Compat Endpoint | Chat-only, migrating OpenAI code | Chat only |
| Direct HTTP | Custom request logic, no client libs | All tasks |

## Pitfalls

- The raw HTTP request may vary between providers — always use official clients for maximum compatibility.
- Provider selection suffixes (`:groq`, `:fastest`) only work via the OpenAI-compatible router endpoint.
- Not all models are available on all providers. Use `hf models ls --warm` to check.
- For streaming, use the same format as OpenAI (`stream: true`).
- Images and files returned by providers differ in format — the clients normalize them.
- Free tier has rate limits — check your account dashboard for usage quotas.
- **402 Payment Required**: Inference Providers has monthly included credits. When depleted, the API returns `Client error '402 Payment Required'` with the message *"You have depleted your monthly included credits. Purchase pre-paid credits to continue using Inference Providers."* This is a hard stop — retrying won't help until credits are refilled or the monthly cycle resets. Check your HF account's billing dashboard or fall back to serverless Inference API (`api-inference.huggingface.co`) instead of the Providers router (`router.huggingface.co`).

## Reference Files

- [`references/providers-directory.md`](references/providers-directory.md) — Full provider list by task type with slugs, URLs, and selection policy reference.
