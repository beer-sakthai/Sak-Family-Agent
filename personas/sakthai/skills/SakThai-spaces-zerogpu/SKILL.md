---
name: SakThai-spaces-zerogpu
author: SakThai
license: MIT
description: "Hugging Face Spaces ZeroGPU — free dynamic GPU allocation for Gradio Spaces: setup, @spaces.GPU decorator, GPU sizes, quotas, and best practices."
version: 1.0.0
tags: [huggingface, spaces, zerogpu, gradio, gpu, free-tier, mlops]
platforms: [linux, macos, windows]
related_skills: [huggingface-hub]
---

# Spaces ZeroGPU — Free Dynamic GPU for Gradio

## ⚠️ Gradio Spaces now require PRO (mid-2026)

As of mid-2026, Hugging Face changed its free tier: **creating new Gradio and Streamlit Spaces on CPU/GPU requires a PRO subscription**. The API returns `402 Payment Required`. **Static Spaces** (HTML/CSS/JS) remain completely free.

For existing ZeroGPU Spaces: those created before the policy change continue to work. New Gradio Spaces are blocked for free accounts.

ZeroGPU is Hugging Face's shared infrastructure for **free dynamic GPU allocation** on Spaces. It attaches NVIDIA RTX Pro 6000 Blackwell GPUs to your Gradio app on demand and releases them when idle.

> **Zero-cost first:** ZeroGPU is Hugging Face's only free GPU tier. Use it for demos, inference, and prototyping before considering paid Inference Endpoints or dedicated GPU Spaces.

---

## How It Works

1. **Dynamic allocation** — A GPU slice is attached to your process only during `@spaces.GPU`-decorated function calls.
2. **CUDA emulation** — Outside the decorated function, PyTorch runs in CUDA emulation mode so `.to('cuda')` works at module level without a real GPU.
3. **Real CUDA** — Inside `@spaces.GPU`, real GPU execution happens.

---

## GPU Sizes

| Size | Backing Hardware | VRAM | Quota Cost |
|------|-----------------|------|------------|
| `large` (default) | Half NVIDIA RTX Pro 6000 Blackwell | 48 GB | 1× |
| `xlarge` | Full NVIDIA RTX Pro 6000 Blackwell | 96 GB | 2× |

---

## Usage Tiers (Daily Quota)

| Account Type | Daily GPU Quota | Queue Priority |
|--------------|----------------|---------------|
| Unauthenticated | 2 minutes | Low |
| Free account | 5 minutes | Medium |
| PRO | 40 minutes (extensible) | Highest |
| Team organization | 40 minutes (extensible) | Highest |
| Enterprise organization | 60 minutes (extensible) | Highest |

- Quota resets **exactly 24 hours after your first GPU usage** each day.
- Remaining quota directly affects queue priority (more quota = higher priority).
- PRO/Team/Enterprise can extend quota at **$1 per 10 minutes** via pre-paid credits.

---

## Hosting Limitations

| Account Type | Max ZeroGPU Spaces |
|-------------|-------------------|
| Free (verified email, 30+ days old) | 2 |
| PRO | 10 |
| Team/Enterprise org | 50 |

---

## Getting Started

### Requirements
- **SDK:** Gradio 4+ only (ZeroGPU is **not** compatible with Streamlit)
- **PyTorch:** 2.8.0+
- **Python:** 3.10.13 or 3.12.12

### Step-by-step

1. **Create a Space** at https://huggingface.co/new-space with Gradio SDK.
2. **Select ZeroGPU hardware** in Space Settings → Hardware → ZeroGPU.
3. **Install dependencies** in `requirements.txt`:
   ```
   spaces
   torch>=2.8.0
   gradio>=4
   ```
4. **Import the `spaces` module** and decorate GPU functions:

```python
import spaces
import gradio as gr
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("model-id")
pipe.to('cuda')

@spaces.GPU
def generate(prompt: str):
    return pipe(prompt).images

gr.Interface(
    fn=generate,
    inputs=gr.Text(),
    outputs=gr.Gallery(),
).launch()
```

### Important Model Loading Rule

**Load models on CUDA at module root level** (outside `@spaces.GPU`), not inside the decorated function. This works because CUDA emulation is active outside `@spaces.GPU`. Lazy-loading inside the decorator is significantly less efficient.

---

## Advanced Usage

### Custom Duration

Default GPU runtime per call is **60 seconds**. Override with the `duration` parameter:

```python
@spaces.GPU(duration=120)
def generate(prompt: str):
    return pipe(prompt).images
```

Shorter durations improve queue priority for visitors.

### Dynamic Duration

Pass a **callable** that computes duration based on inputs:

```python
def get_duration(prompt, steps):
    step_duration = 3.75
    return steps * step_duration

@spaces.GPU(duration=get_duration)
def generate(prompt, steps):
    return pipe(prompt, num_inference_steps=steps).images
```

### GPU Size Selection

```python
@spaces.GPU(size="xlarge")
def generate(prompt: str):
    return pipe(prompt).images
```

> **Caveats with `xlarge`:**
> - Consumes 2× daily quota (e.g., 45s real time → 90s quota consumption)
> - Higher queuing probability and longer wait times
> - Use only when your workload genuinely needs the extra compute or memory

---

## Compilation

- **`torch.compile` is NOT supported** on ZeroGPU.
- Use **PyTorch ahead-of-time (AOT) compilation** instead (requires torch 2.8+).

---

## CLI Management via `hf`

List and manage ZeroGPU Spaces with the `hf` CLI:

```bash
# List your Spaces (filter by hardware type if needed)
hf spaces list

# Enable dev-mode on a Space
hf spaces dev-mode my-space

# Check Space logs
hf spaces logs my-space
```

See also the `huggingface-hub` skill for broader `hf` CLI usage.

---

## Known Limitations

| Limitation | Detail |
|-----------|--------|
| SDK | Gradio 4+ only — no Streamlit support |
| `torch.compile` | Not supported; use AOT compilation instead |
| Concurrent GPU | Multiple `@spaces.GPU` calls per Space are supported via multi-GPU (using multiple decorators on separate functions) |
| Quota | Daily quota is shared across ALL ZeroGPU Spaces for an account |
| Model loading | Must happen at module root level, not inside `@spaces.GPU` |

---

## Debugging Tips

1. **Check Space logs:** `hf spaces logs --full <space-name>`
2. **Verify hardware:** Space Settings → Hardware → should show "ZeroGPU"
3. **CUDA not found error:** Ensure `torch` is installed and the model is moved to CUDA at module root (not inside the decorated function)
4. **Quota exhausted:** Wait 24h from first GPU usage in the current cycle, or upgrade to PRO

---

## Related Resources

- [Official ZeroGPU Docs](https://huggingface.co/docs/hub/en/spaces-zerogpu)
- [AOT Compilation on ZeroGPU Blog Post](https://huggingface.co/blog/zero-gpu-aot-compilation)
- [Curated ZeroGPU Spaces List](https://huggingface.co/spaces/zero-gpu-explorers/README)
- [Spaces Overview](https://huggingface.co/docs/hub/spaces)
- **Reference:** [`references/spaces-api-discovery.md`](references/spaces-api-discovery.md) — Finding trending/recent Spaces via the Hub REST API (sort parameters, combine-sorts workaround, pitfalls)
