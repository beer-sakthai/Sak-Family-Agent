---
name: SakThai-hf-inference-client-audio-tts-asr
description: "HF InferenceClient Audio, TTS & ASR — complete reference for text-to-speech, automatic speech recognition, audio classification, and audio-to-audio inference through the Hugging Face InferenceClient (sync and async)."
---

# HF InferenceClient — Audio, TTS & ASR

Complete reference for the Hugging Face InferenceClient's audio inference capabilities: text-to-speech synthesis, automatic speech recognition, audio classification, and audio-to-audio processing.

## Core Methods

| Method | Returns | Task |
|--------|---------|------|
| `text_to_speech(text, *, model, ...)` | `bytes` | Synthesize speech from text |
| `automatic_speech_recognition(audio, *, model, ...)` | `AutomaticSpeechRecognitionOutput` | Transcribe speech to text |
| `audio_classification(audio, *, model, ...)` | `list[AudioClassificationOutputElement]` | Classify audio by label |
| `audio_to_audio(audio, *, model)` | `list[AudioToAudioOutputElement]` | Speech enhancement, source separation |

## Key Insights

- TTS returns raw WAV bytes — save to file or stream to browser
- ASR returns `AutomaticSpeechRecognitionOutput` with `.text` and optionally `.chunks` (timestamps)
- Audio input: bytes, file path, URL string, file-like object, bytearray, or memoryview
- All audio methods go through provider helpers for routing and adaptation
- Async versions available on `AsyncInferenceClient`
- Zero-cost: free serverless inference for supported models
