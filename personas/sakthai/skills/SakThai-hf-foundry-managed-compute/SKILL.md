---
name: SakThai-hf-foundry-managed-compute
author: SakThai
license: MIT
description: Comprehensive reference on Hugging Face models deployed through Microsoft Foundry Managed Compute — curated catalog, supported runtimes, deployment templates, SDK patterns, and enterprise security model.
version: 1.0.0
created: 2026-07-25
category: mlops
tags:
  - foundry
  - microsoft
  - managed-compute
  - enterprise
  - deployment
---

# HF Models on Foundry Managed Compute
**created:** 2026-07-25
**topic:** hf-foundry-managed-compute

## Purpose

Comprehensive reference on Hugging Face models deployed through Microsoft Foundry Managed Compute — a curated catalog of open-weight models from the Hugging Face ecosystem, refreshed weekly, deployable in one click onto Microsoft's managed GPU platform. Covers the curation pipeline, supported runtimes, deployment templates, SDK patterns, and enterprise security model.

## When to Use

- You need to deploy HF open-weight models on Microsoft Azure with enterprise security, governance, and observability
- You want a managed GPU platform that handles runtime updates, CVE patching, and GPU topology automatically
- You need a curated, license-screened, security-screened model catalog for production workloads
- You're building agentic applications on Foundry that need both frontier and open-weight models through a single endpoint

## Key Resources

- `references/hf-learnings.md` — complete deep-dive with curation pipeline, runtime details, deployment templates, SDK patterns
- Blog post: https://huggingface.co/blog/microsoft/foundry-managed-compute
- Microsoft Foundry: https://learn.microsoft.com/en-us/azure/ai-foundry/
- Foundry Managed Compute: https://learn.microsoft.com/en-us/azure/ai-foundry/managed-compute

## Related Skills

- `hf-hub-foundry-enterprise-deployment-curation` — HF Hub's own enterprise features
- `hf-inference-endpoints-custom-containers` — custom container deployment on HF Inference Endpoints
- `hf-hub-security-scanning-deep-dive` — security screening for models
- `hf-vllm-integration-deep-dive` — vLLM runtime (one of Foundry's supported runtimes)
