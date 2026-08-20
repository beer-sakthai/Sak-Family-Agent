---
name: SakThai-hf-text-embeddings-inference
description: "Hugging Face Text Embeddings Inference (TEI) \u2014 high-performance Rust-based inference\
  \ server for deploying, serving, and consuming embedding models via Docker, gRPC,\
  \ and the Hugging Face Hub."
---

# HF Text Embeddings Inference (TEI)

## Purpose
Deep knowledge of Hugging Face Text Embeddings Inference — deploying, serving, and consuming embedding models via TEI's high-performance Rust-based inference server.

## Covers
- TEI architecture (Rust, Candle, Flash Attention, Safetensors)
- Docker deployment (CPU, CUDA, ROCm, Metal)
- Supported model architectures (BERT, NomicBERT, JinaBERT, XLM-RoBERTa, GTE, Qwen2/3, Mistral, MPNet, ModernBERT, Gemma3)
- API endpoints (`/embed`, `/embed_sparse`, `/embed_sentence`, `/rerank`, `/predict`)
- CLI arguments reference
- Pooling strategies (CLS, mean, last-token, SPLADE)
- Private/gated model serving
- gRPC API
- InferenceClient integration (`feature_extraction`, `sentence_similarity`)
- Re-rankers and sequence classification support
- Distributed tracing and Prometheus metrics
- Zero-cost strategies (CPU-only, serverless inference fallback)
