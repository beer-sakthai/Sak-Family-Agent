---
name: SakThai-hf-gemma3-deep-dive
description: "name: SakThai-hf-gemma3-deep-dive"
---

# Gemma 3 on Hugging Face — Architecture & Inference Deep Dive

## Description

Complete reference for Google's **Gemma 3** family of open multimodal models on Hugging Face. Covers all four sizes (1B, 4B, 12B, 27B), architecture (Deep Gemma text backbone + SigLIP vision encoder, GQA, RoPE scaling, sliding window attention), 128K context, multilingual support (140+ languages), TGI/Inference API usage, GGUF quantization for local deployment, and function calling patterns via Transformers tool-use framework. Based on official model cards, config analysis, and HF Hub API data.

## Files

- `references/hf-learnings.md` — Full research with architecture details, model comparison, inference patterns, and usage code

## Related Skills

- `hf-transformers-5-architecture-deep-dive-v2` — Transformers 5 model registration
- `hf-transformers-pipeline-api` — Pipeline API usage patterns
- `hf-inference-client-chat-completion-deep-dive-v3` — Chat completion with InferenceClient
- `hf-gguf-llama-cpp` — GGUF format for local inference
- `hf-hub-local-agents-with-llamacpp` — Local agent setup with llama.cpp
- `hf-inference-providers-comprehensive-architecture` — Inference Providers for free-tier usage
- `hf-transformers-kv-cache-architecture` — KV-cache for generation
- `hf-transformers-rope-scaling` — RoPE scaling techniques
