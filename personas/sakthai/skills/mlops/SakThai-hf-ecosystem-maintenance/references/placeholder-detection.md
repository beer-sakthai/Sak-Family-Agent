# Placeholder / Skeleton Repo Detection

Documented 2026-07-29 — techniques for distinguishing real HF model repos from
placeholder skeletons that have scaffolding files but no actual trained weights.

## Why This Matters

A repo with 0 downloads and a card that screams "pending" is obvious. But many
placeholder repos look real at first glance:

- They have `config.json`, `generation_config.json`, `tokenizer.json`, etc.
- The HF API reports them as models (`pipeline_tag: text-generation`)
- The model card may even have been improved with badges and descriptions
- Only the actual weight file (`model.safetensors`, `adapter_model.safetensors`,
  or GGUF `.gguf`) reveals the truth

If you base your enrichment decisions on download counts alone, you may waste
a cycle improving a skeleton's card instead of promoting a real model that just
needs visibility.

## Detection via HEAD Request

The most reliable technique: send a **HEAD request** to the weight file's raw URL
and check `Content-Length`. Real models are hundreds of MB to GB; placeholders
are ~134 bytes (the minimum safetensors header).

### Python (stdlib, cron-safe)

```python
import urllib.request

def check_file_size(repo_id: str, filename: str, repo_type: str = "model") -> int:
    """Returns Content-Length in bytes. -1 on error."""
    base = {
        "model": "https://huggingface.co",
        "dataset": "https://huggingface.co/datasets",
    }[repo_type]
    url = f"{base}/{repo_id}/raw/main/{filename}"
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        return int(resp.headers.get("Content-Length", -1))
    except Exception:
        return -1

# Check a 0.5B merged model
size = check_file_size("Nanthasit/sakthai-context-0.5b-merged-v2", "model.safetensors")
print(f"model.safetensors: {size} bytes")
# Real Qwen2.5-0.5B: ~380 MB (398,000,000+ bytes)
# Placeholder skeleton: 134 bytes

# Check a LoRA adapter
size = check_file_size("Nanthasit/sakthai-context-0.5b-tools-v2", "adapter_model.safetensors")
print(f"adapter_model.safetensors: {size} bytes")
# Real LoRA (~20 MB): 20,000,000+ bytes
# Placeholder: 133 bytes
```

### Reading the full sibling list with sizes

For a complete picture of what files exist and their sizes:

```python
import urllib.request, json

def get_file_sizes(repo_id: str, repo_type: str = "model") -> dict:
    """Returns {filename: size_in_bytes} for all files in the repo."""
    base = {
        "model": f"https://huggingface.co/api/models/{repo_id}",
        "dataset": f"https://huggingface.co/api/datasets/{repo_id}",
    }[repo_type]
    resp = urllib.request.urlopen(f"{base}", timeout=10)
    data = json.load(resp)
    sizes = {}
    for sib in data.get("siblings", []):
        rn = sib.get("rfilename", "")
        if rn == ".gitattributes":
            continue
        # Try HEAD for individual file sizes
        try:
            furl = f"https://huggingface.co/{repo_type}/{repo_id}/raw/main/{rn}" if repo_type == "model" \
                   else f"https://huggingface.co/datasets/{repo_id}/raw/main/{rn}"
            h = urllib.request.urlopen(urllib.request.Request(furl, method="HEAD"), timeout=10)
            sizes[rn] = int(h.headers.get("Content-Length", 0))
        except Exception:
            sizes[rn] = -1
    return sizes

sizes = get_file_sizes("Nanthasit/sakthai-context-0.5b-merged-v2")
for fname, sz in sorted(sizes.items()):
    mb = sz / 1024 / 1024 if sz > 0 else sz
    print(f"{fname:40s} {mb:.1f} MB" if sz > 0 else f"{fname:40s} ERROR")

# If model.safetensors is 134 bytes → SKELETON (no real weights)
# If model.safetensors is 380,000,000+ bytes → REAL MODEL
```

### Reference: Known Real Sizes vs Placeholder Stubs

| File | Real Size Range | Placeholder Size | What It Means |
|------|----------------|-----------------|---------------|
| `model.safetensors` | 200 MB–15 GB | **134 bytes** | Full model weights vs empty scaffolding |
| `adapter_model.safetensors` | 5–100 MB | **133 bytes** | LoRA/PEFT adapter vs skeleton |
| `tokenizer.json` | 1–15 MB | **133 bytes** | Real tokenizer vs stub |
| `*.gguf` | 100 MB–15 GB | N/A (file absent) | GGUF quant — if absent, no GGUF exists |

**Important:** Very small `tokenizer.json` (133 bytes) is also a strong signal
the repo is a skeleton — a real Qwen/GPT tokenizer is 1–15 MB. If *both*
`model.safetensors` and `tokenizer.json` are under 200 bytes, the repo is
definitely a placeholder.

## Detection via pipeline_tag Filtering

A simpler but less precise check: the `/api/models` endpoint returns ALL repos
that have model-like structure, including datasets and profiles. These always
have `pipeline_tag: null` (rendered as "N/A" or absent).

```python
import urllib.request, json

resp = urllib.request.urlopen(
    "https://huggingface.co/api/models?author=Nanthasit", timeout=10
)
all_repos = json.load(resp)

# Real models have a pipeline tag
real_models = [m for m in all_repos if m.get("pipeline_tag")]

# Probable non-models: no pipeline_tag
non_models = [m for m in all_repos if not m.get("pipeline_tag")]
for m in non_models:
    name = m["id"].split("/")[-1]
    print(f"⚠️  No pipeline_tag: {name} ({m.get('downloads', 0)} dl)")
    # These may be: profile repos, datasets misindexed as models,
    # or repos with no cardData at all
```

**Why this works:** HF Hub assigns a `pipeline_tag` only when the YAML frontmatter
explicitly sets `pipeline_tag:` or the system can auto-detect it. Dataset repos
pushed to the model namespace have no pipeline_tag, so they're filterable.

**Limitation:** A real model that's missing its YAML pipeline_tag will also be
filtered out. Always combine with HEAD-request verification for accuracy.

## Combined Workflow: "Is This Model Real?"

```python
import urllib.request, json

REPO_ID = "Nanthasit/sakthai-context-0.5b-merged-v2"

def is_real_model(repo_id: str) -> tuple[bool, str]:
    """Returns (is_real: bool, reason: str)."""
    # Step 1: Check pipeline_tag from API
    resp = urllib.request.urlopen(
        f"https://huggingface.co/api/models/{repo_id}", timeout=10
    )
    info = json.load(resp)
    if not info.get("pipeline_tag"):
        return False, "No pipeline_tag — likely not a real model"

    downloads = info.get("downloads", 0)
    if downloads > 0:
        return True, f"Has {downloads} downloads — real model"

    # Step 2: Check weight file size
    weight_files = ["model.safetensors", "adapter_model.safetensors"]
    for wf in weight_files:
        # HEAD request
        url = f"https://huggingface.co/{repo_id}/raw/main/{wf}"
        try:
            req = urllib.request.Request(url, method="HEAD")
            resp = urllib.request.urlopen(req, timeout=10)
            size = int(resp.headers.get("Content-Length", 0))
            if size > 100000:  # >100KB = real weights
                return True, f"{wf} = {size/1024/1024:.1f} MB — real weights"
            else:
                return False, f"{wf} = {size} bytes — placeholder stub"
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # try next weight file
            return False, f"HTTP {e.code} checking {wf}"

    return False, "No weight files found"

result, reason = is_real_model(REPO_ID)
print(f"{REPO_ID}: {'✅ REAL' if result else '❌ PLACEHOLDER'} — {reason}")
```

## How This Affects Ecosystem Counting

When reporting ecosystem model counts, the raw `/api/models` count is misleading.
The correct count pipeline:

```python
import urllib.request, json

resp = urllib.request.urlopen(
    "https://huggingface.co/api/models?author=Nanthasit", timeout=10
)
models = json.load(resp)

# Step 1: Filter out profile repos (author/author)
author = "Nanthasit"
models = [m for m in models if m["id"] != f"{author}/{author}"]

# Step 2: Filter out repos with no pipeline_tag (likely datasets or skeletons)
models = [m for m in models if m.get("pipeline_tag")]

# Step 3: For 0-download models, optionally verify with HEAD request
for m in models:
    if m.get("downloads", 0) == 0 and m.get("pipeline_tag"):
        name = m["id"].split("/")[-1]
        print(f"Zero-dl model with pipeline_tag: {name} — likely real but unpopular")
        # Check weight size to confirm, if desired

print(f"Real models: {len(models)}")
```

**Real-world delta (2026-07-29):**
- Raw `/api/models?author=Nanthasit` count: **16**
- After filtering profile + no-pipeline_tag: **14 real models**
- (1 profile + 1 dataset misindexed as model removed)

## Pitfalls

### Git LFS pointers look like small files

When a repo has been cloned but not pulled, the `model.safetensors` in the
working tree is a tiny text file (a Git LFS pointer, ~130 bytes). This is NOT
a placeholder — it's the LFS pointer file. The HEAD request to the HF raw URL
returns the correct Content-Length because the server resolves LFS pointers.

**What this means:** The HEAD-request pattern always works correctly because
it hits the HF CDN, not the local git working tree. Local `ls -l` showing
134 bytes is unreliable — always use the remote HEAD request.

### A 404 on weight file doesn't mean the model is fake

Some real models only have GGUF files (e.g., `*.gguf`) stored under a
subdirectory (e.g., `gguf/model-q4_k_m.gguf`). The `model.safetensors` path
returns 404 for these models — they were converted to GGUF and the original
safetensors may have been removed.

**Fix:** Check for GGUF files too:
```python
def has_real_weights(repo_id: str) -> bool:
    sizes = get_file_sizes(repo_id)
    # Check all files, not just safetensors
    for fname, size in sizes.items():
        if fname.endswith(".gguf") and size > 1_000_000:
            return True
        if fname.endswith(".safetensors") and size > 1_000_000:
            return True
    return False
```

### Private repos return 401 on HEAD requests

If a repo is private or gated, the HEAD request returns HTTP 401. This doesn't
mean the repo is a skeleton — it means you can't verify files without auth.

**Fix:** Add `Authorization: Bearer $HF_TOKEN` to the HEAD request:
```python
req = urllib.request.Request(url, method="HEAD")
req.add_header("Authorization", f"Bearer {os.environ.get('HF_TOKEN', '')}")
resp = urllib.request.urlopen(req, timeout=10)
```

## When to Use This

| Situation | Use HEAD check? | Alternative |
|-----------|:--------------:|-------------|
| 0-download model with card needing enrichment | ✅ Always | Skip if card pending is clear |
| Model with 5+ downloads | ❌ Skip | Downloads confirm real usage |
| Dataset empty-scaffold check | ❌ Use sibling 0-size check | See `new-asset-discovery.md` |
| Counting ecosystem models | ✅ Filter null pipeline_tag | Then HEAD-check borderline cases |
| Deciding cron target priority | ✅ Check first | Avoid skeleton-card enrichment |

## Relation to Other References

- `new-asset-discovery.md` — covers detecting *new* repos (this covers verifying
  they're actually models)
- `target-selection-strategies.md` — use this technique to avoid selecting
  placeholder repos as enrichment targets
- `cron-mode-workarounds.md` — has the same HEAD-request pattern without the
  placeholder-detection context
