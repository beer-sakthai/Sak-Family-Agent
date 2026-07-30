# API-Backed Spaces — Detection Guide

Many popular HF Spaces don't run the model locally — they wrap a cloud API (Dashscope, Replicate, Together, fal.ai, etc.) behind a Gradio UI. This affects analysis (can't inspect model code) and hardware reports (Space shows `cpu-basic` but inference happens elsewhere).

## How to detect

1. **Check hardware** — `runtime.hardware.current` via API. If `cpu-basic` but the Space does inference-heavy work (video gen, image gen), it's almost certainly API-backed.

2. **Read `app.py`** — look for these signs:
   - `import dashscope` → Alibaba Cloud's Dashscope API
   - `import replicate` → Replicate API
   - `import openai` → OpenAI or compatible API
   - `import boto3`, `import oss2` — cloud storage for file uploads before API call
   - `requests.post("https://api.xxx")` — direct API calls
   - `os.getenv("DASHSCOPE_API_KEY")` or similar env var for API key

3. **Read `requirements.txt`** — if it's tiny (2-3 lines) and includes API SDKs instead of ML libraries (torch, transformers, diffusers), it's API-backed.

4. **Check the `models` field** in the API response — if it references the same org's model name (e.g., `Wan-AI/Wan2.2-Animate-14B`), the Space is a UI wrapper, not a model runner.

## Why this matters for deep dives

- API-backed Spaces can't be forked and modified to run with different models — the backend is controlled by the provider.
- They may stop working if the API changes or the provider decommissions the endpoint.
- Hardware info from the API is misleading: `cpu-basic` doesn't mean inference is CPU-only.
- The Space's uptime depends on the API's availability, not just HF infrastructure.

## Examples

| Space | SDK | Hardware | Backend | Signals |
|-------|-----|----------|---------|---------|
| Wan-AI/Wan2.2-Animate | Gradio | cpu-basic | Dashscope | `dashscope` import, `oss2` for uploads, tiny requirements.txt |
| jbilcke-hf/ai-comic-factory | Gradio | cpu-basic | Replicate/API | External API calls in app.py |

## Pitfall

Don't assume a Space with `cpu-basic` hardware is a lightweight demo. Many heavy video/image generation Spaces use `cpu-basic` because the actual compute happens on the provider's side. Always check `app.py` for API calls before concluding the hardware spec is insufficient.
