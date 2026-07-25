# HF Learnings — hf-transformers-tipsv2

## 2026-07-25: TIPSv2 — Google DeepMind Vision-Language Encoder (Topic #316 — New)

### Summary
Comprehensive deep-dive into **TIPSv2** (Text-Image Pre-training with Spatial awareness v2) — Google DeepMind's contrastive vision-language encoder family, added in Transformers v5.14.0 (July 2026). Covers architecture, dual-class-token design, iBOT++ pretraining, zero-shot classification, DPT dense prediction head, and usage patterns from the official Transformers docs.

### Sources
- Transformers docs (TIPSv2): https://huggingface.co/docs/transformers/main/en/model_doc/tipsv2
- Transformers docs (TIPSv2 DPT): https://huggingface.co/docs/transformers/main/en/model_doc/tipsv2_dpt
- Paper: https://huggingface.co/papers/2604.12012
- HF Collection (checkpoints): https://huggingface.co/collections/google/tipsv2
- GitHub: https://github.com/google-deepmind/tips
- Transformers v5.14.0 release notes

---

### 1. What Is TIPSv2?

TIPSv2 (Text-Image Pre-training with Spatial awareness v2) is a **family of contrastive vision-language encoders** developed by Google DeepMind and added to Transformers in v5.14.0. It is designed to address a critical weakness in prior vision-language models: **aligning dense patch representations with text embeddings of corresponding concepts**.

Key differentiators:
- **Patch-text alignment** — individual image patches meaningfully match corresponding text concepts, not just whole images
- **Dual class tokens** — two separate pooling tokens supervised by different caption sources (web alt-text vs synthetic captions)
- **iBOT++ objective** — unmasked tokens also contribute to the masked image modeling loss
- **Strong backbone reuse** — the vision encoder serves as backbone for depth, normals, and semantic segmentation via a DPT head

---

### 2. Architecture

TIPSv2 follows a **dual-encoder contrastive architecture** (like CLIP, SigLIP) with a vision tower and a text tower:

| Component | Details |
|-----------|---------|
| **Vision encoder** | ViT-based (e.g., ViT-B/14 at 448×448) with register tokens |
| **Text encoder** | Transformer decoder (12 layers, 768 hidden, ReLU activation) |
| **Pooling** | Two class tokens + masked mean pooling for text |
| **Projection** | Linear projection to shared embedding space |
| **Temperature** | Learnable scalar initialized at ~0.005 |
| **Image size** | 448×448 (B14 variant uses 14×14 patches = 32×32 grid) |

#### 2.1 Dual Class Tokens

TIPSv2 repurposes the DINOv2 register token mechanism to create **two class tokens**:

| Token | Position | Supervision Source |
|-------|----------|--------------------|
| CLS token 1 | `sequence[:, 0]` | Web alt-text captions (CLIP-style) |
| CLS token 2 | `sequence[:, 1:1+num_registers]` | PaliGemma synthetic captions |

This dual supervision enables the model to capture complementary semantic signals — one from noisy web text, another from detailed synthetic descriptions.

#### 2.2 Vision Encoder Config (Tipsv2VisionConfig)

Default config for `google/tipsv2-b14`:

| Parameter | Value |
|-----------|-------|
| hidden_size | 768 |
| num_hidden_layers | 12 |
| num_attention_heads | 12 |
| mlp_ratio | 4 (hidden 3072) |
| hidden_act | gelu |
| image_size | 448 |
| patch_size | 14 |
| num_register_tokens | 1 |
| qkv_bias | True |
| layerscale_value | 1.0 |
| use_swiglu_ffn | False |
| apply_layernorm | True |

#### 2.3 Text Encoder Config (Tipsv2TextConfig)

| Parameter | Value |
|-----------|-------|
| vocab_size | 32000 |
| hidden_size | 768 |
| num_hidden_layers | 12 |
| num_attention_heads | 12 |
| intermediate_size | 3072 |
| hidden_act | relu |
| max_position_embeddings | 64 |
| scale_sqrt_depth | True |
| pooling_epsilon | 1e-8 |

Note: The text encoder uses **ReLU activation** (not GELU) and **sinusoidal position embeddings** scaled by `sqrt(hidden_size)`.

---

### 3. iBOT++ Pretraining Objective

The key innovation in TIPSv2's pretraining:

- **Standard iBOT** (image BERT pre-training with Online Tokenizer): masks patches and predicts the teacher's representations for masked patches only
- **iBOT++** (proposed by TIPSv2): **unmasked tokens also contribute directly to the loss**, dramatically enhancing patch-text alignment

The student model's patch-text alignment actually **surpasses the teacher's** after this distillation procedure — a surprising result that drives the design.

Additional pretraining improvements:
- Modified EMA (exponential moving average) setup in the learning recipe
- Caption sampling strategy — benefits from synthetic captions at **different granularities**

---

### 4. Available Models & Checkpoints

All available under the `google/tipsv2` collection on HF Hub:

| Model ID | Description |
|----------|-------------|
| `google/tipsv2-b14` | Base TIPSv2 (ViT-B/14) for zero-shot classification + retrieval |
| `google/tipsv2-b14-dpt` | TIPSv2 + DPT head for depth/normal/segmentation |
| `google/tipsv2-l16` | Large variant (ViT-L/16) — higher capacity |
| `google/tipsv2-l16-dpt` | Large + DPT head |

---

### 5. Usage Patterns

#### 5.1 Zero-Shot Image Classification (pipeline)

```python
from transformers import pipeline

classifier = pipeline(
    task="zero-shot-image-classification",
    model="google/tipsv2-b14",
    device_map="auto"
)
out = classifier(
    "https://huggingface.co/datasets/huggingface/documentation-images/resolve/main/pipeline-cat-chonk.jpeg",
    candidate_labels=["a photo of a cat", "a photo of a dog", "a photo of a car"]
)
# [{'score': 0.999, 'label': 'a photo of a cat'}, ...]
```

#### 5.2 Fine-Grained Control (Tipsv2Model)

```python
from transformers import AutoModel, AutoProcessor
from transformers.image_utils import load_image

model_id = "google/tipsv2-b14"
model = AutoModel.from_pretrained(model_id, device_map="auto")
processor = AutoProcessor.from_pretrained(model_id)

image = load_image(...)
inputs = processor(text=candidate_labels, images=image, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model(**inputs)

probs = outputs.logits_per_image.softmax(dim=1)
```

#### 5.3 Separate Image / Text Encoding (Retrieval)

```python
image_embeds = model.get_image_features(**image_inputs)
text_embeds = model.get_text_features(**text_inputs)
# Apply L2 normalization manually before computing similarity
```

**Important**: `get_image_features()` and `get_text_features()` return **unnormalized** embeddings. Apply `F.normalize(..., dim=-1)` before computing cosine similarity.

#### 5.4 Vision Backbone Only

```python
from transformers import AutoBackbone, AutoImageProcessor

backbone = AutoBackbone.from_pretrained("google/tipsv2-b14", device_map="auto")
image_processor = AutoImageProcessor.from_pretrained("google/tipsv2-b14")

outputs = backbone(**inputs)
patch_features = outputs.feature_maps[-1]  # (batch, hidden, height, width)
```

#### 5.5 Accessing Dual Class Tokens

```python
config = AutoConfig.from_pretrained(model_id)
model = AutoModel.from_pretrained(model_id, config=config.vision_config, device_map="auto")

sequence = outputs.last_hidden_state
cls_token_1 = sequence[:, 0]           # web alt-text supervised
cls_token_2 = sequence[:, 1]           # synthetic caption supervised
```

#### 5.6 DPT Dense Prediction (Depth + Normals + Segmentation)

```python
from transformers import Tipsv2DptForDensePrediction, AutoImageProcessor

model = Tipsv2DptForDensePrediction.from_pretrained("google/tipsv2-b14-dpt", device_map="auto")
image_processor = AutoImageProcessor.from_pretrained("google/tipsv2-b14-dpt")

with torch.no_grad():
    outputs = model(**inputs)

outputs.predicted_depth       # (batch, H, W) — depth in meters
outputs.normals               # (batch, 3, H, W) — XYZ normals
outputs.segmentation_logits   # (batch, num_labels, H, W)

# Post-processing
depth_results = image_processor.post_process_depth_estimation(outputs, target_sizes=...)
normal_results = image_processor.post_process_normal_estimation(outputs, target_sizes=...)
seg_results = image_processor.post_process_semantic_segmentation(outputs, target_sizes=...)
```

The pipeline also works directly:

```python
# Depth estimation
pipe = pipeline("depth-estimation", model="google/tipsv2-b14-dpt", device_map="auto")

# Image segmentation
pipe = pipeline("image-segmentation", model="google/tipsv2-b14-dpt", device_map="auto")
```

---

### 6. Key API Surface (Transformers)

| Class | Purpose |
|-------|---------|
| `Tipsv2Config` | Full model config (text_config + vision_config + temperature) |
| `Tipsv2TextConfig` | Text tower config |
| `Tipsv2VisionConfig` | Vision tower config |
| `Tipsv2Model` | Full dual-encoder model (contrastive) |
| `Tipsv2TextModel` | Text encoder only |
| `Tipsv2VisionModel` | Vision encoder only (exposes both class tokens) |
| `Tipsv2VisionBackbone` | Vision backbone for feature maps (DETR, MaskFormer compatible) |
| `Tipsv2DptForDensePrediction` | TIPSv2 + DPT head (depth, normals, segmentation) |
| `Tipsv2Processor` | Combined text + image processor |
| `Tipsv2ImageProcessor` | Image processor only |
| `Tipsv2Tokenizer` | BPE (SentencePiece) tokenizer |

---

### 7. Notes & Caveats

- **Normalization**: Tipsv2Model returns **normalized** `image_embeds` and `text_embeds` in its forward outputs. But `get_image_features()` / `get_text_features()` return **unnormalized** embeddings — you must normalize manually.
- **Temperature**: The learnable temperature's initial value (`0.005065968260169029`) is very specific to the model architecture — don't change it without retraining.
- **Max text length**: Text encoder supports only **64 tokens** (`max_position_embeddings=64`), making it unsuitable for long-text retrieval.
- **Register tokens**: While `num_register_tokens` defaults to 1, the config supports more for pretraining scenarios.
- **Patch size 14**: At 448×448 image size with 14×14 patches, this produces a 32×32 grid (1024 patches) — manageable for attention computation.
- **No SwiGLU**: The vision encoder uses standard MLP (`use_swiglu_ffn=False`) with GELU activation, unlike many modern LLMs.
- **Relu text encoder**: The text tower uses ReLU activation, which is atypical for modern transformers but keeps inference fast.

---

### 8. Comparison to Similar Models

| Aspect | CLIP | SigLIP | TIPSv2 |
|--------|------|--------|--------|
| Loss | Contrastive (softmax) | Sigmoid (pairwise) | Contrastive + iBOT++ |
| Vision backbone | ViT | ViT | ViT + register tokens |
| Class tokens | 1 | 1 | **2** (dual supervision) |
| Patch-text alignment | Weak | Moderate | **Strong** (iBOT++) |
| Dense prediction | No | No | **Yes** (via DPT head) |
| Text max length | 77 | 77 | 64 |
| Year | 2021 | 2024 | 2026 |

TIPSv2's strength is **patch-level alignment** — it understands not just what objects are in an image, but which patches correspond to which textual concepts. This makes it uniquely suited for dense prediction tasks.
