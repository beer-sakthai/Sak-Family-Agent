---
name: hf-spaces-zerogpu
description: "Hugging Face Spaces ZeroGPU: dynamic GPU allocation for Gradio Spaces, GPU sizes, quotas, decorators, and fallback patterns."
tags: [huggingface, spaces, zerogpu, gpu, inference, mlops]
---

# Hugging Face Spaces ZeroGPU

**Dynamic GPU allocation for Gradio Spaces** on the Hugging Face Hub.

## What It Provides
- **Shared GPU pool** using NVIDIA RTX Pro 6000 Blackwell GPUs.
- **On-demand allocation/release** — GPU only while `@spaces.GPU`-decorated functions run.
- **Free for all users** (with daily quotas); PRO users get 8× higher quotas, queue priority, and credit-based overflow.

## GPU Sizes
| Size | Backing Hardware | VRAM | Quota Cost |
|------|------------------|------|------------|
| `large` (default) | Half RTX Pro 6000 Blackwell | 48GB | 1× |
| `xlarge` | Full RTX Pro 6000 Blackwell | 96GB | 2× |

Select with `hardware="large"` or `hardware="xlarge"` in Space settings.

## Compatibility
- **SDK**: Gradio 4+ only.
- **Python**: 3.10.13, 3.12.12.
- **PyTorch**: wide range (2.8.0 through latest) supported.
- High-level libraries: optimized for `transformers` and `diffusers`.

## Decorator Pattern
```python
import spaces
import gradio as gr
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("...")
pipe.to("cuda")

@spaces.GPU
def generate(prompt):
    return pipe(prompt).images[0]

gr.Interface(fn=generate, inputs=gr.Text(), outputs=gr.Image()).launch()
```

## Critical Rules
1. Decorate only the **actual GPU functions**; ZeroGPU releases the GPU when the decorated function returns.
2. Keep **`pipe.to("cuda")` at module level** — ZeroGPU uses a PyTorch CUDA emulation/mock mode outside `@spaces.GPU` so that construction works; moving the model inside the decorated function is **slower** (extra CUDA transfers).
3. The decorator is **effect-free in non-ZeroGPU environments** (CPU/GCPU Spaces).
4. Pure CPU Spaces get an IP-based daily quota; ZeroGPU Spaces count against a separate GPU quota.

## Quotas & Limits
- **Free Pro**: 8× the non-zero daily quota; highest queue priority.
- **Overflow**: PRO/Team/Enterprise can exceed daily quota with pre-paid credits.
- During peak load, **queueing occurs**; there is no dedicated reserved GPU.
- Session length matters: GPU is billed in seconds. PRO users see messages like “Requested 42s on 60s” indicating remaining quota.

## Fallback Strategies
- **CPU fallback**: offer a slower CPU path when queue is busy or user is out of quota.
- **Lighter models**: smaller variant when wait time is too long.
- **IP-based quota**: if ZeroGPU is failing, Hugging Face may silently fall back to CPU Space quota.

## Common Pitfalls
- **Large models + IO**: loading weights inside `@spaces.GPU` is suboptimal; pre-load at startup.
- **Stateful pipelines**: if pipeline keeps state across calls, see what resets between GPU allocations.
- **ComfyUI**: current ZeroGPU is not suitable for full ComfyUI (pipeline-level, not node-level, GPU control).
- **Batch size**: GPU size must cover VRAM demand; `xlarge` for >48GB peak usage.

## When to Use
- Free or low-cost demos needing real GPU speed.
- Public-facing model showcases.
- Quick prototyping for multimodal workloads.
- **NOT** for long-running servers or reserved GPU.

## References
- Official docs: `huggingface.co/docs/hub/en/spaces-zerogpu`
- Curated list: `huggingface.co/spaces/enzostvs/zero-gpu-spaces`
- Forum: discussions on queueing, quotas, CPU fallback.