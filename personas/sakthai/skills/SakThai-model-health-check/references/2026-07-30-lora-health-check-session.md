# LoRA Adapter Health Check — 2026-07-30 Session

## Model
`Nanthasit/sakthai-plus-1.5b-lora` — LoRA PEFT adapter on Qwen2.5-1.5B-Instruct

## YAML Format Used
Flat structure (no `health_check:` wrapper), distinct from both the "slim-schema" and "old-schema":

```yaml
model:
  id: Nanthasit/sakthai-plus-1.5b-lora
  type: LoRA adapter (PEFT)
  pipeline_tag: text-generation
  library_name: transformers
  license: apache-2.0
  private: false
  gated: false
  sha: ef7c3184…
base_model:
  id: Qwen/Qwen2.5-1.5B-Instruct
  verified_by: [cardData, tags, adapter_config]
adapter_config:
  peft_type: LORA
  r: 16
  lora_alpha: 32
  lora_dropout: 0.05
  target_modules: [q_proj, k_proj, v_proj, o_proj, gate_proj, up_proj, down_proj]
  task_type: CAUSAL_LM
metrics:
  downloads: 0
  likes: 0
  last_modified: "2026-07-30T22:47:04.000Z"  # post-upload fetch
  file_count: 11
  adapter_weights:
    filename: adapter_model.safetensors
    lfs_size_bytes: 73911112
    lfs_oid: sha256:a1b60e3c…
tags: [transformers, safetensors, sft, qwen, lora, peft, instruct, ...]
health_status:
  model_exists: true
  api_reachable: true
  base_model_documented: true
  adapter_config_valid: true
  weights_present: true
  score: 10/10
```

## Key Patterns

### Adapter weight size from LFS pointer
HF API siblings return size=0 for LoRA `adapter_model.safetensors` (LFS pointer). Get real size by fetching the LFS pointer file and reading the `size` line:

```bash
curl -sL "https://huggingface.co/{repo}/resolve/main/adapter_model.safetensors" | head -3
# version https://git-lfs.github.com/spec/v1
# oid sha256:...
# size 73911112
```

The `safetensors` top-level API field (total parameter count) is NOT present for LoRA adapters — only full-model safetensors have it. Do not rely on it for PEFT repos.

### Verification caught lastModified desync
The verification script cross-checked `lastModified` against the live API, which caught the upload bump. Recovery: fetch updated timestamp from API, patch YAML, re-upload.

### Health score for LoRA adapters
LoRA adapters aren't independently usable — they have no standalone benchmarks, no `model-index`, no `base_model_info`. Score is simple pass/fail: 10/10 if all components present (weights, config, README, tokenizer). Full componentized scoring (popularity, momentum, benchmarks, card quality, hygiene) doesn't apply since LoRA adapters are spinoffs, not independent models.
