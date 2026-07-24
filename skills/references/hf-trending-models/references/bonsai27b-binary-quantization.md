# Bonsai 27B — Binary (1-bit) Quantization Architecture

_Reference extracted from `prism-ml/Bonsai-27B-gguf` (base: Qwen/Qwen3.6-27B). Companion to `prism-ml/Ternary-Bonsai-27B-gguf` (1.71 bpw ternary variant)._

## What Makes Bonsai Different

Bonsai is not a conventional low-bit quantisation of Qwen3.6-27B. It is an **end-to-end binary language model**: every weight in embeddings, attention projections, MLP projections, and the LM head is stored as a single sign bit (`{−1, +1}`) with FP16 group-wise scaling. There are no high-precision escape hatches behind a low-bit label. The vision tower (optional, for multimodal input) ships separately in 4-bit HQQ via the mmproj GGUF file.

**True bit-width: 1.125 bits per weight** (1 sign bit + 16-bit scale amortised over 128 weights). This is not the same as "2-bit" quantisation (which is typically 2.8 bpw in practice — see IQ2_XXS on Qwen3.6-27B at 9.4 GB). The Bonsai label matches reality: the "1-bit" name is the actual representation.

## Weight Format: Q1_0_g128

```
Format string: Q = quantised, 1 = 1 bit, 0 = unsigned, g128 = group size 128
```

Each weight is stored as a single bit:
- `0` → decode as `−scale`
- `1` → decode as `+scale`

Every group of 128 weights shares one FP16 scale factor. On decode:
```
weight_i = (bit_i ? 1.0 : -1.0) * scale_group
```

The GGUF pack is the *native* layout — deployed and ideal sizes match (~3.9 GB). No expansion back to FP16 during inference.

### Memory Envelope

| Context | Weights | +KV (FP16) | +KV (4-bit) |
|---------|---------|-------------|-------------|
| 4K      | 3.79 GB | 5.2 GB      | ~4.2 GB     |
| 100K    | 3.79 GB | 11.6 GB     | ~6.8 GB     |
| 262K    | 3.79 GB | ~20 GB      | ~9.4 GB     |

The full 262K window fits in ~9.4 GB with 4-bit KV cache — below what a single 12 GB GPU can hold, or 16 GB unified memory on Apple Silicon.

## Intelligence Density Metric

Bonsai introduces a reusable metric for comparing model efficiency:

```
D = -log₂(1 - score/100) / size_GB
```

Where *score* is a benchmark average and *size_GB* is the deployed footprint (weights only). Higher = more capability per gigabyte.

| Model | Size | Avg | Density |
|-------|------|-----|---------|
| **1-bit Bonsai 27B** | 3.9 GB | 76.11 | **0.530** |
| Ternary Bonsai 27B | 5.9 GB | 80.49 | 0.400 |
| Qwen3.6-27B IQ2_XXS | 9.4 GB | 72.73 | 0.199 |
| Qwen3.6-27B Q4_K_XL | 17.6 GB | 84.99 | 0.155 |

The 1-bit Bonsai delivers ~2.7× the density of IQ2_XXS and over 10× FP16. Use this metric when comparing any future model-family quantisation tradeoffs.

## Hybrid Attention at 1-bit

Bonsai inherits Qwen3.6-27B's hybrid-attention backbone:
- **64 layers total**, split as `16 × (3× Gated DeltaNet → 1× Gated Attention → FFN)`
- **Gated DeltaNet** — linear-attention / SSM variant using a delta rule for state updates. Sub-quadratic in context length; ~75% of layers use this
- **Gated Attention** — standard full causal attention with learned gating on the output projection (`attn_output_gate: true`). ~25% of layers
- This 75/25 split keeps the KV cache manageable: only 16 of 64 layers grow a full `O(L²)` cache (~4.3 GB at the full 262K window in FP16)

Key dimensions:
- `hidden_size`: 5120
- `intermediate_size`: 15360 (3× hidden)
- `num_attention_heads`: 20 (full-attention GQA heads)
- `num_key_value_heads`: 5 (4:1 GQA ratio)
- `head_dim`: 256
- `vocab_size`: 248320
- `max_position_embeddings`: 1,048,576 (1M context supported theoretically; 262K demonstrated on-device)

## DSpark Speculative Decoding

Bonsai 27B ships a **DSpark drafter layer** — not a separate model but a compact six-layer block-parallel transformer trained against the low-bit target.

### Design

- **Six-layer transformer** with hidden states tapped from five evenly spaced layers of the main model
- **Block-parallel**: drafts multiple future tokens in one pass (block size = k = 4)
- **Block-denoising objective**: diffusion-flavoured training — the drafter learns to denoise corrupted token sequences conditioned on hidden states
- **Survival-probability-weighted distillation**: reduces overfitting to the target by down-weighting improbable token continuations
- **Verification is lossless**: the target model (1-bit Bonsai) verifies draft tokens preserving the exact target distribution. Accept/reject decisions don't change output quality — only speed

### Performance Impact

| Config | Tok/s (H100) | Speedup |
|--------|-------------|---------|
| No drafter | 104.8 | 1.0× |
| DSpark (Q4_1, k=4, τ≈3.6) | 143.8 | **1.37×** |

On Apple Silicon (M5 Pro), the drafter does not yet amortise because batch-1 verification overhead exceeds the token-gain — it's disabled by default on-device.

### Shipped Formats

| Pack | Size | Precision |
|------|------|-----------|
| DSpark drafter (default) | 1.79 GB | Q4_1 |
| DSpark drafter (reference) | 7.29 GB | bf16 |

The drafter shares embeddings and output head with the target — its unique weights add ~0.5 GB at serving precision.

## Benchmark Behaviour: The "No Collapse" Claim

### Why It Matters

Conventional sub-4-bit quantisation collapses on reasoning-heavy benchmarks but preserves surface-level metrics. Example with Qwen3.6-27B IQ2_XXS (2.8 bpw):
- MMLU-Redux: **88.93** (looks fine!)
- AIME26: **57.50** (catastrophic!)
- LiveCodeBench: **56.40** (catastrophic!)

This means casual testing (MMLU, GSM8K) misses the failure entirely. The collapse is concentrated on sustained chains of reasoning.

### 1-bit Bonsai 27B Thinking-Mode Benchmarks

| Category | Benchmarks | FP16 | 1-bit Bonsai | Retention |
|----------|-----------|------|-------------|-----------|
| Math | GSM8K, MATH-500, AIME25, AIME26 | 95.33 | **91.66** | 96.2% |
| Coding | HumanEval+, MBPP+, LiveCodeBench | 88.74 | **81.88** | 92.2% |
| Knowledge | MMLU-Redux, MuSR | 83.15 | 73.39 | 88.3% |
| Instruction | IFEval, IFBench | 78.47 | 65.74 | 83.8% |
| Agentic | BFCL v3, τ²-Bench | 80.00 | 66.03 | 82.5% |
| Vision | MMMU-Pro, OCR Bench v2 | 72.61 | 59.57 | 82.0% |
| **Overall (15)** | | **85.07** | **76.11** | **89.5%** |

Key observation: **math stays within 4 points of FP16** (91.66 vs 95.33) and **coding within 7 points** (81.88 vs 88.74) — the exact categories where conventional sub-4-bit quantisation collapses to the 50s. The binary representation preserves reasoning chains that sub-4-bit linear quantisation cannot.

### Per-Benchmark Detail

| Benchmark | FP16 | 1-bit Bonsai |
|-----------|------|-------------|
| AIME25 | 93.29 | **88.75** |
| AIME26 | 93.33 | **87.08** |
| MATH-500 | 99.40 | **98.00** |
| GSM8K | 95.30 | **92.80** |
| HumanEval+ | 95.12 | **89.63** |
| MBPP+ | 83.33 | **79.60** |
| LiveCodeBench | 87.77 | **76.40** |
| MMLU-Redux | 93.42 | **82.75** |

## Supported Platforms & Throughput

| Platform | Backend | TG128 (tok/s) | PP512 (tok/s) |
|----------|---------|--------------|--------------|
| Apple M5 Max (laptop) | Metal | 66.4 | 874 |
| Apple M5 Pro (laptop) | Metal | 44.2 | 421 |
| Apple M4 Pro (laptop) | Metal | 26.0 | 133 |
| NVIDIA H100 (datacenter) | CUDA | 104.8 | 2755 |
| iPhone 17 Pro Max | MLX Swift | ~11 | — |

Decode energy on M5 Pro: **0.275 mWh/token** (with DSpark).

## Key Limitations

1. **Quality-footprint trade-off**: 89.5% of FP16 average. The 4-point gap on math and 7-point gap on coding are predictable but real. If quality is the priority, the Ternary variant (1.71 bpw, 5.9 GB, 94.6%) is the better choice.
2. **Agentic coding** (multi-file, run-test-and-repair) is not a target of this release — a coding-tuned variant is on the roadmap.
3. **DSpark only accelerates CUDA serve** currently — on Apple Silicon the verify pass doesn't amortise at batch-1.

## Cross-Reference

- Base model architecture: `references/qwen35-hybrid-architecture.md` (Qwen3.6-27B specs)
- Companion ternary variant: `prism-ml/Ternary-Bonsai-27B-gguf` (1.71 bpw, 5.9 GB)
- MLX phone deployment: `prism-ml/Bonsai-27B-mlx-1bit`
- Whitepaper: [Prism ML Bonsai 27B (github)](https://github.com/PrismML-Eng/Bonsai-demo)
- Requires custom llama.cpp fork: [PrismML-Eng/llama.cpp](https://github.com/PrismML-Eng/llama.cpp) for Q1_0_g128 kernel support