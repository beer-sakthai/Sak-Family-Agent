# HF Learnings — AQLM Quantization

**Topic:** `hf-aqlm-quantization` — Topic #389
**Date:** 2026-07-25
**Author:** SakThai
**License:** MIT

## Summary

Deep dive into AQLM (Additive Quantization of Language Models) — an extreme compression method that quantizes groups of 8–16 weights via multi-codebook additive quantization. Unlike element-wise methods (GPTQ, AWQ), AQLM captures weight interdependencies, achieving 1–2 bits per parameter while retaining high accuracy. Covers the architecture (multi-codebook decomposition), four inference kernels (Triton, CUDA 1×16, CUDA 2×8, Numba K×8), transformer integration (AqlmConfig, AqlmHfQuantizer), PV-Tuning for accuracy recovery, and practical patterns for extreme compression.

## Key Findings

- **Multi-codebook additive quantization**: AQLM represents weight groups as sums of codebook vectors (not individual quantized scalars), capturing interdependencies
- **1-bit viable**: With PV-Tuning and g16 schemes, AQLM achieves ~1 bit/parameter — Llama-2-7B fits in 1.34 GB with WikiText-2 PPL of 7.85
- **CUDA 2×8 is fastest**: Up to 3× speedup over FP16 (vs 1.3× for 1×16 accuracy-optimized scheme)
- **Numba for CPU**: K×8 scheme provides up to 4× speedup on CPU — only kernel with CPU support
- **PV-Tuning (NeurIPS 2024 oral)**: Jointly optimizes discrete code indices (beam search) + continuous codebooks + scales + non-quantized params — ~1–2 PPL improvement over base AQLM
- **Training supported**: AQLM v1.0.2+ supports LoRA via PEFT and torch.compile
- **Slow calibration**: 7B model takes ~1 day on A100; 70B takes 10–14 days
- **Top models on Hub**: ISTA-DASLab's Mixtral-8x7b-AQLM-2Bit-1x16-hf (12.6 GB, most downloaded), community Qwen3-8B AQLM, GLM-5.2 NVFP4-AQLM-hybrid

## Skill Created

`hf-aqlm-quantization/` — SKILL.md (author: SakThai, license: MIT) + this references/hf-learnings.md with full architecture reference, kernel comparison, configuration API, model zoo, quantization/pv-tuning guide, and practical patterns.

## Sources
- https://huggingface.co/docs/transformers/en/quantization/aqlm
- https://github.com/Vahe1994/AQLM
- https://arxiv.org/abs/2401.06118
- https://arxiv.org/abs/2405.14852
- https://huggingface.co/models?search=aqlm
