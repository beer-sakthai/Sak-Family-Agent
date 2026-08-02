# HF Learnings — Spaces ZeroGPU: Complete API & Architecture Deep Dive

**Topic:** `spaces-zerogpu-free-gpu-allocation` (Topic #4 — Deepened)
**Date:** 2026-07-24
**Skill:** mlops/spaces-zerogpu
**Author:** SakThai
**License:** MIT

## Summary

Comprehensive deep-dive into Hugging Face Spaces ZeroGPU — the free dynamic GPU
allocation infrastructure for Gradio Spaces. Covers the ZeroGPU architecture
(shared GPU pool, dynamic attach/detach, CUDA emulation), the `@spaces.GPU`
decorator API (size, duration, dynamic duration), the programmatic control API
via `huggingface_hub` (hardware requests, volumes, sleep time), quota system
and tiers, GPU size selection, multi-GPU support, and practical patterns for
optimising ZeroGPU usage on free accounts. All research sourced from live
production docs (`hf.co/docs/hub/en/spaces-zerogpu`), the `huggingface_hub`
v1.24.0 source code, and the Spaces GPU upgrades reference.

---

## 1. Architecture Overview

ZeroGPU is Hugging Face's shared GPU infrastructure. Instead of dedicating a GPU
to a Space 24/7, the system **dynamically allocates** NVIDIA RTX Pro 6000
Blackwell GPU slices to your Space on demand and releases them when idle.

### How It Works

```
┌──────────────────────────────────────────────────┐
│                  Space Container                  │
│                                                   │
│  ┌─────────────────┐     ┌──────────────────┐     │
│  │ Module Level     │     │ @spaces.GPU fn    │     │
│  │ (CUDA emulated)  │     │ (REAL CUDA)       │     │
│  │                  │     │                   │     │
│  │ model.to('cuda') │────▶│   generate()      │     │
│  │                  │     │   pipe(prompt)    │     │
│  └─────────────────┘     └──────────────────┘     │
│         │                          │               │
│         ▼                          ▼               │
│  ┌──────────────┐         ┌──────────────┐         │
│  │ CUDA Emu     │         │ Real GPU     │         │
│  │ (no GPU)     │         │ (48/96 GB)   │         │
│  └──────────────┘         └──────────────┘         │
└──────────────────────────────────────────────────┘
```

**Key insight:** PyTorch runs in a **CUDA emulation mode** outside the
`@spaces.GPU` decorator. This means `model.to('cuda')` works at the module level
without a real GPU. Inside the decorated function, a real GPU is attached.

### Backing Hardware

| GPU Size | Hardware | VRAM | Quota Cost |
|----------|----------|------|-----------|
| `large` (default) | Half NVIDIA RTX Pro 6000 Blackwell | **48 GB** | 1× |
| `xlarge` | Full NVIDIA RTX Pro 6000 Blackwell | **96 GB** | 2× |

The RTX Pro 6000 Blackwell is NVIDIA's pro workstation GPU based on the
Blackwell architecture (2025/2026 generation), with enhanced FP8/FP4 tensor
cores and 3rd-gen RT cores.

## 2. The `@spaces.GPU` Decorator API

The `@spaces.GPU` decorator is provided by the `spaces` package (installed
automatically in ZeroGPU Spaces). It marks which functions need a real GPU.

### Basic Usage

```python
import spaces
from diffusers import DiffusionPipeline

pipe = DiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-3.5-medium")
pipe.to("cuda")  # Module-level — CUDA emulation

@spaces.GPU
def generate(prompt: str):
    return pipe(prompt).images

gr.Interface(fn=generate, inputs=gr.Text(), outputs=gr.Gallery()).launch()
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `size` | `str` | `"large"` | GPU size: `"large"` (48 GB) or `"xlarge"` (96 GB) |
| `duration` | `int` or `Callable` | `60` | Max GPU runtime in seconds. Can be a callable for dynamic duration |

### Size Selection

```python
@spaces.GPU(size="xlarge")  # Full RTX Pro 6000 Blackwell (96 GB)
def generate_video(prompt: str):
    return pipe(prompt).videos
```

**Guidelines:**
- Default `large` (48 GB) covers most models (LLaMA 3.3 70B Q4, SD3.5, FLUX)
- `xlarge` (96 GB) needed for full-precision 70B+ models or multi-model pipelines
- `xlarge` consumes 2× daily quota and has higher queue probability
- Only use `xlarge` when your workload truly needs the extra compute/memory

### Duration Management

```python
# Fixed duration
@spaces.GPU(duration=120)
def generate(prompt: str):
    return pipe(prompt).images  # Allows up to 120s GPU time

# Dynamic duration (callable) — v2+ API
def get_duration(prompt, steps):
    step_duration = 3.75
    return steps * step_duration

@spaces.GPU(duration=get_duration)
def generate(prompt, steps):
    return pipe(prompt, num_inference_steps=steps).images
```

**Best practices:**
- Set duration slightly above the expected runtime (10-20% buffer)
- Shorter durations improve queue priority for visitors
- Dynamic duration is ideal for variable-length generation (video, high-res)

### Multi-GPU Support

ZeroGPU supports leveraging **multiple GPUs** on a single Space application.
The exact API depends on the decorator placement — each `@spaces.GPU` call
gets its own GPU allocation. For truly parallel GPU work, multiple decorators
can be used in parallel threads.

### Compatibility

| Component | Supported |
|-----------|-----------|
| **SDK** | Gradio 4+ only |
| **PyTorch** | 2.8.0 to latest |
| **Python** | 3.10.13, 3.12.12 |
| **`torch.compile`** | ❌ Not supported |
| **AOT compilation** | ✅ Supported (torch 2.8+) |

**Important:** `torch.compile` is **not** supported, but PyTorch ahead-of-time
(AOT) compilation works for PyTorch 2.8+.

## 3. Programmatic Space Management API

The `huggingface_hub` library (v1.24.0+) provides the complete API for managing
ZeroGPU Spaces programmatically.

### Request ZeroGPU Hardware

```python
from huggingface_hub import HfApi, SpaceHardware

api = HfApi()

# Request ZeroGPU
runtime = api.request_space_hardware(
    repo_id="username/my-space",
    hardware=SpaceHardware.ZERO_A10G,  # "zero-a10g"
)
# Returns SpaceRuntime with stage, hardware, sleep_time, volumes, etc.
```

### Check Space Runtime

```python
from huggingface_hub import get_space_runtime, SpaceStage

runtime = get_space_runtime("username/my-space")
print(f"Stage: {runtime.stage}")            # SpaceStage.RUNNING
print(f"Hardware: {runtime.hardware}")      # SpaceHardware.ZERO_A10G
print(f"Sleep time: {runtime.sleep_time}")  # seconds or None
print(f"Volumes: {runtime.volumes}")        # list[Volume] or None
```

### Set Sleep Time

```python
# ZeroGPU Spaces use the default sleep time (48h inactivity for free)
# Only configurable on paid hardware
api.set_space_sleep_time("username/my-space", sleep_time=3600)  # 1 hour
```

### Mount Storage Volumes

```python
from huggingface_hub import Volume

volumes = [
    Volume(
        type="bucket",
        source="username/my-bucket",
        mount_path="/data",
        read_only=False,
    ),
    Volume(
        type="model",
        source="username/my-model",
        mount_path="/models",
        read_only=True,
    ),
]
api.set_space_volumes("username/my-space", volumes=volumes)
```

### Pause / Restart

```python
from huggingface_hub import pause_space, restart_space

# Pause (stops execution, no billing)
pause_space("username/my-space")

# Restart
restart_space("username/my-space")

# Restart with factory reboot (clears cache)
restart_space("username/my-space", factory_reboot=True)
```

### Wait for Space to Be Ready

```python
from huggingface_hub import wait_for_space

# Blocks until Space reaches a terminal stage
runtime = wait_for_space("username/my-space", timeout=300)
print(f"Ready! Stage: {runtime.stage}")
```

### Duplicate a Space with ZeroGPU

```python
from huggingface_hub import duplicate_space, SpaceHardware

duplicate_space(
    from_id="other-user/template-space",
    to_id="username/my-new-space",
    hardware=SpaceHardware.ZERO_A10G,
)
```

### Search ZeroGPU Spaces

```python
from huggingface_hub import search_spaces

for space in search_spaces("zerogpu image generation", filter="zero-a10g"):
    print(f"{space.id} — {space.title}")
```

## 4. Quota System & Usage Tiers

### Daily Quota by Account Type

| Account Type | Daily GPU Quota | Queue Priority |
|-------------|----------------|---------------|
| Unauthenticated | 2 minutes | Low |
| Free account | **5 minutes** | Medium |
| PRO | 40 minutes (extensible) | Highest |
| Team organization | 40 minutes (extensible) | Highest |
| Enterprise organization | 60 minutes (extensible) | Highest |

### Key Rules

1. **Reset:** Quota resets exactly **24 hours** after your first GPU usage each day
2. **Priority:** Remaining quota directly affects queue priority (more quota = higher priority)
3. **Extending quota (PRO+):** $1 per 10 minutes via pre-paid credits
4. **Auto-billing:** Once daily quota is exhausted, additional usage is automatically billed against credit balance

### Hosting Limits

| Account Type | Max ZeroGPU Spaces |
|-------------|-------------------|
| Free personal (good standing) | **2 Spaces** |
| PRO subscriber | **10 Spaces** |
| Team/Enterprise org | **50 Spaces** |

**Good standing** requires: verified email + account older than 30 days.

## 5. Optimisation Patterns for Free Accounts

### 5-Minute Daily Budget Maximisation

With only 5 minutes/day of GPU time on a free account, every second counts:

**1. Module-level model loading**
```python
# ✅ GOOD — model loaded once at import time
pipe = DiffusionPipeline.from_pretrained("...")
pipe.to("cuda")

# ❌ BAD — loading inside @spaces.GPU wastes GPU quota
@spaces.GPU
def generate(prompt):
    pipe = DiffusionPipeline.from_pretrained("...")  # 30s+ wasted
    pipe.to("cuda")
    return pipe(prompt).images
```

**2. Ahead-of-time (AOT) compilation**
```python
import torch
import torch._export as export

# Pre-compile model outside @spaces.GPU
model = MyModel().to("cuda")
exported = torch.export.export(model, (example_input,))

@spaces.GPU
def generate(input_tensor):
    return exported(input_tensor)  # Much faster first inference
```

**3. Shrink duration to actual needs**
```python
@spaces.GPU(duration=15)  # Realistic for fast models
def quick_generate(prompt: str):
    return fast_model(prompt).images
```

**4. Cache results**
```python
from functools import lru_cache

@lru_cache(maxsize=128)
@spaces.GPU
def generate(prompt: str):
    return pipe(prompt).images  # Repeated prompts are free after first
```

### Multi-Visitor Queue Strategy

ZeroGPU uses a FIFO queue. For free accounts:
- Each visitor's GPU call enters the queue
- Shorter `duration` values improve queue position
- Active visitors with remaining quota get priority
- **Peak hours** (US daytime) have longer wait times

### Storage Integration

```python
from huggingface_hub import Volume

# Mount a bucket for persistent storage
volumes = [
    Volume(type="bucket", source="username/cache-bucket", mount_path="/cache"),
    Volume(type="model", source="username/preloaded-model", mount_path="/models", read_only=True),
]
api.set_space_volumes("username/my-space", volumes=volumes)
```

**Pattern:** Pre-load model weights from a read-only model volume (avoids
download at startup), then write inference results to a writable bucket.

## 6. Programmatic Full Lifecycle Example

```python
from huggingface_hub import (
    HfApi,
    SpaceHardware,
    SpaceStorage,
    Volume,
    wait_for_space,
    get_space_runtime,
)

api = HfApi()

# 1. Create a Space
repo = api.create_repo(
    repo_id="username/my-zerogpu-demo",
    repo_type="space",
    space_sdk="gradio",
    space_hardware=SpaceHardware.ZERO_A10G,
    space_storage=SpaceStorage.SMALL,
)

# 2. Wait for build
runtime = wait_for_space("username/my-zerogpu-demo", timeout=600)
print(f"Space ready: {runtime.stage}")

# 3. Mount a bucket for outputs
volumes = [
    Volume(type="bucket", source="username/my-bucket", mount_path="/outputs"),
]
api.set_space_volumes("username/my-zerogpu-demo", volumes=volumes)

# 4. Check runtime details
runtime = get_space_runtime("username/my-zerogpu-demo")
print(f"Hardware: {runtime.hardware}")
print(f"Stage: {runtime.stage}")
print(f"Sleep time: {runtime.sleep_time}s")

# 5. Pause when not needed (saves nothing on ZeroGPU, but good practice)
# pause_space("username/my-zerogpu-demo")
```

## 7. Best Practices Summary

### DO
- ✅ Load models at module level (outside `@spaces.GPU`)
- ✅ Use `duration` to match actual function runtime
- ✅ Use AOT compilation instead of `torch.compile`
- ✅ Mount model repos as read-only volumes for faster startup
- ✅ Cache frequently-used prompt results
- ✅ Set dynamic duration for variable-length generation

### DON'T
- ❌ Don't load models inside `@spaces.GPU` — wastes GPU quota
- ❌ Don't use `torch.compile` — not supported
- ❌ Don't request `xlarge` unless you truly need 96 GB
- ❌ Don't leave Spaces running if unused (though ZeroGPU auto-sleeps after 48h)
- ❌ Don't mix Xet and large uploads — use one strategy

### Zero-Cost Strategy for Beer

For Beer's free account:
- **2 ZeroGPU Spaces max** — use for flagship demos only
- **5 min/day GPU quota** — optimise every second
- **Storage buckets** (free tier) for persistent data across restarts
- **Dataset repos** as alternative persistent storage (no GPU quota impact)
- **Prioritise:** One Space for model eval demo, one for agent tool UI

## 8. Known Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| Gradio SDK only | No Streamlit/Docker/Static ZeroGPU | Use Gradio or accept paid GPU |
| No `torch.compile` | Slower first inference | Use AOT compilation (torch 2.8+) |
| 5 min/day free quota | Short demo sessions | Cache aggressively, batch requests |
| Queue delays at peak | Visitor wait time | Set accurate `duration` |
| CUDA emulation quirks | Some PyTorch ops fail outside `@spaces.GPU` | Move all GPU code inside decorated functions |

## 9. Source

- ZeroGPU docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- GPU Spaces docs: https://huggingface.co/docs/hub/en/spaces-gpus
- Spaces hardware spec reference: same page (GPU tiers table)
- `huggingface_hub` v1.24.0 source: `SpaceHardware`, `request_space_hardware`,
  `set_space_volumes`, `Volume`, `wait_for_space`, `pause_space`,
  `restart_space`, `duplicate_space`, `search_spaces`
- `spaces` package: `@spaces.GPU` decorator (from `pip install spaces`)
- Ahead-of-time compilation guide: HF blog (July 2026)
- Storage buckets docs: https://huggingface.co/docs/hub/en/storage-buckets
