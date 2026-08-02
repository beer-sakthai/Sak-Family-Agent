# Model Server for Sibling Agents

When other Sak family agents (SakSee, SakSit) need access to local GGUF models, run a lightweight Python HTTP server that wraps llama.cpp inference.

## Architecture

```
SakSee / SakSit → HTTP POST /chat → Python server → llama-cli → GGUF model → JSON response
```

## Quick Setup

```python
#!/usr/bin/env python3
import subprocess, json, os
from time import time
from http.server import HTTPServer, BaseHTTPRequestHandler

MODEL_05 = "/opt/data/models/sakthai-0.5b/sakthai-0.5b-Q4_K_M.gguf"
MODEL_15 = "/opt/data/models/sakthai-1.5b/gguf/sakthai-1.5b-Q4_K_M.gguf"
LLAMA = "/opt/data/llama-bin/build/bin/llama-cli"
LIB = "/opt/data/llama-bin/build/bin"

def query(model_path, prompt, max_tokens=128):
    full = f"<|im_start|>user\n{prompt}<|im_end|>\n<|im_start|>assistant\n"
    env = {"LD_LIBRARY_PATH": LIB}
    cmd = [LLAMA, "-m", model_path, "-no-cnv", "-p", full,
           "-n", str(max_tokens), "-t", "2", "--temp", "0.3",
           "--no-display-prompt"]
    start = time()
    out = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=30)
    return {"response": out.stdout.strip(), "time": f"{time()-start:.2f}s"}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/status":
            models = {"0.5B": "ready", "1.5B": "ready"}
            self.send_json({"status": "ok", "models": models})
    def do_POST(self):
        if self.path == "/chat":
            body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            model = body.get("model", "0.5B")
            path = MODEL_05 if model == "0.5B" else MODEL_15
            self.send_json(query(path, body.get("prompt", "")))
    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

HTTPServer(("0.0.0.0", 3002), Handler).serve_forever()
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/status` | Returns model readiness |
| GET | `/` | Serves dashboard HTML (if available) |
| POST | `/chat` | Run inference on specified model |

### POST /chat

**Request body:**
```json
{"model": "0.5B", "prompt": "What is the weather in Paris?"}
```

**Response:**
```json
{"response": "...model output...", "time": "1.12s"}
```

## Starting the Server

```bash
cd ~/profiles/saksee && uv run python3 saksee-models.py 3002 &
# Background: use terminal(background=true)
```

## From SakSee's Skills

```python
import requests
r = requests.post("http://localhost:3002/chat", json={
    "model": "0.5B",  # or "1.5B"
    "prompt": "Summarize this text..."
})
result = r.json()["response"]
```

## Pitfalls

- **Port 3002** is the standard port; conflict? Use a different port and update the URL.
- **Model paths are hardcoded** — update if models move.
- **Timeout**: Default 30s. Long-prompts may need higher `max_tokens` or longer timeout.
- **No auth**: Internal-only. Do not expose to the internet.
- **The server is stateless**: Each request starts a fresh llama-cli process (~1s overhead for 0.5B, ~3s for 1.5B).
