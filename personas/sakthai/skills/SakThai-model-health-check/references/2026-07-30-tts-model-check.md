# TTS Model Health Check — 2026-07-30

**Model:** `Nanthasit/sakthai-tts-model` (Kokoro TTS, 82M Q8_0 GGUF, ~135 MB)

## Key findings

1. **Sibling sparsity confirmed**: The `/api/models/{id}` response returned siblings with **only `rfilename`** — no `size`, `lfs`, or `type` fields. Even the GGUF file (`kokoro-82m-q8_0.gguf`) had `size: None`. This is consistent with non-Transformers models that don't use the standard huggingface_hub metadata pattern.

2. **`gguf` top-level key WAS present** contrary to earlier assumptions that TTS models lack it. The key contained:
   ```json
   {"total": 81731256, "architecture": "kokoro", "totalFileSize": 141322336}
   ```
   This contradicts the earlier claim "No `gguf` top-level key for TTS models" — the key may be present for Kokoro GGUF repos. The correction was applied to the skill: always inspect sibling filenames as primary detection, treat `gguf` key as optional bonus.

3. **`usedStorage` matched `gguf.totalFileSize`** exactly (141,322,336 bytes), meaning for a repo with no Git history (single upload, no overwrites), `usedStorage` IS the current file size — no inflation.

4. **HEAD request `x-linked-size` confirmed**: The HEAD request returned `x-linked-size: 141322336`, matching the gguf key. This fallback works for Xet-backed TTS repos.

5. **Downloads/likes unchanged**: 150 downloads, 0 likes — identical to the first check 7 minutes earlier. Only the commit SHA changed (due to the previous health-check YAML upload).

6. **`library_name: kokoro`** confirms this uses the kokoro-onnx TTS engine, not transformers. **`pipeline_tag: text-to-speech`** correctly identifies the task.

## Verification pattern used

```python
# String-based YAML validation (no pyyaml dep)
with open(yaml_path) as f:
    c = f.read()
assert "pipeline_tag: text-to-speech" in c
assert "downloads: 150" in c

# HF API sibling check
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req) as resp:
    data = json.load(resp)
    sibs = [s['rfilename'] for s in data.get('siblings', [])]
    assert '.eval_results/health-check-tts-model.yaml' in sibs
```

## Commands used

```bash
# Fetch model info
curl -s -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/models/Nanthasit/sakthai-tts-model" \
  -o /tmp/sakthai-tts-model.json

# Get file size via HEAD (x-linked-size fallback)
curl -s -I -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/Nanthasit/sakthai-tts-model/resolve/main/kokoro-82m-q8_0.gguf"

# Upload health check
uv run python3 -c "
from huggingface_hub import HfApi
api = HfApi(token=os.environ['HF_TOKEN'])
api.upload_file(path_or_fileobj='...', path_in_repo='.eval_results/health-check-tts-model.yaml',
    repo_id='Nanthasit/sakthai-tts-model', repo_type='model')
"
```
