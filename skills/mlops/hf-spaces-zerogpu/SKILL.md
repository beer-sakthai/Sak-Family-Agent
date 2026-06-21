---
title: Hugging Face Spaces ZeroGPU
description: >
  Use ZeroGPU — Hugging Face’s dynamic shared GPU allocation — to build, host,
  and optimize Gradio Spaces without managing dedicated GPU infrastructure.
  Covers hardware, quotas, decorators, model loading, and queue behavior.
---

# Hugging Face Spaces ZeroGPU

> **Scope:** informational. No local training, uploads, or GPU work.

## What is ZeroGPU?

ZeroGPU is a **shared, dynamically allocated GPU pool** for Hugging Face Spaces.
Instead of reserving a dedicated GPU for every Space, ZeroGPU allocates and
releases NVIDIA RTX Pro 6000 Blackwell GPUs **on demand** when a function runs.
This maximizes utilization and lowers cost for both HF and developers.

**Current hardware:** NVIDIA RTX Pro 6000 Blackwell.

## Who can use it?

| Role | Included daily quota | Queue priority | Notes |
|---|---|---|---|
| Unauthenticated | 2 min | Low | Can use any public ZeroGPU Space |
| Free account | 5 min | Medium | Can host/public Space |
| PRO | 40 min | Highest | Extensible with paid credits; host up to 10 Spaces |
| Team / Enterprise org member | 40 min | Highest | Extensible with credits |
| Enterprise org member | 60 min | Highest | Extensible with credits |

- The included quota resets **24 hours after your first GPU usage** (not at midnight UTC).
- **PRO/Team/Enterprise** users can go beyond the daily limit by consuming
  prepaid credits at **$1 per 10 minutes** of GPU time.
- PRO users get **8× higher daily quota** vs. free accounts and highest queue priority.

## Hosting limits

- **Personal (PRO):** max **10** ZeroGPU Spaces.
- **Organization (Team/Enterprise):** max **50** ZeroGPU Spaces.

## Supported stack

- **SDK:** Gradio only (as of this writing). Not compatible with Streamlit,
  Static HTML, or Docker Spaces.
- **Gradio:** 4+
- **PyTorch:** 2.8.0 through latest (known supported versions: 2.8.0, 2.9.1, 2.10.0, 2.11.0)
- **Python:** 3.10.13, 3.12.12

## GPU sizes

| Size | Hardware | VRAM | Quota cost |
|---|---|---|---|
| `large` (default) | Half RTX Pro 6000 Blackwell | 48 GB | 1× |
| `xlarge` | Full RTX Pro 6000 Blackwell | 96 GB | 2× |

- `xlarge` usually has **higher queue priority** but also **longer wait times**.
- Use `size="xlarge"` only when workloads truly need the extra VRAM/compute.

## Core decorator: `@spaces.GPU`

```python
import spaces
import gradio as gr
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("...")
pipe.to("cuda")

@spaces.GPU
def generate(prompt):
    return pipe(prompt).images

gr.Interface(
    fn=generate,
    inputs=gr.Text(),
    outputs=gr.Gallery(),
).launch()
```

- The decorator **requests a real GPU** when the function runs and **releases it**
  when the function completes.
- It is **effect-free** in non-ZeroGPU environments, so you can develop locally
  and on CPU Spaces without changes.

## Critical rule: Model loading

A common mistake is loading the model **inside** the decorated function.
Inside `@spaces.GPU`, real CUDA is available, so you might expect to load there.
Do not do that.

```python
# Correct: model on CUDA at module level
pipe = DiffusionPipeline.from_pretrained("...")
pipe.to("cuda")  # <-- outside the GPU function
```

**Why this works:** HF enables a **PyTorch CUDA emulation mode** outside
`@spaces.GPU` functions. This allows `pipe.to("cuda")` and similar CUDA
operations to succeed at import/startup even when no real GPU is present yet.
Inside `@spaces.GPU`, real CUDA is used.

Lazy-loading models inside the decorated function is **significantly less
efficient** because CUDA transfers are optimized for placements done at startup.

## Duration management

Default maximum runtime: **60 seconds** of GPU time per call.

### Fixed duration

```python
@spaces.GPU(duration=120)
def generate(prompt):
    ...
```

### Dynamic duration

Pass a callable that returns a duration based on inputs:

```python
def get_duration(prompt, steps):
    step_duration = 3.75
    return steps * step_duration

@spaces.GPU(duration=get_duration)
def generate(prompt, steps):
    return pipe(prompt, num_inference_steps=steps).images
```

Shorter durations improve **queue priority** for visitors.

## Compatibility caveats

- ZeroGPU is not `torch.compile` compatible.
- You **can** use PyTorch **ahead-of-time (AOT) compilation** — requires `torch 2.8+`.
- “Limited compatibility compared to standard GPU Spaces” — some edge cases may
  fail. Test thoroughly.
- High-level HF libraries (`transformers`, `diffusers`) are well supported but
  not guaranteed for every model/setup.

## Queue behavior

- Queue priority is primarily driven by your **tier** (PRO/Team/Enterprise highest).
- Remaining quota affects priority: users with more quota left get bumped up.
- `xlarge` consumes quota faster but may queue faster.
- PRO/Team/Enterprise users can auto-bill with credits once daily quota is exhausted.

## Troubleshooting tips

1. **CUDA OOM?** Try `size="xlarge"` or a smaller model / quantization.
2. **Long queue?** Ensure you’re using the default `large` unless you need `xlarge`.
3. **Model not loading?** Make sure it’s on `cuda` at module level, not inside the GPU function.
4. **`torch.compile` failing?** Switch to AOT compilation or remove compile calls.
5. **Credits not charging?** Verify you have a billing method and credits added in
   HF Billing settings.

## Resources

- Official docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- Feedback/discussions: https://huggingface.co/spaces/zero-gpu-explorers/README/discussions
- AOT compilation guide: linked from the official docs (requires `torch 2.8+`)

## Session references

- `references/official-zerogpu-docs-excerpt.md` — verbatim excerpts and extraction notes from the official docs page (2026-06-21).
