# HF Learnings: Datasets Video Processing

## 2026-07-24: hf-datasets-video-processing — Deep Dive (Topic #115)

### Summary
Comprehensive deep-dive into Hugging Face `datasets` library's video support — the `Video` feature class, its `torchcodec` backend (FFmpeg-based), the `VideoFolder` dataset builder for zero-code video dataset creation, WebDataset TAR shards for scaling to millions of videos, and Lance native blob storage. Covers the full data flow: encoding, Arrow storage, decoding, streaming, metadata integration, and memory management. All patterns verified against the v5.0.0+ datasets source.

### Core Architecture — The Video Feature

The `Video` feature class (`datasets.features.Video`) follows the same architectural pattern as `Image` and `Audio`:

```
Input Types → encode_example() → Arrow struct<bytes: binary, path: string> → decode_example() → torchcodec.VideoDecoder
```

**Arrow storage type:** `pa.struct({"bytes": pa.binary(), "path": pa.string()})` — identical to Image/Audio storage, enabling seamless interop with Parquet and streaming.

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `decode` | bool | `True` | Whether to decode into VideoDecoder objects. `False` yields raw dicts |
| `stream_index` | int \| None | `None` | Which stream from the video container (default: "best") |
| `dimension_order` | Literal["NCHW", "NHWC"] | `"NCHW"` | Frame tensor dimension order |
| `num_ffmpeg_threads` | int | `1` | FFmpeg decode threads (recommended: keep at 1) |
| `device` | str \| torch.device | `"cpu"` | Decode device (CPU or CUDA) |
| `seek_mode` | Literal["exact", "approximate"] | `"exact"` | Frame seek accuracy vs. speed tradeoff |
| `id` | str \| None | `None` | Feature identifier |

### Input Types — encode_example()

The `encode_example()` method normalizes all input formats into the canonical `{"path": ..., "bytes": ...}` dict:

| Input Type | Behaviour |
|------------|-----------|
| `str` | Treated as absolute/relative file path → `{"path": str, "bytes": None}` |
| `pathlib.Path` | Converted to absolute string via `str(value.absolute())` |
| `bytes` / `bytearray` | In-memory video bytes → `{"path": None, "bytes": bytes}` |
| `np.ndarray` | Calls `encode_np_array()` — **raises NotImplementedError** currently |
| `torchcodec.decoders.VideoDecoder` | If the decoder has `_hf_encoded` (was decoded from a datasets Video feature), returns stored dict; otherwise **raises NotImplementedError** |
| `dict` with `"path"` and/or `"bytes"` | Validated and passed through as-is |

**Critical constraint:** `encode_np_array()` and `encode_torchcodec_video()` for freshly-created VideoDecoders are **not implemented** — you cannot round-trip a numpy array or externally-constructed VideoDecoder back through the feature. The only supported round-trip is: decode from datasets → encode back.

### Decoding — decode_example()

Decoding converts the stored Arrow struct into a `torchcodec.decoders.VideoDecoder` object:

```python
def decode_example(self, value, token_per_repo_id=None) -> VideoDecoder:
```

**Flow:**
1. If `value` is a string, treat as path; otherwise extract `path` and `bytes` from dict
2. If `bytes` is not None → `VideoDecoder(bytes_, ...)` (in-memory decode)
3. If `bytes` is None and path is local → `VideoDecoder(path, ...)`
4. If `bytes` is None and path is remote (hf:// or https://) → `hf_video_reader(path, ...)` which downloads via `xopen()` then decodes
5. Stores original `{"path": ..., "bytes": ...}` as `video._hf_encoded` for potential re-encoding
6. Sets `video.metadata.path` to the original path

**Dependency requirement:** `torchcodec` must be installed. Datasets checks `config.TORCHCODEC_AVAILABLE` which is set at import time.

### Storage Casting — cast_storage()

The `cast_storage()` method converts various Arrow types into the canonical struct format:

| Source Arrow Type | Conversion |
|-------------------|------------|
| `pa.string()` | path → `{"bytes": None, "path": string}` |
| `pa.binary()` / `pa.large_binary()` | bytes → `{"bytes": binary, "path": None}` |
| `pa.struct({"bytes": binary, "path": string})` | Any subset of fields; missing fields filled with null |
| `pa.list_(*)` | numpy array → `encode_np_array()` — **raises NotImplementedError** |

### TorchCodec — The Decoding Backend

`torchcodec` (v0.15.0, PyTorch ecosystem) is the required backend for datasets video decoding. It wraps FFmpeg (v4–v8 supported) and returns PyTorch tensors directly.

**Key VideoDecoder API:**

```python
from torchcodec.decoders import VideoDecoder

decoder = VideoDecoder("path/to/video.mp4", device="cpu")
# or from bytes:
decoder = VideoDecoder(video_bytes, device="cpu")

# Metadata
decoder.metadata  # VideoStreamMetadata: num_frames, duration_seconds, codec, fps, etc.

# Simple indexing (returns uint8 tensor [C, H, W])
frame = decoder[0]
batch = decoder[0:-1:20]  # [N, C, H, W] stacked tensor

# Frame batch with PTS/duration
batch = decoder.get_frames_at(indices=[2, 100])
# FrameBatch:
#   data: torch.Size([2, 3, H, W])
#   pts_seconds: tensor
#   duration_seconds: tensor

# Time-based
batch = decoder.get_frames_played_at(seconds=[0.5, 10.4])
```

**TorchCodec Encoding (CPU only):**

```python
from torchcodec.encoders import Encoder

encoder = Encoder()
video_stream = encoder.add_video(height=H, width=W, frame_rate=30)
audio_stream = encoder.add_audio(sample_rate=16000, num_channels=1)
with encoder.open_file("output.mp4"):
    video_stream.add_frames(frames_batch_0)
    audio_stream.add_samples(samples_batch_0)
```

**Note:** encoding from datasets is not yet integrated — `encode_torchcodec_video()` and `encode_np_array()` are stubs that raise `NotImplementedError`.

### VideoFolder — Zero-Code Video Dataset Builder

`VideoFolder` is a `datasets` builder class for creating video datasets from a directory structure without writing any code.

**Directory structure for classification:**

```
folder/
├── train/
│   ├── dog/
│   │   ├── golden_retriever.mp4
│   │   └── german_shepherd.mp4
│   └── cat/
│       ├── maine_coon.mp4
│       └── bengal.mp4
└── test/
    ├── dog/
    └── cat/
```

**Loading:**

```python
from datasets import load_dataset

# Auto-detect VideoFolder from directory structure
dataset = load_dataset("path/to/folder")

# Equivalent explicit form:
dataset = load_dataset("videofolder", data_dir="/path/to/folder")
```

**Split pattern hierarchy:** VideoFolder follows the same split directory conventions as ImageFolder — top-level directories become split names. See [Split pattern hierarchy](https://huggingface.co/docs/datasets/en/image_dataset#videofolder) for details.

**Label inference:** Class labels are automatically inferred from subdirectory names. If all videos are in a single directory or mixed levels, set `drop_labels=False` to force label column creation.

### Metadata Integration — CSV/JSONL/Parquet

For richer datasets (captions, bounding boxes, multi-video rows), add a `metadata.csv`, `metadata.jsonl`, or `metadata.parquet` file:

```
folder/
└── train/
    ├── metadata.csv
    ├── 0001.mp4
    ├── 0002.mp4
    └── 0003.mp4
```

**metadata.csv format:**
```csv
file_name,text
0001.mp4,"A golden retriever playing with a ball"
0002.mp4,A german shepherd running
0003.mp4,One chihuahua barking
```

**Multi-video rows:** Use `file_name` (single) or `*_file_name`/`*_file_names` (plural for lists):

```json
{"input_file_name": "0001.mp4", "output_file_name": "0001_output.mp4"}
{"videos_file_names": ["0001_left.mp4", "0001_right.mp4"], "label": "moving_up"}
```

The `file_name` field must be the relative path from the metadata file's directory to the video file.

### WebDataset — TAR-Based Large-Scale Video

For datasets with thousands-to-millions of videos, group them into TAR archives (~1GB each):

```
folder/
├── train/
│   ├── 00000.tar
│   ├── 00001.tar
│   └── 00002.tar
```

Each TAR contains videos plus associated metadata files (JSON, text):
```
00000.tar/
├── video_000.mp4
├── video_000.json    # {"bbox": [...], "categories": [...]}
├── video_001.mp4
├── video_001.json
```

**Loading:**
```python
dataset = load_dataset("webdataset", data_dir="/path/to/folder", split="train")
# Each file suffix becomes a column: "mp4", "json", etc.
```

**Shard sizing:** 1GB per TAR is the recommended sweet spot — balances random access granularity with filesystem overhead. Datasets streams from TARs without extracting the full archive.

### Lance Format — Native Blob Storage

[Lance](https://lancedb.github.io/lance/) is an open multimodal lakehouse table format. Video blobs are stored natively alongside metadata columns.

**Schema definition:**
```python
import lance
import pyarrow as pa

schema = pa.schema([
    pa.field("caption", pa.utf8()),
    pa.field("aesthetic_score", pa.float64()),
    pa.field("video_blob", pa.large_binary(),
             metadata={"lance-encoding:blob": "true"}),
])
```

**Key advantages:**
- Single directory artifact — `videos.lance/` contains both metadata and videos
- Efficient metadata-only scans without loading video blobs
- On-demand blob fetching when accessing the video column
- `max_bytes_per_file` for controlling shard sizes (~5GB default)

**Upload to Hub:**
```python
api.upload_folder(folder_path="./videos.lance",
                  repo_id="username/my-video-dataset",
                  repo_type="dataset")
```

### Memory Management Patterns

#### Deferred Decode
```python
# Store paths only, no decode until accessed
ds = ds.cast_column("video", Video(decode=False))
# Later: access triggers lazy decode per-row
```

#### embed_storage() — Inline Bytes
```python
# Embed all video bytes into Arrow array (memory-hungry, but self-contained)
ds_embedded = ds.map(...)  # videos embedded automatically
```

#### token_per_repo_id — Private Repos
```python
token_per_repo_id = {"username/private-video-dataset": True}
video = ds[0]["video"]  # Uses token for auth via hf_video_reader
```

#### Streaming with Video
```python
# Stream from Hub without downloading full dataset
ds = load_dataset("username/video-dataset", split="train", streaming=True)
for example in ds:
    video = example["video"]  # Decoded on-demand per row
    break
```

### Remote File Handling — hf_video_reader()

When video files are stored in Hub datasets (hf:// paths) or remote URLs, the `hf_video_reader()` function handles transparent download and decode:

```python
def hf_video_reader(
    path: str,
    token_per_repo_id=None,
    stream="video",
    dimension_order="NCHW",
    num_ffmpeg_threads=1,
    device="cpu",
    seek_mode="exact",
) -> VideoDecoder:
```

It resolves the HF URL pattern, downloads via `xopen()` with optional auth token, and passes the file object to `VideoDecoder`. The decoder reads from the file object directly without writing to disk.

### Zero-Cost Patterns

1. **Small-scale:** Use local `VideoFolder` with metadata CSV — no infrastructure needed
2. **Medium-scale:** Stream from Hub datasets — read videos on-demand, no download
3. **Large-scale:** WebDataset TAR shards — stream from TARs without extraction
4. **Self-contained:** Lance format — single directory, upload to Hub as one artifact
5. **Memory-constrained:** Set `Video(decode=False)` to store paths only, decode only accessed rows
6. **No GPU:** All decoding defaults to CPU; FFmpeg is already system-installed on most Linux distros

### Dependencies & Installation

```bash
# Core: datasets + torchcodec
pip install datasets torchcodec

# FFmpeg must be available (usually pre-installed on Linux)
ffmpeg -version  # Verify

# Lance is optional
pip install lancedb
```

**Note on torchcodec FFmpeg compatibility:** TorchCodec supports FFmpeg v4–v8. Linux distributions typically include FFmpeg. For CUDA decode, torchcodec supports `device="cuda"`.

### Source Code References
- `Video` feature: [`src/datasets/features/video.py`](https://github.com/huggingface/datasets/blob/main/src/datasets/features/video.py)
- Feature registration: [`src/datasets/features/features.py`](https://github.com/huggingface/datasets/blob/main/src/datasets/features/features.py) (Video import at line 50, registration at lines 1373/1535)
- TorchCodec: [`github.com/pytorch/torchcodec`](https://github.com/pytorch/torchcodec)
- VideoFolder builder: [`src/datasets/packaged_modules/videofolder/`](https://github.com/huggingface/datasets/tree/main/src/datasets/packaged_modules/videofolder)
- Docs: https://huggingface.co/docs/datasets/main/en/video_dataset


---

## 2026-07-24: Deep Dive v2 — torchcodec 0.15.0 Advanced Features & Practical Patterns

### Summary
Second deep-dive focusing on **new torchcodec 0.15.0+ features** not covered in the initial deep-dive: in-decoder transforms (`transforms=[]`), `output_dtype` for direct float32/float16 decode, `custom_frame_mappings` for raw FFmpeg filter graphs, the new `samplers` module, `AudioDecoder`/`WavDecoder`, `SimpleVideoDecoder`, enhanced `VideoStreamMetadata` (21+ fields), and `Encoder` improvements. All verified against torchcodec 0.15.0+cu130 and datasets 5.0.0.

### New in 0.15.0+

**1. VideoDecoder new params:**
- `output_dtype` — decode directly as float32/float16 (range [0.0, 1.0]), eliminating `.float() / 255.0`
- `transforms` — in-decoder transforms: `Resize`, `CenterCrop`, `RandomCrop`; extensible via `DecoderTransform`
- `custom_frame_mappings` — raw FFmpeg filter graph expressions (e.g., `"format=gray"` for grayscale)

**2. Samplers module** (`torchcodec.samplers`):
- Index-based: `clips_at_regular_indices`, `clips_at_random_indices`
- Time-based: `clips_at_regular_timestamps`, `clips_at_random_timestamps`
- Policies: `repeat_last`, `wrap`, `error`
- Returns batched `FrameBatch(N, T, C, H, W)` tensors

**3. Audio** — `AudioDecoder(video_path)` extracts audio from video containers; `WavDecoder` for WAV files; `AudioSamples` dataclass with `data, pts_seconds, duration_seconds, sample_rate`

**4. SimpleVideoDecoder** — method-based API without bracket indexing

**5. Metadata expansion** — 21+ fields including `num_frames_from_header`, `num_frames_from_content`, `average_fps_from_header`, `bit_rate`, `pixel_format`, `color_primaries`, `color_space`, `rotation`, `pixel_aspect_ratio`

**6. CpuFallbackStatus** — tracks GPU decode health: `NO_FALLBACK | FALLBACK | ALWAYS_WAS_CPU`

**7. Encoder** — `Encoder` with `add_video(codec, crf, preset)`, `add_audio()`, `open_file()`, `open_file_like()` for in-memory output

### Key Takeaways
- In-decoder transforms + typed decode save ~4x memory (no intermediate uint8)
- Samplers replace manual extraction loops
- datasets Video (5.0.0) lags torchcodec — new features not exposed through datasets
- Direct torchcodec use recommended for full capability

### Full reference
See consolidated `/opt/data/profiles/sakthai/skills/references/hf-learnings.md` for the complete v2 deep-dive with all code examples and parameter tables.
