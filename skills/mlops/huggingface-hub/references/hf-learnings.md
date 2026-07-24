# HF Learnings — Cumulative Reference

## Entry 1: Custom Docker Spaces on HF Hub
**Date:** 2026-07-23
**Topic:** `hf-spaces-docker` — Deep dive into Hugging Face Docker Spaces

### Key Takeaways

1. **Dockerfile permissions are strict** — Container runs as UID 1000. Must create user with `useradd -m -u 1000 user`, use `--chown=user` on COPY/ADD, avoid recursive chown which duplicates files across layers.

2. **Secrets at buildtime vs runtime** — In Docker Spaces, secrets at buildtime are **mounted as files** via `--mount=type=secret,id=SECRET_NAME`. At runtime they behave like standard env vars. Regular Gradio/Streamlit Spaces don't have this distinction.

3. **No GPU during docker build** — GPU is only available at runtime. All GPU-dependent commands must run at container startup, not during build.

4. **Data persistence requires Storage Buckets** — All data on disk is lost on restart. Two main strategies:
   - HF Storage Buckets (S3-compatible object storage, non-versioned)
   - Datasets Hub via Git LFS + huggingface_hub

5. **`/data` volume is runtime-only** — Not available during Docker build step.

6. **Built-in env vars** — `HF_API_TOKEN`, `SPACE_ID`, `SPACE_TITLE`, `SPACE_HOST`, `SPACE_REPO_NAME`, `SPACE_AUTHOR_NAME`, `SPACE_SDK` are auto-injected.

7. **Networking restriction** — Only outbound ports 80, 443, 8080 are open.

8. **Billing** — Per-minute billing only during `Starting` or `Running` states; build time is free. Paused Space = no billing.

### Commands Reference
```bash
# Programmatic hardware config
hf spaces hardware <name> --hardware t4-small

# Bucket operations
hf buckets create my-bucket --private
hf buckets list my-bucket -h -R
hf buckets sync /data hf://buckets/username/my-bucket/

# SSE logs
curl -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/api/spaces/{ns}/{repo}/logs/build?tail=100"

# API: sleep time
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -d '{"sleepTime": 15}' \
  "https://huggingface.co/api/spaces/{ns}/{repo}/settings"

# API: replicas
curl -X POST -H "Content-Type: application/json" \
  -H "Authorization: Bearer $HF_TOKEN" \
  -d '{"replicas": 2}' \
  "https://huggingface.co/api/spaces/{ns}/{repo}/replicas"
```

### Key Differences from Gradio/Static Spaces
- **Docker**: Most flexible (any app), secrets at buildtime are file-mounted, GPU only at runtime, paid plan required
- **Gradio**: Python ML demos, ZeroGPU free tier available, simpler setup
- **Static**: HTML/JS only, completely free, no secrets built-in

## Entry 2: Gradio Advanced Patterns for HF Spaces
**Date:** 2026-07-23
**Topic:** `gradio-spaces-advanced-patterns` — Gradio Blocks architecture, event handling, queue, auth, theming, state, file handling, and client libraries for Hugging Face Spaces

### Key Takeaways

1. **Three APIs for different use cases** — `gr.Interface` (simple demos), `gr.Blocks` (custom layouts/events), `gr.ChatInterface` (chatbots). Blocks is the most flexible and preferred for production-grade Spaces.

2. **Queue is mandatory for Spaces** — Without `demo.queue()`, concurrent users get rejected. Use `default_concurrency` and `max_size` parameters to control throughput.

3. **State management** — `gr.State()` stores per-session Python-serializable objects. `gr.BrowserState()` persists in browser localStorage across page reloads.

4. **Event system is rich** — `.click()`, `.submit()`, `.change()`, `.select()`, `.key_up()`, `.upload()`, `.play()`, `.pause()` plus helper data objects (SelectData, EventData, LikeData, etc.). Events can be chained with `.then()`.

5. **Gradio 5+ introduced** — `gr.DownloadButton`, `gr.ChatInterface` streaming, `gr.MultimodalTextbox`, `@gr.Cache()` decorator, `gr.FileExplorer`, `gr.Sidebar`, `gr.Navbar`, `gr.Timer`, and `set_static_paths()` helper.

6. **Theming is straightforward** — Built-in themes (Soft, Monochrome, Default, Glass) and custom themes via `Theme(primary_hue, secondary_hue, neutral_hue, font)`. Custom CSS injection via `gr.Blocks(css=...)`.

7. **Client libraries** — Python client (`gradio_client`) and JS/TS client (`@gradio/client`) for programmatic access. `handle_file()` simplifies file upload across all environments (local, URL, Blob, Buffer).

8. **HF Spaces integration** — `gr.Request` provides access to user info (username, client host) in authenticated Spaces. `gr.LoginButton` adds HF OAuth login. Environment variables (`HF_TOKEN`, `SPACE_ID`, etc.) are auto-injected.

### Gradio 6.x Latest (mid-2026)
- Gradio 6.20.0 is the current version
- Hot reload mode: `gradio app.py` (auto-reloads on file changes)
- Vibe mode: `gradio --vibe app.py` (in-browser chat for natural language app editing)
- `@gr.Cache()` caches function results keyed by input
- Status events include: sleeping, running, building, error, stopped

## Entry 3: HF Inference Endpoints — Production Model Deployment
**Date:** 2026-07-23
**Topic:** `hf-inference-endpoints` — Deploy, manage, scale, and monitor production-grade model endpoints via Python SDK and REST API

### Key Takeaways

1. **API base**: `https://api.endpoints.huggingface.cloud/v2`. All operations go through `HfApi` in the `huggingface_hub` Python SDK or direct REST with Bearer token auth.

2. **Endpoint statuses**: `pending` → `initializing` → `running` → `paused`/`scaledToZero`/`failed`. `paused` requires manual resume; `scaledToZero` auto-recovers on next request (cold start 20-60s).

3. **Lifecycle methods** on `InferenceEndpoint` object:
   - `ep.wait()` — blocks until running, checks health endpoint
   - `ep.pause()` / `ep.resume()` — manual stop/start
   - `ep.scale_to_zero()` — auto-scale down, charged $0
   - `ep.update(...)` — change compute, model, or secrets
   - `ep.delete()` — irreversible, prefer pause/scale-to-zero

4. **Client inference**: `ep.client` returns an `InferenceClient` pointing at the endpoint URL. Supports all HF inference methods (`text_generation`, `text_classification`, etc.).

5. **Create from catalog** (`create_inference_endpoint_from_catalog`) is simpler — uses pre-tested default configs from the Inference Catalog. Just pass `repo_id` + optional `accelerator`.

6. **Auto-scaling parameters**: `min_replica`, `max_replica`, `scale_to_zero_timeout` (minutes idle), `scaling_metric` (`pendingRequests` or `hardwareUsage`), `scaling_threshold` (0.0–1.0).

7. **Inference engines**: vLLM, TGI, SGLang, TEI, llama.cpp, Inference Toolkit, or custom Docker images. Use `framework="custom"` + `custom_image` dict for custom engines.

8. **Pricing**: Hourly per-replica billing, metered per minute. Only charged when `running`. `paused` and `scaledToZero` states cost $0.

### SDK Methods Reference
```python
api.create_inference_endpoint(name, *, repository, framework, accelerator, instance_size, instance_type, region, vendor, ...)
api.list_inference_endpoints(namespace="*")  # all namespaces
api.get_inference_endpoint(name, namespace=...)
api.update_inference_endpoint(name, ...)
api.delete_inference_endpoint(name, ...)
api.pause_inference_endpoint(name, ...)
api.resume_inference_endpoint(name, ...)
api.scale_to_zero_inference_endpoint(name, ...)
api.create_inference_endpoint_from_catalog(repo_id, name=..., accelerator=...)
```

### Key Constants
```python
INFERENCE_ENDPOINTS_ENDPOINT = "https://api.endpoints.huggingface.cloud/v2"
INFERENCE_ENDPOINT = "https://api-inference.huggingface.co"  # serverless
```

### Pitfalls
- Paid service — requires active HF subscription + credit card
- Cold start (20-60s) when scaled to zero
- Instance type varies by region/vendor
- `update()` triggers rolling restart with brief downtime
- Secrets are write-only (never returned by API)
|- Delete is irreversible

## Entry 4: AutoTrain Advanced — No-Code LLM Fine-Tuning
**Date:** 2026-07-23
**Topic:** `hf-autotrain-advanced` — AutoTrain Advanced for zero-code LLM fine-tuning with SFT, DPO, ORPO, and Reward modeling

### Key Takeaways

1. **What AutoTrain Advanced is** — A Python package (`autotrain-advanced`) and Space-based platform that enables fine-tuning LLMs without writing training code. Supports local training and HF Spaces infrastructure.

2. **Six trainer types** — `llm` (generic), `llm-sft` (supervised fine-tuning), `llm-reward` (reward modeling), `llm-dpo` (Direct Preference Optimization), `llm-orpo` (Optimal Reward Policy Optimization), and `llm-sft-dev` (SFT with dev set).

3. **Data formats** — CSV and JSONL (JSONL preferred). For chatbot/QA data, use `content` + `role` columns (user/assistant/system). The `--chat-template` flag auto-formats data with templates: `none`, `zephyr`, `chatml`, or `tokenizer` (uses tok config).

4. **Length parameter constraints (critical)** — `block_size ≤ model_max_length`, `max_prompt_length ≤ model_max_length` AND `max_prompt_length ≤ block_size`, `max_completion_length ≤ model_max_length` AND `max_completion_length ≤ block_size`. Violating these produces NaN losses or errors.

5. **Training modes:**
   - **Local**: `autotrain --config config.yaml` — YAML config with model, data path, params, and HF hub push settings
   - **Spaces**: Same interface via HF Spaces UI — select model, dataset, splits, column mapping, then Start Training
   - **API**: `autotrain app --port 8000 --host 127.0.0.1` → REST API at `localhost:8000/docs` → POST `/api/create_project`

6. **Optimization knobs** — `--peft` (LoRA, default r=16, alpha=32, dropout=0.05), `--quantization int4/int8` (requires `--peft`), `--mixed_precision fp16/bf16`, `--use_flash_attention_2`, `--merge_adapter` to merge PEFT weights. `--auto_find_batch_size` finds optimal batch size automatically.

7. **Config-driven DPO/ORPO example:**
   ```yaml
   task: llm-orpo
   base_model: meta-llama/Meta-Llama-3-8B-Instruct
   data:
     path: argilla/distilabel-capybara-dpo-7k-binarized
     chat_template: chatml
     column_mapping:
       text_column: chosen
       rejected_text_column: rejected
       prompt_text_column: prompt
   params:
     block_size: 1024
     model_max_length: 8192
     epochs: 3
     lr: 3e-5
     peft: true
     quantization: int4
   hub:
     push_to_hub: true
   ```

8. **Final model options** — Can push to Hub automatically after training (`push_to_hub: true`), merge LoRA adapter into base model (`--merge_adapter`), and publish with full model card.

### Commands Reference
```bash
# Install
pip install autotrain-advanced

# Local training via config
autotrain --config config.yaml

# Run API server
autotrain app --port 8000 --host 127.0.0.1

# API: create training project
curl -X POST "http://127.0.0.1:8000/api/create_project" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer hf_XXXXX" \
  -d '{
    "task": "llm:orpo",
    "base_model": "meta-llama/Meta-Llama-3-8B-Instruct",
    "hub_dataset": "argilla/distilabel-capybara-dpo-7k-binarized",
    "hardware": "spaces-a10g-large",
    "params": {
      "block_size": 1024, "epochs": 1,
      "peft": true, "quantization": "int4"
    }
  }'

# CLI direct training with all params
autotrain llm-sft \
  --model meta-llama/Meta-Llama-3-8B-Instruct \
  --data-path ./my_data \
  --block_size 1024 \
  --epochs 3 \
  --lr 3e-5 \
  --peft --quantization int4 \
  --push-to-hub
```

### Pitfalls
- `--quantization` requires `--peft` (QLoRA pattern)
- NaN losses usually mean length params are out of order (see constraint chain above)
- DPO/ORPO need `prompt` column in addition to `text`/`chosen` and `rejected_text`/`rejected`
- The API server runs locally; Spaces training is the same config but uses the Space's hardware
- `model_max_length` default is 1024 — easy to forget to increase for long-context models
---

## Entry 2: Hub Upload Strategies (2026-07-24)

**Topic:** `hf-hub-upload-strategies` — Deep dive into uploading files, folders, and large models to the HF Hub.

### Quick Reference

| Method | Use When | Command/Code |
|--------|----------|-------------|
| `hf upload` | Single file or small folder (ad-hoc) | `hf upload user/repo ./file.ext` |
| `hf upload-large-folder` | Resumable upload of >1 GB model dir | `hf upload-large-folder user/repo ./dir/` |
| `HfApi.upload_file()` | Single file from Python | `api.upload_file("local", "remote", "user/repo")` |
| `HfApi.upload_folder()` | Folder from Python | `api.upload_folder(folder_path="./dir", repo_id="user/repo")` |
| `HfApi.create_commit()` | Atomic multi-file update | `api.create_commit(operations=[...], message="...")` |
| `HfApi.upload_large_folder()` | Resumable large folder from Python | `api.upload_large_folder(folder_path="./dir", repo_id="user/repo")` |
| `hf_transfer` (Rust) | Speed up files >5 GB | `pip install hf_transfer` + `export HF_HUB_ENABLE_HF_TRANSFER=1` |
| Xet backend | Dedup for iterative releases | `pip install huggingface-hub[hf_xet]` + `export HF_STORAGE_BACKEND=xet` |

### Key Insights
- **Resumable uploads** use a `.hfupload` manifest file to track chunk progress
- **`upload_folder` respects `.gitignore`** — override with `ignore_patterns`
- **Xet deduplication** stores content by hash; only new bytes are transferred on update
- **`hf_transfer`** and **Xet** optimize different layers — don't enable both simultaneously
- **Atomic commits** via `create_commit` guarantee all-or-nothing updates
- Always **validate after upload** with `api.repo_info()` or `api.list_repo_tree()`

See main reference at `skills/references/hf-learnings.md` Entry 89 for the full deep dive.
