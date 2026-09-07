---
name: SakThai-hf-transformers-qwen2-5-vl-deep-dive
description: ">-   Complete reference on Qwen2.5-VL — Alibabas flagship vision-language model   integrated in Hugging Face Transformers. Covers architecture, MRoPE, dynamic   resolution, video understanding, agentic capabilities, inference patterns,   quantization"
---

# Qwen2.5-VL Deep Dive

## Overview

**Qwen2.5-VL** is a multimodal vision-language model family by the Qwen Team (Alibaba), released January 2025. Available in 3 sizes (3B, 7B, 72B), pretrained on **4.1 trillion tokens**. It is the successor to Qwen2-VL with significant improvements in visual understanding, video comprehension, and agentic capabilities.

**Hugging Face Transformers integration**: Full native support via `Qwen2_5_VLForConditionalGeneration`, `Qwen2_5_VLProcessor`, and `Qwen2_5_VLConfig`. Pipeline tag: `image-text-to-text`.

**Model collection**: [Qwen2.5-VL on HF](https://huggingface.co/collections/Qwen/qwen25-vl-679742ff31a10bf973f0b768)

---

## Architecture

### Two-Component Design

Qwen2.5-VL follows the standard VLM architecture — vision encoder + LLM backbone:

1. **Vision Encoder** (ViT with window attention)
   - 32 layers, hidden_size=3584, 16 heads
   - Patch size: 14×14
   - **Window attention** strategically applied (full attention at layers [7, 15, 23, 31] only)
   - SwiGLU activation + RMSNorm (aligned with Qwen2.5 LLM)
   - Temporal patch size: 2 (3D patch embedding for video)
   - Spatial merge size: 2 (reduces visual tokens by merging neighboring patches)

2. **LLM Backbone** — Qwen2.5-based text decoder
   - Processes merged visual + text tokens
   - Chat template: Qwen2 format (`<|im_start|>`, `<|im_end|>`)

### Key Architectural Innovations

| Feature | Description |
|---------|-------------|
| **Window Attention in ViT** | Only 4/32 layers use full attention; rest are windowed. Speeds up both training and inference vs. full-attention ViT. |
| **3D Patch Embedding** | 3D patches (spatial × temporal) for video. `temporal_patch_size=2` means 2 consecutive frames share a patch. |
| **Dynamic FPS Sampling** | Training samples videos at varying frame rates; model learns to handle slow/fast motion. |
| **MRoPE (Multi-Resolution RoPE)** | RoPE with 3 independent sections: height, width, time. Absolute time IDs enable precise temporal grounding. |
| **Dynamic Resolution** | Input images at native resolution; `min_pixels`/`max_pixels` controls compute budget. |
| **Spatial Merge** | `spatial_merge_size=2` halves visual token count by merging 2×2 patch neighborhoods. |

### Configuration

**`Qwen2_5_VLConfig`** — top-level config combining text + vision:

```python
from transformers import Qwen2_5_VLConfig, Qwen2_5_VLForConditionalGeneration

config = Qwen2_5_VLConfig()
model = Qwen2_5_VLForConditionalGeneration(config)
```

Key fields:
- `text_config` — config for the Qwen2.5 text backbone
- `vision_config` — config for the ViT encoder
- `image_token_id` (151655) — placeholder token for images
- `video_token_id` (151656) — placeholder token for videos
- `vision_start_token_id` (151652) / `vision_end_token_id` (151653)

**`Qwen2_5_VLVisionConfig`** — vision encoder details:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `depth` | 32 | ViT layers |
| `hidden_size` | 3584 | Hidden dimension |
| `intermediate_size` | 3420 | MLP expansion |
| `num_heads` | 16 | Attention heads |
| `patch_size` | 14 | Spatial patch size |
| `temporal_patch_size` | 2 | Temporal patch size (3D) |
| `spatial_merge_size` | 2 | Token merging factor |
| `window_size` | 112 | Window attention size |
| `fullatt_block_indexes` | [7, 15, 23, 31] | Layers with full attention |
| `out_hidden_size` | 3584 | Output projection dim |

---

## Capabilities

### 1. Visual Understanding
- Recognizes objects, plants, animals, landmarks, products
- Analyzes text, charts, icons, graphics, and layouts
- Strong OCR (OCRBench 864 — SOTA among open 7B VLMs)

### 2. Video Understanding
- Comprehends videos **over 1 hour** long
- **Event capture**: pinpoints exact moments via temporal grounding
- Dynamic FPS sampling adapts to different frame rates

### 3. Visual Agent / Grounding
- Generates **bounding boxes** and **point coordinates**
- Structured JSON output for coordinates and attributes
- Can be used for computer-use and phone-use agents
- Agent benchmarks: ScreenSpot 84.7%, Android Control High 60.1%

### 4. Structured Output
- Invoice, form, and table data extraction
- JSON-formatted attribute outputs
- Supports complex nested schemas

---

## Inference

### Requirements

```bash
pip install git+https://github.com/huggingface/transformers accelerate
pip install qwen-vl-utils[decord]==0.0.8
```

> Requires transformers ≥5.0.0 (or build from source for `qwen2_5_vl` architecture key). Older versions raise `KeyError: 'qwen2_5_vl'`.

### Pipeline API (Simplest)

```python
from transformers import pipeline

pipe = pipeline(
    task="image-text-to-text",
    model="Qwen/Qwen2.5-VL-7B-Instruct",
    device=0,
)

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "https://example.com/photo.jpg"},
            {"type": "text", "text": "Describe this image."},
        ],
    }
]
output = pipe(text=messages, max_new_tokens=128, return_full_text=False)
print(output[0]["generated_text"])
```

### AutoModel API (Full Control)

```python
import torch
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info

model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    torch_dtype="auto",
    device_map="auto",
)

# Flash Attention 2 recommended for multi-image/video
# model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
#     "Qwen/Qwen2.5-VL-7B-Instruct",
#     torch_dtype=torch.bfloat16,
#     attn_implementation="flash_attention_2",
#     device_map="auto",
# )

processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "https://example.com/photo.jpg"},
            {"type": "text", "text": "Describe this image."},
        ],
    }
]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
image_inputs, video_inputs = process_vision_info(messages)
inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                   padding=True, return_tensors="pt").to(model.device)

generated_ids = model.generate(**inputs, max_new_tokens=128)
generated_ids_trimmed = [out_ids[len(in_ids):] for in_ids, out_ids
                         in zip(inputs.input_ids, generated_ids)]
output_text = processor.batch_decode(generated_ids_trimmed,
                                     skip_special_tokens=True,
                                     clean_up_tokenization_spaces=False)
print(output_text)
```

### Image Resolution Control

Control compute vs. quality via pixel budget:

```python
# Default: 4-16384 visual tokens per image
processor = AutoProcessor.from_pretrained("Qwen/Qwen2.5-VL-7B-Instruct")

# Constrained: 256-1280 tokens (faster, less memory)
min_pixels = 256 * 28 * 28
max_pixels = 1280 * 28 * 28
processor = AutoProcessor.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    min_pixels=min_pixels,
    max_pixels=max_pixels,
)

# Or exact dimensions (must be multiple of 28)
# In message: {"type": "image", "image": url, "resized_height": 280, "resized_width": 420}
```

### Video Inference

```python
messages = [
    {
        "role": "user",
        "content": [
            {"type": "video", "video": "/path/to/video.mp4", "fps": 1.0},
            {"type": "text", "text": "What happened in the video?"},
        ],
    }
]

text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
image_inputs, video_inputs, video_kwargs = process_vision_info(messages, return_video_kwargs=True)
inputs = processor(text=[text], images=image_inputs, videos=video_inputs,
                   fps=1.0, padding=True, return_tensors="pt",
                   **video_kwargs).to(model.device)

output_ids = model.generate(**inputs, max_new_tokens=128)
```

Video inputs can be: local file path, URL list (frames), or URL to .mp4.

**Backend compatibility** for video URLs:

| Backend | HTTP | HTTPS |
|---------|------|-------|
| torchvision ≥ 0.19.0 | ✅ | ✅ |
| torchvision < 0.19.0 | ❌ | ❌ |
| decord | ✅ | ❌ |

Override with env var: `FORCE_QWENVL_VIDEO_READER=decord` or `FORCE_QWENVL_VIDEO_READER=torchvision`

### Multi-Image & Batch Inference

**Multiple images in one turn** — just add more `{"type": "image", ...}` entries. Label with `add_vision_id=True` to auto-generate "Picture 1:", "Picture 2:" etc.

**Batch** — pass a list of message lists:

```python
messages_batch = [messages1, messages2]  # each is a list of turns
texts = [processor.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
         for m in messages_batch]
# ... process as above with padding=True
```

### Quantization

```python
from transformers import Qwen2_5_VLForConditionalGeneration, TorchAoConfig

quantization_config = TorchAoConfig("int4_weight_only", group_size=128)
model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2.5-VL-7B-Instruct",
    device_map="auto",
    quantization_config=quantization_config,
)
```

Also supports: bitsandbytes (8-bit/4-bit), GPTQ, AWQ.

### Structured Output (Grounding)

Qwen2.5-VL can output bounding boxes in JSON format:

```
Detect all motorcyclists and return their locations.
{"bbox_2d": [x1, y1, x2, y2], "label": "motorcyclist", "sub_label": "wearing helmet"}
```

The model natively produces stable JSON for coordinates and attributes without fine-tuning.

---

## Performance Benchmarks (7B Instruct)

### Image Tasks

| Benchmark | Qwen2.5-VL-7B | GPT-4o-mini | Comparison |
|-----------|:-------------:|:-----------:|:----------:|
| MMMU (val) | 58.6 | **60.0** | ~GPT-4o-mini |
| MMMU-Pro (val) | **41.0** | 37.6 | +3.4 |
| DocVQA (test) | **95.7** | — | +1.2 vs Qwen2-VL |
| InfoVQA (test) | **82.6** | — | +6.1 vs Qwen2-VL |
| ChartQA (test) | **87.3** | — | +4.3 vs Qwen2-VL |
| OCRBench | **864** | 785 | +79 |
| MathVista | **68.2** | 52.4 | +15.8 |
| MathVision | **25.07** | — | +8.8 vs Qwen2-VL |
| MMVet (GPT-4-Turbo) | **67.1** | 66.9 | +0.2 |

### Video Tasks

| Benchmark | Qwen2.5-VL-7B |
|-----------|:-------------:|
| Video-MME (wo/w subs) | 65.1 / 71.6 |
| MVBench | 69.6 |
| PerceptionTest (test) | 70.5 |
| MLVU | 70.2 |
| TempCompass | 71.7 |
| LongVideoBench | 54.7 |
| CharadesSTA (mIoU) | 43.6 |

---

## Long-Context & YaRN

The default config supports 32,768 tokens. For longer contexts:

```json
{
    "type": "yarn",
    "mrope_section": [16, 24, 24],
    "factor": 4,
    "original_max_position_embeddings": 32768
}
```

**Warning**: YaRN degrades temporal/spatial localization. For long video inputs, directly increase `max_position_embeddings` (MRoPE is economical with IDs).

---

## Common Pitfalls

1. **`KeyError: 'qwen2_5_vl'`** — transformers version too old. Build from source: `pip install git+https://github.com/huggingface/transformers`
2. **Video URL fails** — HTTPS URLs need torchvision ≥ 0.19.0. Use local files or downgrade to HTTP.
3. **Memory spikes** — high-resolution images generate many visual tokens. Always set `min_pixels`/`max_pixels`.
4. **Batch padding confusion** — when batching mixed image/no-image messages, padding is applied. Set `padding=True` and ensure `attention_mask` is used.
5. **Grounding prompts** — use explicit instruction like "return in JSON format with bbox_2d" for structured output.

---

## References

- [Transformers Docs — Qwen2.5-VL](https://huggingface.co/docs/transformers/en/model_doc/qwen2_5_vl)
- [Model Card — Qwen2.5-VL-7B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-7B-Instruct)
- [Blog Post — Qwen2.5-VL](https://qwenlm.github.io/blog/qwen2.5-vl/)
- [GitHub — Qwen2.5-VL](https://github.com/QwenLM/Qwen2.5-VL)
- [Qwen2-VL Paper](https://arxiv.org/abs/2409.12191)
- [Qwen-VL Paper](https://arxiv.org/abs/2308.12966)
