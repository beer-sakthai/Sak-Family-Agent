# Calling Gradio Spaces as APIs — condensed reference

## Semantic search for Spaces

Find candidate Spaces via natural language:

```bash
curl -s "https://huggingface.co/api/spaces/semantic-search?q=text+to+speech&sdk=gradio"
```

`&sdk=gradio` filters to Spaces that expose an API.

## Retry pattern for client calls

```python
import time
from gradio_client import Client

def predict_with_retry(client, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.predict(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise

client = Client("username/space", token="hf_...")
result = predict_with_retry(client, "input", api_name="/predict")
```

## FastAPI wrapper around a Space

```python
from fastapi import FastAPI
from gradio_client import Client, handle_file

app = FastAPI()
client = Client("username/whisper-space", token="hf_...")

@app.post("/transcribe/")
async def transcribe(file_url: str):
    result = client.predict(audio=handle_file(file_url), api_name="/predict")
    return {"transcription": result}
```

## Key pitfalls

- Do **not** assume synchronous execution. The queue-based API is async by default. Use `job.result()` or iterate the SSE stream.
- Unauthenticated rate limits are strict. Always pass `token=...` for production usage.
- HTTP auth header is required for private Spaces and gives better queue position even on public Spaces.
- File inputs need `handle_file()` in the Python client; pass raw paths/URLs directly via curl/REST.
- CORS is enforced by the browser when calling from client-side JS; for server-side workflows use Python/node backends.
- gRPC or WebSocket fallbacks are not available; use HTTP + SSE only.
