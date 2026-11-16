# HF InferenceClient — Audio, TTS & ASR Deep Dive

## Overview

The Hugging Face InferenceClient provides four audio-related inference methods: text-to-speech (TTS), automatic speech recognition (ASR), audio classification, and audio-to-audio. All are accessible through both `InferenceClient` (sync) and `AsyncInferenceClient` (async). These methods connect to the Hugging Face Inference Providers API, routing through provider-specific helpers.

## Source-Verified Analysis (huggingface_hub v1.24.0)

### 1. `text_to_speech()` — Text-to-Speech Synthesis

**Signature:**
```python
def text_to_speech(
    self,
    text: str,
    *,
    model: str | None = None,
    do_sample: bool | None = None,
    early_stopping: Union[bool, "TextToSpeechEarlyStoppingEnum"] | None = None,
    epsilon_cutoff: float | None = None,
    eta_cutoff: float | None = None,
    max_length: int | None = None,
    max_new_tokens: int | None = None,
    min_length: int | None = None,
    min_new_tokens: int | None = None,
    num_beam_groups: int | None = None,
    num_beams: int | None = None,
    penalty_alpha: float | None = None,
    temperature: float | None = None,
    top_k: int | None = None,
    top_p: float | None = None,
    typical_p: float | None = None,
    use_cache: bool | None = None,
    extra_body: dict[str, Any] | None = None,
) -> bytes:
```

**Key facts:**
- Returns raw `bytes` — the WAV audio blob. Not a JSON response, not structured data.
- Full generation parameters supported (same as text generation): beam search, sampling, top-k/top-p, temperature, length constraints.
- `extra_body` passes provider-specific parameters (e.g., voice ID, speed, language for specific TTS models).
- No streaming parameter currently (response is the complete audio blob).
- Default model: provider-selected default TTS model when `model=None`.

**Inner workings:**
```python
model_id = model or self.model
provider_helper = get_provider_helper(self.provider, task="text-to-speech", model=model_id)
request_parameters = provider_helper.prepare_request(
    inputs=text,                # text input as string
    parameters={...},           # all generation params as dict
    headers=self.headers,
    model=model_id,
    api_key=self.token,
)
response = self._inner_post(request_parameters)
response = provider_helper.get_response(response)
return response
```

**Audio output format:** The raw bytes returned are typically WAV format audio. The provider helper handles converting the API response to bytes. No format negotiation parameter exists in the current API.

**Models:** Popular TTS models available through the Inference API:
- `hexgrad/Kokoro-82M` (10M+ downloads, 6.5K likes) — top open TTS model
- `coqui/XTTS-v2` (9.3M+ downloads) — voice cloning TTS
- `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (2.5M+ downloads) — Qwen's custom voice TTS
- `openbmb/VoxCPM2` (1M+ downloads) — multilingual voice cloning
- `SWivid/F5-TTS` (780K+ downloads) — zero-shot TTS

### 2. `automatic_speech_recognition()` — ASR / Speech-to-Text

**Signature:**
```python
def automatic_speech_recognition(
    self,
    audio: ContentT,
    *,
    model: str | None = None,
    extra_body: dict | None = None,
) -> AutomaticSpeechRecognitionOutput:
```

**ContentT type:** `bytes | BinaryIO | str | Path | Image | bytearray | memoryview`
- Audio can be raw bytes, a local file path (str or Path), a URL string, a file-like object (BinaryIO), bytearray, or memoryview.
- URLs are fetched by the server — no need to pre-download.

**Returns:**
```python
@dataclass
class AutomaticSpeechRecognitionOutput:
    text: str                                    # Transcribed text
    chunks: list[AutomaticSpeechRecognitionOutputChunk] | None  # Optional timestamp chunks

@dataclass
class AutomaticSpeechRecognitionOutputChunk:
    text: str                                    # Text for this chunk
    timestamp: list[float]                       # [start_seconds, end_seconds]
```

**Key facts:**
- Minimal parameters — only `model` and `extra_body`. No generation params (temperature, top-k, etc.) unlike TTS.
- Timestamp chunks are `None` when the model doesn't support timestamp output; otherwise each chunk has `text` and `[start, end]` timestamps.
- Logits/attention output: None for audio methods (no `output_logits` or similar params).

**Inner workings:**
```python
model_id = model or self.model
provider_helper = get_provider_helper(self.provider, task="automatic-speech-recognition", model=model_id)
request_parameters = provider_helper.prepare_request(
    inputs=audio,               # audio content: bytes, URL, file path, etc.
    parameters={**(extra_body or {})},
    headers=self.headers,
    model=model_id,
    api_key=self.token,
)
response = self._inner_post(request_parameters)
response = provider_helper.get_response(response)
return AutomaticSpeechRecognitionOutput.parse_obj_as_instance(response)
```

**Models:** Popular ASR models:
- `openai/whisper-large-v3-turbo` (8.4M+ downloads) — fastest Whisper variant
- `openai/whisper-large-v3` (6.1M+ downloads) — most accurate Whisper
- `openai/whisper-base` (6.6M+ downloads) — lightweight
- `openai/whisper-small` (3.2M+) — balanced size/accuracy
- Various `wav2vec2` models for specific languages (Portuguese, Russian, etc.)

### 3. `audio_to_audio()` — Audio Enhancement & Source Separation

**Signature:**
```python
def audio_to_audio(
    self,
    audio: ContentT,
    *,
    model: str | None = None,
) -> list[AudioToAudioOutputElement]:
```

**Returns:**
```python
@dataclass
class AudioToAudioOutputElement:
    blob: Any                    # Raw audio bytes
    content_type: str            # MIME type (e.g., "audio/flac", "audio/wav")
    label: str                   # Description label (e.g., "speech", "noise", source name)
```

**Key facts:**
- No generation parameters at all — just audio input and model selection.
- Returns a **list** of elements — source separation models return multiple audios.
- Each element has a `label` identifying what the audio represents.
- Used for: speech enhancement, background noise removal, source separation (e.g., separate instruments or speakers).

### 4. `audio_classification()` — Audio Label Classification

**Signature:**
```python
def audio_classification(
    self,
    audio: ContentT,
    *,
    model: str | None = None,
    top_k: int | None = None,
    function_to_apply: Optional["AudioClassificationOutputTransform"] = None,
) -> list[AudioClassificationOutputElement]:
```

**Returns:**
```python
@dataclass
class AudioClassificationOutputElement:
    label: str                     # Class label (e.g., "speech", "music", "applause")
    score: float                   # Confidence score (0-1)
```

**Key facts:**
- `top_k` limits output to top K most probable classes.
- `function_to_apply` controls score transformation (softmax, sigmoid, etc.).
- Returns sorted list by score descending.

### Provider Helper Pattern

All four audio methods use the same provider helper pattern:

1. `get_provider_helper(provider, task="<task-name>", model=model_id)` selects the correct provider adapter.
2. `provider_helper.prepare_request(inputs=..., parameters=..., headers=..., model=..., api_key=...)` prepares the HTTP request (URL, JSON body or binary data, headers).
3. `self._inner_post(request_parameters)` executes the HTTP POST via `httpx` streaming session.
4. `provider_helper.get_response(response)` transforms the raw HTTP response into the typed return value.

The task names are: `"text-to-speech"`, `"automatic-speech-recognition"`, `"audio-to-audio"`, `"audio-classification"`.

### Async Interface

All four methods have async equivalents on `AsyncInferenceClient` with identical signatures but `async def`:

```python
async client.text_to_speech(text, ...) -> bytes
async client.automatic_speech_recognition(audio, ...) -> AutomaticSpeechRecognitionOutput
async client.audio_to_audio(audio, ...) -> list[AudioToAudioOutputElement]
async client.audio_classification(audio, ...) -> list[AudioClassificationOutputElement]
```

### HTTP Layer (`_inner_post`)

All audio tasks flow through `_inner_post()` which uses `get_session().stream("POST", url, json=..., content=..., headers=..., cookies=..., timeout=...)`. The `json` or `content` field is set by the provider helper based on whether audio is sent as JSON (URL) or raw binary data (file bytes). Audio tasks are NOT in `TASKS_EXPECTING_IMAGES` (which only contains `text-to-image` and `image-to-image`), so no automatic Accept header override occurs.

### Zero-Cost Relevance

- All four audio methods are available through free serverless inference for supported models.
- TTS models like Kokoro-82M are small enough for CPU inference (82M params) — zero-cost.
- ASR via Whisper variants is available through free inference tiers with rate limits.
- Audio-to-audio and audio classification models similarly available.
- Beer's TTS Space can use `InferenceClient.text_to_speech()` as a zero-cost backend.

### Practical Usage Patterns

**TTS:**
```python
from huggingface_hub import InferenceClient
client = InferenceClient()
audio_bytes = client.text_to_speech(
    "Hello, this is a test of text-to-speech.",
    model="hexgrad/Kokoro-82M",
)
with open("output.wav", "wb") as f:
    f.write(audio_bytes)
```

**ASR:**
```python
result = client.automatic_speech_recognition("recording.flac")
print(result.text)  # "transcribed text"
if result.chunks:
    for chunk in result.chunks:
        print(f"[{chunk.timestamp[0]:.1f}s-{chunk.timestamp[1]:.1f}s] {chunk.text}")
```

**Audio Classification:**
```python
results = client.audio_classification("audio.wav", top_k=3)
for r in results:
    print(f"{r.label}: {r.score:.3f}")
```

**Audio-to-Audio (Source Separation):**
```python
results = client.audio_to_audio("mixed_audio.wav")
for i, item in enumerate(results):
    print(f"Output {i}: {item.label} ({item.content_type})")
    with open(f"output_{i}.wav", "wb") as f:
        f.write(item.blob)
```

