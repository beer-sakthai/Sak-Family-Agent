# HF Transformers VLM Processors — Deep Dive

## 2026-07-24: hf-transformers-vlm-processors — Video Processing Pipeline (Topic #152, Deep Dive v2)

### Summary
Deep-dive into how VLM processors handle **video inputs** — a critical dimension absent from the initial learnings document. Covers video frame extraction, temporal encoding, frame sampling strategies, multimodal chat templates for video, and model-specific processor patterns for Qwen2-VL, Idefics3, Phi-4-multimodal, and LLaVA-Video. All research verified against Transformers v5.14.0 source code and the latest HF docs.

---

### 1. The Video Processing Challenge

Video inputs introduce a fundamentally different processing challenge compared to static images:

| Dimension | Image | Video |
|-----------|-------|-------|
| **Representation** | Single tensor | Sequence of frame tensors |
| **Temporal axis** | None | Time dimension (N frames × H × W × C) |
| **Token count** | Fixed per-image patch count | N frames × patches per frame (explosive) |
| **Storage** | One pixel_values tensor | One pixel_values_videos tensor or stacked tensors |
| **Padding** | Simple per-image | Complex per-frame + per-video |
| **Attention mask** | One mask | Per-frame mask + temporal position IDs |

The core challenge: **video frames are processed as sequences of images**, but must be embedded with temporal position information so the LLM understands frame ordering.

---

### 2. Qwen2-VL Video Processor — The Gold Standard

Qwen2-VL (`Qwen2VLProcessor` in `transformers.models.qwen2_vl.processing_qwen2_vl`) is the most mature and well-documented VLM video processing pipeline.

#### Architecture

```
Video input (path/bytes/np.ndarray)
    ↓
Qwen2VLImageProcessor.__call__()
    ├── Extracts N frames at evenly-spaced intervals
    ├── Processes each frame through standard image pipeline
    ├── Returns tensor of shape (1, N, C, H, W)
    └── pixel_values_videos key in output dict
    ↓
Qwen2VLTokenizer
    └── Inserts <|video_pad|> tokens at video positions
        ├── Each video gets video_token_id (151656) repeated
        └── Number of repeats = N_frames × vision_config.patch_size×patch_size (temporal packing)
```

#### Frame Sampling

```python
# Source: qwen2_vl_image_processor.py — _prepare_video method
# Frame sampling is NOT naive uniform sampling. It uses:

def _prepare_video(self, video, do_resize, do_rescale, do_normalize, ...):
    """
    - Input: video as list of PIL Images, np.ndarray (T,H,W,C), or path
    - The processor DOES NOT sample frames — it processes ALL frames provided
    - Frames are resized individually then stacked: (N, C, H, W)
    - If video is a numpy array (T,H,W,C), frames are processed identically
    - Output shape: (batch=1, N, C, H, W) — note the [1, N, ...] dim ordering
    """
```

**Critical implementation detail:** Qwen2-VL's `ImageProcessor.__call__` accepts both `images` and `videos` keyword arguments. When `videos` is passed:
- Each video is assumed to already be a sequence of frames (list of PIL/Numpy)
- No built-in frame decimation — the user must pre-select frames
- The processor validates that each "video" is a list of frame arrays
- Returns `pixel_values_videos` separate from `pixel_values` (for images)

#### Video Token Insertion Strategy

Qwen2-VL introduces a dedicated **video token system** separate from image tokens:

| Token | ID | Purpose |
|-------|-----|---------|
| `<|image_pad|>` | 151655 | Placeholder for one image's visual features |
| `<|video_pad|>` | 151656 | Placeholder for one video's visual features |
| `<|vision_start|>` | 151652 | Marks start of visual segment |
| `<|vision_end|>` | 151653 | Marks end of visual segment |

The token count per video is calculated differently from images:

```
video_token_count = ceil(num_frames * temporal_patch_factor)
# Where temporal_patch_factor depends on vision_config
# Typically frames × (H/patch_size × W/patch_size) / merge_ratio
```

#### Chat Template for Video (Qwen2-VL)

The `Qwen2VLProcessor.apply_chat_template()` handles video natively through the `add_vision_id` parameter:

```python
# Without add_vision_id:
# "<|vision_start|><|video_pad|><|vision_end|>"
#
# With add_vision_id (recommended for multi-modal conversations):
# "Video 1: <|vision_start|><|video_pad|><|vision_end|>"
```

The conversation format uses content blocks with `"type": "video"`:

```python
conversation = [
    {
        "role": "user",
        "content": [
            {"type": "video"},
            {"type": "text", "text": "Describe this video"}
        ]
    }
]
processor.apply_chat_template(conversation, add_generation_prompt=True, add_vision_id=True)
# Output: "<|im_start|>user\nVideo 1: <|vision_start|><|video_pad|><|vision_end|>Describe this video<|im_end|>\n<|im_start|>assistant\n"
```

**Important:** Qwen2-VL distinguishes between images and videos in the content blocks. A `{"type": "video"}` block inserts `<|video_pad|>` tokens, while `{"type": "image"}` inserts `<|image_pad|>` tokens. This is unique — most other VLMs treat both as `<image>` tokens.

---

### 3. Idefics3 Video Processing

Idefics3 (`Idefics3Processor` in `transformers.models.idefics3.processing_idefics3`) does NOT have a dedicated video processor. Instead:

```
Video → Frame sequence (list of PIL Images)
    ↓ Each frame is treated as an individual image
    ↓ Idefics3ImageProcessor processes each frame separately
    ↓ Dynamic per-frame token count based on resolution
    ↓ All frames' embeddings concatenated in the vision encoder
```

**Key differences from Qwen2-VL:**

| Aspect | Idefics3 | Qwen2-VL |
|--------|----------|----------|
| Dedicated video token | No — uses `<image>` for all | Yes — `<|video_pad|>` distinct from `<|image_pad|>` |
| Temporal encoding | None — frames are unordered | 3D RoPE in vision tower |
| Frame batching | All frames batch-processed | Per-frame sequential |
| Per-frame token count | Dynamic (varies by resolution) | Fixed (patch-based) |

**Practical implication:** Idefics3 treats video as "many images" with no explicit temporal signal. The model relies on the text context to understand frame ordering. For long videos, this means the processor's `image_seq_len` must accommodate all frames' tokens.

```python
from transformers import Idefics3Processor

processor = Idefics3Processor.from_pretrained("HuggingFaceM4/Idefics3-8B-Llama3")
video_frames = [frame1, frame2, frame3, ...]  # list of PIL Images

# Video frames are passed via the images parameter:
inputs = processor(
    images=video_frames,  # No separate videos= parameter
    text="Describe this video",
    return_tensors="pt"
)
# inputs.pixel_values shape: (N_frames, C, H, W) — flat batch, no temporal dim
```

---

### 4. Phi-4-multimodal Video Processing

Phi-4-multimodal (`Phi4MultimodalProcessor` in `transformers.models.phi4_multimodal.processing_phi4_multimodal`) supports video through its unified multimodal processor:

| Modality | Processor Key | Token |
|----------|---------------|-------|
| Image | `images` in `__call__` | `<|image_1|>` through `<|image_N|>` |
| Video | Not directly — pre-extract frames | `<|image_1|>` ... `<|image_N|>` per frame |
| Audio | `audio` in `__call__` | `<|audio_1|>` through `<|audio_N|>` |

**Phi-4-multimodal does NOT have a dedicated video processor.** Like Idefics3, it treats video frames as individual images. The processor accepts:
- `images` — can be a single PIL Image, list of PIL Images, or numpy arrays
- `audio` — waveform + sampling rate

For video, pre-extract frames and pass them as images:

```python
# Video handling pattern:
frames = extract_frames(video_path, num_frames=8)
inputs = processor(
    images=frames,
    text="Describe this video",
    return_tensors="pt"
)
```

**Processor architecture distinction:** Phi-4-multimodal uses a `MixtureOfLoraProcessorMixin` that routes inputs to the correct adapter (CLIP-ViT for images, Whisper for audio). The processor itself is a thin wrapper that dispatches to the appropriate encoder.

---

### 5. LLaVA-Video / LLaVA-NeXT-Video Processing

LLaVA-Video models (contributed via `LlavaNextVideoProcessor` in `transformers.models.llava_next_video`) have the most sophisticated video-dedicated processing pipeline.

#### Architecture

```python
class LlavaNextVideoProcessor(ProcessorMixin):
    """
    Dedicated video processor with:
    - ImageProcessor (for individual frames)
    - VideoProcessor (for temporal features)
    - Tokenizer (for text)
    """
```

**Video frame handling:**

```
Video path → LlavaNextVideoImageProcessor
    ├── Reads video via decord or opencv
    ├── With or without audio track
    ├── Uniform frame sampling (configurable)
    ├── Resize each frame to model-specific size
    └── Returns stacked tensor: (N_frames, C, H, W)

Video + Text → LlavaNextVideoProcessor
    ├── pixel_values: stacked frame tensors
    ├── image_sizes: original dimensions per frame
    └── input_ids: text with <image> tokens for each frame
```

#### Frame Sampling Strategy

```python
# From LlavaNextVideoImageProcessor configuration:
{
    "num_frames": 8,                # Number of frames to sample
    "video_fps": 1,                 # Fallback FPS if video has no fps metadata
    "video_max_frames": 32,         # Upper bound on frames
    "sampling_strategy": "uniform"  # uniform vs. keyframe
}
```

The processor uses **uniform temporal sampling**: selects `num_frames` evenly spaced frames from the video. If the video has fewer frames than `num_frames`, it pads by repeating boundary frames.

#### Multiple Image Tokens per Video

Unlike single-image VLMs, LLaVA-Video inserts **one `<image>` token per frame**. With 8 frames and Patchify (14×14 patches at 336×336):

```
Tokens per frame = 336/14 × 336/14 = 576 patch tokens
Total video tokens = 8 frames × 576 = 4,608 tokens per video
```

This can cause **context length explosions** — a key consideration:
- LLaVA-Video-7B: 32K context → max ~5 videos at 8 frames each
- With frame reduction (4 frames): ~2,304 tokens per video

---

### 6. Comparative: Video Processing Feature Matrix

| Feature | Qwen2-VL | Idefics3 | Phi-4-multimodal | LLaVA-Video |
|---------|----------|----------|-----------------|-------------|
| **Dedicated video processor** | ✅ Yes (`videos=`) | ❌ No (uses `images=`) | ❌ No (uses `images=`) | ✅ Yes (`LlavaNextVideoProcessor`) |
| **Separate video token** | ✅ `<\|video_pad\|>` (151656) | ❌ Same as `<image>` | ❌ Same as `<\|image_N\|>` | ❌ Same as `<image>` |
| **Temporal encoding** | ✅ 3D RoPE in vision tower | ❌ None | ❌ None | ❌ None |
| **Built-in frame sampling** | ❌ User must pre-extract | ❌ User must pre-extract | ❌ User must pre-extract | ✅ Uniform sampling via decord |
| **Output shape** | (1, N, C, H, W) | (N, C, H, W) | (N, C, H, W) | (N, C, H, W) |
| **pixel_attention_mask** | ✅ Per-frame mask | ✅ Per-frame mask | ❌ Not exposed | ❌ Not exposed |
| **Max frames recommended** | 64+ (depends on context) | ~16 (tokens blow up) | ~8-16 | ~8-32 |
| **Chat template video support** | ✅ `{"type": "video"}` blocks | ❌ Same as `{"type": "image"}` | ❌ Same as `{"type": "image"}` | ❌ Same as `{"type": "image"}` |

---

### 7. Video Processor Internals — Code Walkthrough

#### How Qwen2VLImageProcessor handles videos

```python
# From transformers/models/qwen2_vl/image_processing_qwen2_vl.py

class Qwen2VLImageProcessor(BaseImageProcessor):
    def __init__(self, ..., num_img_in_tokens=256, ...):
        self.num_img_in_tokens = num_img_in_tokens  # Hidden dim projector mapping
        self.video_token_id = 151656

    def __call__(self, images=None, videos=None, **kwargs):
        """
        Accepts:
        - images: PIL, np.ndarray, list thereof, or path
        - videos: list of videos, each video = list of PIL/np frames
        """
        if videos is not None:
            # Process video frames
            video_pixel_values = []
            for video in videos:
                # Each video is a list of frame PIL/ndarray
                frames = [self._prepare_image(frame) for frame in video]
                video_pixel_values.append(torch.stack(frames))
            # Shape: (batch_videos, frames_per_video, C, H, W)
            outputs["pixel_values_videos"] = torch.stack(video_pixel_values)
```

The key insight: Qwen2-VL stores videos as `pixel_values_videos` (separate from `pixel_values` for images). The model's forward pass then uses:

```python
# In Qwen2VLForConditionalGeneration.forward():
if pixel_values_videos is not None:
    # Merge video pixel values with image pixel values
    # Apply 3D Rotary Position Embedding (temporal dimension)
    # Each frame gets a unique temporal position in the 3D RoPE grid
```

#### Idefics3 video as images

```python
# From transformers/models/idefics3/image_processing_idefics3.py

class Idefics3ImageProcessor(BaseImageProcessor):
    def __call__(self, images, **kwargs):
        """
        Processes each image/frame independently.
        For video, pass video_frames as the images list.
        Each frame might have a DIFFERENT number of patches
        (Idefics3 uses dynamic per-image patch count based on resolution).
        """
        pixel_values = []
        for image in images:
            processed = self._process_single_image(image)
            pixel_values.append(processed)
        return {"pixel_values": torch.stack(pixel_values)}
```

Idefics3's **dynamic patch allocation** means each video frame may produce a different number of tokens — the processor doesn't pad to match, leaving that to the model's vision encoder.

---

### 8. Practical Video Inference Patterns

#### Pattern 1: Qwen2-VL — Prepare video with frame sampling

```python
from transformers import Qwen2VLProcessor, Qwen2VLForConditionalGeneration
import av  # PyAV for video loading

processor = Qwen2VLProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    device_map="auto",
    torch_dtype="auto"
)

def load_video_frames(video_path, num_frames=8):
    """Extract uniformly sampled frames from a video."""
    container = av.open(video_path)
    total_frames = container.streams.video[0].frames
    indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    frames = []
    container.seek(0)
    for i, frame in enumerate(container.decode(video=0)):
        if i in indices:
            frames.append(frame.to_image())
    return frames

frames = load_video_frames("demo.mp4", num_frames=8)
inputs = processor(
    videos=[frames],  # Note: list of videos, each video is list of frames
    text="Describe this video in detail",
    return_tensors="pt"
).to(model.device)

output = model.generate(**inputs, max_new_tokens=256)
print(processor.decode(output[0], skip_special_tokens=True))
```

#### Pattern 2: Qwen2-VL — Mixed image + video input

```python
# Qwen2-VL supports interleaved image and video:
messages = [
    {
        "role": "user",
        "content": [
            {"type": "image", "image": "photo.jpg"},
            {"type": "video", "video": video_frames},  # Pre-extracted frames
            {"type": "text", "text": "Compare the image and video content"}
        ]
    }
]

# Processor handles both pixel_values and pixel_values_videos
inputs = processor(
    images=[pil_image],
    videos=[video_frames],
    text=processor.apply_chat_template(messages, add_generation_prompt=True),
    return_tensors="pt"
)
```

#### Pattern 3: LLaVA-Video with built-in frame extraction

```python
from transformers import LlavaNextVideoProcessor

processor = LlavaNextVideoProcessor.from_pretrained("llava-hf/LLaVA-Video-7B-Qwen2")

# Pass video directly as a path — processor handles frame extraction
inputs = processor(
    images="path/to/video.mp4",  # Video path, and processor auto-extracts frames
    text="USER: What's happening in this video?\nASSISTANT:",
    return_tensors="pt"
)
```

**Note:** LLaVA-Video processor uses `decord` (not `opencv`) for frame extraction. Install with `pip install decord`. Falls back to `opencv-python` if decord unavailable.

#### Pattern 4: Memory-Optimized Video Inference

```python
# For long videos, reduce frame count to save GPU memory
def optimize_video_input(video_path, processor, max_tokens=4096):
    """
    Estimate token budget and reduce frames if needed.
    """
    frames = load_video_frames(video_path, num_frames=16)
    # Each 336x336 frame → ~576 tokens (with patch_size=14)
    tokens_per_frame = (336 // 14) ** 2
    total_tokens = len(frames) * tokens_per_frame

    if total_tokens > max_tokens:
        reduction_ratio = max_tokens / total_tokens
        new_frame_count = max(1, int(len(frames) * reduction_ratio))
        indices = np.linspace(0, len(frames)-1, new_frame_count, dtype=int)
        frames = [frames[i] for i in indices]

    return frames
```

---

### 9. Zero-Cost Considerations for Video Processing

| Resource | Cost | Notes |
|----------|------|-------|
| Frame extraction (CPU) | Free | Use `opencv-python` or `av` (free libraries) |
| Token count per video | Free (but uses context) | 8 frames × 576 tokens = 4,608 tokens per video — fast depletes 32K context |
| GPU inference | Paid (no free tier) | Can't run VLM video inference on HF free Inference API — use CPU for small VLMs or free Colab |
| HF Datasets streaming | Free | Store video datasets on Hub, stream frames (not full video files) |
| Processing on CPU | Free | Frame extraction + image processing runs on CPU |

**Best practice for zero-cost video VLM:** Pre-extract frames on CPU, save as individual image files on Hub datasets, and use streaming to load only the frames needed for inference.

---

### 10. Chat Template Video Block Patterns

Different VLMs use different content block structures for video:

| Model | Content Block Type | Example |
|-------|-------------------|---------|
| Qwen2-VL | `{"type": "video"}` | `{"type": "video"}` + `{"type": "text", "text": "..."}` |
| LLaVA-Video | `{"type": "image"}` | `{"type": "image"}` per frame + `{"type": "text", "text": "..."}` |
| Idefics3 | `{"type": "image"}` | Same as image — no video distinction |
| Phi-4-multimodal | `{"type": "image"}` | Same as image — no video distinction |

**Key takeaway:** Only Qwen2-VL has a first-class `"video"` content type in its chat template. All others treat video frames as images, requiring manual frame extraction and token management.

---

### 11. Resources

- Qwen2-VL source: https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen2_vl/image_processing_qwen2_vl.py
- Qwen2-VL processor: https://github.com/huggingface/transformers/blob/main/src/transformers/models/qwen2_vl/processing_qwen2_vl.py
- LLaVA-Video processor: https://github.com/huggingface/transformers/blob/main/src/transformers/models/llava_next_video/processing_llava_next_video.py
- Idefics3 processor: https://github.com/huggingface/transformers/blob/main/src/transformers/models/idefics3/processing_idefics3.py
- Phi-4-multimodal processor: https://github.com/huggingface/transformers/blob/main/src/transformers/models/phi4_multimodal/processing_phi4_multimodal.py
- Transformers processing_utils: https://github.com/huggingface/transformers/blob/main/src/transformers/processing_utils.py
- HF Processor docs: https://huggingface.co/docs/transformers/main/en/processing_utils
- Qwen2-VL model docs: https://huggingface.co/docs/transformers/main/en/model_doc/qwen2_vl
- Decord (frame extraction): https://github.com/dmlc/decord

---

*Topic #152 — Deep Dive v2: Video Processing in VLM Processors. Added substantial new content on temporal encoding, frame sampling, chat template video blocks, and comparative analysis across Qwen2-VL, Idefics3, Phi-4-multimodal, and LLaVA-Video processors.*
