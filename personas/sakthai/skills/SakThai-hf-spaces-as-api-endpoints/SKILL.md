---
name: SakThai-hf-spaces-as-api-endpoints
author: SakThai
license: MIT
description: Complete reference for using Hugging Face Spaces as REST API endpoints — the Gradio client library (Python/JS), REST API via curl, ZeroGPU quotas, error handling, streaming, file handling, and integration patterns
category: mlops
version: 1.0.0
---

# HF Spaces as API Endpoints

Trigger when: user asks about calling Spaces programmatically, using Spaces as APIs, the Gradio client, calling Spaces from curl, or integrating Spaces into applications.

## Overview

Every Gradio Space on Hugging Face automatically exposes a REST API. This means any Space you can use in a browser can also be called programmatically via Python, JavaScript, or plain HTTP (curl).

The API system provides:
- **Auto-generated OpenAPI spec** at `https://{space-subdomain}.hf.space/gradio_api/openapi.json`
- **Queue-based two-step API** for reliable async execution
- **Server-Sent Events (SSE)** for streaming results
- **File upload/download** via `handle_file()`
- **Token authentication** for private Spaces and higher rate limits

## Quick Start

```bash
pip install --upgrade gradio_client
```

```python
from gradio_client import Client

client = Client("abidlabs/en2fr", token="hf_...")
result = client.predict("Hello, world!", api_name="/predict")
print(result)  # "Bonjour, le monde!"
```

## Python Client

### Installation

```bash
pip install --upgrade gradio_client
```

Requires Python 3.10+.

### Connect to a Space

```python
from gradio_client import Client

# Public Space (no token needed for public Spaces)
client = Client("username/space-name")

# Private Space (token required)
client = Client("username/private-space", token="hf_xxxxx")

# With custom headers (e.g., forwarding auth for ZeroGPU)
client = Client("owner/zerogpu-space", headers={"x-ip-token": "..."})
```

Get tokens at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens). For private Spaces, you need at minimum a token with **read** permissions.

### Discover Available Endpoints

```python
client.view_api()  # Prints all endpoints with parameters
```

Alternatively, visit the Space's page and click the "Use via API" link in the footer to see all endpoints, parameter types, and auto-generated code snippets.

You can also fetch the OpenAPI spec:

```bash
curl https://abidlabs-en2fr.hf.space/gradio_api/openapi.json
```

### Make Predictions

**Synchronous (blocking):**

```python
result = client.predict("Hello", api_name="/predict")
```

**Asynchronous (non-blocking):**

```python
job = client.submit("Hello", api_name="/predict")
# Do other work...
result = job.result()  # Blocks until ready
```

### Handle Files

```python
from gradio_client import Client, handle_file

client = Client("abidlabs/whisper", token="hf_...")

# From local file
result = client.predict(audio=handle_file("audio.wav"), api_name="/predict")

# From URL
result = client.predict(
    audio=handle_file("https://example.com/audio.wav"),
    api_name="/predict"
)
```

### Monitor Job Status

```python
job = client.submit("Hello", api_name="/predict")

# Check status
status = job.status()
print(f"Queue position: {status.rank}, ETA: {status.eta}")

# Check if complete
if job.done():
    result = job.result()

# Cancel a pending job
job.cancel()
```

### Streaming / Generator Endpoints

```python
job = client.submit(prompt="Write a story", api_name="/generate")

# Iterate over streaming outputs
for output in job:
    print(output)
```

## JavaScript Client

### Installation

```bash
npm i @gradio/client
```

Or via CDN:

```html
<script type="module">
  import { Client } from "https://cdn.jsdelivr.net/npm/@gradio/client/dist/index.min.js";
</script>
```

### Connect and Predict

```javascript
import { Client } from "@gradio/client";

const app = await Client.connect("abidlabs/en2fr", { token: "hf_..." });
const result = await app.predict("/predict", ["Hello"]);
console.log(result.data);
```

### Handle Files

```javascript
import { Client, handle_file } from "@gradio/client";

const app = await Client.connect("abidlabs/whisper", { token: "hf_..." });
const result = await app.predict("/predict", [
  handle_file("https://example.com/audio.wav")
]);
```

### Stream Results

```javascript
const job = app.submit("/predict", ["Hello"]);

for await (const message of job) {
  if (message.type === "data") {
    console.log("Result:", message.data);
  }
  if (message.type === "status") {
    console.log("Queue position:", message.position);
  }
}
```

## REST API via curl

### Queue-Based API (Recommended)

Most Spaces use a two-step process:

**Step 1: Submit the request**

```bash
curl -X POST "https://abidlabs-en2fr.hf.space/gradio_api/call/predict" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer hf_..." \
  -d '{"data": ["Hello, world"]}'
```

Response:

```json
{"event_id": "abc123"}
```

**Step 2: Get the result**

```bash
curl -N "https://abidlabs-en2fr.hf.space/gradio_api/call/predict/abc123" \
  -H "Authorization: Bearer hf_..."
```

Response (Server-Sent Events):

```
event: complete
data: ["Bonjour, le monde!"]
```

### Queue API Endpoint Format

```
POST   https://{space-subdomain}.hf.space/gradio_api/call/{api_name}
GET    https://{space-subdomain}.hf.space/gradio_api/call/{api_name}/{event_id}
```

The `-N` flag on curl disables buffering for SSE streaming. The `Authorization` header improves rate limits even on public Spaces.

## ZeroGPU Spaces

ZeroGPU Spaces have daily GPU usage quotas:

| Account Type   | Included Daily GPU Quota |
|----------------|--------------------------|
| Unauthenticated | 2 minutes                |
| Free account    | 5 minutes                |
| PRO account     | 40 minutes               |
| Team/Enterprise | Extended (pre-paid credits available) |

**Key details:**
- Authenticated requests consume the account's GPU quota
- Unauthenticated requests use a shared pool with stricter limits
- PRO+ users can purchase credits at $1/10 min of GPU time
- Forwarding authentication is critical when calling ZeroGPU Spaces from another Space

### Calling ZeroGPU Spaces from Another Space

```python
import gradio as gr
from gradio_client import Client

def process(prompt, request: gr.Request):
    x_ip_token = request.headers.get('x-ip-token', '')
    client = Client("owner/zerogpu-space", headers={"x-ip-token": x_ip_token})
    return client.predict(prompt, api_name="/predict")

demo = gr.Interface(fn=process, inputs="text", outputs="text")
demo.launch()
```

## Integration Patterns

### FastAPI Integration

```python
from fastapi import FastAPI
from gradio_client import Client, handle_file

app = FastAPI()
client = Client("abidlabs/whisper", token="hf_...")

@app.post("/transcribe/")
async def transcribe(file_url: str):
    result = client.predict(audio=handle_file(file_url), api_name="/predict")
    return {"transcription": result}
```

### Error Handling with Retries

```python
import time
from gradio_client import Client

def predict_with_retry(client, *args, max_retries=3, **kwargs):
    for attempt in range(max_retries):
        try:
            return client.predict(*args, **kwargs)
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
            else:
                raise

client = Client("username/space", token="hf_...")
result = predict_with_retry(client, "input", api_name="/predict")
```

### Semantic Search for Spaces

Find Spaces for a particular task:

```bash
curl -s "https://huggingface.co/api/spaces/semantic-search?q=text+to+speech&sdk=gradio"
```

Returns Spaces ranked by semantic relevance with metadata (ID, likes, description). Use `sdk=gradio` to filter for Spaces with APIs.

## Pitfalls

- **Space must be running** — you cannot call a Space that is sleeping or paused. Use `hf spaces wake` or the Space runtime API to ensure it's active first.
- **Authentication for private Spaces** — always pass a token with READ permissions. Without a token, private Spaces return HTTP 403.
- **ZeroGPU quota exhaustion** — once the daily quota is consumed, calls fail with a GPU quota error. Monitor usage and implement fallbacks.
- **OpenAPI spec location** — the spec is at `/gradio_api/openapi.json` (not `/openapi.json`). Some Spaces use different subdomain patterns.
- **File size limits** — Gradio Spaces have file size limits. Very large files may need chunked upload or pre-processing.
- **Rate limits** — unauthenticated requests have stricter rate limits. Always authenticate with a token for production use.
- **Space may change** — a Space owner can change its API at any time. Always pin to a specific Space version or handle API changes gracefully.
- **CORS** — browser-based calls from external domains may face CORS restrictions. Use a backend proxy or the Python client.
- **Streaming endpoints** — not all Spaces support streaming. Check the API spec for SSE support before implementing streaming clients.
