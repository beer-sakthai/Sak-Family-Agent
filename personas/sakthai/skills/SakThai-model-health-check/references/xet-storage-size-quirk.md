# Xet Storage: Size=0 in API Workaround

**Problem:** HF API (`/api/models/{id}`) returns `size: 0` for all siblings when the repo uses the Xet storage backend (content-addressable dedup storage replacing Git LFS).

**Detection:**
- If all siblings show `size: 0` but the file clearly exists (confirmed by HEAD request to the resolve URL returning 200), the repo is on Xet.

**Solution:** Get actual file size from the `x-linked-size` response header on a HEAD request:

```bash
curl -sI "https://huggingface.co/{REPO_ID}/resolve/main/{FILENAME}" \
  -H "Authorization: Bearer $HF_TOKEN" | grep -i x-linked-size
```

**Example output:** `x-linked-size: 1117320768` (the size in bytes).

**Python:** The `huggingface_hub` library's `HfApi` may also report `size=0` for Xet files. Always verify with a HEAD request when the API reports zero sizes.

**Note:** The `/api/models/{id}` returns `siblings[].lfs: null` for Xet-backed files (no LFS metadata). This is another indicator — if `lfs` is missing/None AND size is 0, the file is on Xet.

**Reference:** Observed on `Nanthasit/sakthai-coder-1.5b` (2026-07-30 health check). The GGUF file `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf` reported 0 bytes in the API but was actually 1,117,320,768 bytes (1.04 GB) per `x-linked-size`.
