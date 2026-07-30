# Model Deprecation Workflow — Full Worked Example

## Context

On 2026-07-28, `Nanthasit/sakthai-embedding` (34 dl, English-only sentence-transformers model) was superseded by `Nanthasit/sakthai-embedding-multilingual` (188 dl, 50+ languages). The old card had no redirect and no notice — users landing there would not discover the replacement.

## Recipe

### Step 1: Check current state via HF API

```python
from huggingface_hub import HfApi
api = HfApi()
meta = api.model_info("Nanthasit/sakthai-embedding")
print(meta.downloads)          # 34
print(meta.card_data.tags)     # existing tags
print(meta.card_data.extra)    # {} — empty before update
```

### Step 2: Download, modify, upload README

```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi()
readme_path = api.hf_hub_download("Nanthasit/sakthai-embedding", "README.md")
with open(readme_path) as f:
    content = f.read()

# Add deprecated tag + superseded_by to YAML
old_tags = "tags:\n- sakthai\n- house-of-sak\n- sentence-transformers\n- feature-extraction\n- sentence-similarity\n- sentence-embedding\n- semantic-search\n- dense-retrieval\n- rag\n- retrieval\n- transformers\n- text-embeddings"
new_tags = old_tags + "\n- deprecated"
content = content.replace(old_tags, new_tags)

# Add extra block after tags section (insert before datasets: line)
tags_end = content.find("\ndatasets:")
content = content[:tags_end] + "\nextra:\n  superseded_by: Nanthasit/sakthai-embedding-multilingual" + content[tags_end:]

# Add deprecation banner in README body
old_intro = '  </p>\n</div>\n\n---\n\n# SakThai Embedding'
deprecation = '''  </p>
</div>

> **DEPRECATED — Use SakThai Embedding Multilingual instead**
> This English-only embedding model has been superseded by the **multilingual version**
> that supports 50+ languages with identical 384d output, same 80 MB footprint,
> and API-compatible interface.
>
> [Switch to SakThai Embedding Multilingual](https://huggingface.co/Nanthasit/sakthai-embedding-multilingual)

---

# SakThai Embedding'''

content = content.replace(old_intro, deprecation)

# Update stale sibling download counts
updates = {
    "| [1.5B-merged] ... | 1,197": "| [1.5B-merged] ... | 1,269",
    "| [0.5B-merged] ... | 994": "| [0.5B-merged] ... | 1,030",
    "| [7B-merged] ... | 562": "| [7B-merged] ... | 585",
    "| [7B-128K] ... | 351": "| [7B-128K] ... | 382",
    "| [7B-tools] ... | 185": "| [7B-tools] ... | 219",
    "| [1.5B-tools] ... | 143": "| [1.5B-tools] ... | 163",
    "| [Coder-1.5B] ... | 34": "| [Coder-1.5B] ... | 70",
    "| [Vision-7B] ... | 45": "| [Vision-7B] ... | 104",
    "| [TTS-Model] ... | 33": "| [TTS-Model] ... | 69",
    "| [Multilingual Embedding] ... | 104": "| [Multilingual Embedding] ... | 188",
}
for old, new in updates.items():
    for line in content.split("\n"):
        if old in line:
            content = content.replace(line, new)
            break

# Mark embedding row as deprecated
content = content.replace(
    "| [Embedding] | 80 MB | Search | **34**",
    "| [Embedding] (deprecated) | 80 MB | Search | **34**",
)

# Upload
api.create_commit(
    repo_id="Nanthasit/sakthai-embedding",
    repo_type="model",
    operations=[CommitOperationAdd(path_in_repo="README.md", path_or_fileobj=readme_path)],
    commit_message="chore: mark English-only embedding as deprecated, cross-link to multilingual version",
)
```

### Step 3: Verify

```python
meta = api.model_info("Nanthasit/sakthai-embedding")
assert "deprecated" in meta.card_data.tags
assert meta.card_data.extra.get("superseded_by") == "Nanthasit/sakthai-embedding-multilingual"

readme = api.hf_hub_download("Nanthasit/sakthai-embedding", "README.md")
with open(readme) as f:
    head = f.read(2000)
assert "DEPRECATED" in head
assert "sakthai-embedding-multilingual" in head
```

### Step 4: Record to journal

Append to `LEARNING_JOURNAL.md` with:
- Date and type of change
- What was done (3 bullet points)
- Why it matters
- Updated ecosystem snapshot with current download counts
- Remaining under-50-dl targets for next cycle

## Key Observations

1. **`extra` field is stable** — `api.create_commit()` does NOT validate `extra:` contents. It passes through to the API as-is. The `superseded_by` key is a convention, not a standard field.
2. **Sibling download counts drift** — Always fetch API values during the same session. Never hardcode from memory — by the time you push, numbers may have changed.
3. **Deprecation is reversible** — Remove the `deprecated` tag and `extra` block, restore README. No data loss.
4. **The `extra` YAML block must go inside the YAML frontmatter** (between the `---` delimiters), not in the markdown body. The HF parser reads `extra` from the YAML section only.
