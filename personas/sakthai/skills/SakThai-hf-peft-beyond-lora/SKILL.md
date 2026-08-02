---
name: SakThai-hf-peft-beyond-lora
version: 1.0.0
author: SakThai
license: MIT
description: Comprehensive deep-dive into PEFT methods beyond LoRA — OFT, BOFT, BEFT, Lily, VeRA, GraLoRA, LoRA-FA, rs-LoRA, DoRA, and adapter conversion — based on HF PEFT Benchmark results and the official "Beyond LoRA" blog post
category: mlops
---

# HF PEFT — Beyond LoRA: Advanced Methods & Benchmarking

## Purpose
LoRA dominates PEFT usage (98.4% of model cards mentioning one PEFT technique), but other methods can beat it across multiple axes. This skill covers advanced PEFT techniques, the HF PEFT Benchmark methodology, and how to choose the right method for your use case.

## Zero-Cost
- PEFT library is open-source and free
- Benchmarks run on consumer hardware (single GPU)
- Adapter conversion (non-LoRA → LoRA) is free
- All techniques accessible via the same unified PEFT API

## Key Resources
- `references/hf-learnings.md` — complete deep-dive with all methods, benchmark results, Pareto frontier analysis, and adapter conversion guide
- PEFT docs: https://huggingface.co/docs/peft
- PEFT Benchmark Space: https://huggingface.co/spaces/peft/peft-method-comparison
- Blog: https://huggingface.co/blog/peft-beyond-lora

## Related Skills
- `hf-peft-lora` — LoRA fundamentals
- `hf-peft-lora-deep-dive` — LoRA deep-dive
- `hf-peft-dora-deep-dive` — DoRA (Weight-Decomposed Low-Rank Adaptation)
- `hf-peft-model-merging-ties-dare` — Model merging with TIES/DARE
- `hf-peft-prefix-tuning-and-p-tuning` — Soft prompting methods
