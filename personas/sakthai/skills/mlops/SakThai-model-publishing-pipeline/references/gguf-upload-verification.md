# GGUF Upload & Verification Reference

> **Session origin:** 2026-07-28 — discovered that `upload_file()` Python API silently creates 0 MB LFS stubs.

## LFS Upload: CLI vs Python API

**Critical finding:** The `huggingface_hub.upload_file()` Python method creates empty LFS pointer files (0 MB, no LFS info in siblings API) instead of uploading the actual file blob. The `hf upload` CLI works correctly.

### ✅ Works — `hf upload` CLI
```bash
export PATH="/opt/data/.local/bin:$PATH"
hf upload REPO_ID /local/path/file.gguf remote_name.gguf --repo-type model
```
This properly stores the LFS blob and returns a commit URL.

### ❌ Fails — `upload_file()` Python API
```python
from huggingface_hub import HfApi
api = HfApi()

# This creates an empty 0 MB stub, NOT a real file!
api.upload_file(
    path_or_fileobj="/path/to/model.gguf",
    path_in_repo="model.gguf",
    repo_id="org/model",
    repo_type="model",
)
# File appears in siblings API but size=0 and lfs is empty
```

The upload progress bar shows 100% but the underlying LFS blob is never stored. The file exists only as a git pointer text file (~134 bytes containing `version https://git-lfs.github.com/spec/v1`).

### Upload method comparison

| Method | Works for GGUF/LFS? | Notes |
|--------|:-------------------:|-------|
| `hf upload CLI` | ✅ Yes | Use for all GGUF/large binary files |
| `hf cp` | ❌ No | Reports "No files modified" if stub exists |
| `HfApi.upload_file()` | ❌ No | Creates empty 0 MB stubs |
| `HfApi.upload_folder()` | ❌ No | Same underlying issue |
| `HfApi.upload_large_folder()` | ❌ No | Same underlying issue |

## Verification: Confirming LFS Files are Real

The HF API siblings endpoint does NOT reliably return LFS blob sizes. A file may appear as 0 MB in the API but actually be correctly uploaded.

### ❌ Don't use: HEAD requests or API siblings check
```python
# Unreliable — returns 0 MB even for valid files
siblings = api.get_repo_info("org/model").siblings
for s in siblings:
    print(s.size)  # 0 for LFS files
```

### ✅ Use: Range download test
```bash
curl -sL -r 0-1023 -o /dev/null -w "%{http_code}" \
  "https://huggingface.co/ORG/REPO/resolve/main/FILE.gguf"
# Expected: 206 (partial content, file exists)
# If 404: file doesn't exist
```

Python:
```python
import requests
r = requests.get(
    f"https://huggingface.co/org/model/resolve/main/model.gguf",
    headers={"Range": "bytes=0-1023"},
)
# r.status_code == 206 → file exists
# r.status_code == 404 → file doesn't exist
```

### Quick batch verification
```bash
for pair in "org/model|file.gguf"; do
  repo="${pair%|*}"
  file="${pair#*|}"
  url="https://huggingface.co/$repo/resolve/main/$file"
  code=$(curl -sL -r 0-1023 -o /dev/null -w "%{http_code}" --max-time 15 "$url")
  if [ "$code" = "206" ]; then
    echo "✅ $file"
  else
    echo "❌ $file (HTTP $code)"
  fi
done
```

## HF Spaces: Free Tier Limitations

| SDK | Free Tier | Requires PRO |
|-----|:---------:|:------------:|
| **Static** (HTML/CSS/JS) | ✅ Yes ($0) | ❌ No |
| **Gradio** | ❌ No | ✅ Yes ($9/mo) |
| **Streamlit** | ❌ No | ✅ Yes ($9/mo) |
| **Docker** | ❌ No | ✅ Yes ($9/mo) |

Creating a static Space:
```python
api.create_repo(
    repo_id="org/my-space",
    repo_type="space",
    space_sdk="static",  # Free! No PRO needed
)
```

Creating a Gradio/Docker Space returns HTTP 402 (Payment Required) without a PRO subscription. Static Spaces are the only zero-cost option.

## Recovery: Fixing Empty LFS Stubs

If you discover 0 MB stubs already committed:

1. **Delete the empty stub** using the API:
```python
api.delete_file(path_in_repo="model.gguf", repo_id="org/model", repo_type="model")
```

2. **Re-upload using `hf upload` CLI:**
```bash
hf upload org/model /local/path/model.gguf model.gguf --repo-type model
```

3. **Verify** with a range download test (HTTP 206 expected).

Do not attempt to upload the same path with `upload_file()` again — it will produce the same empty stub result.
