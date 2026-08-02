# HF Learnings Log — Transformers Inkling Architecture

## 2026-07-25: hf-transformers-inkling — Inkling by Thinking Machines Lab (Transformers 5.14.0+) (Topic #298 Deepening)

### Summary
Comprehensive deep-dive into **Inkling** — Thinking Machines Lab's 975B
sparse MoE multimodal model (41B active) with 1M context window, added in
Transformers 5.14.0 (2026-07-15). Accepts text, image, audio, and video inputs.
Covers the complete architecture: relative attention (no RoPE), hybrid
global+sliding window attention (5:1 ratio), short 1D convolutions (SConv),
256-expert MoE with shared expert sink, hMLP vision encoder, dmel audio
encoder, 8-layer MTP speculative decoding, chat template with reasoning effort
control, deployment strategies (transformers, SGLang, vLLM, llama.cpp, HF
Inference Providers), and comprehensive evaluation results.

### Key Findings

| Area | Finding |
|------|---------|
| **What it is** | 975B param MoE multimodal model by Thinking Machines Lab. 41B active per token. |
| **Architecture** | 66-layer decoder-only, hybrid attention (55 sliding window + 11 global), MoE (256 experts, 6 active + 2 shared), SConv, relative pos encoding |
| **Modalities** | Text, image, audio, video (via temporal patch dim) — natively processed, no separate encoder |
| **Context** | 1,048,576 tokens (1M) |
| **Position encoding** | Learned relative attention (not RoPE) — per-head relative feature R with distance modulation |
| **Vision** | hMLP hierarchical patchifier — linear layers progressively merge pixels. 40px patches, 2-frame temporal |
| **Audio** | dmel (delta-mel) discretized spectrogram — 80 mel bins → 16 vocab → embedding |
| **MoE** | 256 routed experts, 6 active per token, 2 shared experts (sink). Sigmoid gating, norm-after-topk, global scale, gate bias |
| **MTP** | 8 future-token prediction layers acting as speculative decoding drafters |
| **Reasoning effort** | `reasoning_effort` parameter: none→max (0.0→0.99). Embedded in system message |
| **Tool use** | Native tool calling via `tool_declare` system message, XML-encoded specs |
| **Variants** | BF16 (2TB VRAM), NVFP4 (600GB), GGUF quantized (30-100GB) |
| **Inference engines** | transformers 5.14+, SGLang (fastest), vLLM, llama.cpp, HF Inference Providers |
| **License** | Apache 2.0 |
| **Training data** | 45T tokens — text, images, audio, video |
| **Zero-cost inference** | HF Inference Providers (rate-limited, free), llama.cpp GGUF (needs quantized), token-limited |

### Files Created
`hf-transformers-inkling/` — SKILL.md (author: SakThai, license: MIT, 13KB) +
references/hf-learnings.md with complete architecture deep-dive, config
parameter reference, inference patterns, deployment strategies, evaluation
benchmarks, and zero-cost analysis.

### Sources
- https://huggingface.co/thinkingmachines/Inkling — Official model card
- https://huggingface.co/docs/transformers/main/en/model_doc/inkling — Transformers docs
- https://huggingface.co/blog/thinkingmachines-inkling — Official blog post
- https://github.com/huggingface/transformers/pull/47347 — Main PR
- https://huggingface.co/thinkingmachines/Inkling/raw/main/config.json — Full config

### Tags
`inkling` `transformers` `multimodal` `moe` `mtp` `speculative-decoding`
`hybrid-attention` `relative-position` `sconv` `evaluation` `audio` `vision`
