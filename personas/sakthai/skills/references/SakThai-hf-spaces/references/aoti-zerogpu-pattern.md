# AOTI Compilation for ZeroGPU Spaces

*Pattern discovered: 2026-07-23 from `zerogpu-aoti/wan2-2-fp8da-aoti-faster`*

## What It Is

AOTI (Ahead-of-Time Inductor) compilation is PyTorch's optimization tier where model graphs are pre-compiled into native binaries *before* deployment — bypassing the JIT compilation that normally happens at first-inference time. For ZeroGPU Spaces, this means model startup is near-instant, even for 14B-parameter models.

## Detection Checklist

Scan `app.py` for these signals:

| Signal | Code Pattern | What It Means |
|--------|-------------|----------------|
| `import aoti` | `import aoti` at module top | Custom AOTI loading module present |
| `spaces.aoti_load()` | `spaces.aoti_load(module=pipe.transformer, repo_id='...')` | Pre-compiled inductor graph loaded from HF repo |
| Companion repo | e.g. `cbensimon/WanTransformer3DModel-sm120-cu130-raa` | Contains the `.so` / `.pt2` compiled exports |

**Full example from `zerogpu-aoti/wan2-2-fp8da-aoti-faster`:**
```python
import aoti

pipe = WanImageToVideoPipeline.from_pretrained(...)

# After model loading and LoRA fusion
spaces.aoti_load(
    module=pipe.transformer,
    repo_id='cbensimon/WanTransformer3DModel-sm120-cu130-raa',
)
spaces.aoti_load(
    module=pipe.transformer_2,
    repo_id='cbensimon/WanTransformer3DModel-sm120-cu130-raa',
)
```

## Companion to FP8 Quantization

In the `zerogpu-aoti/wan2-2` Space, AOTI is stacked on top of torchao FP8 quantization:

1. **FP8 quantization** via `torchao` (`Float8DynamicActivationFloat8WeightConfig`) — reduces compute precision
2. **AOTI compilation** via `spaces.aoti_load()` — pre-compiles the reduced-precision graph
3. **Dynamic GPU duration** — `@spaces.GPU(duration=get_duration)` estimates seconds based on resolution × frames^1.5

The order matters: quantize first, *then* compile the quantized graph.

## Companion Module: `import aoti`

The `aoti` module ships alongside the Space's `app.py` and wraps PyTorch's `torch._inductor` or `torch.export` APIs. It's not a standard PyTorch or spaces package — it's a custom helper that:

- Downloads the pre-compiled export from the companion HF repo
- Loads it via `torch.jit.load()` or similar serialization
- Wires it into the model submodule in-place

When you see `import aoti` without finding `aoti.py` in the repo's root (i.e. the file listing via the Hub API), it's embedded in the Docker image or installed as a build-time dependency.

## How to Build Something Similar

Pre-requisites:
1. Export the model graph via PyTorch's `torch.export()` + `torch._inductor` or `torch.compile()` with `mode="reduce-overhead"`
2. Upload the serialized exports to a companion HF repo alongside the Space
3. Use `spaces.aoti_load()` in the Space's `app.py` at startup

The companion repo structure from `cbensimon/WanTransformer3DModel` shows the convention: the repo is named after the model architecture + meta-optimization flags (`sm120-cu130-raa` = compute capability, CUDA version, and optimization variant).

## Reporting

When you detect AOTI in a Space, mention in the deep-dive report:
- Which model submodules are AOTI-compiled
- The companion repo ID
- Whether FP8 quantization runs before or after compilation
- Any dynamic GPU duration function accompanying it
