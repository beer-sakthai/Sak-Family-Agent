---
name: SakThai-model-routing-agent-systems-deep-dive
author: SakThai
license: MIT
skill_type: reference
domain: inference
version: 1.0.0
created: 2026-07-25
updated: 2026-07-25
category: mlops
---

# Model Routing for Agentic Systems — Deep Dive

## Description

Complete reference on model routing strategies for agentic systems, synthesizing practical lessons from production deployments. Covers why naive routing (classification-based difficulty estimation) fails, how caching effects dominate real cost, the latency iceberg beyond model speed, and how IBM Research built an optimization-based router that explores cost-accuracy frontiers. Includes agent architecture patterns (soul/skills/config) from Shippy/Ai2 with their planned routing implementation. Relevant to anyone building multi-model agent systems on Hugging Face Inference Providers, Anthropic, or OpenAI.

## Files

- `references/hf-learnings.md` — Full research with architecture, cost-accuracy frontiers, caching economics, and agent routing systems

## Related Skills

- `hf-inference-providers-comprehensive-architecture` — Inference Providers ecosystem
- `hf-inference-client-provider-fallback-and-routing` — Client-side provider routing
- `hf-inference-providers-multi-provider-routing` — Multi-provider routing strategies
- `hf-inference-providers-pricing-billing-hub-api-deep-dive` — Provider pricing
- `hf-smolagents-deep-dive-v2` — Agent framework knowledge
