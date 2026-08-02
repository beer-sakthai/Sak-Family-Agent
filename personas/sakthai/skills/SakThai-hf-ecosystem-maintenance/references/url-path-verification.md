# URL & File Path Verification for Model Cards

Documented 2026-07-29 — pattern for detecting and fixing broken download URLs in model cards after file reorganization, GGUF cleanup, or rename operations.

## The Problem

Model cards often embed download URLs in Quick Start sections:

```bash
wget https://huggingface.co/Nanthasit/sakthai-coder-1.5b/resolve/main/gguf/sakthai-coder-q4_k_m.gguf
```

If files are later moved (e.g., cleaned from `gguf/` subdirectory to root level) or renamed, these URLs silently **404**. The model card looks professional but the instructions don't work — visitors hit dead ends.

Unlike "stale download counts" (cosmetic), broken URLs are **functional failures** — a user following the Quick Start gets an error.

## When to Check

Check after any:
- **File reorganization** — files moved between directories (e.g., `gguf/` → root)
- **Rename** — files renamed for consistency
- **GGUF requantization** — old quant replaced with new one, different filename
- **Directory cleanup** — subdirectory flattened into root

## Detection: Cross-Reference URLs in Card Against Actual Files

### Step 1: Extract all `resolve/main/` URLs from a model card

```bash
# Extract raw file paths from card
curl -s "https://huggingface.co/Nanthasit/<model>/raw/main/README.md" \
  | grep -oP 'resolve/main/[^\s")]+' \
  | sed 's|resolve/main/||'
```

### Step 2: List actual files in the repo

```python
from huggingface_hub import HfApi
api = HfApi()
files = [s.rfilename for s in api.model_info("Nanthasit/<model>").siblings]
print("\n".join(files))
```

### Step 3: Compare

Any path returned by Step 1 that does NOT appear in Step 2 is a **broken URL** — fix the card.

## URL Pattern Detection by Type

### GGUF files (most common after cleanup)

Look for these patterns in Quick Start sections:

| Suspicious pattern | Likely issue |
|---|---|
| `gguf/<any>.gguf` | Cleaned from `gguf/` to root level |
| `gguf/` in any `wget` URL | Files moved out of `gguf/` directory |
| `./gguf/` in any `ollama create` Modelfile path | Same — `FROM ./gguf/...` |
| `./gguf/` in any `llama-cli -m` path | Same — `-m ./gguf/...` |

Detection command:

```bash
curl -s "https://huggingface.co/Nanthasit/<model>/raw/main/README.md" \
  | grep -oP 'gguf/[^\s")]+'
```

If this returns any output, the card has stale `gguf/` paths.

### Safe patterns

| Pattern | Status |
|---|---|
| `resolve/main/<filename>.gguf` | ✅ Correct — file at root |
| `resolve/main/subdir/<filename>.gguf` | ✅ Correct if subdir actually exists |
| `resolve/main/<filename>.safetensors` | ✅ Correct if file exists |

## Fixing a Broken URL

### 1. Find the actual filename

```python
from huggingface_hub import HfApi
api = HfApi()
files = api.list_repo_files("Nanthasit/<model>", repo_type="model")
gguf_files = [f for f in files if f.endswith(".gguf")]
print(f"Actual GGUF files: {gguf_files}")
```

### 2. Update the card

```python
from huggingface_hub import HfApi
api = HfApi()

readme = api.hf_hub_download(repo_id="Nanthasit/<model>", filename="README.md", repo_type="model")
with open(readme) as f:
    content = f.read()

# Replace old paths — check each pattern
content = content.replace("gguf/sakthai-coder-q4_k_m.gguf", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf")
content = content.replace("FROM ./gguf/", "FROM ./")

api.upload_file(
    path_or_fileobj=content.encode(),
    path_in_repo='README.md',
    repo_id='Nanthasit/<model>',
    repo_type='model',
)
```

### 3. Verify

```bash
# Confirm old paths gone
curl -s "https://huggingface.co/Nanthasit/<model>/raw/main/README.md" \
  | grep -c "gguf/"
# Should return 0 or matches to legitimate non-path uses

# Confirm new paths present
curl -s "https://huggingface.co/Nanthasit/<model>/raw/main/README.md" \
  | grep -c "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"
# Should return ≥1
```

## Multi-Card Scan for Broken GGUF Paths

To check ALL ecosystem model cards for stale `gguf/` paths at once:

```bash
for model in \
  sakthai-context-1.5b-merged \
  sakthai-context-0.5b-merged \
  sakthai-context-7b-merged \
  sakthai-context-7b-128k \
  sakthai-context-7b-tools \
  sakthai-context-1.5b-tools \
  sakthai-embedding-multilingual \
  sakthai-context-0.5b-tools \
  sakthai-coder-1.5b \
  sakthai-vision-7b \
  sakthai-tts-model; do
  count=$(curl -s "https://huggingface.co/Nanthasit/$model/raw/main/README.md" \
    | grep -cP 'gguf/[^\s")]+')
  [ "$count" -gt 0 ] && echo "STALE gguf/ path in $model ($count occurences)"
done
```

## Integration with the Standard Verification Checklist

Add this to the existing checks in `verification-patterns.md`:

| Check | Grep Pattern | Expected |
|---|---|---|
| No stale gguf/ paths | `grep -cP 'gguf/[^\s")]+'` | 0 per card |
| wget URL resolves | Cross-ref against `api.list_repo_files()` | All paths in card exist in repo |

## Order of Operations with Card Enrichment

When both enriching a card AND fixing broken URLs:

1. **Fix URLs first** — you'll likely replace the entire Quick Start section, which overlaps with enrichment
2. Then add sections, badges, download counts
3. Upload once with both fixes

This avoids sequential uploads (makes HF history cleaner) and prevents having to verify the same card twice.

## Real Example

**Coder-1.5b (2026-07-29):** The GGUF was cleaned from `gguf/sakthai-coder-q4_k_m.gguf` to root `qwen2.5-coder-1.5b-instruct-q4_k_m.gguf`. Three patterns broken:
- `wget` URL → pointed to nonexistent `gguf/` subdirectory
- `llama-cli -m` argument → wrong filename
- Ollama `FROM` path → wrong filename

All three fixed in one card update.
