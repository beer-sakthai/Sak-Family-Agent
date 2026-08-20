---
name: SakThai-hf-hub-model-dependents
author: SakThai
license: MIT
description: "A skill for Hf Hub Model Dependents."
version: 0.1.0
---

# HF Hub Model Dependents API

author: SakThai
license: MIT
type: mlops
tags: huggingface-hub, api, models, dependents, children, discovery

## Purpose
Reference skill for discovering and navigating model dependency relationships on the Hugging Face Hub — including children counts, base model declarations, and dependents filtering.

## Key Capabilities
- Query children count breakdown (finetune/quantized/adapter/merge) via `expand[]=childrenModelCount`
- Discover parent model relationship via `expand[]=baseModels`
- List all children models via `filter=base_model:org/model` on `list_models()`
- Enumerate Spaces using a model via `expand[]=spaces`

## Dependencies
- `huggingface_hub >= 0.24.0`
- HF Hub REST API access

## References
See `references/hf-learnings.md` for full API reference with code examples.
