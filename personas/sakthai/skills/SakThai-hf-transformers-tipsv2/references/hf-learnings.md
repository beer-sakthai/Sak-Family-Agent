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

---

## 2026-07-25: TIPSv2 Source Code Deep-Dive (Topic #316 — Deepening)

### Summary
Deep-dive into the actual Transformers v5.14.1 source code for TIPSv2. Covers the architectural lineage (modular inheritance from DINOv2 + CLIP), implementation details of every module, weight initialization strategies, the DPT dense prediction head pipeline, and critical nuances found only in the code.

### Sources
- Source: `transformers/models/tipsv2/modeling_tipsv2.py` (1198 lines)
- Source: `transformers/models/tipsv2/modular_tipsv2.py` (878 lines)
- Source: `transformers/models/tipsv2/configuration_tipsv2.py` (201 lines)
- Source: `transformers/models/tipsv2/image_processing_tipsv2.py` (36 lines)
- Source: `transformers/models/tipsv2/tokenization_tipsv2.py` (line 61+)
- Source: `transformers/models/tipsv2_dpt/modeling_tipsv2_dpt.py` (714 lines)
- Source: `transformers/models/tipsv2_dpt/configuration_tipsv2_dpt.py` (96 lines)

---

### 1. Modular Architecture (Inheritance Chain)

TIPSv2 in Transformers is built using the **modular system** — `modeling_tipsv2.py` is auto-generated from `modular_tipsv2.py`. This enables code reuse from established architectures:

| Module | Inherits From | Source |
|--------|--------------|--------|
| `Tipsv2VisionConfig` | `Dinov2WithRegistersConfig` | DINOv2 with registers |
| `Tipsv2TextConfig` | `Siglip2TextConfig` | SigLIP-2 |
| `Tipsv2VisionEmbeddings` | Custom (DINOv2-style) | handles CLS + mask + register tokens |
| `Tipsv2VisionEncoder` | Standalone (DINOv2-style) | repeated `Tipsv2VisionLayer` |
| `Tipsv2TextModel` | Custom (CLIP-style) | uses `CLIPAttention`, `CLIPEncoderLayer` patterns |
| `Tipsv2TextEmbeddings` | Custom | uses `Speech2TextSinusoidalPositionalEmbedding` |
| `Tipsv2VisionBackbone` | `BackboneMixin` + `Tipsv2VisionPreTrainedModel` | DPT / DETR compatible |
| `Tipsv2DptConfig` | Standalone | `backbone_config` default = `tipsv2_vision_model` |
| Contrastive loss | Adapted from CLIP | `image_text_contrastive_loss` copied locally |

```python
# From modular_tipsv2.py — imports prove the lineage:
from ..dinov2_with_registers.configuration_dinov2_with_registers import Dinov2WithRegistersConfig
from ..dinov2_with_registers.modeling_dinov2_with_registers import (
    Dinov2WithRegistersBackbone, Dinov2WithRegistersEmbeddings,
    Dinov2WithRegistersEncoder, Dinov2WithRegistersModel,
)
from ..clip.modeling_clip import (
    CLIPAttention, CLIPEncoder, CLIPEncoderLayer, CLIPOutput,
    CLIPTextEmbeddings, _get_vector_norm, image_text_contrastive_loss,
)
from ..siglip2.configuration_siglip2 import Siglip2TextConfig
from ..speech_to_text.modeling_speech_to_text import Speech2TextSinusoidalPositionalEmbedding
```

### 2. Vision Encoder — Source-Level Details

#### 2.1 Embeddings (`Tipsv2VisionEmbeddings`)

```python
# Initialization
self.cls_token = nn.Parameter(torch.randn(1, 1, config.hidden_size))
self.mask_token = nn.Parameter(torch.zeros(1, config.hidden_size))  # iBOT pre-training
self.register_tokens = nn.Parameter(torch.zeros(1, config.num_register_tokens, config.hidden_size))
self.position_embeddings = nn.Parameter(torch.randn(1, num_patches + 1, config.hidden_size))
```

**Forward pass (exact order)**:
1. Conv2D projection → flatten → transpose (ViT standard)
2. Apply `mask_token` at bool_masked_pos (for iBOT pre-training only)
3. Prepend CLS token (`embeddings[:, :1]`)
4. Add position embeddings (bilinear interpolated if resolution differs)
5. **Insert register tokens after CLS** (`embeddings[:, :1] + register_tokens + embeddings[:, 1:]`)
6. Apply dropout

**Position interpolation uses bilinear** (not bicubic like DINOv2). Comparison:
- DINOv2: `mode="bicubic", antialias=True`
- TIPSv2: `mode="bilinear", antialias=True` — intentional design choice

```python
patch_pos_embed = nn.functional.interpolate(
    patch_pos_embed.to(dtype=torch.float32),  # cast to fp32 for precision
    size=(torch_int(height), torch_int(width)),
    mode="bilinear",  # different from Dinov2
    align_corners=False,
    antialias=True,
).to(dtype=target_dtype)
```

**Register tokens are positioned between CLS and patch tokens in the sequence**:
```
Sequence: [CLS] → [register_tokens] → [patch_0, patch_1, ..., patch_N]
               ^--- token 0        ^--- tokens 1 to 1+num_register     ^--- rest
```

#### 2.2 Vision Layer (`Tipsv2VisionLayer`) — Block Structure

Pre-LN design with LayerScale and optional DropPath:

```python
def forward(self, hidden_states):
    # Block 1: Attention
    hidden_states_norm = self.norm1(hidden_states)
    self_attention_output = self.attention(hidden_states_norm)
    self_attention_output = self.layer_scale1(self_attention_output)
    hidden_states = self.drop_path(self_attention_output) + hidden_states  # residual 1
    
    # Block 2: MLP
    layer_output = self.norm2(hidden_states)
    layer_output = self.mlp(layer_output)
    layer_output = self.layer_scale2(layer_output)
    layer_output = self.drop_path(layer_output) + hidden_states  # residual 2
    return layer_output
```

**Key**: LayerScale is applied **after** attention/MLP but **before** residual add. This is the standard DINOv2 pattern.

#### 2.3 MLP Options

Two FFN variants:

| Variant | Class | When Used | Implementation |
|---------|-------|-----------|----------------|
| Standard MLP | `Tipsv2VisionMLP` | `use_swiglu_ffn=False` (default) | GELU, `hidden_size * mlp_ratio` |
| SwiGLU | `Tipsv2VisionSwiGLUFFN` | `use_swiglu_ffn=True` | SiLU(x1) * x2, hidden dim = nearest_multiple_of_8(hidden * 2/3) |

SwiGLU uses the **hidden-nearest-multiple-of-8** pattern for hardware efficiency:
```python
hidden_features = (int(hidden_features * 2 / 3) + 7) // 8 * 8
```

#### 2.4 Attention Backend Architecture

Uses the ALL_ATTENTION_FUNCTIONS interface for backend-agnostic attention:

```python
attention_interface: Callable = ALL_ATTENTION_FUNCTIONS.get_interface(
    self.config._attn_implementation, eager_attention_forward
)
```

Supported backends (from `_supports_*` flags):
- SDPA (`_supports_sdpa = True`)
- Flash Attention (`_supports_flash_attn = True`)
- Flex Attention (`_supports_flex_attn = True`)
- Eager (fallback: `eager_attention_forward`)

The vision `eager_attention_forward` computes attention as:
```python
attn_weights = torch.matmul(query, key.transpose(2, 3)) * scaling
if attention_mask is not None:
    attn_weights = attn_weights + attention_mask
attn_weights = nn.functional.softmax(attn_weights, dim=-1)  # in query dtype
```

The text `text_eager_attention_forward` casts softmax to **float32** for numerical stability:
```python
attn_weights = nn.functional.softmax(attn_weights, dim=-1, dtype=torch.float32).to(query.dtype)
```

#### 2.5 Weight Initialization

```python
def _init_weights(self, module):
    if isinstance(module, (nn.Linear, nn.Conv2d)):
        init.trunc_normal_(module.weight, mean=0.0, std=self.config.initializer_range)  # std=0.02
        zeros_(module.bias)
    elif isinstance(module, Tipsv2VisionEmbeddings):
        trunc_normal_(module.position_embeddings, std=0.02)
        trunc_normal_(module.cls_token, std=0.02)
        zeros_(module.mask_token)      # mask token starts as zero
        zeros_(module.register_tokens) # register tokens start as zero
    elif isinstance(module, Tipsv2VisionLayerScale):
        constant_(module.lambda1, self.config.layerscale_value)  # default 1.0
```

Contrast with DPT initialization (kaiming_normal):
```python
# In Tipsv2DptPreTrainedModel:
if isinstance(module, (nn.Linear, nn.Conv2d, nn.ConvTranspose2d)):
    init.kaiming_normal_(module.weight, mode="fan_out", nonlinearity="relu")
```

---

### 3. Text Encoder — Source-Level Details

#### 3.1 Embeddings (`Tipsv2TextEmbeddings`)

- Token embeddings: `nn.Embedding(vocab_size=32000, embed_dim=768)` — standard
- Position embeddings: `Tipsv2SinusoidalPositionalEmbedding` — sinusoidal (not learned)
- Embedding scale: `inputs_embeds * self.embed_scale` where `embed_scale = sqrt(hidden_size)` (when `scale_sqrt_depth=True`)
- Max sequence length: **64 tokens** — enforced at forward time:
  ```python
  if seq_length > max_position_embedding:
      raise ValueError(...)
  ```

#### 3.2 Text Encoder Layer (`Tipsv2TextEncoderLayer`)

Post-LN design (layernorm **before** sublayers):
```python
def forward(self, hidden_states, attention_mask):
    residual = hidden_states
    hidden_states = self.layer_norm1(hidden_states)
    hidden_states, _ = self.self_attn(hidden_states, attention_mask)
    hidden_states = residual + hidden_states
    
    residual = hidden_states
    hidden_states = self.layer_norm2(hidden_states)
    hidden_states = self.mlp(hidden_states)  # ReLU activation
    hidden_states = residual + hidden_states
    return hidden_states
```

**No LayerScale, no DropPath** — simpler than the vision encoder.

#### 3.3 Masked Mean Pooling

The text model uses **masked mean pooling** (not CLS token pooling like CLIP):

```python
if pooling_mask is not None:
    masked_hidden_state = last_hidden_state * pooling_mask[..., None]
    pooled_output = masked_hidden_state.sum(dim=1) / (
        pooling_mask.sum(dim=1, keepdim=True) + self.config.pooling_epsilon  # 1e-8
    )
else:
    pooled_output = last_hidden_state.mean(dim=1)
```

The attention mask is bidirectional (not causal), created via `create_bidirectional_mask`.

#### 3.4 Sinusoidal Positional Embedding

Copied from Speech2Text. Uses the standard sinusoidal formula:
```python
half_dim = embedding_dim // 2
emb = math.log(10000) / (half_dim - 1)
emb = torch.exp(torch.arange(half_dim) * -emb)
emb = torch.arange(num_embeddings).unsqueeze(1) * emb.unsqueeze(0)
emb = torch.cat([torch.sin(emb), torch.cos(emb)], dim=1)
```
If `embedding_dim` is odd, pads with zeros. Registered as a persistent buffer.

---

### 4. Contrastive Model (`Tipsv2Model`) — Core Forward Pass

```python
class Tipsv2Model(Tipsv2PreTrainedModel):
    _keys_to_ignore_on_load_missing = ["temperature"]  # learnable but not in published checkpoints

    def __init__(self, config):
        self.text_model = Tipsv2TextModel._from_config(config.text_config)
        self.vision_model = Tipsv2VisionModel._from_config(config.vision_config)
        self.temperature = nn.Parameter(torch.tensor(config.temperature_init_value))  # ~0.00507
```

**Key implementation details**:

1. **Normalization behaviour**:
   - `get_text_features()` and `get_image_features()` return **raw encoder outputs** (unnormalized)
   - `forward()` **automatically L2-normalizes** both embeddings before computing logits
   - This is why the docs say `get_image_features()` returns unnormalized — check source lines 1153, 1167:
     ```python
     image_embeds = image_embeds / _get_vector_norm(image_embeds)
     text_embeds = text_embeds / _get_vector_norm(text_embeds)
     ```

2. **`_get_vector_norm` uses executorch-compatible pattern**:
   ```python
   def _get_vector_norm(tensor):
       square_tensor = torch.pow(tensor, 2)
       sum_tensor = torch.sum(square_tensor, dim=-1, keepdim=True)
       normed_tensor = torch.pow(sum_tensor, 0.5)
       return normed_tensor
   ```
   Instead of `tensor.norm(p=2, dim=-1, keepdim=True)` — this is for `executorch` exportability (see GitHub issue #3566).

3. **Temperature** is a learnable parameter but `_keys_to_ignore_on_load_missing` — existing published checkpoints may not include it, so it takes the init value from config on first load.

4. **Contrastive Loss** — symmetric formulation:
   ```python
   def contrastive_loss(logits):
       return nn.functional.cross_entropy(logits, torch.arange(len(logits), device=logits.device))
   
   def image_text_contrastive_loss(similarity):
       caption_loss = contrastive_loss(similarity)      # image→text direction
       image_loss = contrastive_loss(similarity.T)       # text→image direction
       return (caption_loss + image_loss) / 2.0
   ```

5. **Optional return_loss** flag — when not set, no loss is computed (inference-mode efficient).

---

### 5. DPT Dense Prediction Head — Full Pipeline

#### 5.1 Architecture Overview

```
Input → TIPSv2 Vision Backbone → feature_maps[3, 6, 9, 12]
                                           ↓
                                   [Reassemble Stage]
                                   (readout + reshape + upsample)
                                           ↓
                                   [Conv 1×1 projection]
                                           ↓
                                   [Feature Fusion Stage]
                                   (top-down with ResConv)
                                           ↓
                            ┌──────────────┼──────────────┐
                            ↓              ↓              ↓
                     Depth Decoder   Normals Decoder  Seg Decoder
                            ↓              ↓              ↓
                    Depth Bins (256)  3-channel XYZ   num_labels
```

#### 5.2 Reassemble Stage (`Tipsv2DptReassembleStage`)

The critical transformation from transformer sequence back to spatial feature maps:

```python
for stage_idx, hidden_state in enumerate(hidden_states):
    cls_token = hidden_state[:, 0]
    patch_tokens = hidden_state[:, 1 + self.num_register_tokens :]  # strip CLS + registers
    
    # Readout: concatenate CLS token to every patch (DPT innovation)
    readout = cls_token.unsqueeze(1).expand(-1, num_patches, -1)
    patch_tokens = self.readout_projects[stage_idx](torch.cat([patch_tokens, readout], dim=-1))
    
    # Reshape to 2D spatial: (B, H*W, C) → (B, C, H, W)
    patch_tokens = patch_tokens.reshape(batch_size, patch_height, patch_width, hidden_size)
    patch_tokens = patch_tokens.permute(0, 3, 1, 2).contiguous()
    
    # Resize via ConvTranspose2D (factor > 1), Identity (factor = 1), or Conv2D (factor < 1)
    patch_tokens = self.layers[stage_idx](patch_tokens)
```

**Readout projection** doubles the input dimension (patch token + CLS → projection):
```python
class Tipsv2DptReadoutProjectLayer(nn.Module):
    def __init__(self, in_dim, out_dim, activation):
        self.layers = nn.ModuleList([nn.Linear(in_dim, out_dim), activation])
```
Uses `"gelu_pytorch_tanh"` activation by default.

**Reassemble factors**: `[4, 2, 1, 0.5]` — stages 3 (early) get upsampled 4×, while stage 12 (deepest) gets downsampled 2×.

#### 5.3 Feature Fusion Stage (`Tipsv2DptFeatureFusionStage`)

Top-down refinement: starts from the deepest (last) feature map and progressively fuses with shallower ones.

```python
hidden_states = hidden_states[::-1]  # reverse: deepest first
for hidden_state, layer in zip(hidden_states, self.layers):
    if fused_hidden_state is None:
        fused_hidden_state = layer(hidden_state)  # no residual for first
    else:
        fused_hidden_state = layer(fused_hidden_state, hidden_state)  # with residual
```

Each fusion layer (`Tipsv2DptFeatureFusionLayer`):
1. Optionally adds residual from previous stage (bilinear interpolated if shape mismatch)
2. Two **pre-activation residual units** (ReLU → Conv3×3 → ReLU → Conv3×3 + residual)
3. Bilinear upsample ×2
4. 1×1 Conv projection

#### 5.4 Depth Estimation Head

Uses **depth bins** — discretizes continuous depth into 256 bins:

```python
class Tipsv2DptFeaturesToDepth(nn.Module):
    def __init__(self, config):
        self.min_depth = 0.001
        self.max_depth = 10.0
        bin_centers = torch.linspace(0.001, 10.0, 256)  # equally spaced in meters
        self.register_buffer("bin_centers", bin_centers, persistent=False)
    
    def forward(self, depth_logits):
        probs = self.activation(depth_logits) + self.min_depth  # ReLU + offset
        probs = probs / probs.sum(dim=1, keepdim=True)           # normalize to distribution
        bin_centers = self.bin_centers.to(dtype=depth_logits.dtype)
        return probs.permute(0, 2, 3, 1) @ bin_centers           # weighted sum
```

This produces a continuous depth map in meters.

#### 5.5 Three Independent Heads (DensePrediction)

`Tipsv2DptForDensePrediction` has **three separate neck + decoder sets** (not shared):

```python
def __init__(self, config):
    self.backbone = load_backbone(config)           # shared
    self.depth_neck = Tipsv2DptNeck(config)          # independent
    self.depth_decoder = Tipsv2DptDecoder(config, out_channels=256, activation="relu")
    self.depth_bin_regressor = Tipsv2DptFeaturesToDepth(config)
    self.normals_neck = Tipsv2DptNeck(config)        # independent
    self.normals_decoder = Tipsv2DptDecoder(config, out_channels=3)
    self.segmentation_neck = Tipsv2DptNeck(config)   # independent
    self.segmentation_decoder = Tipsv2DptDecoder(config, out_channels=num_labels)
```

All three run in parallel on the same backbone feature maps, so forward pass cost is backbone + 3 necks + 3 decoders.

#### 5.6 Specialized Variants (Single Head)

| Class | Heads | Weight Loading |
|-------|-------|----------------|
| `Tipsv2DptForDensePrediction` | Depth + Normals + Seg (all) | Full model |
| `Tipsv2DptForDepthEstimation` | Depth only | Ignores `normals_head`, `segmentation_head` |
| `Tipsv2DptForNormalEstimation` | Normals only | Ignores `depth_head`, `segmentation_head` |
| `Tipsv2DptForSemanticSegmentation` | Seg only | Ignores `depth_head`, `normals_head` |

The `_keys_to_ignore_on_load_unexpected` ensures single-head checkpoints load cleanly from the full model.

---

### 6. Tokenizer & Processor Details

#### 6.1 Tokenizer (BPE with SentencePiece-style)

| Property | Value |
|----------|-------|
| Model | BPE with `fuse_unk=True, byte_fallback=True` |
| Normalizer | Lowercase (+ optional `_spm_precompiled_charsmap`) |
| Pre-tokenizer | `WhitespaceSplit` → `Metaspace(replacement="▁", prepend_scheme="always")` |
| Decoder | Metaspace → ByteFallback → Fuse |
| Unk token | `<unk>` (id=1) |
| Pad token | `<pad>` (id=0) |
| Max length | 64 tokens |
| Padding | Right side |
| Lowercase | True (default) |

#### 6.2 Image Processor

```python
class Tipsv2ImageProcessor(TorchvisionBackend):
    resample = PILImageResampling.BILINEAR
    size = {"height": 448, "width": 448}
    do_resize = True
    do_rescale = True
    do_normalize = False     # No normalization! Unusual for vision models.
    do_convert_rgb = True
```

**Critical**: `do_normalize = False` — TIPSv2 does NOT normalize pixel values. This is unusual and aligns with the iBOT++ pre-training objective expecting raw [0, 1] pixel values.

#### 6.3 Processor Default Kwargs

```python
Tipsv2ProcessorKwargs._defaults = {
    "text_kwargs": {
        "padding": "max_length",  # pads to 64 tokens
        "truncation": True,
        "max_length": 64,
    },
}
```

---

### 7. Implementation Quirks & Lessons

1. **executorch compatibility**: The `_get_vector_norm` function uses `torch.pow` + `torch.sum` instead of `tensor.norm()` for export compatibility. Pattern found in CLIP source.

2. **Temperature checkpoint issue**: `temperature` is in `_keys_to_ignore_on_load_missing` — meaning published checkpoints from Google may not include it. The model falls back to the config's `temperature_init_value`.

3. **Stage name convention vs actual layers**: `stage_names = ["stem"] + [f"stage{idx}" for idx in range(1, 13)]` — the "stem" corresponds to the embedding layer, not a transformer block.

4. **Backbone reshape bug acknowledged**: In `Tipsv2VisionBackbone`, the comment says "this was actually a bug in the original implementation that we copied here, cause normally the order is height, width" — the reshape uses `height // patch_size` then `width // patch_size` but notes this is the wrong order. Kept for compatibility.

5. **Config strict validation**: Both `Tipsv2TextConfig` and `Tipsv2Config` use `@strict` decorator with `validate_architecture()` methods that enforce:
   - `hidden_size % num_attention_heads == 0` (text config)
   - `text_config.hidden_size == vision_config.hidden_size` (both must match)
   - `temperature_init_value > 0`

6. **Cross-profile weight loading**: Vision model ignores `text_encoder` keys; text model ignores `vision_encoder` keys. This allows loading the full `Tipsv2Model` checkpoint into sub-models.

7. **SwiGLU hidden dim alignment**: The SwiGLU variant explicitly aligns intermediate dim to multiples of 8: `(int(hidden_features * 2 / 3) + 7) // 8 * 8` — same pattern used in Llama, Mistral.

8. **Text attention does fp32 softmax**: Unlike vision attention (which uses the query dtype), text attention casts `softmax` to float32 then casts back — critical for precision with ReLU activations.

9. **No gradient checkpointing in text encoder**: While `Tipsv2TextPreTrainedModel` has `supports_gradient_checkpointing = True`, the text encoder's `gradient_checkpointing` attribute is set separately and not automatically inherited.

10. **DPT training not implemented**: The `raise NotImplementedError("Training is not yet supported")` in depth/normal heads indicates that TIPSv2-DPT is currently inference-only in Transformers. Training support may come in a future release.
