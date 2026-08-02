# Embedding Model Deployment — HF Upload + Local RAG Server

How to upload a sentence-transformers model to Hugging Face Hub and set up a local RAG server for semantic search across agent knowledge.

## Pipeline

```
1. Download model  →  2. Upload to HF  →  3. Index docs  →  4. RAG server
     (80 MB)           (5 min)            (64 chunks)        (port 3003)
```

## Step 1: Download + Upload Embedding Model

```python
from sentence_transformers import SentenceTransformer
from huggingface_hub import HfApi, create_repo
import tempfile

# Download
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Save to temp dir
tmpdir = tempfile.mkdtemp()
model.save(tmpdir)

# Upload to HF
api = HfApi()
create_repo("Nanthasit/sakthai-embedding", repo_type="model", exist_ok=True)
api.upload_folder(
    folder_path=tmpdir,
    repo_id="Nanthasit/sakthai-embedding",
    repo_type="model",
    commit_message="Upload embedding model"
)
```

**Important:** The sentence-transformers model must be uploaded as `Nanthasit/sakthai-embedding` with proper pipeline tag: `sentence-similarity`. Users should reference `Nanthasit/sakthai-embedding` (NOT the upstream `sentence-transformers/all-MiniLM-L6-v2`) so the family has a stable canonical source.

**Model card** must include:
- `pipeline_tag: sentence-similarity`
- `library_name: sentence-transformers`
- Usage example with `Nanthasit/sakthai-embedding`
- Specs: 384-dim, 256 max tokens, 80 MB
- Model type: MiniLM-L6-v2

## Step 2: Build Index

```python
import json, numpy as np
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Nanthasit/sakthai-embedding")

chunks = []
for path in ["SOUL.md", "other/docs"]:
    with open(path) as f:
        for para in f.read().split("\n\n"):
            para = para.strip()
            if len(para) > 60:
                chunks.append({"text": para[:500], "source": path})

embeddings = model.encode([c["text"] for c in chunks])

with open("rag_index.json", "w") as f:
    json.dump({"chunks": chunks, "embeddings": embeddings.tolist()}, f)
```

**Memory note:** On machines with <4 GB free RAM (~2.4 GB as seen in this environment), index building with >64 chunks may hit OOM. Keep the index small (SOULs only, ~64 chunks) and embed the model only once. Use pre-built index, not live embedding during query.

## Step 3: Query Server

Minimal `rag-server.py`:

```python
import json, sys, numpy as np
from http.server import HTTPServer, BaseHTTPRequestHandler
from sentence_transformers import SentenceTransformer

with open("rag_index.json") as f:
    data = json.load(f)
chunks = data["chunks"]
embeddings = np.array(data["embeddings"])

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/search?q="):
            q = self.path.split("?q=")[1][:200]
            model = SentenceTransformer("Nanthasit/sakthai-embedding")
            q_emb = model.encode([q])[0]
            scores = embeddings @ q_emb / (
                np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_emb) + 1e-8
            )
            top = np.argsort(scores)[-5:][::-1]
            results = [{"score": round(float(scores[i]), 3), "text": chunks[i]["text"][:300]}
                       for i in top if scores[i] > 0.3]
            self.send_json({"results": results})
    
    def send_json(self, d):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(d).encode())

HTTPServer(("0.0.0.0", int(sys.argv[1]) if len(sys.argv) > 1 else 3003), Handler).serve_forever()
```

## Usage

```bash
# Start server
python3 rag-server.py 3003

# Query
curl "http://localhost:3003/search?q=Hugging+Face+models"

# Response
{"results": [{"score": 0.55, "text": "...", "source": "sakthai/SOUL.md"}]}
```

## Pitfalls

- **The uploaded model tokenizer may produce "Missing [UNK] token" error** — Use the original upstream model (`sentence-transformers/all-MiniLM-L6-v2`) for encoding, not the uploaded one. Or verify tokenizer_config.json is complete before uploading.
- **First request to the server is slow (~5s)** — Subsequent requests are faster (~0.1s) because the model stays loaded in memory.
- **OOM with large indexes** — On memory-constrained machines (<4 GB), limit index to ~64 chunks from SOUL files only. Don't index all 500+ skills.
- **Process keeps dying on second+ request** — If the server crashes after the first query under low memory, reduce `np.linalg.norm` computations or switch to a simpler similarity method.

## Related

- `model-publishing-pipeline` skill — full pipeline for publishing models to HF
- `huggingface-hub` skill — HF CLI and Python API reference
