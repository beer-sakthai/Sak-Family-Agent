# FastAPI Voice Proxy Gateway — Case Study

**Space:** `smolagents/hf-realtime-voice` (454 likes)
**Detected:** 2026-07-23
**Architecture:** FastAPI Docker proxy-gateway + WebSocket real-time audio
**Models used:** `google/gemma-4-31B-it` (LLM), `nvidia/parakeet-tdt-1.1b` (ASR), `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` (TTS)

## Why this Space matters

This Space is a **Docker Space that doesn't load any model weights** — it's a pure proxy/gateway that sits between the browser and a remote speech-to-speech backend. All heavy inference happens on Hugging Face's managed compute backend; the Space itself runs on `cpu-basic`. This is an increasingly common architecture pattern for production-grade Spaces that need secrets management and usage metering.

## Detection signals

When investigating an unfamiliar Docker Space, use these signals to determine if it's a proxy-gateway:

### From HF API (`/api/spaces/{id}`)
- `sdk: docker`
- `runtime.hardware.current: cpu-basic` — even though the Space orchestrates LLM/VLM/ASR/TTS inference
- `models` array present but references large foundation models → inference happens remotely
- `cardData.hf_oauth: true` — the Space needs user identity for metering/permissions

### From Dockerfile
- `FROM python:3.x-slim` — lightweight image, no CUDA/cuDNN
- `CMD ["uvicorn", "server:app", ...]` — FastAPI entrypoint
- No model weight downloads in the build stage

### From `server.py`
- Imports `FastAPI`, `httpx`, `StaticFiles`
- Defines API routes that proxy to remote backends: `/api/session`, `/api/search`, `/api/config`
- Exposes `GET /api/config` returning environment state (search key presence, LB URL mode, auth config)
- Exposes `POST /api/search` as a server-side proxy (hides API key from browser)
- Exposes `POST /api/session` that proxies load balancer handshake (hides LB URL from browser)

### From `requirements.txt`
- `fastapi`, `uvicorn[standard]`, `httpx` — network proxy stack
- `huggingface_hub[oauth]` — HF login integration
- No ML inference libraries (`torch`, `transformers`, `diffusers`)

## Architecture diagram (text)

```
Browser (SPA)
  ├── getUserMedia() → mic capture (AudioWorklet: 48k→16k PCM)
  ├── WebSocket → wss://<compute>/v1/realtime (direct to backend)
  │     ├── input_audio_buffer.append (PCM16 16kHz base64)
  │     ├── session.update (OpenAI Realtime GA schema)
  │     └── response.output_audio.delta (PCM16 24kHz base64)
  ├── GET /api/config → FastAPI → env state
  ├── POST /api/search → FastAPI → Serper.dev (hidden key)
  ├── POST /api/session → FastAPI → Load Balancer (hidden URL)
  └── HF OAuth → hugginface_hub[oauth]
```

## Key patterns to reuse

1. **Secret sandwich:** The browser sees only same-origin endpoints. The FastAPI server holds the secrets (Serper API key, LB URL) and proxies requests server-side. The browser never knows the actual backend URLs or API keys.

2. **Metering middleware:** Usage limits by HF login tier, backed by SQLite, activated only when both `LOAD_BALANCER_URL` and `SPACE_ID` are set. This means local development runs unmetered automatically.

3. **Dual front-end delivery:** The same FastAPI server serves static files AND handles API routes — single container, no reverse proxy needed. The `StaticFiles` mount catches everything that isn't an `/api/*` route.

4. **WebSocket audio pipeline:** Raw PCM16 over WebSocket instead of WebRTC. Simpler debugging (DevTools network tab), works on all networks (no UDP/STUN), but needs careful audio resampling (48k→16k mic, 24k→48k playback) in AudioWorklet.

5. **Tiered tool system:** Tools (web search, camera) are declared to the backend via the OpenAI Realtime protocol. The browser toggles them on/off in localStorage and appends tool declarations to the `session.update` message. The server-side search proxy only activates if `SERPER_API_KEY` is set.

## Pitfalls

- **Docker Space with `sdk: docker` may NOT load models locally.** Check `Dockerfile` for `FROM python:3.x-slim` and `CMD uvicorn` — this signals a proxy, not a model server. Don't expect GPU hardware.
- **`models` field in API response ≠ model is loaded into this Space.** For Docker Spaces, the `models` array lists the models the backend uses, not the Space itself. The Space just orchestrates API calls to them.
- **Raw file access may 401 even for public repos.** Use `/resolve/main/` fallback or the Gradio config endpoint (if applicable). For Docker Spaces with no Gradio, the README at `/raw/main/` is the primary source — try `/resolve/main/README.md` if `/raw/main/` 401s.
