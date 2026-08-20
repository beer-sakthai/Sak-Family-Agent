# Config.json Raw URL 404 Despite File Existing in Siblings/Tree

**Observed:** 2026-07-30 on `Nanthasit/sakthai-embedding-multilingual`
**Updated:** 2026-07-30 — added `-sL` redirect-follow note for `/resolve/main/`
**Expanded:** 2026-07-30 — `/resolve/main/config.json` also returned empty (0 bytes) on text-generation model `Nanthasit/sakthai-context-7b-merged` even with `-sL`; fell back to `hf_hub_download()`.
**Refined:** 2026-07-30 — **`/raw/main/` with Authorization header works** (cheapest option, one request, no redirect). Added as Option A.

## Symptom

```
$ curl -s "https://huggingface.co/Nanthasit/sakthai-embedding-multilingual/raw/main/config.json"
{"error":"Sorry, we can't find the page you are looking for."}
```

Yet the same file was confirmed present in:
- **Sibling list** (`?expand[]=siblings`): 747 bytes, no LFS field
- **Tree API** (`/api/models/{id}/tree/main`): 747 bytes, type=file

## Root Cause (Speculative)

The `/raw/main/` endpoint routes through HF CDN and may not serve files that were uploaded via certain tools (sentence-transformers CLI, HF transfer agent, etc.) or that are pending cache propagation. This is **not** an LFS/Xet issue — the file is a regular Git-tracked file (no LFS pointer), yet raw still 404s.

## Workaround

**Option A — Raw URL with Auth Header** (cheapest — one request, no redirect):

```bash
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/sakthai-embedding-multilingual/raw/main/config.json"
```

**Key finding (2026-07-30):** Adding the Authorization header to `/raw/main/` requests makes them succeed where unauthenticated raw requests return 404. This is an access-control behaviour — unauthenticated `/raw/main/` for certain file types is denied. With `-H "Authorization: Bearer $HF_TOKEN"`, the raw endpoint serves content directly (no redirect chain), making this the cheapest option: one request, no `-L` needed, the response body IS the file content.

Confirmed on `Nanthasit/sakthai-embedding-multilingual` (sentence-transformers model): `raw/main/config.json` with auth returned 747 bytes of actual JSON; without auth returned 404.

**Option B — Resolve URL** (works without auth, needs redirect follow):

```
curl -sL "https://huggingface.co/Nanthasit/sakthai-embedding-multilingual/resolve/main/config.json"
```

**⚠ `-sL` is critical.** Bare `curl -s` (without `-L`) returns the 302 redirect page (~258 B), not the actual config file. Use `curl -sL` to follow the redirect to the storage backend. Without `-L`, your health-check will silently load a redirect page as if it were the config JSON, causing JSON decode errors.

The `/resolve/main/` endpoint follows the same redirect chain as model downloads and typically serves content when `/raw/main/` does not.

**Option B — Hugging Face Hub Python** (more robust, bypasses raw CDN):

```python
from huggingface_hub import hf_hub_download
content = hf_hub_download(
    repo_id="Nanthasit/sakthai-embedding-multilingual",
    filename="config.json",
    repo_type="model"
)
with open(content) as f:
    config = json.load(f)
```

**Option C — Accept partial coverage.** For sentence-transformers embedding models, `1_Pooling/config.json` provides `embedding_dimension` and `pooling_mode`, and `config_sentence_transformers.json` provides the toolchain versions. The main `config.json` (hidden_size, num_layers, attention heads) is useful but not critical for the health score.

## When to Try This Workaround

When any component of this trio is true:
1. `/raw/main/{filename}` returns 4xx
2. Sibling list or tree API confirms the file exists
3. The file is NOT an LFS-tracked blob (no `.lfs` key in sibling entry)

## Prevention

For future health checks where config.json returns 404 from raw, attempt Option A or B before falling back to partial data. The health score's architecture section will lack hidden_size/num_layers/vocab_size without it, but the card quality score is not impacted (config.json absence is not a quality deduction — it's a CDN issue).
