# HF Learnings — InferenceClient Image Generation Patterns

> **author:** SakThai  
> **license:** MIT  

## 2026-07-25: hf-inference-client-image-generation-patterns — Image Generation via Serverless Inference API (Topic #374)

### Summary
Deep dive into image generation through Hugging Face's serverless Inference API using `huggingface_hub`'s `InferenceClient`. Covers all four image generation methods (`text_to_image`, `image_to_image`, `inpaint`, `controlnet`), supported model families (Stable Diffusion 1.5/XL/3, Flux.1-dev, FLUX.1-schnell, Playground v2.5), parameter tuning per model family, streaming limitations, content filter handling, provider routing for image models, and cost/rate-limit considerations unique to image generation.

---

### 1. Core API Methods — Request/Response Architecture

All image generation methods in `InferenceClient` follow the same pattern:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(api_key="hf_...")  # or set HF_TOKEN env var

# All return PIL.Image by default (or raw bytes with output_type="bytes")
image = client.text_to_image(
    prompt="a photo of a cat",
    model="black-forest-labs/FLUX.1-dev",
    width=1024,
    height=1024,
    num_inference_steps=50,
    guidance_scale=3.5,
)
```

**Key architectural points:**

- **PIL.Image return by default** — `output_type` param controls: `"pil"` (default), `"bytes"` (raw PNG/JPEG bytes), or return raw Response object.
- **All params are model-specific** — the Inference API passes parameters as JSON body to the provider's inference endpoint. Unknown params are silently ignored by some providers, rejected by others.
- **Prompt weighting** — Some models support `(word:weight)` syntax (SD), others don't (Flux). Use `prompt_2` or `prompt_3` for T5-XXL encoder models.
- **Seed for reproducibility** — Always pass `seed=42` (or any int) for deterministic outputs. Omission = random seed.

---

### 2. Method-by-Method Reference

#### 2.1 `text_to_image()` — Text-to-Image

```python
def text_to_image(
    self,
    prompt: str,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    output_type: Literal["pil", "bytes", "raw"] = "pil",
    **kwargs,  # Model-specific extras
) -> Union[Image.Image, bytes, Response]:
```

**Model-specific defaults:**

| Model | Default Steps | Default Size | Guidance Scale | Notes |
|-------|--------------|-------------|---------------|-------|
| SD 1.5 | 25 | 512×512 | 7.5 | legacy, widely available |
| SDXL | 30 | 1024×1024 | 7.5 | 2x CLIP encoders |
| SD 3.5 | 40 | 1024×1024 | 4.5 | CFG rescale recommended |
| FLUX.1-dev | 50 | 1024×1024 | 3.5 | T5-XXL max_seq_length=512 |
| FLUX.1-schnell | 4 | 1024×1024 | 0.0 | distilled, 4 steps only |
| Playground v2.5 | 50 | 1024×1024 | 3.0 | edm-style scheduler |

**SD3/3.5 specific kwargs** (passed as `**kwargs`):
- `cfg_rescale=0.7` — CFG rescaling factor (0–1). Default 0.7 recommended for SD3.
- `max_sequence_length=256` — T5 context window (77 for CLIP-only, up to 512 for Flux).
- `prompt_2` / `prompt_3` — separate prompts for each text encoder.

**Flux-specific kwargs:**
- `max_sequence_length=512` — T5 context (default 512, reduce to 256 for speed).
- `guidance_scale=3.5` — Flux uses guidance, Schnell uses 0.0 (disabled).

#### 2.2 `image_to_image()` — Image-to-Image

```python
def image_to_image(
    self,
    prompt: str,
    image: Image.Image,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    strength: float = 0.8,  # How much to transform (0.0 = no change, 1.0 = full)
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    output_type: Literal["pil", "bytes", "raw"] = "pil",
    **kwargs,
) -> Union[Image.Image, bytes, Response]:
```

**Key parameter — `strength`:**
- `0.0` — no change (returns original image)
- `0.3` — subtle texture/style change
- `0.5` — moderate reinterpretation
- `0.8` (default) — significant change, preserves composition
- `1.0` — complete regeneration (same as text_to_image with noise)

**Image preparation:**
- The input `image` is converted to bytes internally (PNG format, auto-resized to model's target size if `height`/`width` not specified).
- Best practice: pre-process to the model's native resolution to avoid unexpected cropping.

#### 2.3 `inpaint()` — Inpainting

```python
def inpaint(
    self,
    prompt: str,
    image: Image.Image,
    mask_image: Image.Image,
    model: Optional[str] = None,
    negative_prompt: Optional[str] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    strength: Optional[float] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    output_type: Literal["pil", "bytes", "raw"] = "pil",
    **kwargs,
) -> Union[Image.Image, bytes, Response]:
```

**Mask requirements:**
- `mask_image` must be a **binary mask** (white = keep, black = inpaint).
- Automatically resized to match `image` dimensions.
- For best results with SD inpainting models (e.g., `runwayml/stable-diffusion-inpainting`), use a model fine-tuned specifically for inpainting rather than a base text-to-image model.

**Available inpainting models on serverless:**
- `runwayml/stable-diffusion-inpainting` — SD 1.5 inpaint fine-tune (fast, widely available)
- `stabilityai/stable-diffusion-xl-inpainting` — SDXL inpaint (higher quality)
- `black-forest-labs/FLUX.1-dev` — via FluxFillPipeline behind the API (auto-detected when mask provided with Flux model)

#### 2.4 `controlnet()` — ControlNet Conditioning

```python
def controlnet(
    self,
    prompt: str,
    image: Image.Image,  # Control image (depth, canny, pose, etc.)
    model: Optional[str] = None,
    controlnet_model: Optional[str] = None,  # ControlNet model to use
    negative_prompt: Optional[str] = None,
    height: Optional[int] = None,
    width: Optional[int] = None,
    num_inference_steps: Optional[int] = None,
    guidance_scale: Optional[float] = None,
    seed: Optional[int] = None,
    output_type: Literal["pil", "bytes", "raw"] = "pil",
    **kwargs,
) -> Union[Image.Image, bytes, Response]:
```

**ControlNet model selection:**
The `controlnet_model` parameter selects which control condition to apply. Common options:

| controlnet_model | Input Image Type | Use Case |
|-----------------|-----------------|----------|
| `lllyasviel/sd-controlnet-canny` | Canny edge map | Edge-preserving generation |
| `lllyasviel/sd-controlnet-depth` | Depth map | Structure-preserving |
| `lllyasviel/sd-controlnet-hed` | HED soft edge | Soft boundary preservation |
| `lllyasviel/sd-controlnet-openpose` | OpenPose skeleton | Pose-controlled generation |
| `lllyasviel/sd-controlnet-scribble` | Hand-drawn scribble | Rough sketch refinement |
| `lllyasviel/sd-controlnet-mlsd` | M-LSD line segments | Architectural straight lines |

**Note:** ControlNet via InferenceClient varies by provider. Some providers (e.g., Fal, Replicate) support it natively; others require the base model to be a ControlNet-compatible checkpoint. Not all serverless providers support all control types — test with `hf-inference-router-openai-compatible-endpoint` patterns for fallback.

---

### 3. Provider Routing for Image Models

Image generation models have different provider availability than text models.

**Default provider routing** (when `model` is specified):
1. The Hub maps the model ID to its available serverless providers.
2. Image models are typically NOT routed through text-inference providers (TGI, etc.).
3. They use dedicated image inference providers: Fal AI, Replicate, Banana, etc.

**Forcing a specific provider:**
```python
# Use the InferenceClient with provider hint via headers
image = client.text_to_image(
    "a cat",
    model="black-forest-labs/FLUX.1-dev",
    # Provider routing is automatic; use InferenceClient with
    # different API keys for different providers
)
```

**Provider availability matrix (common image models, 2026):**

| Model | Fal | Replicate | HF Native | Notes |
|-------|:---:|:---------:|:---------:|-------|
| SD 1.5 | ✅ | ✅ | ✅ | Available everywhere |
| SDXL | ✅ | ✅ | ✅ | HF native on T4 |
| SD 3.5 | ✅ | ✅ | Limited | Needs A10G+ |
| FLUX.1-dev | ✅ | ✅ | Limited | Needs A100 |
| FLUX.1-schnell | ✅ | ✅ | ✅ | 4-step, runs on T4 |
| Playground v2.5 | ✅ | ✅ | Limited | |

---

### 4. Error Handling Patterns

Image generation has distinct failure modes vs text inference:

#### 4.1 Content Filtering (NSFW Detection)

```python
from huggingface_hub import InferenceClient
from huggingface_hub.utils import HfHubHTTPError

client = InferenceClient()

try:
    image = client.text_to_image(
        "a violent scene",  # May trigger NSFW filter
        model="stabilityai/stable-diffusion-xl-base-1.0",
    )
except HfHubHTTPError as e:
    if "content_filter" in str(e).lower() or e.response.status_code == 422:
        print("NSFW content detected — try a different prompt")
    else:
        raise
```

**Content filter behavior by provider:**
- **HF Native:** Returns 422 with `"content_filter"` error message. Image may be a black placeholder.
- **Fal:** Returns success but with a safety check warning in response headers.
- **Replicate:** Returns a black image by default (configurable via `disable_safety_checker` param where supported).

#### 4.2 Image Size Validation

```python
# Model-specific size constraints:
# SD 1.5: 512×512, 512×768, 768×512 (preferred: 512×512)
# SDXL: 1024×1024, 1152×896, 896×1152 (preferred: 1024×1024)  
# SD 3.5: 1024×1024 (strict)
# Flux: 1024×1024, can vary but quality drops at extreme aspect ratios

# Best practice: validate before sending
VALID_SIZES_SDXL = [(1024, 1024), (1152, 896), (896, 1152), (1216, 832), (832, 1216)]

def validate_size(model_hint: str, width: int, height: int) -> bool:
    if "sdxl" in model_hint.lower() or "stable-diffusion-xl" in model_hint.lower():
        if (width, height) not in VALID_SIZES_SDXL:
            print(f"Warning: SDXL prefers specific sizes, got {width}×{height}")
            return False
    return True
```

#### 4.3 Rate Limiting and Cost

Image generation is significantly more expensive than text:
- **HF Free tier:** ~3–5 image generations per hour (varies by model, GPU availability)
- **Paid tier:** Pay-per-image (Fal: ~$0.002–0.05/image depending on model and steps)
- **Rate limit errors:** 429 status → retry with exponential backoff (same as text)

```python
import time
from huggingface_hub.utils import HfHubHTTPError

def generate_with_retry(client, prompt, model, max_retries=3):
    for attempt in range(max_retries):
        try:
            return client.text_to_image(prompt, model=model)
        except HfHubHTTPError as e:
            if e.response.status_code == 429:
                wait = 2 ** attempt * 5
                print(f"Rate limited, waiting {wait}s...")
                time.sleep(wait)
                continue
            raise
    raise Exception("Max retries exceeded")
```

---

### 5. Output Formats and Optimization

**Output byte format negotiation:**
- Default output is PNG (lossless, large).
- JPEG yields smaller payloads (2–5× smaller) with quality loss.
- Not all models support format selection — falls back to PNG when unsupported.

```python
# Request JPEG for faster transfers
image = client.text_to_image(
    "a cat",
    model="black-forest-labs/FLUX.1-dev",
    output_type="bytes",  # Get raw bytes
)
# The API defaults to PNG; some providers accept output_format param
# but this is NOT standardized across providers.
```

**In-memory optimization:**
```python
from io import BytesIO

# Get bytes, not PIL (avoids PIL decode if you're saving to disk)
raw_bytes = client.text_to_image("a cat", model="...", output_type="bytes")

# Write directly without PIL intermediary
with open("output.png", "wb") as f:
    f.write(raw_bytes)

# Or decode only when needed
from PIL import Image
img = Image.open(BytesIO(raw_bytes))
```

---

### 6. Streaming — NOT Supported for Images

Unlike text generation where `stream=True` yields token-by-token output, **image generation does NOT support streaming** in the Inference API. The entire image is returned as a complete binary payload.

**Workaround for progress feedback:**
```python
import threading
import time

def generate_with_progress(client, prompt, model):
    result = [None]
    
    def _run():
        result[0] = client.text_to_image(prompt, model=model)
    
    t = threading.Thread(target=_run)
    t.start()
    
    while t.is_alive():
        print(".", end="", flush=True)
        time.sleep(1)
    
    print(" Done!")
    return result[0]
```

---

### 7. Multi-Model Ensembling Pattern

Combine multiple image models via parallel calls for diversity:

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def ensemble_generate(prompt: str, models: list[str], n_images: int = 4):
    """Generate from multiple models in parallel and collect results."""
    client = InferenceClient()
    results = []
    
    with ThreadPoolExecutor(max_workers=len(models)) as executor:
        futures = {
            executor.submit(client.text_to_image, prompt, model=m): m
            for m in models
        }
        for future in as_completed(futures):
            model = futures[future]
            try:
                img = future.result()
                results.append((model, img))
            except Exception as e:
                print(f"{model} failed: {e}")
    
    return results
```

---

### 8. Model Selection Strategy

**Fastest (cheapest):**
- `stabilityai/stable-diffusion-2-1` — ~2s on T4, widely available
- `black-forest-labs/FLUX.1-schnell` — 4 steps, ~3s, excellent quality-to-speed ratio

**Best quality:**
- `black-forest-labs/FLUX.1-dev` — 50 steps, best overall quality, ~15–30s
- `stabilityai/stable-diffusion-3.5-large` — good quality, ~10–15s
- `playgroundai/playground-v2.5-1024px-aesthetic` — excellent aesthetics, ~10s

**Free tier optimized:**
- Stick to models ≤ 2GB (SD 1.5, SDXL-turbo, FLUX.1-schnell)
- Reduce steps: SD 1.5 at 15 steps, SDXL at 20 steps, Schnell at 4 steps

---

### Summary of Key Learnings

1. **No streaming** — image generation is always a single-shot response.
2. **Content filters vary** by provider; handle 422 errors gracefully.
3. **Size constraints** are model-specific — SDXL ≠ SD 1.5 ≠ Flux.
4. **Seed is required** for reproducibility; omit for randomness.
5. **PNG default** — use `output_type="bytes"` and save directly for disk efficiency.
6. **Provider routing** is implicit — you get whatever provider the Hub assigns for that model.
7. **Rate limits** are stricter for images (higher compute cost per call).
8. **Prompt engineering** differs per family — Flux needs `max_sequence_length`, SD3 needs `cfg_rescale`.
9. **Parallel execution** is safe and recommended for ensemble/multi-model workflows.
10. **Inpainting masks** must be binary (white=keep, black=fill); auto-resized to match input.
