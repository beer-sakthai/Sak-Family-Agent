# HF Transformers VLM Processors — Deep Dive

## 2026-07-24: hf-transformers-vlm-processors

### Summary
Researched how Transformers handles Vision-Language Model (VLM) processing through the processor abstraction layer. Processors combine an image processor (or video processor) with a tokenizer, handling the bridging of visual features with text tokenization for multimodal models like LLaVA, Idefics3, Florence-2, Qwen2-VL, and Phi-4-multimodal.

### Key Concepts

**Processor Architecture:**
1. **`ProcessorMixin` base class** (in `transformers.processing_utils`) — provides the `__call__` interface accepting `images`, `text`, `videos`, `audio` as optional inputs
2. **`ImageProcessingMixin`** — standard image preprocessing (resize, crop, rescale, normalize, pad) with model-specific defaults
3. **`TokenizersBackend`** — wraps any HF tokenizer with unified encode/decode interface
4. **Processor classes merge both** — each VLM has its own processor (e.g., `LlavaProcessor`, `Idefics3Processor`, `Florence2Processor`)

**Common Preprocessing Pipeline:**
1. Image → resize to model-specific size (e.g., 336×336 for LLaVA, 384×384 for Idefics3, 1024×1024 for Florence-2)
2. Convert to tensor, rescale to [0,1], normalize with model-specific mean/std
3. Text → apply chat template (if messages format) → tokenize
4. Insert image tokens (`<image>`, `<|image|>`, `<img>`) into text at correct positions
5. Return `BatchFeature` dict with `pixel_values`, `input_ids`, `attention_mask`

**Image Token Strategies:**
- **LLaVA-style:** Single `<image>` token replaced by vision encoder's patch embeddings. `vision_feature_select_strategy="default"` keeps all patches; `"full"` includes CLS token.
- **Idefics3-style:** Multiple `<image>` tokens per image, dynamically computed based on image resolution (per-image token counts vary)
- **Florence-2-style:** Fixed task prompt tokens + image embedding via DaViT encoder (no `<image>` token insertion — image is processed separately)
- **Qwen2-VL-style:** Uses `|<image_pad|*N|>` pattern where N is the number of image patches

**Key Processor Parameters:**
- `image_processor` — the image preprocessing instance
- `tokenizer` — the text tokenizer instance
- `patch_size` — vision encoder patch size (used to calculate how many tokens an image produces)
- `vision_feature_select_strategy` — "default" (no CLS) vs "full" (with CLS) vs "cls_patch"
- `chat_template` — Jinja template for converting conversation messages to tokenizable strings
- `image_token` — the special token used to mark image location in text (varies by model)
- `num_additional_image_tokens` — extra tokens appended to image embeddings (e.g., CLS = +1)

**Multimodal Processor `__call__` Signature (unified in v5):**
```
processor(images=None, text=None, videos=None, audio=None, **kwargs) → BatchFeature
```
Accepts PIL images, numpy arrays, torch tensors, or lists thereof. Returns unified dict with model-specific keys.

**Handling Multiple Images:**
- Processor handles image lists by inserting multiple `<image>` tokens
- Some VLMs (Idefics3, Qwen2-VL) natively support interleaved image-text sequences
- `padding=True` required for batched multi-image inputs to pad to consistent dimensions

**VLM-Specific Processor Details:**

| Model | Image Processor Base | Tokenizer | Image Token | Special Handling |
|---|---|---|---|---|
| LLaVA 1.5/1.6 | LlavaImageProcessor | LlamaTokenizer | `<image>` | Vision tower patch embedding + projection layer |
| LLaVA-NeXT | LlavaNextImageProcessor | LlamaTokenizer | `<image>` | Supports dynamic high-res grid |
| Idefics3 | Idefics3ImageProcessor | GemmaTokenizer | `<image>` | Per-res flexible image splitting |
| Florence-2 | CLIPImageProcessor | BERTTokenizer | (none) | Task prompts as text; encoder-decoder architecture |
| Qwen2-VL | Qwen2VLImageProcessor | Qwen2Tokenizer | `|<image_pad|*N|>` | 3D rotary embedding in vision tower |
| Phi-4-multimodal | CLIPImageProcessor | Phi3Tokenizer | `<|image_1|>` | Wraps CLIP vision + whisper audio |

### Memory Optimization Tips
- Use `do_rescale=False` if passing already-scaled [0,1] tensors
- Reduce `image_size` in processor config if model supports it (not all do)
- Process images individually and avoid batching for very high-res VLMs
- Precompute `pixel_values` and cache them for repeated inference
- For Idefics3, `image_seq_len` is dynamically computed — lower resolution = fewer tokens

### Resources
- https://huggingface.co/docs/transformers/main/en/processing_utils — Processor base class
- https://huggingface.co/docs/transformers/main/en/model_doc/llava — LLaVA model docs
- https://huggingface.co/docs/transformers/main/en/model_doc/idefics3 — Idefics3 model docs
- https://huggingface.co/docs/transformers/main/en/model_doc/florence2 — Florence-2 model docs
- https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_vl — Qwen2-VL model docs
- https://github.com/huggingface/transformers/blob/main/src/transformers/models/llava/processing_llava.py — LLaVA processor source

---
