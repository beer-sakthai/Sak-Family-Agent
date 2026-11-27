---
name: SakThai-hf-audio-course
version: 1.0.0
description: Process audio with transformers — ASR, TTS, classification, music gen,
  audio processing, fine-tuning.
category: mlops
tags:
- audio
- course
- hf
- huggingface
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

---

## Deep Dive Reference

For exhaustive reference specifications, cookbook snippets, and extended documentation, see [HF Audio Course Task Procedures & Cookbooks](./references/audio-course-task-procedures.md).
