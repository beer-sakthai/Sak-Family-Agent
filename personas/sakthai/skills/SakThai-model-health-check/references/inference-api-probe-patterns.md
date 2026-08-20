# Inference API Probe Patterns

Session-specific detail from the Jul 30 2026 cron eval of `Nanthasit/sakthai-plus-1.5b`.

## Fallback chain

When running an inference availability check in cron mode, probe in this order:

1. **`HfApi.model_info()`** — quick pre-check: does the model exist? Pipeline tag? Download count?
   ```python
   from huggingface_hub import HfApi
   api = HfApi(token=HF_TOKEN)
   info = api.model_info("Nanthasit/sakthai-plus-1.5b")
   print(f"pipeline_tag={info.pipeline_tag}, downloads={info.downloads}")
   ```
   - If `downloads == 0`: model has never been cached by any provider. Likely will fail inference.

2. **`router.huggingface.co/hf-inference/models/{model}`** — modern inference endpoint (confirmed working in cron env).
   ```python
   import requests
   r = requests.post(
       f"https://router.huggingface.co/hf-inference/models/{model_id}",
       headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
       json={"inputs": prompt, "parameters": {"max_new_tokens": 50}},
       timeout=30
   )
   ```
   - 200 → model works, record output.
   - 400 with `{"error":"Model not supported by provider hf-inference"}` → model isn't deployed on any provider. Record as `status: unavailable`.
   - Other errors → DNS or auth issue.

3. **`api-inference.huggingface.co/models/{model}`** — legacy endpoint. **May fail DNS in cron** (`NameResolutionError`). Only use as last resort.

4. **`huggingface.co/api/models/{model}`** — metadata-only REST API. Always resolves. Use for the Metadata Health Check mode.

## YAML diagnostic format (for `Nanthasit/eval_results`)

When inference is unavailable, upload a diagnostic YAML:

```yaml
model: Nanthasit/sakthai-plus-1.5b
timestamp: '2026-07-30T23:26:40Z'
inference_api:
  status: unreachable
  error: 'DNS resolution failure: api-inference.huggingface.co did not resolve'
  detail: 'Model is not supported by any HF Inference provider (confirmed by router.huggingface.co)'
model_info:
  pipeline_tag: text-generation
  downloads: 0
  likes: 0
  inference_available: false
  note: 'Model exists on Hub but never requested via Inference API. Must be run locally.'
```

## Upload pattern

```python
from huggingface_hub import HfApi, create_repo
import yaml, datetime

api = HfApi(token=token)
create_repo("Nanthasit/eval_results", repo_type="dataset", exist_ok=True)

ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%d_%H%M%S")
filename = f"inference-check-{ts}.yaml"

api.upload_file(
    path_or_fileobj=yaml.dump(data, default_flow_style=False, sort_keys=False).encode(),
    path_in_repo=filename,
    repo_id="Nanthasit/eval_results",
    repo_type="dataset",
    commit_message=f"chore(eval): inference check {ts}",
)
```
