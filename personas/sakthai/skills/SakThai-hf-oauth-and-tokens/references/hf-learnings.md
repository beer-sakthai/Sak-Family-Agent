# HF Learnings — Cumulative Reference

---

## Entry 145: Fine-Grained Token Presets — Deep Dive (2026-07-24)
**Date:** 2026-07-24
**Topic:** `hf-token-presets-fine-grained-tokens-v3` — Fine-grained token preset system added Jul 14, 2026

### What Changed

On **Jul 14, 2026**, Hugging Face introduced **Token Presets** — a curated UI for creating fine-grained access tokens with pre-configured permission sets. Instead of manually fine-tuning individual permissions, users pick a preset that selects the appropriate scope group automatically.

### The Five Presets

| Preset | Token Role | Intended Use | Typical Permissions |
|--------|-----------|-------------|-------------------|
| **Read-Only** | `fine-grained` | Download models, read datasets, inference on public/gated repos | Read access to repos, inference calls |
| **Inference** | `fine-grained` | Serverless inference calls via Inference Providers | Inference API access, no repo write |
| **Write** | `fine-grained` | Push models/datasets, update Spaces | Read + write to repos the user/org owns |
| **CI/CD** | `fine-grained` | Automated pipelines, GitHub Actions, GitLab CI | Write access scoped to specific repos, no user-level grants |
| **Full Access** | `write` | Personal dev workflows, complete access | Everything the user can do |

**Key design choice:** Only the Full Access preset uses the legacy `write` role. All other presets use the `fine-grained` role, which restricts scope to only what's needed.

### Linkable Preset URLs

Presets have URL query parameters, making them shareable:

```
# Direct to inference preset
https://huggingface.co/settings/tokens/new?preset=inference

# Read-only preset with organizations attached
https://huggingface.co/settings/tokens/new?preset=read-only&orgs=huggingface

# CI/CD preset (bind to specific repos)
https://huggingface.co/settings/tokens/new?preset=ci-cd
```

This is useful for:
- **Docs/onboarding guides** — link new contributors directly to the right token type
- **Scoped deployment guides** — "Create a token for inference via [this link](...)"

### How Presets Work Under the Hood

When a user selects a preset and clicks Create:
1. The UI pre-fills the permission scope toggles for that preset's curated set
2. Users can review the permissions summary before creating
3. Users can **switch to Custom** at any point to fine-tune further
4. Organization scoping is a single click (attach orgs)
5. The token is created with `fine-grained` role and the selected scopes

### Comparison with Pre-Preset Token Creation

| Aspect | Before (Jul 13) | After (Jul 14+) |
|--------|----------------|-----------------|
| UI | Manual permission toggles, no guidance | Preset selector with curated scopes |
| Token role | Choose read/write/fine-grained from dropdown | Preset auto-selects role |
| Org attachment | Multi-step | One-click on preset screen |
| Shareability | Not linkable | URL-based linking with `?preset=` |
| Error risk | Easy to over-scope or under-scope | Curated presets reduce mistakes |
| Customization | Always manual | Start from preset, then Custom if needed |

### Best Practices with Presets

1. **Inference preset for API keys** — Any token used solely for `huggingface_hub.inference_api` or Inference Providers should use the Inference preset. No repo write access = reduced blast radius.
2. **Read-Only for CI read access** — If a CI pipeline only needs to download gated models or read private datasets, use Read-Only (not CI/CD, which grants write).
3. **CI/CD for publishing pipelines** — Use CI/CD preset when your pipeline pushes models, datasets, or Spaces. Pair with Trusted Publishers for keyless OIDC auth.
4. **Always attach orgs** — Fine-grained tokens scoped to an org provide the smallest blast radius. If the token leaks, only that org's resources are at risk.
5. **Review before save** — Even with presets, review the permissions summary. The Inference preset grants inference access across all providers the org/user has access to.

### Token Management Policies (Team/Enterprise) — Updated

The Jul 14 release also reinforced these existing policies:

| Policy | Behaviour |
|--------|-----------|
| **Admin approval required** | Fine-grained tokens scoped to an org enter `pending` state until an admin approves |
| **Auto-approval for admins** | Token creators who are org admins skip the pending state |
| **Denied tokens** | Cannot access org resources (403). Token still works for non-org resources. Can be re-approved later without creating a new token. |
| **Revoked tokens** | Permanent. Must delete and recreate. 403 with message: "Your token has been revoked by the organization administrator." |
| **Fine-grained-only policy** | Orgs can require all tokens to be fine-grained; read/write tokens get 403 on org resources. |

### Resources

- Changelog: https://huggingface.co/changelog/token-presets
- Token settings: https://huggingface.co/settings/tokens
- Token creation (inference preset): https://huggingface.co/settings/tokens/new?preset=inference
- Token creation (read-only preset): https://huggingface.co/settings/tokens/new?preset=read-only
- Hub docs — User Access Tokens: https://huggingface.co/docs/hub/en/security-tokens
- Trusted Publishers docs: https://huggingface.co/docs/hub/en/security-trusted-publishers

---

## Entry 1: Transformers Pipeline API — Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-transformers-pipeline-api` — Complete reference on the Transformers `pipeline()` API

### Overview

The `pipeline()` function is Transformers' monolithic inference API. It abstracts tokenizer, model, and post-processing into a single callable. Two pipeline classes exist:

- **`Pipeline`** (generic): wraps any supported task. Created via `pipeline(task="...")`.
- **Task-specific pipelines**: e.g. `TextClassificationPipeline`, `AutomaticSpeechRecognitionPipeline`. Use task identifiers to instantiate via `pipeline()`.

### Full List of Supported Tasks (v5.14.0)

| Task string | Pipeline class | Modality |
|-------------|----------------|----------|
| `"audio-classification"` | AudioClassificationPipeline | Audio |
| `"automatic-speech-recognition"` | AutomaticSpeechRecognitionPipeline | Audio |
| `"depth-estimation"` | DepthEstimationPipeline | CV |
| `"document-question-answering"` | DocumentQuestionAnsweringPipeline | Multimodal |
| `"feature-extraction"` | FeatureExtractionPipeline | NLP |
| `"fill-mask"` | FillMaskPipeline | NLP |
| `"image-classification"` | ImageClassificationPipeline | CV |
| `"image-feature-extraction"` | ImageFeatureExtractionPipeline | CV |
| `"image-segmentation"` | ImageSegmentationPipeline | CV |
| `"image-text-to-text"` | ImageTextToTextPipeline | Multimodal |
| `"keypoint-matching"` | KeypointMatchingPipeline | CV |
| `"mask-generation"` | MaskGenerationPipeline | CV |
| `"object-detection"` | ObjectDetectionPipeline | CV |
| `"table-question-answering"` | TableQuestionAnsweringPipeline | NLP |
| `"text-classification"` (alias: `"sentiment-analysis"`) | TextClassificationPipeline | NLP |
| `"text-generation"` | TextGenerationPipeline | NLP |
| `"text-to-audio"` (alias: `"text-to-speech"`) | TextToAudioPipeline | Audio |
| `"token-classification"` (alias: `"ner"`) | TokenClassificationPipeline | NLP |
| `"video-classification"` | VideoClassificationPipeline | CV |
| `"visual-question-answering"` | VisualQuestionAnsweringPipeline | Multimodal |
| `"zero-shot-classification"` | ZeroShotClassificationPipeline | NLP |
| `"zero-shot-image-classification"` | ZeroShotImageClassificationPipeline | CV |
| `"zero-shot-audio-classification"` | ZeroShotAudioClassificationPipeline | Audio |
| `"zero-shot-object-detection"` | ZeroShotObjectDetectionPipeline | CV |

### Key Constructor Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `task` | `str` | Task identifier from the table above. Required unless `model` already defines its task on the Hub. |
| `model` | `str` or `PreTrainedModel` | Model ID (e.g. `"google/gemma-2-2b"`) or a loaded model instance. If omitted, uses task default. |
| `tokenizer` | `str` or `PreTrainedTokenizer` | Auto-loaded from model if omitted. |
| `feature_extractor` | `str` or `FeatureExtractionMixin` | Required for audio/vision models. Auto-loaded if omitted. |
| `image_processor` | `str` or `BaseImageProcessor` | For vision models. Auto-loaded if omitted. |
| `processor` | `str` or `ProcessorMixin` | For multimodal models. Auto-loaded if omitted. |
| `device` | `int` or `str` | `-1` = CPU (default), `0` = first GPU, `"mps"` = Apple Silicon, `"cuda:1"` etc. |
| `device_map` | `str` or `dict` | `"auto"` lets Accelerate distribute across devices. Mutually exclusive with `device`. |
| `dtype` | `torch.dtype` or `str` | `torch.float16`, `"auto"`, `torch.bfloat16` for half-precision. |
| `batch_size` | `int` | Batch size for streaming inference via DataLoader. Disabled by default. |
| `trust_remote_code` | `bool` | Allow custom code from Hub repos. Default `False`. Security-sensitive. |
| `use_fast` | `bool` | Use Fast tokenizer if available. Default `True`. |
| `revision` | `str` | Branch/tag/commit ID for model on Hub. Default `"main"`. |
| `token` | `str` or `bool` | HF auth token for gated models. `True` uses cached token from `hf auth login`. |
| `model_kwargs` | `dict` | Extra kwargs passed to `from_pretrained()` (e.g. `quantization_config`). |

### Code Patterns

**Basic usage:**
```python
from transformers import pipeline

pipe = pipeline("text-classification")
pipe("This restaurant is awesome")
# [{'label': 'POSITIVE', 'score': 0.9998743534088135}]
```

**List/batch input:**
```python
pipe(["This restaurant is awesome", "This restaurant is awful"])
# [{'label': 'POSITIVE', 'score': 0.9998743534088135},
#  {'label': 'NEGATIVE', 'score': 0.9996669292449951}]
```

**Specific model (task auto-detected from model card):**
```python
pipe = pipeline(model="FacebookAI/roberta-large-mnli")
```

**GPU with half-precision:**
```python
pipe = pipeline("text-generation", model="google/gemma-2-2b",
                device=0, dtype=torch.float16)
```

**device_map auto for large models + quantization:**
```python
from transformers import BitsAndBytesConfig

pipe = pipeline(
    model="google/gemma-7b",
    dtype=torch.bfloat16,
    device_map="auto",
    model_kwargs={"quantization_config": BitsAndBytesConfig(load_in_8bit=True)}
)
```

**Streaming over large datasets with Dataset + KeyDataset:**
```python
from transformers.pipelines.pt_utils import KeyDataset
import datasets

dataset = datasets.load_dataset("stanfordnlp/imdb", split="unsupervised")
pipe = pipeline("text-classification", device=0)
for out in pipe(KeyDataset(dataset, "text"), batch_size=8, truncation="only_first"):
    print(out)
```

**Generator/iterator for infinite data:**
```python
def data():
    for i in range(1000):
        yield f"My example {i}"

pipe = pipeline(model="openai-community/gpt2", device=0)
for out in pipe(data()):
    print(out[0]["generated_text"])
```

**Task-specific parameters — ASR with word timestamps:**
```python
pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")
pipe("https://example.com/audio.flac", return_timestamps="word")
# Returns chunks with (start, end) timestamps per word
```

**Text generation with multiple sequences:**
```python
pipe = pipeline("text-generation", model="openai-community/gpt2")
pipe("the secret is", num_return_sequences=4, return_full_text=False)
```

### Batch Inference Rules of Thumb

1. **Measure, measure, measure** — real numbers on your hardware/data are the only way.
2. **Don't batch** if latency-constrained (live product).
3. **Don't batch** on CPU.
4. **Don't batch** if sequence_length is unpredictable (risk of OOM).
5. **Do batch** if sequence_length is regular — push until OOM.
6. Larger GPUs benefit more from batching.
7. Always include OOM recovery when batching.

### Chunk Batching (ChunkPipeline)

Used by `zero-shot-classification` and `question-answering` where single inputs may trigger multiple forward passes. The pipeline handles this transparently:

```python
# Internal flow for ChunkPipeline:
all_model_outputs = []
for preprocessed in pipe.preprocess(inputs):
    model_outputs = pipe.model_forward(preprocessed)
    all_model_outputs.append(model_outputs)
outputs = pipe.postprocess(all_model_outputs)
```

You can still use `batch_size` independently — the pipeline batches within chunks.

### Custom Pipelines

Subclass any task-specific pipeline:

```python
class MyPipeline(TextClassificationPipeline):
    def postprocess(self, model_outputs, **kwargs):
        scores = super().postprocess(model_outputs, **kwargs)
        # Custom logic
        for item in scores:
            item['score'] *= 100
        return scores

my_pipe = MyPipeline(model=model, tokenizer=tokenizer)
# Or via pipeline():
my_pipe = pipeline(model="xxx", pipeline_class=MyPipeline)
```

### Key Insights

- **pipeline() auto-loads everything**: model, tokenizer, feature extractor, image processor, processor — whichever is needed for the task.
- **No GPU during first call with device_map="auto"**: Accelerate determines device layout at call time. Model loading happens once.
- **FP16 works on PyTorch backend only**: inputs are auto-converted to float16 internally.
- **Custom code on Hub**: `trust_remote_code=True` enables custom modeling files. Only use for repos you trust.
- **The `task` parameter is optional if the model ID on the Hub already has a `pipeline_tag`** in its model card — `pipeline()` will auto-detect the task.

### References
- https://huggingface.co/docs/transformers/en/main_classes/pipelines
- https://huggingface.co/docs/transformers/en/pipeline_tutorial

---

## Entry 2: Gradio Python Client — Programmatic Space API Access
**Date:** 2026-07-23
**Topic:** `hf-gradio-client-python` — Complete reference on the `gradio_client` Python SDK

### Overview

The `gradio_client` library lets you call any Gradio app's API from Python — including all Hugging Face Spaces. Install via `pip install gradio-client`. The central class is `gradio_client.Client` which connects to a remote Gradio app and exposes its endpoints as callable methods.

### Constructor

```python
from gradio_client import Client

client = Client("abidlabs/whisper-large-v2")       # HF Space
client = Client("https://bec81a83-5b5c-471e.gradio.live")  # Share URL
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `src` | `str` | HF Space name (user/repo) or full Gradio app URL |
| `token` | `str \| None` | HF token for private Spaces (default: locally saved token) |
| `max_workers` | `int` | Thread workers for concurrent requests (default: 40) |
| `verbose` | `bool` | Print statements to console (default: True) |
| `auth` | `tuple[str,str] \| None` | HTTP basic auth for the app |
| `httpx_kwargs` | `dict \| None` | Extra kwargs for httpx (timeouts, proxies, etc.) |
| `headers` | `dict \| None` | Additional HTTP headers per request |
| `download_files` | `str \| Path \| Literal[False]` | Dir for downloaded output files (default: GRADIO_TEMP_DIR or /tmp/gradio) |
| `ssl_verify` | `bool` | Skip cert validation for self-signed certs (default: True) |
| `analytics_enabled` | `bool` | Basic telemetry (default: True) |

### Core Methods

**`client.predict(*args, api_name=None, fn_index=None, headers=None) -> Any`**

Blocking call — sends one request and returns the result directly.

```python
result = client.predict(
    "test.mp4",
    api_name="/predict"
)
# >> "What a nice recording!"
```

**`client.submit(*args, api_name=None, fn_index=None, headers=None) -> Job`**

Non-blocking — returns a `Job` object that runs in a background thread.

```python
job = client.submit("hello", api_name="/predict")
job.result()  # blocking — waits for completion
# >> 49

# Job also supports status tracking:
job.status()  # -> JobStatus(stage="complete", ...)
```

**`client.view_api(return_format="dict") -> dict`**

Discovers all API endpoints, their inputs, and outputs. When `return_format="dict"`, returns a parsed dictionary instead of printing.

```python
info = client.view_api(return_format="dict")
for endpoint in info["named_endpoints"]:
    print(endpoint, "→", info["named_endpoints"][endpoint]["parameters"])
```

**`client.duplicate(src, token, private=True, hardware="cpu-basic", timeout=5) -> Client`**

Duplicates a Space under your account and returns a new Client connected to it. If the duplicate already exists, reconnects to it.

```python
new_client = Client.duplicate(
    "user/space-name",
    token="hf_...",
    private=False,
    hardware="t4-small"
)
```

**Client instance also has:**
- `client.config` — app configuration as a dict
- `client.api_name` / `client.fn_index` — for apps with a single endpoint, set once and omit from predict/submit

### File Handling

The Gradio API expects files as `FileData` objects (pre-v1) or simple file references. The client handles file uploads automatically:

```python
# Files passed as paths are auto-uploaded
result = client.predict("/path/to/image.jpg", api_name="/predict")

# Remote URLs also work
result = client.predict("https://example.com/audio.mp3", api_name="/predict")
```

The `download_files` constructor parameter controls where output files land (set to `False` to get `FileData` objects instead).

### Version 1 Release (major changes)

- **Simplified API** — no more `__call__()` magic, explicit `predict()`/`submit()`/`view_api()`/`duplicate()`
- **`handle_file()` utility** in the JS/TS client for consistent file handling across local paths, URLs, Blobs, and Buffers
- **Space duplication** via `Client.duplicate()` with optional hardware, timeout, and privacy settings
- **Status tracking** via `Job` objects with queue position, ETA, and progress data
- **Queue-aware** — automatically handles Spaces with queue systems, including position feedback
- **Zero GPU Spaces support** — client can connect to Spaces running on free ZeroGPU hardware

### Key Insights

- `predict()` is blocking and best for simple req/res; `submit()` returns a `Job` that can be polled, cancelled, or awaited — use it for long-running or streaming endpoints.
- The client auto-discovers endpoints via the Gradio app's underlying `/info` route — `view_api()` is the user-facing wrapper.
- Authentication for private Spaces uses the locally cached HF token by default, or an explicitly passed `token`.
- `max_workers=40` means up to 40 concurrent requests by default — tune down for rate-limited Spaces.
- The `duplicate()` method is zero-cost for public Spaces under the free tier — ideal for testing forks.
- Output files default to system temp dir; pass a persistent path to keep them or `False` to work with remote file references.
- The client works with any Gradio app (5.x, 6.x) — the API is backward-compatible across Gradio versions.

### References
- https://www.gradio.app/docs/python-client/client
- https://www.gradio.app/docs/python-client/introduction
- https://www.gradio.app/docs/python-client/version-1-release

---

## Entry 3: `hf` CLI — Complete Command Reference
**Date:** 2026-07-23
**Topic:** `hf-cli-complete-reference` — Full command suite for the `huggingface_hub` CLI tool (v1.23.0)

### Overview

The `hf` CLI is the official command-line interface for Hugging Face Hub operations. Installed via `pip install huggingface_hub[cli]` or standalone installer. On this machine: `/opt/data/.local/bin/hf` (symlink → venv). Version: **1.23.0**. Logged in as **Nanthasit**.

All commands support `--format` (auto/human/agent/json/quiet) and `--json`/`-q` shorthands. The `--format agent` mode is optimised for AI agent consumption.

### Command Tree

```
hf
├── auth          # Authentication management
├── buckets       # Object storage (buckets) operations
├── cache         # Local cache management
├── collections   # Hub collections CRUD
├── cp            # Copy files between local/repos/buckets
├── datasets      # Dataset Hub interactions
├── discussions   # Discussions & PRs on repos
├── download      # Download files from Hub
├── endpoints     # Inference Endpoints (dedicated)
├── env           # Environment diagnostics
├── extensions    # Third-party hf CLI extensions
├── jobs          # Run & manage remote Jobs
├── models        # Model Hub interactions
├── papers        # Daily papers on the Hub
├── repos         # Repository management
├── sandbox       # Remote sandbox execution
├── skills        # HF marketplace skills for AI assistants
├── spaces        # Space management
├── sync          # Bucket ↔ local rsync-style sync
├── upload        # Upload files to Hub
├── upload-large-folder  # [Deprecated]
├── webhooks      # Webhook management
└── version       # Version info
```

### Detailed Command Reference

#### `hf auth` — Authentication
| Subcommand | Purpose |
|------------|---------|
| `list` (`ls`) | List all stored access tokens |
| `login` | Login via browser or `--token`; supports `--add-to-git-credential` |
| `logout` | Logout from a token by name (`--token-name`) |
| `switch` | Switch between saved tokens (`--token-name`) |
| `token` | Print current token to stdout |
| `whoami` | Show current user identity; supports `--format json` |

**Key patterns:**
- `hf auth login --token $HF_TOKEN --add-to-git-credential` — one-shot login + git setup
- `hf auth whoami --format json` — machine-readable identity
- `hf auth list` — see all stored tokens

#### `hf buckets` — Object Storage
| Subcommand | Purpose |
|------------|---------|
| `cp` | Copy files between local, repos, and buckets via `hf://buckets/namespace/name/` URIs |
| `create` | Create a bucket (`--private`, `--region us\|eu`) |
| `delete` | Delete a bucket |
| `info` | Get bucket metadata |
| `list` (`ls`) | List buckets or bucket contents |
| `move` | Rename/move a bucket |
| `remove` (`rm`) | Remove files from a bucket |
| `sync` | Rsync-style sync between local dir and bucket |

**URI pattern:** `hf://buckets/namespace/bucket_name(/prefix)`

#### `hf cache` — Local Cache
| Subcommand | Purpose |
|------------|---------|
| `list` (`ls`) | List cached repos/revisions |
| `prune` | Remove detached revisions + incomplete downloads |
| `rm` | Remove specific cached repos/revisions |
| `verify` | Verify checksums for a cached repo revision |

**Key pattern:** `hf cache prune` — periodic cache cleanup to reclaim disk space.

#### `hf collections` — Hub Collections
| Subcommand | Purpose |
|------------|---------|
| `add-item` | Add a model/dataset/space to a collection |
| `create` | Create a new collection with a title |
| `delete` | Delete a collection |
| `delete-item` | Remove an item by object ID |
| `info` | Get collection details |
| `list` (`ls`) | List collections |
| `update` | Update collection metadata (title, description) |
| `update-item` | Update item note by object ID |

**Pattern:** `hf collections add-item username/my-collection moonshotai/kimi-k2 model`

#### `hf cp` — Universal Copy
Copies between local paths, repos (`hf://username/repo`), buckets (`hf://buckets/...`), and stdin/stdout (`-`).

- **Local → Repo:** `hf cp ./model.safetensors hf://username/my-model/`
- **Repo → Local:** `hf cp hf://username/my-model/config.json ./config.json`
- **Stdin → Bucket:** `hf cp - hf://buckets/username/my-bucket/config.json`
- **Repo → Bucket (same region):** `hf cp hf://username/source-model/ hf://buckets/username/dest-bucket/`

**Pitfall:** Remote-to-remote only works within the same storage region. Directory copies must use `hf upload`/`hf download` for repos or `hf buckets sync` for buckets.

#### `hf datasets` — Dataset Hub
| Subcommand | Purpose |
|------------|---------|
| `card` | Get dataset README |
| `info` | Get dataset metadata |
| `leaderboard` | List model scores from a dataset leaderboard |
| `list` (`ls`) | List datasets or dataset files; supports `--sort`, `--limit` |
| `parquet` | List parquet file URLs for a dataset |
| `sql` | Execute DuckDB SQL against dataset parquet URLs |

**Power pattern:**
```bash
hf datasets sql "SELECT COUNT(*) AS rows FROM read_parquet('https://huggingface.co/api/datasets/cfahlgren1/hub-stats/parquet/models/train/0.parquet')"
```
This enables zero-download SQL querying of any dataset's Parquet files.

#### `hf discussions` — Discussions & PRs
| Subcommand | Purpose |
|------------|---------|
| `close` | Close discussion/PR (#N) |
| `comment` | Comment on discussion/PR |
| `create` | Create discussion/PR with `--title` |
| `diff` | Show PR diff |
| `edit` | Edit existing comment (by comment ID) |
| `info` | Get discussion/PR details |
| `list` (`ls`) | List discussions on a repo |
| `merge` | Merge a PR |
| `rename` | Rename discussion/PR |
| `reopen` | Reopen closed discussion/PR |

**Pattern:** `hf discussions create username/my-model --title "Add training script" --type pr`

#### `hf download` — File Downloads
| Flag | Purpose |
|------|---------|
| `--type`, `--repo-type` | model / dataset / space |
| `--revision` | Branch, tag, or commit |
| `--include` | Glob patterns to include |
| `--exclude` | Glob patterns to exclude |
| `--cache-dir` | Custom cache directory |
| `--local-dir` | Download to specific directory (not cache) |
| `--force-download` | Re-download even if cached |
| `--dry-run` | Preview without downloading |
| `--max-workers` | Parallel download threads (default: 8) |
| `--format` | Output format: auto/human/agent/json/quiet |

**Patterns:**
```bash
hf download meta-llama/Llama-3.2-1B-Instruct
hf download meta-llama/Llama-3.2-1B-Instruct config.json tokenizer.json
hf download meta-llama/Llama-3.2-1B-Instruct --include "*.safetensors" --exclude "*.bin"
hf download meta-llama/Llama-3.2-1B-Instruct --local-dir ./models/llama
hf download hf://datasets/HuggingFaceH4/ultrachat_200k
```

**Key insight:** `--local-dir` places files directly in the specified directory (no symlinks). `--max-workers` defaults to 8 — increase for many small files.

#### `hf endpoints` — Inference Endpoints (Dedicated)
| Subcommand | Purpose |
|------------|---------|
| `catalog` | Browse endpoint hardware catalog (GPUs) |
| `delete` | Delete an endpoint permanently |
| `deploy` | Deploy an endpoint from a Hub repo |
| `describe` | Get endpoint info |
| `list` (`ls`) | List all endpoints for namespace |
| `pause` | Pause endpoint (stop billing) |
| `resume` | Resume a paused endpoint |
| `scale-to-zero` | Scale endpoint to zero replicas |
| `update` | Update endpoint config (`--min-replica`, etc.) |

**Note:** Inference Endpoints are a **paid service**. Always check cost before deploying.

#### `hf jobs` — Remote Computation
| Subcommand | Purpose |
|------------|---------|
| `cancel` | Cancel a job |
| `hardware` | List available hardware for jobs |
| `inspect` | Detailed job info |
| `labels` | Set labels on a job |
| `list` (`ls`, `ps`) | List jobs |
| `logs` | Fetch job logs |
| `run` | Run a job (e.g., `hf jobs run python:3.12 python -c 'print("Hello!")'`) |
| `scheduled` | Manage scheduled jobs |
| `ssh` | SSH into a running job |
| `stats` | Resource usage metrics |
| `uv` | Run UV scripts with inline deps on HF infra |
| `wait` | Wait for job completion |

**Key pattern:** `hf jobs uv` — run Python scripts with inline dependencies on HF infrastructure. Free tier available for lightweight jobs.

#### `hf models` — Model Hub
| Subcommand | Purpose |
|------------|---------|
| `card` | Get model card README |
| `info` | Get model metadata |
| `list` (`ls`) | List models or model files; supports `--sort downloads --limit 10` |

#### `hf papers` — Daily Papers
| Subcommand | Purpose |
|------------|---------|
| `info` | Get paper info by arXiv ID |
| `list` (`ls`) | List daily papers |
| `read` | Read paper markdown |
| `search` | Search papers by query |

**Pattern:** `hf papers read 2601.15621` — renders full paper as terminal-friendly markdown.

#### `hf repos` — Repository Management
| Subcommand | Purpose |
|------------|---------|
| `branch` | Manage branches |
| `cp` | Copy files (same as `hf cp`) |
| `create` | Create a new repo |
| `delete` | Delete repo |
| `delete-files` | Delete files from repo |
| `duplicate` | Duplicate a repo (cross-type) |
| `list` (`ls`) | List all repos with storage info |
| `move` | Move repo to another namespace |
| `settings` | Update repo settings (`--private`, `--license`, etc.) |
| `tag` | Manage repo tags |

**Pattern:** `hf repos duplicate openai/gdpval --type dataset` — duplicate across repo types.

#### `hf sandbox` — Remote Sandboxes
| Subcommand | Purpose |
|------------|---------|
| `cp` | Copy files between local and sandbox |
| `create` | Create a sandbox VM |
| `exec` | Run command, streaming output |
| `kill` | Terminate sandboxes |
| `pool` | Warm pools of host VMs for cheap shared sandboxes |
| `process` | List/stop background processes in sandbox |
| `spawn` | Start long-running background process |

**Note:** `hf sandbox create` creates a VM. Free tier available but limited. `hf sandbox pool` for cheaper shared sandboxes.

#### `hf skills` — AI Assistant Skills
| Subcommand | Purpose |
|------------|---------|
| `add` | Install a skill from HF marketplace |
| `list` (`ls`) | List available marketplace skills |
| `preview` | Preview generated SKILL.md |
| `update` | Update installed skills |

#### `hf spaces` — Space Management
| Subcommand | Purpose |
|------------|---------|
| `card` | Get Space README |
| `dev-mode` | Enable/disable dev mode |
| `hardware` | List available Space hardware |
| `hot-reload` | Hot-reload a Python file remotely |
| `info` | Get Space info |
| `list` (`ls`) | List spaces or space files |
| `logs` | Fetch run/build logs |
| `pause` | Pause a Space |
| `restart` | Restart a Space |
| `search` | Semantic search for spaces |
| `secrets` | Manage secrets |
| `settings` | Update Space settings (e.g., `--sleep-time 300`) |
| `ssh` | SSH into dev mode container |
| `templates` | List Space templates |
| `variables` | Manage environment variables |
| `volumes` | Manage volumes |
| `wait` | Wait for Space to finish building |

**Key patterns:**
```bash
hf spaces hardware                        # List GPU options & pricing
hf spaces logs username/my-space          # Debug build/runtime issues
hf spaces settings username/my-space --sleep-time 300  # Auto-sleep after 5 min idle
hf spaces secrets username/my-space       # List secrets (names only, values hidden)
hf spaces wait username/my-space          # CI-ready: blocks until Space is live
```

#### `hf webhooks` — Webhook Management
| Subcommand | Purpose |
|------------|---------|
| `create` | Create webhook (`--url`, `--watch model:bert-base-uncased`) |
| `delete` | Delete a webhook |
| `disable` | Disable without deleting |
| `enable` | Re-enable a disabled webhook |
| `info` | Get webhook details |
| `list` (`ls`) | List all webhooks |
| `update` | Update webhook config (`--url`, `--watch`) |

#### `hf sync` — Bucket Sync
Rsync-style bidirectional sync between local directories and buckets. Supports `--delete`, `--dry-run`, `--include`/`--exclude`, `--plan` (save to JSONL), `--apply` (apply plan).

```bash
hf sync ./local-data hf://buckets/username/my-bucket/data/ --dry-run
hf sync hf://buckets/username/my-bucket/data/ ./local-data --delete
```

#### `hf extensions` — Third-Party Extensions
| Subcommand | Purpose |
|------------|---------|
| `exec` | Execute installed extension |
| `install` | Install from public GitHub repo |
| `list` (`ls`) | List installed extensions |
| `remove` (`rm`) | Remove extension |
| `search` | Search GitHub for `hf-extension`-tagged repos |
| `update` | Update extensions |

**Security note:** Extensions run as arbitrary code. Only install from trusted sources.

### Global Format Options

All commands support these formatting flags:
- `--format auto` — picks `agent` or `human` based on terminal detection
- `--format human` — colorful human-readable tables
- `--format agent` — structured plain-text for AI agents
- `--format json` — machine-readable JSON output
- `--format quiet` (`-q`) — one ID per line, for piping
- `--no-truncate` — prevent truncation of scalar values in tables

### Key Insights

1. **`hf cp` is the universal Swiss Army knife** — handles local, repo, and bucket paths in one command with stdin/stdout support.
2. **`--format json` is your agent friend** — pipe through `jq` for programmatic access to any Hub resource.
3. **`hf datasets sql`** brings zero-download SQL analytics to any dataset's Parquet files — incredibly powerful for data exploration without GBs of downloads.
4. **`hf jobs uv`** is the most accessible free compute option on HF — runs Python with inline deps on HF infrastructure.
5. **`hf cache prune`** should run periodically to reclaim disk — detached revisions accumulate over time.
6. **`hf spaces wait`** is CI-friendly — blocks until a Space finishes building, perfect for deployment pipelines.
7. **HF URIs** (`hf://`) are the universal addressing scheme: models, datasets, spaces, buckets, and even individual files all addressed via `hf://namespace/repo-name` or `hf://buckets/namespace/bucket-name`.
8. **The `hf auth` suite supports multiple tokens** — `hf auth list` / `hf auth switch` / `hf auth logout --token-name` for multi-account workflows.
9. **`hf papers read`** renders full academic papers as terminal markdown — skimming ML papers never leaves the terminal.

### References
- Official CLI docs: https://huggingface.co/docs/huggingface_hub/en/guides/cli
- HuggingFace Hub Python library docs: https://huggingface.co/docs/huggingface_hub/en/index
|- CLI reference (package): https://huggingface.co/docs/huggingface_hub/package_reference/cli

---

## Entry 4: Vision-Language Models (VLMs) on Hugging Face — Qwen2-VL, PaliGemma2, and the image-text-to-text Pipeline
**Date:** 2026-07-23
**Topic:** `hf-vlm-vision-language-models-hub` — Complete reference on Vision-Language Models via the Transformers pipeline and Hub

### Overview

Vision-Language Models (VLMs) process both images/video and text, generating text responses grounded in visual content. Hugging Face supports VLMs through the `image-text-to-text` pipeline task in Transformers (v5.14.0+). Major model families:

| Model Family | Developer | Pipeline | Parameters | License | Downloads |
|---|---|---|---|---|---|
| **Qwen2-VL** | Qwen (Alibaba) | `image-text-to-text` | 2B, 7B, 72B | Apache-2.0 | 1.4M+ (7B) |
| **PaliGemma2** | Google | `image-text-to-text` | 3B | Gemma | 100K+ |
| **Idefics3** | Hugging Face | `image-text-to-text` | 8B | Apache-2.0 | — |
| **LLaVA-NeXT** | Community | `image-text-to-text` | 7B, 13B | Apache-2.0 | — |

### Qwen2-VL Architecture

Qwen2-VL (`Qwen2VLForConditionalGeneration`) is a decoder-only vision-language model with these components:

- **Vision encoder**: A Vision Transformer (ViT) with 675M parameters, processes images at native resolution (no fixed resize — supports dynamic resolution)
- **Vision-language connector**: A single-layer cross-attention module (not MLP), more parameter-efficient than LLaVA-style connectors
- **Language backbone**: Qwen2 decoder, sharing token embeddings with the vision connector
- **Dynamic resolution**: Images are not resized to a fixed grid — the model processes them at their native aspect ratio, making it especially good for documents and high-resolution images
- **Video support**: Processes videos natively via frame sampling — up to 256 frames per video

**Key token IDs** (Qwen2-VL specific):
```python
image_token_id = 151655      # placeholder for input images
video_token_id = 151656      # placeholder for input video
vision_start_token_id = 151652  # marks start of visual segment
vision_end_token_id = 151653    # marks end of visual segment
```

### Usage via Transformers Pipeline

**Single image inference:**
```python
from transformers import pipeline
from PIL import Image
import requests

pipe = pipeline("image-text-to-text", model="Qwen/Qwen2-VL-7B-Instruct")
url = "https://example.com/cat.jpg"
image = Image.open(requests.get(url, stream=True).raw)

messages = [
    {"role": "user", "content": [
        {"type": "image"},
        {"type": "text", "text": "What is in this image?"}
    ]}
]
output = pipe(text=messages, max_new_tokens=128)
print(output[0]["generated_text"])
```

**Multi-image with labels:**
```python
messages = [
    {"role": "user", "content": [
        {"type": "text", "text": "Compare these two images:"},
        {"type": "image"},  # first image
        {"type": "image"},  # second image
        {"type": "text", "text": "What are the similarities?"}
    ]}
]
output = pipe(text=messages, max_new_tokens=256)
```

### Direct Model Usage (Lower-Level)

For precise control over image preprocessing and generation:

```python
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
import torch

model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    torch_dtype=torch.bfloat16,
    device_map="auto",
    attn_implementation="flash_attention_2"  # requires flash-attn installed
)
processor = AutoProcessor.from_pretrained("Qwen/Qwen2-VL-7B-Instruct")

conversation = [
    {"role": "user", "content": [
        {"type": "image", "image": "https://example.com/photo.jpg"},
        {"type": "text", "text": "Describe this image in detail."}
    ]}
]

# processor handles image preprocessing + chat template
inputs = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
    tokenize=True,
    return_tensors="pt"
).to(model.device)

output_ids = model.generate(**inputs, max_new_tokens=256)
response = processor.decode(output_ids[0], skip_special_tokens=True)
```

### Key Parameters

| Parameter | Effect |
|---|---|
| `attn_implementation="flash_attention_2"` | 2-4x speedup on compatible GPUs (Ampere+, H100, etc.) — requires `pip install flash-attn` and `torch.float16`/`torch.bfloat16` |
| `torch_dtype=torch.bfloat16` | Half-precision, halves memory usage. Required for Flash Attention 2. |
| `device_map="auto"` | Distributes large models across multiple GPUs/CPU via Accelerate |
| `max_new_tokens` | Controls generation length (128-512 typical for VLM tasks) |
| `add_vision_id=True` | In chat template, labels images as "Picture 1: ...", "Picture 2: ..." for referencing |
| `do_sample=True/False` | Sampling vs greedy decoding for generation |

### Video Understanding

Qwen2-VL processes video by extracting frames (up to 256 frames default):

```python
messages = [
    {"role": "user", "content": [
        {"type": "video", "video": "https://example.com/video.mp4"},
        {"type": "text", "text": "Summarize what happens in this video."}
    ]}
]
output = pipe(text=messages, max_new_tokens=256)
```

The model handles key events, temporal reasoning, and multi-frame analysis out of the box.

### Hub Integration

All major VLMs are discoverable on the Hub via:
- Pipeline tag: `image-text-to-text`
- Task filter: https://huggingface.co/models?pipeline_tag=image-text-to-text
- All models use `pipeline("image-text-to-text")` — unified API regardless of the VLM family
- Model cards include `pipeline_tag: "image-text-to-text"` and `library_name: "transformers"`

**Inference API support:** Qwen2-VL and PaliGemma2 are both deployable via HF Inference Endpoints (paid) and serverless Inference API (free tier available for select models). Check the model's `endpoints_compatible` tag on the Hub.

### Flash Attention 2 Prerequisite

```bash
pip install -U flash-attn --no-build-isolation
```

Only works with `torch.float16` or `torch.bfloat16`. On non-GPU environments, omit `attn_implementation` — the model falls back to eager attention.

### Key Insights

1. **The `image-text-to-text` pipeline is the unified VLM API** — same `pipeline()` call works across Qwen2-VL, PaliGemma2, Idefics3, and LLaVA-NeXT. Model swapping is trivial.
2. **Qwen2-VL's dynamic resolution is unique** — no fixed resize grid means it can read documents, dense text, and fine details better than fixed-resolution VLMs.
3. **Multi-image conversations require the chat template** — the `processor.apply_chat_template()` method handles all the special tokens (<|vision_start|>, <|image_pad|>, <|vision_end|>) automatically.
4. **Flash Attention 2 dramatically speeds inference** — 2-4x faster on compatible hardware. Always try it first on GPU.
5. **Zero-download model discovery** — use the Hub API (`/api/models?pipeline_tag=image-text-to-text`) or `hf models list --pipeline image-text-to-text` to find all VLMs without downloading.

### References
- Qwen2-VL docs: https://huggingface.co/docs/transformers/en/model_doc/qwen2_vl
- Pipeline API: https://huggingface.co/docs/transformers/en/main_classes/pipelines
- PaliGemma2 docs: https://huggingface.co/docs/transformers/en/model_doc/paligemma2
- Qwen2-VL on Hub: https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct
- VLM models by task: https://huggingface.co/models?pipeline_tag=image-text-to-text
- Flash Attention 2: https://github.com/Dao-AILab/flash-attention

---
## Entry 48: HF PEFT DoRA — Weight-Decomposed Low-Rank Adaptation
**Date:** 2026-07-23
**Topic:** `hf-peft-dora-deep-dive` — DoRA: Weight-Decomposed Low-Rank Adaptation in HF PEFT

### What is DoRA
DoRA (arXiv:2402.09353) decomposes pre-trained weights into magnitude and direction components. Direction is fine-tuned via standard LoRA; magnitude gets a separate learnable scalar per module. This improves LoRA quality, especially at low ranks (rank 8 difference > rank 64 difference).

### Usage
- `LoraConfig(use_dora=True)` — single flag, everything else same as LoRA
- `LoraRuntimeConfig(ephemeral_gpu_offload=True)` — speeds up CPU-offloaded DoRA adapters
- `PeftModel.from_pretrained(..., ephemeral_gpu_offload=True)` — load with offload
- `DoraCaching` context manager (`from peft.helpers import DoraCaching`) — eval-mode speed boost at +41% memory cost

### Key facts
- Supported layers: **embedding, linear, Conv2d only**
- **Always merge for inference** (`merge_and_unload()`) — DoRA has significant overhead otherwise
- DoRA without caching: +139% time, +4% memory vs LoRA. With caching: +17% time, +41% memory
- QDoRA (quantized DoRA) works with bitsandbytes but has reported issues with DeepSpeed Zero2
- May need different hyperparameters than LoRA (slower convergence, better final quality)

---
## Entry 49: Chat Templates in Transformers
**Date:** 2026-07-23
**Topic:** `hf-chat-templates-deep-dive` — Chat templates: Jinja2-based message formatting for chat models

### Core Concept
Chat templates are **Jinja2 templates** stored in a tokenizer's `chat_template` attribute (saved in `chat_template.jinja`). They define how a list of `{role, content}` messages is converted into a single token sequence for a causal LM. Every chat model has one — different models use different control tokens (e.g., `[INST]`/`[/INST]` for Mistral, `<|user|>`/`<|assistant|>` for Zephyr).

### `apply_chat_template()` API
```python
# Basic — returns formatted string
tokenizer.apply_chat_template(chat, tokenize=False)

# Tokenize directly (safer — avoids duplicate special tokens)
tokenizer.apply_chat_template(chat, tokenize=True, add_generation_prompt=True, return_tensors="pt")

# Key params:
# - add_generation_prompt=True: appends tokens to signal assistant reply start
# - continue_final_message=True: removes EOS so model continues final message
# - tokenize=True: returns token IDs (avoids add_special_tokens=False pitfalls)
```

### Critical Flags
| Flag | Effect |
|------|--------|
| `add_generation_prompt` | Adds assistant-start tokens at end (default in TextGenerationPipeline) |
| `continue_final_message` | Removes EOS so model continues prefilled content (mutually exclusive with `add_generation_prompt`) |
| `add_special_tokens` | Must be `False` if formatting first then tokenizing later |

### Prefilling Pattern
Steer model completions by prefilling the start of the assistant response:
```python
chat = [
    {"role": "user", "content": "Format as JSON"},
    {"role": "assistant", "content": '{"name": "'},
]
formatted = tokenizer.apply_chat_template(chat, tokenize=True, return_dict=True, continue_final_message=True)
model.generate(**formatted)
```
For reasoning models, prefill a named field:
```python
continue_final_message="reasoning_content"  # Qwen — keeps reasoning block open
continue_final_message="thinking"           # Gemma — keeps thinking block open
```

### Writing Custom Templates
- Template variables: `messages` (list), `add_generation_prompt` (bool), `tools` (list of JSON schemas), tokenizer special tokens by name (`bos_token`, `eos_token`)
- Use Jinja `{%- ... -%}` (with `-`) to strip whitespace — extra whitespace harms model performance
- Callables: `raise_exception(msg)` and `strftime_now(format_str)`
- **Multimodal**: set template on **processor**, not tokenizer. Use `<|image|>`/`<|video|>` placeholder tokens
- **Tool-calling**: handle `tool_calls` key on assistant messages, `tool` role responses, and `tools` variable for definitions
- **Cross-language compat**: use Jinja filters (`|lower`, `|trim`, `|tojson`) instead of Python methods; use `true`/`false`/`none` not `True`/`False`/`None`

### Viewing & Contributing
```python
tokenizer.chat_template                          # view current template
open("template.jinja", "w").write(tokenizer.chat_template)  # save to file
tokenizer.chat_template = open("template.jinja").read()     # load edited template
tokenizer.push_to_hub("user/model", commit_message="Add chat template", create_pr=True)
```

### Training with Templates
Set `add_generation_prompt=False` during training — assistant prompt tokens aren't needed in training data.
```python
dataset = dataset.map(lambda x: {"formatted_chat": tokenizer.apply_chat_template(x["chat"], tokenize=False, add_generation_prompt=False)})
```

### Key Insights
1. **Always prefer `tokenize=True`** in `apply_chat_template` — the `add_special_tokens=False` pitfall is easy to miss when formatting manually first.
2. **`continue_final_message` is the prefilling mechanism** — use it to guide model output without overwriting the full assistant response.
3. **Custom templates are contributed via PRs** — open a PR on any model repo to add a missing/correct template. The standard API ensures tool-calling and RAG templates are portable.
4. **Multimodal templates live on the processor** — different lifecycle from text-only templates. The processor replaces placeholder tokens with actual image/video token sequences after template rendering.

### References
- Chat templating guide: https://huggingface.co/docs/transformers/en/chat_templating
- Writing custom templates: https://huggingface.co/docs/transformers/en/chat_templating_writing
- Jinja2 template docs: https://jinja.palletsprojects.com/en/stable/templates/
- Tool-calling templates: https://huggingface.co/docs/transformers/en/chat_extras

---
## Entry 50: vLLM — Hugging Face Integration Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-vllm-integration-deep-dive` — vLLM's seamless integration with Hugging Face Hub for LLM serving

### Overview
vLLM is a high-performance LLM inference and serving engine originally from UC Berkeley's Sky Computing Lab. It downloads models from Hugging Face Hub by default, supporting 200+ model architectures including Llama, Qwen, Gemma, DeepSeek-V3, Mixtral, LLaVA, Pixtral, and embedding models like ColBERT. Its HF integration goes far beyond simple model loading.

### Loading models from HF Hub
```python
from vllm import LLM, SamplingParams

# Auto-download from HF Hub — model name is a Hub repo ID
llm = LLM(model="Qwen/Qwen2.5-1.5B-Instruct")
# Or a local path
llm = LLM(model="/path/to/model")
# From ModelScope
# export VLLM_USE_MODELSCOPE=True
```
- vLLM reads and respects `config.json`, `tokenizer_config.json`, and `generation_config.json` from the HF repo
- By default, it applies the model creator's recommended sampling params from `generation_config.json`
- To use vLLM defaults instead: `LLM(model=..., generation_config="vllm")`
- Chat templates from HF tokenizer are used for `llm.chat()` calls

### Architecture: LLM class (offline) vs vllm serve (online)
- **Offline**: `LLM` class — initialize engine, call `.generate()` or `.chat()`
- **Online**: `vllm serve <model>` — starts an OpenAI-compatible server at port 8000
  - Drop-in replacement for OpenAI API: same `/v1/completions`, `/v1/chat/completions`, `/v1/models` endpoints
  - Can be queried via `curl`, `openai` Python client, or any OpenAI-compatible tool

### Key HF integration features
1. **Auto-chat-template**: `llm.chat()` applies the HF chat template from `tokenizer_config.json` automatically
2. **LoRA adapter loading**: vLLM loads LoRA adapters from HF Hub via `--lora-modules`
3. **Quantization presets**: Works with HF-quantized models (AWQ, GPTQ, GGUF, bitsandbytes)
4. **Multimodal**: Supports LLaVA, Qwen-VL, Pixtral etc — images passed alongside text
5. **Pooling models**: Embedding, classification, reward models loaded from HF Hub
6. **`hf_hub_resolver` plugin**: A dedicated LoRA resolver that fetches adapters from HF Hub on demand

### PagedAttention (core innovation)
vLLM's PagedAttention manages KV cache in fixed-size blocks (pages), eliminating fragmentation that plagues naive concatenation. This enables:
- **~2-4x higher throughput** vs traditional Transformers inference
- **Near-zero wasted memory** from KV cache fragmentation
- **Copy-on-write** for shared prefixes (beam search, parallel sampling)

### Serving via Hugging Face Inference Endpoints
vLLM is the default serving backend for HF Inference Endpoints (custom container). Users can:
1. Upload a `Dockerfile` to a Space
2. Deploy the Space as an Inference Endpoint
3. vLLM handles the GPU backend automatically

### Quantization support
vLLM loads quantized models from HF Hub with automatic detection:
- FP8, MXFP8/MXFP4, NVFP4 — native vLLM quant formats
- INT8, INT4 — via AWQ/GPTQ (loaded from HF repos)
- GGUF — for llama.cpp quantized models
- bitsandbytes — for on-the-fly quantization
- compressed-tensors, ModelOpt, TorchAO — additional formats

### Distributed inference
vLLM supports tensor, pipeline, data, expert, and context parallelism out of the box. Models from HF Hub are automatically sharded across GPUs with a single `--tensor-parallel-size N` flag.

### Speculative decoding
- **EAGLE/EAGLE3** — draft model loaded from HF Hub alongside the main model
- **N-gram, suffix** — no extra model needed
- **DFlash, MTP** — advanced speculative techniques

### Key Insights
1. **vLLM is the fastest HF-compatible serving engine** — PagedAttention + continuous batching beats vanilla Transformers by 2-4x in throughput
2. **Drop-in OpenAI replacement** — point any existing OpenAI client at vLLM's server endpoint
3. **200+ architectures supported** — most HF decoder models work without code changes
4. **LoRA serving without restart** — dynamic LoRA adapter loading via `hf_hub_resolver`
5. **Same code for offline + online** — the `LLM` class works identically in scripts and notebooks

### References
- vLLM docs: https://docs.vllm.ai/en/latest/
- Quickstart: https://docs.vllm.ai/en/latest/getting_started/quickstart.html
- Supported models: https://docs.vllm.ai/en/latest/models/supported_models.html
- vLLM paper (PagedAttention): https://arxiv.org/abs/2309.06180
- HF Inference Endpoints + vLLM: https://huggingface.co/docs/inference-endpoints/en/index
- GitHub: https://github.com/vllm-project/vllm

## Entry 8: AWQ (Activation-aware Weight Quantization) — Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-awq-quantization-deep-dive` — AWQ 4-bit quantization with Transformers

### Overview
AWQ (Activation-aware Weight Quantization) is a 4-bit weight-only quantization method that preserves model quality by protecting ~1% of "salient" weights based on activation magnitude. Unlike GPTQ (group-wise equalization), AWQ scales weights per-channel using activation statistics rather than applying post-quantization rounding corrections. This makes AWQ faster at prefill while maintaining competitive accuracy.

### Installation
```bash
pip install autoawq
```
**Known issue:** AutoAWQ currently downgrades Transformers to v4.47.1. After installing, reinstall your target Transformers version if needed.

### Identifying AWQ models
Check `quantization_config.quant_method` in the model's `config.json` on the Hub:
```json
{
  "quantization_config": {
    "quant_method": "awq",
    "zero_point": true,
    "group_size": 128,
    "bits": 4,
    "version": "gemm"
  }
}
```

### Loading for inference
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "TheBloke/zephyr-7B-alpha-AWQ",
    dtype=torch.float32,          # other weights mapped to fp16 by default
    device_map="cuda:0"
)
```
Combine with FlashAttention2 for additional speed (but NOT compatible with fused modules — see below):
```python
model = AutoModelForCausalLM.from_pretrained(
    "TheBloke/zephyr-7B-alpha-AWQ",
    attn_implementation="flash_attention_2",
    device_map="cuda:0"
)
```

### Fused modules (performance boost)
Fused AWQ modules (supported for Llama and Mistral architectures) merge the AWQ linear layers and scaling factors into single GPU kernels, giving ~2× decode throughput and ~10% lower VRAM.

```python
from transformers import AwqConfig, AutoModelForCausalLM

quantization_config = AwqConfig(
    bits=4,
    fuse_max_seq_len=512,
    do_fuse=True,
)
model = AutoModelForCausalLM.from_pretrained(
    "TheBloke/Mistral-7B-OpenOrca-AWQ",
    quantization_config=quantization_config
).to(0)
```

**Benchmarks (Mistral-7B, batch=1, seq_len=2048):**
| Metric | Unfused | Fused | Improvement |
|--------|---------|-------|-------------|
| Decode throughput | ~35 tok/s | ~89 tok/s | ~2.5× |
| Peak VRAM | 5.73 GB | 5.57 GB | ~3% less |
| Prefill throughput | ~2927 tok/s | ~2715 tok/s | Slightly lower |

**Limitations:** Fused modules CANNOT be combined with FlashAttention2.

### ExLlamaV2 kernels
For even faster prefill and decoding, install the latest AutoAWQ from source and set `version="exllama"`:
```python
quantization_config = AwqConfig(version="exllama")
model = AutoModelForCausalLM.from_pretrained(
    "TheBloke/Mistral-7B-Instruct-v0.1-AWQ",
    quantization_config=quantization_config,
    device_map="auto",
)
```
ExLlamaV2 is also supported on AMD GPUs.

### Key differences from bitsandbytes quantization
| Feature | AWQ (autoawq) | bitsandbytes (8/4-bit) |
|---------|---------------|----------------------|
| Weight format | 4-bit only (int4) | 8-bit (int8) or 4-bit (nf4/fp4) |
| Quantization | Offline (pre-quantized model) | Online (load-time quantization) |
| Inference speed | Fast (native kernels) | Slower (HuggingFace Linear4bit) |
| Model availability | Pre-quantized on Hub | Quantize any model at load time |
| GPU requirement | CUDA GPU | CUDA GPU |

### Resources
- HF docs: https://huggingface.co/docs/transformers/en/quantization/awq
- AutoAWQ repo: https://github.com/casper-hansen/AutoAWQ
- AWQ paper: https://arxiv.org/abs/2306.00978
- Colab notebook: https://colab.research.google.com/drive/1HzZH89yAXJaZgwJDhQj9LqSBux932BvY

---

## Entry 5: Custom Model Integration on Hugging Face Hub — Full Workflow
**Date:** 2026-07-23
**Topic:** `hf-custom-model-integration` — Creating, registering, uploading, and loading custom model architectures on the Hub

### Overview

Hugging Face Transformers supports custom model architectures that live outside the library's source code. Users can share models that use novel architectures (not natively supported in Transformers) by uploading the modeling code alongside the weights. Loading requires `trust_remote_code=True`.

The full workflow has four stages:
1. **Configuration** — define a `PretrainedConfig` subclass with a unique `model_type`
2. **Model** — define the `PreTrainedModel` subclass(es)
3. **AutoClass registration** — register with `AutoConfig`, `AutoModel`, and task-specific `AutoModelFor*` classes
4. **Upload to Hub** — push code + weights, enabling `from_pretrained("user/model")` for anyone

### Stage 1: Configuration Class

Every custom model needs a configuration class inheriting from `PretrainedConfig`. The `model_type` attribute is the unique identifier and must differ from all existing Transformers model types.

```python
from transformers import PretrainedConfig

class ResnetConfig(PretrainedConfig):
    model_type = "resnet"  # MUST be unique — check against existing types

    def __init__(
        self,
        block_type="bottleneck",
        stem_width=64,
        stem_type="",
        avg_down=False,
        **kwargs,
    ):
        self.block_type = block_type
        self.stem_width = stem_width
        self.stem_type = stem_type
        self.avg_down = avg_down
        super().__init__(**kwargs)
```

**Convention:** Save in `configuration_<model_type>.py` (e.g. `configuration_resnet.py`).

### Stage 2: Model Class

Define the model by subclassing `PreTrainedModel`. Set `config_class` to the configuration class. Implement `__init__` using the config object and a `forward` method.

```python
from transformers import PreTrainedModel
import torch.nn as nn

class ResnetModel(PreTrainedModel):
    config_class = ResnetConfig  # Links model to its config

    def __init__(self, config):
        super().__init__(config)
        # Build architecture from config fields
        self.conv1 = nn.Conv2d(3, config.stem_width, kernel_size=7, stride=2)
        # ... rest of architecture
        self.pool = nn.AdaptiveAvgPool2d((1, 1))

    def forward(self, pixel_values, labels=None):
        # Forward pass
        x = self.conv1(pixel_values)
        # ...
        return {"logits": x}
```

**For task-specific output heads**, create a subclass:

```python
class ResnetModelForImageClassification(ResnetModel):
    config_class = ResnetConfig

    def __init__(self, config):
        super().__init__(config)
        self.classifier = nn.Linear(config.stem_width, config.num_labels)

    def forward(self, pixel_values, labels=None):
        outputs = super().forward(pixel_values)
        logits = self.classifier(outputs["logits"])
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels)
        return {"loss": loss, "logits": logits}
```

**Convention:** Save in `modeling_<model_type>.py` (e.g. `modeling_resnet.py`).

**Critical rule when copying from Transformers source:** Replace all relative imports at the top of the `modeling.py` file with imports from the `transformers` package. Relative imports like `from ...modeling_utils import ...` will fail when the code lives outside the library.

### Stage 3: AutoClass Registration

Register the custom config and model with the AutoClass API so `AutoModel.from_pretrained()` works:

```python
from transformers import AutoConfig, AutoModel, AutoModelForImageClassification

AutoConfig.register("resnet", ResnetConfig)
AutoModel.register(ResnetConfig, ResnetModel)
AutoModelForImageClassification.register(ResnetConfig, ResnetModelForImageClassification)
```

**Rules:**
- The first argument to `AutoConfig.register()` must match `model_type` in the config class
- The first argument to `AutoModel.register()` must be the config class (not the model type string)
- Register task-specific classes for each supported task — pick the appropriate `AutoModelFor*` class

### Stage 4: Upload to Hub

**Directory structure required in the repo:**

```
.
└── resnet_model/
    ├── __init__.py          # Can be empty, enables Python module resolution
    ├── configuration_resnet.py
    └── modeling_resnet.py
```

**Using `register_for_auto_class()` for automatic JSON mapping:**

Before uploading, call `register_for_auto_class()` on the config and models. This writes an `auto_map` field into the saved `config.json`:

```python
ResnetConfig.register_for_auto_class()
ResnetModel.register_for_auto_class("AutoModel")
ResnetModelForImageClassification.register_for_auto_class("AutoModelForImageClassification")
```

**The `auto_map` JSON structure in `config.json`:**

```json
{
  "auto_map": {
    "AutoConfig": "<your-repo-name>--<config-class-name>",
    "AutoModel": "<your-repo-name>--<model-class-name>",
    "AutoModelForImageClassification": "<your-repo-name>--<model-class-name>"
  }
}
```

**Upload:**

```python
model.push_to_hub("custom-resnet50d")
# Pushes: config.json, model.safetensors, modeling_resnet.py,
#         configuration_resnet.py, __init__.py
```

### Loading a Custom Model

Users load the model with `trust_remote_code=True`:

```python
from transformers import AutoModelForImageClassification

model = AutoModelForImageClassification.from_pretrained(
    "username/custom-resnet50d",
    trust_remote_code=True  # REQUIRED for custom architectures
)
```

**Why `trust_remote_code=True` is required:** Transformers does not bundle the custom model's code. The Hub stores `modeling_*.py` and `configuration_*.py` alongside the weights. Without this flag, Transformers refuses to load/execute arbitrary Python from the Hub (security measure). Always instruct users to verify the code is from a trusted source before setting this.

### Updating the `auto_map` Manually

If a model needs to support multiple tasks, edit `auto_map` in `config.json` directly:

```json
{
  "auto_map": {
    "AutoConfig": "custom-resnet50d--ResnetConfig",
    "AutoModel": "custom-resnet50d--ResnetModel",
    "AutoModelForImageClassification": "custom-resnet50d--ResnetModelForImageClassification",
    "AutoModelForObjectDetection": "custom-resnet50d--ResnetModelForObjectDetection"
  }
}
```

### Loading Pretrained Weights from External Libraries

Before uploading, you can load pretrained weights from external libraries (e.g. `timm`, `torchvision`) and transfer them:

```python
import timm

# Create custom model
config = ResnetConfig(block_type="bottleneck", stem_width=32, stem_type="deep", avg_down=True)
model = ResnetModelForImageClassification(config)

# Load pretrained weights from timm
pretrained = timm.create_model("resnet50d", pretrained=True)
model.model.load_state_dict(pretrained.state_dict())
```

### Key Insights

1. **`model_type` must be globally unique** — check against all existing Transformers model types before choosing one. Conflicts cause silent loading errors.
2. **`trust_remote_code=True` is non-negotiable** — without it, Transformers refuses to execute custom modeling code. Always document this requirement.
3. **`register_for_auto_class()` is the easiest path** — it auto-generates `auto_map` in `config.json`, saving manual JSON editing.
4. **Relative imports from Transformers source must be replaced** — copying `modeling_llama.py` wholesale will fail because `from ...modeling_utils import ...` paths break outside the library.
5. **Custom models work with `device_map="auto"`** — Accelerate can still distribute layers across devices, as long as the custom code uses standard PyTorch.
6. **`push_to_hub()` uploads code files automatically** — any `.py` files in the same directory as the saved model are included in the upload.
7. **Gated repos and custom models** — combine gated access with `trust_remote_code=True` for production deployments (gate the repo, require token auth).

### References
- https://huggingface.co/docs/transformers/en/custom_models
- https://huggingface.co/docs/transformers/en/custom_models#autoclass
- https://huggingface.co/docs/transformers/en/custom_models#upload
- https://huggingface.co/docs/transformers/en/custom_models#loading-a-custom-model
- https://huggingface.co/docs/transformers/en/models#custom-models

## Entry 55: Hub Commit & Branch Management API — Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-hub-commit-api` — Complete reference on the Hugging Face Hub's commit, branch, and PR management API via the `huggingface_hub` Python library

### Overview

The `HfApi` class in `huggingface_hub` provides a comprehensive API for managing repositories on the Hugging Face Hub: creating/deleting repos, committing files, managing branches, and creating/merging pull requests. This entry covers the full lifecycle of Hub repo management.

### Repository Lifecycle

**`HfApi.create_repo(repo_id, token, private, visibility, repo_type, exist_ok, resource_group_id, region, space_sdk, space_hardware, space_storage, space_sleep_time, space_secrets, space_variables, space_volumes, space_template)`**

Creates a repo. Supports model, dataset, Space repos with full configuration. Returns a `RepoUrl` object.

Key parameters:
- `repo_id`: Namespace/name (e.g. `"user/my-model"`)
- `visibility`: `"public"`, `"private"`, or `"protected"`
- `exist_ok`: If `True`, no error if repo already exists
- Space-specific: `space_hardware`, `space_storage`, `space_sleep_time`, `space_secrets`, `space_variables`

**`HfApi.delete_repo(repo_id, token, repo_type, missing_ok)`** — Deletes a repo. Use `missing_ok=True` to avoid errors if already deleted.

**`HfApi.duplicate_repo(from_repo, to_repo, token, repo_type, private, visibility)`** — Duplicates a repo (models and Spaces only, not datasets). Copies files and configs.

**`HfApi.move_repo(from_repo, to_repo, token, repo_type)`** — Moves/renames a repo. Old URL becomes a redirect.

### Branch Management

**`HfApi.create_branch(repo_id, branch, revision=None, token=None, repo_type=None, exist_ok=False)`**
Creates a new branch from an optional revision. Set `exist_ok=True` to avoid errors if branch already exists.

**`HfApi.delete_branch(repo_id, branch, token=None, repo_type=None)`**
Deletes a branch from a repo.

**`HfApi.list_repo_refs(repo_id, token=None, repo_type=None, reverse=False, sort="last_modified")`**
Lists all branches and tags. Returns a `RepoRefs` object with `.branches` and `.converts` attributes (list of `BranchRef`/`TagRef`).

**`HfApi.list_repo_commits(repo_id, token=None, repo_type=None, revision=None, format=None, page_size=None)`**
Lists commits on a repo/branch with pagination support.

### Commit Operations

**`HfApi.create_commit(repo_id, operations, message, branch=None, parent=None, token=None, repo_type=None, run_as_future=False)`**
The core commit method. `operations` is a list of commit operation objects:

| Operation | Purpose | Constructor params |
|-----------|---------|-------------------|
| `CommitOperationAdd` | Upload a new file | `path_in_repo`, `path_or_fileobj` |
| `CommitOperationDelete` | Delete a file/folder | `path_in_repo` |
| `CommitOperationCopy` | Copy file within repo | `src_path`, `path_in_repo` |

Example — multi-file update:
```python
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete

api = HfApi()
api.create_commit(
    repo_id="username/my-model",
    operations=[
        CommitOperationAdd(path_in_repo="config.json", path_or_fileobj="config.json"),
        CommitOperationAdd(path_in_repo="model.safetensors", path_or_fileobj="model.safetensors"),
        CommitOperationDelete(path_in_repo="old_file.bin"),
    ],
    message="Update model and config, remove legacy file",
)
```

### High-Level Upload Methods

**`HfApi.upload_file(path_or_fileobj, path_in_repo, repo_id, token, repo_type, revision, run_as_future)`**
Uploads a single file. Simpler than create_commit for one-file changes.

**`HfApi.upload_folder(folder_path, path_in_repo, repo_id, token, repo_type, revision, ignore_patterns, run_as_future)`**
Uploads an entire folder. Supports `.gitignore`-style patterns via `ignore_patterns`.

**`HfApi.delete_file(path_in_repo, repo_id, token, repo_type, revision, commit_message)`**
Deletes a single file with an automatic commit message.

### Pull Requests

**`HfApi.create_pull_request(repo_id, title, token=None, description=None, repo_type=None)`**
Creates a Pull Request in **draft** status. Returns a `DiscussionWithDetails` object.

**`HfApi.merge_pull_request(repo_id, pr_number, token=None, repo_type=None)`**
Merges a pull request by its number.

PR workflow:
1. Create a branch: `api.create_branch(repo_id, "my-feature")`
2. Commit changes to the branch: `api.create_commit(repo_id, operations, branch="my-feature", message="...")`
3. Open PR: `api.create_pull_request(repo_id, "My feature", description="...")`
4. Merge: `api.merge_pull_request(repo_id, pr_number)`

### Repo Content Querying

**`HfApi.get_paths_info(repo_id, paths, token, repo_type, revision, expand)`**
Get metadata about specific file paths. `expand` can include `"blobs"`, `"lastCommit"`, `"security"`.

**`HfApi.repo_exists(repo_id, token, repo_type)`**
Check if a repo exists without downloading anything.

**`HfApi.get_repo(repo_id, token, repo_type)`**
Get full repo metadata (card data, siblings, etc.).

**`HfApi.update_repo_visibility(repo_id, private, token, repo_type)`**
Change repo visibility (public ↔ private).

### Pitfalls

1. **Draft PRs are not mergable until converted** — `create_pull_request` always creates draft PRs. Use the Hub web UI to mark them ready for review before merging.
2. **Branch names are case-sensitive** — the API treats `"MyFeature"` and `"myfeature"` as different branches.
3. **Commit operations are atomic** — either all operations in `create_commit` succeed or none do. No partial commits.
4. **`exist_ok` is your friend** — set to `True` on both `create_repo` and `create_branch` to make scripts idempotent.
5. **`upload_folder` respects `.gitignore`** — patterns from `.gitignore` in the source folder are applied unless overridden with `ignore_patterns`.

### References
- https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api
- https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions
- https://huggingface.co/docs/huggingface_hub/main/en/guides/upload
- https://huggingface.co/docs/huggingface_hub/main/en/guides/manage-branches

---
## Entry 56: Diffusers LoRA Training — Text-to-Image Personalization
**Date:** 2026-07-23
**Topic:** `hf-diffusers-lora-training` — Training and loading LoRA adapters with 🤗 Diffusers for text-to-image personalization

### Overview

LoRA (Low-Rank Adaptation) in Diffusers enables lightweight fine-tuning of diffusion models (SD1.5, SDXL, etc.) by inserting small trainable weight matrices into the UNet and/or text encoder. Only the LoRA layers train (~100MB output vs. multi-GB full checkpoints). Training is ~5 hours on a 2080 Ti (11GB VRAM) vs. days for full fine-tune.

LoRA is supported for: DreamBooth, Stable Diffusion XL, Kandinsky 2.2, text-to-image (SD1.5), and Wuerstchen.

### Training Script Architecture

Diffusers provides two canonical training scripts:
- `train_text_to_image_lora.py` — SD1.5/2.1 text-to-image LoRA
- `train_text_to_image_sdxl_lora.py` — SDXL LoRA (dual text encoder: CLIP-L + OpenCLIP-g/14)

**Prerequisites:**
```bash
git clone https://github.com/huggingface/diffusers
cd diffusers
pip install .
cd examples/text_to_image
pip install -r requirements.txt
```

### PEFT Integration

Diffusers uses `LoraConfig` from the PEFT library for LoRA setup:

```python
from peft import LoraConfig

unet_lora_config = LoraConfig(
    r=4,
    lora_alpha=8,
    init_lora_weights="gaussian",
    target_modules=["to_k", "to_q", "to_v", "to_out.0"],
)
unet.add_adapter(unet_lora_config)
lora_layers = filter(lambda p: p.requires_grad, unet.parameters())
```

**Key `LoraConfig` parameters:**

| Parameter | Purpose | Default |
|-----------|---------|---------|
| `r` (rank) | Inner dimension of low-rank matrices | 4 |
| `lora_alpha` | Scaling factor | 8 |
| `target_modules` | Which attention modules to inject LoRA into | `["to_k", "to_q", "to_v", "to_out.0"]` |
| `init_lora_weights` | Weight initialization | `"gaussian"` |

### Launching Training

**SD1.5 example (Naruto BLIP captions):**
```bash
export MODEL_NAME="stable-diffusion-v1-5/stable-diffusion-v1-5"
export DATASET_NAME="lambdalabs/naruto-blip-captions"
export OUTPUT_DIR="/sddata/finetune/lora/naruto"
export HUB_MODEL_ID="naruto-lora"

accelerate launch --mixed_precision="fp16" train_text_to_image_lora.py \
  --pretrained_model_name_or_path=$MODEL_NAME \
  --dataset_name=$DATASET_NAME \
  --lr_scheduler="cosine" \
  --output_dir=${OUTPUT_DIR} \
  --hub_model_id=${HUB_MODEL_ID} \
  --validation_prompt="A naruto with blue eyes." \
  --seed=1337
```

**SDXL:** Uses `train_text_to_image_sdxl_lora.py` with optional `--train_text_encoder` flag and `--learning_rate_text_encoder=5e-6`.

### Inference with Trained LoRAs

```python
from diffusers import AutoPipelineForText2Image
import torch

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
).to("cuda")
pipeline.load_lora_weights("path/to/lora/model", weight_name="pytorch_lora_weights.safetensors")
image = pipeline("A naruto with blue eyes").images[0]
```

### Adapter-Level Loading vs. Pipeline-Level

| Method | Scope | Use Case |
|--------|-------|----------|
| `pipeline.load_lora_weights()` | UNet + text encoder | Preferred — handles both combined and separate weight files |
| `pipeline.unet.load_lora_adapter()` | UNet only | When targeting a specific component |
| `unload_lora_weights()` | Full pipeline | Restore to base model weights |

### Adjusting LoRA Influence

**Global scale:**
```python
pipeline("prompt", cross_attention_kwargs={"scale": 0.5})  # 0=none, 1=full LoRA
```

**Per-layer scale via `set_adapters()`:**
```python
pipe.load_lora_weights(..., adapter_name="my_adapter")
scales = {
    "text_encoder": 0.5,
    "unet": {
        "down": 0.9,
        "up": {
            "block_0": 0.6,
            "block_1": [0.4, 0.8, 1.0],
        },
    },
}
pipe.set_adapters("my_adapter", scales)
```
Currently only attention weights support `set_adapters()`.

### Hotswapping LoRAs (v0.39+)

Hotswap avoids recompilation with `torch.compile` when switching adapters:
```python
pipe.enable_lora_hotswap()               # call before first adapter + compile
pipeline.load_lora_weights("adapter1", ...)
pipe.unet = torch.compile(pipe.unet, ...)
# Switch to another adapter without recompile:
pipeline.load_lora_weights("adapter2", hotswap=True, adapter_name="default_0")
```
`target_rank=max_rank` sets max rank across all swapable adapters (default 128). Not supported for text-encoder LoRAs.

### Loading Community LoRAs (Kohya / TheLastBen)

```python
pipeline.load_lora_weights("path/to/weights", weight_name="blueprintify-sd-xl-10.safetensors")
```
Limitations: LyCORIS checkpoints (Hada, LoKR) are not fully supported. Only LoRA and LoCon modules.

### Key Training Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--rank` | LoRA rank (higher = more params) | 4 |
| `--learning_rate` | LR for LoRA layers | 1e-4 |
| `--train_text_encoder` | Also train text encoder LoRA (SDXL) | False |
| `--mixed_precision` | fp16/bf16 for memory savings | no |
| `--lr_scheduler` | LR schedule type | constant |
| `--resolution` | Training image resolution | 512 (1024 for SDXL) |
| `--gradient_accumulation_steps` | Accumulate grads over N steps | 1 |

### Output Artifacts

Training produces `pytorch_lora_weights.safetensors` (~50-200MB) plus optional checkpoint dirs and validation images.

### References
- https://huggingface.co/docs/diffusers/main/en/training/lora
- https://huggingface.co/docs/diffusers/main/en/using-diffusers/loading_adapters
- https://huggingface.co/docs/peft/en/package_reference/lora

## Entry 57: Diffusers Scheduler Architecture — Complete Reference
**Date:** 2026-07-23
**Topic:** `hf-diffusers-schedulers-deep-dive` — Comprehensive guide to all Diffusers schedulers, their architecture, and usage patterns

### Overview

Diffusers schedulers are the mathematical core of the diffusion process. A scheduler takes a model's output (the denoising prediction) and a timestep to return a denoised sample. The timestep dictates where in the diffusion process the step is — data is generated by iterating forward `N` timesteps during training, and inference propagates backward through the timesteps.

All schedulers inherit from `SchedulerMixin` (which provides loading/saving via `from_pretrained()` / `save_pretrained()`) and `ConfigMixin` (which stores configuration as `scheduler.config.*`). The two broad categories are:

- **Discrete schedulers** — timestep is an `int` (e.g., DDPM, DDIM, DPM++ family)
- **Continuous schedulers** — timestep is a `float` (e.g., `ScoreSdeVeScheduler`, `ScoreSdeVpScheduler`)

### Base Classes

| Class | Role |
|-------|------|
| `SchedulerMixin` | Common loading/saving, `from_pretrained()`, `save_pretrained()`, `_compatibles` |
| `ConfigMixin` | Config storage (`scheduler.config.*`), JSON serialization |
| `SchedulerOutput` | Base output dataclass — `prev_sample` (x_{t-1}) torch.Tensor |
| `KarrasDiffusionSchedulers` | Umbrella enum for mainstream ODE/SDE-based schedulers inspired by k-diffusion |

### Core Methods (shared across scheduler types)

```python
scheduler.set_timesteps(num_inference_steps)     # Pre-compute the noise schedule
scheduler.scale_model_input(sample, timestep)     # Scale input for model compatibility
scheduler.step(model_output, timestep, sample)    # One denoising step → prev_sample
scheduler.add_noise(original_samples, noise, timesteps)  # Forward diffusion
```

### A1111 / k-diffusion ↔ Diffusers Mapping

This table maps the most common scheduler names from Automatic1111 / k-diffusion to their Diffusers counterparts:

| A1111 / k-diffusion | 🤗 Diffusers Class | Init Flags |
|---------------------|-------------------|------------|
| DPM++ 2M | `DPMSolverMultistepScheduler` | default |
| DPM++ 2M Karras | `DPMSolverMultistepScheduler` | `use_karras_sigmas=True` |
| DPM++ 2M SDE | `DPMSolverMultistepScheduler` | `algorithm_type="sde-dpmsolver++"` |
| DPM++ 2M SDE Karras | `DPMSolverMultistepScheduler` | `use_karras_sigmas=True, algorithm_type="sde-dpmsolver++"` |
| Euler | `EulerDiscreteScheduler` | default |
| Euler a | `EulerAncestralDiscreteScheduler` | default |
| Heun | `HeunDiscreteScheduler` | default |
| LMS | `LMSDiscreteScheduler` | default |
| LMS Karras | `LMSDiscreteScheduler` | `use_karras_sigmas=True` |
| DPM2 | `KDPM2DiscreteScheduler` | default |
| DPM2 a | `KDPM2AncestralDiscreteScheduler` | default |
| DDIM | `DDIMScheduler` | default |
| — | `UniPCMultistepScheduler` | default (4-step SOTA) |
| — | `DEISMultistepScheduler` | default |
| — | `LCMScheduler` | Latent Consistency Model |
| — | `TCDScheduler` | Trajectory Consistency Distillation |

### Noise Schedules & Sigma Types

| A1111 Type | Diffusers Init |
|------------|---------------|
| Karras | `use_karras_sigmas=True` |
| sgm_uniform | `timestep_spacing="trailing"` |
| simple | `timestep_spacing="trailing"` |
| exponential | `timestep_spacing="linspace", use_exponential_sigmas=True` |
| beta | `timestep_spacing="linspace", use_beta_sigmas=True` |

### Scheduler Family Deep-Dive

#### 1. DDPM (`DDPMScheduler`)
The original Denoising Diffusion Probabilistic Model scheduler. Adds Gaussian noise in a Markov chain forward process and learns to reverse it.

**Key parameters:**
- `beta_schedule`: `"linear"` (DDPM original), `"scaled_linear"` (SD1/2), `"squaredcos_cap_v2"` (cosine, SDXL)
- `variance_type`: `"fixed_small"` (default), `"fixed_large"`, `"learned"`, `"learned_range"`
- `prediction_type`: `"epsilon"` (predict noise), `"sample"` (predict x₀), `"v_prediction"` (predict velocity)
- `rescale_betas_zero_snr`: enables zero terminal SNR for very bright/dark sample generation

**Forward process — `add_noise()`:**
```python
noisy_samples = sqrt(α̅_t) · x₀ + sqrt(1 - α̅_t) · ε
```
where `α̅_t = ∏ᵢ₌₁ᵗ (1 - βᵢ)` and `ε ~ N(0, I)`

**Reverse process — `step()`:**
Performs one denoising step using the learned noise prediction ε_θ:
```python
x_{t-1} = (1 / √α_t) · (x_t - (β_t / √(1-α̅_t)) · ε_θ(x_t, t)) + σ_t · z
```
where `σ_t` is the variance schedule and `z ~ N(0, I)`.

#### 2. DDIM (`DDIMScheduler`)
Denoising Diffusion Implicit Models — non-Markovian deterministic sampling.

**Key difference from DDPM:** DDIM makes the reverse process deterministic (σ_t = 0), enabling:
- **Fast sampling** — can skip intermediate timesteps (e.g., 50 steps instead of 1000)
- **Deterministic generation** — same latent → same output (useful for inversion, interpolation)
- **Inversion** — `DDIMInverseScheduler` reverses the process for editing

```python
from diffusers import DDIMScheduler

scheduler = DDIMScheduler.from_pretrained("stabilityai/stable-diffusion-2-1", subfolder="scheduler")
scheduler.set_timesteps(num_inference_steps=50)
```

#### 3. DPM++ Family (`DPMSolverMultistepScheduler`)
The most widely used family for practical Stable Diffusion inference. Based on DPM-Solver++ (Lu et al., 2022), which solves the diffusion ODE analytically using exponential integrators.

**Key variants controlled by init args:**

| Setting | Effect |
|---------|--------|
| `solver_order=1` | 1st-order Euler-like (fast but lower quality) |
| `solver_order=2` | Default — best quality-speed trade-off for guided sampling |
| `solver_order=3` | Highest quality for unconditional sampling |
| `algorithm_type="dpmsolver++"` | Predicts x₀ instead of ε (default, handles high CFG better) |
| `algorithm_type="sde-dpmsolver++"` | Adds stochastic noise — better variety, slight quality boost |
| `use_karras_sigmas=True` | Karras noise schedule — sharper details, especially at low steps |
| `lower_order_final=True` | Switches to lower-order solver in final steps for stability (<15 steps) |
| `thresholding=True` | Dynamic thresholding (pixel-space models only) |

**Typical configurations:**
```python
# DPM++ 2M Karras (most popular)
DPMSolverMultistepScheduler(
    use_karras_sigmas=True,
    algorithm_type="dpmsolver++",
    solver_order=2,
    lower_order_final=True,
)

# DPM++ 2M SDE Karras (best quality, slightly slower)
DPMSolverMultistepScheduler(
    use_karras_sigmas=True,
    algorithm_type="sde-dpmsolver++",
    solver_order=2,
    lower_order_final=True,
)
```

#### 4. Euler (`EulerDiscreteScheduler`)
The simplest first-order ODE solver. Equivalent to DPM-Solver++ with `solver_order=1`.

- **Fastest** but lowest quality per step
- Good for previews or when speed is critical
- Non-ancestral (deterministic with fixed seed)

#### 5. Euler Ancestral (`EulerAncestralDiscreteScheduler`)
Euler with added stochastic noise. The "Euler a" in A1111.

- Adds Brownian motion noise at each step
- Produces slightly different outputs each time (even with same seed)
- Often preferred for creative generation

```python
EulerAncestralDiscreteScheduler()
```

#### 6. UniPC (`UniPCMultistepScheduler`)
A **training-free** predictor-corrector framework that achieves SOTA quality at extremely low step counts (4–10 steps).

**Architecture:**
- **UniP** (predictor): unified analytical form supporting arbitrary order
- **UniC** (corrector): applied after any solver to increase order of accuracy without extra model evaluations

**Recommended settings:**
```python
UniPCMultistepScheduler(
    solver_order=2,       # For guided (CFG) sampling
    # solver_order=3      # For unconditional sampling
    predict_x0=True,      # Enable x₀ prediction
    lower_order_final=True,
    disable_corrector=[], # Corrector enabled at all steps
)
```

**Performance:** 3.87 FID on CIFAR10 (unconditional), 7.51 FID on ImageNet 256×256 with only **10 function evaluations**.

#### 7. LCM (`LCMScheduler`)
Latent Consistency Models — distilled from pre-trained diffusion models for **1–4 step inference**.

- Requires a LoRA or full model fine-tuned with LCM distillation
- Works best with `guidance_scale=0` (no CFG)
- 1–4 steps vs 20–50 for standard schedulers

```python
from diffusers import LCMScheduler

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    scheduler=LCMScheduler.from_config(pipeline.scheduler.config),
)
```

#### 8. TCD (`TCDScheduler`)
Trajectory Consistency Distillation — similar to LCM but distilled along the PF-ODE trajectory rather than directly predicting the endpoint. Produces higher quality at 1–4 steps than LCM.

#### 9. KarrasVe (`KarrasVeScheduler`)
Implements the stochastic sampling from Karras et al. (2022) "Elucidating the Design Space of Diffusion-Based Generative Models" (EDM).

- Uses a continuous-time ODE/SDE formulation
- Churn-based sampling (adds and removes noise in progressive schedule)
- Best for pixel-space diffusion models (not latent-space)

### Practical Usage

#### Switching Schedulers at Inference Time

The recommended pattern — just swap the scheduler object:

```python
from diffusers import DPMSolverMultistepScheduler, EulerDiscreteScheduler

pipeline = AutoPipelineForText2Image.from_pretrained("sd-model")

# Switch to DPM++ 2M Karras
pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
    pipeline.scheduler.config,
    use_karras_sigmas=True,
    algorithm_type="dpmsolver++",
)

# Or Euler for speed
pipeline.scheduler = EulerDiscreteScheduler.from_config(pipeline.scheduler.config)
```

The `from_config()` call preserves the base model's noise schedule (betas, alpha-bars) while switching the ODE solver.

#### Scheduler Selection Guide

| Use Case | Recommended Scheduler | Steps |
|----------|----------------------|-------|
| Maximum quality, any steps | DPM++ 2M SDE Karras | 20–30 |
| Default quality-speed trade-off | DPM++ 2M Karras | 20–30 |
| Very fast (<10 steps) | UniPCMultistepScheduler | 4–10 |
| Real-time (1–4 steps) | LCMScheduler / TCDScheduler | 1–4 |
| Deterministic / inversion | DDIMScheduler | 50 |
| Fastest possible preview | EulerDiscreteScheduler | 10–20 |
| Creative / varied outputs | EulerAncestralDiscreteScheduler | 20–30 |
| High-quality pixel-space | KarrasVeScheduler | 30–40 |

### Advanced: Flow Matching Schedulers (v0.39+)

Recent versions add **flow-matching** schedulers for rectified flow models (e.g., Stable Diffusion 3, Flux):

- `FlowMatchEulerDiscreteScheduler` — Euler ODE solver for flow-matching models
- `FlowMatchHeunDiscreteScheduler` — 2nd-order Heun solver for higher quality

Flow-matching predicts the velocity field `v_t` rather than noise ε, with the forward process defined as a linear interpolation between noise and data:
```python
x_t = (1 - t) · x₀ + t · ε
```

### References
- https://huggingface.co/docs/diffusers/main/en/api/schedulers/overview
- https://huggingface.co/docs/diffusers/main/en/api/schedulers/dpmsolver_multistep
- https://huggingface.co/docs/diffusers/main/en/api/schedulers/ddpm
- https://huggingface.co/docs/diffusers/main/en/using-diffusers/schedulers
- Lu et al. "DPM-Solver++" (2022) — https://arxiv.org/abs/2211.01095
- Zhao et al. "UniPC" (2023) — https://arxiv.org/abs/2302.04867
- Karras et al. "EDM" (2022) — https://arxiv.org/abs/2206.00364

## Entry 57: GPTQ Quantization in Transformers — GPT-QModel Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-transformers-gptq-quantization` — AutoGPTQ replacement, GPTQConfig, Marlin kernel, and GPT-QModel

### Overview

GPTQ (GPT Post-Training Quantization) is a post-training quantization technique that compresses weights to **int4**, dequantizing them to fp16 on the fly during inference via a fused kernel. This yields **~4x memory savings** over fp16 while maintaining accuracy. Inference is also faster because lower-bitwidth weights take less time to communicate.

**Key paradigm shift (2026):** AutoGPTQ is **no longer supported** in Transformers. The actively maintained backend is **GPT-QModel** (`pip install gptqmodel`), originally forked from AutoGPTQ but now significantly diverged.

### Architecture: How GPTQ Works

1. **Layer-by-layer quantization:** Each row of the weight matrix is quantized independently to find a version that minimizes the squared error relative to the original weights.
2. **Hessian-based weight selection:** Uses the second-order information (Hessian of the loss w.r.t. weights) to determine which weights can be quantized with minimal accuracy loss.
3. **Optimal Brain Quantization (OBQ):** Iteratively quantizes weights, then compensates the error by adjusting the remaining un-quantized weights.
4. **Int4 storage, fp16 compute:** Dequantized inside a fused CUDA kernel, never exposing full fp16 weights in global memory.

### GPTQConfig — The Transformers API

```python
from transformers import AutoModelForCausalLM, AutoTokenizer, GPTQConfig

tokenizer = AutoTokenizer.from_pretrained("facebook/opt-125m")
gptq_config = GPTQConfig(bits=4, dataset="c4", tokenizer=tokenizer)

quantized_model = AutoModelForCausalLM.from_pretrained(
    "facebook/opt-125m",
    device_map="auto",
    quantization_config=gptq_config
)
```

**Key parameters:**
- `bits` (int): Quantization bitwidth (4 is standard, 3/2/8 also supported)
- `dataset` (str | list[str]): Calibration dataset. Default `"c4"` (Colossal Clean Crawled Corpus). Can pass a custom list of strings.
- `tokenizer`: Required to tokenize the calibration dataset
- `backend` (str): `"marlin"` for A100-optimized CUDA kernel (inference only, no quantization)
- `max_memory` (dict): Device memory limits for quantization
- `desc_act` (bool, default=True): Whether to quantize columns in order of decreasing activation norm (GPTQ paper's default). Set `False` for Marlin compatibility.
- `sym` (bool, default=False): Symmetric vs asymmetric quantization. GPT-QModel supports asymmetric (lower quantization error) while some kernels (e.g. legacy Marlin) require symmetric.

### Loading a Pre-quantized Model

```python
model = AutoModelForCausalLM.from_pretrained(
    "{your_username}/opt-125m-gptq",
    device_map="auto"
)
```

No need to pass `GPTQConfig` for reloading — the config is saved alongside the model in `quantize_config.json`.

### Saving & Sharing

```python
quantized_model.push_to_hub("opt-125m-gptq")
tokenizer.push_to_hub("opt-125m-gptq")
```

For local save, move to CPU first if `device_map` was used during quantization:
```python
quantized_model.to("cpu")
quantized_model.save_pretrained("opt-125m-gptq")
tokenizer.save_pretrained("opt-125m-gptq")
```

### Marlin Kernel

Marlin is a **4-bit only CUDA GPTQ kernel** optimized for NVIDIA A100 (Ampere architecture). It provides:

- Highly parallelized weight loading, dequantization, and execution
- Substantial inference speedup over the standard CUDA GPTQ kernel
- **Not** for model quantization — only for inference of already-quantized models

Activate via `GPTQConfig(bits=4, backend="marlin")`.

### GPT-QModel vs AutoGPTQ

| Feature | AutoGPTQ (legacy) | GPT-QModel (active) |
|---------|-------------------|---------------------|
| Status | Deprecated in Transformers | Actively maintained |
| Quantization | Supported | Supported (faster, lower memory) |
| Asymmetric quantization | Limited | Full support (lower error) |
| Multi-modal support | Limited | Qwen2-VL, Ovis1.6-VL |
| Platform support | Linux only | Linux, macOS, Windows 11 |
| Hardware support | NVIDIA CUDA | NVIDIA, AMD ROCm, Apple Silicon, Intel/AMD CPUs, Intel DC GPUs |
| Checkpoint compat | Legacy format | **Not** backward-compatible with AutoGPTQ |
| Marlin kernel | Original | Updated for A100 + auto-padding |

### Quantization Time Estimates

| Model Size | Hardware | Time |
|-----------|----------|------|
| 350M params | Google Colab (free GPU) | ~5 minutes |
| 175B params | NVIDIA A100 | ~4 hours |

### Memory Savings

| Precision | Size (7B model) | Throughput |
|-----------|-----------------|------------|
| fp16 | ~14 GB | Baseline |
| GPTQ int4 | ~3.5 GB | ~1.2-1.5x faster |

### Resources
- https://huggingface.co/docs/transformers/main/en/quantization/gptq — Transformers GPTQ guide
- https://github.com/ModelCloud/GPTQModel — GPT-QModel (1213★, 195 forks, Python)
- GPTQ paper: Frantar et al. "GPTQ: Accurate Post-Training Quantization for Generative Pre-trained Transformers" (2023) — https://arxiv.org/abs/2210.17323
- Marlin paper: Frantar et al. "Marlin: A Fast 4-bit Inference Kernel" (2024)

---

## Entry 60: Transformers DeepSpeed Integration — ZeRO Stages & Trainer
**Date:** 2026-07-23
**Topic:** `hf-transformers-deepspeed-integration` — Complete reference on using DeepSpeed ZeRO with the Transformers `Trainer` class

### Overview

DeepSpeed, powered by the Zero Redundancy Optimizer (ZeRO), eliminates memory redundancy across distributed training by sharding optimizer states, gradients, and parameters across GPUs. The Transformers `Trainer` class integrates DeepSpeed through the `deepspeed` argument, which accepts a JSON config file. Alternatively, use an Accelerate config file instead of TrainingArguments.

### ZeRO Stages

| Stage | Shards | Memory savings | Communication overhead |
|-------|--------|---------------|----------------------|
| **ZeRO-1** | Optimizer states only | Moderate | Low |
| **ZeRO-2** | Gradients + optimizer states | High | Moderate |
| **ZeRO-3** | Parameters + gradients + optimizer states | Highest | Highest |

ZeRO-2 has lower communication overhead than ZeRO-3. Use ZeRO-3 only when your model doesn't fit across GPUs with ZeRO-2.

### Installation

```shell
pip install deepspeed
pip install transformers[deepspeed]
```

Installing from source is more reliable as it matches exact hardware and includes features not yet in PyPI.

### Configuration with Trainer

Use `"auto"` in your config for values DeepSpeed fills from TrainingArguments:

```json
{
    "train_micro_batch_size_per_gpu": "auto",
    "gradient_accumulation_steps": "auto",
    "optimizer": {"params": {"lr": "auto"}},
    "bf16": {"enabled": "auto"},
    "gradient_clipping": "auto"
}
```

Pass the config to `TrainingArguments`:

```python
from transformers import TrainingArguments

args = TrainingArguments(
    deepspeed="path/to/ds_config.json",
    ...
)
```

### Launch Methods

| Method | Command |
|--------|---------|
| DeepSpeed launcher | `deepspeed --num_gpus 4 train.py` |
| torchrun | `torchrun --nproc_per_node 4 train.py` |
| Accelerate | `accelerate launch --num_processes 4 train.py` |

> **Note:** Accelerate ignores the `deepspeed` argument in TrainingArguments. Use `accelerate config` to create a `default_config.yaml` with `distributed_type: DEEPSPEED`.

### ZeRO-3 Critical Pitfall

**WARNING:** ZeRO-3 shards parameters **during initialization**. You must instantiate `TrainingArguments` **before** loading your model. If the model is already on each GPU before DeepSpeed is configured, no memory is saved.

### Config Key Parameters

| Parameter | Purpose | Recommendation |
|-----------|---------|---------------|
| `zero_optimization.stage` | ZeRO stage (1, 2, or 3) | Start with 2, use 3 only if needed |
| `overlap_comm` | Hide all-reduce latency behind backward pass | Set to `true` |
| `contiguous_gradients` | Contiguous gradient buffer | Set to `true` |
| `allgather_bucket_size` | AllGather bucket size (ZeRO-2) | Default 2e8; lower = less memory, slower |
| `reduce_bucket_size` | Reduce bucket size | Same tradeoff as allgather |
| `stage3_prefetch_bucket_size` | Prefetch bucket size (ZeRO-3) | `"auto"` recommended |
| `stage3_param_persistence_threshold` | Param persistence threshold (ZeRO-3) | `"auto"` recommended |
| `stage3_gather_16bit_weights_on_model_save` | Reconstruct full weights on save (ZeRO-3) | `true` for loadable checkpoints |
| `offload_optimizer` | Offload optimizer to CPU/NVMe | `{"device": "cpu", "pin_memory": true}` |
| `offload_param` | Offload parameters to CPU (ZeRO-3 only) | `{"device": "cpu", "pin_memory": true}` |

### Offloading

```json
{
    "zero_optimization": {
        "stage": 3,
        "offload_optimizer": {"device": "cpu", "pin_memory": true},
        "offload_param": {"device": "cpu", "pin_memory": true}
    }
}
```

Set `pin_memory` to `true` to speed up CPU-GPU transfers, but this locks RAM unavailable to other processes. If offloading the optimizer, set `zero_force_ds_cpu_optimizer` to `false` to use DeepSpeed's CPU Adam optimizer.

### Checkpoints & Saving

DeepSpeed saves checkpoints in a **sharded format** that cannot be loaded directly with `from_pretrained()`.

- Set `load_best_model_at_end=True` to have Trainer track and reload the best checkpoint
- After training, call `trainer.save_model("./best-model")` for a normal transformers checkpoint
- For ZeRO-3: always set `stage3_gather_16bit_weights_on_model_save: true` to reconstruct full weights
- `save_only_model=True` skips optimizer state — **cannot** be combined with `load_best_model_at_end=True`

### HfDeepSpeedConfig (Non-Trainer Usage)

When using DeepSpeed without Trainer, Transformers provides `HfDeepSpeedConfig`:

```python
from transformers.integrations import HfDeepSpeedConfig

ds_config = HfDeepSpeedConfig("path/to/ds_config.json")
```

A `weakref` of this object is stored in the module's globals for access from `from_pretrained` and `_get_resized_embeddings`. Trainer uses the `HfTrainerDeepSpeedConfig` subclass which has logic to sync config with TrainingArguments by expanding `"auto"` placeholder values.

### Resources
- https://huggingface.co/docs/transformers/en/deepspeed — DeepSpeed ZeRO guide
- https://huggingface.co/docs/transformers/en/main_classes/deepspeed — `HfDeepSpeedConfig` API reference
- ZeRO-1 paper: "Memory Optimizations Toward Training Trillion Parameter Models" (SC 2020)
- ZeRO-2 paper: "Democratizing Billion-Scale Model Training" (ATC 2021)
- ZeRO-3 paper: "Breaking the GPU Memory Wall for Extreme Scale Deep Learning" (SC 2021)
## Entry 59: Transformers GenerationConfig & Advanced Decoding Strategies
**Date:** 2026-07-23
**Topic:** `hf-transformers-generation-config` — Generation configuration, `generate()` parameters, and decoding strategies

### Overview

Transformers' `generate()` method is the unified API for autoregressive text generation. Its behaviour is controlled by a `GenerationConfig` object merged with pass-through kwargs. The framework supports six decoding strategies, custom generation methods, and streaming output.

### GenerationConfig

Every model ships with a default `generation_config.json` in its Hub repository. Load it explicitly:

```python
from transformers import GenerationConfig
config = GenerationConfig.from_pretrained("google/gemma-2-2b")
config.max_new_tokens = 512
config.temperature = 0.7
config.do_sample = True
config.top_p = 0.9
```

Pass as a config object or individual kwargs.

### Decoding Strategy Parameters

| Strategy | Key params | Behaviour |
|----------|-----------|-----------|
| **Greedy** | `do_sample=False`, `num_beams=1` | Always picks highest-probability next token |
| **Sampling** | `do_sample=True`, `temperature`, `top_k`, `top_p` | Random sampling from probability distribution |
| **Beam search** | `num_beams>=2`, `num_beam_groups` | Maintains `num_beams` candidates, picks highest overall score |
| **Beam sampling** | `num_beams>=2` + `do_sample=True` | Combines beam search with sampling |
| **Contrastive** | `penalty_alpha>0`, `top_k` | Balances confidence vs past similarity (SimCTG) |
| **Diverse beam** | `num_beams>=2`, `num_beam_groups`, `diversity_penalty` | Groups beams, penalises inter-group similarity |

### Key `generate()` Parameters

**Length control:** `max_new_tokens`, `max_length`, `min_new_tokens`, `min_length`, `stop_strings`

**Output selection:** `num_return_sequences`, `num_beams`, `early_stopping`

**Sampling:** `temperature` (0.0-∞), `top_k`, `top_p` (nucleus), `repetition_penalty`, `typical_p`

**Logits processors:** `no_repeat_ngram_size`, `encoder_no_repeat_ngram_size`, `bad_words_ids`, `force_words_ids`, `diversity_penalty`, `constraints`

**Advanced:** `assistant_model` (speculative decoding, 2-3x speedup), `streamer`, `synced_gpus`, `output_scores`, `custom_generate` (str or callable)

### LogitsProcessor Pipeline Order

1. RepetitionPenaltyLogitsProcessor  2. NoRepeatNGramLogitsProcessor  3. EncoderNoRepeatNGramLogitsProcessor  4. NoBadWordsLogitsProcessor  5. MinLengthLogitsProcessor  6. ForcedBOS/EOSLogitsProcessor  7. InfNanRemoveLogitsProcessor  8. TemperatureLogitsWarper  9. TopKLogitsWarper  10. TopPLogitsWarper  11. TypicalLogitsWarper

### Key Takeaways
1. Always prefer `max_new_tokens` over `max_length` to avoid prompt truncation.
2. `do_sample=True` is required for any sampling parameters to take effect.
3. Speculative decoding via `assistant_model` is the easiest free speedup.
4. `custom_generate` enables publishing custom generation algorithms as reusable Hub repos.

### Resources
- https://huggingface.co/docs/transformers/en/generation_strategies
- https://huggingface.co/docs/transformers/en/main_classes/text_generation
- https://huggingface.co/blog/how-to-generate

## Entry 61: Llama 4 Integration in Transformers — MoE, NoPE, and Native Multimodality
**Date:** 2026-07-23
**Topic:** `hf-transformers-llama-4-deep-dive` — Meta Llama 4 (Scout & Maverick) integration in Transformers

### Overview

Llama 4, released April 5, 2025, is Meta's fourth-generation LLM family featuring a **Mixture-of-Experts (MoE) architecture** with **early fusion for native multimodality** (text + image). Two models ship:

| Model | Active Params | Total Params | Experts | Context (Instruct) |
|-------|--------------|-------------|---------|-------------------|
| **Scout** | 17B | ~109B | 16 | 10M tokens |
| **Maverick** | 17B | ~400B | 128 | 1M tokens |

Both trained on up to 40T tokens across 200 languages (12 supported for fine-tuning). Integrated in Transformers v4.51.0+.

### Architecture Highlights

**iRoPE (interleaved RoPE + NoPE):** Every 4 decoder layers, 1 layer uses **NoPE** (No Positional Encoding) with a full causal mask for long-context awareness; the other 3 use standard RoPE with **chunked attention** (8192-token chunks). This balance keeps compute feasible while enabling 10M-token context.

**Chunked Attention (RoPE layers):** Only visible tokens within the same 8K chunk — a memory-efficient sliding-window variant. NoPE layers see the full context.

**Attention Temperature Tuning:** Scaled softmax in NoPE layers prevents attention probability collapse on very long sequences — key to Scout's 10M context.

**QK Normalization:** Scout adds learnable-parameter-free RMS norm on Query/Key states in RoPE layers (after RoPE embeddings).

**MoE Interleaving:** Scout = full MoE (all 16 experts in every MoE layer). Maverick = alternating MoE/dense layers (experts in half the layers only).

**Co-distillation:** Maverick distilled from the larger Llama Behemoth using dynamic logit weighting.

**MetaP:** Hyperparameter tuning inspired by µP (maximal update parameterization).

### Transformers API

```python
from transformers import Llama4ForConditionalGeneration, AutoTokenizer, AutoProcessor

# Text-only generation
model = Llama4ForConditionalGeneration.from_pretrained(
    "meta-llama/Llama-4-Scout-17B-16E-Instruct",
    device_map="auto",
    dtype=torch.bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-4-Scout-17B-16E-Instruct")

# Multimodal (text + image)
processor = AutoProcessor.from_pretrained(model_id)
inputs = processor.apply_chat_template(messages, tokenize=True, return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=256)
```

### Attention Methods

Three implementations available: `eager` (default), `sdpa` (faster), `flex_attention` (best for long context). Flex attention requires tensor-parallel mode via `torchrun`.

```python
model = Llama4ForConditionalGeneration.from_pretrained(
    model_id,
    attn_implementation="flex_attention",  # or "sdpa" / "eager"
    device_map="auto",
    dtype=torch.bfloat16,
)
```

### Long-context Generation

Scout's 10M context uses `prefill_chunk_size` and `cache_implementation="hybrid"`:

```python
out = model.generate(
    input_ids,
    prefill_chunk_size=2048 * 8,
    max_new_tokens=300,
    cache_implementation="hybrid",
)
```

### Deployment Notes

- Scout fits on one server GPU via **on-the-fly int4/int8 quantization**
- Maverick ships in **BF16 and FP8** formats
- Both models require accepting the **Llama 4 Community License** on the Hub
- Use `pip install transformers[hf_xet]` for faster downloads (Xet backend, ~25% dedup)
- TGI supported for production
- Tensor parallelism (`torchrun --nproc-per-node=N`) recommended for multi-GPU

### Key Takeaways

1. NoPE layers every 4 layers are the key innovation enabling 10M context without RoPE memory blowup.
2. Use `flex_attention` + tensor parallelism for the best long-context performance.
3. Scout (16E) is more practical for single-GPU deployment; Maverick (128E) for maximum quality.
4. Always install `hf_xet` for large model downloads.
5. Early fusion means images and text can be freely interleaved in a single prompt.

### Resources
- https://huggingface.co/docs/transformers/en/model_doc/llama4 — Transformers docs
- https://huggingface.co/blog/llama4-release — Official HF integration blog
- https://github.com/meta-llama/llama-models/blob/main/models/llama4/MODEL_CARD.md — Official model card
- https://huggingface.co/meta-llama/Llama-4-Scout-17B-16E-Instruct — Scout Hub repo
- https://huggingface.co/meta-llama/Llama-4-Maverick-17B-128E-Instruct — Maverick Hub repo
|
|---
|
|## Entry 62: Hub Model Download Statistics — Counting Methodology & Queries
|**Date:** 2026-07-23
|**Topic:** `hf-hub-model-download-stats` — How download counts are computed per library on the Hugging Face Hub
|
|### Overview
|
|The Hugging Face Hub tracks model downloads server-side. Counting is non-trivial — a single repo may contain multiple weight files (sharded, different formats per library). The Hub uses **query files**: a per-library set of file paths that trigger download counting. Every HTTP GET or HEAD request to a query file increments the counter.
|
|### Default Query Files
|
|When no library is specified, the Hub uses these default query files:
|`config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`
|
|Libraries can override by specifying their own `countDownloads` filter. The code is **open-source** at the Hub's internal repository.
|
|### Per-Library Query Files
|
|| Library | Query File(s) | Notes |
||---------|--------------|-------|
|| Default | `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml` | Fallback when no library filter defined |
|| Nemo | All `.nemo` files | All Nemo checkpoint files counted |
|| diffusers | `model_index.json` + top-level `.safetensors`/`.ckpt`/`.bin` | Special edge case — counts both library usage and direct UI downloads |
|| GGUF | All `.gguf` files | Self-contained; no library dependency |
|
|### Diffusers Edge Case
|
|Diffusers repos are an exception because users download weights via:
|1. **Python library** (`diffusers.from_pretrained`) — counts `model_index.json` hits
|2. **Direct UI downloads** (Stable Diffusion WebUI, ComfyUI, etc.) — counts top-level `.safetensors`, `.ckpt`, `.bin`
|
|The Hub's internal filter uses a boolean `should` query with `minimum_should_match: 1`:
|```json
|[
|  {
|    "bool": {
|      "should": [
|        { "term": { "path": "model_index.json" } },
|        { "regexp": { "path": "[^/]*\\.safetensors" } },
|        { "regexp": { "path": "[^/]*\\.ckpt" } },
|        { "regexp": { "path": "[^/]*\\.bin" } }
|      ],
|      "minimum_should_match": 1
|    }
|  }
|]
|```
|Nested files are excluded from the regex patterns to avoid double-counting library-based downloads.
|
|### GGUF Handling
|
|GGUF files are **self-contained** (model weights + architecture + tokenizer in one file) and not tied to a specific library. All GGUF files in a repo are counted. Repo cloning counts each file, but most users download a single GGUF file per repo, so double-counting is minimal in practice.
|
|### Adding Custom Query Files
|
|Library authors can add custom download filters by opening a PR at the Hub's internal count-downloads configuration. Example: VFIMamba integration added custom query files for download metrics.
|
|### Publisher Analytics (Granular Logs)
|
|For organizations needing more detailed data:
|- Distinguish `config.json` from model weights downloads
|- Exclude CI/CD pipeline traffic
|- Deduplicate unique downloaders
|- **Publisher Analytics** provides anonymized request-level access logs for all models and datasets published by an organization
|- Logs are raw (unprocessed) so organizations apply their own custom rules
|
|### Key Insights
|
|1. Download counts are **server-side only** — no client-side reporting. Each HTTP request to a query file = one count.
|2. HEAD requests count too, which means `git lfs` fetch/previews also increment counters.
|3. Query files prevent double-counting from repo clones (since not every file in a repo is a query file).
|4. Diffusers repos get the most complex counting logic due to dual library/UI usage patterns.
|5. GGUF is the simplest case — every GGUF file in a repo counts.
|6. For truly granular data (unique downloaders, CI/CD filtering), Publisher Analytics is the enterprise solution.
|7. The `hf` CLI `models info` subcommand shows download counts in the model metadata.
|
|### Resources
|- https://huggingface.co/docs/hub/en/models-download-stats — Official docs on download counting methodology
- https://huggingface.co/docs/hub/en/publisher-analytics — Publisher Analytics for granular logs

|---

## Entry 63: Transformers KV Cache Architecture — Dynamic, Static, Quantized & Beyond

**Date:** 2026-07-23
**Topic:** `hf-transformers-kv-cache-architecture` — Complete reference on the Transformers KV Cache class hierarchy (layers, caches, quantization, offloading)

### Overview

Transformers v5.14.0+ has a **two-tier KV cache architecture**: **CacheLayer** objects (storing per-layer key/value states) wrapped in **Cache** containers (managing all layers of the model). The architecture supports dynamic growth, pre-allocated static caches, quantization, CPU offloading, and hybrid attention (full + linear/SSM layers).

### CacheLayerMixin — The Per-Layer Foundation

The `CacheLayerMixin` (ABC) defines the interface every layer cache implements:

```python
class CacheLayerMixin(ABC):
    def lazy_initialization(self, key_states, value_states) -> None: ...
    def update(self, key_states, value_states) -> tuple[Tensor, Tensor]: ...
    def get_seq_length(self) -> int: ...
    def get_max_length(self) -> int: ...
    def get_mask_sizes(self, query_length) -> tuple[int, int]: ...
    def offload(self): ...          # Move to CPU
    def prefetch(self): ...         # Move back to GPU
    def reset(self): ...            # Zero out (preserve objects)
    def reorder_cache(self, beam_idx): ...  # Beam search support
    def crop(self, max_length): ...         # Truncate
```

Two concrete branches:

| Branch | Classes | Allocation |
|--------|---------|------------|
| **Dynamic** | `DynamicLayer`, `DynamicSlidingWindowLayer`, `DynamicIndexedLayer` | Grows via `torch.cat` on each `update()` |
| **Static** | `StaticLayer`, `StaticSlidingWindowLayer`, `StaticIndexedLayer` | Pre-allocated tensor; overwrites in-place |

**Auto-registration**: Subclasses set `_layer_type` (e.g. `"full_attention"`, `"sliding_attention"`) to auto-register in `DYNAMIC_LAYER_TYPE_MAPPING` or `STATIC_LAYER_TYPE_MAPPING` — the model config's `layer_types` list dispatches to the correct class.

### Caches — Multi-Layer Containers

The `Cache` base class holds a list of `CacheLayerMixin` objects (one per decoder layer):

| Cache Class | Key Features | Best For |
|-------------|-------------|----------|
| **DynamicCache** | Layers grow via `torch.cat`; config auto-detects sliding/hybrid; optional CPU offloading | Standard inference, default in `generate()` |
| **StaticCache** | Pre-allocated fixed-size tensors; compatible with `torch.compile()` and `torch.export()` | Production inference, compiled graphs, export |
| **QuantizedCache** | Per-channel 4-bit KV quantization (KIVI-inspired); backends: "quanto" or "hqq"; configurable `q_group_size` (default 64) and `residual_length` (default 128) | Long-context generation, GPU memory-constrained |
| **EncoderDecoderCache** | Combines self-attention + cross-attention caches; wraps two `Cache` objects | Encoder-decoder models (Whisper, T5, Flan) |
| **MtpCache** | Extends DynamicCache with token-offset logic for Multi-Token Prediction (MTP) depth tracking | MTP training (DeepSeek-style speculative decoding) |

### DynamicCache — The Default

```python
# Automatic config-based layer type detection
cache = DynamicCache(config=model.config)

# Sliding window layers use DynamicSlidingWindowLayer (~O(window) memory)
# Full attention layers use DynamicLayer (~O(seq_len) memory)
# Hybrid models auto-dispatch to appropriate layer classes

# CPU offloading for GPU memory savings
cache = DynamicCache(config=model.config, offloading=True, offload_only_non_sliding=True)
```

- Layers are lazily initialized on first `update()` call
- `DynamicSlidingWindowLayer` caps memory at `[batch, heads, min(seq, window), dim]`
- `DynamicIndexedLayer` adds an indexer key cache (used by MQA/GQA cross-attention optimizations)
- Compatible with DDP: accepts `ddp_cache_data` iterable for distributed gather compatibility

### StaticCache — Pre-Allocated for Performance

```python
# Pre-allocate space for prompt + 10 new tokens
past_key_values = StaticCache(config=model.config, max_cache_len=input_len + 10)
outputs = model(**inputs, past_key_values=past_key_values, use_cache=True)
```

- **Required** for `torch.compile()` and `torch.export()` — dynamic growth is not exportable
- Allocates once: `[batch, heads, max_cache_len, dim]` — no `torch.cat` overhead
- Layers overwrite pre-allocated positions in-place using index arithmetic
- Config determines layer types (full vs sliding vs hybrid), same as DynamicCache

### QuantizedCache — KV Cache Compression

```python
from transformers import QuantizedCache

cache = QuantizedCache(
    backend="quanto",          # "quanto" or "hqq"
    config=model.config,
    nbits=4,                   # 4-bit KV cache
    axis_key=0,                # Per-channel quantization axis
    axis_value=0,
    q_group_size=64,           # Group size for quantization
    residual_length=128        # Keep pre-128 tokens in full precision
)
```

Based on [KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache](https://huggingface.co/papers/2402.02750):
- First `residual_length` tokens stored in full precision (important for attention to recent context)
- Older tokens quantized to `nbits` per-channel with group-size granularity
- Only supports full-attention layers (no sliding/hybrid)
- Two backends: `"quanto"` (PyTorch-native, simple) and `"hqq"` (Half-Quadratic Quantization, more accurate)

### EncoderDecoderCache — Two Caches in One

```python
self_cache = DynamicCache(config=model.config)
cross_cache = DynamicCache(config=model.config)
past_key_values = EncoderDecoderCache(self_cache, cross_cache)
```

- `self_attention_cache`: caches decoder self-attention KV pairs
- `cross_attention_cache`: caches encoder-decoder cross-attention KV pairs
- Both caches can be different types (e.g. StaticCache for self, DynamicCache for cross)
- Tracks `is_updated` dict per layer to know if cross-attention has been computed

### Memory Management & Offloading

```python
# CPU offloading
DynamicCache(config=model.config, offloading=True, offload_only_non_sliding=True)
```

- Uses `torch.Stream` (PyTorch 2.7+) or `torch.cuda.Stream` for non-blocking prefetch
- Default stream waits for prefetch stream before computing each layer
- Sliding window layers are small and skipped from offloading by default
- Prefetch always circles back to layer 0 after the last layer

### Layer Type Auto-Discovery

```python
# From config: layer_types = ["full_attention", "full_attention", ...] or
# ["sliding_attention", ...] or hybrid ["full_attention", "linear_attention", ...]
layer_types, layer_kwargs = get_layer_types_and_kwargs(config)

# Auto-mapping
DYNAMIC_LAYER_TYPE_MAPPING = {
    "full_attention": DynamicLayer,
    "sliding_attention": DynamicSlidingWindowLayer,
    "indexed_attention": DynamicIndexedLayer,
    # ... linear attention variants
}
STATIC_LAYER_TYPE_MAPPING = {
    "full_attention": StaticLayer,
    "sliding_attention": StaticSlidingWindowLayer,
    "indexed_attention": StaticIndexedLayer,
    # ... linear attention variants
}
```

**Deprecated aliases:**
- `SlidingWindowCache` → renamed to `StaticCache` (v5.x)
- `get_max_cache_shape()` → use `get_max_length()`
- `max_cache_len` property → use `get_max_length()`
- `max_batch_size` property → use `batch_size`

### Linear Attention Cache Layers

Transformers 5.x adds native support for **linear attention layers** (Mamba/SSM-style) alongside standard attention in hybrid models:

| Layer Class | Combines With |
|-------------|---------------|
| `LinearAttentionLayer` | SSM-only layers |
| `LinearAttentionAndFullAttentionLayer` | SSM + Standard Attention |
| `LinearAttentionAndSlidingWindowAttentionLayer` | SSM + Sliding Window |
| `LinearAttentionAndStaticFullAttentionLayer` | SSM + Static (compilable) |
| `LinearAttentionAndStaticSlidingWindowAttentionLayer` | SSM + Static Sliding (compilable) |

These layers manage conv states and recurrent states (SSM hidden states) alongside KV caches, using `update_conv_state()` and `update_recurrent_state()` methods.

### Key Takeaways

1. **DynamicCache** is the default — flexible, lazy, supports all layer types, but not exportable
2. **StaticCache** is for production — compile/export ready, pre-allocated, no overhead
3. **QuantizedCache** saves GPU memory for long contexts — 4-bit KV with full-precision residual
4. **EncoderDecoderCache** wraps two sub-caches for encoder-decoder architectures
5. **MtpCache** enables multi-token prediction training with token offsets
6. **CPU offloading** now has async prefetch via `torch.Stream` — GPU memory savings without blocking
7. Hybrid models (transformer + SSM) get specialized layer classes that handle both KV and SSM states
8. Config-based auto-discovery eliminates manual layer-type specification

### Resources
- https://github.com/huggingface/transformers/blob/main/src/transformers/cache_utils.py — Full source (Cache, DynamicCache, StaticCache, QuantizedCache, EncoderDecoderCache, MtpCache)
- https://huggingface.co/papers/2402.02750 — KIVI: A Tuning-Free Asymmetric 2bit Quantization for KV Cache
- https://huggingface.co/docs/transformers/en/llm_tutorial — LLM text generation with cache support

## Entry 66: Microsoft Phi-4 — Data-Centric Small Language Model in Transformers
**Date:** 2026-07-23
**Topic:** `hf-transformers-phi4` — Phi-4 (14B) architecture, Transformers integration, and synthetic-data-first training approach

### Overview

Phi-4 is a **14-billion parameter dense decoder-only Transformer** developed by **Microsoft Research**, released Dec 12, 2024 under the **MIT** license. It is the fourth generation of the Phi model family and represents a paradigm shift from distillation-based training (Phi-3 distilled GPT-4) to a **data-quality-first approach** where synthetic data constitutes the bulk of training material.

**Key training specs:**
- Architecture: Dense decoder-only Transformer, 14B params
- Context window: 16K tokens
- Training compute: 1,920 H100-80G GPUs over 21 days
- Training tokens: 9.8T total
- Data cutoff: June 2024

### Data Quality Innovation

Phi-4's core contribution is a **three-pillar training recipe**:

1. **Synthetic Data for Pretraining + Midtraining** — Generated via multi-agent prompting, self-revision workflows, and instruction reversal. Designed to induce stronger reasoning and problem-solving. Synthetic tokens significantly increased over Phi-3 allocation.

2. **Curated Organic Data** — Meticulously filtered web content, licensed academic books, and code repositories. Seeds for the synthetic pipeline are sourced from high-reasoning, high-educational-value organic data.

3. **Advanced Post-Training** — New SFT dataset versions + a novel **pivotal token search** technique for generating DPO (Direct Preference Optimization) pairs. Rejection sampling refines outputs further.

Unlike Phi-3 which largely distilled GPT-4, Phi-4 **surpasses GPT-4o on STEM QA** (GPQA: 56.1 vs 50.6) and MATH (80.4 vs 74.6), proving the approach goes beyond distillation.

### Benchmarks (OpenAI SimpleEval, temp=0.5)

| Benchmark | Phi-4 (14B) | GPT-4o-mini | Llama-3.3-70B | GPT-4o |
|-----------|-------------|-------------|---------------|--------|
| MMLU      | **84.8**    | 81.8        | 86.3          | 88.1   |
| GPQA      | **56.1**    | 40.9        | 49.1          | 50.6   |
| MATH      | **80.4**    | 73.0        | 66.3*         | 74.6   |
| HumanEval | 82.6        | **86.2**    | 78.9*         | 90.6   |
| DROP      | 75.5        | 79.3        | **90.2**      | 80.9   |

*Llama scores below Meta's reported values due to SimpleEval formatting strictness.

Phi-4 matches or exceeds Llama-3.1-405B on reasoning tasks — remarkable for a 14B model.

### Transformers Integration

The model uses the standard `Phi3ForCausalLM` architecture (minimal changes from Phi-3) and supports:

```python
import transformers

pipeline = transformers.pipeline(
    "text-generation",
    model="microsoft/phi-4",
    model_kwargs={"torch_dtype": "auto"},
    device_map="auto",
)

messages = [
    {"role": "system", "content": "You are a medieval knight."},
    {"role": "user", "content": "How should I explain the Internet?"},
]

outputs = pipeline(messages, max_new_tokens=128)
print(outputs[0]["generated_text"][-1])
```

**Chat format:** Uses the standard `phi`/`<|im_start|>` chat template with `<|im_sep|>` separators (same format as Phi-3). Tagged in Transformers as `phi4` model architecture.

### Key Takeaways

1. **Data quality beats scale** — Phi-4 shows 14B model can rival 70B+ models on reasoning via superior data curation
2. **Synthetic data is a first-class citizen** — Not just for post-training; bulk of pretraining data is synthetic
3. **Beyond distillation** — First Phi model to surpass its teacher (GPT-4o) on key STEM benchmarks
4. **MIT licensed** — Fully open for commercial and research use via Hugging Face
5. **Standard Transformers API** — Drop-in replacement for Phi-3; same pipeline/code patterns

### Resources
- https://huggingface.co/microsoft/phi-4 — Model card + files
- https://arxiv.org/abs/2412.08905 — Phi-4 Technical Report
- https://huggingface.co/docs/transformers/main/en/model_doc/phi4 — Transformers Phi-4 docs
- https://github.com/microsoft/Phi-4CookBook — Official cookbook with inference/finetuning recipes

---

## Entry 67: Mixture of Experts (MoE) in Hugging Face Transformers — Architecture & Integration

**Date:** 2026-07-23
**Topic:** `hf-transformers-moe-deep-dive` — How Transformers v5.14.0 supports Mixture-of-Experts architectures across model families

### Overview

Mixture-of-Experts (MoE) is a neural architecture where each forward pass activates only a subset of the total parameters via a learned router. In Transformers, MoE replaces dense FFN layers with multiple "expert" FFNs and a gating/routing mechanism. Key supported MoE model families:

| Model Family | Developer | Config Class | Experts | Top-K | Shared Expert | Notes |
|---|---|---|---|---|---|---|
| **Qwen2MoE** | Alibaba | `Qwen2MoeConfig` | 60 | 4 | Yes (shared_expert_intermediate_size=5632) | Decoder-sparse-step controlled, supports mlp_only_layers |
| **DBRX** | Databricks | `DbrxConfig` | 16 | 4 | No | FFN config dict for expert details, uses `router_aux_loss_coef`, `output_router_logits` |
| **DeepSeek** | DeepSeek | `DeepseekConfig` (main) | Varies | Varies | Yes | Fine-grained MoE, supports `num_experts_per_tok`, `n_shared_experts` |
| **Mixtral** | Mistral | `MixtralConfig` | 8 | 2 | No | Router z-loss for load balancing |
| **JetMoE** | Community | `JetMoeConfig` | 8 | 2 | No | Uses `num_experts`, `topk` params, GEGLU activation |
| **Llama 4** | Meta | `Llama4Config` | Varies | Varies | No | MoE variant (also NoPE, 10M context) |

### How MoE Works in Transformers

**The SparseMoeBlock pattern:**

All MoE implementations in Transformers follow a consistent pattern with a `SparseMoeBlock` module that contains:

```python
class SparseMoeBlock(nn.Module):
    def __init__(self, config):
        self.gate = nn.Linear(hidden_size, num_experts, bias=False)
        self.experts = nn.ModuleList([FFN(config) for _ in range(num_experts)])
    
    def forward(self, hidden_states):
        # 1. Compute router logits
        router_logits = self.gate(hidden_states)
        # 2. Top-K routing (token-choice routing)
        routing_weights, selected_experts = torch.topk(router_logits, top_k, dim=-1)
        # 3. Only compute selected experts
        final_hidden_states = ...  # weighted sum of expert outputs
        return final_hidden_states, router_logits
```

**Token-choice routing**: Each token independently selects its top-K experts. The router computes a probability distribution over experts (via softmax), and only the top-K probabilities contribute. This is the standard for all supported MoE models.

**Load balancing via auxiliary loss**: MoE layers add an auxiliary load-balancing loss to encourage uniform expert utilization. This is controlled by `router_aux_loss_coef` (default 0.001 for Qwen2MoE, 0.01 for DBRX). The loss is computed during training when `output_router_logits=True`.

### Qwen2MoE — Comprehensive Reference

Qwen2MoE (`Qwen2MoeForCausalLM`) is the most configurable MoE implementation in Transformers.

**Architecture config:**

```python
from transformers import Qwen2MoeConfig, Qwen2MoeForCausalLM

config = Qwen2MoeConfig(
    num_hidden_layers=24,
    hidden_size=2048,
    intermediate_size=5632,      # Dense FFN intermediate size
    num_experts=60,              # Total number of routed experts (unique to MoE)
    num_experts_per_tok=4,       # Top-K: each token activates 4 experts
    moe_intermediate_size=1408,  # Intermediate size of routed expert MLPs
    shared_expert_intermediate_size=5632,  # Intermediate size of shared expert
    decoder_sparse_step=1,       # Every N-th layer uses MoE (1 = every layer)
    norm_topk_prob=False,        # Whether to normalize routed expert weights
    output_router_logits=False,  # Enable for auxiliary loss computation
    router_aux_loss_coef=0.001,  # Load balancing loss coefficient
    mlp_only_layers=[],          # Layer indices to use dense MLP instead of MoE
)
```

**Key MoE-specific parameters:**

| Parameter | Purpose |
|---|---|
| `num_experts` | Total expert count in MoE layers (Qwen: 60, DBRX: 16, Mixtral: 8) |
| `num_experts_per_tok` | Top-K experts per token (Qwen: 4, DBRX: 4, Mixtral: 2) |
| `moe_intermediate_size` | FFN hidden dim for each expert (smaller than dense intermediate_size) |
| `shared_expert_intermediate_size` | Shared expert FFN dim — activated for ALL tokens regardless of routing |
| `decoder_sparse_step` | MoE frequency: 1 = every layer, 2 = every other layer, etc. |
| `mlp_only_layers` | Explicit list of layers to use dense MLP instead of sparse MoE |
| `norm_topk_prob` | Normalize routing weights after top-k selection |
| `output_router_logits` | Enable to return router logits (needed for auxiliary loss) |
| `router_aux_loss_coef` | Weight for load-balancing auxiliary loss |
| `shared_expert_intermediate_size` | Intermediate size of the shared expert that processes all tokens |

**Shared expert pattern**: Qwen2MoE and DeepSeek use a shared expert that processes ALL tokens in addition to the top-K routed experts. This ensures every token gets a minimum compute allocation, with routed experts providing specialized capacity. The shared expert has a larger intermediate size than individual routed experts.

**Sparse step control**: The `decoder_sparse_step` parameter controls MoE density. For a 24-layer model:
- `decoder_sparse_step=1`: All 24 layers use MoE
- `decoder_sparse_step=2`: 12 layers use MoE (every other layer)
- `decoder_sparse_step=3`: 8 layers use MoE

The `mlp_only_layers` list provides finer control — specific layer indices can use dense MLPs regardless of the sparse step.

### DBRX — Expert FFN via Config Dict

DBRX uses a different approach: the FFN configuration is passed as a dict:

```python
from transformers import DbrxConfig

config = DbrxConfig(
    d_model=256,
    n_heads=8,
    ffn_config={
        "ffn_type": "moe",           # "moe" or "dense"
        "moe_num_experts": 16,        # 16 routed experts
        "moe_top_k": 4,               # top-K = 4
        "output_router_logits": True, # Enable for auxiliary loss
        "router_aux_loss_coef": 0.01, # Load balancing coefficient
        "moe_jitter_eps": 0.0,        # Optional routing noise
    },
)
```

DBRX also computes router z-loss (in addition to load balancing loss) for training stability.

### DeepSeek MoE — Fine-Grained Expert Architecture

DeepSeek models (DeepSeekMoE, DeepSeek-V2/V3) employ a **fine-grained MoE** with:
- `num_experts`: Total experts (e.g., 160 for DeepSeek-V2)
- `num_experts_per_tok`: Active per token (e.g., 6)
- `n_shared_experts`: Shared expert count
- `routed_scaling_factor`: Scale routed expert logits
- `scoring_func`: Routing scoring function ("softmax" or "sigmoid")

DeepSeek models also support **multi-token prediction (MTP)** training heads alongside MoE.

### Loading and Inference

MoE models load exactly like dense models — Transformers handles the sparse blocks transparently:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Load MoE model — same API as any other Transformers model
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen1.5-MoE-A2.7B",
    torch_dtype=torch.bfloat16,
    device_map="auto",
)
tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen1.5-MoE-A2.7B")

# Inference — no special MoE handling needed
inputs = tokenizer("The future of AI is", return_tensors="pt").to(model.device)
outputs = model.generate(**inputs, max_new_tokens=50)
```

**Memory implications of MoE:**
- **Total parameters** may be large (e.g., 60 experts × 1408-dim FFN), but per-token FLOPs are only `num_experts_per_tok / num_experts` of total
- **VRAM usage** still requires loading all expert weights — MoE doesn't reduce memory during inference, only compute
- **Quantization** (AWQ, GPTQ, bitsandbytes) works on MoE models — each expert is quantized independently
- **vLLM** supports MoE models with expert parallelism across GPUs

### Saving and Offloading

```python
# Save MoE model normally — same as dense
model.save_pretrained("./my-moe-model")
tokenizer.save_pretrained("./my-moe-model")

# Offloading works layer-by-layer
model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen1.5-MoE-A2.7B",
    device_map="auto",
    offload_folder="./offload",
)
```

Note: `save_pretrained()` saves all expert weights — the output size is proportional to total parameters, not active parameters.

### Training MoE with Transformers

Training MoE models requires the auxiliary load-balancing loss. Enable it when training:

```python
from transformers import Trainer, TrainingArguments

training_args = TrainingArguments(
    output_dir="./moe-output",
    per_device_train_batch_size=4,
    # Enable router logits output during training
    remove_unused_columns=False,  # MoE returns additional outputs
)

model.config.output_router_logits = True  # Enable router logits
# The model automatically computes aux_loss = load_balancing_loss + z_loss
# Trainer tracks aux_loss in the total loss
```

**Load balancing pitfalls:**
- Without auxiliary loss, routing collapses to a few experts — most experts become dead weights
- `router_aux_loss_coef` needs tuning: too low → unbalanced routing, too high → routing becomes uniform (no specialization)
- Z-loss (DBRX) stabilizes training by penalizing extreme router logit values

### Key Insights

1. **MoE is transparent in Transformers** — loading, inference, saving all use the same API as dense models. The `SparseMoeBlock` is internal.
2. **Per-token compute is low but total VRAM is high** — MoE trades memory for compute efficiency. 60 experts × 1408-dim = 84K total hidden dim per layer.
3. **Router configuration is per-model** — Qwen2MoE uses config params directly; DBRX uses a dict; DeepSeek has fine-grained controls. No unified MoE config exists.
4. **Shared experts are a Qwen/DeepSeek innovation** — every token gets a base compute allocation from the shared expert, preventing routing collapse at inference time.
5. **`output_router_logits=True` is required during training** — without it, the model cannot compute the auxiliary load-balancing loss and routing will collapse.
6. **vLLM supports expert parallelism** — MoE models are a natural fit for distributed inference, with different experts placed on different GPUs.
7. **Transformers v5.14.0 supports 6+ MoE architectures** — Qwen2MoE, DBRX, DeepSeek, Mixtral, JetMoE, Llama 4 — all through the same `AutoModel` API.

### References
- Qwen2MoE docs: https://huggingface.co/docs/transformers/en/model_doc/qwen2_moe
- DBRX docs: https://huggingface.co/docs/transformers/en/model_doc/dbrx
- DeepSeek docs: https://huggingface.co/docs/transformers/main/en/model_doc/deepseek
- Mixtral docs: https://huggingface.co/docs/transformers/en/model_doc/mixtral
- JetMoE docs: https://huggingface.co/docs/transformers/en/model_doc/jetmoe
- Qwen1.5-MoE-A2.7B on Hub: https://huggingface.co/Qwen/Qwen1.5-MoE-A2.7B
- Load Balancing paper (Switch Transformer): https://arxiv.org/abs/2101.03961
- ST-MoE paper: https://arxiv.org/abs/2202.08906


## Entry 68: Optimum Quanto — PyTorch-Native Quantization Backend for Hugging Face

**Date:** 2026-07-23
**Topic:** `hf-optimum-quanto` — Deep dive into the `optimum-quanto` quantization library

### Overview

Optimum Quanto (`optimum-quanto`) is a PyTorch-native quantization backend integrated with Optimum. Designed for versatility — eager mode (no tracing required), any device (CUDA, MPS, CPU), automatic module substitution. **As of 2025–2026 it is in maintenance mode** — for production use, prefer bitsandbytes or torchAO.

### Supported Quantization Types

| Target | Types | Notes |
|---|---|---|
| **Weights** | int2, int4, int8, float8 | Per-channel along first dim (output features) |
| **Activations** | int8, float8 | Per-tensor with static scales, requires calibration |
| **CUDA matmul** | int8×int8, fp16×int4, bf16×int8, bf16×int4 | Accelerated kernels |

### 5-Step Quantization Workflow

```python
from optimum.quanto import quantize, freeze, Calibration, qint8

# 1. Dynamic quantization (inserts quant stubs)
quantize(model, weights=qint8, activations=qint8)

# 2. Calibrate activation ranges (momentum-based)
with Calibration(momentum=0.9):
    model(samples)

# 3. QAT — fine-tune to recover accuracy
model.train()
for batch in dataloader:
    loss = criterion(model(batch).dequantize(), targets)
    loss.backward()
    optimizer.step()

# 4. Freeze — replace float weights with quantized integers
freeze(model)

# 5. Serialize with safetensors + quantization map
from safetensors.torch import save_file
save_file(model.state_dict(), 'model.safetensors')
from optimum.quanto import quantization_map
with open('quantization_map.json', 'w') as f:
    json.dump(quantization_map(model), f)
```

### HF Model Helpers

**CausalLM:** `QuantizedModelForCausalLM.quantize(model, weights=qint4, exclude='lm_head')` — supports `save_pretrained`/`from_pretrained`.

**Diffusers:** `QuantizedPixArtTransformer2DModel.quantize(model, weights=qfloat8)` — quantize individual pipeline submodels, save/load independently.

**Requantize (low-level):** `requantize(new_model, state_dict, quantization_map, device=...)` — load from separate state_dict + qmap into a fresh model.

### Quantized Modules

- **QLinear** — weights always, biases never, inputs/outputs optional
- **QConv2d** — same as QLinear
- **LayerNorm** — weights/biases not quantized, outputs optional

Biases intentionally unquantized: they'd need ~int12 to avoid clipping with int8 inputs/weights (wasteful).

### Design

Quanto uses a `torch.Tensor` subclass that projects source tensor into optimal range for destination type, then maps via `Tensor.to()` (float) or `torch.round()` (int). Projection is symmetric per-tensor or per-channel (int8/float8) or group-wise affine (lower bitwidths).

### Key Pitfalls

1. **Outliers kill int8 activations**: Per-tensor int8 activation quantization collapses when tensors have outliers. Use float8 or SmoothQuant.
2. **Freeze is one-way**: After `freeze()`, weights are integer and non-trainable. Do QAT before freezing.
3. **No torch.compile**: Quanto works in eager mode only — dynamo/torch.compile not supported.
4. **No mixed types per tensor**: Each tensor uses one quantization type.
5. **Maintenance mode**: bitsandbytes or torchAO recommended for new projects.

### References
- GitHub: https://github.com/huggingface/optimum-quanto
- PyPI: https://pypi.org/project/optimum-quanto/
- Optimum docs: https://huggingface.co/docs/optimum/en/index
- SmoothQuant: https://github.com/mit-han-lab/smoothquant
- bitsandbytes: https://github.com/bitsandbytes-foundation/bitsandbytes
- torchAO: https://github.com/pytorch/ao

---

## Entry 29: Transformers RoPE Scaling — Complete Reference
**Date:** 2026-07-23
**Topic:** `hf-transformers-rope-scaling` — Full coverage of Rotary Position Embedding scaling techniques in Transformers

### Overview

Transformers v5.14.0+ includes a unified RoPE scaling framework through `rope_parameters` (a `RopeParameters` TypedDict) replacing the older `rope_scaling` dict. The new system supports 6 scaling methods plus the default, all defined in `transformers.modeling_rope_utils.ROPE_INIT_FUNCTIONS`.

### Architecture — `RopeParameters` TypedDict

```python
from transformers.modeling_rope_utils import RopeParameters

# Stored in model config as `rope_parameters`
params: RopeParameters = {
    "rope_type": str,          # "default" | "linear" | "dynamic" | "yarn" | "longrope" | "llama3" | "proportional"
    "rope_theta": float,       # Base period (default: 10000.0, accessible via config.default_theta)
    "factor": float,           # Scaling factor (for all types except "default")
    "partial_rotary_factor": float,  # Fraction of head_dim to apply RoPE (default: 1.0)
    "original_max_position_embeddings": int,  # Original pretraining length
    "attention_factor": float, # Attention scaling (yarn, longrope)
    "beta_fast": float,        # Extrapolation boundary (yarn, default: 32)
    "beta_slow": float,        # Interpolation boundary (yarn, default: 1)
    "short_factor": list[float],  # Per-dimension short-context factors (longrope)
    "long_factor": list[float],   # Per-dimension long-context factors (longrope)
    "low_freq_factor": float,     # Low-freq scaling weight (llama3)
    "high_freq_factor": float,    # High-freq scaling weight (llama3)
}
```

### The 6 Scaling Methods

| `rope_type` | Function | Mechanism | Key Parameters |
|------------|----------|-----------|----------------|
| `"default"` | Vanilla RoPE | Standard sinusoidal frequencies at base `rope_theta` | `rope_theta` |
| `"linear"` | Linear scaling (kaiokendev) | Divides inverse frequencies by `factor` | `factor` |
| `"dynamic"` | Dynamic NTK-aware scaling | Adjusts base frequency using `base * factor^(dim/(dim-2))` based on seq_len | `factor`, seq_len |
| `"yarn"` | YaRN (Yet another RoPE extensioN) | NTK+linear ramp interpolation with attention scaling | `factor`, `beta_fast`, `beta_slow`, `attention_factor` |
| `"longrope"` | LongRoPE (Microsoft) | Per-dimension short/long factors + dynamic switch | `short_factor`, `long_factor`, `original_max_position_embeddings` |
| `"llama3"` | Llama 3 style | Low/high frequency decomposition with separate scaling | `low_freq_factor`, `high_freq_factor`, `original_max_position_embeddings` |
| `"proportional"` | Proportional RoPE | Scales position IDs proportionally | `factor` |

### How It Works Internally

The `dynamic_rope_update` decorator in `modeling_rope_utils.py` wraps each RoPE forward pass:

```python
def wrapper(self, x, position_ids, layer_type=None):
    rope_type = self.rope_type
    if "dynamic" in rope_type:
        dynamic_frequency_update(self, position_ids, device=x.device)
    elif rope_type == "longrope":
        longrope_frequency_update(self, position_ids, device=x.device)
    return rope_forward(self, x, position_ids)
```

- **Dynamic methods** (linear, dynamic/ntk, yarn): Recompute `inv_freq` when seq_len > cached max
- **LongRoPE**: Switches between `long_factor` and `short_factor` based on whether seq_len exceeds `original_max_position_embeddings`
- **Llama 3**: Uses fixed decomposition — low frequencies scale by `low_freq_factor`, high by `high_freq_factor`

### Backward Compatibility

The old `rope_scaling` dict format is auto-converted:

```python
# Old format (still works → auto-converted in __post_init__)
config.rope_scaling = {"type": "linear", "factor": 2.0}

# New standardized format
config.rope_parameters = {
    "rope_type": "linear",
    "rope_theta": 500000.0,
    "factor": 2.0,
}
```

The property `rope_scaling` on `PreTrainedConfig` now delegates to `rope_parameters`:

```python
@property
def rope_scaling(self):
    return self.rope_parameters

@rope_scaling.setter
def rope_scaling(self, value):
    self.rope_parameters = value
```

### Per-Layer RoPE (Heterogeneous)

Transformers v5.14+ supports different RoPE configs per layer via `per_layer_config`. For example, Llama 4 uses different `rope_type` for different layers in its MoE structure. The `rope_parameters` dict can have per-layer keys instead of scalar values.

### Key Patterns

```python
# 1. Linear scaling — extend 4K → 8K
config.rope_parameters = {"rope_type": "linear", "factor": 2.0}

# 2. Dynamic NTK — extend 4K → 8K (better than linear for long range)
config.rope_parameters = {"rope_type": "dynamic", "factor": 2.0}

# 3. YaRN — best quality for large extensions (4K → 32K)
config.rope_parameters = {
    "rope_type": "yarn",
    "factor": 8.0,
    "original_max_position_embeddings": 4096,
    "beta_fast": 32,
    "beta_slow": 1,
}

# 4. Llama 3 style (used by Llama 3.1 8B → 128K context)
config.rope_parameters = {
    "rope_type": "llama3",
    "factor": 8.0,
    "low_freq_factor": 1.0,
    "high_freq_factor": 4.0,
    "original_max_position_embeddings": 8192,
    "rope_theta": 500000.0,
}

# 5. LongRoPE (per-dimension factors, used by Phi-4)
config.rope_parameters = {
    "rope_type": "longrope",
    "short_factor": [1.0, 1.0, ...],  # len = head_dim // 2
    "long_factor": [0.5, 0.5, ...],   # len = head_dim // 2
    "original_max_position_embeddings": 4096,
}
```

### Key Insights

1. **Default RoPE** uses theta=10000.0; Llama 3 uses 500000.0 (higher = longer base period)
2. **Dynamic NTK** outperforms linear scaling for the same factor because it preserves high-frequency information
3. **YaRN** adds an attention scaling factor `sqrt(1/log(factor))` to prevent attention entropy collapse
4. **LongRoPE** and **Llama 3 scaling** both use frequency decomposition — splitting the head_dim bands into low and high frequencies and scaling them differently
5. **The old `rope_scaling` dict format** is deprecated but still loads — new code should use `rope_parameters` instead
6. **Models trained with extended context** (e.g., GLM-4-9B-Chat-1M) typically use LongRoPE or YaRN during continued pretraining
7. **Zero-cost inference extension**: Dynamic NTK and YaRN work at inference time without fine-tuning — but quality degrades beyond 2-3x the pretraining length

### References
- https://huggingface.co/docs/transformers/en/main_classes/configuration
- https://github.com/huggingface/transformers/blob/main/src/transformers/modeling_rope_utils.py
- https://github.com/huggingface/transformers/blob/main/src/transformers/configuration_utils.py
- https://huggingface.co/papers/2309.00071 (YaRN paper)
- LongRoPE: https://arxiv.org/abs/2402.13753
- NTK-aware scaling: https://www.reddit.com/r/LocalLLaMA/comments/14lz7j5/ntkaware_scaling_unified/

## Entry 69: IP-Adapter in Hugging Face Diffusers — Image Prompt Adapter Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-diffusers-ip-adapter` — Full coverage of IP-Adapter (Image Prompt Adapter) for image-conditioned text-to-image generation

### Overview

IP-Adapter is a lightweight adapter that injects image-based guidance into text-to-image diffusion models without fine-tuning the base model. It decouples cross-attention for image features from the existing text-conditioned cross-attention, keeping the original UNet frozen and adding new cross-attention layers. IP-Adapter files are typically ~100MB because they only contain image embedding weights — the base model loads separately.

Key advantage: unlike Textual Inversion, DreamBooth, or LoRA, IP-Adapter can be **switched at inference time** without retraining — just call `load_ip_adapter()` with a different checkpoint.

### Architecture

```
CLIP Image Encoder → Image Embeddings → [IP-Adapter Cross-Attn Layers] → UNet
Text Encoder → Text Embeddings → [Original Cross-Attn Layers] → UNet
```

The IP-Adapter cross-attention layers are inserted into the UNet's down/up blocks. A `set_ip_adapter_scale()` parameter controls how much the image prompt influences generation (0.0 = text only, 1.0 = image only, 0.5 = balanced).

### Model Variants

| Variant | Image Encoder | Weight Prefix | Use Case |
|---------|---------------|---------------|----------|
| **Standard** | CLIP ViT-L/14 | `ip-adapter_sdxl.bin` / `ip-adapter_sd15.bin` | General image prompting |
| **Plus** | CLIP ViT-H | `ip-adapter-plus_sdxl_vit-h.safetensors` | Higher fidelity image adherence (patch embeddings) |
| **FaceID** | InsightFace → ID embedding | `ip-adapter-faceid_sdxl.bin` | Consistent face generation from cropped face images |
| **FaceID Plus** | InsightFace + CLIP ViT-H | `ip-adapter-plus-face_sdxl_vit-h.safetensors` | Face generation with style transfer |

All variants live in the [`h94/IP-Adapter`](https://huggingface.co/h94/IP-Adapter) HF Hub repo. FaceID variants are in [`h94/IP-Adapter-FaceID`](https://huggingface.co/h94/IP-Adapter-FaceID).

### Core API

```python
import torch
from diffusers import AutoPipelineForText2Image
from diffusers.utils import load_image

# 1. Load base model
pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16
).to("cuda")

# 2. Load IP-Adapter on top (no fine-tuning needed)
pipeline.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="sdxl_models",
    weight_name="ip-adapter_sdxl.bin"  # or .safetensors
)

# 3. Set blending scale
pipeline.set_ip_adapter_scale(0.8)

# 4. Generate
image = load_image("https://.../ip_adapter_diner.png")
output = pipeline(
    prompt="a polar bear sitting in a chair drinking a milkshake",
    ip_adapter_image=image,
    negative_prompt="deformed, ugly, wrong proportion, low res, bad anatomy, worst quality, low quality",
).images[0]
```

### Using Plus Variant (Higher Quality)

```python
from transformers import CLIPVisionModelWithProjection

image_encoder = CLIPVisionModelWithProjection.from_pretrained(
    "h94/IP-Adapter",
    subfolder="models/image_encoder",
    torch_dtype=torch.float16
)

pipeline = AutoPipelineForText2Image.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    image_encoder=image_encoder,
    torch_dtype=torch.float16
).to("cuda")

pipeline.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="sdxl_models",
    weight_name="ip-adapter-plus_sdxl_vit-h.safetensors"
)
```

### Pre-computed Image Embeddings (Reuse Pattern)

When running the same image through multiple prompts, pre-compute embeddings once:

```python
image_embeds = pipeline.prepare_ip_adapter_image_embeds(
    ip_adapter_image=image,
    ip_adapter_image_embeds=None,
    device="cuda",
    num_images_per_prompt=1,
    do_classifier_free_guidance=True,
)
torch.save(image_embeds, "image_embeds.ipadpt")

# Later — load and reuse
pipeline.load_ip_adapter(
    "h94/IP-Adapter", subfolder="sdxl_models",
    image_encoder_folder=None,
    weight_name="ip-adapter_sdxl.bin"
)
pipeline.set_ip_adapter_scale(0.8)

image_embeds = torch.load("image_embeds.ipadpt")
output = pipeline(
    prompt="a polar bear sitting in a chair drinking a milkshake",
    ip_adapter_image_embeds=image_embeds,
    negative_prompt="deformed, ugly, wrong proportion, low res, bad anatomy, worst quality, low quality",
).images[0]
```

### Advanced: Binary Masking for Multi-Image Composition

Use `IPAdapterMaskProcessor` to assign different IP-Adapter images to specific regions:

```python
from diffusers.image_processor import IPAdapterMaskProcessor

mask1 = load_image("https://.../mask1.png")
mask2 = load_image("https://.../mask2.png")

processor = IPAdapterMaskProcessor()
masks = processor.preprocess([mask1, mask2], height=1024, width=1024)

# Load face model with multiple adapters
pipeline.load_ip_adapter(
    "h94/IP-Adapter", subfolder="sdxl_models",
    weight_name=["ip-adapter-plus-face_sdxl_vit-h.safetensors"]  # list for multi
)
pipeline.set_ip_adapter_scale([[0.7, 0.7]])

output = pipeline(
    prompt="2 girls",
    ip_adapter_image=[[face_image1, face_image2]],
    cross_attention_kwargs={"ip_adapter_masks": masks},
).images[0]
```

### Applications

1. **Image-to-Image** — Use `AutoPipelineForImage2Image` with `ip_adapter_image` parameter
2. **Inpainting** — Masks work naturally with IP-Adapter
3. **Video** — Frame-by-frame consistent IP-Adapter conditioning
4. **Structural Control** — Combine IP-Adapter + ControlNet (depth/edge/pose) for both style and structure:
   ```python
   from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
   controlnet = ControlNetModel.from_pretrained("lllyasviel/control_v11f1p_sd15_depth")
   pipeline = StableDiffusionControlNetPipeline.from_pretrained(
       "stable-diffusion-v1-5/stable-diffusion-v1-5",
       controlnet=controlnet
   ).to("cuda")
   pipeline.load_ip_adapter("h94/IP-Adapter", subfolder="models", weight_name="ip-adapter_sd15.bin")
   ```
5. **Instant Generation** — IP-Adapter + LCM LoRA = 4-step generation
6. **Multi-IP-Adapter** — Combine FaceID + Style adapters with per-adapter scale control
7. **Style & Layout Control** — IP-Adapter + InstantStyle for block-level style injection

### Per-Layer Scale Control

IP-Adapter can be activated only in specific UNet layers using a dict-based scale:

```python
scale = {
    "down": {"block_2": [0.0, 1.0]},      # layout info injection
    "up": {"block_0": [0.0, 1.0, 0.0]},    # style injection
}
pipeline.set_ip_adapter_scale(scale)
```

Layers not included default to 0.0 (disabled). Down block 2 controls layout; up block 0 controls style.

### Flux IP-Adapter

Flux models also support IP-Adapter via `XLabs-AI/flux-ip-adapter`:

```python
from diffusers import FluxPipeline
pipe = FluxPipeline.from_pretrained("black-forest-labs/FLUX.1-dev", torch_dtype=torch.bfloat16)
pipe.load_ip_adapter("XLabs-AI/flux-ip-adapter", weight_name="ip_adapter.safetensors")
pipe.set_ip_adapter_scale(1.0)
pipe.to("cuda")
output = pipe(
    prompt="a cat wearing a hat",
    ip_adapter_image=image,
    guidance_scale=3.5,
).images[0]
```

### Key Insights

1. **Lightweight and modular** — IP-Adapter is ~100MB vs a full LoRA at ~150MB. No base model modification.
2. **Swappable at inference** — Unlike LoRA which requires `fuse_lora()` or separate pipelines, IP-Adapter can be hot-swapped with `load_ip_adapter()` between generations.
3. **Scale is critical** — `set_ip_adapter_scale(0.5)` gives best balance for most prompts. Too high (0.9+) overpowers text prompt.
4. **FaceID requires InsightFace** — `pip install insightface` for FaceID models. They use ID embeddings instead of CLIP.
5. **Memory optimization** — Use `enable_model_cpu_offload()` when combining IP-Adapter + ControlNet or multiple adapters.
6. **Scheduler matters** — DDIMScheduler and EulerDiscreteScheduler give best results with IP-Adapter, especially for face models.
7. **Plus variant needs custom image encoder** — Must pass a CLIPVisionModelWithProjection to the pipeline; standard variant uses the model's built-in encoder.
8. **Binary masking unlocks composition** — The IPAdapterMaskProcessor enables region-specific image conditioning within a single generation.

### References
- https://huggingface.co/docs/diffusers/en/using-diffusers/ip_adapter
- https://huggingface.co/h94/IP-Adapter
- https://huggingface.co/h94/IP-Adapter-FaceID
- https://huggingface.co/XLabs-AI/flux-ip-adapter
- https://arxiv.org/abs/2308.06721 (IP-Adapter paper)
- https://huggingface.co/docs/diffusers/en/api/loaders/ip_adapter


---

## Entry 70: Mamba & Hybrid SSM Architectures — Transformers Integration

**Date:** 2026-07-23
**Topic:** `hf-transformers-mamba-hybrid-architectures` — Deep dive on State Space Model support in Transformers (Mamba, Jamba, Zamba)

### Overview

Transformers v5.14.0 supports three distinct SSM-based architectures:

| Architecture | Type | Developer | Classes | Key Innovation |
|-------------|------|-----------|---------|----------------|
| **Mamba** | Pure SSM | Albert Gu & Tri Dao | `MambaModel`, `MambaForCausalLM`, `MambaConfig` | Selective scan (S6) — linear-time, no attention |
| **Jamba** | Mamba + Attention + MoE | AI21 Labs | `JambaModel`, `JambaForCausalLM`, `JambaConfig` | Interleaved SSM/attention layers + Mixture-of-Experts |
| **Zamba** | Shared Attention + Mamba | Zyphra | `ZambaModel`, `ZambaForCausalLM`, `ZambaConfig` | Single shared attention layer surrounded by Mamba blocks |

### Mamba — Pure SSM Architecture

The original Mamba architecture replaces self-attention entirely with structured state space models (S4 derivative with selective scan algorithm).

**Core Principles:**
- **State space model (SSM):** Maps a 1D input sequence to output via a hidden state, parameterized by matrices A, B, C
- **Selective scan (S6):** Key innovation — makes SSM parameters input-dependent (selection mechanism), enabling content-aware reasoning
- **Hardware-efficient parallel scan:** Unlike RNNs which process sequentially, Mamba uses a parallel associative scan (with `torch.compile` optimization)
- **Conv1d + SiLU + SSM:** Each Mamba block: layer norm → depthwise conv1d → SiLU activation → SSM → gated output

**Linear complexity:** O(n) vs O(n²) for attention — crucial for long sequences.

**Transformers API:**
```python
from transformers import MambaConfig, MambaForCausalLM

config = MambaConfig(vocab_size=50280, hidden_size=768, num_hidden_layers=24, state_size=16)
model = MambaForCausalLM(config)

# Or load pretrained
model = MambaForCausalLM.from_pretrained("state-spaces/mamba-130m-hf")
```

**Inference with cache (sequential decoding):**
```python
# First forward pass
outputs = model(input_ids)
cache = outputs.cache_params

# Subsequent token generation
next_token_logits = outputs.logits[:, -1, :]
next_token = next_token_logits.argmax(dim=-1, keepdim=True)
outputs = model(next_token, cache_params=cache)
```

**Forward Parameters:**
- `input_ids` — token indices
- `attention_mask` — padding mask
- `inputs_embeds` — direct embeddings alternative
- `cache_params` — previous SSM state (for recurrent decoding)
- `labels` — for language modeling loss (shifted internally)
- `output_hidden_states` — return all layer states
- `use_cache` — return cache params for next step
- `logits_to_keep` — only compute last N logits (memory saving — critical for large vocab sizes)

**Key config parameters (`MambaConfig`):**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `state_size` | 16 | SSM state expansion factor |
| `conv_kernel` | 4 | Conv1d kernel size |
| `expand_factor` | 2 | Inner dimension expansion (FFN) |
| `use_bias` | False | Whether to use bias in linear layers |
| `use_conv_bias` | True | Whether to use bias in conv1d |
| `hidden_act` | "silu" | Activation function |
| `tie_conv_bias` | True | Tie conv bias across channels |

### Jamba — Mamba + Attention + MoE Hybrid

Jamba (AI21 Labs, Jan 2024) interleaves Mamba SSM layers with standard multi-head attention layers and adds Mixture-of-Experts.

**Architecture Pattern:**
Every Nth layer is an attention layer; remaining layers use Mamba. Each layer uses MoE FFN with top-2 routing.

**Benefits:**
- Mamba layers handle long-context efficiency (linear complexity)
- Attention layers maintain recall quality (retrieval of distant patterns)
- MoE expands model capacity without proportional compute

**Both cache types:** Jamba maintains both `past_key_values` (for attention layers — standard KV cache) and SSM state (for Mamba layers). This is unique among Transformers models.

**Forward uniqueness — `output_router_logits`:**
Jamba's forward accepts `output_router_logits` — returns per-token router probabilities for each MoE layer (auxiliary load-balancing loss during training).

### Zamba — Shared Attention + Mamba Blocks

Zamba (Zyphra, Feb 2024) uses a single shared attention layer that all Mamba blocks connect to.

**Architecture:**
```
[Mamba Block → Shared Attention] × N layers
```

Key insight: share one attention module across the entire depth. Mamba blocks process most sequence; shared attention provides global context injection.

**Available models on HF Hub:**
- `Zyphra/Zamba-7B-v1` — 7B parameter hybrid
- `Zyphra/Zamba-1.2B-v1` — 1.2B parameter hybrid

### Usage Comparison

| Aspect | Mamba (pure SSM) | Jamba (hybrid) | Zamba (shared) |
|--------|-----------------|----------------|----------------|
| Complexity | O(n) | O(n) Mamba + O(n²) attention | O(n) with periodic O(n²) |
| KV cache needed? | No (SSM state) | Yes + SSM state | Shared attention KV |
| Best for | Long context, efficiency | Quality + efficiency | Small footprint models |

### Key Insights

1. **SSM state replaces KV cache for Mamba layers** — uses `cache_params` instead of `past_key_values`. Compact state vector growing with `state_size × hidden_size`, not sequence length.
2. **Hybrid models use two cache systems simultaneously** — Jamba maintains both `past_key_values` (attention) and `cache_params` (Mamba).
3. **`logits_to_keep` is critical for memory in Mamba** — long-sequence models benefit from only computing last-token logits.
4. **Zamba's shared attention is the most parameter-efficient hybrid design** — 1 attention layer vs 32 in standard Transformer.
5. **Mamba requires `torch>=2.0`** for `torch.compile` and selective scan ops.
6. **The MoE in Jamba is load-balanced** — auxiliary loss (router_z_loss, aux_loss) prevents expert collapse.
7. **LinearAttentionLayer API in Transformers 5.x** supports generic SSM/attention hybrid layers with `update_conv_state()` and `update_recurrent_state()` methods.

### References
- https://huggingface.co/docs/transformers/en/model_doc/mamba
- https://huggingface.co/docs/transformers/en/model_doc/jamba
- https://huggingface.co/docs/transformers/en/model_doc/zamba
- https://arxiv.org/abs/2312.00752 (Mamba paper)
| - https://github.com/state-spaces/mamba
|- https://arxiv.org/abs/2405.16712 (Zamba paper)
|- https://github.com/state-spaces/mamba

---

## Entry 9: Big Model Inference — Accelerate device_map, Empty Weights Init & Quantization for Fitting Any Model on Any Hardware
**Date:** 2026-07-23
**Topic:** `hf-transformers-empty-weights-device-map-inference` — Techniques for running models exceeding available VRAM via init_empty_weights + load_checkpoint_and_dispatch + quantization

### Overview

Big Model Inference (part of the `accelerate` library) enables loading and running models whose total size exceeds single-GPU VRAM. It combines three techniques:

1. **`init_empty_weights()`** — creates a model skeleton without allocating memory for parameters
2. **`load_checkpoint_and_dispatch()`** — loads real weights and intelligently places layers across devices
3. **Quantization + dtype reduction** — shrinks each parameter's footprint via lower precision

The key insight: **as long as the largest single layer fits on your GPU, you can run any model** — Accelerate handles CPU offload, disk offload, and multi-GPU dispatch automatically.

### Core API — Accelerate (low-level)

```python
from accelerate import init_empty_weights, load_checkpoint_and_dispatch

with init_empty_weights():
    my_model = ModelClass(...)  # no memory allocated

model = load_checkpoint_and_dispatch(
    my_model,
    checkpoint=checkpoint_file,   # safetensors state_dict
    device_map="auto",           # fills GPU(s) → CPU → disk
    no_split_module_classes=["LlamaDecoderLayer"],  # don't split these
)
```

### Device Map Strategies

| Strategy | Behaviour | Best for |
|----------|-----------|----------|
| `device_map="auto"` | Fill fastest device (GPU/MPS/XPU) first, then CPU, then disk | General use, no tuning needed |
| `device_map="balanced"` | Distribute layers equally across all visible devices | Multi-GPU with similar memory |
| `device_map="sequential"` | Fill device 0 completely, then device 1, etc. | Heterogeneous GPUs |
| `device_map={0: "10GiB", 1: "5GiB", "cpu": "40GiB"}` | Manual per-device allocation | Precise memory control |
| `device_map="mps"` | Force Apple Silicon (Metal) | MPS-only inference |
| `device_map="cuda:0"` | Force single GPU without offloading | Model fits one GPU |
| `device_map="disk"` | All layers on disk, load on demand | Emergency — model doesn't fit RAM+CPU+GPU combined |

**Priority order for `"auto"`:** GPU → MPS → XPU → NPU → MLU → SDAA → MUSA → CPU → disk.

### Custom max_memory

Constrains per-device budgets (with unit suffixes):

```python
max_memory = {0: "12GiB", 1: "12GiB", "cpu": "48GiB"}
model = load_checkpoint_and_dispatch(model, device_map="balanced", max_memory=max_memory)
```

### Integration in Transformers (high-level)

The cleanest path: `from_pretrained(device_map="auto")` — this internally triggers the same empty-init + dispatch pipeline:

```python
from transformers import AutoModelForCausalLM

# Single line — Accelerate handles the rest
model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2-9b",
    device_map="auto",                  # dispatches across available devices
    torch_dtype=torch.bfloat16,         # half-precision halves memory
)

# Explicit max_memory also works:
model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2-9b",
    device_map="auto",
    max_memory={0: "8GiB", "cpu": "32GiB"},
    torch_dtype=torch.bfloat16,
)
```

### Quantization + Device Map (combined)

The `quantization_config` + `device_map="auto"` combo is **the zero-cost inference superpower** — especially for free/constrained environments:

```python
from transformers import BitsAndBytesConfig, AutoModelForCausalLM

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",          # NormalFloat4 — best quality for 4-bit
    bnb_4bit_compute_dtype=torch.bfloat16,
    bnb_4bit_use_double_quant=True,      # QLoRA-style double quantization
)

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B-Instruct",
    device_map="auto",                   # fits on 8GiB GPU after 4-bit
    quantization_config=bnb_config,
)
```

**Memory implications by quantization type:**

| Quantization | Type | Memory vs FP16 | Use case |
|---|---|---|---|
| `load_in_8bit` | int8 (LLM.int8()) | ~50% | Older GPUs, no calibration needed |
| `load_in_4bit` (nf4) | 4-bit NF4 | ~25% | Best quality/size ratio |
| `load_in_4bit` (fp4) | 4-bit FP4 | ~25% | Slightly lower quality than NF4 |
| `bnb_4bit_use_double_quant=True` | NF4 + DDQ | ~22% | QLoRA training (tiny extra savings) |
| GPTQ (`GPTQConfig`) | 2/3/4/8-bit | ~25-50% | Pre-quantized models need calibration dataset |
| AWQ (`AwqConfig`) | 4-bit | ~25% | Activation-aware; pre-quantized models only |
| HQQ (`HqqConfig`) | 1-8 bit | ~12-50% | Offline quantization, no calibration data needed |
| Quanto (`QuantoConfig`) | int2/int4/int8/float8 | ~12-50% | Flexible, supports float8 activations |
| TorchAO | int4/int8/float8 | ~25-50% | Native PyTorch quant; no extra dependencies |

### Layer Dispatch Mechanics

When `device_map="auto"` dispatches layers:

- **GPU layers**: weights stay resident on GPU, activations remain in fast memory
- **CPU layers**: weights on CPU, copied to GPU one layer at a time on forward pass, then freed → adds inference latency
- **Disk layers**: weights on disk, loaded into CPU → GPU on forward pass → **slowest** (only for emergency)
- **no_split_module_classes**: prevents splitting critical layers (e.g., decoder blocks with residual connections that need full state)

**Critical constraint**: only one GPU is active at a time during dispatched inference (sequential passes between GPUs). For parallel multi-GPU, use pipeline parallelism instead (see `accelerate` PP guide).

### Memory Estimation Recipe

Before attempting to load a model, estimate its memory footprint:

```python
# Using Accelerate's estimator
from accelerate.utils import calculate_maximum_sizes

# Manual: FP16 = 2 bytes/param, FP32 = 4 bytes
# 7B params × 2 bytes (FP16) = 14 GB
# 7B params × 0.5 bytes (4-bit) = 3.5 GB
# + ~20% overhead for activations + optimizer states (training only)
# + KV cache during generation (~2 MB per token for 7B @ FP16)
```

### Putting It All Together — The "Fit Anything" Pattern

```python
from transformers import (
    AutoModelForCausalLM, AutoTokenizer,
    BitsAndBytesConfig
)

model_id = "meta-llama/Llama-3.1-70B-Instruct"

# Strategy 1: 4-bit + device_map auto → 70B on 24GB card
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
    ),
)

# Strategy 2: max_memory constraints + multi-device
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="sequential",
    max_memory={
        0: "16GiB",    # GPU 0
        1: "16GiB",    # GPU 1
        "cpu": "64GiB" # remainder on CPU
    },
    torch_dtype=torch.float16,
)

# Strategy 3: disk offload (emergency — model exceeds RAM)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",
    offload_folder="offload",
    offload_state_dict=True,
    torch_dtype=torch.float16,
)
```

### Pitfalls & Gotchas

1. **`device_map` vs `device` are mutually exclusive** — use `device_map="auto"` for multi-device, `device=0` for single GPU. Passing both raises an error.
2. **Quantized models + device_map auto** — bitsandbytes quantizers auto-set device_map to "auto" if not provided, overriding any explicit `device` setting.
3. **First inference is slow** — Accelerate computes dispatch the first time, and CPU/disk-offloaded layers need to transfer data. Warm up with a short prompt.
4. **no_split_module_classes must match model architecture** — for Llama it's `LlamaDecoderLayer`, for Gemma it's `GemmaDecoderLayer`, etc. Mismatch causes split across critical layer boundaries.
5. **Disk offload can fill your disk** — each forward pass writes intermediate activations. Monitor `offload_folder` size.
6. **Pipeline parallelism vs device_map** — `device_map` uses sequential GPU pass (only one GPU active at a time). For true simultaneous multi-GPU throughput, use `accelerate` pipeline parallelism or DeepSpeed inference.
7. **`load_in_8bit` + CPU offload** — `llm_int8_enable_fp32_cpu_offload=True` keeps CPU weights in FP32 while GPU weights stay in int8. The int8 matmul kernels only run on GPU.

### Key Insights

- `device_map="auto"` + `quantization_config` = **the most important pattern for fitting large models on free/constrained hardware** (e.g., T4 15GB → run 70B models at 4-bit with CPU offload).
- `init_empty_weights()` is the low-level mechanism; `from_pretrained(device_map="auto")` wraps it for 99% of use cases.
- `max_memory` provides fine-grained control when `device_map="auto"` fills devices suboptimally.
- NF4 (bitsandbytes) is the recommended 4-bit quantization for dynamic loading (no calibration needed). GPTQ/AWQ require pre-quantized checkpoints but run faster.
- Quanto's float8 activation support is unique among HF quantizers — useful for inference throughput on H100/B200 hardware with native FP8 Tensor Cores.

### References
- https://huggingface.co/docs/accelerate/en/usage_guides/big_modeling
- https://huggingface.co/docs/transformers/en/main_classes/quantization
- https://huggingface.co/docs/accelerate/en/usage_guides/device_map
|- https://huggingface.co/blog/4bit-transformers-bitsandbytes

---

## Entry 25: torch.compile — GPU Inference Optimization with PyTorch Compiler
**Date:** 2026-07-23
**Topic:** `hf-transformers-torch-compile-deep-dive` — Complete reference on using torch.compile with Transformers for 30-70% inference speedup

### Overview

`torch.compile` compiles PyTorch code into optimized kernels that significantly speed up inference. It is the **primary recommended optimization** for GPU inference in Transformers v5.14.0+. It relies on two components:

- **TorchDynamo**: captures PyTorch computation graphs safely and efficiently (no monkey-patching, works at frame level via CPython's PEP 523)
- **TorchInductor**: compiles captured graphs into optimized GPU kernels using Triton (default backend) or other backends

In many cases, adding `torch.compile` is a **single line of code** that yields 30-70% speedup on GPU.

### Basic Usage

```python
from transformers import AutoModelForCausalLM
import torch

model = AutoModelForCausalLM.from_pretrained(
    "google/gemma-2b", device_map="auto"
)
compiled_model = torch.compile(model)
```

**Important:** The first call is slow (compilation happens). Subsequent calls are much faster because the compiled graph is cached.

### Modes

The `mode` parameter controls the optimization tradeoff:

| Mode | Speed | Compile Time | Memory | Use Case |
|------|-------|-------------|--------|----------|
| `"default"` | Balanced | Moderate | Moderate | General-purpose, safe default |
| `"reduce-overhead"` | Faster | Slightly longer | Slightly higher | Production inference, batch workloads |
| `"max-autotune"` | Fastest | Very long (minutes) | Highest | Max throughput for fixed-size inputs |

```python
compiled_model = torch.compile(model, mode="reduce-overhead")
```

**Recommendation:** Start with `"reduce-overhead"` for most production inference scenarios. `"max-autotune"` is for deployment where compile-time cost is amortized over millions of calls.

### Fullgraph Mode

`fullgraph=True` forces the entire model into a single graph. If a graph break occurs (e.g., Python control flow that Dynamo can't trace), `torch.compile` raises an error rather than falling back to eager mode for the untraceable parts.

```python
compiled_model = torch.compile(model, mode="reduce-overhead", fullgraph=True)
```

**Pitfall:** Not all Transformers models support fullgraph — graph breaks are common in models with conditional control flow (e.g., branching in generation loops). Test with your specific model first.

### Integration with Transformers Features

| Feature | Works with torch.compile? | Notes |
|---------|--------------------------|-------|
| StaticCache | ✅ Native | StaticCache was designed for compiled inference; pre-allocated KV cache tensors are export-friendly |
| DynamicCache | ⚠️ Partial | May cause recompilation on shape changes |
| FlashAttention2 | ✅ Compatible | SDPA + FlashAttention2 backend works inside compiled graphs |
| SDPA (default) | ✅ Fully compatible | Most tested path |
| generate() | ✅ Works | The generate loop compiles; use StaticCache for best results |
| device_map="auto" | ✅ Works | Compiled model respects device placement |
| bitsandbytes 4-bit | ⚠️ Partial | Quantized modules may cause graph breaks in some configs |
| LoRA adapters | ⚠️ Partial | Adapter switching causes recompilation (use hotswap + compile after) |

### Compatibility with Caching Strategies

**StaticCache** is the recommended cache format when using `torch.compile`:

```python
from transformers import StaticCache

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    device_map="auto",
    attn_implementation="sdpa"
)
model.generation_config.cache_implementation = "static"
compiled_model = torch.compile(model, mode="reduce-overhead")
```

**Why StaticCache:** It allocates fixed-size tensors for the KV cache, which avoids recompilation due to changing sequence lengths. Without StaticCache, every new sequence length can trigger recompilation in the attention module.

### Performance Benchmarks (from HF docs)

For vision models on NVIDIA GPUs with batch processing:
- **Mean inference time reduction:** 30-50% with `reduce-overhead` mode
- **Larger speedups at larger batch sizes** — compilation overhead is amortized
- **Fullgraph mode** gives additional ~5-10% over `reduce-overhead`

For LLMs (causal LM):
- **Text generation:** 1.5-2x tokens/second improvement on supported architectures
- **Prefill phase:** 40-60% faster with compiled attention
- **Decode phase:** 20-30% faster per generated token

### Cross-Model Compatibility

| Architecture | Status | Notes |
|-------------|--------|-------|
| Llama 3.x / 4 | ✅ Native | Best-supported, most tested |
| Gemma 2/3 | ✅ Native | Official examples use Gemma |
| Mistral | ✅ Native | Same architecture family as Llama |
| Qwen2 | ✅ Native | Verified compatible |
| Falcon | ⚠️ Partial | May have graph breaks in attention |
| MPT | ⚠️ Partial | Custom attention may need workarounds |
| Mamba-based | ❌ Not compatible | Selective scan ops are not Dynamo-traceable |
| Mixture-of-Experts | ⚠️ Partial | Routing logic may cause graph breaks |

### Export Pipeline (torch.compile → torch.export)

For production deployment, you can trace a compiled model to a deployable artifact:

```python
exported_program = torch.export.export(
    compiled_model,
    (input_ids,),
    dynamic_shapes={"input_ids": {0: torch.export.Dim.DYNAMIC}}
)
```

This produces a **graph module** that can be run without the Python runtime — ideal for serving with C++, TorchServe, or ONNX export from the traced graph.

### Key Insights

- **torch.compile is complementary to quantization:** use 4-bit to fit the model in GPU memory, then compile for speed
- **The compilation penalty is per-model, not per-input:** pay once, benefit forever within the same session
- **StaticCache is the most important companion optimization** — it prevents costly recompilations during generation
- **Not all models benefit equally:** models with simple decoder-only architectures (Llama, Gemma) benefit most; models with complex branching (encoder-decoder, multimodal fusion) see less gain
- **torch.compile works with ZeroGPU spaces** — the AOTI (Ahead-of-Time Inductor) export path is used by HF ZeroGPU for precompiled Spaces

### Common Pitfalls

1. **Tensor shape changes cause recompilation** — use StaticCache + pad inputs to fixed lengths
2. **`output_attentions=True` breaks compilation** — attention weights as tensors can't be part of the compiled graph
3. **First-call latency is misleading** — time only subsequent calls for benchmarks
4. **Not all GPUs support Triton kernels** — older GPUs (Pascal, Maxwell) fall back to eager mode silently
5. **`max-autotune` can OOM** — the autotuning process allocates significant extra memory for benchmarking candidate kernels

### References
- https://huggingface.co/docs/transformers/main/en/perf_torch_compile
- https://pytorch.org/docs/stable/compile.html
- https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one
- https://huggingface.co/docs/transformers/main/en/llm_tutorial_optimization

## Entry 76: GRPO Trainer — Deep Dive for Reasoning RL
**Date:** 2026-07-23
**Topic:** `hf-trl-grpo-deep-dive` — Complete reference on the TRL `GRPOTrainer` for reinforcement learning on reasoning tasks

### Overview

GRPO (Group Relative Policy Optimization) is TRL's implementation of the RL algorithm introduced in the **DeepSeekMath** paper. It is an **online learning algorithm** — it improves iteratively by using data generated by the trained model itself during training. Unlike PPO, GRPO eliminates the need for a separate value function model (critic), saving ~50% memory on the reference model.

The intuition: for each prompt, generate **G completions**, compute their rewards, normalize them within the group to get an advantage, then optimize the policy to increase the probability of high-advantage tokens while staying close to the reference policy.

### Core Algorithm (4 Steps)

1. **Generating completions:** Sample a batch of prompts, generate `G` completions per prompt (denoted `o_i`).

2. **Computing the advantage:** For each completion, compute reward via a reward model or reward function. Normalize within the group:
   ```
   Â_i,t = (r_i - mean(r)) / std(r)
   ```
   This group-relative normalization gives the method its name.

3. **Estimating KL divergence:** Uses Schulman et al. (2020) approximator to keep the policy close to the reference model.

4. **Computing the loss:** Maximize the advantage while penalizing KL divergence from the reference policy.

### Quick Start

```python
from datasets import load_dataset
from trl import GRPOTrainer
from trl.rewards import accuracy_reward

dataset = load_dataset("trl-lib/DeepMath-103K", split="train")
trainer = GRPOTrainer(
    model="Qwen/Qwen2.5-0.5B-Instruct",
    reward_funcs=accuracy_reward,
    train_dataset=dataset,
)
trainer.train()
```

Launch with: `accelerate launch train_grpo.py` (distributed across 8 GPUs, ~1 day for 0.5B).

### Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_generations` | 8 | Number of completions per prompt (G) |
| `beta` | 0.0 | KL penalty coefficient (0 = no KL term, recent papers show it's optional) |
| `loss_type` | `"grpo"` | Options: `"grpo"`, `"dapo"`, `"dr_grpo"`, `"sapo"` |
| `scale_rewards` | True | Normalize by std(r). Can also set to `"batch"` for batch-level scaling |
| `use_vllm` | False | Use vLLM for accelerated generation |
| `vllm_mode` | `"colocate"` | `"colocate"` (same GPU) or `"server"` (separate process) |
| `num_iterations` | 1 | Number of policy updates per generation round (μ) |
| `entropy_coef` | 0.0 | Entropy bonus coefficient for exploration |
| `use_adaptive_entropy` | False | Adaptive entropy from Skywork-OR1 |

### Loss Types

Four loss formulations supported via `loss_type`:

1. **`"grpo"` (original):** Sample-level normalization — `1/G * Σ 1/|o_i| * Σ l_i,t`. Introduces response length bias (longer sequences under-penalized).

2. **`"dapo"`:** Token-level normalization — `1/Σ|o_i| * Σ Σ l_i,t`. Fixes the long-CoT under-penalization issue from DAPO paper.

3. **`"dr_grpo"`:** Constant-divisor normalization — `1/(L*G) * Σ Σ l_i,t` where L = max completion length. Fully removes length bias as shown in "Understanding R1-Zero-Like Training" paper.

4. **`"sapo"`:** Soft attention policy optimization — replaces hard clipping with temperature-controlled soft gating. Uses asymmetric temperatures (τ_neg > τ_pos defaults 1.05 vs 1.0) to penalize bad actions more strictly.

### vLLM Integration for Speed

Generation is the main bottleneck in online RL. Two modes:

- **Colocate mode** (default): vLLM runs inside the trainer process, shares GPU memory. Simple setup but potential memory contention.

- **Server mode:** vLLM runs in a separate process on a dedicated node. Required for multi-node training of 70B+ models (vLLM on one node, training on others).

**Truncated Importance Sampling (TIS):** Activated by default when using vLLM. Corrects for the training-inference mismatch caused by vLLM and training engine producing slightly different outputs (precision effects, hardware optimizations). TIS clips importance weights to `[C_min, C_max]`. Masked Importance Sampling (MIS) sets out-of-range ratios to zero instead.

### Transformers Continuous Batching (Alternative to vLLM)

Built-in continuous batching removes finished sequences immediately. Drop-in upgrade, no server setup:
```python
training_args = GRPOConfig(
    use_transformers_continuous_batching=True,
    transformers_continuous_batching_config={
        "use_cuda_graph": False,
        "max_memory_percent": 0.4,
    }
)
```
Best for single-GPU or memory-constrained environments. vLLM is better for maximum throughput at scale.

### Custom Reward Functions

Reward functions are Python callables (sync or async) accepting `prompts`, `completions`, `completion_ids`, plus dataset columns as kwargs. Must return `list[float]`.

**Patterns:**
- **Format reward:** Check for `<think>...</think><answer>...</answer>` structure (DeepSeek-R1 style)
- **Accuracy reward:** Extract `\boxed{}` content and compare to ground truth
- **Multi-task:** Return `None` for irrelevant tasks — GRPOTrainer ignores them
- **Async functions:** Run concurrently via `asyncio.gather` — useful for HTTP-based rewards
- **Logging:** Use `log_extra()` for completions table columns, `log_metric()` for scalar plots

### Agent Training

GRPO supports **tool use and environment-based training**:

- **Tools:** Plain Python functions with type hints + Google-style docstrings. Model calls them during generation.
- **Environments:** Stateful objects with `reset()` method that self-sample tasks. The environment can own the reward via `get_reward()`.
- **Composition:** Standalone tools + environment_factory work together.

### Multi-Node Scaling (70B+)

Example SLURM setup for training a 70B model: 4 training nodes + 1 vLLM node. Uses DeepSpeed ZeRO-3 for model state distribution across GPUs.

### Entropy Regularization

Two modes:
- **Static:** Fixed `entropy_coef` throughout training
- **Adaptive** (Skywork-OR1 style): Updates coefficient based on target entropy. When current entropy ≤ `entropy_target`, increment coefficient by `entropy_coef_delta`; otherwise decrement. Typical per-token entropy is 2–10 nats for language models.

### Key Insights

- **GRPO is memory-efficient vs PPO** — no critic model to store. Frees ~50% of reference model memory.
- **KL term (beta) is often zero** in practice — recent papers (Open-Reasoner-Zero, DAPO, Understanding R1-Zero-Like Training) show it's not essential for GRPO.
- **Loss type matters for long-CoT:** DAPO > GRPO for long chain-of-thought reasoning; Dr. GRPO is theoretically cleanest.
- **TIS is essential with vLLM** — without importance sampling correction, the train-inference mismatch destabilizes training.
- **Tool-use chat templates need prefix-preserving tokenizers** — TRL auto-patches known model families (Qwen3, DeepSeek-V3) when tools are enabled.

### References
- https://huggingface.co/docs/trl/en/grpo_trainer
- https://arxiv.org/abs/2402.03300 (DeepSeekMath - original GRPO paper)
- https://arxiv.org/abs/2503.14499 (DAPO: Dynamic Sampling and Policy Optimization)
- https://arxiv.org/abs/2502.03312 (Understanding R1-Zero-Like Training)
- https://arxiv.org/abs/2504.07645 (Skywork-OR1: Adaptive Entropy)
- https://arxiv.org/abs/2503.14499 (SAPO: Soft Attention Policy Optimization)

## Entry 77: Nunchaku 4-bit Diffusion Inference in Diffusers
**Date:** 2026-07-23
**Topic:** `hf-diffusers-nunchaku-svdquant` — SVDQuant-based W4A4 diffusion inference via Nunchaku Lite, natively in Diffusers

### Overview

Nunchaku is the reference CUDA inference engine for **SVDQuant**, a 4-bit quantization method targeting diffusion transformers (DiTs). The key innovation: SVDQuant moves activation outliers into the weights via a small 16-bit low-rank SVD correction branch, then quantizes the remaining residual to 4-bit (W4A4). This **reduces both memory and latency simultaneously** — unlike weight-only methods (AWQ, GPTQ) that only save memory.

**Nunchaku Lite** is the new Diffusers integration path (July 2026). It loads Nunchaku-style checkpoints without a custom pipeline or separate engine:
1. Patches stock `nn.Linear` modules with SVDQ/AWQ runtime linear layers
2. CUDA kernels come from the Hub via the `kernels` package
3. No local CUDA compilation required

### Two Kernel Families

| Kernel | Precision | Targets | Use case |
|--------|-----------|---------|---------|
| `svdq_w4a4` | INT4 or NVFP4 | Attention + MLP projections (compute-bound) | Nearly all transformer compute — W4A4 with low-rank correction |
| `awq_w4a16` | INT4 | Adaptive norm/modulation (memory-bound, precision-sensitive) | FLUX `adaNorm`, Qwen-Image modulation layers |

### Hardware Support

| Precision | GPUs |
|-----------|------|
| `svdq_w4a4` NVFP4 | Blackwell (RTX 50 series, RTX PRO 6000, B200) |
| `svdq_w4a4` INT4 | Turing/Ampere/Ada (RTX 30 & 40 series, A100, L40S) |
| `awq_w4a16` INT4 | Turing/Ampere/Ada (RTX 30 & 40 series, A100, L40S) |

Volta and Hopper are **not supported** by the 4-bit kernels.

### Usage

```bash
pip install -U diffusers transformers accelerate kernels bitsandbytes
```

```python
import torch
from diffusers import ErnieImagePipeline

pipe = ErnieImagePipeline.from_pretrained(
    "lite-infer/ERNIE-Image-Turbo-nunchaku-lite-nvfp4_r32-bnb4-text-encoder",
    torch_dtype=torch.bfloat16,
).to("cuda")

image = pipe("A cinematic portrait of a red fox", height=1024, width=1024,
             num_inference_steps=8, guidance_scale=1.0).images[0]
```

### Performance (RTX PRO 6000 Blackwell, 1024×1024)

| Configuration | Full pipeline | Denoise loop | Peak VRAM | Speedup |
|--------------|---------------|-------------|-----------|---------|
| BF16 baseline | 3.00 s | 2.86 s | 31.1 GB | 1.0× |
| Nunchaku Lite NVFP4 | 2.27 s | 2.13 s | 20.6 GB | 1.35× |
| NVFP4 + `torch.compile` | 1.68 s | 1.53 s | 20.6 GB | **1.8×** |
| NVFP4 + NF4 text encoder | 2.29 s | 2.13 s | 16.0 GB | 1.35× |

### Quantizing Your Own Model

The `diffuse-compressor` toolkit provides an end-to-end workflow: calibrate → quantize → package → publish.

```bash
# Inspect first
python examples/text_to_image/quantize_hf.py black-forest-labs/FLUX.2-klein-4B \
  --precision int4 --rank 32 --inspect-config

# Quantize
python examples/text_to_image/quantize_hf.py black-forest-labs/FLUX.2-klein-4B \
  --precision int4 --output outputs/checkpoints/svdq-int4_r32-flux-2-klein-4b.safetensors

# Package as Diffusers pipeline
python examples/convert_nunchaku_lite_diffusers.py \
  --checkpoint outputs/checkpoints/svdq-int4_r32-flux-2-klein-4b.safetensors \
  --model-id black-forest-labs/FLUX.2-klein-4B \
  --bnb4-text-encoder text_encoder \
  --compute-dtype bfloat16 \
  --output-dir outputs/diffusers/FLUX.2-klein-4B-nunchaku-lite-int4
```

The quantized model retains the exact module structure, so downstream features (schedulers, LoRA loading, offloading, `torch.compile`) all work natively.

### Key Insights

- SVDQuant is unique among 4-bit methods: it is **W4A4 not W4A16** — activations are also quantized, enabling actual throughput gains alongside memory savings
- The low-rank branch (rank 32 typical) captures activation outliers that standard 4-bit quantization cannot handle
- `torch.compile` on the quantized transformer improves speedup from 1.35× to 1.8×
- Together with bitsandbytes NF4 text encoders, peak VRAM drops from 31.1 GB (BF16) to 16.0 GB — **48% reduction**

### References
- https://huggingface.co/blog/nunchaku-diffusers
- https://arxiv.org/abs/2411.05007 (SVDQuant paper)
- https://github.com/nunchaku-tech/nunchaku (original inference engine)
- https://github.com/rootonchair/diffuse-compressor (quantization toolkit)
|- https://huggingface.co/kernels/rootonchair/nunchaku-lite-kernels (NVFP4 kernels on Hub)
|- https://huggingface.co/docs/diffusers/main/en/quantization/nunchaku

---

## Entry 8: Transformers Tool-Use / Function-Calling Chat Template — Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-transformers-tool-use-chat-template` — Complete reference on tool-use/function-calling via Transformers chat templates

### Overview

Transformers v5.14.0 provides a first-class tool-use (function-calling) API integrated directly into chat templates. Rather than relying on external libraries, the `apply_chat_template()` method accepts a `tools` parameter containing Python functions or JSON schemas, renders them into the model's expected tool-use format, and provides `parse_response()` for extracting structured tool calls from generated text.

The system has three layers:
1. **Tool definition** — Python functions or raw JSON schemas
2. **Tool rendering** — `apply_chat_template(messages, tools=tools)` injects tool definitions into the chat
3. **Response parsing** — `tokenizer.parse_response()` extracts structured tool_calls from model output

### Defining Tools

**Python functions (recommended):**
```python
def get_current_temperature(location: str, unit: str):
    """
    Get the current temperature at a location.

    Args:
        location: The location to get the temperature for, in the format "City, Country"
        unit: The unit for the temperature. Choices: ["celsius", "fahrenheit"]
    """
    return 22.  # Mock — real function would call a weather API

def get_current_wind_speed(location: str):
    """
    Get the current wind speed in km/h at a given location.

    Args:
        location: The location to get the wind speed for, in the format "City, Country"
    """
    return 6.

tools = [get_current_temperature, get_current_wind_speed]
```

**Key rules for Python functions:**
- Only **Google-style docstrings** are parsed (Args: block with parameter descriptions)
- The **function body is ignored** — only name, arguments, types, and docstring matter
- `self` and `cls` parameters are treated as implicit receivers and ignored
- A `Returns:` block and return type hint are optional and rarely used by models

**JSON schemas (explicit):**
```python
from transformers.utils import get_json_schema

schema = get_json_schema(multiply)
# Returns a dict with "type": "function", "function": { "name", "description", "parameters" }

# Or write JSON schemas directly:
tools = [{
    "type": "function",
    "function": {
        "name": "multiply",
        "description": "A function that multiplies two numbers",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"}
            },
            "required": ["a", "b"]
        }
    }
}]
```

### Tool-Calling Loop

The full tool-use cycle has 4 steps:

**Step 1 — Render tools into chat template:**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

checkpoint = "NousResearch/Hermes-2-Pro-Llama-3-8B"
tokenizer = AutoTokenizer.from_pretrained(checkpoint)
model = AutoModelForCausalLM.from_pretrained(checkpoint, dtype="auto", device_map="auto")

messages = [
    {"role": "user", "content": "What's the weather like in Paris?"},
]

inputs = tokenizer.apply_chat_template(
    messages, tools=tools, add_generation_prompt=True,
    return_dict=True, return_tensors="pt"
)
outputs = model.generate(**inputs.to(model.device), max_new_tokens=128)
response = tokenizer.decode(outputs[0][len(inputs["input_ids"][0]):])
# '<tool_call>\n{"arguments": {"location": "Paris, France", "unit": "celsius"}, "name": "get_current_temperature"}\n</tool_call>'
```

**Step 2 — Parse the tool call and append to history:**
```python
tool_call = {"name": "get_current_temperature", "arguments": {"location": "Paris, France", "unit": "celsius"}}
messages.append({
    "role": "assistant",
    "tool_calls": [{"type": "function", "function": tool_call}]
})
```

**Important API distinction:** Transformers' `tool_calls` expects a **dict** per call, not a JSON string. The OpenAI API uses JSON strings — using that format will cause errors or strange model behavior.

**Step 3 — Append tool response and generate final answer:**
```python
messages.append({"role": "tool", "content": "22"})  # content is always a string!

inputs = tokenizer.apply_chat_template(
    messages, tools=tools, add_generation_prompt=True,
    return_dict=True, return_tensors="pt"
)
out = model.generate(**inputs.to(model.device), max_new_tokens=128)
print(tokenizer.decode(out[0][len(inputs["input_ids"][0]):]))
# "The temperature in Paris, France right now is 22°C."
```

### Response Parsing API

Models that define a `response_template` in their tokenizer's chat template get structured response parsing:

**Basic parsing:**
```python
# Single sequence
parsed = tokenizer.parse_response(response_text, prefix=input_ids[0])
# Returns a structured dict with tool_calls

# Batch
parsed = tokenizer.parse_response([response_1, response_2], prefix=input_ids)
```

**Streaming parsing:**
```python
parser = tokenizer.get_response_parser(response_text, prefix=input_ids[0])

# Generator-style iteration:
for event in parser:
    # Events: partial text tokens, complete tool calls, final message
    if event["type"] == "function_call":
        print(f"Tool call: {event['name']}({event['arguments']})")
    elif event["type"] == "text":
        print(f"Text chunk: {event['content']}")
```

The `prefix` parameter tells the parser where the chat prompt ends so it can isolate the model's generated content. Without `prefix`, the parser doesn't know what's part of the prompt vs. the response.

**Pitfalls:**
- `parse_response()` raises an error if the tokenizer has no `response_template` set
- Not all models support `response_template` — check model card
- The `prefix` must be the original tokenized input IDs (not the decoded text) for accurate offset tracking

### Tool Call IDs and Multiple Calls

While the `tool_calls` key is a **list** (supporting multiple concurrent calls), most models emit a single tool call at a time. Some older models emit multiple simultaneous calls, which requires:
- Disambiguating calls with `tool_call_id`
- Handling multiple tool responses before the next model turn
- Checking the model card for expected format

```python
# Multi-call format:
messages.append({
    "role": "assistant",
    "tool_calls": [
        {"type": "function", "function": {"name": "func_a", "arguments": {"x": 1}}},
        {"type": "function", "function": {"name": "func_b", "arguments": {"y": 2}}}
    ]
})
```

### Chat Template Authorship

For model authors creating custom tool-use chat templates:

1. The `tools` parameter is rendered by `apply_chat_template()` and injected into the template's Jinja context as `{{ tools }}`
2. Tools are converted to JSON schema internally via `get_json_schema()` before rendering
3. The model's template must handle the `tools` variable to render tool definitions correctly
4. Response templates define how to parse model output into structured `tool_calls`

### Key Insights

- **`apply_chat_template(tools=...)` is the single entry point** — no separate preprocessing needed
- **Python functions are preferred** over raw JSON schemas — the docstring parser handles 90% of use cases
- **`parse_response()`** is the cleanest way to extract tool calls; manual string parsing of `<tool_call>` XML tags is fragile and model-specific
- **Tool responses use `role: "tool"`** — this is the Transformers-native role, equivalent to `role: "function"` in the OpenAI API
- **Content is always a string** in tool responses — cast numbers/bools to `str()` before appending
- **`tool_calls` expects dicts, not JSON strings** — OpenAI format JSON strings will cause errors
- **Streaming parsers** enable progressive UI updates during long generations
- **Model support varies** — models like Hermes-2-Pro-Llama-3-8B, Command-R, and Mixtral-8x22B have native tool-use support; always check the model card

### References
- https://huggingface.co/docs/transformers/en/chat_extras (Tool use section)
- https://huggingface.co/docs/transformers/en/chat_response_parsing
- https://huggingface.co/docs/transformers/en/chat_templating
- https://huggingface.co/docs/transformers/en/internal/tokenization_utils#transformers.PreTrainedTokenizerBase.apply_chat_template
- https://huggingface.co/docs/transformers/en/main_classes/pipelines#transformers.TextGenerationPipeline

---

## Entry 29: SDPA Attention Backend — Transformers GPU Inference Optimization
**Date:** 2026-07-23
**Topic:** `hf-transformers-sdpa-attention-backend` — PyTorch's SDPA (Scaled Dot Product Attention) backend in Transformers

### Overview

PyTorch's `torch.nn.functional.scaled_dot_product_attention` (SDPA) is a native, CUDA-optimized implementation of the scaled dot product attention mechanism. It is the **default attention backend** in Transformers for PyTorch v2.1.1+ and serves as the dispatch layer that auto-selects the most performant kernel available: FlashAttention-2, xFormers (memory-efficient attention), or the PyTorch C++ fallback.

Three supported backends:
- **FlashAttention-2** — tiles computation into smaller blocks, uses fast on-chip SRAM; requires fp16/bf16
- **xFormers / Memory-Efficient Attention** — supports fp32 as well as fp16/bf16
- **PyTorch C++ implementation** — default fallback, always available

### Enabling SDPA

**At load time** — explicit via `attn_implementation`:
```python
from transformers import AutoModelForCausalLM

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    device_map="auto",
    attn_implementation="sdpa"
)
```

**Dynamic switching** — after model is already loaded:
```python
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B", device_map="auto")
model.set_attention_implementation("sdpa")   # or "flash_attention_2", "eager"
```

**SDPA context manager** — force a specific kernel for a single block:
```python
import torch
from torch.nn.attention import SDPBackend, sdpa_kernel
from transformers import AutoModelForCausalLM, AutoTokenizer

tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.1-8B")
model = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.1-8B", device_map="auto")

inputs = tokenizer("Hello, my llama is cute", return_tensors="pt").to(model.device)

with sdpa_kernel(SDPBackend.FLASH_ATTENTION):
    outputs = model.generate(**inputs)

print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

### Available Attention Backend Strings

Transformers supports the following `attn_implementation` values:

| Value | Description |
|-------|-------------|
| `"eager"` | PyTorch's native scaled dot product attention (baseline) |
| `"sdpa"` | Auto-selects best available SDPA kernel (FlashAttention-2, xFormers, or C++) |
| `"flash_attention_2"` | FlashAttention-2 tiles; requires fp16/bf16 |
| `"flash_attention_3"` | FlashAttention-3 adds operation overlap; requires Hopper GPUs (SM90+) |
| `"paged"` | Paged attention for long sequences (e.g., vLLM-style) |
| `"paged\|flash_attention_2"` | Paged + FlashAttention-2 combined |
| `"paged\|flash_attention_3"` | Paged + FlashAttention-3 combined |
| `"paged\|sdpa"` | Paged + SDPA combined |
| `"paged\|eager"` | Paged + eager combined |

### Key Constraints

- **`output_attentions=True` is incompatible with SDPA/FlashAttention** — Transformers falls back to the slower eager implementation with a warning
- **FlashAttention-2/3 requires fp16 or bf16** — cast model dtype first; does NOT support fp32
- **SDPA context manager** (`sdpa_kernel`) may raise `RuntimeError: No available kernel. Aborting execution.` if the selected kernel is not compiled for the current PyTorch version — install nightly PyTorch for broader FlashAttention coverage or use a different `SDPBackend`
- **Padding tokens degrade batched FlashAttention-2** — FlashAttention-2 doesn't natively support padding masks; batched generation is slower with padding. Mitigation: pack/pad datasets to avoid padding tokens during training, or use padding-free inference

### Backbone-Specific Attention (Multimodal Models)

Multimodal models can set different attention backends per backbone via a dict:

```python
model = AutoModel.from_pretrained(
    "meta-llama/Llama-3.2-11B-Vision",
    attn_implementation={
        "vision_config": "sdpa",
        "text_config": "flash_attention_2"
    }
)
```

Omitted backbones use the default (SDPA). This is critical for multimodal models where vision and text may have different optimal backends.

### Benchmarks & Performance

FlashAttention-2 provides significant speedup, especially for **long sequences**:
- **Short sequences (<512 tokens):** modest speedup; single forward-pass overhead reduces gain
- **Long sequences (4096+ tokens):** substantial speedup; FlashAttention-2 excels at parallelizing over sequence length
- **Without padding tokens:** maximum speed in batched inference
- **With padding tokens:** slower batched generation due to manual pad/unpad; pack datasets to avoid

Reference: `meta-llama/Llama-7b-hf` and `tiiuae/falcon-7b` benchmarks show FlashAttention-2 speed increasing with batch size and sequence length when padding is absent.

### Custom Attention Functions

Advanced users can register custom attention functions via `AttentionInterface`:

```python
from transformers.integrations.sdpa_attention import sdpa_attention_forward
from transformers.masking_utils import sdpa_mask
from transformers import AttentionInterface, AttentionMaskInterface

# Register custom function
def my_new_sdpa(*args, **kwargs):
    return sdpa_attention_forward(*args, **kwargs)

AttentionInterface.register("my_new_sdpa", my_new_sdpa)
AttentionMaskInterface.register("my_new_sdpa", sdpa_mask)

# Use it
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.2-1B",
    attn_implementation="my_new_sdpa"
)
```

### Key Insights

- SDPA is **enabled by default** for PyTorch >=2.1.1 — you already benefit without setting it explicitly
- Explicit `attn_implementation="sdpa"` guarantees SDPA is used (vs. the model's own default, which could be `"eager"`)
- `model.set_attention_implementation()` allows runtime switching without reloading the model — ideal for A/B testing backends
- The `sdpa_kernel` context manager is the most fine-grained control, enabling per-generation kernel selection
- FlashAttention-2 speedup is most dramatic for long-context inference; for short prompts, the overhead of kernel selection may negate gains
- **Constraint conflict alert:** `output_attentions=True` disables SDPA silently — if you need attention weights AND performance, restructure the pipeline to avoid requesting `output_attentions`

### References
- https://huggingface.co/docs/transformers/main/en/perf_infer_gpu_one (GPU inference optimization — SDPA section)
- https://huggingface.co/docs/transformers/main/en/attention_interface (Attention backends API)
- https://pytorch.org/docs/stable/generated/torch.nn.functional.scaled_dot_product_attention.html
- https://github.com/Dao-AILab/flash-attention
- https://pytorch.org/docs/stable/generated/torch.nn.attention.sdpa_kernel.html

## Entry 87: Transformers Speculative Decoding — Assisted Generation Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-transformers-speculative-decoding-deep-dive` — Complete reference on speculative/assisted decoding in Transformers

### Overview

Speculative decoding (a.k.a. **Assisted Generation**) is an inference-speed technique where a smaller, faster **draft model** generates candidate tokens, and the larger **target model** verifies them in a single forward pass. When the draft is correct (high acceptance rate), the effective speedup can be 2–3× without any quality degradation — the output distribution is mathematically identical to the target model's greedy or sampled distribution.

Transformers implements this natively via `assistant_model` or `prompt_lookup_num_tokens` in `.generate()`.

### How It Works

1. **Draft phase:** Draft model generates K candidate tokens auto-regressively.
2. **Verification phase:** Target model processes all K candidates in a single forward pass, producing logits for each.
3. **Acceptance:** Each candidate is accepted or rejected via a rejection sampling scheme that preserves the exact target distribution.
4. **Fallback:** Rejected positions are re-sampled from the corrected distribution; the draft model is re-synchronised to avoid compounding errors.

The key insight: verification (step 2) costs roughly the same as generating one token, but verifies K tokens at once. K is typically 3–10, leading to 2–3× wall-clock speedup.

### Methods Available in Transformers

| Method | Parameter | Draft Source | Model Required? |
|--------|-----------|-------------|-----------------|
| **Draft model** | `assistant_model` | Separate small model | Yes (e.g., `google/gemma-2-2b-it` for a 27B target) |
| **Prompt lookup** | `prompt_lookup_num_tokens` | N-gram matches from the prompt itself | No — fully self-contained |
| **Early exit** | `assistant_early_exit` | Intermediate layers of the same model | No — uses internal early-exit heads |
| **Static ensemble** | `assistant_ensemble_weight` | Mixture of draft + target logits | Yes — trades exactness for higher acceptance |

### Draft Model Speculative Decoding

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

target = AutoModelForCausalLM.from_pretrained("meta-llama/Llama-3.2-3B")
draft = AutoModelForCausalLM.from_pretrained("google/gemma-2-2b-it")
tokenizer = AutoTokenizer.from_pretrained("meta-llama/Llama-3.2-3B")

inputs = tokenizer("Explain quantum computing", return_tensors="pt")

# Assisted generation — pass draft model
outputs = target.generate(
    **inputs,
    assistant_model=draft,
    max_new_tokens=200,
    temperature=0.7,
    do_sample=True,
)
```

**Best practices:**
- Draft model should be **same family or vocabulary** (or use `assistant_lookbehind`/`target_lookbehind` for different tokenizers)
- Draft should be 2–10× smaller than target — too similar and verification gains are lost; too different and acceptance rate drops
- Works best with **high-acceptance scenarios** (low temperature, deterministic tasks)

### Prompt Lookup Decoding (No Model Required)

Uses the input prompt itself as a candidate pool via n-gram matching — no separate model needed:

```python
outputs = model.generate(
    **inputs,
    prompt_lookup_num_tokens=10,       # generate 10 candidate tokens per round
    max_matching_ngram_size=3,         # look back up to 3 n-grams for matching
    max_new_tokens=200,
)
```

This is ideal when:
- No suitable smaller model is available
- The prompt has repetitive or structured content (code, lists, templates)
- Running on CPU or memory-constrained environments

### Cross-Tokenizer Speculative Decoding

When draft and target use **different tokenizers**, tokens must be aligned across vocabularies. Transformers provides:

- **`assistant_lookbehind`** (int): Re-encodes considering N previous assistant tokens to align correctly
- **`target_lookbehind`** (int): Re-encodes considering N previous target tokens

This enables using any draft model regardless of tokenizer compatibility, at the cost of some re-encoding overhead.

### Static Ensemble Verification

Set `assistant_ensemble_weight` to a float in `(0.0, 1.0)`:

```python
outputs = model.generate(
    **inputs,
    assistant_model=draft,
    assistant_ensemble_weight=0.3,      # w * p_target + (1-w) * q_draft
    do_sample=True,
)
```

The verifier accepts tokens against the **mixture** `w * p_target + (1-w) * q_draft` instead of `p_target` alone. This trades controlled distributional bias for higher acceptance rates. Does NOT work with prompt lookup decoding (requires draft logits).

### Advanced: Dynamic Speculation Lookahead

Transformers auto-adjusts the number of candidate tokens based on recent acceptance rates — `kanon` strategy from [Dynamic Speculation Lookahead](https://huggingface.co/papers/2405.04304). No user config needed; enabled by default with `assistant_model`.

### Key Insights

- Speedup is most dramatic on **batch size 1** (chat/API serving) — batched inference already amortises overhead
- **Lossless guarantee:** The output distribution (greedy or sampled) is mathematically identical to running the target model alone
- Prompt lookup decoding is **free** (no extra model in memory) but has lower acceptance rates than a dedicated draft model
- Static ensemble (`assistant_ensemble_weight`) compromises output quality slightly for higher throughput — only use when latency is the binding constraint
- Cross-tokenizer support (`assistant_lookbehind`/`target_lookbehind`) is relatively new (v4.45+) and adds per-verify re-encoding overhead
- Max speedup is bounded by the ratio of draft-to-target forward pass cost — typical is 2–3× in practice, not 10×

### References
- https://huggingface.co/docs/transformers/en/main_classes/text_generation (GenerationConfig — assisted generation parameters)
- https://huggingface.co/blog/assisted-generation (Joao Gante's original blog post, May 2023)
- https://huggingface.co/papers/2405.04304 (Dynamic Speculation Lookahead)
- https://huggingface.co/docs/transformers/en/llm_tutorial_optimization#speculative-decoding

---

## Entry 80b: Speculative Decoding — 2025/2026 Advances (Deepening)

**Date:** 2026-07-24
**Topic:** `hf-transformers-speculative-decoding-deep-dive` — Modern speculative decoding techniques: Eagle 3, Medusa, Self-Speculative, MTP, Universal Assisted Decoding, and framework comparisons

This entry deepens the original speculative decoding reference (Entry 80) with significant advances from 2025–2026.

### New Methods Now in Transformers (v5.14+)

#### 1. Self-Speculative Decoding (No Draft Model)

Introduced in Transformers v5.14. Uses a model's **intermediate layers** as the draft source — no separate model needed.

```python
outputs = model.generate(
    **inputs,
    assistant_early_exit=True,            # enable self-speculative
    assistant_early_exit_layer=12,        # exit at layer 12 (of 32)
    max_new_tokens=200,
)
```

**How it works:** The forward pass stops at the early-exit layer, generates candidate tokens from its logits, then runs full forward to verify. If the candidates are accepted, the model skips the remaining layers for those positions — saving compute on both the draft and verification phases.

**Best for:** When no suitable small draft model exists, or when GPU memory cannot fit two models. Typical speedup: 1.5–2× (less than dedicated draft, but zero extra VRAM).

#### 2. Universal Assisted Decoding (Cross-Tokenizer)

Eliminates the tokenizer-matching requirement entirely. Works with **any** draft model regardless of vocabulary:

```python
outputs = model.generate(
    **inputs,
    assistant_model=draft_model,          # any tokenizer
    max_new_tokens=200,
)
```

The algorithm re-encodes candidate tokens from the draft's vocabulary into the target's vocabulary each verification round. The `assistant_lookbehind` and `target_lookbehind` parameters control the re-encoding context window (default: 0). This makes speculative decoding practical with heterogeneous model families.

#### 3. Static Ensemble Verification

Relaxes the strict acceptance criterion for higher throughput:

```python
outputs = model.generate(
    **inputs,
    assistant_model=draft,
    assistant_ensemble_weight=0.2,        # 0.0 = exact, 1.0 = full draft
)
```

At weight 0.2, the verifier accepts against `w * p_target + (1-w) * q_draft`. This trades *exact* output distribution for a 10–30% acceptance rate boost. Recommended starting value: 0.2. Paper: [arxiv.org/abs/2604.07622](https://arxiv.org/abs/2604.07622).

### Third-Generation Draft Architectures

#### 4. Eagle 3 (2025)

Eagle 3 is the current state-of-the-art speculative decoding framework. Unlike classic draft models that are independent LMs, Eagle 3 **conditions the draft on the target model's hidden states**:

- **Feature-level drafting:** Takes the target model's last-layer hidden state as input to a lightweight transformer (2–4 layers) that predicts future tokens
- **No fine-tuning required:** The draft head is trained on a small dataset of target model generations (50K–100K samples)
- **Multi-token prediction:** Predicts 3–5 tokens in a single pass using a parallel head structure
- **Speedup:** 3.5–4.5× on Llama 3.1-70B, 2.5–3.5× on smaller models
- **VRAM overhead:** ~2 GB for the draft head (vs. 7+ GB for a full draft model)

**Architecture comparison:**

| Aspect | Classic Draft | Eagle 3 | Medusa |
|--------|--------------|---------|--------|
| Draft input | Token embeddings | Target hidden states | Token embeddings |
| Draft params | 1–7B | 100M–500M | 50M–200M |
| Training data | Full pretraining | 50K gen samples | 50K gen samples |
| Speedup | 2–3× | 3.5–4.5× | 2.3–3× |
| VRAM overhead | High | Low | Very low |
| Requires FT | Yes (full) | No (adapter) | No (heads only) |

#### 5. Medusa (2024–2025)

Medusa adds **multiple lightweight prediction heads** on top of the target model's final layer:

- **Parallel heads:** Typically 5 heads, each predicting the token at offset k+1, k+2, ..., k+5
- **Tree attention:** All head predictions are verified in a single tree-structured forward pass
- **Training:** Only the heads are trained (LoRA), ~50K samples, ~1 hour on 1 GPU
- **Speedup:** 2.3–3× on Llama/CodeLlama models
- **vLLM integration:** Native support via `--speculative-model-type "medusa"`

Transformers does **not** have native Medusa support (use vLLM or custom implementation).

#### 6. Multi-Token Prediction (MTP) — DeepSeek-Style

MTP is a **training-time** technique (DeepSeek V3/R1) where the model is trained to predict N future tokens simultaneously via lightweight MTP heads. During inference:

- The MTP heads act as a built-in draft mechanism
- Target model verifies the draft in a single pass
- The `MtpCache` class in Transformers tracks per-depth token offsets

**Key distinction:** Unlike Medusa/Eagle (post-training adapters), MTP requires training from scratch or continued pretraining. DeepSeek V3 uses `mtp_num_hidden_layers: 1` (single MTP head predicting 1 future token).

```python
# MTP-aware generation (for MTP-trained models like DeepSeek V3)
outputs = model.generate(
    **inputs,
    use_mtp=True,                         # enable MTP draft mode
    mtp_num_tokens=1,                     # tokens to draft per step
)
```

### Framework Comparison

| Capability | Transformers | vLLM | TGI |
|------------|-------------|------|-----|
| Draft model | ✅ `assistant_model` | ✅ `--speculative-model` | ✅ `--draft-model` |
| Prompt lookup | ✅ `prompt_lookup_num_tokens` | ✅ `--num-speculative-tokens` | ❌ |
| Self-speculative | ✅ `assistant_early_exit` | ❌ | ❌ |
| Universal decode | ✅ (v5.14+) | ❌ | ❌ |
| Medusa | ❌ | ✅ `--spec-model medusa` | ❌ |
| Eagle | ❌ | ❌ | ❌ (custom) |
| MLPSpeculator | ❌ | ✅ `--spec-model mlp-speculator` | ❌ |
| N-gram | ❌ | ✅ `--spec-model ngram` | ❌ |
| Top-k rejection | ✅ (auto) | ✅ configurable | ❌ |
| Dynamic lookahead | ✅ (auto) | ❌ | ❌ |
| Streaming | ✅ | ✅ | ✅ |
| Batch spec decode | ❌ | ✅ | ❌ |

### Acceptance Rate Optimization

The **acceptance rate** (fraction of draft tokens accepted) is the primary lever for speedup. Key factors:

| Factor | Low Acceptance | High Acceptance |
|--------|---------------|-----------------|
| Temperature | High (0.8–1.5) | Low (0.0–0.3) |
| Task | Creative writing | Code generation, math |
| Draft quality | Small / untrained | Same-family / trained |
| Sequence length | Short (<100) | Long (>500) |
| Batch size | Large (>8) | 1 (latency-bound) |

**Rule of thumb:** Target ≥60% acceptance for meaningful speedup. Below 40%, the verification overhead outweighs the savings.

### vLLM Speculative Decoding API (Production)

vLLM provides the most mature production-grade speculative decoding:

```bash
# Start vLLM with Eagle-style speculator
vllm serve meta-llama/Llama-3.1-70B \
    --speculative-model "ibm-research/Eagle2-Llama-3.1-8B" \
    --speculative-draft-tensor-parallel-size 1 \
    --num-speculative-tokens 5 \
    --speculative-model-enforce-eager \
    --use-v2-block-manager

# Start with n-gram spec decode (no extra model)
vllm serve meta-llama/Llama-3.1-8B \
    --speculative-model "[ngram]" \
    --num-speculative-tokens 5 \
    --ngram-prompt-lookup-max 4
```

**vLLM unique features:**
- `--spec-decoding-acceptance-method` (rejection_sampling / typical_acceptance)
- Top-k acceptance sampling for quality/speed tradeoff
- Pluggable speculator workers for custom architectures
- Batch speculative decoding (unique to vLLM — verify multiple sequences at once)

### When to Use Each Method

| Use Case | Recommended Method | Speedup |
|----------|-------------------|---------|
| Chat serving (1 user) | Eagle 3 or dedicated draft | 3–4× |
| Code completion | Prompt lookup (code is repetitive) | 2–3× |
| CPU / Edge | Self-speculative (no VRAM overhead) | 1.5× |
| Batch serving | Draft model (batch-friendly) | 1.5–2× |
| Max quality required | Draft model with rejection sampling | 2–3× |
| Max throughput | Universal decode + ensemble weight | 2.5–4× |
| Fast iteration (no training) | Prompt lookup or self-speculative | 1.5–2× |

### Key Takeaways

1. **Self-Speculative** (Transformers v5.14+) is the zero-VRAM option — identical output, 1.5–2× speedup, no extra model
2. **Eagle 3** is the throughput king: 3.5–4.5× but needs a trained draft head (~2 GB VRAM)
3. **Universal Assisted Decoding** eliminates the tokenizer barrier — pair any draft with any target
4. **Static ensemble** trades exactness for speed — use ≤0.2 weight for minimal drift with 10–30% acceptance lift
5. **vLLM** leads for production serving with batch speculative decode and pluggable speculators
6. **MTP** only works with models trained for it (DeepSeek V3/R1 family) — not retrofittable

### New References (Post-2024)

- https://arxiv.org/abs/2405.04304 (Dynamic Speculation Lookahead)
- https://arxiv.org/abs/2604.07622 (Static Ensemble Verification)
- https://github.com/SafeAILab/EAGLE (Eagle 3 — hidden-state draft heads)
- https://arxiv.org/abs/2402.19199 (Medusa: Multiple prediction heads)
- https://arxiv.org/abs/2405.14837 (Self-Speculative Decoding via Early Exit)
- https://huggingface.co/docs/transformers/en/assisted_decoding (Transformers assisted decoding page)
- https://docs.vllm.ai/en/latest/features/spec_decode.html (vLLM speculative decoding)
- https://arxiv.org/abs/2404.07340 (DeepSeek V2 MTP precursor)
- https://arxiv.org/abs/2302.01318 (Blockwise Parallel Decoding / Lookahead)

---

## Entry 81: Diffusers Video Generation Pipelines — CogVideoX Deep Dive
**Date:** 2026-07-23
**Topic:** `hf-diffusers-video-generation-pipeline` — Text-to-video and image-to-video pipelines in Diffusers (CogVideoX)

### Overview

Diffusers ships several video generation pipelines. The flagship is **CogVideoX** (THUDM), available as:
- `CogVideoXPipeline` — text-to-video (T2V)
- `CogVideoXImageToVideoPipeline` — image-to-video (I2V), accepts an initial image as conditioning

Both inherit from `DiffusionPipeline` and follow the same architecture: T5 text encoder → 3D transformer (spatio-temporal attention) → AutoencoderKL CogVideoX VAE → DDIM/DPM scheduler.

### Key Pipeline Components

| Component | Type | Notes |
|-----------|------|-------|
| `tokenizer` | `T5Tokenizer` | Encodes text prompt |
| `text_encoder` | `T5EncoderModel` | Generates text embeddings |
| `vae` | `AutoencoderKLCogVideoX` | Encodes/decodes video latents |
| `transformer` | `CogVideoXTransformer3DModel` | Core denoising with 3D attention |
| `scheduler` | `CogVideoXDDIMScheduler` or `CogVideoXDPMScheduler` | DDIM for speed, DPM for quality |

### Usage — Text-to-Video

```python
import torch
from diffusers import CogVideoXPipeline
from diffusers.utils import export_to_video

pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-5b", torch_dtype=torch.bfloat16
)
pipe.to("cuda")
pipe.enable_model_cpu_offload()

video = pipe(
    prompt="A detailed wooden toy ship gliding over a plush blue carpet",
    guidance_scale=6,
    num_inference_steps=50,
).frames[0]
export_to_video(video, "output.mp4", fps=8)
```

### Usage — Image-to-Video

I2V checkpoints accept an initial image as conditioning. The height must be 758px, width varies 768–1360 (both divisible by 16). Works best with 81–161 frames at 16 fps.

### Resolution and Frame Guidelines

| Variant | Optimal Resolution | Frame Count | FPS |
|---------|-------------------|-------------|-----|
| T2V (text-to-video) | 1360×768 | 81–161 | 16 |
| I2V (image-to-video) | Width 768–1360, Height 758 | 81–161 | 16 |

### LoRA Support

CogVideoX supports LoRAs via `load_lora_weights()` and `set_adapters()`:

```python
pipe.load_lora_weights("finetrainers/CogVideoX-1.5-crush-smol-v0", adapter_name="crush-lora")
pipe.set_adapters("crush-lora", adapter_weight=0.9)
```

### Memory-Saving Techniques

| Method | VRAM Usage (enabled) | VRAM Usage (disabled) | Notes |
|--------|---------------------|----------------------|-------|
| `enable_model_cpu_offload` | 19 GB | 33 GB | Best balance |
| `enable_sequential_cpu_offload` | < 4 GB | ~33 GB | Very slow |
| `enable_tiling` (+ model offload) | 11 GB | — | Reduces VAE peak memory |
| `enable_slicing` | Reduces VAE peak | — | Complements tiling |

### Quantization (torchao)

CogVideoX supports torchao Int8 weight-only quantization via `PipelineQuantizationConfig`:

```python
from diffusers.quantizers import PipelineQuantizationConfig
from torchao.quantization import Int8WeightOnlyConfig
from diffusers import TorchAoConfig

quant_config = PipelineQuantizationConfig(
    quant_mapping={"transformer": TorchAoConfig(Int8WeightOnlyConfig())}
)
pipe = CogVideoXPipeline.from_pretrained(
    "THUDM/CogVideoX-5b", transformer=transformer,
    quantization_config=quant_config, torch_dtype=torch.bfloat16
)
```

### Available Checkpoints on HF Hub

- `THUDM/CogVideoX-5b` — 5B parameter T2V model
- `THUDM/CogVideoX-2b` — 2B parameter T2V (lighter)
- `THUDM/CogVideoX1.5-5b` — Improved 1.5 version
- `THUDM/CogVideoX1.5-5b-I2V` — Image-to-video variant
- Community finetunes: `finetrainers/CogVideoX-1.5-crush-smol-v0` (LoRA), etc.

### Key Insights

- **export_to_video()** utility handles MP4 encoding from frame tensors; accepts `fps=` parameter
- The `__call__` params mirror standard Diffusers: `prompt`, `negative_prompt`, `height`, `width`, `num_frames`, `num_inference_steps`, `guidance_scale` (default 6), `use_dynamic_cfg`, `generator`, `latents`
- `use_dynamic_cfg=True` enables dynamic classifier-free guidance (adjusts guidance scale per timestep)
- Group offloading (`apply_group_offloading`) can further reduce memory by offloading model groups rather than full layers
- CogVideoX tends to produce best results with **1360×768** and **50 steps** — lower resolutions lose detail, higher may exceed 5B model capacity
- The VAE uses `AutoencoderKLCogVideoX` which supports tiling for high-resolution video generation (enabled via `enable_vae_tiling()`)

### References
- https://huggingface.co/docs/diffusers/main/en/api/pipelines/cogvideox
- https://huggingface.co/THUDM/CogVideoX-5b
- https://huggingface.co/docs/diffusers/main/en/api/pipelines/overview#video

---

## Entry 82: Spaces Secrets & Environment Variables Management
**Date:** 2026-07-23
**Topic:** `hf-spaces-secrets-management` — Complete reference on managing secrets, variables, and environment configuration in Hugging Face Spaces

### Overview

HF Spaces supports two types of environment configuration: **Variables** (non-sensitive, public) and **Secrets** (sensitive, private). Both are managed through the Space Settings page on the HF Hub. The distinction is crucial for security and shareability.

### Variables vs Secrets

| Feature | Variables | Secrets |
|---------|-----------|---------|
| Visibility | Publicly accessible and viewable | Private; value hidden once set |
| Share on duplicate | ✅ Auto-included in duplicated Spaces | ❌ NOT included in duplicates |
| Use case | Config values, non-sensitive settings | API keys, tokens, credentials |
| Access method | Environment variable at runtime | Environment variable at runtime |

### Setting Up Secrets & Variables

1. Go to your Space repository on HF Hub
2. Click **Settings** (the gear icon)
3. In the "Repository Secrets" section, add:
   - **Variable**: name + value (visible to everyone)
   - **Secret**: name + value (masked after save)

### Access by Space SDK

**Gradio Spaces** — Both secrets and variables are available as environment variables:
```python
import os
api_key = os.environ.get("MY_API_KEY")  # Secret
mode = os.environ.get("MODE")           # Variable
```

**Docker Spaces** — Two-level access:
- **Build-time**: Variables are passed as `build-arg`s when building the Docker image
  ```dockerfile
  ARG MY_VAR
  RUN echo "Building with $MY_VAR"
  ```
- **Secrets at build-time**: Mounted at `/run/secrets/SECRET_NAME`:
  ```
  RUN curl -H "Authorization: Bearer $(cat /run/secrets/SECRET_EXAMPLE)" https://api.example.com
  ```
- **Runtime**: Both secrets and variables accessible as standard env vars (same as Gradio):
  ```python
  import os
  os.environ.get("SECRET_EXAMPLE")  # Secret at runtime
  ```

**Static Spaces** — Both are available client-side via JavaScript:
```javascript
const variables = window.huggingface.variables;
// Access: variables.MY_VAR or variables.MY_SECRET
```

### Built-in Environment Variables

HF Spaces automatically injects these environment variables:

| Variable | Description |
|----------|-------------|
| `HF_TOKEN` | HF access token (for interacting with gated repos) |
| `SPACE_ID` | Full Space repo ID (e.g. `user/space-name`) |
| `SPACE_TITLE` | Display title of the Space |
| `SPACE_HOST` | Hostname of the Space |
| `SPACE_REPO_NAME` | Repo name part of the Space ID |
| `SPACE_AUTHOR_NAME` | Author/owner of the Space |

### Best Practices

1. **Never hard-code secrets** in app code, README, or config files pushed to the repo
2. **Use Environment Variables** via Settings page — they're encrypted at rest
3. **Rotate secrets** periodically by deleting and re-adding them
4. **Use `os.environ.get()` with defaults** to fail gracefully: `os.environ.get("HF_TOKEN", "")`
5. **For multi-secret apps**, consider grouping with a naming convention: `DB_HOST`, `DB_PORT`, `DB_PASSWORD`
6. **Never log secrets** — sanitize output before debugging
7. **Docker Secrets** (`/run/secrets/`) are only available during `docker build`, not at runtime for build-time-only commands like `curl`

### Limitations

- Secrets cannot be read back from the UI once saved (you can only replace or delete them)
- No API-based secrets management yet (must use the web UI or git-based approaches)
- Private repo preloading does NOT work with secrets at build time
- Variables are public on duplicate — don't put anything sensitive in variables

### Key Insights

- The Variables vs Secrets distinction is a **privacy boundary on duplication** — secrets don't leak when users duplicate your Space
- Docker Secrets at build time use a special filesystem path (`/run/secrets/`) rather than env vars, which is unique to Docker Spaces
- The `HF_TOKEN` built-in env var is automatically set to the repo owner's token — useful for Spaces that need to download gated models
- Secrets UI field is one-way: once you save, you can only overwrite, never retrieve. Keep a local copy of your secrets

### References
- https://huggingface.co/docs/hub/en/spaces-overview (see "Managing secrets and environment variables" section)
- https://huggingface.co/docs/hub/en/spaces-sdks-docker (see "Secrets and Variables Management")
- https://huggingface.co/docs/hub/en/spaces-config-reference
- https://huggingface.co/docs/hub/en/security-secrets

---

## Entry 4: Gradio 5.x — Complete Migration & Feature Reference
**Date:** 2026-07-23
**Topic:** `hf-gradio-5-api-reference` — Comprehensive reference on the Gradio 4→5 migration and all new features in the 5.x series up to 6.20

### Overview

Gradio 5.0 (released in beta from PR #8797 onwards) was a **ground-up rewrite** with a modernised UI, SSR support, i18n, streaming inputs, new security model, and many breaking changes. As of July 2026, Gradio is at **6.20.0**, with 6.x adding Workflows, Navbar, and further refinements.

### Breaking Changes (4.x → 5.x)

| Change | Old (4.x) | New (5.x) | Impact |
|--------|-----------|-----------|--------|
| Python version | 3.8+ | **3.10+** | Drop py3.8/3.9 support |
| Chatbot `type` | `'tuples'` (default) | **`'messages'`** (default, `'tuples'` deprecated) | All new code should use `type='messages'` |
| `theme`, `css`, `js`, `head` | `gr.Blocks(theme=..., css=...)` | **`demo.launch(theme=..., css=...)`** | Moved from constructor to `launch()` |
| Token in `gr.load()` | Auto-passed by default | **No token by default** | Must pass `token=` explicitly for private repos |
| Image preprocessing | Implicit format handling | Explicit `format=None` default | Set `format` in `gr.Audio`/`gr.Image` to avoid re-encoding |
| `gr.make_waveform()` | Available | **Removed** | Use a third-party tool |
| `matplotlib` | Dependency | **Removed** as core dependency | Install separately if using native plots |
| Checkbox defaults | Various | "select all" checkbox for boolean Dataframe columns | Verify existing Dataframe UIs |
| File security | Basic path checks | **Strict `_safe_join`** (no path traversal) | `FileExplorer` selections are validated against `root_dir` |

### New Components & Features (5.x series)

| Feature | Version | Description |
|---------|---------|-------------|
| **SSR (Server-Side Rendering)** | 5.0-b | All components are SSR-compatible. `launch(ssr=True)` enables it. Frontend assets shipped with the library — works **offline** |
| **Redesigned UI** | 5.0-b | Tabs, Buttons, Sliders, CheckboxGroup, ColorPicker, DataFrames, Audio, Chatbot all got redesigns. Default theme changed from gray to **zinc**. Component radii decreased |
| **i18n** | 5.0-b | Runtime language switching. Components re-translate labels/values when language changes |
| **Streaming inputs** | 5.0-b | `fn` can receive streaming data from Audio, Image, Video input components via WebSocket |
| **MCP Server** | 5.46+ | Gradio apps can act as MCP (Model Context Protocol) servers. Use `launch(mcp=True)` |
| **`gr.Workflow` + `gr.WorkflowCanvas`** | **6.17** | Visual AI pipeline builder — drag-and-drop canvas for wiring Python functions into graphs |
| **`gr.Navbar`** | 5.45 | Multipage app navigation bar |
| **`gr.Walkthrough` + `gr.Step`** | 5.45 | Guided walkthrough/multi-step workflow components |
| **`gr.Toast`** | 5.x | Configurable notifications (`expanded: True` by default from 6.0-dev) |
| **Dark mode** | 5.x | Full dark mode support for docs and components. Default dark theme is zinc |
| **Chatbot examples** | 5.0-b | `examples=` parameter in `gr.ChatInterface` |
| **Native plots** | 5.x | `gr.LinePlot`, `gr.ScatterPlot`, `gr.BarPlot` with x-limit control, export button, long legend support |
| **`css_paths`/`head_paths`** | 5.0-b8 | Path-based CSS/head injection |
| **Max length for Textbox** | 5.0-b0 | `max_length` parameter |
| **Object detection from webcam** | 5.0-b2 | Streaming guides |
| **Video gallery** | 5.0-b0 | Video gallery display |
| **`gradio openaichat`** | 5.48 | CLI command to launch a default ChatInterface with --share |
| **`allow_tags=True` default** | **6.0-dev** | Chatbot tags enabled by default |

### Component Parameter Changes (5.x)

**`gr.ChatInterface` changes:**
- `submit_btn` / `stop_btn` props added to Textbox
- Built-in submit/stop buttons (no longer requires custom buttons)
- `examples=` for quick-start example prompts
- `multimodal=True/False` — multimodal textbox variant
- Retry/undo for bot messages (configurable via `likeable`)

**`gr.Chatbot` changes:**
- `type='messages'` is now the default (deprecates `'tuples'`)
- `allow_tags=True` by default in 6.x
- Panels layout for code/media
- Thoughts (`reasoning_tags`) can be collapsed automatically
- `like_user_message=False` by default (configurable)

**`gr.Dataframe` changes:**
- Action popover UI (icons moved into popover)
- "Select all" checkbox for boolean columns
- `header` change triggers `change` event
- `datatype="auto"` for 1D and empty values

**`gr.Image` changes:**
- `source` parameter with `None` option to disable image mirroring
- SPA mode (Svelte 5 migration in progress across 5.x/6.x)
- `format=None` default avoids unnecessary preprocessing

**`gr.Textbox` changes:**
- `max_length` parameter added
- `submit_btn` / `stop_btn` props
- Disabled state shows gray placeholder

**`gr.Slider` changes:** Redesigned UI.

**`gr.Tabs` changes:** Redesigned UI, `render_children` parameter for performance.

**`gr.Button` changes:** Redesigned UI, huggingface variant for `gr.LoginButton` / `gr.DuplicateButton`.

### Security Hardening (Notable CVEs Fixed)

| CVE/Issue | Fixed In | Description |
|-----------|----------|-------------|
| SSRF via Image/Gallery SVG + Audio streaming | v6.15 | User-influenced URL fetches routed through `safehttpx` |
| Path traversal in FileExplorer | v6.16 | `_safe_join` validates selected paths |
| Open redirect bypass (CVE-2026-28415) | v6.16 | 4+ leading slashes in `_target_url` no longer produce scheme-relative redirects |
| XSS via `<script>` in `gr.HTML` | v6.18 | Warning when script tag included in content |
| SSRF via `Blocks.from_config()` proxy_url | v6.15 | GHSA-jmh7-g254-2cq9 regression coverage |
| File size enforcement | v6.20 | `max_file_size` enforced for multipart uploads to `/component_server` |
| Content-disposition security | v5.0-b2 | `attachment` header only for files not explicitly allowed by developer |
| IP address hashing | v5.0-b0 | Machine-specific hashes replace IP addresses in analytics |
| Strict CORS | v5.0-b0 | `strict_cors` parameter in `launch()` |
| DNS resolver on IP check | v5.0-b0 | DNS resolution for IP validation |

### Queue & Performance Improvements

- **Queue performance**: Major optimisations in 5.x for request throughput (especially MCP use cases)
- **Heartbeat interval**: Configurable via `GRADIO_HEARTBEAT_INTERVAL` env var (v6.16)
- **Caching**: Refactored to lazy caching — examples cache only when Blocks is launched, not at creation time
- **File caching**: Files moved to cache only when they have a meta key
- **WebSocket streaming**: Data sent over WebSocket when possible, with `base64` output format support (v5.0-b8)
- **Reduced files in build**: Smaller npm package

### ZeroGPU Support

- `GRADIO_ZERO_GPU_IP_TOKEN` env var for ZeroGPU Spaces
- ZeroGPU headers forwarding fixed in gradio_client (v6.0-dev.2)
- Best practices guide updated for manually passing an IP token
- ZeroGPU select events no longer cause errors (v5.46)

### OAuth & Authentication

- `hf_oauth` scopes: login, profile, repos, inference_api, openid
- Expired OAuth sessions treated as logged out (v6.18)
- `gr.LoginButton` with `variant="huggingface"` (default in 5.0)
- Async auth functions now supported (`#9244` fix, v5.47)
- Token forwarding in Workflow nodes (v6.18)

### Code Examples

**SSR mode:**
```python
import gradio as gr

with gr.Blocks() as demo:
    gr.Markdown("# SSR demo")

demo.launch(ssr=True)  # Server-side rendering
```

**ChatInterface with examples:**
```python
import gradio as gr

def echo(message, history):
    return f"You said: {message}"

gr.ChatInterface(
    echo,
    examples=["Hello!", "What's new?", "Tell me a joke"],
    type="messages"
).launch()
```

**MCP server mode (5.46+):**
```python
import gradio as gr

def greet(name, intensity):
    return "Hello, " + name + "!" * intensity

with gr.Blocks() as demo:
    gr.Markdown("# MCP Demo")
    name = gr.Textbox(label="Name")
    intensity = gr.Slider(1, 5, value=1, step=1)
    output = gr.Textbox(label="Greeting")
    greet_btn = gr.Button("Greet")
    greet_btn.click(fn=greet, inputs=[name, intensity], outputs=output)

demo.launch(mcp=True)  # Exposes as MCP server
```

**Workflow (6.17+):**
```python
import gradio as gr

def summarize(text: str) -> str:
    return text[:100] + "..."

def classify(text: str) -> str:
    return "positive" if "good" in text.lower() else "negative"

with gr.Blocks() as demo:
    gr.Markdown("# AI Workflow Demo")
    input_text = gr.Textbox(label="Input")
    summary = gr.Textbox(label="Summary")
    label = gr.Textbox(label="Classification")
    btn = gr.Button("Run")
    btn.click(summarize, input_text, summary).then(classify, input_text, label)

demo.launch()
```

### Key Insights

- **Gradio 5 is a complete visual overhaul** — all components were redesigned. If your Space looks like Gradio 4, it will look noticeably different on 5.x
- **SSR breaks some custom JS patterns** — if you use `js=` in event handlers for DOM manipulation, test with `ssr=True` first
- **MCP mode is automatic** — any Gradio app can become an MCP server with `mcp=True`
- **The `theme=` / `css=` / `js=` move to `launch()`** is the most likely migration stumbling block — old code that sets them in `gr.Blocks()` will raise an error
- **Chatbot `type='messages'` is the future** — the old `'tuples'` format will be removed in Gradio 6
- **Security posture is much stronger** — path traversal, SSRF, and open redirect vulnerabilities have been systematically closed
- **Workflow (6.17+) is a new paradigm** — visual pipeline building moves Gradio beyond simple demos into full workflow orchestration

### References
- https://github.com/gradio-app/gradio/blob/main/CHANGELOG.md
- https://www.gradio.app/docs/gradio/changelog
- https://www.gradio.app/docs/guides/version-5 (migration guide)
- https://huggingface.co/docs/hub/en/spaces-gradio

---

## Entry 6: HfFileSystem — fsspec Integration for the Hub
**Date:** 2026-07-24
**Topic:** `hf-hub-fsspec` — Deep dive on the `HfFileSystem` fsspec implementation for treating HF Hub repos and buckets as a local filesystem

### Overview

`HfFileSystem` (in `huggingface_hub`) implements the [fsspec](https://filesystem-spec.readthedocs.io/) protocol so you can read, write, list, and manage files on the Hugging Face Hub as if they were local files. It supports models, datasets, Spaces repos, **and** HF Storage Buckets — all through the same `hf://` URI scheme.

**Performance note:** `HfFileSystem` adds overhead from the fsspec compatibility layer. For direct programmatic access, `HfApi.list_repo_tree()`, `HfApi.hf_hub_download()`, `HfApi.upload_folder()` are generally faster and more reliable. Use `HfFileSystem` when:
- You need to work with a library that speaks fsspec (pandas, dask, zarr, etc.)
- You want interactive/exploratory file inspection without committing to a full download
- You're writing generic filesystem-agnostic code

### Path Format

```python
# Models (default repo_type)
hf://<namespace>/<name>[@<revision>]/<path>
hf://<namespace>/<name>/path/to/file.json

# Datasets
hf://datasets/<namespace>/<name>[@<revision>]/<path>

# Spaces
hf://spaces/<namespace>/<name>[@<revision>]/<path>

# Buckets (Storage Buckets — S3-compatible)
hf://buckets/<bucket-id>/<path>
```

Using `HfFileSystem` directly, the `hf://` prefix is optional:
```python
from huggingface_hub import HfFileSystem
fs = HfFileSystem()
fs.ls("google-bert/bert-base-uncased")
# same as
fs.ls("hf://google-bert/bert-base-uncased")
```

### Module-Level Singleton

```python
from huggingface_hub import hffs
# hffs is a pre-configured HfFileSystem instance
```

### Constructor

```python
from huggingface_hub import HfFileSystem

fs = HfFileSystem(
    token="hf_...",           # Auth. Defaults to saved token. Pass False to disable.
    endpoint=None,             # Custom Hub endpoint (default: https://huggingface.co)
    block_size=None,           # Block size for read/write buffering
    expand_info=None,          # Whether to expand file info in results
)
```

### Read Operations

| Method | Description | Example |
|--------|-------------|---------|
| `ls(path, detail=True)` | List directory contents | `fs.ls("user/repo", detail=False)` |
| `info(path)` | Get metadata (type, size, commit) | `fs.info("user/repo/config.json")` |
| `exists(path)` | Check path exists | `fs.exists("user/repo/config.json")` |
| `glob(pattern)` | Pattern match in repo root | `fs.glob("user/repo/*.json")` |
| `find(path, glob="*.py")` | Recursive search | `fs.find("user/repo", glob="*.json")` |
| `walk(path)` | Recursive directory tree | `next(fs.walk("user/repo"))` → `(root, dirs, files)` |
| `tree(path)` | Recursive flat listing | `fs.tree("user/repo", detail=False)` |
| `cat(path)` | Read file as bytes | `data = fs.cat("user/repo/config.json")` |
| `cat_file(path)` | Stream file contents | `data = fs.cat_file("user/repo/model.bin", start=0, end=1024)` |
| `read_text(path)` | Read file as string | `text = fs.read_text("user/repo/config.json")` |
| `open(path, "rb")` | Return file-like object | `with fs.open("user/repo/file.bin", "rb") as f: data = f.read()` |
| `head(path, size=1024)` | Read first N bytes | `fs.head("user/repo/model.bin", size=512)` |
| `tail(path, size=1024)` | Read last N bytes | `fs.tail("user/repo/model.bin", size=512)` |
| `read_block(path, offset, size)` | Read byte range | `fs.read_block("user/repo/file.bin", 4096, 1024)` |
| `du(path)` | Disk usage (total size) | `fs.du("user/repo")` |
| `sign(path)` | Generate signed (temporary) URL | `signed_url = fs.sign("user/repo/model.safetensors")` |
| `url(path)` | Get direct URL to file | `fs.url("user/repo/config.json")` |

### Write Operations

| Method | Description | Example |
|--------|-------------|---------|
| `open(path, "wb")` | Write file via file-like object | `with fs.open("user/repo/new.txt", "wb") as f: f.write(b"hello")` |
| `pipe_file(path, value)` | Write bytes atomically | `fs.pipe_file("user/repo/new.txt", b"hello world")` |
| `write_text(path, text)` | Write string | `fs.write_text("user/repo/new.txt", "hello world")` |
| `put(lpath, rpath)` | Upload local file/dir | `fs.put("local.txt", "user/repo/remote.txt")` |
| `put_file(lpath, rpath)` | Upload single file | `fs.put_file("local.py", "user/repo/script.py")` |
| `touch(path)` | Create empty file | `fs.touch("user/repo/.keep")` |
| `copy(path1, path2)` | Copy within filesystem | `fs.copy("user/repo/a.txt", "user/repo/b.txt")` |
| `mv(path1, path2)` | Move/rename | `fs.mv("user/repo/old.txt", "user/repo/new.txt")` |
| `rm(path)` | Delete file(s) | `fs.rm("user/repo/file.txt")` |
| `rmdir(path)` | Remove directory | `fs.rmdir("user/repo/subdir")` |
| `makedirs(path)` | Create directories | `fs.makedirs("user/repo/subdir/nested")` |
| `delete(path)` | Alias for rm | `fs.delete("user/repo/file.txt")` |

### Key Implementation Details

**File mode `"rb"` / `"wb"` only.** The `open()` method wraps `HfFileSystemFile` (block-based) or `HfFileSystemStreamFile` (zero-block streaming). Append mode (`"a"`) is **not supported** — raises `NotImplementedError`.

**Block size behavior:**
- `block_size=None` (default): Each read/write fetches the entire file at once via `requests`.
- `block_size=0`: Uses `HfFileSystemStreamFile` — streams data in chunks without buffering the whole file.
- `block_size>0`: Uses `HfFileSystemFile` — fetches fixed-size blocks with local caching via a `BlockCache`.

**Write commits:** When writing via `open(..., "wb")`, data is buffered in memory and committed to the Hub as a single atomic commit when `close()` is called (or on context manager exit). This means the file only appears on the Hub after the file object is fully closed — partial writes are not visible.

**Revision support:** Every read method accepts a `revision` parameter (branch name, tag, or commit hash). When omitted, defaults to `"main"`. Write operations always write to the default branch (typically `"main"`).

**Expanded info:** By default, `info()` returns basic metadata (type, size, name). Set `expand_info=True` in the constructor or pass it per-call to get commit history, security status, and LFS details.

### Caching

`HfFileSystem` caches:
- **Repo existence** (in `_repo_and_revision_exists_cache`): Avoids repeated checks for the same repo+revision pair.
- **Directory listings** (in `dircache`): Caches `ls()` calls. Pass `refresh=True` to bypass.

The dircache uses the resolved path (repo_type + repo_id + revision) as the key. Cache invalidation happens implicitly when a write operation modifies the repo, but for read-heavy workloads you may need to call `fs.invalidate_cache()` or `fs.invalidate_cache(path)` explicitly.

### Bucket Support

Storage Buckets (HF's S3-compatible object storage) are accessible via `hf://buckets/<bucket-id>/<path>`:

```python
# List bucket contents
fs.ls("hf://buckets/my-bucket/training-data/")

# Read from bucket
fs.cat("hf://buckets/my-bucket/checkpoints/model-001.pt")

# Upload to bucket
fs.put_file("/local/checkpoint.pt", "hf://buckets/my-bucket/checkpoints/")
```

Note: `sign()` generates temporary signed URLs for bucket files, enabling time-limited direct downloads.

### Pandas / DataFrame Integration

This is one of the most powerful use cases — fsspec allows pandas to read Hub files directly:

```python
import pandas as pd

# Read a CSV directly from a dataset repo
df = pd.read_csv("hf://datasets/user/dataset/data.csv")

# Read Parquet files
df = pd.read_parquet("hf://datasets/user/dataset/train.parquet")

# Read JSON
df = pd.read_json("hf://datasets/user/dataset/data.json")
```

No local download needed — data streams directly from the Hub.

### Shell/Python Integration with `hf` CLI

The `hf` CLI also provides filesystem-level operations:

```bash
# List contents
hf ls <repo-id>

# Copy files between local/repos/buckets
hf cp local/file.txt <repo-id>/path/in/repo
hf cp <repo-id>/config.json ./config.json
hf cp <repo-id>/file.txt buckets/my-bucket/
```

### Practical Examples

**1. Explore a model repo without downloading:**
```python
from huggingface_hub import hffs

files = hffs.glob("google-bert/bert-base-uncased/*.json")
for f in files:
    size = hffs.info(f)["size"]
    print(f"{f}: {size} bytes")
```

**2. Read a specific file from a dataset:**
```python
import json
from huggingface_hub import hffs

content = hffs.read_text("datasets/cornell-movie-review-data/rotten_tomatoes/README.md")
print(content[:500])
```

**3. Stream a large model file partially:**
```python
from huggingface_hub import hffs

# Read only the first 1KB of a model file
header = hffs.head("google-bert/bert-base-uncased/model.safetensors", size=1024)
```

**4. Write a file to your own repo:**
```python
from huggingface_hub import hffs

hffs.write_text("my-org/my-repo/data/results.json", '{"accuracy": 0.95}')
# File is now committed to the Hub
```

**5. Copy files between repos:**
```python
from huggingface_hub import hffs

hffs.copy(
    "google-bert/bert-base-uncased/config.json",
    "my-org/my-repo/bert-config.json",
)
```

**6. Upload an entire directory:**
```python
from huggingface_hub import hffs

hffs.put(
    "./training-runs/experiment-1/",
    "my-org/my-repo/runs/experiment-1/",
    recursive=True,
)
```

**7. Use with pandas for data exploration:**
```python
import pandas as pd
from huggingface_hub import hffs

df = pd.read_parquet(
    "hf://datasets/cornell-movie-review-data/rotten_tomatoes/train.parquet"
)
print(df.head())
```

### Limitations & Pitfalls

| Limitation | Details |
|------------|---------|
| **No append mode** | `open(path, "a")` raises `NotImplementedError` |
| **Write commit semantics** | Data is written atomically on `close()`. No chunked/incremental writes. |
| **No file locking** | Concurrent writes to the same file can cause conflicts. |
| **Performance overhead** | fsspec adds overhead. For bulk operations, use `HfApi` methods directly. |
| **Path format strict** | Must use `namespace/name` format — single-segment IDs (e.g. `gpt2`) no longer work. |
| **Repository not found** | Non-existent repos raise `FileNotFoundError` with a clear message. |
| **Write operations require auth** | Must be authenticated with write permissions to the target repo. |
| **Revision for writes** | Write operations always target the default branch. Cannot write to arbitrary revisions. |

### When to Use HfApi Instead

```python
# Prefer HfApi for performance:
from huggingface_hub import HfApi
api = HfApi()

# Instead of fs.ls() → use api.list_repo_tree()
api.list_repo_tree("user/repo")

# Instead of fs.cat() → use api.hf_hub_download() with local caching
api.hf_hub_download("user/repo", "file.bin")

# Instead of fs.put() → use api.upload_folder()
api.upload_folder(folder_path="./data", repo_id="user/repo", path_in_repo="data")

# Instead of fs.info() → use api.repo_info() or api.get_paths_info()
api.repo_info("user/repo")
api.get_paths_info("user/repo", paths=["config.json"])
```

### References

- https://huggingface.co/docs/huggingface_hub/main/en/guides/hf_filesystem — Official HfFileSystem guide
- https://huggingface.co/docs/hub/en/storage-buckets — HF Storage Buckets (fsspec integration)
- https://filesystem-spec.readthedocs.io/ — fsspec specification
- Source: `huggingface_hub.hf_file_system` module (v1.24.0)

|---

## Entry 88: Gradio Workflows — Visual AI Pipeline Builder (6.17+ Deep Dive)
**Date:** 2026-07-24
**Topic:** `hf-gradio-workflows-deep-dive` — Complete reference on the `gr.Workflow` and `gr.WorkflowCanvas` visual pipeline builder, from the 6.17.0 release through 6.20.0

### Overview

Gradio **Workflows** (introduced in 6.17.0) is a visual AI pipeline builder that lets users wire Python functions, Hugging Face Spaces, and Inference API models together in a drag-and-drop canvas — no code required for the end user. The system has two layers:

- **`gr.Workflow`** (high-level, extends `gr.Blocks`): Self-contained app that reads/writes a `workflow.json` graph file, binds Python functions, exposes them as canvas nodes, and auto-registers API endpoints for subgraphs.
- **`gr.WorkflowCanvas`** (low-level component): The canvas UI itself. Can be embedded in arbitrary `gr.Blocks` layouts for fine-grained control over server functions.

### Architecture

A workflow graph has three core concepts:

| Concept | Description |
|---------|-------------|
| **Nodes** | Processing units. Each has an `id`, `kind` (transform), `source` (fn / space / model / dataset), and typed input/output ports. |
| **Edges** | Wires connecting a source node's output port to a target node's input port. Carry a `type` field (text/number/boolean/image/audio). |
| **Ports** | Typed connection points. Scalar Python types map to port types: `int`/`float` → `"number"`, `bool` → `"boolean"`, everything else → `"text"` (round-trips as JSON). |

#### Node Sources

| Source | Description | Backend |
|--------|-------------|---------|
| **`fn`** | Python function bound via `Workflow(bind=...)` | `call_fn()` — calls the bound function with JSON args |
| **`space`** | Any public HF Space (e.g. `black-forest-labs/FLUX.1-schnell`) | `call_space()` — uses `gradio_client` to call the Space's API |
| **`model`** | Any model on the HF Hub via Inference API | `call_model()` — uses `InferenceClient` with provider auto-routing |
| **`dataset`** | HF Dataset query node | `fetch_dataset()` — returns schema and fetches rows |

#### Graph JSON Format (Version 2)

```json
{
  "schema_version": "2",
  "name": "My Workflow",
  "nodes": [
    {
      "id": "fn_summarize",
      "source": "fn",
      "fn": "summarize",
      "kind": "transform",
      "label": "summarize",
      "x": 80,
      "y": 150,
      "width": 220,
      "height": 150,
      "inputs": [{"id": "in_text", "label": "text", "type": "text"}],
      "outputs": [{"id": "out_0", "label": "output", "type": "text"}],
      "data": {}
    },
    {
      "id": "img_gen",
      "source": "space",
      "space_id": "black-forest-labs/FLUX.1-schnell",
      "kind": "transform",
      "label": "FLUX.1-schnell",
      "x": 380,
      "y": 150,
      "width": 220,
      "height": 150,
      "inputs": [{"id": "in_0", "label": "input", "type": "text"}],
      "outputs": [{"id": "out_0", "label": "Image", "type": "image"}],
      "data": {}
    }
  ],
  "edges": [
    {
      "id": "edge_0",
      "from_node_id": "fn_summarize",
      "from_port_id": "out_0",
      "to_node_id": "img_gen",
      "to_port_id": "in_0",
      "type": "text"
    }
  ]
}
```

Save payloads **must** use `"schema_version": "2"` — version 1 payloads are rejected.

### `gr.Workflow` API Reference

```python
from gradio import Workflow

def summarize(text: str) -> str:
    """Summarize input text.

    Args:
        text: The text to summarize
    """
    return text[:200] + "..."

def reverse(text: str) -> str:
    """Reverse input text.

    Args:
        text: The text to reverse
    """
    return text[::-1]

# High-level API: extends gr.Blocks(mode="workflow")
Workflow(
    graph="workflow.json",             # Path to graph file (default: workflow.json in script's dir)
    bind={"summarize": summarize},      # Dict of name → callable, or list (auto-named by __name__)
    edges=[                             # Wire nodes when generating from bind (ignored if graph exists)
        ("summarize", "reverse"),
    ]
).launch()
```

#### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `graph` | `str \| None` | `workflow.json` in caller's directory | Path to graph JSON file. Created on first save if it doesn't exist. |
| `bind` | `dict[str, Callable] \| list[Callable] \| None` | `None` | Functions exposed as canvas nodes. List auto-names by `__name__`. Dict allows explicit names. |
| `edges` | `list[tuple[str, str]] \| None` | `None` | Wiring tuples `(from_endpoint, to_endpoint)`. `"fn_name"` uses first port; `"fn_name.port_label"` targets specific port. |

**Important:** `Workflow` cannot be created inside another `gr.Blocks` context — it IS a Blocks (subclass of `gr.Blocks` with `mode="workflow"`). Use `WorkflowCanvas` directly for nested scenarios.

#### Launch Behaviour

`Workflow.launch()` accepts all `gr.Blocks.launch()` parameters plus:

- **Write token (local mode):** A random `WRITE_TOKEN` is generated per process. The full edit link (including `?write_token=...`) is printed at launch. Share-link and tunnelled visitors get **read-only** access.
- **On Spaces:** Write access requires OAuth — the user must own the Space (or be an admin/write member of the owning org).
- **Allowed paths:** System tempdir is automatically added to `allowed_paths` so inference outputs (images, audio, video) served as `/gradio_api/file=...` URLs resolve correctly.

### `gr.WorkflowCanvas` API Reference

For fine-grained control (embedding in existing Blocks layouts):

```python
import gradio as gr

def my_custom_fn(text: str) -> str:
    return f"Processed: {text}"

with gr.Blocks() as demo:
    canvas = gr.WorkflowCanvas(
        value=None,                     # Initial JSON string, or callable returning JSON
        server_functions=[my_custom_fn],  # Functions callable from canvas via `server.my_custom_fn()`
    )

demo.launch()
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `value` | `str \| Callable \| None` | `None` | Initial workflow JSON. Callable re-reads per session load. |
| `server_functions` | `list[Callable] \| None` | `None` | Python functions exposed to the frontend canvas via a `server` object. Each is wrapped with `@server`. |
| `label` | `str \| None` | `None` | Not displayed by default (`show_label=False`) |
| `container` | `bool` | `False` | Renders without a container border |

**Duplicate name guard:** `server_functions` raises `ValueError` if any two functions share the same `__name__`.

### Backend Server Functions

The Workflow registers these server functions (all callable from the canvas frontend):

| Function | Purpose |
|----------|---------|
| `get_token()` | Return HF token for authenticated sessions (local: only with write token) |
| `get_write_access()` | Whether this session can edit the workflow |
| `get_oauth_available()` | Whether OAuth sign-in is wired (Space with `hf_oauth: true`) |
| `call_space(space_id, endpoint, args, hf_token)` | Call any public HF Space via `gradio_client` |
| `call_model(model_id, pipeline_tag, args, hf_token, provider)` | Call HF Inference API via `InferenceClient` |
| `fetch_dataset(dataset_id)` | Fetch dataset schema and sample rows |
| `search_spaces(query)` | Search HF Spaces by keyword |
| `search_models(query)` | Search HF Models by keyword |
| `search_datasets(query)` | Search HF Datasets by keyword |
| `search_quick(query)` | Unified search across all repo types |
| `resolve_repo(repo_id)` | Resolve repo ID to its metadata |
| `is_curated(repo_id)` | Check if repo is in curated workflow dataset |
| `curated_modalities()` | List available curated modalities |
| `curated_modality_tasks(modality)` | List tasks for a curated modality |
| `get_dataset_schema(dataset_id)` | Get column schema for a dataset |
| `list_bound_fns()` | List bound Python functions with their input/output port shapes |
| `get_workflow_api()` | Describe workflow subgraph API endpoints |
| `get_model_endpoints()` | List available Inference API endpoint schemas |
| `save_workflow(payload)` | Save workflow graph to disk (write-access required) |

#### Inference Endpoint Schemas

The `call_model` server function supports 18+ pre-built inference endpoint schemas:

| Endpoint | Inputs | Output |
|----------|--------|--------|
| `text_to_image` | prompt (text) | Image |
| `image_to_image` | image (image), prompt (text) | Image |
| `text_to_speech` | text (text) | Audio |
| `text_to_video` | prompt (text) | Video |
| `image_to_video` | image (image), prompt (text) | Video |
| `text_generation` | prompt (text) | Text |
| `summarization` | text (text) | Summary |
| `translation` | text, src_lang, tgt_lang | Translation |
| `fill_mask` | text (text) | JSON |
| `text_classification` | text (text) | JSON |
| `token_classification` | text (text) | JSON |
| `zero_shot_classification` | text, candidate_labels | JSON |
| `sentence_similarity` | sentence, other_sentences | JSON |
| `question_answering` | question, context | Answer |
| `feature_extraction` | text (text) | Embeddings |
| `image_classification` | image (image) | Labels |
| `object_detection` | image (image) | Detections |
| `image_segmentation` | image (image) | Segments |
| `image_to_text` | image (image) | Text |
| `automatic_speech_recognition` | audio (audio) | Text |
| `audio_classification` | audio (audio) | Labels |
| `visual_question_answering` | image, question | Answer |
| `document_question_answering` | image, question | Answer |

Unmapped pipeline tags fall through to `InferenceClient.chat_completion()`, then to a raw POST as last resort. Depth estimation uses a direct `httpx` POST (no InferenceClient method).

### Subgraph API Endpoints (6.19+)

Each workflow **subject** (output of a top-level group of connected nodes) is automatically exposed as a named API endpoint:

- Endpoints are registered via `WorkflowEndpointManager` during `_build()`
- Re-synced on every `save_workflow()` call — adding/removing/renaming outputs updates the live API
- Usable via Gradio's standard `/info`, `/call`, and `/api` routes
- The frontend "View API" panel shows these endpoints via `get_workflow_api()`

**Code-level registration:**
```python
# Each bound fn gets a named endpoint:
gr.api(wrapped_fn, api_name="predict_fn_summarize", concurrency_limit="default", api_visibility="undocumented")
```

### Security Model

| Context | Write Access | Read Access |
|---------|-------------|-------------|
| **Local** | Write token (`?write_token=...`) in URL | Anyone with the share link |
| **HF Space (OAuth)** | User must own Space (or admin/write org member) | Anyone with Space URL |
| **Share tunnel** | ❌ No write access | ✅ Read-only |

The write token is a per-process random `secrets.token_urlsafe(32)`. Checked in order: `x-gradio-workflow-write-token` header → `gradio_workflow_write_token_*` cookie → `write_token` query parameter. Cookie names are prefix-matched against the port to prevent cross-port clobbering.

Bound Python functions only execute in the server process — the `call_fn` server function receives the function name to call, not arbitrary code.

### Persistence & Auto-save

- **File location:** Defaults to `workflow.json` in the calling script's directory. Override with the `graph` parameter.
- **Save trigger:** User clicks Save in the canvas UI → frontend sends `save_workflow` server function with version-2 JSON payload.
- **Max payload:** 5 MB.
- **Re-read on load:** The canvas `value` is a callable that re-reads the file each browser session, so concurrent edits are visible on page refresh.
- **`edges` parameter ignored if graph file exists:** Delete the file to regenerate from `bind`/`edges`.

### Complete Code Example

**Python app (workflow_app.py):**
```python
from gradio import Workflow

def summarize(text: str) -> str:
    """Truncate text to first 200 chars as a summary.

    Args:
        text: The text to summarize
    """
    return text[:200] + "..."

def classify_sentiment(text: str) -> str:
    """Classify text sentiment.

    Args:
        text: The text to classify
    """
    if any(w in text.lower() for w in ["good", "great", "amazing", "excellent"]):
        return "positive"
    return "negative"

Workflow(
    bind={"summarize": summarize, "classify_sentiment": classify_sentiment},
    edges=[
        ("summarize", "classify_sentiment"),
    ]
).launch(share=True)
```

**WorkflowCanvas inside Blocks (advanced):**
```python
import gradio as gr

def fetch_temperature(location: str) -> str:
    """Get current temperature at a location.

    Args:
        location: City, Country format
    """
    return "22°C"  # mock

with gr.Blocks(title="Custom Workflow") as demo:
    gr.Markdown("# My Custom AI Pipeline")
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Controls")
            refresh = gr.Button("Refresh Canvas")
        with gr.Column(scale=3):
            canvas = gr.WorkflowCanvas(
                server_functions=[fetch_temperature],
            )
    refresh.click(None, None, None, js="() => location.reload()")

demo.launch()
```

### Changelog Evolution (6.17 → 6.20)

| Version | Key Workflow Changes |
|---------|---------------------|
| **6.17.0** | Initial release: `gr.Workflow` + `gr.WorkflowCanvas`. Graph persistence via `workflow.json`. HF Space/model/dataset/fn node types. Write token security model. |
| **6.17.2** | Bug fixes for initial adoption. |
| **6.17.3** | Additional stability fixes. |
| **6.18.0** | Drag selection of multiple nodes. Pipeline UX around pro accounts. HF token forwarding in Workflow nodes. Dropdown/radio/checkbox inputs preserved. Optional params not rendered on spawn. |
| **6.19.0** | **Subgraph endpoints** — each subgraph exposed as a named API endpoint, reused via `/info`, `/call`, `/api`. "View API" panel in canvas. |
| **6.20.0** | Auto-add node on port click. Downstream output shown on subgraph run. Inject token into bound `fn` functions. Model validation before invoking inference client. Gallery Download All support for image outputs. |

### Key Insights & Best Practices

1. **`gr.Workflow` is a standalone app** — it owns the full page (extends `Blocks` with `mode="workflow"`). Cannot nest inside another Blocks layout. Use `WorkflowCanvas` for embedding.
2. **Write token is single-use-per-process** — restart the app to get a new token. The token is printed at launch and is the ONLY way to edit locally.
3. **Edges only apply on first run** — once `workflow.json` exists on disk, the `edges` parameter is silently ignored. Delete the file to regenerate.
4. **Bound functions must be deterministic** — the `call_fn` server function executes them synchronously (or with `asyncio.run()` for coroutines). No persistent state between calls.
5. **Python function docstrings matter** — they are parsed (Google-style `Args:` blocks) to generate port labels and tooltips in the canvas.
6. **Scalar type hints are respected** — `int`/`float` params get number ports; `bool` gets boolean ports. Everything else is text (serialised as JSON).
7. **Injected params (`OAuthToken`, `OAuthProfile`, `Request`)** are automatically filled by the framework — the frontend doesn't see them as input ports.
8. **Dataset nodes** query the HF Hub directly — they're primarily for browsing/exploration rather than large-scale ETL.
9. **Schema v2 is mandatory for saves** — older v1 payloads are rejected with a clear error.
10. **Beta warning** — `gr.Workflow` prints a `UserWarning` at init: the API may change.

### References
- Gradio source: `gradio/workflow.py` (1853 lines) — the complete Workflow implementation
- Gradio source: `gradio/components/workflowcanvas.py` — the WorkflowCanvas component
- Gradio CHANGELOG (6.17.0 → 6.20.0): https://github.com/gradio-app/gradio/blob/main/CHANGELOG.md
- Gradio documentation: https://www.gradio.app/docs/gradio/main
- Hugging Face curated workflow dataset: `gradio/workflow-curated` on HF Hub

---

## Entry 89: Hub Upload Strategies — Publishing to Hugging Face Hub (Deep Dive)
**Date:** 2026-07-24
**Topic:** `hf-hub-upload-strategies` — Complete deep-dive on uploading files, folders, and large models to the Hugging Face Hub

### Overview

The Hugging Face Hub supports multiple upload strategies, each suited for different use cases — from single-file updates to publishing multi-gigabyte models. Choosing the right strategy affects upload speed, reliability, resumability, and storage efficiency. This entry provides a comprehensive comparison and deep-dive into each method.

### Upload Methods Comparison

| Method | Best For | Resumable | Concurrency | Atomic | CLI/Python |
|--------|----------|-----------|-------------|-------|------------|
| `hf upload` CLI | Ad-hoc single file/folder uploads | ❌ No | Sequential | ✅ Yes | CLI |
| `hf upload-large-folder` CLI | Large model directories (>1 GB) | ✅ Yes (manifest-based) | Parallel chunks | ❌ No (per-file) | CLI |
| `HfApi.upload_file()` | Single file from Python | ❌ No | Sequential | ❌ No | Python |
| `HfApi.upload_folder()` | Folder from Python | ❌ No | Sequential | ❌ No | Python |
| `HfApi.create_commit()` | Atomic multi-file update | ❌ No | Sequential ops | ✅ Yes | Python |
| `HfApi.upload_large_folder()` | Large folders from Python | ✅ Yes (manifest-based) | Parallel chunks | ❌ No | Python |
| `hf_transfer` Rust client | Very large files >5 GB | ⚠️ Semi (TCP-level) | Multi-threaded I/O | ❌ No | Env flag + pip |
| Xet storage backend | Dedup-friendly iterative releases | ✅ Content-addressed | Parallel + delta-only | ✅ Content-level | Env flag |
| Raw HTTP (requests) | Custom workflows, edge cases | ❌ No | Custom | ❌ No | Python |

### Method 1: `hf upload` CLI — Simple File/Folder Upload

The `hf` CLI's `upload` subcommand is the simplest path for one-off uploads:

```bash
# Upload a single file
hf upload user/my-model ./model.safetensors model.safetensors

# Upload a folder
hf upload user/my-model ./checkpoints/ --repo-type model

# Upload with specific commit message
hf upload user/my-model ./config.json --message "Update config for v2"

# Upload to specific branch
hf upload user/my-model ./model.safetensors --revision refs/pr/1

# Dry run (shows what would be uploaded)
hf upload user/my-model ./folder/ --dry-run
```

**Behind the scenes:** The CLI wraps `HfApi.upload_file()`/`upload_folder()` — it creates a commit operation for each file, then calls `create_commit()` atomically.

### Method 2: `hf upload-large-folder` CLI — Resumable Large Uploads

For model repositories >1 GB, use `upload-large-folder`:

```bash
# Upload a large model directory (resumable)
hf upload-large-folder user/my-70b-model ./full-model/

# With specific repo type
hf upload-large-folder user/my-dataset ./data/ --repo-type dataset

# Limit parallel uploads (default: all cores)
hf upload-large-folder user/my-model ./weights/ --num-workers 4
```

**How it works:**
1. Scans the folder and computes a manifest (file hashes + sizes)
2. Uploads files in parallel chunks (configurable via `--num-workers`)
3. Tracks progress in a local manifest file
4. On interruption, resumes from the last checkpoint
5. After all chunks complete, creates a final commit

**When to use:** Any repository >500 MB, especially models with multiple checkpoint files. Best for large publishing pipelines and CI/CD workflows.

### Method 3: `HfApi.upload_file()` / `upload_folder()` — Python API

```python
from huggingface_hub import HfApi

api = HfApi()

# Single file
api.upload_file(
    path_or_fileobj="model.safetensors",
    path_in_repo="model.safetensors",
    repo_id="user/my-model",
    repo_type="model",
)

# Folder with ignore patterns
api.upload_folder(
    folder_path="./output/",
    path_in_repo="checkpoints/",
    repo_id="user/my-model",
    repo_type="model",
    ignore_patterns=["*.tmp", "__pycache__/*", ".DS_Store"],
)

# Asynchronous (returns Future)
future = api.upload_file(
    path_or_fileobj="large.bin",
    path_in_repo="large.bin",
    repo_id="user/my-model",
    run_as_future=True,
)
result = future.result()
```

**Pitfall:** `upload_folder` respects `.gitignore` in the source folder unless `ignore_patterns` overrides it. If you have a `.gitignore` that excludes your model files, they won't be uploaded.

### Method 4: `HfApi.create_commit()` — Atomic Multi-File Operations

For atomic updates involving multiple files (add, delete, copy in one commit):

```python
from huggingface_hub import HfApi, CommitOperationAdd, CommitOperationDelete, CommitOperationCopy

api = HfApi()

api.create_commit(
    repo_id="user/my-model",
    operations=[
        CommitOperationAdd(
            path_in_repo="model.safetensors",
            path_or_fileobj="./model.safetensors",
        ),
        CommitOperationAdd(
            path_in_repo="config.json",
            path_or_fileobj={"architectures": ["LlamaForCausalLM"], "hidden_size": 4096},
        ),
        CommitOperationDelete(path_in_repo="old_version.bin"),
        CommitOperationCopy(
            src_path="README.md",
            path_in_repo="docs/README_ARCHIVE.md",
        ),
    ],
    message="Release v2.0: new model, config, archive old version",
    branch="main",
)
```

**Key properties:**
- **Atomic:** All operations succeed or none — no partial commits
- **Ordered:** Delete operations must precede copies/adds on the same path
- **Fileobj support:** Can pass dictionaries (auto-serialized as JSON), bytes, or file objects
- **Branch support:** Commits to any branch or PR ref

### Method 5: `HfApi.upload_large_folder()` — Resumable from Python

```python
from huggingface_hub import HfApi

api = HfApi()

api.upload_large_folder(
    folder_path="/models/my-70b",
    repo_id="user/my-70b",
    repo_type="model",
    num_workers=8,                   # parallel upload threads
    allow_duplicates=False,          # skip files with identical content
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `folder_path` | str | required | Local folder to upload |
| `repo_id` | str | required | Target repo |
| `path_in_repo` | str | `""` | Subdirectory in repo |
| `repo_type` | str | `"model"` | Type of repo |
| `revision` | str | `None` | Branch to commit to |
| `num_workers` | int | CPU cores | Parallel upload threads |
| `allow_duplicates` | bool | `False` | Skip files with same hash as existing |
| `ignore_patterns` | list | `None` | Glob patterns to exclude |

**Resumability mechanism:**
- On first run, creates a `.hfupload` manifest file alongside the folder
- Each chunk's upload status is tracked in the manifest
- On resume, already-uploaded chunks are skipped
- The manifest is cleaned up after a successful final commit
- If the manifest is lost or corrupted, the upload restarts from scratch

### Method 6: `hf_transfer` — Rust-Based Acceleration

```bash
# Install the Rust transport layer
pip install hf_transfer

# Enable it
export HF_HUB_ENABLE_HF_TRANSFER=1
```

**How it works:**
- Replaces Python's HTTP/HTTPS transport with a Rust implementation using `hyper` + `tokio`
- Provides true multi-threaded I/O: uploads file chunks in parallel
- Reduces CPU overhead from Python's GIL during large uploads
- Uses connection pooling for better throughput

**Performance characteristics:**
- **Files < 500 MB:** Marginal improvement (Python overhead is small)
- **Files 500 MB–5 GB:** 1.5–2× faster uploads
- **Files > 5 GB:** 2–3× faster with stable throughput (no Python GC pauses)

```python
import os
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"

from huggingface_hub import HfApi
api = HfApi()
# Now all uploads use the Rust transport
api.upload_file("large.bin", "large.bin", "user/my-model")
```

**Limitations:**
- Less granular progress reporting (no per-chunk progress bars)
- May be less stable on very slow/unreliable connections (no automatic retry at transport level)
- Must be set BEFORE importing `huggingface_hub` (env var is read at import time)

### Method 7: Xet Storage Backend — Content-Addressed Deduplication

The Xet backend provides content-addressed storage for the Hub:

```bash
# Install Xet support
pip install huggingface-hub[hf_xet]

# Enable Xet backend
export HF_STORAGE_BACKEND=xet
```

**Key concepts:**
- **Content-addressed:** Files are stored by hash, not path — identical content across revisions is stored once
- **Delta-only uploads:** When updating a model, only the changed bytes are uploaded, not entire files
- **Deduplication across repos:** If two repos share identical files (e.g., a base model), Xet stores them once
- **Bandwidth-efficient:** A fine-tuning checkpoint that changes 10% of weights only transfers 10% of data

```python
import os
os.environ["HF_STORAGE_BACKEND"] = "xet"

from huggingface_hub import HfApi
api = HfApi()

# Upload a model with dedup
# Only new/changed content is uploaded
api.upload_large_folder(
    folder_path="./finetuned-model",
    repo_id="user/finetuned-model",
)
```

**When Xet matters most:**
- Iterative model releases (multiple checkpoints, fine-tune variants)
- Large base models with small delta changes
- Repository families sharing common components
- CI/CD pipelines that publish regularly

**Xet vs hf_transfer:**

| Feature | Xet | hf_transfer |
|---------|-----|-------------|
| Deduplication | ✅ Content-addressed | ❌ No |
| Transport speed | Fast with dedup | ✅ Faster I/O |
| Best for | Iterative releases, CI/CD | Single large uploads |
| Resumable | ✅ Built-in | ⚠️ Partial |
| Env var | `HF_STORAGE_BACKEND=xet` | `HF_HUB_ENABLE_HF_TRANSFER=1` |
| Install | `huggingface-hub[hf_xet]` | `hf_transfer` |
| Both at once | ⚠️ Not recommended (conflicting optimization layers) | |

### Upload Lifecycle on the Hub

```
Client                              Hub
  |                                   |
  |-- 1. Preflight (auth + quota) --> |
  |<-- 2. Staging URL + token ------- |
  |                                   |
  |-- 3. Upload chunks to staging --> |
  |   (parallel, with retries)        |
  |                                   |
  |-- 4. Finalize staging ----------> |
  |                                   |
  |     5. Hub processing:            |
  |        • Virus scan               |
  |        • LFS detection            |
  |        • Xet dedup (if enabled)   |
  |        • Metadata extraction      |
  |        • Storage quota update     |
  |                                   |
  |<-- 6. Commit finalized ---------- |
  |                                   |
  |-- 7. Verify (optional) ---------> |
  |<-- 8. Repo info returned -------- |
```

### Upload Strategies by Use Case

#### Publishing a New Model (1–10 files, <1 GB)
```python
from huggingface_hub import HfApi, CommitOperationAdd

api = HfApi()
api.create_repo("user/new-model", repo_type="model")
api.create_commit(
    repo_id="user/new-model",
    operations=[
        CommitOperationAdd("config.json", "./config.json"),
        CommitOperationAdd("model.safetensors", "./model.safetensors"),
        CommitOperationAdd("README.md", "./README.md"),
    ],
    message="Initial release",
)
```

#### Publishing a Large Model (>1 GB, multiple shards)
```python
api.upload_large_folder(
    folder_path="./llama-70b-sharded",
    repo_id="user/llama-70b",
    num_workers=8,
)
```

#### Iterative Fine-Tuning Checkpoints
```python
import os
os.environ["HF_STORAGE_BACKEND"] = "xet"

from huggingface_hub import HfApi
api = HfApi()

for epoch in range(10):
    # Train... then upload only the changed files
    api.upload_folder(
        folder_path=f"./checkpoints/epoch-{epoch}",
        path_in_repo=f"checkpoints/epoch-{epoch}",
        repo_id="user/finetuned-model",
    )
```

#### CI/CD Pipeline Publishing
```bash
#!/bin/bash
set -euo pipefail

# Config
REPO="user/my-model"
VERSION="${CI_COMMIT_TAG:-$(git rev-parse --short HEAD)}"

# Upload with versioned directory
hf upload-large-folder "$REPO" "./release/" --path-in-repo "releases/$VERSION/"

# Verify
hf repo info "$REPO" --revision "main"
echo "Published $VERSION successfully"
```

### Error Handling & Retries

```python
from huggingface_hub import HfApi
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=30))
def upload_with_retry(api, path, repo_id):
    api.upload_file(path, path, repo_id)

api = HfApi()
try:
    upload_with_retry(api, "model.safetensors", "user/my-model")
except Exception as e:
    print(f"Upload failed after retries: {e}")
```

**Common errors:**
| Error | Cause | Solution |
|-------|-------|----------|
| `413 Payload Too Large` | File exceeds LFS limit | Use `upload_large_folder` for large files |
| `403 Forbidden` | No write permission | Check token scope; use `--token` flag |
| `409 Conflict` | Branch protection | Push to a feature branch, open PR |
| `502 Bad Gateway` | Hub temporary issue | Retry with exponential backoff |
| `InsufficientStorage` | Quota exceeded | Delete old LFS files or upgrade plan |

### Best Practices

1. **Use `upload_large_folder` for any repo >500 MB** — resumable upload saves time on failures
2. **Enable Xet for iterative releases** — deduplication dramatically reduces bandwidth for checkpoints
3. **Use `hf_transfer` for single large file uploads >5 GB** — maximizes throughput on fast connections
4. **Prefer `create_commit` for multi-file updates** — atomicity prevents partial-publish states
5. **Version your uploads** — use explicit branch names or directory structures for tracking
6. **Validate after upload** — always verify with `api.repo_info()` or `api.list_repo_tree()`
7. **Set `ignore_patterns`** — exclude cache, temp files, and virtual environments from folders
8. **Don't mix Xet and hf_transfer** — they optimize different layers; pick one based on your use case
9. **Use `allow_duplicates=False`** — skips files already present, saving time on re-runs
10. **Set `--dry-run` first** — preview what the CLI will upload before committing

### References
- https://huggingface.co/docs/huggingface_hub/main/en/guides/upload — Upload guide
- https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api — HfApi reference
- https://huggingface.co/docs/hub/en/repositories-getting-started#uploading-files — Hub upload docs
- https://huggingface.co/blog/hf_transfer — hf_transfer announcement blog
- https://huggingface.co/docs/hub/en/storage-xet — Xet storage backend docs
- https://huggingface.co/docs/huggingface_hub/main/en/guides/upload#resumable-uploads — Resumable uploads guide

---

## Entry 90: smolagents v1.26.0 — Complete Deep Dive
**Date:** 2026-07-24
**Topic:** `hf-smolagents` — Deep dive into Hugging Face's smolagents library v1.26.0

### Overview

`smolagents` is Hugging Face's open-source Python library for building AI agents. v1.26.0 (mid-2026) is a major evolution with first-class MCP (Model Context Protocol) support, multi-agent systems, structured output, and six model backends. The library's core philosophy is minimal abstractions — the agent loop fits in ~1000 lines of code.

### Architecture: Two Agent Types

smolagents provides two fundamentally different agent paradigms:

#### CodeAgent (Code-Writing Agent)
Generates Python code snippets to perform actions. Tools are exposed as Python functions:
```python
from smolagents import CodeAgent, InferenceClientModel
agent = CodeAgent(tools=[], model=InferenceClientModel())
agent.run("Calculate the sum of numbers from 1 to 10")
```

**Strengths:**
- Highly expressive — loops, conditionals, function composition, dynamic tool combination
- Flexible — no need to predefine every action; agent can synthesize new code
- Emergent reasoning — ideal for multi-step problems
- Additional imports via `additional_authorized_imports=['requests', 'bs4']`

**Limitations:**
- Requires secure execution environment (local, E2B, Blaxel, or Docker)
- Syntax errors and runtime exceptions possible
- Less predictable output format

#### ToolCallingAgent (JSON Tool-Calling Agent)
Outputs structured JSON tool calls (OpenAI-compatible format):
```python
from smolagents import ToolCallingAgent, WebSearchTool
agent = ToolCallingAgent(tools=[WebSearchTool()], model=model)
agent.run("Search for latest HF news")
```

**Strengths:**
- Reliable — structured outputs, strict schema validation
- Safe — no arbitrary code execution, arguments validated by schema
- Interoperable — maps directly to external APIs

**Limitations:**
- Low expressivity — can't easily chain or transform results dynamically
- Must predefine all possible actions
- No code synthesis

### Model Backends (6 Options)

smolagents v1.26.0 supports six model classes, all sharing the same agent interface:

| Model Class | Installation | Use Case |
|------------|-------------|----------|
| `InferenceClientModel` | Built-in (default) | HF Inference Providers (free tier available), most popular |
| `TransformersModel` | `smolagents[transformers]` | Local inference via transformers |
| `LiteLLMModel` | `smolagents[litellm]` | 100+ providers via LiteLLM (OpenAI, Anthropic, etc.) |
| `AzureOpenAIModel` | `smolagents[openai]` | Azure OpenAI deployments |
| `AmazonBedrockModel` | `smolagents[bedrock]` | AWS Bedrock (Claude, Nova) |
| `MLXModel` | `smolagents[mlx-lm]` | Apple Silicon local inference |

**Key patterns:**
```python
# HF Inference (default, free credits)
model = InferenceClientModel()  # Default model
model = InferenceClientModel(model_id="meta-llama/Llama-3.3-70B-Instruct", provider="together")

# LiteLLM for OpenAI/Anthropic
model = LiteLLMModel(model_id="gpt-4o")

# Local transformers
model = TransformersModel(model_id="meta-llama/Llama-3.2-3B-Instruct")
```

All models accept standard completion kwargs (`temperature`, `max_tokens`, `top_p`) plus the `REMOVE_PARAMETER` sentinel to explicitly exclude parameters.

### Secure Code Execution

CodeAgent supports four execution environments:

| `executor_type` | Environment | Setup Required |
|----------------|-------------|----------------|
| (default) | Local Python interpreter | None |
| `"blaxel"` | Blaxel sandbox | `BL_API_KEY`, `BL_WORKSPACE` env vars |
| `"e2b"` | E2B sandbox | `E2B_API_KEY` env var |
| `"docker"` | Docker container | Docker installed |

**Security model:**
- Only tools provided to the agent can be called
- Only safe builtins (print, math) available by default
- Imports restricted to a safe list; extend with `additional_authorized_imports`
- Submodule access is forbidden unless explicitly listed (e.g., `'numpy.random'`)
- Code execution stops on illegal operations or Python errors

### Tool System

#### Creating Tools

**Decorator method (recommended for simple tools):**
```python
from smolagents import tool

@tool
def model_download_tool(task: str) -> str:
    """Returns the most downloaded model of a given task on the HF Hub.

    Args:
        task: The task category (e.g., 'text-classification')
    """
    from huggingface_hub import list_models
    model = next(iter(list_models(filter=task, sort="downloads", direction=-1)))
    return model.id
```

**Subclass method (for complex tools):**
```python
from smolagents import Tool

class HFModelDownloadsTool(Tool):
    name = "model_download_counter"
    description = "Returns the most downloaded model for a task on the HF Hub."
    inputs = {"task": {"type": "string", "description": "the task category"}}
    output_type = "string"

    def forward(self, task: str):
        from huggingface_hub import list_models
        model = next(iter(list_models(filter=task, sort="downloads", direction=-1)))
        return model.id
```

**Pydantic input types:** `["string", "boolean", "integer", "number", "image", "audio", "array", "object", "any", "null"]`

#### Default Toolbox (with `add_base_tools=True`)

When using `smolagents[toolkit]`:
- **DuckDuckGo Web Search**: web search via DuckDuckGo
- **Python code interpreter**: secure code execution (CodeAgent only)
- **Transcriber**: speech-to-text via Whisper-Turbo

#### Sharing Tools to the Hub
```python
tool.push_to_hub("{username}/hf-model-downloads", token="hf_...")
```
Tools pushed to Hub become Gradio Spaces automatically. Load with:
```python
from smolagents import load_tool
tool = load_tool("{username}/hf-model-downloads", trust_remote_code=True)
```

#### Importing HF Spaces as Tools
```python
image_tool = Tool.from_space(
    "black-forest-labs/FLUX.1-schnell",
    name="image_generator",
    description="Generate an image from a prompt"
)
```
Uses `gradio-client` under the hood. Any public Gradio Space becomes an agent tool.

#### Using LangChain Tools
```python
from langchain.agents import load_tools
from smolagents import Tool

search_tool = Tool.from_langchain(load_tools(["serpapi"])[0])
```

### MCP (Model Context Protocol) Integration

smolagents v1.26.0 has first-class MCP support, the most advanced integration among HF agent frameworks.

#### Stdio-based MCP servers
```python
from smolagents import MCPClient, CodeAgent
from mcp import StdioServerParameters
import os

server_params = StdioServerParameters(
    command="uvx",
    args=["--quiet", "pubmedmcp@0.1.3"],
    env={"UV_PYTHON": "3.12", **os.environ},
)

with MCPClient(server_params) as tools:
    agent = CodeAgent(tools=tools, model=model, add_base_tools=True)
    agent.run("Find latest COVID-19 research.")
```

#### Streamable HTTP-based MCP servers
```python
with MCPClient({"url": "http://127.0.0.1:8000/mcp", "transport": "streamable-http"}) as tools:
    agent = CodeAgent(tools=tools, model=model, add_base_tools=True)
```

#### Multi-MCP support (connect to multiple servers)
```python
with MCPClient([server_params1, server_params2]) as tools:
    agent = CodeAgent(tools=tools, model=model, add_base_tools=True)
```

#### Structured Output (MCP 2025-06-18+ spec)
```python
with MCPClient(server_params, structured_output=True) as tools:
    agent = CodeAgent(tools=tools, model=model)
```
When enabled, tools with `outputSchema` return structured data. The agent's system prompt includes JSON schema info for smarter tool usage. **Will become default in a future release.**

#### ToolCollection.from_mcp() — Alternative API
```python
from smolagents import ToolCollection

with ToolCollection.from_mcp(server_params, trust_remote_code=True) as tc:
    agent = CodeAgent(tools=[*tc.tools], model=model, add_base_tools=True)
```

**Security note:** Always verify MCP server sources. Stdio servers execute code on your machine; Streamable HTTP servers don't, but still vet them.

### Advanced Agent Configuration

#### Custom Termination Conditions
```python
def is_integer(final_answer: str, agent_memory=None) -> bool:
    try:
        int(final_answer)
        return True
    except ValueError:
        return False

agent = CodeAgent(
    tools=[],
    model=InferenceClientModel(),
    final_answer_checks=[is_integer]
)
```
The agent will continue running if any check returns `False`, logging the error.

#### Custom Instructions (System Prompt Extension)
```python
agent = CodeAgent(
    tools=[],
    model=model,
    instructions="Always verify your answer with at least two sources."
)
```
Instructions are appended to the system prompt, not replacing it.

#### Inspecting Agent Runs
```python
agent.logs  # Fine-grained step logs (dict per step)
agent.write_memory_to_messages()  # Chat-format memory for LLM viewing
```

#### Passing Additional Arguments
```python
agent.run(
    "Transcribe this audio file",
    additional_args={"audio_url": "https://example.com/audio.mp3"}
)
```
These become accessible as Python variables in the agent's code execution.

#### Managing Toolbox at Runtime
```python
agent.tools["new_tool"] = my_custom_tool  # Add or replace
```

### CLI Tools

smolagents ships with a CLI for quick agent runs:
```bash
# Run interactively (prompts for arguments)
smolagent

# Run with direct prompt and options
smolagent "Plan a trip to Tokyo, Kyoto and Osaka between Mar 28 and Apr 7." \
  --model-type "InferenceClientModel" \
  --model-id "Qwen/Qwen2.5-Coder-32B-Instruct" \
  --imports "pandas numpy" \
  --tools "web_search"
```

### Best Practices for Building Good Agents

1. **Simplify workflows** — Group related tools into one to reduce LLM calls (latency, cost, error risk).
2. **Deterministic over agentic** — Prefer deterministic functions for logic; only use agent decisions when necessary.
3. **Log everything** — Each tool's `forward` method should `print()` useful info (including error details) for the LLM.
4. **Write clear tool descriptions** — Include format examples, error handling, and output format specifications.
5. **Start with a strong LLM** — Weak models fail at agentic reasoning. Test with Qwen2.5-72B or Llama-3.3-70B first.
6. **Provide detailed instructions** — If the task requires specific patterns, say so explicitly in instructions or tool descriptions.
7. **Don't overload tools** — Too many tools overwhelm weaker LLMs. Keep the toolbox focused.
8. **Use `final_answer_checks`** — Enforce output format requirements for robust agents.

### Key Insights

1. **`CodeAgent` is smolagents' killer feature** — no other HF agent framework has code-writing agents with this level of security controls and sandboxing.
2. **MCP support is best-in-class** — supports stdio, Streamable HTTP, multi-server, and structured output (2025-06-18+ spec). Hundreds of MCP servers from glama.ai/smithery.ai are directly usable.
3. **Free-tier accessible** — `InferenceClientModel` with default HF token works via Inference Providers, which include free credits.
4. **Model-agnostic** — Switch between HF Inference, OpenAI, Anthropic, local transformers, Ollama, AWS Bedrock, Azure, or MLX without changing agent code.
5. **Hub ecosystem** — Tools can be pushed to Hub as Gradio Spaces, Spaces can be imported as tools, and tool collections from Hub are first-class.
6. **Structured output is the future** — MCP 2025-06-18+ spec with `outputSchema` is the direction; adopt `structured_output=True` proactively.
7. **smolagents ≠ smol-course** — smolagents is an agent framework; smol-course is a fine-tuning curriculum.

### References
- Official docs: https://huggingface.co/docs/smolagents/en/index
- Guided tour: https://huggingface.co/docs/smolagents/en/guided_tour
- Tools guide: https://huggingface.co/docs/smolagents/en/tutorials/tools
- Building good agents: https://huggingface.co/docs/smolagents/en/tutorials/building_good_agents
- Secure code execution: https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution
- MCP specification: https://modelcontextprotocol.io/specification/2025-06-18
- GitHub: https://github.com/huggingface/smolagents
- Inference Providers blog: https://huggingface.co/blog/inference-providers
- Collection from Hub: https://huggingface.co/docs/smolagents/en/tutorials/tools#use-a-collection-of-tools

## Entry 85: HF Hub OAuth and Token Management — Complete Reference
**Date:** 2026-07-24
**Topic:** `hf-hub-oauth-and-token-management` — Authentication on the HF Hub: token types, OAuth flows, Token Exchange, Trusted Publishers, and Spaces OAuth

### Overview

The Hugging Face Hub supports multiple authentication mechanisms for different use cases:
- **User Access Tokens** — direct tokens for humans, scripts, and CI
- **OAuth 2.0 / OpenID Connect** — "Sign in with HF" for web apps, CLIs, and device flows
- **Token Exchange (RFC 8693)** — Enterprise feature to programmatically issue tokens for org members by email
- **Trusted Publishers** — CI/CD OIDC-based keyless authentication (no HF_TOKEN storage)
- **Spaces OAuth** — built-in OAuth for Spaces via `hf_oauth: true` in metadata

### 1. User Access Token Types

| Role | Scope | Use Case |
|------|-------|----------|
| **fine-grained** | Scoped to specific repos/orgs | Production: token scoped to exactly one gated model |
| **read** | All repos you can read (public + private) | Downloading private models, reading datasets |
| **write** | Read + write repos you have access to | Pushing models/datasets, CI/CD |

Best practice: **one token per app/use case**. Fine-grained tokens recommended for production — reduced blast radius if leaked.

### 2. Managing Tokens

- **Create**: `https://huggingface.co/settings/tokens` → New token → select role/name
- **Delete**: Manage → Delete (permanent)
- **Refresh**: Manage → Refresh (invalidates old token, keeps same scopes)
- **Organization Policies** (Team/Enterprise plans):
  - **Pending approval**: Fine-grained tokens scoped to an org with admin approval enter pending state
  - **Denied**: Token can't access org resources (gets 403), but still works outside org. Can be later approved.
  - **Revoked** (Enterprise only): Permanent — must delete and recreate. 403 with specific message.
  - **Fine-grained only policy**: Orgs can require fine-grained tokens; read/write tokens get 403 on org resources.

### 3. OAuth App Creation

#### Standard OAuth App
Create at `https://huggingface.co/settings/applications/new`:
- Client ID (public)
- Client Secret (confidential — keep secure)
- Redirect URIs (for authorization code flow)

#### Public OAuth Apps (No Secret)
- Create an app without a client secret
- Uses PKCE (Proof Key for Code Exchange) instead
- Ideal for CLIs, native apps, SPAs

#### Automated OAuth via CIMD
Supports **Client ID Metadata Documents** (CIMD) — add `/.well-known/oauth-cimd` to your domain returning:

```json
{
  "client_id": "https://yourdomain/.well-known/oauth-cimd",
  "client_name": "Your App",
  "redirect_uris": ["https://yourdomain/oauth/callback/huggingface"],
  "token_endpoint_auth_method": "none",
  "logo_uri": "https://...",
  "client_uri": "https://..."
}
```

Use the CIMD URL as client ID + PKCE — no manual app registration needed. Useful for ephemeral environments and MCP clients.

### 4. OAuth Flows

#### Authorization Code Flow (Web Apps)
```
GET https://huggingface.co/oauth/authorize?client_id=ID&redirect_uri=URI&scope=SCOPES&response_type=code&state=STATE
```
User authorizes → redirect back with `code` → `POST /oauth/token` with code → get access + ID tokens.

#### Device Code Flow (CLIs, Headless)
```
POST https://huggingface.co/oauth/device -d "client_id=$CLIENT_ID"
```
Returns `device_code`, `user_code`, `verification_uri`. User opens URL, enters code, authorizes. Then:

```
POST https://huggingface.co/oauth/token -d "grant_type=urn:ietf:params:oauth:grant-type:device_code" -d "device_code=$DEVICE_CODE" -d "client_id=$CLIENT_ID"
```

#### PKCE (Public Apps)
For apps without a client secret. Generate `code_verifier` (random string) → hash to `code_challenge` → send with authorization request → send verifier with token request.

### 5. OAuth Scopes (Supported)

| Scope | Access |
|-------|--------|
| `openid` | ID token (always included with OIDC) |
| `profile` | Username, avatar, etc. |
| `email` | User's email address |
| `read-billing` | Whether user has payment method |
| `read-repos` | Read access to user's personal repos |
| `gated-repos` | Read gated repos (not private repos) |
| `contribute-repos` | Create repos and access those created by app |
| `write-repos` | Write/read to user's personal repos |
| `manage-repos` | Full repo access + create/delete repos |
| `read-collections` | Read user's personal collections |
| `write-collections` | Write/read collections + create/delete |
| `inference-api` | Inference on behalf of user |
| `jobs` | Run Jobs |
| `webhooks` | Manage webhooks |
| `write-discussions` | Discussions, PRs, comments, reactions |

### 6. Spaces OAuth Integration

Add to Space's `README.md` metadata:

```yaml
hf_oauth: true
hf_oauth_expiration_minutes: 480
hf_oauth_scopes:
  - read-repos
  - inference-api
hf_oauth_authorized_org: ORG_NAME
```

Exposed as env vars: `OAUTH_CLIENT_ID`, `OAUTH_CLIENT_SECRET`, `OAUTH_SCOPES`, `OPENID_PROVIDER_URL`.

OpenID metadata available at `{OPENID_PROVIDER_URL}/.well-known/openid-configuration`.

Gradio has built-in OAuth support: `gr.Button(variant="primary").click(login, ...)` with `gr.OAuthLogin` component integration.

### 7. Token Exchange for Organizations (RFC 8693) — Enterprise

Programmatic token issuance for organization members — no interactive user consent.

**Prerequisites**: Organization-bound OAuth app with `token-exchange` privilege (contact HF support).

**Authentication**: HTTP Basic with Base64-encoded `client_id:client_secret`.

**Request** (issue token by email):
```bash
curl -X POST "https://huggingface.co/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $(echo -n 'client_id:client_secret' | base64)" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=user@yourorg.com" \
  -d "subject_token_type=urn:huggingface:token-type:user-email"
```

**Response**:
```json
{
  "access_token": "hf_oauth_...",
  "token_type": "bearer",
  "expires_in": 28800,
  "scope": "openid profile email read-repos",
  "id_token": "eyJhbGciOiJS...",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
}
```

**Security**:
- Organization-scoped only (cannot access user's personal repos)
- Default 8-hour expiry (org admin can configure up to 30 days)
- No refresh tokens
- All exchanges auditable via Audit Logs
- Protect OAuth app credentials — anyone with client secret can issue tokens for any org member

**Errors**: `invalid_client`, `invalid_grant`, `invalid_scope`

### 8. Trusted Publishers (CI/CD OIDC)

Keyless authentication from CI/CD pipelines — no `HF_TOKEN` secret to store.

**Supported providers**: GitHub Actions, GitLab CI, CircleCI, Bitbucket Pipelines (any OIDC-compliant provider works).

**Two flavors**:
- **Repo publisher** (configured on repo Settings → Trusted Publishers): write access to that one repo
- **User publisher** (configured in Authentication Settings → CI/CD Access): read-only, `gated-repos` scope

**How it works**:
1. CI provider mints an OIDC ID token describing the job
2. Client POSTs token to `POST https://huggingface.co/oauth/token` with `resource` (repo or username)
3. Hub verifies claims against configured publisher → returns short-lived HF token (valid 60 min)

**GitHub Actions example**:
```yaml
jobs:
  publish:
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Upload checkpoint
        env:
          HF_OIDC_RESOURCE: acme/awesome-model
        run: hf upload acme/awesome-model ./checkpoint .
```

**GitLab CI example**:
```yaml
publish:
  id_tokens:
    HF_ID_TOKEN:
      aud: https://huggingface.co
  script:
    - curl -LsSf https://hf.co/cli/install.sh | bash
    - export PATH="$HOME/.local/bin:$PATH"
    - HF_OIDC_ID_TOKEN="$HF_ID_TOKEN" HF_OIDC_RESOURCE="acme/awesome-model" hf upload acme/awesome-model .
```

**API reference**:
```
POST https://huggingface.co/oauth/token
Content-Type: application/json
{
  "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
  "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
  "subject_token": "<raw OIDC JWT>",
  "resource": "<namespace/name or username>"
}
```

**Security**: Tokens last 60 min, repo-scoped (can't touch other repos), attributed to `[OIDC]` system user. No refresh tokens.

### 9. Accessing Organization Resources via OAuth

By default OAuth apps don't access org resources. Add `orgIds=ORG_ID` as query param to authorization URL. Org ID is available in `organizations.sub` field of userinfo response.

Users select which orgs to grant access to during authorization.

### 10. Best Practices

1. **One token per app** — easy to rotate individual tokens without breaking everything
2. **Fine-grained tokens in production** — minimal blast radius if leaked
3. **Trusted Publishers for CI/CD** — no HF_TOKEN secret to store or rotate
4. **PKCE for public clients** — no client secret to embed in mobile/CLI apps
5. **Least privilege scopes** — request only scopes your app actually needs
6. **Short-lived tokens where possible** — Token Exchange (8h default), Trusted Publishers (1h)
7. **Monitor audit logs** — track token exchanges and failed auth attempts
8. **Use `whoami-v2` to verify** — `GET https://huggingface.co/api/whoami-v2` with Bearer token to check identity and permissions

### Key URLs

| Resource | URL |
|----------|-----|
| Token settings | https://huggingface.co/settings/tokens |
| Create OAuth app | https://huggingface.co/settings/applications/new |
| OAuth docs | https://huggingface.co/docs/hub/en/oauth |
| Token docs | https://huggingface.co/docs/hub/en/security-tokens |
| Trusted Publishers | https://huggingface.co/docs/hub/en/trusted-publishers |
| Spaces OAuth | https://huggingface.co/docs/hub/en/spaces-oauth |
| OpenID config | https://huggingface.co/.well-known/openid-configuration |
| Token endpoint | `POST https://huggingface.co/oauth/token` |
| Authorize endpoint | `GET https://huggingface.co/oauth/authorize` |
| Device endpoint | `POST https://huggingface.co/oauth/device` |
|| WhoAmI API | `GET https://huggingface.co/api/whoami-v2` |
|| RFC 8693 | https://www.rfc-editor.org/rfc/rfc8693.html |
|| RFC 8628 (Device Code) | https://www.rfc-editor.org/rfc/rfc8628.html |

---
## Entry 86: HF Hub Auth Deep-Dive — Device Code OAuth, Trusted Publishers API & Token Exchange in Practice
**Date:** 2026-07-24
**Topic:** `hf-hub-oauth-and-token-management` — Deep-dive into practical implementation of Device Code OAuth (Python polling loop), Trusted Publishers API (OIDC keyless CI/CD), and Token Exchange (RFC 8693) for organizations

### 1. Device Code OAuth — Full Python Implementation

Device Code flow is the primary authentication mechanism for CLIs, headless servers, and Hermes agents that cannot open a browser to redirect back.

#### Step 1: Create a Public OAuth App (PKCE-compatible)
- Visit https://huggingface.co/settings/applications/new
- Create an app with `token_endpoint_auth_method = none` (no client secret)
- For CIMD-automated creation: host `/.well-known/oauth-cimd.json` on your domain with `token_endpoint_auth_method: "none"`
- PKCE is used automatically when no client secret is provided

#### Step 2: Request Device Code

```python
import httpx
import webbrowser
import time
import json

CLIENT_ID = "your-public-client-id"

# Step 1: Get device code
resp = httpx.post(
    "https://huggingface.co/oauth/device",
    data={"client_id": CLIENT_ID},
)
device_data = resp.json()
# {
#   "device_code": "xxx",
#   "user_code": "ABCD-1234",
#   "verification_uri": "https://huggingface.co/device",
#   "verification_uri_complete": "https://huggingface.co/device?user_code=ABCD-1234",
#   "interval": 5,
#   "expires_in": 900
# }

print(f"Open: {device_data['verification_uri_complete']}")
print(f"Enter code: {device_data['user_code']}")
webbrowser.open(device_data['verification_uri_complete'])
```

#### Step 3: Poll for Token

```python
def poll_for_token(client_id: str, device_code: str, interval: int = 5, timeout: int = 900):
    """Poll the token endpoint until the user authorizes or the code expires."""
    start = time.time()
    while time.time() - start < timeout:
        resp = httpx.post(
            "https://huggingface.co/oauth/token",
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                "device_code": device_code,
                "client_id": client_id,
            },
        )
        if resp.status_code == 200:
            return resp.json()
        error = resp.json().get("error")
        if error == "authorization_pending":
            time.sleep(interval)
            continue
        elif error == "slow_down":
            interval += 5  # back off per RFC 8628
            time.sleep(interval)
            continue
        elif error == "expired_token":
            raise TimeoutError("Device code expired — user did not authorize in time")
        elif error == "access_denied":
            raise PermissionError("User denied authorization")
        else:
            raise RuntimeError(f"Unexpected error: {error}")
    raise TimeoutError("Polling timed out")

# On success, returns:
# {
#   "access_token": "hf_oauth_...",
#   "token_type": "bearer",
#   "expires_in": 28800,
#   "scope": "openid profile email read-repos",
#   "id_token": "eyJ...",
#   "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
# }
```

#### Step 4: Use the Token

```python
# Verify identity via whoami
whoami = httpx.get(
    "https://huggingface.co/api/whoami-v2",
    headers={"Authorization": f"Bearer {token['access_token']}"},
)
print(whoami.json()["name"])  # e.g., "beer-sakthai"

# Use with huggingface_hub
from huggingface_hub import HfApi
api = HfApi(token=token["access_token"])
models = api.list_models()
```

**Key considerations:**
- Tokens expire after 8 hours (28800s). No refresh token is issued — re-authenticate via device flow.
- The `id_token` is a JWT. Decode its payload (without verification for debugging) using `jwt.decode(id_token, options={"verify_signature": False})`.
- For headless environments without a browser, print `verification_uri_complete` as a QR code or direct URL.

### 2. Trusted Publishers — CI/CD OIDC Keyless Auth (API Reference)

Trusted Publishers let CI/CD workflows get a short-lived HF token without storing any `HF_TOKEN` secret, by exchanging the CI provider's OIDC identity token.

#### Architecture

```
┌──────────┐  1. mint ID token   ┌──────────┐  2. POST /oauth/token   ┌────────────┐
│ CI job   │ ──────────────────▶ │ CI OIDC  │ ──────────────────────▶│ huggingface│
│          │                     │ issuer   │                         │ /oauth/    │
│          │ ◀────────────────────────────────────────────────────────│ token      │
└──────────┘        3. short-lived HF token (valid 1h)                └────────────┘
```

#### Two Flavors

**Repo-scoped token:**
- Configure Trusted Publisher on a specific repo (Settings → Trusted Publishers)
- Token can read/write only that repo
- Pushes attributed to synthetic `[OIDC]` system user
- Token prefix: `hf_jwt_...`

**User-scoped token:**
- Configure Trusted Publisher on a user account
- Token can read gated repos the user has access to, uses user's rate limits
- Read-only: `gated-repos` scope only. Cannot write or read private repos.
- Token prefix: `hf_oauth_...`

#### Raw API — Exchange OIDC Token (Python)

```python
import httpx, os

# Get the OIDC token from CI environment
id_token = os.environ.get("HF_OIDC_ID_TOKEN") or os.environ.get("ID_TOKEN") or os.environ.get("CIRCLE_OIDC_TOKEN_V2")

resp = httpx.post(
    "https://huggingface.co/oauth/token",
    json={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
        "subject_token": id_token,
        "resource": "beer-sakthai",  # username for user-scoped, or "acme/model" for repo-scoped
    },
)
if resp.status_code == 200:
    hf_token = resp.json()["access_token"]
    # hf_token expires in 3600 seconds (1 hour) — re-exchange for long jobs
else:
    error = resp.json().get("error", "unknown")
    print(f"Exchange failed: {error}")
```

#### CI Provider Examples

**GitHub Actions:**
```yaml
jobs:
  publish:
    permissions:
      id-token: write  # required to mint OIDC token
    steps:
      - name: Download gated model
        env:
          HF_OIDC_RESOURCE: beer-sakthai
        run: hf download acme/gated-model
```

**GitLab CI:**
```yaml
job:
  id_tokens:
    HF_ID_TOKEN:
      aud: https://huggingface.co
  script:
    - HF_OIDC_ID_TOKEN=$HF_ID_TOKEN HF_OIDC_RESOURCE=beer-sakthai hf download acme/gated-model
```

**CircleCI:**
```yaml
version: 2.1
jobs:
  publish:
    steps:
      - run: |
          HF_OIDC_ID_TOKEN=$CIRCLE_OIDC_TOKEN_V2 HF_OIDC_RESOURCE=beer-sakthai hf download acme/gated-model
```

#### Error Handling for Trusted Publishers

| `error` | Cause | Fix |
|---------|-------|-----|
| `invalid_request` | Missing/malformed parameter or bad resource format | Check `resource` syntax |
| `invalid_grant` | Repo/user not found; no publisher matches; claim mismatch; signature/audience failed; account locked | Verify Trusted Publisher config, audience claim, and issuer URL |

The `hf` CLI surfaces `(Request ID: ...)` on failure — include this in support requests.

#### Security Model

- Tokens are short-lived (60 min). No refresh token. Long jobs must re-exchange.
- Repo tokens are repo-scoped only — cannot touch other repos.
- Claims are matched exactly — no regex, no prefix matching.
- Every exchange is logged in audit logs with last-used timestamp.
- Configure claims per provider (e.g., only `repo:owner/name:ref:refs/heads/main` for main-branch-only access).

### 3. Token Exchange for Organizations (RFC 8693) — Enterprise

Enterprise orgs can programmatically issue tokens for members by email, without requiring each member to create their own token.

#### Prerequisites
- Enterprise plan
- OAuth app bound to the organization
- Org admin creates the app at Settings → Applications

#### Authentication

```bash
# Basic Auth with client_id:client_secret
AUTH_HEADER=$(echo -n "client_id:client_secret" | base64)

curl -X POST "https://huggingface.co/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -H "Authorization: Basic $AUTH_HEADER" \
  -d "grant_type=urn:ietf:params:oauth:grant-type:token-exchange" \
  -d "subject_token=user@yourorg.com" \
  -d "subject_token_type=urn:huggingface:token-type:user-email"
```

#### Python Implementation

```python
import httpx, base64

client_id = "your-client-id"
client_secret = "your-client-secret"
auth = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()

resp = httpx.post(
    "https://huggingface.co/oauth/token",
    data={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": "user@yourorg.com",
        "subject_token_type": "urn:huggingface:token-type:user-email",
    },
    headers={"Authorization": f"Basic {auth}"},
)
token = resp.json()
# access_token, token_type, expires_in, scope, issued_token_type
```

#### Scope Control

By default, issued tokens inherit all scopes configured on the OAuth app. Request specific scopes via the `scope` parameter:

```python
resp = httpx.post(
    "https://huggingface.co/oauth/token",
    data={
        "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
        "subject_token": "user@yourorg.com",
        "subject_token_type": "urn:huggingface:token-type:user-email",
        "scope": "openid profile read-repos",  # restrict to only needed scopes
    },
    headers={"Authorization": f"Basic {auth}"},
)
```

**Security constraints:**
- Organization-scoped only: tokens access resources within the org only
- No personal private repos or other orgs
- Short-lived: 8 hours default (admin-configurable up to 30 days)
- No refresh tokens
- All exchanges logged in org audit logs

#### Error Responses

| Error | Description |
|-------|-------------|
| `invalid_client` | Client not authorized for token exchange, or app not bound to org |
| `invalid_grant` | User not found in the bound organization |
| `invalid_scope` | Requested scope is not valid |

### 4. Organization Token Policies (Team/Enterprise)

Orgs on Team/Enterprise plans can enforce token policies:

**Pending Approval:** Fine-grained tokens scoped to the org require admin approval. Until approved, they show an orange hourglass icon and cannot access org resources. Admins auto-approve their own tokens.

**Denied:** Token gets 403 on org resources but works outside the org. Can be later approved by an admin without recreation.

**Revoked (Enterprise only):** Permanent — token must be deleted and recreated. 403 with message: *"Your token has been revoked by the organization administrator..."* Only affects the revoking org.

**Fine-grained-only policy:** Orgs can require fine-grained tokens globally. Read/write tokens get 403 on org resources.

### Key Differences Between Auth Mechanisms

| | Device Code OAuth | Trusted Publishers | Token Exchange |
|---|---|---|---|
|**Use case** | CLI / headless auth | CI/CD pipelines | Enterprise org member tokens |
|**Auth method** | Browser-based consent | OIDC identity token | Client secret + user email |
|**Token lifetime** | 8 hours | 1 hour | 8 hours (configurable to 30d) |
|**Refresh** | No — re-auth | No — re-exchange | No |
|**Scope** | Full per-user scopes | Repo-scoped or read-only user | Org-scoped |
|**Plan required** | Free | Free | Enterprise |
|**Token prefix** | `hf_oauth_` | `hf_jwt_` (repo) / `hf_oauth_` (user) | `hf_oauth_` |

---

## 2026-07-27: hf-spaces-oauth-app-integration — Complete Spaces OAuth Guide (Topic #208)

### Summary
Comprehensive guide to adding a **"Sign-In with HF"** button to Hugging Face Spaces using OAuth 2.0 / OpenID Connect. Covers the automatic OAuth app creation via Space config (`hf_oauth: true`), the full list of scopes, the authorization code flow with PKCE, device code flow for CLIs, CIMD (Client ID Metadata Documents) for ephemeral apps, Gradio's built-in OAuth support, huggingface.js integration, and Python device code examples. Complements the existing OAuth token presets and token exchange content above.

### Sources
- Official docs: https://huggingface.co/docs/hub/en/spaces-oauth
- General OAuth page: https://huggingface.co/docs/hub/en/oauth
- CIMD spec: https://datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/
- OpenID metadata: https://huggingface.co/.well-known/openid-configuration
- Gradio OAuth guide: https://www.gradio.app/guides/sharing-your-app#o-auth-login-via-hugging-face
- huggingface.js OAuth: https://huggingface.co/docs/huggingface.js/hub/README#oauth-login
- Reference Space (Gradio): https://huggingface.co/spaces/Wauplin/gradio-oauth-test
- Reference Space (JS/static): https://huggingface.co/spaces/huggingfacejs/client-side-oauth

### 1. Architecture Overview

HF Spaces OAuth uses the **authorization code flow** with PKCE (Proof Key for Code Exchange by OAuth public clients). There are two modes:

| Mode | Setup Effort | Auth Method | Best For |
|------|-------------|-------------|----------|
| **Automatic (Spaces)** | Minimal — one YAML line | Auto-provisioned OAuth app via Space metadata | Gradio/Streamlit/Docker Spaces |
| **Manual (External)** | Register app in settings | Manual client ID + secret creation | Websites, CLIs, non-Space apps |

Spaces automatically create and associate an OAuth app when `hf_oauth: true` is set in the Space's config. No manual app creation needed.

```
User's Browser           HF OAuth Server          Your Space
     │                        │                      │
     │── authorize request ──→│                      │
     │                        │── consent modal ──→  │
     │←── auth code ──────────│                      │
     │── token exchange ────→│                      │
     │←── access token ──────│                      │
     │── API calls ──────────│─────────────────────→│
```

### 2. Automatic OAuth in Spaces (The Easy Way)

#### Step 1: Enable in Space Metadata

Add to your Space's `README.md`:

```yaml
hf_oauth: true
# optional: token duration (default 480 min, max 43200 min = 30 days)
hf_oauth_expiration_minutes: 480
# optional: request additional scopes beyond openid + profile
hf_oauth_scopes:
  - read-repos
  - inference-api
# optional: restrict auth to specific org members
hf_oauth_authorized_org:
  - ORG_NAME1
  - ORG_NAME2
```

#### Step 2: Environment Variables Injected

The Space runtime automatically injects these environment variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `OAUTH_CLIENT_ID` | Public client ID | `Spaces_abc123` |
| `OAUTH_CLIENT_SECRET` | Client secret (keep private) | `sk-...` |
| `OAUTH_SCOPES` | Comma-separated scope list | `openid,profile,inference-api` |
| `OPENID_PROVIDER_URL` | OpenID metadata endpoint | `https://huggingface.co` |

Use them anywhere in your code: `os.getenv("OAUTH_CLIENT_ID")`.

#### Step 3: Redirect URLs

Any URL targeting your Space can be a redirect URI. Use `SPACE_HOST` (another environment variable):

```python
import os
redirect_uri = f"https://{os.getenv('SPACE_HOST')}/login/callback"
```

### 3. OAuth Scopes — Complete Reference

#### Always Included (mandatory, no extra config needed)

| Scope | Grants |
|-------|--------|
| `openid` | ID token (user identity) |
| `profile` | Username, avatar, name from user profile |

#### Optional (add via `hf_oauth_scopes`)

| Scope | Grants | Use Case |
|-------|--------|----------|
| `email` | User's email address | User verification |
| `read-billing` | Whether user has payment method set up | Check subscription status |
| `read-repos` | Read access to user's personal repos | List user repos |
| `gated-repos` | Read content from gated repos user has access to | Access gated model weights |
| `contribute-repos` | Create repos + access app-created repos | Allow users to push to their own Spaces |
| `write-repos` | Write/read to user's personal repos | Edit configs, push datasets |
| `manage-repos` | Full repo access + create/delete repos | Admin-like access |
| `read-collections` | Read user's personal collections | Browse collections |
| `write-collections` | Write/read + create/delete collections | Manage collections |
| `inference-api` | Call Inference Providers on user's behalf | Serverless inference using user's quota |
| `jobs` | Run HF Jobs | Scheduled inference/training |
| `webhooks` | Manage webhooks | Subscribe to Hub events |
| `write-discussions` | Open/interact with discussions and PRs | Community engagement |

**Important:** Scopes are additive — more scopes = more trust. Only request what you need.

### 4. The OAuth Flow — Step by Step

#### Authorization Code Flow with PKCE (Spaces)

**Step A — Build the authorize URL:**
```
https://huggingface.co/oauth/authorize?
  redirect_uri={REDIRECT_URI}&
  scope=openid%20profile&
  client_id={CLIENT_ID}&
  state={STATE}&
  code_challenge={SHA256_CODE_VERIFIER}&
  code_challenge_method=S256
```

- `STATE`: cryptographically random string (validated on callback — prevents CSRF)
- `code_challenge`: SHA-256 hash of a random `code_verifier` string (PKCE — prevents auth code interception)
- Always use PKCE for public clients (Spaces apps are public by nature)

**Step B — Handle the callback:**
User authorizes → HF redirects to `{REDIRECT_URI}?code={AUTH_CODE}&state={STATE}`
- Verify `state` matches what you sent
- Exchange `code` for tokens

**Step C — Token exchange (POST to `https://huggingface.co/oauth/token`):**
```
POST /oauth/token
Content-Type: application/x-www-form-urlencoded
Authorization: Basic {base64(client_id:client_secret)}

client_id={CLIENT_ID}&
code={AUTH_CODE}&
grant_type=authorization_code&
redirect_uri={REDIRECT_URI}&
code_verifier={ORIGINAL_CODE_VERIFIER}
```

**Response:**
```json
{
  "access_token": "hf_oauth_...",
  "token_type": "bearer",
  "expires_in": 28800,
  "id_token": "eyJ..."
}
```

- `access_token` — Bearer token for API calls (prefix: `hf_oauth_`)
- `id_token` — JWT containing user identity claims (username, avatar URL, name)
- Tokens expire in 8 hours by default, no refresh token

#### Device Code Flow (CLI / Headless)

For CLI tools that can't open a browser redirect:

**Step 1 — Request device code (POST to `/oauth/device`):**
```
POST https://huggingface.co/oauth/device
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
scope=openid profile
```

For apps with a secret, add: `Authorization: Basic {base64(client_id:client_secret)}`

**Response:**
```json
{
  "device_code": "abc-def-ghi",
  "user_code": "HF-1234",
  "verification_uri": "https://huggingface.co/oauth/authorize",
  "verification_uri_complete": "https://huggingface.co/oauth/authorize?user_code=HF-1234",
  "expires_in": 900,
  "interval": 5
}
```

**Step 2 — Poll for token (POST to `/oauth/token`):**
```
POST https://huggingface.co/oauth/token
Content-Type: application/x-www-form-urlencoded

client_id={CLIENT_ID}
device_code={DEVICE_CODE}
grant_type=urn:ietf:params:oauth:grant-type:device_code
```

Poll every `interval` seconds until user completes auth in browser.

**Python device code example (public app, no secret):**
```python
import httpx, time, webbrowser

CLIENT_ID = "your-client-id"
client = httpx.Client()

# Step 1: request device code
resp = client.post("https://huggingface.co/oauth/device", data={
    "client_id": CLIENT_ID,
    "scope": "openid profile",
})
device = resp.json()
print(f"Go to {device['verification_uri_complete']} and enter code: {device['user_code']}")
webbrowser.open(device["verification_uri_complete"])

# Step 2: poll for token
for _ in range(device["expires_in"] // device["interval"]):
    time.sleep(device["interval"])
    resp = client.post("https://huggingface.co/oauth/token", data={
        "client_id": CLIENT_ID,
        "device_code": device["device_code"],
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
    })
    if resp.status_code == 200:
        token = resp.json()["access_token"]
        print(f"Authenticated! Token: {token[:20]}...")
        break
    elif resp.status_code == 400 and resp.json().get("error") == "authorization_pending":
        continue  # user hasn't completed auth yet
```

### 5. Gradio Built-in OAuth (Zero-Code Option)

Gradio Spaces have **built-in OAuth support** that requires no custom OAuth code. Add `hf_oauth: true` to Space metadata, then use `gr.OAuthView` or `gr.OAuthIdentity`:

```python
import gradio as gr

# Option 1: Check authentication in any function
def greet(request: gr.Request):
    if request.oauth_user:
        return f"Hello, {request.oauth_user['name']}!"
    return "Please sign in."

# Option 2: Use OAuth-protected views
with gr.Blocks() as demo:
    gr.OAuthView(gr.Markdown("🔒 You are logged in!"))
    gr.OAuthButton("Sign in with HF")

demo.launch()
```

Gradio automatically handles the redirect, token exchange, and user info retrieval. The `request.oauth_user` dict contains:
```python
{
  "sub": "user_id",
  "name": "Display Name",
  "preferred_username": "username",
  "avatar_url": "https://cdn-avatars.huggingface.co/...",
  "email": "user@example.com",  # only if `email` scope requested
}
```

### 6. JavaScript / Static Spaces (huggingface.js)

For static Spaces built with JavaScript, use `@huggingface/hub`:

```javascript
import { oauthLoginUrl, oauthHandleRedirectIfPresent } from "@huggingface/hub";

const oauthResult = await oauthHandleRedirectIfPresent();

if (!oauthResult) {
  window.location.href = await oauthLoginUrl();
}

// Access token + user info available
console.log(oauthResult.accessToken);
console.log(oauthResult.userInfo);
```

The library reads `OAUTH_CLIENT_ID` from the environment, handles PKCE automatically, and manages the full redirect flow.

### 7. CIMD (Client ID Metadata Documents)

Hugging Face supports **Client ID Metadata Documents** (CIMD), an IETF draft standard for automated OAuth app creation. This is useful for ephemeral environments or MCP clients.

Instead of manually creating an OAuth app, the server reads metadata from `/.well-known/oauth-client-metadata/{client_id}`:

```
https://huggingface.co/.well-known/oauth-client-metadata/Spaces_abc123
```

This allows:
- Automated app discovery
- No settings page registration needed
- Metadata includes redirect URIs, scopes, and app info

**Implementation example:** HuggingChat's PR #1978 shows how CIMD works in practice.

### 8. Organization Restriction

Restrict OAuth to organization members only:

```yaml
# Single org
hf_oauth_authorized_org: MY_ORG

# Multiple orgs
hf_oauth_authorized_org:
  - ORG_1
  - ORG_2
```

Unauthorized users see "You are not authorized to use this Space" on sign-in.

### 9. Security & Production Patterns

| Pattern | Implementation |
|---------|---------------|
| **Always use PKCE** | Public client (no secret) apps must use code_challenge + code_verifier |
| **Validate state** | Prevents CSRF on callback — generate random string, verify on return |
| **HTTPS only** | Redirect URIs must use HTTPS (Spaces auto-provide it) |
| **Short expiration** | Default 8h (480 min); max 30 days (43200 min) |
| **Use target=_blank** | Open auth in new tab to avoid iframe cookie issues |
| **Scoped tokens** | Request minimum scopes needed — never `manage-repos` unless required |
| **Secret rotation** | Space OAuth secrets are auto-managed, no manual rotation needed |
| **Audit logging** | Enterprise orgs get audit logs of all token exchanges |

### 10. Limitations & Constraints

| Constraint | Detail |
|------------|--------|
| No refresh tokens | User must re-auth after expiration |
| Max expiration | 30 days (43200 minutes) |
| Scope changes | Require re-authorization from user |
| Device code max polling | 15 minutes (900 seconds) before device_code expires |
| Redirect URI scheme | HTTPS only (Spaces enforce this automatically) |
| Gradio version | OAuth support requires Gradio 4.x+ (built-in since ~4.0) |
| Static Spaces | Must use JS library or implement OAuth manually |

### References
- https://huggingface.co/docs/hub/en/spaces-oauth
- https://huggingface.co/docs/hub/en/oauth
- https://huggingface.co/.well-known/openid-configuration
- https://www.gradio.app/guides/sharing-your-app#o-auth-login-via-hugging-face
- https://huggingface.co/docs/huggingface.js/hub/README#oauth-login
- https://github.com/huggingface/chat-ui/pull/1978 (CIMD example)
- https://datatracker.ietf.org/doc/draft-ietf-oauth-client-id-metadata-document/
- https://huggingface.co/docs/hub/spaces-overview#helper-environment-variables
- Gradio OAuth reference Space: https://huggingface.co/spaces/Wauplin/gradio-oauth-test
- Static JS OAuth reference: https://huggingface.co/spaces/huggingfacejs/client-side-oauth

---

## Entry 146: huggingface_hub Authentication Pipeline — Source-Code Deep Dive (2026-07-25)
**Date:** 2026-07-25
**Topic:** hf-auth-login-internals-deep-dive — The complete internal implementation of login/logout/token management in huggingface_hub v1.24.0

### Modules Involved

The authentication pipeline spans four modules:

| Module | File | Role |
|--------|------|------|
| _login.py | huggingface_hub/_login.py | High-level user-facing API: login(), logout(), auth_switch(), auth_list(), notebook_login(), interpreter_login() |
| utils/_auth.py | huggingface_hub/utils/_auth.py | Token resolution, storage, refresh: get_token(), _save_token(), OIDC token exchange, transparent OAuth token refresh |
| utils/_oauth_device.py | huggingface_hub/utils/_oauth_device.py | Pure protocol implementation of Device Code OAuth (RFC 8628) and OAuth token refresh — no UI, no persistence, just HTTP |
| _oidc.py | huggingface_hub/_oidc.py | CI/CD Trusted Publishers — OIDC id token minting + RFC 8693 token exchange for keyless auth |

### 1. Token Resolution Chain (get_token())

The single entry point for all auth is get_token() (in utils/_auth.py). Resolution order:

1. HF_OIDC_RESOURCE set? -> OIDC token exchange (Trusted Publishers)
2. HF_TOKEN env var? -> from environment (HF_TOKEN -> HUGGING_FACE_HUB_TOKEN for backward compat)
3. ~/.cache/huggingface/token? -> from file, with transparent OAuth refresh
4. Google Colab vault? -> google.colab.userdata.get("HF_TOKEN")
5. None -> not logged in

Key design: each step short-circuits. If OIDC is configured, it takes precedence over everything (and raises on failure — no silent fallback). The Colab path runs only once per process (global _IS_GOOGLE_COLAB_CHECKED flag with per-process secret cache _GOOGLE_COLAB_SECRET, thread-safe via Lock()).

### 2. Token Storage System

Tokens are stored in two files:

**Active token file** (HF_TOKEN_PATH):
- Single raw token value (just the string, no metadata)
- Created/updated by _write_secret() which sets 0o600 file mode + 0o700 parent dir mode (POSIX only; best-effort on Windows)

**Stored tokens file** (HF_STORED_TOKENS_PATH):
- INI format using configparser (interpolation disabled to preserve % in tokens)
- Each section is a token name, with fields:
  - hf_token (required) — the actual token value
  - refresh_token (optional) — OAuth refresh token
  - expires_at (optional) — Unix timestamp of token expiry
- Written atomically via _write_secret() — same restrictive permissions

### 3. OAuth Token Refresh Pipeline

OAuth tokens obtained via browser-based login have refresh_token and expires_at. The _get_token_from_file_refreshed() function in utils/_auth.py transparently refreshes them:

get_token() -> _get_token_from_file_refreshed(token)
  -> _get_token_from_file() (read raw token)
  -> _refresh_oauth_token_if_needed(token)

Key mechanics:
- **In-process cache** (_OAUTH_REFRESH_CACHE): avoids re-reading stored tokens file (and re-hitting the network) on every get_token() call — critical since get_token() runs on every HTTP request
- **Recheck interval**: _OAUTH_RECHECK_INTERVAL = 300s (5 min) when no metadata or refresh failed
- **Refresh margin**: _OAUTH_REFRESH_MARGIN = 86400s (24 hours) — refreshes when less than 1 day of validity remains
- **Cross-process safety**: uses WeakFileLock on HF_STORED_TOKENS_PATH with 30s timeout to prevent multiple processes invalidating each other's refresh token
- **Graceful failure**: refresh failures never raise — the expired token is returned (API will reject it) and a warning is logged at most once per process (_OAUTH_REFRESH_WARNED global flag)
- **Refresh token rotation**: the server may rotate refresh tokens; the old refresh token is kept if the response doesn't include a new one

### 4. Login Entry Points

**login(token=None)** (default path):
1. If token passed directly -> _validate_and_save_token(token, add_to_git_credential)
2. If no token -> auto-detect environment:
   - In a notebook: delegates to notebook_login()
   - In a terminal: delegates to interpreter_login()

**notebook_login()**:
1. Checks skip_if_logged_in (default True) — returns early if get_token() is not None
2. Falls back to interpreter_login() if IPython not available
3. Calls request_device_code() to get device + user code
4. Displays HTML widget with verification URL + code
5. Calls poll_device_token(device_info) to poll for authorization
6. On success: _save_oauth_token(response) -> _validate_and_save_token(response["access_token"])
7. On failure: displays error in HTML widget

**interpreter_login()**:
1. Checks skip_if_logged_in
2. Offers a choice via select_choice(): browser-based OAuth vs paste existing token
3. Browser choice: calls _device_code_login()
4. Paste choice: prompts for token with getpass(), calls _validate_and_save_token()

### 5. Token Validation Pipeline (_validate_and_save_token)

When a token is provided (from any login path), the validation chain is:

1. **Org token rejection**: tokens starting with api_org raise ValueError immediately
2. **whoami(token) call**: validates against /api/whoami-v2
3. **Extract metadata**:
   - name -> HF username
   - auth.accessToken.displayName -> token display name (or oauth-{username} for OAuth tokens)
   - auth.accessToken.role -> permission role (logged as info)
4. **Persist**: _save_token(token, token_name, refresh_token, expires_at) -> stored_tokens INI
5. **Set active**: _set_active_token(token_name, add_to_git_credential):
   - Writes token to HF_TOKEN_PATH via _write_secret()
   - Optionally sets git credential helper
6. **Env var override warning**: warns if HF_TOKEN env var is set (overrides stored token)

### 6. Logout Pipeline

**logout(token_name=None)**:
- No token_name -> delete ALL stored tokens: unlink both HF_TOKEN_PATH and HF_STORED_TOKENS_PATH
- Specific token_name -> _logout_from_token():
  1. Remove the token's section from stored_tokens INI
  2. If it was the active token, unlink HF_TOKEN_PATH
- **Always** calls unset_git_credential() to clean git credentials
- **Post-logout checks**: warns if still logged in via Colab secret or env variable (raises OSError for Colab/Env — user must manually clear those)

### 7. Token Switching (auth_switch)

auth_switch(token_name):
1. Looks up token by name in stored_tokens INI via _get_token_by_name()
2. Writes it to HF_TOKEN_PATH -> becomes active
3. Optionally sets git credential
4. Warns if HF_TOKEN env var overrides the switch

### 8. OIDC / Trusted Publishers (_oidc.py)

The zero-cost, no-secret auth for CI/CD:

**Flow**: CI provider mints an OIDC id token -> exchanges at /oauth/token using RFC 8693 token-exchange grant with id_token subject type

**Supported providers**: GitHub Actions only (native minting via ACTIONS_ID_TOKEN_REQUEST_URL env vars). Any OIDC-compatible provider can pass a pre-minted token via HF_OIDC_ID_TOKEN env var.

**In-process caching**: _OIDC_TOKEN_CACHE with expires_at check (300s refresh margin) — avoids re-exchanging on every get_token() call during long CI runs.

**Scope via HF_OIDC_RESOURCE env var**: repo path (e.g. username/model) for write tokens, or bare username for gated-repo read tokens.

### 9. Device Code OAuth (RFC 8628) — Pure Protocol

utils/_oauth_device.py contains two functions:

**request_device_code()**:
- POST with client_id (constant)
- Normalizes response: defaults interval to 5s, expires_in to 900s
- Returns typed dict DeviceCodeInfo

**poll_device_token()**:
- Polls token endpoint with grant_type=device_code + device_code + client_id
- Handles OAuth error states per RFC 8628:
  - authorization_pending -> call on_pending callback, keep polling
  - slow_down -> increase poll interval by 5s
  - expired_token -> raise with EXPIRED_TOKEN error code
  - access_denied -> raise with ACCESS_DENIED
  - Unknown errors -> raise with the raw error code
- Network resilience: HTTP 5xx, JSON parse failures, proxy errors silently retried — only the expires_in deadline bounds total wait
- Returns OAuthTokenResponse typed dict

**refresh_access_token()**:
- POST with grant_type=refresh_token + refresh_token + client_id
- Raises DeviceCodeError with invalid_grant on expiry/revocation
- Used by utils/_auth.py::_refresh_oauth_token_if_needed()

### 10. Security-Critical Design Details

| Feature | Implementation |
|---------|---------------|
| Secret file permissions | 0o600 file + 0o700 parent directory, best-effort on Windows |
| INI interpolation disabled | configparser(interpolation=None) — prevents % in tokens from being interpreted |
| OAuth refresh thread-safe | WeakFileLock for cross-process; _OAUTH_REFRESH_LOCK for in-process |
| OIDC cache | Per-process _OIDC_TOKEN_LOCK + _OIDC_TOKEN_CACHE globals |
| Colab secret | Per-process _GOOGLE_COLAB_SECRET_LOCK + globals |
| Rate-limited endpoint | whoami() heavily rate-limited; whoami(cache=True) caches per-token |
| Token validation | Server-side via /api/whoami-v2 — never trusts local token format |
| Git credential helper | Detects configured helpers before setting |

### 11. Constants Reference

| Constant | Purpose |
|----------|---------|
| HF_TOKEN_PATH | Active token file |
| HF_STORED_TOKENS_PATH | Multi-token INI store |
| ENDPOINT | Hub API base URL |
| DEVICE_CODE_OAUTH_CLIENT_ID | OAuth client ID for device code |
| HF_HUB_DOWNLOAD_TIMEOUT | HTTP timeout for OAuth requests |
| _OAUTH_REFRESH_MARGIN (86400s) | Refresh margin for OAuth tokens |
| _OAUTH_RECHECK_INTERVAL (300s) | Re-check interval on refresh failure |
| _OIDC_REFRESH_MARGIN (300s) | Refresh margin for OIDC tokens |

### Sources
- Source code: huggingface_hub/_login.py
- Source code: huggingface_hub/utils/_auth.py
- Source code: huggingface_hub/utils/_oauth_device.py
- Source code: huggingface_hub/_oidc.py
- Source code: huggingface_hub/constants.py
- Docs: Trusted Publishers
- RFC 8628 (Device Code OAuth), RFC 8693 (Token Exchange)


---

## Entry 146: huggingface_hub Authentication Pipeline — Source-Code Deep Dive (2026-07-25)
**Date:** 2026-07-25  
**Topic:**   

### Modules Involved

...

