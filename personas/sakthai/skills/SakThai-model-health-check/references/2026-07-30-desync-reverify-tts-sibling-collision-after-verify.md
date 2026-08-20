# TTS Health Check — 2026-07-30: Post-Verification Sibling Overwrite Detected by System Re-prompt

**Model:** `Nanthasit/sakthai-tts-model` (Kokoro TTS, 82M Q8_0 GGUF)
**Run:** Cron auto-eval, 2026-07-30 evening.

## Pattern: System Re-Requested Verification After It Already Passed

**Sequence:**

1. Health check YAML written to `.eval_results/health-check.yaml` (1581 bytes, correct TTS model data)
2. Uploaded to HF Hub — commit `35cce26164`
3. System asked for verification — created `/tmp/hermes-verify-*` script, ran it → **PASS** (14 checks)
4. System asked AGAIN for verification immediately after — this is the signal
5. Re-read local `health-check.yaml` → **wrong model** (sakthai-coder-1.5b data)
6. A sibling subagent had overwritten the generic file between steps 3 and 4
7. Re-wrote correct content, re-verified → **PASS**
8. Re-uploaded → identical content, commit skipped (correct)

## The Canary Signal

**When the system re-prompts for verification after the first verification passed, check for file corruption first.** The system tracks file modification timestamps independently of your verification script. If a sibling agent modifies the file between your verification pass and the system's next check, the system flags it as "unverified" again — even though you already validated the content correctly.

This is distinct from the `write_file _warning` pattern (detects collision *during* write) and the generic-overwrite pattern (detected *during* verification by wrong model ID). Here, the sibling wrote AFTER verification completed, and the system's re-prompt was the only signal.

**Recovery response when system re-requests verification:**

```python
# Don't just re-run verify — first check if the file is still yours
import yaml
with open('.eval_results/health-check.yaml') as f:
    d = yaml.safe_load(f)
model_id = d.get('model') or (d.get('target_model') or {}).get('id') or ''
if 'sakthai-tts-model' not in model_id:
    print(f'⚠ File corrupted by sibling — contains {model_id}')
    # Re-write from session data, then re-verify
```

## Incidental Discovery: Language Count Mismatch Caught by Verification

The YAML wrote `count: 16` for languages, but the API data actually has 15:
```json
"language": ["en","ja","ko","zh","fr","es","pt","it","de","pl","ru","ar","hi","bn","th"]
```

15 items, not 16. The discrepancy was caused by manual counting instead of programmatic
`len(data['cardData']['language'])`. The verification script caught this because it cross-checked
the count field against the actual list length.

**Lesson:** Never hardcode element counts from manual inspection. Always derive them from
the parsed data at YAML generation time:
```python
langs = card_data.get('language', [])
# count = 16  ← WRONG (manual)
count = len(langs)  ← RIGHT (programmatic)
```

## Commands Used

```bash
# Fetch model data
curl -s -o /tmp/tts_model.json "https://huggingface.co/api/models/Nanthasit/sakthai-tts-model"
python3 -c "import json; d=json.load(open('/tmp/tts_model.json')); print(d['downloads'], d['likes'], d['cardData']['language'])"

# Write + upload
uv run --with huggingface_hub python3 -c "
from huggingface_hub import HfApi
import os
api = HfApi(token=os.environ['HF_TOKEN'])
api.upload_file(path_or_fileobj='.eval_results/health-check.yaml', path_in_repo='.eval_results/health-check.yaml', repo_id='Nanthasit/sakthai-tts-model')
"

# Verify remote content identity
curl -s "https://huggingface.co/Nanthasit/sakthai-tts-model/raw/main/.eval_results/health-check.yaml" | head -3
```

## Key Stats

| Metric | Value |
|--------|-------|
| Model | Kokoro 82M Q8_0 GGUF |
| Downloads | 150 |
| Likes | 0 |
| Languages | 15 |
| Datasets | 8 |
| GGUF tensor size | 81,731,256 bytes |
| GGUF file size | 141,322,336 bytes (134.8 MB) |
| YAML size | 1581 bytes |
| Upload commits | 2 (first + fix count) |

## Related References

- `references/2026-07-31-tts-health-check-sibling-collision.md` — sibling detected via `write_file _warning` BEFORE upload (different detection point)
- `references/2026-07-30-lora-generic-yaml-overwrite.md` — generic file overwritten mid-session, detected by verification model mismatch
- `references/2026-07-30-tts-model-check.md` — original TTS methodology
