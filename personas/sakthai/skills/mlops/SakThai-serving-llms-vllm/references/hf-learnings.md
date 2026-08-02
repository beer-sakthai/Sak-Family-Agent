# HF Learnings Log — serving-llms-vllm

## 2026-07-25: hf-vllm-transformers-modeling-backend-native-speed — Dynamic Graph Rewriting Enables Native vLLM Speed from Transformers Models

### Summary
Deep-dive into the July 2026 advancement in the **vLLM transformers modeling backend** — the integration layer that lets Hugging Face Transformers models run inside the vLLM engine at **native (or better) speed** compared to hand-written vLLM implementations. The key innovation is dynamic `torch.fx`-based graph analysis and AST manipulation at runtime, which rewrites model operations in-place to fuse them into vLLM's ultra-optimized kernels — achieving throughput parity without writing a single line of custom inference code.

Source: [HF Blog — Native-speed vLLM transformers modeling backend](https://huggingface.co/blog/native-speed-vllm-transformers-backend) (July 8, 2026, by Harry Mellor & Lysandre)

### Background

The transformers library has become the **reference modeling library** for ML — supporting 450+ architectures through self-contained, easy-to-understand implementations. Historically, achieving maximum inference performance required porting a transformers model to vLLM's custom implementation framework. The transformers modeling backend (initially integrated in vLLM in 2025) bridged attention implementations, but full performance parity required custom ports.

This latest iteration **eliminates that gap entirely** for compatible architectures.

### Key Innovation: Dynamic Graph Rewriting Pipeline

The backend now uses a **three-stage optimization pipeline** at model load time:

```
1. torch.fx Static Analysis
   └── Walks the model's computation graph
   └── Searches for known patterns that can be fused/optimized

2. AST Source Code Manipulation
   └── Uses Python's `ast` module to rewrite operations in-place
   └── Fuses multi-step patterns into single vLLM kernel calls

3. torch.compile + CUDA Graphs
   └── Rewritten model is still fully torch-compilable
   └── Compose with existing vLLM optimizations (continuous batching, prefix caching)
```

### What Gets Fused

| vLLM Kernel | Transformers Pattern | Benefit |
|---|---|---|
| `MergedColumnParallelLinear` | Multiple separate linear layers for the same input | Fewer kernel launches, better GPU utilization |
| `QKVParallelLinear` | Scattered Q/K/V projections | Enables tensor-parallel (TP) plan inference |
| MoE Expert Parallel (EP) gates | Mixture-of-Experts routing | Expert-parallel execution across GPUs without model changes |
| Pipeline-parallel plans | Decoder block list identification | Automatic PP plan inference |

### Performance Results

Tested across three Qwen3 configurations on a single 8×H100 node:

| Model | Config | TP Size | EP Size | Native (vLLM) | Transformers Backend |
|---|---|---|---|---|---|
| Qwen3-4B (dense) | 1 GPU | 1 | — | Baseline | **Meets or beats** |
| Qwen3-32B (dense) | 2 GPU TP | 2 | — | Baseline | **Meets or beats** |
| Qwen3-235B-A22B (MoE FP8) | 8 GPU DP+EP | — | 8 | Baseline | **Matches** |

The transformers backend now **meets or exceeds** native vLLM throughput on every tested configuration — including the complex MoE model with expert + data parallelism.

### Usage

Single flag enables the feature:

```bash
# Any model, any parallelism scheme
vllm serve Qwen/Qwen3-4B --model-impl transformers

# With tensor parallelism
vllm serve Qwen/Qwen3-32B --model-impl transformers --tensor-parallel-size 2

# With MoE expert parallelism
vllm serve Qwen/Qwen3-235B-A22B-FP8 --model-impl transformers \
  --data-parallel-size 8 --enable-expert-parallel

# Upgrade to the latest vLLM
uv pip install --upgrade vllm --torch-backend auto
```

### Limitations

- **Linear attention models** are not currently supported (coming soon)
- **Custom Hub repo models** are unlikely to work unless written compliantly with the expected patterns
- Requires `torch.fx`-tracable model code (standard transformers implementations work)

### Key Takeaways for Skill

1. **No more porting needed.** Model authors get vLLM-native performance from their transformers implementation automatically.
2. **Same code, dual use.** The same transformers model code works for training, evaluation, RL rollouts, AND production serving — unlike pure vLLM implementations.
3. **`--model-impl transformers`** is now the recommended flag for any Hugging Face model being served with vLLM.
4. **Under the hood:** `torch.fx` + `ast` = dynamic fusion without manual kernel writing.
5. **Composable** with all existing vLLM features: TP, PP, EP, prefix caching, chunked prefill, speculative decoding, metrics.

### References
- Blog post: https://huggingface.co/blog/native-speed-vllm-transformers-backend
- Transformers model definition: https://huggingface.co/blog/transformers-model-definition
- vLLM transformers backend (initial): https://vllm.ai/blog/2025-04-11-transformers-backend
- Large scale serving: https://vllm.ai/blog/2025-12-17-large-scale-serving
- Torch FX: https://pytorch.org/docs/stable/fx.html
- Benchmark script: https://huggingface.co/datasets/ariG23498/useful-scripts/blob/main/transformers-backend-vllm-benchmark.sh
