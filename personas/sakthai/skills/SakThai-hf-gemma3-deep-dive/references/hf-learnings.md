# HF Learnings — Gemma 3 on Hugging Face Deep Dive

## 2026-07-25: hf-gemma3-deep-dive — Google Gemma 3 Multimodal Open Model Family (Topic #356)

### Summary

Complete deep dive into **Gemma 3** — Google's third-generation open model family released March 2025, built from the same research and technology as Gemini. Gemma 3 is the first Gemma generation to be **natively multimodal** (text + image input, text output) for the 4B, 12B, and 27B sizes, with a 1B text-only variant. Key innovations: **Deep Gemma** text backbone with grouped-query attention (GQA), 8× linear RoPE scaling for 128K context, sliding window attention (1,024 tokens), and a **SigLIP** vision encoder with 256 token image representations. All instruction-tuned variants are TGI-compatible and available via HF Inference API (serverless and Endpoints). The 27B model tops the family with 2000+ HF likes, 14T training tokens, and 62 transformer layers.

---

### 1. Model Family Overview

| Model | Params | Pipeline | Context | Training Tokens | Downloads | Likes |
|-------|--------|----------|---------|----------------|-----------|-------|
| google/gemma-3-270m | 270M | text-generation | 32K | — | 1.89M | 1,054 |
| google/gemma-3-270m-it | 270M | text-generation | 32K | — | 958K | 607 |
| google/gemma-3-1b-pt | 1B | text-generation | 32K | 2T | 62K | 196 |
| google/gemma-3-1b-it | 1B | text-generation | 32K | 2T | 3.22M | 1,065 |
| google/gemma-3-4b-pt | 4B | image-text-to-text | 128K | 4T | 66K | 158 |
| google/gemma-3-4b-it | 4B | image-text-to-text | 128K | 4T | 2.20M | 1,429 |
| google/gemma-3-12b-pt | 12B | image-text-to-text | 128K | 12T | 26K | 91 |
| google/gemma-3-12b-it | 12B | image-text-to-text | 128K | 12T | 1.21M | 792 |
| google/gemma-3-27b-pt | 27B | image-text-to-text | 128K | 14T | 11K | 124 |
| google/gemma-3-27b-it | 27B | image-text-to-text | 128K | 14T | 854K | 2,002 |

**Key:** `-pt` = pre-trained (base), `-it` = instruction-tuned. The 270M variants are text-only. All others multimodal (text + image). All gated under Gemma license — requires HF login + agreement.

---

### 2. Architecture (27B Reference)

#### 2.1 Text Backbone (Deep Gemma)

| Parameter | Value |
|-----------|-------|
| Model type | `gemma3_text` |
| Hidden size | 5,376 |
| Layers | 62 |
| Attention heads | 32 |
| KV heads | 16 (GQA ratio: 2×) |
| Head dim | 128 |
| Intermediate size | 21,504 (GLU: gate/up/down) |
| RoPE scaling | Linear, factor=8.0 |
| Sliding window | 1,024 tokens |
| Query pre-attention scalar | 168 |
| EOS tokens | [1, 106] |
| Vocab size | 262,144 |
| Torch dtype | bfloat16 |

**Architecture innovations:**
- **Deep Gemma**: The text backbone uses a very deep + narrow design (62 layers, 5,376 hidden) with **GQA** (2 heads per KV head) for efficient inference.
- **Sliding window attention**: Layer-local attention window of 1,024 tokens — only the most recent tokens attend to each other fully, while global context is preserved via the KV cache structure. This reduces the quadratic cost of full 128K attention.
- **8× RoPE linear scaling**: Extends the context window from the native 16K pre-trained length to 128K without position interpolation (uses simple frequency scaling).
- **Query pre-attention scalar**: A learned constant (168) that scales query vectors before attention, stabilizing training for deep models — a Gemma-specific technique.
- **GLU MLP**: Gated Linear Unit with gate/up/down projections (ratio ~4× hidden size).

#### 2.2 Vision Encoder (SigLIP)

| Parameter | Value |
|-----------|-------|
| Model type | `siglip_vision_model` |
| Hidden size | 1,152 |
| Layers | 27 |
| Attention heads | 16 |
| Image size | 896 × 896 |
| Patch size | 14 × 14 |
| Patches per image | 4,096 (64²) |
| Tokens per image | 256 (compressed from 4,096 via spatial pooling) |
| Vision use head | False (no classification head) |

**Vision processing:**
1. Input image resized to 896×896
2. Split into 14×14 patches = 4,096 patches
3. Encoded by SigLIP vision encoder (27-layer ViT)
4. 4,096 patch tokens compressed to **256 visual tokens** via spatial pooling
5. Inserted into text sequence at `<image_token_index>` (262144) positions, delimited by `boi_token` (255999) and `eoi_token` (256000)

#### 2.3 Multimodal Integration

- **Architecture class**: `Gemma3ForConditionalGeneration` (transformers)
- Image encoder output (256 tokens) is projected to text hidden dimension (5,376) and concatenated into the text token sequence
- **mm_tokens_per_image**: 256 — each image consumes exactly 256 positions in the token sequence
- No cross-attention between vision and text; images are embedded as a **prefix** in the token space
- The text backbone handles both text and projected visual embeddings uniformly

---

### 3. Performance Benchmarks

#### 3.1 Reasoning (27B Instruct)

| Benchmark | Score |
|-----------|-------|
| HellaSwag (10-shot) | 85.6 |
| BoolQ (0-shot) | 82.4 |
| PIQA (0-shot) | 83.3 |
| TriviaQA (5-shot) | 85.5 |
| ARC-c (25-shot) | 70.6 |
| WinoGrande (5-shot) | 78.8 |
| BIG-Bench Hard (few-shot) | 77.7 |
| DROP (1-shot) | 77.2 |

#### 3.2 STEM & Code

| Benchmark | 4B | 12B | 27B |
|-----------|:--:|:---:|:---:|
| MMLU (5-shot) | 59.6 | 74.5 | **78.6** |
| MATH (4-shot) | 24.2 | 43.3 | **50.0** |
| GSM8K (8-shot) | 38.4 | 71.0 | **82.6** |
| HumanEval (0-shot) | 36.0 | 45.7 | **48.8** |
| MBPP (3-shot) | 46.0 | 60.4 | **65.6** |

#### 3.3 Multimodal (Vision)

| Benchmark | 4B | 12B | 27B |
|-----------|:--:|:---:|:---:|
| DocVQA (val) | 72.8 | 82.3 | **85.6** |
| MMMU (pt) | 39.2 | 50.3 | **56.1** |
| TextVQA (val) | 58.9 | 66.5 | **68.6** |
| ChartQA | 63.6 | 74.7 | **76.3** |
| AI2D | 63.2 | 75.2 | **79.0** |
| VQAv2 | 63.9 | 71.2 | **72.9** |

#### 3.4 Multilingual (140+ languages)

| Benchmark | 27B |
|-----------|:---:|
| MGSM | 74.3 |
| Global-MMLU-Lite | 75.7 |
| XQuAD (all) | 76.8 |

---

### 4. Inference Patterns

#### 4.1 Via Transformers Pipeline

```python
from transformers import pipeline
import torch

# Multimodal (image-text-to-text) pipeline
pipe = pipeline(
    "image-text-to-text",
    model="google/gemma-3-27b-it",
    device="cuda",
    torch_dtype=torch.bfloat16
)

# With chat template (required for instruction-tuned)
messages = [
    {
        "role": "system",
        "content": [{"type": "text", "text": "You are a helpful assistant."}]
    },
    {
        "role": "user",
        "content": [
            {"type": "image", "url": "https://example.com/image.jpg"},
            {"type": "text", "text": "Describe this image in detail."}
        ]
    }
]

output = pipe(text=messages, max_new_tokens=200)
print(output[0]["generated_text"][-1]["content"])
```

#### 4.2 Via AutoProcessor + Model

```python
from transformers import AutoProcessor, Gemma3ForConditionalGeneration
import torch

model_id = "google/gemma-3-27b-it"

model = Gemma3ForConditionalGeneration.from_pretrained(
    model_id, device_map="auto"
).eval()

processor = AutoProcessor.from_pretrained(model_id)

messages = [
    {"role": "system", "content": [{"type": "text", "text": "You are a helpful assistant."}]},
    {"role": "user", "content": [
        {"type": "image", "image": "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/bee.jpg"},
        {"type": "text", "text": "Describe this image in detail."}
    ]}
]

inputs = processor.apply_chat_template(
    messages, add_generation_prompt=True, tokenize=True,
    return_dict=True, return_tensors="pt"
).to(model.device, dtype=torch.bfloat16)

input_len = inputs["input_ids"].shape[-1]
with torch.inference_mode():
    generation = model.generate(**inputs, max_new_tokens=100, do_sample=False)
    generation = generation[0][input_len:]

decoded = processor.decode(generation, skip_special_tokens=True)
print(decoded)
```

#### 4.3 Via HF InferenceClient (Serverless / Providers)

```python
from huggingface_hub import InferenceClient

client = InferenceClient("google/gemma-3-27b-it")

# Text-only usage (instruction-tuned models need chat format)
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Explain quantum computing in simple terms."}
]

response = client.chat.completions.create(
    messages=messages,
    max_tokens=500,
    temperature=0.7,
)
print(response.choices[0].message.content)
```

**Note:** Gemma 3 models are **gated** — you must:
1. Log into HF (`huggingface-cli login`)
2. Accept the license at https://huggingface.co/google/gemma-3-27b-it
3. Use a valid HF token with access granted

#### 4.4 Via TGI (Text Generation Inference)

All Gemma 3 instruction-tuned models are **TGI-compatible** (`text-generation-inference` tag present). Deploy via Inference Endpoints or self-hosted TGI:

```bash
# Self-hosted TGI
docker run --gpus all -p 8080:80 \
  -v ~/.cache/huggingface:/data \
  ghcr.io/huggingface/text-generation-inference:latest \
  --model-id google/gemma-3-4b-it
```

---

### 5. Function Calling & Tool Use

Gemma 3's default chat template does **not** include native tool-use tokens. However, Transformers supports function calling through its **generic tool-use framework**, which automatically wraps user-provided tools into the chat template. To use Gemma 3 with tools:

```python
from transformers import pipeline
import torch

pipe = pipeline(
    "text-generation",  # use text-generation, not image-text-to-text for tools
    model="google/gemma-3-1b-it",
    device="cuda",
    torch_dtype=torch.bfloat16
)

# Define tools
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name"
                    }
                },
                "required": ["location"]
            }
        }
    }
]

# Transformers handles the tool-use template automatically
messages = [
    {"role": "system", "content": "You are a helpful assistant with tool access."},
    {"role": "user", "content": "What's the weather in Tokyo?"}
]

# Apply with tool support
outputs = pipe(
    messages,
    tools=tools,
    max_new_tokens=256
)
```

**Limitation:** For the 4B+ multimodal variants, tool-use with image inputs is not directly supported through the simple function-calling interface — use the text-only pipeline tag for tool interactions.

---

### 6. GGUF & Local Deployment

Community GGUF quantizations available via `bartowski` and others:

| Repo | Base Model |
|------|-----------|
| bartowski/google_gemma-3-1b-it-GGUF | 1B IT |
| bartowski/google_gemma-3-4b-it-GGUF | 4B IT |
| bartowski/google_gemma-3-12b-it-GGUF | 12B IT |
| bartowski/google_gemma-3-27b-it-GGUF | 27B IT |

For **zero-cost local deployment** (Beer's context): the 1B model runs on CPU/RAM with minimal resources. The 4B fits in 4GB RAM with Q4 quantization. Use llama.cpp or ollama:

```bash
# Via ollama
ollama pull gemma3:1b
ollama pull gemma3:4b

# Via llama.cpp direct
wget https://huggingface.co/bartowski/google_gemma-3-4b-it-GGUF/resolve/main/gemma-3-4b-it-Q4_K_M.gguf
./llama-cli -m gemma-3-4b-it-Q4_K_M.gguf -p "Hello"
```

---

### 7. Key Insights & Strategic Value

1. **Best free-tier multimodal model**: The 1B/text-only variants are accessible via HF free Inference API (text-generation pipeline). For image tasks, the 4B is available through serverless Inference with a free account.

2. **128K context is transformative**: With 8× RoPE linear scaling, Gemma 3 handles long documents, codebases, and multi-turn conversations without context truncation — critical for agent memory.

3. **Sliding window for efficiency**: The 1,024-token sliding window means KV-cache requirements are bounded, making long-context inference more memory-efficient than full-attention models.

4. **GQA is inference-friendly**: 2× GQA ratio means KV-cache is half the size of MHA, directly reducing memory pressure for local deployment.

5. **Function calling via framework**: No native tool-use tokens, but Transformers' tool-use framework bridges the gap. For production agent systems, consider fine-tuning with tool-use data or using the framework's auto-template.

6. **Community momentum**: 3.2M downloads for 1B IT, 2.2M for 4B IT, 2,000+ likes for 27B IT — Gemma 3 is among the most popular open model families on HF.

---

### 8. Related Topics

- `gf-gemma3` / `hf-gemma3-quantization-deep-dive` — Deeper dive into AQLM/AWQ/GGUF quantized variants and their quality benchmarks
- `hf-gemma3-fine-tuning` — LoRA fine-tuning of Gemma 3 with PEFT/TRL for custom tool-use
- `hf-gemma3-vs-llama4-comparison` — Direct comparison with Llama 4 Scout/Maverick for agent use cases
