# HF Learnings Log

## 2026-07-25: hf-transformers-flash-attention-3-deep-dive — FlashAttention-3 & FA4 Integration in Transformers

### Summary
Comprehensive deep-dive into the Hugging Face Transformers FlashAttention-3 and FlashAttention-4 integration as of mid-2026. Covers the full AttentionInterface abstraction, all 8 registered backend implementations, the Kernels Hub for runtime kernel downloading, FA3 beta release specifics (FP16/BF16/FP8 support, Hopper-only), FA4 (CuTeDSL for Hopper + Blackwell), paged attention variants, backbone-specific dispatch for multimodal models, runtime switching, and the FlashAttention fallback mechanism. Based on the official Transformers docs (main branch) and Dao-AILab/flash-attention repository.

### Source
- Transformers AttentionInterface: https://huggingface.co/docs/transformers/main/en/attention_interface
- FlashAttention repo: https://github.com/Dao-AILab/flash-attention
- FA3 blogpost: https://tridao.me/blog/2024/flash3/
- FA3 paper: https://tridao.me/publications/flash3/flash3.pdf
- Published: 2026-07-25, Transformers v5.x main

### 1. The Attention Backend Architecture

Transformers v5.x introduced the **AttentionInterface**, a decoupled attention backend abstraction. Instead of each model class implementing its own attention logic, the attention computation is separated into pluggable backends. This means:

- Models don't hardcode attention logic
- Backends are registered via a central registry
- Users switch backends at runtime
- New backends (FA3, FlexAttention) added without model code changes

```
┌─────────────────────────────────────────────┐
│              AttentionInterface               │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ FA3      │ │ FA2      │ │ SDPA         │ │
│  │ (Hopper) │ │ (Ampere+)│ │ (All GPUs)   │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │FlexAttn  │ │ Paged|*  │ │ Kernels Hub  │ │
│  │(Custom)  │ │ (Memory) │ │ (Pre-compiled)││
│  └──────────┘ └──────────┘ └──────────────┘ │
└─────────────────────────────────────────────┘
```

### 2. All 8 Registered Attention Backends

| Backend | String Key | Description | Hardware |
|---------|-----------|-------------|----------|
| FlashAttention-3 | `"flash_attention_3"` | Overlaps operations, tighter fusion of fwd/bwd | H100/H800 only (Hopper) |
| FlashAttention-2 | `"flash_attention_2"` | Tiles into smaller blocks, fast on-chip SRAM | Ampere, Ada, Hopper |
| FlexAttention | `"flex_attention"` | Custom attention patterns without writing CUDA | Hopper+ with torch.compile |
| SDPA | `"sdpa"` | PyTorch native SDPA, auto-selects best impl | All CUDA GPUs |
| Paged FA3 | `"paged\|flash_attention_3"` | Paged version of FA3 | H100/H800 |
| Paged FA2 | `"paged\|flash_attention_2"` | Paged version of FA2 | Ampere, Ada, Hopper |
| Paged SDPA | `"paged\|sdpa"` | Paged version of SDPA | All CUDA GPUs |
| Paged eager | `"paged\|eager"` | Paged version of basic eager attention | All devices |

**Paged attention** variants manage KV-cache as fixed-size pages in memory, critical for serving long-context models efficiently. They are particularly useful when combined with vLLM or TGI-style batching.

### 3. FlashAttention-3: The Beta Release

**Status:** Beta (as of July 2026), published by Tri Dao @ Dao-AILab.

**What's new in FA3 vs FA2:**
1. **Warp-specialization** — Warps are specialized into producer/consumer roles rather than all doing the same work
2. **Async pipeline** — Overlaps GEMM (matrix multiply) with softmax operations
3. **FP8 support** — Forward pass in FP8 (requires H100 native FP8 Tensor Cores)
4. **Tighter fusion** — More operations fused into a single kernel, fewer global memory round-trips

**Requirements:**
- GPU: H100 or H800 (Hopper architecture only — NOT Ampere or Ada)
- CUDA: >= 12.3 (CUDA 12.8 recommended for best performance)
- PyTorch: 2.2+

**Installation:**
```bash
# Beta package from the hopper/ subdirectory
cd hopper
python setup.py install

# Or via uv
pip install flash-attn-3

# Or from source with uv
# pyproject.toml:
# [tool.uv.sources]
# flash-attn-3 = { git = "https://github.com/Dao-AILab/flash-attention", subdirectory = "hopper" }
```

**API:**
```python
from flash_attn_3 import flash_attn_interface
flash_attn_interface.flash_attn_func(q, k, v, causal=True)
```

### 4. FlashAttention-4: CuTeDSL (Latest)

**Status:** Released via `pip install flash-attn-4`

FA4 is written in **CuTeDSL** (NVIDIA's CUDA Template DSL) and targets both Hopper (H100) and Blackwell (B200) GPUs.

```bash
# Standard install
pip install flash-attn-4

# CUDA 13 best performance
pip install "flash-attn-4[cu13]"
```

**Usage:**
```python
from flash_attn.cute import flash_attn_func
out = flash_attn_func(q, k, v, causal=True)
```

### 5. Using FA3 in Transformers

#### 5.1 At Load Time

```python
import torch
from transformers import AutoModelForCausalLM

# Direct FA3 backend (requires Hopper GPU)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    attn_implementation="flash_attention_3",
    torch_dtype=torch.bfloat16,  # FA3 requires fp16 or bf16
    device_map="auto"
)
```

**Important:** FA3 (and FA2) require fp16 or bf16. Cast the model before inference:
```python
model = model.to(dtype=torch.bfloat16)
```

#### 5.2 Runtime Switching

Switch attention backends without reloading the model:

```python
# After loading with eager, switch to FA3
model.set_attn_implementation("flash_attention_3")

# Switch to SDPA
model.set_attn_implementation("sdpa")

# Back to FA2
model.set_attn_implementation("flash_attention_2")
```

This is zero-overhead — the AttentionInterface simply redirects the forward call to the new backend's kernel.

#### 5.3 Kernels Hub (Pre-compiled Kernels)

The **Kernels** system downloads and loads pre-compiled attention kernels directly from the Hugging Face Hub at runtime. This avoids all packaging issues from mismatched PyTorch or CUDA versions.

```python
# Load a kernel from the Hub
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    attn_implementation="kernels-community/flash-attn2"
)
```

**Key benefits:**
- No need to install `flash-attn` package explicitly
- Kernels auto-register to AttentionInterface upon detection
- Requesting FA by name falls back to Hub kernel if local install missing
- Community-maintained kernels at `huggingface.co/kernels-community`

#### 5.4 FlashAttention Fallback Chain

When you request `attn_implementation="flash_attention_3"`:
1. Check if `flash_attention_3` is locally installed (pip package)
2. If not, check the Kernels Hub for pre-compiled FA3 kernel
3. If neither available, fall back to SDPA (silent, documented)

This means FA3 "just works" on Hopper GPUs without manual installation, as long as the Hub has a matching pre-compiled kernel for your CUDA/PyTorch version.

### 6. Backbone-Specific Attention for Multimodal Models

Multimodal models (like Chameleon, LLaVA, Idefics) use different backbones for each modality. The AttentionInterface supports per-backbone attention dispatch:

```python
# Assign different backends to vision vs text backbones
attention_implementation_per_backbone = {
    "vision_config": "sdpa",                    # Vision: SDPA (fp32 compatible)
    "text_config": "flash_attention_2"          # Text: FA2 (bf16 required)
}

model = AutoModelForImageTextToText.from_pretrained(
    "facebook/chameleon-7b",
    attn_implementation=attention_implementation_per_backbone
)
```

**Rules:**
- Keys must match sub-config names (`vision_config`, `text_config`, etc.)
- Each backbone gets its own attention function
- Mix and match — vision backbones often work better in fp32 (SDPA), text in fp16/bf16 (FA2/FA3)

### 7. Custom Attention Functions

Register custom attention backends through the `AttentionInterface.register()` API:

```python
from transformers import AttentionInterface, AttentionMaskInterface

# 1. Define custom attention function
def my_custom_attention(hidden_states, attention_mask, **kwargs):
    # Custom attention logic
    return attn_output

# 2. Register it
AttentionInterface.register("custom_fa", my_custom_attention)

# 3. Register matching mask function
AttentionMaskInterface.register("custom_fa_mask", my_mask_function)

# 4. Use it
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    attn_implementation="custom_fa"
)
```

**Critical:** If no mask function is registered for your custom attention, Transformers skips mask creation and passes `attention_mask=None`. Your function must handle causal/padding/packing constraints itself.

### 8. 4D Attention Mask Compatibility

Not all backends accept the same mask format:

| Backend | Mask Format Accepted |
|---------|---------------------|
| SDPA | Boolean or float 4D mask |
| Eager | Float 4D mask only |
| FlashAttention-2 | 2D padding mask (custom format) |
| FlexAttention | BlockMask (custom) |
| FlashAttention-3 | Same as FA2 (2D padding mask) |

**Common mistake:** Passing a 1/0 binary 4D mask to a float-expecting backend. Because the mask is *added* to attention scores, `1.0` adds a small bias instead of masking out. Use `0.0` for keep and `-inf` for mask-out in float mode.

### 9. Performance Characteristics

| Aspect | FA2 | FA3 | FA4 |
|--------|-----|-----|-----|
| GPU Generation | Ampere/Ada/Hopper | Hopper only | Hopper + Blackwell |
| FP16/BF16 | Full fwd+bwd | Full fwd+bwd | Full fwd+bwd |
| FP8 | No | Forward only | Forward only |
| Speedup (vs eager) | 2-4× | 3-5× (FP16), 6-8× (FP8) | 3-5× |
| Memory (vs eager) | ~50% less | ~50% less | ~50% less |
| Padding support | Manual pad/unpad | Manual pad/unpad | Manual pad/unpad |
| Installation | `flash-attn` | `flash-attn-3` | `flash-attn-4` |

**Key caveat:** For short sequences (<512 tokens), the overhead of kernel launch may make FA3/FA4 slower than SDPA. The benefit grows with sequence length — FA3 shines at 8K-128K tokens.

### 10. Zero-Cost Application for Beer

Beer's setup (no GPU, inference via HF Inference Providers):
- FA3/FA4 are **GPU-side optimizations** — they don't affect serverless inference costs
- The Inference Providers handle attention implementation server-side
- Beer benefits from FA3 when providers deploy Hopper GPUs
- For local CPU/GGUF inference: attention backend choice has minimal impact (CPUs use eager attention)
- The **Kernels Hub** concept is relevant: if Beer ever deploys a Space with a GPU, pre-compiled kernels remove build headaches

### Resources
- https://huggingface.co/docs/transformers/main/en/attention_interface
- https://github.com/Dao-AILab/flash-attention
- https://tridao.me/blog/2024/flash3/
- https://tridao.me/publications/flash3/flash3.pdf
- https://huggingface.co/kernels-community
- https://arxiv.org/abs/2205.14135 (FlashAttention)
