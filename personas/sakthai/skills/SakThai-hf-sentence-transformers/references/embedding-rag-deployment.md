# Embedding Model Deployment + RAG Server (2026-07-24 session)

Deployed a sentence-transformers embedding model to HF Hub and built a lightweight RAG search server for the SakThai family.

## Pipeline

```bash
# 1. Download sentence-transformers model
pip install sentence-transformers
python3 -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')  # 80 MB, 384-dim
model.save('./model-dir')
"

# 2. Upload to HF
from huggingface_hub import HfApi, create_repo
api = HfApi()
create_repo('Nanthasit/sakthai-embedding', repo_type='model', exist_ok=True)
api.upload_folder(folder_path='./model-dir', repo_id='Nanthasit/sakthai-embedding', repo_type='model')

# 3. Create RAG index (SOULs + key docs)
from sentence_transformers import SentenceTransformer
import numpy as np, json

model = SentenceTransformer('Nanthasit/sakthai-embedding')  # or upstream
chunks = [{"text": para[:500], "source": src, "agent": agent}]
embeddings = model.encode([c["text"] for c in chunks])
with open('rag_index.json', 'w') as f:
    json.dump({"chunks": chunks, "embeddings": embeddings.tolist()}, f)
```

## RAG Server

A lightweight HTTP server that:
- Loads pre-built index from `rag_index.json`
- Accepts queries via `GET /search?q=...` or `POST /search`
- Returns cosine-similarity ranked results with source + agent metadata
- Runs on port 3003

RAM usage: ~120 MB server + ~80 MB model (loaded on first request).
Server script: `~/profiles/sakthai/rag-server.py`

## Tokenizer pitfalls

Uploading a model with `model.save()` alone omits critical tokenizer config files. After upload, you may see `IndexError: index out of range in self` during embedding. Fix: upload the missing config files from the ORIGINAL model repo:

```python
from huggingface_hub import snapshot_download, HfApi
orig = snapshot_download('sentence-transformers/all-MiniLM-L6-v2')
api = HfApi()
for fname in os.listdir(orig):
    if fname not in ['model.safetensors', 'pytorch_model.bin']:
        api.upload_file(path_or_fileobj=os.path.join(orig, fname),
                       path_in_repo=fname,
                       repo_id='Nanthasit/sakthai-embedding',
                       repo_type='model')
```

## Models deployed this session

| Repo | Type | Dim | Size |
|------|------|:---:|:----:|
| `Nanthasit/sakthai-embedding` | English only | 384 | 80 MB |
| `Nanthasit/sakthai-embedding-multilingual` | 50+ languages | 384 | 80 MB |
