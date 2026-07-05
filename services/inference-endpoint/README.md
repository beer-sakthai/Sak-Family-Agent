# SakThai 1.5B Inference Endpoint

Live serving endpoint for the merged 1.5B model.

**Endpoint URL:**
```
https://eh3lv509oegmvapd.us-east-1.aws.endpoints.huggingface.cloud
```

**Config:**
- **Model:** [sakthai-context-1.5b-merged](https://huggingface.co/Nanthasit/sakthai-context-1.5b-merged)
- **GPU:** nvidia-a10g ×1 (t4-small unavailable)
- **Framework:** pytorch
- **Scaling:** 0 min / 1 max replica, scale-to-zero (15 min timeout)
- **Cost:** ~$0.60/hr (only when active)
- **Created:** 2026-07-05

**Files:**
- `poll_endpoint.py` — polls endpoint status until running

**Usage:**
```bash
curl https://eh3lv509oegmvapd.us-east-1.aws.endpoints.huggingface.cloud \
  -H "Authorization: Bearer \$HF_TOKEN" \
  -d '{"inputs":"Hello!","parameters":{"max_new_tokens":50}}'
```
