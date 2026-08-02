# Adding Local Inference Instructions to Model Cards

Documented 2026-07-29 — patterns for adding ollama, llama.cpp, and other local runner usage sections to model cards.

## When to Add

| Signal | Priority |
|--------|:--------:|
| Model is a GGUF and has no llama.cpp instructions | High |
| Vision model (GGUF + mmproj) and has no ollama instructions | High |
| Coder/text model and has no ollama instructions | Medium |
| Model uses a non-standard runner but has no setup instructions at all | High |

## Standard Insertion Points

Most model cards have a Quick Start section near the top (after the intro/badges, before benchmarks). Within Quick Start, the standard order is:

```
## Quick Start
### CLI (llama.cpp)        ← if applicable
### Ollama (local)         ← insert here if missing
### Python                 ← always present
```

**Vision models** get the extra `--image` flag and mmproj notes. **Text/coder models** don't need mmproj or `--image`.

## Pattern: Add Ollama Instructions

### Step 1 — Identify insertion point

Find the `### Python` header (or whichever section follows the intended insertion point):

```python
content = read_card("author/repo")
idx = content.index("### Python (something)")
before = content[:idx]
after = content[idx:]
```

### Step 2 — Craft the ollama section

**Vision model template:**

```markdown
### Ollama (local)

```bash
# Download the model files
huggingface-cli download <author>/<repo> --local-dir ./<model-dir>

# Import into Ollama
ollama create <model-name> -f Modelfile
# FROM ./<model-dir>/<model-file>.gguf
# TEMPLATE """{{ .System }}
#
# USER: {{ .Prompt }}
# ASSISTANT:
# """

# Run with an image (vision models)
ollama run <model-name> "Describe this image in detail"
ollama run <model-name> "What's in this photo?" --image path/to/photo.jpg
```

> **Tip:** The `mmproj-model-f16.gguf` file is auto-detected when placed alongside the model GGUF.
```

**Text/coder model template:**

```markdown
### Ollama (local)

```bash
# Download the GGUF
huggingface-cli download <author>/<repo> --local-dir ./<model-dir>

# Import into Ollama
ollama create <model-name> -f Modelfile   # FROM ./<model-dir>/<model-file>.gguf

# Run
ollama run <model-name> "Your prompt here"
```
```

### Step 3 — Verify structural integrity

After insertion, verify these markers are ALL still present (use `.contains()` on the final content):

| # | Marker | Why |
|---|--------|-----|
| 1 | `### Ollama` | Header exists |
| 2 | `ollama create` | Modelfile example |
| 3 | `--image` (vision only) | Vision CLI works |
| 4 | `mmproj` (vision only) | mmproj note present |
| 5 | `### Python` | Python section preserved |
| 6 | `img.shields.io/endpoint` | Download badge intact |
| 7 | `## License` | License section preserved |
| 8 | Pipeline diagram (if present) | Diagram intact |
| 9 | `## Quick Start` | Quick Start header intact |
| 10 | Ecosystem footer (e.g. "models · datasets · Spaces") | Footer intact |

### Step 4 — Upload

```python
from huggingface_hub import HfApi

api = HfApi()
api.upload_file(
    path_or_fileobj=new_content.encode(),
    path_in_repo='README.md',
    repo_id='author/repo',
    repo_type='model',
    commit_message='Add ollama usage instructions to Quick Start'
)
```

## What NOT to Do

- **Don't break the Modelfile syntax** — the `TEMPLATE` line must use proper quoting. The `FROM` line references the local GGUF path.
- **Don't remove existing content** — insert, don't replace. Check 10 markers after edit.
- **Don't add ollama for pytorch models** — ollama only loads GGUF. If the model has no GGUF, skip ollama.
- **Don't forget mmproj for vision models** — without it, ollama can't process images. The mmproj note is critical.
- **Don't use stale download counts** — if you mention downloads in the section, use API values or a dynamic badge.

## Real Example: vision-7b (2026-07-29)

The `Nanthasit/sakthai-vision-7b` card (11,469 → 12,204 chars) gained an ollama section between the existing llama.cpp CLI and Python sections. The section shows:
- `huggingface-cli download` to get the GGUF + mmproj
- `ollama create` with Modelfile example
- `ollama run` with `--image` flag
- Tip about mmproj auto-detection
