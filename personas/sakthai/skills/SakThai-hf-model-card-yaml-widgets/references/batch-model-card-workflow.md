# Batch Model Card Generation & Upload Workflow

Generate and upload proper README.md model cards for multiple repos under an HF author in a single pipeline.

## Workflow: Discover → Analyze → Generate → Upload → Verify

### Step 1: Discover all repos under an author

```python
from huggingface_hub import HfApi
api = HfApi(token="hf_...")

models = list(api.list_models(author="Nanthasit"))
for m in models:
    print(f"{m.modelId} — downloads: {m.downloads}, likes: {m.likes}")
```

Key details available from each model object:
- `modelId` — full repo ID
- `downloads` — total download count (use for prioritization)
- `likes` — heart count
- `pipeline_tag` — e.g. "text-generation", "sentence-similarity"
- `tags` — metadata tags array
- `private` — boolean privacy flag

### Step 2: Gather architecture + training details per model

**Model architecture** (from `config.json`):

```python
path = api.hf_hub_download(repo_id, "config.json")
with open(path) as f:
    cfg = json.load(f)

info = {
    "architectures": cfg.get("architectures", ["?"])[0],
    "hidden_size": cfg.get("hidden_size"),
    "num_hidden_layers": cfg.get("num_hidden_layers"),
    "num_attention_heads": cfg.get("num_attention_heads"),
    "max_position_embeddings": cfg.get("max_position_embeddings"),
    "vocab_size": cfg.get("vocab_size"),
    "intermediate_size": cfg.get("intermediate_size"),
}
```

**LoRA adapter details** (from `adapter_config.json` — present on PEFT adapters):

```python
path = api.hf_hub_download(repo_id, "adapter_config.json")
with open(path) as f:
    cfg = json.load(f)

lora_info = {
    "r": cfg.get("r"),
    "lora_alpha": cfg.get("lora_alpha"),
    "lora_dropout": cfg.get("lora_dropout"),
    "target_modules": cfg.get("target_modules"),
    "base_model": cfg.get("base_model_name_or_path"),
    "peft_type": cfg.get("peft_type"),
    "peft_version": cfg.get("peft_version"),
}
```

**Context extension details** (YaRN, from `config.json`):

```python
rope_scaling = cfg.get("rope_scaling", {})
# e.g. {"factor": 4.0, "original_max_position_embeddings": 32768, "type": "yarn"}
```

**Training metrics** (from `training_metrics.json`):

```python
path = api.hf_hub_download(repo_id, "training_metrics.json")
with open(path) as f:
    metrics = json.load(f)
# Contains log array with loss, grad_norm, learning_rate, token_accuracy per step
```

### Step 3: Generate the README.md

Structure each model card with:

1. **YAML frontmatter** (between `---` fences):
   ```yaml
   ---
   license: apache-2.0
   language:
   - en
   library_name: transformers   # or peft, sentence-transformers
   pipeline_tag: text-generation
   tags:
   - qwen2.5
   - sakthai
   - tool-calling
   datasets:
   - Nanthasit/sakthai-combined-v5
   base_model: Qwen/Qwen2.5-7B-Instruct
   model-index:
   - name: sakthai-context-7b-merged
     results:
     - task:
         type: text-generation
       dataset:
         name: Eval Suite
       metrics:
       - type: pass_rate
         value: 100.0
   ---
   ```

2. **Header** — dynamic download badge, title, one-line tagline, collection link
3. **What it is** — 2–3 sentences: base, method, what it does
4. **Quick Start** — load + generate Python code (one block)
5. **Training table** — base model, dataset, LoRA config + one-line architecture
6. **Evaluation** — honest pass rates, internal-vs-verified labeled
7. **SakThai model family** — the canonical table, **size + role, no download counts**
8. **Links** — GitHub, profile, collection (no "paper" link — that repo does not exist)

> Follow the lean card standard: `SakThai-model-publishing-pipeline/references/model-card-enrichment-workflow.md`.
> No hardcoded download counts, no repeated family tables, no "Rising Stars"/funnel sections,
> story on the profile card only.

**Download badge — use the dynamic JSON badge, never a hardcoded number**:
```html
<img src="https://img.shields.io/badge/dynamic/json?url=https%3A//huggingface.co/api/models/Nanthasit/REPO&query=%24.downloads&label=downloads&color=blue&cacheSeconds=3600" alt="Downloads"/>
```
Not `shields.io/endpoint` — the HF API does not implement shields' endpoint schema, so that
form renders `invalid properties: label, message`. Keep `url=` percent-encoded.

### Step 4: Upload via HfApi.upload_file

```python
def upload_readme(repo_id, content):
    """Upload README.md to a model repo."""
    path = f"/tmp/readme_{repo_id.replace('/', '_')}.md"
    with open(path, "w") as f:
        f.write(content)
    api.upload_file(
        path_or_fileobj=path,
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",  # or "dataset" for dataset repos
    )
    os.unlink(path)
```

**Batch upload pattern** — upload priority models first, then remaining:

```python
priority = [
    ("Nanthasit/sakthai-context-1.5b-merged", readme_1_5b),
    ("Nanthasit/sakthai-context-7b-merged", readme_7b),
    ...
]
remaining = [...]

for repo_id, content in priority + remaining:
    upload_readme(repo_id, content)
```

### Step 5: Verify

Re-download each README and check:
- YAML frontmatter present (`content.startswith("---")`)
- Required keywords present (tool-calling, architecture, training, eval)
- Minimum content length (>500 chars)
- YAML has required fields (tags, license, language)

```python
path = api.hf_hub_download(repo_id, "README.md")
with open(path) as f:
    content = f.read()

assert content.startswith("---"), f"{repo_id}: missing YAML"
assert len(content) > 500, f"{repo_id}: too short"
assert "## Quick Start" in content, f"{repo_id}: missing usage section"
```

### Pitfalls

- **`api.upload_file` skips identical content** — if the file hasn't changed from the last commit, HFHub returns "No files have been modified since last commit. Skipping to prevent empty commit." This is benign — the upload succeeded.
- **Dataset repos need `repo_type="dataset"`** — omitting this or using "model" for a dataset repo causes a 404.
- **YAML comma-formatted numbers** — badges use URL-encoded commas (e.g. `1%2C025` for "1,025"). The raw number string "1025" does NOT appear in the rendered badge alt text. If verification checks for "1025", ensure the markdown body also contains the raw number, not just the comma-formatted version.
- **Profile repos** (`Nanthasit/Nanthasit`) are regular model repos, not a special type. Use `repo_type="model"`.
- **Private repos** require authentication with write token. `list_models` may not return them unless the token is the repo owner's.
- **`exec()` for multi-variable export** — When you need to access multiple string variables from a Python file that assigns them (e.g., `readme_0_5b = """..."""`), use `exec()` with locals or globals dict rather than importlib, since these aren't module-level functions.

### Related

- `hf-model-card-yaml-widgets` — YAML metadata schema reference
- `huggingface-hub` → `references/hf-hub-python-api.md` — HfApi class reference
