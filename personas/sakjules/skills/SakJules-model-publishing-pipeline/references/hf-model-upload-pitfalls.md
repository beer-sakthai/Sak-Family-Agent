# HF Model Upload Pitfalls

Captures issues that occur when uploading models (sentence-transformers, GGUF, safetensors) to Hugging Face Hub.

## 1. Sentence-Transformers Upload — Missing Tokenizer Files

**Symptom:** Upload succeeds but `model.encode()` fails with:
```
WordPiece error: Missing [UNK] token from the vocabulary
```

**Root cause:** `SentenceTransformer.save()` writes the model weights but some tokenizer files (vocab.txt, tokenizer.json, tokenizer_config.json, special_tokens_map.json, added_tokens.json) may not be included. The HF Hub then serves a partial model.

**Fix — upload all config files from the ORIGINAL pretrained model, not just the saved version:**

```python
from huggingface_hub import snapshot_download
orig = snapshot_download('sentence-transformers/all-MiniLM-L6-v2')  # original
for fname in os.listdir(orig):
    if fname not in ['model.safetensors', 'pytorch_model.bin']:
        api.upload_file(path_or_fileobj=os.path.join(orig, fname), ...)
```

Files to ensure are present in the repo:
- `tokenizer.json` — BPE/WordPiece tokenizer
- `tokenizer_config.json` — tokenizer configuration
- `vocab.txt` — vocabulary (for WordPiece models)
- `special_tokens_map.json` — special token definitions
- `config.json` — model configuration
- `config_sentence_transformers.json` — sentence-transformers config
- `modules.json` — module pipeline definition
- `sentence_bert_config.json` — SBERT config
- `1_Pooling/` — pooling module directory

Always verify with `model.encode(["test"])` after uploading before declaring done.

## 2. GGUF Upload — Missing Sibling Metadata

**Symptom:** GGUF file is downloadable but the model page shows no widget, no pipeline tag, no metadata.

**Root cause:** GGUF-only repos need YAML frontmatter in README.md to be discoverable. The `pipeline_tag` must be set explicitly since it's not inferred from file type.

**Fix — add YAML frontmatter with explicit pipeline_tag:**

```yaml
---
pipeline_tag: text-generation
library_name: transformers
tags: [gguf, qwen2, tool-calling]
---
```

## 3. Large File Upload Timeout

**Symptom:** Upload starts, progresses to 90%+, then hangs or fails with ConnectionError.

**Root cause:** HF Hub's upload endpoint has a timeout for very large files (>1 GB) over slow connections. The `huggingface_hub` library retries but may exhaust retries.

**Fix — use `HfApi.upload_file()` with explicit `chunk_size`:**

```python
api.upload_file(..., chunk_size=50 * 1024 * 1024)  # 50 MB chunks
```

For very large files (>3 GB), consider using `upload_lfs_files()` or splitting into shards.

## 4. Model Repo Already Exists With Wrong Content

**Symptom:** Uploading to a repo that was previously created with empty/minimal content fails or conflicts.

**Fix — use `create_repo(exist_ok=True)` before uploading:**

```python
api.create_repo('org/model-name', repo_type='model', exist_ok=True)
# Then overwrite files
api.upload_folder(folder_path=..., repo_id='org/model-name', repo_type='model')
```

This ensures the repo exists in the right state before files go up.

## 5. Sentence-Transformers Upload from Save — Fails on Load

**Symptom:** After `model.save(tmpdir)` and `upload_folder()`, loading the model from HF fails with import path errors.

**Root cause:** `model.save()` creates a local directory with symlinks or relative paths that break when re-uploaded.

**Fix — use `snapshot_download` of the original model and upload the files directly instead of saving and re-uploading:**

```python
# ❌ Don't:
model.save(tmpdir)
api.upload_folder(tmpdir, ...)

# ✅ Do:
orig = snapshot_download('original/model')
api.upload_folder(orig, ..., ignore_patterns=['*.bin', '*.safetensors'])
# Then upload safetensors separately if needed
```

## 6. Pipeline Tag Not Set — Model Shows "Unknown" Pipeline

**Symptom:** Model appears on HF profile with no pipeline tag, no widget, and doesn't appear in search filters.

**Root cause:** No `pipeline_tag` in YAML frontmatter, and the model type can't be auto-detected.

**Fix — always set pipeline_tag explicitly:**

```yaml
---
pipeline_tag: sentence-similarity  # or text-generation, text-to-speech, etc.
---
```

Common values:
- Text models: `text-generation`, `text-classification`, `fill-mask`
- Embedding: `sentence-similarity`, `feature-extraction`
- Multimodal: `image-text-to-text`, `text-to-image`
- Speech: `text-to-speech`, `automatic-speech-recognition`
- Vision: `image-classification`, `object-detection`

## 7. Uploading GGUF Without Quant — Model Too Large

**Symptom:** FP16 GGUF is 2-3× larger than Q4_K_M, making download slow and limiting adoption.

**Fix — always quantize before uploading unless FP16 is explicitly needed:**

```bash
llama-quantize model-f16.gguf model-q4_k_m.gguf Q4_K_M
```

Upload only the quantized version to save bandwidth and storage. Keep FP16 locally or upload as a secondary variant.
