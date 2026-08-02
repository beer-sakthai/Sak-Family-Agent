---
name: SakThai-hf-jobs-serving-vllm
author: SakThai
license: MIT
skill_type: reference
domain: hub
version: 1.0.0
created: 2026-07-25
updated: 2026-07-25
topic: hf-jobs-serving-vllm
category: mlops
---

# Run a vLLM Server on HF Jobs — One-Command Serving Patterns

## Description

Complete reference for running inference servers on Hugging Face **Jobs** — the one-command `hf jobs run` CLI pattern for deploying vLLM, llama.cpp, SGLang, and other OpenAI-compatible servers as ephemeral or persistent endpoints. Covers the full lifecycle: CLI invocation, port exposure, authentication, detach/cancel workflow, pricing, and cost-optimization strategies.

## When to Use

- You need a temporary OpenAI-compatible inference endpoint for testing, evaluation, or agent integration
- You want to serve a model without managing infrastructure, paying only for seconds used
- You need authenticated access to gated/private models via HF token forwarding
- You're building agent workflows that need ephemeral model endpoints
- You want to serve GGUF-quantized models with llama.cpp on CPU/GPU

## Key Resources

- `references/hf-learnings.md` — full research with CLI patterns, code examples, and pricing reference
- https://huggingface.co/docs/hub/en/jobs-serving — official docs
- https://huggingface.co/blog/vllm-jobs — announcement blog post
- https://huggingface.co/docs/hub/en/jobs-pricing — hardware pricing

## Related Skills

- `hf-jobs-api-deep-dive` — Python SDK for Jobs (complements CLI patterns here)
- `hf-vllm-integration-deep-dive` — vLLM integration with HF
- `hf-hub-gguf-llama-cpp` — GGUF models and llama.cpp
- `hf-jobs-complete-ecosystem-deep-dive` — broader Jobs ecosystem
