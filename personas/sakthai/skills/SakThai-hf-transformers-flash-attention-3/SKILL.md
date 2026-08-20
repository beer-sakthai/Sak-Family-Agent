---
name: SakThai-hf-transformers-flash-attention-3
description: ">-   FlashAttention-3 integration in Hugging Face Transformers \u2014 attention \
  \  backend architecture, FA3/FA4 kernel system, Kernels Hub, paged attention,  \
  \ backbone-specific dispatch, and runtime switching."
---

# FlashAttention-3 in Hugging Face Transformers

## Overview

FlashAttention-3 is the latest generation of the FlashAttention family,
optimized for Hopper GPUs (H100/H800). It improves on FlashAttention-2 by
overlapping operations and fusing forward/backward passes more tightly.
Transformers v5.14+ integrates FA3 as a first-class attention backend through
the AttentionInterface abstraction, alongside FA2, SDPA, FlexAttention, and
paged variants.

## Key Concepts

- **AttentionInterface**: Decouples attention implementation from model code
- **8 registered backends**: flash_attention_3, flash_attention_2, flex_attention,
  sdpa, paged|flash_attention_3, paged|flash_attention_2, paged|sdpa, paged|eager
- **Kernels Hub**: Pre-compiled kernels served from Hugging Face, no manual install
- **Backbone-specific dispatch**: Different backends per modality in multimodal models
- **Runtime switching**: Change attention backend without reloading
