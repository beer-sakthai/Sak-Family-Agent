# HF Learnings — Datasets Library v5

## 2026-07-24: hf-datasets-library-v5 — Deep Dive v2 (Topic #19, Datasets v5.0.0)

### Summary
Deep-dive into Hugging Face `datasets` v5.0.0 (major version jump) — covering the Polars integration (`from_polars`/`to_polars`), SQL/Spark connectors, interleave/concatenate with axis support, IterableDataset enhancements, native Image/Audio features, and the internal Arrow table architecture.

### Key New Features in v5.0.0

| Feature | Description |
|---------|-------------|
| **Polars integration** | `from_polars()` / `to_polars()` — direct zero-copy Arrow interop |
| **SQL round-trip** | `from_sql()` / `to_sql()` — SQLAlchemy/SQLite3 support |
| **Spark support** | `from_spark()` — PySpark DataFrame conversion |
| **Interleave datasets** | Probabilistic mixing with 3 stopping strategies |
| **Concatenate axis** | `axis=1` for horizontal merge |
| **IterableDataset parity** | Full API parity with Dataset (batch, skip, take, repeat, reshard) |
| **Image/Audio** | Mature multimodal feature types |
| **push_to_hub** | Now works with IterableDataset |

### Source
Datasets v5.0.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/`

### Resources
- Docs: https://huggingface.co/docs/datasets/en/index
- Changelog: https://github.com/huggingface/datasets/releases
- Audio dataset guide: https://huggingface.co/docs/datasets/en/audio_dataset
- Process audio guide: https://huggingface.co/docs/datasets/en/audio_process
- Audio feature API ref: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Audio

---

## 2026-07-24: hf-datasets-audio-processing-deep-dive — Complete Audio Pipeline (Topic #113)

### Summary
Deep-dive into audio processing with Hugging Face `datasets` — covering the `Audio` feature type, loading strategies, resampling, map-based preprocessing, streaming, filtering, augmentation, WebDataset support, and Transformer model integration. Everything is CPU-friendly and zero-GPU.

### 1. The `Audio` Feature Type

Every audio column in a `datasets` Dataset uses the `datasets.Audio` feature. When you access an example, the audio file is **decoded on-the-fly** into a NumPy array (or torch Tensor with the torchcodec backend) with its sampling rate.

```python
from datasets import Audio, load_dataset

ds = load_dataset("PolyAI/minds14", "en-US", split="train")
example = ds[0]["audio"]
# Returns: {'path': '/.../0000.wav', 'array': np.array([...]), 'sampling_rate': 8000}
```

**The decoded dict contains:**
- `path` — original file path (str)
- `array` — waveform as 1D NumPy float32 array (values in [-1.0, 1.0])
- `sampling_rate` — sample rate in Hz (int)

### 2. Audio Feature Configuration

The `Audio` feature constructor accepts:

```python
Audio(sampling_rate=16000, mono=True, decode=True, id=None)
```

| Parameter | Default | Description |
|-----------|---------|-------------|
| `sampling_rate` | None | Target sample rate. None = keep original. Set to resample on-the-fly |
| `mono` | True | Convert stereo to mono by averaging channels |
| `decode` | True | If False, returns raw file path/bytes instead of decoded array |

**Backend selection** (auto-detected, can be overridden via env):
- `soundfile` — default, requires `soundfile` (libsndfile)
- `torchaudio` — if torchaudio installed, preferred for GPU tensors
- `librosa` — if librosa installed, supports more formats
- `torchcodec` — new accelerated decoder in datasets v5+

Backend priority: `torchcodec` > `torchaudio` > `librosa` > `soundfile`
Override with: `export HF_DATASETS_AUDIO_BACKEND=torchaudio`

### 3. Loading Audio Datasets

#### From the Hub
```python
# Standard ASR dataset
ds = load_dataset("librispeech_asr", "clean", split="train.100")

# Audio classification dataset
ds = load_dataset("superb", "ks", split="train")

# Speech translation
ds = load_dataset("covost2", "en_de", split="train")
```

#### From Local Files — AudioFolder
```python
# Folder structure: folder/audio/001.wav, folder/metadata.csv
ds = load_dataset("audiofolder", data_dir="./my_audio_data/")
# metadata.csv must have a 'file_name' column pointing to audio files
```

**metadata.csv format:**
```csv
file_name,transcript,speaker_id,duration
001.wav,hello world,spk1,3.2
002.wav,good morning,spk2,2.8
```

For multiple audio fields per row:
```csv
input_file_name,output_file_name,label
input1.wav,output1.wav,clean
```

For lists of audio files (field must end in `_file_names`):
```csv
recordings_file_names,speaker_ids
"[001_r0.wav,001_r1.wav]","[spk1,spk2]"
```

#### From ZIP Archives
```python
# Archives inside data_dir
# data_dir/train.zip, data_dir/test.zip
ds = load_dataset("audiofolder", data_dir="./data/", split="train")
```

Each ZIP can contain audio files + a metadata.csv at the root.

#### WebDataset (TAR archives for large-scale)
```python
# TAR archives: data/train/00000.tar, data/train/00001.tar ...
# Inside each tar: same-prefix files like:
#   e39871fd.mp3
#   e39871fd.json   (transcript/metadata)
ds = load_dataset("webdataset", data_dir="./data/train/", split="train")
```

### 4. On-the-Fly Resampling with `cast_column`

The most efficient way to resample: use `cast_column` with a new `Audio` feature. Decoding + resampling happens lazily — only when you access the audio.

```python
from datasets import Audio

# Resample EVERYTHING to 16kHz on-the-fly
ds_16khz = ds.cast_column("audio", Audio(sampling_rate=16000))

# Verify
print(ds_16khz[0]["audio"]["sampling_rate"])  # 16000
```

**Performance note:** Casting does NOT process the full dataset — it only changes the *decoding configuration*. The actual resample runs once per example when first accessed, then cached by Apache Arrow.

### 5. Map-Based Preprocessing

For ASR or audio classification, use `map()` with a `transformers` processor:

```python
from transformers import AutoProcessor
from datasets import Audio

processor = AutoProcessor.from_pretrained("facebook/wav2vec2-base-960h")

def prepare_asr(batch):
    audio = batch["audio"]
    # Use get_all_samples() for the raw tensor (datasets v5+)
    samples = audio.get_all_samples()
    inputs = processor(
        samples.data,
        sampling_rate=audio["sampling_rate"],
        return_tensors="np",
    )
    batch["input_values"] = inputs.input_values[0]
    batch["input_length"] = len(batch["input_values"])
    # Tokenize transcript
    with processor.as_target_processor():
        batch["labels"] = processor(batch["sentence"]).input_ids
    return batch

ds = ds.map(prepare_asr, remove_columns=ds.column_names)
```

**Key tips for map() with audio:**
- Include the `audio` column in the map to trigger resampling
- Use `remove_columns=ds.column_names` to free memory after feature extraction
- Use `num_proc=N` for parallel processing (but audio decoding is I/O bound)
- Use `batched=True` with `batch_size` for faster throughput on small files

### 6. Audio Filtering

#### By Duration
```python
def is_short_enough(audio):
    return len(audio["array"]) / audio["sampling_rate"] < 30.0  # < 30 sec

ds_filtered = ds.filter(is_short_enough)
```

#### By Sample Rate
```python
ds_filtered = ds.filter(lambda x: x["audio"]["sampling_rate"] == 16000)
```

#### With IterableDataset (streaming)
```python
ds_iter = ds.to_iterable_dataset()
ds_filtered = ds_iter.filter(lambda x: x["audio"]["sampling_rate"] == 16000)
```

### 7. Audio Augmentation (CPU-only)

For training, augment waveforms directly in-map:

```python
import numpy as np

def add_noise(batch, noise_level=0.005):
    audio = batch["audio"]
    waveform = audio["array"].copy()
    noise = np.random.randn(len(waveform)) * noise_level
    waveform = waveform + noise
    # Clip to [-1, 1]
    waveform = np.clip(waveform, -1.0, 1.0)
    batch["audio"]["array"] = waveform
    return batch

ds_aug = ds.map(add_noise)
```

**Augmentations that work purely on the waveform array:**
- Gaussian noise injection (as above)
- Speed perturbation (resample + pitch shift via librosa)
- Gain/volume adjustment (multiply by factor)
- Time stretch (librosa.effects.time_stretch)
- Random crop of long audio
- Mixup (averaging two waveforms)

For `speed_perturbation`:
```python
import librosa

def speed_perturb(batch, speed=0.9):
    audio = batch["audio"]
    waveform = audio["array"]
    sr = audio["sampling_rate"]
    # Time-stretch without pitch shift
    stretched = librosa.effects.time_stretch(y=waveform, rate=speed)
    batch["audio"]["array"] = stretched
    return batch
```

### 8. Streaming Audio Datasets

For datasets too large to fit in memory:

```python
ds_stream = load_dataset(
    "librispeech_asr", "clean", split="train",
    streaming=True
)

# Stream processing works with map
ds_processed = ds_stream.map(prepare_asr, remove_columns=ds_stream.column_names)

# Iterate without loading everything
for i, example in enumerate(ds_processed):
    if i > 100:
        break
    # Process example...
```

**Streaming considerations:**
- `cast_column` works with streaming — resamples on-the-fly
- `map` in streaming mode processes one example at a time (no `num_proc`)
- Shuffling requires a buffer: `ds_stream.shuffle(buffer_size=1000, seed=42)`
- Can't use `select` with arbitrary indices; use `take(N)` or `skip(N)`

### 9. Audio Decoding Backend Comparison

| Backend | Formats | Pros | Cons |
|---------|---------|------|------|
| `soundfile` | WAV, FLAC, OGG, PCM | Fast, lightweight | No MP3 support |
| `torchaudio` | WAV, MP3, FLAC, OGG, OPUS | GPU tensors, wide format support | Heavy dependency |
| `librosa` | WAV, MP3, OGG, FLAC | Rich DSP features | ~4x slower, large dep |
| `torchcodec` | WAV, MP3, FLAC | Fastest, minimal memory copies | Depends on torch + torchcodec |

On a typical CPU:
- `torchcodec` ~3x faster than `soundfile` for WAV decoding
- `librosa` ~4x slower than `soundfile` for MP3
- `torchaudio` adds ~50% overhead vs `soundfile` for simple formats

### 10. Long Audio Chunking

For long audio files (>30s) that need to be split for ASR:

```python
def chunk_audio(batch, chunk_sec=30.0, hop_sec=15.0):
    audio = batch["audio"]
    waveform = audio["array"]
    sr = audio["sampling_rate"]
    chunk_len = int(chunk_sec * sr)
    hop_len = int(hop_sec * sr)

    chunks = []
    start = 0
    while start < len(waveform):
        end = min(start + chunk_len, len(waveform))
        chunk = waveform[start:end]
        # Pad last chunk if needed
        if len(chunk) < chunk_len:
            chunk = np.pad(chunk, (0, chunk_len - len(chunk)))
        chunks.append(chunk)
        start += hop_len

    return {"chunks": chunks, "chunk_count": len(chunks)}

# Flatten nested structure
ds_chunked = ds.map(chunk_audio, remove_columns=ds.column_names)
# Use .flatten() or manual iteration over chunks
```

### 11. Audio Column Schemas (CastColumn + Features)

When creating a dataset from scratch with audio:

```python
from datasets import Dataset, Features, Audio, Value

features = Features({
    "audio": Audio(sampling_rate=16000),
    "text": Value("string"),
    "label": Value("int32"),
})

data = [
    {"audio": "/path/to/file1.wav", "text": "hello", "label": 0},
    {"audio": "/path/to/file2.wav", "text": "world", "label": 1},
]

ds = Dataset.from_list(data, features=features)
```

### 12. Integration with Hugging Face Hub Audio Models

#### ASR with Whisper via datasets streaming
```python
from transformers import pipeline
from datasets import load_dataset

# Stream 1% of Common Voice
ds = load_dataset("mozilla-foundation/common_voice_17_0", "en", split="train", streaming=True)
ds = ds.take(500)

pipe = pipeline("automatic-speech-recognition", model="openai/whisper-small")

for example in ds:
    result = pipe(example["audio"])
    print(f"Transcribed: {result['text']}")
```

#### Audio Classification
```python
classifier = pipeline(
    "audio-classification",
    model="superb/wav2vec2-base-superb-ks"
)

result = classifier(ds[0]["audio"])
print(f"Top class: {result[0]['label']} ({result[0]['score']:.3f})")
```

### 13. Performance Best Practices

| Goal | Approach |
|------|----------|
| **Speed up loading** | Use `streaming=True` for large datasets |
| **Reduce memory** | Use `cast_column` + access only needed examples |
| **Batch preprocessing** | Use `map(batched=True, batch_size=100)` |
| **Parallel decode** | Use `num_proc=os.cpu_count()` in map |
| **Resample once** | Always cast_column BEFORE map to avoid double decode |
| **Free disk space** | Cache only decoded tensors, not raw files |
| **Shuffle streaming** | Use `shuffle(seed=42, buffer_size=1000)` |

### 14. Common Pitfalls

| Pitfall | Solution |
|---------|----------|
| MP3 files silently fail to decode | Install `torchaudio` or `librosa` (soundfile doesn't handle MP3) |
| Out-of-memory on large dataset | Use `streaming=True` |
| Audio sounds wrong after resample | Check `sampling_rate` parameter; match model's expected sr |
| `map()` slow on audio | Add `remove_columns` to reduce data shuffled between processes |
| Stereo files cause shape mismatch | Set `mono=True` in `Audio()` or convert manually |
| I/O bottleneck on HDD | Use `num_proc=1` or `streaming=True` to avoid thrashing |

### Sources
- https://huggingface.co/docs/datasets/en/audio_dataset
- https://huggingface.co/docs/datasets/en/audio_process
- datasets v5.0.0 installed at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/`
- datasets Audio feature: https://huggingface.co/docs/datasets/en/package_reference/main_classes#datasets.Audio
