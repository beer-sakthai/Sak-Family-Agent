---
name: SakThai-hf-audio-course
description: "Process audio with transformers — ASR, TTS, classification, music gen, audio processing, fine-tuning."
---

# Audio Transformers with Hugging Face

Based on the [HF Audio Course](https://huggingface.co/learn/audio-course). Covers the full pipeline: audio data processing → model selection → inference → fine-tuning → deployment.

## Course Structure (HF Audio Course)

The official course has 8 units released progressively:

| Unit | Topic | Key Content |
|------|-------|-------------|
| 0 | Getting Ready | Setup, prerequisites, environment |
| 1 | Working with Audio Data | Sampling rates, spectrograms, mel-frequency cepstral coefficients, data loading |
| 2 | Audio Applications via Pipelines | ASR, audio classification, TTS — one-liner inference |
| 3 | Audio Transformer Architectures | Encoder-only (Wav2Vec2, HuBERT), Encoder-decoder (Whisper, SpeechT5), Decoder-only (AudioLM) |
| 4 | Build a Music Genre Classifier | Fine-tune a pretrained audio model on GTZAN dataset |
| 5 | Speech Recognition | Fine-tune Whisper on meeting recordings, evaluation with WER |
| 6 | Text-to-Speech | Bark, SpeechT5, Parler-TTS — generate speech from text |
| 7 | Real-world Audio Applications | Streaming, deployment on Spaces, Gradio demos |
| 8 | Finish Line | Certification, next steps |

**Certification**: 80% exercises → Certificate of Completion. 100% → Certificate of Honors.

## When to Use

- "transcribe audio" or "convert speech to text" → ASR (Whisper)
- "generate speech from text" → TTS (Bark, SpeechT5, Parler-TTS)
- "classify audio" or "music genre detection" → Audio Classification (Wav2Vec2, AST)
- "fine-tune on my audio dataset" → Use `transformers.Trainer` with audio models
- "Music generation from text" → MusicGen (facebook/musicgen-small)
- "Multilingual speech translation" → SeamlessM4T
- "speaker diarization" → pyannote-audio
- "voice cloning" → SpeechT5 + speaker embeddings

## Prerequisites

```bash
pip install transformers datasets librosa soundfile torch accelerate
# For Whisper fine-tuning (GPU recommended)
pip install evaluate jiwer
# For MusicGen
pip install audiocraft
# For PEFT-based fine-tuning (memory-efficient)
pip install peft
# For speaker diarization
pip install pyannote-audio
```

Audio files: wav, mp3, flac, ogg. Model expects 16kHz mono — resample if needed.

## Model Comparison Table

### ASR Models

| Model | Parameters | Languages | WER (LibriSpeech-clean) | Speed | VRAM |
|-------|-----------|-----------|------------------------|-------|------|
| `openai/whisper-large-v3-turbo` | 809M | 100+ | 1.8% | Fast | 6GB |
| `openai/whisper-large-v3` | 1.5B | 100+ | 1.6% | Moderate | 10GB |
| `openai/whisper-medium` | 769M | 100+ | 3.3% | Fast | 5GB |
| `openai/whisper-small` | 244M | 100+ | 5.0% | Fast | 2.5GB |
| `openai/whisper-base` | 74M | 100+ | 7.8% | Very Fast | 1GB |
| `openai/whisper-tiny` | 39M | 100+ | 11.2% | Fastest | 0.5GB |
| `distil-whisper/distil-large-v3` | 756M | 100+ | 2.0% | 2x faster than large-v3 | 5GB |
| `distil-whisper/distil-medium.en` | 384M | EN | 3.5% | 2x faster | 3GB |
| `facebook/wav2vec2-large-960h` | 317M | EN | 2.7% | Fast | 4GB |
| `facebook/hubert-large-ls960` | 317M | EN | 3.0% | Fast | 4GB |
| `facebook/mms-1b-all` | 1B | 1400+ | 4.5%* | Moderate | 8GB |

### TTS Models

| Model | Parameters | Voice Control | Languages | Speed | Quality |
|-------|-----------|---------------|-----------|-------|---------|
| `suno/bark` | 1.2B | Speaker prompt | EN+ | Slow (CPU) | Very Expressive |
| `parler-tts/parler-tts-large-v1` | 1.5B | Text description | EN | Moderate | High |
| `microsoft/speecht5_tts` | 600M | Speaker embedding | Multi | Fast | Good |
| `facebook/mms-tts` | 1B | Language select | 1100+ | Moderate | Good |
| `coqui/XTTS-v2` | 1.6B | Voice cloning 3s | 17 | Moderate | High |

### Audio Classification Models

| Model | Parameters | Tasks | 
|-------|-----------|-------|
| `facebook/wav2vec2-base` | 95M | General audio events |
| `MIT/ast-finetuned-audioset-10-10-0.2` | 87M | AudioSet (527 classes) |
| `google/speech-commands` | 60M | Keyword spotting |
| `facebook/musicgen-small` | 1.5B | Music generation |

## Quick Reference by Task

| Task | Best Model | Pipeline Tag | Notes |
|------|-----------|-------------|-------|
| ASR | `openai/whisper-large-v3-turbo` | `automatic-speech-recognition` | 100 langs, faster than v3 |
| Lightweight ASR | `openai/whisper-base` | `automatic-speech-recognition` | Good for CPU |
| Distilled ASR | `distil-whisper/distil-large-v3` | `automatic-speech-recognition` | 2x faster, <1% WER degradation |
| TTS | `suno/bark` | `text-to-speech` | Expressive, supports laughter/music |
| TTS (speaker control) | `parler-tts/parler-tts-large-v1` | `text-to-speech` | Control voice via text prompts |
| TTS (multispeaker) | `microsoft/speecht5_tts` | `text-to-speech` | Speaker embeddings for voice cloning |
| Audio Classification | `facebook/wav2vec2-base` | `audio-classification` | General purpose |
| Music Genre | `facebook/musicgen-small` | `text-to-audio` | Generate music from text |
| Speech Translation | `facebook/seamless-m4t-v2-large` | `automatic-speech-recognition` | Multilingual speech-to-speech |
| Voice Activity Detection | `pyannote/voice-activity-detection` | (custom) | Detect speech segments |

## Procedures

### 1. Complete ASR Pipeline (Whisper)

#### Basic Transcription
```python
from transformers import pipeline
import torch

# Load model (use "openai/whisper-large-v3-turbo" for speed-accuracy balance)
pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-large-v3-turbo",
    device=0 if torch.cuda.is_available() else -1,
)

# Basic transcription
result = pipe("speech.mp3")
print(result["text"])

# With timestamps (for diarization/alignment)
result = pipe("speech.mp3", return_timestamps=True)
for chunk in result["chunks"]:
    print(f"[{chunk['timestamp'][0]:.2f} - {chunk['timestamp'][1]:.2f}] {chunk['text']}")

# Long-form audio (>30s) — chunked automatically
result = pipe("long_meeting.mp3", chunk_length_s=30, return_timestamps=True)

# Multilingual — specify language
result = pipe("french_speech.mp3", generate_kwargs={"language": "fr", "task": "transcribe"})
result = pipe("french_speech.mp3", generate_kwargs={"language": "fr", "task": "translate"})
```

#### Batch Transcription
```python
import glob

files = glob.glob("audio_folder/*.wav")
results = pipe(files, batch_size=8)  # Batch on GPU for throughput
for file, res in zip(files, results):
    print(f"{file}: {res['text'][:80]}...")
```

#### Streaming ASR (real-time)
```python
# Uses the Transformers pipeline with chunk_length_s for streaming
pipe = pipeline(
    "automatic-speech-recognition",
    model="openai/whisper-tiny",  # Use tiny for low latency
    chunk_length_s=5,  # Process every 5 seconds
    device=0 if torch.cuda.is_available() else -1,
)

# Simulate streaming chunks
import soundfile as sf
audio, sr = sf.read("long_speech.wav")
for i in range(0, len(audio), sr * 5):
    chunk = audio[i:i + sr * 5]
    result = pipe({"raw": chunk, "sampling_rate": sr})
    print(f"[{i//sr}s]: {result['text']}")
```

#### Forced Decoding with Language/Task Prompt
```python
# For multilingual ASR, use the generate_kwargs
result = pipe(
    "meeting.mp3",
    generate_kwargs={
        "language": "<|zh|>",  # Force Chinese
        "task": "transcribe",
        "condition_on_previous_text": False,  # Avoid hallucination
    },
    return_timestamps=True,
)
```

### 2. Complete TTS Pipeline (Bark)

```python
from transformers import pipeline
import scipy.io.wavfile as wav
import numpy as np

pipe = pipeline("text-to-speech", model="suno/bark")

# Basic TTS
output = pipe("Hello, welcome to the Hugging Face audio course!")

# output["audio"] is a numpy array, output["sampling_rate"] is the rate
wav.write("output.wav", rate=output["sampling_rate"], data=output["audio"])

# Bark with speaker prompt (voice cloning from audio)
output = pipe(
    "This is the cloned voice speaking.",
    speaker_embeddings="speaker_reference.wav",  # 7-10s reference
)

# Bark with non-speech sounds
output = pipe("[laughter] This is funny [laughs] and now [music] some music.")
```

### 3. TTS Pipeline (Parler-TTS — voice control)

```python
from transformers import pipeline

pipe = pipeline("text-to-speech", model="parler-tts/parler-tts-large-v1")

# Control voice via description
output = pipe(
    "Hello, this is my voice speaking.",
    voice="A male speaker with a deep, soothing voice speaking at a moderate pace."
)

# Different voice descriptions
voices = [
    "A young female speaker with a high-pitched voice speaking quickly.",
    "An elderly male speaker with a raspy voice speaking slowly and deliberately.",
    "A robotic monotone voice speaking at a normal pace.",
]
for voice in voices:
    output = pipe("This is a voice description test.", voice=voice)
    wav.write(f"voice_test.wav", rate=output["sampling_rate"], data=output["audio"])
```

### 4. TTS Pipeline (SpeechT5 — speaker embedding cloning)

```python
from transformers import SpeechT5Processor, SpeechT5ForTextToSpeech, SpeechT5HifiGan
from datasets import load_dataset
import torch
import soundfile as sf

processor = SpeechT5Processor.from_pretrained("microsoft/speecht5_tts")
model = SpeechT5ForTextToSpeech.from_pretrained("microsoft/speecht5_tts")
vocoder = SpeechT5HifiGan.from_pretrained("microsoft/speecht5_hifigan")

# Load speaker embedding from a reference audio
embeddings_dataset = load_dataset("Matthijs/cmu-arctic-xvectors", split="validation")
speaker_embeddings = torch.tensor(embeddings_dataset[7300]["xvector"]).unsqueeze(0)

# Generate speech
inputs = processor(text="Hello, this is a speech synthesis demo.", return_tensors="pt")
speech = model.generate_speech(inputs["input_ids"], speaker_embeddings, vocoder=vocoder)
sf.write("speecht5_output.wav", speech.numpy(), samplerate=16000)
```

### 5. Audio Classification

```python
from transformers import pipeline

# General audio events
pipe = pipeline("audio-classification", model="facebook/wav2vec2-base")
result = pipe("audio_clip.wav")
print(result)  # List of {label, score} dicts

# Speech command recognition
pipe = pipeline("audio-classification", model="google/speech-commands")

# Top-K results
result = pipe("music.wav", top_k=5)
for r in result:
    print(f"{r['label']}: {r['score']:.3f}")
```

### 6. Music Generation (MusicGen)

```python
from transformers import pipeline

pipe = pipeline("text-to-audio", model="facebook/musicgen-small")
output = pipe("Upbeat electronic dance music with synth bass and drums")
# output["audio"] is stereo numpy array, output["sampling_rate"] is 32000

# Melody conditioning
pipe = pipeline("text-to-audio", model="facebook/musicgen-melody")
output = pipe(
    "Jazz piano with walking bass",
    melody="melody_reference.wav",  # Conditioning melody
)
```

### 7. Load & Process Audio

```python
from datasets import load_dataset, Audio

# Load audio dataset with resampling
dataset = load_dataset("superb", "asr", split="train")
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))
sample = dataset[0]["audio"]["array"]  # numpy array
sr = dataset[0]["audio"]["sampling_rate"]

# Raw audio loading with librosa
import librosa
audio, sr = librosa.load("file.wav", sr=16000)

# Feature extraction (mel-spectrogram)
import librosa.display
import numpy as np
mel_spec = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=80, fmax=8000)
log_mel = librosa.power_to_db(mel_spec)

# Noise reduction
import noisereduce as nr
reduced_audio = nr.reduce_noise(y=audio, sr=sr)

# Audio augmentation
import audiomentations as A
augment = A.Compose([
    A.AddBackgroundNoise(sounds_path="noise_files/", min_snr_in_db=10, max_snr_in_db=20, p=0.5),
    A.TimeStretch(min_rate=0.9, max_rate=1.1, p=0.5),
    A.PitchShift(min_semitones=-2, max_semitones=2, p=0.5),
])
augmented = augment(samples=audio, sample_rate=sr)
```

### 8. Fine-tune Whisper on Custom Dataset

#### Full Fine-Tuning (Seq2SeqTrainer)

```python
from transformers import (
    WhisperProcessor, WhisperForConditionalGeneration,
    Seq2SeqTrainingArguments, Seq2SeqTrainer
)
from datasets import load_dataset, Audio

# Load processor and model
processor = WhisperProcessor.from_pretrained("openai/whisper-small")
model = WhisperForConditionalGeneration.from_pretrained("openai/whisper-small")

# Load and prepare dataset
dataset = load_dataset("your-dataset", split="train")
dataset = dataset.cast_column("audio", Audio(sampling_rate=16000))

def prepare_dataset(batch):
    audio = batch["audio"]
    # Log-mel spectrogram input
    batch["input_features"] = processor(
        audio["array"], sampling_rate=audio["sampling_rate"], return_tensors="pt"
    ).input_features[0]
    # Labels (tokenized transcription)
    batch["labels"] = processor(
        text=batch["text"], return_tensors="pt"
    ).input_ids[0]
    return batch

dataset = dataset.map(prepare_dataset, remove_columns=dataset.column_names)

# Training arguments
training_args = Seq2SeqTrainingArguments(
    output_dir="./whisper-finetuned",
    per_device_train_batch_size=8,
    gradient_accumulation_steps=2,
    learning_rate=1e-5,
    warmup_steps=500,
    num_train_epochs=5,
    fp16=True,
    evaluation_strategy="steps",
    predict_with_generate=True,
    generation_max_length=225,
    save_steps=1000,
    eval_steps=1000,
    logging_steps=25,
    report_to=["tensorboard"],
    load_best_model_at_end=True,
    metric_for_best_model="wer",
)

# WER metric
from evaluate import load
wer_metric = load("wer")

def compute_metrics(pred):
    pred_ids = pred.predictions
    label_ids = pred.label_ids
    label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
    pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
    label_str = processor.batch_decode(label_ids, skip_special_tokens=True)
    wer = wer_metric.compute(predictions=pred_str, references=label_str)
    return {"wer": wer}

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    eval_dataset=dataset,
    tokenizer=processor.tokenizer,
    data_collator=processor,
    compute_metrics=compute_metrics,
)
trainer.train()
```

#### Memory-Efficient Fine-Tuning with LoRA (PEFT)

```python
from transformers import WhisperForConditionalGeneration, WhisperProcessor, Seq2SeqTrainingArguments, Seq2SeqTrainer
from datasets import load_dataset, Audio
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
import torch

model_name = "openai/whisper-small"
processor = WhisperProcessor.from_pretrained(model_name)
model = WhisperForConditionalGeneration.from_pretrained(
    model_name, load_in_8bit=True, device_map="auto"
)

# Freeze the base model and add LoRA adapters
model = prepare_model_for_kbit_training(model)
lora_config = LoraConfig(
    r=32,
    lora_alpha=64,
    target_modules=["q_proj", "v_proj", "k_proj", "out_proj", "fc1", "fc2"],
    lora_dropout=0.05,
    bias="none",
)
model = get_peft_model(model, lora_config)

# Enable gradient checkpointing to save memory
model.config.use_cache = False
model.gradient_checkpointing_enable()

# Train with 4x smaller batch size vs full fine-tuning
training_args = Seq2SeqTrainingArguments(
    output_dir="./whisper-lora",
    per_device_train_batch_size=4,  # Smaller batch for LoRA
    gradient_accumulation_steps=4,
    learning_rate=2e-4,
    warmup_steps=100,
    num_train_epochs=10,
    fp16=True,
    logging_steps=25,
    report_to=["tensorboard"],
    save_strategy="epoch",
    predict_with_generate=True,
    generation_max_length=225,
)

trainer = Seq2SeqTrainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    tokenizer=processor.tokenizer,
    data_collator=processor,
    compute_metrics=compute_metrics,
)
trainer.train()

# Save only LoRA weights (~14MB)
model.save_pretrained("./whisper-lora-final")

# Inference with LoRA adapter
from peft import PeftModel
base_model = WhisperForConditionalGeneration.from_pretrained(model_name)
model = PeftModel.from_pretrained(base_model, "./whisper-lora-final")
pipe = pipeline("automatic-speech-recognition", model=model, tokenizer=processor.tokenizer)
```

### 9. Speaker Diarization (pyannote)

```python
from pyannote.audio import Pipeline
from pyannote.core import segment

# Load pre-trained pipeline (requires huggingface-cli login + acceptance of pyannote models)
diarization_pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token=True,
)

# Run diarization
diarization = diarization_pipeline("meeting.wav")

# Print speaker segments
for turn, _, speaker in diarization.itertracks(yield_label=True):
    print(f"[{turn.start:.1f}s - {turn.end:.1f}s] {speaker}")

# Combine with ASR for speaker-attributed transcript
# (Use Whisper chunks aligned with diarization segments)
```

### 10. Gradio Demo (ASR)

```python
import gradio as gr
from transformers import pipeline

pipe = pipeline("automatic-speech-recognition", model="openai/whisper-small")

def transcribe(audio_path):
    result = pipe(audio_path)
    return result["text"]

demo = gr.Interface(
    fn=transcribe,
    inputs=gr.Audio(type="filepath"),
    outputs="text",
    title="Whisper Speech Recognition",
    description="Upload audio to transcribe with Whisper",
)
demo.launch()
```

## Audio Processing Fundamentals

### Key Concepts
- **Sampling Rate**: CD quality = 44100Hz, speech = 16000Hz. Whisper expects 16000Hz.
- **Bit Depth**: 16-bit PCM is standard. 24-bit gives more dynamic range.
- **Spectrogram**: Time-frequency representation. X-axis = time, Y-axis = frequency, color = amplitude.
- **Mel Scale**: Perceptual frequency scale — human hearing is logarithmic. Mel-spectrograms are standard for audio ML.
- **MFCCs**: Mel-Frequency Cepstral Coefficients — compact representation, used in traditional ASR.
- **Log-Mel Spectrogram**: Standard input for modern audio models (Whisper, Wav2Vec2).

### Audio Preprocessing Checklist
1. Resample to target SR (16kHz for speech models)
2. Convert to mono if stereo
3. Normalize amplitude (avoid clipping)
4. Trim silence (optional but recommended)
5. Split long audio into chunks (Whisper handles 30s windows)
6. Apply noise reduction for noisy recordings
7. Normalize volume to -3dB LUFS for consistent levels

## Model Architecture Comparison

| Architecture | Example | Best For |
|-------------|---------|----------|
| **Encoder-only** (CTC) | Wav2Vec2, HuBERT, MMS | Audio classification, lightweight ASR |
| **Encoder-decoder** | Whisper, SpeechT5, SeamlessM4T | High-quality ASR, translation, TTS |
| **Decoder-only** | AudioLM, MusicGen | Music/audio generation |
| **Encoder-only (AST)** | `MIT/ast-finetuned-audioset-10-10-0.2` | Audio classification (transformer-based) |

### Architecture Decision Guide

| Criterion | Encoder-only (CTC) | Encoder-Decoder | Decoder-only |
|-----------|--------------------|----------------|--------------|
| Latency | Low | Medium | High |
| Accuracy | Good | Best | Good |
| Memory | Low | Medium | High |
| Streaming | ✅ Native | ⚠️ Chunked | ❌ Not suitable |
| Languages | Single typically | Multilingual | Single typically |

## Troubleshooting

### Common Errors

| Error | Likely Cause | Solution |
|-------|-------------|----------|
| `CUDA out of memory` | Model too large | Use smaller variant, enable CPU offload, or use LoRA |
| `KeyError: 'input_features'` | Wrong processor | Ensure WhisperProcessor is used, not AutoProcessor |
| `Blank transcriptions` | Sample rate mismatch | Verify audio is 16kHz mono |
| `Hallucinated text` | Long silence/background | Set `condition_on_previous_text=False` |
| `ValueError: Audio longer than 30s` | Chunking not set | Add `chunk_length_s=30` |
| `Bark too slow` | Running on CPU | Use SpeechT5 or Parler-TTS on CPU |
| `ModuleNotFoundError: soundfile` | Missing backend | `pip install soundfile` or `pip install librosa` |

### Performance Tuning

| Goal | Strategy |
|------|----------|
| Max accuracy | Use `whisper-large-v3`, fp16, return_timestamps=False |
| Max speed | Use `whisper-tiny` or `distil-whisper`, batch_size=16 |
| Low memory | Use `whisper-base`, enable_attention_slicing |
| Low latency (streaming) | Use `whisper-tiny`, chunk_length_s=5, device='cuda' |
| Multi-speaker | Combine Whisper + pyannote diarization |

## Pitfalls

- **Sample rate mismatch**: Whisper expects 16kHz mono. Always resample — wrong SR = garbage output.
- **Channel mismatch**: Stereo audio breaks many models. Convert to mono.
- **Long audio**: Models have max input lengths. Use `chunk_length_s` for ASR or chunk the audio manually.
- **Bark on CPU**: Extremely slow. Use smaller models (SpeechT5) or GPU.
- **Overlapping speech**: Whisper handles one speaker at a time. Use speaker diarization (pyannote) for multi-speaker.
- **Background noise**: Preprocess with noise reduction for best ASR quality.
- **Memory for fine-tuning**: Use LoRA (PEFT) or train small variant (whisper-small, tiny) on limited GPU.
- **MusicGen quality**: small=1.5B, medium=3.3B, large=5B. Larger = better quality but higher VRAM.
- **Evaluation metric**: WER (word error rate) for ASR, CER (character error rate) for noisy/ multilingual, accuracy for classification.
- **Pyannote auth**: Requires accepting model licenses on HF Hub and `use_auth_token=True`.

## Verification

```python
from transformers import pipeline

# Test ASR with a known sample
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny")
result = pipe("https://huggingface.co/datasets/Narsil/asr_dummy/resolve/main/1.flac")
print(result["text"])  # Should transcribe the spoken text

# Test TTS
pipe = pipeline("text-to-speech", model="suno/bark-small")
output = pipe("Testing TTS.")
assert "audio" in output
assert "sampling_rate" in output

# Test classification
pipe = pipeline("audio-classification", model="facebook/wav2vec2-base")
```

## Additional Resources

- [HF Audio Course](https://huggingface.co/learn/audio-course) — full interactive curriculum
- [OpenAI Whisper](https://huggingface.co/openai/whisper-large-v3-turbo) — best general ASR model
- [Distil-Whisper](https://huggingface.co/distil-whisper) — distilled, faster versions
- [Parler-TTS](https://huggingface.co/parler-tts) — controllable TTS via text prompts
- [SeamlessM4T](https://huggingface.co/facebook/seamless-m4t-v2-large) — multilingual speech translation
- [OpenASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) — compare ASR models
- [pyannote-audio](https://huggingface.co/pyannote/speaker-diarization-3.1) — speaker diarization
- [SpeechBrain](https://huggingface.co/speechbrain) — alternative audio toolkit
- [OpenAI Whisper Blog](https://openai.com/research/whisper) — original paper
