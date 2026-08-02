# RAG Agent Knowledge System

Build a semantic search system over agent SOULs + skills using sentence-transformers.

## Architecture

```
SOUL.md files ──→ embed ──→ numpy array ──→ JSON index
skills/*.md   ──→         (384-dim)        (rag_index.json)
                                    ↕
                              HTTP API (port 3003)
                                    ↕
                           /search?q=your question
```

## Implementation

### 1. Build Index

```python
from sentence_transformers import SentenceTransformer
import glob, json, numpy as np

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

chunks = []
for path in glob.glob('/path/to/**/SKILL.md', recursive=True):
    with open(path) as f:
        for para in f.read().split('\n\n'):
            para = para.strip()
            if len(para) > 60:
                src = path.split('/profiles/')[1]
                agent = src.split('/')[0]
                chunks.append({'text': para[:500], 'source': src, 'agent': agent})

embeddings = model.encode([c['text'] for c in chunks])

with open('rag_index.json', 'w') as f:
    json.dump({'chunks': chunks, 'embeddings': embeddings.tolist()}, f)
```

### 2. Serve HTTP API

```python
from http.server import HTTPServer, BaseHTTPRequestHandler

class RAGHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/search?q='):
            q = self.path.split('?q=')[1][:200]
            q_emb = model.encode([q])[0]
            scores = embeddings @ q_emb / (norm * np.linalg.norm(q_emb))
            top = np.argsort(scores)[-5:][::-1]
            results = [...]
            self.send_json(results)
```

### 3. Memory Management

- **OOM risk**: Embedding all skills (>600) at once uses ~1GB RAM. Batch in groups of 50.
- **Pre-built index**: Store as JSON, load at startup — much faster than rebuilding.
- **Model caching**: sentence-transformers model is cached on first load (~80MB RAM).

## Pitfalls

- **Tokenization errors with HF-uploaded models**: `IndexError: index out of range in self` means the tokenizer config files are missing. Fix: use the original model ID, not a minimal upload.
- **RAM limit**: Full index of 464 chunks + model = ~1.1GB RAM. Reduce scope (SOULs only = 64 chunks = ~500MB).
- **Cold start**: First request to the server loads the model (~8s). Subsequent requests are instant.
- **Scores threshold**: Filter results with `scores[i] > 0.3` to avoid noise.
- **CORS**: Add `Access-Control-Allow-Origin: *` header for dashboard embedding.
