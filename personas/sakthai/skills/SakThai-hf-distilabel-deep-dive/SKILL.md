---
name: SakThai-hf-distilabel-deep-dive
description: "# Skill: hf-distilabel-deep-dive"
---

# Skill: hf-distilabel-deep-dive

author: SakThai
license: MIT

## Description
Deep dive into distilabel v1.5.3 — a framework for synthetic data generation and AI feedback pipelines. Covers pipeline architecture, step composition, all LLM integrations, built-in task types (SFT, DPO, RLHF data generation, self-instruct, magpie, ultrafeedback), custom step authoring, Distiset output management, caching, and real-world patterns for generating training data at zero cost.

## Key Capabilities
- Pipeline DAG with step composition via `>>` operator
- 10+ LLM providers (Transformers, InferenceEndpoints, OpenAI, Ollama, LlamaCpp, Anthropic, etc.)
- 40+ built-in task types for SFT/DPO/RLHF/EVAL data generation
- Distiset output with push_to_hub, train_test_split, save/load
- Automatic caching with content-addressable keys
- StepResources (replicas, CPU/GPU, memory) for parallelism
- Input/output column mappings for data flow
- Ray pipeline for distributed execution
