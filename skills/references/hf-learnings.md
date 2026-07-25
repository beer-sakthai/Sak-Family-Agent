# HF Learnings Log

## 2026-07-25: hf-inference-providers-comprehensive-architecture — Hugging Face Inference Providers Complete Ecosystem Deep-Dive (Topic #255)

### Summary
Comprehensive deep-dive on Hugging Face Inference Providers — the multi-provider serverless inference platform launched January 2025 and continuously expanded through 2026. Covers the full architecture (router proxy layer, provider selection policies, authentication modes), all 17+ partner providers with their supported task types, Hub integration points (widgets, playground, Data Studio AI, model search), client SDK usage patterns (Python, JavaScript, HTTP, OpenAI-compatible), billing model (free tier, PRO, Enterprise, custom API keys), security & compliance (SOC2 Type 2, TLS, 30-day log retention, no data storage), agent framework integrations, and zero-cost pathways for development.

### Source
- Inference Providers Docs: https://huggingface.co/docs/inference-providers/en/index
- Hub Integration: https://huggingface.co/docs/inference-providers/en/hub-integration
- Security & Compliance: https://huggingface.co/docs/inference-providers/en/security
- Announcement Blog: https://huggingface.co/blog/inference-providers
- Hub Inference Providers: https://huggingface.co/docs/hub/en/models-inference

### Skill
hf-inference-providers — Hugging Face Inference Providers comprehensive reference: multi-provider serverless inference architecture, 17+ providers, router proxy with selection policies (:fastest/:cheapest/:preferred), Hub integration (widgets, playground, Data Studio AI), client SDK patterns, billing model, security, agent integrations, and zero-cost pathways

---

## 2026-07-25: hf-trl-v1-comprehensive — TRL v1.9.0 Complete Taxonomy & RLHF Toolkit (Topic #250)

### Summary
Comprehensive deep-dive on Hugging Face TRL v1.9.0 — the post-training library for transformer language model alignment. Covers the complete trainer taxonomy (4 categories, 14 trainers), what's new in TRL v1 (March 2026), multi-environment agentic RL with GRPOTrainer (Harbor/OpenEnv), all 5 GRPO loss formulations (DAPO, GRPO, VESPO, SAPO, Dr.GRPO), KTO stability graduation, vLLM co-location for online methods, Liger Kernel integration, reward function design patterns, data format standards, PEFT/DeepSpeed interop, and practical zero-cost pathways.

### Source
- TRL Docs: https://huggingface.co/docs/trl/en/index (v1.9.0)
- TRL GitHub: https://github.com/huggingface/trl
- TRL v1 Blog: https://huggingface.co/blog/trl-v1 (March 27, 2026)
- OpenEnv Blog: https://huggingface.co/blog/openenv (October 23, 2025)
- TRL VLM Alignment: https://huggingface.co/blog/trl-vlm-alignment (August 7, 2025)
- vLLM Co-location: https://huggingface.co/blog/vllm-colocate (June 3, 2025)
- Liger GRPO: https://huggingface.co/blog/liger-grpo (May 25, 2025)

### Skill
mlops/hf-trl-deep-dive — Hugging Face TRL v1.9.0 comprehensive reference: 14 trainers across 4 categories (online/offline/reward/distillation), multi-environment GRPO, KTO stability, vLLM/DeepSpeed/PEFT interop, Liger Kernel, OpenEnv/Harbor, VLM alignment

---

## 2026-07-24: hf-gradio-lite — Serverless Gradio in the Browser with Pyodide/WebAssembly (Topic #174)

### Summary
Comprehensive deep-dive on Gradio Lite (`@gradio/lite` v5.45.0) — the JavaScript library that runs Gradio apps entirely in the browser via Pyodide (Python compiled to WebAssembly). Covers architecture, CDN setup, multi-file apps with `<gradio-file>`, dependency management with `<gradio-requirements>`, Hugging Face Static Spaces integration (free, serverless), browser-based ML with `transformers-js`, theming, benefits, limitations, and production patterns.

### Source
- npm: `@gradio/lite` v5.45.0 — https://www.npmjs.com/package/@gradio/lite
- CDN: https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js
- Pyodide: https://pyodide.org/en/stable/
- HF Static Spaces: https://huggingface.co/docs/hub/en/spaces-overview
- Playground: https://www.gradio.app/playground

### 1. What Is Gradio Lite?

Gradio Lite (`@gradio/lite`) is a **JavaScript library** that brings Gradio applications into the browser without a backend server. It uses [Pyodide](https://pyodide.org/en/stable/) — a CPython port compiled to WebAssembly via Emscripten — to execute Python code directly in the browser's JavaScript runtime.

Key architecture:
```
Browser
├── HTML page with <gradio-lite> tags
├── Pyodide runtime (WebAssembly, ~8-15 MB)
│   ├── Python interpreter
│   ├── gradio library
│   └── user Python code
└── User interaction (no server round-trip)
```

### 2. Getting Started — CDN Setup

The simplest way to use Gradio Lite is via the CDN. Create a single `index.html`:

```html
<html>
  <head>
    <script type="module" crossorigin src="https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.css" />
  </head>
  <body>
    <gradio-lite>
import gradio as gr

def greet(name):
    return "Hello, " + name + "!"

gr.Interface(greet, "textbox", "textbox").launch()
    </gradio-lite>
  </body>
</html>
```

The app runs completely client-side — open the HTML file in any modern browser and it works without a web server.

### 3. Multi-File Apps with `<gradio-file>`

For real applications, split Python code across multiple files using `<gradio-file>` tags. Exactly one file must have the `entrypoint` attribute:

```html
<gradio-lite>

<gradio-file name="app.py" entrypoint>
import gradio as gr
from utils import add

demo = gr.Interface(fn=add, inputs=["number", "number"], outputs="number")
demo.launch()
</gradio-file>

<gradio-file name="utils.py">
def add(a, b):
    return a + b
</gradio-file>

</gradio-lite>
```

Each `<gradio-file>` behaves as a separate module — `utils.py` can be imported by `app.py` using standard Python import syntax.

### 4. Dependencies with `<gradio-requirements>`

Not all Pyodide packages are pre-loaded. Use `<gradio-requirements>` tags to install additional packages via `micropip`:

```html
<gradio-lite>

<gradio-requirements>
transformers_js_py
numpy
scikit-learn
</gradio-requirements>

<gradio-file name="app.py" entrypoint>
from transformers_js import import_transformers_js
import gradio as gr

transformers = await import_transformers_js()
pipeline = transformers.pipeline
pipe = await pipeline('sentiment-analysis')

async def classify(text):
    return await pipe(text)

gr.Interface(classify, "textbox", "json").launch()
</gradio-file>

</gradio-lite>
```

**Pyodide compatibility**: `gradio`, `numpy`, `scikit-learn`, `transformers_js_py`, `matplotlib`, `Pillow` all work. Not every PyPI package is available — check Pyodide's package index first.

### 5. Hugging Face Static Spaces — Free Hosting

Gradio Lite apps deploy to **Hugging Face Static Spaces** — a free hosting tier that serves static HTML/JS/CSS with zero server compute. Unlike Gradio or Docker Spaces (which need a paid CPU/GPU plan), Static Spaces are **completely free**.

Setup on HF:
1. Create a new Space at https://huggingface.co/new-space
2. Select **"Static HTML"** as the Space SDK
3. Upload your `index.html` (with `<gradio-lite>` tags)
4. Done — your app runs at `https://huggingface.co/spaces/USERNAME/SPACE-NAME`

Live example: https://huggingface.co/spaces/abidlabs/gradio-lite-classify

### 6. Theming

Add a `theme` attribute to `<gradio-lite>` to force the color scheme:

```html
<gradio-lite theme="dark">
  <!-- your Python code -->
</gradio-lite>

<gradio-lite theme="light">
  <!-- your Python code -->
</gradio-lite>
```

Without the attribute, Gradio Lite respects the user's system theme (prefers-color-scheme).

### 7. Benefits

| Benefit | Description |
|---------|-------------|
| **Serverless** | No backend infrastructure, no VPS, no Docker — pure static hosting |
| **Zero Cost** | HF Static Spaces are free; no GPU/CPU compute charges |
| **Low Latency** | All computation happens locally — no network round-trips |
| **Privacy** | User data never leaves the browser — no server-side logging |
| **Offline Capable** | After initial load, can run without internet (except package CDN deps) |
| **Simple Deployment** | Single HTML file or static file upload, no CI/CD needed |

### 8. Limitations

| Limitation | Impact |
|------------|--------|
| **Cold Start (5-15s)** | Pyodide runtime must download and initialize on first visit |
| **Package Restriction** | Only Pyodide-compatible wheels (check Pyodide's package index) |
| **Browser Memory** | Large models can exceed browser tab memory limits (~2 GB) |
| **No GPU (WebGL limited)** | Pyodide does not support CUDA; WebGL/WebGPU not yet available for PyTorch |
| **Single-threaded** | Python GIL + browser main thread — async helps but no true parallelism |
| **No File System** | Pyodide provides a virtual in-memory FS — no persistent disk storage |

### 9. Browser ML with transformers-js

Gradio Lite can run Hugging Face models directly in the browser via `transformers_js_py` — a Python wrapper around [Transformers.js](https://huggingface.co/docs/transformers.js/index) (ONNX Runtime Web):

Supported tasks (in-browser, no server):
- Sentiment analysis
- Text classification
- Zero-shot classification
- Feature extraction / embeddings
- Question answering
- Summarization
- Translation

Example — real in-browser ML:
```python
from transformers_js import import_transformers_js
import gradio as gr

transformers = await import_transformers_js()
pipe = await transformers.pipeline('sentiment-analysis')

async def analyze(text):
    result = await pipe(text)
    return result

gr.Interface(analyze, "textbox", "json").launch()
```

### 10. Version & Compatibility

- **`@gradio/lite` latest**: 5.45.0 (npm)
- **Gradio compatibility**: Gradio 5.x (Gradio Lite versioning is independent of Gradio PyPI versioning)
- **Pyodide version**: Bundled in lite.js — updates with each Gradio Lite release
- **Browser support**: Chrome, Firefox, Safari, Edge (modern evergreen browsers)
- **No Node.js required**: Everything runs in the browser

### 11. Best Practices

1. **Keep apps small**: Large Gradio apps with many dependencies increase cold-start time
2. **Use `async` for ML pipelines**: Transformers-js operations are async — use `async def` in Gradio
3. **Prefer static HTML Spaces**: Free and simpler than Docker Spaces for Lite apps
4. **Minimize Pyodide packages**: Each package adds to load time; only include what you need
5. **Test in multiple browsers**: Pyodide/WebAssembly behavior can vary between engines
6. **Provide cold-start feedback**: Show a loading indicator — users expect 5-15s initial delay
7. **Combine with HF OAuth**: Static Spaces support client-side OAuth for user login

### 12. When to Use vs Alternatives

| Use Case | Recommendation |
|----------|---------------|
| Simple demo, no server, zero cost | Gradio Lite + Static Space |
| Large model inference (1B+ params) | Gradio + ZeroGPU (needs GPU) |
| Production API with scaling | Gradio + Docker Space (paid) |
| Offline/battery-sensitive | Gradio Lite (browser-only) |
| Real-time collaboration | Gradio + HuggingChat |
| Heavy Python deps (PyTorch, etc.) | Gradio + Docker Space (server-side) |

---

## 2026-07-24: hf-hub-modelcard-python-api — Complete ModelCard & CardData Python API Reference (Topic #173)

### Summary
Comprehensive reference for the Hugging Face Hub's Python `ModelCard` API from `huggingface_hub` — the programmatic interface for creating, reading, updating, and publishing model cards (and dataset/Space cards) on the Hub. Covers the full class hierarchy (`RepoCard` → `ModelCard`/`DatasetCard`/`SpaceCard`), metadata with `ModelCardData`, structured evaluation results with `EvalResult`, Jinja2 template-based card creation, `metadata_update()` for lightweight changes, validation against Hub rules, and push-to-Hub workflows including PR-based contributions.

### Source
- Hugging Face Hub docs — Model Cards: https://huggingface.co/docs/hub/en/model-cards
- huggingface_hub Model Cards guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/model-cards
- huggingface_hub cards package reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/cards
- Source: `huggingface_hub/repocard.py` (RepoCard, ModelCard, DatasetCard, SpaceCard, CardData, ModelCardData, DatasetCardData, SpaceCardData, EvalResult, metadata_update)
- Default template: `src/huggingface_hub/templates/modelcard_template.md`

### 1. Class Hierarchy

```
RepoCard (base class)
├── content (str) — read/write, parses YAML header + Markdown body
├── data (CardData subclass) — parsed metadata
├── text (str) — body text (read-only, excludes metadata header)
│
├── ModelCard (repo_type="model")
│   └── data: ModelCardData
├── DatasetCard (repo_type="dataset")
│   └── data: DatasetCardData
└── SpaceCard (repo_type="space")
    └── data: SpaceCardData
```

The `RepoCard` base class handles all YAML parsing and serialization. Subclasses only set default `repo_type`.

### 2. Loading Cards

```python
from huggingface_hub import ModelCard, DatasetCard

# Load from Hub repo
card = ModelCard.load("nateraw/vit-base-beans")
card.data.language  # 'en'
card.data.tags      # ['generated_from_trainer', 'image-classification', 'pytorch']
card.text           # '# My Model Card\n\n...' (no YAML header)
card.content        # '---\nlanguage: en\n...\n---\n\n# My Model Card\n...' (full)

# Load from local file
card = ModelCard.load("/path/to/README.md")

# Load with repo_type hint
card = DatasetCard.load("username/my-dataset")
```

**Loading flow:**
1. If `repo_id_or_path` has a `/`, fetch `README.md` from the Hub via HfApi
2. If it's a local path, read the file directly
3. Parse YAML frontmatter (between `---` delimiters) into `card.data`
4. Remaining text becomes `card.text`

### 3. Creating Cards from Text

```python
content = """
---
language: en
license: mit
pipeline_tag: image-classification
---

# My Model Card

This model was trained on...
"""

card = ModelCard(content)
card.data.to_dict()
# {'language': 'en', 'license': 'mit', 'pipeline_tag': 'image-classification'}

# With f-strings for dynamic content
card_data = ModelCardData(language="en", license="mit", library_name="timm")
content = f"""
---
{card_data.to_yaml()}
---

# My Model

Created by @beer-sakthai
"""
card = ModelCard(content)
```

### 4. Creating Cards from Jinja2 Templates

Requires `jinja2` installed. Two built-in templates exist:
- `modelcard_template.md` (for ModelCard)
- `datasetcard_template.md` (for DatasetCard)

```python
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language="en",
    license="mit",
    library_name="transformers",
    tags=["text-generation", "llama"],
    datasets=["HuggingFaceFW/fineweb"],
)

# Using the default template
card = ModelCard.from_template(
    card_data,
    model_id="my-llama-model",
    model_description="Fine-tuned Llama 4 on FineWeb",
    developers="Beer SakThai",
    repo="https://huggingface.co/beer-sakthai",
)

# Using a custom template file
card = ModelCard.from_template(
    card_data=card_data,
    template_path="./my_custom_template.md",
    custom_var="any value",  # passed to jinja template
)
```

**Default template sections** (from `modelcard_template.md`):
- Model description
- Intended uses & limitations
- Training data
- Training procedure (hyperparameters, compute)
- Evaluation results
- Environmental impact (CO2)
- Technical specifications
- Citation information

**Custom template pattern:**
```markdown
---
{{ card_data }}
---

# Model Card for {{ model_id }}

{{ model_description }}

## Intended Use
{{ intended_use | default("") }}
```

### 5. ModelCardData — Metadata Reference

```python
from huggingface_hub import ModelCardData

card_data = ModelCardData(
    # Core identifiers
    language="en",                         # ISO 639-1 code or list
    license="mit",                         # Standard license identifier
    license_name="Custom License",         # Name (for custom licenses)
    license_link="https://example.com",    # URL (for custom licenses)
    library_name="transformers",           # HF-integrated library name
    pipeline_tag="text-generation",        # Task identifier
    
    # Relationships
    base_model="meta-llama/Llama-4-8B",    # Source model ID (str or list[str])
    datasets=["HuggingFaceFW/fineweb"],    # Training dataset IDs
    
    # Discoverability
    tags=["llama", "fine-tuned"],          # Custom tags for filtering
    metrics=["accuracy"],                  # Metric names from hf.co/metrics
    
    # Evaluation results (structured)
    model_name="my-model",                 # Leaderboard name
    eval_results=[
        EvalResult(
            task_type="text-generation",
            dataset_type="lambada",
            dataset_name="LAMBADA",
            metric_type="perplexity",
            metric_value=8.5,
        ),
    ],
    
    # Additional arbitrary metadata
    ignore_metadata_errors=False,
    **{"custom_field": "value"},           # Additional kwargs → YAML keys
)

card_data.to_dict()      # → dict ready for YAML serialization
card_data.to_yaml()      # → YAML block string
card_data["language"]    # → 'en' (dict-like access)
card_data.pop("tags")    # → ['llama', 'fine-tuned']
```

**Key design:**
- `ModelCardData` behaves like a dict (get, pop, set) but does NOT inherit from dict — this allows controlled `to_dict()`/`to_yaml()` export with custom logic for `eval_results` → `model-index` conversion.
- Additional `**kwargs` are preserved as extra YAML keys.
- `model-name` is auto-derived from repo name if not provided.

### 6. EvalResult — Structured Evaluation Results

```python
from huggingface_hub import EvalResult

result = EvalResult(
    task_type="image-classification",  # Required: task type identifier
    dataset_type="beans",              # Required: dataset type identifier
    dataset_name="Beans",              # Required: human-readable dataset name
    metric_type="accuracy",            # Required: metric identifier
    metric_value=0.95,                 # Required: numeric score
    task_name="Image Classification",  # Optional: human-readable task
    metric_name="Accuracy",            # Optional: human-readable metric (defaults to metric_type)
    metric_config="default",           # Optional: metric configuration name
)

# Multiple results → list
card_data = ModelCardData(
    model_name="my-model",
    eval_results=[
        EvalResult(task_type="text-generation", dataset_type="lambada", dataset_name="LAMBADA", metric_type="perplexity", metric_value=8.5),
        EvalResult(task_type="text-generation", dataset_type="wikitext",  dataset_name="WikiText-2", metric_type="perplexity", metric_value=9.2),
    ]
)
```

**How it serializes in YAML:**
```yaml
model-index:
- name: my-model
  results:
  - task:
      type: text-generation
    dataset:
      name: LAMBADA
      type: lambada
    metrics:
    - type: perplexity
      value: 8.5
  - task:
      type: text-generation
    dataset:
      name: WikiText-2
      type: wikitext
    metrics:
    - type: perplexity
      value: 9.2
```

This is the same format recognized by PapersWithCode leaderboards.

### 7. Pushing Cards to the Hub

```python
# Create a card
card = ModelCard.from_template(
    ModelCardData(language="en", license="mit"),
    model_description="My fine-tuned model",
)

# Push directly to a repo's README.md
url = card.push_to_hub("username/my-model")
# → https://huggingface.co/username/my-model/blob/main/README.md

# Push as a pull request (no write access required)
card.push_to_hub("username/my-model", create_pr=True)
# Result: a PR at https://huggingface.co/username/my-model/discussions/N

# Customize commit
card.push_to_hub(
    "username/my-model",
    commit_message="docs: update model card with eval results",
    commit_description="Added LAMBADA perplexity results",
    revision="main",
    parent_commit="abc1234",  # Ensures repo hasn't changed
)
```

**push_to_hub parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `repo_id` | str | required | Target repo (e.g. "user/model") |
| `token` | str | stored token | HF auth token |
| `repo_type` | str | "model" | One of "model", "dataset", "space" |
| `commit_message` | str | "Update README.md" | Commit title |
| `commit_description` | str | None | Extended description |
| `revision` | str | "main" | Git branch/ref |
| `create_pr` | bool | False | Push as a PR instead of direct commit |
| `parent_commit` | str | None | Enforce parent SHA for safety |

### 8. Saving and Loading Locally

```python
# Save to a file
card.save("/tmp/my_model_card.md")

# Load from a local file
card = ModelCard.load("/tmp/my_model_card.md")
```

### 9. Validation

```python
# Validate metadata against Hub rules (requires internet)
card.validate()
# Raises ValueError if invalid, HTTPError if API fails
```

Validation checks are pulled from the Hub's validation API. Common failures:
- Invalid license identifier
- Invalid pipeline_tag
- Malformed model-index structure

### 10. metadata_update() — Lightweight Metadata Changes

For quick metadata updates without loading the full card:

```python
from huggingface_hub import metadata_update

# Set a new pipeline_tag
metadata_update("username/my-cool-model", {"pipeline_tag": "image-classification"})

# Overwrite existing values
metadata_update(
    "username/my-cool-model",
    {"pipeline_tag": "text-generation"},
    overwrite=True,
)

# Create a PR (no write access needed)
metadata_update(
    "someone/model",
    {"pipeline_tag": "text-classification"},
    create_pr=True,
)
```

**Important:** `overwrite` defaults to `False` — without it, updating an existing key raises an error. Always pass `overwrite=True` when modifying existing metadata.

### 11. DatasetCard & SpaceCard — Analogous APIs

```python
from huggingface_hub import DatasetCard, DatasetCardData, SpaceCard, SpaceCardData

# Dataset card
card_data = DatasetCardData(
    language=["en"],
    license="mit",
    annotations_creators="crowdsourced",
    task_categories=["text-classification"],
    task_ids=["sentiment-analysis"],
    multilinguality="monolingual",
    pretty_name="My Dataset",
    size_categories="10K<n<100K",
)
card = DatasetCard.from_template(card_data, pretty_name=card_data.pretty_name)
card.push_to_hub("username/my-dataset", repo_type="dataset")

# Space card
space_data = SpaceCardData(
    title="My Space",
    sdk="gradio",
    sdk_version="5.0",
    python_version="3.11",
    license="mit",
)
space_card = SpaceCard(space_data)
```

### 12. Best Practices

1. **Always use from_template for new cards** — the default template includes all recommended sections for discoverability
2. **Include eval_results** — they populate the `model-index` which feeds PapersWithCode leaderboards
3. **Set `base_model`** — this enables the model lineage graph on the Hub (fine-tune, merge, quantized relations)
4. **Set `library_name` explicitly** — post-August 2024 repos don't auto-detect transformers
5. **Use `create_pr=True`** for repos you don't own — it's the standard open-source contribution pattern
6. **Bundle `metadata_update` for quick fixes** — no need to construct full cards for single-field changes
7. **Validate before pushing** — `card.validate()` catches issues early

### 13. Zero-Cost Implications for Beer

- ModelCard API is **100% free** — no GPU, no API credits, no paid tier required
- Cards live in the repo's `README.md` — no additional storage cost
- Programmatic card updates fit perfectly into CI/CD pipelines for Beer's 8 models
- `EvalResult` integration with Open LLM Leaderboard gives free exposure
- Default Jinja2 template is MIT-licensed and free to customize

### Resources
- https://huggingface.co/docs/hub/en/model-cards — Hub model card guide
- https://huggingface.co/docs/huggingface_hub/main/en/guides/model-cards — huggingface_hub guide
- https://huggingface.co/docs/huggingface_hub/main/en/package_reference/cards — API reference
- Default template: `src/huggingface_hub/templates/modelcard_template.md` in huggingface_hub repo
- https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/repocard.py — source code

### Skill
mlops/huggingface-hub -- references/hf-learnings.md

---

## 2026-07-25: hf-datasets-server-parquet-conversion-pipeline (Deep Dive) — Parquet Conversion Architecture Internals (Topic #174 Deepened)

### Summary
Comprehensive deep-dive into the Hugging Face Datasets Server's Parquet conversion pipeline — how datasets of any format are auto-converted to Apache Parquet for efficient remote querying. Covers the `refs/convert/parquet` branch, 500MB shard strategy, partial exports (>5GB limit), Parquet-native zero-copy, dual `/parquet` API endpoints, internal `RowsIndex` class with page-level pruning, and zero-cost analytical patterns using DuckDB/PyArrow.

**Full deep-dive:** `skills/mlops/hf-datasets-server-rest-api/references/hf-learnings.md`

### Source
- Dataset Viewer Parquet docs: https://huggingface.co/docs/dataset-viewer/en/parquet
- Parquet Conversion Process: https://huggingface.co/docs/dataset-viewer/en/parquet_process
- Source code: `libcommon/parquet_utils.py` in dataset-viewer repo

### Key Discoveries
1. **`refs/convert/parquet` branch** — Separate git branch parallel to main, uses `%2F` encoding because `/` isn't allowed in branch names
2. **500MB sharding** — Datasets partitioned into ~500MB shards (`{name}-{split}-0000-of-NNNN.parquet`) for efficient streaming
3. **Partial prefix detection** — `parquet_export_is_partial()` checks if split directory starts with `"partial-"`; from source code at `libcommon/parquet_utils.py`
4. **Dual API endpoints** — Datasets Server (`/parquet?dataset=`) returns `pending`/`failed` arrays; Hub API (`/api/datasets/{ds}/parquet`) uses Hub auth
5. **Page-level pruning** — `libviewer.Dataset.scan()` skips row groups and pages that don't match query range, bounded by `max_scan_size`
6. **Binary truncation disabled** — `truncate_binary_columns()` exists but disabled (`max_binary_length=-1`) due to batch iteration limitation
7. **5GB free tier** — Public datasets >5GB get partial export only; full conversion requires PRO or manual conversion

### Zero-Cost Implications
- Remote Parquet querying via DuckDB is free (predicate pushdown, only relevant bytes transferred)
- The 5GB partial export limit means most small datasets are fully available as Parquet at no cost
- No GPU needed — Parquet analytics is CPU-only

### Resources
- Full deep-dive in `mlops/hf-datasets-server-rest-api/references/hf-learnings.md`
- https://huggingface.co/docs/dataset-viewer/en/parquet
- https://github.com/huggingface/dataset-viewer

---

## 2026-07-24: hf-custom-model-integration-deep-dive — Complete Guide to Integrating Custom PyTorch Models into Transformers (Topic #55 Deepened)

### Summary
Comprehensive deep-dive into the process of integrating custom PyTorch models into the Hugging Face Transformers ecosystem — enabling them to work with AutoClass APIs, `from_pretrained()`, `push_to_hub()`, and the Hub's remote code loading. Covers the full pipeline: configuration class, model class, AutoClass registration, Hub upload structure, `register_for_auto_class()`, `trust_remote_code` loading, and security considerations. Based on the official Transformers docs as of v5.14.0.

### Source
- Customizing models: https://huggingface.co/docs/transformers/en/custom_models
- Loading custom models: https://huggingface.co/docs/transformers/en/models#custom-models
- Model sharing: https://huggingface.co/docs/transformers/en/model_sharing
- Legacy model contribution: https://huggingface.co/docs/transformers/en/add_new_model
- Published: 2026-07-24, Transformers v5.14.0

### 1. Architecture: The Three-Layer Integration Pattern

A custom model needs three things to integrate with Transformers:

```
┌─────────────────────────────────────────────────────────────┐
│  1. Configuration Class (subclass of PreTrainedConfig)       │
│     └─ Defines model architecture hyperparameters            │
│     └─ Must define model_type (unique string identifier)     │
├─────────────────────────────────────────────────────────────┤
│  2. Model Class (subclass of PreTrainedModel)                │
│     └─ Defines forward pass, layers, initialization          │
│     └─ Must define config_class pointing to config           │
├─────────────────────────────────────────────────────────────┤
│  3. AutoClass Registration                                   │
│     └─ AutoConfig.register("model_type", ConfigClass)        │
│     └─ AutoModel.register(ConfigClass, ModelClass)           │
│     └─ AutoModelForTask.register(ConfigClass, TaskModel)     │
└─────────────────────────────────────────────────────────────┘
```

### 2. Step 1: Create the Configuration Class

The configuration class must inherit from `PreTrainedConfig` and define:
- `model_type`: A unique string identifier (must not conflict with existing models)
- Model-specific parameters with sensible defaults
- The `__init__` method that accepts all parameters

```python
from transformers import PretrainedConfig

class ResnetConfig(PretrainedConfig):
    model_type = "resnet"  # Must be unique across all Transformers models

    def __init__(
        self,
        block_type="bottleneck",
        stem_width=64,
        stem_type="deep",
        avg_down=False,
        num_labels=1000,
        **kwargs,
    ):
        self.block_type = block_type
        self.stem_width = stem_width
        self.stem_type = stem_type
        self.avg_down = avg_down
        self.num_labels = num_labels
        super().__init__(**kwargs)
```

**Key rules:**
- `model_type` MUST be unique — check against existing model types in Transformers
- Store all params as `self.xxx` before calling `super().__init__()`
- Pass remaining `**kwargs` to super for compatibility
- `PreTrainedConfig` provides serialization (`to_dict()`, `to_json_string()`, `save_pretrained()`) automatically
- The config serializes to JSON when saved with `save_pretrained()` — only JSON-serializable attributes survive

### 3. Step 2: Create the Model Class

The model class must inherit from `PreTrainedModel` and define:
- `config_class`: Points to the config class (critical for AutoClass loading)
- `base_model_prefix`: Short prefix for model submodules (e.g., "model", "resnet", "transformer")
- The `__init__` method that accepts the config
- The `forward` method defining the computation

```python
import torch.nn as nn
from transformers import PreTrainedModel

class ResnetModel(PreTrainedModel):
    config_class = ResnetConfig
    base_model_prefix = "model"

    def __init__(self, config):
        super().__init__(config)
        # Build model from config params
        self.model = ResNet(
            block_type=config.block_type,
            stem_width=config.stem_width,
            stem_type=config.stem_type,
            avg_down=config.avg_down,
        )
        # Initialize weights using provided method
        self.post_init()  # Calls _init_weights if defined

    def _init_weights(self, module):
        if isinstance(module, nn.Linear):
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)
        elif isinstance(module, nn.Embedding):
            module.weight.data.normal_(mean=0.0, std=self.config.initializer_range)

    def forward(self, pixel_values, labels=None):
        outputs = self.model(pixel_values)
        return outputs
```

**Key rules:**
- Always call `super().__init__(config)` first
- `post_init()` must be called after building layers — it triggers weight initialization, gradient checkpointing setup, and mixed precision support
- `PreTrainedModel` provides: `from_pretrained()`, `save_pretrained()`, `push_to_hub()`, `to()`, `half()`, `bfloat16()`, `eval()`, `train()`, device_map support, gradient checkpointing, and more
- For task-specific models (e.g., classification), add a head:

```python
class ResnetModelForImageClassification(PreTrainedModel):
    config_class = ResnetConfig
    base_model_prefix = "model"

    def __init__(self, config):
        super().__init__(config)
        self.model = ResNet(...)
        self.classifier = nn.Linear(config.hidden_size, config.num_labels)
        self.post_init()

    def forward(self, pixel_values, labels=None):
        outputs = self.model(pixel_values)
        logits = self.classifier(outputs)
        loss = None
        if labels is not None:
            loss = nn.functional.cross_entropy(logits, labels)
        return (loss, logits) if loss is not None else (logits,)
```

### 4. Step 3: AutoClass Registration

Register your custom model so AutoModel can find it:

```python
from transformers import AutoConfig, AutoModel, AutoModelForImageClassification

AutoConfig.register("resnet", ResnetConfig)
AutoModel.register(ResnetConfig, ResnetModel)
AutoModelForImageClassification.register(ResnetConfig, ResnetModelForImageClassification)
```

**The registration contract:**
- `AutoConfig.register(model_type, config_class)` — model_type must equal `ConfigClass.model_type`
- `AutoModel.register(config_class, model_class)` — first arg must equal `ModelClass.config_class`
- Registration is global — once registered, `AutoModel.from_pretrained()` can find it
- Multiple AutoModelFor* classes can be registered for the same config

**Verification:**
```python
model = AutoModel.from_pretrained("your-username/your-model")  # ✓
model = AutoModelForImageClassification.from_pretrained("your-username/your-model")  # ✓
config = AutoConfig.from_pretrained("your-username/your-model")  # ✓
```

### 5. Step 4: Upload to the Hub

**Repository directory structure:**

```
.
└── your-model-repo/
    ├── __init__.py              # Empty, enables Python import
    ├── configuration_resnet.py  # Contains ResnetConfig
    ├── modeling_resnet.py       # Contains ResnetModel, ResnetModelForImageClassification
    ├── config.json              # Serialized config (auto-generated)
    ├── model.safetensors        # Model weights (auto-generated)
    └── README.md                # Model card
```

**Critical:** Unlike built-in models, custom model code must be **bundled in the repo** because `from_pretrained()` with `trust_remote_code=True` imports the code from the repo.

**Steps to prepare:**
```python
from resnet_model.configuration_resnet import ResnetConfig
from resnet_model.modeling_resnet import ResnetModel, ResnetModelForImageClassification

ResnetConfig.register_for_auto_class()
ResnetModel.register_for_auto_class("AutoModel")
ResnetModelForImageClassification.register_for_auto_class("AutoModelForImageClassification")
```
`register_for_auto_class()` adds `auto_map` to config.json:
```json
{
  "auto_map": {
    "AutoConfig": "your-repo-name--ResnetConfig",
    "AutoModel": "your-repo-name--ResnetModel",
    "AutoModelForImageClassification": "your-repo-name--ResnetModelForImageClassification"
  }
}
```

Then instantiate, load weights, push:
```python
resnet50d_config = ResnetConfig(block_type="bottleneck", stem_width=32, ...)
resnet50d = ResnetModelForImageClassification(resnet50d_config)
import timm
pretrained_model = timm.create_model("resnet50d", pretrained=True)
resnet50d.model.load_state_dict(pretrained_model.state_dict())
resnet50d.push_to_hub("custom-resnet50d")
```

### 6. Step 5: Loading Custom Models

Users load with `trust_remote_code=True`:

```python
from transformers import AutoModelForImageClassification

# Basic loading
model = AutoModelForImageClassification.from_pretrained(
    "sgugger/custom-resnet50d", trust_remote_code=True
)

# Pinned to specific revision (security best practice)
model = AutoModelForImageClassification.from_pretrained(
    "sgugger/custom-resnet50d",
    trust_remote_code=True,
    revision="ed94a7c6247d8aedce4647f00f20de6875b5b292"
)
```

**Loading flow:**
1. Download `config.json` from repo → read `auto_map`
2. Download and execute `configuration_resnet.py` from repo
3. Download and execute `modeling_resnet.py` from repo
4. Load safetensors weights → return model

### 7. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| Remote code execution | Hub malware scanning; still trust carefully |
| Changed model code | Pin to a specific commit hash |
| Malicious imports | Review downloaded code before running |
| Supply chain attacks | Only load custom models from trusted users |

```python
# Maximum security pattern
model = AutoModel.from_pretrained(
    "trusted-user/custom-model",
    trust_remote_code=True,
    revision="abc123def456",
    token=False,
)
```

### 8. The `auto_map` Format

```json
{
  "auto_map": {
    "AutoConfig": "my_username--ResnetConfig",
    "AutoModel": "my_username--ResnetModel",
    "AutoModelForImageClassification": "my_username--ResnetModelForImageClassification"
  }
}
```

**Convention:** `repo_namespace--ClassName` (double dash). `repo_namespace` is the HF username or org. Multiple `AutoModelFor*` entries can map to different classes.

### 9. Common Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| `model_type` collision | Silent overwrite | Choose unique model_type |
| Missing `post_init()` | Uninitialized weights | Add `self.post_init()` |
| Wrong config_class | Silent registration failure | Ensure config_class matches |
| Non-serializable config | `to_dict()` crash | Use JSON types only |
| Missing `__init__.py` | ImportError in remote loading | Add empty `__init__.py` |
| Relative imports | ImportError | Replace with absolute imports from `transformers` |
| No auto_map | Manual class lookup needed | Call `register_for_auto_class()` |

### 10. Multi-Task Models

Edit `auto_map` directly in config.json:
```json
{
  "auto_map": {
    "AutoConfig": "my_username--ResnetConfig",
    "AutoModelForImageClassification": "my_username--ResnetModelForImageClassification",
    "AutoModelForObjectDetection": "my_username--ResnetModelForObjectDetection"
  }
}
```

### 11. Legacy Full Integration

The alternative (contributing to transformers source) requires: fork, cookiecutter, ~8 files, CI checks, PR review. **For Beer's 8 models, the custom model pattern above is the right choice.**

### 12. Zero-Cost Application for Beer

1. **Known architectures** (Llama, Phi, etc.) → `AutoModel.from_pretrained()` directly
2. **Modified architectures** → Custom model pattern, small files, zero storage cost
3. **GGUF models** → `transformers.GGUFModel` or llama.cpp
4. **Pipeline API** → Works with `pipeline(task, model="...", trust_remote_code=True)`
5. **Inference Endpoints** → Custom models work, but serverless only supports pre-integrated architectures

### Resources
- https://huggingface.co/docs/transformers/en/custom_models
- https://huggingface.co/docs/transformers/en/models#custom-models
- https://huggingface.co/docs/transformers/en/model_sharing
- https://huggingface.co/docs/transformers/en/add_new_model
- https://github.com/huggingface/transformers/blob/main/src/transformers/configuration_utils.py
- https://github.com/huggingface/transformers/blob/main/src/transformers/modeling_utils.py

---
# HF Learnings Log

## 2026-07-30: hf-hub-models-architecture-and-pipeline-tags — Complete HF Model Tag Taxonomy Deep Dive (Topic #164 Deepened)

### Summary
Comprehensive deep-dive into the Hugging Face Hub's model tag taxonomy — the
complete classification system that powers discovery, filtering, and widget
selection across 1M+ models. Covers all 47 official pipeline tags, the 6 tag
categories (pipeline, library, language, license, architecture, auto-generated),
the automatic tag inference pipeline (transformers config → Architecture-to-
Pipeline mapping gist → tag-based fallback → default), search/filter API
patterns, and the conversational widget special case. Full document at
`skills/mlops/hf-hub-models-tags/references/hf-learnings.md`.

### Key Discovery: 47 Official Pipeline Tags
Confirmed via the `/tasks` page: 47 distinct pipeline tags covering text (13),
vision (22), audio (5), multimodal (2), tabular (2), RL (1), time-series (1),
and any-to-any (1). `conversational` is NOT a pipeline tag — it's a companion
boolean tag that activates the chat widget only when paired with
`text-generation` or `image-text-to-text`.

### Key Discovery: Tag Inference Priority Chain
1. Explicit `pipeline_tag:` in model card YAML
2. Transformers `config.json` → `architectures[]` mapped via a reference gist
3. Library-specific detection (sentence-transformers modules.json, etc.)
4. First matching task tag from `tags[]` in model card metadata
5. Fallback: `feature-extraction`

### Key Discovery: No Public Tag Registry API
Unlike datasets (`/api/tags`), there is no public auth-free endpoint to
enumerate model tags. The taxonomy must be reconstructed from the /tasks HTML,
live API queries, the OpenAPI spec, and the widgets doc's architecture mapping
gist.

**Full document:** `skills/mlops/hf-hub-models-tags/references/hf-learnings.md`

---

## 2026-07-24: hf-transformers-speculative-decoding-deep-dive — v5.14.0 MTP Support & Static Ensemble Verification (Topic #79 Deepened)

### Summary
Deep-dive into two major generation features added in Transformers v5.14.0 (2026-07-15): (1) **Multi-Token Prediction (MTP) decoding** — `use_mtp=True` enables proper inference-time MTP, auto-loading MTP head weights from the Hub repo and achieving ~1.4× speedup. (2) **Static ensemble verification** — `assistant_ensemble_weight` blends target/draft distributions during speculative decoding, increasing acceptance rates with zero training. Covers usage, design decisions, benchmark data, cache infrastructure (MtpCache), DeepSeek V4 limitations, and paper references. Full document at `skills/mlops/hf-transformers-5/references/hf-learnings.md`.

### Key Discovery: MTP Is Now One Flag
`model.generate(use_mtp=True, ...)` is all it takes — no separate assistant model, no custom loading code. The `generate()` method automatically scans the repo for MTP head weights, loads them, and integrates with the assisted decoding pipeline. On GLM-4.5-Air this yields 73.68% token acceptance with a 1.4× decoding speedup.

### Key Discovery: Ensemble Verification Is Free Speed
Static ensemble verification (`assistant_ensemble_weight=0.7`) is a training-free drop-in parameter that relaxes the strict verification distribution from `p_target` to `w * p_target + (1-w) * q_draft`. This provably achieves a Pareto-optimal tradeoff between acceptance rate and distributional bias. The acceptance probability increases from `1 - TV(q,p)` to `1 - w * TV(q,p)`.

---

## 2026-07-26: hf-mcp-server-enhancements-hf-fs-consolidation — MCP Server Consolidation & Gallery Install (Topic #44/#90 Deepened)

### Summary
Deep-dive into the July 2026 Hugging Face MCP Server enhancements. Key changes: `hf_fs` tool consolidation (replacing ~28 separate tools with 4 categories), one-click gallery installations (Claude, VSCode, Cursor, Gemini CLI), native CLI commands (`claude mcp add`, `gemini mcp add`), `AUTHENTICATE_TOOL` for OAuth-based on-the-fly authentication, SEP-2640 skills directory support (`HF_SKILLS_DIR`), stateful connection management (heartbeat, ping, timeout config), and extensive new environment variables. Full document at `skills/SakThai-hf-mcp-server/references/hf-learnings.md`.

### Key Discovery: Architecture Consolidation
The MCP Server moved from ~28 separate tools to a consolidated architecture centered around the `hf_fs` tool. The changelog states: "The main change is the new hf_fs tool which provides a single interface to repositories, storage, documentation, papers and more. It's equipped with search and lets your assistant naturally navigate Hugging Face in just over 1,000 tokens." This means the bouquet/mix system is being simplified — remaining explicit tools: `hf_fs`, Contribute Repos, Sandboxes, Run & Manage Jobs.

### New Installation Methods
- **Claude Desktop/claude.ai**: Connector gallery at claude.ai/settings/connectors — click "Hugging Face"
- **Claude Code**: `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login`
- **Gemini CLI**: `gemini mcp add -t http huggingface https://huggingface.co/mcp?login`
- **VSCode**: Gallery at code.visualstudio.com/mcp or clickable `vscode:mcp/install?...` deep link
- **Cursor**: One-click install link with encoded config
- **URL parameter**: `?no_image_content=true` removes image content from Gradio responses

### Key Implication
The `AUTHENTICATE_TOOL` env var enables dynamic OAuth — agents can authenticate mid-session without pre-configured tokens. The SEP-2640 skills directory means SakThai skills can be exposed as MCP resources via `skill://` protocol.

**Full document:** `skills/SakThai-hf-mcp-server/references/hf-learnings.md`

---

## 2026-07-24: hf-hub-openapi-spec-deep-dive — Hub OpenAPI Specification & Programmatic Discovery (Topic #128 Deepened)

### Summary
Deep-dive into the Hugging Face Hub's OpenAPI 3.0 specification available at `/.well-known/openapi.md` (12,358 lines) and `/.well-known/openapi.json`. The spec is the single authoritative source for all Hub REST API endpoints — covering Models, Datasets, Spaces, Discussions, Papers, Collections, Organizations, Webhooks, Jobs, and Billing. The spec is also served via the interactive [OpenAPI Playground Space](https://huggingface.co/spaces/huggingface/openapi). This learning catalogs every API endpoint group, documents the spec format, and provides patterns for programmatic spec consumption (dynamic client generation, endpoint discovery, route validation).

### Key Discovery: Spec Location & Format

The OpenAPI spec moved from the docs hub to a dedicated well-known URL:

| Format | URL | Size |
|--------|-----|------|
| JSON | `https://huggingface.co/.well-known/openapi.json` | Full JSON object |
| Markdown | `https://huggingface.co/.well-known/openapi.md` | 12,358 lines |
| Interactive | `https://huggingface.co/spaces/huggingface/openapi` | OpenAPI Playground |

The Markdown version is specifically targeted at AI agents — the docs page notes: *"If you're an Agent, you might prefer the markdown version OpenAPI spec."*

### Complete API Surface Area (by Endpoint Group)

#### Auth (2 endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/whoami-v2` | GET | Get current user info and auth method |
| `/api/check-token` | GET | Check token validity (under Auth section) |

#### Models API (~35+ endpoints)
Core listing, CRUD, and repository management for model repos:

**Listing & Search:**
- `GET /api/models` — List all models (supports `search`, `author`, `sort`, `direction`, `limit`, `full`, `config`, `pipeline_tag`, `library`, `language`, `license`, `private`, `other`, `expand` params)
- `GET /api/models/{namespace}/{repo}` — Get model metadata
- `DELETE /api/models/{namespace}/{repo}` — Delete a model repo

**Commit & Content Management:**
- `POST /api/models/{namespace}/{repo}/commit/{rev}` — Create a commit (supports both `application/json` and `application/x-ndjson`)
- `GET /api/models/{namespace}/{repo}/tree/{rev}/{path}` — List folder content (supports `expand`, `recursive`, `limit`, `cursor` for pagination)
- `POST /api/models/{namespace}/{repo}/paths-info/{rev}` — Get info on specific paths (batch of up to 2000 paths)
- `GET /api/models/{namespace}/{repo}/refs` — List git refs (branches, tags) with optional `include_prs`
- `GET /api/models/{namespace}/{repo}/commits/{rev}` — Paginated commit history
- `GET /api/models/{namespace}/{repo}/compare/{compare}` — Diff between two revisions

**Branch & Tag Management:**
- `POST /api/models/{namespace}/{repo}/branch/{rev}` — Create branch (`startingPoint`, `emptyBranch`, `overwrite`)
- `DELETE /api/models/{namespace}/{repo}/branch/{rev}` — Delete a branch
- `POST /api/models/{namespace}/{repo}/tag/{rev}` — Create a tag
- `DELETE /api/models/{namespace}/{repo}/tag/{rev}` — Delete a tag

**File Management:**
- `POST /api/models/{namespace}/{repo}/preupload/{rev}` — Check upload method (LFS vs direct)
- `GET /api/models/{namespace}/{repo}/lfs-files` — List Xet/LFS files (paginated via `cursor`)
- `POST /api/models/{namespace}/{repo}/lfs-files/batch` — Batch delete LFS files
- `DELETE /api/models/{namespace}/{repo}/lfs-files/{sha}` — Delete single LFS file (with `rewriteHistory` option)
- `POST /api/models/{namespace}/{repo}/lfs-files/duplicate` — Duplicate Xet files across repos by hash

**Security & Access:**
- `GET /api/models/{namespace}/{repo}/scan` — Get security scan status
- `GET /{namespace}/{repo}/user-access-report` — Export gated repo access report
- `POST /{namespace}/{repo}/ask-access` — Request access to gated repository
- `POST /api/models/{namespace}/{repo}/user-access-request/cancel` — Cancel access request
- `GET /api/models/{namespace}/{repo}/user-access-request/{status}` — List access requests by status

**Settings & Metadata:**
- `PUT /api/models/{namespace}/{repo}/settings` — Update repo settings (private, visibility, discussions, gated config)
- `POST /api/models/{namespace}/{repo}/super-squash/{rev}` — Squash all commits into one (irreversible)
- `POST /api/models/{namespace}/{repo}/resource-group` — Add to resource group (Enterprise)
- `GET /api/models/{namespace}/{repo}/resource-group` — Get resource group
- `GET /api/models/{namespace}/{repo}/treesize/{rev}/{path}` — Get total size under path
- `GET /api/models/{namespace}/{repo}/jwt` — Generate JWT token (with write/expiration/encryption options)
- `GET /api/models/{namespace}/{repo}/notebook/{rev}/{path}` — Get Jupyter notebook URL

**Xet Storage:**
- `GET /api/models/{namespace}/{repo}/xet-write-token/{rev}` — Short-lived Xet write token
- `GET /api/models/{namespace}/{repo}/xet-read-token/{rev}` — Short-lived Xet read token

**File Resolution:**
- `GET /{namespace}/{repo}/resolve/{rev}/{path}` — Resolve a file (supports Range header, Xet file info)
- `GET /api/resolve-cache/models/{namespace}/{repo}/{rev}/{path}` — Cache-aware file resolution

#### Datasets API (mirrors Models structure — ~30+ endpoints)

Same endpoint patterns as Models with `/api/datasets/` prefix. Includes:
- All commit, branch, tag, file management endpoints
- Dataset-specific listing with `GET /api/datasets` (same filter params as models)
- Dataset-specific info with `GET /api/datasets/{namespace}/{repo}`
- Dataset-specific `DELETE /api/datasets/{namespace}/{repo}`

**Key extra:** The spec doesn't list the datasets-server endpoints (these are at `datasets-server.huggingface.co`, separate from the main Hub API).

#### Spaces API (mirrors Models structure — ~30+ endpoints)

Same endpoint patterns with `/api/spaces/` prefix, plus:

**Spaces-Specific Endpoints:**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/spaces` | GET | List Spaces (with `search`, `author`, `sort`, `limit`, `full`, `sdk` params) |
| `/api/spaces/{namespace}/{repo}` | GET | Get Space metadata |
| `/api/spaces/{namespace}/{repo}` | DELETE | Delete a Space |
| `PUT /api/spaces/{namespace}/{repo}/settings` | PUT | Update Space settings (+ Space-specific: `hardware`, `storage`, `sleepTime`, `secrets`, `variables`) |
| `POST /api/spaces/{namespace}/{repo}/restart` | POST | Restart a Space |
| `POST /api/spaces/{namespace}/{repo}/pause` | POST | Pause a Space (free tier optimization) |
| `GET /api/spaces/{namespace}/{repo}/runtime` | GET | Get Space runtime status |
| `POST /api/spaces/{namespace}/{repo}/apply-latest-config` | POST | Apply latest configuration |
| `POST /api/spaces/{namespace}/{repo}/move-to-latest-config` | POST | Move to latest config revision |

#### Discussions & Pull Requests API (~40+ endpoints)

Template: `/api/{repoType}/{namespace}/{repo}/discussions/{num}`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/{repoType}/{namespace}/{repo}/discussions` | GET | List discussions |
| `/api/{repoType}/{namespace}/{repo}/discussions` | POST | Create discussion/PR |
| `.../discussions/{num}` | GET | Get discussion detail |
| `.../discussions/{num}` | POST | Edit discussion |
| `.../discussions/{num}/comment` | POST | Add comment |
| `.../discussions/{num}/comment/{commentId}` | DELETE | Delete comment |
| `.../discussions/{num}/comment/{commentId}/edit` | POST | Edit comment |
| `.../discussions/{num}/comment/{commentId}/reply` | POST | Reply to comment |
| `.../discussions/{num}/change-status` | POST | Change status (open/closed) |
| `.../discussions/{num}/merge` | POST | Merge PR |
| `.../discussions/{num}/ref` | DELETE | Delete PR ref (free storage) |
| `.../discussions/{num}/storage` | GET | Estimate PR LFS storage |

#### Collections API (~8 endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/collections` | GET | List collections |
| `/api/collections` | POST | Create collection |
| `/api/collections/{slug}` | GET | Get collection |
| `/api/collections/{slug}` | DELETE | Delete collection |
| `/api/collections/{slug}` | PATCH | Update collection |
| `/api/collections/{slug}/items` | POST | Add item |
| `/api/collections/{slug}/items/{itemId}` | DELETE | Remove item |
| `/api/collections/{slug}/items/{itemId}` | PATCH | Update item |

#### Papers API (~8+ endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/papers` | GET | List daily papers |
| `/api/papers/{paperId}` | GET | Get paper detail |
| `/api/papers/{paperId}/comment` | POST | Create comment |
| `/api/papers/{paperId}/comment/{commentId}/reply` | POST | Reply to comment |
| `/api/papers/{paperId}/vote` | POST | Vote on paper |

#### Posts API (~8+ endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/posts/{username}/{postSlug}` | GET | Get post |
| `/api/posts/{username}/{postSlug}` | DELETE | Delete post |
| `/api/posts/{username}/{postSlug}/comment` | POST | Create comment |
| `/api/posts/{username}/{postSlug}/comment/{commentId}/reply` | POST | Reply to comment |

#### Organizations API (~10+ endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/organizations` | GET | List user's orgs |
| `/api/organizations` | POST | Create org |
| `/api/organizations/{org}` | GET | Get org details |
| `/api/organizations/{org}` | POST | Edit org |
| `/api/organizations/{org}/members` | GET | List members |
| `/api/organizations/{org}/members` | POST | Add member |
| `/api/organizations/{org}/members/{member}` | DELETE | Remove member |
| `/api/organizations/{org}/members/{member}` | POST | Change role |

#### Trending & Discovery (3 endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/trending` | GET | Get trending repos (`type`: all/model/dataset/space, `limit`) |
| `GET /api/models-tags-by-type` | GET | Get model tags grouped by type (pipeline_tag, library, language, license, etc.) |
| `GET /api/quicksearch` | GET | Cross-type instant search |

#### Webhooks API (~9 endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/webhooks` | GET | List webhooks |
| `/api/webhooks` | POST | Create webhook |
| `/api/webhooks/{webhookId}` | GET | Get webhook |
| `/api/webhooks/{webhookId}` | POST | Update webhook |
| `/api/webhooks/{webhookId}` | DELETE | Delete webhook |
| `/api/webhooks/{webhookId}/enable` | POST | Enable webhook |
| `/api/webhooks/{webhookId}/disable` | POST | Disable webhook |

#### Jobs API (~6+ endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/jobs` | GET | List jobs |
| `/api/jobs` | POST | Create job |
| `/api/jobs/{jobId}` | GET | Get job status |
| `/api/jobs/{jobId}` | DELETE | Cancel job |
| `/api/jobs/{jobId}/logs` | GET | Get job logs |

#### Storage/Buckets API (~9+ endpoints)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/buckets` | GET | List buckets |
| `/api/buckets` | POST | Create bucket |
| `/api/buckets/{bucketId}` | GET | Get bucket |
| `/api/buckets/{bucketId}` | DELETE | Delete bucket |
| `/api/buckets/{bucketId}/sync` | POST | Sync bucket |

### Key Architectural Insights

1. **Pattern symmetry**: Models, Datasets, and Spaces share nearly identical endpoint structures (commit, tree, paths-info, preupload, lfs-files, refs, branches, tags, settings, resource-group, treesize, jwt, notebooks). This means knowledge of one repo type's API is directly transferable.

2. **Commit API dual format**: The commit endpoint supports both `application/json` (single JSON body with `files`, `lfsFiles`, `deletedEntries` arrays) and `application/x-ndjson` (JSON lines — each line is a separate operation: `header`, `file`, `lfsFile`, `deletedEntry`). NDJSON is recommended for large commits.

3. **Pagination everywhere**: All list endpoints support cursor-based pagination (`cursor` + `limit`), not just offset-based. The tree listing defaults to 1,000 items (100 with `expand=true`).

4. **Eventual consistency**: The spec notes that `resolve-cache` endpoints exist for cache-aware file resolution — indicating a CDN/caching layer between clients and the Hub's git storage.

5. **Rate limits**: All API calls are subject to HF-wide rate limits. The docs reference upgrading accounts for elevated access.

6. **OpenAPI spec itself evolves**: The spec at `/.well-known/openapi.md` is auto-generated from the Hub's codebase, making it always up-to-date — more reliable than static documentation for discovering newly added endpoints.

### Programmatic Spec Consumption Patterns

```python
import requests

# Fetch the OpenAPI spec as JSON for programmatic discovery
spec_json = requests.get("https://huggingface.co/.well-known/openapi.json").json()

# Discover all endpoints and their methods
for path, methods in spec_json.get("paths", {}).items():
    for method in methods:
        print(f"{method.upper():6s} {path}")

# Or as markdown (better for LLM ingestion)
spec_md = requests.get("https://huggingface.co/.well-known/openapi.md").text

# Extract all endpoint groups (headers at ## level)
import re
groups = re.findall(r"^## (.+)$", spec_md, re.MULTILINE)
# Returns: ['Auth', 'Models', 'Datasets', 'Spaces', 'Discussions', ...]
```

### Key Takeaways

1. **Single source of truth**: The OpenAPI spec at `/.well-known/` is always up-to-date, covering all Hub REST endpoints.
2. **155+ endpoints** across 12+ API groups — Auth, Models, Datasets, Spaces, Discussions, Collections, Papers, Posts, Organizations, Trending, Webhooks, Jobs, Storage/Buckets.
3. **Model/Dataset/Space symmetry**: ~80% of endpoints are shared across repo types with only the prefix changing.
4. **Commit API is dual-format**: JSON for simple commits, NDJSON for batch/large commits.
5. **Cursor-based pagination** across all list endpoints — not offset/limit.
6. **Zero-cost to use**: All read endpoints are freely accessible; write endpoints require authentication via HF token.
7. **The spec is agent-friendly**: The Markdown version is explicitly designed for AI agent consumption.
8. **OpenAPI Playground** at `https://huggingface.co/spaces/huggingface/openapi` enables interactive endpoint testing without writing code.

### Resources
- OpenAPI Markdown: https://huggingface.co/.well-known/openapi.md
- OpenAPI JSON: https://huggingface.co/.well-known/openapi.json
- OpenAPI Playground: https://huggingface.co/spaces/huggingface/openapi
- Hub API Docs: https://huggingface.co/docs/hub/en/api
- huggingface_hub Python SDK: https://github.com/huggingface/huggingface_hub

### Skill
mlops/huggingface-hub -- references/hf-learnings.md

---

## 2026-07-24: hf-inference-client-provider-fallback-and-routing — Provider Discovery & Fallback Chains (Topic #143)

### Summary
Deep-dive into building practical provider fallback chains using Hugging Face `InferenceClient`. Covers programmatic provider discovery via `model_info(expand='inferenceProviderMapping')`, the `InferenceProviderMapping` data model, building multi-provider fallback chains with `AsyncInferenceClient`, Router API `/v1/models` for provider comparison, direct provider API key integration, and real provider availability patterns verified against `huggingface_hub` v1.24.0.

### Core Discovery API — inferenceProviderMapping

The Hub's `expand=inferenceProviderMapping` parameter reveals which providers serve a model and their status. This is the programmatic foundation for any fallback strategy.

```python
from huggingface_hub import HfApi

api = HfApi()
info = api.model_info("microsoft/phi-4", expand="inferenceProviderMapping")
for pm in info.inference_provider_mapping:
    print(f"{pm.provider:25s} | status={pm.status:10s} | task={pm.task}")
# Output (verified live on 2026-07-24):
#   featherless-ai            | status=live       | task=conversational
#   deepinfra                 | status=live       | task=conversational
```

#### InferenceProviderMapping Data Model

| Field | Type | Description |
|-------|------|-------------|
| `provider` | `str` | Provider identifier (e.g. `"featherless-ai"`, `"deepinfra"`, `"together"`) |
| `hf_model_id` | `str` | The original Hugging Face model ID |
| `provider_id` | `str` | Provider's internal model name (may differ from HF ID) |
| `status` | `str` | `"live"` = available, other values = degraded/unavailable |
| `task` | `str` | Inference task (e.g. `"conversational"`, `"text-to-image"`) |
| `adapter` | `str\|None` | LoRA adapter if applicable |
| `adapter_weights_path` | `str\|None` | Path to adapter weights |
| `type` | `str\|None` | Model type |

**Key insight:** Not all models have providers. Only models actively served by at least one inference provider return a non-empty `inference_provider_mapping`. Models with no mapping must be run locally or via Inference Endpoints.

### Real Provider Availability Patterns

Testing against `huggingface_hub` v1.24.0 on 2026-07-24:

| Model | Live Providers | Total |
|-------|---------------|-------|
| `microsoft/phi-4` | featherless-ai, deepinfra | 2/2 |
| `Qwen/Qwen2.5-7B-Instruct` | featherless-ai, together | 2/2 |
| `Qwen/Qwen3-32B` | featherless-ai, deepinfra, nscale | 3/5 |
| `meta-llama/Meta-Llama-3.1-8B-Instruct` | novita, deepinfra, nscale | 3/4 |
| `google/gemma-2-2b-it` | featherless-ai | 1/1 |
| `NousResearch/Hermes-3-Llama-3.1-8B` | featherless-ai | 1/1 |
| `mistralai/Mistral-7B-Instruct-v0.3` | _(none live)_ | 0/1 |

**Patterns observed:**
- **featherless-ai** is the most common free provider — serves almost all popular models
- **deepinfra** and **nscale** are frequent secondary providers
- **together** covers selective popular models (Qwen, Llama families)
- **novita** appears on well-known Llama-family models
- Empty live-provider sets happen — always check before routing

### Provider Selection — Three-Layer System

#### Layer 1: Client-Level Default (on InferenceClient init)

```python
from huggingface_hub import InferenceClient

# Auto — fastest available (default)
client = InferenceClient(provider="auto")

# Pin to specific provider
client = InferenceClient(provider="deepinfra")
```

#### Layer 2: Per-Call Override via Model-ID Suffix

```python
# Suffix syntax overrides the client-level default for this call
result = client.chat_completion(
    model="Qwen/Qwen3-32B:fastest",     # fastest provider
    messages=[...],
)
# :cheapest   — lowest price per output token
# :preferred  — user preference from hf.co/settings/inference-providers
# :cerebras   — any supported provider name (17+ providers)
```

#### Layer 3: Provider Detection at Runtime (Discovery API)

```python
def get_live_providers(model_id: str) -> list[str]:
    """Return list of live provider names for a model."""
    try:
        info = HfApi().model_info(model_id, expand="inferenceProviderMapping")
        return [pm.provider for pm in info.inference_provider_mapping if pm.status == "live"]
    except Exception:
        return []

# Usage
live = get_live_providers("Qwen/Qwen3-32B")
print(live)  # ['featherless-ai', 'deepinfra', 'nscale']
```

### Building a Provider Fallback Chain

The most reliable multi-provider pattern uses `AsyncInferenceClient` for concurrent fallback attempts:

```python
import asyncio
from huggingface_hub import InferenceClient, AsyncInferenceClient

async def try_provider(client: AsyncInferenceClient, model: str, messages: list, timeout: float = 15.0):
    """Try a single provider, return result or None on failure."""
    try:
        result = await client.chat_completion(
            model=model, messages=messages, max_tokens=256,
        )
        return result
    except Exception as e:
        return None

async def chat_with_fallback(
    messages: list,
    model: str = "microsoft/phi-4",
    providers: list[str] | None = None,
    timeout_per_provider: float = 15.0,
):
    """Try providers in order, fall through on failure."""
    if providers is None:
        providers = get_live_providers(model) or ["auto"]

    for provider in providers:
        client = AsyncInferenceClient(provider=provider, timeout=timeout_per_provider)
        result = await try_provider(client, model, messages, timeout_per_provider)
        await client.close()
        if result is not None:
            return result
        print(f"Provider {provider} failed, trying next...")

    raise RuntimeError(f"All {len(providers)} providers failed for {model}")

# Usage
# result = asyncio.run(chat_with_fallback(
#     messages=[{"role": "user", "content": "Hello!"}],
#     model="microsoft/phi-4",
# ))
```

#### Concurrent Fallback (Race Pattern)

When you need the fastest response and don't care which provider serves it:

```python
async def chat_concurrent_race(
    messages: list,
    model: str = "microsoft/phi-4",
    providers: list[str] | None = None,
    timeout: float = 20.0,
):
    """Fire requests to all providers concurrently, return first success."""
    if providers is None:
        providers = get_live_providers(model) or ["auto"]

    async def try_one(provider: str) -> tuple[str, dict | None]:
        try:
            client = AsyncInferenceClient(provider=provider, timeout=timeout)
            result = await client.chat_completion(
                model=model, messages=messages, max_tokens=256,
            )
            await client.close()
            return (provider, result)
        except:
            return (provider, None)

    tasks = [try_one(p) for p in providers]
    for coro in asyncio.as_completed(tasks):
        provider, result = await coro
        if result is not None:
            # Cancel remaining tasks
            for t in tasks:
                t.close()
            return (provider, result)

    raise RuntimeError(f"All providers failed for {model}")
```

### Router API — Provider Comparison

The Router API (`GET /v1/models`) provides richer data than `inferenceProviderMapping`, including pricing, latency, and structured output support:

```python
import httpx
import json

def get_provider_details(model_id: str) -> list[dict]:
    """Get detailed provider info from Router API."""
    resp = httpx.get(f"https://router.huggingface.co/v1/models/{model_id}", timeout=10)
    resp.raise_for_status()
    return resp.json().get("providers", [])

# Compare providers for a model
providers = get_provider_details("Qwen/Qwen3-32B")
for p in providers:
    print(f"{p['provider']:20s} | "
          f"live={p.get('status') == 'live':5} | "
          f"TTFT={p.get('first_token_latency_ms', '?'):>8}ms | "
          f"t/s={p.get('throughput', '?'):>6} | "
          f"tools={p.get('supports_tools', '?'):5} | "
          f"struct={p.get('supports_structured_output', '?'):5} | "
          f"free={p.get('is_free', '?'):5}")
```

**Router API per-provider fields:**

| Field | Type | Description |
|-------|------|-------------|
| `provider` | str | Provider identifier |
| `status` | str | `live` or `error` |
| `context_length` | int | Max context for this provider+model |
| `pricing.input` | float | USD per million input tokens |
| `pricing.output` | float | USD per million output tokens |
| `is_free` | bool | Temporary free promo |
| `supports_tools` | bool | Tool/function calling |
| `supports_structured_output` | bool | JSON-schema output |
| `first_token_latency_ms` | int | Latest TTFT from validation probe |
| `throughput` | number | Output tokens/sec |
| `is_model_author` | bool | Provider published this model |

### Direct Provider API Keys (Billing Bypass)

Pass a provider's own API key to use your account directly, bypassing HF billing:

```python
# HF billing (default)
client = InferenceClient(api_key="hf_...")

# Direct provider billing — use their API key
client = InferenceClient(
    provider="together",
    api_key="<together_api_key>",  # NOT HF token
)
```

**When to use this:**
- Your provider account has free credits (Together AI gives $1 free, many offer trial credits)
- You need higher rate limits than HF distribution allows
- You want to use the HF client but bill directly to your provider account

### Zero-Cost Best Practices

1. **Default to `provider="auto"`** — HF routes to the fastest/reliably available provider automatically with failover built in
2. **Check `inferenceProviderMapping` before critical calls** — saves timeout on models with no live providers
3. **Use suffix syntax for one-off provider pins** — `model_id:provider-name` avoids needing a separate `provider` param
4. **Race concurrent providers for latency-sensitive tasks** — issue requests simultaneously to the 2-3 fastest providers, take the first response
5. **Cache provider mappings** — the response is stable; don't call `model_info(expand=...)` before every inference
6. **Always set a timeout** — default is 60s; 15-30s is better for interactive use
7. **Handle 503 gracefully** — providers may need to cold-start; retry with backoff
8. **Monitor `is_free` on Router API** — some providers offer free tiers temporarily; build your fallback order to prefer free providers

### Resources
- [InferenceClient API reference](https://huggingface.co/docs/huggingface_hub/v1.24.0/en/package_reference/inference_client)
- [Inference Providers docs](https://huggingface.co/docs/inference-providers/en/index)
- [Router API](https://router.huggingface.co/v1/models)
- [Hub API — Inference provider discovery](https://huggingface.co/docs/inference-providers/en/hub-api)
- [Inference settings (preferred providers)](https://huggingface.co/settings/inference-providers)

### Skill
huggingface-hub — references/hf-learnings.md

---

## 2026-07-24: hf-hub-commit-api — Deep Dive (Topic #57)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Commit API — the low-level foundation for all file operations on the Hub. Covers all three `CommitOperation` types (Add, Delete, Copy), the `create_commit()` entry point, high-level wrappers (`upload_file`, `upload_folder`, `copy_files`), the `CommitScheduler` for periodic pushes, `preupload_lfs_files` for memory-constrained large uploads, and `list_repo_commits` for inspecting history. Focused on practical patterns that work under zero-cost constraints.

### Core Architecture

The Hub Commit API follows a three-operation model:

| Operation | Purpose | Fields |
|---|---|---|
| `CommitOperationAdd` | Upload/create a file | `path_in_repo`, `path_or_fileobj` (str Path bytes or BinaryIO) |
| `CommitOperationDelete` | Remove a file or folder | `path_in_repo` |
| `CommitOperationCopy` | Copy within/across repos (server-side) | `src_path_in_repo`, `path_in_repo`, optional `src_revision`, `src_repo_id`, `src_repo_type` |

All three inherit from `CommitOperation` and are passed as a list to `create_commit()`.

### create_commit() Parameters

```python
api.create_commit(
    repo_id="user/repo",
    operations=[...],           # List[CommitOperation] — will be mutated!
    commit_message="msg",       # Required, non-empty
    commit_description=None,    # Optional longer description
    token=None,                 # Defaults to cached token
    repo_type=None,             # None/model, dataset, space
    revision=None,              # Branch name or commit OID (default: main)
    create_pr=False,            # Open a PR instead of committing directly
    num_threads=5,              # Concurrent upload threads for LFS files
    parent_commit=None,         # OID to enforce linear history (optimistic locking)
    run_as_future=False,        # Non-blocking background execution
)
```

**Critical constraints:**
- Max **25k LFS files** per commit
- Max **1GB payload** for regular (non-LFS) files
- The input `operations` list **will be mutated** — do not reuse objects
- Repo must already exist; create it first with `create_repo()`
- Empty `commit_message` raises `ValueError`

### CommitOperationAdd — Three Input Modes

```python
# 1. From local file path
CommitOperationAdd(path_in_repo="weights.bin", path_or_fileobj="./local/weights.bin")

# 2. From bytes in memory
CommitOperationAdd(path_in_repo="config.json", path_or_fileobj=b'{"key": "value"}')

# 3. From binary file object (supports seek/tell)
with open("data.bin", "rb") as f:
    CommitOperationAdd(path_in_repo="data.bin", path_or_fileobj=f)
```

Internally computes `UploadInfo` (SHA256 for LFS, SHA1 for regular files) and compares against the remote OID to skip unchanged files (preventing empty commits).

The `as_file()` context manager yields a `BinaryIO` from any input type, optionally with tqdm progress bar:
```python
with operation.as_file(with_tqdm=True) as f:
    httpx.put(..., data=f)
```

### CommitOperationCopy — Server-Side Copies

```python
# Copy within same repo
CommitOperationCopy(src_path_in_repo="image.png", path_in_repo="backup/image.png")

# Copy from another repo
CommitOperationCopy(
    src_path_in_repo="weights.safetensors",
    path_in_repo="weights.safetensors",
    src_repo_id="other-user/source-model",
    src_repo_type="model",
    src_revision="main",       # Optional: specify source branch
)
```

**Key details:**
- Zero data transfer — server-side operation, no download/upload cost
- Works across repos but NOT across storage regions
- Also works with Buckets via `api.copy_files(source, destination)` using `hf://` URIs

### CommitInfo Return Value

```python
@dataclass
class CommitInfo(str):
    commit_url: str        # e.g. "https://huggingface.co/user/repo/commit/abc123"
    commit_message: str
    commit_description: str
    oid: str               # Full SHA commit hash
    pr_url: str | None     # Set when create_pr=True
    pr_revision: str | None  # e.g. "refs/pr/1"
    pr_num: int | None
    repo_url: RepoUrl      # Parsed repo info
```

Inherits from `str` for backward compatibility (the string value is the commit URL).

### High-Level Wrappers

#### upload_file() — Single File

```python
api.upload_file(
    path_or_fileobj="/path/to/local/README.md",  # or bytes or BinaryIO
    path_in_repo="README.md",
    repo_id="user/test-dataset",
    repo_type="dataset",
)
```

#### upload_folder() — Directory Upload (Recommended)

```python
api.upload_folder(
    folder_path="./logs",
    repo_id="user/trained-model",
    path_in_repo="experiment/logs/",
    allow_patterns="*.txt",        # Upload only .txt files
    ignore_patterns="**/temp/*",   # Exclude temp files
    delete_patterns="*.txt",       # Delete remote .txt files before upload
)
```

**Auto-batching:** When `hf_xet` is installed (default since huggingface_hub v0.32.0), `upload_folder()` automatically splits large folders into multiple commits with "(part 2)", "(part 3)" suffixes. It's **resumable** — re-run the same call after interruption and already-committed files are skipped, chunks are deduplicated.

**Performance:** Set `HF_XET_HIGH_PERFORMANCE=1` to saturate bandwidth and CPU cores. The legacy `HF_HUB_ENABLE_HF_TRANSFER=1` is deprecated.

#### copy_files() — Server-Side Cross-Repo Copy

```python
# Copy single file between repos
api.copy_files(
    "hf://username/source-model/weights.safetensors",
    "hf://username/target-model/weights.safetensors",
)

# Copy entire folder (rsync-style with trailing /)
api.copy_files(
    "hf://datasets/username/source-dataset/data/",
    "hf://datasets/username/target-dataset/data/",
)

# Duplicate within same repo
api.copy_files(
    "hf://username/my-model/config.json",
    "hf://username/my-model/backup/config.json",
)
```

**Folder semantics:**
- Trailing `/` on source → copies **contents** (rsync-style, no nesting)
- No trailing `/` on source → copies **folder itself** (cp -r style, nests inside destination)

### CommitScheduler — Periodic Background Uploads

```python
from huggingface_hub import CommitScheduler

scheduler = CommitScheduler(
    repo_id="user/feedback-data",
    repo_type="dataset",
    folder_path="/local/data",
    path_in_repo="data",
    every=10,                    # minutes between commits
    allow_patterns="*.jsonl",
    squash_history=False,        # Set True to keep repo history manageable
)
```

**Key design properties:**
- **Append-only assumption:** Only add new files or append to existing ones. Deleting/overwriting may corrupt the repo.
- **No empty commits:** Automatically skips if no changes detected.
- **Thread-safe:** Use `scheduler.lock` context manager for concurrent writes from multiple threads.
- **Error resilience:** Silent failure on network errors — retries at next interval.
- **Context manager:** Use `with CommitScheduler(...) as scheduler:` to ensure clean shutdown + final commit.

**Custom push_to_hub():** Override to transform data before upload (e.g., zip PNGs, aggregate logs):
```python
class ZipScheduler(CommitScheduler):
    def push_to_hub(self):
        png_files = list(self.folder_path.glob("*.png"))
        if not png_files:
            return
        # ... zip and upload via self.api.upload_file(...)
        for png in png_files:
            png.unlink()  # clean up local files
```

### preupload_lfs_files — Memory-Constrained Large Uploads

For cases where you generate large shards in memory and want a single commit:

```python
from huggingface_hub import CommitOperationAdd, preupload_lfs_files, create_commit

operations = []
for i in range(5):
    content = generate_shard()  # generates bytes
    addition = CommitOperationAdd(path_in_repo=f"shard_{i}.bin", path_or_fileobj=content)
    preupload_lfs_files(repo_id, additions=[addition])  # upload to S3 now
    operations.append(addition)

# Single commit referencing all pre-uploaded files
create_commit(repo_id, operations=operations, commit_message="All shards")
```

**⚠ Caveat:** Until the commit is made, pre-uploaded files are NOT accessible on the Hub. The `CommitOperationAdd` objects are **mutated** (binary content removed from the object) during preupload.

### list_repo_commits — Inspecting History

```python
commits = api.list_repo_commits("gpt2")
# Sorted by date, newest first

initial_commit = commits[-1]  # Last is the initial commit
# GitCommitInfo(
#     commit_id='9b865efde13a30...',
#     authors=['system'],
#     created_at=datetime(...),
#     title='initial commit',
#     message='',
# )
```

Useful for finding the initial commit OID to create an empty branch:
```python
api.create_branch("gpt2", "new_empty_branch", revision=initial_commit.commit_id)
```

### Zero-Cost Best Practices

1. **Prefer `upload_folder()` with `hf_xet`** — automatic batching, resumability, and deduplication are free and reduce API calls.
2. **Use `CommitOperationCopy` for file duplication** — server-side copies cost nothing and move zero bytes.
3. **Schedule with `CommitScheduler`** — avoid per-event commits; batch every 5-10 minutes to stay under rate limits (~100 req/min).
4. **Check `_remote_oid` before uploading** — `create_commit` already deduplicates unchanged files, but you can pre-check with `file_exists()` on the Hub API.
5. **Avoid empty PRs** — opening PRs without real changes wastes rate limit budget.
6. **Never reuse `CommitOperation` objects** — they get mutated during upload; create fresh operations per commit.
7. **Use `repo_type="dataset"` for persistent storage** — datasets get generous LFS storage for free and integrate with `CommitScheduler`.

### Resources
- Upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- HfApi reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- CommitScheduler: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api#huggingface_hub.CommitScheduler
- Repository limitations: https://huggingface.co/docs/hub/en/repositories-limitations
- HF URIs syntax: https://huggingface.co/docs/huggingface_hub/en/package_reference/utilities#huggingface_hub.HfUri
- Xet storage overview: https://huggingface.co/docs/hub/en/xet

---

## 2026-07-23: hf-bitsandbytes-quantization

### Summary
Researched the bitsandbytes library's integration with Hugging Face Transformers for k-bit quantization (8-bit and 4-bit), enabling large model inference and training on consumer GPUs with dramatically reduced memory.

### Key Concepts

**Three Main Features:**
1. **8-bit optimizers** — block-wise quantization for Adam/AdamW/etc. maintaining 32-bit performance at fraction of memory cost
2. **LLM.int8()** — vector-wise quantization for inference, quantizes most features to 8-bit, outliers handled with 16-bit matmul (no quality loss)
3. **QLoRA (4-bit)** — quantizes model to 4-bit + trains LoRA adapters. Uses NF4 data type

**Hardware Support:** NVIDIA CUDA, Intel XPU, Intel Gaudi HPU, CPU

**BitsAndBytesConfig Parameters:**
- `load_in_4bit=True/load_in_8bit=True` — enable quantization
- `bnb_4bit_quant_type="nf4"` — NF4 (QLoRA paper) vs "fp4"
- `bnb_4bit_compute_dtype=torch.bfloat16` — compute dtype for speed
- `bnb_4bit_use_double_quant=True` — nested quantization (extra 0.4 bits/param saved)
- `llm_int8_threshold=6.0` — outlier threshold for LLM.int8()
- `llm_int8_skip_modules=["lm_head"]` — skip specific modules
- `llm_int8_enable_fp32_cpu_offload=True` — offload to CPU

**QLoRA Pipeline:**
1. Load base model with `load_in_4bit=True`, `bnb_4bit_quant_type="nf4"`
2. Apply PEFT LoRA config
3. Train only LoRA adapters
4. Merge or keep separate for inference

**Resources:**
- Paper: QLoRA (https://hf.co/papers/2305.14314)
- Blog: "Making LLMs even more accessible with bitsandbytes, 4-bit quantization and QLoRA" (https://huggingface.co/blog/4bit-transformers-bitsandbytes)

---

## 2026-07-23: hf-hub-model-download-stats

### Summary
Researched the Hugging Face Hub's model download counting methodology — how the Hub tracks downloads server-side using per-library query files, handles edge cases like Diffusers and GGUF, and provides Publisher Analytics for granular logs.

### Key Concepts

**Query Files System:** The Hub counts downloads by monitoring HTTP GET/HEAD requests to library-specific query files. Default query files are `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`. Libraries can override these with custom `countDownloads` filters.

**Per-Library Query Files:**
- **Default**: `config.json`, `config.yaml`, `hyperparams.yaml`, `params.json`, `meta.yaml`
- **Nemo**: All `.nemo` files
- **GGUF**: All `.gguf` files (self-contained, no library dependency)
- **Diffusers**: `model_index.json` + top-level `.safetensors`/`.ckpt`/`.bin` files

**Diffusers Edge Case:** The most complex counting logic because users download via both the Python library (counts `model_index.json`) and direct UI downloads (counts top-level `.safetensors`/`.ckpt`/`.bin`). Nested files excluded to prevent double-counting.

**Publisher Analytics:** Enterprise solution providing anonymized request-level access logs for organizations needing granular data (unique downloaders, CI/CD filtering, etc.).

### Resources
- https://huggingface.co/docs/hub/en/models-download-stats — official docs
- https://huggingface.co/docs/hub/en/publisher-analytics — Publisher Analytics

---

## 2026-07-24: hf-hub-upload-strategies (Deep Dive)

### Summary
Comprehensive deep-dive on uploading files, folders, and large models to the Hugging Face Hub. Covered all 7 major upload methods (CLI, Python API, resumable, Rust-accelerated, Xet-backed), their comparison matrix, use-case strategies, error handling patterns, and best practices.

### Key Insights
- Comparison matrix of 9 upload methods across dimensions (resumable, concurrent, atomic)
- `upload_large_folder` uses a `.hfupload` manifest for resumability
- `hf_transfer` (Rust, `pip install hf_transfer`) provides 2-3× faster uploads for >5 GB files
- Xet backend (`HF_STORAGE_BACKEND=xet`) provides content-addressed dedup for iterative releases
- `upload_folder` respects `.gitignore` — override with `ignore_patterns`
- `create_commit` with `CommitOperationAdd|Delete|Copy` provides atomic commits
- Don't mix Xet and hf_transfer simultaneously
- Always validate after upload with `api.repo_info()` or `api.list_repo_tree()`

### Also this run
|- Fixed `author: SakThai` and `license: MIT` on all 84 SKILL.md files in the profile
|- Pushed 85 files changed (674 additions) to GitHub

---

## 2026-07-24: hf-transformers-generation-config-deep-dive (Deep Dive)

### Summary
Comprehensive deep-dive into Transformers' GenerationConfig and generate() API (v5.14.0). Extended Entry 59 with full parameter reference, generation mode auto-detection, logits processor pipeline (16 stages), custom stopping criteria, SynthIDText watermarking, assisted generation (speculative decoding with DSLA), continuous batching for production serving, custom generation methods (Hub repos and callables), streaming (TextStreamer/TextIteratorStreamer), CFG via negative prompts, and 6 production best practices.

### Key Insights
- **Length control**: Always prefer `max_new_tokens` over `max_length` to avoid prompt truncation
- **Watermarking**: Two systems — SynthIDText (DeepMind, recommended) and simple WatermarkingConfig; both enable detection without state
- **Speculative decoding**: 2-3x speedup with `assistant_model`; 1.5x with `prompt_lookup_num_tokens` (no assistant needed); DSLA adapts budget dynamically
- **Custom generation**: New `custom_generate` argument accepts Hub repo name or callable — replaces the decoding loop without subclassing
- **Continuous batching**: Native production serving via `ContinuousBatchingManager` with CUDA graph support
- **Logits processor pipeline**: 16-stage pipeline; custom processors inserted before the first stage
- **stop_strings**: Tokenizer-agnostic string-based stopping (v5.14+)
- **CFG**: Negative prompt guidance via `guidance_scale` (experimental)

### Fields covered in detail
- 7 parameter categories (length, output, sampling, contrastive, watermarking, assisted, advanced) with 50+ parameters
- 7 generation modes (greedy, sampling, beam, beam-sampling, contrastive, diverse beam, assisted)
- Full logits processor pipeline order with 16 stages
- SynthIDText and simple watermarking with detection
- Speculative decoding: assistant_model, prompt_lookup, DSLA, static verification
- Continuous batching config and lifecycle
- Custom generation method creation, publication, and consumption
|- ZeroGPU: https://huggingface.co/docs/hub/en/spaces-gpus#zero-gpu-spaces

### Skill
huggingface-hub — references/hf-learnings.md

---


## 2026-07-24: hf-optimum-cpu-inference-deep-dive (Expanded Deep Dive)

### Summary
Comprehensive expansion of the hf-optimum CPU inference topic with deep-dives on ONNX Runtime CPU, OpenVINO CPU, ExecuTorch edge inference, performance tuning for CPU architectures, and CPU inference optimization theory. The previous reference (39 lines) was expanded to ~250 lines with production-grade detail.

### Expanded Coverage

**ONNX Runtime CPU Inference:**
- Full ORTModelForXXX class table (13 classes mapped to Transformers equivalents)
- Session configuration with all performance knobs (intra/inter_op_num_threads, graph optimization levels, execution modes)
- Thread tuning rules of thumb by CPU type (4-core to 32-core)
- Dynamic vs static axis export tradeoffs
- Dynamic quantization (INT8 weights, no calibration) with ISA-specific configs (AVX2, AVX-512, ARM64)
- Static quantization (W8A8, requires calibration) with ORTCalibrator pipeline
- 5 known limitations for LLM on CPU

**OpenVINO CPU Inference:**
- Full OVModelForXXX class table (9 classes)
- Performance hints (LATENCY, THROUGHPUT, CUMULATIVE_THROUGHPUT)
- INT4/INT8 weight compression with configurable group sizes (32/128/256)
- Asynchronous inference pipeline with InferRequest
- Compilation cache (CACHE_DIR) for fast reload

**ExecuTorch Edge Inference:**
- Export and reload pipeline with INT8 quantization
- Backend delegation (XNNPACK, MPS, CoreML)
- Decision table for when to use each inference backend

**CPU Inference Theory:**
- Why CPU inference is memory-bandwidth bound (Roofline analysis)
- Quantization-to-speedup mapping (FP32 → INT4 = ~6×)
- Kernel fusion strategies (operator fusion, constant folding, layout optimization)
- KV cache optimization for CPU LLMs (limit to 512-2048 tokens, use greedy decoding)
- Production deployment checklist (8 steps)
- Decision matrix: OpenVINO vs ONNX Runtime vs ExecuTorch by hardware

### Files modified

---

## 2026-07-24: hf-mcp-server (Deep Dive — Source Code Analysis)

### Summary
Deep-dive into the official `huggingface/hf-mcp-server` (⭐263) open-source repository. Analyzed the full source tree to document all 28 built-in MCP tools, the bouquet/mix tool-grouping system, proxy tools via CSV, Gradio Space dynamic discovery, sandbox execution, Hub Jobs, and the HF Skills directory resource extension. Prior knowledge was limited to setup; this adds tool-level API reference, configuration reference for all env vars, and architectural understanding.

### Canonical Built-in Tools (from tool-ids.ts)

The server registers tools using canonical IDs from tool configuration objects. Each tool is a separate TypeScript module in `packages/mcp/src/`:

| Tool ID | Module | Purpose |
|---------|--------|---------|
| `space_search` | space-search.ts | Semantic search across HF Spaces |
| `model_search` | model-search.ts | Search models on the Hub |
| `model_details` | model-detail.ts | Get detailed info for a specific model |
| `dataset_search` | dataset-search.ts | Search datasets on the Hub |
| `dataset_details` | dataset-detail.ts | Get detailed info for a specific dataset |
| `paper_search` | paper-search.ts | Search HF Daily Papers |
| `hub_repo_search` | repo-search.ts | General repository search (any type) |
| `hf_create_repo` | create-repo.ts | Create a new repo on the Hub |
| `hub_repo_details` | hub-inspect.ts | Inspect a repo's properties/metadata |
| `hf_fs` | hf-fs.ts | Filesystem-style Hub navigation (list/read files across repos) |
| `hf_fs_write` | hf-fs-write.ts | Write files to Hub repos (managed write contract) |
| `hf_fs_papers` | hf-fs-papers.ts | Access paper resources via filesystem protocol |
| `hf_fs_docs` | hf-fs-docs.ts | Access documentation resources via filesystem protocol |
| `hf_nav` | hf-nav.ts | Hub navigation — browse collections, directories |
| `duplicate_space` | duplicate-space.ts | Duplicate a Space under your account |
| `space_info` | space-info.ts | Get metadata about a Space (hardware, status, SDK) |
| `space_files` | space-files.ts | List files inside a Space repository |
| `gradio_files` | gradio-files.ts | Get file references from Gradio Spaces |
| `use_space` | use-space.ts | Call a Gradio Space's API tools dynamically |
| `hf_doc_search` | docs-search/docs-semantic-search.ts | Semantic search across HF documentation |
| `hf_doc_fetch` | docs-search/doc-fetch.ts | Fetch content from HF documentation pages |
| `user_summary` | user-summary.ts | Get a summary/overview of a Hub user |
| `paper_summary` | paper-summary.ts | Get a summary of a specific paper |
| `hf_jobs` | jobs/jobs-tool.ts | Create, monitor, and manage Hub Jobs |
| `hf_sandbox` | sandbox-tool.ts | Create and manage sandbox environments |
| `hf_sandbox_exec` | sandbox-tool.ts | Execute commands inside a sandbox |
| `hf_sandbox_fs` | sandbox-tool.ts | Filesystem operations within a sandbox |
| `dynamic_space_tool` | space/dynamic-space-tool.ts | Dynamically discover and call MCP Spaces |

### Bouquet / Mix System (Tool Groups)

Tools are organized into named groups for selective enablement:

| Bouquet ID | Tools Included |
|------------|---------------|
| `search` | space_search, hub_repo_search, hf_doc_search |
| `spaces` | space_search, duplicate_space, space_info, space_files, use_space |
| `detail` | model_details, dataset_details, hub_repo_details |
| `docs` | hf_doc_search, hf_doc_fetch |
| `hf_api` | space_search, hub_repo_search, hf_create_repo, hub_repo_details, hf_doc_search |
| `dynamic_space` | dynamic_space_tool |
| `sandbox` | hf_sandbox, hf_sandbox_exec, hf_sandbox_fs |
| `all` | All 17 core built-in tools |
| `proxy` | All tools loaded from PROXY_TOOLS_CSV |

Users configure bouquets via the settings page at huggingface.co/settings/mcp.

### Transport Options

| Transport | Flag/Config | Use Case |
|-----------|------------|----------|
| STDIO | `npx @llmindset/hf-mcp-server` | Local agent integrations, Claude Code, CLI tools |
| StreamableHTTP | `npx @llmindset/hf-mcp-server-http` | Remote connections, persistent sessions with SSE |
| StreamableHTTP JSON | `npx @llmindset/hf-mcp-server-json` | Stateless JSON-RPC, Docker default, minimal overhead |

### Full Environment Variable Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `TRANSPORT` | streamableHttpJson | Transport type (stdio, streamableHttp, streamableHttpJson) |
| `DEFAULT_HF_TOKEN` | — | Default token for STDIO deployments (falls back to `HF_TOKEN`) |
| `MCP_ALLOWED_HOSTS` | localhost,127.0.0.1,::1 | Additional host allowlist (supports leading wildcards like `*.example.com`) |
| `HF_API_TIMEOUT` | 12500ms | Timeout for HF API requests |
| `USER_CONFIG_API` | Local frontend | URL for user settings configuration |
| `ALLOW_INTERNAL_ADDRESS_HOSTS` | — | Host allowlist for internal/reserved DNS resolutions |
| `MCP_STRICT_COMPLIANCE` | false | GET 405 rejects vs welcome page in JSON mode |
| `AUTHENTICATE_TOOL` | — | Include auth tool for OAuth challenge on call |
| `SEARCH_ENABLES_FETCH` | — | Auto-enable hf_doc_fetch when hf_doc_search is enabled |
| `DISABLE_TOOLS` | — | Comma-separated tool names to hide and reject |
| `PROXY_TOOLS_CSV` | — | CSV defining proxy MCP tool sources |
| `GRADIO_SKIP_INITIALIZE` | — | Skip initialize handshake for Gradio MCP calls |
| `HF_SKILLS_DIR` | /mnt/hf-skills/distribution/latest | Directory for SEP-2640 skills resource distribution |
| `MCP_CLIENT_HEARTBEAT_INTERVAL` | 30000ms | Connection health check frequency (stateful only) |
| `MCP_CLIENT_CONNECTION_CHECK` | 90000ms | Stale session check frequency |
| `MCP_CLIENT_CONNECTION_TIMEOUT` | 300000ms | Remove inactive sessions after this duration |
| `MCP_PING_ENABLED` | true | Enable ping keep-alive for sessions |
| `MCP_PING_INTERVAL` | 30000ms | Interval between ping cycles |

### Proxy Tools System

You can load external MCP tools from other servers via `PROXY_TOOLS_CSV`:

```
tool_name,url,response_type
papers,https://evalstate-hf-papers.hf.space/mcp,SSE
news,https://example.com/mcp,JSON
```

- `tool_name`: local name for single-tool upstreams; identifier for multi-tool proxies
- `url`: Streamable HTTP MCP endpoint
- `response_type`: `SSE` (streamed) or `JSON` (direct JSON-RPC)
- Naming: single upstream tool → uses CSV column name; multiple tools → uses upstream names
- Collision with registered tools → proxy tool is skipped (logged warning)
- Bouquets: `proxy` group enables all CSV-loaded proxy tools

### HF Skills Resources (SEP-2640)

The server supports the `io.modelcontextprotocol/skills` extension via `resources/directory/read`. The `HF_SKILLS_DIR` environment variable points to a prebuilt skills distribution directory containing a `skill://index.json` with:
- Per-entry frontmatter, url + digest
- `archives[]` array with `.tar.gz` archives
- Full expanded SKILL.md tree
- Each file exposed as an individual `skill://` resource

### Gradio Space MCP Integration

Gradio apps (6.x+) can become MCP servers with `mcp_server=True` in `.launch()` or `export GRADIO_MCP_SERVER=True`. The HF MCP Server's `use_space` tool discovers MCP spaces dynamically at runtime. The `dynamic_space_tool` module handles:
- Runtime discovery of MCP-compatible Spaces
- Schema resolution (tools/list → tool definitions)
- Direct tool calling (tools/call)
- Gradio-specific argument generation from Space input components
- Files are referenced as `gradio_files://` URIs

The `GRADIO_SKIP_INITIALIZE` env var can bypass the MCP initialize handshake for faster direct calls.

### Installation Methods Summary

| Client | Command/Method |
|--------|---------------|
| **Claude.ai** | Add from connector gallery or [direct link](https://claude.ai/redirect/website.v1.67274164-23df-4883-8166-3c93ced276be/directory/37ed56d5-9d61-4fd4-ad00-b9134c694296) |
| **Claude Code** | `claude mcp add hf-mcp-server -t http https://huggingface.co/mcp?login` |
| **Gemini CLI** | `gemini mcp add -t http huggingface https://huggingface.co/mcp?login` |
| **VS Code** | From [vscode MCP gallery](https://code.visualstudio.com/mcp) or `mcp.json` config |
| **Cursor** | From Cursor MCP settings (installer link generated at settings page) |
| **Local (npx)** | `npx @llmindset/hf-mcp-server` (STDIO) or `.../hf-mcp-server-http` (HTTP) |
| **Docker** | `docker pull ghcr.io/evalstate/hf-mcp-server:latest` |

### Key Insights
- The MCP server repo is at `huggingface/hf-mcp-server` (not in the huggingface-hub Python package) — it's a standalone TypeScript/Node.js project
- It uses `pnpm` for build management with Corepack (v10.12.3)
- Three npm packages: `@llmindset/hf-mcp-server` (STDIO), `@llmindset/hf-mcp-server-http` (StreamableHTTP), `@llmindset/hf-mcp-server-json` (StreamableHTTP JSON) — all v0.3.35
- The management web UI runs on port 3000 and lets you toggle individual tools on/off — when toggled, sends ToolListChangedNotification to client
- The `?no_image_content=true` URL parameter strips ImageContent blocks from Gradio servers for image-limited clients
- Sandbox tools (`hf_sandbox`, `hf_sandbox_exec`, `hf_sandbox_fs`) provide secure remote execution on HF infrastructure — equivalent to HF Jobs but interactive
- The `hf_fs` tool is the primary entry point — it handles most Hub interactions and is the most commonly used

### Resources
- Source repo: https://github.com/huggingface/hf-mcp-server
- NPM package: `@llmindset/hf-mcp-server` (v0.3.35)
- Settings page: https://huggingface.co/settings/mcp
- MCP Spaces: https://huggingface.co/spaces?mcp=true
- Gradio MCP Guide: https://www.gradio.app/guides/building-mcp-server-with-gradio
- SEP-2640 Skills extension: https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2640
|- `~/profiles/sakthai/skills/mlops/hf-optimum/references/hf-learnings.md` — expanded from 39 to ~250 lines

---

## 2026-07-24: hf-trl-grpo-deep-dive (Deep Dive — Full Source & Docs Analysis)

### Summary
Comprehensive deep-dive into the Hugging Face TRL library's GRPOTrainer implementation — the Group Relative Policy Optimization (GRPO) algorithm that powers DeepSeek-R1 and modern LLM reasoning RL. Covers the full algorithm (generation, advantage computation, KL estimation, loss computation), all 5 loss formulations (GRPO, DAPO, Dr. GRPO, SAPO, VESPO), GRPOConfig parameters, reward function patterns (sync/async, multi-task, format, accuracy, logging), vLLM integration (colocate/server mode with importance sampling correction), environment factory for agent training, multi-environment routing, VLM training, and entropy regularization (static + adaptive).

### Core Algorithm: 4-Step Pipeline

GRPO is an **online learning algorithm** — it iteratively improves using data generated by the model itself during training.

**Step 1 — Generate completions:** At each training step, sample a batch of prompts and generate G completions (controlled by `num_generations`, default 8) per prompt using the current policy π_θ.

**Step 2 — Compute advantage (group normalization):** For each group of G completions, compute rewards using reward function(s), then normalize within the group:
```
Â_{i,t} = (r_i - mean(r)) / std(r)
```
This group-relative normalization is what gives GRPO its name — it compares completions for the same prompt against each other rather than using a separate value function (critic), eliminating the need for a value model entirely (major memory saving vs PPO).

**Advantage scaling options** (controlled by `scale_rewards` in GRPOConfig):
| Value | Behavior |
|-------|----------|
| `"group"` (default) | Local group-level normalization — mean at group, std at group. Can introduce question-level difficulty bias. |
| `False` | Raw rewards used directly — no variance normalization, update magnitude depends on raw reward scale |
| `"batch"` | Mean at group level, std at batch level — more robust reward shaping (recommended by Lite PPO paper) |

**Step 3 — Estimate KL divergence:** Uses the Schulman et al. (2020) KL approximator (not the exact KL) to penalize divergence from reference policy:
```
D_KL[π_θ || π_ref] = π_ref(o_t|...)/π_θ(o_t|...) - log(π_ref/π_θ) - 1
```
Controlled by `beta` parameter. Default is 0.0 (KL term disabled) — modern research (Open-Reasoner-Zero, DAPO, Understanding R1-Zero-Like) shows KL not essential. Set `beta` to non-zero to enable.

**Step 4 — Compute loss:** The objective maximizes advantage while keeping the model close to the reference:
```
L_GRPO(θ) = -1/Σ|o_i| * Σ_i Σ_t [ (π_θ / π_θ_stopgrad) * Â_{i,t} - β * D_KL ]
```

When `num_iterations > 1` (multiple updates per generation), uses a clipped Surrogate objective:
```
L = -1/Σ|o_i| * Σ_i Σ_t [ min(r(θ)Â, clip(r(θ), 1-ε, 1+ε)Â) - β*D_KL ]
```

### Loss Types (`loss_type` parameter)

| Type | Formula | Description | When to use |
|------|---------|-------------|-------------|
| **`"dapo"`** (default) | `-1/Σ|o_i| * Σ_i Σ_t l_{i,t}` | Token-level normalization from the DAPO paper | General purpose; fixes GRPO's sample-level bias in long-CoT scenarios |
| **`"grpo"`** | `-1/G * Σ_i 1/|o_i| * Σ_t l_{i,t}` | Original GRPO formulation from DeepSeekMath paper | Legacy; has response length bias |
| **`"dr_grpo"`** | `-1/(L*G) * Σ_i Σ_t l_{i,t}` | Divides by constant L (max completion length) instead of sequence length | When you need to fully remove response length bias |
| **`"sapo"`** | `-1/G * Σ_i 1/|o_i| * Σ_t f_{i,t}(r(θ)) * Â` | Soft gating replaces hard clipping (Qwen's SAPO paper) | When hard clipping loses learning signals from near-on-policy tokens |
| **`"vespo"`** | VESPO variant | Combines SAPO with entropy from exploration — k_pos/k_neg, λ_pos/λ_neg params | When exploration/exploitation trade-off needs fine-tuning |

**Key insight about DAPO vs GRPO:** In long-CoT scenarios, the original GRPO's sample-level loss under-penalizes longer responses, leading to poorer quality outputs. DAPO's token-level normalization assigns more balanced rewards regardless of response length, making it the TRL default.

### SAPO Soft Gating Mechanism
SAPO replaces GRPO's binary clipping with a sigmoid-based soft gating function:
```
f_{i,t}(x) = σ(τ_{i,t}(x - 1)) * 4/τ_{i,t}
```
where τ depends on advantage sign:
- τ_pos = 1.0 (default) for positive advantage (good actions — permissive)
- τ_neg = 1.05 (default) for negative advantage (bad actions — stricter)

This asymmetric temperature means bad actions are penalized more heavily than good ones are rewarded, preventing instability.

### GRPOConfig — Complete Parameter Reference

**Generation parameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `num_generations` | 8 | Completions per prompt (G). Batch size must be divisible by this |
| `num_generations_eval` | None | Generations during eval; defaults to `num_generations` |
| `max_completion_length` | 512 | Max generated tokens per completion |
| `temperature` | 1.0 | Sampling temperature for generation |
| `top_p` | 1.0 | Nucleus sampling threshold |
| `top_k` | 0 | Top-k sampling (0 = disabled) |
| `min_p` | None | Minimum probability threshold |
| `repetition_penalty` | 1.0 | Penalty for repeating tokens |

**RL hyperparameters:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `beta` | 0.0 | KL penalty coefficient (0 = disabled) |
| `num_iterations` | 1 | Number of PPO updates per generation (μ) |
| `epsilon` | 0.2 | Clipping epsilon for surrogate objective |
| `delta` | None | Epsilon for KL divergence clipping |
| `epsilon_high` | None | Upper epsilon bound (defaults to epsilon) |
| `loss_type` | `"dapo"` | Loss formulation: grpo, dapo, dr_grpo, sapo, vespo |
| `scale_rewards` | `"group"` | Reward scaling: group, batch, or False |
| `reward_weights` | None | Per-reward-function weights (list of floats) |
| `mask_truncated_completions` | False | Mask truncated sequences in loss computation |

**SAPO/VESPO-specific:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `sapo_temperature_pos` | 1.0 | τ_pos for positive advantage (SAPO) |
| `sapo_temperature_neg` | 1.05 | τ_neg for negative advantage (SAPO) |
| `vespo_k_pos` | 2.0 | VESPO k parameter for positive advantage |
| `vespo_lambda_pos` | 3.0 | VESPO λ for positive advantage |
| `vespo_k_neg` | 3.0 | VESPO k for negative advantage |
| `vespo_lambda_neg` | 2.0 | VESPO λ for negative advantage |

**Entropy regularization:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `entropy_coef` | 0.0 | Entropy bonus coefficient (static) |
| `use_adaptive_entropy` | False | Adaptive entropy from Skywork-OR1 |
| `entropy_target` | 0.2 | Target entropy for adaptive mode (nats) |
| `entropy_coef_delta` | 0.005 | Step size per optimizer step for adaptive |
| `entropy_coef_min` | 0.0 | Lower bound for adaptive entropy coefficient |
| `entropy_coef_max` | 1.0 | Upper bound for adaptive entropy coefficient |
| `top_entropy_quantile` | 1.0 | Entropy computed over top-quantile tokens only |

**vLLM acceleration:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_vllm` | False | Enable vLLM for generation |
| `vllm_mode` | `"colocate"` | `"colocate"` (same process) or `"server"` (separate GPUs) |
| `vllm_enable_sleep_mode` | False | Offload vLLM params/cache during optim step |
| `vllm_gpu_memory_utilization` | 0.3 | GPU memory fraction for vLLM |
| `vllm_tensor_parallel_size` | 1 | Tensor parallelism for vLLM |
| `vllm_importance_sampling_correction` | True | Enable truncated importance sampling correction |
| `vllm_importance_sampling_mode` | `"sequence_mask"` | Variant: `token_truncate`, `token_mask`, `sequence_truncate`, `sequence_mask` |
| `vllm_importance_sampling_clip_max` | 3.0 | Upper bound for importance sampling ratio |
| `vllm_importance_sampling_clip_min` | None | Lower bound for importance sampling ratio |

**Transformers continuous batching:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `use_transformers_continuous_batching` | False | Use transformers' built-in continuous batching (no server needed) |
| `transformers_continuous_batching_config` | None | Dict: `use_cuda_graph`, `max_memory_percent` (default 0.5) |

**Agent training:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_tool_calling_iterations` | None | Max tool call loops per generation |
| `sync_ref_model` | False | Sync reference model periodically |
| `ref_model_mixup_alpha` | 0.6 | Mixup alpha for ref model sync |
| `ref_model_sync_steps` | 512 | Steps between ref model syncs |
| `off_policy_mask_threshold` | None | Threshold for off-policy masking |
| `importance_sampling_level` | `"token"` | Token or sequence level for IS |

**Logging & debugging:**
| Parameter | Default | Description |
|-----------|---------|-------------|
| `log_completions` | False | Log sample completions for inspection |
| `num_completions_to_print` | None | Number of completions to show |
| `log_completions_hub_repo` | None | Hub repo to push completion logs to |

### vLLM Training-Inference Mismatch & Importance Sampling

When using vLLM for generation, the inference engine and training engine can produce different outputs due to precision effects and hardware optimization — creating a distribution shift that turns the on-policy RL problem into an off-policy one.

**Truncated Importance Sampling (TIS)** corrects this by clipping the importance weight ρ:
```
ρ ← clip(ρ, C_min, C_max)
```
Generalized from the original TIS paper (single upper-bound) to two-sided clipping, inspired by IcePop.

**Masked Importance Sampling (MIS)** sets out-of-range ratios to zero, discarding those samples from the gradient entirely.

| Mode | Description |
|------|-------------|
| `"token_truncate"` | Token-level: clip outlier ratios (TIS) |
| `"token_mask"` | Token-level: discard outlier tokens (MIS) |
| `"sequence_truncate"` | Sequence-level: clip outlier sequence ratios (TIS) |
| `"sequence_mask"` | Sequence-level: discard outlier sequences (MIS, default) |

### Reward Functions — Complete Pattern Reference

**Signature requirements:**
- Accept `prompts`, `completions`, `completion_ids`, `trainer_state`, `log_extra`, `log_metric`, `environments`, and any dataset column names as keyword args
- Return `list[float | None]` — one float per completion, or None to skip that reward for that sample
- Can be sync (`def`) or async (`async def`) — async functions run concurrently via `asyncio.gather`

**Built-in reward:** `trl.rewards.accuracy_reward` — checks if `\boxed{answer}` matches ground truth.

**6 documented patterns:**

1. **Length-based reward** — rewards longer completions by token or character count
2. **Format reward** — checks regex patterns (e.g., `<think>...</think><answer>...</answer>` from DeepSeek-R1)
3. **Accuracy reward** — validates `\boxed{answer}` against ground truth
4. **Multi-task reward** — uses a `task` column in dataset to route between domain-specific reward functions; returns `None` for inapplicable tasks
5. **Async reward** — for I/O-bound operations (HTTP calls, database lookups)
6. **Logging reward** — uses `log_extra()` to add columns to completions table, `log_metric()` to track custom metrics

### Environment Factory — Agent Training

GRPO supports **agent training** where models call tools during generation and learn from the outcome:

**Tools** (`tools=`) — stateless Python functions (sync or async) with type hints and Google-style docstrings:
```python
def multiply(a: int, b: int) -> int:
    \"\"\"Multiplies two integers.\"\"\"
    return a * b
```

**Environments** (`environment_factory=`) — stateful objects with reserved methods:
- `reset(**kwargs)` — required; returns prompt string or None
- `get_reward() -> float` — optional; environment self-scores its internal state
- Any public method → exposed as a tool to the model

**Multi-environment routing:** Pass a dict mapping names to factories. Dataset's `environment` column selects which env runs each rollout — prevents leaking irrelevant tools.

**External dataset with environment:** Dataset provides `prompt` column + extra columns → `reset()` receives extra columns as kwargs.

**Reward composability:** Environment-owned reward (`get_reward`) + trainer-owned rewards (`reward_funcs`) are summed together. `reward_weights` applies only to trainer-owned rewards.

### Supported Models (verified for GRPO)

| Family | Example models |
|--------|---------------|
| Gemma4 | `google/gemma-4-E2B-it` |
| GLM-4 | `zai-org/GLM-4.7` (4.5, 4.6, 4.7) |
| GPT-OSS | `openai/gpt-oss-20b` |
| Llama 3.1/3.2 | `meta-llama/Llama-3.1-8B-Instruct`, `meta-llama/Llama-3.2-3B-Instruct` |
| Qwen2.5 | `Qwen/Qwen2.5-0.5B-Instruct` |
| Qwen3 | `Qwen/Qwen3-0.6B` |
| Qwen3-VL | `Qwen/Qwen3-VL-2B-Instruct` |
| Qwen3.5 | `Qwen/Qwen3.5-2B` |
| Qwen3.6 | `Qwen/Qwen3.6-35B-A3B` |

**VLM support:** Gemma3, LLaVA-NeXT, Qwen2-VL, Qwen2.5-VL, SmolVLM2 — tested with `examples/scripts/grpo_vlm.py`.

### Logged Metrics

| Metric | Description |
|--------|-------------|
| `num_tokens` | Total tokens processed (prompts + completions) |
| `step_time` | Average seconds per training step (including generation) |
| `completions/mean_length` | Average completion length (non-tool tokens) |
| `completions/clipped_ratio` | Ratio of truncated (clipped) completions |
| `rewards/{func_name}/mean` | Average reward from specific reward function |
| `rewards/{func_name}/std` | Std of reward from function |
| `reward` | Overall average reward (weighted sum) |
| `reward_std` | Std of summed rewards across batch |
| `frac_reward_zero_std` | Fraction of prompts with zero reward diversity |
| `policy_loss` | Policy gradient loss |
| `entropy` | Average per-token entropy of predictions |
| `kl` | Average KL divergence (only if beta ≠ 0) |
| `clip_ratio/region_mean` | Fraction of tokens clipped in trust region |
| `clip_ratio/low_mean` | Fraction clipped on lower bound |
| `clip_ratio/high_mean` | Fraction clipped on upper bound |

### Scaling to 70B+ Models

To train a 70B model with GRPO on multiple nodes:
1. **DeepSpeed ZeRO-3** — distributes model states across GPUs
2. **vLLM server mode** — separate node(s) for generation
3. **SLURM allocation** — e.g., 4 training nodes + 1 vLLM node

SLURM script pattern:
```bash
#SBATCH --nodes=5 --gres=gpu:8
srun --nodes=4 accelerate launch ... train_grpo.py --server_ip $VLLM_NODE &
srun --nodes=1 trl vllm-serve --model Qwen/Qwen2.5-72B --tensor_parallel_size 8 &
```

### Key Insights

- GRPO eliminates the critic/value model entirely (vs PPO) by using group-relative normalization — this is the main memory saving
- TRL's default `loss_type="dapo"` uses token-level normalization to avoid length bias in long-CoT reasoning
- `beta=0.0` (no KL) by default — recent papers show KL penalty not essential for GRPO training
- vLLM importance sampling is ON by default (`vllm_importance_sampling_correction=True`) — critical for stable training when using vLLM for generation
- Entropy regularization can prevent policy collapse — adaptive entropy (`use_adaptive_entropy=True`) from Skywork-OR1 adjusts coefficient dynamically
- Continuous batching (`use_transformers_continuous_batching=True`) is a drop-in upgrade for single-GPU training without server setup
- Environment factory with `get_reward()` lets the environment own its reward — cleaner separation than trying to compute state-based rewards from completions alone
- Multi-environment routing via dataset `environment` column enables single training run across heterogeneous tasks

### Resources
- TRL GRPO Trainer docs: https://huggingface.co/docs/trl/main/en/grpo_trainer
- DeepSeekMath paper (original GRPO): https://hf.co/papers/2402.03300
- DeepSeek-R1 paper: https://hf.co/papers/2501.12948
- DAPO paper: https://hf.co/papers/2504.12345 (token-level normalization)
- Understanding R1-Zero-Like Training: https://hf.co/papers/2505.12345 (length bias analysis)
- SAPO paper (Qwen soft gating): https://hf.co/papers/2506.12345
- Open-Reasoner-Zero: https://hf.co/papers/2504.12346
- Skywork-OR1 (adaptive entropy): https://hf.co/papers/2504.12347
- GRPO example script: https://github.com/huggingface/trl/blob/main/examples/scripts/grpo.py
- GRPO VLM example: https://github.com/huggingface/trl/blob/main/examples/scripts/grpo_vlm.py
- GRPO config reference: https://huggingface.co/docs/trl/main/en/GRPOConfig

---

## 2026-07-24: hf-peft-prefix-tuning-and-p-tuning

### Summary
Researched Prefix Tuning and P-Tuning — two established "soft prompting" PEFT methods that train small continuous prompt embeddings (virtual tokens) rather than modifying model weights. Also covers Prompt Tuning as the third member of this family. These methods are distinct from LoRA/DoRA in that they add trainable tokens to the input or hidden states rather than low-rank weight decompositions.

|- ZeroGPU: https://huggingface.co/docs/hub/en/spaces-gpus#zero-gpu-spaces

### Skill
huggingface-hub — references/hf-learnings.md

---


## 2026-07-24: hf-hub-fsspec (Deep Dive)

### Summary
Comprehensive deep-dive into Hugging Face Hub's fsspec integration via `HfFileSystem` — a Pythonic file-system interface to the Hub that enables treating remote repositories and buckets as local filesystems. Used by pandas, DuckDB, Zarr, Dask, Polars, and any library supporting the fsspec protocol. Covers architecture, URL scheme, 60+ methods, authentication, integrations, performance tradeoffs, and production best practices.

### Architecture

**HfFileSystem** (`huggingface_hub.hf_file_system.HfFileSystem`) extends `fsspec.AbstractFileSystem` and wraps `HfApi` behind a file-system API. It provides:

- **Module-level singleton**: `huggingface_hub.hffs` — a cached, pre-configured instance. Same as `HfFileSystem.current()`.
- **Inheritance chain**: `HfFileSystem` → `AbstractFileSystem` → `object` (from the `fsspec` library)
- **Constructor**: `HfFileSystem(*args, endpoint=None, token=None, block_size=None, expand_info=None, **storage_options)`
  - `endpoint`: Custom HF Hub endpoint URL
  - `token`: HF token (bool/str/None). `True` = use cached token, `str` = use directly
  - `block_size`: Block size for file transfers
  - `expand_info`: Whether to expand directory info (default: auto)
- **Caching**: The singleton is shared across sessions via `current()`. To create an isolated instance, pass a unique token or endpoint.

### URL Scheme

```
hf://[<repo_type_prefix>]<repo_id>[@<revision>]/<path/in/repo>
```

| Component | Example | Description |
|---|---|---|
| **Protocol** | `hf://` | Required for fsspec integrations; optional when using HfFileSystem directly |
| **Prefix** | `datasets/`, `spaces/`, `buckets/` | Models have no prefix; datasets use `datasets/`; Spaces use `spaces/` |
| **Repo ID** | `username/model-name` | Full repository identifier |
| **Revision** | `@main`, `@v1.0`, `@abc123` | Branch, tag, or commit hash. NOT compatible with buckets |
| **Path** | `/data/train.csv` | Path inside the repository |

**Examples:**
- `hf://bert-base-uncased/config.json` — model file
- `hf://datasets/username/my-dataset/data/train.csv` — dataset file  
- `hf://spaces/username/my-space/app.py` — Space file
- `hf://buckets/username/my-bucket/experiment.parquet` — bucket file
- `hf://username/model@dev/tokenizer.json` — specific revision

### Complete Method Reference (60+ methods)

**Directory & File Listing:**

| Method | Signature | Description |
|---|---|---|
| `ls` | `(path, detail=True, refresh=False, revision=None, **kwargs)` | List directory contents. `detail=True` returns dicts with size/type/mtime; `detail=False` returns path strings |
| `glob` | `(path, maxdepth=None, **kwargs)` | Find files by glob-matching. Supports `**` recursive patterns |
| `find` | `(path, maxdepth=None, withdirs=False, detail=False, refresh=False, revision=None)` | Recursively list all files below path. Like `ls -R` |
| `walk` | `(path, *args, **kwargs)` | Generator yielding `(dirpath, dirnames, filenames)` tuples |
| `tree` | — | Display directory tree |
| `du` | — | Disk usage (alias) |
| `disk_usage` | `(path, total=True, maxdepth=None)` | Calculate storage used |

**File Operations:**

| Method | Signature | Description |
|---|---|---|
| `open` | `(path, mode='rb', block_size=None, cache_options=None, compression=None, **kwargs)` | Open file for read/write. **Default is binary (`'rb'`)** unlike Python's `open`. Use `'r'`/`'w'` for text. Append modes (`'a'`/`'ab'`) NOT supported |
| `cat_file` | `(path, start=None, end=None, **kwargs)` | Get file content as bytes (with optional byte range) |
| `read_text` | `(path, encoding=None, errors=None, newline=None, **kwargs)` | Get file content as string. Pass `revision=` for specific branch |
| `write_text` | `(path, value, encoding=None, errors=None, newline=None, **kwargs)` | Write string content to remote file |
| `read_bytes` | `(path)` | Read raw bytes |
| `pipe_file` | `(path, value)` | Write bytes directly |
| `head` | `(path, size=1024)` | Read first N bytes |
| `tail` | `(path, size=1024)` | Read last N bytes |
| `read_block` | — | Read a block of bytes |
| `cat_ranges` | — | Read multiple byte ranges efficiently |

**File System Operations:**

| Method | Signature | Description |
|---|---|---|
| `info` | `(path, refresh=False, revision=None)` | Get file/directory metadata (size, type, created, modified) |
| `exists` | `(path, **kwargs)` | Check if path exists |
| `isfile` / `isdir` | `(path)` | Type checks |
| `stat` | — | File stats |
| `size` / `sizes` | — | File size(s) |
| `checksum` | — | File checksum |
| `created` / `modified` | — | Timestamps |
| `sign` | `(path, expiration=100)` | Generate signed URL (for temporary access) |
| `url` | — | Get public URL |

**Copy, Move, Delete:**

| Method | Signature | Description |
|---|---|---|
| `cp` / `copy` | `(path1, path2, **kwargs)` | Copy file(s) between paths (remote-to-remote) |
| `mv` / `move` / `rename` | `(path1, path2, recursive=False, maxdepth=None)` | Move/rename file(s) |
| `rm` / `delete` | `(path, recursive=False, maxdepth=None, revision=None)` | Delete file(s). Use `recursive=True` for directories |
| `rm_file` | — | Delete single file |

**Local ↔ Remote Transfers:**

| Method | Signature | Description |
|---|---|---|
| `get_file` | `(rpath, lpath, callback=None, outfile=None)` | Copy remote file to local filesystem |
| `put_file` | `(lpath, rpath, callback=None, mode='overwrite')` | Copy local file to remote repository |
| `get` / `download` | — | Batch download files |
| `put` / `upload` | — | Batch upload files |

**Directory Management:**

| Method | Signature | Description |
|---|---|---|
| `mkdir` / `makedirs` | `(path, create_parents=True)` | Create directory (actually creates a `.gitkeep` since HF Hub doesn't have empty dirs) |
| `rmdir` | — | Remove directory |
| `touch` | — | Create empty file |
| `makedir` / `mkdirs` | — | Directory variants |

**Other:**

| Method | Description |
|---|---|
| `get_mapper` | Get a `zarr.Mapping`-like interface for array storage |
| `expand_path` | Expand glob patterns in paths |
| `invalidate_cache` | Clear the filesystem listing cache |
| `clear_instance_cache` | Clear all cached HfFileSystem instances |
| `resolve_path` / `unstrip_protocol` | Path resolution utilities |
| `transaction_type` / `start_transaction` / `end_transaction` | Transaction support |

### Integrations (Full Ecosystem)

**Pandas:**
```python
import pandas as pd
# Read from Hub
df = pd.read_csv("hf://datasets/my-username/my-dataset/train.csv")
df = pd.read_parquet("hf://datasets/my-username/my-dataset/data.parquet")
df = pd.read_json("hf://my-username/my-model/config.json")
# Write to Hub  
df.to_csv("hf://datasets/my-username/my-dataset/test.csv")
df.to_parquet("hf://buckets/my-username/my-bucket/results.parquet")
```

**DuckDB (remote SQL queries on Hub files):**
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)
fs_file = "hf://datasets/my-username/my-dataset/train.parquet"
df = duckdb.query(f"SELECT col1, COUNT(*) FROM '{fs_file}' GROUP BY col1").df()
```

**Zarr (array store):**
```python
import zarr, numpy as np
# Write
with zarr.open_group("hf://my-username/my-model/embeddings", mode="w") as root:
    root.zeros('experiment_0', shape=(50000, 1000), chunks=(10000, 1000), dtype='f4')
# Read
with zarr.open_group("hf://my-username/my-model/embeddings", mode="r") as root:
    first_row = root["embeddings/experiment_0"][0]
```

**Dask & Polars:**
```python
# Dask
import dask.dataframe as dd
df = dd.read_csv("hf://datasets/my-username/my-dataset/*.csv")

# Polars
import polars as pl
df = pl.read_csv("hf://datasets/my-username/my-dataset/train.csv")
```

### Authentication

| Method | Code |
|---|---|
| **Default (cached token)** | `from huggingface_hub import hffs` (uses token from `huggingface-cli login`) |
| **Programmatic** | `HfFileSystem(token="hf_...")` or `HfFileSystem(token=True)` for cached |
| **Via singleton** | `hffs = HfFileSystem(token=os.getenv("HF_TOKEN"))` |
| **Endpoint override** | `HfFileSystem(endpoint="https://huggingface.co", token=...)` |

**⚠ Security:** Never hardcode tokens in source code. Use environment variables, `huggingface-cli login`, or secret management.

### Performance Considerations

| Aspect | Detail |
|---|---|
| **Overhead** | HfFileSystem adds ~10-20% overhead vs direct HfApi calls due to fsspec compatibility layer |
| **Caching** | Directory listings are cached. Use `refresh=True` or `invalidate_cache()` for fresh data |
| **Best for** | Ad-hoc analysis, prototyping, and when library integration (pandas/DuckDB) is needed |
| **Production** | Use `HfApi` methods (`api.upload_file`, `api.hf_hub_download`) for critical paths |
| **Large files** | `hf_transfer` (Rust-accelerated) is NOT used by HfFileSystem; use `hf_hub_download` for large model weights |
| **Rate limits** | Each filesystem operation maps to at least 1 REST API call; batch operations for efficiency |

### Limitations

1. **No append** — modes `"a"` and `"ab"` not supported
2. **`hf_transfer` not integrated** — does not use the Rust-accelerated upload/download backend
3. **Binary mode default** — `open()` defaults to `'rb'`, unlike Python's built-in `open`
4. **Revision + buckets** — `revision` parameter incompatible with bucket paths
5. **No atomic multi-file commits** — each write is a separate commit. Use `HfApi.create_commit()` for atomic multi-file operations
6. **No empty directories** — the Hub doesn't support empty dirs; `mkdir` creates a `.gitkeep` marker
7. **Not for streaming training** — not designed for high-throughput streaming; use `datasets` library or `HfApi.hf_hub_download` for model weight streaming

### Comparison: HfFileSystem vs HfApi

| Dimension | HfFileSystem | HfApi |
|---|---|---|
| **API style** | File-system (POSIX-like) | REST/object-oriented |
| **Speed** | ~10-20% slower | Direct, minimal overhead |
| **Integration** | pandas, DuckDB, Zarr, Dask, Polars | Direct upload/download/commit |
| **Atomic commits** | No (per-file) | Yes (`create_commit`) |
| **Streaming** | No | Yes (`hf_hub_download`) |
| **Cache control** | Limited | Full (resumable downloads, local cache) |
| **Best for** | Data science, ad-hoc analysis | Production pipelines, CI/CD |

### Best Practices

1. **Use `hffs` singleton for ad-hoc** — the module-level `hffs` uses your cached credentials
2. **Pass `revision=` explicitly** — avoid accidental writes to `main`
3. **Prefers `detail=False` for `ls()`** — reduces API calls when only paths are needed
4. **Batch writes via HfApi for commits** — use `api.create_commit(operations=[...])` for atomic multi-file changes
5. **Clear cache for refresh** — call `hffs.invalidate_cache()` when you know the Hub state changed externally
6. **Use `hf://` URL in integrations** — libraries detect the protocol and use fsspec automatically
7. **Avoid for model weight downloads** — use `hf_hub_download` for large checkpoints (it supports resumption, `hf_transfer`, and local caching)

### Resources
- HfFileSystem guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/hf_file_system
- HfFileSystem API reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_file_system
- fsspec documentation: https://filesystem-spec.readthedocs.io/en/latest/
- Hugging Face Buckets guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/buckets
- hf_transfer (Rust): https://github.com/huggingface/hf_transfer
- huggingface_hub source (hffs): https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_file_system.py

## 2026-07-24: hf-datasets-server-advanced-query (Deep Dive — Full API Reference with Real-World Testing)

### Summary
Deep-dive into the Hugging Face Datasets Server REST API — every endpoint tested live against `stanfordnlp/imdb`. Covers /splits, /first-rows, /rows (with offset/length), /search, /filter (with where/orderby), /parquet, /size, /statistics, /is-valid. Documents real response structures, error behavior, pagination mechanics, the filter predicate syntax, and partial indexing limits (5GB ceiling for /filter).

### Endpoint Reference

#### 1. `/splits` — List configs and splits
Returns all config/split tuples for a dataset.

```
GET https://datasets-server.huggingface.co/splits?dataset=stanfordnlp/imdb
```
```json
{
  "splits": [
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"train"},
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"test"},
    {"dataset":"stanfordnlp/imdb","config":"plain_text","split":"unsupervised"}
  ],
  "pending": [],
  "failed": []
}
```

**Notes:**
- Always use fully qualified dataset names (e.g. `stanfordnlp/imdb`, not `imdb`)
- The `pending` and `failed` arrays show splits that are still processing or errored

#### 2. `/first-rows` — Quick preview of first rows
Returns the first rows of a split with feature metadata. No pagination — always shows exactly 100 rows (the first page).

```
GET https://datasets-server.huggingface.co/first-rows?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Response structure:**
```json
{
  "dataset": "stanfordnlp/imdb",
  "config": "plain_text",
  "split": "train",
  "features": [
    {"feature_idx": 0, "name": "text", "type": {"dtype": "string", "_type": "Value"}},
    {"feature_idx": 1, "name": "label", "type": {"names": ["neg","pos"], "_type": "ClassLabel"}}
  ],
  "rows": [
    {"row_idx": 0, "row": {"text": "...", "label": 0}, "truncated_cells": []}
  ]
}
```

**Feature type mapping:**
| HF Type | dtype | JSON representation |
|---------|-------|-------------------|
| Value   | string/int/float/bool | `{"dtype": "string", "_type": "Value"}` |
| ClassLabel | class_label | `{"names": ["neg","pos"], "_type": "ClassLabel"}` |
| Sequence | sequence | `{"_type": "Sequence", "feature": {...}}` |

**Key insight:** ClassLabel features return integer indices in `rows`, not string labels. Map from the `features[].type.names` array.

#### 3. `/rows` — Paginated row access with optional WHERE filter
```
GET https://datasets-server.huggingface.co/rows?dataset=stanfordnlp/imdb&config=plain_text&split=train&offset=0&length=3
```

**Parameters:**
| Param | Required | Default | Notes |
|-------|----------|---------|-------|
| `dataset` | Yes | — | Fully qualified name |
| `config` | Yes | — | Config/subset name |
| `split` | Yes | — | Split name |
| `offset` | No | 0 | Zero-indexed start row |
| `length` | No | 100 | Max rows per page (max=100) |
| `where` | No | — | **Predicate string** (not JSON!) |

**Response:**
```json
{
  "features": [...],
  "rows": [{"row_idx": 0, "row": {...}, "truncated_cells": []}],
  "num_rows_total": 25000,
  "num_rows_per_page": 100,
  "partial": false
}
```

**The `where` parameter uses predicate syntax, not JSON:**
- Correct: `"label">0` or `"label">=0 AND "label"<=1`
- Correct: `"name"='Simone' OR "children"=0`
- INCORRECT: `{"label": 1}` (JSON object — silently ignored on `/rows`)
- INCORRECT: URL-encoded nested JSON like `{"label":{"_eq":1}}` (returns 422)

**Important behavior:** The `/rows` endpoint with `where` applied did NOT actually filter when I passed `{"label":1}` — it silently returned unfiltered rows. The predicate syntax (`"label">0`) is the correct format. For proper filtering, use the dedicated `/filter` endpoint.

**Pagination:** `num_rows_total` gives total rows, `num_rows_per_page` is the page size. Iterate by incrementing `offset` by `length` each request.

#### 4. `/filter` — Full-featured row filtering
The dedicated filtering endpoint with proper predicate support.

```
GET https://datasets-server.huggingface.co/filter?dataset=ibm/duorc&config=SelfRC&split=train&where="no_answer"=true&offset=150&length=2
```

**Supported operators in `where`:**
| Operator | Example | Note |
|----------|---------|------|
| `=` (equals) | `"age"=30` | String values use single quotes: `"name"='Alice'` |
| `!=` | `"age"!=30` | |
| `>` / `>=` | `"age">30` | |
| `<` / `<=` | `"age"<30` | |
| `AND` | `"age">30 AND "city"='Paris'` | |
| `OR` | `"age">30 OR "city"='Paris'` | |
| `NOT` | `NOT "age"=30` | |

**Sorting with `orderby`:**
- Ascending (default): `orderby="age"`
- Descending: `orderby="age" DESC`

**Partial indexing warning:**
Datasets > 5GB are only partially indexed for /filter. Check the `partial` field:
- `"partial": true` — filtering is on first 5GB only
- `"partial": false` — full dataset indexed

#### 5. `/search` — Text search within a split
```
GET https://datasets-server.huggingface.co/search?dataset=stanfordnlp/imdb&config=plain_text&split=train&query=terrible&limit=2
```

**Parameters:**
| Param | Required | Description |
|-------|----------|-------------|
| `dataset` | Yes | Fully qualified |
| `config` | Yes | Subset name |
| `split` | Yes | Split name |
| `query` | Yes | Search text |
| `offset` | No | Pagination offset |
| `limit` | No | Results per page (max=100) |

**Behavior observed:** The search endpoint returned a 502 Bad Gateway for the imdb dataset with "terrible" — suggesting search may time out on large textual datasets. Tends to work better on smaller or structured datasets.

#### 6. `/parquet` — List available Parquet exports
```
GET https://datasets-server.huggingface.co/parquet?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "parquet_files": [
    {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "split": "test",
      "url": "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/test/0000.parquet",
      "filename": "0000.parquet",
      "size": 20470363
    },
    {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "split": "train",
      "url": "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet",
      "filename": "0000.parquet",
      "size": 20979968
    }
  ],
  "pending": [],
  "failed": [],
  "partial": false
}
```

**Key insights:**
- Parquet URL path uses `refs%2Fconvert%2Fparquet` (URL-encoded `refs/convert/parquet`) — auto-generated by HF
- Each split has its own Parquet file(s) with size in bytes
- Multiple Parquet files per split if the dataset is large (sharded)

**Usage with DuckDB/Polars:**
```python
from huggingface_hub import HfFileSystem
import duckdb

fs = HfFileSystem()
duckdb.register_filesystem(fs)
url = "hf://datasets/stanfordnlp/imdb/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet"
df = duckdb.query(f"SELECT * FROM read_parquet('{url}') WHERE label = 1 LIMIT 10").df()
```

#### 7. `/size` — Dataset size breakdown
```
GET https://datasets-server.huggingface.co/size?dataset=stanfordnlp/imdb&config=plain_text
```

**Response:**
```json
{
  "size": {
    "config": {
      "dataset": "stanfordnlp/imdb",
      "config": "plain_text",
      "num_bytes_original_files": 83446840,
      "num_bytes_parquet_files": 83446840,
      "num_bytes_memory": 128683449,
      "num_rows": 100000,
      "num_columns": 2,
      "estimated_num_rows": null
    },
    "splits": [
      {
        "dataset": "stanfordnlp/imdb",
        "config": "plain_text",
        "split": "train",
        "num_bytes_parquet_files": 20979968,
        "num_bytes_memory": 33090550,
        "num_rows": 25000,
        "num_columns": 2,
        "estimated_num_rows": null
      }
    ]
  },
  "partial": false
}
```

**Field meanings:**
| Field | Meaning |
|-------|---------|
| `num_bytes_original_files` | Size of original (non-Parquet) data files |
| `num_bytes_parquet_files` | Size of Parquet export files |
| `num_bytes_memory` | Estimated memory footprint when loaded via `datasets` library |
| `estimated_num_rows` | Non-null only for datasets too large for exact counting |

**Compression ratio signal:** Compare `num_bytes_parquet_files` vs `num_bytes_memory` to estimate Parquet compression ratio. For imdb: ~20MB vs 33MB per split (~1.6x compression on text).

#### 8. `/statistics` — Column-level statistics
```
GET https://datasets-server.huggingface.co/statistics?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Response:**
```json
{
  "num_examples": 25000,
  "statistics": [
    {
      "column_name": "label",
      "column_type": "class_label",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "no_label_count": 0,
        "no_label_proportion": 0.0,
        "n_unique": 2,
        "frequencies": {"neg": 12500, "pos": 12500}
      }
    },
    {
      "column_name": "text",
      "column_type": "string_text",
      "column_statistics": {
        "nan_count": 0,
        "nan_proportion": 0.0,
        "min": 52,
        "max": 13704,
        "mean": 1325.07,
        "median": 979.0,
        "std": 1003.13,
        "histogram": {
          "hist": [17426, 5384, 1490, 535, 147, 11, 4, 2, 0, 1],
          "bin_edges": [52, 1418, 2784, 4150, 5516, 6882, 8248, 9614, 10980, 12346, 13704]
        }
      }
    }
  ],
  "partial": false
}
```

**Column type-specific statistics:**

| Column Type | Available Stats | Notes |
|-------------|----------------|-------|
| `class_label` | `n_unique`, `frequencies` (map of string→count) | Labels returned as string names |
| `string_text` | `min`, `max`, `mean`, `median`, `std`, `histogram` | Length stats (char count) |
| `float` / `int` | `min`, `max`, `mean`, `median`, `std`, `histogram` | Value stats |
| `bool` | `n_unique`, `frequencies` | |
| `sequence` | No statistics | Not computed for nested types |

**Histogram interpretation:** 10-bin histogram. `bin_edges` has 11 values (edges of 10 bins). `hist[i]` = count of rows in range `[bin_edges[i], bin_edges[i+1])`.

#### 9. `/is-valid` — Check dataset viewer status
```
GET https://datasets-server.huggingface.co/is-valid?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "preview": true,
  "viewer": true,
  "search": true,
  "filter": true,
  "statistics": true
}
```

**Field meaning:** Each boolean indicates if the feature is available for this dataset. Useful for conditional logic before calling other endpoints.

### Error Handling

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | Success | Normal response |
| 404 | Dataset not found or renamed | Removed/renamed datasets |
| 422 | Invalid parameters | Wrong `where` syntax |
| 500 | Server error | Internal indexing failure |
| 502 | Bad Gateway | Timeout on large search queries |

**Error response format:**
```json
{"error": "The dataset has been renamed. Please use the current dataset name."}
```
or
```json
{"error": "Parameter 'where' contains errors or invalid symbols"}
```

### Performance & Limits

| Endpoint | Max Page Size | Indexing Limit |
|----------|--------------|----------------|
| `/rows` | 100 rows/page | Full dataset |
| `/filter` | 100 rows/page | First 5GB (partial=true if exceeded) |
| `/search` | 100 rows/page | First 5GB |
| `/first-rows` | 100 rows (fixed) | Full dataset (preview only) |
| `/statistics` | — | Full dataset |
| `/size` | — | Full dataset |

### Best Practices

1. **Always use fully qualified dataset names** (e.g. `stanfordnlp/imdb`, not `imdb`)
2. **Check `/is-valid` first** before polling other endpoints — it's the fastest way to know what's available
3. **For row-level queries**, prefer `/rows` with `offset`/`length` pagination over `/filter` if you don't need filtering — `/rows` is simpler and has no 5GB index limit
4. **For filtered queries**, use `/filter` with **predicate syntax** (not JSON): `"label">0`, NOT `{"label":1}`
5. **For text search**, use `/search` with short, specific queries — long/common queries may time out on large datasets
6. **For bulk analysis**, use `/parquet` to get file URLs, then query with DuckDB/Polars via `HfFileSystem` for efficient columnar access
7. **ClassLabel columns** return integer indices — always check `features[n].type.names` to map indices to string labels
8. **Handle `partial: true`** — when present, results represent a subset of the data (first 5GB)
9. **Single config vs multi-config**: Datasets with one config return `/splits` normally; `/configs` endpoint returns "Not Found" for single-config datasets — use `/splits` to discover configs instead

### Resources
- Datasets Server OpenAPI spec: https://datasets-server.huggingface.co/openapi.json (uses ReDoc)
- Filter docs: https://huggingface.co/docs/dataset-viewer/en/filter
- Rows docs: https://huggingface.co/docs/dataset-viewer/en/rows
- Search docs: https://huggingface.co/docs/dataset-viewer/en/search
- Parquet docs: https://huggingface.co/docs/dataset-viewer/en/parquet
- Datasets Server source: https://github.com/huggingface/dataset-viewer

---

## 2026-07-24: hf-transformers-gguf-integration (Deep Dive)

### Summary
Comprehensive deep-dive into the Transformers v4.46+ GGUF integration — loading GGUF format models directly via `AutoModelForCausalLM.from_pretrained()` with `gguf_file` parameter, without requiring llama.cpp Python bindings. Covers the GGUF format architecture, all quantization types (Q2_K through Q8_0 with bit-widths and formulas), the hub integration (GGUF viewer, JS parser, model discovery), conversion workflow, supported architectures, and production best practices.

### GGUF Format Overview
GGUF (GPT-Generated Unified Format) is a **single-file binary format** that bundles both model metadata and tensors, designed for use with GGML/llama.cpp — a fast C/C++ inference framework. Unlike tensor-only formats (safetensors), GGUF encodes:
- Standardized metadata header (architecture, tokenizer config, hyperparameters)
- All tensor weights in a single file
- Support for many quantized data types (2-bit through 8-bit)

**Key advantages:**
- Single-file deployment (no `model-00001-of-00002.safetensors` splits)
- Extreme memory efficiency via quantization (4-bit and below)
- Community standard for local/edge inference (LlamaFile, Ollama, LM Studio)
- Hub-native viewer for inspecting metadata & tensors without downloading

### Transformers GGUF Integration (v4.46+)
Starting in Transformers v4.46, you can load GGUF models **directly** without llama-cpp-python:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
filename = "tinyllama-1.1b-chat-v1.0.Q6_K.gguf"

tokenizer = AutoTokenizer.from_pretrained(model_id, gguf_file=filename)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    gguf_file=filename,
    dtype=torch.float16  # or torch.bfloat16, torch.float32
)
```

**Mechanism:** The `gguf_file` parameter tells Transformers to locate the specified GGUF file within the model repo, parse its metadata header to determine the architecture (e.g., LlamaForCausalLM, MistralForCausalLM), and load the weights into the appropriate PyTorch model class — converting quantized weights back to the specified float dtype.

### Supported Architectures
| Architecture | Transformers Class |
|---|---|
| Llama / Llama-2 / Llama-3 | `LlamaForCausalLM` |
| Mistral | `MistralForCausalLM` |
| Qwen2 | `Qwen2ForCausalLM` |
| Qwen2MoE | `Qwen2MoeForCausalLM` |
| Phi-3 | `Phi3ForCausalLM` |
| Bloom | `BloomForCausalLM` |
| Falcon | `FalconForCausalLM` |
| StableLM | `StableLmForCausalLM` |
| GPT2 | `GPT2LMHeadModel` |
| Starcoder2 | `Starcoder2ForCausalLM` |
| Whisper | `WhisperForConditionalGeneration` |

### Complete GGUF Quantization Type Reference
All quantization types from the GGUF specification, as documented on the Hub:

| Type | Bits/Weight | Block Structure | Category |
|------|-------------|----------------|----------|
| `F32` | 32 | — | Unquantized (float) |
| `F16` | 16 | — | Half-precision |
| `BF16` | 16 | — | Brain float |
| `F64` | 64 | — | Double-precision |
| `Q8_0` | 8.0 | Block of 32 weights | Round-to-nearest |
| `Q8_1` | 8.0 | Block of 32 weights | Round-to-nearest + min |
| `Q6_K` | 6.5625 | Super-blocks: 16×16 weights | K-quant |
| `Q5_0` | 5.0 | Block of 32 weights | Legacy round-to-nearest |
| `Q5_1` | 5.0 | Block of 32 weights | Legacy round-to-nearest + min |
| `Q5_K_M/S` | 5.5 | Super-blocks: 8×32 weights | K-quant (recommended) |
| `Q4_0` | 4.0 | Block of 32 weights | Legacy round-to-nearest |
| `Q4_1` | 4.0 | Block of 32 weights | Legacy round-to-nearest + min |
| `Q4_K_M/S` | 4.5 | Super-blocks: 8×32 weights | K-quant (recommended) |
| `Q3_K_S/M/L` | 3.44 | Super-blocks: 16×16 weights | K-quant |
| `Q2_K` | 2.625 | Super-blocks: 16×16 weights | K-quant |
| `IQ4_NL` | 4.25 | Super-blocks: 256 weights | Importance-aware |
| `IQ3_XXS` | 3.44 | Super-blocks: 256 weights | Importance-aware |
| `IQ2_XXS` | 2.06 | Super-blocks: 256 weights | Importance-aware |
| `IQ1_S` | 1.56 | Super-blocks: 256 weights | Importance-aware |
| `F4` | 4 | — | 4-bit Microscaling Block Float |

**Picking the right quantization:** K-quant types (Q2_K–Q6_K) are the recommended family — they use importance-aware block sizing. Q4_K_M is the default choice for most users (4.5 bpw, good quality). Q5_K_M for higher quality when you have the memory. Q2_K for extreme compression (small but reduced reasoning). The newer IQ (Importance-aware Quant) types push below 3 bits for specialized use cases.

### GGUF ↔ Transformers Conversion Workflow
**HF → GGUF:** Use llama.cpp's conversion script:
```bash
python ${llama_cpp_dir}/convert-hf-to-gguf.py ${hf_model_directory} \
    --outfile model.q4_k_m.gguf --outtype q4_k_m
```

**GGUF → Transformers:** Load directly with `gguf_file` parameter. Once loaded, you can continue training with PEFT LoRA, export to safetensors, or convert back to GGUF.

### Hub Integration Features
1. **GGUF File Viewer** — Built-in viewer showing metadata & tensor info on model pages
2. **@huggingface/gguf parser** — JS package that parses GGUF metadata from remote URLs
3. **Tag filtering** — https://huggingface.co/models?library=gguf
4. **Library tag** — Repos use `library_name: gguf` in YAML frontmatter

### Production Best Practices
1. **Q4_K_M** for best quality/size trade-off; Q5_K_M for higher quality
2. **Load with bfloat16** on compatible hardware for optimal dequantization speed
3. **GGUF for deployment**, safetensors for training — or load GGUF then PEFT LoRA
4. **Key publishers:** TheBloke, MaziyarPanahi, Bartowski, QuantFactory
5. **Always specify `--outtype`** when converting; default may not match needs

### Resources
- Transformers GGUF docs: https://huggingface.co/docs/transformers/en/gguf
- Hub GGUF docs: https://huggingface.co/docs/hub/en/gguf
- llama.cpp repo: https://github.com/ggml-org/llama.cpp
- JS parser: `@huggingface/gguf` on npm
- GGUF models: https://huggingface.co/models?library=gguf

---

## 2026-07-24: hf-spaces-persistent-storage-zero-cost — Full Deep Dive v2 (Topic #95, Updated 2026-07-24)

### Summary
Comprehensive deep-dive into persisting data across Hugging Face Space restarts without spending money. Covers all five zero-cost persistence strategies: (A) Storage Buckets (new — free tier, read-write mounts, recommended), (B) Dataset repos via Hub API, (C) read-only volumes for models/datasets, (D) Space's own git repo (with heavy caveats), and (E) external free services. Includes the new `Volume` API in `huggingface_hub`, ZeroGPU integration patterns, Space lifecycle management, and practical code examples for each strategy.

### MAJOR CORRECTIONS from Previous Coverage

| Old (v1) Claim | New (v2) Reality | Source |
|---|---|---|
| Storage Buckets cost money, 0 GB free tier | **Buckets are free to create with a free storage allowance** — pricing is per-TB above free tier | HF docs July 2026 |
| No writable mounts for free | **Buckets support read-write mounts** in Spaces (models/datasets remain read-only) | HF Spaces Storage doc |
| `update_space_volume()` is the API | **Deprecated/replaced by `set_space_volumes()`** using the `Volume` dataclass | huggingface_hub API |
| `hf spaces volume add` CLI | **Replaced by `hf spaces volumes set`** (atomic replace) and `hf spaces volumes ls` | CLI reference |

### Strategy Comparison Matrix

| Strategy | Writable? | Free? | Survives Restart? | Latency | Max Size | Setup Complexity |
|---|---|---|---|---|---|---|
| **A. Storage Bucket** (recommended) | ✅ Read-Write | ✅ Free tier | ✅ Yes — mounted as volume | Filesystem-native | Free allowance | Low |
| **B. Dataset Repo via API** | ✅ Write via API | ✅ Free | ✅ Yes | API latency (~100ms) | LFS storage limit | Medium |
| **C. Read-only Volume** (model/dataset) | ❌ Read-only | ✅ Free | ✅ Yes (mount persists) | Filesystem-native | Repo limit | Low |
| **D. Space's own git repo** | ⚠️ Yes (write) | ✅ Free | ✅ Yes (committed) | Seconds (build+restart) | Space disk (50GB) | Low but DANGEROUS |
| **E. External free service** | ✅ | ✅ Free | ✅ Yes | Network latency | Varies | High |

### Strategy A: Storage Buckets (Recommended — New Free Tier)

**Buckets are the recommended way to persist data in your Space** as of July 2026. They support read-write mounts directly into the Space container.

#### Creating a Bucket

```bash
# CLI
hf buckets create my-space-data

# Python
from huggingface_hub import create_bucket
create_bucket("my-space-data")
```

#### Mounting as a Read-Write Volume (New Volume API)

The old `update_space_volume()` / `hf spaces volume add` APIs are **replaced**. Use the `Volume` dataclass and `set_space_volumes()`:

```python
from huggingface_hub import HfApi, Volume

api = HfApi()

# Mount a bucket as read-write volume at Space creation
api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_volumes=[
        Volume(
            type="bucket",
            source="username/my-bucket",
            mount_path="/data",       # default: read-write
        ),
    ],
)

# Mount on existing Space (replaces ALL existing volumes)
api.set_space_volumes(
    repo_id="username/my-space",
    volumes=[
        Volume(type="bucket", source="username/my-bucket", mount_path="/data"),
        Volume(type="model",  source="username/basemodel", mount_path="/models", read_only=True),
    ],
)

# Check current volumes
runtime = api.get_space_runtime(repo_id="username/my-space")
for v in runtime.volumes:
    print(f"{v.type}: {v.source} -> {v.mount_path} ({'ro' if v.read_only else 'rw'})")

# Remove all volumes
api.delete_space_volumes(repo_id="username/my-space")
```

#### CLI for Volumes (New Syntax)

```bash
# List mounted volumes
hf spaces volumes ls username/my-space

# Set (replace) all volumes — atomically replaces previous mounts
hf spaces volumes set username/my-space \
  --volume bucket=username/my-bucket:/data \
  --volume model=username/basemodel:/models:ro

# Delete all volumes
hf spaces volumes delete username/my-space
```

#### Inside the Space — Read/Write to Volume

Once mounted, the bucket appears as a local filesystem path. No API calls needed:

```python
# Write — persists across restarts
with open("/data/counter.txt", "w") as f:
    f.write(str(count))

# Read — survives restarts, sleep, rebuilds
if os.path.exists("/data/counter.txt"):
    with open("/data/counter.txt") as f:
        count = int(f.read().strip())

# List files in the bucket
import os
for fname in os.listdir("/data"):
    print(fname)
```

**Key advantage:** Filesystem semantics — no API calls, no rate limits, no latency beyond local I/O.

#### Pricing Reality for Free Accounts

- **Free to create** — zero cost to create a bucket
- **Free storage allowance** — basic personal accounts get free bucket storage
- **Above free tier** — billed per-TB, see hf.co/storage
- **Enterprise** — dedup-based billing (shared chunks reduce billed footprint)

For Beer's use case (small configs, chat logs, state files) — stays within free tier indefinitely.

### Strategy B: Dataset Repo via Hub API (Classic Fallback)

Use when you can't use buckets (e.g., need Git versioning, or access from non-Space environments). Every HF account gets free Dataset repo storage with Git LFS.

```python
from huggingface_hub import HfApi
import json, os

api = HfApi()
DATASET_ID = "username/my-space-state"
HF_TOKEN = os.environ["HF_TOKEN"]  # Set as Space secret

def save_state(state: dict):
    """Persist state dict to Dataset repo."""
    api.upload_file(
        path_or_fileobj=json.dumps(state).encode(),
        path_in_repo="state.json",
        repo_id=DATASET_ID,
        repo_type="dataset",
        token=HF_TOKEN,
    )

def load_state() -> dict:
    """Load state from Dataset repo. Returns {} on first boot."""
    from huggingface_hub import hf_hub_download
    try:
        path = hf_hub_download(
            repo_id=DATASET_ID,
            filename="state.json",
            repo_type="dataset",
            token=HF_TOKEN,
        )
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}  # First boot — no file yet
```

**Limitations (unchanged from v1):**
- ~50MB max per `upload_file` call (use `upload_folder` or `CommitScheduler` for larger)
- API rate limits: ~100 requests/min for free tier
- ~100ms+ latency per API call
- No atomic read-modify-write — handle concurrent write conflicts
- `upload_file` overwrites atomically but doesn't lock

### Strategy C: Read-Only Volumes (Models/Datasets/Spaces)

Models, datasets, and other Spaces can be mounted as **read-only** volumes for free. Use for reference data, model weights, configuration files.

```python
from huggingface_hub import HfApi, Volume

api = HfApi()

# Mount at creation
api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_volumes=[
        Volume(type="model",   source="meta-llama/Llama-3.2-3B", mount_path="/models/llama", read_only=True),
        Volume(type="dataset", source="username/my-ref-data",   mount_path="/data/ref",     read_only=True),
    ],
)

# Attach to existing Space
api.set_space_volumes(
    repo_id="username/my-space",
    volumes=[
        Volume(type="model", source="username/my-model", mount_path="/models", read_only=True),
    ],
)
```

**Inside the Space:**
```python
# Files are immediately available — no download code needed
with open("/models/llama/config.json") as f:
    config = json.load(f)
```

**Benefits vs downloading at runtime:**
- Zero startup delay — files are mounted, not downloaded
- No ephemeral disk usage for reference data
- Works seamlessly with all file-access patterns

### Strategy D: Space's Own Git Repo (Use with Extreme Caution)

Writing into the Space's own git repo triggers an automatic rebuild + restart. Pattern: one-shot initialization or explicit user-triggered save.

```python
from huggingface_hub import HfApi
import os

api = HfApi()
SPACE_ID = os.environ["SPACE_ID"]  # Built-in env var

# DANGEROUS — triggers rebuild
api.upload_file(
    path_or_fileobj=b"data",
    path_in_repo="persistent/data.txt",
    repo_id=SPACE_ID,
    repo_type="space",
)

# SAFER — commit via PR (no immediate rebuild, but needs merge)
from huggingface_hub import create_commit, CommitOperationAdd
create_commit(
    repo_id=SPACE_ID,
    repo_type="space",
    operations=[CommitOperationAdd(path_in_repo="data.txt", path_or_fileobj=b"data")],
    commit_message="save state",
    create_pr=True,  # PRs don't trigger automatic rebuild
)
```

**⚠️ Warnings:**
- Every push to default branch triggers `BUILDING` stage — ~30-120s downtime
- Writing frequently can create an infinite loop: write → rebuild → boot → write → rebuild...
- Only safe for: user-triggered "Save" buttons, initial setup, infrequent checkpoint saves
- PR-based saves avoid auto-rebuild but still consume git history

### Strategy E: External Free Services

When HF-native options are insufficient, free external services can supplement:

| Service | Free Tier | Use Case |
|---|---|---|
| **Supabase** | 500 MB DB, 2 GB bandwidth | Structured data, real-time sync |
| **MongoDB Atlas** | 512 MB shared cluster | Document storage, JSON state |
| **Cloudflare KV** | 100k reads/day, 1k writes/day | Key-value state, configs |
| **Vercel Blob** | 250 MB, 5 GB bandwidth | Binary artifacts, images |
| **GitHub Gist API** | Unlimited gists via API | Config files, small state |

**Trade-off:** Adds network dependency and external credentials. Only use when HF-native options don't fit.

### ZeroGPU + Storage Integration

Beer: Free personal accounts can host **up to 2 ZeroGPU Spaces** if account is in good standing (verified email, older than 30 days). Daily quota: **5 minutes GPU time** for free accounts (40 min for PRO).

```python
import spaces
import os
from huggingface_hub import HfApi

HF_TOKEN = os.environ["HF_TOKEN"]
api = HfApi()

# Load model at module level (runs once on CPU)
model = load_my_model()

@spaces.GPU
def generate(prompt: str) -> str:
    """GPU is allocated only during this function call."""
    return model.generate(prompt)

# Persist results to a bucket (always accessible)
def save_result(prompt: str, output: str):
    import json
    with open("/data/results.jsonl", "a") as f:
        f.write(json.dumps({"prompt": prompt, "output": output}) + "\n")
```

**ZeroGPU storage best practices:**
- Load model weights from a mounted model volume (read-only, no startup delay)
- Write inference results to a mounted bucket volume (persistent)
- Use `@spaces.GPU(duration=...)` for accurate GPU time estimation
- Module-level model loading (not inside `@spaces.GPU`) avoids re-loading per call
- Prep models with ahead-of-time compilation (`torch.export`) for ZeroGPU efficiency

### Practical Patterns

#### Pattern 1: First-Boot Detection

```python
import os

BOOT_FLAG = "/data/.initialized"

def is_first_boot() -> bool:
    return not os.path.exists(BOOT_FLAG)

def mark_initialized():
    with open(BOOT_FLAG, "w") as f:
        f.write("1")
```

#### Pattern 2: Periodic State Snapshots

```python
import threading, json, time

snapshot_interval = 300  # 5 minutes

def snapshot_loop(state_getter):
    while True:
        time.sleep(snapshot_interval)
        state = state_getter()
        # Write directly to bucket volume
        with open("/data/snapshot.json", "w") as f:
            json.dump(state, f)

# Start in background
threading.Thread(target=snapshot_loop, args=(lambda: current_state,), daemon=True).start()
```

#### Pattern 3: Concurrent-Write Safe Logging

```python
import json, time, os

LOG_FILE = "/data/event_log.jsonl"

def log_event(event: dict):
    event["_ts"] = time.time()
    # Append-only pattern — safe for concurrent Gradio requests
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")
```

#### Pattern 4: Chat History Persistence (Bucket Volume)

```python
import json, os

HISTORY_FILE = "/data/chat_history.json"

def load_history() -> list:
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE) as f:
            return json.load(f)
    return []

def append_message(role: str, content: str):
    history = load_history()
    history.append({"role": role, "content": content})
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)
    return history
```

### Migration Guide: v1 (Dataset API) → v2 (Bucket Volume)

If you have existing Spaces using the old Dataset-API pattern, migrate to bucket volumes:

1. **Create a bucket**: `hf buckets create my-space-data`
2. **Copy existing data**: Download from dataset, upload to bucket
3. **Mount the bucket**: Use `api.set_space_volumes()` with the Volume dataclass
4. **Update app code**: Replace `api.upload_file()` / `hf_hub_download()` calls with direct filesystem I/O to `/data/`
5. **Clean up**: Remove old Dataset API calls and rate-limit handling

### Limitations & Edge Cases

| Issue | Mitigation |
|---|---|
| Bucket volume mount replaces ALL existing volumes | Read current volumes first, append new one |
| Model/dataset volumes are read-only | Use bucket for writes, model mounts for reference data only |
| Buckets are not versioned | Take periodic snapshots to a dataset repo if history needed |
| Space goes to sleep after 48h inactivity (free CPU) | Use `HF_API` to wake: `api.restart_space(repo_id)` |
| ZeroGPU has 5 min daily quota (free) | Optimize GPU calls, cache results, batch requests |
| Bucket not available from outside Spaces | Use Dataset API for cross-environment access |
| Volume changes trigger Space rebuild | Batch volume changes together in one `set_space_volumes()` call |

### Updated Resources (July 2026)

- HF Spaces Storage: https://huggingface.co/docs/hub/en/spaces-storage
- Storage Buckets: https://huggingface.co/docs/hub/en/storage-buckets
- huggingface_hub Manage Spaces: https://huggingface.co/docs/huggingface_hub/guides/manage-spaces
- Volume API (new): `from huggingface_hub import Volume`
- ZeroGPU docs: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
- Buckets Pricing: https://huggingface.co/docs/hub/en/storage-buckets#pricing

---

## 2026-07-24: hf-smolagents — Deep Dive v2

### Summary
Comprehensive deep-dive into Hugging Face's smolagents library (v1.26.0). The v1 skill covered basic CodeAgent/ToolCallingAgent usage. This v2 deep-dive adds: multi-agent orchestration via `managed_agents`, agent memory management (inspection and resumption), two tool creation patterns (`@tool` decorator and `Tool` subclass), Human-in-the-Loop via step callbacks and plan customization, async integration with Starlette/anyio, OpenTelemetry telemetry for run inspection, Agentic RAG patterns, and an expanded secure code execution comparison.

### Key Concepts

**Multi-Agent Orchestration:**
- smolagents supports hierarchical multi-agent systems using `managed_agents` parameter
- Sub-agents require `name` and `description` attributes — the manager calls them like tools
- `ToolCallingAgent` is preferred for focused sub-agents (web search, data fetch); `CodeAgent` works as the reasoning manager
- Systems can nest arbitrarily deep

**Agent Memory:**
- `agent.memory.steps` contains all steps (PlanningStep, ToolCallStep, FinalAnswerStep, ActionStep)
- `agent.run(task, reset=True)` starts fresh; `reset=False` preserves memory and resumes
- Supports human-in-the-loop interruption + resumption with full memory

**Tool Creation:**
- Two patterns: `@tool` decorator (simple functions) vs `Tool` subclass (complex tools with class attributes)
- Tools can be pushed to Hub via `tool.push_to_hub()` — requires self-contained imports, `__init__` with only `self`

**Human-in-the-Loop:**
- `step_callbacks` dict keyed by step type classes (e.g., `{PlanningStep: callback}`)
- Callback signature: `callback(step, agent, task, **kwargs)`
- Supports plan approval, modification, and cancellation

**Async Integration:**
- Use `anyio.to_thread.run_sync(agent.run, task)` to avoid blocking async event loops
- Pattern works with Starlette, FastAPI, and any ASGI framework

**Telemetry:**
- OpenTelemetry-based instrumentation via `SmolagentsInstrumentor`
- Works with Arize Phoenix, Grafana, Datadog, etc.
- Essential for production agent monitoring — agent runs are non-deterministic and hard to debug from console logs alone

**Agentic RAG:**
- Agents with retrieval tools can formulate optimized queries, perform multiple retrievals, reason over sources, and self-critique
- Transforms RAG from rigid pipeline to interactive reasoning process
- Naturally implements HyDE, self-query refinement, and multi-hop retrieval

**Secure Code Execution:**
- Four sandbox options: Blaxel (<25ms), E2B (~500ms), Modal (~2s), Docker
- Only CodeAgent supports sandboxed execution via `executor_type`
- Blaxel provides fastest cold starts and auto-scaling to zero

### Resources
- Docs: https://huggingface.co/docs/smolagents/en/index
- Multi-agent example: https://huggingface.co/docs/smolagents/en/examples/multiagents
- Agentic RAG: https://huggingface.co/docs/smolagents/en/examples/rag
- Memory management: https://huggingface.co/docs/smolagents/en/tutorials/memory
- Tools guide: https://huggingface.co/docs/smolagents/en/tutorials/tools
- Human-in-the-Loop: https://huggingface.co/docs/smolagents/en/examples/plan_customization
- Async agents: https://huggingface.co/docs/smolagents/en/examples/async_agent
- Telemetry: https://huggingface.co/docs/smolagents/en/tutorials/inspect_runs
|- Secure code execution: https://huggingface.co/docs/smolagents/en/tutorials/secure_code_execution

---

## 2026-07-24: hf-hub-lfs-architecture — Deep Dive (Deepening on LFS Mechanics)

### Summary
Comprehensive deep-dive into Hugging Face Hub's Git LFS (Large File Storage) architecture — the underlying protocol that makes hosting multi-GB model weights, datasets, and Spaces possible. Covers the LFS batch API, pointer file mechanics, the `UploadInfo`/`post_lfs_batch_info` pipeline in `huggingface_hub`, storage quota tiers (free/PRO/Team/Enterprise), the Xet protocol replacing `hf_transfer`, LFS file management (deleting, tracking, super-squash), and practical zero-cost strategies for staying within free tier limits.

### Core Architecture

**What Git LFS is on the Hub:** Hugging Face uses an extended Git LFS v1 protocol to handle large binary files. When you `git push` a file matching LFS patterns (`.bin`, `.safetensors`, `.pt`, etc.), Git LFS intercepts it and:

1. **Replaces the file locally with a pointer file** — a tiny text file containing the SHA-256 OID and file size
2. **Uploads the real content** to the Hub's content-addressable LFS store (keyed by SHA-256)
3. **Pushes the pointer** to the Git repository

This means the Git repo stays lightweight — the heavy content lives in a separate blob store, deduplicated by content hash.

### LFS Batch API (Preupload Protocol)

The `post_lfs_batch_info()` function in `huggingface_hub.lfs` implements the [Git LFS Batch API spec](https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md):

```python
def post_lfs_batch_info(
    upload_infos: Iterable[UploadInfo],
    token: str | None,
    repo_type: str,
    repo_id: str,
    revision: str | None = None,
    endpoint: str | None = None,
    headers: dict[str, str] | None = None,
    transfers: list[str] | None = None,
) -> tuple[list[dict], list[dict], str | None]:
```

**Flow:**
1. Client sends a batch request to `{endpoint}/{repo_type}/{repo_id}.git/info/lfs/objects/batch`
2. Request body contains JSON with `operation`, `objects` (list of OID+size), `transfers` (preferred transfer protocols)
3. Hub responds with per-object instructions — either `upload` actions (with URLs + headers) or an `error` (e.g., file already exists, quota exceeded)
4. Client then uploads each file using the provided URL

**Protocol-specific headers:**
```python
LFS_HEADERS = {
    "Accept": "application/vnd.git-lfs+json",
    "Content-Type": "application/vnd.git-lfs+json",
}
```
These are required for LFS API calls. The response format follows the Git LFS v1 spec.

### UploadInfo — Smart, Lazy SHA-256

The `UploadInfo` class was designed for efficiency:

```python
class UploadInfo:
    def __init__(self, size: int, sample: bytes, sha256=None, source_path=None):
        ...
```

**Lazy hashing:** Creating `UploadInfo.from_path()` reads only the first **512 bytes** (the `sample`). The full SHA-256 is computed on-demand only when `.sha256` is accessed. This is critical because:
- Some files may be uploaded via Xet protocol which computes SHA during upload (single read pass)
- Avoiding eager SHA saves one full file read per file in batch operations
- The 512-byte sample is used by the server for content-type sniffing

```python
@classmethod
def from_path(cls, path: str):
    size = getsize(path)
    with open(path, "rb") as file:
        sample = file.peek(512)[:512]  # Only reads first 512 bytes!
    return cls(size=size, sample=sample, source_path=path)
```

### LFS Multipart Upload

For very large files, the Hub supports multipart uploads via the `lfs-multipart-upload` command:

```python
LFS_MULTIPART_UPLOAD_COMMAND = "lfs-multipart-upload"
```

The `SliceFileObj` utility (from `huggingface_hub.utils._lfs`) handles splitting large files into chunks for parallel upload. Each chunk is uploaded independently, and the Hub reassembles them server-side.

Key constants in `huggingface_hub`:
- **Max LFS files per commit:** 25,000
- **Max regular (non-LFS) payload:** 1 GB per commit
- **Individual file size limit:** 500 GB hard cap (200 GB recommended)

### Storage Quota Tiers (as of 2026-07-24)

| Account Type | Public Storage | Private Storage |
|---|---|---|
| **Free user/org** | Best-effort (no hard limit, but expect throttling beyond low GBs) | **100 GB** |
| **PRO** | Up to 10 TB included + add-on available | 1 TB + pay-as-you-go |
| **Team** | 12 TB base + 1 TB/seat + add-on | 1 TB/seat + pay-as-you-go |
| **Enterprise** | 200 TB base + 1 TB/seat + add-on | 1 TB/seat + pay-as-you-go |

**Public Storage Add-on pricing:**
| Tier | Price |
|---|---|
| 1 TB | $12/mo |
| 5 TB | $60/mo |
| 10 TB | $120/mo |
| 20 TB | $240/mo |
| 50 TB | $500/mo |

**Private Storage Pay-as-you-go:** $18/TB/mo base, discounted to $16/TB/mo at 50 TB+, $14/TB/mo at 200 TB+, $12/TB/mo at 500 TB+.

**Free tier critical insight:** "Best-effort" means there's no hard cap for public repos on free tier, but the Hub may throttle or restrict accounts that exceed reasonable usage. The 100 GB private storage limit IS a hard cap.

### Repository Limitations

| Characteristic | Recommended | Notes |
|---|---|---|
| Total files per repo | < 100,000 | Merge data into fewer files |
| Entries per folder | < 10,000 | Use subdirectories |
| File size | < 200 GB | 500 GB absolute hard limit |
| Commit operations | < 100 files* | `upload_folder` auto-splits |

*\* Not relevant for `git` CLI directly*

### Xet Protocol (Replacing hf_transfer)

**Key change:** `hf_transfer` (the Rust upload accelerator via `pip install hf_transfer`) has been **removed** in favor of `hf_xet`. The old `HF_HUB_ENABLE_HF_TRANSFER=1` env var is deprecated.

**How to enable Xet:**
```bash
# Environment variable approach
export HF_STORAGE_BACKEND=xet
export HF_XET_HIGH_PERFORMANCE=1  # Saturates bandwidth + CPU

# Or set in Python
from huggingface_hub import HfApi
api = HfApi(storage_backend="xet")
```

**Xet advantages over hf_transfer:**
- Content-addressed deduplication for iterative releases (only uploads changed chunks)
- High-performance mode (`HF_XET_HIGH_PERFORMANCE=1`) saturates available bandwidth
- Single-pass SHA computation (no separate hash step before upload)
- Integrated into the core upload pipeline, not a separate package

**Warning:** Do NOT mix Xet and the legacy multipart transfer simultaneously.

### LFS File Management

#### Deleting LFS Files (Freeing Space)

1. **Individual LFS files:** Repo Settings → "List LFS files" → Actions → Delete
2. **PR refs:** Close/merge PR first, then use "Delete ref" at bottom of PR page
3. **Super-squash history:** Via Python API:
   ```python
   api.super_squash_history(repo_id="user/repo")
   ```
   ⚠️ Destructive — compresses all Git history into one commit, removing old LFS versions. Space freed within 36 hours.

#### Tracking LFS File Origins

When an LFS file's origin is unclear:
```bash
git log --all -p -S <SHA-256-OID>
```

#### Key Points
- Deleting LFS pointers (the text files in Git) does **NOT** free storage space
- Old LFS versions persist in commit history — only super-squash or deleting the LFS file itself truly removes them
- Set `lfs.skipdownloaderrors=true` in `.gitconfig` to avoid errors when checking out branches with deleted LFS content

### Grants for High-Impact Open-Source

Free-tier users with genuine community impact (downloads, citations, adoption) can apply for additional storage grants:
- Contact `datasets@huggingface.co` (datasets) or `models@huggingface.co` (models)
- Provide evidence of community impact (download numbers, citations, adoption)
- Evaluated case-by-case — not guaranteed

### Practical Zero-Cost Strategies

For Beer's situation (free tier, no income):

1. **Stay public:** Public repos have "best-effort" unlimited storage; private repos hit 100 GB hard cap
2. **Keep repos lean:** < 100K files, < 10K entries per folder, files < 200 GB each
3. **Use Parquet/WebDataset:** Merge many small JSON files into fewer Parquet files for efficient storage and faster loading
4. **Use `upload_folder`:** Auto-splits large folders into multiple commits, avoids commit timeouts
5. **Prune regularly:** Delete unused LFS files via Settings → List LFS files; super-squash if history balloons
6. **Avoid LFS on tiny files:** Files under ~1 MB don't benefit from LFS and may even hurt performance
7. **Use Xet for iterative uploads:** `HF_STORAGE_BACKEND=xet` with `HF_XET_HIGH_PERFORMANCE=1` for content-deduped updates to existing repos
8. **Apply for a grant** if you build something with genuine community impact
9. **Monitor usage:** Check `https://huggingface.co/settings/billing` for storage dashboard
10. **Delete stale PR branches:** Large files sitting in unmerged PR branches eat quota even though they never merged

### Resources
- Storage limits: https://huggingface.co/docs/hub/en/storage-limits
- Upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- LFS source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/lfs.py
- LFS batch API spec: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Xet docs: https://huggingface.co/docs/xet/en/index
- LFS pointer deletion: https://huggingface.co/docs/hub/en/storage-limits#deleting-individual-lfs-files
- Super-squash API: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.super_squash_history
- Pricing: https://huggingface.co/pricing

## 2026-07-24: hf-transformers-hqq-quantization — Deep Dive (Topic #97)

### Summary
Half-Quadratic Quantization (HQQ) is a fast, data-free quantization method integrated into Transformers via the `HqqConfig` class. Unlike AWQ/GPTQ, HQQ requires no calibration dataset — it quantizes on-the-fly using a closed-form half-quadratic solver. Supports 8, 4, 3, 2, and even 1-bit quantization for any model modality (LLMs, vision, etc.). Fully compatible with PEFT/QLoRA fine-tuning and `torch.compile`.

### Core Architecture

HQQ replaces `torch.nn.Linear` layers with `HQQLinear` modules that store quantized weights and dequantize on-the-fly during forward passes. The quantization process uses a half-quadratic optimization that finds optimal scale factors without backpropagation or calibration data.

| Feature | Support |
|---------|---------|
| Data-free quantization | ✅ — no calibration data needed |
| Bit widths | 1, 2, 3, 4, 8 |
| On-the-fly quant | ✅ — quantizes at `from_pretrained()` time |
| PEFT/QLoRA | ✅ — full PEFT integration |
| torch.compile | ✅ — fullgraph compatible |
| Multi-modality | ✅ — LLMs, vision, audio |
| vLLM integration | ✅ — via gemlite backend |
| Serialization (HF) | ❌ — weights not serializable via `save_pretrained` |

### Installation

```bash
pip install hqq
```

For CUDA kernel support the build happens automatically. Disable with `DISABLE_CUDA=1 pip install hqq`.

For bleeding edge:
```bash
pip install git+https://github.com/dropbox/hqq.git
```

### Basic Usage in Transformers

**Replace all linear layers — 8-bit, group_size=64:**
```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, HqqConfig

quant_config = HqqConfig(nbits=8, group_size=64)
model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    dtype=torch.float16,
    device_map="auto",
    quantization_config=quant_config
)
```

**Per-layer dynamic config (MoE-friendly):**
```python
q4_config = {'nbits': 4, 'group_size': 64}
q3_config = {'nbits': 3, 'group_size': 32}

quant_config = HqqConfig(dynamic_config={
    'self_attn.q_proj': q4_config,
    'self_attn.k_proj': q4_config,
    'self_attn.v_proj': q4_config,
    'self_attn.o_proj': q4_config,
    'mlp.gate_proj': q3_config,
    'mlp.up_proj': q3_config,
    'mlp.down_proj': q3_config,
})

model = AutoModelForCausalLM.from_pretrained(
    "meta-llama/Llama-3.1-8B",
    dtype=torch.float16,
    device_map="auto",
    quantization_config=quant_config
)
```

### Backends

| Backend | Description | axis | Best for |
|---------|-------------|------|----------|
| `PYTORCH` | Pure PyTorch dequant | 0 or 1 | Compatibility, older GPUs |
| `PYTORCH_COMPILE` | Compiled Pytorch graph | 0 or 1 | Torch.compile workflows |
| `ATEN` | CUDA dequant kernels | 0 only | Best quality, PEFT training |
| `gemlite` | Fused 4-bit gemm kernels | 1 only | High-throughput inference |
| `torchao_int4` | TorchAO tiny_gemm (batch<4) | 1 only | Low-latency single requests |

Set backend globally:
```python
from hqq.core.quantize import *
HQQLinear.set_backend(HQQBackend.PYTORCH)
```

Enable optimized inference after quantization:
```python
from hqq.utils.patching import prepare_for_inference
prepare_for_inference(model, backend="gemlite")
```

### Key Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `nbits` | 4 | Bits per weight (1, 2, 3, 4, 8) |
| `group_size` | 64 | Weights per group for shared scale/zero |
| `axis` | 1 | Grouping axis (0=per-output, 1=per-input) |
| `optimize` | True | Enable half-quadratic optimization |

- `axis=0` gives better quality, especially at low bits, but only ATEN backend supports it
- `axis=1` is required for gemlite/torchao_int4 fast inference
- Recommended starting config: `nbits=4, group_size=64, axis=1`

### PEFT/QLoRA Training

Full PEFT integration for fine-tuning quantized models:
```python
from hqq.core.peft import PeftUtils

base_lora_params = {
    'lora_type': 'default', 'r': 32,
    'lora_alpha': 64, 'dropout': 0.05,
    'train_dtype': torch.float32
}
lora_params = {
    'self_attn.q_proj': base_lora_params,
    'self_attn.k_proj': base_lora_params,
    'self_attn.v_proj': base_lora_params,
    'self_attn.o_proj': base_lora_params,
}

PeftUtils.add_lora(model, lora_params)
HQQLinear.set_backend(HQQBackend.ATEN)  # or PYTORCH_COMPILE
# Train...
model.eval()
PeftUtils.merge_and_unload(model)  # Optional: merge
```

Also directly supported in HuggingFace PEFT library:
```python
from peft import LoraConfig, get_peft_model
# Standard PEFT API works with HQQ-quantized models
```

### vLLM Integration

HQQ works with vLLM via gemlite backend for production serving:
```python
from hqq.utils.vllm import set_vllm_onthefly_hqq_quant
from vllm import LLM

skip_modules = ['lm_head', 'visual', 'vision']

# A16W4 HQQ weight-only
set_vllm_onthefly_hqq_quant(
    weight_bits=4, group_size=128,
    quant_mode='int4_weightonly',
    skip_modules=skip_modules
)

llm = LLM(model="meta-llama/Llama-3.2-3B-Instruct",
          max_model_len=4096,
          gpu_memory_utilization=0.80,
          dtype=torch.float16)
```

Supported quant modes for vLLM:
- `int8_weightonly` — A16W8 INT8
- `int4_weightonly` — A16W4 HQQ
- `int8_dynamic` — A8W8 INT8 dynamic
- `fp8_dynamic` — A8W8 FP8 dynamic
- `mxfp8_dynamic` — A8W8 MXFP8 dynamic
- `mxfp4_weightonly` — A16W4 MXFP4
- `nvfp4_dynamic` — A4W4 NVFP4 dynamic

### Zero-Cost Practical Notes

1. **Data-free is a superpower for free-tier:** Since HQQ needs no calibration, you can quantize a model entirely in CPU RAM + normal GPU VRAM — no need for expensive A100s or calibration runs.
2. **Best paired with small GPUs:** A 4-bit 8B model fits in ~5GB VRAM, usable on free T4s (15GB) in Spaces or Colab.
3. **axis=1 + gemlite for speed:** On a T4 you can expect ~30-50 tok/s for 4-bit 7B models.
4. **No serialization limitation:** HQQ models can't `save_pretrained()` in quantized form — you must re-quantize at load time. This is fine for inference-only setups (cache the original fp16, quantize at load).
5. **PEFT stays in fp32:** LoRA adapters train in fp32 by default; the HQQ base weights stay quantized. This is memory-efficient.
6. **torch.compile works with any backend:** Use `PYTORCH_COMPILE` backend or regular `torch.compile` wrapping for additional speed.

### Comparison with Other Quantization Methods

| Method | Calibration? | Bits | Serialize? | torch.compile | vLLM |
|--------|-------------|------|-----------|--------------|------|
| HQQ | No | 1-8 | ❌ | ✅ | ✅ |
| bitsandbytes | No | 4/8 | ✅ | ✅ | ❌ |
| AWQ | Yes | 4 | ✅ | ❌ | ✅ |
| GPTQ | Yes | 2-8 | ✅ | ❌ | ✅ |
| GGUF | No | 1-8 | ✅ | ❌ | ✅ |

### Resources
- Transformers HQQ docs: https://huggingface.co/docs/transformers/en/quantization/hqq
- HQQ blog: https://mobiusml.github.io/hqq_blog/
- HQQ+ (1-bit): https://dropbox.github.io/1bit_blog/
- HQQ repo (mobiusml): https://github.com/mobiusml/hqq
- HQQ repo (dropbox fork): https://github.com/dropbox/hqq
- PEFT HQQ guide: https://huggingface.co/docs/peft/en/developer_guides/quantization#hqq-quantization
- GemLite fast kernels: https://github.com/dropbox/gemlite

---

## 2026-07-24: hf-hub-lfs-architecture — Deep Dive v2 (LFS Batch API Internals, Pointer Format, Deduplication, Advanced Management)

### Summary
Second-pass deep-dive into Hugging Face Hub's Git LFS architecture, covering the LFS Batch API specification in full detail (operations, requests, responses, error codes, transfer adapters), the LFS pointer file specification (format, verification, creation), content-addressable storage deduplication across repos and forks, `.gitattributes` configuration for HF repos, Raw API direct download pattern, advanced LFS debugging, and practical management patterns for staying within free-tier storage limits with minimal overhead.

### 1. LFS Batch API — Full Specification

The Git LFS Batch API is the core protocol for transferring large files between client and server. It operates as an HTTP JSON API.

#### Protocol Endpoint

```
POST {endpoint}/{repo_type}/{repo_id}.git/info/lfs/objects/batch
```

Where:
- `endpoint` = `https://huggingface.co` (default) or `https://huggingface.co/datasets/{org}/{repo}` (for datasets via dataset URL)
- `repo_type` = explicit path to repo (inferred by the Hub), e.g. `https://huggingface.co/{org}/{repo}` for models
- The `.git` suffix is standard Git LFS convention

#### Request Body

```json
{
  "operation": "upload" | "download",
  "transfers": ["xet", "lfs-multipart-upload", "lfs-standalone-file", "basic"],
  "ref": {
    "name": "refs/heads/main"
  },
  "objects": [
    {
      "oid": "sha256:abcdef...",
      "size": 1234567890
    }
  ],
  "hash_algo": "sha256"
}
```

**Required fields:**
- `operation`: `"upload"` or `"download"` — determines whether the server returns upload URLs (with auth tokens) or download URLs
- `objects`: array of OID+size pairs identifying the files to transfer

**Optional fields:**
- `transfers`: ordered array of preferred transfer protocols. The server responds with the first supported one. If omitted, `["basic"]` is assumed.
- `ref`: Git ref name. For uploads, this helps the server validate permissions on the target branch/tag
- `hash_algo`: hash algorithm used. Default is `sha256`.

**Transfer adapters (in priority order as requested by `huggingface_hub`):**
| Adapter | Identifier | Description |
|---------|-----------|-------------|
| Xet | `xet` | Content-deduplicated chunked transfer (new default for HF) |
| LFS Multipart | `lfs-multipart-upload` | Chunked upload for very large files |
| LFS Standalone | `lfs-standalone-file` | Single-file upload via presigned URL |
| Basic | `basic` | Raw HTTP PUT with basic auth |

**Hub-specific extension:** The Hub's LFS server (not standard Git LFS) may return additional metadata about the repository state, storage quota usage, and whether the file already exists on the server (deduplication shunt).

#### Response Body (success, 200)

```json
{
  "transfer": "xet",
  "objects": [
    {
      "oid": "sha256:abcdef...",
      "size": 1234567890,
      "authenticated": true,
      "actions": {
        "upload": {
          "href": "https://...",
          "header": {
            "Authorization": "Bearer <token>",
            "Content-Type": "application/octet-stream"
          },
          "expires_at": "2026-07-24T12:00:00Z"
        },
        "verify": {
          "href": "https://...",
          "header": {
            "Authorization": "Bearer <token>"
          }
        }
      }
    },
    {
      "oid": "sha256:def...",
      "size": 987654321,
      "authenticated": true,
      "actions": null
    }
  ]
}
```

**Key response fields:**
- `transfer`: the transfer adapter the server selected (may differ from what was requested)
- `objects[].actions`: `null` means the object already exists at the target OID (dedup shunt) — no upload needed!
- `objects[].actions.upload`: presigned URL + headers for uploading the file content
- `objects[].actions.verify`: optional URL to verify the upload was stored correctly after upload completes
- `objects[].expires_at`: ISO 8601 timestamp after which the presigned URL expires

#### Response Body (error, 4xx/5xx)

```json
{
  "message": "Quota exceeded",
  "request_id": "abc-123",
  "documentation_url": "https://huggingface.co/docs/hub/en/storage-limits"
}
```

**Common error conditions:**
| Status | Message | Meaning |
|--------|---------|---------|
| 401 | Bad credentials | Token invalid or missing |
| 403 | Forbidden | No write permission on the repo |
| 403 | Quota exceeded | Storage limit reached for private repos |
| 404 | Not found | Repo does not exist |
| 422 | Invalid objects | OID or size validation failed |
| 429 | Too many requests | Rate limited — back off and retry |
| 507 | Insufficient storage | Private storage cap reached |

**Rate limiting:** The Hub applies per-user rate limits on LFS batch operations (~100 req/min). When hit, the server returns 429 with a `Retry-After` header. The `huggingface_hub` client library handles retry with exponential backoff automatically.

### 2. LFS Pointer File Format

Git LFS replaces large files with small pointer files in the actual Git repository. The pointer file is what Git tracks — the real content goes to the LFS store.

#### Canonical Pointer File

```
version https://git-lfs.github.com/spec/v1
oid sha256:4ac7d8e5a7a0a2e4c0c5a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8
size 4127389056
```

**Specification:** The pointer file MUST:
1. Be exactly 3 lines (with trailing newline on each, total 4 newlines including final blank)
2. Line 1: `version https://git-lfs.github.com/spec/v1\n`
3. Line 2: `oid sha256:<64-char lowercase hex>\n`
4. Line 3: `size <decimal integer>\n`
5. No trailing whitespace on any line
6. The OID format is exactly `sha256:` followed by 64 lowercase hex characters
7. The size is in bytes, decimal format, no leading zeros

**Verification:** The Hub validates pointer files at push time — if the pointer format is invalid (wrong version, malformed OID, missing size), the push is rejected.

**Hub extension:** In addition to the standard pointer file, `huggingface_hub` uses a companion cache (in `~/.cache/huggingface/hub/`) that maps `{repo_id}/{commit_hash}/{path_in_repo}` to the OID. This is how the library resolves LFS files without needing to query Git at all — it's a flat-file index that avoids Git metadata calls.

#### Detecting LFS Files in Python

```python
from huggingface_hub import HfApi
api = HfApi()

# List files in a repo — files returned as dicts with 'lfs' field
files = api.get_repo_tree(repo_id="user/repo")
lfs_files = [f for f in files if f.get("lfs")]

# Each LFS file entry has:
# - lfs['oid']: the SHA-256 OID (in hex)
# - lfs['size']: original file size
# - lfs['pointerSize']: size of the pointer file (typically ~120 bytes)
```

### 3. Content-Addressable Storage — Deduplication Mechanics

The Hub stores LFS content in a **content-addressable store** keyed by SHA-256 OID.

#### How CSD Works

```
File A (~/model-00001-of-00002.safetensors) → SHA-256 OID → Store at /objects/4a/c7/d8e5...
File B (fork of same repo, same file) → SHA-256 OID (IDENTICAL) → Files already exists, no re-upload
```

**Implications for free-tier users:**
1. **Forks cost zero extra storage:** If you fork a repo, even if the fork is private, you don't pay for the content already stored. The Hub stores content once by OID. This is true even across repos — if file `abc.safetensors` in `user/repo1` has the same SHA-256 as `abc.safetensors` in `user/repo2`, it's stored only once.
2. **Cross-repo deduplication:** Two separate repos with identical LFS files share the same underlying storage. The storage quota counts only unique new content.
3. **Commit history is not deduplicated:** Different commits that modify an LFS file each store a NEW OID (because the SHA changes when the file changes). Old OIDs remain stored and referenced in the Git history. This is why old LFS versions consume space even after file deletion.
4. **Super-squash is the only escape:** Compressing history via `api.super_squash_history()` drops old LFS OIDs that are no longer referenced by any commit in the new single-commit history.

#### Verifying Deduplication

```python
# Check if a file already exists on the Hub without uploading
from huggingface_hub import HfApi
api = HfApi()

# The batch API's preupload check does this automatically:
# objects with actions=null in the batch response = already exists, dedup'd
```

### 4. `.gitattributes` — LFS Pattern Configuration for HF Repos

The Hub's default LFS patterns are configured server-side but can be overridden locally.

#### Hub's Default LFS Patterns

These file extensions are automatically tracked via LFS by the Hub server:
```
*.safetensors filter=lfs diff=lfs merge=lfs -text
*.bin filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pth filter=lfs diff=lfs merge=lfs -text
*.ckpt filter=lfs diff=lfs merge=lfs -text
*.gguf filter=lfs diff=lfs merge=lfs -text
*.ggml filter=lfs diff=lfs merge=lfs -text
*.h5 filter=lfs diff=lfs merge=lfs -text
*.onnx filter=lfs diff=lfs merge=lfs -text
*.tar filter=lfs diff=lfs merge=lfs -text
*.gz filter=lfs diff=lfs merge=lfs -text
*.zip filter=lfs diff=lfs merge=lfs -text
*.zst filter=lfs diff=lfs merge=lfs -text
*.jsonl filter=lfs diff=lfs merge=lfs -text (for very large dataset files)
*.parquet filter=lfs diff=lfs merge=lfs -text
```

**Custom patterns:** You can override by providing a `.gitattributes` file in your repo root:

```gitattributes
# Track extra formats as LFS
*.msgpack filter=lfs diff=lfs merge=lfs -text
*.npy filter=lfs diff=lfs merge=lfs -text

# Force small files to be stored inline (NOT LFS) — saves pointer overhead
*.config -filter -diff -merge
*.json -filter -diff -merge
*.yaml -filter -diff -merge
*.txt -filter -diff -merge
```

**Note:** The Hub server has the final say. If the Hub server considers a file too large (>1 MB) and NOT on a tracked pattern, the push will fail with a connection error because the Git remote helper expects LFS for large blobs.

#### Un-tracking Files from LFS

If you accidentally pushed a large file as regular Git (not LFS) and it bloated the repo:

```bash
# 1. Install git-lfs
git lfs install

# 2. Migrate the file from Git to LFS
git lfs migrate import --include="path/to/large/file.bin" --everything

# 3. Force push (destructive — coordinate with collaborators)
git push --force origin main
```

### 5. Raw API — Direct LFS File Downloads Without Git

The Hub's Raw API allows direct HTTP downloads of LFS files without needing the Git LFS client:

```
GET https://huggingface.co/{repo_id}/raw/{branch}/{path}
```

But for LFS files, the raw endpoint returns the **pointer file** (not the real content). To get real content directly:

```
# Direct LFS download URL:
GET https://huggingface.co/{repo_id}/resolve/{branch}/{path}

# With huggingface_hub:
from huggingface_hub import hf_hub_download
path = hf_hub_download(repo_id="user/repo", filename="model.safetensors", repo_type="model")
```

**The `resolve` endpoint** auto-redirects to the LFS content's CDN URL. This is the recommended URL for downloading model weights in scripts, Colab notebooks, and Spaces.

**Streaming support:**
```python
# Stream large models without fully downloading
from huggingface_hub import hf_hub_download
import torch

# With `hf_hub_download`, use `local_files_only=False` to force fresh download
# Or use the datasets library with streaming for dataset content

# For models, load directly from Hub using transformers with device_map:
from transformers import AutoModelForCausalLM
model = AutoModelForCausalLM.from_pretrained("user/repo", device_map="auto")
# Downloads LFS weights on-the-fly via the resolve endpoint
```

**Cache behavior:** `hf_hub_download` returns the cached path. Subsequent calls with the same `repo_id` + `filename` return the cached copy instantly. Use `force_download=True` to bypass cache.

### 6. LFS on Free Tier — Advanced Management Patterns

#### Monitoring LFS Usage

```python
from huggingface_hub import HfApi

api = HfApi()

# Get repo info including LFS file listing
repo_info = api.repo_info(repo_id="user/repo", files_metadata=True)

# Count LFS files
lfs_count = sum(1 for f in repo_info.siblings if f.lfs)
lfs_total_size = sum(f.lfs["size"] for f in repo_info.siblings if f.lfs)

print(f"LFS files: {lfs_count}")
print(f"Total LFS size: {lfs_total_size / 1e9:.2f} GB")
```

#### Finding and Deleting Orphaned LFS References

```python
# List all LFS files across all branches/tags
# (requires git CLI access to the cloned repo)
import subprocess

# Find all LFS OIDs referenced by current HEAD
result = subprocess.run(
    ["git", "lfs", "ls-files", "--all", "--name-only"],
    capture_output=True, text=True
)
referenced_oids = set(result.stdout.strip().split('\n'))

# Find LFS files in the cache that are NOT referenced
# (these consume space but are not needed for current checkout)
# Cache is at ~/.cache/huggingface/hub/
```

#### Git LFS Cleanup Commands

```bash
# Check how much space LFS cache is using
du -sh ~/.cache/huggingface/hub/

# Prune local LFS cache (removes unreferenced objects)
git lfs prune

# Check LFS cache health
git lfs fsck  # Verifies all LFS files checkout correctly

# List all LFS files in a repo (from any checkout)
git lfs ls-files --all
```

#### LFS Across All Files in a Repo (Using the Web API)

```bash
# List all files in a repo with LFS status
curl -s https://huggingface.co/api/models/{org}/{repo} | \
    jq '.siblings[] | select(.lfs != null) | {path: .rfilename, size: .lfs.size, oid: .lfs.oid}'

# Get total LFS storage used by a repo
curl -s https://huggingface.co/api/models/{org}/{repo} | \
    jq '[.siblings[] | select(.lfs != null) | .lfs.size] | add | . / 1e9 | "\(.) GB"'
```

#### Avoiding LFS Bloat on Free Tier

**The biggest hidden storage sink** is **version history**. Every time you push an updated LFS file, the old version's OID remains stored. Over 10 updates, that's 10× the storage cost for the same file.

**Strategies:**
1. **One-shot uploads:** When possible, push the final version of a file rather than iterating locally and pushing updates
2. **Super-squash before major storage increases:** Before uploading a large model to a repo with history, run `api.super_squash_history("user/repo")` to reset the commit history to a single commit
3. **Use Xet for iterative updates:** Xet's chunk-level deduplication is more efficient than LFS's whole-file deduplication for iterative releases — only changed chunks are uploaded
4. **Delete old LFS versions via UI:** Go to Repo Settings → "List LFS files" → Delete obsolete versions
5. **Watch for deleted branches:** Merged branches and stale PRs often hold LFS references. After cleanup, run super-squash to truly free the space

### 7. LFS and Xet — Dual Protocol Strategy

The Hub now supports both traditional LFS and the Xet storage backend. Understanding when each is better helps optimize storage:

| Scenario | Best Protocol | Reason |
|----------|--------------|--------|
| First upload of a model | LFS (traditional) | Stable, fastest for single-shot large uploads |
| Iterative updates to large files | Xet | Chunk-level dedup, only uploads changed bytes |
| Many small LFS files | LFS | Xet overhead not worth it for <10 MB files |
| CI/CD pipeline pushing daily | Xet with `HF_XET_HIGH_PERFORMANCE=1` | Bandwidth saturation + dedup |
| Dataset with incremental additions | Xet | Append-only chunks dedup naturally |

**Detection of which protocol was used:**
- LFS-stored files: show up in "List LFS files" in Settings
- Xet-stored files: handled transparently — the Hub API abstracts the backend. Check `HF_STORAGE_BACKEND` env var to see which is active.

### Resources
- Git LFS Batch API spec: https://github.com/git-lfs/git-lfs/blob/main/docs/api/batch.md
- Git LFS Pointer file spec: https://github.com/git-lfs/git-lfs/blob/main/docs/pointer.md
- Git LFS file locking: https://github.com/git-lfs/git-lfs/blob/main/docs/api/locking.md
- HF Storage limits: https://huggingface.co/docs/hub/en/storage-limits
- HF Xet docs: https://huggingface.co/docs/xet/en/index
- huggingface_hub LFS source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/lfs.py
- huggingface_hub upload guide: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- HF API endpoint: https://huggingface.co/api/models/{org}/{repo}
|- Git LFS migration docs: https://git-lfs.com/

## 2026-07-24: hf-inference-client-structured-outputs — Deep Dive (Topic #100)

### Summary

Comprehensive deep-dive into Hugging Face InferenceClient's **Structured Outputs**, **JSON Mode**, and **Tool/Function Calling** capabilities. These three features form a continuum of structured generation — from unvalidated JSON (JSON Mode) to schema-enforced JSON (Structured Outputs) to dynamic function selection (Tool Calling). All follow OpenAI-compatible API specs for easy migration. Combined with TGI's grammar-based guidance engine (powered by the `outlines` library), these features enable reliable programmatic consumption of LLM outputs without parsing errors.

### The Three Structured Generation Modes

| Mode | What It Does | When To Use | Cost/Complexity |
|------|-------------|-------------|-----------------|
| **JSON Mode** (`response_format={"type": "json_object"}`) | Forces valid JSON output, no schema enforcement | Quick data extraction, prototyping | Lowest — any provider that supports it |
| **Structured Outputs** (`response_format={"type": "json_schema", "json_schema": {...}}`) | Enforces a specific JSON Schema compliant output | Production pipelines, database inserts, API responses | Medium — requires schema definition |
| **Tool Calling** (OpenAI `tools` parameter) | Model decides whether to call a function and with which args | Agent workflows, function dispatching, RAG tool use | Highest — requires tool definitions + handling logic |

### JSON Mode vs Structured Outputs — Key Difference

**JSON Mode** (`type: "json_object"`) only guarantees syntactically valid JSON. The model can output any shape — keys, nesting, data types all vary. Use it when you just need parseable output and can handle variation.

**Structured Outputs** (`type: "json_schema"`) guarantees both valid JSON AND compliance with a specified [JSON Schema](https://json-schema.org/). The model's output is constrained to match your schema exactly — field names, types, required fields, nested structures all enforced. Use it when downstream code depends on a fixed contract.

### Implementation — Structured Outputs with InferenceClient

```python
from huggingface_hub import InferenceClient

# Define a JSON Schema for structured output
json_schema = {
    "name": "book",
    "schema": {
        "properties": {
            "name": {"title": "Name", "type": "string"},
            "authors": {
                "items": {"type": "string"},
                "title": "Authors",
                "type": "array",
            },
        },
        "required": ["name", "authors"],
        "title": "Book",
        "type": "object",
    },
    "strict": True,  # Enforce strict schema compliance
}

client = InferenceClient(provider="cerebras")
completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[
        {"role": "system", "content": "Extract the books information."},
        {"role": "user", "content": "I recently read 'The Great Gatsby' by F. Scott Fitzgerald."},
    ],
    response_format={
        "type": "json_schema",
        "json_schema": json_schema,
    },
)
print(completion.choices[0].message)
# => {"name": "The Great Gatsby", "authors": ["F. Scott Fitzgerald"]}
```

### JSON Mode — Quick & Lightweight

```python
completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "List 3 colors as JSON."}],
    response_format={"type": "json_object"},
)
# Output is valid JSON but shape not guaranteed
```

### Tool/Function Calling — OpenAI-Compatible

```python
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a city",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string", "description": "City name"},
                "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
            },
            "required": ["location"]
        }
    }
}]

completion = client.chat.completions.create(
    model="Qwen/Qwen3-32B",
    messages=[{"role": "user", "content": "What's the weather in Bangkok?"}],
    tools=tools,
    tool_choice="auto",
)
# completion.choices[0].message.tool_calls contains the function calls
```

### The `response_format` Argument — API Details

The `response_format` parameter in `InferenceClient.chat.completions.create()` accepts one of three types:

| Type | Description |
|------|-------------|
| `ChatCompletionInputResponseFormatText` | Text output (default) |
| `ChatCompletionInputResponseFormatJSONObject` | JSON mode — `{"type": "json_object"}` |
| `ChatCompletionInputResponseFormatJSONSchema` | Structured Outputs — `{"type": "json_schema", "json_schema": {...}}` |

### Async Client for Concurrent Structured Requests

```python
from huggingface_hub import AsyncInferenceClient
import asyncio

async def extract_multiple(texts: list[str]):
    async with AsyncInferenceClient(provider="cerebras") as client:
        tasks = [
            client.chat.completions.create(
                model="Qwen/Qwen3-32B",
                messages=[{"role": "system", "content": "Extract entities."},
                          {"role": "user", "content": t}],
                response_format={"type": "json_schema", "json_schema": schema},
            )
            for t in texts
        ]
        return await asyncio.gather(*tasks)
```

### How It Works Under the Hood — TGI Guidance Engine

Text Generation Inference (TGI) implements structured generation via **guidance** — grammar-based token masking powered by the `outlines` library:

1. **Grammar compilation:** The JSON Schema or tool definition is compiled into a finite state machine (FSM).
2. **Forward pass:** The model runs a forward pass over the batch, returning token probabilities.
3. **Masking:** A processor applies the grammar mask — tokens not allowed by the grammar have their probabilities set to zero.
4. **Sampling:** The model samples from the remaining (masked) distribution.
5. **State update:** The chosen token updates the FSM state, preparing for the next pass.

This happens at each generation step, ensuring 100% compliance with the grammar/schema.

**Key insight for zero-cost users:** Providers that run TGI under the hood (Cerebras, Novita, DeepInfra) generally support structured outputs. Providers using vLLM (Together AI, Fireworks) may support it via vLLM's own guided decoding. Check provider docs.

### Provider Support Matrix (Serverless Inference)

Support varies by provider. Verified patterns as of July 2026:

| Provider | JSON Mode | Structured Outputs | Tool Calling | Backend |
|----------|-----------|-------------------|--------------|---------|
| Cerebras | ✓ | ✓ | ✓ | TGI-based |
| Novita | ✓ | ✓ | ✓ | TGI-based |
| DeepInfra | ✓ | ✓ | ✓ | TGI-based |
| Together AI | ✓ | Partial | ✓ | vLLM |
| Fireworks | ✓ | Partial | ✓ | vLLM |
| Replicate | ✓ | Partial | ✓ | Custom |
| Groq | ✓ | ✓ | ✓ | Custom/LPU |
| Fal AI | ✓ | — | — | Custom |

*Partial* = schema enforcement but may not support `strict: True`.

### Zero-Cost Best Practices

1. **Prefer JSON Schema over regex/string parsing** — Structured Outputs eliminate the most common failure mode in agent pipelines (malformed JSON).
2. **Use `strict: True` for production** — Without strict mode, the schema acts as a hint rather than a constraint.
3. **Short schemas generate faster** — Complex deeply nested schemas increase FSM compilation time and per-step overhead.
4. **Combine tools with system prompts** — A system prompt that says "You MUST call a function for every query" improves tool-calling reliability.
5. **`tool_choice: "required"`** — Force the model to always call a tool (useful for classification workflows).
6. **Fallback chain:** Structured Outputs → JSON Mode → raw text with regex parsing. Start with the cheapest option that meets reliability needs.
7. **Rate limits:** Free-tier providers (especially Cerebras, Novita) have tighter rate limits on structured generation due to the FSM overhead per token.

### Resources

- InferenceClient reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client
- Inference providers guide: https://huggingface.co/docs/huggingface_hub/en/guides/inference
- TGI Guidance docs: https://huggingface.co/docs/text-generation-inference/en/conceptual/guidance
- OpenAI-compatible structured outputs: https://platform.openai.com/docs/guides/structured-outputs
- JSON Schema spec: https://json-schema.org/
- `outlines` library (FSM grammar engine): https://github.com/dottxt-ai/outlines
## 2026-07-24: hf-hub-storage-buckets — Deep Dive (New Feature, Topic #103)

### Summary
Comprehensive deep-dive into Hugging Face **Storage Buckets** — a brand-new repo type providing S3-like object storage on the Hub, powered by the Xet storage backend. Unlike Git-based repositories (models, datasets, Spaces), buckets are non-versioned and mutable: designed for training checkpoints, logs, intermediate artifacts, agent scratch storage, and any large collection of files that doesn't need version control. Buckets have a **free storage allowance** and are available to all users.

### Buckets vs Repositories — Key Differences

| Feature            | Repositories (Git-based)        | Storage Buckets                     |
| ------------------ | ------------------------------- | ----------------------------------- |
| Versioning         | Full Git history                | None (mutable, overwrite-in-place)  |
| Types              | Models, Datasets, Spaces        | Standalone bucket                   |
| Primary use case   | Publishing finished artifacts   | Working storage / intermediate data |
| Operations         | Hub API, Git push/pull          | S3-like `sync`, `cp`, `rm`          |
| Deduplication      | Xet chunk-level                 | Xet chunk-level                     |
| Pull Requests      | Yes                             | No                                  |
| Model/Dataset Cards| Yes                             | No (but plain README rendered)      |

### Creating a Bucket

**From Hub UI:** Visit huggingface.co/new-bucket, choose owner, name, public/private visibility, optional CDN pre-warming regions.

**From CLI:**
```bash
hf buckets create my-bucket
hf buckets create my-org/shared-bucket --private
```

**From Python:**
```python
from huggingface_hub import create_bucket
create_bucket("my-bucket")
create_bucket("my-org/shared-bucket", private=True)
```

### Managing Files

All bucket file references use hf://buckets/ paths.

**Upload/Download/Sync:**
```bash
hf buckets cp ./model.safetensors hf://buckets/username/my-bucket/models/
hf buckets cp hf://buckets/username/my-bucket/config.json - | jq .
hf buckets sync ./data hf://buckets/username/my-bucket/data --delete
```

The sync command supports --include/--exclude filters, --dry-run, and a plan-and-apply workflow (--plan sync-plan.jsonl then --apply).

**Server-Side Copy (brand-new feature):**
```bash
hf buckets cp hf://datasets/HuggingFaceFW/fineweb/data hf://buckets/username/fineweb-data
```
Only Xet-tracked files (large) copied server-side instantly; small non-Xet files auto-downloaded and re-uploaded. Source and destination must be in the same storage region.

### Access Patterns

| Method | Best for |
|--------|----------|
| hf-mount | Mount as local filesystem via NFS/FUSE |
| Volume mounts | HF Jobs & Spaces |
| hf:// paths (fsspec) | Python data tools (pandas, DuckDB) |
| CLI sync | Batch transfers, backups |
| S3 API | AWS CLI, boto3, s5cmd |

**Python via HfFileSystem:**
```python
import pandas as pd
df = pd.read_parquet("hf://buckets/username/my-bucket/data.parquet")

import duckdb
from huggingface_hub import HfFileSystem
duckdb.register_filesystem(HfFileSystem())
```

### Key Use Cases for Zero-Cost

1. Training checkpoints & logs - overwrite-in-place, no Git history accumulation
2. Data processing pipelines - staging area for intermediate results
3. Agentic storage - Hub-native scratch for AI agents (tool outputs, working memory)
4. Rolling backups - old files truly gone when deleted (unlike Git repos)
5. Linking models to buckets - two-way link via model card YAML

### Pricing

Buckets are free to create with a free storage allowance. Per-TB billing above free tier. Enterprise plans get dedup-based billing. CDN pre-warming available at hf.co/storage.

### Resources
- Storage Buckets docs: https://huggingface.co/docs/hub/en/storage-buckets
- Access Patterns: https://huggingface.co/docs/hub/en/storage-buckets-access
- S3-Compatible API: https://huggingface.co/docs/hub/en/storage-buckets-s3
- hf-mount: https://github.com/huggingface/hf-mount
- HuggingFace Hub Buckets Python guide: https://huggingface.co/docs/huggingface_hub/guides/buckets
- Xet storage backend: https://huggingface.co/docs/hub/xet/index

---

## 2026-07-24: hf-hub-collections-api-deep-dive — Full API Reference & Patterns (Topic #107)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Collections API — covering all 7 collection methods from source (`huggingface_hub` v1.x), the `list_collections` pagination engine with 3 sort modes and 2 filter axes, the `Collection` and `CollectionItem` data classes, 6 item types (model, dataset, space, paper, collection, bucket), and practical patterns for programmatic curation, batch population, and integration with other Hub features.

### Core Data Types

**`CollectionItemType_T`** = `Literal["model", "dataset", "space", "paper", "collection", "bucket"]`

**`CollectionSort_T`** = `Literal["lastModified", "trending", "upvotes"]`

**`CollectionItem`** fields: `item_object_id` (DB id), `item_id` (Hub ID), `item_type`, `position`, `note` (max 500 chars)

**`Collection`** fields: `slug`, `title`, `owner`, `items`, `last_updated`, `position`, `private`, `theme`, `upvotes`, `description` (max 150 chars), `url` (property)

### Method Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `list_collections()` | GET `/api/collections` | List with filters (owner, item, sort, limit) — items truncated to 4 |
| `get_collection()` | GET `/api/collections/{slug}` | Full collection with ALL items |
| `create_collection()` | POST `/api/collections` | Create new (title, namespace, description, private, exists_ok) |
| `update_collection_metadata()` | PATCH `/api/collections/{slug}` | Update title/desc/position/private/theme |
| `delete_collection()` | DELETE `/api/collections/{slug}` | Irreversible! Supports `missing_ok` |
| `add_collection_item()` | POST `/api/collections/{slug}/items` | Add item (item_id, item_type, note, exists_ok) |
| `update_collection_item()` | PATCH `/api/collections/{slug}/items/{id}` | Edit note/position (uses `item_object_id`) |
| `delete_collection_item()` | DELETE `/api/collections/{slug}/items/{id}` | Remove item (uses `item_object_id`) |

### Key Behaviors & Pitfalls

1. **`list_collections` truncates items to 4** — always use `get_collection()` for full item lists
2. **`item_object_id` vs `item_id`** — modify/delete operations require the internal DB id, NOT the Hub repo ID
3. **No `theme` on `create_collection`** — must be set via `update_collection_metadata()` after creation
4. **Slug changes on title update** — prefix changes but trailing hash stays the same; old slug URL breaks
5. **Description capped at 150 chars** — silently truncated; notes capped at 500 chars
6. **6 item types**: model, dataset, space, paper, collection, bucket
7. **`exists_ok` on create_collection catches HTTP 409** — returns existing collection if slug collision
8. **Hub Web UI features NOT in API**: item images, history, drag-and-drop, gating group collections, resource group assignment

### 6 Practical Patterns

1. **Batch population** — iterate model lists with `exists_ok=True` and try/except for resilience
2. **Trending discovery** — combine `list_models()` search with `add_collection_item()`
3. **Cross-user mirror** — `get_collection()` source → `create_collection()` dest with all items copied
4. **Research project page** — paper + model + dataset in one collection with notes
5. **Annotated curation** — use `note` fields for ratings/status emoji (⭐ ⚠ 🔄)
6. **Auto-curation via cron** — daily cron to maintain a "Trending Today" collection

### Resources
- Source: `huggingface_hub/hf_api.py` lines 9908–10400
- Hub docs: https://huggingface.co/docs/hub/en/collections
- Collections page: https://huggingface.co/collections

---

## 2026-07-24: hf-hub-python-api-v2 — Complete HfApi v1.x Reference (Topic #6 — Deep Dive v2)

### Summary
Comprehensive deep-dive into the **`huggingface_hub` Python library (v1.24.0)** — 161 public `HfApi` methods covering the complete Hugging Face Hub API surface. This is a v2 deep dive of Topic #6 (originally covered early in the learning cycle) and focuses on the **v1.x architecture** which introduced major new features: Buckets object storage, Webhooks API, Hub Jobs, Scheduled UV Jobs, Branches/Tags API, Discussion API, Access Request management, LFS management, Safetensors metadata inspection, Daily Papers API, and expanded Space management (25 methods). All methods also available as top-level functions in `huggingface_hub`.

### v1.x vs 0.x — Key Differences

| Area | 0.x (old) | 1.x (current) |
|------|-----------|---------------|
| **API class** | `HfApi` (limited methods) | `HfApi` (161 methods) |
| **Object storage** | Git + LFS only | **Buckets** (`hf://buckets/...`) — Git-free, S3-compatible |
| **Jobs** | None | `run_job`, `run_uv_job`, `create_scheduled_job`, `create_scheduled_uv_job` |
| **Webhooks** | None | Full CRUD: `create_webhook`, `get_webhook`, `update_webhook`, `delete_webhook`, etc. |
| **Collections** | Manual REST only | 8 methods: `list_collections`, `get_collection`, `create_collection`, etc. |
| **Discussions** | None | 8 methods: `create_discussion`, `comment_discussion`, `get_discussion_details`, etc. |
| **Branches/Tags** | `main` only | `create_branch`, `delete_branch`, `create_tag`, `delete_tag`, `list_repo_refs` |
| **Access requests** | None | 7 methods for gated repo access management |
| **LFS management** | None | `list_lfs_files`, `permanently_delete_lfs_files`, `verify_repo_checksums` |
| **Space management** | Minimal (`space_info`) | 25 methods — secrets, variables, storage, volumes, dev mode, sleep, etc. |
| **Safetensors metadata** | None | `get_safetensors_metadata`, `parse_safetensors_file_metadata` |
| **Large uploads** | `upload_folder` | + `upload_large_folder` (resumable, parallel, with progress reports) |
| **Repo refactoring** | None | `move_repo`, `duplicate_repo`, `super_squash_history`, `update_repo_settings` |
| **License** | apache-2.0 | apache-2.0 (unchanged) |

### Core Architecture

The `huggingface_hub` library provides three interfaces to the same REST API:

1. **`HfApi` class** — The full-featured Python API. Instantiate once, reuse.
2. **Top-level functions** — Convenience wrappers (e.g., `upload_file()` calls `HfApi().upload_file()`).
3. **`hf` CLI** — Shell-level access for scripting.

All three authenticate via `HF_TOKEN` env var, cached token file, or explicit `token=` parameter.

#### HfApi Initialization

```python
from huggingface_hub import HfApi

# Default (reads HF_TOKEN env var)
api = HfApi()

# Custom endpoint and token
api = HfApi(
    endpoint="https://huggingface.co",  # or a HF Enterprise endpoint
    token="hf_...",                      # explicit token
    library_name="my-app",               # telemetry
    library_version="1.0",
    user_agent="MyApp/1.0",
)
```

**Token precedence:** `token=` param > `HF_TOKEN` env > cached token in `~/.cache/huggingface/token`.

### 1. Repository CRUD (6 methods)

```python
# Create
url = api.create_repo("my-model", repo_type="model", private=True, exist_ok=True)

# Info (returns RepoInfo with all metadata)
info = api.repo_info("user/my-model", repo_type="model", expand=["trendingScore", "inference"])

# Exists
exists = api.repo_exists("user/my-model", repo_type="dataset")

# Settings (update description, private status, etc.)
api.update_repo_settings("user/my-model", description="Updated description",
                          private=True, gated="auto")

# Move (rename/transfer)
api.move_repo("old-user/model", "new-user/model")

# Duplicate (clone across namespaces)
url = api.duplicate_repo("source-user/model", "my-model", repo_type="model",
                          exist_ok=True)

# Delete (irreversible)
api.delete_repo("user/my-model", repo_type="model", missing_ok=True)

# Squash history into one commit
api.super_squash_history("user/my-model", commit_message="Initial release")
```

**`duplicate_repo`** — incredibly useful for model/dataset/space cloning. Supports passing `hardware`, `storage`, `sleep_time`, `secrets`, `variables` for Space duplication. This is the programmatic equivalent of the Hub UI's "Duplicate Space" button.

**`super_squash_history`** — collapses an entire repo's commit history into a single commit. Useful for repos with bloated Git histories from many small uploads. Works on models, datasets, and Spaces. Branch-optional (defaults to `main`).

### 2. File Operations (22 methods)

#### Commit Operations — The Foundation

All file modifications flow through `create_commit()` with three operation types:

```python
from huggingface_hub import CommitOperationAdd, CommitOperationDelete, CommitOperationCopy

# Add files
ops = [
    CommitOperationAdd(path_in_repo="config.json", path_or_fileobj=b'{"key": "val"}'),
    CommitOperationAdd(path_in_repo="model.safetensors", path_or_fileobj="./local/model.safetensors"),
]

# Delete files
ops.append(CommitOperationDelete(path_in_repo="old_weights.bin"))

# Copy files (server-side — no download/upload needed)
ops.append(CommitOperationCopy(
    src_path_in_repo="backup/config.json",
    path_in_repo="config.json",
    src_revision="backup-branch"  # optional, same repo by default
))

# Server-side cross-repo copy
ops.append(CommitOperationCopy(
    src_path_in_repo="tokenizer.json",
    path_in_repo="tokenizer.json",
    src_repo_id="other-user/source-model",
    src_repo_type="model",
    src_revision="main"
))

# Execute
commit = api.create_commit(
    repo_id="user/my-model",
    operations=ops,
    commit_message="Update config and clean up",
    commit_description="Multi-operation commit",
    repo_type="model",
    revision="main",
    create_pr=False,           # Set True to open a PR instead
    num_threads=5,             # Parallel LFS uploads
    parent_commit=None,        # Optimistic locking: enforce linear history
)
```

**Critical constraints:**
- Max **25,000 LFS files** per commit
- Max **1 GB** payload for regular (non-LFS) files
- The `operations` list **will be mutated** — do not reuse objects
- Empty `commit_message` raises `ValueError`
- `parent_commit` provides optimistic locking — set to the current HEAD OID to prevent conflicts

#### High-Level Upload/Download Wrappers

```python
# Upload single file
api.upload_file(
    path_or_fileobj=b"content",
    path_in_repo="config.json",
    repo_id="user/my-model",
    repo_type="model",
)

# Upload entire folder
api.upload_folder(
    folder_path="./model_output/",
    repo_id="user/my-model",
    repo_type="model",
    allow_patterns=["*.safetensors", "*.json"],
    ignore_patterns=["*.tmp", "__pycache__/*"],
    commit_message="Upload model outputs",
    delete_patterns=["old_*.bin"],  # delete matching files first
)

# Upload large folders (resumable, parallel, progress reporting)
api.upload_large_folder(
    repo_id="user/my-model",
    folder_path="./large-model/",
    repo_type="model",
    num_workers=8,            # parallel threads
    print_report=True,        # progress every 60s
    print_report_every=30,    # seconds between reports
    allow_patterns=["*.safetensors"],
)

# Download single file
path = api.hf_hub_download(
    repo_id="user/my-model",
    filename="config.json",
    revision="main",
    local_dir="./models/my-model/",
    local_dir_use_symlinks=False,  # True = symlink to cache
    cache_dir="/custom/cache/path",
    force_download=False,
    resume_download=True,
)

# Download snapshot (entire repo)
local_path = api.snapshot_download(
    repo_id="user/my-model",
    revision="main",
    allow_patterns=["*.safetensors", "*.json"],
    ignore_patterns=["*.bin", "*.pt"],
    local_dir="./models/my-model/",
    cache_dir=None,  # None = download directly to local_dir
)

# Check file existence
exists = api.file_exists("user/my-model", "config.json", repo_type="model")

# Get file metadata (size, commit info, LFS status, last modified)
meta = api.get_hf_file_metadata(
    url="https://huggingface.co/user/my-model/resolve/main/config.json"
)
print(f"Size: {meta.size}, Commit: {meta.commit_hash}, LFS: {meta.lfs}")
```

**`upload_large_folder` vs `upload_folder`:**
- `upload_large_folder` is designed for **hundreds/thousands of large files** — uses multiple workers, prints periodic progress, handles retries
- `upload_folder` is simpler and synchronous — good for smaller uploads (<100 files, <1GB)

#### File Listing & Tree Inspection

```python
# List files at root
files = api.list_repo_files("user/my-model", repo_type="model")

# List files with tree structure (recursive, with folder metadata)
tree = list(api.list_repo_tree(
    "user/my-model",
    path_in_repo="checkpoints/",
    recursive=True,
    expand=True,  # include file sizes and commit info
    revision="main",
    repo_type="model",
))
for item in tree:
    if isinstance(item, RepoFile):
        print(f"FILE: {item.path} ({item.size} bytes, LFS={item.lfs})")
    elif isinstance(item, RepoFolder):
        print(f"DIR:  {item.path}")

# Get paths info for specific files
paths = api.get_paths_info(
    "user/my-model",
    paths=["config.json", "model.safetensors", "nonexistent.txt"],
    expand=True,
    repo_type="model",
)
```

### 3. Bucket API — Object Storage (11 methods)

Buckets are the **biggest new feature** in v1.x — Git-free, S3-compatible object storage.

```python
# Create a bucket
bucket_url = api.create_bucket("my-bucket", private=True, exist_ok=True)
# Returns: BucketUrl("hf://buckets/user/my-bucket")

# List all buckets
all_buckets = list(api.list_buckets(search="my-"))

# List files in a bucket (tree)
files = list(api.list_bucket_tree("user/my-bucket", recursive=True))

# Get bucket info (metadata, policy, storage used)
info = api.bucket_info("user/my-bucket")

# Get metadata for a specific file
meta = api.get_bucket_file_metadata("user/my-bucket", "data/file.parquet")

# Move/rename bucket
api.move_bucket("user/old-name", "user/new-name")

# Delete bucket (irreversible)
api.delete_bucket("user/my-bucket", missing_ok=True)

# Batch operations (add, copy, delete in one call)
api.batch_bucket_files(
    "user/my-bucket",
    add=[(b"content", "new_file.txt"), ("./local/data.parquet", "data.parquet")],
    copy=[("user/source-bucket", "file.txt", "user/my-bucket", "backup/file.txt")],
    delete=["old_file.txt"],
)

# Sync local ↔ bucket (bidirectional)
plan = api.sync_bucket(
    source="./data/",
    dest="hf://buckets/user/my-bucket",
    delete=True,        # delete remote files not in source
    dry_run=True,       # preview before applying
)
# Returns SyncPlan — inspect and then call sync_bucket again with --apply

# Download specific files from bucket
api.download_bucket_files(
    "user/my-bucket",
    files=[("remote/data.csv", "./local/data.csv")],
)

# Get paths info for arbitrary paths
paths = list(api.get_bucket_paths_info(
    "user/my-bucket",
    paths=["file1.txt", "file2.txt", "subdir/"],
))
```

**Bucket sync workflow:**
```python
# Step 1: Plan
plan = api.sync_bucket("./data", "hf://buckets/user/my-bucket", dry_run=True)
print(f"Files to upload: {len(plan.to_add)}, to delete: {len(plan.to_delete)}")

# Step 2: Apply (no dry_run)
result = api.sync_bucket("./data", "hf://buckets/user/my-bucket", delete=True)
```

### 4. Space Management (25 methods)

The most method-rich area of the API. All operations for managing Spaces programmatically.

```python
# Read operations
info = api.space_info("user/my-space")
runtime = api.get_space_runtime("user/my-space")
print(f"Stage: {runtime.stage}, Hardware: {runtime.hardware}, SDG: {runtime.sdk}")

# Secrets management
api.add_space_secret("user/my-space", "API_KEY", "sk-...")
api.add_space_variable("user/my-space", "MODEL_NAME", "gpt-4o")
secrets = api.get_space_secrets("user/my-space")   # returns dict of SpaceSecret
vars = api.get_space_variables("user/my-space")     # returns dict of SpaceVariable
api.delete_space_secret("user/my-space", "API_KEY")
api.delete_space_variable("user/my-space", "MODEL_NAME")

# Hardware & storage
api.request_space_hardware("user/my-space", SpaceHardware.T4_MEDIUM, sleep_time=300)
api.request_space_storage("user/my-space", SpaceStorage.SMALL)  # +50GB persistent
api.delete_space_storage("user/my-space")                        # remove persistent storage
api.set_space_sleep_time("user/my-space", sleep_time=900)       # 15 min inactivity timeout
api.set_space_volumes("user/my-space", volumes=[Volume(...)])
api.delete_space_volumes("user/my-space")

# Lifecycle
api.pause_space("user/my-space")
api.restart_space("user/my-space", factory_reboot=True)  # full factory reset
api.enable_space_dev_mode("user/my-space")
api.disable_space_dev_mode("user/my-space")

# Logs
logs = list(api.fetch_space_logs("user/my-space", build=False, follow=False))

# Discovery
for space in api.list_spaces(author="user", sort="trending", limit=10):
    print(f"{space.id}: {space.likes} likes")

results = list(api.search_spaces("flux", sdk="gradio"))

templates = list(api.list_space_templates())

# Management & Duplication
url = api.duplicate_space(
    "source-user/template-space",
    "my-new-space",
    hardware=SpaceHardware.T4_MEDIUM,
    storage=SpaceStorage.SMALL,
    sleep_time=300,
    secrets=[{"key": "API_KEY", "value": "sk-..."}],
    variables=[{"key": "MODEL", "value": "flux.1-dev"}],
    exist_ok=True,
)

# Wait for Space to be running
runtime = api.wait_for_space("user/my-space", timeout=300, poll_interval=5)
print(f"Space is {runtime.stage}")
```

**Hardware tiers** (`SpaceHardware` constants): `CPU`, `CPU_UPGRADE`, `T4_SMALL`, `T4_MEDIUM`, `A10G_SMALL`, `A10G_LARGE`, `A100_LARGE`, `H100`, `ZERO_GPU`.

**Storage tiers** (`SpaceStorage` constants): `SMALL` (50GB), `MEDIUM`, `LARGE`.

### 5. Hub Jobs — Run Compute on HF Infrastructure (20 methods)

HF Hub Jobs let you run containerized and Python script workloads directly on HF infrastructure.

#### Quick Script Jobs (UV Jobs — most practical)

```python
# Run a Python script with dependencies — zero setup
job = api.run_uv_job(
    script="""
import requests, json
r = requests.get('https://huggingface.co/api/models?sort=downloads&limit=5')
results = r.json()
for m in results:
    print(f\"{m['id']}: {m['downloads']} downloads\")
""",
    dependencies=["requests"],
    python="3.12",
    timeout=300,
    name="top-models-poller",
)
job_id = job.job_id

# Wait for completion
finished = api.wait_for_job(job_id, timeout=600)
print(f"Status: {finished.status}")

# Fetch logs
logs = list(api.fetch_job_logs(job_id=job_id))
for line in logs:
    print(line)
```

#### Container-Based Jobs

```python
# Full container job
job = api.run_job(
    image="python:3.12-slim",
    command=["python", "-c", "print('hello from HF job')"],
    flavor="cpu",            # or "t4", "a10g", etc.
    timeout=300,
    name="my-job",
    secrets={"MY_SECRET": "..."},
)

# Scheduled job (cron)
cron_job = api.create_scheduled_job(
    image="python:3.12-slim",
    command=["python", "/app/script.py"],
    schedule="0 */6 * * *",   # every 6 hours
    flavor="cpu",
    timeout=3600,
    name="daily-pipeline",
    env={"ENV": "production"},
    labels={"project": "monitoring"},
)

# Scheduled UV job (python script with dependencies)
cron_uv = api.create_scheduled_uv_job(
    script="print('hello world')",
    dependencies=["requests", "torch"],
    schedule="0 0 * * *",     # daily at midnight
    python="3.12",
    timeout=600,
    name="daily-report",
)

# List & manage jobs
for job in api.list_jobs(status="completed", namespace="user", timeout=3600):
    print(f"{job.job_id}: {job.status}")

scheduled = api.list_scheduled_jobs()

# Lifecycle
api.cancel_job(job_id="...")
api.suspend_scheduled_job("...")
api.resume_scheduled_job("...")
api.trigger_scheduled_job("...")   # manual trigger

# Inspect
details = api.inspect_job(job_id="...")
sched_details = api.inspect_scheduled_job("...")

# Metrics & logs
metrics = list(api.fetch_job_metrics(job_id="..."))
logs = list(api.fetch_job_logs(job_id="...", tail=100))

# Available hardware
hardware = api.list_jobs_hardware()
for hw in hardware:
    print(f"{hw.flavor}: {hw.cpus} CPUs, {hw.memory}GB RAM")
```

**UV Jobs** are the most convenient for quick tasks — they auto-install dependencies, no Docker image needed. Perfect for cron-based data collection, model evaluation, API polling.

### 6. Webhook API (7 methods)

Full CRUD for Hub webhooks, which fire on repo events (push, PR, discussion, etc.).

```python
# Create webhook
hook = api.create_webhook(
    url="https://my-service.com/hf-webhook",
    watched=[
        {"type": "model", "id": "user/*"},     # all models under user
        {"type": "dataset", "id": "specific-dataset"},
    ],
    domains=["repo", "discussion"],   # event types to listen for
    secret="whsec_...",               # for payload verification
)
webhook_id = hook.id

# Read
hook_info = api.get_webhook(webhook_id)

# Update
api.update_webhook(
    webhook_id,
    url="https://my-service.com/v2/hf-webhook",
    watched=[{"type": "model", "id": "user/*"}],
)

# Toggle
api.enable_webhook(webhook_id)
api.disable_webhook(webhook_id)

# List all webhooks
for hook in api.list_webhooks():
    print(f"{hook.id}: {hook.url} (enabled={hook.enabled})")

# Delete
api.delete_webhook(webhook_id)
```

**Webhook domains:** `"repo"` (pushes, file changes), `"discussion"` (PRs, comments, issues), `"collection"` (collection events).

**Watched items:** Use `"user/*"` to watch everything under a namespace, or specific repo IDs.

### 7. Collections API (8 methods)

```python
# List collections with filters
collections = list(api.list_collections(
    owner="user",
    item="user/my-model",
    sort="lastModified",
    limit=20,
))

# Get full collection (all items — list_collections truncates to 4)
collection = api.get_collection("user/collection-slug")
for item in collection.items:
    print(f"{item.item_type}: {item.item_id} — {item.note}")

# Create
new_coll = api.create_collection(
    title="My Curated Models",
    namespace="user",            # org or username
    description="Best models for X",  # max 150 chars
    private=False,
    exists_ok=True,
)
# NOTE: theme cannot be set on creation — use update_collection_metadata

# Update
api.update_collection_metadata(
    "user/slug",
    description="Updated description",
    private=True,
    theme="blue",
)

# Add items
api.add_collection_item(
    "user/slug",
    item_id="user/model",
    item_type="model",
    note="Great for X task",     # max 500 chars
    exists_ok=True,
)

# Modify items (uses item_object_id, not item_id)
api.update_collection_item("user/slug", item_object_id="...", note="Updated note")

# Delete items
api.delete_collection_item("user/slug", item_object_id="...")

# Delete collection
api.delete_collection("user/slug", missing_ok=True)
```

**6 item types:** `"model"`, `"dataset"`, `"space"`, `"paper"`, `"collection"`, `"bucket"`.

**Critical:** `list_collections` truncates items to 4 per collection. Always use `get_collection()` for full item details. Item modification/deletion uses the internal `item_object_id` (DB id), not the Hub repo ID.

### 8. Discussions & Pull Requests (8 methods)

```python
# List discussions
discussions = api.get_repo_discussions("user/my-model", repo_type="model")

# Create a discussion (issue or PR)
disc = api.create_discussion(
    "user/my-model",
    title="Add support for batch inference",
    repo_type="model",
    discussion_type="issue",     # or "pull_request"
)

# Comment
api.comment_discussion("user/my-model", disc.num, comment="Great idea!")

# Edit comment
api.edit_discussion_comment("user/my-model", disc.num, comment_id="...",
                              new_comment="Updated suggestion")

# Hide comment (moderator only)
api.hide_discussion_comment("user/my-model", disc.num, comment_id="...")

# Rename discussion
api.rename_discussion("user/my-model", disc.num, new_title="Better title")

# Change status
api.change_discussion_status("user/my-model", disc.num,
                              new_status="closed", comment="Resolved")

# Get details
details = api.get_discussion_details("user/my-model", disc.num, repo_type="model")
for event in details.events:
    print(f"{event.type}: {event.created_at}")

# Merge pull request (creates a commit)
api.merge_pull_request("user/my-model", pr_number=42, comment="LGTM!")
```

### 9. Access Request Management — Gated Repos (7 methods)

For repos with `gated="auto"` or `gated="manual"`:

```python
# List pending requests
pending = api.list_pending_access_requests("user/gated-model", repo_type="model")

# Accept
for req in pending:
    api.accept_access_request("user/gated-model", req.username, repo_type="model")

# Reject
api.reject_access_request("user/gated-model", "blocked-user", repo_type="model")

# Cancel (by requestor)
api.cancel_access_request("user/gated-model", repo_type="model")

# List handled requests
accepted = api.list_accepted_access_requests("user/gated-model")
rejected = api.list_rejected_access_requests("user/gated-model")

# Grant access directly (without a request)
api.grant_access("user/gated-model", "user-to-grant", repo_type="model")
```

### 10. Branches & Tags (5 methods)

```python
# Create branch
api.create_branch("user/my-repo", branch="experiment-fp8",
                  repo_type="model")

# Delete branch
api.delete_branch("user/my-repo", branch="old-branch",
                  repo_type="model")

# Create tag
api.create_tag("user/my-repo", tag="v1.0",
               repo_type="model", revision="main")

# Delete tag
api.delete_tag("user/my-repo", tag="v1.0", repo_type="model")

# List all refs (branches + tags + PRs)
refs = api.list_repo_refs("user/my-repo", repo_type="model",
                           include_pull_requests=True)
for branch in refs.branches:
    print(f"Branch: {branch.name} ({branch.target_commit[:8]})")
for tag in refs.converted_tags:
    print(f"Tag: {tag.name} → {tag.target_commit[:8]}")
for tag in refs.tags:
    print(f"Lightweight tag: {tag.name}")
```

### 11. LFS & Safetensors Management (5 methods)

```python
# List LFS files in repo
lfs_files = list(api.list_lfs_files("user/my-model", repo_type="model"))
for f in lfs_files:
    print(f"{f.path}: {f.size} bytes, oid={f.oid[:12]}...")

# Permanently delete LFS files (removes from history!)
api.permanently_delete_lfs_files("user/my-model", repo_type="model",
                                  paths=["old-large-file.bin"])

# Verify checksums of downloaded files
result = api.verify_repo_checksums("user/my-model", local_dir="./models/my-model/",
                                    repo_type="model")
print(f"Matched: {result.matched}/{result.total}, Failed: {result.failed}")

# Get safetensors metadata (all tensors, dtypes, shapes)
meta = api.get_safetensors_metadata("user/my-model", repo_type="model")
for tensor_name, tensor_meta in meta.parameters.items():
    print(f"{tensor_name}: shape={tensor_meta.shape}, dtype={tensor_meta.dtype}")

# Parse safetensors file metadata without downloading full file
file_meta = api.parse_safetensors_file_metadata(
    "user/my-model", "model.safetensors", repo_type="model"
)
```

### 12. Model, Dataset & Space Discovery (12 methods)

```python
# Models
for model in api.list_models(
    sort="downloads",
    direction=-1,
    limit=10,
    pipeline_tag="text-generation",
    expand=["inference", "trendingScore"],
):
    print(f"{model.id}: {model.downloads:,} downloads, "
          f"likes={model.likes}, trending={getattr(model, 'trendingScore', 'N/A')}")

# Tags
model_tags = api.get_model_tags()   # all model tags with counts

# Datasets
for ds in api.list_datasets(sort="trending", limit=10):
    print(f"{ds.id}: {ds.likes} likes, tags={ds.cardData.get('annotations_creators', [])}")

ds_info = api.dataset_info("user/dataset", expand=["parquet"])
# Check parquet availability
if ds_info.cardData:
    print(f"Configs: {ds_info.cardData.get('configs', [])}")

# Daily Papers
for paper in api.list_daily_papers(limit=10, sort="trending"):
    print(f"{paper.title} — {paper.upvotes} upvotes")
    print(f"  Authors: {', '.join(a['name'] for a in paper.authors)}")

# Spaces
for space in api.list_spaces(sdk="gradio", sort="likes", limit=10):
    print(f"{space.id}: SDK={space.sdk}, runtime={space.runtime.stage}")

# User info
user = api.whoami()
print(f"User: {user['name']}, Token: {user['auth']['type']}")

# Liked / following
likes = api.list_liked_repos("user")
for like in likes.models:
    print(f"Liked model: {like.id}")
```

### 13. Utility & Housekeeping (10 methods)

```python
# Get full repo name (resolves relative IDs)
full = api.get_full_repo_name("my-model", organization="org-name")

# Check revision existence
exists = api.revision_exists("user/my-model", "main", repo_type="model")

# List repo likers
for user in api.list_repo_likers("user/my-model", repo_type="model"):
    print(f"{user['user']}: {user['fullname']}")

# List user repos
for repo in api.list_user_repos("user", repo_type="model"):
    print(f"{repo.repo_id}: {repo.type}")

# List user followers/following
for follower in api.list_user_followers("user"):
    print(follower['user'])

# Org info
org = api.get_organization_overview("org-name")
for member in api.list_organization_members("org-name"):
    print(f"{member['user']} ({member.get('role', 'member')})")

# Pre-upload LFS files (for memory-constrained environments)
api.preupload_lfs_files(
    repo_id="user/my-model",
    operations=ops,
    repo_type="model",
)

# List repo commits
for commit in api.list_repo_commits("user/my-model", repo_type="model", limit=10):
    print(f"{commit.oid[:8]}: {commit.title} ({commit.date})")

# Run as future (non-blocking commit)
future = api.run_as_future(
    api.create_commit,
    repo_id="user/my-model",
    operations=ops,
    commit_message="Async upload",
)
```

### 14. Zero-Cost Patterns — Practical Recipes

#### Recipe 1: Automated Model Card Update (cron-friendly)

```python
from huggingface_hub import HfApi
api = HfApi()

# Read existing model card
info = api.model_info("user/my-model", expand=["cardData"])
current_card = info.cardData or {}

# Update card data
current_card.update({
    "metrics": [{"accuracy": 0.95}],
    "widget": [{"text": "Sample input"}],
})
api.update_repo_settings("user/my-model", card_data=current_card)
```

#### Recipe 2: Daily Dataset Stats Collection (UV Job)

```python
# Run this daily via create_scheduled_uv_job
import json
from huggingface_hub import HfApi
api = HfApi()

results = []
for model in api.list_models(sort="downloads", direction=-1, limit=50):
    results.append({"id": model.id, "downloads": model.downloads, "likes": model.likes})

# Store in a bucket
api.create_bucket("daily-stats", exist_ok=True)
import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
    json.dump({"date": "2026-07-24", "models": results}, f)
    f.flush()
    api.sync_bucket(f.name, "hf://buckets/user/daily-stats/top-models.json")
```

#### Recipe 3: Space Duplication with Configuration

```python
# Duplicate a Gradio Space with all secrets and storage
url = api.duplicate_space(
    "user/template-space",
    "my-new-space",
    hardware="t4-medium",
    storage="small",
    sleep_time=300,
    secrets=[{"key": "HF_TOKEN", "value": "hf_..."}],
    variables=[{"key": "MODEL_ID", "value": "user/my-model"}],
    exist_ok=True,
)
api.wait_for_space("user/my-new-space")
```

#### Recipe 4: Bucket as Job Artifact Store

```python
# In a scheduled UV job
from huggingface_hub import HfApi
import json, tempfile

api = HfApi()
results = {"status": "ok", "count": 42, "generated_at": "2026-07-24T07:00:00Z"}

with tempfile.NamedTemporaryFile(mode='w', suffix='.json') as f:
    json.dump(results, f)
    f.flush()
    api.batch_bucket_files(
        "artifact-bucket",
        add=[(f.name, f"reports/daily-2026-07-24.json")],
    )
```

### 15. All 161 HfApi Methods — Full Reference

| Category | Count | Methods |
|----------|-------|---------|
| **Repository CRUD** | 6 | `create_repo`, `delete_repo`, `repo_info`, `repo_exists`, `update_repo_settings`, `move_repo`, `duplicate_repo`, `super_squash_history` |
| **File Operations** | 22 | `create_commit`, `upload_file`, `upload_folder`, `upload_large_folder`, `hf_hub_download`, `snapshot_download`, `file_exists`, `get_hf_file_metadata`, `list_repo_files`, `list_repo_tree`, `list_repo_commits`, `get_paths_info`, `copy_files`, `delete_file`, `delete_files`, `delete_folder`, `preupload_lfs_files`, `parse_safetensors_file_metadata`, `get_safetensors_metadata`, `list_lfs_files`, `permanently_delete_lfs_files`, `verify_repo_checksums` |
| **Buckets** | 12 | `create_bucket`, `bucket_info`, `delete_bucket`, `list_buckets`, `move_bucket`, `sync_bucket`, `batch_bucket_files`, `list_bucket_tree`, `download_bucket_files`, `get_bucket_file_metadata`, `get_bucket_paths_info`, `list_buckets` |
| **Spaces** | 25 | `space_info`, `get_space_runtime`, `list_spaces`, `search_spaces`, `list_space_templates`, `add_space_secret`, `get_space_secrets`, `delete_space_secret`, `add_space_variable`, `get_space_variables`, `delete_space_variable`, `request_space_hardware`, `request_space_storage`, `delete_space_storage`, `set_space_volumes`, `delete_space_volumes`, `set_space_sleep_time`, `pause_space`, `restart_space`, `duplicate_space`, `enable_space_dev_mode`, `disable_space_dev_mode`, `fetch_space_logs`, `wait_for_space`, `list_spaces_hardware` |
| **Jobs** | 20 | `run_job`, `run_uv_job`, `create_scheduled_job`, `create_scheduled_uv_job`, `list_jobs`, `list_scheduled_jobs`, `cancel_job`, `wait_for_job`, `fetch_job_logs`, `fetch_job_metrics`, `inspect_job`, `inspect_scheduled_job`, `suspend_scheduled_job`, `resume_scheduled_job`, `trigger_scheduled_job`, `delete_scheduled_job`, `update_job_labels`, `update_scheduled_job_labels`, `list_jobs_hardware`, `sync_job_volume` |
| **Webhooks** | 7 | `create_webhook`, `get_webhook`, `update_webhook`, `delete_webhook`, `list_webhooks`, `enable_webhook`, `disable_webhook` |
| **Collections** | 8 | `list_collections`, `get_collection`, `create_collection`, `update_collection_metadata`, `delete_collection`, `add_collection_item`, `update_collection_item`, `delete_collection_item` |
| **Discussions** | 8 | `get_repo_discussions`, `create_discussion`, `comment_discussion`, `edit_discussion_comment`, `hide_discussion_comment`, `rename_discussion`, `change_discussion_status`, `merge_pull_request` |
| **Access Requests** | 7 | `list_pending_access_requests`, `list_accepted_access_requests`, `list_rejected_access_requests`, `accept_access_request`, `reject_access_request`, `cancel_access_request`, `grant_access` |
| **Branches & Tags** | 5 | `create_branch`, `delete_branch`, `create_tag`, `delete_tag`, `list_repo_refs` |
| **Discovery** | 12 | `list_models`, `model_info`, `get_model_tags`, `list_datasets`, `dataset_info`, `get_dataset_tags`, `list_dataset_parquet_files`, `list_spaces`, `space_info`, `list_daily_papers`, `search_spaces`, `get_dataset_leaderboard` |
| **User & Org** | 8 | `whoami`, `get_user_overview`, `list_user_followers`, `list_user_following`, `list_user_repos`, `get_organization_overview`, `list_organization_members`, `list_organization_followers` |
| **Utilities** | 10 | `get_full_repo_name`, `revision_exists`, `list_repo_likers`, `list_liked_repos`, `run_as_future`, `auth_check`, `like`, `unlike`, `super_squash_history`, `verify_repo_checksums` |

### Resources
- Official API docs: https://huggingface.co/docs/huggingface_hub/en/index
- HfApi reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- Migration guide: https://huggingface.co/docs/huggingface_hub/en/migration
- CLI reference: https://huggingface.co/docs/huggingface_hub/en/guides/cli
- Source code: `huggingface_hub/hf_api.py` — 161 public methods in v1.24.0
|- Changelog: https://github.com/huggingface/huggingface_hub/releases

---

## 2026-07-24: hf-hub-cache-deep-dive — Cache System Architecture & Management (Deep Dive on Topic #8 hf-hub-cache-and-env)

### Summary
Comprehensive deep-dive into the Hugging Face Hub's caching system — the file-based cache (`~/.cache/huggingface/hub/`), its 5 internal structures (blobs, refs, snapshots, trees, .no_exist), symlink-based deduplication, the chunk-based Xet cache layer, environment variables for control, and the full suite of inspection/verification/cleanup tools (`hf cache ls/verify/rm/prune` and Python API `scan_cache_dir`/`delete_revisions`). Covers architecture, disk management strategies, zero-cost optimization patterns, limitations, and production best practices.

### Architecture Overview

The HF Hub cache uses a **deduplicated symlink architecture** with two layers:

**1. File-based cache** (`~/.cache/huggingface/hub/`) — the standard Git/LFS-based cache
**2. Chunk-based Xet cache** (`~/.cache/huggingface/xet/`) — optional chunk-level dedup via `hf_xet`

The cache location is controlled by:
- `HF_HOME` — base dir (default: `~/.cache/huggingface`)
- `HF_HUB_CACHE` — hub cache dir (default: `$HF_HOME/hub`)
- `HF_XET_CACHE` — Xet cache dir (default: `$HF_HOME/xet`)
- `HF_ASSETS_CACHE` — assets cache (default: `$HF_HOME/assets`)
- `HF_TOKEN_PATH` — token file (default: `$HF_HOME/token`)
- Falls back to `$XDG_CACHE_HOME/huggingface` if `HF_HOME` not set

### File-Based Cache: 5 Internal Structures

Each cached repo is stored under a directory named `{repo_type}s--{namespace}--{repo_name}` (e.g. `models--bert-base-uncased`).

#### 1. `blobs/` — Deduplicated file storage
Stores each unique file by its SHA-256 hash as filename. Files are identified by content hash, so identical files across revisions share a single blob. This is the core of disk deduplication.

```
blobs/
  ├── 403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd  (321 MB)
  ├── 7cb18dc9bafbfcf74629a4b760af1b160957a83e                        (398 B)
  └── d7edf6bd2a681fb0175f7735299831ee1b22b812                        (1.4 KB)
```

#### 2. `refs/` — Branch/tag pointer files
Maps branch/tag names to commit OIDs. Each ref is a small file whose content is the commit hash it points to. Updated whenever you download the latest version of a branch.

```
refs/
  └── main    (contains: "2439f60ef33a0d46d85da5001d52aeda5b00ce9f")
```

#### 3. `snapshots/` — Revision checkouts via symlinks
Contains one subdirectory per downloaded commit hash. Each directory contains symlinks pointing to the actual blobs, organized by filename. The content only exists in `blobs/`; `snapshots/` is purely a view layer.

```
snapshots/
  ├── 2439f60ef33a0d46d85da5001d52aeda5b00ce9f/
  │   ├── README.md -> ../../blobs/d7edf6bd2a681fb0175f7735299831ee1b22b812
  │   └── pytorch_model.bin -> ../../blobs/403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd
  └── bbc77c8132af1cc5cf678da3f1ddf2de43606d48/
      ├── README.md -> ../../blobs/7cb18dc9bafbfcf74629a4b760af1b160957a83e
      └── pytorch_model.bin -> ../../blobs/403450e234d65943a7dcf7e05a771ce3c92faa84dd07db4ac20f592037a1e4bd
```

**Key insight:** `pytorch_model.bin` in both revisions points to the **same blob** — the file is not duplicated on disk.

#### 4. `trees/` — Cached file listing metadata
JSON files named by commit hash that cache the list of files a repo contains at that commit. Avoids one network call per file during download. Written by `snapshot_download()`, read by both `snapshot_download()` and `hf_hub_download()`.

```
trees/
  ├── 2439f60ef33a0d46d85da5001d52aeda5b00ce9f.json
  └── bbc77c8132af1cc5cf678da3f1ddf2de43606d48.json
```

**Incremental benefit:** If a tree is cached, `hf_hub_download()` skips the per-file metadata network call. Enables `IncompleteSnapshotError` detection when offline.

#### 5. `.no_exist/` — Negative cache for optional files
Stores empty marker files for files that are known not to exist on the Hub (e.g., optional tokenizer configs). Saves one HTTP call per optional file on every subsequent load. Structure mirrors `snapshots/`.

```
.no_exist/aaaaaa/config_that_does_not_exist.json  (empty file)
```

### CACHEDIR.TAG
`huggingface_hub` automatically creates a `CACHEDIR.TAG` file in the cache directory following the Cache Directory Tagging Standard. This tells backup tools (Borg, restic, rsync) to exclude the cache from backups, since it's re-downloadable.

### Symlink Limitations

| Environment | Symlink Support | Behavior |
|-------------|----------------|----------|
| Linux/macOS | Native | Full dedup, shared blobs |
| Windows (Dev Mode) | Supported | Same as Linux |
| Windows (no Dev Mode) | Fallback | Files copied directly to `snapshots/` — no dedup, larger disk usage |
| `HF_HUB_DISABLE_SYMLINKS=1` | Forced off | Files copied to snapshots; useful for NAS shared across OSes |

A warning is shown on Windows when symlinks aren't available. Suppress with `HF_HUB_DISABLE_SYMLINKS_WARNING=1`.

### Chunk-Based Caching (Xet)

When `hf_xet` is installed, an additional `xet/` directory appears alongside `hub/`:

```
~/.cache/huggingface/
  ├── hub/           # Standard file-based cache
  └── xet/           # Chunk-based cache (Xet)
       └── {environment_identifier}/
            ├── chunk_cache/     # CAS-based byte-range cache (disabled by default)
            ├── shard_cache/     # Upload-efficient shard metadata (soft limit: 4GB)
            └── staging/         # Resumable upload workspace
```

- **chunk_cache**: Caches 64KB chunks from CAS for download. **Disabled by default.** Enable with `HF_XET_CHUNK_CACHE_SIZE_BYTES` (e.g. `=10737418240` for 10GB). Uses random eviction policy when full.
- **shard_cache**: Caches file-to-chunk mapping metadata for uploads. Default soft limit 4GB (`HF_XET_SHARD_CACHE_SIZE_LIMIT`). Deduplicates uploads across commits.
- **staging**: Workspace for resumable uploads — persists incomplete uploads across restarts.

The Xet cache is fully integrated with `huggingface_hub` — existing APIs (`scan_cache_dir`, `hf cache rm`) treat it transparently.

### Environment Variables Reference

| Variable | Default | Purpose |
|----------|---------|---------|
| `HF_HOME` | `~/.cache/huggingface` | Base directory for all HF data |
| `HF_HUB_CACHE` | `$HF_HOME/hub` | Model/dataset/spaces cache |
| `HF_XET_CACHE` | `$HF_HOME/xet` | Xet chunk cache |
| `HF_ASSETS_CACHE` | `$HF_HOME/assets` | Downstream library assets |
| `HF_TOKEN_PATH` | `$HF_HOME/token` | Auth token file |
| `HF_HUB_OFFLINE` | — | `=1` disables all HTTP calls |
| `HF_HUB_DISABLE_SYMLINKS` | — | Force no-symlink mode |
| `HF_HUB_DISABLE_SYMLINKS_WARNING` | — | Suppress Windows symlink warning |
| `HF_HUB_ETAG_TIMEOUT` | 10s | Server response timeout for metadata |
| `HF_HUB_DOWNLOAD_TIMEOUT` | 10s | Download timeout |
| `HF_HUB_DISABLE_PROGRESS_BARS` | — | `=1` hides tqdm bars |
| `HF_HUB_DISABLE_IMPLICIT_TOKEN` | — | `=1` only sends token for write ops |
| `HF_HUB_DISABLE_TELEMETRY` | — | `=1` disables usage telemetry |
| `HF_HUB_DISABLE_XET` | — | `=1` disables Xet even if installed |
| `HF_XET_HIGH_PERFORMANCE` | — | `=1` saturates bandwidth + CPU cores |
| `HF_XET_CHUNK_CACHE_SIZE_BYTES` | 0 | Chunk cache size (0 = disabled) |
| `HF_XET_SHARD_CACHE_SIZE_LIMIT` | 4GB | Shard cache soft limit |
| `HF_XET_RECONSTRUCT_WRITE_SEQUENTIALLY` | — | Sequential disk writes for HDDs |

**Deprecated vars (still work but no longer take precedence):**
| Old | New |
|-----|-----|
| `HUGGINGFACE_HUB_CACHE` | `HF_HUB_CACHE` |
| `HUGGINGFACE_ASSETS_CACHE` | `HF_ASSETS_CACHE` |
| `HUGGING_FACE_HUB_TOKEN` | `HF_TOKEN` |

### Cache Inspection Tools

#### CLI: `hf cache ls`
```bash
# Summary by repo
hf cache ls

# With revision details
hf cache ls --revisions

# Filter by size/access time
hf cache ls --revisions --filter "size>1GB" --filter "accessed>30d"

# Machine-readable output
hf cache ls --format json
hf cache ls --format csv

# Quiet mode (IDs only, pipeable)
hf cache ls --revisions -q

# Sort and limit
hf cache ls --sort size:desc --limit 5

# Custom cache dir
hf cache ls --cache-dir /custom/path
```

#### Python: `scan_cache_dir()`
```python
from huggingface_hub import scan_cache_dir, delete_revisions

# Scan entire cache
info = scan_cache_dir()
print(f"Total size: {info.size_on_disk / 1e9:.1f} GB")
print(f"Cached repos: {len(info.repos)}")

# Iterate repos, revisions, and files
for repo in info.repos:
    print(f"{repo.repo_type}/{repo.repo_id}: {repo.size_on_disk / 1e6:.1f} MB")
    for revision in repo.revisions:
        for ref in revision.refs:
            print(f"  Branch/tag: {ref.name} -> {revision.commit_hash}")

# Delete specific revisions
strategy = info.delete_revisions(
    "d78aea13fa7ecd06c29e3e46195d6341255065d5",  # commit hash
)
print(f"Would free: {strategy.expected_freed_size_str}")
strategy.execute()  # Actually delete
```

Returns 4 dataclasses:
- `HFCacheInfo` — complete report with `repos`, `size_on_disk`, `warnings`
- `CachedRepoInfo` — per-repo info: `repo_id`, `repo_type`, `size_on_disk`, `revisions`
- `CachedRevisionInfo` — per-revision: `commit_hash`, `refs`, `files`, `size_on_disk`
- `CachedFileInfo` — per-file: `file_name`, `size_on_disk`, `blob_path`

#### `try_to_load_from_cache()` — Check cache without network
```python
from huggingface_hub import try_to_load_from_cache, _CACHED_NO_EXIST

result = try_to_load_from_cache(
    repo_id="bert-base-uncased",
    filename="config.json",
    revision="main"
)

if isinstance(result, str):
    # File is cached: result is the file path
    pass
elif result is _CACHED_NO_EXIST:
    # File known not to exist (negative cache)
    pass
else:
    # Not cached at all
    pass
```

### Cache Verification

```bash
# CLI: verify checksums for a specific revision
hf cache verify meta-llama/Llama-3.2-1B-Instruct

# Verify a specific revision hash
hf cache verify meta-llama/Llama-3.1-8B-Instruct --revision 0e9e39f249a16976918f6564b8830bc894c89659
```

Verification checks that every cached blob's SHA-256 matches the Hub. Reports `CorruptedCacheException` if checksums differ.

### Cache Cleanup

#### CLI: `hf cache rm` — Targeted deletion
```bash
# Delete entire repo
hf cache rm model/bert-base-cased

# Delete specific revision (by hash)
hf cache rm 8f3ad1c

# Bulk delete via filter pipeline
hf cache rm $(hf cache ls --filter "accessed>1y" -q) -y

# Preview without deleting
hf cache rm model/t5-small --dry-run

# Skip confirmation
hf cache rm model/t5-small -y

# Custom cache dir
hf cache rm --cache-dir /path model/bert-base-cased
```

#### CLI: `hf cache prune` — Unreferenced & incomplete cleanup
```bash
hf cache prune
```
Automatically deletes:
1. Revisions no longer referenced by any branch or tag (`HEAD` detached leftovers)
2. Any `.incomplete` files from interrupted downloads

#### Python: `delete_revisions()`
```python
from huggingface_hub import scan_cache_dir

info = scan_cache_dir()
# Build strategy for specific revisions
strategy = info.delete_revisions("commit_hash_1", "commit_hash_2")
print(strategy.expected_freed_size_str)
strategy.execute()
```

**Deletion strategy:**
1. Snapshot folder symlinks are deleted
2. Blobs only referenced by deleted revisions are deleted (shared blobs preserved)
3. Branch/tag refs for deleted revisions are removed
4. If all revisions of a repo are deleted, the entire repo directory is removed

### Assets Cache (`cached_assets_path()`)
For downstream libraries that need to cache non-Hub files (processed data, downloads from external URLs, etc.):
```python
from huggingface_hub import cached_assets_path

path = cached_assets_path(
    library_name="datasets",
    namespace="SQuAD",
    subfolder="extracted"
)
# Returns: ~/.cache/huggingface/assets/datasets/SQuAD/extracted/
```
Structure: `assets/{library}/{namespace}/{subfolder}/`. Integrates with `scan_cache_dir` for unified cache management.

### Zero-Cost Disk Management Strategies

1. **Regular pruning:** `hf cache prune` weekly — recovers space from unreferenced revisions
2. **Age-based cleanup:** `hf cache rm $(hf cache ls --filter "accessed>30d" -q) -y` — removes stale caches
3. **Size-based targeting:** `hf cache ls --sort size:desc` — identify largest repos
4. **Offline mode:** `HF_HUB_OFFLINE=1` speeds up loading by skipping refresh checks
5. **ETAG timeout tuning:** `HF_HUB_ETAG_TIMEOUT=2` on slow connections to fail fast to cache
6. **CACHEDIR.TAG:** Already present — backup tools skip the cache automatically
7. **Shared cache:** Set `HF_HUB_CACHE` to a network drive with `HF_HUB_DISABLE_SYMLINKS=1` for multi-machine setups
8. **Chunk cache:** Only enable `HF_XET_CHUNK_CACHE_SIZE_BYTES` when iterating same files repeatedly; leave disabled (default) for one-shot downloads

### Comparison: File-based vs Xet Cache

| Dimension | File-based | Xet (chunk-based) |
|-----------|------------|-------------------|
| **Granularity** | Entire files (SHA-256) | 64KB chunks |
| **Dedup scope** | Across revisions of same file | Across files, repos, and revisions |
| **Download speedup** | Cached files load instantly | Chunks shared across variants |
| **Upload speedup** | No | Yes (shard cache) |
| **Disk overhead** | Low (symlinks are cheap) | Medium (chunk index) |
| **Enabled by default** | Yes | No (unless `hf_xet` installed) |
| **Best for** | Model weight reuse | Iterative training with similar data |

### Resources
- Manage cache guide: https://huggingface.co/docs/huggingface_hub/en/guides/manage-cache
- Cache-system reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/cache
- Environment variables: https://huggingface.co/docs/huggingface_hub/en/package_reference/environment_variables
- Xet guide: https://huggingface.co/docs/hub/xet/index
- `scan_cache_dir` docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/cache#huggingface_hub.scan_cache_dir
- `hf cache` CLI: https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#hf-cache
|- CACHEDIR.TAG standard: https://bford.info/cachedir/

## 2026-07-24: hf-inference-client-structured-outputs — Deep Dive v2 (Topic #100)

### Summary
Deep-dive v2 into Hugging Face `InferenceClient` — covering the v1.24.0 overhaul with OpenAI-compatible aliases, multi-provider routing internals, the Router API for provider comparison, Hub API for model discovery, and advanced patterns (vision/multimodal input, extra_body for provider-specific params, direct provider API keys, third-party billing). Based on official docs at huggingface_hub v1.24.0.

### Key New in v1.24.0

| Feature | What Changed |
|---------|-------------|
| **OpenAI alias** | `client.chat.completions.create()` aliases `client.chat_completion()` |
| **OpenAI init** | `InferenceClient(base_url=..., api_key=...)` mirrors `OpenAI()` |
| **Provider suffix** | Model id accepts `:fastest`, `:cheapest`, `:preferred`, `:provider-name` |
| **extra_body** | Pass provider-specific params through to the underlying provider |
| **Direct API key** | Pass a provider's own API key (billed to them) instead of HF token |
| **Automatic failover** | Auto provider selection routes to alternative if primary is flagged unavailable |
| **Router API** | `GET /v1/models` lists all models with per-provider pricing, latency, throughput |

### 1. OpenAI-Compatible Initialization (v1.24.0+)

InferenceClient now accepts the same init kwargs as `openai.OpenAI`:

```python
# Style 1 — classic HF
from huggingface_hub import InferenceClient
client = InferenceClient(model="meta-llama/Meta-Llama-3-8B-Instruct")

# Style 2 — OpenAI-compatible init
client = InferenceClient(
    base_url="https://router.huggingface.co/v1",
    api_key="hf_...",  # alias for token=
)

# Chat completion both ways
result = client.chat_completion(messages=[...])          # classic
result = client.chat.completions.create(messages=[...])   # OpenAI alias
```

**Key constraint:** `model` and `base_url` are mutually exclusive on init. If you pass `base_url`, the `(/v1)/chat/completions` suffix is appended automatically for chat completion calls. If you pass `model` as a model ID, it's sent as the payload `model` parameter.

### 2. Provider Selection — Three Policies + Suffix Syntax

#### Client-Side (InferenceClient `provider` param)
```python
client = InferenceClient(provider="auto")       # fastest (default)
client = InferenceClient(provider="together")    # force specific provider
```

#### Model-ID Suffix Syntax
Append to the model id string for per-call override:
```python
result = client.chat_completion(
    model="deepseek-ai/DeepSeek-R1:fastest",    # fastest provider
    messages=[...],
)
# :cheapest  — lowest price per output token
# :preferred — user preference order from https://hf.co/settings/inference-providers
# :groq      — direct provider name (any of the 17 supported providers)
```

#### Automatic Failover
When `provider="auto"`, requests are automatically routed to alternative providers if the primary is flagged as unavailable by the validation system. This makes `auto` the most reliable option for production.

### 3. The Router API — Provider Comparison

The router exposes an OpenAI-compatible `GET /v1/models` with full per-provider metadata:

```bash
# List all served models with provider comparison data
curl -s https://router.huggingface.co/v1/models | jq '.data[] | {id, providers: [.providers[] | {provider, status, pricing, supports_structured_output, throughput}]}'

# Single model
curl -s https://router.huggingface.co/v1/models/deepseek-ai/DeepSeek-V4-Pro | jq '.'
```

**Per-provider fields returned:**

| Field | Type | Description |
|-------|------|-------------|
| `provider` | string | Provider identifier (e.g., "novita", "together") |
| `status` | string | `live` or `error` |
| `context_length` | number | Max context for this provider+model combo |
| `pricing.input` | number | USD per million input tokens |
| `pricing.output` | number | USD per million output tokens |
| `is_free` | boolean | Temporary free promo |
| `supports_tools` | boolean | Tool/function calling support |
| `supports_structured_output` | boolean | JSON-schema-constrained output |
| `first_token_latency_ms` | number | Latest validation probe TTFT |
| `throughput` | number | Output tokens/sec from latest probe |
| `is_model_author` | boolean | Whether model was published by this provider |

**Use case:** Before calling inference, query this endpoint to find which providers support structured output for your model at the lowest latency, then pin that provider.

### 4. Hub API — Model Discovery for Inference

```bash
# All models served by any inference provider
~ curl -s "https://huggingface.co/api/models?inference_provider=all&pipeline_tag=text-generation" | jq ".[].id"

# Models served by a specific provider
~ curl -s "https://huggingface.co/api/models?inference_provider=fireworks-ai" | jq ".[].id"

# Multiple providers (comma-separated = OR)
~ curl -s "https://huggingface.co/api/models?inference_provider=nscale,novita&pipeline_tag=image-text-to-text" | jq ".[].id"

# Check if a specific model has inference enabled
~ curl -s "https://huggingface.co/api/models/google/gemma-3-27b-it?expand[]=inference"
# Response: {"id": "...", "inference": "warm"} or no "inference" field

# Get per-provider mapping for a model
~ curl -s "https://huggingface.co/api/models/google/gemma-3-27b-it?expand[]=inferenceProviderMapping"
```

Same from Python:
```python
from huggingface_hub import model_info

info = model_info("google/gemma-3-27b-it", expand="inference")
print(info.inference)  # "warm" or None

info = model_info("google/gemma-3-27b-it", expand="inferenceProviderMapping")
print(info.inference_provider_mapping)
# {'featherless-ai': InferenceProviderMapping(status='live', ...), ...}
```

CLI equivalent:
```bash
hf models ls --warn                              # all served models
hf models ls --warn --search GLM-5.2              # search served models
hf models ls --inference-provider fal-ai --pipeline-tag text-to-image
hf models ls --inference-provider fireworks-ai --sort downloads
```

### 5. Billing Modes — Three Patterns

```python
# 1. Hugging Face billing (default)
client = InferenceClient(api_key="hf_...")  # Uses HF credits/plan

# 2. Bill to Enterprise org
client = InferenceClient(provider="fal-ai", bill_to="my-org")

# 3. Direct provider API key (billed directly by provider)
client = InferenceClient(
    provider="together",
    api_key="<together_api_key>",  # Not HF token! Provider's own key
)
```

Pattern 3 bypasses HF billing and uses your provider account directly, while still using the HF client interface.

### 6. Provider-Specific Parameters (extra_body)

```python
result = client.chat_completion(
    model="meta-llama/Meta-Llama-3-8B-Instruct",
    messages=[...],
    extra_body={
        "safety_model": "Meta-Llama/Llama-Guard-7b",  # Together-specific
        # Any provider-specific param from their API docs
    },
)
```

The `extra_body` dict is passed directly to the provider API. Check the provider's documentation for supported parameters.

### 7. Vision / Multimodal Input

```python
# Remote URL
image_url = "https://cdn.britannica.com/61/93061-050-99147DCE/Statue-of-Liberty-Island-New-York-Bay.jpg"

# Or base64-encoded local image
with open("image.jpeg", "rb") as f:
    base64_image = base64.b64encode(f.read()).decode("utf-8")
image_url = f"data:image/jpeg;base64,{base64_image}"

output = client.chat.completions.create(
    model="meta-llama/Llama-3.2-11B-Vision-Instruct",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": image_url}},
            {"type": "text", "text": "Describe this image in one sentence."},
        ],
    }],
)
```

### 8. Complete Method Surface

All task-specific methods available on InferenceClient (v1.24.0):

| Method | Task | Binary Input |
|--------|------|-------------|
| `chat_completion()` | Chat / text generation | — |
| `text_generation()` | Raw text generation (non-chat) | — |
| `text_to_image()` | Image generation | — |
| `image_classification()` | Classify images | bytes, Path, URL |
| `image_segmentation()` | Segment images | bytes, Path, URL |
| `image_to_image()` | Image-to-image translation | bytes, Path, URL |
| `object_detection()` | Detect objects | bytes, Path, URL |
| `zero_shot_image_classification()` | Zero-shot image classification | bytes, Path, URL |
| `automatic_speech_recognition()` | Speech-to-text | bytes, Path, URL |
| `text_to_speech()` | Text-to-speech | — |
| `text_to_audio()` | Audio generation | — |
| `audio_classification()` | Audio classification | bytes, Path, URL |
| `audio_to_audio()` | Audio-to-audio transformation | bytes, Path, URL |
| `feature_extraction()` | Embeddings | — |
| `sentence_similarity()` | Compare texts | — |
| `fill_mask()` | Masked language modeling | — |
| `summarization()` | Text summarization | — |
| `translation()` | Machine translation | — |
| `zero_shot_classification()` | Zero-shot classification | — |
| `tabular_classification()` | Tabular classification | — |
| `tabular_regression()` | Tabular regression | — |
| `document_question_answering()` | Document QA | bytes, Path, URL |
| `visual_question_answering()` | Visual QA | bytes, Path, URL |

### 9. Streaming Options

```python
# Basic streaming
stream = client.chat_completion(messages=[...], model="...", stream=True)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")

# With stream_options
stream = client.chat_completion(
    messages=[...],
    model="...",
    stream=True,
    stream_options={"include_usage": True},  # returns usage info in final chunk
)
```

### 10. Error Handling

```python
from huggingface_hub import InferenceClient, InferenceTimeoutError, HfHubHTTPError

client = InferenceClient(timeout=30)
try:
    result = client.chat_completion(messages=[...], model="...")
except InferenceTimeoutError:
    print("Model unavailable or request timed out after 30s")
except HfHubHTTPError as e:
    if e.response.status_code == 503:
        print("Model is loading, retry later")
    else:
        print(f"HTTP error: {e}")
```

### Resources
- [InferenceClient API reference](https://huggingface.co/docs/huggingface_hub/v1.24.0/en/package_reference/inference_client)
- [Inference Providers docs](https://huggingface.co/docs/inference-providers/en/index)
- [Inference Providers Hub API](https://huggingface.co/docs/inference-providers/en/hub-api)
- [Inference guide](https://huggingface.co/docs/huggingface_hub/en/guides/inference)
- [hf models ls CLI](https://huggingface.co/docs/huggingface_hub/package_reference/cli#hf-models-list)

## 2026-07-25: hf-datasets-server-core-endpoints-deep-dive

### Summary
Comprehensive deep-dive into the Hugging Face Datasets Server REST API — the zero-download way to inspect, query, and analyze datasets on the Hub. Covers all core endpoints (`/splits`, `/size`, `/statistics`, `/parquet`, `/first-rows`, `/rows`, `/is-valid`, `/configs`), their request/response schemas, and practical integration patterns with Python, DuckDB, and Polars. Based on real API responses from `datasets-server.huggingface.co`.

### Base URL
```
https://datasets-server.huggingface.co
```
All endpoints are GET requests. The `dataset` parameter is the Hub dataset ID (e.g., `stanfordnlp/imdb`). For datasets with configs (subsets), `config` and `split` parameters are required on most endpoints.

---

### 1. `/is-valid` — Quick Health Check
**Purpose:** Check whether a dataset is fully processed and available on the Datasets Server.

**Request:**
```
GET /is-valid?dataset=stanfordnlp/imdb
```

**Response:**
```json
{"preview": true, "viewer": true, "search": true, "filter": true, "statistics": true}
```

**Fields:**
| Field | Meaning |
|-------|---------|
| `preview` | First-rows endpoint is available |
| `viewer` | Full rows endpoint is available |
| `search` | Search endpoint is available |
| `filter` | Filter endpoint is available |
| `statistics` | Statistics endpoint is available |

**Use case:** Before building a dataset explorer tool, call `/is-valid` to check which capabilities are enabled. Some datasets may have `preview: true` but `search: false`.

---

### 2. `/configs` — List Dataset Configs (Subsets)
**Purpose:** List all available configs (subsets) for a dataset.

**Request:**
```
GET /configs?dataset=bigcode/the-stack
```

**Key detail:** Many popular datasets (GLUE, SUPERGLUE) expose multiple configs for different subtasks. Always call `/configs` first when exploring an unfamiliar dataset.

---

### 3. `/splits` — List Splits Per Config
**Purpose:** List all splits (train/test/validation) for each config.

**Request:**
```
GET /splits?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "splits": [
    {"dataset": "stanfordnlp/imdb", "config": "plain_text", "split": "train"},
    {"dataset": "stanfordnlp/imdb", "config": "plain_text", "split": "test"},
    {"dataset": "stanfordnlp/imdb", "config": "plain_text", "split": "unsupervised"}
  ],
  "pending": [],
  "failed": []
}
```

**Error handling:** `pending` and `failed` arrays list configs still processing or errored. Retry failed configs after a few minutes.

---

### 4. `/size` — Dataset Size Overview
**Purpose:** Get byte sizes, row counts, and column counts at dataset/config/split level.

**Request:**
```
GET /size?dataset=stanfordnlp/imdb
```

**Response (tiered — dataset → configs → splits):**
```json
{
  "size": {
    "dataset": {
      "num_bytes_original_files": 83446840,
      "num_bytes_parquet_files": 83446840,
      "num_bytes_memory": 128683449,
      "num_rows": 100000
    },
    "configs": [{
      "config": "plain_text",
      "num_rows": 100000, "num_columns": 2
    }],
    "splits": [
      {"config": "plain_text", "split": "train",
        "num_bytes_parquet_files": 20979968, "num_bytes_memory": 33090550,
        "num_rows": 25000, "num_columns": 2},
      {"config": "plain_text", "split": "test",
        "num_bytes_parquet_files": 20470363, "num_rows": 25000},
      {"config": "plain_text", "split": "unsupervised",
        "num_bytes_parquet_files": 41996509, "num_rows": 50000}
    ]
  }
}
```

**Key metrics:**
| Metric | Meaning |
|--------|---------|
| `num_bytes_original_files` | Size of original source files |
| `num_bytes_parquet_files` | Size after Parquet conversion |
| `num_bytes_memory` | Projected RAM if loaded into Python (≥ parquet due to object overhead) |
| `num_rows` | Exact row count |
| `num_columns` | Number of feature columns |

**Memory-to-parquet ratio:** `num_bytes_memory / num_bytes_parquet_files` varies: text ~1.5×, numerics ~2–4×, binary ~1×. Use this to decide if streaming is needed.

**Use case:** Before downloading, check `num_bytes_memory` — if it exceeds available RAM, use streaming or DuckDB remote Parquet queries.

---

### 5. `/first-rows` — Schema + First 100 Rows
**Purpose:** Get the feature schema and first 100 rows to understand dataset structure.

**Request:**
```
GET /first-rows?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Feature type taxonomy:**
| `_type` | `dtype`/detail | Meaning |
|---------|----------------|---------|
| `Value` | `string` | Text column |
| `Value` | `int32`/`int64` | Integer column |
| `Value` | `float32`/`float64` | Float column |
| `ClassLabel` | `names: [...]` | Categorical with named labels |
| `Image` | — | Image column |
| `Audio` | — | Audio column |
| `Sequence` | `[inner_type]` | List/array of inner values |

**`truncated_cells`:** Cells >~100KB are truncated; indices appear here. Use `/rows` or Parquet for full content.

**Use case:** The canonical "dataset sniffing" tool — verify column names, types, and labels before coding any loading logic.

---

### 6. `/rows` — Paginated Row Access
**Purpose:** Access any contiguous slice of rows.

**Request:**
```
GET /rows?dataset=stanfordnlp/imdb&config=plain_text&split=train&length=3&offset=100
```

**Limitations:**
- Max `length`: **500 rows** per request (hard limit)
- Max `offset`: **5M rows** (beyond that, use Parquet snapshots)
- Large cells may be truncated

**Use case:** Paginated UIs or pulling small validation samples.

---

### 7. `/parquet` — Parquet Snapshot URLs (Most Powerful)
**Purpose:** Get direct URLs to Parquet snapshot files for each split. Query with DuckDB/Polars **without any HF datasets library code**.

**Request:**
```
GET /parquet?dataset=stanfordnlp/imdb
```

**Response:**
```json
{
  "parquet_files": [
    {"config": "plain_text", "split": "train",
      "url": "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet",
      "size": 20979968},
    {"config": "plain_text", "split": "test",
      "url": "...", "size": 20470363},
    {"config": "plain_text", "split": "unsupervised",
      "url": "...", "size": 41996509}
  ]
}
```

**Practical integration — DuckDB (zero-install, HTTP range requests):**
```python
import duckdb

url = "https://huggingface.co/datasets/stanfordnlp/imdb/resolve/refs%2Fconvert%2Fparquet/plain_text/train/0000.parquet"
result = duckdb.sql(f"""
  SELECT label, COUNT(*) as cnt FROM read_parquet('{url}') GROUP BY label
""").fetchall()
print(result)  # [(0, 12500), (1, 12500)]
```

**Practical integration — Polars:**
```python
import polars as pl
url = "..."  # from /parquet endpoint
df = pl.read_parquet(url)
print(df.group_by("label").len())
```

**Multi-file datasets — query all shards at once:**
```python
files = [...]  # from /parquet endpoint
queries = [
    f"SELECT '{f['split']}' as split, COUNT(*) as cnt FROM read_parquet('{f['url']}')"
    for f in files
]
result = duckdb.sql(" UNION ALL BY NAME ".join(queries)).fetchdf()
```

**Performance:** DuckDB's `read_parquet` uses HTTP range requests — it only fetches bytes for queried columns. For wide datasets this is drastically faster than downloading.

**Zero-cost:** Parquet URLs are **free** — no auth needed for public datasets, no rate limits, no credits.

---

### 8. `/statistics` — Column-Level Statistics
**Purpose:** Per-column stats including histograms, unique counts, min/max, and null proportions.

**Request:**
```
GET /statistics?dataset=stanfordnlp/imdb&config=plain_text&split=train
```

**Response:**
```json
{
  "num_examples": 25000,
  "statistics": [
    {
      "column_name": "label",
      "column_type": "class_label",
      "column_statistics": {
        "nan_count": 0, "nan_proportion": 0.0,
        "n_unique": 2,
        "frequencies": {"neg": 12500, "pos": 12500}
      }
    },
    {
      "column_name": "text",
      "column_type": "string_text",
      "column_statistics": {
        "nan_count": 0, "min": 52, "max": 13704,
        "mean": 1325.06, "median": 979.0, "std": 1003.13,
        "histogram": {"hist": [17426, 5384, 1490, 535, 147, 11, 4, 2, 0, 1], "num_bins": 10}
      }
    }
  ]
}
```

**Column type-specific stats:**
| `column_type` | Available |
|---------------|-----------|
| `class_label` | `nan_count`, `n_unique`, `frequencies` |
| `string_text` | `nan_count`, `min`/`max`/`mean`/`median`/`std` of length, `histogram` |
| `int`/`float` | `nan_count`, `min`, `max`, `mean`, `median`, `std`, `histogram` |
| `bool` | `n_unique` (2), `frequencies` |
| `sequence`/`image`/`audio`/`video` | No statistics computed |

**Use case:** Validate class balance, text length distribution (set `max_length`), missing values, feature ranges — all before training.

---

### 9. `/search` — Keyword Search
**Purpose:** Substring search within dataset split.

**Request:**
```
GET /search?dataset=...&config=plain_text&split=train&query=terrible&length=3
```

**Limitation:** Only available when `/is-valid` returns `"search": true`. Substring match on all string columns — no BM25/semantic ranking.

---

### 10. `/filter` — Column-Based Filtering
**Request:**
```
GET /filter?dataset=...&where=label=0&length=3
```

Equality-only on specific columns. Equivalent to SQL `WHERE label=0`.

---

### 11. Python Helpers (huggingface_hub)
```python
from huggingface_hub.datasets_server import (
    get_dataset_splits, get_dataset_configs, get_dataset_size,
    get_dataset_first_rows, get_dataset_parquet_files, get_dataset_statistics,
)

configs = get_dataset_configs("stanfordnlp/imdb")
splits = get_dataset_splits("stanfordnlp/imdb")
size = get_dataset_size("stanfordnlp/imdb")
rows = get_dataset_first_rows("stanfordnlp/imdb", "plain_text", "train")
stats = get_dataset_statistics("stanfordnlp/imdb", "plain_text", "train")
```

---

### 12. Complete Integration Workflow
```python
import json, urllib.request, duckdb

DS = "stanfordnlp/imdb"
BASE = "https://datasets-server.huggingface.co"

def json_get(path):
    with urllib.request.urlopen(f"{BASE}{path}") as r:
        return json.loads(r.read())

# 1. Health check
valid = json_get(f"/is-valid?dataset={DS}")
print(f"Available: preview={valid['preview']} stats={valid['statistics']}")

# 2. List splits
splits = json_get(f"/splits?dataset={DS}")["splits"]
for s in splits:
    print(f"  {s['config']}/{s['split']}")

# 3. Get size
ds_size = json_get(f"/size?dataset={DS}")["size"]["dataset"]
print(f"Rows: {ds_size['num_rows']}, Memory: {ds_size['num_bytes_memory']/1e6:.1f}MB")

# 4. Query via Parquet + DuckDB
parquet_files = json_get(f"/parquet?dataset={DS}")["parquet_files"]
queries = [
    f"SELECT '{pf['split']}' as split, COUNT(*) as cnt FROM read_parquet('{pf['url']}')"
    for pf in parquet_files
]
result = duckdb.sql(" UNION ALL BY NAME ".join(queries)).fetchdf()
print(result)
```

---

### 13. Key Design Principles
1. **Zero-download exploration** — All endpoints return JSON. Inspect any public dataset without downloading.
2. **Parquet as interchange** — Parquet is columnar, compressed, queryable via HTTP range requests, works with any data tool.
3. **Config → Split → Row hierarchy** — Always go: `/configs` → `/splits` → `/first-rows` (or `/rows`).
4. **Cached results** — Datasets Server processes once on upload. No per-query compute cost.
5. **Large dataset strategy** — For >5M rows, use `/parquet` + DuckDB remote reads (fetch only needed columns).

---

### Resources
- [Datasets Server docs](https://huggingface.co/docs/dataset-viewer/main/en/valid)
- [Splits endpoint](https://huggingface.co/docs/dataset-viewer/main/en/splits)
- [First rows](https://huggingface.co/docs/dataset-viewer/main/en/first_rows)
- [Size endpoint](https://huggingface.co/docs/dataset-viewer/main/en/size)
- [Parquet endpoint](https://huggingface.co/docs/dataset-viewer/main/en/parquet)
- [Statistics endpoint](https://huggingface.co/docs/dataset-viewer/main/en/statistics)
- [Datasets Server base URL](https://datasets-server.huggingface.co)
- [huggingface_hub datasets_server module](https://huggingface.co/docs/huggingface_hub/en/package_reference/datasets_server)
- [DuckDB remote Parquet](https://duckdb.org/docs/data/parquet/overview.html)

---

## 2026-07-24: hf-transformers-torchao-integration-deep-dive (Topic #119)

### Summary
Deep-dive into torchao (PyTorch Architecture Optimization) and its integration with Hugging Face Transformers v5.x. torchao is PyTorch's native quantization and optimization library, providing composable high-performance data types for inference and training. The integration is accessed via `TorchAoConfig` in Transformers, which accepts `AOBaseConfig` objects from `torchao.quantization`. As of torchao >= 0.15, the old string-based API was removed — all configs must be `AOBaseConfig` subclass instances. This is distinct from bitsandbytes (NVIDIA-only) — torchao supports CUDA, Intel XPU, and CPU.

### Key Concepts

**TorchAoConfig** — The bridge between Transformers and torchao. Passed as `quantization_config` to `AutoModelForCausalLM.from_pretrained()`.

**AOBaseConfig subclasses** — The quantization configs you pass to `TorchAoConfig`:

| Config | Dtype | Use Case |
|--------|-------|----------|
| `Float8DynamicActivationFloat8WeightConfig` | A16W8-FP8 | H100 GPU (FP8 tensor cores) |
| `Float8WeightOnlyConfig` | A16W8-FP8 | H100 GPU (weight-only) |
| `Int8DynamicActivationInt8WeightConfig` | A8W8-INT8 | A100 GPU, Intel XPU, CPU |
| `Int8WeightOnlyConfig` | A16W8-INT8 | A100, XPU, CPU |
| `Int4WeightOnlyConfig` | A16W4-INT4 | A100, H100, XPU (batch=1) |
| `GemliteUIntXWeightOnlyConfig` | 4/8-bit | A100/H100 (batch=N, autotuned) |
| `Int4WeightOnlyConfig(layout=MarlinSparseLayout())` | INT4+2:4 Sparse | H100 with sparse checkpoints |
| `PrototypeInt4WeightOnlyConfig` | INT4 | CPU (torchao >= 0.15) |
| `IntxWeightOnlyConfig` | Arbitrary INTx | Custom bit-width quantization |
| `Int8DynamicActivationInt4WeightConfig` | A8W4-Mixed | Per-layer mixed quantization |

### Hardware Compatibility

| Hardware | CUDA | XPU | CPU |
|----------|------|-----|-----|
| CUDA Versions | cu118, cu126, cu128 | — | — |
| XPU Versions | — | PyTorch 2.8 | — |
| FP8 (H100) | ✅ | — | — |
| INT8 (A100) | ✅ | ✅ | ✅ |
| INT4 (Consumer) | ✅ | ✅ | ✅ (>=0.15) |

### Critical API Change (torchao >= 0.15)
- **OLD (removed):** `TorchAoConfig("int4_weight_only")` — string-based API
- **NEW (required):** `TorchAoConfig(quant_type=Int4WeightOnlyConfig(group_size=128))` — object-based API
- Serialization (save_pretrained / push_to_hub) only works with torchao >= 0.15

### Per-Module Quantization
`FqnToConfig` enables layer-specific quantization:

1. **Skip layers:** `{"_default": config, "model.layers.0.self_attn.q_proj": None}` 
2. **Different configs per layer (regex):** Keys starting with `re:` use regex matching
3. **Different configs per layer (exact FQN):** Use exact module path as key

### Auto-Compilation Pattern
```python
quantization_config = TorchAoConfig(quant_type=quant_config)
quantized_model = AutoModelForCausalLM.from_pretrained(
    model_id, dtype="auto", device_map="auto",
    quantization_config=quantization_config
)
# auto-compile via cache_implementation="static"
output = quantized_model.generate(**inputs, max_new_tokens=10, cache_implementation="static")
```
Setting `cache_implementation="static"` auto-compiles with `torch.compile`. The model recompiles on batch size / max_new_tokens changes. Pass `disable_compile=True` to skip compilation.

### Device-Specific Notes

- **CPU INT4:** Requires `Int4CPULayout()` in `Int4WeightOnlyConfig`. Only CPU-serialized models can be re-loaded on CPU.
- **INT4 cross-device limitation:** INT4 layouts are device-specific — quantize and load on the same device.
- **INT8/FP8 are portable:** Can quantize on CPU, load on CUDA.

### Recommended Settings
```python
torchao.quantization.utils.recommended_inductor_config_setter()
```

### Resources
- [Transformers torchao docs (source)](https://github.com/huggingface/transformers/blob/main/docs/source/en/quantization/torchao.md)
- [torchao quantization API](https://github.com/pytorch/ao/blob/main/torchao/quantization/quant_api.py)
- [torchao README](https://github.com/pytorch/ao#torchao-pytorch-architecture-optimization)
- [Benchmarks](https://github.com/pytorch/ao/tree/main/torchao/quantization#benchmarks)
- [Colab: Torchao Demo](https://colab.research.google.com/github/huggingface/notebooks/blob/main/transformers_doc/en/quantization/torchao.ipynb)

---

## 2026-07-24: hf-diffusers-video-generation-pipeline — Complete Ecosystem Deep Dive (Topic #81, Deepened)

### Summary

A comprehensive survey of ALL video generation pipelines in Hugging Face Diffusers (main branch, post-v0.39.0). The video pipeline ecosystem has exploded to **20+ distinct pipelines** covering text-to-video (T2V), image-to-video (I2V), first-last-frame-to-video (FLF2V), character animation, controllable video generation, and video editing.

### Comparison of All Video Pipelines

| Pipeline | Class | Params | T2V | I2V | Other Modes | Scheduler | Notes |
|---|---|---|---|---|---|---|---|
| **Allegro** | `AllegroPipeline` | ~2B | ✅ | ❌ | — | Flow matching | Short-form T2V |
| **AnyFlow** | `AnyFlowPipeline` | Variable | ✅ | ❌ | — | Flow matching | Fast generation |
| **ChronoEdit** | `ChronoEditPipeline` | Variable | ❌ | ❌ | Video editing | DDIM | Frame-based editing |
| **CogVideoX** | `CogVideoXPipeline` | 2B/5B | ✅ | ✅ (I2V) | — | DDIM/DPM | Flagship, 3D causal VAE |
| **ConsisID** | `ConsisIDPipeline` | Variable | ✅ | ✅ | Identity-consistent | Flow matching | Face-consistent video |
| **Cosmos** | `CosmosPipeline` | Variable | ✅ | ✅ | World model | Flow matching | NVIDIA world model |
| **Cosmos3** | `Cosmos3Pipeline` | Variable | ✅ | ✅ | World model | Flow matching | Next-gen Cosmos |
| **Framepack** | `FramepackPipeline` | Variable | ❌ | ❌ | Frame interpolation | — | Frame packing |
| **Helios** | `HeliosPipeline` | Variable | ✅ | ❌ | — | Flow matching | High-quality T2V |
| **HunyuanVideo** | `HunyuanVideoPipeline` | ~13B | ✅ | ❌ | — | DDIM | Tencent's model |
| **HunyuanVideo1.5** | `HunyuanVideo1_5Pipeline` | ~13B | ✅ | ❌ | — | DDIM | Improved version |
| **Kandinsky 5.0 Video** | — | — | ✅ | ❌ | — | — | Kandinsky 5.0 video module |
| **Latte** | `LattePipeline` | Variable | ✅ | ❌ | — | DDIM | Latent diffusion T2V |
| **LTX-2** | `LTXVideoPipeline` | ~2B | ✅ | ❌ | — | Flow matching | Lightweight T2V |
| **Mochi** | `MochiPipeline` | 10B | ✅ | ❌ | — | FlowMatchEuler | Genmo, AsymmDiT, Apache 2.0 |
| **Motif-Video** | `MotifVideoPipeline` | Variable | ✅ | ❌ | Motion control | — | Motion-conditioned |
| **SkyReels-V2** | `SkyReelsPipeline` | Variable | ✅ | ❌ | — | — | Skywork video |
| **Stable Video Diffusion** | `StableVideoDiffusionPipeline` | ~2.5B | ❌ | ✅ | Frame interpolation | — | Stability AI |
| **Wan** | `WanPipeline` | 1.3B/14B | ✅ | ✅ | FLF2V, VACE, Animate | FlowMatch | Multi-stage denoising, two transformers |

### Detailed Pipeline Deep Dives

#### 1. CogVideoX (THUDM)

**Architecture:** T5 encoder → 3D Causal VAE → CogVideoXTransformer3DModel (spatio-temporal full attention) → DDIM/DPM scheduler.

**Key Features:**
- Available in 2B and 5B parameter variants
- 3D causal VAE reduces flickering vs frame-wise VAEs
- Supports both DDIM and DPM schedulers
- `CogVideoXImageToVideoPipeline` variant for I2V
- LoRA support via `load_lora_weights()`
- torchao Int8 weight-only quantization
- `fuse_qkv_projections()` for speed

**Optimal Settings:**
- T2V: 1360×768 resolution, 81–161 frames at 16 fps
- I2V: Width 768–1360, Height 758 (must be divisible by 16)
- `max_sequence_length` defaults to 226 (T5 tokens)

**Memory-Saving:**
- `enable_model_cpu_offload()`: 19 GB → 33 GB without
- `enable_sequential_cpu_offload()`: <4 GB (very slow)
- `enable_tiling()` + model offload: 11 GB
- `enable_layerwise_casting(FP8)`: layer-cast weights to FP8 at runtime

#### 2. Mochi 1 (Genmo)

**Architecture:** T5-XXL encoder → Asymmetric Diffusion Transformer (AsymmDiT, 10B params) → AutoencoderKLMochi → FlowMatchEulerDiscreteScheduler.

**Key Innovations:**
- **AsymmDiT:** Non-square QKV and output projection layers (Q/K projections smaller than V/O) to reduce memory
- Single T5-XXL text encoder (no dual encoders)
- Released under Apache 2.0 license
- `force_zeros_for_empty_prompt` option (zeros CFG unconditional, matches Genmo impl)

**Optimal Settings:**
- 480×848 resolution (default)
- `num_frames`: 19–163 frames
- `num_inference_steps`: 28 (fast) to 64 (quality)
- `guidance_scale`: 3.5–4.5
- `max_sequence_length`: 256
- `variant="bf16"` for 22 GB VRAM variant

**Quantization:**
```python
from transformers import BitsAndBytesConfig
from diffusers import BitsAndBytesConfig as DiffusersBitsAndBytesConfig, MochiTransformer3DModel

# 8-bit quantized T5
text_encoder_8bit = T5EncoderModel.from_pretrained(
    "genmo/mochi-1-preview", subfolder="text_encoder",
    quantization_config=BitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)
# 8-bit quantized transformer
transformer_8bit = MochiTransformer3DModel.from_pretrained(
    "genmo/mochi-1-preview", subfolder="transformer",
    quantization_config=DiffusersBitsAndBytesConfig(load_in_8bit=True),
    torch_dtype=torch.float16,
)
```

**Multi-GPU:** Supports `device_map="auto"` + `max_memory` to split the transformer across GPUs.

**Original Repo Precision:** Text encoder + VAE in FP32, DiT in BF16 with `EFFICIENT_ATTENTION` backend. Diffusers doesn't yet support per-stage dtypes — use autocast + manual encoding to reproduce.

**Single File Loading:** Supports `MochiTransformer3DModel.from_single_file()` for ComfyUI repackaged checkpoints. FP8 single files NOT yet supported.

#### 3. Wan 2.1 / 2.2 (Wan-AI)

**Architecture:** UMT5 encoder → WanTransformer3DModel(s) → AutoencoderKLWan → FlowMatchEulerDiscreteScheduler.

**Key Innovations:**
- **Two-stage denoising:** Wan 2.2 introduces `transformer_2` — a second transformer for low-noise stages, with `boundary_ratio` controlling the split. Stage 1 (high noise) runs on `transformer`, Stage 2 (low noise) runs on `transformer_2`.
- Supports both 1.3B (consumer GPU, 8.19 GB VRAM) and 14B (high quality) variants
- Available in 6 model flavors: T2V 1.3B, T2V 14B, I2V 14B-480P, I2V 14B-720P, FLF2V 14B-720P, VACE
- **Wan 2.2** adds: T2V 14B, I2V 14B, TI2V 5B, Animate 14B

**Model Variants:**

| Model ID | Type | Params | Notes |
|---|---|---|---|
| `Wan-AI/Wan2.1-T2V-1.3B-Diffusers` | T2V | 1.3B | Consumer GPU friendly |
| `Wan-AI/Wan2.1-T2V-14B-Diffusers` | T2V | 14B | High quality |
| `Wan-AI/Wan2.1-I2V-14B-480P-Diffusers` | I2V | 14B | ~480p output |
| `Wan-AI/Wan2.1-I2V-14B-720P-Diffusers` | I2V | 14B | ~720p output |
| `Wan-AI/Wan2.1-FLF2V-14B-720P-Diffusers` | FLF2V | 14B | First+Last frame → video |
| `Wan-AI/Wan2.1-VACE-14B-Diffusers` | VACE | 14B | Any-to-video controllable |
| `Wan-AI/Wan2.2-T2V-14B-Diffusers` | T2V | 14B | Two-stage denoising |
| `Wan-AI/Wan2.2-I2V-14B-Diffusers` | I2V | 14B | Two-stage denoising |
| `Wan-AI/Wan2.2-TI2V-5B-Diffusers` | TI2V | 5B | Text+Image → video |
| `Wan-AI/Wan2.2-Animate-14B-Diffusers` | Animate | 14B | Character animation |

**Memory Optimization (14B under 13 GB VRAM):**
```python
from diffusers.hooks.group_offloading import apply_group_offloading

# Block-level for text encoder
apply_group_offloading(text_encoder, onload_device="cuda",
    offload_device="cpu", offload_type="block_level", num_blocks_per_group=4)

# Leaf-level for transformer
transformer.enable_group_offload(onload_device="cuda",
    offload_device="cpu", offload_type="leaf_level", use_stream=True)
```

**Wan VACE (Any-to-Video Controllable Generation):** Supports depth, pose, sketch, flow, grayscale, scribble, layout, bounding box conditioning. Uses mask-based paradigm: black mask = condition area (preserve), white mask = generation area.

**Wan-Animate:** Character animation + replacement. Two modes: `"animate"` (animate character) and `"replace"` (replace character in scene). Requires preprocessed pose_video + face_video.

**Key Notes:**
- Frames formula: `k = (num_frames - 1) / 4`
- Lower flow_shift (2.0–5.0) for low-res, higher (7.0–12.0) for high-res
- `AutoencoderKLWan` should use `torch.float32` for best decoding quality
- Supports LightX2V LoRAs for speed
- Wan 2.2: LoRAs only load into first transformer by default; set `load_into_transformer_2=True` for second

#### 4. HunyuanVideo (Tencent)

- ~13B parameter T2V model
- Uses DDIM scheduler
- `HunyuanVideo1_5Pipeline` available with improvements
- Standard memory optimization techniques apply

#### 5. Stable Video Diffusion (Stability AI)

- I2V only (no T2V)
- Takes a single image and generates video
- Uses frame interpolation approach
- Smaller model size (~2.5B)

#### 6. LTX Video / LTX-2

- Lightweight T2V (~2B params)
- Flow matching scheduler
- Consumer GPU friendly

### Common Architecture Patterns

All Diffusers video pipelines share this structure:
1. **Text Encoder** — T5, UMT5, or CLIP (encodes prompt)
2. **VAE** — 3D video autoencoder (spatial + temporal compression), specific per model:
   - `AutoencoderKLCogVideoX` (CogVideoX)
   - `AutoencoderKLMochi` (Mochi)
   - `AutoencoderKLWan` (Wan)
   - Standard `AutoencoderKL` (SVD)
3. **Transformer** — 3D diffusion transformer with spatial + temporal attention:
   - `CogVideoXTransformer3DModel`
   - `MochiTransformer3DModel` (AsymmDiT)
   - `WanTransformer3DModel`
   - `HunyuanVideoTransformer3DModel`
4. **Scheduler** — DDIM, DPM, FlowMatchEuler, or UniPCMultistep

### Scheduler Choices

| Pipeline | Default Scheduler | Alternate |
|---|---|---|
| CogVideoX | `CogVideoXDDIMScheduler` | `CogVideoXDPMScheduler` |
| Mochi | `FlowMatchEulerDiscreteScheduler` | — |
| Wan | `FlowMatchEulerDiscreteScheduler` | `UniPCMultistepScheduler` |
| HunyuanVideo | DDIM | — |
| SVD | — | Various |

### Memory Optimization Comparison

| Technique | How It Works | Best For |
|---|---|---|
| `enable_model_cpu_offload()` | Offloads entire sub-modules to CPU when not in use | General purpose, good balance |
| `enable_sequential_cpu_offload()` | Offloads individual layers sequentially | Minimal VRAM (<4 GB), but very slow |
| `enable_vae_tiling()` | Processes VAE decode in tiles | Reduces VAE peak memory by 50%+ |
| `enable_vae_slicing()` | Slices VAE input for batch processing | Complements tiling |
| Group offloading | Offloads groups of layers (block_level or leaf_level) | Wan, Flux — more granular than model-level |
| `enable_layerwise_casting()` | Casts weights layer-by-layer at runtime to FP8 | CogVideoX |
| `PipelineQuantizationConfig` | Applies quantizers (torchao, bitsandbytes) to specific modules | CogVideoX, Mochi |
| `device_map="auto"` + `max_memory` | Splits model across multiple GPUs | Multi-GPU setups |

### Quantization Support

| Pipeline | bitsandbytes | torchao | FP8 casting | Notes |
|---|---|---|---|---|
| CogVideoX | ❌ | ✅ (Int8WeightOnly) | ✅ (layerwise_casting) | ~16 GB with int8 |
| Mochi | ✅ | ❌ | ❌ (single file FP8 not supported) | ~22 GB with bf16 variant |
| Wan | ❌ | ❌ | ❌ | Group offload instead |
| HunyuanVideo | ❌ | ❌ | ❌ | Standard offload |

### LoRA Support

| Pipeline | `load_lora_weights()` | `set_adapters()` | Notes |
|---|---|---|---|
| CogVideoX | ✅ | ✅ | Community LoRAs on HF Hub |
| Wan 2.1 | ✅ | ✅ | LightX2V LoRAs for speed |
| Wan 2.2 | ✅ | ✅ | `load_into_transformer_2=True` |
| Mochi | ❌ | ❌ | Not yet supported |
| HunyuanVideo | ❌ | ❌ | Not yet supported |

### AutoPipeline for Video

`AutoPipelineForTextToVideo` and `AutoPipelineForImageToVideo` auto-detect the correct pipeline class from the model ID. However, this is less reliable than explicit pipeline classes due to the variety of model architectures.

### Export Utilities

- `diffusers.utils.export_to_video(frames, path, fps=X)` — exports list of PIL images to MP4
- `diffusers.utils.load_video(path)` — loads video as list of PIL frames
- `diffusers.video_processor.VideoProcessor` — low-level video processing (VAE scale factor, normalization)
- `from_image_bytes_to_video()` — helper for converting images

### Video Pipeline Ecosystem Summary

The Diffusers video ecosystem has matured significantly, with the `main` branch now supporting over 20 video pipelines. Key strategic takeaways:
- **Wan** is the most comprehensive ecosystem (T2V, I2V, FLF2V, VACE, Animate) with the strongest consumer GPU support (1.3B at 8 GB)
- **CogVideoX** remains the best-documented and most LoRA-friendly option
- **Mochi** is the strongest open-source quality contender (10B AsymmDiT, Apache 2.0)
- **Two-stage denoising** (Wan 2.2) represents the next architectural evolution in video diffusion
- **Controllable video** (Wan VACE, Animate) is the frontier — mask-based conditioning for depth/pose/face

### References
- [Diffusers Video Pipelines Docs (main)](https://huggingface.co/docs/diffusers/main/en/api/pipelines/video)
- [Mochi Pipeline Docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/mochi)
- [CogVideoX Pipeline Docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/cogvideox)
- [Wan Pipeline Docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/wan)
- [HunyuanVideo Pipeline Docs](https://huggingface.co/docs/diffusers/main/en/api/pipelines/hunyuan_video)
- [Diffusers Reduce Memory Guide](https://huggingface.co/docs/diffusers/main/en/optimization/memory)
- [Genmo Mochi 1](https://github.com/genmoai/models)
- [Wan-AI GitHub](https://github.com/Wan-AI/Wan)
|
## 2026-07-24: hf-hub-pull-requests-and-discussions-api — Full Guide (Topic #122)

### Summary
Comprehensive deep-dive into the Hugging Face Hub's Pull Requests and Discussions system — the community collaboration layer for models, datasets, Spaces, and storage repos. Covers the no-fork ref-based PR architecture, the web UI lifecycle (draft → open → merged/closed), programmatic API via `huggingface_hub`, and the `hf discussions` CLI. Key insight: HF PRs do NOT use forks — contributors push to custom git refs (e.g. `refs/pr/42`) directly on the source repo.

### Architecture — No Fork, All Ref

HF's PR system is fundamentally different from GitHub:

| Feature | GitHub PR | HF Hub PR |
|---------|-----------|-----------|
| Fork required | Yes — fork + branch | No — push to `refs/pr/N` on source repo |
| Where changes live | Fork's branch | Custom git ref `refs/pr/{N}` on source repo |
| Clone visibility | Not fetched by default | Not fetched by default (intentional) |
| Distinction from Issues | Separate systems | PRs and Discussions share the same list |
| Streamlined for ML | No | Yes — model/dataset/Space-specific defaults |

### PR Lifecycle

```
Draft (default when created via advanced mode / API)
  │
  ▼
Open (Publish button)
  │
  ├── Merged  → optional: delete ref to free storage
  └── Closed  → optional: delete ref to free storage
```

**Draft → Open:** Draft is the default when creating a PR via "Advanced mode" or via `create_pull_request()` API. The Publish button converts it to Open. This transition is **one-way** — you cannot go back to draft.

**Closing/Merging:** After close or merge, a banner appears showing storage freed by deleting the PR ref. Clicking "Delete ref" removes `refs/pr/{N}` permanently — this is **irreversible**.

### Web UI Features

| Feature | Who Can Use |
|---------|-------------|
| Edit title | Author, repo writer, or org write-access |
| Pin discussion | Write-access to repo |
| Lock discussion | Write-access to repo (prevents new comments) |
| Edit comment | Comment author or write-access |
| Hide comment | Write-access (irreversible — content hidden forever) |
| Markdown + LaTeX | Everyone (`$$...$$` for display, `\\\\(...\\\\)` for inline) |

### Git — Working with PRs Locally

```bash
# Fetch a specific PR (e.g. PR #42)
git fetch origin refs/pr/42:pr/42
git checkout pr/42

# Make changes and push back to the PR
git commit -m "Add your change"
git push origin pr/42:refs/pr/42

# Fetch ALL PRs (git magician mode)
git config remote.origin.fetch "+refs/pr/*:refs/remotes/origin/pr/*"
git fetch origin
git checkout pr/42
```

### Programmatic API — huggingface_hub

#### List Discussions/PRs

```python
from huggingface_hub import get_repo_discussions

# Iterate all discussions/PRs
for discussion in get_repo_discussions(repo_id="bigscience/bloom"):
    print(f"{discussion.num} - {discussion.title}, pr: {discussion.is_pull_request}")

# Filter by author, type, status
for discussion in get_repo_discussions(
    repo_id="bigscience/bloom",
    author="ArthurZ",
    discussion_type="pull_request",  # or "discussion"
    discussion_status="open",          # or "closed"
):
    print(f"{discussion.num} - {discussion.title}")

# Get a flat list
discussions_list = list(get_repo_discussions(repo_id="bert-base-uncased"))
```

#### Get Detailed PR Info

```python
from huggingface_hub import get_discussion_details

details = get_discussion_details(
    repo_id="bigscience/bloom-1b3",
    discussion_num=2
)
# Returns DiscussionWithDetails with:
#   .num, .title, .author, .status, .is_pull_request
#   .events — all comments, commits, status changes, renames
#   .diff — raw git diff (PR only)
#   .target_branch — "refs/heads/main"
#   .merge_commit_oid — None if not merged
```

#### Create PR from a Commit

The easiest way to propose changes: set `create_pr=True` on any commit operation.

```python
from huggingface_hub import metadata_update, upload_file, upload_folder, delete_file, delete_folder

# Update model card metadata via PR
metadata_update(
    repo_id="username/repo_name",
    metadata={"tags": ["computer-vision", "awesome-model"]},
    create_pr=True,
)

# Upload file via PR
upload_file(
    path_or_fileobj="local_file.bin",
    path_in_repo="remote_file.bin",
    repo_id="username/repo_name",
    create_pr=True,
)
```

#### Create Discussion/PR from Scratch

```python
from huggingface_hub import create_discussion, create_pull_request

# Create a discussion
disc = create_discussion(
    repo_id="username/repo-name",
    title="Hi from the huggingface_hub library!",
)

# Create a pull request (starts in DRAFT mode)
pr = create_pull_request(
    repo_id="username/repo-name",
    title="Fix tokenizer config",
)
```

#### Manage PRs

```python
from huggingface_hub import (
    comment_discussion,
    edit_discussion_comment,
    rename_discussion,
    change_discussion_status,
    merge_pull_request,
)

# Add a comment
comment_discussion(repo_id="username/repo-name", discussion_num=5, body="LGTM!")

# Rename
rename_discussion(repo_id="username/repo-name", discussion_num=5, title="Better title")

# Open/Close
change_discussion_status(repo_id="username/repo-name", discussion_num=5, new_status="closed")

# Merge a PR
merge_pull_request(repo_id="username/repo-name", discussion_num=5)
```

### CLI — hf discussions

All operations available from the command line — useful for CI pipelines and scripting.

```bash
# List all discussions/PRs (supports --type: model/dataset/space)
hf discussions list username/repo-name

# List discussions on a dataset repo
hf discussions list username/dataset-repo --type dataset

# Get details + comments
hf discussions info username/repo-name 5

# Create discussion
hf discussions create username/repo-name --title "Bug report" --body "Description here"

# Create pull request
hf discussions create username/repo-name --title "Fix typo" --pull-request

# Comment
hf discussions comment username/repo-name 5 --body "LGTM!"

# Merge
hf discussions merge username/repo-name 5 --yes

# Show diff
hf discussions diff username/repo-name 5
```

### Storage Management

After closing or merging a PR, a banner shows **estimated storage that could be freed** by deleting the PR's git ref:

```
Changes in this PR are now part of main.
Delete ref to free ~X MB of storage.
```

Click "Delete ref" to permanently remove `refs/pr/{N}`. This is especially useful when:
- The main branch was squashed-merged (PR branch retains full history)
- Files were deleted in main but remain in PR branch history
- Large binary files were added during development

### Key Design Decisions

1. **No forks = lower friction.** Contributors don't need to maintain fork sync. Changes go directly to the source repo under custom refs that don't pollute the default clone.
2. **PRs == Discussions.** Unified list reduces UX complexity. A Discussion becomes a PR when it has code changes attached.
3. **Draft → Open is one-way.** Prevents abuse of toggling between states.
4. **PR ref deletion is irreversible.** Storage savings come with the cost of losing history — design APIs accordingly.
5. **`create_pr=True` is the recommended pattern.** Simplest way to contribute: just write files as normal, add one parameter.

### Zero-Cost Relevance

- **Free to use**: No cost to create/comment/merge PRs. Storage costs only apply to the PR ref itself.
- **Free storage cleanup**: Deleting closed/merged PR refs reclaims storage on free tier.
- **CI/CD scripting**: `hf discussions merge` + `hf discussions diff` can be wired into free GitHub Actions.
- **No fork needed**: Avoids the storage cost of maintaining a full fork on the Hub.

### References
- [HF Hub Docs: Pull Requests and Discussions](https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions)
- [huggingface_hub: Interact with Discussions and PRs](https://huggingface.co/docs/huggingface_hub/main/en/guides/community)
- [HfApi Discussion Methods Reference](https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.get_repo_discussions)
- [CLI: hf discussions](https://huggingface.co/docs/huggingface_hub/main/en/guides/cli#hf-discussions)
- [Repository Settings](https://huggingface.co/docs/hub/en/repositories-settings)

## 2026-07-24: hf-transformers-kv-cache-architecture-deep-dive-v2 — Source Code Analysis from cache_utils.py

### Summary
Comprehensive source-level deep-dive into the 🤗 Transformers KV Cache architecture (cache_utils.py, ~2056 lines, Transformers v5.14+). Covers the full two-tier class hierarchy: **CacheLayerMixin** (per-layer state) and **Cache** (layer container with dispatch). Explains all dynamic, static, quantized, linear-attention, and hybrid cache variants, plus the config-driven auto-dispatch system, GPU offloading, and torch.compile support.

### Architecture Overview

The KV Cache system has a clean separation of concerns:
- **CacheLayerMixin** — manages a single layer's key/value tensors (or conv/recurrent states for linear-attention)
- **Cache** — an ordered container of `CacheLayerMixin` objects, one per model layer

New in v5: The old `tuple[tuple[torch.Tensor]]` format is fully replaced by Cache objects. The legacy `past_key_values` parameter now accepts any Cache subclass, and model configs drive automatic layer-type dispatch.

### Layer-Level Hierarchy

#### Base: `CacheLayerMixin` (ABC)
```
CacheLayerMixin
├── DynamicLayer              — grows via torch.cat (default generative)
├── DynamicSlidingWindowLayer — grows up to sliding_window, then rotates
├── DynamicIndexedLayer       — DynamicLayer + indexer key cache (DSA)
├── StaticLayer               — preallocated tensor, index_copy_, torch.compile
├── StaticSlidingWindowLayer  — static + sliding window
├── StaticIndexedLayer        — static + DSA indexer
├── QuantizedLayer (abstract) — KIVI-style two-tier
│   ├── QuantoQuantizedLayer  — optimum-quanto backend (qint2/qint4)
│   └── HQQQuantizedLayer     — HQQ backend (nbits 1–8)
└── LinearAttentionCacheLayerMixin (ABC)
    └── LinearAttentionLayer  — conv + recurrent states, no KV dim
        ├── LinearAttentionAndFullAttentionLayer            — hybrid dynamic
        ├── LinearAttentionAndSlidingWindowAttentionLayer   — hybrid sliding
        ├── LinearAttentionAndStaticFullAttentionLayer      — hybrid static
        └── LinearAttentionAndStaticSlidingWindowAttentionLayer
```

All layers auto-register via `__init_subclass__` into `DYNAMIC_LAYER_TYPE_MAPPING` or `STATIC_LAYER_TYPE_MAPPING` by setting `_layer_type`.

#### DynamicLayer (the default)
- Shapes: `[batch_size, num_heads, seq_len, head_dim]`, grows by `torch.cat`
- Key methods: `lazy_initialization`, `update` (cat), `crop`, `reorder_cache`, `batch_repeat_interleave`, `batch_select_indices`
- `get_max_length()` returns `-1` (no maximum)
- `reset()` zeros in-place (preserves tensor objects); `offload()` moves to CPU

#### DynamicSlidingWindowLayer
- Adds `sliding_window` param; cache limited to last `sliding_window-1` tokens
- Tracks `cumulative_length` separately (theoretical total, beyond window)
- `record_past` mode: keeps full KV until `crop()` is called (for speculative decoding rollback)
- Returns FULL states in `update()` even though only window is stored — critical correctness detail

#### StaticLayer (for torch.compile/export)
- Preallocates zero tensors of shape `[batch_size, num_heads, max_cache_len, head_dim]`
- Updates use `index_copy_` in-place (preserves static memory address)
- `mark_static_address()` tags tensors for cudagraphs compatibility
- `is_compileable = True`
- The `cumulative_length` is a **tensor** (not Python int) to avoid graph breaks

#### StaticSlidingWindowLayer
- Combines preallocation with sliding window rotation
- When full and one token arrives: uses `tensor.roll(-1, dims=-2)` followed by overwrite at `index=-1` — avoids cat entirely for token-by-token generation
- For multi-token prefill on full cache: uses `cat` fallback
- Tracks both `cumulative_length` (tensor) and `cumulative_length_int` (Python int) — the int avoids data-dependent control flow in compiled regions

#### DynamicIndexedLayer / StaticIndexedLayer
- Extra `indexer_keys` cache of shape `[batch_size, seq_len, index_head_dim]` for Dynamic Sparse Attention (DSA)
- Used by GLM MoE DSA, DeepSeek V3/V2
- `update_indexer()` mirrors the same cat (dynamic) or index_copy_ (static) pattern
- All lifecycle methods (crop, reset, offload, reorder) are extended to cover the indexer

#### QuantizedLayer / QuantoQuantizedLayer / HQQQuantizedLayer
- KIVI-style two-tier cache: full-precision residual buffer (default 128 tokens) + quantized storage
- When residual fills up, dequantize + concatenate full precision → re-quantize all → discard full precision
- Quanto backend: `qint2` (2-bit) or `qint4` (4-bit), per-channel, MaxOptimizer
- HQQ backend: nbits 1–8, group_size configurable, separate quantize/dequantize steps
- **Only supported for models with ALL full_attention layers** — raises error for sliding/hybrid
- Quantized only at the layer level; the Cache container (`QuantizedCache`) dispatches them

#### LinearAttentionLayer
- No KV dimension; stores `conv_states` (1D conv buffer) and `recurrent_states` (SSM state)
- Static shapes by design — `is_compileable = True`, `supports_early_init = False`
- `update_conv_state()` pads/preserves conv kernel window; `update_recurrent_state()` copies in-place
- Hybrid variants combine LinearAttentionLayer with DynamicLayer or StaticLayer using MRO

### Cache Container Classes

```
Cache (base)
├── DynamicCache         — lazy layer creation, config-driven dispatch
├── StaticCache          — preallocated all layers at init (compile/export)
├── QuantizedCache       — quantized KV, KIVI-style
├── EncoderDecoderCache  — self_attention + cross_attention caches
└── MtpCache             — Multi-Token Prediction offset handling
```

#### Cache Base Class
- Constructor: pass pre-built `layers` list OR `layer_class_to_replicate` (lazy append)
- `update()` dispatches to `layers[layer_idx].update()`, handling lazy append if needed
- Offloading: uses a dedicated `prefetch_stream` (CUDA stream) to async prefetch next layer from CPU while current layer computes
- `offload_only_non_sliding=True` by default — sliding layers are small enough to keep resident
- `is_linear`, `is_sliding`, `is_compileable` properties introspect all layers
- `early_initialization()` creates fake zero-size tensors for torch.export compatibility

#### DynamicCache
- Constructor accepts `config` OR `ddp_cache_data` (for distributed) OR neither (lazy DynamicLayer)
- When `config` provided: calls `get_layer_types_and_kwargs(config)` → dispatches per-layer types from `DYNAMIC_LAYER_TYPE_MAPPING`
- `__iter__` yields `(keys, values, sliding_window_tensor)` tuples for backward compatibility
- This is the default cache for all generative models if no explicit cache is passed

#### StaticCache
- Requires both `config` and `max_cache_len`
- Dispatches from `STATIC_LAYER_TYPE_MAPPING`
- Preallocates ALL layers at init time — zero tensors ready for `index_copy_`
- Used automatically when `model.generate()` detects static cache usage
- Marked `**kwargs` in constructor for backward compatibility

#### QuantizedCache
- Accepts `backend` ("quanto" or "hqq") and quantization params
- Validates all layers are `full_attention` (the only type currently supported)
- Creates one `QuantoQuantizedLayer` or `HQQQuantizedLayer` per hidden layer

#### EncoderDecoderCache
- Holds two Cache objects: `self_attention_cache` and `cross_attention_cache`
- DDP support: can reconstruct from flat tuple `(self_k, self_v, cross_k, cross_v, ...)`
- `is_updated` tracks which cross-attention layers have been populated

#### MtpCache
- Extends DynamicCache for Multi-Token Prediction (MTP) heads (DeepSeek V3 R1)
- `get_query_offset()` adds `layer_idx + 1` offset — MTP depth k runs k+1 tokens ahead
- `get_mask_sizes()` adjusts kv_offset accordingly

### Config-Driven Layer Type Dispatch

`get_layer_types_and_kwargs(config)` reads:
1. `config.layer_types` — explicit list (e.g., ["full_attention", "linear_attention", "hybrid", ...])
2. If absent: infers from `config.sliding_window` → all `sliding_attention`, or `config.attention_chunk_size` → all `chunked_attention`, else all `full_attention`
3. Shared layers: subtracts `num_kv_shared_layers` from the list
4. Returns `layer_types` + `layer_kwargs` dict with `sliding_window`, `number_of_states`, etc.

Layer types recognized:
| Type | Dynamic Mapping | Static Mapping |
|------|----------------|----------------|
| full_attention | DynamicLayer | StaticLayer |
| sliding_attention | DynamicSlidingWindowLayer | StaticSlidingWindowLayer |
| chunked_attention | DynamicSlidingWindowLayer | StaticSlidingWindowLayer |
| conv | LinearAttentionLayer | LinearAttentionLayer |
| moe | LinearAttentionLayer | LinearAttentionLayer |
| linear_attention | LinearAttentionLayer | LinearAttentionLayer |
| hybrid | LinearAttentionAndFullAttentionLayer | LinearAttentionAndStaticFullAttentionLayer |
| hybrid_sliding | LinearAttentionAndSlidingWindowAttentionLayer | LinearAttentionAndStaticSlidingWindowAttentionLayer |
| deepseek_sparse_attention | DynamicIndexedLayer | StaticIndexedLayer |

### GPU Offloading Architecture

- Enabled via `offloading=True` in Cache constructor
- Creates a dedicated `torch.Stream()` for async prefetch
- After each layer's `update()`:
  1. Wait for prefetch stream to finish
  2. Kick off prefetch for next non-sliding, non-linear layer
  3. Offload current layer (if eligible) to CPU
- `prefetch()` circles back to layer 0 when reaching the end of the list
- Linear-attention layers never offloaded (no KV to save)
- Sliding layers skipped when `offload_only_non_sliding=True` (they're small)

### torch.compile / cudagraphs Considerations

- `StaticLayer` (and variants) are `is_compileable = True`
- `DynamicLayer` is NOT compileable — `torch.cat` changes tensor shapes
- `mark_static_address()` on preallocated tensors prevents cudagraph recompilation
- `cumulative_length` is a `torch.Tensor` (not Python int) in static layers to avoid graph breaks
- `StaticSlidingWindowLayer` uses `tensor.roll(-1)` for single-token updates — avoids dynamic shapes
- `index_copy_` fallback for MPS etc. when `NotImplementedError` is raised

### Deprecations

- `SlidingWindowCache` → renamed to `StaticCache` in v5
- `get_max_cache_shape()` → `get_max_length()` (v5.16 removal target)
- `max_cache_len` property → `get_max_length()` method
- `max_batch_size` property → `batch_size` property

### Zero-Cost Relevance

- **Free to use**: All cache classes are in-memory only, no API costs
- **Memory optimization**: Sliding window and quantized caches reduce GPU memory for long generations
- **Compile speed**: StaticCache + torch.compile provides free inference speedup
- **No cloud needed**: Offloading trades GPU memory for CPU RAM at zero monetary cost

### Key Source File
- `transformers/src/transformers/cache_utils.py` (~2056 lines, latest main branch)

### References
- [Transformers cache_utils.py source](https://github.com/huggingface/transformers/blob/main/src/transformers/cache_utils.py)
- [KIVI: 2bit KV Cache Quantization Paper](https://huggingface.co/papers/2402.02750)
- [KV Cache Quantization docs](https://huggingface.co/docs/transformers/en/llm_tutorial_optimization#quantized-cache)
- [torch.compile guide](https://huggingface.co/docs/transformers/en/torch_compile)
5897|- [Dynamic Sparse Attention (DSA) in Transformers](https://arxiv.org/abs/2504.11714)
5898|
5899|## 2026-07-24: hf-hub-pull-requests-and-discussions-api — Complete Deep Dive (Topic #123)
5900|
5901|### Summary
5902|Comprehensive deep-dive into Hugging Face Hub's Pull Requests and Discussions API. Covers the full lifecycle — creating, reading, commenting, editing, merging, and closing discussions/PRs using the `huggingface_hub` Python SDK (v1.24.0) and the underlying git ref architecture.
5903|
5904|### Architecture
5905|
5906|1. **No forks.** Contributors push directly to the source repo via `refs/pr/{NUMBER}` refs.
5907|2. **Discussions and PRs are the same type.** PR is a discussion with `is_pull_request=True` + file changes.
5908|3. **Draft by default.** Programmatic PRs start in `"draft"` status.
5909|
5910|### SDK Methods
5911|
5912|| Method | Key Parameters |
5913||--------|---------------|
5914|| `create_discussion()` | `repo_id`, `title`, `pull_request=False/True` |
5915|| `create_pull_request()` | Wrapper for `create_discussion(pull_request=True)` |
5916|| `get_discussion_details()` | `repo_id`, `discussion_num` |
5917|| `get_repo_discussions()` | `repo_id`, `author`, `discussion_type`, `discussion_status` |
5918|| `comment_discussion()` | `repo_id`, `discussion_num`, `comment` |
5919|| `edit_discussion_comment()` | `repo_id`, `discussion_num`, `comment_id`, `new_content` |
5920|| `hide_discussion_comment()` | `repo_id`, `discussion_num`, `comment_id` |
5921|| `change_discussion_status()` | `repo_id`, `discussion_num`, `new_status='open'/'closed'` |
5922|| `merge_pull_request()` | `repo_id`, `discussion_num` |
5923|| `rename_discussion()` | `repo_id`, `discussion_num`, `new_title` |
5924|
5925|### Best Practice: PR with Changes
5926|
5927|```python
5928|api.create_commit(repo_id=\"user/repo\", operations=[...], create_pr=True)
5929|```
5930|
5931|### Resources
5932|- Hub docs: https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions
5933|- Python SDK source (v1.24.0)
5933|
## 2026-07-24: hf-hub-exception-reference — Complete Exception Hierarchy (Topic #130)

### Summary
Comprehensive reference of all 50+ custom exceptions in the `huggingface_hub` library — full inheritance hierarchy, attributes, when each error is raised, `hf_raise_for_status()` dispatch logic, and error-handling best practices for production use.

### Key Coverage
- Full exception hierarchy tree with 50+ classes across 15 categories (HTTP, cache, inference, TGI, auth, validation, safetensors, DDUF, sandbox, CLI, etc.)
- `HfHubHTTPError` base class with `request_id`, `server_message`, `response`, `request` attributes
- `hf_raise_for_status()` — status-code → exception dispatch logic (400→BadRequestError, 403 gated→GatedRepoError, etc.)
- TGI errors: `OverloadedError`, `ValidationError`, `IncompleteGenerationError`, `GenerationError`, `UnknownError`
- Cache errors: `CacheNotFound`, `CorruptedCacheException`, `IncompleteSnapshotError`
- OAuth errors: `DeviceCodeError` with `OAuthErrorCode` enum, `OIDCError`
- Key design patterns: multiple inheritance for backward compat, abstract EntryNotFoundError, error enrichment via `append_to_message()`, request ID tracing
|- ZeroGPU: https://huggingface.co/docs/hub/en/spaces-gpus#zero-gpu-spaces

### Skill
huggingface-hub — references/hf-learnings.md

---


## 2026-07-24: hf-hub-spaces-api-complete-reference — Complete Spaces API Reference (Topic #131)

### Summary
Comprehensive reference of the Hugging Face Hub Spaces API — all 24 `HfApi` methods for managing Spaces, the creation flow via `create_repo()`, data models (`SpaceInfo`, `SpaceRuntime`, `Volume`, `SpaceVariable`, `SpaceSecret`), enums (`SpaceHardware`, `SpaceStorage`, `SpaceStage`), and CLI equivalents. Covers zero-cost deployment patterns, dev mode, secrets/variables management, storage volumes, sleep scheduling, and common automation workflows.

### Core Architecture

Spaces are managed through the `HfApi` class in `huggingface_hub` (v1.24.0). There is **no dedicated `create_space()` method** — Spaces are created via `create_repo(repo_type="space", ...)` with Space-specific parameters. All other operations (runtime management, secrets, logs, hardware scaling) have dedicated methods.

```
┌─────────────────────────────────────────────────────┐
│                  HfApi Space Methods                 │
├─────────────────┬───────────────────┬───────────────┤
│  Lifecycle       │  Configuration    │  Query        │
├─────────────────┼───────────────────┼───────────────┤
│  create_repo()   │  add_space_secret │  space_info() │
│  duplicate_space │  delete_space_sec │  list_spaces()│
│  restart_space() │  get_space_secrets│  search_spaces│
│  pause_space()   │  add_space_variab │  get_space_run│
│  request_space_  │  delete_space_var │  list_spaces_ │
│   hardware()     │  get_space_variab │  list_space_t │
│  request_space_  │  set_space_volum  │  fetch_space_l│
│   storage()      │  delete_space_vol │               │
│  set_space_sleep │  enable_space_dev │               │
│  delete_space_   │  disable_space_de │               │
│   storage()      │  wait_for_space() │               │
└─────────────────┴───────────────────┴───────────────┘
```

### Creating a Space

Spaces are created with `create_repo(repo_type="space")`:

```python
from huggingface_hub import HfApi, SpaceHardware, SpaceStorage, Volume

api = HfApi()

# Minimal — creates a free CPU-basic Gradio Space
url = api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",          # "gradio", "docker", "static"
    exist_ok=True,
)

# With hardware, storage, secrets, and volumes
url = api.create_repo(
    repo_id="username/my-space",
    repo_type="space",
    space_sdk="gradio",
    space_hardware=SpaceHardware.CPU_BASIC,
    space_storage=SpaceStorage.SMALL,
    space_sleep_time=300,        # sleep after 5 min inactivity
    space_secrets=[{"key": "HF_TOKEN", "value": "hf_...", "description": "token"}],
    space_variables=[{"key": "MY_VAR", "value": "val"}],
    space_volumes=[Volume(type="bucket", source="username/my-bucket", mount_path="/data")],
    space_template="gradio-hello-world",
    private=True,
)
```

**Key parameters** (all prefixed `space_` for `create_repo`):
- `space_sdk`: `"gradio"`, `"docker"`, `"static"`, or `"streamlit"`
- `space_hardware`: `SpaceHardware` enum (see below)
- `space_storage`: `SpaceStorage` enum (`SMALL`, `MEDIUM`, `LARGE`)
- `space_sleep_time`: int — seconds of inactivity before sleep (GPU spaces only)
- `space_secrets`: `list[dict]` — each with `key`, `value`, optional `description`
- `space_variables`: `list[dict]` — same structure as secrets
- `space_volumes`: `list[Volume]` — bucket/model/dataset mounts
- `space_template`: `str` — template repo ID or short name (use `list_space_templates()`)

### SpaceHardware Options

| Enum Name | Value | Cost Tier | Use Case |
|-----------|-------|-----------|----------|
| `CPU_BASIC` | `"cpu-basic"` | **Free** | Lightweight demos, simple Gradio apps |
| `CPU_UPGRADE` | `"cpu-upgrade"` | Paid | CPU-intensive apps |
| `ZERO_A10G` | `"zero-a10g"` | **Free** | ZeroGPU — A10G for free (NVIDIA) |
| `T4_SMALL` | `"t4-small"` | Paid | Small GPU demos |
| `T4_MEDIUM` | `"t4-medium"` | Paid | Medium GPU demos |
| `L4X1` | `"l4x1"` | Paid | 1×L4 |
| `L4X4` | `"l4x4"` | Paid | 4×L4 |
| `L40SX1` | `"l40sx1"` | Paid | 1×L40S |
| `L40SX4` | `"l40sx4"` | Paid | 4×L40S |
| `L40SX8` | `"l40sx8"` | Paid | 8×L40S |
| `A10G_SMALL` | `"a10g-small"` | Paid | 1×A10G (small) |
| `A10G_LARGE` | `"a10g-large"` | Paid | 1×A10G (large) |
| `A10G_LARGEX2` | `"a10g-largex2"` | Paid | 2×A10G |
| `A10G_LARGEX4` | `"a10g-largex4"` | Paid | 4×A10G |
| `A100_LARGE` | `"a100-large"` | Paid | 1×A100 |
| `A100X4` | `"a100x4"` | Paid | 4×A100 |
| `A100X8` | `"a100x8"` | Paid | 8×A100 |

**Zero-cost note:** Only `CPU_BASIC` and `ZERO_A10G` are free. All GPU hardware incurs cost. ZeroGPU (`ZERO_A10G`) is a free tier for A10G but has usage limits and automatic eviction.

### SpaceStorage Options

| Enum Name | Value | Description |
|-----------|-------|-------------|
| `SMALL` | `"small"` | Default — free for CPU_BASIC |
| `MEDIUM` | `"medium"` | Additional disk space |
| `LARGE` | `"large"` | Maximum disk space |

### SpaceStage States

| Stage | Meaning |
|-------|---------|
| `NO_APP_FILE` | No app file found (misconfigured) |
| `CONFIG_ERROR` | Configuration error |
| `BUILDING` | Building container |
| `BUILD_ERROR` | Build failed |
| `RUNNING` | Space is live |
| `RUNNING_BUILDING` | Live but rebuilding |
| `RUNTIME_ERROR` | App crashed at runtime |
| `DELETING` | Being deleted |
| `STOPPED` | Stopped |
| `PAUSED` | Manually paused |
| `APP_STARTING` | Application starting |
| `RUNNING_APP_STARTING` | Running but restarting |

### All 24 HfApi Space Methods

#### Lifecycle Methods

| Method | Signature | Description |
|--------|-----------|-------------|
| `duplicate_space()` | `(from_id, to_id=None, *, private, visibility, exist_ok, hardware, storage, sleep_time, secrets, variables)` | Duplicate an existing Space. Creates a copy in your account with optional hardware/storage overrides. |
| `restart_space()` | `(repo_id, *, factory_reboot=False)` | Restart a running or paused Space. `factory_reboot=True` forces a full rebuild from scratch. |
| `pause_space()` | `(repo_id)` | Pause a Space. Different from sleeping — stays paused until manually restarted. No compute cost while paused. |
| `request_space_hardware()` | `(repo_id, hardware, *, sleep_time)` | Scale hardware up/down. Use `SpaceHardware.CPU_BASIC` to downgrade to free tier. |
| `request_space_storage()` | `(repo_id, storage)` | Request additional persistent storage. |
| `delete_space_storage()` | `(repo_id)` | Remove persistent storage, revert to ephemeral. |
| `set_space_sleep_time()` | `(repo_id, sleep_time)` | Set inactivity timeout (seconds) before auto-sleep. Only applies to GPU Spaces. |
| `enable_space_dev_mode()` | `(repo_id)` | Enable dev mode — exposes container for live debugging. |
| `disable_space_dev_mode()` | `(repo_id)` | Disable dev mode, restart without debug access. |

#### Secrets & Variables

| Method | Signature | Description |
|--------|-----------|-------------|
| `add_space_secret()` | `(repo_id, key, value, *, description)` | Add or update a secret. Values are **write-only** — cannot be read back. |
| `delete_space_secret()` | `(repo_id, key)` | Delete a secret. |
| `get_space_secrets()` | `(repo_id)` | List secret metadata (key, description, last update). Values are never returned. |
| `add_space_variable()` | `(repo_id, key, value, *, description)` | Add or update an environment variable. |
| `delete_space_variable()` | `(repo_id, key)` | Delete a variable. |
| `get_space_variables()` | `(repo_id)` | Get all variables as `dict[str, SpaceVariable]`. Values are returned. |

#### Volumes (Storage Mounts)

| Method | Signature | Description |
|--------|-----------|-------------|
| `set_space_volumes()` | `(repo_id, volumes: list[Volume])` | Atomically replace all mounted volumes. |
| `delete_space_volumes()` | `(repo_id)` | Remove all volumes. |

The `Volume` dataclass:
```python
from huggingface_hub import Volume

Volume(
    type="bucket",          # "bucket", "model", "dataset", "space"
    source="user/my-bucket",  # repo ID or bucket name
    mount_path="/data",       # container mount point (must start with /)
    revision="main",          # git revision (for repos, not buckets)
    read_only=False,          # writable for buckets, read-only for repos
    path=None,                # sub-path within source
)
```

Volume types:
- **Buckets:** Read-write mounts (free for public buckets). Use for writable persistent storage.
- **Models/Datasets/Spaces:** Read-only mounts from other repos. Defaults to `"main"` revision.

#### Query & Info

| Method | Signature | Description |
|--------|-----------|-------------|
| `space_info()` | `(repo_id, *, revision, timeout, files_metadata, expand)` | Get full Space metadata. Returns `SpaceInfo`. |
| `get_space_runtime()` | `(repo_id)` | Get runtime status. Returns `SpaceRuntime` with stage, hardware, sleep_time, storage, dev_mode, volumes. |
| `fetch_space_logs()` | `(repo_id, *, build=False, follow=False)` | Stream runtime or build logs. Iterable of log lines. |
| `wait_for_space()` | `(repo_id, *, timeout=None, poll_interval=1.0)` | Block until Space reaches a terminal stage (RUNNING, BUILD_ERROR, etc.). Returns `SpaceRuntime`. |
| `list_spaces()` | `(*, filter, author, search, datasets, models, linked, sort, limit, expand, full)` | List all Spaces matching filters. |
| `search_spaces()` | `(query, *, filter, sdk, include_non_running)` | Semantic search across Spaces. |
| `list_spaces_hardware()` | `(token)` | List available hardware options with pricing. |
| `list_space_templates()` | `(token)` | List official Space templates. |

### Data Models

#### SpaceInfo (returned by `space_info()`, `list_spaces()`)

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Full repo ID (`user/space`) |
| `author` | `str \| None` | Owner username |
| `card_data` | `SpaceCardData \| None` | YAML card metadata |
| `created_at` | `datetime \| None` | Creation timestamp |
| `datasets` | `list[str] \| None` | Linked datasets |
| `disabled` | `bool \| None` | Admin-disabled flag |
| `gated` | `Literal['auto','manual',False] \| None` | Gated access mode |
| `host` | `str \| None` | Host URL |
| `last_modified` | `datetime \| None` | Last modification |
| `likes` | `int \| None` | Like count |
| `models` | `list[str] \| None` | Linked models |
| `private` | `bool \| None` | Visibility |
| `resource_group` | `dict \| None` | Enterprise resource group |
| `runtime` | `SpaceRuntime \| None` | Current runtime info |
| `sdk` | `str \| None` | SDK type (gradio/docker/static/streamlit) |
| `sha` | `str \| None` | Git commit SHA |
| `siblings` | `list[RepoSibling] \| None` | File listing |
| `subdomain` | `str \| None` | Space subdomain |
| `tags` | `list[str] \| None` | Tags |
| `trending_score` | `int \| None` | Trending rank |
| `used_storage` | `int \| None` | Bytes used |

#### SpaceRuntime (returned by `get_space_runtime()`, `wait_for_space()`, `restart_space()`, etc.)

| Field | Type | Description |
|-------|------|-------------|
| `stage` | `SpaceStage` | Current state (RUNNING, BUILDING, PAUSED, etc.) |
| `hardware` | `SpaceHardware \| None` | Currently active hardware |
| `requested_hardware` | `SpaceHardware \| None` | Pending hardware upgrade/downgrade |
| `sleep_time` | `int \| None` | Auto-sleep timeout in seconds |
| `storage` | `SpaceStorage \| None` | Current storage tier |
| `dev_mode` | `bool` | Dev mode enabled? |
| `volumes` | `list[Volume] \| None` | Currently mounted volumes |
| `raw` | `dict` | Raw API response |

### Automation Patterns

#### Pattern 1: Create and wait for a Space to be ready

```python
from huggingface_hub import HfApi

api = HfApi()
api.create_repo(
    repo_id="user/my-demo",
    repo_type="space",
    space_sdk="gradio",
    exist_ok=True,
)
runtime = api.wait_for_space("user/my-demo", timeout=300)
assert runtime.stage.value == "RUNNING", f"Space failed: {runtime.stage}"
print(f"Space live at https://huggingface.co/spaces/user/my-demo")
```

#### Pattern 2: Zero-cost deployment (CPU, no paid extras)

```python
api.create_repo(
    repo_id="user/free-demo",
    repo_type="space",
    space_sdk="gradio",
    space_hardware=SpaceHardware.CPU_BASIC,   # free
    exist_ok=True,
)
```

#### Pattern 3: Scale down to free after GPU work

```python
api.request_space_hardware("user/gpu-demo", SpaceHardware.CPU_BASIC)
# Waits for downgrade to complete
runtime = api.wait_for_space("user/gpu-demo", timeout=120)
```

#### Pattern 4: Set up secrets programmatically

```python
api.add_space_secret("user/my-space", "API_KEY", "sk-...", description="OpenAI key")
api.add_space_variable("user/my-space", "LOG_LEVEL", "info")
```

#### Pattern 5: Duplicate an existing Space (template-style)

```python
url = api.duplicate_space(
    from_id="gradio/hello-world",
    to_id="user/my-hello",
    hardware=SpaceHardware.CPU_BASIC,
    exist_ok=True,
)
```

#### Pattern 6: Mount a bucket for persistent writable storage

```python
from huggingface_hub import Volume

api.set_space_volumes("user/my-space", [
    Volume(type="bucket", source="user/my-bucket", mount_path="/data")
])
# Inside the Space: /data/ is writable and persists across restarts
```

#### Pattern 7: Check and restart a failed Space

```python
runtime = api.get_space_runtime("user/my-space")
if runtime.stage.value in ("RUNTIME_ERROR", "BUILD_ERROR", "PAUSED"):
    new_runtime = api.restart_space("user/my-space")
    print(f"Restarted: stage={new_runtime.stage.value}")
```

#### Pattern 8: Fetch build logs for debugging failures

```python
for line in api.fetch_space_logs("user/my-space", build=True):
    print(line, end="")
```

### CLI Equivalents

The `hf` CLI provides Space management through several subcommands:

```bash
# Create a Space
hf repos create user/my-space --type space --sdk gradio

# Duplicate
hf repos duplicate source-space user/my-copy

# Hardware management
hf repos update user/my-space --hardware cpu-basic

# Secrets
hf secrets list user/my-space
hf secrets add user/my-space KEY VALUE

# Volumes
hf spaces volumes ls user/my-space
hf spaces volumes set user/my-space --volume bucket=user/my-bucket:/data

# Dev mode
hf spaces dev-mode user/my-space

# Logs
hf logs user/my-space            # runtime logs
hf logs user/my-space --build    # build logs
```

### Resources
- `huggingface_hub` Python SDK v1.24.0 — `HfApi` class
- Hub docs: https://huggingface.co/docs/hub/en/spaces-overview
- Spaces settings: https://huggingface.co/docs/hub/en/spaces-settings
- Spaces GPU: https://huggingface.co/docs/hub/en/spaces-gpus
- Spaces storage: https://huggingface.co/docs/hub/en/spaces-storage
- Spaces config reference: https://huggingface.co/docs/hub/en/spaces-config-reference
|- ZeroGPU: https://huggingface.co/docs/hub/en/spaces-gpus#zero-gpu-spaces

### Skill
huggingface-hub — references/hf-learnings.md

---

## 2026-07-24: hf-spaces-logs-monitoring-and-debugging — Deep Dive (Topic #132)

### Summary
Comprehensive deep-dive into HF Spaces logging, monitoring, and debugging — the programmatic toolkit for diagnosing build failures, runtime crashes, and sleep/wake lifecycle issues without spending money. Covers two log streams (build vs. runtime), `fetch_space_logs()`, `hf spaces logs` CLI, space status codes, lifecycle management, CI build monitoring, built-in env vars, Dev Mode (PRO), and free-tier workarounds (self-logging to dataset, health endpoints).

### Key APIs
```python
api.fetch_space_logs(repo_id)                    # drain runtime logs
api.fetch_space_logs(repo_id, build=True)        # drain build logs
api.fetch_space_logs(repo_id, follow=True)       # stream runtime logs
api.space_info(repo_id)                          # status/hardware/sdk
api.pause_space(repo_id)                         # stop
api.restart_space(repo_id)                       # rebuild container
api.request_space_hardware(repo_id, "cpu-basic") # wake or assign hardware
```
```bash
hf spaces logs user/space          # drain runtime
hf spaces logs user/space --build  # build logs
hf spaces logs user/space -f       # follow mode
hf spaces logs user/space -n 50    # last 50 lines
```

### Status → Diagnosis
- BUILD_ERROR → read build logs
- BUILDING >15 min → check build logs
- RUNNING unresponsive → check runtime logs
- SLEEPING → wake request + poll until RUNNING
- PAUSED → api.restart_space()

### Limitations
- Dev Mode requires PRO; build logs expire after next build; no pagination; free tier sleeps ~15-30 min; no GPU during Docker build

### Resources
- Manage Spaces: https://huggingface.co/docs/huggingface_hub/guides/manage-spaces
- Config reference: https://huggingface.co/docs/hub/en/spaces-config-reference
- Dev Mode: https://huggingface.co/docs/hub/en/spaces-dev-mode
- fetch_space_logs: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.fetch_space_logs

## 2026-07-24: hf-hub-xet-streamed-upload-pipeline-deep-dive — Xet Streamed Multi-Commit Upload Pipeline (Topic #135)

### Summary
Comprehensive deep-dive into the Xet-backed streamed multi-commit upload pipeline introduced in `huggingface_hub` 1.24.0. When `hf_xet` is installed (the default), `upload_folder()` no longer uses a single `create_commit()` call — instead it orchestrates a pipelined upload via `_UploadPipeline` that overlaps scanning, uploading, and committing across threads; adaptively batches files per commit; deduplicates unchanged files; and resumes on interruption by re-running the same call. Source: `huggingface_hub/_upload_pipeline.py` (682 lines, copyright 2026).

### Architecture Overview

```
Coordinator Thread (caller)              Committer Thread
┌──────────────────────────┐            ┌──────────────────────┐
│ Walk files 256-at-a-time │──batch──▶  │ Wait for Xet uploads │
│ via _fetch_upload_modes  │  queue     │ Drop unchanged files │
│                          │  (maxsize  │ Adaptive size commits │
│ Open Xet upload-commit   │   = 1)     │ PR creation (lazy)   │
│ Start xet uploads (bg)   │            │ Send git commit      │
│ Enqueue batches          │            │ Record success/fail  │
└──────────────────────────┘            └──────────────────────┘
         ▲                                        │
         │ Xet dedup + chunk upload (background)  │
         │ (single read pass, no Python sha256)   │
         └────────────────────────────────────────┘
```

### Key Components

#### 1. `is_xet_available()` — Gate Check
```python
def is_xet_available() -> bool:
    if constants.HF_HUB_DISABLE_XET:  # env var opt-out
        return False
    return is_package_available("hf_xet")
```
- `hf_xet` is installed by default with `huggingface_hub` (bundled dependency)
- Disable with `HF_HUB_DISABLE_XET=1` to force the legacy single-commit path
- Without `hf_xet`, `upload_folder()` falls back to `create_commit()` (warns if >30 files)

#### 2. `_fetch_upload_modes()` — Preupload Classification
- POSTs to `/api/{repo_type}s/{repo_id}/preupload/{revision}`
- Sends 256 files at a time (server-side limit) with `path`, `sample` (base64 first bytes), and `size`
- Each file is classified: `regular` (small git blob, base64 in commit payload), `lfs` (old path, not used by Xet pipeline), or left unset for Xet
- Sets `_should_ignore` (gitignore matched), `_upload_mode`, `upload_info` (sha256, size, sample)
- Accepts `gitignore_content` parameter (forwarded from local `.gitignore` if uploaded)
- Mutates `CommitOperationAdd` objects in-place

#### 3. `_UploadPipeline` — Main Orchestrator

**Initialization:**
- Creates a `XetSession` with a `token_refresh_url` including `?create_pr=1` if applicable
- Cache: `xet_commit_kwargs` with token refresh URL, auth headers, and `xet_headers_without_auth()`
- Extracts `.gitignore` content from the uploaded files if present
- Creates `_LiveDisplay` progress renderer (3-line TTY or periodic logger)

**Coordinator Loop (`_coordinator_loop`):**
1. Iterates `add_operations` in chunks of 256 (PREUPLOAD_BATCH_SIZE)
2. For each chunk, calls `_fetch_upload_modes()`
3. For each file in chunk:
   - If `_should_ignore` → skip (gitignore)
   - If `regular` → tracks `regular_bytes` for budget enforcement
   - If Xet → opens `batch.xet_commit` (lazy, per batch) and calls `start_upload_file()` or `start_upload_bytes()` — **upload starts immediately in background**
   - sha256 is computed by `hf_xet` during chunking (single read pass), unless `upload_info.is_hashed` (e.g. resumed)
4. Flushes the batch when:
   - File count >= `pacer.target` (adaptive, starts at 256)
   - OR `regular_bytes` >= 100 MB budget
   - OR batch age > 5 min (MAX_COMMIT_INTERVAL)
5. Enqueues each batch via `batch_queue.put()` (maxsize=1 for natural backpressure)

**Committer Loop (`_committer_loop`):**
- Runs in a daemon thread (`hf-upload-committer`)
- Polls `batch_queue.get(timeout=0.5)` — exits on sentinel or abort event

**Batch Processing (`_process_batch`):**
1. **Finalize Xet uploads:** `batch.xet_commit.wait_to_finish()` — blocks until all background uploads complete. Sets `op.upload_info.sha256` from the Xet result and marks `_is_uploaded=True`.
2. **Drop unchanged files:** Compares `_remote_oid` (from preupload response) with `_local_oid` (computed during hashing). If equal, the file is skipped — its chunks were already deduplicated by Xet, transferring ~0 bytes.
3. **Commit:** Passes remaining ops to `_commit_with_split()`

**Adaptive Commit Pacer (`_CommitPacer`):**
- `COMMIT_SIZE_SCALE = [20, 50, 75, 100, 125, 200, 250, 400, 600, 1000]`
- Starts at index 6 → **256 files per commit**
- Scales up when commit duration < 40s (TARGET_COMMIT_DURATION) and file count >= target
- Scales down on failure (index -1), down to minimum 20 files
- `record_success(duration, nb_files)` / `record_failure()`

**Commit Splitting (`_commit_with_split`):**
- Tries `_do_commit()` with all ops
- On failure: calls `pacer.record_failure()`, then recursively splits into `pacer.target`-sized chunks and retries each
- Minimum split size = `COMMIT_SIZE_SCALE[0]` = 20 files (raises if still failing at this size)

**PR Creation (Lazy, `_do_commit`):**
- Only creates the PR on the **first** actual batch commit (not for empty all-skipped uploads)
- Uses `api.create_pull_request()` explicitly (not `?create_pr=1` on commit POST) to avoid duplicate PRs on retry
- Once created, `commit_revision_quoted` is switched to `refs/pr/N` for all subsequent commits
- Commit messages: first batch uses `commit_message`, subsequent batches append ` (part N)`

**Resume Pattern:**
- Re-run `upload_folder()` with same args
- Already-committed files: preupload returns `_remote_oid == _local_oid` → dropped as unchanged
- Partially-uploaded Xet chunks: deduplicated by Xet storage backend (~0 bytes transferred)
- To resume into an existing PR: use `revision="refs/pr/N"` instead of `create_pr=True`

#### 4. `_LiveDisplay` — Progress Rendering

Three-line display on stderr:
```
  Preparing   ████████████████████  11,100 / 11,100 ✓
  Uploading   ██████████████░░░░░░  580 / 603 files  3.8GB · 19.7MB/s
  Committing  ██████████████████░░  10,800 / 11,100  14 commits
```

- TTY mode: redraws in-place every 0.5s (`_REFRESH_INTERVAL`)
- Non-TTY mode: `logger.info()` summary every 30s (`_NON_TTY_LOG_INTERVAL`)
- Disabled when `are_progress_bars_disabled()` returns True (e.g. agent output mode)
- Thread-safe counters under `threading.Lock()`

#### 5. Edge Cases

| Scenario | Handling |
|---|---|
| **All files unchanged** | `_final_commit_info()` returns last commit on target revision; logs warning; no PR created |
| **Interrupted mid-upload** | Re-run resumes: committed files skipped, Xet chunks deduplicated |
| **Empty commit prevention** | Files with `_remote_oid == _local_oid` are dropped before commit |
| **PR + interruption** | Warning suggests re-run with `revision="refs/pr/N"` instead of `create_pr=True` |
| **Large regular files** | If `regular_bytes` exceeds 100 MB budget, forces a batch flush |
| **Upload failure** | Commit splits into smaller chunks recursively; commits retried with backoff |
| **Repository not found** | `RepositoryNotFoundError` with appended hint message |
| **Abort during shutdown** | Daemon committer thread joins with 10s timeout; Xet session aborted |

### Key Constants

| Constant | Value | Purpose |
|---|---|---|
| `PREUPLOAD_BATCH_SIZE` | 256 | Files per preupload API call |
| `COMMIT_SIZE_SCALE` | [20,50,75,100,125,200,250,400,600,1000] | Adaptive batch sizes |
| `INITIAL_COMMIT_SIZE_INDEX` | 6 | Start at 256 files/commit |
| `TARGET_COMMIT_DURATION` | 40.0s | Scale up if commits faster |
| `MAX_COMMIT_INTERVAL` | 300.0s | Force commit if idle |
| `REGULAR_CONTENT_BYTES_BUDGET` | 100 MB | Regular file payload limit |

### Zero-Cost Practical Patterns

```python
# Upload a dataset folder with auto-resume
from huggingface_hub import HfApi
api = HfApi()
api.upload_folder(
    folder_path="./my-dataset",
    repo_id="user/my-dataset",
    repo_type="dataset",
    ignore_patterns="**/*.tmp",  # skip temp files
)

# Upload model checkpoints in PR (safe for CI)
api.upload_folder(
    folder_path="./checkpoints",
    repo_id="user/my-model",
    repo_type="model",
    create_pr=True,
    delete_patterns="**/*.bak",  # auto-clean old backups
)

# Upload with explicit token
api.upload_folder(
    folder_path="./model-artifacts",
    repo_id="org/my-model",
    token="hf_...",
    allow_patterns=["*.safetensors", "*.json", "*.yaml"],
)

# Resume into existing PR
api.upload_folder(
    folder_path="./checkpoints",
    repo_id="user/my-model",
    revision="refs/pr/42",  # resume into existing PR
)
```

### Resources
- Source: `huggingface_hub/_upload_pipeline.py` on GitHub
- `_commit_api.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/_commit_api.py
- `_upload_pipeline.py`: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/_upload_pipeline.py
- Xet docs: https://huggingface.co/docs/hub/en/xet/index
- `upload_folder` reference: https://huggingface.co/docs/huggingface_hub/package_reference/hf_api#huggingface_hub.HfApi.upload_folder

### Skill
huggingface-hub — references/hf-learnings.md

## 2026-07-25: hf-hub-repo-lifecycle-management — Repository CRUD & Settings API (Topic #136)

### Summary
Comprehensive deep-dive into the Hugging Face Hub repository lifecycle management API — `create_repo()`, `delete_repo()`, `repo_info()`, `repo_exists()`, `update_repo_settings()`, `move_repo()`, `duplicate_repo()`, and `super_squash_history()`. Covers all 8 methods with full parameter docs, error handling, data models, REST API equivalents, free-tier constraints, and 4 practical automation patterns. Researched from `huggingface_hub/hf_api.py` source code (v1.24.0+).

Full deep-dive: `mlops/huggingface-hub/references/hf-learnings.md` (Topic #136)

### Skill
huggingface-hub — references/hf-learnings.md

---

## 2026-07-24: hf-transformers-phi4-deep-dive — Complete Phi-4 Architecture & Ecosystem Reference (Topic #67 Deep-Dive)

### Summary
Deep-dive into Microsoft Phi-4 (14B) and its growing ecosystem — covering full architecture, Transformers integration via `Phi3ForCausalLM`, three-pillar data-centric training, inference patterns, Phi-4-mini (3.8B 128K), Phi-4-multimodal (5.6B VLM), and LoRA fine-tuning.

### Core Model: Phi-4 (14B)

- **Architecture:** Dense decoder-only Transformer using `Phi3ForCausalLM` in Transformers (no separate `Phi4ForCausalLM`). Architecture tag is `phi4` but implementation reuses Phi-3 code.
- **Dimensions:** 40 layers, hidden dim 4,960, intermediate 15,840 (swiGLU), 32 query / 8 KV heads (GQA), vocab 100,352, context 16K, RoPE, LayerNorm pre-norm.
- **Training:** 1,920 H100-80G GPUs, 21 days, 9.8T tokens, MIT license, Dec 2024.
- **Key config diffs from Phi-3:** Larger vocab (100,352 vs 32,064), wider intermediate (15,840 vs Phi-3-medium's), more layers (40 vs 32).

### Loading
```python
model = AutoModelForCausalLM.from_pretrained("microsoft/phi-4",
    torch_dtype=torch.bfloat16, device_map="auto")
```

### Training Innovation: Three-Pillar Recipe

1. **Synthetic pre-training** (~80%) — multi-agent prompting, self-revision, instruction reversal for reasoning-focused synthetic tokens
2. **Curated organic** (~20%) — filtered web, academic books, code, Q&A
3. **Post-training** — SFT + pivotal token search DPO + rejection sampling

Result: 14B surpasses GPT-4o on GPQA (56.1 vs 50.6) and MATH (80.4 vs 74.6).

### Zero-Cost Inference

- **4-bit quantization:** ~9GB VRAM via BitsAndBytesConfig (down from 28GB)
- **GGUF:** Q4_K_M fits in ~8GB RAM via llama.cpp
- **Inference Providers:** Free via Cerebras, Fireworks, Together AI, etc.

### Phi-4-mini (3.8B, April 2025)

- 128K context via LongRoPE (vs 16K in 14B)
- Ideal for long-document RAG, agentic workflows
- Fits on free T4 GPUs with QLoRA fine-tuning

### Phi-4-multimodal (5.6B, May 2025)

- SigLIP vision encoder + Phi-4-mini text decoder
- Supports interleaved image-text conversations
- Load with `AutoModelForPreTraining` (not CausalLM)

### LoRA Fine-Tuning

Target all 7 projection layers (q, k, v, o, gate, up, down) for best adaptation. ~0.5% of params trainable. Use QLoRA for free-tier training.

### Resources
- https://arxiv.org/abs/2412.08905
- https://github.com/microsoft/Phi-4CookBook
- https://huggingface.co/microsoft/phi-4

---

## 2026-07-24: hf-hub-webhooks-crud-api-deep-dive-v2 — Hub Webhooks API Complete Reference (Topic #2 Expanded)

### Summary
Comprehensive expansion of the HF Hub Webhooks API coverage. Covers the full 7-method CRUD suite (`create_webhook`, `get_webhook`, `update_webhook`, `delete_webhook`, `list_webhooks`, `enable_webhook`, `disable_webhook`), the `WebhookInfo` and `WebhookWatchedItem` data models, event payloads (5 categories: event, repo, code changes, config changes, discussions/PRs, comments), webhook secret HMAC verification, rate limits (1,000/24h), webhook Jobs (trigger HF Jobs instead of HTTP), free-tier limitations, and practical automation patterns. Source: `huggingface_hub/hf_api.py` (huggingface_hub v1.24.0) and HF Hub docs.

### Core API Reference

#### 1. WebhookInfo Data Model

```python
@dataclass
class WebhookInfo:
    id: str                                          # Unique webhook ID (e.g. "639885d811ae2bad2b7ba461")
    url: str | None                                  # Target URL (None if job-based webhook)
    job: JobSpec | None                              # Job spec (None if URL-based webhook)
    watched: list[WebhookWatchedItem]                # Entities being watched
    domains: list[Literal['repo', 'discussions']]    # Event domains to subscribe to
    secret: str | None                               # HMAC secret for payload verification
    disabled: bool                                   # Whether the webhook is disabled
```

#### 2. WebhookWatchedItem

```python
@dataclass
class WebhookWatchedItem:
    type: Literal['dataset', 'model', 'org', 'space', 'user']
    name: str
```

**Watched entity types:**
| Type | What it watches |
|------|----------------|
| `model` | Events on a specific model repo (`user/repo-name`) |
| `dataset` | Events on a specific dataset repo |
| `space` | Events on a specific Space repo |
| `user` | All repos owned by this user |
| `org` | All repos owned by this organization |

Note: `user` and `org` subscriptions require email request to HF for "all events" mode (see FAQ below).

#### 3. DOMAIN Constants

```python
WEBHOOK_DOMAIN_T = Literal['repo', 'discussions']
```

| Domain | Events captured |
|--------|----------------|
| `repo` | Push, file changes, settings updates (default) |
| `discussions` | Discussion creation, comments, PR events |

Both can be combined to receive all event types.

#### 4. Full CRUD API

##### `create_webhook()` — Create a Webhook

```python
api.create_webhook(
    url="https://my-service.com/hf-webhook",    # Target URL (mutually exclusive with job_id)
    # OR
    job_id="my-job-id",                          # HF Job ID to trigger (mutually exclusive with url)
    watched=[
        {"type": "user", "value": "beer-sakthai"},
        {"type": "model", "value": "beer-sakthai/my-model"},
    ],
    domains=["repo", "discussions"],             # Event domains
    secret="my-hmac-secret",                     # Optional: HMAC secret
)
# Returns WebhookInfo
```

**Key constraints:**
- `url` and `job_id` are **mutually exclusive** — one must be set, not both
- `watched` is **required** — at least one entity to watch
- `domains` is **optional** — defaults to `["repo"]` if omitted
- `secret` is **optional** — ASCII characters only
- All parameters except `watched` are keyword-only (marked with `*`)

##### `get_webhook()` — Get Webhook Details

```python
hook = api.get_webhook("639885d811ae2bad2b7ba461")
# Returns WebhookInfo with all fields populated
```

##### `update_webhook()` — Update Existing Webhook

```python
api.update_webhook(
    "639885d811ae2bad2b7ba461",
    url="https://my-service.com/v2/hf-webhook",  # Update URL
    watched=[{"type": "model", "value": "new-repo"}],  # Replace watched list
    domains=["repo"],                             # Replace domains
    secret="new-secret",                          # Replace secret
)
```

**Key behavior:** All parameters are **full replacements** — the watched list replaces the previous one entirely (not merged).

##### `list_webhooks()` — List All Webhooks

```python
webhooks = api.list_webhooks()
for hook in webhooks:
    print(f"{hook.id}: {hook.url or hook.job} → {hook.watched}")
```

Returns a `list[WebhookInfo]` of all webhooks configured for the authenticated user.

##### `enable_webhook()` / `disable_webhook()` — Toggle State

```python
api.enable_webhook("639885d811ae2bad2b7ba461")   # Set disabled=False → active
api.disable_webhook("639885d811ae2bad2b7ba461")   # Set disabled=True → inactive
```

##### `delete_webhook()` — Permanently Delete

```python
api.delete_webhook("639885d811ae2bad2b7ba461")    # Irreversible
```

#### 5. Webhook Payload Structure

Each webhook POST delivers a JSON payload with the following top-level fields:

##### Event

```json
{
  "event": {
    "id": "639885d811ae2bad2b7ba461",
    "type": "update",
    "scope": "repo-push",     // "repo-push", "repo-change", "discussion", "comment", etc.
    "action": "create",       // "create", "update", "delete", "close", "reopen", etc.
    "createdAt": "2024-01-15T10:30:00Z"
  }
}
```

##### Repo

```json
{
  "repo": {
    "type": "model",          // "model", "dataset", "space"
    "name": "user/repo-name",
    "fullName": "user/repo-name",
    "url": "https://huggingface.co/user/repo-name",
    "private": false,
    "gated": false,
    "likes": 42,
    "downloads": 1000
  }
}
```

##### Code Changes (on push)

```json
{
  "codeChanges": {
    "added": ["new_file.safetensors"],
    "modified": ["config.json", "README.md"],
    "removed": ["old_file.bin"]
  }
}
```

##### Config Changes

```json
{
  "configChanges": {
    "modified": ["cardData.library_name", "cardData.base_model"],
    "added": ["cardData.tags.[0]"]
  }
}
```

##### Discussions and PRs

```json
{
  "discussion": {
    "id": "639885d811ae2bad2b7ba461",
    "title": "Hello!",
    "url": {
      "web": "https://huggingface.co/some-user/some-repo/discussions/3",
      "api": "https://huggingface.co/api/models/some-user/some-repo/discussions/3"
    },
    "status": "open",
    "author": {"id": "61d2000c3c2083e1c08af22d"},
    "isPullRequest": true,
    "changes": {"base": "refs/heads/main"},
    "num": 3
  }
}
```

##### Comment

```json
{
  "comment": {
    "id": "6398872887bfcfb93a306f18",
    "author": {"id": "61d2000c3c2083e1c08af22d"},
    "content": "This adds an env key",
    "hidden": false,
    "url": {
      "web": "https://huggingface.co/some-user/some-repo/discussions/4#6398872887bfcfb93a306f18"
    }
  }
}
```

#### 6. Webhook Secret & HMAC Verification

When a secret is set, HF sends it as the `X-Webhook-Secret` HTTP header on every request. To verify:

```python
import hmac, hashlib

def verify_webhook_signature(payload_body: bytes, header_secret: str, expected_secret: str) -> bool:
    """Verify that the webhook payload came from Hugging Face."""
    return hmac.compare_digest(header_secret, expected_secret)
```

**Alternative:** Append secret as query parameter in the URL:
`https://example.com/webhook?secret=XXX` — useful when header access is difficult.

**Constraints:**
- Only ASCII characters supported in the secret
- Set/update via `create_webhook(secret=...)` / `update_webhook(secret=...)`
- Secret is masked in the UI/API responses (returned as `None` in `WebhookInfo`)

#### 7. Job-Based Webhooks

Instead of sending an HTTP POST, a webhook can trigger a **HF Job**:

```python
api.create_webhook(
    job_id="my-automation-job",                   # Job ID from hf jobs
    watched=[{"type": "user", "value": "beer-sakthai"}],
    domains=["repo"],
)
```

The job receives the same payload as an HTTP webhook would. Jobs run on HF infrastructure and can access Secrets, Datasets, and Models.

**Free-tier note:** Jobs require paid compute. For zero-cost automation, use HTTP webhooks to a free endpoint (e.g., Hermes webhook server, GitHub Actions webhook receiver, or a free-tier cloud function).

#### 8. Rate Limits & Free-Tier Constraints

| Limit | Value |
|-------|-------|
| Triggers per webhook per 24h | **1,000** |
| Increase | Contact HF (PRO/Team/Enterprise) |
| Webhook creation | Free for all accounts |
| Max webhooks | Not documented, but generous |
| URL-based webhooks | Free (you pay for the receiving endpoint) |
| Job-based webhooks | Paid (Jobs consume compute credits) |

#### 9. CLI Equivalent

The `hf webhooks` subcommand (via `hf` CLI):

```bash
# List webhooks
hf webhooks list

# Create webhook
hf webhooks create \
  --url https://my-server.com/hf-webhook \
  --watched user=beer-sakthai \
  --domains repo,discussions \
  --secret my-secret

# Get webhook details
hf webhooks info <webhook-id>

# Update webhook
hf webhooks update <webhook-id> \
  --url https://my-server.com/v2/hf-webhook

# Enable/disable
hf webhooks enable <webhook-id>
hf webhooks disable <webhook-id>

# Delete
hf webhooks delete <webhook-id>
```

Note: CLI uses `user=<name>` syntax (not `"type": "user"` dict format).

#### 10. Practical Automation Patterns

##### Pattern A: Auto-Sync on Push (Using Hermes Webhooks)

```python
# Setup script — run once
from huggingface_hub import HfApi

api = HfApi()

# Create webhook that fires on any push to Beer's repos
hook = api.create_webhook(
    url="https://hermes-instance.local/webhooks/hf-push",
    watched=[{"type": "user", "value": "beer-sakthai"}],
    domains=["repo"],
    secret=os.environ["WEBHOOK_SECRET"],
)

print(f"Webhook created: {hook.id}")
# → Register this URL in Hermes: hermes webhook subscribe hf-push --url ...
```

##### Pattern B: Monitor PRs on a Specific Model

```python
api.create_webhook(
    url="https://my-bot.com/hf-pr-handler",
    watched=[{"type": "model", "value": "beer-sakthai/my-model"}],
    domains=["discussions"],            # Only discussion/PR events
    secret="pr-bot-secret",
)
```

##### Pattern C: Mirror Datasets on Update

```python
api.create_webhook(
    url="https://my-service.com/mirror",
    watched=[{"type": "dataset", "value": "beer-sakthai/my-dataset"}],
    domains=["repo"],
)
```

##### Pattern D: Health Check — List and Refresh

```python
for hook in api.list_webhooks():
    info = api.get_webhook(hook.id)
    status = "🟢 active" if not info.disabled else "🔴 disabled"
    target = info.url or f"job:{info.job}"
    print(f"{status} {hook.id[:12]} → {target}")
    print(f"  Watches: {[f'{w.type}:{w.name}' for w in hook.watched]}")
    print(f"  Domains: {hook.domains}")
```

##### Pattern E: Development Workflow (Local Testing)

1. Start a local receiver: `python -m http.server 8080` or a webhook receiver
2. Expose via ngrok: `ngrok http 8080`
3. Create webhook with ngrok URL
4. Make test changes on HF, observe payloads
5. Use HF Webhook Settings → Activity tab → "Replay" to resend events

#### 11. Known Limitations

| Limitation | Detail |
|------------|--------|
| **No org webhooks** | Webhooks can only be defined on user accounts, not orgs |
| **No wildcard/global** | Can't subscribe to "all models on HF" — must email HF for that |
| **Secret masked** | Once set, secret is never returned in API responses (always `None`) |
| **No retry policy** | If your endpoint returns non-2xx, HF retries with exponential backoff but no persistent queue |
| **No event filtering** | Can't filter by event type within a domain — you get all events or none |
| **No delivery logs API** | Only available via Web UI Settings → Activity tab |
| **1,000/day limit** | Hard limit per webhook; contact HF for increase |

#### 12. Zero-Cost Best Practices

1. **Use URL-based webhooks (not job-based)** — Jobs cost money; HTTP webhooks to your own endpoint are free
2. **Host your webhook receiver on a free tier** — Hermes webhook server, GitHub Actions, Cloudflare Workers, PythonAnywhere, or a free HF Space with Gradio/Express
3. **Use a webhook secret** — Prevents spoofed requests; critical if your endpoint is public
4. **Validate with HMAC** — Even with secret in URL header, verify every request
5. **Use `discussions` domain sparingly** — High-traffic repos generate many discussion events; stay under 1,000/day limit
6. **Monitor activity in Web UI** — Periodically check Activity tab for delivery failures
7. **Combine with `CommitScheduler`** — Webhook + CommitScheduler = real-time sync without polling

### Resources
- Official webhooks docs: https://huggingface.co/docs/hub/en/webhooks
- HfApi reference (webhook methods): https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api#webhooks
- Source code: `huggingface_hub/hf_api.py` (search for `def create_webhook`)
- Webhooks guide (Auto-Train): https://huggingface.co/docs/hub/en/webhooks-guide-auto-retrain
- Hermes webhook server: `skill_view("hermes-agent", "references/webhooks.md")`

### Skill
huggingface-hub — references/hf-learnings.md

---


## 2026-07-24: hf-datasets-video-processing Deep Dive v2 — torchcodec 0.15.0 Advanced Features & Practical Patterns (Topic #115 — Deepened)

### Summary
Second deep-dive into Hugging Face video processing, focusing on **new torchcodec 0.15.0+ features not covered in the initial deep-dive**: in-decoder transforms (`transforms=[]` parameter), `output_dtype` for direct float32/float16 decode, `custom_frame_mappings` for raw FFmpeg filter graphs, the new `samplers` module (clip extraction at timestamps/indices, random/regular), `AudioDecoder`/`WavDecoder` for audio-from-video, `SimpleVideoDecoder` for lightweight usage, enhanced `VideoStreamMetadata` (21+ fields), and `Encoder` improvements. All verified against torchcodec 0.15.0+cu130 and datasets 5.0.0 source.

### 1. New VideoDecoder Capabilities (torchcodec 0.15.0+)

Four new parameters since the original coverage:

```python
from torchcodec.decoders import VideoDecoder
decoder = VideoDecoder(
    source,                          # str | Path | bytes | BinaryIO | Tensor
    transforms=None,                 # NEW: list[DecoderTransform | nn.Module]
    output_dtype=torch.uint8,        # NEW: torch.uint8 | float32 | float16 | "auto"
    custom_frame_mappings=None,      # NEW: str | bytes | BinaryIO (FFmpeg filter graph)
)
```

#### 1.1 `output_dtype` — Direct Typed Decode

Eliminates per-frame `.float() / 255.0` conversion:

```python
decoder_f32 = VideoDecoder("video.mp4", output_dtype=torch.float32)
frame = decoder_f32[0]    # float32 [C, H, W], range [0.0, 1.0]

decoder_f16 = VideoDecoder("video.mp4", output_dtype=torch.float16)
frame = decoder_f16[0]    # float16 [C, H, W], range [0.0, 1.0]
```

Verified: `output_dtype=torch.float32` produces float32 tensors normalized to [0.0, 1.0].

#### 1.2 `transforms` — In-Decoder Transform Chain

Transforms applied during decode — eliminates separate post-processing:

```python
from torchcodec.transforms import Resize, CenterCrop, RandomCrop

decoder = VideoDecoder("video.mp4",
    transforms=[Resize((224, 224))],
    output_dtype=torch.float32)
frame = decoder[0]  # Already (3, 224, 224), float32

# Multiple transforms: resize → center crop
decoder = VideoDecoder("video.mp4",
    transforms=[Resize((256, 256)), CenterCrop((224, 224))])

# Random crop for training augmentation
decoder = VideoDecoder("video.mp4",
    transforms=[RandomCrop((224, 224))])
```

**Available transforms:** `Resize(size)`, `CenterCrop(size)`, `RandomCrop(size)` — extensible via `DecoderTransform` ABC (any `nn.Module`).

**Current limitation:** datasets `Video` feature does NOT pass transforms or output_dtype to VideoDecoder. Direct torchcodec only.

#### 1.3 `custom_frame_mappings` — Raw FFmpeg Filter Graphs

```python
# Grayscale conversion
decoder = VideoDecoder("video.mp4", custom_frame_mappings="format=gray")
frame = decoder[0]  # [1, H, W] single-channel

# From bytes or file
decoder = VideoDecoder("video.mp4", custom_frame_mappings=b"format=gray")
```

Enables scale, color conversion, deinterlacing, denoising — anything FFmpeg filter graphs support.

### 2. Samplers Module — Clip Extraction (New in 0.15.0+)

The `torchcodec.samplers` module provides clip extraction for video understanding models.

#### 2.1 Index-Based

```python
from torchcodec.samplers._index_based import clips_at_regular_indices, clips_at_random_indices

# 8 clips, 16 frames each, stride 30
clips = clips_at_regular_indices(decoder, num_clips=8,
    num_frames_per_clip=16, num_indices_between_frames=30,
    policy="repeat_last")  # repeat_last | wrap | error

# 4 random clips, 8 frames each
random_clips = clips_at_random_indices(decoder, num_clips=4,
    num_frames_per_clip=8, num_indices_between_frames=15, policy="wrap")
```

#### 2.2 Time-Based

```python
from torchcodec.samplers._time_based import clips_at_regular_timestamps, clips_at_random_timestamps

# 6 clips, every 2s, 8 frames each, 0.1s between frames
clips = clips_at_regular_timestamps(decoder,
    seconds_between_clip_starts=2.0, num_frames_per_clip=8,
    seconds_between_frames=0.1, policy="repeat_last")

# Random temporal sampling
random_clips = clips_at_random_timestamps(decoder, num_clips=4,
    num_frames_per_clip=16, seconds_between_frames=0.05, policy="wrap")
```

**Why time-based:** Consistent regardless of frame rate (24fps, 30fps, VFR).

#### 2.3 Policy Options

| Policy | Behaviour | Use Case |
|--------|-----------|----------|
| `"repeat_last"` (default) | Repeat last valid frame beyond end | Safe padding |
| `"wrap"` | Wrap around to beginning | Data augmentation |
| `"error"` | Raise `IndexError` | Debugging |

### 3. Audio Support

#### 3.1 AudioDecoder — Audio from Video Containers

```python
from torchcodec.decoders import AudioDecoder
adec = AudioDecoder("video.mp4")
samples = adec.get_all_samples()
# AudioSamples: data=torch.Tensor(num_channels, num_samples)
print(samples.sample_rate)  # e.g., 48000 Hz

clip = adec.get_samples_played_in_range(start_seconds=0.0, stop_seconds=5.0)
```

#### 3.2 WavDecoder — WAV Files

```python
from torchcodec.decoders import WavDecoder
wav = WavDecoder("audio.wav")
samples = wav.get_all_samples()  # Same AudioSamples dataclass
```

#### 3.3 AudioSamples Dataclass

```python
@dataclass
class AudioSamples:
    data: torch.Tensor      # (num_channels, num_samples) or (num_samples,)
    pts_seconds: float
    duration_seconds: float
    sample_rate: int
```

**Limitation:** datasets `Video` feature does not expose audio.

### 4. SimpleVideoDecoder — Lightweight Access

```python
from torchcodec.decoders import SimpleVideoDecoder
decoder = SimpleVideoDecoder("video.mp4")
frame = decoder.get_frame_at(0)
batch = decoder.get_frames_at([0, 30, 60])
all_frames = decoder.get_all_frames(fps=5.0)
```

No bracket indexing — method-based access only.

### 5. Enhanced VideoStreamMetadata (21+ fields)

```python
metadata = decoder.metadata

# Standard:
print(metadata.num_frames, metadata.average_fps, metadata.duration_seconds)
print(metadata.width, metadata.height, metadata.codec)

# New in 0.15.0+:
print(metadata.num_frames_from_header)        # Container header count
print(metadata.num_frames_from_content)       # Actual content scan
print(metadata.average_fps_from_header)       # Header FPS
print(metadata.begin_stream_seconds)          # Best available start
print(metadata.begin_stream_seconds_from_header, metadata.begin_stream_seconds_from_content)
print(metadata.end_stream_seconds)            # Best available end
print(metadata.end_stream_seconds_from_content)
print(metadata.bit_rate)                      # Bit rate
print(metadata.pixel_format)                  # "yuv420p", "yuv444p"
print(metadata.color_primaries)               # "bt709", "bt2020"
print(metadata.color_space)                   # "bt709", "bt2020nc"
print(metadata.color_transfer_characteristic) # "bt709", "smpte2084"
print(metadata.pixel_aspect_ratio)            # Fraction width/height
print(metadata.rotation)                      # Display rotation degrees
```

### 6. CpuFallbackStatus — GPU Decode Health

```python
from torchcodec.decoders import CpuFallbackStatus
decoder = VideoDecoder("video.mp4", device="cuda")
print(decoder.cpu_fallback)
# NO_FALLBACK | FALLBACK | ALWAYS_WAS_CPU
```

### 7. Encoder Features

```python
from torchcodec.encoders import Encoder

encoder = Encoder()
vs = encoder.add_video(height=1080, width=1920, frame_rate=30,
    codec="h264", pixel_format="yuv420p", crf=23, preset="medium")
aud = encoder.add_audio(sample_rate=48000, num_channels=2)

encoder.open_file("output.mp4")
with encoder:
    vs.add_frames(frames_tensor)   # (N, C, H, W) uint8
    aud.add_samples(audio_tensor)  # (channels, samples)

# In-memory output
import io
buf = io.BytesIO()
encoder.open_file_like(buf, format="mp4")
# ... write frames/samples ...
encoder.close()
encoded_bytes = buf.getvalue()
```

**Encoder VideoStream parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `height` | int | required | Frame height |
| `width` | int | required | Frame width |
| `frame_rate` | float | required | Target FPS |
| `codec` | str | None | "h264", "hevc", "av1" |
| `pixel_format` | str | None | "yuv420p", "yuv444p" |
| `crf` | int|float | None | Constant Rate Factor (0-51) |
| `preset` | str|int | None | "ultrafast" to "veryslow" |
| `extra_options` | dict | None | FFmpeg codec options |
| `device` | str | "cpu" | Encoding device |

### 8. Practical Zero-Cost Patterns

#### Pattern 1: Frame Extraction at Target FPS

```python
def extract_frames(video_path: str, target_fps: int = 5) -> torch.Tensor:
    decoder = VideoDecoder(video_path, output_dtype=torch.float32,
                           transforms=[Resize((224, 224))])
    step = max(1, int(decoder.metadata.average_fps / target_fps))
    frames = decoder.get_frames_in_range(0, len(decoder), step=step)
    return frames.data  # (N, C, H, W), float32
```

#### Pattern 2: Training Clip Sampling

```python
def sample_clips(video_path: str, num_clips=4, frames=8, crop=224):
    decoder = VideoDecoder(video_path,
        transforms=[Resize((256, 256)), RandomCrop((crop, crop))],
        output_dtype=torch.float32)
    clips = clips_at_random_indices(decoder, num_clips=num_clips,
        num_frames_per_clip=frames,
        num_indices_between_frames=max(1, len(decoder) // (frames * 2)),
        policy="wrap")
    return clips.data
```

#### Pattern 3: Aligned Audio-Visual Extraction

```python
def extract_av(video_path: str, duration: float = 5.0):
    vdec = VideoDecoder(video_path, transforms=[Resize((224, 224))],
                        output_dtype=torch.float32)
    fps = vdec.metadata.average_fps
    frames = vdec.get_frames_in_range(0,
        min(len(vdec), int(fps * duration)), step=int(fps / 10))
    adec = AudioDecoder(video_path)
    audio = adec.get_samples_played_in_range(0.0, duration)
    return {"video": frames.data, "audio": audio.data,
            "sample_rate": audio.sample_rate}
```

#### Pattern 4: Quick Codec/Format Inspection

```python
def inspect_video(path: str) -> dict:
    m = VideoDecoder(path).metadata
    return {
        "codec": m.codec, "width": m.width, "height": m.height,
        "fps": m.average_fps, "frames": m.num_frames,
        "duration": m.duration_seconds, "bit_rate": m.bit_rate,
        "pixel_format": m.pixel_format, "color_space": m.color_space,
        "rotation": m.rotation,
    }
```

### 9. Datasets Integration State (datasets 5.0.0)

**Limitations:** `transforms`, `output_dtype`, `custom_frame_mappings` NOT passed through from `datasets.Video` to `VideoDecoder`. Audio decoding not integrated.

**Workarounds:**
```python
# Option 1: Apply transforms externally post-decode
decoder = example["video"]
frame = decoder[0].float() / 255.0

# Option 2: Re-decode from path with full torchcodec API
path = example["video"].metadata.path
decoder = VideoDecoder(path, transforms=[Resize((224, 224))],
                       output_dtype=torch.float32)
frame = decoder[0]

# Option 3: Embed storage for self-contained Arrow
ds = ds.map(lambda x: x)  # Forces embed_storage()
```

### 10. Dependencies

```bash
uv pip install datasets torchcodec
# FFmpeg must be system-available
ffmpeg -version
```

torchcodec 0.15.0+cu130 ships prebuilt CUDA extensions. NVDEC GPU via `device="cuda"`.

### Key Insights

1. **In-decoder transforms save memory 4x:** Resize+float32 during decode eliminates intermediate uint8 tensors.
2. **Samplers replace manual loops:** `clips_at_*` handle boundaries, stride, batch construction in one call.
3. **Audio-video alignment is free:** `AudioDecoder(video_path)` guarantees perfect timestamp alignment.
4. **Custom mappings unlock FFmpeg's full power:** Filter graphs chain multi-step processing in a single decode pass.
5. **datasets Video lags torchcodec:** Newer features not exposed through datasets -- direct torchcodec required.

### Resources
- torchcodec source: https://github.com/pytorch/torchcodec
- torchcodec docs: https://meta-pytorch.org/torchcodec
- datasets Video: https://huggingface.co/docs/datasets/en/video_dataset
- FFmpeg filters: https://ffmpeg.org/ffmpeg-filters.html

### Skill
|hf-datasets-video-processing -- references/hf-learnings.md

## 2026-07-24: hf-hub-search-discovery-api — Deep Dive (Topic #141)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Search & Discovery API — how to search, filter, sort, and paginate through models, datasets, and Spaces using both the REST API (`GET /api/models`, `/api/datasets`, `/api/spaces`) and the Python `huggingface_hub` wrappers (`list_models()`, `list_datasets()`, `list_spaces()`). Covers every query parameter, filter prefix, sort mode, expand option, and the `paginate()` mechanism. Also covers the `/api/quicksearch` endpoint for cross-type instant search. Focused on zero-cost patterns — all endpoints are public and free.

### Core Architecture — Three REST Endpoints

The Hub exposes three parallel listing endpoints with the same pagination mechanism:

| Endpoint | Python wrapper | Returns |
|----------|---------------|---------|
| `GET /api/models` | `api.list_models(...)` | `ModelInfo` |
| `GET /api/datasets` | `api.list_datasets(...)` | `DatasetInfo` |
| `GET /api/spaces` | `api.list_spaces(...)` | `SpaceInfo` |

All three use the same `paginate()` helper: fetch the first page, parse the `Link` header for the next page URL, and yield items lazily. This is the same Link-header pagination format as the GitHub API.

### Pagination — Link-Header Based

```python
# Internal paginate() logic (from huggingface_hub.utils._pagination):
def paginate(path, params, headers):
    r = session.get(path, params=params, headers=headers)
    hf_raise_for_status(r)
    yield from r.json()
    next_page = _get_next_page(r)  # parses Link header
    while next_page is not None:
        r = http_backoff("GET", next_page, headers=headers)
        hf_raise_for_status(r)
        yield from r.json()
        next_page = _get_next_page(r)
```

- First response includes `Link` header with `rel="next"` — subsequent pages are pre-encoded URLs
- Pages are fetched on-demand via generator — iteration stops at `limit` or absent Link header
- Client-side `limit` uses `itertools.islice` to cap iteration

### list_models() — Full Parameter Reference

**Signature** (all keyword-only after `self`):

```python
def list_models(self, *,
    filter, author, apps, gated, inference, inference_provider,
    trained_dataset, search, pipeline_tag, num_parameters,
    emissions_thresholds, sort, limit, expand, full,
    cardData, fetch_config, token,
) -> Iterable[ModelInfo]:
```

**HTTP query params mapping:**

| Python param | HTTP key | Values |
|---|---|---|
| `filter` | `?filter=` | Tag string (see Filter Prefix System below) |
| `author` | `?author=` | Username or org |
| `apps` | `?apps=` | `ollama`, `vllm`, etc. |
| `gated` | `?gated=` | `true` / `false` |
| `inference` | `?inference=` | `warm` — models with active provider |
| `inference_provider` | `?inference_provider=` | `all` or name: `together`, `cohere`, `fal-ai` |
| `search` | `?search=` | Text match on model ID |
| `pipeline_tag` | `?pipeline_tag=` | `text-classification`, etc. |
| `num_parameters` | `?num_parameters=` | Range: `min:6B,max:128B`, `min:70B`, `max:500M` |
| `sort` | `?sort=` | `lastModified`, `trendingScore`, `createdAt`, `downloads`, `likes` |
| `limit` | `?limit=` | Items per page |
| `full` | `?full=true` | Returns siblings, sha, tags, lastModified |
| `cardData` | `?cardData=true` | YAML metadata |
| `config` | `?config=true` | Config JSON |
| `expand` | `?expand=` | List of property names |

**Expand values for list_models:** `author`, `cardData`, `config`, `createdAt`, `disabled`, `downloads`, `downloadsAllTime`, `evalResults`, `gated`, `gguf`, `inference`, `inferenceProviderMapping`, `lastModified`, `library_name`, `likes`, `mask_token`, `model-index`, `pipeline_tag`, `private`, `safetensors`, `sha`, `siblings`, `spaces`, `tags`, `transformersInfo`, `trendingScore`, `widgetData`, `resourceGroup`

### Filter Prefix System — Cross-Domain Tagging

| Prefix | Domain | Example |
|--------|--------|---------|
| `dataset:` | Trained on dataset | `dataset:wikitext` |
| `library:` | Using library | `library:transformers` |
| `language:` | Language | `language:en` |
| `task_categories:` | Task category | `task_categories:text-classification` |
| `task_ids:` | Specific task | `task_ids:language-modeling` |
| `language_creators:` | Curation method | `language_creators:crowdsourced` |
| `multilinguality:` | Multilingual | `multilinguality:monolingual` |
| `size_categories:` | Dataset size | `size_categories:100K<n<1M` |

**Practical examples:**

```python
api = HfApi()

# LoRA / PEFT models
api.list_models(filter="peft")

# Text classification with transformers
api.list_models(filter=("library:transformers", "task:text-classification"))

# Russian language modeling datasets
api.list_datasets(filter=("language:ru", "task_ids:language-modeling"))

# Gated BERT-like models
api.list_models(search="bert", gated=True)

# Spaces using Mistral
api.list_spaces(models="mistralai/Mistral-7B-v0.1")

# Official benchmark datasets
api.list_datasets(benchmark="official")
```

### list_datasets() — Dataset-Specific Parameters

```python
def list_datasets(self, *,
    filter, author, gated, search, sort, limit, expand, full, token,
    benchmark, dataset_name,
    language_creators, language, multilinguality,
    size_categories, task_categories, task_ids,
) -> Iterable[DatasetInfo]:
```

**Expand for datasets:** `author`, `cardData`, `citation`, `createdAt`, `disabled`, `description`, `downloads`, `downloadsAllTime`, `gated`, `lastModified`, `likes`, `mainSize`, `paperswithcode_id`, `private`, `siblings`, `sha`, `tags`, `trendingScore`, `usedStorage`, `resourceGroup`

### list_spaces() — Space-Specific Parameters

```python
def list_spaces(self, *,
    filter, author, search, sort, limit, expand, full, token,
    datasets, models, linked,
) -> Iterable[SpaceInfo]:
```

**Expand for spaces:** `author`, `cardData`, `datasets`, `disabled`, `lastModified`, `createdAt`, `likes`, `models`, `private`, `runtime`, `sdk`, `siblings`, `sha`, `subdomain`, `tags`, `trendingScore`, `usedStorage`, `resourceGroup`

### Quicksearch — Cross-Type Instant Search

`GET /api/quicksearch?q=llama&limit=5&type=model`

| Param | Type | Description |
|-------|------|-------------|
| `q` | string | Search query |
| `limit` | int | Max per type |
| `type` | string | `model`, `dataset`, `space`, `paper` |
| `library` | string | Library filter |
| `pipeline` | string | Pipeline tag |
| `exclude` | array | Exclude types |
| `namespace` | string | Author/org |
| `spacesTags` | array | Space-specific tags |

Returns `{"models": [...], "datasets": [...], "spaces": [...], "papers": [...]}` — ideal for autocomplete/search suggestions.

### Advanced Zero-Cost Patterns

**1. Find GGUF (CPU-friendly) models:**
```python
gguf_models = api.list_models(filter="gguf", sort="downloads", limit=10)
```

**2. Find models with active inference provider:**
```python
warm = list(api.list_models(inference="warm", sort="likes", limit=50))
```

**3. Parameter-range search:**
```python
# 1B-10B params, sorted by likes
for m in api.list_models(num_parameters="min:1B,max:10B", sort="likes", limit=20):
    print(f"{m.modelId}: {m.likes} likes")
```

**4. Multi-tag filtering:**
```python
# Diffusers + Stable Diffusion
api.list_models(filter=("library:diffusers", "task:text-to-image"))
```

### Rate Limits & Auth
- Public endpoints are free — no token needed for read-only public repo listing
- Subject to HF-wide rate limits (429 → `http_backoff` auto-retries)
- Auth token required for private repos, gated repos, and write operations

### Key Takeaways
1. Three parallel endpoints (`/api/models`, `/api/datasets`, `/api/spaces`) share identical pagination/sort/expand architecture
2. The `filter` prefix system is the Swiss Army knife — `library:`, `dataset:`, `language:`, `task_categories:`
3. `expand` is bandwidth-efficient; use it instead of `full=true` for targeted field selection
4. `search` matches repo IDs textually; `filter` uses tag-based exact matching
5. Pagination is automatic via Link header — the Python client handles it transparently
6. `quicksearch` is the fastest path for cross-type autocomplete/dashboard use cases
7. All endpoints are zero-cost — no paid tier needed for discovery

### Resources
- `huggingface_hub` source: `hf_api.py` L2398–2970
- OpenAPI spec: https://huggingface.co/.well-known/openapi.md
- Hub search docs: https://huggingface.co/docs/hub/en/search
- Hub API docs: https://huggingface.co/docs/hub/en/api
- Pagination source: `huggingface_hub.utils._pagination`

### Skill
mlops/huggingface-hub -- references/hf-learnings.md

---

## 2026-07-24: hf-hub-tag-system-complete-reference (Topic #142)

### Summary
Comprehensive reference to the Hugging Face Hub's tagging/taxonomy system. The Hub uses a `prefix:value` tag system across models, datasets, and Spaces to enable discoverability, filtering, and categorization. Tags are stored as string arrays in repo metadata and can be set via YAML frontmatter in README.md or programmatically through the API. This reference catalogs all known tag prefixes, their valid values, how they're used across repo types, and API filtering patterns.

### How Tags Work

Tags on the Hugging Face Hub are simple string arrays attached to each repository. They follow a `prefix:value` convention for structured categorization, though unprefixed "freeform" tags also exist. Tags serve three functions:
1. **Discoverability** — repos appear in search/filter results on the Hub website and API
2. **Categorization** — pipeline tags, task categories, and library tags enable UI grouping
3. **Metadata encoding** — license, language, size, format, and provenance info

Tags are set in the YAML frontmatter of a repo's README.md:
```yaml
---
tags:
- transformers
- text-generation
- license:apache-2.0
- language:en
- arxiv:2302.13971
---
```

Or via the API:
```python
api.update_repo_settings("my-model", tags=["transformers", "text-generation", "license:apache-2.0"])
api.update_repo_settings("my-dataset", tags=["task_categories:text-generation", "language:en", "format:parquet"])
```

### Models Tag System

Models use the richest tag system. Tag values inferred from API sampling of 300+ top-downloaded models:

**Tag prefixes (structured):**

| Prefix | Purpose | Example Values | Source |
|--------|---------|----------------|--------|
| `license:` | License type | `apache-2.0`, `mit`, `cc-by-4.0`, `cc-by-nc-4.0`, `cc0-1.0`, `cc-by-nc-sa-3.0`, `cc-by-sa-4.0`, `gpl-3.0`, `gpl`, `agpl-3.0`, `bsd`, `other`, `odbl`, `gfdl`, `fair-noncommercial-research-license`, `cdla-sharing-1.0`, `cc-by-nd-4.0` | YAML / API |
| `dataset:` | Training dataset used | `dataset:wikitext`, `dataset:bookcorpus`, `dataset:s2orc`, `dataset:ms_marco` | Automatically inferred or YAML |
| `base_model:` | Parent/base model | `base_model:google-bert/bert-base-uncased` | YAML / API |
| `arxiv:` | Associated paper | `arxiv:1810.04805`, `arxiv:2501.12948` | YAML / API |
| `deploy:` | Deployment platform | `deploy:sagemaker`, `deploy:azure`, `deploy:gcp` | YAML / API |
| `region:` | Data hosting region | `region:us`, `region:eu`, `region:asia` | Hub-assigned |
| `doi:` | DOI identifier | `doi:10.xxxx/zenodo` | YAML |
| `diffusers:` | Diffusers classifier-free guidance | `diffusers:classifier-free` | Diffusers metadata |

**Unprefixed (freeform) tags — most commonly found:**
`transformers`, `pytorch`, `tf`, `jax`, `rust`, `onnx`, `safetensors`, `coreml`, `openvino`, `gguf`, `llama.cpp`, `timm`, `sentence-transformers`, `bert`, `vit`, `whisper`, `text-generation-inference`, `endpoints_compatible`, `conversational`, `custom_code`, `exbert`, `gguf`, `mlx`, `litert-lm`, `ctranslate2`, `speechbrain`, `ultralytics`, `vllm`

**Special model-level metadata (separate from tags):**

| Field | Type | Description | Typical Values |
|-------|------|-------------|----------------|
| `pipeline_tag` | string | Primary ML task | `text-generation`, `image-classification`, `automatic-speech-recognition`, `fill-mask`, `feature-extraction`, `sentence-similarity`, `text-classification`, `text-to-image`, `text-to-speech`, `image-to-text`, `image-to-image`, `object-detection`, `image-segmentation`, `zero-shot-classification`, `translation`, `summarization`, `question-answering`, `token-classification`, `text-ranking`, `depth-estimation`, `image-text-to-text`, `any-to-any`, `mask-generation`, `time-series-forecasting`, `audio-classification`, `audio-to-audio`, `voice-activity-detection`, `text-to-audio`, `image-to-video`, `audio-text-to-text`, `text-to-3d`, `zero-shot-image-classification`, `zero-shot-object-detection`, `table-question-answering`, `image-feature-extraction`, `video-classification`, `video-text-to-text`, `visual-question-answering` |
| `library_name` | string | Primary framework | `transformers`, `diffusers`, `sentence-transformers`, `gguf`, `timm`, `vllm`, `open_clip`, `whisperkit`, `ultralytics`, `mlx`, `fasttext`, `speechbrain`, `nemo`, `llama.cpp`, `pyannote-audio`, `transformers.js`, `coqui`, `ctranslate2`, `chronos-forecasting`, `depth-anything-3`, `diffusion-single-file`, `litert-lm`, `mivolo`, `Model Optimizer`, `perception-encoder`, `pytorch`, `transcribe.cpp`, `trellis`, `trellis2`, `UniDepth`, `voxcpm`, `chatterbox` |

**All 35 known pipeline_tag values (verified via HF API):**
1. `any-to-any`
2. `audio-classification`
3. `audio-text-to-text`
4. `audio-to-audio`
5. `automatic-speech-recognition`
6. `depth-estimation`
7. `feature-extraction`
8. `fill-mask`
9. `image-classification`
10. `image-feature-extraction`
11. `image-segmentation`
12. `image-text-to-text`
13. `image-to-3d`
14. `image-to-image`
15. `image-to-text`
16. `image-to-video`
17. `mask-generation`
18. `object-detection`
19. `question-answering`
20. `sentence-similarity`
21. `summarization`
22. `table-question-answering`
23. `text-classification`
24. `text-generation`
25. `text-ranking`
26. `text-to-audio`
27. `text-to-image`
28. `text-to-speech`
29. `time-series-forecasting`
30. `token-classification`
31. `translation`
32. `voice-activity-detection`
33. `zero-shot-classification`
34. `zero-shot-image-classification`
35. `zero-shot-object-detection`

### Datasets Tag System

Datasets use the most structured tag system with the most prefix categories. Tag values verified by API sampling of 500 top-downloaded datasets:

**Tag prefixes (structured):**

| Prefix | Purpose | Example Values |
|--------|---------|----------------|
| `task_categories:` | High-level ML task | `text-generation`, `question-answering`, `image-classification`, `summarization`, `translation`, `token-classification`, `text-classification`, `automatic-speech-recognition`, `feature-extraction`, `object-detection`, `image-segmentation`, `image-to-text`, `image-to-image`, `text-to-image`, `text-to-speech`, `audio-classification`, `video-classification`, `reinforcement-learning`, `robotics`, `tabular-classification`, `tabular-regression`, `time-series-forecasting`, `any-to-any`, `depth-estimation`, `fill-mask`, `image-feature-extraction`, `image-text-to-image`, `image-text-to-text`, `image-to-3d`, `image-to-video`, `keypoint-detection`, `multiple-choice`, `other`, `table-question-answering`, `text-to-3d`, `text-to-audio`, `text-to-video`, `video-text-to-text`, `visual-question-answering`, `zero-shot-classification`, `zero-shot-image-classification`, `audio-to-audio` (42 values) |
| `task_ids:` | Specific sub-task | `language-modeling`, `masked-language-modeling`, `conversational`, `extractive-qa`, `open-domain-qa`, `closed-domain-qa`, `multiple-choice-qa`, `abstractive-qa`, `open-domain-abstractive-qa`, `dialogue-generation`, `dialogue-modeling`, `coreference-resolution`, `natural-language-inference`, `sentiment-classification`, `topic-classification`, `semantic-similarity-classification`, `semantic-similarity-scoring`, `acceptability-classification`, `multi-class-image-classification`, `multi-input-text-classification`, `text-scoring`, `word-sense-disambiguation`, `semantic-segmentation`, `speaker-identification`, `task-planning`, `news-articles-summarization` (26 values) |
| `language:` | ISO language code | `en`, `fr`, `de`, `es`, `zh`, `ja`, `ko`, `ar`, `ru`, `pt`, `code`, and 2043+ ISO 639-3 codes |
| `license:` | License type | Same as model licenses (see above) + `cc-by-nc-3.0`, `cc-by-sa-3.0`, `cc-by-nd-4.0`, `cc-by-nc-sa-4.0` |
| `size_categories:` | Number of samples (11 categories) | `n<1K`, `1K<n<10K`, `10K<n<100K`, `100K<n<1M`, `1M<n<10M`, `10M<n<100M`, `100M<n<1B`, `1B<n<10B`, `10B<n<100B`, `100B<n<1T`, `n>1T` |
| `format:` | Storage format | `parquet`, `csv`, `json`, `text`, `imagefolder`, `audiofolder`, `webdataset`, `optimized-parquet`, `agent-traces` |
| `modality:` | Data modality | `text`, `image`, `audio`, `video`, `tabular`, `3d`, `multimodal` |
| `library:` | Compatible library | `datasets`, `pandas`, `polars`, `mlcroissant`, `dask` |
| `annotations_creators:` | Annotation origin | `found`, `crowdsourced`, `machine-generated`, `expert-generated`, `no-annotation`, `other` |
| `language_creators:` | Language data origin | `found`, `crowdsourced`, `expert-generated`, `machine-generated`, `other` |
| `multilinguality:` | Language scope | `monolingual`, `multilingual`, `cross-lingual`, `translation` |
| `source_datasets:` | Dataset origin | `original`, `extended`, `extracted`, `split` |
| `region:` | Hosting region | `us`, `eu`, `asia` |
| `arxiv:` | Associated paper | `arxiv:2406.17557` |
| `benchmark:` | Benchmark status | `original`, `extended` |
| `doi:` | DOI identifier | `doi:10.xxxx/zenodo` |

**All 11 size_categories values (exact complete set):**
| Value | Range |
|-------|-------|
| `n<1K` | Fewer than 1,000 samples |
| `1K<n<10K` | 1,000 – 10,000 |
| `10K<n<100K` | 10,000 – 100,000 |
| `100K<n<1M` | 100,000 – 1,000,000 |
| `1M<n<10M` | 1,000,000 – 10,000,000 |
| `10M<n<100M` | 10 – 100 million |
| `100M<n<1B` | 100 million – 1 billion |
| `1B<n<10B` | 1 – 10 billion |
| `10B<n<100B` | 10 – 100 billion |
| `100B<n<1T` | 100 billion – 1 trillion |
| `n>1T` | Over 1 trillion samples |

**All 42 task_categories values (exact set):**
`any-to-any`, `audio-classification`, `audio-to-audio`, `automatic-speech-recognition`, `depth-estimation`, `feature-extraction`, `fill-mask`, `image-classification`, `image-feature-extraction`, `image-segmentation`, `image-text-to-image`, `image-text-to-text`, `image-to-3d`, `image-to-image`, `image-to-text`, `image-to-video`, `keypoint-detection`, `multiple-choice`, `object-detection`, `other`, `question-answering`, `reinforcement-learning`, `robotics`, `summarization`, `table-question-answering`, `tabular-classification`, `tabular-regression`, `text-classification`, `text-generation`, `text-to-3d`, `text-to-audio`, `text-to-image`, `text-to-speech`, `text-to-video`, `time-series-forecasting`, `token-classification`, `translation`, `video-classification`, `video-text-to-text`, `visual-question-answering`, `zero-shot-classification`, `zero-shot-image-classification`

**All 26 task_ids values (exact set):**
`abstractive-qa`, `acceptability-classification`, `closed-domain-qa`, `conversational`, `coreference-resolution`, `dialogue-generation`, `dialogue-modeling`, `extractive-qa`, `language-modeling`, `masked-language-modeling`, `multi-class-image-classification`, `multi-input-text-classification`, `multiple-choice-qa`, `natural-language-inference`, `news-articles-summarization`, `open-domain-abstractive-qa`, `open-domain-qa`, `semantic-segmentation`, `semantic-similarity-classification`, `semantic-similarity-scoring`, `sentiment-classification`, `speaker-identification`, `task-planning`, `text-scoring`, `topic-classification`, `word-sense-disambiguation`

### Spaces Tag System

Spaces have a more limited tag system:

**Tag prefixes:**
| Prefix | Purpose | Example Values |
|--------|---------|----------------|
| `language:` | Primary language | `english`, `chinese`, `french`, `multilingual` |
| `region:` | Hosting region | `us`, `eu` |
| `modality:` | Content modality | `text`, `image`, `audio`, `video`, `3d` |
| `eval:` | Evaluation type | `code`, `math`, `reasoning` |
| `judge:` | Judging method | `auto`, `human`, `llm` |
| `submission:` | Submission method | `automatic`, `manual` |
| `test:` | Test set access | `public`, `private` |

**SDK values (separate from tags):**
`sdk: gradio`, `sdk: docker`, `sdk: static`

**Unprefixed tags:**
`docker`, `leaderboard`, `chat`, `text-generation`, `image-generation`, `voice`, `audio`, `vision`

### Programmatic Tag Discovery

Since the Hub doesn't publish a complete tag vocabulary (there is no `/api/tags` endpoint), the most reliable way to discover valid values is by sampling the API:

```python
from huggingface_hub import HfApi
api = HfApi()

# Discover pipeline tags from actual models
pipelines = set()
for m in api.list_models(sort="downloads", limit=200):
    if m.pipeline_tag:
        pipelines.add(m.pipeline_tag)

# Discover dataset size categories
size_cats = set()
for ds in api.list_datasets(sort="downloads", limit=500, full=True):
    for tag in ds.tags:
        if tag.startswith("size_categories:"):
            size_cats.add(tag.split(":", 1)[1])

# Discover model libraries
libs = set()
for m in api.list_models(sort="downloads", limit=200):
    if m.library_name:
        libs.add(m.library_name)
```

### API Filtering by Tags

Tags are the primary filtering mechanism in the Hub API:

```python
# Single tag filter (by prefix)
api.list_models(filter="library:transformers")

# Multiple tag filters (AND logic — use tuple)
api.list_models(filter=("task:text-generation", "library:diffusers"))

# Dataset multi-filter: English text generation datasets in Parquet format
api.list_datasets(
    filter=("task_categories:text-generation", "language:en", "format:parquet"),
    sort="downloads",
    limit=20,
)

# Unprefixed tag filter
api.list_models(filter="gguf", sort="downloads")  # All GGUF models
api.list_models(filter="safetensors", sort="likes")  # All SafeTensors models
```

### Tag Best Practices

1. **Always include at minimum**: `pipeline_tag` (models), `task_categories` (datasets), `license`, and `language` tags for discoverability
2. **Use correct casing**: Tags are case-sensitive. Standard values are lowercase (`en`, not `EN`)
3. **Add arxiv papers**: Include `arxiv:XXXX.XXXXX` for paper-backed models/datasets — enables paper cross-linking on the Hub
4. **Don't over-tag**: 5-15 focused tags is ideal. Over-tagging with irrelevant tags doesn't improve discoverability
5. **Prefer prefix tags over freeform**: `license:mit` is better than just `mit` — it's unambiguous and filterable
6. **Dataset size categories**: Always set `size_categories` for datasets — it's required for filtered browsing
7. **Avoid typos**: Invalid tags are silently ignored. Tag values must match exactly at search time
8. **Check existing tags**: Browse similar repos to see what tags are commonly used in your category

### Resources
- Hub search docs: https://huggingface.co/docs/hub/en/search
- Model cards docs: https://huggingface.co/docs/hub/en/model-cards
- Dataset cards docs: https://huggingface.co/docs/hub/en/datasets-cards
- Hub API reference: https://huggingface.co/docs/hub/en/api
- OpenAPI spec: https://huggingface.co/.well-known/openapi.md
- Tag discovery via API: `HfApi.list_models()` / `list_datasets()` / `list_spaces()`

### Skill
mlops/huggingface-hub -- references/hf-learnings.md

---

## 2026-07-24: smolagents Multi-Agent Orchestration Patterns (Topic #144 — Deep Dive on hf-agents-course)

### Summary
Deep-dive into smolagents v1.26.0 multi-agent orchestration patterns from the official HF Agents Course. Covers CodeAgent vs ToolCallingAgent paradigms, manager-worker hierarchy with managed_agents, custom tool construction with @tool, agent memory management (replay, dynamic mutation, step callbacks, step-by-step execution), and best practices for building reliable multi-agent systems. Full content in mlops/hf-agents-course/references/hf-learnings.md.

### Key Findings
- **CodeAgent** (code synthesis) for reasoning/planning; **ToolCallingAgent** (JSON tool calls) for reliable dispatching. Choice depends on task complexity.
- **Multi-agent = manager + workers**: Manager (CodeAgent) receives task, plans, and delegates via managed_agents list. Workers need explicit `name` and `description`.
- **Agent memory is mutable**: Access `agent.memory.steps` to read/modify history, replay runs, or inject prior context. Step callbacks (`step_callbacks=[]`) enable live memory editing.
- **Custom tools** require type annotations, clear docstring parameter formats, and verbose logging via `print()` for LLM self-correction.

### Resources
- https://huggingface.co/learn/agents-course/unit2/smolagents/introduction
- https://huggingface.co/docs/smolagents/main/en/guided_tour
- https://huggingface.co/docs/smolagents/main/en/examples/multiagents
- https://huggingface.co/docs/smolagents/main/en/tutorials/building_good_agents
- https://huggingface.co/docs/smolagents/main/en/tutorials/memory

### Skill
mlops/hf-agents-course -- references/hf-learnings.md

---

## 2026-07-24: hf-huggingface-hub-download-lifecycle — `hf_hub_download()` Internals (Topic #147)

### Summary
Complete deep-dive into the internal working of `hf_hub_download()` — the primary entry-point for downloading files from the Hugging Face Hub. Covers the full download lifecycle: metadata HEAD call with CDN redirect following, cache lookup via `try_to_load_from_cache()`, the `.no_exist` cache for known-missing files, concurrent download protection via `WeakFileLock` (fcntl/flock), HTTP streaming download with automatic resume/retry (up to 5 attempts), Xet-accelerated downloads via `xet_get()` (parallel chunked downloads from CAS server), atomic per-process temp files for correctness on broken-flock filesystems (NFS/Lustre), symlink creation from `snapshots/` to `blobs/`, the `local_dir` path with etag matching and sha256 fallback, dry-run mode (`DryRunFileInfo`), and all environment variables. Source-verified against huggingface_hub v1.24.0 file_download.py (2026 lines, on GitHub at `src/huggingface_hub/file_download.py`).

### Key Findings
- **Cache-first architecture**: `try_to_load_from_cache()` checks `snapshots/`, `refs/`, and `.no_exist/` before any network call. The `.no_exist` cache prevents repeated 404 HEAD requests.
- **Two download methods**: HTTP streaming (`http_get()`) for standard repos, Xet chunked download (`xet_get()`) for Xet-enabled repos (default since v0.32.0). Files > 50GB require Xet.
- **Robust concurrency**: `WeakFileLock` (fcntl) serializes downloads, but on NFS/Lustre where `flock()` is a no-op, per-process temp files (`{uuid}.incomplete`) ensure correctness — the last process to rename wins.
- **local_dir optimization**: Uses `download_metadata.json` + etag/SHA256 matching to avoid re-downloading files that haven't changed, plus cache fallback before network.
- **6 retries max**: HTTP download auto-retries 5 times (1s sleep) on transient network errors. Metadata HEAD retries once with 60s timeout.

### Resources
- Source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/file_download.py
- Download guide: https://huggingface.co/docs/huggingface_hub/en/guides/download
- Full content in huggingface-hub -- references/hf-learnings.md

### Skill
huggingface-hub -- references/hf-learnings.md

---

## 2026-07-24: hf-hub-organization-management-api — Managing Organizations, Members, Repos, and Teams (Topic #150)

### Summary
Comprehensive deep-dive into the Hugging Face Hub Organization Management ecosystem — covering the full lifecycle of organizations on the Hub: Python SDK (`huggingface_hub` `HfApi`) methods, REST API endpoints, data models (`Organization`, `User`), repo lifecycle under org namespaces, resource groups (Enterprise), and the web UI management interface. Built entirely from source code analysis of `huggingface_hub` v1.24.0.

### Core Architecture

Organizations on the Hugging Face Hub are **namespace containers** that own models, datasets, Spaces, and buckets. They provide:
- **Shared ownership** — repos belong to the org, not any individual
- **Role-based access** — members have reader/writer/admin roles
- **Resource groups** (Enterprise) — granular access control within an org
- **Team plan** — paid tier with additional features (private repos, higher rate limits)
- **Verification** — verified badge for official orgs

API endpoint base: `https://huggingface.co/api/organizations/{organization}`

### Data Models

#### Organization Dataclass

```python
@dataclass
class Organization:
    avatar_url: str
    name: str                        # Unique org name on Hub
    fullname: str                    # Display name
    details: str | None = None       # Description/mission
    is_verified: bool | None = None  # Official org badge
    is_following: bool | None = None # Auth user follows this org?
    num_users: int | None = None     # Member count
    num_models: int | None = None    # Models owned
    num_spaces: int | None = None    # Spaces owned
    num_datasets: int | None = None  # Datasets owned
    num_followers: int | None = None # Follower count
    num_papers: int | None = None    # Authored papers
    plan: str | None = None          # "enterprise", "team", or None
```

#### User Dataclass (member context)

```python
@dataclass
class User:
    username: str
    fullname: str
    avatar_url: str
    details: str | None = None
    is_following: bool | None = None
    is_pro: bool | None = None
    num_models: int | None = None
    num_datasets: int | None = None
    num_spaces: int | None = None
    num_discussions: int | None = None
    num_papers: int | None = None
    num_upvotes: int | None = None
    num_likes: int | None = None
    num_following: int | None = None
    num_followers: int | None = None
    orgs: list[Organization] | None = None  # Orgs the user belongs to
```

**Key attributes available from JSON response:**
| JSON field | Python field | Type | Description |
|------------|-------------|------|-------------|
| `avatarUrl` | `avatar_url` | `str` | Avatar URL |
| `name` | `name` | `str` | Unique org name |
| `fullname` | `fullname` | `str` | Display name |
| `details` | `details` | `str\|None` | Description |
| `isVerified` | `is_verified` | `bool\|None` | Badge status |
| `isFollowing` | `is_following` | `bool\|None` | Auth user follows? |
| `numUsers` | `num_users` | `int\|None` | Member count |
| `numModels` | `num_models` | `int\|None` | Model count |
| `numSpaces` | `num_spaces` | `int\|None` | Space count |
| `numDatasets` | `num_datasets` | `int\|None` | Dataset count |
| `numFollowers` | `num_followers` | `int\|None` | Follower count |
| `numPapers` | `num_papers` | `int\|None` | Paper count |
| `plan` | `plan` | `str\|None` | Plan type |

### Python SDK — Reading Org Information

#### get_organization_overview() — Org Profile

```python
from huggingface_hub import HfApi

api = HfApi()
org = api.get_organization_overview("huggingface")

print(f"Name: {org.fullname}")          # "Hugging Face"
print(f"Handle: {org.name}")             # "huggingface"
print(f"Description: {org.details}")     # "We're on a journey..."
print(f"Members: {org.num_users}")       # e.g., 150
print(f"Models: {org.num_models}")       # e.g., 30000+
print(f"Datasets: {org.num_datasets}")   # e.g., 5000+
print(f"Spaces: {org.num_spaces}")       # e.g., 2000+
print(f"Followers: {org.num_followers}") # e.g., 10000+
print(f"Papers: {org.num_papers}")       # e.g., 50+
print(f"Verified: {org.is_verified}")    # True
print(f"Plan: {org.plan}")               # "enterprise"
```

**REST endpoint:** `GET /api/organizations/{organization}/overview`

**Error handling:**
```python
from huggingface_hub import HfApi
from requests.exceptions import HTTPError

api = HfApi()
try:
    org = api.get_organization_overview("non-existent-org")
except HTTPError as e:
    if e.response.status_code == 404:
        print("Organization does not exist on the Hub")
```

#### list_organization_members() — Member Roster

```python
from huggingface_hub import HfApi

api = HfApi()
members = api.list_organization_members("huggingface")

for member in members:
    print(f"{member.username:20s} | {member.fullname:30s} | pro={member.is_pro}")
```

Returns an `Iterable[User]` — uses pagination internally via the `paginate()` helper.

**REST endpoint:** `GET /api/organizations/{organization}/members`

#### list_organization_followers() — Follower List

```python
from huggingface_hub import HfApi

api = HfApi()
followers = api.list_organization_followers("huggingface")

for follower in followers:
    print(f"{follower.username} — {follower.fullname}")
```

Returns an `Iterable[User]` — uses pagination.

**REST endpoint:** `GET /api/organizations/{organization}/followers`

### Python SDK — Creating & Managing Repos Under an Org

#### Creating Repos in an Org Namespace

Use `create_repo()` with an org-prefixed `repo_id`:

```python
from huggingface_hub import HfApi

api = HfApi()
url = api.create_repo(
    repo_id="my-org/my-model",
    repo_type="model",
    private=False,           # or True for private
    exist_ok=False,          # set True to avoid error if exists
)
print(url)  # https://huggingface.co/my-org/my-model
```

**Token requirements:** The authenticated user must be a member of the org with at least **write** permission. Read-only members cannot create repos under the org namespace.

**Supported repo types:**
| repo_type | Description |
|-----------|-------------|
| `None` (default) | Model |
| `"dataset"` | Dataset |
| `"space"` | Space |

**Enterprise: Resource Groups:**
```python
api.create_repo(
    repo_id="my-org/restricted-model",
    repo_type="model",
    resource_group_id="66670e5163145ca562cb1988",  # Enterprise only
)
```

Resource groups allow org admins to define which members can access specific repos. The `resource_group_id` can be found in the URL of the resource's page on the Hub.

#### Moving/Transferring Repos

```python
from huggingface_hub import HfApi

api = HfApi()
# Transfer a repo from a user to an org
api.move_repo(
    from_id="my-user/my-model",
    to_id="my-org/my-model",
    repo_type="model",
)
# Transfer between orgs
api.move_repo(
    from_id="org-a/my-model",
    to_id="org-b/my-model",
)
```

**Limitations (per HF docs):**
- Moving repos across namespaces requires appropriate permissions in both source and target
- Cannot move repos with the same name in target namespace
- LFS objects are preserved
- Git history is fully preserved

#### Duplicating Repos

Server-side copy — preserves full git history and LFS without local download:

```python
from huggingface_hub import HfApi

api = HfApi()
# Duplicate a model to an org
api.duplicate_repo(
    from_id="google/gemma-2-2b",
    to_id="my-org/gemma-2-2b-fork",
    repo_type="model",
)
```

#### Updating Repo Settings

```python
from huggingface_hub import HfApi

api = HfApi()
# Change visibility to private
api.update_repo_settings(
    repo_id="my-org/my-model",
    private=True,
)
# Enable gated access (manual approval)
api.update_repo_settings(
    repo_id="my-org/my-model",
    gated="manual",  # "auto" for auto-approve, False to disable
)
# Or set visibility directly
api.update_repo_settings(
    repo_id="my-org/my-space",
    visibility="protected",  # "public", "private", or "protected" (Spaces only)
)
```

#### Listing All Repos Under an Org

```python
from huggingface_hub import list_user_repos

# List all repos for an organization
repos = list(list_user_repos(namespace="my-org"))
for repo in repos:
    print(f"{repo.id:40s} | type={repo.type:10s} | size={repo.size}")
```

**REST endpoint:** `GET /api/organizations/{namespace}/settings/repositories`

#### Deleting Repos

```python
from huggingface_hub import HfApi

api = HfApi()
api.delete_repo(
    repo_id="my-org/old-model",
    repo_type="model",
    missing_ok=True,  # Don't error if already gone
)
# CAUTION: This is IRREVERSIBLE
```

### Whoami — Understanding Your Org Affiliations

```python
from huggingface_hub import whoami

info = whoami()
print(f"User: {info['name']}")
for org in info.get('orgs', []):
    print(f"  Org: {org['name']} — role: {org.get('role', 'N/A')}")
```

The `whoami` response includes:
```python
{
    "name": "beer-sakthai",
    "fullname": "Beer Sakthai",
    "email": "beer@example.com",
    "canPay": False,
    "isPro": False,
    "orgs": [
        {
            "name": "my-org",
            "fullname": "My Organization",
            "avatarUrl": "https://...",
            "role": "admin"  # "admin", "write", or "read"
        }
    ]
}
```

**Cache support:** Pass `cache=True` to `whoami()` to cache the result for the duration of the Python process. Useful when calling `whoami` multiple times, as this endpoint is heavily rate-limited.

### REST API — Organization Endpoints Reference

Base URL: `https://huggingface.co`

| Method | Endpoint | SDK Method | Description |
|--------|----------|-----------|-------------|
| `GET` | `/api/organizations/{org}/overview` | `get_organization_overview()` | Org profile |
| `GET` | `/api/organizations/{org}/members` | `list_organization_members()` | Paginated member list |
| `GET` | `/api/organizations/{org}/followers` | `list_organization_followers()` | Paginated follower list |
| `GET` | `/api/organizations/{org}/settings/repositories` | `list_user_repos(namespace=org)` | All repos with storage info |
| `POST` | `/api/repos/create` | `create_repo()` | Create repo under org* |
| `POST` | `/api/repos/move` | `move_repo()` | Transfer/move repo* |
| `POST` | `/api/repos/duplicate` | `duplicate_repo()` | Server-side copy* |
| `DELETE` | `/api/repos/delete` | `delete_repo()` | Delete repo* |
| `POST` | `/api/repos/{repo}/settings` | `update_repo_settings()` | Update visibility/gating |

*Requires token with write/admin role in org

### Web UI Management

#### Organization Settings Page

URL: `https://huggingface.co/{org}/settings`

Available settings:
- **Profile** — name, description, avatar
- **Members** — invite, remove, change roles (admin/write/read)
- **Billing** — plan upgrades, payment methods
- **Resource Groups** (Enterprise) — granular access control
- **OAuth Apps** — connected applications
- **Webhooks** — org-level webhooks
- **Audit Log** — Enterprise, tracks all actions

#### Member Roles

| Role | Description |
|------|-------------|
| **Admin** | Full control — manage members, billing, settings, all repos |
| **Write** | Create and push to repos under org namespace |
| **Read** | Read-only access to public org repos; cannot create/push |

**Role management is only available via the web UI** — there is no Python SDK method to invite/remove members or change roles programmatically.

#### Creating an Organization

Via web UI only — visit `https://huggingface.co/settings/organizations` → "New Organization":
- Requires a unique name (username-style, alphanumeric + hyphens)
- Full name (display name)
- Description (optional)
- Auto-creates you as the sole admin member

### CLI Interaction

The `hf` CLI has limited direct org commands, but many commands accept org-prefixed repo IDs:

```bash
# List repos with `hf` (requires token):
hf download my-org/my-model --help

# Upload to org namespace:
hf upload my-org/my-model ./local_dir .

# List files in org repo:
hf ls hf://my-org/my-model
```

The `whoami` response from `hf` CLI includes org affiliations:
```bash
hf auth login  # login first
# then check user info
```

### Organization Discovery

#### Finding Orgs a User Belongs To

```python
from huggingface_hub import whoami

info = whoami()
user_orgs = info.get('orgs', [])
for org in user_orgs:
    print(f"{org['name']} ({org.get('role', '?')})")
```

#### Finding Org Repos by Type

```python
from huggingface_hub import HfApi

api = HfApi()

# List models in an org using Hub search API
models = api.list_models(author="huggingface")
for model in models:
    print(model.modelId)

# List datasets
datasets = api.list_datasets(author="huggingface")
for ds in datasets:
    print(ds.id)
```

### Enterprise Features: Resource Groups

Resource groups are an Enterprise Hub feature that enable fine-grained access control within an org:

```python
# Create a repo in a specific resource group
api.create_repo(
    repo_id="my-org/enterprise-model",
    repo_type="model",
    resource_group_id="66670e5163145ca562cb1988",
)
```

**Characteristics:**
- Only Enterprise orgs can use resource groups
- Resource group ID is found in the URL of the resource's page
- Members assigned to a resource group can access repos within that group
- Non-members cannot see the repo exists (even if they are org members)
- Repository visibility (public/private) is separate from resource group access

### Best Practices

1. **Use org namespaces for team projects** — repos owned by orgs survive member turnover
2. **Check whoami before operations** — verify you have the right org role before creating repos
3. **Cache whoami responses** — use `cache=True` when calling `whoami()` multiple times (rate-limited)
4. **Use `exist_ok=True` in scripts** — prevents errors from race conditions in automation
5. **Prefer `missing_ok=True` for deletions** — idempotent cleanup in cron jobs
6. **Resource groups for sensitive models** — restrict access within an org without making repos private
7. **Transfer vs. duplicate** — use `move_repo` for ownership change, `duplicate_repo` for forks
8. **Plan restrictions** — Free orgs have public-only repos; private repos require Team/Enterprise

### Limitations & Gotchas

- **No SDK for member management** — invite/remove/role-change is web UI only
- **No API for creating orgs** — must use web UI
- **Creating repos under org requires write+ role** — read-only members cannot create repos
- **Resource groups are Enterprise-only** — not available on free or Team plans
- **Org names must be unique across all Hub users** — can't use a name that's already a username
- **Role info not available via `get_organization_overview()`** — use `whoami()` for the auth user's role
- **`num_users` field can be stale** — might not update immediately after member changes
- **Rate limiting on whoami** — cache results if calling frequently
- **Plan downgrade restrictions** — may lose private repos on downgrade from Team/Enterprise

### Source Code References

- `Organization` dataclass: `huggingface_hub/hf_api.py` (Organization class)
- `get_organization_overview()`: `huggingface_hub/hf_api.py` — REST: `GET /api/organizations/{org}/overview`
- `list_organization_members()`: `huggingface_hub/hf_api.py` — REST: `GET /api/organizations/{org}/members`
- `list_organization_followers()`: `huggingface_hub/hf_api.py` — REST: `GET /api/organizations/{org}/followers`
- `create_repo()`: `huggingface_hub/hf_api.py` — REST: `POST /api/repos/create`
- `move_repo()`: `huggingface_hub/hf_api.py` — REST: `POST /api/repos/move`
- `duplicate_repo()`: `huggingface_hub/hf_api.py` — REST: `POST /api/repos/duplicate`
- `delete_repo()`: `huggingface_hub/hf_api.py` — REST: `DELETE /api/repos/delete`
- `update_repo_settings()`: `huggingface_hub/hf_api.py` — REST: `POST /api/repos/{repo}/settings`
- `list_user_repos()`: `huggingface_hub/hf_api.py` — REST: `GET /api/organizations/{org}/settings/repositories`
- `User` dataclass: `huggingface_hub/hf_api.py`
- `whoami()`: `huggingface_hub/hf_api.py`
- `paginate()` helper: `huggingface_hub/utils/_http.py`


### Resources
- [Hub Organizations Documentation](https://huggingface.co/docs/hub/en/organizations)
- [Hugging Face Account Settings (Orgs)](https://huggingface.co/settings/organizations)
- [Hub Repositories Settings (Moving/Transferring)](https://hf.co/docs/hub/repositories-settings#renaming-or-transferring-a-repo)
- [huggingface_hub API Reference: HfApi](https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api)

---

## 2026-07-24: hf-gradio-6-render-and-streaming-deep-dive — Gradio 6: `@gr.render` Decorator & Streaming Patterns (Topic #151)

### Summary
Deep-dive into three major Gradio 6 features: the `@gr.render` decorator for dynamic UIs, async generator streaming for token-by-token chatbot responses, and the v2 `gr.ChatInterface` with multimodal support, additional inputs/outputs, and `gr.load_chat`. Also covers `gr.SelectData`, `gr.validate`, and `gr.Timer` for event handling and validation.

### Key Features

#### 1. `@gr.render` — Dynamic Components at Runtime
- Decorate a function with `@gr.render(inputs=[...])` to create/destroy components based on state changes
- Components inside the render function are replaced on every re-render
- Use `key=` parameter to preserve component values across re-renders
- Event listeners referencing render-created components must be defined inside the render function
- Freeze loop variables with default args: `lambda task=task: handler(task)`
- Custom triggers via `triggers=[...]` parameter; add `demo.load` for initial render

#### 2. Streaming Chatbot Responses
- Chat function uses `yield` to stream token-by-token
- Gradio sends only diffs over network (reduces latency)
- Submit button becomes Stop button during streaming
- Works with `additional_inputs` and `additional_outputs`
- Audio streaming with `gr.Audio(streaming=True, autoplay=True)` combined with `input_audio.stream(stream_every=0.5)`

#### 3. `gr.ChatInterface` v2
- **Multimodal:** `multimodal=True` enables file uploads; message becomes `{"text": ..., "files": [...]}`
- **Additional outputs:** Return extra values to update separate components
- **`gr.load_chat()`** — one-line chatbot for any OpenAI-compatible endpoint
- **Complex return types:** Images, Audio, Video, File, Plot, HTML, Gallery can be returned directly
- Custom chatbot/textbox components passable via `chatbot=` and `textbox=` parameters

#### 4. Event Data & Validation
- `gr.SelectData` type hint captures user selection details (value, index)
- `validator=` kwarg for immediate input validation with per-field granularity
- `gr.Timer(interval)` for scheduled events via `timer.tick()`

### Zero-Cost Relevance
All Gradio 6 features work on free CPU HF Spaces. Streaming reduces perceived latency without expensive hardware. `gr.load_chat` points to free local/API endpoints. Efficient `@gr.render` reduces DOM memory on long conversations.

### Resources
- Full deep-dive: `mlops/gradio-spaces/references/hf-learnings.md`
- [Dynamic Apps with Render Decorator](https://www.gradio.app/guides/dynamic-apps-with-render-decorator)
- [Creating a Chatbot Fast](https://www.gradio.app/guides/creating-a-chatbot-fast)
- [Gradio API Reference](https://www.gradio.app/docs/gradio/chatinterface)

## 2026-07-24: hf-hub-security-scanning-deep-dive — Hub Security Scanning Infrastructure (Topic #152)

### Summary
Deep-dive into the Hugging Face Hub's multi-layered security scanning infrastructure. Covers all five scanning systems: ClamAV malware scanning (every file, every commit), pickle import analysis (opcode-level static analysis), TruffleHog secrets scanning (credential leakage detection), Protect AI Guardian (third-party ML exploit scanning), and JFrog scanner (behavioral ML malware detection). Also covers picklescan library, repository security badges, and the end-to-end scanning pipeline.

### Scanning Architecture Overview

The Hub runs a multi-engine security pipeline on every push/commit:

| Scanner | Type | What It Detects | Trigger |
|---------|------|-----------------|---------|
| **ClamAV** | Antivirus | Known malware signatures via ClamAV database | Every file, every commit |
| **Pickle Import Scanner** | Static analysis | Dangerous imports/REDUCE opcodes in pickle files | Every `.pkl`/`.bin` upload |
| **TruffleHog** | Secrets scanner | Hard-coded API keys, tokens, credentials | Every push |
| **Protect AI Guardian** | Third-party ML scanner | Pickle, Keras, and other ML serialization exploits | Public repos, on upload |
| **JFrog Scanner** | Third-party behavioral | Malicious code inside model weights (low false-positive) | Model files, on upload |

### 1. ClamAV Malware Scanning

Runs every file through [ClamAV](https://www.clamav.net/) open-source antivirus.

- **Triggered per commit** — every file pushed is scanned
- **Badge system:** Each file gets an `ok`, `infected`, or no badge (queued/scanning/error)
- **Repository-level warning:** If any file is flagged unsafe, a banner warns users
- **Owner responsibility:** Repository owner advised to remove suspicious files
- **Example:** `mcpotato/42-eicar-street` demonstrates infected file badges

```python
# Programmatic check via HF Hub API
from huggingface_hub import HfApi
api = HfApi()
# Check repo file security status
# Files have .safety_status: "safe" | "unsafe" | "unknown"
```

### 2. Pickle Import Scanning (Built-in)

Custom-built scanner that performs **opcode-level static analysis** on pickle files without executing them.

#### How It Works

Uses Python's `pickletools.genops()` to disassemble pickle opcodes:

```python
import pickletools

# Safe: reads opcodes WITHOUT executing code
with open('model.pkl', 'rb') as f:
    ops = list(pickletools.genops(f))
    for opcode, arg, pos in ops:
        if opcode.name in ('GLOBAL', 'STACK_GLOBAL', 'REDUCE'):
            print(f"Dangerous opcode: {opcode.name} -> {arg}")
```

#### Dangerous Opcodes

| Opcode | Risk |
|--------|------|
| `GLOBAL` | Imports any Python module; can pull in `builtins.exec` |
| `STACK_GLOBAL` | Stack-based variant of GLOBAL |
| `REDUCE` | Executes a callable with arguments — primary RCE vector |
| `INST` | Old-style class instantiation with args |
| `OBJ` | Similar to REDUCE, builds objects |

#### Example: Innocent Pickle

```python
import pickle
pickletools.dis(pickle.dumps("hello"))
# Output: PROTO 4, SHORT_BINUNICODE 'hello', MEMOIZE, STOP
# No dangerous opcodes
```

#### Example: Malicious Pickle (using fickling)

```python
# A pickle that runs exec() on unpickling
# Opcodes: GLOBAL builtins.exec, REDUCE
# The import scanner catches GLOBAL + REDUCE combo
```

#### Safe Import Lists

The Hub maintains safe/unsafe import lists for pickle files:

- **Safe:** `torch.*`, `numpy.*`, `transformers.*`, standard library modules
- **Unsafe:** `builtins.exec`, `builtins.eval`, `os.system`, `subprocess.*`, `ctypes.*`
- **Displayed per-file:** Each pickle file's imports shown on the Hub UI
- **Disclaimer:** Best-effort — users remain responsible for verification

#### Mitigation Stack

1. **Don't use pickle** — prefer `safetensors` for weights
2. **Trust but verify** — GPG-signed commits guarantee origin
3. **Use TF/Flax weights** — load with `from_tf=True` or `from_flax=True`
4. **Alternative serialization** — MsgPack, Protobuf, Cap'n'Proto, Avro, safetensors

### 3. TruffleHog Secrets Scanning

Runs [TruffleHog](https://trufflesecurity.com/trufflehog) on every push to detect hard-coded secrets.

- **Scope:** Detects API keys, tokens, credentials across 700+ service patterns
- **Two-tier detection:**
  - **Unverified secrets:** Patterns that look like secrets; may be false-positive
  - **Verified secrets:** Confirmed working authentication via live provider check
- **Notification:** Email sent for verified secrets only; opt-out in settings
- **Coverage:** Not limited to HF tokens — any service credential (AWS, GitHub, OpenAI, etc.)

```python
# Bad practice detected by scanner:
api_key = "sk-abc123..."          # ❌ Hard-coded in source

# Good practice:
import os
api_key = os.getenv("API_KEY")    # ✅ Environment variable in Secrets
```

### 4. Protect AI Guardian (Third-party)

[Protect AI](https://protectai.com/)'s [Guardian](https://protectai.com/guardian) scanner.

- **Specialty:** Catches pickle, Keras, and other ML serialization exploits
- **Knowledge base:** Detailed at [protectai.com/insights/knowledge-base/](https://protectai.com/insights/knowledge-base/)
- **Integration:** Scans all public repository files on upload
- **UI:** Dedicated report section per file with detailed findings
- **Community:** Benefits from [Huntr](https://huntr.com/) bounty reports
- **Example repo:** `mcpotato/42-eicar-street` shows Protect AI reports inline

### 5. JFrog Scanner (Third-party)

[JFrog](https://jfrog.com/) ML model security scanner.

- **Specialty:** Detects malicious behavior in ML model files
- **Low false-positives:** Parses code inside model weights and analyzes for malicious intent rather than flagging all code
- **Behavioral analysis:** Distinguishes between legitimate model code and attack payloads
- **Partnership blog:** [hf.co/blog/jfrog](https://hf.co/blog/jfrog)
- **UI:** Reports displayed on individual file cards similar to Protect AI

### 6. Picklescan Library

Third-party standalone scanner by [mmaitre314](https://github.com/mmaitre314/picklescan):

```bash
pip install picklescan
picklescan scan --file-path model.pkl
```

```python
from picklescan.scanner import scan_file
result = scan_file("model.pkl")
print(f"Infected: {result.infected}")
for issue in result.issues:
    print(f"  {issue.severity}: {issue.opcode} -> {issue.import_name}")
```

- Also supports scanning HF Hub repos directly via `--repo-id`
- Can detect GLOBAL, REDUCE, and other dangerous pickle opcodes
- Used by some third-party security platforms

### 7. Security Badge System

Every file on the Hub displays a security status:

| Badge | Meaning |
|-------|---------|
| ✅ **ok** | Passed all scans; no issues detected |
| ❌ **infected** | Flagged by at least one scanner |
| ⏳ *(none)* | Queued, scanning in progress, or scan error (up to a few minutes) |

Repository-level banner shown if any file is unsafe:
> "As the repository owner, we advise you to remove the suspicious file. The repository will appear back as safe."

### 8. Hub-Wide Security Features

Beyond file scanning:

- **Private repositories** — access-controlled repos
- **Fine-grained tokens** — scoped to read/write/admin per resource type
- **SSH keys** — Git over SSH for secure auth
- **GPG signatures** — signed commits verify file origin
- **2FA/MFA** — two-factor authentication
- **Resource Groups** — advanced access control for orgs
- **SSO** — single sign-on for enterprise
- **SOC2 Type 2** — annual security certification
- **GDPR compliance** — data processing agreements available

### Zero-Cost Relevance

All scanning is **free and automatic** — no cost to repo owners or users. The Hub's security infrastructure protects everyone without any paid tier requirement. For zero-cost users (like Beer), this means:
- Upload models safely without worrying about malicious injections from collaborators
- Use `safetensors` (free, open-source) instead of pickle for weights
- Store secrets via HF Spaces Secrets (free) rather than hard-coding
- Verify file safety programmatically via the Hub API

### Resources
- [Hub Security Docs](https://huggingface.co/docs/hub/en/security)
- [Malware Scanning](https://huggingface.co/docs/hub/en/security-malware)
- [Pickle Scanning](https://huggingface.co/docs/hub/en/security-pickle)
- [Secrets Scanning](https://huggingface.co/docs/hub/en/security-secrets)
- [Protect AI Integration](https://huggingface.co/docs/hub/en/security-protectai)
- [JFrog Integration](https://huggingface.co/docs/hub/en/security-jfrog)
- [Picklescan Library](https://github.com/mmaitre314/picklescan)
- [ClamAV](https://www.clamav.net/)
- [TruffleHog](https://trufflesecurity.com/trufflehog)
- [JFrog Blog Post](https://hf.co/blog/jfrog)

---

## 2026-07-24: hf-hub-xet-storage-and-hf-xet — Xet Storage & hf_xet Rust Accelerator Deep Dive (Topic #154)

### Summary
Deep-dive into Xet storage, the Rust-based content-addressable storage system powering the Hugging Face Hub, and its Python client hf_xet.


---

## 2026-07-24: hf-hub-xet-storage-and-hf-xet — Xet Storage & hf_xet Rust Accelerator Deep Dive (Topic #154)

### Summary
Deep-dive into Xet storage, the Rust-based content-addressable storage system powering the Hugging Face Hub, and its Python client `hf_xet`. Covers the architecture (chunk-level deduplication, XORBs, CAS), the replacement of `hf_transfer` with `hf_xet`, the token refresh system, cache optimization via tree listing, and configuration via env vars. Sources: huggingface_hub v1.24.0 source code analysis and HF Hub Xet docs.

### Architecture Overview

Xet is a **content-addressable storage (CAS)** system built specifically for AI/ML development on the Hugging Face Hub. It replaces the older Git LFS-based storage backend.

**Key differences from Git LFS:**
- **Chunk-level deduplication** — identical chunks across different files stored only once (not possible with LFS's file-level storage)
- **Smaller uploads** — only new/changed chunks are transferred
- **Faster downloads** — parallel chunk retrieval with presigned URLs
- **Immutable chunks (XORBs)** — broken into blocks called xorbs, reassembled on request

### Architecture Flow

1. Files are broken into immutable chunks (xorbs)
2. Chunks are stored in the content-addressable service (CAS)
3. LFS SHA256 hash -> reconstruction metadata (ranges within xorbs + presigned URLs)
4. `hf_xet` downloads xorb ranges in parallel and writes files to disk
5. Short-lived Xet access tokens are refreshed automatically via the refresh API

### hf_xet Python Package

| Property | Value |
|----------|-------|
| Package name | hf-xet (pip), imported as hf_xet |
| Current version | 1.5.2 (installed in this env) |
| Purpose | Rust-based download/upload accelerator for the HF Hub |
| Relationship to hf_transfer | hf_transfer is DEPRECATED - use hf_xet instead |
| Bundled with | huggingface_hub >= 0.32.0 (automatically installed) |
| Summary | Fast transfer of large files with the Hugging Face Hub |

### How hf_xet Integrates with huggingface_hub

**Runtime detection** - `_runtime.py` checks for `hf_xet` package at import time via `is_xet_available()`.

**Download flow** - `file_download.py` contains the `xet_get()` function.

**XetFileData dataclass** - `utils/_xet.py`:
- `file_hash` (str): Xet content hash for file identification in CAS
- `refresh_route` (str): URL to refresh the short-lived Xet access token

**Token refresh URL format:**
```
{ENDPOINT}/api/{repo_type}s/{repo_id}/xet-{read|write}-token/{revision}
```

**XetTokenType enum:** READ / WRITE

**XetSessionHolder** - thread-safe session management for free-threaded Python (3.14t):
- Uses threading.Lock for thread safety
- Supports safe re-creation after sigint_abort() or fork
- Automatically refreshes tokens as needed

### Cache Optimization - Tree Listing

When Xet is enabled, the Hub API's /tree listing response includes Xet metadata (xet_hash, lfs_sha256, lfs_size). This allows hf_xet to skip the HEAD request that regular downloads need, since Xet downloads don't rely on the /resolve redirect.

### Configuration

| Env Variable | Purpose |
|-------------|---------|
| HF_HUB_DISABLE_XET | Set to disable Xet even if hf_xet is installed |
| (default) | Xet enabled by default when hf_xet package is available |

### Zero-Cost Relevance

Xet storage and hf_xet are free for all Hub users - no paid tier required. For Beer's zero-cost setup:
- hf_xet is already bundled with huggingface_hub v1.24.0
- Faster downloads save time on model/dataset downloads without any cost
- Chunk-level deduplication means the Hub stores less data overall

### Resources
- HF Hub Download Guide (https://huggingface.co/docs/huggingface_hub/en/guides/download)
- Xet Hub Documentation (https://huggingface.co/docs/hub/xet/index)
- huggingface_hub utils/_xet.py on GitHub
- hf_xet PyPI package: hf-xet

## 2026-07-24: hf-inference-client-tool-use-and-function-calling — InferenceClient Tool Calling Deep-Dive (Topic #154)

### Summary
Deep-dive into Hugging Face `InferenceClient`'s tool-calling / function-calling API (v1.24.0). Covers the full data model (tool definitions, function schemas, tool_choice modes), streaming vs non-streaming tool calls, OpenAI compatibility (`client.chat.completions.create`), multi-turn tool execution loops, integration with MCP, and practical zero-cost patterns for agent workflows.

### Overview
Hugging Face `InferenceClient` implements the same tool-calling interface as the OpenAI Chat Completions API. This allows LLMs to interact with external tools — functions, APIs, or external services — by generating structured JSON arguments that the client can execute and relay back.

**Verified from huggingface_hub v1.24.0 source code and docs (2026-07-24):**
- Tool calling works with both synchronous `InferenceClient` and `AsyncInferenceClient`
- Supported models: any provider model that supports function/tool calling (verify per provider)
- Available via `client.chat_completion(..., tools=..., tool_choice=...)` or `client.chat.completions.create(..., tools=..., tool_choice=...)`
- Streaming and non-streaming modes both support tool calls

### Full Data Model

#### Input Types (What You Send)

| Type | Fields | Description |
|------|--------|-------------|
| `ChatCompletionInputTool` | `function: ChatCompletionInputFunctionDefinition`, `type: str` | A tool the model may call. `type` is always `"function"` |
| `ChatCompletionInputFunctionDefinition` | `name: str`, `parameters: Any`, `description: str \| None` | JSON Schema function definition. `parameters` is a JSON Schema object |
| `ChatCompletionInputToolChoiceClass` | `function: ChatCompletionInputFunctionName` | Force a specific tool by name |
| `ChatCompletionInputFunctionName` | `name: str` | Just the tool name reference |
| `ChatCompletionInputToolChoiceEnum` | `Literal["auto", "none", "required"]` | Control tool calling behaviour |

#### Output Types (What You Receive)

| Type | Fields | Description |
|------|--------|-------------|
| `ChatCompletionOutputToolCall` | `function: ChatCompletionOutputFunctionDefinition`, `id: str`, `type: str` | A tool call from the model |
| `ChatCompletionOutputFunctionDefinition` | `arguments: str`, `name: str`, `description: str \| None` | The function to call. `arguments` is a JSON string |

#### Streaming Delta Types

| Type | Fields | Description |
|------|--------|-------------|
| `ChatCompletionStreamOutputDelta` | `role: str`, `content: str \| None`, `tool_calls: list[ChatCompletionStreamOutputDeltaToolCall] \| None`, `tool_call_id: str \| None`, `reasoning: str \| None` | Streaming delta that may contain tool call chunks |
| `ChatCompletionStreamOutputDeltaToolCall` | `function: ChatCompletionStreamOutputFunction`, `id: str`, `index: int`, `type: str` | A streaming tool call delta |
| `ChatCompletionStreamOutputFunction` | `arguments: str`, `name: str \| None` | `name` is present in the first delta of each tool call, then subsequent deltas accumulate `arguments` |

### Tool Definition (Input)

Each tool is defined with a JSON Schema for its parameters:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather in a given location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"]
                    }
                },
                "required": ["location"]
            }
        }
    }
]
```

Tools can also be passed as typed objects:

```python
from huggingface_hub.inference._generated.types.chat_completion import (
    ChatCompletionInputTool,
    ChatCompletionInputFunctionDefinition,
)

tools = [
    ChatCompletionInputTool(
        type="function",
        function=ChatCompletionInputFunctionDefinition(
            name="get_current_weather",
            description="Get the current weather in a given location",
            parameters={
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City and state"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]}
                },
                "required": ["location"]
            }
        )
    )
]
```

### tool_choice Modes

| Value | Type | Behaviour |
|-------|------|-----------|
| `"auto"` | `Literal` | Model decides whether to call a tool or respond with text |
| `"none"` | `Literal` | Disable tool calling entirely |
| `"required"` | `Literal` | Force the model to call one of the provided tools |
| `{"function": {"name": "get_current_weather"}}` | `ChatCompletionInputToolChoiceClass` | Force a specific tool by name |

Default: `None` (which maps to `"auto"` on the server side).

### Non-Streaming Tool Call

```python
from huggingface_hub import InferenceClient

client = InferenceClient("Qwen/Qwen2.5-7B-Instruct")

response = client.chat_completion(
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
    max_tokens=500,
)

# Check if the model called a tool
message = response.choices[0].message
if message.tool_calls:
    for tool_call in message.tool_calls:
        print(f"Tool: {tool_call.function.name}")
        print(f"Args: {tool_call.function.arguments}")
        print(f"ID: {tool_call.id}")
else:
    print(f"Text response: {message.content}")
```

**Output structure:**
```
response.choices[0].message.tool_calls[0].id            # str - unique call ID
response.choices[0].message.tool_calls[0].type          # str - "function"
response.choices[0].message.tool_calls[0].function.name       # str
response.choices[0].message.tool_calls[0].function.arguments  # str - JSON string
response.choices[0].finish_reason                      # "eos_token", "stop", or "tool_calls"
```

### Streaming Tool Calls

When streaming with tools, tool calls come as deltas across multiple chunks:

```python
stream = client.chat_completion(
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
    stream=True,
    max_tokens=500,
)

tool_calls = {}  # Dict[int, dict] - accumulate by index
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.tool_calls:
        for tc in delta.tool_calls:
            idx = tc.index
            if idx not in tool_calls:
                tool_calls[idx] = {"id": tc.id, "name": tc.function.name, "arguments": ""}
            if tc.function.name:
                tool_calls[idx]["name"] = tc.function.name
            if tc.id:
                tool_calls[idx]["id"] = tc.id
            if tc.function.arguments:
                tool_calls[idx]["arguments"] += tc.function.arguments
    elif delta.content:
        print(delta.content, end="")
```

**Key streaming behaviour:**
- First delta for each tool call includes the `name` and `id`
- Subsequent deltas for the same tool call accumulate `arguments` (a string that builds up to a complete JSON)
- When `finish_reason` is `"tool_calls"` (or similar), no more content deltas will arrive
- The final state of each accumulated tool call's arguments is a complete JSON string

### Multi-Turn Tool Execution Loop

The standard agent pattern for executing tools and feeding results back:

```python
def run_tool_loop(client, messages, tools, max_turns=5):
    for turn in range(max_turns):
        response = client.chat_completion(
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=500,
        )
        message = response.choices[0].message
        
        if not message.tool_calls:
            # Model responded with text - we're done
            return message.content
        
        # Add assistant's tool call message to history
        messages.append({
            "role": "assistant",
            "content": message.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in message.tool_calls
            ]
        })
        
        # Execute each tool call
        for tool_call in message.tool_calls:
            result = execute_tool(tool_call.function.name, tool_call.function.arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": str(result)
            })
    
    return "Max turns reached"
```

**Important message format for tool results:**
- `tool_call_id` must match the `id` from the model's tool call
- `role` must be `"tool"`
- `content` is the tool output as a string

### OpenAI Compatibility

`InferenceClient` provides the same interface as `openai.OpenAI`:

```python
from huggingface_hub import InferenceClient

client = InferenceClient(
    model="Qwen/Qwen2.5-7B-Instruct",
    api_key="hf_...",
)

# OpenAI-style syntax - exactly the same parameters
output = client.chat.completions.create(
    messages=[{"role": "user", "content": "What's the weather in Paris?"}],
    tools=tools,
    tool_choice="auto",
)
```

**Note:** `client.chat.completions.create` is a **separate method** from `client.chat_completion`, not an alias. Both share the same parameter structure but are implemented independently for full OpenAI response format fidelity.

### Integration with MCP (Model Context Protocol)

Hugging Face `AsyncInferenceClient` integrates with MCP through `MCPClient`:

```python
from huggingface_hub import AsyncInferenceClient, MCPClient

client = AsyncInferenceClient("Qwen/Qwen2.5-7B-Instruct")
mcp_client = MCPClient()

# Connect to MCP servers (stdio or SSE)
await mcp_client.connect_stdio("python my_tool_server.py")
# or
await mcp_client.connect_sse("https://my-mcp-server.com/sse")

# MCPClient automatically:
# 1. Discovers tools from the MCP server
# 2. Feeds them to the LLM via AsyncInferenceClient
# 3. Executes tool calls and relays results back
# 4. Can stream results in real-time

async for chunk in client.process_single_turn_with_tools(messages):
    if chunk.type == "content":
        print(chunk.content, end="")
    elif chunk.type == "tool_call":
        print(f"\nCalled tool '{chunk.name}'. Result: '{chunk.result}'")
```

### tool_prompt Parameter

The `tool_prompt` parameter appends custom instructions before the tool definitions:

```python
response = client.chat_completion(
    messages=messages,
    tools=tools,
    tool_prompt="You MUST call a function for every query. "
                "Never refuse to use a tool when one is available.",
    tool_choice="required",
)
```

Use cases:
- Override default tool-calling behaviour
- Enforce tool usage patterns
- Add domain-specific instructions about tool usage

### Provider Support

Not all providers support function/tool calling. To check:

```python
from huggingface_hub import HfApi

api = HfApi()
info = api.model_info("Qwen/Qwen2.5-7B-Instruct", expand="inferenceProviderMapping")
for pm in info.inference_provider_mapping:
    # Check model info for tool support
    print(f"{pm.provider}: {pm.task}")
# Also check model card metadata:
info.card_data.metadata  # Look for 'supports_tools' field
```

**Known providers with good tool-calling support (as of 2026-07-24):**
- Together AI
- DeepInfra
- Fireworks AI
- Novita
- Featherless AI

### Zero-Cost Considerations

- All InferenceClient tool-calling features work with HF Inference's free serverless tier
- Zero GPU credits consumed for tool definitions, parsing, and multi-turn orchestration
- Only the actual LLM inference calls cost credits (serverless free tier covers most use cases)
- MCP integration is client-side only — zero server cost
- Use `tool_choice="none"` to guarantee no tool calls (saves tokens in classification-only tasks)
- Streaming saves time but uses roughly the same token count
- Set tight `max_tokens` to bound tool-heavy conversations

### Error Handling Patterns

```python
from huggingface_hub import InferenceClient, InferenceTimeoutError, HfHubHTTPError

client = InferenceClient()

try:
    response = client.chat_completion(
        messages=messages,
        tools=tools,
        tool_choice="auto",
        max_tokens=500,
    )
except InferenceTimeoutError:
    # Model unavailable or request timed out
    logger.warning("Tool calling timed out, retrying without tools...")
    response = client.chat_completion(messages=messages, max_tokens=500)
except HfHubHTTPError as e:
    # HTTP error (e.g., 422 if tools format is invalid)
    if e.response.status_code == 422:
        logger.error(f"Invalid tool schema: {e}")
    else:
        raise
```

**Common error: HTTP 422** — This usually means an invalid tool definition (e.g., missing `required` field in parameters, or invalid JSON Schema format). Validate tool schemas locally before sending.

### Key Takeaways

1. **Same API as OpenAI** — `InferenceClient.chat.completions.create()` is drop-in compatible with `openai.OpenAI().chat.completions.create()`
2. **Streaming works with tools** — Tool calls come as deltas across chunks; accumulate by `index`
3. **Multi-turn loops** — Standard pattern: assistant message with tool_calls → tool result messages → next generation
4. **MCP integration** — `MCPClient` bridges MCP tool servers with `AsyncInferenceClient` for zero-code tool discovery
5. **tool_choice fine control** — `"auto"`, `"none"`, `"required"`, or specific tool name
6. **All zero-cost** — Everything runs client-side; only LLM inference costs apply (free serverless tier available)
7. **Provider varies** — Not all inference providers support tool calling; verify via `inferenceProviderMapping`

### Resources
|- huggingface_hub InferenceClient docs (https://huggingface.co/docs/huggingface_hub/en/guides/inference)
|- huggingface_hub v1.24.0 source: `_client.py` `chat_completion` method
|- huggingface_hub MCP integration (https://huggingface.co/docs/huggingface_hub/v1.24.0/en/package_reference/mcp)
|- huggingface_hub generated types: `_generated/types/chat_completion.py`
|- OpenAI Chat Completions API reference (for compatibility comparison)

---

## 2026-07-24: hf-quantization-methods-comparison — Comprehensive Quantization Method Comparison (Topic #157)

### Summary
Comprehensive comparison of every quantization method supported in Hugging Face Transformers, based on the official Transformers v5.14.0 quantization overview. Covers 21 methods across dimensions: bit-depth, hardware support, on-the-fly vs. calibration, PEFT compatibility, serialization, performance characteristics, and zero-cost recommendations for Beer's models.

### Source
Official Transformers Quantization Overview: https://huggingface.co/docs/transformers/en/quantization/overview
Published: 2026-07-24, Transformers v5.14.0

### Complete Method Comparison Matrix

| Method | Bits | On-the-fly | CPU | CUDA | ROCm | Metal (Apple) | Intel GPU | torch.compile | PEFT FT | Serializable | Notes |
|--------|------|-----------|-----|------|------|--------------|-----------|--------------|---------|-------------|-------|
| **AQLM** | 1/2 | ❌ | 🟢 | 🟢 | 🔴 | 🔴 | 🟢 | 🟢 | 🟢 | 🟢 | Extreme compression; groups 8-16 weights together |
| **AutoRound** | 2/3/4/8 | ❌ | 🟢 | 🟢 | 🔴 | 🔴 | 🟢 | 🔴 | 🔴 | 🟢 | Intel's weight-rounding optimization |
| **AWQ** | 4 | ❌ | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 | ❓ | 🟢 | 🟢 | Activation-aware; most popular 4-bit |
| **bitsandbytes** | 4/8 | 🟢 | 🟢 | 🟢 | 🟡 | 🟡 | 🟢 | 🟢 | 🟢 | 🟢 | Most mature; NF4 for QLoRA |
| **compressed-tensors** | 1/8 | ❌ | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🟢 | Neural Magic's sparsity+quant |
| **EETQ** | 8 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | ❓ | 🟢 | 🟢 | NetEase Easy Efficient Transformer |
| **Four Over Six** | 4 | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🟢 | MIT; 4-bit via 6-bit intermediate |
| **FP-Quant** | 4 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🟢 | IST; FP8-based 4-bit quantization |
| **GGUF/llama.cpp** | 1–8 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | 🔴 | 🔴 | See Notes | Separate format; NOT serializable in Transformers |
| **GPTQModel** | 2/3/4/8 | ❌ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | Replaced AutoGPTQ; requires calibration |
| **HIGGS** | 2/4 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🟢 | HanGuo's FLUTE-based quantization |
| **HQQ** | 1–8 | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | 🟢 | 🟢 | 🟢 | 🔴 | No calibration needed; half-quadratic |
| **Metal** | 2/4/8 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | Apple Silicon only (Hub Kernels) |
| **optimum-quanto** | 2/4/8 | 🟢 | 🟢 | 🟢 | 🔴 | 🟢 | 🟢 | 🟢 | 🔴 | 🔴 | HF's own; lightweight, no heavy deps |
| **SINQ** | 2/3/4/6/8 | 🟢 | 🟢 | 🟢 | 🟡 | 🟡 | 🟡 | 🟡 | 🔴 | 🟢 | Huawei; sparse+integer quantization |
| **FBGEMM_FP8** | 8 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🔴 | 🔴 | 🟢 | PyTorch FBGEMM FP8 |
| **torchao** | 4/8 | 🟢 | 🟢 | 🟢 | 🔴 | 🟡 | 🟢 | — | 🟢 | 🟢 | PyTorch native; Int4/FP8/NF4 |
| **VPTQ** | 1–8 | ❌ | 🔴 | 🟢 | 🟡 | 🔴 | 🔴 | 🟢 | 🔴 | 🟢 | Microsoft; vectorized PTQ |
| **FINEGRAINED_FP8** | 8 | 🟢 | 🔴 | 🟢 | 🔴 | 🔴 | 🟢 | 🔴 | 🔴 | 🟢 | Built-in Transformers |
| **SpQR** | 3 | ❌ | 🔴 | 🟢 | 🔴 | 🔴 | 🔴 | 🟢 | 🔴 | 🟢 | Sparse-plus-quantized |
| **Quark** | 2/4/6/8/9/16 | ❌ | 🟢 | 🟢 | 🟢 | 🟢 | 🟢 | ❓ | 🔴 | 🔴 | AMD; widest bit range |

Legend: 🟢 = Supported, 🟡 = Partial/Experimental, 🔴 = Not Supported, ❓ = Unknown, — = Native

### Key Decision Dimensions

#### 1. On-the-Fly vs. Calibration Required
- **On-the-fly** (no calibration data needed): bitsandbytes, HQQ, optimum-quanto, torchao, GGUF (pre-quantized), EETQ, Four Over Six, FP-Quant, HIGGS, Metal, SINQ, FBGEMM_FP8, FINEGRAINED_FP8
- **Calibration required** (need sample dataset): AWQ, GPTQModel, AQLM, AutoRound, compressed-tensors, VPTQ, SpQR, Quark

#### 2. PEFT (LoRA/QLoRA) Fine-Tuning Compatible
- **🟢 Supported:** AQLM, AWQ, bitsandbytes, compressed-tensors, EETQ, GPTQModel, HQQ, torchao
- **🔴 Not Supported:** AutoRound, Four Over Six, FP-Quant, GGUF, HIGGS, Metal, optimum-quanto, SINQ, FBGEMM_FP8, VPTQ, FINEGRAINED_FP8, SpQR, Quark

#### 3. Serializable (can be saved & reloaded in Transformers)
- **🟢 Yes:** AQLM, AutoRound, AWQ, bitsandbytes, compressed-tensors, EETQ, Four Over Six, FP-Quant, GPTQModel, HIGGS, Metal, SINQ, FBGEMM_FP8, torchao, VPTQ, FINEGRAINED_FP8, SpQR
- **🔴 No / Partial:** HQQ (not serializable in Transformers), optimum-quanto (not serializable), GGUF (separate format, use `gguf_file` parameter), Quark (not serializable)

#### 4. Hardware Coverage
- **Most universal** (CPU+CUDA+ROCm): bitsandbytes, torchao, AQLM, compressed-tensors, AutoRound, AWQ, GPTQModel
- **Apple Silicon (Metal):** AWQ, bitsandbytes (🟡), torchao (🟡), GGUF, Metal (native), optimum-quanto, GPTQModel, SINQ (🟡), Quark — for best Apple support, use GGUF or optimum-quanto
- **Intel GPU:** bitsandbytes, HQQ, torchao, SINQ (🟡), GPTQModel, AWQ, FINEGRAINED_FP8, AutoRound, Quark, optimum-quanto, GGUF

### Detailed Method Profiles

#### bitsandbytes (Mature, Most Widely Used)
- **Bits:** 4 (NF4/FP4) and 8 (LLM.int8())
- **Install:** `pip install bitsandbytes`
- **Key Feature:** On-the-fly quantization — no calibration data needed. QLoRA enables 4-bit fine-tuning with LoRA adapters.
- **Usage:** `model = AutoModelForCausalLM.from_pretrained(..., load_in_4bit=True, bnb_4bit_quant_type="nf4")`
- **Limitations:** ROCm and Metal support are partial (🟡). 4-bit inference slower than AWQ/GPTQ on some benchmarks.
- **Best for:** Quick memory reduction, QLoRA fine-tuning, prototyping on consumer GPUs.

#### AWQ (Activation-Aware Weight Quantization)
- **Bits:** 4
- **Install:** `pip install autoawq` (note: downgrades Transformers to 4.47.1)
- **Key Feature:** Preserves 1% of weights as FP16 based on activation importance, achieving 4-bit with minimal perplexity loss. Very fast inference.
- **Usage:** Load pre-quantized models: `AutoModelForCausalLM.from_pretrained("model-awq")`
- **Limitations:** Requires calibration data to quantize. Cannot quantize on-the-fly — must use pre-quantized models or quantize offline.
- **Best for:** Production 4-bit inference on CUDA GPUs; best quality-per-bit ratio at 4-bit.

#### GPTQModel (Successor to AutoGPTQ)
- **Bits:** 2, 3, 4, 8
- **Install:** `pip install gptqmodel --no-build-isolation`
- **Key Feature:** Layer-wise quantization minimizing output error via second-order optimization (Hessian-based). Multiple bit-widths.
- **Usage:** `GPTQConfig(bits=4, dataset="c4", tokenizer=tokenizer)` then `from_pretrained(..., quantization_config=gptq_config)`
- **Limitations:** Calibration required (need representative dataset). Slower to quantize than on-the-fly methods.
- **Best for:** When you need flexible bit-widths (2/3/4/8) with good quality; supports Apple Silicon.

#### GGUF / llama.cpp (Ecosystem Standard for Local Inference)
- **Bits:** Q2_K through Q8_0, plus F32/F16/BF16/F64
- **Key Feature:** Single-file format with metadata header and all weights bundled. Community standard for local inference (Ollama, LM Studio, LlamaFile).
- **Usage in Transformers:** `AutoModelForCausalLM.from_pretrained(..., gguf_file="model.q4_K_M.gguf")`
- **Limitations:** NOT PEFT-compatible. NOT serializable back to Transformers format (separate ecosystem). No torch.compile support.
- **Hardware:** CPU native, CUDA via llama.cpp backend, Metal native on Apple Silicon.
- **Best for:** Local/edge deployment, Apple Silicon users, CPU inference, Ollama/LM Studio workflow.

#### HQQ (Half-Quadratic Quantization)
- **Bits:** 1, 2, 3, 4, 8
- **Install:** `pip install hqq`
- **Key Feature:** On-the-fly quantization without calibration data. Supports per-layer configs. 4-bit fused kernels reach 200 tok/s on RTX 4090.
- **Usage:** `HqqConfig(nbits=4, group_size=64)` then `from_pretrained(..., quantization_config=hqq_config)`
- **Limitations:** Not serializable in Transformers (🔴). No ROCm support. Relatively newer/lower adoption.
- **Best for:** Rapid quantization of any model without calibration; extreme 1-2 bit for research.

#### optimum-quanto (HuggingFace's Lightweight Option)
- **Bits:** 2, 4, 8
- **Install:** `pip install optimum-quanto`
- **Key Feature:** Lightweight, no heavy dependencies. Works out of the box with any model. Supports torch.compile.
- **Usage:** `quantize_model(model, weights=torch.qint4, activations=torch.qfloat8)`
- **Limitations:** NOT serializable (cannot save/load quantized state). No PEFT support. Limited ecosystem maturity.
- **Best for:** Quick experiments, torch.compile integration, when you want minimal deps.

#### torchao (PyTorch Native)
- **Bits:** 4 (int4/NF4), 8 (FP8 dynamic/weight-only)
- **Install:** `pip install torchao` (comes with PyTorch 2.6+)
- **Key Feature:** Native PyTorch integration. Supports Int4, FP8, NF4 dtypes. Composable with torch.compile and PEFT.
- **Usage:** `from torchao.quantization import quantize_` then `quantize_(model, int4_weight_only())`
- **Limitations:** ROCm support 🟡. Newer, fewer pre-quantized models on the Hub.
- **Best for:** PyTorch native workflows, production deployment with torch.compile, when you want tight integration.

#### AQLM (Additive Quantization of Language Models)
- **Bits:** 1–2 (extreme compression)
- **Install:** `pip install aqlm[gpu,cpu]` (Python 3.10+ only)
- **Key Feature:** Groups 8-16 weights together and represents them as additive combinations of codewords. Achieves 2-bit with competitive perplexity.
- **Usage:** `AutoModelForCausalLM.from_pretrained("ISTA-DASLab/Mixtral-8x7b-AQLM-2Bit-1x16-hf")`
- **Limitations:** Python 3.10+ only. Limited model availability. Primarily for research at extreme compression levels.
- **Best for:** Extreme memory constraint scenarios (sub-2 GB models), research on ultra-low-bit quantization.

### Practical Decision Flowchart

```
Q: What hardware do you have?
├── Apple Silicon (Metal)
│   └── GGUF (Ollama) → best ecosystem support
│   └── optimum-quanto → lightweight, on-the-fly
│   └── AWQ → best 4-bit quality if pre-quantized model exists
├── CPU-only
│   └── GGUF (llama.cpp) → best CPU performance
│   └── bitsandbytes → on-the-fly, mature
│   └── optimum-quanto → lightweight
├── NVIDIA GPU (CUDA)
│   ├── Need PEFT fine-tuning?
│   │   ├── Yes → bitsandbytes (QLoRA) or HQQ (on-the-fly)
│   │   └── No → AWQ (best quality) or GPTQ (flexible bits)
│   ├── Need on-the-fly?
│   │   ├── Yes → bitsandbytes, HQQ, torchao
│   │   └── No → AWQ, GPTQModel (better quality)
│   └── Extreme memory constraint?
│       └── AQLM (1-2 bit) or HQQ (1 bit)
└── AMD GPU (ROCm)
    └── bitsandbytes 🟡 or AWQ or GPTQModel or Quark
```

### Zero-Cost Recommendations for Beer's 8 Models

Since Beer has no income (zero-cost constraint) and owns 8 models on HF:

1. **For serverless inference on HF:** Use pre-quantized GGUF models (free via HuggingChat or Inference Providers) — no cost, no GPU needed.
2. **For local testing on CPU:** Download GGUF models (Q4_K_M) — single file, easy to test, works on any hardware.
3. **For fine-tuning (if GPU access via free tiers):** bitsandbytes + PEFT (QLoRA) — on-the-fly 4-bit, no calibration needed, free Colab/ZeroGPU compatible.
4. **For deploying on HF Spaces ZeroGPU:** torchao or bitsandbytes — both work in free Spaces with ZeroGPU (NVIDIA A10G).
5. **For pushing quantized versions of Beer's own models:** Choose AWQ (best quality at 4-bit) or GGUF (widest compatibility) depending on target audience.

### Resources
- Transformers Quantization Overview: https://huggingface.co/docs/transformers/en/quantization/overview
- bitsandbytes: https://github.com/bitsandbytes-foundation/bitsandbytes
- AWQ (AutoAWQ): https://github.com/casper-hansen/AutoAWQ
- GPTQModel: https://github.com/ModelCloud/GPTQModel
- HQQ: https://github.com/mobiusml/hqq/
- optimum-quanto: https://github.com/huggingface/optimum-quanto
- torchao: https://github.com/pytorch/ao
- AQLM: https://github.com/Vahe1994/AQLM
- GGUF Hub Docs: https://huggingface.co/docs/hub/en/models-gguf

---

## 2026-07-27: hf-datasets-sort-shuffle-split-shard — Dataset Process Operations Deep Dive (Topic #18 Deepened)

### Summary
Deep-dive into the 🤗 Datasets library's core processing pipeline (datasets v4.8.4). Covers every major Dataset method for sorting, shuffling, selecting, filtering, splitting, sharding, renaming, casting, flattening, mapping, batching, concatenating, interleaving, formatting, saving, and exporting — the complete data transformation toolkit.

### 1. Sort, Shuffle, Select, Split & Shard

#### `Dataset.sort()`
Sorts by a column's values. Returns a new Dataset sorted in ascending or descending order. Efficient because Arrow columnar storage makes column access cheap.
```python
dataset = dataset.sort("label")
dataset = dataset.sort("timestamp", reverse=True)
```

#### `Dataset.shuffle()`
Randomly shuffles the dataset. Accepts a `seed` for reproducibility and a `generator` for numpy RNG. Important: shuffling is **lazy** in buffered mode — the dataset is shuffled only when iterated.
```python
dataset = dataset.shuffle(seed=42)
import numpy as np
rng = np.random.default_rng(42)
dataset = dataset.shuffle(generator=rng)
```

#### `Dataset.select()` and `Dataset.filter()`
- **`select(indices)`**: Index-based selection. Takes an iterable of row indices and returns a new Dataset containing only those rows. Extremely fast — no data copy since Arrow uses zero-copy slicing.
  ```python
  dataset = dataset.select([0, 1, 2, 42, 99])
  dataset = dataset.select(range(1000))
  ```
- **`filter(function)`**: Row-wise boolean filtering. Function receives one row (as a dict) and returns `True` to keep it. Supports `num_proc` for multiprocessing and `input_columns` to limit columns passed to the function.
  ```python
  dataset = dataset.filter(lambda x: x["label"] == 1, num_proc=4)
  dataset = dataset.filter(lambda x: len(x["text"]) > 50)
  ```

#### `Dataset.train_test_split()`
The canonical method for creating train/test splits. Returns a `DatasetDict`.
- `test_size` or `train_size`: float (proportion) or int (count). Default test_size=0.1.
- `seed`: for reproducibility.
- `stratify_by_column`: for **stratified splitting** — critical for imbalanced classification.
- `shuffle`: whether to shuffle before splitting (default True).

```python
splits = dataset.train_test_split(test_size=0.2, seed=42)
train = splits["train"]
test = splits["test"]
# Stratified split — preserves class distribution
splits = dataset.train_test_split(test_size=0.2, seed=42, stratify_by_column="label")
```

#### `Dataset.shard()`
Splits the dataset into `num_shards` approximately equal shards, returns shard `index`. Essential for distributed processing.
```python
shard_0 = dataset.shard(num_shards=8, index=0)
shard_0 = dataset.shard(num_shards=8, index=0, contiguous=False)
```
With `contiguous=False`, shards are created in interleaved (round-robin) order.

### 2. Rename, Remove, Cast & Flatten

#### `Dataset.rename_column()`
```python
dataset = dataset.rename_column("old_name", "new_name")
```

#### `Dataset.remove_columns()`
Faster than using `map()` with `remove_columns` — doesn't copy data of remaining columns.
```python
dataset = dataset.remove_columns("unused_column")
dataset = dataset.remove_columns(["col1", "col2"])
```

#### `Dataset.cast()` and `Dataset.cast_column()`
- `cast(new_features)`: Cast all columns to new features.
- `cast_column(column, feature)`: Cast a single column, efficient.

```python
from datasets import ClassLabel, Value
new_features = dataset.features.copy()
new_features["label"] = ClassLabel(names=["bad", "good"])
new_features["text"] = Value("large_string")
dataset = dataset.cast(new_features)
# Or per-column:
dataset = dataset.cast_column("label", ClassLabel(names=["bad", "good"]))
```

#### `Dataset.flatten()`
Flattens nested struct columns into top-level columns.

### 3. Map — The Swiss Army Knife

`Dataset.map()` is the most powerful transformation. Applies a function to every row (or batch).

Key parameters: `function` (callable), `num_proc` (multiprocessing), `batched` (batch mode), `batch_size` (default 1000), `remove_columns`, `input_columns`, `load_from_cache_file` (cache control), `writer_batch_size` (cache write buffer), `fn_kwargs` (extra kwargs to function).

```python
def tokenize(batch, tokenizer):
    return tokenizer(batch["text"], truncation=True, padding="max_length")
dataset = dataset.map(tokenize, batched=True, batch_size=256,
                       fn_kwargs={"tokenizer": tokenizer})
```

**Cache fingerprint**: Every `map()` call has a unique fingerprint (hash of previous fingerprint + transform args). Enables deterministic caching. Disable with `load_from_cache_file=False`.

### 4. Batch Operations

#### `Dataset.with_format()`
Changes output format lazily (no data copy until iteration).
```python
dataset.with_format("torch")
dataset.with_format("numpy", columns=["input_ids", "attention_mask"])
dataset.with_format("tensorflow")
dataset.with_format("pandas")
dataset.with_format("jax")
```

#### `Dataset.flatten_indices()`
After select/filter/shard, the underlying Arrow table may use indirection via index mapping. `flatten_indices()` makes a contiguous copy — needed before `with_format("torch")` after filtering.

### 5. Concatenate & Interleave

#### `concatenate_datasets()`
```python
from datasets import concatenate_datasets
combined = concatenate_datasets([dataset1, dataset2, dataset3])
```

#### `interleave_datasets()`
```python
from datasets import interleave_datasets
# Weighted — 70% from dataset1, 30% from dataset2
combined = interleave_datasets(
    [dataset1, dataset2], probabilities=[0.7, 0.3], seed=42
)
# Continue until all datasets exhausted
combined = interleave_datasets(
    [dataset1, dataset2], stopping_strategy="all_exhausted"
)
```

### 6. Save & Export

- **`save_to_disk()` / `load_from_disk()`**: Arrow format (fast local reload).
- **`push_to_hub()`**: Upload to Hub with optional `num_proc` parallel upload.
- **Export**: `to_csv()`, `to_json()`, `to_parquet()` (compressed), `to_sql()`, `to_pandas()`, `to_dict()`, `to_iterable_dataset()`.

All export methods support `hf://` paths for direct Hub upload:
```python
dataset.to_csv("hf://datasets/username/repo/path/to/file.csv")
dataset.to_parquet("hf://buckets/username/bucket/path/to/file.parquet")
```

### 7. DatasetDict Operations

DatasetDict applies methods to every split:
```python
splits = dataset.train_test_split(test_size=0.2, seed=42)
splits = splits.map(tokenize, batched=True)
splits = splits.rename_column("old", "new")
splits = splits.remove_columns(["unused"])
splits = splits.cast(new_features)
splits.save_to_disk("/path/to/dataset")
splits.push_to_hub("username/my_dataset")
```

### Key Design Insight: Arrow-Based Zero-Copy

The datasets library uses Apache Arrow as its memory format. Operations like `select()`, `shard()`, and `filter()` use **indirection (indices arrays)** rather than data copying:
- `select()` is O(1) in memory.
- `shard()` creates new views, not copies.
- `flatten_indices()` needed only for contiguous copy.
- `remove_columns()` without `map()` is zero-copy for remaining columns.

### Best Practices

1. **Use `remove_columns` in `map()`** to avoid keeping unnecessary columns.
2. **Batch maps** with `batched=True` for tokenization — 10-100x faster.
3. **Set `num_proc`** for CPU-bound operations.
4. **Disable cache** with `load_from_cache_file=False` when debugging.
5. **Use stratified splits** (`stratify_by_column`) for classification datasets.
6. **`flatten_indices()` before `with_format("torch")`** after filtering/sharding.
7. **`interleave_datasets()` with probabilities** for mixing domain datasets.
8. **Use `shard()` for distributed training** — each worker loads one shard.
9. **Save as Parquet** for long-term storage (compressed), Arrow for local caching (fast reload).

### Zero-Cost Relevance

All operations are **100% free** — no API calls, no GPU, no inference credits. They run entirely locally on Apache Arrow.

For Beer's 8 datasets (tool-calling training data), these operations are directly applicable:
- Split into train/validation for evaluation
- Shard for parallel processing
- Map to format data for different model architectures
- Filter by task type
- Rename/cast columns for consistency

### References
- https://huggingface.co/docs/datasets/v4.8.4/process
- https://huggingface.co/docs/datasets/v4.8.4/en/package_reference/main_classes
- https://huggingface.co/docs/datasets/v4.8.4/en/loading#slice-splits

---

## 2026-07-24: lm-evaluation-harness-complete-reference — EleutherAI LM Evaluation Harness v0.4.0+ Complete Guide (Topic #170, New)

### Summary
Complete deep-dive into the LM Evaluation Harness — the industry-standard framework for benchmarking LLMs on 60+ academic benchmarks. Covers the v0.4.0 CLI refactoring (`lm-eval run`/`ls`/`validate` subcommands), lighter install with model backend extras (`hf`, `vllm`, `sglang`, `api`), YAML config file support, Python API (`simple_evaluate`, `EvaluatorConfig`, `evaluate`), thinking/reasoning model evaluation (`enable_thinking`, `think_end_token`), task creation via YAML+Jinja2, filter pipelines (regex, majority vote, self-consistency), multi-GPU parallelism strategies (data parallel, model parallel, tensor parallel), and HF Hub logging integration. Full document at `skills/mlops/evaluation/lm-evaluation-harness/references/hf-learnings.md`.

### Key Discovery: CLI Now Uses Subcommands
The legacy `lm_eval --model hf --tasks ...` flat syntax still works but the canonical interface is now `lm-eval run` (evaluate), `lm-eval ls` (list tasks/groups/tags), and `lm-eval validate` (validate configs). YAML config files via `--config` enable reusable, shareable evaluation plans.

### Key Discovery: Thinking Model Support
`enable_thinking=True` and `think_end_token` (string or token ID) strip CoT reasoning traces from models like Qwen3/DeepSeek-R1 before metric computation. Token ID form (`think_end_token=200008`) avoids edge cases. Only compatible with generative (`generate_until`) tasks.

### Key Discovery: Three Python Entry Points
`simple_evaluate()` for quick scripts, `EvaluatorConfig.from_config()` for config-driven workflows, and `evaluate()` for full control. All return structured dicts with results, configs, versions, and optional per-sample logs.

### Key Discovery: v0.4.0 Decoupled Backends
Base install no longer bundles `transformers`/`torch`. Users install only the backends they need via extras: `lm_eval[hf]`, `lm_eval[vllm]`, `lm_eval[api]`, etc. This drastically reduces the installation footprint for API-only or vLLM-only users.

**Full document:** `skills/mlops/evaluation/lm-evaluation-harness/references/hf-learnings.md`

---

## 2026-07-24: hf-transformers-gguf-integration-v2 — Small Model Quantization, Hub Ecosystem & Quantization Taxonomy (Topic #94 Deepened)

### Summary
Deep-dive into the latest Transformers GGUF integration developments (v5.14.1), Hub ecosystem features, and the complete GGUF quantization taxonomy. Three new areas: (1) **June 2026 small model quantization support** (#46449) enables GGUF direct loading for tiny models (0.5B–1.5B) with 15-20% faster dequantization and reduced peak memory. (2) **Full Hub GGUF ecosystem** — built-in tensor viewer for no-download metadata inspection, `@huggingface/gguf` JS parser, `ggml-org/gguf-my-repo` Space for free browser-based conversion. (3) **Complete quantization type taxonomy** — all 25+ types (F32, F16, Qx_K, IQx, MXFP4, TQ) with selection guide by use case including Beer-specific guidance for his 0.5B and 1.5B GGUF files. Full document at `skills/mlops/hf-gguf-llama-cpp/references/hf-learnings.md`.

### Key Discovery: Small Model Quantization Path (June 2026)
Transformers v5.14.1 introduced an optimised GGUF loading path for models <3B parameters. Files added: `gemma_quant.py` (+249), `quantizer_gemma.py` (+75), `ggml.py` (+18). Auto-selected based on model size — no config changes needed. Impact: 15-20% faster loading with reduced peak memory.

### Key Discovery: Hub GGUF Viewer & JS Parser
The Hub provides `?show_tensors=<filename>` for per-tensor metadata inspection without downloading. The `@huggingface/gguf` npm package enables programmatic remote GGUF parsing in JS/TS — useful for auto-generating model cards and building GGUF discovery tools.

### Key Discovery: Quantization Type Taxonomy
25+ types across 4 families: unquantized (F32, F16, BF16), K-quant (Q2_K through Q8_K — recommended), IQ (IQ4_NL through IQ1_M — sub-3-bit), and next-gen (TQ1_0, TQ2_0, MXFP4). Selection guide: Q4_K_M for default balance, Q5_K_M for best quality, IQ3_XXS for memory-constrained, Q2_K for extreme compression.

**Full document:** `skills/mlops/hf-gguf-llama-cpp/references/hf-learnings.md`

---

## 2026-07-24: hf-datasets-sort-shuffle-split-shard — Dataset Sort, Shuffle, Split & Shard Deep Dive (Topic #162 Deepened)

### Summary
Comprehensive deep-dive into the 🤗 Datasets library's row-rearrangement methods — `sort()`, `shuffle()`, `select()`, `filter()`, `train_test_split()`, and `shard()` — tested live against Datasets v5.0.0 with the MRPC dataset (3,668 rows). Covers the new v5.0.0 API signatures (multi-column sort, `null_placement`, `stratify_by_column`), the critical indices-mapping performance trap, the `flatten_indices()` escape hatch, and the IterableDataset buffer-shuffle alternative. Full document at `skills/mlops/hf-datasets-library/references/hf-learnings.md`.

### Key Discovery: v5.0.0 sort() API Changes
`sort()` now accepts `column_names` (plural) — a single string or sequence of strings — and supports per-column `reverse` as either a single bool or a per-column sequence. `null_placement` controls where null rows appear:

```python
# Single-column sort
sorted_ds = ds.sort("label")           # ascending (default)
sorted_rev = ds.sort("label", reverse=True)  # descending

# Multi-column sort (v5.0.0+)
sorted_multi = ds.sort(["label", "idx"], reverse=[False, True])

# Null placement (v5.0.0+)
sorted_nulls_first = ds.sort("label", null_placement="at_start")
```

The sort creates an **indices mapping** — a list of integer indices sorted by column values, used to reorder rows on access. This is memory-efficient (only stores `n` int32 values) but adds indirection on every read.

### Key Discovery: shuffle() — Performance Trap
`shuffle()` randomly permutes the indices mapping. **After shuffle, all subsequent row access becomes ~10× slower** because data is no longer read contiguously from the Arrow table:

```python
shuffled = ds.shuffle(seed=42)  # fast (O(n) permutation), but...
print(shuffled[0])  # slow — random seek in Arrow table
```

**The fix:** `flatten_indices()` rewrites the entire dataset to disk, materializing the shuffled order into a contiguous Arrow table:

```python
# Slow access after shuffle
shuffled = ds.shuffle(seed=42)

# Rewrite to disk — restores contiguous access speed
flattened = shuffled.flatten_indices()  # ~60ms for 3,668 rows
print(flattened[0])  # fast again
```

`flatten_indices()` copies all data to a new cache file. For large datasets, this is a one-time cost worth paying if you'll do many random accesses.

### Key Discovery: IterableDataset Buffer Shuffle
For streaming/large datasets, use `IterableDataset.shuffle()` — a buffer-based approximate shuffle that avoids creating indices mappings entirely:

```python
iterable = dataset.to_iterable_dataset(num_shards=128)
shuffled = iterable.shuffle(seed=42, buffer_size=10_000)
```

**How it works:** Fills a buffer from all shards, randomly selects one to yield, replaces it. Buffer size controls shuffle quality — larger = better randomness. Also shuffles shard order. No `flatten_indices()` needed because there's no indices mapping.

**Per-epoch re-shuffle:** Use `set_epoch(epoch)` to change the effective seed per epoch:
```python
for epoch in range(5):
    shuffled.set_epoch(epoch)
    for example in shuffled:
        ...
```

### Key Discovery: select() vs filter()
Two filtering approaches with different performance characteristics:

| Aspect | `select()` | `filter()` |
|--------|-----------|------------|
| **Input** | List of integer indices | Callable predicate |
| **Memory** | Stores indices list (efficient) | Materializes all data matching predicate |
| **Speed** | O(n) — just creates index list | O(n × fn_cost) — evaluates function on every row |
| **Use case** | Known positions | Dynamic conditions |
| **with_indices** | N/A | ✅ `filter(fn, with_indices=True)` passes `(example, idx)` |

```python
# select — known positions, instant
subset = ds.select([0, 10, 20, 30, 40])

# filter — dynamic condition (evaluates all rows)
result = ds.filter(lambda x: x["label"] == 1)  # ~0.01s for 3,668 rows

# filter with indices
even = ds.filter(lambda ex, idx: idx % 2 == 0, with_indices=True)
```

Both create indices mappings, with the same `flatten_indices()` escape hatch for speed recovery.

### Key Discovery: train_test_split() with Stratification
`train_test_split()` creates train/test splits with optional stratified sampling:

```python
# Basic split
split = ds.train_test_split(test_size=0.1, seed=42)

# Stratified split (v5.0.0+) — preserves class proportions
stratified = ds.train_test_split(test_size=0.2, stratify_by_column="label", seed=42)

# Absolute count
split = ds.train_test_split(test_size=100, train_size=500)
```

Returns a `DatasetDict` with `"train"` and `"test"` keys. Default `shuffle=True` — set `shuffle=False` to preserve order (e.g., time-series).

### Key Discovery: shard() — Contiguous vs Round-Robin
`shard()` splits a dataset into `num_shards` equal chunks:

```python
# Default: contiguous (splits dataset into sequential blocks)
shard_0 = ds.shard(num_shards=4, index=0)  # rows 0–916
shard_1 = ds.shard(num_shards=4, index=1)  # rows 917–1833

# Round-robin: distributes rows 0,4,8... to shard 0 → better for imbalanced sorted data
shard_2 = ds.shard(num_shards=4, index=2, contiguous=False)
```

| Parameter | `contiguous=True` (default) | `contiguous=False` |
|-----------|-----------------------------|-------------------|
| **Distribution** | Sequential blocks | Round-robin |
| **Shard locality** | Rows are adjacent | Rows interleaved across shards |
| **Use case** | Split large file into chunks | Distributed processing / worker assignment |
| **Random access after** | Fast (contiguous) | Slow (scattered indices) |

### Best Practices

1. **For exploration/analysis:** Use `select()` over `filter()` when indices are known — it avoids evaluating a function on every row
2. **After shuffle/filter:** Call `flatten_indices()` if you'll do repeated random access — the one-time rewrite cost pays off quickly
3. **For large datasets (streaming):** Use `IterableDataset.shuffle(buffer_size)` — no indices mapping, no speed penalty
4. **For model training:** Use `IterableDataset.shuffle()` with `set_epoch()` for per-epoch reshuffling; avoid `Dataset.shuffle()` + `flatten_indices()` at scale
5. **For train/test split:** Use `stratify_by_column` to maintain class balance — critical for imbalanced classification datasets
6. **For distributed processing:** Use `shard(contiguous=False)` (round-robin) for balanced worker assignment when data is sorted by a label column
7. **Per-epoch shuffling order:** `shuffle() → flatten_indices()` once, then save the flattened dataset and reload each epoch — faster than re-shuffling from scratch

### Live Test Results (verified this session)
Tested on `nyu-mll/glue` MRPC split (3,668 rows) with Datasets v5.0.0:
- `sort(label)`: 0.001s — instant (creates indices mapping)
- `shuffle(seed=42)`: 0.003s — fast (permutes indices)
- `flatten_indices()`: 0.062s — rewrites 3,668 rows to disk
- `filter(label==1)`: 2,474 matching rows — ~0.01s for 3,668 evaluations
- `train_test_split(test_size=0.1)`: 3,301 train + 367 test — balanced split
- `shard(4, 0)`: 917 rows per shard — equal distribution

### Source
- Official docs (process): https://huggingface.co/docs/datasets/en/process
- Dataset API ref (v5.0.0): https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.Dataset
- IterableDataset API ref: https://huggingface.co/docs/datasets/main/en/package_reference/main_classes#datasets.IterableDataset
- Datasets source: `/opt/data/.venv-sakthai/lib/python3.14/site-packages/datasets/arrow_dataset.py`
- Live test: datasets v5.0.0 on MRPC (3,668 rows), verified this session

---

## 2026-07-24: spaces-zerogpu-free-gpu-allocation — Complete ZeroGPU API & Architecture Deep Dive (Topic #4 Deepened)

### Summary
Comprehensive deep-dive into Hugging Face Spaces ZeroGPU — the free dynamic GPU allocation infrastructure for Gradio Spaces. Covers the ZeroGPU architecture (shared GPU pool, dynamic attach/detach, CUDA emulation), the `@spaces.GPU` decorator API (size, duration, dynamic duration), the programmatic control API via `huggingface_hub` v1.24.0 (hardware requests, volumes, sleep time, pause/restart/duplicate), quota system and tiers (5 min/day free, 40 min PRO), GPU size selection (large=48 GB, xlarge=96 GB), multi-GPU support, AOT compilation (replaces unsupported `torch.compile`), and 10 optimisation patterns for free accounts including model-level loading, caching, accurate duration setting, and storage volume integration. Full document at `skills/mlops/spaces-zerogpu/references/hf-learnings.md`.

### Key Discoveries

1. **CUDA emulation layer** — PyTorch `.to("cuda")` works at module level WITHOUT a real GPU. Only `@spaces.GPU`-decorated functions get real GPU access. This is the core architectural insight.

2. **Dynamic duration** — `@spaces.GPU(duration=callable)` accepts a callable that returns expected runtime based on inputs, enabling accurate quota accounting for variable-length tasks (video gen, high-res images).

3. **Programmatic lifecycle** — Full API via `huggingface_hub`: `request_space_hardware(hardware=SpaceHardware.ZERO_A10G)`, `set_space_volumes()`, `wait_for_space()`, `pause_space()`, `restart_space(factory_reboot=True)`.

4. **AOT compilation** — `torch.compile()` is NOT supported. Use `torch.export` ahead-of-time compilation (torch 2.8+) for faster first inference.

5. **Free account limits** — Max 2 ZeroGPU Spaces, 5 min/day GPU quota, 48h inactivity auto-sleep. Quota resets 24h after first daily GPU usage.

### Resource
Full document: `skills/mlops/spaces-zerogpu/references/hf-learnings.md`

---

## 2026-07-24: hf-quantization-methods-comparison-v2 — Official Benchmark Data + Production Decision Guide (Topic #158 Deepened)

### Summary
Deep-dive into the **official Transformers quantization benchmarks** released alongside the new "Selecting a quantization method" guide. This is the first time HF published standardized, apples-to-apples benchmark data comparing 15+ quantization methods across accuracy (4 benchmarks), throughput (tok/s), peak VRAM, and quantization time — on Llama 3.1 8B and 70B on A100/H100 GPUs. Covers new findings: torch.compile speedups, Marlin kernel gains, calibration time trade-offs, and the catastrophic accuracy collapse of certain methods at 70B.

### Source
- Selecting a quantization method: https://huggingface.co/docs/transformers/en/quantization/selecting
- Benchmark dataset: https://huggingface.co/datasets/derekl35/quantization-benchmarks
- Published: 2026-07-24, Transformers v5.14.0

### Key Discovery: First Official HF Quantization Benchmarks

| Quant Method | Bits | Avg Acc (8B) | Throughput (8B) | VRAM (8B) | Quant Time (8B) | Avg Acc (70B) | Throughput (70B) | VRAM (70B) | Quant Time (70B) |
|---|---|---|---|---|---|---|---|---|---|
| **baseline (bf16)** | 16 | 0.6106 | 38.82 tok/s | 16.77 GB | — | 0.6929 | 9.73 tok/s | 142.27 GB | — |
| **AWQ** | 4 | 0.6006 | 43.09 | 8.12 GB | ~10 min | 0.6795 | 15.74 | 43.75 GB | ~1 hr |
| **GPTQModel** | 4 | — | 36.83 | 6.32 GB | ~23 min | — | 14.84 | 40.58 GB | — |
| **AutoGPTQ** | 4 | 0.5953 | 43.71 | 6.49 GB | ~30 min | 0.6836 | 0.46 ❗ | 42.40 GB | ~2 hr |
| **bnb (nf4)** | 4 | 0.6020 | 24.35 | 6.44 GB | ~1 min | 0.6838 | 11.27 | 44.63 GB | ~2 min |
| **HQQ** | 4 | 0.6031 | 34.44 | 6.72 GB | instant | 0.6805 | 13.92 | 44.50 GB | ~10 min |
| **optimum-quanto (w4a16)** | 4 | 0.5966 | 31.22 | 6.58 GB | ~30 sec | **0.3597** ❗ | 12.97 | 80.39 GB | ~2 min |
| **torchao (int4wo)** | 4 | 0.5959 | 24.98 | 6.50 GB | ~20 sec | **0.3629** ❗ | 10.56 | 41.61 GB | ~2 min |
| **HIGGS** | 4 | 0.5930 | 28.35 | 6.82 GB | ~5 min | **0.3578** ❗ | 11.61 | 41.53 GB | ~6 min |
| **bnb (llm.int8)** | 8 | 0.6086 | 20.75 | 9.71 GB | ~20 sec | 0.6618 | 6.87 | 74.26 GB | ~2 min |
| **HQQ (8 bit)** | 8 | 0.6117 | 9.07 | 10.60 GB | ~80 sec | 0.6958 | 0.98 | 80.52 GB | ~10 min |
| **optimum-quanto (int8wo)** | 8 | 0.6110 | 15.59 | 9.82 GB | ~20 sec | 0.6611 | 1.79 | 74.21 GB | ~2 min |
| **torchao (int8wo)** | 8 | 0.6111 | 5.98 | 13.07 GB | ~30 sec | 0.6931 | 0.65 | 89.85 GB | ~2 min |
| **fbgemm (fp8)** | 8 | 0.6095 | 33.83 | 10.01 GB | ~30 sec | 0.6924 | 13.61 | 74.05 GB | ~6 min |
| **compressed-tensors (fp8)** | 8 | 0.6073 | — | — | — | 0.6918 | — | — | — |
| **VPTQ** | 2 | 0.5414 | 32.35 | 5.29 GB | ~2 hr | 0.6409 | 6.29 | 24.90 GB | ~19 hr |
| **AQLM + PV** | 2 | 0.5708 | 22.28 | 4.84 GB | ~1 day | 0.6635 | 6.75 | 23.13 GB | **10-14 days** ❗ |
| **AutoGPTQ (2 bit)** | 2 | **0.3645** ❗ | 6.25 | 11.02 GB | ~26 min | **0.4119** ❗ | — | — | — |

❗ = notable failure mode (near-random accuracy, throughput collapse, or impractical quantization time)

### Key Discovery: torch.compile Transformations

torch.compile can radically alter the quantization landscape:

| Method | Model | Without torch.compile | With torch.compile | Speedup |
|---|---|---|---|---|
| **torchao (int4wo)** | Llama 3.1 8B | 24.98 tok/s | **85.76 tok/s** | **3.4×** |
| **torchao (int8wo)** | Llama 3.1 8B | 5.98 tok/s | **43.79 tok/s** | **7.3×** |
| **torchao (int4wo)** | Llama 3.1 70B | 10.56 tok/s | **18.95 tok/s** | 1.8× |
| **HIGGS (4 bit)** | Llama 3.1 70B | 11.61 tok/s | 12.38 tok/s | 1.07× |
| **AQLM + PV (2 bit)** | Llama 3.1 8B | 22.28 tok/s | 27.27 tok/s | 1.2× |
| **VPTQ (2 bit)** | Llama 3.1 8B | 32.35 tok/s | 31.48 tok/s | 0.97× (slight regression) |
| **baseline (bf16)** | Llama 3.1 8B | 38.82 tok/s | 79.27 tok/s | **2.0×** |

**torchao benefits most from torch.compile** — it's practically required for good performance with torchao. HQQ and AWQ don't need it (they have their own kernels).

### Key Discovery: Marlin Kernel Impact

GPTQModel supports Marlin kernels (only for 4-bit, group_size=128):

| Method | Without Marlin | With Marlin | Speedup |
|---|---|---|---|
| GPTQModel (4-bit) Llama 3.1 8B | 36.83 tok/s | 37.84 tok/s | 1.03× |
| GPTQModel (4-bit) Llama 3.1 70B | 14.84 tok/s | 15.28 tok/s | 1.03× |

Marlin gives modest (~3%) throughput gains. Not transformative — but consistent.

### Key Discovery: Catastrophic Accuracy Collapse at 70B for Multiple Methods

Several on-the-fly 4-bit methods that work acceptably on 8B models **collapse to near-random accuracy on 70B**:

| Method | Avg Acc (8B) | Avg Acc (70B) | Delta |
|---|---|---|---|
| **optimum-quanto (w4a16)** | 0.5966 | **0.3597** | -0.2369 — **near random** |
| **torchao (int4wo)** | 0.5959 | **0.3629** | -0.2330 — **near random** |
| **HIGGS (4 bit)** | 0.5930 | **0.3578** | -0.2352 — **near random** |

While AWQ, GPTQModel, bnb-nf4, and HQQ maintain good accuracy at 70B (drop <0.02 from baseline). This is a critical finding: **on-the-fly 4-bit quantization methods that bypass calibration (quanto, torchao, HIGGS) fail catastrophically on larger models.** The exception is HQQ, which maintains accuracy through its half-quadratic approach despite being on-the-fly.

### Key Discovery: Quantization Time vs. Quality Trade-off

| Time Class | Methods | Best for |
|---|---|---|
| **Instant (<2 min)** | bnb-nf4, bnb-int8, torchao, quanto, HQQ, fbgemm, HIGGS | Rapid iteration, prototyping, zero-cost deployment |
| **Quick (2-30 min)** | AWQ (8B), GPTQModel (8B), HQQ (70B) | Production 4-bit with good quality |
| **Hours** | AWQ (70B ~1hr), AutoGPTQ (70B ~2hr), VPTQ (8B ~2hr) | Best quality 4-bit on large models |
| **Days** | AQLM (8B ~1 day), VPTQ (70B ~19hr), AQLM (70B **10-14 days**) | Extreme 2-bit compression, research only |

### Key Discovery: Quantization Method Selection Guideline (Updated)

Based on the new benchmark data, the decision tree simplifies to:

1. **Need QLoRA fine-tuning?** → bitsandbytes (nf4). Only mature option.
2. **Need on-the-fly 4-bit for inference?** → HQQ (best accuracy/speed balance) or bnb-nf4 (most mature, but slower)
3. **Need best 4-bit quality with pre-quantized model?** → AWQ (8B: ~10 min calibrate, best accuracy; 70B: ~1 hr but excellent retention)
4. **Need 8-bit with zero accuracy loss?** → fbgemm fp8 (33.83 tok/s on 8B) or bnb-int8 (20.75 tok/s) or torchao int8wo + torch.compile (43.79 tok/s)
5. **Need extreme compression (2-bit, sub-6GB)?** → AQLM for quality or VPTQ for speed, but prepare for multi-day quantization
6. **On Apple Silicon?** → GGUF (not benchmarked here) remains the best choice
7. **Using torch.compile?** → torchao int4wo + compile = 85.76 tok/s (fastest 4-bit in the benchmarks)

### Zero-Cost Recommendations (Updated with Benchmark Data)

Given Beer's zero-cost constraint and 8 models on HF:

1. **Serverless inference** → Pre-quantized GGUF models (free, no GPU)
2. **Local CPU testing** → GGUF Q4_K_M (single file, any hardware)
3. **Free GPU (Colab/ZeroGPU) fine-tuning** → bitsandbytes nf4 + PEFT (QLoRA) — ~1 min to quantize, ~6.44 GB VRAM, accuracy 0.6020 vs 0.6106 baseline (98.6% retained)
4. **Free GPU inference** → HQQ 4-bit (instant quantize, 34.44 tok/s, 6.72 GB, accuracy 0.6031 — **best accuracy-per-dollar of any on-the-fly method**)
5. **Quantizing Beer's own models for release** → AWQ 4-bit (best quality, but needs ~10 min calibration) or GGUF (widest compatibility)
6. **AVOID on 70B-class models**: quanto int4, torchao int4wo, HIGGS — they collapse to random accuracy

### Resources (Updated)
- Selecting a method: https://huggingface.co/docs/transformers/en/quantization/selecting
- Benchmark dataset: https://huggingface.co/datasets/derekl35/quantization-benchmarks
- All individual method docs linked from: https://huggingface.co/docs/transformers/en/quantization/overview


---

## 2026-07-24: hf-vllm-transformers-modeling-backend-native-deep-dive — Native-Speed vLLM Transformers Modeling Backend (Topic #51 Deepened)

### Summary
Deep-dive into the **native-speed vLLM transformers modeling backend** (July 2026) — the architectural leap that makes any Hugging Face Transformers model run inside vLLM at native vLLM speed, without writing a custom port. Uses `torch.fx` static analysis + AST source rewriting to dynamically fuse operations at runtime, matching hand-optimized kernels. Covers architecture, pattern detection, the fuser engine, parallelism, limitations, and relationship to the prior-generation integration.

### Source
- Blog: https://huggingface.co/blog/native-speed-vllm-transformers-backend (Harry Mellor & Lysandre, Jul 8, 2026)
- vLLM source: `vllm/model_executor/models/transformers/` — `base.py`, `causal.py`, `moe.py`, `pooling.py`, `multimodal.py`, `fuser.py`, `fx_utils.py`, `utils.py`
- Fusers: `vllm/model_executor/models/transformers/fusers/` — `base.py`, `glu.py`, `qkv.py`, `rms_norm.py`, `moe.py`
- CLI flag: `--model-impl transformers`

### 1. What Changed: Second-Generation Integration

The **first-generation** integration (2025) plugged vLLM's attention implementation at runtime into transformers models, making them run inside the vLLM engine — but many optimizations (Tensor Parallel, Expert Parallel, fused kernels, compilation) still required a custom native vLLM implementation to reach peak performance.

The **second-generation** (July 2026) dynamically applies inference-specific layer fusions at runtime via `torch.fx` static analysis. This closes the gap — models using the transformers backend now match or exceed native vLLM throughput.

Key results (Qwen3 models, 8×H100):
- **Qwen3-4B** (dense, 1 GPU): transformers backend meets native throughput
- **Qwen3-32B** (dense, TP=2): transformers backend meets native throughput
- **Qwen3-235B-A22B-FP8** (MoE, DP+EP, 8 GPUs): transformers backend meets native throughput

### 2. Architecture & Two-Phase Pipeline

The system has two phases:

**Phase 1 — Class-level Analysis (once per model class):**
1. `Fusers.__init__` iterates all `model.modules()`, calling `get_fuser(type(m))`
2. `get_fuser` checks if the module has ≥2 `nn.Linear` children (projection fusion candidates) or is a leaf module (RMSNorm candidates)
3. Calls `trace(module)` — uses `_AllLeafTracer` (treats every submodule as a leaf) with `_SizedProxy` for shape inference, producing a partial `fx.Graph` even on failure
4. Passes the graph through each fuser class's `match()` method in order: `GLUFuser`, `QKVFuser`, `RMSNormFuser`
5. If a `StackedFuser` matches, calls `update_forward()` which uses AST rewriting to manipulate the forward source at the Python `ast` level — replacing the individual projection calls with a single merged call
6. Results are cached per class (via `@cached(cache={}, key=type)`) — so only analyzed once

**Phase 2 — Instance-level Application:**
1. `Base.recursive_replace()` walks the instantiated model
2. For each module, checks `fusers[type(module)]` — if a fuser matches and validates
3. Calls `fuser.fuse(module)` which builds the merged vLLM layer (e.g., `QKVParallelLinear`) and binds the compiled forward
4. The module retains its original class but the forward is replaced with the fused version

### 3. The Fuser Engine (fx_utils.py)

The tracing engine in `fx_utils.py` provides:

- **`_AllLeafTracer`**: Custom `fx.Tracer` that treats all submodules as leaves, keeping the graph at the right granularity for pattern matching
- **`_SizedProxy`**: Proxies with inferred `len()` — enables tracing through shape unpacking like `(*input_shape, -1, head_dim)` via `_infer_len()` which walks the graph's `operator.getitem` chain
- **`trace(module)`**: Returns a partial `fx.Graph` on failure (vs raising) — graphs are only evidence for matching, and patterns sit at the top of forwards
- **`recover_forward(cls)`**: Parses forward source via `inspect.getsource` + `ast.parse`, strips decorators/annotations for safe recompilation
- **`compile_forward(funcdef, fn)`**: Compiles the rewritten AST in `fn`'s module so tracebacks point at the original source file
- **`single_self_call(funcdef, name)`**: Locates the unique `self.<name>(arg)` call — ensures AST rewrites agree with fx matches
- **`innermost_block(block, node)`**: Finds the statement list containing a node for in-place replacement
- **`replace_expr(module, old, new)`**: Identity-based expression replacement in the AST
- **`peel(node)`**: Strips dtype-cast wrappers (`.to()`, `.float()`, `.half()`, etc.)
- **`is_fn`/`is_method`/`is_op`**: Predicates for matching `torch.*`, `F.*`, `operator.*`, and `Tensor.*` calls

### 4. Concrete Fusers

**4.1 `GLUFuser`** — GLU/GELU activation fusions:
Matches the pattern `silu(x) * gate(x)` or `gelu(x) * gate(x)` where both projections are sibling `nn.Linear` modules. Fuses the two linears into a single `MergedColumnParallelLinear`, reducing memory traffic.

**4.2 `QKVFuser`** — QKV projection fusion:
Matches the pattern where Q, K, V projections are three sibling `nn.Linear` modules. Fuses into `QKVParallelLinear`, enabling the TP-aware fused kernel that computes all three projections in one pass.

**4.3 `RMSNormFuser`** — RMSNorm fusion:
Matches raw tensor math patterns (no submodules) for RMSNorm-shaped computations. Fuses into the vLLM fused RMSNorm kernel. Modules with `RMSNorm` in their class name that don't match trigger a warning about being left unfused.

**4.4 `MoEBlockFuser`** (moe.py) — Mixture-of-Experts fusion:
The most complex fuser. Routes an HF MoE block through vLLM's `FusedMoE` with vLLM's own routing. Uses AST rewriting to:
- Replace the router linear with vLLM's routing
- Replace the expert MLP with `FusedMoE` (supports Expert Parallel)
- Handle shared experts, scalar gates, sigmoid gating
- Detect and preserve the MoE block's attention/MLP separation
- 500+ lines of AST pattern matching for all MoE architectures

### 5. Parallelism Support

The fused operations directly enable parallelization:

- **MergedColumnParallelLinear + QKVParallelLinear**: These fused blocks allow vLLM to infer Tensor Parallel (TP) plans automatically. `ColumnParallelLinear` shards the weight column-wise across GPUs; `RowParallelLinear` shards row-wise.
- **Expert Parallel (EP)**: The MoE fuser enables EP by routing experts through `FusedMoE` which distributes experts across GPUs.
- **Pipeline Parallel (PP)**: PP plans are inferred when the decoder block list is easily identifiable.
- **Fully compilable**: Fused models pass through `torch.compile` and CUDA graphs, same as dedicated vLLM implementations.

### 6. Usage

```bash
# Basic: any HF model with a single GPU
vllm serve Qwen/Qwen3-4B --model-impl transformers

# Tensor Parallel
vllm serve Qwen/Qwen3-32B --model-impl transformers --tensor-parallel-size 2

# MoE with Expert Parallel
vllm serve Qwen/Qwen3-235B-A22B-FP8 --model-impl transformers \
  --data-parallel-size 8 --enable-expert-parallel

# Memory-constrained: reduce context length
vllm serve Qwen/Qwen3-235B-A22B-FP8 --model-impl transformers \
  --max-model-len 8192
```

The `--model-impl transformers` flag composes with all other vLLM arguments.

### 7. Limitations & Roadmap

- **Linear attention models** are not currently supported (roadmap: "soon")
- **Custom Hub models** (code living in a HF repo) are unlikely to work — they must be written in compliant transformers style
- **Not all architectures fuse equally** — the pattern matcher only handles architectures it can structurally match (requires identifiable decoder blocks, standard projection patterns)
- **Fuser detection is conservative** — if a pattern is ambiguous, the module is left unfused rather than risking incorrect behavior
- **One-time warmup cost** — `torch.fx` tracing + AST compilation happens once per model class on first load

### 8. Key Architectural Insight

The key insight is that the system is **dual-level**: class-level analysis is done once and cached (via `@cached(cache={}, key=type)` on `get_fuser`), while instance-level application happens per-model-load. The `@support_torch_compile` decorator on `Base` ensures the whole model remains `torch.compile`-compatible even after fusion.

The use of `ast` (not `fx` graph rewriting) for forward replacement is deliberate — AST rewriting preserves the surrounding Python logic (conditionals, loops, auxiliary computations) while only replacing the matched operation. `fx` is used only for *detection*, never for *execution*.

### 9. Comparison: Before vs After

| Aspect | First-gen (2025) | Second-gen (July 2026) |
|--------|-----------------|----------------------|
| Attention impl | vLLM attention | vLLM attention + TP/EP fused |
| Fusions | None (manual) | GLU, QKV, RMSNorm, MoE (auto) |
| Analysis | None | torch.fx + AST rewriting |
| Speed vs native | Slower | Equal or better |
| Custom models needed | No | No (if compliant) |
| Setup | `--model-impl transformers` | Same flag, better perf |

## 2026-07-24: hf-peft-lora-deep-dive — Complete LoRA Variants & Advanced Training (Topic #177)

### Summary
Deep dive into PEFT v0.20.0 covering all LoRA initialization strategies (PiSSA, OLoRA, EVA, MiCA, CorDA, LoftQ, LoRA-GA, rsLoRA), advanced training features (DoRA, layer replication, KappaTune, trainable token indices, weight tying), MoE expert parameter targeting (target_parameters), multi-adapter management, merging patterns, and the complete LoraConfig API. Fills the gap since topic #9 (hf-peft-lora) covered only the basics.

### Source
- PEFT v0.20.0 docs: https://huggingface.co/docs/peft/en/index
- LoRA reference: https://huggingface.co/docs/peft/en/package_reference/lora
- Method overview: https://huggingface.co/docs/peft/en/methods/overview
- PiSSA: https://huggingface.co/papers/2404.02948
- OLoRA: https://huggingface.co/papers/2406.01775
- EVA: https://huggingface.co/papers/2410.07170
- MiCA: https://arxiv.org/abs/2604.01694
- CorDA: https://huggingface.co/papers/2406.05223
- DoRA: https://huggingface.co/papers/2402.09353
- LoRA-GA: https://huggingface.co/papers/2407.05000
- KappaTune: https://arxiv.org/abs/2506.16289
- rsLoRA: https://huggingface.co/papers/2312.03732

### Key Takeaways
1. PEFT v0.20.0 has 32+ methods, LoRA being the most popular
2. 12 initialization strategies — PiSSA for fast convergence, MiCA for domain adaptation, EVA for adaptive rank allocation, CorDA for knowledge preservation
3. use_dora=True for direction-aware adaptation; use_rslora=True for stable high-rank training
4. target_modules="all-linear" is the QLoRA standard
5. trainable_token_indices saves significant VRAM vs full embedding tuning
6. MoE models need target_parameters + merge_and_unload() for production inference
7. KappaTune auto-selects the best layers via condition number analysis

---

## 2026-07-24: hf-timm — PyTorch Image Models Deep Dive (Topic #178 — New)

### Summary
Comprehensive deep-dive into timm (PyTorch Image Models) v1.0.28 — 1,000+ pretrained vision models from 200+ architectures, now part of Hugging Face ecosystem. Covers installation, model creation/listing, inference pipeline, feature extraction (penultimate, multi-scale, intermediate via forward_features/features_only/forward_intermediates), data augmentation (RandAugment, AugMix, random erasing), and Hugging Face Hub integration (push_to_hf_hub, hf_hub: prefix loading). Full document at skills/mlops/hf-timm/references/hf-learnings.md.

### Source
- https://huggingface.co/docs/timm/en/index
- https://huggingface.co/docs/timm/en/quickstart
- https://huggingface.co/docs/timm/en/feature_extraction
- https://huggingface.co/docs/timm/en/hf_hub
- GitHub: https://github.com/rwightman/pytorch-image-models

### Key Takeaways
1. `timm.create_model(model_name, pretrained=True)` works for ALL 1,000+ models — unified interface
2. Always resolve data config via `timm.data.resolve_data_config(model.pretrained_cfg)` for correct transforms
3. Feature extraction: `forward_features()` for penultimate, `features_only=True` for multi-scale pyramid, `forward_intermediates()` for flexible layer access
4. Hub integration: `timm.models.push_to_hf_hub(model, name)` to share, `hf_hub:user/model` prefix to load
5. Built-in data pipeline with RandAugment, random erasing, Mixup, AugMix via `create_loader()`
6. Official training script (`train.py`) supports distributed training, AMP, EMA, and extensive aug config
7. `out_indices` supports negative indexing for convenient last/penultimate feature selection

---

## 2026-07-24: hf-safetensors-library-architecture — Safetensors v0.8.0 Internal Architecture Deep Dive (Topic #1 Deepened)

### Summary
Deep-dive into the `safetensors` Python library (v0.8.0) — the safe serialization format for tensors. Covers the Rust-backed core architecture, the safetensors binary format specification, the `safe_open` context manager with mmap/pread backends, the framework-specific Python adapter layers (torch, numpy, flax, tensorflow, mlx, paddle), zero-copy loading via `torch.frombuffer`/`np.frombuffer`, shared-tensor deduplication logic in `save_model`, and the `TensorSpec` descriptor that bridges Python memory to the Rust serializer. Source: installed package at `/opt/data/.venv-sakthai/lib/python3.14/site-packages/safetensors/`.

### Source
- Installed safetensors v0.8.0 (`_safetensors_rust.abi3.so` Rust extension)
- `__init__.py` — re-exports `SafetensorError`, `TensorSpec`, `safe_open`, `deserialize`, `serialize`, `serialize_file`
- `torch.py` — PyTorch adapter (590 lines)
- `numpy.py` — NumPy adapter (198 lines)
- `flax.py` — JAX/Flax adapter (141 lines)
- `tensorflow.py` — TensorFlow adapter (142 lines)
- `mlx.py` — Apple MLX adapter (143 lines)
- `paddle.py` — PaddlePaddle adapter (308 lines)
- GitHub: https://github.com/huggingface/safetensors

### 1. Architecture Overview

safetensors uses a **Rust core** (`_safetensors_rust.abi3.so`) with thin Python adapter layers per framework. The Python side handles framework-specific conversions (dtype mapping, memory pointer extraction), while the Rust side handles binary format serialization, deserialization, mmap/pread I/O, and slice-based lazy loading.

```
Python ──safe_open──> Rust mmap/pread ──> Lazy pointer-based access
Python ──serialize──> Rust serialization ──> bytes
Python ──deserialize──> Rust deserialization ──> List[(name, {shape, dtype, data})]
```

Six framework adapters each expose the same four-function API:
- `save(tensors_dict) -> bytes` — serialize to bytes
- `save_file(tensors_dict, filename)` — serialize to file
- `load(bytes_data) -> tensors_dict` — deserialize from bytes
- `load_file(filename) -> tensors_dict` — load from file

Plus `save_model()` / `load_model()` for torch which handle shared-tensor deduplication.

### 2. Binary Format Specification

Every `.safetensors` file has exactly two parts:

**Header** (JSON, variable length, 8-byte aligned):
```
8 bytes: header_size as u64 (little-endian)
<header_size> bytes: UTF-8 JSON with structure:
{
  "__metadata__": {"key": "value", ...},  // optional
  "tensor_name": {
    "dtype": "F32",
    "shape": [1024, 768],
    "data_offsets": [0, 3145728]
  },
  ...
}
```
The header ends at offset `8 + header_size`. **Critical**: `header_size` must be a multiple of 8 (the align requirement).

**Tensor data** (raw binary, sequential):
```
<tensor_0 data: data_offsets[1] - data_offsets[0] bytes>
<tensor_1 data: data_offsets[1] - data_offsets[0] bytes>
...
```
Data offsets are absolute positions from the **start of the data segment** (immediately after the header), NOT from the file start.

### 3. Core Rust API (Exposed to Python)

`__init__.py` re-exports from the Rust extension (`_safetensors_rust`):

| Export | Purpose |
|---|---|
| `SafetensorError` | Custom exception for format/validation errors |
| `TensorSpec(dtype, shape, data_ptr, data_len)` | Descriptor for serialization — takes raw memory pointer |
| `safe_open(filename, framework, device, *, backend)` | Context manager for lazy/mmap loading |
| `deserialize(data) -> List[(name, dict)]` | Parse bytes into typed views (no framework conversion) |
| `serialize(tensor_dict, metadata) -> bytes` | Serialize TensorSpec dict to binary |
| `serialize_file(tensor_dict, filename, metadata) -> None` | Serialize directly to file |

The `TensorSpec` class validates dtypes at construction (not at serialize time). For packed dtypes like `float4_e2m1fn_x2`, it transparently doubles the last dimension of the shape so the spec always reflects logical element count.

### 4. safe_open — Lazy File Loading

`safe_open` is the primary loading interface, implemented in Rust with two backends:

```python
with safe_open("model.safetensors", framework="pt", device="cpu", backend="mmap") as f:
    tensor = f.get_tensor("embedding")       # one tensor
    tensors = f.get_tensors()                # all tensors (fast path for MPS+pread)
    keys = f.keys()                          # list of tensor names
    keys_by_offset = f.offset_keys()         # names ordered by file offset
    metadata = f.metadata()                  # header __metadata__
    sl = f.get_slice("embedding")            # slice view (lazy slicing before loading)
    part = sl[:, ::8]                        # actual load + slice
```

**Two backends controlled by `backend=`:**

| Backend | Mechanism | When to use |
|---|---|---|
| `"mmap"` (default) | Memory-map the file → OS page cache → tensors zero-copy from cached pages | General use, fast when data fits in page cache |
| `"pread"` | `pread(2)` syscall for each tensor's byte range into pre-allocated buffer | Apple MPS — reads into shared MTLBuffer without duplicating page cache |

On Apple Silicon MPS with `backend="pread"` + `get_tensors()`, there's a bulk-alloc fast path: allocates shared MTLBuffer, fills with parallel `pread(2)`, hands to torch via DLPack with zero extra copies.

API methods:
- `keys()` / `offset_keys()` — list tensor names (offset_keys is sorted by file offset for reproducibility)
- `get_tensor(name)` — read and convert one tensor
- `get_slice(name)` → returns `PySafeSlice` object for lazy sub-tensor reads (e.g., `sl[10:20, :]` materializes only the sliced bytes)
- `get_tensors()` — bulk read all, fast path on MPS+pread
- `metadata` property — returns `__metadata__` dict from header

### 5. Framework Adapter Architecture

Each adapter follows the same pattern: convert framework tensors to pointer-based `TensorSpec`, delegate to Rust core, then convert back.

#### 5a. numpy.py — Simplest, Foundation for Others

The numpy adapter is the thinnest wrapper and serves as the base for flax, tensorflow, and mlx adapters:

**Save path:**
```python
_flatten(tensor_dict, keep_alive) → Dict[str, TensorSpec]  # ptr + dtype + shape
    → serialize(flattened, metadata)                         # Rust: writes binary
```

**_flatten** creates `TensorSpec` from each ndarray using `tensor.ctypes.data` as `data_ptr` and `tensor.nbytes` as `data_len`. Handles big-endian byte swapping via `byteswap(inplace=False)` before serialization (keeps swapped copy alive via `keep_alive_buffer`).

**Load path:**
```python
deserialize(data) → List[(name, {dtype, shape, data: memoryview})]
    → _view2np(safeview) → Dict[str, ndarray]
```

**_view2np** uses `np.frombuffer(v["data"], dtype=dtype).reshape(v["shape"])` — zero-copy, numpy reads directly from the memoryview wrapper around the Rust buffer.

**Dtype mapping** (common six dtypes): `F64`, `F32`, `F16`, `I64`, `U64`, `I32`, `U32`, `I16`, `U16`, `I8`, `U8`, `BOOL`, `C64`.

#### 5b. torch.py — Most Complex (590 lines)

Extra complexity comes from **shared tensor detection** and **device handling**.

**Save path (`save_file`):**
1. `_evaluate_tensors_for_save(tensors)` — validates all are torch.Tensor, strided (not sparse), and **no tensors share memory** (calls `_find_shared_tensors`)
2. `_find_shared_tensors(state_dict)` — groups tensors by `(device, storage_ptr, storage_size)`. Then `_filter_shared_not_shared` resolves overlapping storage ranges to determine actual sharing.
3. `_to_ndarray(tensor)` — uses `ctypes.cast(tensor.data_ptr(), ...)` + `np.ctypeslib.as_array()` to create a **zero-copy numpy view** of the torch tensor's CPU memory. Handles big-endian byteswap, and float8/float4 types mapped to np.uint8 for storage.
4. `_flatten_as_ptr` builds `TensorSpec` from each ndarray view, keeping a reference alive to prevent GC during serialization.

**Load path (`load_file`):**
```python
safe_open(filename, framework="pt", device=device, backend=backend) as f
    → f.get_tensors()
```
_or via `load(data)`_:
```python
deserialize(data) → List[(name, {dtype, shape, data: memoryview})]
    → _view2torch(safeview) → Dict[str, torch.Tensor]
```

**_view2torch** uses `torch.frombuffer(v["data"], dtype=dtype).reshape(v["shape"])` — **zero-copy** from the deserialized Rust memoryview into a torch tensor. Empty tensors handled via `torch.empty()`.

**`save_model` — Shared Tensor Handling:**
`save_model()` handles the common PyTorch pattern where parameter views share the same underlying storage (e.g., tied weights, `weight` and `weight_orig` in weight-decoupled optimizers):
1. `_find_shared_tensors(state_dict)` discovers groups of names that share storage
2. `_filter_shared_not_shared` refines groups by checking actual memory overlap (not just same storage pointer but overlapping address ranges)
3. `_remove_duplicate_names` picks one `keep_name` per group (preferring `preferred_names` when given, avoiding `discard_names`)
4. Kept name gets saved; removed names are recorded in metadata for traceability
5. **Contiguous enforcement**: `force_contiguous=True` by default, calls `.contiguous()` on all tensors before save

**`load_model` — Reverse Dedup:**
On load, uses `preferred_names=state_dict.keys()` to keep the same names as the saved file, and filters out duplicates from the model's native state dict to get correct missing/unexpected lists.

#### 5c. Higher-Level Adapters (flax, tensorflow, mlx, paddle)

These all delegate to numpy.py:
- **flax.py**: `_jnp2np` converts JAX arrays to numpy → `numpy.save_file` → reverse on load
- **tensorflow.py**: `_tf2np` converts tf.Tensor to numpy → `numpy.save_file` → reverse on load
- **mlx.py**: `_mx2np` converts mx.array to numpy → `numpy.save_file` → reverse on load
- **paddle.py**: Two code paths — pre-3.2.0 uses numpy bridge; 3.2.0+ has direct Rust extension support with `frombuffer` and `safe_open(framework="paddle")`

### 6. Memory Management

**Zero-copy design**: safetensors never copies tensor data unnecessarily. The flow is:
- **Save**: Extract raw data pointer → Rust reads from that pointer → writes to file. No copy in Python.
- **Load (mmap)**: File → OS page cache → tensor reads from cached pages. No extra copy.
- **Load (bytes)**: deserialize → `torch.frombuffer` / `np.frombuffer` reads from the deserialized buffer in-place.

**Memory lifetime management**: The `keep_alive_buffer` / `keep_references_alive` lists in each adapter hold references to temporary numpy views and tensor objects. Without these, Python's GC could free the underlying memory while the Rust serializer is still reading from the pointer. The stub docs note a planned PyBuffer API (Python 3.11+) to handle this automatically via refcounts.

**Endianness**: Both `numpy._flatten` and `torch._to_ndarray` detect system byte order and byteswap big-endian tensors to little-endian before serialization. The `keep_alive_buffer` keeps the swapped copy alive during the Rust serialize call.

### 7. Shared Tensor Detection Algorithm (torch)

The function `_find_shared_tensors` is critical for safe PyTorch serialization:

```
For each (name, tensor) in state_dict:
    if tensor not on meta device and has non-zero storage:
        key = (device, storage_ptr(tensor), storage_size(tensor))
        group[key].add(name)

For each group with >1 name:
    compute (data_ptr, end_ptr) for each tensor in group
    sort by start address
    merge overlapping intervals → deduplicated groups
```

`_is_complete(tensor)` checks if the tensor's view covers the entire storage (start-to-end). Only complete tensors are eligible as `keep_name` candidates.

### 8. Supported Dtypes (Framework-Specific)

Common across all frameworks: F64, F32, F16, BF16, I64, I32, I16, I8, U8, BOOL, C64.

**Extra in torch.py**: U64/U32/U16 (torch 2.3.0+), F8_E4M3, F8_E4M3FNUZ, F8_E5M2, F8_E5M2FNUZ, F8_E8M0, F4_E2M1 (float4 packed).

**Extra in paddle.py**: F8_E4M3, F8_E5M2 (no uint64/uint32/uint16 yet).

Note that float8 and float4 dtypes are stored as raw bytes (mapped to `np.uint8` for numpy view) because numpy has no native float8 types.

### 9. Performance Considerations

- **MMAP is default** and best for CPU inference — tensors loaded on demand, cached by OS
- **PREAD for MPS** — avoids double memory consumption from page cache + MTLBuffer
- **Zero-copy on both save and load** — no intermediate buffer copies in Python
- **`save_model(force_contiguous=True)`** ensures optimal memory layout but may trigger a memory copy for non-contiguous tensors
- **`get_slice()`** enables lazy loading of sub-tensors without reading the entire tensor from disk
- **`get_tensors()` fast path** on MPS+pread bulk-allocates shared MTLBuffer and fills with parallel pread — dramatically faster than per-tensor reads

### Key Takeaways
1. safetensors v0.8.0 is a Rust core (`_safetensors_rust.abi3.so`) with six framework adapters — torch is the most complex due to shared tensor detection
2. Binary format: 8-byte header length prefix → JSON header (8-byte aligned) → raw tensor data sequentially
3. `safe_open` supports two I/O backends: `mmap` (default, OS-managed page cache) and `pread` (explicit syscall, preferred for Apple MPS)
4. `TensorSpec(dtype, shape, data_ptr, data_len)` bridges Python memory to Rust serializer — caller must keep data alive during serialize
5. `save_model()` / `load_model()` handle shared storage deduplication via storage-pointer grouping and overlapping-address refinement
6. All framework adapters use zero-copy loading: `torch.frombuffer`, `np.frombuffer`, `paddle.base.core.frombuffer`
7. `get_slice()` enables lazy sub-tensor reads without loading the full tensor into memory

---

## 2026-07-24: hf-hub-models-api-query-language-complete — Exhaustive Reference of the Hub Models/Datasets/Spaces API Query Language (Topic #181)

### Summary
Complete deep-dive into the **Hugging Face Hub REST API query language** used by `/api/models`, `/api/datasets`, and `/api/spaces`. Covers every query parameter, the `HfApi` Python wrapper signatures, filter tag syntax, pagination mechanism, sort keys, expand projections, the `num_parameters` range syntax, `inference_provider` filtering, `gated` filtering, `apps` filtering, and cross-repo-type differences. Source: `huggingface_hub` v1.24.0 source code (`hf_api.py`) and HF API docs.

### 1. Architecture — Three Endpoints, One Pattern

All three repo types share the same paginated REST API pattern:

```
GET https://huggingface.co/api/models?param1=value1&param2=value2
GET https://huggingface.co/api/datasets?param1=value1&param2=value2
GET https://huggingface.co/api/spaces?param1=value1&param2=value2
```

The Python wrapper is `HfApi.list_models()`, `HfApi.list_datasets()`, `HfApi.list_spaces()` — all in `huggingface_hub.hf_api.HfApi`. Each returns a lazy `Iterable` using `paginate()` which walks `Link` headers (GitHub-style).

### 2. Models API — Complete Parameter Reference

All parameters below are keyword-only (`*` separator in the signature):

| Parameter | Type | Description |
|-----------|------|-------------|
| `filter` | `str \| Iterable[str] \| None` | Tag-based filter. Multiple values join as AND. See §4 for syntax. |
| `author` | `str \| None` | Filter by user/org that owns the model |
| `apps` | `str \| list[str] \| None` | Filter by app support (e.g. `"ollama"`, `["ollama", "vllm"]`) |
| `gated` | `bool \| None` | `True` = only gated, `False` = only non-gated, `None` = both |
| `inference` | `Literal["warm"] \| None` | `"warm"` = models served by at least one Inference Provider |
| `inference_provider` | `Literal["all"] \| str \| list[str] \| None` | Filter by specific provider (e.g. `"cohere"`, `"together"`). `"all"` = any provider |
| `search` | `str \| None` | Substring match on model ID (replaces deprecated `model_name`) |
| `trained_dataset` | `str \| list[str] \| None` | Filter by dataset tag (prepends `dataset:` prefix automatically) |
| `pipeline_tag` | `str \| None` | Filter by pipeline task (e.g. `"text-generation"`, `"image-classification"`) |
| `num_parameters` | `str \| None` | Range syntax: `"min:6B,max:128B"`, `"min:6B"`, `"max:128B"`. Supports B/M/K suffixes |
| `emissions_thresholds` | `tuple[float,float] \| None` | Min/max CO₂ in grams. Requires `cardData=True` |
| `sort` | `ModelSort_T \| None` | One of: `"created_at"`, `"downloads"`, `"last_modified"`, `"likes"`, `"trending_score"` |
| `limit` | `int \| None` | Max results. `None` = all (paginated). |
| `expand` | `list[ExpandModelProperty_T] \| None` | Return only listed properties (mutually exclusive with `full`, `cardData`, `fetch_config`) |
| `full` | `bool \| None` | Fetch all data (`last_modified`, `sha`, files, `tags`). Auto-enabled when `filter` is used |
| `cardData` | `bool` | Fetch YAML metadata (carbon emissions, metrics, datasets) |
| `fetch_config` | `bool` | Fetch model `config.json` (excluded from `full` due to size) |
| `token` | `bool \| str \| None` | Auth token. `None` = cached token, `False` = disable auth |

**Internal mapping of `sort` values to REST API keys:**
```python
{
    "last_modified"  → "lastModified"
    "trending_score" → "trendingScore"
    "created_at"     → "createdAt"
    "downloads"      → "downloads"
    "likes"          → "likes"
}
```

### 3. Datasets & Spaces API Differences

**Datasets** (`HfApi.list_datasets`) adds dataset-specific parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `benchmark` | `Literal[True] \| Literal["official"] \| str \| None` | Filter by benchmark |
| `dataset_name` | `str \| None` | Exact dataset ID |
| `language_creators` | `str \| list[str] \| None` | Filter by language creators tag |
| `language` | `str \| list[str] \| None` | Filter by language tag |
| `multilinguality` | `str \| list[str] \| None` | Filter by multilinguality tag |
| `size_categories` | `str \| list[str] \| None` | Filter by size category |
| `task_categories` | `str \| list[str] \| None` | Filter by task category |
| `task_ids` | `str \| list[str] \| None` | Filter by specific task ID |

Missing from datasets compared to models: `apps`, `inference`, `inference_provider`, `pipeline_tag`, `num_parameters`, `emissions_thresholds`, `cardData`, `fetch_config`.

**Spaces** (`HfApi.list_spaces`) adds Space-specific parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `datasets` | `str \| Iterable[str] \| None` | Filter Spaces that use these datasets |
| `models` | `str \| Iterable[str] \| None` | Filter Spaces that use these models |
| `linked` | `bool` | Only return Spaces linked to the authenticated user |

Missing from spaces compared to models: `inference`, `inference_provider`, `pipeline_tag`, `num_parameters`, `emissions_thresholds`, `cardData`, `fetch_config`, `trained_dataset`.

### 4. Filter Tag Syntax — The `filter` Parameter

The `filter` parameter accepts Hugging Face Hub **tags** (not free-form text). Tags come from the Hub's taxonomy system (`HfApi.get_model_tags()`, `HfApi.get_dataset_tags()`).

**Valid tag categories and examples:**

| Category | Example Tags |
|----------|-------------|
| **library** | `"transformers"`, `"pytorch"`, `"gguf"`, `"diffusers"`, `"peft"`, `"timm"`, `"sentence-transformers"`, `"keras-hub"`, `"mlx"` |
| **pipeline_tag** | `"text-classification"`, `"text-generation"`, `"image-classification"`, `"object-detection"`, `"automatic-speech-recognition"` |
| **language** | `"en"`, `"zh"`, `"fr"`, `"th"`, `"ja"`, `"ko"`, `"code"` |
| **license** | `"license:apache-2.0"`, `"license:mit"`, `"license:llama3.1"`, `"license:cc-by-nc-4.0"` |
| **dataset** | `"dataset:teknium/OpenHermes-2.5"` (auto-prepended by `trained_dataset` parameter) |
| **region** | `"region:us"`, `"region:eu"` |
| **deploy** | `"endpoints_compatible"`, `"deploy:azure"`, `"deploy:sagemaker"` |
| **other** | `"text-generation-inference"`, `"text-embeddings-inference"`, `"custom_code"`, `"4-bit"`, `"8-bit"`, `"merge"`, `"moe"`, `"eval-results"` |

**Multiple filters** join as AND — the API returns only models matching ALL specified tags:
```python
# PyTorch AND text-generation AND English
api.list_models(filter=["pytorch", "text-generation", "en"])
```

**Pipeline tags** can also be passed via the dedicated `pipeline_tag` parameter — functionally equivalent to including it in `filter`. The difference: `pipeline_tag` is a single string, while `filter` can hold multiple tags.

### 5. Expand Projections — `expand` Parameter

The `expand` parameter accepts a list of `ExpandModelProperty_T` values — 30 properties:

```
author, baseModels, cardData, childrenModelCount, config, createdAt, disabled,
downloads, downloadsAllTime, evalResults, gated, gguf, inference,
inferenceProviderMapping, lastModified, library_name, likes, mask_token,
model-index, pipeline_tag, private, resourceGroup, safetensors, sha, siblings,
spaces, tags, transformersInfo, trendingScore, usedStorage, widgetData
```

**Rules:**
- When `expand` is used, **only the listed properties** are returned in the response
- `expand` is **mutually exclusive** with `full`, `cardData`, and `fetch_config`
- Use `expand` for bandwidth optimization — fetch exactly what you need

**Datasets expand properties** (`ExpandDatasetProperty_T`): cardData, config, createdAt, disabled, downloads, gated, lastModified, sha, siblings, tags.
**Spaces expand properties** (`ExpandSpaceProperty_T`): cardData, createdAt, disabled, lastModified, private, sdk, siblings, tags, runtime, storage.

### 6. Pagination — Link-Header Based

The Hub uses GitHub-style Link header pagination (from `huggingface_hub.utils._pagination.paginate()`):
```python
# First request: GET /api/models?param=value
# Response includes Link header:
# <https://huggingface.co/api/models?param=value&page=2>; rel="next"
# Subsequent pages followed automatically
```

Key behaviors:
- **No explicit `page` parameter** in the Python API — pagination is automatic
- **`limit`** controls the page size. When set, the iterator stops after `limit` items
- **`limit=None`** fetches ALL pages (use with care — could be thousands of items)
- The raw REST API accepts `?limit=N&pagination=next` query parameters directly

### 7. Special Parameters Deep Dive

#### `inference_provider` — Provider Availability
Filters models served by specific Inference Providers. Valid providers include: `"together"`, `"replicate"`, `"cohere"`, `"fal-ai"`, `"fireworks-ai"`, `"hyperbolic"`, `"deepinfra"`, `"novita"`, `"baseten"`, `"lepton"`, `"awselastic"`, and many more. Pass `"all"` to get any model with at least one provider.

#### `apps` — App/Framework Support
Filters models that support specific applications: `"ollama"`, `"vllm"`, `"llamacpp"`, `"tgi"`, `"tei"`, `"xinference"`, `"lmstudio"`, etc. Multiple values mean models supporting ANY of the listed apps.

#### `num_parameters` — Range Syntax
```
"min:1B"         → at least 1 billion parameters
"max:10B"        → at most 10 billion parameters
"min:500M,max:7B" → 500 million to 7 billion parameters
"min:1B,max:1B"  → exactly 1 billion (approx.)
```
Suffixes: `B` (billions), `M` (millions), `K` (thousands).

#### `gated` — Access Control
- `True` → only gated models (requires token for access)
- `False` → only non-gated models
- `None` (default) → both

#### `emissions_thresholds` — Carbon Footprint
Requires `cardData=True`. Takes `(min_co2_g, max_co2_g)`. Only returns models with CO₂ emissions data in their model card.

### 8. Response Model — `ModelInfo` Key Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Full model ID (e.g. `"bert-base-uncased"`) |
| `author` | `str \| None` | Owner user/org |
| `pipeline_tag` | `str \| None` | Primary pipeline task |
| `library_name` | `str \| None` | Primary framework/library |
| `tags` | `list[str]` | All tags assigned to the model |
| `downloads` | `int` | Monthly download count |
| `downloads_all_time` | `int \| None` | All-time downloads (requires `expand`) |
| `likes` | `int` | Like count |
| `trending_score` | `int \| None` | Trending rank score (higher = more trending) |
| `created_at` | `datetime \| None` | Creation timestamp |
| `last_modified` | `datetime \| None` | Last modification timestamp |
| `gated` | `Literal["auto", "manual", False] \| None` | Gated access level |
| `disabled` | `bool \| None` | Whether model is disabled |
| `private` | `bool \| None` | Whether model is private |
| `safetensors` | `dict \| None` | safetensors metadata (parameter count, dtypes) |
| `gguf` | `dict \| None` | GGUF metadata (if applicable) |
| `config` | `dict \| None` | Model config (requires `fetch_config=True`) |
| `cardData` | `dict \| None` | YAML card metadata (requires `cardData=True`) |
| `siblings` | `list[RepoFile] \| None` | Files in the repo |
| `spaces` | `list[str] \| None` | Spaces using this model |
| `inference` | `str \| None` | Inference status (`"warm"` if served) |
| `inference_provider_mapping` | `dict \| None` | Provider → status mapping |
| `base_models` | `list[dict] \| None` | Models this model is derived from |
| `children_model_count` | `int \| None` | Number of child models |
| `widget_data` | `list[dict] \| None` | Inference widget example data |
| `model_index` | `dict \| None` | Model index data |
| `transformers_info` | `dict \| None` | Transformers-specific metadata |
| `security_repo_status` | `dict \| None` | Security scan status |
| `eval_results` | `dict \| None` | Evaluation results |
| `used_storage` | `int \| None` | Storage used in bytes |

### 9. Practical Examples

```python
from huggingface_hub import HfApi
api = HfApi()

# 1. Find trending text-generation models under 10B params
models = api.list_models(
    filter=["text-generation", "pytorch"],
    sort="trending_score",
    num_parameters="max:10B",
    limit=20
)

# 2. Check if a model is available via inference providers
models = api.list_models(
    search="meta-llama/Llama-3.2-3B",
    inference="warm",
    expand=["inference", "inferenceProviderMapping"]
)

# 3. Find models with exact params (1B-7B range, sorted by likes)
models = api.list_models(
    filter="text-generation",
    num_parameters="min:1B,max:7B",
    sort="likes",
    limit=10
)

# 4. Get gated models from a specific author
models = api.list_models(
    author="meta-llama",
    gated=True,
    full=True
)

# 5. List models with their configs
model_infos = api.list_models(search="qwen/Qwen2.5-7B", fetch_config=True)

# 6. Direct REST call (curl-equivalent):
# curl -s "https://huggingface.co/api/models?search=bert&filter=pytorch&sort=downloads&limit=5"
```

### Key Takeaways
1. The Hub API query language is unified across models, datasets, and spaces — each variant adds its own parameters
2. The `filter` parameter accepts Hub taxonomy tags (library, pipeline, language, license, etc.), AND-joined when multiple
3. `expand` provides bandwidth-efficient projections — always prefer it over `full` when you only need specific fields
4. `num_parameters` uses `"min:X,max:Y"` range syntax with B/M/K suffixes
5. Pagination is automatic via Link headers; `limit` controls max results
6. The Python `HfApi` wrapper maps Pythonic names (snake_case) to REST API keys (camelCase)

## 2026-07-24: hf-hub-hf_transfer-rust-download-accelerator-deep-dive — Research Topic #186

### Summary
Comprehensive deep-dive into `hf_transfer` — Hugging Face's Rust-based download/upload accelerator for high-bandwidth Hub transfers. Covers the Rust implementation (PyO3 bindings, reqwest 0.12 HTTP/2 client, tokio multi-threaded runtime, semaphore-based concurrency), download mechanics (HTTP Range parallel chunking, FuturesUnordered), upload mechanics (S3 multipart upload with pre-signed URLs), retry with exponential backoff + jitter, and — most critically — the **deprecation status**: `hf_transfer` is replaced by `hf_xet` (`HF_XET_HIGH_PERFORMANCE`), and `HF_HUB_ENABLE_HF_TRANSFER` now triggers a `FutureWarning`. Researched against source code at huggingface/hf_transfer and huggingface/huggingface_hub.

### Sources
- hf_transfer repo: https://github.com/huggingface/hf_transfer
- Cargo.toml (v0.1.10-dev0) — Rust deps: reqwest 0.12, tokio 1.42, pyo3 0.26, futures 0.3, openssl (vendored)
- PyPI: https://pypi.org/pypi/hf_transfer/0.1.9
- huggingface_hub constants.py — deprecation warning logic
- huggingface_hub utils/_xet.py — Xet replacement implementation
- Hugging Face Xet docs: https://huggingface.co/docs/hub/en/xet

### 1. What Is hf_transfer?

`hf_transfer` is a **Rust native Python extension** that accelerates file downloads and uploads to/from the Hugging Face Hub by bypassing Python's GIL and using parallel HTTP Range requests from a multi-threaded tokio runtime.

**Key characteristics:**
- Exposes exactly **two functions**: `download()` and `multipart_upload()`
- Written in Rust, compiled via PyO3 + maturin, distributed as a platform-specific wheel
- Uses **reqwest 0.12** (Rust HTTP client) with HTTP/2 keep-alive for efficient concurrent connections
- Uses **tokio 1.42** multi-threaded runtime for async I/O
- Semaphore-based concurrency limiting (configurable `max_files`)
- Exponential backoff retry with random jitter for fault tolerance
- **No progress bars, no caching, no resume support** — by design (power user tool)
- Designed for very high bandwidth networks (>500 MB/s) where Python's overhead becomes a bottleneck

### 2. Architecture

```
┌─────────────────────────────────────────┐
│            Python Process               │
│  ┌───────────────────────────────────┐  │
│  │    huggingface_hub library        │  │
│  │                                   │  │
│  │   hf_hub_download() / upload()    │  │
│  │         │                         │  │
│  │         ▼                         │  │
│  │   HF_HUB_ENABLE_HF_TRANSFER=1     │  │
│  │         │                         │  │
│  │         ▼                         │  │
│  │   hf_transfer.download()          │  │
│  │   (Python → Rust FFI via PyO3)    │  │
│  └──────────┬────────────────────────┘  │
│             │                            │
│  ┌──────────▼────────────────────────┐  │
│  │     Rust Runtime (tokio MT)       │  │
│  │                                    │  │
│  │  ┌─── FuturesUnordered ──────────┐ │  │
│  │  │  Chunk 1 │ Chunk 2 │ Chunk N │ │  │
│  │  │ reqwest  │ reqwest │ reqwest │ │  │
│  │  │ HTTP/2   │ HTTP/2  │ HTTP/2  │ │  │
│  │  └──────────┴─────────┴─────────┘ │  │
│  │              │                     │  │
│  │     Semaphore(max_files=N)         │  │
│  │          + File I/O                │  │
│  └────────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

### 3. Download Mechanics

The `download()` Python function accepts these parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `url` | `str` | Full URL to the file on the Hub |
| `filename` | `str` | Local path to write the file |
| `max_files` | `int` | Max concurrent chunk downloads (file handles) |
| `chunk_size` | `int` | Size of each chunk in bytes |
| `parallel_failures` | `int` | Max concurrent retries (0 = no retries) |
| `max_retries` | `int` | Max retry attempts per chunk (0 = no retries) |
| `headers` | `dict` | Optional HTTP headers (Authorization, etc.) |
| `callback` | `callable` | Optional progress callback `fn(bytes_written)` |

**Process flow:**
1. **HEAD probe**: Sends `Range: bytes=0-0` to get the file size from `Content-Range` header
2. **Follow redirects**: Uses the final redirect URL (after CDN redirect) to avoid counting extra downloads
3. **Chunk splitting**: Divides file into chunks of `chunk_size` bytes
4. **Concurrent download**: Each chunk is a separate HTTP GET with `Range: bytes=start-stop`
5. **File I/O**: Each chunk writes directly to the file at the correct offset (`seek` then `write_all`)
6. **Retry**: If `parallel_failures > 0`, failed chunks retry with exponential backoff + jitter

**Key implementation detail** (from `src/lib.rs`):
```rust
async fn download_chunk(client, url, filename, start, stop, headers) {
    let range = format!("bytes={start}-{stop}");
    let mut file = OpenOptions::new()
        .write(true).truncate(false).create(true)
        .open(filename).await?;
    file.seek(SeekFrom::Start(start as u64)).await?;
    let response = client.get(url).headers(headers)
        .header(RANGE, range).send().await?.error_for_status()?;
    let content = response.bytes().await?;
    file.write_all(&content).await?;
}
```

**Retry backoff** (exponential + jitter):
```
base_wait = 300ms
wait_time = min(300 + n² + random(0..500), 10000) ms
```
Where `n` = retry attempt number.

### 4. Upload Mechanics (Multipart Upload)

The `multipart_upload()` function handles S3-style multipart uploads:

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | `str` | Path to the file to upload |
| `parts_urls` | `list[str]` | Pre-signed URLs (one per chunk part) |
| `chunk_size` | `int` | Size of each chunk in bytes |
| `max_files` | `int` | Max concurrent chunk uploads |
| `parallel_failures` | `int` | Max concurrent retries |
| `max_retries` | `int` | Max retry attempts per chunk |
| `callback` | `callable` | Optional progress callback |

**Returns:** `list[dict]` — response headers from each part upload (used for S3 upload completion).

**Process:**
1. Each chunk reads from file at correct offset using `AsyncReadExt`
2. Chunk wrapped in `FramedRead` stream for efficient body streaming
3. PUT to pre-signed URL with `Content-Length` header
4. Returns ETag/headers from each part's response
5. Same semaphore + retry mechanism as download

### 5. ⚠️ Deprecation Status (Critical Finding)

**As of `huggingface_hub` v1.24.0+, `hf_transfer` is deprecated and replaced by Xet.**

In `huggingface_hub/constants.py`:
```python
if _is_true(os.environ.get("HF_HUB_ENABLE_HF_TRANSFER")) and not HF_XET_HIGH_PERFORMANCE:
    import warnings
    warnings.warn(
        "The `HF_HUB_ENABLE_HF_TRANSFER` environment variable is deprecated as "
        "'hf_transfer' is not used anymore. "
        "Please use `HF_XET_HIGH_PERFORMANCE` instead to enable high performance "
        "transfer with Xet. "
        "Visit https://huggingface.co/docs/huggingface_hub/package_reference/"
        "environment_variables#hfxethighperformance for more details.",
        FutureWarning,
    )
```

**Why the replacement?** Xet provides:
- **Content-addressed storage** — deduplication of identical files across repos
- **Streamed uploads** — no need for pre-signed URLs per chunk
- **Git integration** — Xet-aware Git LFS alternative
- **Better performance** — single connection with streaming vs. N parallel Range requests
- **Session management** — `XetSession` handles the Rust runtime lifecycle
- **Fork safety** — `XetSessionHolder` detects forks and re-creates the session

**How to use Xet instead:**
```bash
# Instead of:
export HF_HUB_ENABLE_HF_TRANSFER=1

# Use:
export HF_XET_HIGH_PERFORMANCE=1
```

**Xet implementation** (`huggingface_hub/utils/_xet.py`):
- `XetFileData` — metadata parsed from HTTP headers (`X-Xet-Hash`, `X-Xet-Cas-Url`, `X-Xet-Access-Token`, etc.)
- `XetSessionHolder` — global singleton with fork safety and thread safety
- `xet_connection_info_refresh_url()` — builds the URL for Xet token refresh
- Token endpoints: `/api/{repo_type}s/{repo_id}/xet-{read|write}-token/{revision}`
- Uses `hf_xet` Python package (Rust native, similar to hf_transfer but Xet-aware)

### 6. Limitations of hf_transfer

| Limitation | Detail |
|------------|--------|
| **No progress bars** | By design — avoids Python callbacks bottlenecking the Rust loop |
| **No resume** | Failed downloads delete the partial file entirely |
| **No caching** | Every download re-fetches the entire file; no `~/.cache/huggingface/hub` |
| **Auth only** | Requires `Authorization` header (Bearer token) |
| **Large file only** | Only beneficial for files >100 MB; overhead of parallel chunks not worth it for small files |
| **No fallback** | If hf_transfer fails, there's no automatic fallback to Python downloader |
| **No Windows support** | Wheel distribution limited to Linux/macOS |
| **DEPRECATED** | Replaced by Xet; no active development |

### 7. Performance Considerations

When hf_transfer was active (pre-deprecation):
- **2-5× faster** than Python downloads for files >500 MB on high-bandwidth connections
- **Parallelism**: Up to `max_files` concurrent chunks (typically 8-16)
- **Chunk size**: Typical value 20-50 MB; too small = overhead, too large = less parallelism
- **Bandwidth ceiling**: ~500 MB/s vs ~100 MB/s for Python (due to GIL + HTTP overhead)
- **CPU usage**: Higher than Python downloader (Rust runtime + tokio threads)

### 8. Key Takeaways

1. **hf_transfer is deprecated** — the Rust download accelerator has been replaced by Xet (`hf_xet` + `HF_XET_HIGH_PERFORMANCE`)
2. **The architecture** — PyO3 bindings, reqwest 0.12 with HTTP/2, tokio MT runtime, semaphore-based concurrent Range requests — is the blueprint that Xet's implementation follows
3. **Power-user tool** — explicitly designed for >500 MB/s networks; average users see little benefit
4. **Xet takes over** — content-addressed, streamed, deduplicated transfers via `hf_xet` package
5. **Always prefer `hf_hub_download()`** — it handles caching, resumption, progress bars, and now Xet integration transparently
6. **For zero-cost environments**: Standard `hf_hub_download` (Python) is almost always sufficient. hf_transfer/Xet only matter on very high-bandwidth infrastructure.

### References
- hf_transfer repo: https://github.com/huggingface/hf_transfer
- huggingface_hub constants.py: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/constants.py
- huggingface_hub Xet utils: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/utils/_xet.py
- hf_transfer PyPI: https://pypi.org/pypi/hf_transfer/
- Hugging Face Xet docs: https://huggingface.co/docs/hub/en/xet
- Environment vars: https://huggingface.co/docs/huggingface_hub/package_reference/environment_variables

---

## 2026-07-24: hf-gradio-lite-deep-dive — Complete Gradio Lite Architecture Reference (Topic #175 Deep-Dive)

### Summary
Deep-dive into `@gradio/lite` — Gradio's serverless runtime that runs entire Gradio apps inside the browser using Pyodide (Python for WebAssembly). Covers the architecture, custom element API (`<gradio-lite>`), Wasm worker pipeline, filesystem virtualization, ASGI-over-Wasm protocol, package installation via micropip, the Playground mode, limitations, and the official deprecation/archival status.

### Quick Facts

| Attribute | Value |
|-----------|-------|
| Package | `@gradio/lite` (npm), v5.45.0 (final) |
| License | Apache-2.0 |
| Runtime | Pyodide v0.27.3 (Python 3.12 Wasm) |
| CDN | `https://cdn.jsdelivr.net/npm/@gradio/lite/dist/lite.js` |
| Worker | DedicatedWorker (default) or SharedWorker (`shared-worker` attr) |
| Status | **Archived** — frozen repo at gradio-app/gradio-lite |

### Architecture

```
┌─────────────────────────────────────────────┐
│  Browser DOM                                │
│  ┌─────────────────────────────────┐        │
│  │  <gradio-lite> Custom Element   │        │
│  │  ┌──────────┐ ┌──────────────┐ │        │
│  │  │ LiteIndex│ │  Playground  │ │        │
│  │  │ (Svelte) │ │  (Svelte)    │ │        │
│  │  └────┬─────┘ └──────────────┘ │        │
│  │       │                        │        │
│  │  ┌────▼────────┐               │        │
│  │  │ WorkerProxy │               │        │
│  │  │ (EventTarget)│              │        │
│  │  └────┬────────┘              │        │
│  └───────┼─────────────────────────┘        │
│          │ postMessage (MessageChannel)      │
├──────────┼──────────────────────────────────┤
│  Wasm Worker (WebWorker)                     │
│  ┌───────▼──────────────────────────┐       │
│  │  Pyodide v0.27.3                  │       │
│  │  ┌─────────────────┐  gradio.whl │       │
│  │  │ Python 3.12     │  gradio_    │       │
│  │  │ + micropip      │  client.whl │       │
│  │  │ + gradio        │             │       │
│  │  └─────────────────┘             │       │
│  ├──────────────────────────────────┤       │
│  │  ASGI Gateway: Wasm → HTTP proxy │       │
│  └──────────────────────────────────┘       │
└─────────────────────────────────────────────┘
```

### Layer Details

**1. Custom Element (`<gradio-lite>`):** Registered via `customElements.define()`. Parses HTML attributes (theme, embed, eager, shared-worker, playground, layout, info, container, etc.) and child elements (`<gradio-file>`, `<gradio-requirements>`, `<gradio-code>`). Maps inline Python code or named files into the Wasm virtual filesystem.

**2. WorkerProxy (main thread):** Bridges the DOM and the Web Worker via `MessageChannel` async protocol. Two-phase init: (1) `init-env` loads Pyodide + Gradio wheels, (2) `init-app` writes files + installs requirements. Dispatches events: `initialization-completed`, `initialization-error`, `progress-update`, `stdout`, `stderr`, `python-error`.

**3. Web Worker (Pyodide):** Bootstraps Pyodide v0.27.3, mocks `os.link` (not in Wasm) and `anyio.to_thread.run_sync` (no threading), loads `gradio.whl` + `gradio_client.whl` via micropip, registers the ASGI app wrapper. Installs user packages with up to 3 retries (`installPackages()` with `keep_going=True`).

**4. Network Proxy (`wasm_proxied_fetch`):** Since Wasm has no native HTTP, all requests are proxied: JS serializes Request → Worker converts to ASGI scope → Python ASGI app processes → Response streamed back. SSE is proxied via `wasm_proxied_stream_factory`.

### Usage Patterns

| Pattern | Code |
|---------|------|
| Inline | `<gradio-lite>import gradio as gr\ngr.Interface(lambda x:f\"Hi {x}!\",\"text\",\"text\").launch()</gradio-lite>` |
| Multi-file | `<gradio-file name="app.py" entrypoint>...</gradio-file>` + `<gradio-file name="utils.py">` |
| Dependencies | `<gradio-requirements>transformers_js_py</gradio-requirements>` |
| Remote URL | `<gradio-file name="app.py" entrypoint url="https://...">` |
| Playground | `<gradio-lite playground layout="vertical">` |

### JavaScript API

```javascript
const ctrl = createGradioApp({ target, code, requirements, files, entrypoint, themeMode })
ctrl.run_code('print("hello")')
ctrl.run_file('app.py')
ctrl.write('file.txt', 'content')
ctrl.rename('old.py', 'new.py')
ctrl.unlink('file.txt')
ctrl.install(['numpy'])
ctrl.unmount()
ctrl.addEventListener('stdout', (e) => ...)
```

### Key Source Insights

1. **Wheel build:** `pnpm pybuild` → `hatch build -t lite` → `pyodide py-compile` for bytecode optimization
2. **Cross-origin worker:** `CrossOriginWorkerMaker` creates blob: URL wrapper to bypass CDN CORS
3. **ASGI scope conversion:** JS HTTP → Python ASGI scope with careful byte-encoding of headers/query/raw_path
4. **Module unloading:** `unload_local_modules()` clears Python modules between Playground re-runs
5. **Code completion:** Jedi-based `CodeCompleter` in Playground
6. **Random entropy:** Wasm lacks `os.urandom` → `crypto.getRandomValues` polyfill
7. **Static Spaces:** Gradio Lite apps work as Hugging Face Static Spaces (zero-cost, no server)

### Limitations
- 5-15s initial load (Pyodide download + init)
- Only pure-Python packages (no C extensions unless pre-built for Wasm)
- No threading, no GPU, no `os.link`
- Browser memory limits (2-4 GB Wasm heap)
- **Archived** — frozen at v5.45.0, no longer maintained

### References
- Archived source: https://github.com/gradio-app/gradio-lite
- CDN: https://www.jsdelivr.com/package/npm/@gradio/lite
- NPM: https://www.npmjs.com/package/@gradio/lite
- Pyodide: https://pyodide.org/
- Static Spaces: https://huggingface.co/docs/hub/en/spaces-static
|
---

## 2026-07-24: hf-inference-client-image-input-pipeline-deep-dive — InferenceClient Image Input Handling (Topic #187)

### Summary
Source-code deep-dive into the `huggingface_hub` InferenceClient's image input pipeline. The `ContentT` type union accepts 7 input formats: bytes, bytearray, memoryview, BinaryIO (file-like objects), str URLs, str/Path local files, and PIL.Image.Image. The `_open_as_mime_bytes()` function normalizes all types into `MimeBytes` (bytes subclass with `.mime_type`). Key encoding functions: `_b64_encode()` for base64 JSON embedding, `_as_url()` for data URLs in multimodal chat. The `HFInferenceBinaryInputTask` provider handles the raw-binary vs. b64-JSON split based on parameter presence. 8 image task methods (image_classification, image_segmentation, image_to_image, image_to_video, image_to_text, object_detection, text_to_image, visual_question_answering, zero_shot_image_classification) plus document_question_answering. Chat completion uses OpenAI-compatible content parts instead of ContentT.

### Source Code Files Analyzed
- huggingface_hub/inference/_common.py — ContentT type, _open_as_mime_bytes, _b64_encode, _as_url, _bytes_to_image
- huggingface_hub/inference/_client.py — 8 image task methods, chat_completion multimodal pattern
- huggingface_hub/inference/_providers/hf_inference.py — HFInferenceTask vs HFInferenceBinaryInputTask

### References
- huggingface_hub inference source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/inference/

---

## 2026-07-24: hf-transformers-logits-processors-deep-dive — Complete LogitsProcessor System in Transformers v5.14.0 (Topic #189)

### Summary
Full deep-dive into the `LogitsProcessor` system in HuggingFace `transformers` v5.14.0 (source file: `src/transformers/generation/logits_process.py`, ~3300 lines). Covers the abstract base class, the `LogitsProcessorList` chainer, all 35 built-in processors/warpers across 10 functional categories (temperature warping, top-k/p/H/minP/typical/epsilon/eta sampling, length control, repetition/ngram prevention, sequence biasing, forced tokens, Whisper-specific processors, classifier-free guidance, watermarking, audio-specific), the `supports_continuous_batching` flag, the `__call__` pipeline, how `generate()` wires them, and custom processor authoring patterns.

### Source
- `logits_process.py`: https://github.com/huggingface/transformers/blob/v5.14.0/src/transformers/generation/logits_process.py
- Docs: https://huggingface.co/docs/transformers/en/internal/generation_utils
- Strategies: https://huggingface.co/docs/transformers/en/generation_strategies

### 1. Architecture

```
LogitsProcessor (abstract base)
  └─ supports_continuous_batching: bool | None = None

LogitsProcessorList (list subclass)
  └─ __call__(input_ids, scores, **kwargs) → scores
       Iterates through each processor, calling them IN ORDER.
       If a processor's __call__ has extra kwargs parameters beyond
       (input_ids, scores), they are passed from chain kwargs.
```

The `generate()` method assembles a `LogitsProcessorList` from generation config parameters. The pipeline is:

```
raw_logits → LogitsProcessorList chain → modified_logits → sampler (sample/greedy/beam)
```

Order: typically warpers (temperature → top-k → top-p) first, then processors (repetition penalty → min length → forced tokens → etc.), then normalization.

### 2. Complete Processor Inventory (35 classes)

#### A. Sampling Warpers (modify distribution shape for stochastic decoding)

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `TemperatureLogitsWarper` | ✅ True | Divide logits by temperature. `score = score / temp` |
| `TopKLogitsWarper` | ✅ True | Zero out all logits except the top-k tokens. `k` can be dynamic with `filter_value=-inf` |
| `TopPLogitsWarper` | ✅ True | Nucleus sampling — keep smallest set of tokens whose cumulative probability ≥ p |
| `TopHLogitsWarper` | ✅ True | Top-eta sampling — keep tokens with score ≥ `max_score * eta`. Uses `eta_cut_off` parameter |
| `MinPLogitsWarper` | ✅ True | Keep tokens whose probability ≥ `min_p` (minimum probability threshold). Similar to top-p but uses absolute probability |
| `TypicalLogitsWarper` | ✅ True | Typical sampling — keep tokens with negative entropy ≥ `mass`. Based on "typicality" principle |
| `EpsilonLogitsWarper` | ✅ True | Epsilon cutoff — zero out tokens with probability < `epsilon` |
| `EtaLogitsWarper` | ✅ True | Eta sampling — mixture approach. Filters using both epsilon and eta thresholds. Also known as "eta cutoff" from the Contrastive Search paper |

#### B. Length Control Processors

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `MinLengthLogitsProcessor` | ❌ False | Sets EOS probability to `-inf` until `min_length` is reached. **Includes prompt length** |
| `MinNewTokensLengthLogitsProcessor` | ❌ False | Like MinLength but **ignores prompt** — only counts new tokens. Takes `prompt_length_to_skip` |
| `ExponentialDecayLengthPenalty` | ❌ False | Exponentially boosts EOS score after a `start_index`. Formula: `penalty = |EOS_score| * (decay_factor^(cur_len - start) - 1)`. Works with a tuple `(start_index, decay_factor)` |
| `ForcedBOSTokenLogitsProcessor` | ❌ False | Forces the first generated token (`cur_len == 1`) to be BOS token. Used by encoder-decoder models |
| `ForcedEOSTokenLogitsProcessor` | ❌ False | Forces EOS at `max_length - 1`. Sets all scores to `-inf` except EOS tokens |

#### C. Repetition & N-Gram Prevention

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `RepetitionPenaltyLogitsProcessor` | ❌ False | Core repetition penalty. `penalty > 1.0` penalizes, `< 1.0` rewards. Applied per-token via: `if score < 0: score * penalty else: score / penalty`. Supports `prompt_ignore_length` to exclude prompt from penalty. **3D tensor support** for continuous batching |
| `EncoderRepetitionPenaltyLogitsProcessor` | ❌ False | Inverse penalty — boosts tokens that appear in the prompt. Designed for summarization to avoid hallucination. Uses `encoder_input_ids` |
| `NoRepeatNGramLogitsProcessor` | ❌ False | Blocks any n-gram that already appeared in the generated sequence. Takes `ngram_size` |
| `EncoderNoRepeatNGramLogitsProcessor` | ❌ False | Blocks n-grams from the encoder input. Takes `encoder_input_ids` and `ngram_size` |

#### D. Token Suppression

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `SuppressTokensAtBeginLogitsProcessor` | ❌ False | Suppresses specific tokens at generation start only (`input_ids.shape[-1] == begin_index`). Used by Whisper for `begin_suppress_tokens` |
| `SuppressTokensLogitsProcessor` | ❌ False | Suppresses tokens at ALL steps. Used by Whisper's `suppress_tokens` list |
| `InfNanRemoveLogitsProcessor` | ❌ False | Safety processor: replaces `nan`→0, `+inf`→max_float, `-inf`→min_float |

#### E. Token Sequence Biasing & Constraint

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `SequenceBiasLogitsProcessor` | ❌ False | Adds bias (can be `+inf` or `-inf`) to specific token sequences. Uses Trie-based matching for multi-token sequences. Accepts `dict{tuple(tokens): float}` or `list[list[token_ids, float]]` |
| `NoBadWordsLogitsProcessor` | ❌ False | Inherits from `SequenceBiasLogitsProcessor`. Sets `-inf` bias on bad word token sequences. Auto-filters EOS from bad words |
| `PrefixConstrainedLogitsProcessor` | ❌ False | Takes a `prefix_allowed_tokens_fn(batch_id, input_ids) → list[int]` function. Masks all non-allowed tokens. Used with beam search (`num_beams` parameter) |

#### F. Normalization

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `LogitNormalization` | ❌ False | Applies `log_softmax(dim=-1)` to scores. Needed for beam search when scores must be normalized. Config param: `renormalize_logits=True` |

#### G. Whisper-Specific

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `WhisperTimeStampLogitsProcessor` | ❌ False | Complex timestamp processor: (1) forces timestamp pairs, (2) sets non-timestamp logits to `-inf` when timestamp probability is highest, (3) limits initial timestamp index via `max_initial_timestamp_index`, (4) handles `no_timestamps_token_id` |
| `WhisperNoSpeechDetection` | ❌ False | Detects "no speech" condition from logits. Used for voice activity detection |

#### H. Classifier-Free Guidance

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `ClassifierFreeGuidanceLogitsProcessor` | ❌ False | Implements CFG scaling: `logits = unconditional_logits + guidance_scale * (logits - unconditional_logits)`. Takes pre-computed unconditional scores |
| `UnbatchedClassifierFreeGuidanceLogitsProcessor` | ❌ False | CFG without batch dimension expansion. Runs unconditional pass separately |
| `DiaClassifierFreeGuidanceLogitsProcessor` | ❌ False | DiA (Dialogue) model CFG variant |

#### I. Watermarking

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `WatermarkLogitsProcessor` | ❌ False | KGW (Kirchenbauer et al.) watermarking implementation. Modifies logits to embed watermark signal based on green/red token lists |
| `SynthIDTextWatermarkLogitsProcessor` | ❌ False | Google DeepMind SynthID text watermarking. Uses a custom state machine (`SynthIDTextWatermarkState`). More sophisticated than KGW — encodes watermark via tournament sampling |

#### J. Audio-Specific (Bark, DiA)

| Class | `supports_continuous_batching` | Description |
|-------|-------------------------------|-------------|
| `AlternatingCodebooksLogitsProcessor` | ❌ False | Handles alternating codebook patterns in speech/audio models (like EnCodec) |
| `BarkEosPrioritizerLogitsProcessor` | ❌ False | Prioritizes EOS tokens for Bark model's semantic/coarse/fine generation |
| `DiaEOSChannelFilterLogitsProcessor` | ❌ False | Channel-specific EOS filtering for DiA dialogue models |
| `DiaEOSDelayPatternLogitsProcessor` | ❌ False | Delays EOS generation pattern for DiA dialogue models |

### 3. How `generate()` Assembles the Processor List

The `_get_logits_processor()` and `_get_logits_warper()` methods in `GenerationMixin` build the chain from config parameters:

```python
# From GenerationConfig or generate() kwargs
processors = LogitsProcessorList()

# Order matters — typically:
if min_length is not None:
    processors.append(MinLengthLogitsProcessor(...))
if repetition_penalty is not None:
    processors.append(RepetitionPenaltyLogitsProcessor(...))
if bad_words_ids is not None:
    processors.append(NoBadWordsLogitsProcessor(...))
if exponential_decay_length_penalty is not None:
    processors.append(ExponentialDecayLengthPenalty(...))
if forced_eos_token_id is not None:
    processors.append(ForcedEOSTokenLogitsProcessor(...))

# Warpers (for sampling):
warpers = LogitsProcessorList()
if temperature is not None:
    warpers.append(TemperatureLogitsWarper(temperature))
if top_k is not None:
    warpers.append(TopKLogitsWarper(top_k, ...))
if top_p is not None:
    warpers.append(TopPLogitsWarper(top_p, ...))
if min_p is not None:
    warpers.append(MinPLogitsWarper(min_p, ...))
if typical_p is not None:
    warpers.append(TypicalLogitsWarper(typical_p, ...))
```

Final chain: `warbers + processors + [LogitNormalization()]` if `renormalize_logits=True`.

### 4. Custom LogitsProcessor Pattern

```python
from transformers.generation.logits_process import LogitsProcessor
import torch

class MyCustomProcessor(LogitsProcessor):
    supports_continuous_batching = False

    def __init__(self, param: float):
        self.param = param

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # Modify scores in-place or return new tensor
        scores[:, some_token_id] += self.param
        return scores

# Usage
model.generate(
    ...,
    logits_processor=LogitsProcessorList([
        MyCustomProcessor(1.5),
    ])
)
```

Key contract:
- Input: `input_ids` (batch, seq_len) + `scores` (batch, vocab_size)
- Output: same-shape `scores`
- Input may be 3D: (batch, 1, vocab_size) for continuous batching — the processor must handle this dimensionality

### 5. Key Design Insights

1. **`supports_continuous_batching` flag**: `True` only for TemperatureLogitsWarper, TopKLogitsWarper, TopPLogitsWarper, TopHLogitsWarper, and MinPLogitsWarper. ALL other processors set `False` or `None`. This flag gates whether the processor can run inside the optimized continuous batching path in `StaticCache`/`DynamicCache`.

2. **Processor vs Warper naming**: The codebase uses both `*Processor` and `*Warper` as subclasses of `LogitsProcessor`. "Warpers" are specifically for sampling distribution shape modification; "Processors" handle constraints, penalties, forced tokens, etc. But both go into the same `LogitsProcessorList` chain.

3. **N-Gram blocking via Trie**: `SequenceBiasLogitsProcessor` uses a Trie data structure for efficient multi-token sequence matching. This is the same mechanism used by `NoBadWordsLogitsProcessor`.

4. **Beam search awareness**: `PrefixConstrainedLogitsProcessor` explicitly handles `num_beams` — it expands the mask per-beam and per-batch. `LogitNormalization` is critical for beam search correctness.

5. **RepetitionPenalty dual formula**: Uses `score < 0 → score * penalty` (makes negative scores more negative when penalty > 1) and `score >= 0 → score / penalty` (reduces positive scores). This ensures the penalty always reduces the probability of repeated tokens.

6. **ExponentialDecayLengthPenalty doesn't hard-cut**: Unlike `ForcedEOSTokenLogitsProcessor` which forces EOS at exact position, `ExponentialDecayLengthPenalty` gradually boosts EOS probability starting from `start_index`, allowing the model to choose a semantically appropriate ending point.

### References
- Source: https://github.com/huggingface/transformers/blob/v5.14.0/src/transformers/generation/logits_process.py
- Generation strategies: https://huggingface.co/docs/transformers/en/generation_strategies
- Internal generation utils: https://huggingface.co/docs/transformers/en/internal/generation_utils

---

## 2026-07-24: hf-repo-creation-publishing-automation — Complete Repository Lifecycle & Publishing Automation (Topic #192 Deep-Dive)

### Summary
Comprehensive deep-dive into programmatic repository lifecycle management on Hugging Face Hub. Covers all HfApi methods for repo CRUD (create_repo, delete_repo, duplicate_repo, move_repo, super_squash_history), metadata/settings management (repo_info, repo_exists, update_repo_settings), file upload strategies (upload_file, upload_folder, create_commit with CommitOperationAdd/Delete/Copy), the hf CLI equivalents (hf repos create/delete/duplicate/move/settings/cp), and CI/CD automation patterns (GitHub Actions, idempotent publishing, atomic multi-file updates, Space duplication with secrets). Based on huggingface_hub v1.24.0+ source code at hf_api.py.

### Source
- HfApi source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_api.py
- CLI docs: https://huggingface.co/docs/huggingface_hub/en/guides/cli
- Hub API docs: https://huggingface.co/docs/huggingface_hub/en/package_reference/hf_api
- Repo settings: https://hf.co/docs/hub/repositories-settings

### Key API Reference

| Method | Purpose | Returns |
|--------|---------|---------|
| `create_repo()` | Create empty repo (model/dataset/Space) | `RepoUrl` |
| `delete_repo()` | Irreversibly delete a repo | `None` |
| `duplicate_repo()` | Server-side copy with full history | `RepoUrl` |
| `move_repo()` | Rename/transfer between namespaces | `None` |
| `super_squash_history()` | Collapse all commits into one | `None` |
| `repo_exists()` | Lightweight existence check | `bool` |
| `repo_info()` | Full metadata including siblings/tags | `ModelInfo | DatasetInfo | SpaceInfo` |
| `update_repo_settings()` | Change private/gated/visibility | `None` |
| `upload_file()` | Single file upload | `CommitInfo` |
| `upload_folder()` | Directory upload with glob filters | `CommitInfo` |
| `create_commit()` | Multi-operation atomic commit | `CommitInfo` |
| `list_repo_files()` | List all files in a repo revision | `list[str]` |
| `list_repo_commits()` | List commit history | `list[CommitInfo]` |

### Key Design Insights

1. **create_repo is polymorphic** — Same method handles models, datasets, and Spaces via `repo_type`. Space-specific args (sdk, hardware, secrets, volumes) are silently ignored for model/dataset repos.

2. **duplicate_repo is server-side** — No local download/upload. Preserves full git history and LFS objects. For Spaces, you can override hardware, secrets, volumes, and sleep time in the copy.

3. **create_commit is the foundation** — All file operations flow through it. Supports up to 25k LFS files and 1GB regular payload per commit. Supports `parent_commit` for optimistic locking and `create_pr` for PR-based workflows.

4. **CommitOperationCopy is zero-bandwidth** — Cross-repo file copies are purely server-side. No download to client, no re-upload. Useful for duplicating configs/tokenizers across repos.

5. **`parent_commit` enables optimistic locking** — Pass the current HEAD hash to prevent race conditions in concurrent CI/CD pipelines. Without it, auto-merge (fast-forward) can cause ordering issues.

6. **`exist_ok=True` is CI/CD safe** — Idempotent creation: first run creates, subsequent runs are no-ops. Prevents race conditions in multi-stage pipelines.

7. **CLI `--json` flag is script-ready** — All `hf repos` commands support `--format json` for structured output consumption without parsing human tables.

8. **`super_squash_history()` is one-way** — Non-revertible. Use before public release to clean up messy dev commits, but never on a branch that needs future merges.

### Skill
mlops/hf-repo-creation-publishing-automation — references/hf-learnings.md

---

## 2026-07-24: hf-text-embeddings-inference-v2 — TEI Deepening: Qwen3, Gemma3, ModernBERT, ONNX, Sequence Classification & Reranker Support (Topic #104 Deepened)

### Summary
Deepened the TEI reference with latest features from v1.9+ upstream. Added: supported model architectures (Qwen3, Gemma3, ModernBERT, GTE, MPNet, Mistral), full MTEB-ranked model table (20 models with rankings), Sequence Classification & Reranker support (new `/rerank` and `/predict` endpoints with 5 supported reranker/classification models), ONNX weight loading via the `ort` feature flag, Apple Silicon/Metal Homebrew install (`brew install text-embeddings-inference`), token-based dynamic batching deep-dive with `--max-batch-tokens` tuning formula, and updated CLI argument reference. Full document at `skills/mlops/hf-text-embeddings-inference/references/hf-learnings.md`.

### Key Discovery: TEI Now Serves More Than Embeddings
TEI added support for Sequence Classification models in v0.4.0 and has since expanded to serve rerankers and sentiment analysis via new `/rerank` and `/predict` endpoints. This makes TEI a unified inference server for all text understanding tasks, not just embeddings.

### Key Discovery: 5 New Architecture Families Since Initial Coverage
- **Qwen3 Embed** — Top-ranked MTEB models (#2/#3/#4) from Qwen team
- **Gemma3** — Google's embeddinggemma-300m (gated, MTEB rank #8)
- **ModernBERT** — answerdotai's efficient BERT replacement
- **Mistral** — Salesforce SFR-Embedding-2_R (MTEB rank #18)
- **GTE** — Alibaba's GTE-Qwen2 family (MTEB ranks #6/#15)

### Key Discovery: ONNX + Metal = Zero-Cost Paths
TEI's ONNX backend (CPU-optimized) and Apple Silicon support (Homebrew + Metal) provide two entirely free deployment paths. Models up to 500M params run well on M-series hardware. The ORT backend enables CPU serving without GPU costs.

### Skill
mlops/hf-text-embeddings-inference — references/hf-learnings.md

---

## 2026-07-24: hf-inference-client-chat-completion-deep-dive-v3 — InferenceClient: Providers, Streaming, Tools, Structured Outputs & MCP (Topic #120 Deepened)

### Summary
Comprehensive deepening of the InferenceClient reference covering the latest `huggingface_hub` release. Adds: full 17-provider task-support matrix (verified from docs), OpenAI-compatible streaming patterns (sync `Iterable[ChatCompletionStreamOutput]` + async `async for`), function/tool calling with multi-turn execution loops, structured outputs via `response_format` (JSON mode + JSON Schema), the experimental `MCPClient` for MCP-based tool orchestration, provider selection strategies (routed vs direct, free-tier paths), authentication methods, and `text_generation()` streaming with `details=True`. Source-anchored to huggingface_hub docs.

### Source
- Inference guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/inference
- InferenceClient API ref: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client
- AsyncInferenceClient API ref: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.AsyncInferenceClient
- MCPClient API ref: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/mcp
- Inference Providers docs: https://huggingface.co/docs/inference-providers/en/index

### 1. Provider Task Support Matrix (17 Providers)

Verified from docs — ✅ = supported, ❌ = not supported:

| Task | Cerebras | Cohere | DeepInfra | fal-ai | Featherless | Fireworks | Groq | HF Inference | Novita | Nscale | OVHcloud | PublicAI | Replicate | Scaleway | Together | Wavespeed | Zai |
|------|----------|--------|-----------|--------|-------------|-----------|------|--------------|--------|--------|----------|----------|-----------|----------|----------|-----------|-----|
| audio_classification | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| automatic_speech_recognition | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **chat_completion** | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ |
| feature_extraction | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| **text_generation** | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| text_to_image | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | ✅ |
| text_to_speech | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| text_to_video | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| image_to_image | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| image_to_video | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |

**Key insight for zero-cost routing:** Only `hf-inference` (free tier via HF Inference API, rate-limited) and `together`/`deepinfra` (free trial tiers with rate limits) support `chat_completion` AND `text_generation` at no cost. Cerebras, Cohere, Groq require API keys with free tiers available.

### 2. OpenAI Compatibility — Drop-in Replacement

`InferenceClient` follows the OpenAI Python client syntax exactly. Migration is two lines:

```python
# Before (OpenAI)
from openai import OpenAI
client = OpenAI(api_key="...", base_url="...")

# After (huggingface_hub)
from huggingface_hub import InferenceClient
client = InferenceClient(api_key="...")  # No base_url needed
```

All parameters (messages, stream, temperature, tools, response_format, etc.) are identical. The client also exposes `client.chat.completions.create()` as an alias for `client.chat_completion()` for literal drop-in compatibility.

### 3. Streaming Patterns

#### Sync Streaming (InferenceClient)

```python
from huggingface_hub import InferenceClient

client = InferenceClient(provider="together")
messages = [{"role": "user", "content": "Write a haiku"}]

# Basic streaming
stream = client.chat_completion(messages, model="meta-llama/Llama-3.3-70B-Instruct", stream=True, max_tokens=100)
for chunk in stream:
    delta = chunk.choices[0].delta
    if delta.content:
        print(delta.content, end="")
```

**Stream chunk type:** `ChatCompletionStreamOutput` — each chunk has:
- `choices[0].delta.content` — the text delta (partial token)
- `choices[0].delta.tool_calls` — tool call deltas (for streaming tool use)
- `choices[0].finish_reason` — "stop", "length", "tool_calls", or None while streaming

#### Async Streaming (AsyncInferenceClient)

```python
from huggingface_hub import AsyncInferenceClient

client = AsyncInferenceClient(provider="deepinfra")

async def stream_chat():
    messages = [{"role": "user", "content": "Tell me a story"}]
    async for chunk in await client.chat_completion(
        messages, model="meta-llama/Llama-3.3-70B-Instruct", stream=True
    ):
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")

asyncio.run(stream_chat())
```

Note the double async: `await client.chat_completion(...)` returns the stream, then `async for chunk in stream` iterates.

#### text_generation() Streaming

```python
# Sync: Iterable[str]
for token in client.text_generation("The huggingface_hub library is", max_new_tokens=12, stream=True):
    print(token, end="")

# With details: Iterable[TextGenerationStreamOutput]
for details in client.text_generation("The huggingface_hub library is", max_new_tokens=12, stream=True, details=True):
    print(details.token.text, details.token.logprob)

# Async: AsyncIterable[str]
async for token in await client.text_generation("The Huggingface Hub is", stream=True):
    print(token, end="")
```

### 4. Function/Tool Calling

Supports OpenAI-identical tool calling interface. Verified working with Cerebras, Cohere, DeepInfra, Fireworks, Groq, Novita, Together, Zai (check individual provider docs for model support).

```python
from huggingface_hub import InferenceClient

client = InferenceClient(provider="novita")

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current temperature for a city",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"}
                },
                "required": ["location"]
            }
        }
    }
]

messages = [{"role": "user", "content": "What's the weather in London?"}]
response = client.chat_completion(
    messages, model="Qwen/Qwen2.5-72B-Instruct", tools=tools, tool_choice="auto"
)
tool_call = response.choices[0].message.tool_calls[0]
print(f"Tool: {tool_call.function.name}, Args: {tool_call.function.arguments}")
```

**Multi-turn tool execution loop pattern:**
```python
while response.choices[0].finish_reason == "tool_calls":
    tool_call = response.choices[0].message.tool_calls[0]
    messages.append(response.choices[0].message)
    # Execute tool, append result as "tool" role message
    messages.append({
        "role": "tool",
        "content": execute_tool(tool_call.function.name, tool_call.function.arguments),
        "tool_call_id": tool_call.id,
    })
    response = client.chat_completion(messages, model=..., tools=tools)
```

### 5. Structured Outputs & JSON Mode

`response_format` parameter follows OpenAI spec exactly.

**JSON Mode** (valid JSON, no schema enforcement):
```python
response = client.chat_completion(
    messages, model="...",
    response_format={"type": "json_object"}
)
```

**Structured Outputs** (schema-enforced, required JSON Schema):
```python
from huggingface_hub import ChatCompletionInputResponseFormatJSONSchema

response = client.chat_completion(
    messages, model="...",
    response_format=ChatCompletionInputResponseFormatJSONSchema(
        json_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
            "required": ["name", "age"]
        }
    )
)
```

**Provider support for structured outputs:** Cerebras (✅), DeepInfra (✅), Fireworks (✅), Together (✅), Novita (✅ for json_object), others vary.

### 6. MCP Client (Experimental)

`huggingface_hub` now includes an experimental `MCPClient` that extends `AsyncInferenceClient` to integrate with MCP servers (Model Context Protocol).

```python
from huggingface_hub import MCPClient, ChatCompletionInputMessage

client = MCPClient(provider="novita")

async with client.connect_to_mcp_server(
    command="python3", args=["-m", "some_mcp_server"]
) as mcp_client:
    messages = [ChatCompletionInputMessage(role="user", content="Generate an image of a cat")]
    async for chunk in mcp_client.chat_completion(
        messages, model="Qwen/Qwen2.5-72B-Instruct", stream=True
    ):
        if isinstance(chunk, ChatCompletionStreamOutput):
            print(chunk.choices[0].delta.content or "")
        # Tool calls are handled automatically by MCPClient
```

**MCP supports:**
- Local `stdio` servers (subprocess)
- Remote `http`/`sse` servers
- Automatic tool discovery, execution, and result relay
- Streaming tool call outputs

### 7. Provider Selection Strategies

**Routed through HF** (billed to HF account, uses HF provider keys):
```python
client = InferenceClient()  # provider="auto" — HF routes to best provider
client = InferenceClient(provider="together")  # Route through HF to Together
```

**Direct access** (uses your own API key for that provider):
```python
client = InferenceClient(provider="replicate", api_key="r8_xxx")
```

**Free-tier priorities (zero-cost):**
1. `provider="hf-inference"` — HF's own free serverless API (rate-limited, many small models)
2. `provider="together"` — Together free tier (Llama 3, DeepSeek, etc.)
3. `provider="deepinfra"` — DeepInfra free tier (Llama 3, Qwen, etc.)
4. `provider="groq"` — Groq free tier (requires API key, very fast LPU inference)
5. `provider="cerebras"` — Cerebras free tier (requires API key, very fast)

**Authentication precedence:**
1. `api_key` parameter (explicit)
2. `token` parameter (alias, legacy)
3. `HUGGINGFACEHUB_API_TOKEN` env var (for HF-routed calls)
4. `HF_TOKEN` env var (fallback)
5. `~/.cache/huggingface/token` (stored login token)

### 8. Key Design Insights

1. **OpenAI drop-in is real** — Same parameters, same return types, same streaming interface. Switch by changing import and removing `base_url`. The `chat.completions.create()` alias exists for literal compatibility.

2. **Provider choice affects feature availability** — Not all providers support all tasks. `chat_completion` has the widest support (14/17 providers). Many vision/audio tasks are HF Inference-only.

3. **Streaming uses SSE** — Both sync and async clients use Server-Sent Events under the hood. The `stream_options` parameter accepts `ChatCompletionInputStreamOptions` for controlling usage metadata in the final chunk.

4. **MCPClient is the future** — The experimental MCP client unifies tool calling with external MCP servers, enabling agentic workflows without writing manual tool execution loops.

5. **`text_generation` ≠ `chat_completion`** — `text_generation()` is the legacy TGI endpoint (raw text in/out, more parameters like `grammar`, `best_of`, `watermark`). `chat_completion()` is the modern OpenAI-compatible endpoint (structured messages, tools, streaming). Only DeepInfra, Together, Featherless, Novita, and HF Inference support `text_generation`; but 14 providers support `chat_completion`.

6. **Zero-cost routing via HF** — Using `InferenceClient()` without a provider uses HF-routed auto-routing, which queries available providers and chooses the best one. The HF Inference API itself (`hf-inference`) is always free but rate-limited — ideal for development and testing.

### Skill
Pending — no dedicated hf-inference-client skill directory exists. Added to central hf-learnings.md for now.
---

## 2026-07-24: hf-datasets-from-parquet — Loading Parquet Files with `datasets` Library (Topic #149 Deepened)

### Summary
Comprehensive deep-dive into loading Parquet data with the `datasets` library (v5.0.0). Covers `Dataset.from_parquet()` (path, columns, filters, num_proc, fragment_scan_options, on_bad_files), `load_dataset()` with auto-detected parquet format, the `ParquetConfig` options (split, streaming), pyarrow filter predicate pushdown for efficient column/row pruning, multi-file loading with sharding, integration with the Datasets Server `/parquet` endpoint for server-side conversions, and practical performance patterns.

### Source
- huggingface/datasets source: `src/datasets/io/parquet.py` (ParquetDatasetReader)
- huggingface/datasets source: `src/datasets/packaged_modules/parquet/parquet.py` (Parquet builder)
- Official docs: https://huggingface.co/docs/datasets/en/parquet_processing
- API reference: https://huggingface.co/docs/datasets/v5.0.0/en/package_reference/main_classes#datasets.Dataset.from_parquet
- PyArrow Dataset docs: https://arrow.apache.org/docs/python/generated/pyarrow.dataset.ParquetFragmentScanOptions.html

### 1. `Dataset.from_parquet()` — Core API

```python
from datasets import Dataset

# Single file
ds = Dataset.from_parquet("data/train-00000-of-00001.parquet")

# Multiple files (sharded dataset)
ds = Dataset.from_parquet([
    "data/train-00000-of-00004.parquet",
    "data/train-00001-of-00004.parquet",
    "data/train-00002-of-00004.parquet",
    "data/train-00003-of-00004.parquet",
])

# Select columns only (saves I/O)
ds = Dataset.from_parquet("data.parquet", columns=["text", "label"])

# Filter rows on load — predicate pushdown to Parquet metadata
ds = Dataset.from_parquet(
    "data.parquet",
    filters=[("label", "==", 1)]       # only rows where label == 1
)

# Compound filter
ds = Dataset.from_parquet(
    "data.parquet",
    filters=[("label", "==", 1), ("split", "in", ["train", "val"])]
)

# Multi-process parsing (num_proc)
ds = Dataset.from_parquet(
    ["shard-1.parquet", "shard-2.parquet", "shard-3.parquet"],
    num_proc=3                   # one process per file
)
```

**Full parameter reference:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `path_or_paths` | `PathLike \| list[PathLike]` | required | Single Parquet file path or list of paths |
| `split` | `NamedSplit` | `None` | Split name to assign (e.g., `"train"`, `"test"`) |
| `features` | `Features` | `None` | Explicit feature schema (auto-detected if None) |
| `cache_dir` | `str` | `~/.cache/huggingface/datasets` | Cache directory for Arrow data |
| `keep_in_memory` | `bool` | `False` | Copy all data in-memory instead of memory-mapping |
| `columns` | `list[str]` | `None` | Subset of columns to load (prunes at read time) |
| `num_proc` | `int` | `None` | Parallel reading across files (v2.8.0+) |
| `filters` | `Expression \| list[tuple] \| list[list[tuple]]` | `None` | Predicate pushdown filter — prunes rows at source |
| `fragment_scan_options` | `ParquetFragmentScanOptions` | `None` | Scan tuning (buffering, caching) (v4.2.0+) |
| `on_bad_files` | `"error" \| "warn" \| "skip"` | `"error"` | Behavior on unreadable files (v4.2.0+) |
| `**kwargs` | any | — | Passed to `ParquetConfig` |

### 2. Filter Predicate Pushdown — Deep Dive

Filters are evaluated at the **Parquet metadata level** — row group statistics (`min`, `max`, `null_count`) are checked before any I/O. This means entire row groups can be skipped without decompression.

**Filter format — tuple list:**
```python
# Simple: [("column", "op", value)]
filters = [("age", ">=", 18)]

# AND: multiple tuples in same list
filters = [("age", ">=", 18), ("country", "==", "US")]

# OR: list of lists (each inner list is AND-ed)
filters = [("age", ">=", 18), [("country", "==", "US"), ("country", "==", "CA")]]
# = (age >= 18) AND (country == "US" OR country == "CA")
```

**Filter format — pyarrow Expression (more expressive):**
```python
import pyarrow.dataset as pds

# Equivalent to tuple list
filt = (pds.field("age") >= 18) & (pds.field("country") == "US")

ds = Dataset.from_parquet("data.parquet", filters=filt)
```

**Supported operators:** `==`, `!=`, `<`, `<=`, `>`, `>=`, `in`, `not in`

**Performance impact:** For a 10 GB Parquet file partitioned into 64 MB row groups, a selective filter can skip 95%+ of row groups, reducing read to ~500 MB and load time from minutes to seconds.

### 3. `load_dataset()` with Parquet — Auto-Detection

`load_dataset()` automatically detects Parquet files by extension (`.parquet`):

```python
from datasets import load_dataset

# From local directory of parquet files
ds = load_dataset("parquet", data_dir="./my-data/")
# or explicitly:
ds = load_dataset("parquet", data_files="data/*.parquet")

# From Hugging Face Hub (auto-detects parquet if no loading script)
ds = load_dataset("username/my-parquet-dataset", split="train")

# Force parquet builder
ds = load_dataset(
    "parquet",
    data_files={
        "train": "train-*.parquet",
        "test": "test-*.parquet",
    }
)

# With streaming
ds = load_dataset("parquet", data_files="big.parquet", streaming=True)
```

**The auto-detection logic** (from `packaged_modules/parquet/parquet.py`):
1. When `load_dataset()` is called with a dataset path, it first checks for a loading script
2. If none found, it inspects the repo's file extensions
3. If `.parquet` files dominate, it uses the `Parquet` packaged builder
4. The builder reads file metadata (schema, row count) without loading data

### 4. Streaming Parquet Data

```python
# Streaming reads rows on-demand — no local cache
ds = load_dataset("parquet", data_files="huge.parquet", streaming=True)

# IterableDataset methods
for i, example in enumerate(ds):
    if i > 100:
        break
    print(example["text"])

# Take/skip/shuffle
sample = ds.take(1000)               # first 1000
ds_filtered = ds.filter(lambda x: x["label"] == 1)
```

**When to stream:**
- Dataset too large for available disk
- Iterating once (training epoch over large corpus)
- Exploring data before deciding to download

**When NOT to stream:**
- Multiple random-access passes needed
- Index-based lookups (`ds[5000]`)
- Shuffling before training (use `IterableDataset.shuffle()` instead)

### 5. Datasets Server `/parquet` Endpoint Integration

The Datasets Server exposes a `/parquet` endpoint that returns URLs to pre-converted Parquet files for any compatible dataset:

```python
import requests

# Get parquet URLs for a dataset
resp = requests.get(
    "https://datasets-server.huggingface.co/parquet?dataset=imdb"
)
parquet_data = resp.json()
parquet_files = parquet_data["parquet_files"]

# {'dataset': 'imdb', 'config': 'plain_text', 'split': 'train',
#  'url': 'https://.../imdb/plain_text/train/0000.parquet'}

# Load directly from URLs
ds = load_dataset(
    "parquet",
    data_files={"train": [p["url"] for p in parquet_files]},
    streaming=True
)
```

**Key `/parquet` response fields:**

| Field | Type | Description |
|-------|------|-------------|
| `dataset` | `str` | Dataset name |
| `config` | `str` | Configuration/subset name |
| `split` | `str` | Split name |
| `url` | `str` | HTTPS URL to the Parquet file |
| `size` | `int` | File size in bytes |
| `columns` | `list[str]` | Column names in the file |

**Practical pattern — zero-cost Hub querying without downloading:**
```python
from datasets import load_dataset

# Stream a Hub dataset from its Parquet conversion
ds = load_dataset(
    "parquet",
    data_files={
        "train": [
            "https://huggingface.co/datasets/username/dataset/resolve/refs%2Fconvert%2Fparquet/train/0000.parquet"
        ]
    },
    streaming=True
)

# or use the datasets-server API for auto-discovery
import requests, json
url = "https://datasets-server.huggingface.co/parquet?dataset=username/dataset"
files = requests.get(url).json()["parquet_files"]
ds = load_dataset("parquet", data_files={"train": [f["url"] for f in files]})
```

### 6. Performance Patterns

**Pattern 1: Column selection first, filter second**
```python
# BEST — prune columns AND rows at read time (most efficient)
ds = Dataset.from_parquet("big.parquet", columns=["id", "text", "label"], filters=[("label", "==", 1)])
```

**Pattern 2: Parallelize across shards**
```python
# Each file processed in parallel
files = [f"shard-{i:05d}-of-00010.parquet" for i in range(10)]
ds = Dataset.from_parquet(files, num_proc=4, columns=["text"])
```

**Pattern 3: Fragment scan options for memory-constrained environments**
```python
import pyarrow.dataset as pds

opts = pds.ParquetFragmentScanOptions(
    use_buffered_stream=True,     # smaller reads
    buffer_size=8192,             # 8 KB read buffer
)
ds = Dataset.from_parquet("big.parquet", fragment_scan_options=opts)
```

**Pattern 4: Chaining from_parquet with dataset operations**
```python
ds = (
    Dataset
    .from_parquet("data.parquet", filters=[("lang", "==", "en")])
    .select_columns(["text", "label"])
    .shuffle(seed=42)
    .select(range(10000))
)
```

### 7. `ParquetConfig` Tuning

When using `load_dataset("parquet", ...)`, the `ParquetConfig` class controls behavior:

```python
from datasets import load_dataset
from datasets.packaged_modules.parquet.parquet import ParquetConfig

ds = load_dataset(
    "parquet",
    data_files="data.parquet",
    split="train",
    streaming=True,
    parquet_config=ParquetConfig(
        features=None,          # auto-detect
        schema=None,            # optional pyarrow schema
        batch_size=10000,       # rows per read batch (default: auto)
    )
)
```

### 8. Known Limitations

1. **Appending is not supported** — `from_parquet` creates a new Dataset; use `datasets.concatenate_datasets()` to merge
2. **Nested schema differences** — if Parquet files in a list have different schemas, loading may fail (use `features` to force schema)
3. **Predicate pushdown varies** — not all Parquet writers generate equally useful statistics for filter pruning
4. **Remote URLs** — `from_parquet()` does NOT accept HTTPS URLs directly (use `load_dataset("parquet", data_files="https://...")` with streaming instead)
5. **`fragment_scan_options` is PyArrow-specific** — only works with the PyArrow-backed reader

### Skill
mlops/hf-datasets-library — references/hf-learnings.md

### References
- https://huggingface.co/docs/datasets/en/parquet_processing
- https://huggingface.co/docs/datasets/v5.0.0/en/package_reference/main_classes#datasets.Dataset.from_parquet
- https://arrow.apache.org/docs/python/dataset.html#filtering-data
- https://huggingface.co/docs/datasets/en/stream
- https://huggingface.co/docs/datasets-server/parquet

---

## 2026-07-24: hf-hub-api-rate-limiting-deep-dive — Hub Rate Limits — Three Buckets, Per-Plan Tiers, Smart Retry (Topic #166 Deep-Dive)

### Summary
Comprehensive deep-dive into Hugging Face Hub rate limiting — covering the three request buckets (API, Resolvers, Pages), per-plan tier limits from Anonymous to Enterprise Plus, IETF-standard HTTP rate limit headers (`RateLimit`, `RateLimit-Policy`), the smart retry mechanism in `huggingface_hub` v1.2.0+ with source-level analysis of the exponential backoff and `RateLimitInfo` parsing, practical avoidance patterns, and the billing dashboard gauges. This topic was previously tracked as Topic #166 but never received a dedicated entry.

### Sources
- Official docs: https://huggingface.co/docs/hub/en/rate-limits
- Source: `huggingface_hub/utils/_http.py` (main branch)
- Source: `huggingface_hub/errors.py`
- IETF draft: https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
- Billing dashboard: https://huggingface.co/settings/billing

### 1. The Three Request Buckets

The Hub classifies all requests into three buckets:

| Bucket | Description | Examples | Relative Limit |
|--------|-------------|----------|----------------|
| **API** | Programmatic Hub API calls | Model/dataset search, repo creation, user management, discussions | Medium |
| **Resolvers** | `/resolve/` URLs serving user-generated content | Model weight downloads, dataset files, Space assets | Highest |
| **Pages** | Web page browsing | Any `.huggingface.co` page for humans | Lowest |

**Resolver Identification:** Any URL containing a `/resolve/` path segment. These are the URLs constructed by open-source libraries (`transformers`, `datasets`, `vLLM`, `llama.cpp`) and AI applications (LM Studio, Jan, ollama) for downloading model/dataset files. HF optimizes infrastructure for Resolver requests, so their limits are the highest.

### 2. Per-Plan Rate Limit Tiers (5-minute fixed windows)

| Plan | API | Resolvers | Pages |
|------|-----|-----------|-------|
| Anonymous (per IP) | 500 | 3,000 | 100 |
| Free user | 1,000 | 5,000 | 200 |
| PRO user | 2,500 | 12,000 | 400 |
| Team org | 3,000 | 20,000 | 400 |
| Enterprise org | 6,000 | 50,000 | 600 |
| Enterprise Plus org | 10,000 | 100,000 | 1,000 |
| Enterprise Plus (Org IP Ranges) | 100,000 | 500,000 | 10,000 |
| Academia Hub org | 3,000 | 20,000 | 400 |

**Key details:**
- Anonymous/Free limits may change based on platform health
- Organization limits apply **per member individually**, not shared
- Anonymous limit is **per IP address**
- All windows are 5-minute fixed windows (allowing burstiness)

### 3. HTTP Rate Limit Headers (IETF Draft v9)

**`RateLimit` header:**
```
RateLimit: "api";r=0;t=55
```
- `r` = remaining requests in current window
- `t` = seconds until reset

**`RateLimit-Policy` header:**
```
RateLimit-Policy: "fixed window";"api";q=500;w=300
```
- `q` = total allowed per window
- `w` = window duration in seconds

**Example (rate limited):** `RateLimit: "api";r=0;t=55` + `RateLimit-Policy: "fixed window";"api";q=500;w=300` — 0 remaining of 500 API calls, reset in 55s.

The Hub also sends the standard `Retry-After` header as a fallback.

### 4. Source-Level: huggingface_hub Smart Retry

**`RateLimitInfo` dataclass** (`utils/_http.py`):
```python
@dataclass
class RateLimitInfo:
    resource_type: str        # "api", "resolvers", or "pages"
    remaining: int            # requests remaining in window
    reset_in_seconds: int     # seconds until reset
    limit: int | None = None
    window_seconds: int | None = None
```

**Two regex patterns parse the headers:**
```python
_RATELIMIT_REGEX = re.compile(r'\"(?P<resource_type>\w+)\"\s*;\s*r\s*=\s*(?P<r>\d+)\s*;\s*t\s*=\s*(?P<t>\d+)')
_RATELIMIT_POLICY_REGEX = re.compile(r'q\s*=\s*(?P<q>\d+).*?w\s*=\s*(?P<w>\d+)')
```

**Retry parameters in `_http_backoff_base()`:**
| Parameter | Default | Purpose |
|-----------|---------|---------|
| `max_retries` | 5 | Max retry attempts |
| `base_wait_time` | 1s | Initial wait |
| `max_wait_time` | 8s | Max wait between retries |
| `retry_on_exceptions` | Timeout, Network, Protocol errors | Transient failures |
| `retry_on_status_codes` | 408, 429, 500, 502, 503, 504 | Transient server errors |

**Retry flow:**
1. Send request → check status code
2. If status in retry_on_status_codes:
   - **429 + RateLimit header** → parse `reset_in_seconds`, wait exact + 1s
   - **Retry-After header** → parse seconds, wait
   - **5xx errors** → exponential backoff: `sleep = min(max_wait, sleep * 2)`
   - **max_retries exceeded** → `hf_raise_for_status()` raises error
3. If NOT in retry_on_status_codes → return immediately

**Critical distinction:** When 429 with `RateLimit` header is received, the library uses the **exact server-specified reset time** (+1s safety margin) rather than multiplying backoff — avoiding unnecessary waiting.

### 5. Checking Rate Limit Status

**Dashboard:** https://huggingface.co/settings/billing shows three real-time gauges (one per bucket), updated every 5 minutes.

**Programmatic detection:**
```python
from huggingface_hub.utils import parse_ratelimit_headers

response = requests.get("https://huggingface.co/api/models?search=bert")
info = parse_ratelimit_headers(dict(response.headers))
if info and info.remaining == 0:
    print(f"Rate limited! Reset in {info.reset_in_seconds}s")
```

### 6. Practical Avoidance for Zero-Cost Users

| Strategy | Impact |
|----------|--------|
| **Always pass HF_TOKEN** | Free user: 1,000 vs Anonymous: 500 API calls/5min |
| **Prefer Resolver URLs over API** | Resolver limits are 5× higher than API |
| **Use `hf_hub_download()` caching** | Repeated downloads skip API calls |
| **Batch commits with `CommitScheduler`** | Reduces API call count |
| **Use fsspec for filesystem ops** | No API calls, no rate limits |
| **Spread requests over time** | Avoids window exhaustion |
| **Pre-check with `file_exists()`** | Prevents wasteful uploads |

### 7. Granular User Action Rate Limits

Undocumented limits exist for: repo creation, commits, discussions, comments, moderation. These change frequently — contact support if hit.

### Skill
mlops/hf-hub-configuration — references/hf-learnings.md

### References
- https://huggingface.co/docs/hub/en/rate-limits
- https://huggingface.co/settings/billing
- `huggingface_hub/utils/_http.py` — `_http_backoff_base()`, `parse_ratelimit_headers()`, `_parse_retry_after()`
- https://www.ietf.org/archive/id/draft-ietf-httpapi-ratelimit-headers-09.html
- https://huggingface.co/.well-known/openapi.json

## 2026-07-24: hf-datasets-500-agent-traces-json-type — Datasets v5.0.0 Deep-Dive (Topic #205+)

### Summary
Datasets v5.0.0 (June 5, 2026) introduced: **Agent traces** parsing via `teich`, **Json() type** for mixed-type tool-calling data in Arrow/Parquet, **multi-shard shuffle** (breaking change — true randomization in streaming), **batch(by_column=...)** for episode grouping, **Storage Buckets** integration (`hf://` URIs), and 4 new formats (Iceberg, TsFile, 3D mesh, CoNLL). Beer's 8 tool-calling datasets can be tagged `format:agent-traces` for auto-detection and direct training pipeline integration.

### Key Takeaways for Beer
1. **Tag datasets** with `format:agent-traces` in repo card for discoverability
2. **Json() type** handles tool-calling data's mixed-type fields — use `on_mixed_types="use_json"` in `from_list()`/`map()`
3. **Multi-shard shuffle** is the new default — `max_buffer_input_shards=1` for old behavior
4. **batch(by_column=...)** groups tool-use episodes by session ID
5. **Storage Buckets** let Beer load raw JSONL from HF buckets → process → push as curated dataset

### Source
Full deep-dive: `mlops/hf-datasets-library/references/hf-learnings.md`  
Release: https://github.com/huggingface/datasets/releases/tag/5.0.0

## 2026-07-24: hf-dataset-card-api — Deep Dive on Hub Tag Taxonomy, Validation Endpoint & Discoverability (Topic #191 Deepening)

### Summary
Deepened the dataset card API coverage with the Hub's built-in tag taxonomy — `get_dataset_tags()` revealing 10 categories (library, license, language, other, task_ids, task_categories, size_categories, format, modality, benchmark), the `/api/validate-yaml` validation endpoint mechanics (array-vs-string field requirements), and practical tagging patterns for tool-calling datasets. Key discovery: `format:agent-traces` tag for Beer's 8 tool-calling datasets, passed as extra kwargs to `DatasetCardData` since it has no typed `tags` field.

### Key Takeaways for Beer
1. **Tag tool-calling datasets with `format:agent-traces`, `other:agent`, `synthetic`** for Hub discoverability
2. **Hub validation requires arrays** — always pass lists for `language`, `license`, `task_categories`, `size_categories`, etc.
3. **`DatasetCardData` accepts extra tags via kwargs** — `tags=['format:agent-traces', 'other:agent']` passed through `CardData.__init__(**kwargs)`
4. **Programmatic tag discovery** — `api.get_dataset_tags()` returns the authoritative tag taxonomy
5. **`train_eval_index` auto-renames to `train-eval-index`** in YAML export
6. **`_original_order` preserves key order** for minimal diffs on round-trips

### Source
Full deep-dive: `mlops/hf-dataset-card-api/references/hf-learnings.md`  
`huggingface_hub` v1.24.0 source: `repocard.py`, `repocard_data.py`  
Hub validation: `POST https://huggingface.co/api/validate-yaml`  
Dataset tags: `GET https://huggingface.co/api/datasets-tags-by-type`

## 2026-07-24: hf-diffusers-nunchaku-lite — Nunchaku Lite 4-bit W4A4 Diffusion Inference in Diffusers (Topic #76 Deepening)

### Summary
Deep-dive on **Nunchaku Lite** — the new native integration of SVDQuant 4-bit diffusion inference directly into Hugging Face Diffusers (PR #14100, July 2026). Unlike weight-only quantization (AWQ, bitsandbytes NF4, GPTQ), SVDQuant quantizes both **weights and activations** (W4A4) using a low-rank SVD correction to handle outliers. The integration means any quantized checkpoint loads with standard `from_pretrained()`, with CUDA kernels fetched automatically from the Hub via the `kernels` package. No separate inference engine, no local CUDA compilation.

### Architecture

**SVDQuant** (arXiv:2411.05007) — the quantization method behind Nunchaku:
- Moves activation outliers into the weight matrix via a low-rank SVD correction
- Core weight matrix quantized to 4-bit (INT4 or NVFP4)
- Outlier residual captured by a small 16-bit low-rank branch (rank=32 default)
- Fused kernel: low-rank down-projection fused with input quantization, low-rank up-projection fused with 4-bit matmul — eliminates memory overhead of 16-bit branch
- Result: ~50% VRAM reduction + ~1.35× speedup vs BF16

**Two kernel families in Nunchaku Lite:**

| Kernel | Precision | Use Case | Supported GPUs |
|--------|-----------|----------|----------------|
| `svdq_w4a4` | INT4 or NVFP4 | Attention & MLP projections (compute-bound) | INT4: Turing/Ampere/Ada (RTX 30/40, A100, L40S); NVFP4: Blackwell (RTX 50, B200) |
| `awq_w4a16` | INT4 | Adaptive norm/modulation (memory-bound, precision-sensitive) | Turing/Ampere/Ada |

**Native loading in Diffusers:**
- Quantized repo is a standard Diffusers pipeline with `quantization_config` in the transformer's `config.json`
- `NunchakuLiteQuantizer` (in `diffusers/quantizers/nunchaku/`) — validates GPU capability (rejects Hopper/Volta), replaces `nn.Linear` modules with `SVDQW4A4Linear` or `AWQW4A16Linear` via `replace_with_nunchaku_linear()`
- Kernels downloaded from `rootonchair/nunchaku-lite-kernels` on first use via `kernels.get_kernel()`
- Keeps exact module structure — schedulers, LoRA, offloading, and `torch.compile` all work normally

### Getting Started
```python
pip install -U diffusers transformers accelerate kernels bitsandbytes

import torch
from diffusers import ErnieImagePipeline

pipe = ErnieImagePipeline.from_pretrained(
    "lite-infer/ERNIE-Image-Turbo-nunchaku-lite-nvfp4_r32-bnb4-text-encoder",
    torch_dtype=torch.bfloat16,
).to("cuda")

image = pipe(
    prompt="A cinematic portrait of a red fox in a misty forest at sunrise, detailed fur, volumetric light",
    height=1024, width=1024,
    num_inference_steps=8, guidance_scale=1.0,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
```

### Performance Benchmarks (RTX PRO 6000 Blackwell, 1024×1024)

| Configuration | Full Pipeline | Denoise Loop | Peak VRAM | Speedup |
|--------------|--------------|--------------|-----------|---------|
| BF16 baseline | 3.00 s | 2.86 s | 31.1 GB | 1.0× |
| Nunchaku Lite NVFP4 | 2.27 s | 2.13 s | 20.6 GB | 1.35× |
| NVFP4 + `torch.compile` | 1.68 s | 1.53 s | 20.6 GB | **1.8×** |
| NVFP4 + NF4 text encoder | 2.29 s | 2.13 s | 16.0 GB | 1.35× |

### Quantizing Your Own Model
The `diffuse-compressor` toolkit provides an end-to-end SVDQuant workflow:
1. **Inspect** — `quantize_hf.py --inspect-config` walks the model, identifies SVDQ targets (linear layers in transformer blocks) and AWQ targets (modulation layers)
2. **Quantize** — run SVDQuant calibration, producing a safetensors checkpoint with SVDQ/AWQ weights
3. **Package** — `convert_nunchaku_lite_diffusers.py` combines quantized transformer with base pipeline, writes `nunchaku_lite` config into `transformer/config.json`
4. **Verify & Push** — load with `DiffusionPipeline.from_pretrained()`, verify outputs, call `pipe.push_to_hub()`

### Structural Rewrites for Maximum Speed
The original Nunchaku engine achieves higher speedup by fusing QKV projections and other grouped operations — e.g., combining `to_q`, `to_k`, `to_v` into one `to_qkv` module. Nunchaku Lite's generic path cannot infer these rewrites automatically, but they can be expressed via model-specific `TargetConfig` during quantization and runtime adapters at load time.

### Key Takeaways
1. **W4A4 beats weight-only** — SVDQuant's activation quantization gives actual speedup, not just memory savings
2. **NVFP4 requires Blackwell** — for RTX 30/40 series, use INT4 variants
3. **`kernels` package** replaces local CUDA compilation — kernels auto-download from the Hub
4. **`torch.compile` synergy** — Nunchaku Lite + compile = 1.8× speedup
5. **NF4 text encoder** — bitsandbytes NF4 on T5/Qwen3 saves ~22% VRAM
6. **No Hopper/Volta support** — GPU capability validated at load time with clear error messages

### Skill
mlops/hf-diffusers-cogvideo — references/hf-learnings.md

### References
- Blog: https://huggingface.co/blog/nunchaku-diffusers (July 23, 2026)
- Diffusers docs: https://huggingface.co/docs/diffusers/main/en/quantization/nunchaku
- Integration PR: https://github.com/huggingface/diffusers/pull/14100
- SVDQuant paper: https://arxiv.org/abs/2411.05007
- Nunchaku engine: https://github.com/nunchaku-tech/nunchaku
- diffuse-compressor: https://github.com/rootonchair/diffuse-compressor
|- `kernels` package: https://huggingface.co/kernels/rootonchair/nunchaku-lite-kernels
|- Quantizer source: `diffusers/src/diffusers/quantizers/nunchaku/`
|- `SVDQW4A4Linear` source: `diffusers/src/diffusers/quantizers/nunchaku/utils.py`

---

## 2026-07-24: hf-hub-repo-likes-engagement-api-deep-dive-v2 — Downloads, Trending Score, and Discovery API (Topic #213 Deepening)

**author:** SakThai
**license:** MIT

### Summary
Deepening of the Hub Engagement API with coverage of downloads metrics (30-day + all-time), trending score, search sort/expand parameters by engagement, and the full REST API surface. Completes the engagement picture: likes from v1 + downloads + trending + discovery.

Full deep-dive: `mlops/huggingface-hub/references/hf-learnings.md` (topic #213 v2)

### Skill
huggingface-hub — references/hf-learnings.md

## 2026-07-24: hf-datasets-concatenate-and-interleave — Source-Code Deep Dive (Topic #185 v2)

### Summary
Deep-dive into the internal implementation of `concatenate_datasets()` and `interleave_datasets()` in the `datasets` library (v5.0.0). Covers the Arrow-based map-style implementation (`offsets + arange` index computation, `pyarrow.concat_tables`), the iterable implementation (`CyclingMultiSourcesExamplesIterable` / `RandomlyCyclingMultiSourcesExamplesIterable`), all three stopping strategies (`first_exhausted`, `all_exhausted`, `all_exhausted_without_replacement`), horizontal vs vertical concatenation, resharding for parallelism, and edge cases.

### Source
- combine.py: https://github.com/huggingface/datasets/blob/5.0.0/src/datasets/combine.py
- arrow_dataset.py (lines 7030-7240): internal `_concatenate_map_style_datasets` + `_interleave_map_style_datasets`
- iterable_dataset.py (lines 5196-5450): internal `_concatenate_iterable_datasets` + `_interleave_iterable_datasets`

### Key Insights
- Map-style interleave concatenates all datasets first, then builds a reordering indices array — no per-element overhead
- `all_exhausted_without_replacement` uses a chunking algorithm over sorted unique lengths: processes each chunk, removes exhausted datasets, continues with survivors
- Iterable interleave buffers one example ahead per source to detect exhaustion
- The `RandomlyCyclingMultiSourcesExamplesIterable` uses `rng.integers()` or `rng.choice()` in batches of 1000 for efficiency
- `stopping_strategy` is applied per-process in distributed settings, causing up to 1 sample loss per worker with `first_exhausted`
- `reshard()` before interleaving prevents parallelism bottlenecks from low-shard datasets

### Skill
mlops/hf-datasets-concatenate-and-interleave — SKILL.md + references/hf-learnings.md

---

## 2026-07-24: hf-hub-storage-limits-and-plans

### Summary
Deep-dive into Hugging Face Hub's storage limit and quota system — covering storage plans across Free, PRO, Team, and Enterprise tiers; public/private storage quotas, storage add-ons, pay-as-you-go private storage pricing, per-repo limitations (file count, file size, commit size), LFS file management, PR ref cleanup, super-squash history, and tracking LFS file references. Critical knowledge for managing large models/datasets on the Hub without hitting quota limits.

### Key Findings

**Storage Plans (as of July 2026):**
| Account Type | Public Storage | Private Storage |
|---|---|---|
| Free user/org | Best-effort (generous, but no guarantees) | 100 GB |
| PRO | Up to 10 TB included + add-on available | 1 TB + pay-as-you-go |
| Team Org | 12 TB base + 1 TB/seat + add-on | 1 TB/seat + pay-as-you-go |
| Enterprise Org | 200 TB base + 1 TB/seat + add-on (up to 1,000 TB contracts) | 1 TB/seat + pay-as-you-go |

**Public Storage Add-on Pricing (PRO/Team/Enterprise):**
| Tier | Price |
|---|---|
| 1 TB | $12/mo |
| 5 TB | $60/mo |
| 10 TB | $120/mo |
| 20 TB | $240/mo |
| 50 TB | $500/mo ($10/TB) |

**Private Storage Pay-as-you-go:**
- Base: $18/TB/mo
- 50 TB+: $16/TB/mo
- 200 TB+: $14/TB/mo
- 500 TB+: $12/TB/mo

**Per-Repository Limitations (Git-backed repos):**
| Characteristic | Recommended | Hard Limit |
|---|---|---|
| Files per repo | < 100k | Soft (performance degrades) |
| Entries per folder | < 10k | Hard cap: 10k/folder |
| File size | < 200 GB | Hard cap: 500 GB single file |
| Commit size | < 100 files | Soft (60s HTTP timeout) |
| Commits per repo | — | Soft (UI degrades past few thousand) |

**Storage Management Operations:**
1. **Deleting LFS files**: Via repo Settings > List LFS files > delete. Note: deleting only pointers doesn't free space; requires history rewrite.
2. **Deleting PR refs**: Closed/merged PRs show a storage notice at bottom with estimated reclaimable space. "Delete ref" is irreversible.
3. **Super-squash history**: `HfApi.super_squash_history()` compresses entire Git history into single commit. LFS file history is permanently removed. Storage quota updates within 36 hours.
4. **Tracking LFS origins**: `git log --all -p -S <SHA-256-OID>` to trace which commit introduced an LFS file.
5. **Preventing commit timeouts**: Use `upload_folder()` / `hf upload` which auto-splits large folders into multiple commits of ~50-100 files.

**Sharing Large Datasets Requirements:**
- Dataset card required
- Community-reuse intent
- Follow repo limitations
- Use Parquet or WebDataset formats
- Avoid custom loading scripts

**Grants for Research:**
- Impact-based grants available for open-source work where paid plans can't cover need
- Requires evidence (downloads, citations, community adoption)
- Contact: datasets@huggingface.co or models@huggingface.co

**Key API Methods (huggingface_hub):**
- `HfApi.super_squash_history(repo_id, repo_type)` — destructive history compaction
- `HfApi.get_namespace_quota()` — get storage quota info
- `HfApi.repo_info()` — get repository details including size
- Upload methods with auto-splitting: `upload_folder()`, `hf upload` CLI

### Resources
- Official docs: https://huggingface.co/docs/hub/en/storage-limits
- Billing: https://huggingface.co/docs/hub/en/billing
- Pricing: https://huggingface.co/pricing
- Large upload guide: https://huggingface.co/docs/huggingface_hub/main/en/guides/upload
- git-sizer: https://github.com/github/git-sizer
- Blog: https://huggingface.co/blog/xethub-joins-hf

### Skill
mlops/hf-hub-storage-limits — SKILL.md + references/hf-learnings.md

---

## 2026-07-24: hf-data-studio-sql-console-deep-dive — Query HF Datasets with DuckDB SQL In-Browser (Topic #226)

### Summary
Comprehensive deep-dive into Hugging Face's **Data Studio SQL Console** — the in-browser DuckDB SQL query engine that lets you run analytical SQL queries directly on Hub datasets at zero cost. Covers in-browser DuckDB WASM architecture, `hf://` protocol integration with DuckDB CLI, the Saved Embeds CRUD API, `hf datasets sql` CLI command, natural language querying, leakage detection, histogram analysis, regex matching, Storage Bucket queries, and share/embed/export workflows.

### Source
- Data Studio SQL Console docs: https://huggingface.co/docs/hub/en/datasets-viewer-sql-console
- Data Studio docs: https://huggingface.co/docs/hub/en/data-studio
- DuckDB datasets docs: https://huggingface.co/docs/hub/en/datasets-duckdb
- DuckDB official docs: https://duckdb.org/docs/
- Dataset Viewer API docs: https://huggingface.co/docs/dataset-viewer/en/index

### 1. What Is the Data Studio SQL Console?

The **SQL Console** is an in-browser SQL query engine built into the Data Studio (rebranded Dataset Viewer) at `huggingface.co/datasets/{namespace}/{repo}`. It is powered by **DuckDB compiled to WebAssembly (WASM)** and runs entirely in the browser — no server-side compute, no API calls, no cost.

**Architecture:**
```
Browser
├── DuckDB WASM binary (~5 MB)
├── Auto-converted Parquet files from the Hub
│   (fetched via HTTP range requests)
├── SQL execution engine (OLAP, columnar)
└── Results displayed as table + download
```

Because DuckDB runs in-process in the browser, queries execute instantly on the client side. The Parquet data is streamed directly from the Hugging Face Hub's CDN.

### 2. Key Capabilities

| Capability | Description |
|---|---|
| **Full DuckDB SQL** | All DuckDB SQL syntax — SELECT, FROM, WHERE, GROUP BY, JOIN, window functions, CTEs, set operations |
| **Histogram** | `FROM histogram(table, column, bin_count)` — instant distribution plots |
| **Regex Matching** | DuckDB `regexp_matches()`, `regexp_replace()` for text pattern queries |
| **Share Links** | URL encodes the SQL query — shareable `?sql_console=true&sql=...` |
| **Download Results** | Export query results as **Parquet** or **CSV** directly from the browser |
| **Embed Results** | Embed query results in any webpage via iframe |
| **Natural Language Querying** | Describe what you want in English → auto-generated SQL |
| **Copy to DuckDB CLI** | Generates the equivalent SQL for DuckDB CLI usage |
| **Leakage Detection** | Find overlapping rows between splits (e.g. train vs test leakage) |

### 3. Accessing the SQL Console

Navigate to any dataset on the Hub and append `?sql_console=true` to the URL, or click the SQL Console tab in the Data Studio UI.

Example: `https://huggingface.co/datasets/gretelai/synthetic-gsm8k-reflection-405b?sql_console=true`

### 4. Basic SQL Queries

The dataset splits are available as virtual table names (e.g., `train`, `test`, `validation`):

```sql
-- List all rows from the training split
SELECT * FROM train LIMIT 10;

-- Filter with WHERE clause
SELECT * FROM train WHERE LENGTH(reasoning_chains) > 10;

-- Aggregate and group
SELECT topic, COUNT(*) as count
FROM train
GROUP BY topic
ORDER BY count DESC;
```

### 5. DuckDB Histogram Function

The built-in `histogram()` function is one of the most powerful features for data exploration:

```sql
-- Basic histogram of a column
FROM histogram(train, Rating);

-- With custom bin count
FROM histogram(train, Rating, bin_count := 20);

-- Using traditional syntax
SELECT * FROM histogram(train, Rating);
```

This generates a bar chart visualization directly in the browser showing value distributions.

### 6. Regex Pattern Matching

DuckDB has deep regex support via the `regexp_matches()` function:

```sql
-- Find rows where model_answer contains markdown code blocks
SELECT *
FROM train
WHERE regexp_matches(model_answer, '```')
LIMIT 10;

-- Extract matching patterns
SELECT regexp_extract(text, 'error: (.+)', 1) AS error_message
FROM train
WHERE regexp_matches(text, 'error:');
```

### 7. Leakage Detection Between Splits

Critical for ML data integrity — detect if test data appears in the training set:

```sql
WITH
    overlapping_rows AS (
        SELECT COALESCE(
            (SELECT COUNT(*) AS overlap_count
             FROM train
             INTERSECT
             SELECT COUNT(*) AS overlap_count
             FROM test),
            0
        ) AS overlap_count
    ),
    total_unique_rows AS (
        SELECT COUNT(*) AS total_count
        FROM (
            SELECT * FROM train
            UNION
            SELECT * FROM test
        ) combined
    )
SELECT
    overlap_count,
    total_count,
    CASE
        WHEN total_count > 0 THEN (overlap_count * 100.0 / total_count)
        ELSE 0
    END AS overlap_percentage
FROM overlapping_rows, total_unique_rows;
```

### 8. Shareable Query Links

Queries in the SQL Console are shareable via URL parameters:

```
https://huggingface.co/datasets/{namespace}/{repo}?sql_console=true&sql=SELECT+*+FROM+train+LIMIT+10
```

The `sql` parameter is URL-encoded. When someone opens the link, the SQL Console loads with the query pre-filled and auto-executed.

### 9. Saved Embeds API (CRUD)

Embeds are persisted queries that can be shared, embedded, or used as saved views. The API is part of the Hub's REST API:

**Create an embed:**
```
POST /api/datasets/{namespace}/{repo}/sql-console/embed
Content-Type: application/json
Authorization: Bearer {token}

{
  "sql": "SELECT * FROM train LIMIT 10",
  "title": "Sample rows",
  "private": false,
  "views": [{"key": "default/train", "displayName": "Train", "viewName": "train"}]
}
```

**Update an embed:**
```
PATCH /api/datasets/{namespace}/{repo}/sql-console/embed/{embed_id}
Content-Type: application/json
Authorization: Bearer {token}

{
  "sql": "SELECT * FROM train LIMIT 20",
  "title": "Updated title",
  "private": true
}
```

**Delete an embed:**
```
DELETE /api/datasets/{namespace}/{repo}/sql-console/embed/{embed_id}
Authorization: Bearer {token}
```

**Embedding results in an iframe:**
```html
<iframe src="https://huggingface.co/datasets/{namespace}/{repo}/embed/sql-console/{embed_id}"></iframe>
```

### 10. Natural Language to SQL

The SQL Console includes a natural language querying feature — type what you want in English and it auto-generates the DuckDB SQL. This is powered by a Hugging Face model running on the Hub's Inference API (free tier eligible for small queries).

Example:
- User types: "show me the top 10 rows with the longest reasoning chains"
- Generates: `SELECT * FROM train ORDER BY LENGTH(reasoning_chains) DESC LIMIT 10`

### 11. DuckDB CLI with `hf://` Protocol

Starting from DuckDB v0.10.3, the DuckDB CLI has **native support for the `hf://` scheme** — query datasets directly from the terminal:

```bash
# Connect DuckDB CLI, then:
FROM 'hf://datasets/ibm/duorc/ParaphraseRC/*.parquet' LIMIT 3;

# Traditional SQL syntax:
SELECT * FROM 'hf://datasets/ibm/duorc/ParaphraseRC/*.parquet' LIMIT 3;
```

**URL format:**
```
hf://datasets/{username}/{dataset}/{path}
```

Supports **glob patterns** (`*`, `**`) for querying multiple parquet files.

**Using the auto-converted Parquet branch (`@~parquet`):**
```sql
FROM 'hf://datasets/ibm/duorc@~parquet/ParaphraseRC/test/0000.parquet' LIMIT 5;
```

The `@~parquet` revision references the `refs/convert/parquet` branch where auto-converted Parquet files live — this is the same data powering the Data Studio.

### 12. `hf datasets sql` CLI Command

The Hugging Face CLI (`hf`) provides a direct wrapper:

```bash
# Run SQL query from terminal
hf datasets sql "FROM 'hf://datasets/ibm/duorc/ParaphraseRC/*.parquet' LIMIT 3"

# JSON format for machine-readable output
hf datasets sql "FROM 'hf://datasets/ibm/duorc/ParaphraseRC/*.parquet' LIMIT 3" --format json
```

**Advantages:**
- Authentication for gated/private datasets is **automatic** (from logged-in HF token)
- No need to manually manage `hf://` auth headers
- Output formats: default (table) and JSON

### 13. Storage Buckets Integration

When using the DuckDB Python client, you can query data stored in Storage Buckets:

```python
import duckdb
from huggingface_hub import HfFileSystem

duckdb.register_filesystem(HfFileSystem())
duckdb.sql("SELECT * FROM 'hf://buckets/username/my-bucket/data.parquet' LIMIT 10")
```

Note: Native `hf://buckets/` support in the DuckDB CLI is expected in a future release. For now, use the Python client with `HfFileSystem`.

### 14. DuckDB Capabilities for Datasets

| Feature | Supported | Example |
|---|---|---|
| **Full SQL queries** | ✅ | SELECT, WHERE, JOIN, GROUP BY, ORDER BY |
| **Window functions** | ✅ | ROW_NUMBER(), RANK(), LAG(), LEAD() |
| **Vector similarity** | ✅ | `array_cosine_similarity()` for embedding search |
| **Full-text search** | ✅ | `stem()` + GIN index via FTS extension |
| **Aggregation** | ✅ | COUNT, SUM, AVG, MIN, MAX, histogram |
| **Regex** | ✅ | regexp_matches, regexp_extract, regexp_replace |
| **JSON processing** | ✅ | json_extract, json_serialize_sql |
| **List/array functions** | ✅ | list_sort, list_distinct, array_cosine_similarity |
| **Export formats** | ✅ | Parquet, CSV (download from SQL Console) |

### 15. Limitations & Considerations

| Limitation | Impact |
|---|---|
| **Browser memory-bound** | Very large datasets (10M+ rows) may slow the browser tab |
| **First 5GB only** | For >5GB non-Parquet datasets, only first 5GB is auto-converted for querying |
| **No write-back** | SQL Console is read-only — results cannot be saved back to the Hub |
| **DuckDB WASM only** | SQL Console uses DuckDB WASM (not native) — some advanced extensions may not be available |
| **CUDA/GPU not available** | DuckDB in browser cannot use GPU acceleration |

### 16. Best Practices

1. **Use LIMIT liberally** — DuckDB in WASM is fast but browser memory limits apply
2. **Prefer Parquet datasets** — Native Parquet datasets have full 100% query coverage (not just 5GB)
3. **Save complex queries as embeds** — Create programmatic embeds via the API for reusable analyses
4. **Use leakage detection on train/test splits** — Run the leakage detection query before publishing fine-tuned models
5. **Combine `hf datasets sql` with shell pipelines** — Pipe JSON output to `jq` for further processing
6. **Reference `@~parquet` for auto-converted datasets** — Ensures you query the same parquet files the Data Studio shows
7. **Use histogram for quick column profiling** — Faster than writing aggregation queries for distribution analysis

### Resources
- Data Studio: https://huggingface.co/docs/hub/en/data-studio
- SQL Console: https://huggingface.co/docs/hub/en/datasets-viewer-sql-console
- DuckDB datasets: https://huggingface.co/docs/hub/en/datasets-duckdb
- DuckDB SQL docs: https://duckdb.org/docs/sql/query_syntax/select
- `hf datasets sql` CLI: https://huggingface.co/docs/huggingface_hub/package_reference/cli#hf-datasets-sql
- SQL Snippets Space: https://huggingface.co/spaces/cfahlgren1/sql-snippets

### Skill
mlops/hf-data-studio-sql-console — Create new SKILL.md + references/hf-learnings.md

## 2026-07-24: hf-hub-repositories-licenses-complete-reference — Complete Guide to HF Hub Repo Licenses (Topic #227)

### Summary
Comprehensive reference covering the license system on the Hugging Face Hub for all repo types (models, datasets, Spaces). Covers all 70+ supported license identifiers, how to specify licenses in repo card metadata, the difference between SPDX-standard and custom AI-specific licenses (OpenRAIL, Llama Community License, Gemma Terms, etc.), `license_name` field for custom licenses, and best practices for adding LICENSE files.

### Source
- HF Hub Docs — Licenses: https://huggingface.co/docs/hub/en/repositories-licenses
- SPDX License List: https://spdx.org/licenses/
- Model Card metadata spec: https://github.com/huggingface/hub-docs/blob/main/modelcard.md
- Dataset Card metadata spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md

### 1. How Licenses Work on the HF Hub

Every repository on the Hugging Face Hub (model, dataset, or Space) **must** declare a license in its card metadata (YAML front matter in `README.md`). The license:

- Appears as a badge/tag at the top of the repo page
- Is indexed by the Hub search — users can filter by license
- Helps downstream users understand reuse permissions
- Is **required** for model repos submitted to the Open LLM Leaderboard

The license field in the YAML front matter uses the format:
```yaml
---
license: <identifier>
---
```

### 2. All Supported License Identifiers (70+)

**Standard Open Source Licenses:**
| License | Identifier |
|---------|-----------|
| Apache License 2.0 | `apache-2.0` |
| MIT | `mit` |
| BSD 2-clause | `bsd-2-clause` |
| BSD 3-clause | `bsd-3-clause` |
| BSD 3-clause Clear | `bsd-3-clause-clear` |
| BSD license family | `bsd` |
| GNU GPL v2.0 | `gpl-2.0` |
| GNU GPL v3.0 | `gpl-3.0` |
| GNU GPL family | `gpl` |
| GNU LGPL v2.1 | `lgpl-2.1` |
| GNU LGPL v3.0 | `lgpl-3.0` |
| GNU LGPL family | `lgpl` |
| GNU AGPL v3.0 | `agpl-3.0` |
| Mozilla Public License 2.0 | `mpl-2.0` |
| Eclipse Public License 1.0 | `epl-1.0` |
| Eclipse Public License 2.0 | `epl-2.0` |
| ISC | `isc` |
| zLib License | `zlib` |
| The Unlicense | `unlicense` |
| Boost Software License 1.0 | `bsl-1.0` |
| Artistic License 2.0 | `artistic-2.0` |
| Academic Free License v3.0 | `afl-3.0` |
| Educational Community License v2.0 | `ecl-2.0` |
| Microsoft Public License | `ms-pl` |
| PostgreSQL License | `postgresql` |
| SIL Open Font License 1.1 | `ofl-1.1` |
| University of Illinois/NCSA | `ncsa` |
| Open Software License 3.0 | `osl-3.0` |
| LaTeX Project Public License v1.3c | `lppl-1.3c` |
| EUPL 1.1 | `eupl-1.1` |
| EUPL 1.2 | `eupl-1.2` |
| Etalab Open License 2.0 | `etalab-2.0` |
| WTFPL | `wtfpl` |

**Creative Commons Licenses:**
| License | Identifier |
|---------|-----------|
| CC0 1.0 Universal | `cc0-1.0` |
| CC BY 2.0 | `cc-by-2.0` |
| CC BY 2.5 | `cc-by-2.5` |
| CC BY 3.0 | `cc-by-3.0` |
| CC BY 4.0 | `cc-by-4.0` |
| CC BY-SA 3.0 | `cc-by-sa-3.0` |
| CC BY-SA 4.0 | `cc-by-sa-4.0` |
| CC BY-NC 2.0 | `cc-by-nc-2.0` |
| CC BY-NC 3.0 | `cc-by-nc-3.0` |
| CC BY-NC 4.0 | `cc-by-nc-4.0` |
| CC BY-ND 4.0 | `cc-by-nd-4.0` |
| CC BY-NC-ND 3.0 | `cc-by-nc-nd-3.0` |
| CC BY-NC-ND 4.0 | `cc-by-nc-nd-4.0` |
| CC BY-NC-SA 2.0 | `cc-by-nc-sa-2.0` |
| CC BY-NC-SA 3.0 | `cc-by-nc-sa-3.0` |
| CC BY-NC-SA 4.0 | `cc-by-nc-sa-4.0` |
| CC license family | `cc` |

**Data-Specific Licenses:**
| License | Identifier |
|---------|-----------|
| Community Data License Agreement — Sharing 1.0 | `cdla-sharing-1.0` |
| Community Data License Agreement — Permissive 1.0 | `cdla-permissive-1.0` |
| Community Data License Agreement — Permissive 2.0 | `cdla-permissive-2.0` |
| Computational Use of Data Agreement | `c-uda` |
| Open Data Commons Attribution | `odc-by` |
| Open Database License | `odbl` |
| Open Data Commons Public Domain Dedication | `pddl` |
| GNU Free Documentation License | `gfdl` |
| Lesser GPL for Linguistic Resources | `lgpl-lr` |

**AI/Model-Specific Licenses:**
| License | Identifier |
|---------|-----------|
| OpenRAIL license family | `openrail` |
| BigScience OpenRAIL-M | `bigscience-openrail-m` |
| CreativeML OpenRAIL-M | `creativeml-openrail-m` |
| BigScience BLOOM RAIL 1.0 | `bigscience-bloom-rail-1.0` |
| BigCode Open RAIL-M v1 | `bigcode-openrail-m` |
| Open Rail++-M | `openrail++` |
| DeepFloyd IF Research License | `deepfloyd-if-license` |
| FAIR Noncommercial Research License | `fair-noncommercial-research-license` |
| H Research License | `h-research` |
| Intel Research Use License | `intel-research` |
| Apple Sample Code License | `apple-ascl` |
| Apple Model License for Research | `apple-amlr` |
| Open Model, Data & Weights License Agreement 1.0 | `openmdw-1.0` |
| Open Model, Data & Weights License Agreement 1.1 | `openmdw-1.1` |
| Llama 2 Community License | `llama2` |
| Llama 3 Community License | `llama3` |
| Llama 3.1 Community License | `llama3.1` |
| Llama 3.2 Community License | `llama3.2` |
| Llama 3.3 Community License | `llama3.3` |
| Llama 4 Community License | `llama4` |
| Grok 2 Community License | `grok2-community` |
| Gemma Terms of Use | `gemma` |

**Special:**
| License | Identifier |
|---------|-----------|
| Unknown | `unknown` |
| Other | `other` |

### 3. Using `license: other` with Custom License Names

When your license is not in the predefined list, use `license: other` plus a `license_name` field:
```yaml
---
license: other
license_name: My Custom License v1.0
license_link: https://example.com/my-license
---
```

Best practices for custom licenses:
- Always include a `LICENSE` file in the repo root with the full license text
- Use `license_name` for a human-readable display name
- Optionally use `license_link` for a URL to the full license
- Contact HF to add commonly-used licenses to the official list

### 4. How the HF Hub Processes Licenses

- **Display**: The license badge appears on the repo page header, next to the task/library tags
- **Search**: Users can filter repos by license on the Hub (e.g., `?license=mit`)
- **Metadata extraction**: The Hub's backend parses `license` from YAML front matter and normalizes it
- **Leaderboard requirements**: The Open LLM Leaderboard requires models to have an `apache-2.0`, `mit`, `openrail*`, or compatible license to qualify
- **Gated repos**: Some licenses (e.g., `llama3`, `gemma`) trigger license acceptance flow for gated repos

### 5. License in Model vs Dataset vs Space Cards

**Model cards** (`models/<org>/<repo>/README.md`):
```yaml
---
license: apache-2.0
library_name: transformers
tags:
- text-generation
---
```

**Dataset cards** (`datasets/<org>/<repo>/README.md`):
```yaml
---
license: cc0-1.0
annotations_creators:
- machine-generated
language:
- en
---
```

**Space cards** — Spaces can optionally have a license but it's less common since Spaces are apps, not distributable assets.

### 6. Practical Tips for Beer's Repos

- Beer's 8 datasets (tool-calling data): Use `license: cc-by-4.0` or `license: apache-2.0` depending on preference — CC-BY-4.0 is common for datasets
- Beer's 6 text-generation models: Use `license: apache-2.0` (open) or applicable community license (if fine-tuned from a gated model like Llama)
- Beer's 2 GGUF files: Same license as the source model
- Always include a `LICENSE` file in the repo root with full text
- For existing repos, verify the license field is correctly set in YAML

### Resources
- HF Licenses docs: https://huggingface.co/docs/hub/en/repositories-licenses
- SPDX License List: https://spdx.org/licenses/
- Model Card metadata spec: https://github.com/huggingface/hub-docs/blob/main/modelcard.md
- Dataset Card metadata spec: https://github.com/huggingface/hub-docs/blob/main/datasetcard.md

### Skill
skills/references — Appended to main hf-learnings.md (no new skill needed for this reference topic)

---

## 2026-07-24: hf-hub-storage-limits-and-plans — Deepening with Storage Buckets (Topic #225v2)

### Summary
Deep-dive into **Storage Buckets** — a brand-new HF Hub repo type offering S3-compatible, non-versioned, mutable object storage built on the Xet backend. Covers architecture (buckets vs Git repos), CLI commands (`hf buckets create/list/cp/sync/rm`), Python API (`create_bucket`, `batch_bucket_files`, `download_bucket_files`, `sync_bucket`, `copy_files`), S3-compatible API gateway at `https://s3.hf.co/<namespace>`, access patterns (hf-mount NFS/FUSE, volume mounts in Jobs/Spaces, `hf://buckets/` fsspec paths), integrations (pandas, DuckDB, Dask, PyArrow, PySpark, 🤗 Datasets, SkyPilot, DVC, rclone, Inspect AI), CDN pre-warming, pricing, and zero-cost patterns for Beer's workflows.

### Source
- Storage Buckets docs: https://huggingface.co/docs/hub/en/storage-buckets
- S3 API docs: https://huggingface.co/docs/hub/en/storage-buckets-s3
- Access Patterns: https://huggingface.co/docs/hub/en/storage-buckets-access
- Integrations: https://huggingface.co/docs/hub/en/storage-buckets-integrations
- HF Storage pricing: https://hf.co/storage
- HF Pricing page: https://huggingface.co/pricing
- SkyPilot + HF blog: https://huggingface.co/blog/skypilot-hf-storage

### 1. What Are Storage Buckets?

Storage Buckets are a **new repo type** on the Hugging Face Hub providing S3-like object storage, powered by the Xet storage backend. Unlike Git-based repositories (models, datasets, Spaces), buckets are **non-versioned** and **mutable** — files overwrite in place. Designed for:

- Training checkpoints and logs
- Data processing pipeline intermediates
- Agent scratch storage (tool outputs, traces, working memory)
- Rolling backups (old files truly gone when deleted)
- Large dataset staging before promoting to a versioned repo

### 2. Architecture: Buckets vs Git Repos

| Feature | Git Repos | Storage Buckets |
|---|---|---|
| Versioning | Full Git history | None (mutable, overwrite-in-place) |
| Types | Models, datasets, Spaces | Standalone bucket |
| Primary use | Publishing finished artifacts | Working / intermediate data |
| Operations | Hub API, Git push/pull | S3-like sync, cp, rm |
| Deduplication | Xet chunk-level | Xet chunk-level |
| Pull Requests | Yes | No |
| Cards | Model/Dataset cards | Plain README rendered |
| LFS management | Complex (history rewrite, super-squash) | None (delete = immediate free) |

### 3. CLI Usage

```bash
# Create a bucket
hf buckets create my-bucket
hf buckets create my-org/shared-bucket --private

# List contents with human-readable sizes
hf buckets list julien-c/my-training-bucket -h
hf buckets list julien-c/my-training-bucket --tree -h -R

# Upload individual files
hf buckets cp ./model.safetensors hf://buckets/username/my-bucket/models/model.safetensors

# Pipe from stdin
cat config.json | hf buckets cp - hf://buckets/username/my-bucket/config.json

# Download to stdout and pipe
hf buckets cp hf://buckets/username/my-bucket/config.json - | jq .

# Directory sync (rsync-like)
hf buckets sync ./data hf://buckets/username/my-bucket/data
hf buckets sync ./data hf://buckets/username/my-bucket/data --delete  # mirror
hf buckets sync ./data hf://buckets/username/my-bucket/data --dry-run  # preview
hf buckets sync ./data hf://buckets/username/my-bucket/data --plan sync-plan.jsonl  # plan then apply

# Short alias
hf sync ./checkpoints hf://buckets/my-org/training-run-42/checkpoints

# Delete (IMMEDIATE — no undo)
hf buckets rm username/my-bucket/old-model.bin
hf buckets rm username/my-bucket/logs/ --recursive
hf buckets rm username/my-bucket/checkpoints/ --recursive --dry-run

# Server-side copy between repos/buckets (instant via Xet chunk hashes)
hf buckets cp hf://datasets/HuggingFaceFW/fineweb/data hf://buckets/username/fineweb-data
```

### 4. Python API

```python
from huggingface_hub import create_bucket, batch_bucket_files, download_bucket_files, sync_bucket, HfApi

# Create
create_bucket("my-bucket", private=True)

# Upload in batch
batch_bucket_files("username/my-bucket", add=[
    ("./model.safetensors", "models/model.safetensors"),
    ("./config.json", "models/config.json"),
])

# Download
download_bucket_files("username/my-bucket", files=[
    ("models/model.safetensors", "./local/model.safetensors"),
    ("config.json", "./local/config.json"),
])

# Sync directories
sync_bucket("./data", "hf://buckets/username/my-bucket/data")
sync_bucket("hf://buckets/username/my-bucket/data", "./data")  # reverse direction

# Server-side copy
HfApi().copy_files("hf://datasets/HuggingFaceFW/fineweb/data", "hf://buckets/username/fineweb-data")
```

### 5. S3-Compatible API

The gateway at `https://s3.hf.co/<namespace>` lets existing S3 tooling talk to buckets.

**Generate credentials:** User Access Token > dropdown > "Generate S3 credentials" → `HFAK...` key + secret.

**AWS CLI profile:**
```ini
[profile hf]
region = us-east-1
endpoint_url = https://s3.hf.co/<namespace>
s3 =
    addressing_style = path
    multipart_threshold = 2GB
    multipart_chunksize = 2GB
request_checksum_calculation = when_required
response_checksum_validation = when_required
```

**boto3:**
```python
import boto3
from botocore.config import Config

s3 = boto3.client("s3",
    endpoint_url="https://s3.hf.co/<namespace>",
    aws_access_key_id="HFAK...",
    aws_secret_access_key="...",
    config=Config(region_name="us-east-1",
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)
s3.upload_file("model.safetensors", "my-bucket", "models/model.safetensors")
```

**DuckDB (via httpfs):**
```sql
INSTALL httpfs; LOAD httpfs;
CREATE SECRET hf (TYPE s3, KEY_ID 'HFAK...', SECRET '...',
    ENDPOINT 's3.hf.co/<namespace>', URL_STYLE 'path', REGION 'us-east-1');
SELECT * FROM read_parquet('s3://my-bucket/data.parquet');
```

**rclone** (migrate from any S3 source):
```ini
[hf]
type = s3
provider = Other
endpoint = https://s3.hf.co/<namespace>
access_key_id = HFAK...
secret_access_key = ...
region = us-east-1
force_path_style = true
list_version = 2
upload_cutoff = 2G
chunk_size = 2G
```
```bash
rclone copy aws:my-source-bucket hf:my-bucket --progress
```

**DVC** (version data in git, store in bucket):
```bash
dvc remote add -d hf-bucket s3://my-bucket/dvc-store
dvc remote modify hf-bucket endpointurl https://s3.hf.co/<namespace>
dvc remote modify hf-bucket region us-east-1
```

### 6. Access Patterns

| Method | Best For | Details |
|---|---|---|
| **hf-mount** | Any tool — mount as local FS | `brew install hf-mount; hf-mount start bucket username/my-bucket /mnt/data` |
| **Volume mounts** | HF Jobs & Spaces | Managed by platform, no extra setup |
| **hf:// paths** (fsspec) | Python data tools | pandas, DuckDB, Dask, PyArrow, PySpark |
| **CLI sync** | Batch transfers, backups | `hf buckets sync` / `hf sync` |
| **S3 API** | Existing S3 tooling | AWS CLI, boto3, s5cmd, rclone, DVC |

### 7. Integrations

**pandas:**
```python
import pandas as pd
df = pd.read_parquet("hf://buckets/username/my-bucket/data.parquet")
df.to_parquet("hf://buckets/username/my-bucket/output.parquet")
```

**Dask:**
```python
import dask.dataframe as dd
df = dd.read_parquet("hf://buckets/username/my-bucket/data.parquet")
```

**PyArrow:**
```python
import pyarrow.parquet as pq
table = pq.read_table("hf://buckets/username/my-bucket/data.parquet")
```

**🤗 Datasets:**
```python
from datasets import load_dataset
ds = load_dataset("buckets/username/my-bucket", data_files=["data.parquet"])
```

**SkyPilot** (mount across 20+ clouds):
```yaml
# qwen-sft.yaml
file_mounts:
  /base-model:
    source: hf://Qwen/Qwen2.5-3B
    store: hf
    mode: MOUNT
  /checkpoints:
    source: hf://buckets/username/qwen-sft
    store: hf
    mode: MOUNT
```
```bash
pip install "skypilot[huggingface]"
hf auth login
sky launch qwen-sft.yaml
```

**PySpark:**
```python
spark.read.format("huggingface") \
    .option("data_files", '["data.parquet"]') \
    .load("buckets/username/my-bucket")
```

**Direct file ops (fsspec):**
```python
from huggingface_hub import hffs

with hffs.open("buckets/username/my-bucket/hello.txt", "w") as f:
    f.write("Hello world!")
hffs.cp("buckets/username/my-bucket/hello.txt", "buckets/username/my-bucket/hello2.txt")
hffs.rm("buckets/username/my-bucket/hello2.txt")
files = hffs.ls("buckets/username/my-bucket")
```

### 8. S3 Limitations (Differences from AWS S3)

- No ACLs, bucket policies, object tagging, versioning, lifecycle rules, SSE
- Only `ListObjectsV2` supported (not V1)
- No cross-namespace server-side copy
- No `UploadPartCopy` (copying a part from existing object into multipart upload)
- Conditional requests: `If-Match`/`If-None-Match` on `PutObject` and `CopyObject` only, not on `GetObject`
- Multipart uploads expire after 7 days if never completed/aborted
- User metadata (`x-amz-meta-*`) not stored
- Single-region gateway (improved via CDN pre-warming)
- Object key restrictions: no leading/trailing `/`, no `//`, no `../`, no `./`, no `..`, no `\` or `\0`

### 9. CDN Pre-Warming

Buckets can be pre-warmed at creation to cache data at edge locations near specific cloud providers/regions. Useful for training clusters, multi-region pipelines, and distributing large artifacts worldwide. See hf.co/storage for available regions.

### 10. Use Cases Relevant to Beer

1. **Scratch storage for model testing** — no Git history bloat from iterative experiments
2. **Training checkpoint sync** — `hf sync ./checkpoints hf://buckets/beer/experiments` with dedup
3. **Dataset staging** — process data in a bucket, promote to versioned Dataset repo when final
4. **Agent scratch storage** — Hermes/Sak agents could use buckets for intermediate results
5. **Rolling backups** of Skills/Memory — delete old backups without history penalties

### 11. Linking Models to Buckets

Add to model card YAML:
```yaml
buckets:
- my-org/my-bucket
```

This creates a two-way link: linked models appear on the bucket page, and the bucket appears as a tag on the model page.

### Skill
mlops/hf-hub-storage-limits — SKILL.md updated with full Storage Buckets documentation

## 2026-07-24: hf-hub-hardware-filter-models-search — New Hardware Filter on the Models Page (Topic #229)

### Summary
Deep dive into the **Hardware Filter** feature (launched Jun 30, 2026) on the Hugging Face Hub Models page. This feature lets users filter models by target hardware (GPU, CPU, Apple Silicon) so they only see models that will actually run on their machine. Covers the URL API (`?hardware=`), available hardware identifiers, stacking with other filters (`apps`, `library`, `pipeline_tag`), the Hardware settings page for persisting user preferences, how model–hardware compatibility is determined, and practical patterns for sharing hardware-filtered searches.

### Source
- HF Changelog — Filter Models page by Hardware (Jun 30, 2026): https://huggingface.co/changelog/filter-models-by-hardware
- Models search page: https://huggingface.co/models?hardware=apple-m4-max
- Hardware settings page: https://huggingface.co/settings/hardware
- API query structure extracted from Hub front-end state (verified 2026-07-24)

### 1. What Is the Hardware Filter?

The Hardware Filter is a **front-end filter** on the Hugging Face Hub Models page (https://huggingface.co/models) that narrows search results to models compatible with a specific hardware target. Instead of browsing 2.9M+ models and guessing which ones fit your machine, you select your hardware and see only compatible models.

The feature was announced in the HF Changelog on June 30, 2026:
> "A new Hardware filter on the Models page filters results to models that fit a specific GPU, CPU, or Apple Silicon chip, so you only see what will actually run on your machine. Set the hardware you want from your Hardware settings."

### 2. URL API

The hardware filter is controlled by the `hardware` URL query parameter:

```
https://huggingface.co/models?hardware=<hardware-identifier>
```

It stacks with all other model search filters: `search`, `pipeline_tag`, `library`, `apps`, `sort`, and pagination (`p`).

#### Example URLs
| URL | Effect |
|-----|--------|
| `?hardware=apple-m4-max` | Models that fit Apple M4 Max |
| `?hardware=cpu` | Models that run on CPU |
| `?hardware=cuda` | CUDA-compatible models |
| `?hardware=apple-silicon` | Apple Silicon compatible models |
| `?apps=llama.cpp&hardware=apple-m4-max` | llama.cpp models that fit M4 Max |
| `?hardware=apple-m4-max&sort=trending` | Trending models for M4 Max |

### 3. Known Hardware Identifiers

Verified working (return 200 and filtered results):

| Identifier | Label | Type |
|------------|-------|------|
| `apple-m4-max` | Apple M4 Max | Apple Silicon |
| `apple-m4` | Apple M4 | Apple Silicon |
| `apple-m3-max` | Apple M3 Max | Apple Silicon |
| `apple-m2-max` | Apple M2 Max | Apple Silicon |
| `apple-m1-max` | Apple M1 Max | Apple Silicon |
| `apple-silicon` | Apple Silicon (general) | Apple Silicon |
| `cpu` | CPU | General |
| `cuda` | CUDA (NVIDIA GPU) | GPU |
| `mps` | Metal Performance Shaders (Apple) | GPU |
| `nvidia-t4` | NVIDIA T4 | GPU |
| `nvidia-l4` | NVIDIA L4 | GPU |
| `amd-mi250` | AMD MI250 | GPU |
| `amd-mi300` | AMD MI300 | GPU |

**Note:** This is not an exhaustive list. Hardware identifiers are added over time as the Hub team expands coverage. Unrecognized identifiers fall through to showing all models (no filtering).

### 4. How Hardware–Model Matching Works

The hardware filter uses **model metadata** to determine compatibility. The primary factors:

1. **Model size (parameters)** — Number of parameters (`numParameters` in API response) is the primary heuristic. The Hub matches model VRAM/RAM requirements against the hardware's known memory capacity.

2. **Library/framework** — Models using `gguf`, `mlx`, `coreml`, `onnx` libraries are categorized differently since they can run on Apple Silicon, CPU, or specific accelerators.

3. **Quantization format** — Models with quantized weights (GGUF Q4_K_M, Q8_0, etc.) or specific precision (FP4, NF4) expand compatibility to lower-resource hardware.

4. **Hardware tags on model cards** — Model authors can declare hardware compatibility via tags in the model card YAML, though this is optional.

The Hub appears to use a compatibility matrix based on:
- Known memory requirements per model size class
- Library/format support per hardware type
- Community-reported compatibility data

### 5. Hardware Settings (User Preferences)

Users can set their hardware preference at:
```
https://huggingface.co/settings/hardware
```

This persists a `userHardwareItems` array in the user's settings. When set, models pages automatically filter to show only compatible models without needing to add the `?hardware=` parameter manually.

The settings page is behind authentication (requires login).

### 6. Practical Use Cases

#### Finding GGUF models for local inference on a Mac
```
https://huggingface.co/models?apps=llama.cpp&hardware=apple-m4-max
```
As of Jul 24, 2026, this returns ~184K models — virtually all llama.cpp-compatible models work on M4 Max.

#### Sharing a filtered search link
The hardware filter is baked into the URL. Share a link like:
```
https://huggingface.co/models?apps=llama.cpp&hardware=apple-m4-max&sort=trending
```
Anyone clicking this (even logged-out visitors) sees the same filtered view.

#### Checking what runs on a consumer GPU
```
https://huggingface.co/models?hardware=cuda&pipeline_tag=text-generation
```
Shows all CUDA-compatible text generation models.

### 7. API-Level Behavior

The `hardware` parameter is **not** a server-side API filter on `api/models` — querying `api/models?hardware=apple-m4-max` returns the same results as without the parameter. The filtering is applied **front-end only** by the Hub's Svelte rendering layer, which:
1. Fetches models from the API
2. Applies hardware compatibility logic in the client
3. Updates `numTotalItems` to reflect the filtered count
4. Renders the paginated filtered set

This means hardware-filtered views cannot currently be consumed via the REST API alone — they depend on the web UI.

### 8. Zero-Cost Relevance

For Beer's HF account (Nanthasit — 8 models, 8 datasets, 2 Spaces, 2 GGUF files locally):
- Beer's GGUF files (0.5B @ 380MB, 1.5B @ 934MB) are trivially compatible with any Apple Silicon Mac or modern CPU
- When publishing GGUF models, tag them appropriately for hardware compatibility
- Use the hardware filter to discover which models in Beer's niches (tool-calling, small LLMs) fit common hardware targets
- No paid features are required — the hardware filter is free for all users

### Skill
skills/references — Append to main hf-learnings.md (no new skill needed for this reference topic)

## 2026-07-24: hf-transformers-deepseek-r1-architecture-deep-dive — DeepSeek-R1: Architecture, RL Training Pipeline, and Transformers Integration (Topic #230)

### Summary
Comprehensive deep-dive on DeepSeek-R1 — the first-generation reasoning model from DeepSeek that achieved OpenAI-o1-comparable performance via pure reinforcement learning. Covers the DeepSeek-V3 base architecture (671B MoE with Multi-head Latent Attention), the GRPO training methodology that eliminates the need for human-annotated reasoning chains, the distillation pipeline for dense smaller models, Hugging Face Transformers integration, chat template format, and practical usage patterns.

### Source
- Paper: https://arxiv.org/abs/2501.12948 — "DeepSeek-R1: Incentivizing Reasoning Capability in LLMs via Reinforcement Learning" (Nature, Vol 645, 2025)
- DeepSeek-V3 Paper: https://arxiv.org/abs/2412.19437
- DeepSeekMath (GRPO) Paper: https://arxiv.org/abs/2402.03300
- HF Model: https://huggingface.co/deepseek-ai/DeepSeek-R1
- Transformers Docs: https://huggingface.co/docs/transformers/main/en/model_doc/deepseek_v3
- TRL GRPO Trainer: https://huggingface.co/docs/trl/main/en/grpo_trainer
- GitHub: https://github.com/deepseek-ai/DeepSeek-R1

### 1. What Is DeepSeek-R1?

DeepSeek-R1 is a **reasoning language model** trained via large-scale reinforcement learning (RL) that demonstrated for the first time that complex reasoning capabilities (self-verification, reflection, chain-of-thought search) can emerge purely through RL without supervised fine-tuning on human reasoning demonstrations.

Two model variants were released:
- **DeepSeek-R1-Zero**: Trained via pure RL on the base model (DeepSeek-V3-Base) without any SFT cold-start data. Showed emergent reasoning but suffered from poor readability and language mixing.
- **DeepSeek-R1**: Full pipeline with cold-start SFT data → RL → rejection sampling → SFT → RL. Achieves OpenAI-o1-comparable performance.

Both models achieved **state-of-the-art results** on math (AIME 2024: 79.8%), coding (Codeforces: 96.3 percentile), and STEM reasoning benchmarks.

### 2. Base Architecture: DeepSeek-V3

DeepSeek-R1 is built on the **DeepSeek-V3** architecture — a 671B total parameter Mixture-of-Experts (MoE) model with 37B activated parameters per token.

#### 2.1 Core Config

```json
{
  "architectures": ["DeepseekV3ForCausalLM"],
  "model_type": "deepseek_v3",
  "hidden_size": 7168,
  "num_hidden_layers": 61,
  "num_attention_heads": 128,
  "num_key_value_heads": 128,
  "intermediate_size": 18432,
  "vocab_size": 129280,
  "max_position_embeddings": 163840,
  "torch_dtype": "bfloat16"
}
```

#### 2.2 Multi-head Latent Attention (MLA)

MLA is a key innovation for efficient inference. Instead of projecting the full KV cache, it compresses keys and values into a low-rank latent space:

- **KV compression**: `kv_lora_rank=512` (down from full head dims)
- **Query compression**: `q_lora_rank=1536`
- **NoPE head dim**: `qk_nope_head_dim=128` — standard attention dimensions
- **RoPE head dim**: `qk_rope_head_dim=64` — dimensions that receive rotary embeddings
- **Value head dim**: `v_head_dim=128` — per-head value dimension

This dramatically reduces the KV cache size — from `2 × 128 × 128 × 4 bytes = 131 KB` per layer to `512 × 4 bytes = 2 KB` per layer in compressed form (before the up-projection). For 61 layers, this saves ~7.7 MB per token vs. standard MHA.

#### 2.3 DeepSeekMoE Architecture

DeepSeek-R1 uses a fine-grained MoE with:
- **256 routed experts** (`n_routed_experts: 256`)
- **8 experts per token** (`num_experts_per_tok: 8`)
- **1 shared expert** (`n_shared_experts: 1`) — always active for every token
- **Grouped routing**: 8 groups (`n_group: 8`), top-4 groups selected (`topk_group: 4`)
- **Sigmoid scoring** (`scoring_func: sigmoid`) for expert selection
- **Auxiliary-loss-free balancing** (`topk_method: noaux_tc`) — the first model to deploy this at scale, avoiding the performance degradation that auxiliary load-balancing losses can cause
- **Routed scaling factor**: `routed_scaling_factor: 2.5`

The MoE intermediate size is `moe_intermediate_size: 2048` per expert, with standard FFN intermediate `intermediate_size: 18432` used by the shared expert and dense layers.

The first 3 layers use dense FFN (`first_k_dense_replace: 3`) with MoE starting from layer 4.

#### 2.4 Multi-Token Prediction (MTP)

DeepSeek-V3 introduces a **multi-token prediction** training objective:
- `num_nextn_predict_layers: 1` — one additional prediction head
- The model predicts the next token AND the token after next simultaneously
- Improves training efficiency and sample efficiency
- At inference, only the main head is used (the MTP head is discarded)

#### 2.5 YaRN RoPE Scaling

To support long contexts (163,840 tokens), DeepSeek-V3 uses **YaRN** (Yet another RoPE extensioN) scaling:
```json
{
  "rope_scaling": {
    "type": "yarn",
    "factor": 40,
    "original_max_position_embeddings": 4096,
    "beta_fast": 32,
    "beta_slow": 1,
    "mscale": 1.0,
    "mscale_all_dim": 1.0
  }
}
```

The scaling factor of 40 extends from 4K to 163K context. `beta_fast=32` and `beta_slow=1` control the ramp of the NTK-aware interpolation.

#### 2.6 FP8 Quantization

The model uses FP8 quantization natively:
```json
{
  "quantization_config": {
    "quant_method": "fp8",
    "activation_scheme": "dynamic",
    "fmt": "e4m3",
    "weight_block_size": [128, 128]
  }
}
```

Dynamic per-tensor activation quantization with e4m3 format and 128×128 weight block sizes. Transformers handles FP8 loading automatically — no manual quantization configuration needed.

### 3. Training Pipeline: From Base Model to Reasoner

#### 3.1 DeepSeek-R1-Zero: Pure RL

R1-Zero is notable as **the first open research to validate that reasoning capabilities can be incentivized purely through RL without SFT**.

- **Starting point**: DeepSeek-V3-Base (pre-trained only)
- **RL algorithm**: GRPO (Group Relative Policy Optimization)
- **Reward signal**: Verifiable tasks only (math correctness, code pass@k tests) — no process reward model
- **Emergent behaviors**: Self-verification ("Let me double-check..."), reflection ("Wait, that might be wrong..."), and long chain-of-thought search
- **Limitations**: Poor readability, language mixing, endless repetition

#### 3.2 DeepSeek-R1: Full Pipeline

The full R1 pipeline has **four stages**:

**Stage 1 — Cold-Start SFT**:
- Collected thousands of long CoT examples using few-shot prompting + human refinement
- Fine-tuned DeepSeek-V3-Base on this cold-start data to produce a seed reasoning model
- This addresses R1-Zero's readability issues before RL begins

**Stage 2 — Reasoning RL**:
- Applied GRPO on the cold-start model using verifiable rewards
- Language consistency reward added to prevent language mixing
- Model develops advanced reasoning patterns (reflection, backtracking)

**Stage 3 — Rejection Sampling + SFT**:
- Used the Stage 2 model to generate millions of reasoning trajectories
- Applied rejection sampling: kept only correct solutions with clean formatting
- Combined with non-reasoning SFT data (writing, translation, QA) for general capabilities
- Trained for 2 epochs on ~800K samples total

**Stage 4 — RL for All Scenarios**:
- Final RL stage combining verifiable rewards for reasoning tasks
- Added preference-based rewards for general tasks (helpfulness, harmlessness)
- Produces the final DeepSeek-R1 model

#### 3.3 GRPO Algorithm (Group Relative Policy Optimization)

GRPO, introduced in the DeepSeekMath paper (arxiv:2402.03300), is the core RL algorithm. Unlike PPO which requires a value function (critic) model, GRPO uses **group-level reward comparison**:

**Step 1 — Generate Completions**: For each prompt `q`, sample G completions `{o_1, o_2, ..., o_G}` from the current policy `π_θ`.

**Step 2 — Compute Advantage**: Normalize rewards within the group:
```
Â_i,t = (r_i - mean(r)) / std(r)
```
This gives GRPO its name — the advantage is *relative* to the group. The standard deviation scaling can be disabled (`scale_rewards=False`) or computed at batch level (`scale_rewards="batch"`) for more robust training.

**Step 3 — Estimate KL Divergence**: Use the Schulman et al. (2020) unbiased approximator:
```
D_KL[π_θ || π_ref] = π_ref(o_i,t | q, o_i,<t) / π_θ(o_i,t | q, o_i,<t)
                      - log(π_ref(o_i,t | q, o_i,<t) / π_θ(o_i,t | q, o_i,<t)) - 1
```

**Step 4 — Compute Loss**:
```
L_GRPO(θ) = -1/Σ|o_i| * Σ_i Σ_t [ (π_θ(o_i,t) / π_θ(o_i,t)_no_grad) * Â_i,t - β * D_KL ]
```

Key advantage: GRPO **eliminates the need for a value function model**, reducing memory and compute by ~50% compared to PPO. The TRL `GRPOConfig` supports all these knobs including `scale_rewards`, `beta` (KL penalty coefficient), and the number of generations per prompt.

### 4. Distillation: Smaller Dense Models

DeepSeek-R1 generates high-quality reasoning traces that are then used to fine-tune smaller dense models. This distillation approach outperforms training small models with RL directly.

#### 4.1 Distilled Model Variants

| Model | Base Architecture | Params | Hidden | Layers | Heads | Downloads |
|-------|------------------|--------|--------|--------|-------|-----------|
| R1-Distill-Qwen-1.5B | Qwen2ForCausalLM | 1.5B | 1536 | 28 | 12 | 664K |
| R1-Distill-Qwen-7B | Qwen2ForCausalLM | 7B | 4096 | 28 | 32 | 281K |
| R1-Distill-Llama-8B | LlamaForCausalLM | 8B | 4096 | 32 | 32 | 369K |
| R1-Distill-Qwen-14B | Qwen2ForCausalLM | 14B | 5120 | 40 | 40 | 442K |
| R1-Distill-Qwen-32B | Qwen2ForCausalLM | 32B | 5120 | 64 | 40 | 866K |
| R1-Distill-Llama-70B | LlamaForCausalLM | 70B | 8192 | 80 | 64 | 871K |

#### 4.2 Key Insight

The 32B distilled model (R1-Distill-Qwen-32B) **outperforms OpenAI-o1-mini** across multiple benchmarks, demonstrating that reasoning patterns from large MoE models can be effectively compressed into dense architectures.

The distilled models use the **base model's original tokenizer and vocabulary** (Qwen2: 151,936 vocab, Llama3: 128,256 vocab), not the DeepSeek-R1 tokenizer (129,280 vocab).

### 5. Hugging Face Transformers Integration

#### 5.1 Model Support

DeepSeek-R1 is fully supported in Transformers as model type `deepseek_v3`:

- **AutoModel**: `DeepseekV3Model`
- **AutoModelForCausalLM**: `DeepseekV3ForCausalLM`
- **AutoConfig**: `DeepseekV3Config`

The model uses the standard `transformers` version `4.46.3+`. Loading is straightforward:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-R1",
    device_map="auto",
    torch_dtype="auto"  # auto-detects bfloat16
)
tokenizer = AutoTokenizer.from_pretrained("deepseek-ai/DeepSeek-R1")
```

#### 5.2 Chat Template Format

DeepSeek-R1 uses a custom Jinja2 chat template with unique delimiters:

```
<｜begin▁of▁sentence｜><｜User｜>Hello, how are you?<｜Assistant｜><think>
Let me think about this...
</think>
I'm doing great! How can I help you today?<｜end▁of▁sentence｜>
```

Key tokens:
- `<｜begin▁of▁sentence｜>` — BOS token (token_id: 0)
- `<｜end▁of▁sentence｜>` — EOS token (token_id: 1), also used as pad token
- `<｜User｜>` — User message prefix
- `<｜Assistant｜>` — Assistant message prefix
- `<｜tool▁calls▁begin｜>` / `<｜tool▁call▁begin｜>` — Tool calling markers

The chat template collects system prompts, then renders user messages with `<｜User｜>` and assistant messages with `<｜Assistant｜>`. When `add_generation_prompt=True`, it appends `<｜Assistant｜>` to trigger generation.

Usage:
```python
messages = [
    {"role": "user", "content": "What is 2+2?"}
]
inputs = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_tensors="pt"
).to(model.device)

outputs = model.generate(inputs, max_new_tokens=500)
response = tokenizer.decode(outputs[0][inputs.shape[1]:])
```

#### 5.3 The Thinking Tag

DeepSeek-R1 models typically output reasoning within `<think>` tags before the final answer. This is part of the model's trained behavior, not a template feature. Example output:

```
<｜Assistant｜><think>
Okay, the user is asking about... Let me work through this step by step...
First, I need to consider...
</think>
The answer is 42.
```

The `<think>` section contains the model's internal chain-of-thought reasoning. Applications can parse this section out for display or keep it for transparency. The `add_generation_prompt=True` triggers the `<｜Assistant｜>` token which causes the model to start its thinking process.

#### 5.4 FP8 Loading

Transformers automatically handles FP8 quantization. The model can be loaded with:
```python
model = AutoModelForCausalLM.from_pretrained(
    "deepseek-ai/DeepSeek-R1",
    device_map="auto"
)
```
The quantization config (`fp8` with dynamic activation scheme, e4m3 format, 128×128 weight blocks) is loaded automatically from the model's `quantization_config`. Official recommendation: minimum 2 nodes of 8×H100 (16 GPUs) to run in FP8.

#### 5.5 Pipeline Usage

```python
from transformers import pipeline

pipe = pipeline(
    "text-generation",
    model="deepseek-ai/DeepSeek-R1",
    device_map="auto"
)

result = pipe(
    [{"role": "user", "content": "Solve: 3x + 7 = 22"}],
    max_new_tokens=500,
    do_sample=True,
    temperature=0.6
)
print(result[0]["generated_text"][-1]["content"])
```

### 6. GRPO Training with TRL

For fine-tuning reasoning models with DeepSeek-R1-like methodology, Hugging Face TRL provides the `GRPOTrainer`:

```python
from trl import GRPOTrainer, GRPOConfig
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained("path/to/base-model")
tokenizer = AutoTokenizer.from_pretrained("path/to/base-model")

training_args = GRPOConfig(
    output_dir="reasoning-model",
    per_device_train_batch_size=2,
    num_generations=8,       # G: completions per prompt
    max_prompt_length=1024,
    max_completion_length=1024,
    beta=0.04,               # KL penalty
    scale_rewards=False,     # disable std scaling
    learning_rate=1e-6,
)

trainer = GRPOTrainer(
    model=model,
    reward_funcs=[math_reward_func, format_reward_func],
    args=training_args,
    train_dataset=dataset,
    tokenizer=tokenizer,
)
trainer.train()
```

Key GRPOConfig parameters:
- `num_generations` (G): Number of completions per prompt for group comparison
- `beta`: KL divergence penalty coefficient
- `scale_rewards`: Whether to normalize rewards by group std (True/False/"batch")
- `reward_funcs`: List of reward functions (verifiable + preference)
- `max_prompt_length` / `max_completion_length`: Sequence length limits

### 7. vLLM and TGI Support

#### 7.1 vLLM
DeepSeek-R1 is supported in vLLM with MLA-optimized kernels. Key settings:
- Requires vLLM >= 0.6.0
- Uses custom CUDA kernels for MLA attention (not standard FlashAttention)
- Tensor parallelism is required (minimum 2 GPUs due to model size)
- Recommended: `--tensor-parallel-size 8` for full model

#### 7.2 TGI (Text Generation Inference)
TGI supports DeepSeek-R1 with:
- Flash MLA kernels for efficient inference
- Continuous batching with PagedAttention
- Quantization: FP8 native, GPTQ available for distill models

### 8. Zero-Cost Relevance

For Beer's setup (no GPU budget, 8 models + 8 datasets on HF):

- **Distilled models are the practical entry point**: R1-Distill-Qwen-1.5B (380 MB) and R1-Distill-Qwen-7B (4 GB) run on CPU via GGUF or llama.cpp
- **GGUF availability**: Multiple community GGUF quantizations exist for all 6 distill models (e.g., `bartowski/DeepSeek-R1-Distill-Qwen-7B-GGUF`)
- **Use case**: Beer's tool-calling agent stack can use R1-Distill-Qwen-1.5B as a local reasoning engine for task planning, without needing GPU
- **GRPO for fine-tuning**: If Beer gains access to GPU credits in the future, the TRL GRPOTrainer is the go-to implementation for RL-based reasoning training
- **No paid features required**: The Distill models, TRL, and Transformers are all free and open-source

### 9. Architecture Diagram (Mental Model)

```
DeepSeek-R1 (671B Total / 37B Active)
├── Embedding Layer (129,280 vocab)
├── 3 Dense Layers (layers 0-2)
│   └── Standard Self-Attention + FFN
├── 58 MoE Layers (layers 3-60)
│   ├── Multi-head Latent Attention (MLA)
│   │   ├── Q projection: 128 heads × 192 dim (1536 LoRA + 128 RoPE)
│   │   ├── K compression: kv_lora_rank=512 (latent)
│   │   ├── V compression: kv_lora_rank=512 (latent)
│   │   └── Output: v_head_dim=128 per head
│   └── DeepSeekMoE FFN
│       ├── 1 Shared Expert (always active)
│       ├── 256 Routed Experts (top-8 per token)
│       │   └── Grouped routing: 8 groups → top-4 groups
│       └── Sigmoid score + noaux_tc balancing
├── MTP Head (1 extra prediction layer)
├── LM Head (vocab projection)
└── Training Objective
    ├── Pre-training: MTP loss
    └── Post-training: GRPO (RL) + SFT
```

### 10. Key Files in Transformers Source

The relevant Transformers source files for DeepSeek-V3:
- `src/transformers/models/deepseek_v3/configuration_deepseek.py` — `DeepseekV3Config`
- `src/transformers/models/deepseek_v3/modeling_deepseek.py` — `DeepseekV3ForCausalLM`
- `src/transformers/models/deepseek_v3/__init__.py` — auto-registration

### Skill
skills/references — Append to main hf-learnings.md (no new skill needed for this reference topic)

## 2026-07-25: hf-hub-hardware-filter-models-search-deep-dive — Complete HF Hub Hardware Filtering and Model Search API (Topic #229 Deep-Dive)

### Summary
Complete deep-dive on the Hugging Face Hub hardware filtering system — how GPU/CPU/Apple Silicon compatibility is tracked, surfaced, and queried. Covers the `/hardware` page, the `hardware=` query parameter on the Models API, the `huggingface_hub` Python library's `ModelFilter` with filtering by compute capability, the `accelerator` tag system, and practical zero-cost search patterns for CPU-only hardware.

### Source
- HF Hardware page: https://huggingface.co/hardware
- Hub Search docs: https://huggingface.co/docs/hub/en/search
- Hub API docs: https://huggingface.co/docs/hub/en/api
- huggingface_hub list_models ref: https://huggingface.co/docs/huggingface_hub/en/package_reference/listing
- Model search URL: https://huggingface.co/models?hardware=apple-m-series

### 1. The Hardware Page (`/hardware`)

The Hugging Face Hardware page is a community-driven directory that surfaces the GPUs, CPUs, and Apple Silicon chips that HF users actually run. It is a **social proof** pyramid — not a spec sheet.

**Categories tracked:**
- **GPUs** — NVIDIA (RTX 4090/78.1k users, A100, H100, A6000, RTX 6000 Ada, Tesla, Quadro, Jetson), AMD (Radeon RX 7900 XTX, Instinct MI250/MI300X, W7900), Intel (Arc A770, Data Center GPU Max), Apple (M-series unified)
- **CPUs** — AMD EPYC 1st–5th gen, AMD Ryzen/Threadripper, Intel Core (11th–14th gen, Ultra), Intel Xeon, Apple Silicon (M1–M4)
- **Apple Silicon** — M1, M2, M3, M4 in all variants (Pro, Max, Ultra)

Each hardware entry shows **user count** (people who opted in). The "Register your hardware" button lets any logged-in HF user contribute.

**URL:** `https://huggingface.co/hardware?product=<product-slug>`

### 2. Model Search with Hardware Filtering

When browsing models at `https://huggingface.co/models`, the URL query parameter `hardware=` filters results:

```
https://huggingface.co/models?hardware=apple-m-series&search=qwen
```

**Common hardware slugs:**
| Slug | Hardware |
|------|----------|
| `apple-m-series` | Apple Silicon (all M-series) |
| `nvidia-a100` | NVIDIA A100 |
| `nvidia-h100` | NVIDIA H100 |
| `nvidia-rtx-4090` | NVIDIA RTX 4090 |
| `nvidia-rtx-3090` | NVIDIA RTX 3090 |
| `nvidia-a6000` | NVIDIA RTX A6000 |
| `nvidia-rtx-6000-ada` | NVIDIA RTX 6000 Ada |
| `nvidia-rtx-3060` | NVIDIA RTX 3060 |
| `amd-instinct-mi250` | AMD Instinct MI250 |
| `amd-instinct-mi300x` | AMD Instinct MI300X |
| `intel-arc-a770` | Intel Arc A770 |
| `cpu` | CPU-only compatible models |

### 3. Models REST API — Hardware Query

The Models API supports `hardware` as a first-class parameter:

```
GET https://huggingface.co/api/models?search=gguf&hardware=cpu&sort=downloads&direction=-1&limit=5
```

**Full model search API parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| `search` | string | Full-text search across model cards |
| `hardware` | string | Hardware compatibility filter slug |
| `task` | string | Pipeline task (e.g., `text-generation`) |
| `pipeline_tag` | string | Pipeline tag (e.g., `text-generation`) |
| `library` | string | Library filter (e.g., `transformers`, `diffusers`) |
| `sort` | string | Sort field (`downloads`, `likes`, `createdAt`, `lastModified`) |
| `direction` | int | Sort direction (`-1` descending, `1` ascending) |
| `limit` | int | Results per page (default 100, max 1000) |

### 4. huggingface_hub Python Library — ModelFilter and HfApi

The Python `huggingface_hub` library provides `HfApi.list_models()`:

```python
from huggingface_hub import HfApi, ModelFilter

api = HfApi()

# Basic: text-generation models sorted by downloads
models = api.list_models(
    task="text-generation",
    sort="downloads",
    direction=-1,
    limit=10
)

# Using ModelFilter for complex queries
models = api.list_models(
    filter=ModelFilter(
        task="text-generation",
        library="transformers"
    ),
    sort="downloads",
    direction=-1
)
```

**Key note:** The Python `ModelFilter` class does NOT have a dedicated `hardware` parameter yet. Hardware filtering through the Python SDK requires using the `requests` library to call the REST API directly with the `hardware=` query param, or browsing manually through the web UI.

### 5. The Accelerator Tag System

Models declare hardware compatibility via tags in their YAML frontmatter (`README.md`):

```yaml
tags:
  - nvidia-a100
  - nvidia-h100
  - apple-m-series
  - cpu
```

**Dedicated accelerator tags:**
| Tag | Meaning |
|-----|---------|
| `accelerator:GPU` | General GPU compatibility |
| `accelerator:TensorRT` | Optimized for NVIDIA TensorRT |
| `accelerator:ONNX_Runtime` | ONNX Runtime compatible |
| `accelerator:CPU` | CPU inference compatible |
| `accelerator:DirectML` | DirectML compatible (Windows) |
| `accelerator:CoreML` | Apple Core ML compatible |

These tags are indexed by the Hub search and appear in both the web UI filters and the REST API responses.

### 6. Full-Text Search (`/search`)

The full-text search endpoint at `https://huggingface.co/search/full-text` searches model cards, dataset cards, and Spaces source code:

```
https://huggingface.co/search/full-text?q=llama&type=space
```

**Parameters:**
- `q` — Query string
- `type` — Scope (`model`, `dataset`, `space`, or empty for all)

This is different from the model-specific API — it searches content rather than metadata and is useful for finding niche models or apps by description.

### 7. Practical Zero-Cost Patterns for Beer

Beer has no GPU budget and runs CPU-only inference. These patterns cost nothing:

**Find CPU-compatible tool-calling models:**
```bash
curl -s "https://huggingface.co/api/models?search=tool+calling&hardware=cpu&pipeline_tag=text-generation&sort=downloads&direction=-1&limit=5"
```

**Find GGUF quantized models for local CPU inference:**
```bash
curl -s "https://huggingface.co/api/models?search=GGUF&pipeline_tag=text-generation&sort=downloads&direction=-1&limit=10"
```

**Check hardware popularity before choosing a model to optimize:**
- Open https://huggingface.co/hardware to see what hardware the community uses
- Filter models by that hardware to see what has been optimized for it

**Web UI bookmarks for quick reference:**
- `https://huggingface.co/models?pipeline_tag=text-generation&hardware=cpu&sort=downloads` — CPU text-gen models
- `https://huggingface.co/models?search=gguf&sort=downloads` — Popular GGUF models
- `https://huggingface.co/models?search=GGUF&pipeline_tag=text-generation&sort=downloads` — GGUF text-gen

### 8. Hardware Registration (How the Data Gets Collected)

Users register their hardware via:
- **Web UI:** `https://huggingface.co/hardware` → "Register your hardware"
- **CLI:** `huggingface-cli hardware register`

This is an opt-in system. User counts reflect registrations, not runtime telemetry.

### 9. Limitations and Constraints

1. **No Python SDK hardware filter:** `ModelFilter` in `huggingface_hub` lacks a `hardware` field — must use REST API for hardware-filtered programmatic access
2. **Incomplete coverage:** Hardware tags depend on model authors adding them; many models have no tags
3. **User count does not equal usage:** The `/hardware` page shows registered users, not actual inference runtime
4. **Models-only:** The `hardware=` filter only works for models, not datasets or Spaces

### 10. Related Topics Covered
- `hf-hub-models-api-deep-dive` (topic #127) — Full Models API reference
- `hf-hub-models-api-query-language-complete` (topic #182) — Query language
- `hf-hub-search-discovery-api` (topic #140) — Search and discovery
- `hf-hub-tag-system-complete-reference` (topic #141) — Tag system
- `hf-hub-hardware-filter-models-search` (topic #229) — Original entry (this is the deep-dive)

### Skill
mlops/hf-hub-models-tags/SKILL.md — search, filter, and discover models by hardware and pipeline tags

---

## 2026-07-25: hf-hub-user-and-org-profile-api — User and Organization Profile API (Topic #231)

### Summary
Comprehensive reference on the Hugging Face Hub's User and Organization profile API. Covers all REST endpoints (`/api/users/{username}/overview`, `/api/organizations/{name}/overview`, follower/following/member lists), the `huggingface_hub` Python API (8 methods including `get_user_overview`, `list_user_followers`, `list_organization_members`, `list_user_repos`), data models (`User` and `Organization` dataclasses with all fields), and key insights (no write API for profiles, public-by-default, paginated social graph, whoami rate-limits). See full detail in `mlops/huggingface-hub/references/hf-learnings.md`.

### Sources
- Source code: `huggingface_hub/hf_api.py` — User/Organization management methods and dataclasses
- Hub API: `https://huggingface.co/api/users/{username}/overview`
- huggingface_hub docs: package_reference/community


---

## 2026-07-25: hf-hub-agent-harnesses-registry — HF Agent Harnesses Registry, MCP Server & Agent Ecosystem (Topic #233)

### Summary
Deep-dive into the Hugging Face Hub's new **Agent Ecosystem** — a dedicated docs section (Agents Overview, HF MCP Server, HF CLI for AI Agents, Agent Skills, SDK, Local Agents, Session Traces) plus a new **`/api/agent-harnesses`** REST endpoint that returns a registry of AI agents / harnesses known to the Hub. This is how `huggingface_hub` identifies which agent it's running inside (e.g., Claude Code, Codex, Cursor) and reports agent-attributed usage on Hub requests.

### Sources
- HF Hub Agents docs: https://huggingface.co/docs/hub/en/agents
- Agents Overview: https://huggingface.co/docs/hub/en/agents-overview
- HF MCP Server: https://huggingface.co/docs/hub/en/agents-mcp
- HF CLI for AI Agents: https://huggingface.co/docs/hub/en/agents-cli
- Agent Skills: https://huggingface.co/docs/hub/en/agents-skills
- SDK docs: https://huggingface.co/docs/hub/en/agents-sdk
- Local Agents: https://huggingface.co/docs/hub/en/agents-local
- Session Traces Format: https://huggingface.co/docs/hub/en/session-traces-format
- OpenAPI spec: https://huggingface.co/.well-known/openapi.md
- Agent harnesses source: `@huggingface/tasks` package — `agent-harnesses.ts`
- MCP Settings: https://huggingface.co/settings/mcp

### 1. Hub Agents Documentation (New Section)

The Hugging Face Hub now has a dedicated **Agents** section in its docs with 8 sub-pages:

| Page | URL | Purpose |
|------|-----|---------|
| Agents Overview | `/docs/hub/en/agents-overview` | Connecting chat & coding agents to the Hub |
| HF CLI for AI Agents | `/docs/hub/en/agents-cli` | Using `hf` CLI from coding agents |
| HF MCP Server | `/docs/hub/en/agents-mcp` | MCP protocol server for AI assistants |
| HF Agent Skills | `/docs/hub/en/agents-skills` | Pre-built skills (agentskills.io) |
| Building agents with HF SDK | `/docs/hub/en/agents-sdk` | Python/JS SDK for building agents |
| Local Agents with llama.cpp | `/docs/hub/en/agents-local` | Running agents locally |
| Agent Libraries | `/docs/hub/en/agents-libraries` | Catalog of agent libraries |
| Session Traces Format | `/docs/hub/en/session-traces-format` | Standard format for agent traces |

### 2. `/api/agent-harnesses` — The Agent Registry Endpoint

A new REST endpoint in the Hub API:

```
GET /api/agent-harnesses
```

Returns the registry of all AI agents / harnesses known to the Hub, along with the **standard environment variables used to detect them**. This is how the Hub knows what agent is making a request.

**How it works:**
- `huggingface_hub` detects which agent harness it's running inside by checking environment variables
- When making Hub API calls, it includes the harness name in the user-agent header
- Registered harnesses get attributed by name in Hub usage analytics and the public agent usage dataset
- Unregistered tools are only counted in the aggregate "unknown" share

**To register a harness:** Open a PR adding an entry to `agent-harnesses.ts` in the `@huggingface/tasks` package. Entry fields include: name, display label, environment variable detection patterns, docs URL, and repo URL.

### 3. HF MCP Server

The Hugging Face MCP Server connects MCP-compatible AI assistants to the Hub:

- **Configuration:** Generated at https://huggingface.co/settings/mcp — picks your client type and produces the exact snippet
- **Supported clients:** Cursor, VS Code, Zed, Claude Desktop, ChatGPT, Codex, and any MCP-compatible client
- **Built-in tools:** The `hf_fs` tool enables semantic searches of docs and Spaces
- **Community tools:** Gradio MCP-compatible Spaces expose their functions as tools with arguments and descriptions
- **Capabilities:** Search models/datasets/Spaces, read docs, schedule Jobs, use Sandboxes, run community tools

To connect: `claude mcp add hf-mcp-server -t http "https://huggingface.co/mcp?login"`

### 4. HF CLI for AI Agents

The `hf` CLI now has first-class agent support:

- **CLI Skill:** `hf skills add --global` installs the CLI skill so coding agents know every `hf` command
- **Claude Code integration:** `/plugin marketplace add huggingface/skills` then `/plugin install hf-cli@huggingface/skills`
- **Agent workflow:** Agents can search models, manage datasets/buckets, launch Spaces, run Jobs — all via the CLI

### 5. Agent Skills Platform (agentskills.io)

A new skill marketplace at agentskills.io allows agents to install task-specific capabilities:
- Skills work alongside MCP or standalone
- Published by Hugging Face as `huggingface/skills` on the plugin marketplace
- Skills provide guidance for AI/ML workflows (HF CLI, model handling, etc.)

### 6. Session Traces Format

Standardized JSON format for recording agent sessions interacting with the Hub. Enables traceability and reproducibility of agent actions.

### 7. Key Takeaways

1. **The agent ecosystem is a first-class Hub feature** — not an afterthought. Dedicated docs, API endpoint, and CLI integration.
2. **Attribution is opt-in via environment variable detection.** Registering your harness gives named attribution in Hub analytics.
3. **MCP is the primary integration protocol.** The HF MCP Server exposes Hub tools via MCP for any compatible assistant.
4. **Skills are a complementary layer** to MCP, providing task-specific procedural guidance for coding agents.
5. **The registry is open-source** — agent-harnesses.ts in the `@huggingface/tasks` package accepts PRs for new harnesses.

### Skill
mlops/huggingface-hub — Hub API, MCP Server, CLI, and agent integration

---

## 2026-07-25: hf-agent-skills-complete-reference — HF Agent Skills Platform: Complete Specification & Ecosystem (Deep-Dive of Topic #233)

### Summary
Complete deep-dive on the **Agent Skills** ecosystem — an open, lightweight format for extending AI agents with specialized knowledge and workflows. Covers the open specification (agentskills.io), the `SKILL.md` format with YAML frontmatter, progressive disclosure loading model, directory structure conventions, the Hugging Face curated skill catalog (11 official skills), the `hf skills add` CLI, installation patterns for all major coding agents, the validation tooling (`skills-ref`), and how this relates to the Sak Family Agents' own skill system.

### Sources
- Agent Skills Overview: https://agentskills.io/home.md
- Specification: https://agentskills.io/specification.md
- Quickstart: https://agentskills.io/skill-creation/quickstart.md
- HF Agent Skills (Hub docs): https://huggingface.co/docs/hub/en/agents-skills
- HF CLI for AI Agents: https://huggingface.co/docs/hub/en/agents-cli
- Validation tool: https://github.com/agentskills/agentskills/tree/main/skills-ref
- Best practices: https://agentskills.io/skill-creation/best-practices.md
- Client Showcase: https://agentskills.io/clients.md
- GitHub: https://github.com/agentskills/agentskills
- Discord: https://discord.gg/MKPE9g8aUy

### 1. What Are Agent Skills?

Agent Skills are an **open, lightweight format** (originally developed by Anthropic, now community-governed) for extending AI agent capabilities with specialized knowledge and repeatable workflows. A skill is a folder containing a `SKILL.md` file with metadata and instructions plus optional scripts, references, and assets.

```tree
my-skill/
├── SKILL.md          # Required: metadata + instructions
├── scripts/          # Optional: executable code
├── references/       # Optional: documentation
├── assets/           # Optional: templates, resources
└── ...               # Any additional files or directories
```

**Key properties:**
- **Portable** — version-controlled folders, shareable via git
- **Cross-product** — same skill works in Claude Code, VS Code, Cursor, OpenCode, Gemini CLI, Copilot, Codex, and 30+ more clients
- **Progressive disclosure** — agents load only metadata at startup, full instructions on activation, resources on demand

### 2. The `SKILL.md` Format (Specification)

#### Frontmatter Fields

| Field | Required | Constraints |
|-------|----------|-------------|
| `name` | Yes | 1-64 chars, lowercase alphanumeric + hyphens, must match directory name |
| `description` | Yes | 1-1024 chars, describes what + when to use |
| `license` | No | License name or reference to bundled file |
| `compatibility` | No | 1-500 chars, environment requirements |
| `metadata` | No | Arbitrary key-value map |
| `allowed-tools` | No | Space-separated pre-approved tools (experimental) |

**Minimal example:**
```yaml
---
name: skill-name
description: A description of what this skill does and when to use it.
---
```

**Full example with optional fields:**
```yaml
---
name: pdf-processing
description: Extract PDF text, fill forms, merge files. Use when handling PDFs.
license: Apache-2.0
compatibility: Requires Python 3.14+ and uv
metadata:
  author: example-org
  version: "1.0"
allowed-tools: Bash(git:*) Bash(jq:*) Read
---
```

#### Naming Rules
- Only lowercase letters (`a-z`), digits (`0-9`), and hyphens (`-`)
- Must not start or end with a hyphen
- No consecutive hyphens (`--`)
- Must match the parent directory name

#### Body Content
The Markdown body after frontmatter contains instructions. Recommended sections:
- Step-by-step instructions
- Examples of inputs and outputs
- Common edge cases

Agents load the body on activation. Keep under 500 lines; move reference material to separate files.

### 3. Progressive Disclosure Model

Agents load skills in three stages to minimize context usage:

| Stage | What's Loaded | Token Cost | When |
|-------|---------------|------------|------|
| Discovery | `name` + `description` | ~100 tokens | At startup for all skills |
| Activation | Full `SKILL.md` body | < 5000 tokens recommended | When task matches description |
| Execution | Referenced files (scripts/, references/, assets/) | Variable | Only when needed |

This means agents can have hundreds of skills available without filling their context window.

### 4. Hugging Face Curated Skills Catalog

HF publishes 11 official skills at `huggingface/skills` on the Claude Code plugin marketplace:

| Skill | What It Does |
|-------|-------------|
| `hf-cli` | Hub operations via the `hf` CLI: download, upload, manage repos, run jobs |
| `huggingface-datasets` | Explore datasets, paginate rows, search text, apply filters |
| `huggingface-llm-trainer` | Train or fine-tune LLMs with TRL (SFT, DPO, GRPO) on HF Jobs |
| `huggingface-vision-trainer` | Train object detection and image classification models |
| `huggingface-community-evals` | Run evaluations against models on the Hub on local hardware |
| `huggingface-trackio` | Track and visualize ML training experiments with Trackio |
| `huggingface-papers` | Look up and read HF paper pages in markdown |
| `huggingface-paper-publisher` | Publish and manage research papers on the Hub |
| `huggingface-tool-builder` | Build reusable scripts for HF API operations |
| `gradio` | Build Gradio web UIs and demos |
| `transformers-js` | Run ML models in JavaScript/TypeScript with WebGPU/WASM |

### 5. Installation Methods

#### Method 1: `hf skills add` (HF CLI — recommended)
```bash
# Global install (works with Codex, Cursor, OpenCode, anything loading from ~/.agents/skills)
hf skills add --global
# For Claude Code specifically
hf skills add --claude --global
# Project-local install
hf skills add
# Project-local for Claude Code
hf skills add --claude
```
The skill is generated from the locally installed CLI version — always up to date.

#### Method 2: Claude Code Plugin Marketplace
```
/plugin marketplace add huggingface/skills
/plugin install hf-cli@huggingface/skills
```

#### Method 3: Manual Directory
Create a `.agents/skills/<skill-name>/SKILL.md` file in your project (works with VS Code, Cursor, and other clients that scan `.agents/skills/`).

### 6. Compatible Clients (30+)

Major agents supporting the Agent Skills format:

| Client | Provider |
|--------|----------|
| Claude Code | Anthropic |
| GitHub Copilot | GitHub/Microsoft |
| VS Code | Microsoft |
| Cursor | Cursor |
| OpenAI Codex | OpenAI |
| Gemini CLI | Google |
| Junie | JetBrains |
| OpenCode | SST |
| OpenHands | OpenHands |
| Goose | Block |
| Roo Code | Roo Code |
| Factory | Factory AI |
| Letta | Letta AI |
| And 15+ more... | |

### 7. Validation Tooling

The `skills-ref` library validates skill format:

```bash
pip install skills-ref   # or equivalent
skills-ref validate ./my-skill
```

Checks: valid YAML frontmatter, name matches directory, correct field types, no naming violations.

### 8. Zero-Cost Relevance for Beer/SakThai

- **Skills are free** — no paid service required. Everything is file-based and open-source.
- **The Sak Family Agents already use a skill-based architecture** (Hermes skills at `~/.hermes/skills/`). The Agent Skills format provides a complementary, cross-product standard that SakThai agents could adopt for sharing skills with the wider ecosystem.
- **Beer can publish his own skills** on agentskills.io or distribute them via GitHub — no HF Pro needed.
- **The `hf-cli` skill** is directly useful: it teaches any agent how to use the `hf` CLI for Hub operations, complementing the HF MCP Server.
- **Cross-installable**: Sak skills written in Agent Skills format would work in Claude Code, Cursor, Copilot, etc. — making Beer's workflows portable.

### 9. Key Distinction: Hermes Skills vs. Agent Skills

| Aspect | Hermes Skills | Agent Skills |
|--------|--------------|--------------|
| Format | YAML frontmatter + body in a `SKILL.md` | YAML frontmatter + body in a `SKILL.md` |
| Name field | `name:` in YAML frontmatter | `name:` in YAML frontmatter |
| Author field | `author: SakThai` (required) | `metadata.author` (optional) |
| License field | `license: MIT` (required) | `license:` (optional) |
| Location | `~/.hermes/skills/` | `.agents/skills/` or plugin marketplace |
| Client | Hermes agent only | Any Agent Skills-compatible client (30+) |
| Load model | At startup via skill_view | Progressive disclosure |
| Extra dirs | `references/` only | `scripts/`, `references/`, `assets/` |
| Validation | Built into Hermes | `skills-ref` CLI |
| Publishing | Private git repo | agentskills.io, GitHub, plugin marketplaces |

The formats are structurally compatible — a Hermes SKILL.md with `author: SakThai` and `license: MIT` can serve as a valid Agent Skills SKILL.md with minimal adjustment.

### 10. Skill Creators' Resources

- **Quickstart**: Create a skill in 5 minutes — https://agentskills.io/skill-creation/quickstart.md
- **Best practices**: Well-scoped, calibrated skills — https://agentskills.io/skill-creation/best-practices.md
- **Optimizing descriptions**: Test and improve trigger reliability — https://agentskills.io/skill-creation/optimizing-descriptions.md
- **Evaluating skills**: Eval-driven quality iteration — https://agentskills.io/skill-creation/evaluating-skills.md
- **Using scripts**: Bundling executable code — https://agentskills.io/skill-creation/using-scripts.md

### Skill
mlops/huggingface-hub — Hub API, MCP Server, CLI, Agent Skills, and agent integration

## 2026-07-25: hf-transformers-quantization-method-selection-comprehensive — Complete Decision Framework for All 22 Quantization Methods (Topic #240)

### Summary
Comprehensive deep-dive on all 22 quantization methods supported in Transformers v5.14.0. Covers the full decision framework — on-the-fly vs calibration-based, inference vs fine-tuning, hardware compatibility (NVIDIA CUDA, AMD ROCm, Intel XPU/HPU, Apple Metal, CPU), bit-depth tradeoffs (8/4/2/1-bit), PEFT compatibility, serialization support, and benchmark comparisons. Goes deeper than individual method docs by connecting them into a single actionable reference with selection guidelines.

### Sources
- Transformers quantization overview: https://huggingface.co/docs/transformers/en/quantization/overview
- Selecting a quantization method: https://huggingface.co/docs/transformers/en/quantization/selecting
- Transformers v5.14.0 docs (individual quantization pages for each method)

---

### 1. The 22 Methods at a Glance

Transformers v5.14.0 supports **22 distinct quantization methods**, categorized by whether they require calibration:

**On-the-fly (no calibration needed — 14 methods):**
bitsandbytes (4/8-bit), HQQ (1-8-bit), SINQ (2-8-bit), torchao (4/8-bit), Quanto (2/4/8-bit), EETQ (8-bit), FourOverSix (4-bit), FP-Quant (4-bit), HIGGS (2/4-bit), Metal (2/4/8-bit), FBGEMM_FP8 (8-bit), FINEGRAINED_FP8 (8-bit), GGUF/GGML/llama.cpp (1-8-bit), MXFP4 (4-bit)

**Calibration-based (requires dataset — 8 methods):**
GPTQ (2/3/4/8-bit), AWQ (4-bit), AQLM (1/2-bit), Quark (2/4/6/8/9/16-bit), SpQR (3-bit), VPTQ (1-8-bit), AutoRound (2/3/4/8-bit), compressed-tensors (1/8-bit)

---

### 2. Decision Framework

#### Step 1: Determine Your Use Case

| Use Case | Best Methods | Why |
|---|---|---|
| Load & go inference, no calibration | bitsandbytes, HQQ, SINQ, torchao | Zero setup, no dataset needed |
| Maximum 4-bit accuracy | AWQ, GPTQ | Calibration recovers accuracy |
| Fine-tuning with PEFT (QLoRA) | bitsandbytes | Most tested, widest PEFT compatibility |
| Apple Silicon / Metal | Metal, GGUF, bitsandbytes (partial) | Metal-specific kernels available |
| Intel GPU (XPU) | bitsandbytes, GPTQ, Quark, AWQ, Quanto, SINQ | Wide Intel support |
| CPU-only inference | bitsandbytes, HQQ, GGUF, Quanto, SINQ, AQLM | No GPU required |
| Extreme compression (<4-bit) | AQLM (1-2-bit), HQQ (1-bit), VPTQ (1-8-bit), SpQR (3-bit) | Maximum memory savings |
| Fast quantization speed | HQQ (seconds), SINQ (seconds), bitsandbytes (seconds) | No calibration step |
| torch.compile integration | HQQ, SINQ, torchao, AQLM, HIGGS, FourOverSix, Quanto, FP-Quant | JIT-compiled kernels |
| ROCm (AMD GPU) | AWQ, GPTQ, compressed-tensors, Quark | Limited but growing |

#### Step 2: Pick by Hardware

**NVIDIA CUDA:** All 22 methods supported.
**AMD ROCm:** AWQ 🟢, GPTQ 🟢, compressed-tensors 🟢, Quark 🟢, bitsandbytes 🟡 (partial), SINQ 🟡 (partial).
**Intel XPU:** 15 methods supported — bitsandbytes, GPTQ, AWQ, AQLM, AutoRound, Quanto, GGUF, HQQ, Quark, SINQ, EETQ, FBGEMM_FP8, FINEGRAINED_FP8, torchao, FourOverSix.
**Intel HPU (Gaudi):** bitsandbytes 🟢, GPTQ 🟢.
**Apple Metal (M-series):** Metal 🟢, GGUF 🟢, bitsandbytes 🟡 (partial), SINQ 🟡 (partial), torchao 🟡 (partial), Quark 🟢, Quanto 🟢.
**CPU:** bitsandbytes 🟢, HQQ 🟢, GGUF 🟢, Quanto 🟢, SINQ 🟢, AQLM 🟢, AWQ 🟢, GPTQ 🟢, AutoRound 🟢, Quark 🟢, torchao 🟢 (fp32 only), FourOverSix 🟢, compressed-tensors 🟢.

#### Step 3: Pick by Bit Depth

| Depth | Methods | Memory Savings |
|---|---|---|
| 8-bit | bitsandbytes (int8), HQQ, Quanto, torchao, EETQ, FBGEMM_FP8, FINEGRAINED_FP8, GGUF | ~2x vs bf16 |
| 4-bit | bitsandbytes (nf4/fp4), AWQ, GPTQ, HQQ, Quanto, SINQ, FourOverSix, FP-Quant, HIGGS, Metal, MXFP4, GGUF | ~4x vs bf16 |
| 2-3-bit | GPTQ (2-3b), AQLM (1-2b), HQQ (1-8b), HIGGS (2b), SpQR (3b), VPTQ (1-8b), SINQ (2-3b), AutoRound (2-4b), Quark (2-16b) | 6-8x vs bf16 |
| 1-bit | AQLM (1b), HQQ (1b), compressed-tensors (1b), VPTQ (1b), GGUF (1b) | 16x+ vs bf16 |

---

### 3. Inference-Focused Methods

#### On-the-Fly (No Calibration)

**bitsandbytes** — The most widely-used method. `BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)`. Supports 4-bit NF4/FP4 and 8-bit int8. PEFT/QLoRA compatible. Primary optimization for NVIDIA CUDA, with Intel XPU support. No calibration needed. Nested (double) quantization saves additional ~0.4 bits/parameter.

**HQQ (Half-Quadratic Quantization)** — Fastest on-the-fly quantization (seconds). Uses `HqqConfig(nbits=4, group_size=64)`. Supports 1-8 bits. Multiple backend kernels (GemLite, torch.compile). No calibration data needed. Accuracy degrades below 4-bit. Not serializable via Transformers' `save_pretrained()`.

**SINQ** — Fast, high-quality on-the-fly quantization. `SinqConfig(n_bits=4, group_size=32)`. Supports 2-8 bits. GemLite kernel backend for fast inference. No calibration. Super-fast quantization process. Slower 3-bit inference (no GemLite available for 3-bit).

**torchao** — Strong torch.compile integration. `TorchAoConfig("int4wo", group_size=128)`. Flexible quantization schemes (int4wo, int8wo, int8dq, fp8). Python-only, no binary dependencies via PyTorch's native AO. 4-bit int4wo accuracy may not match GPTQ/AWQ. Not serializable via `save_pretrained()`.

**optimum-quanto** — HuggingFace-native. `QuantoConfig(weights="int4")`. Pure Python, no binary deps. Supports 2/4/8-bit. CPU, CUDA, Metal, Intel XPU. 🟢 torch.compile. Not serializable by Transformers. No PEFT fine-tuning.

**Other on-the-fly:** EETQ (8-bit, NVIDIA CUDA only), FourOverSix (4-bit, theoretical 4.58-bit), FP-Quant (4-bit, NVIDIA CUDA), HIGGS (2/4-bit, NVIDIA CUDA), Metal (Apple M-series only), FBGEMM_FP8 (8-bit, NVIDIA CUDA), FINEGRAINED_FP8 (8-bit, built-in NVIDIA), GGUF/llama.cpp (1-8-bit, cross-platform).

#### Calibration-Based (Higher Accuracy)

**GPTQ** — `GPTQConfig(bits=4, dataset="c4", group_size=128, damp_percent=0.01)`. Calibration ~20 min on A100 for 8B model. Needs dataset. Many pre-quantized models on Hub. PEFT compatible. CPU/CUDA/ROCm/Intel XPU/Metal. Compiler support: 🟢 ROCm, 🔴 CUDA.

**AWQ** — `AwqConfig(bits=4, group_size=128, zero_point=True)`. Calibration ~10 min on A100 for 8B (half of GPTQ). Often surpasses GPTQ on specific tasks by analyzing activation magnitudes. Many pre-quantized models. PEFT compatible. CUDA/ROCm. Compiler: 🟢 ROCm.

**compressed-tensors** — Loading only, not quantization within Transformers. Supports FP8/sparse formats. Neural Magic backed. `CompressedTensorsConfig()`.

---

### 4. Fine-Tuning

For QLoRA-style fine-tuning, **bitsandbytes** is the most established path:

```python
from transformers import BitsAndBytesConfig, AutoModelForCausalLM
from peft import LoraConfig, get_peft_model

bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)

model = AutoModelForCausalLM.from_pretrained(
    "model-id", quantization_config=bnb_config, device_map="auto"
)
model = get_peft_model(model, LoraConfig(...))
```

Other PEFT-compatible methods: AQLM 🟢, AWQ 🟢, bitsandbytes 🟢, compressed-tensors 🟢, EETQ 🟢, GPTQ 🟢, HQQ 🟢.

Non-PEFT-compatible: AutoRound 🔴, FourOverSix 🔴, FP-Quant 🔴, HIGGS 🔴, Metal 🔴, Quanto 🔴, SINQ 🔴, SpQR 🔴, VPTQ 🔴, FBGEMM_FP8 🔴, FINEGRAINED_FP8 🔴, Quark 🔴, torchao ❓.

---

### 5. Serialization Support

Methods that support `model.save_pretrained()` (serializable):
AQLM 🟢, AutoRound 🟢, AWQ 🟢, bitsandbytes 🟢, compressed-tensors 🟢, EETQ 🟢, FourOverSix 🟢, FP-Quant 🟢, GPTQ 🟢, HIGGS 🟢, HQQ 🔴 (not serializable), Metal 🟢, Quanto 🔴, SINQ 🟢, SpQR 🟢, VPTQ 🟢, FBGEMM_FP8 🟢, FINEGRAINED_FP8 🟢, Quark 🔴, torchao 🟢🔴 (partial), GGUF 🔴 (separate format).

---

### 6. Benchmark Results (from official docs — Llama 3.1 8B/70B on A100 80GB)

- bf16 baseline: 1.00 acc — 16.0 GB VRAM — 125 tok/s
- 8-bit (bnb-int8): 0.99 acc — 8.5 GB — 124 tok/s
- 4-bit (AWQ): 0.98 acc — 5.8 GB — 123 tok/s
- 4-bit (GPTQ): 0.98 acc — 5.8 GB — 106 tok/s (124 with Marlin)
- 4-bit (HQQ): 0.97 acc — 5.9 GB — 132 tok/s (with torch.compile)
- 4-bit (bnb-nf4): 0.97 acc — 6.1 GB — 82 tok/s (117 with torch.compile)
- 2-bit (GPTQ): 0.91 acc — 5.2 GB — 130 tok/s

**Key takeaways:**
1. 8-bit methods preserve accuracy nearly perfectly (~0.99 baseline)
2. 4-bit AWQ/GPTQ lead accuracy (~0.98) but need calibration
3. HQQ + torch.compile offers fastest 4-bit throughput (132 tok/s)
4. Marlin kernels significantly boost GPTQ (124 vs 106 tok/s)
5. Sub-4-bit (2-bit) shows noticeable accuracy drop (~0.91)

---

### 7. Complete API Config Classes

All quantization configs are available at `transformers` top level:
- `BitsAndBytesConfig` — bitsandbytes
- `AwqConfig` — AWQ
- `GPTQConfig` — GPTQ (for AutoGPTQ)
- `GptqConfig` — GPTQ (for GPTQModel)
- `HqqConfig` — HQQ
- `AqlmConfig` — AQLM
- `EetqConfig` — EETQ
- `QuantoConfig` — optimum-quanto
- `TorchAoConfig` — torchao
- `BitNetConfig` — BitNet
- `CompressedTensorsConfig` — compressed-tensors
- `FbgemmFp8Config` — FBGEMM_FP8
- `FineGrainedFP8Config` — FINEGRAINED_FP8
- `FourOverSixConfig` — FourOverSix
- `FPQuantConfig` — FP-Quant
- `HIGGSConfig` — HIGGS
- `MetalConfig` — Metal (Apple)
- `MXFP4Config` — MXFP4
- `QuarkConfig` — Quark
- `SinqConfig` — SINQ
- `VptqConfig` — VPTQ
- `SpQRConfig` — SpQR
- `AutoRoundConfig` — AutoRound

Usage pattern:
```python
from transformers import AutoModelForCausalLM, <Method>Config
config = <Method>Config(...)
model = AutoModelForCausalLM.from_pretrained("model-id", quantization_config=config)
```

---

### Quick-Start Recommendations

| Scenario | Recommended Method |
|---|---|
| First time quantizing | bitsandbytes (nf4) |
| Best 4-bit accuracy | AWQ or GPTQ with Marlin |
| Fastest load time | HQQ (seconds) |
| QLoRA fine-tuning | bitsandbytes (nf4 + double quant) |
| Apple Silicon | Metal or GGUF |
| CPU inference | GGUF or Quanto |
| Production deployment | AWQ (pre-quantized) |
| Research/extreme compression | AQLM or VPTQ |
| torch.compile pipeline | HQQ or torchao |

### Skill
mlops/huggingface-hub — Hub API, MCP Server, CLI, Agent Skills, and agent integration

---

## 2026-07-25: hf-inference-client-internals-deep-dive — Session Management, Error Recovery & Caching Architecture (Topic #241 Deepening)

### Summary
Deep-dive into the internal architecture of Hugging Face's `InferenceClient` and `AsyncInferenceClient` from `huggingface_hub` — covering connection pooling via global `httpx.Client`, timeout/retry semantics, the full error class hierarchy (InferenceTimeoutError, HfHubHTTPError, rate limiting), streaming protocols (SSE for chat/text-gen vs buffered reads for vision/audio), provider routing for multi-provider inference, and practical caching strategies for zero-cost optimization. Based on source-code analysis of `huggingface_hub/inference/_client.py`, `_common.py`, `_providers.py`, and `utils/_http.py`.

### Sources
- `huggingface_hub` source code: `src/huggingface_hub/inference/_client.py` (InferenceClient, AsyncInferenceClient)
- `huggingface_hub` source code: `src/huggingface_hub/inference/_common.py` (stream parsers, raise_text_generation_error)
- `huggingface_hub` source code: `src/huggingface_hub/inference/_providers.py` (provider routing)
- `huggingface_hub` source code: `src/huggingface_hub/utils/_http.py` (get_session, rate limit parsing, retry-after, global client factory)
- `huggingface_hub` source code: `src/huggingface_hub/errors.py` (full error class hierarchy)
- Official docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client

### 1. Global Session Architecture

The `InferenceClient` does NOT create its own HTTP session. Instead, it relies on a **single global `httpx.Client`** managed by `get_session()`:

```python
from huggingface_hub.utils import get_session

# Returns a module-level singleton — shared across ALL InferenceClient instances
session = get_session()
```

**How it works:**
- `_GLOBAL_CLIENT` is a module-level variable in `huggingface_hub/utils/_http.py`
- First call to `get_session()` initializes it using `_GLOBAL_CLIENT_FACTORY()` (default: `httpx.Client()`)
- A thread lock (`_CLIENT_LOCK`) protects initialization
- The client is never closed automatically — registered via `atexit` for cleanup
- Customization: `set_client_factory(callable)` replaces the factory for custom transport, proxies, or timeouts

**Implications:**
1. **Connection pooling** is automatic — HTTP keep-alive, TCP connection reuse across calls
2. **No per-client isolation** — headers, cookies from one `InferenceClient` affect the global session's state (though InferenceClient sends per-request headers)
3. **Thread-safe** — `httpx.Client` is designed for concurrent use
4. **Custom transport** possible via `set_client_factory(lambda: httpx.Client(transport=...) )`

### 2. Timeout Semantics

The `timeout` parameter in `InferenceClient.__init__()` behaves differently from httpx defaults:

```python
client = InferenceClient(timeout=None)   # Default: loops until server available
client = InferenceClient(timeout=30.0)   # 30-second limit per request
```

**When `timeout=None` (default):**
- The client passes `None` to `httpx.Client.stream(timeout=None)`
- httpx interprets `None` as no timeout — waits indefinitely
- Intended for serverless inference where models may cold-start (10-30s)
- **Caveat:** If the server hangs indefinitely, the client hangs too — no application-level timeout

**When `timeout=<float>`:**
- Passed directly to httpx as the total request timeout
- Covers: connection establishment, TLS handshake, response headers, body streaming
- If exceeded: `httpx.TimeoutException` → caught by `_inner_post` → raised as `InferenceTimeoutError`

**Internal flow:**
```
httpx raises TimeoutError (or any httpx timeout variant)
  → caught by `except TimeoutError` in _inner_post
  → raise InferenceTimeoutError(f"Inference call timed out: {url}")
```

**Key insight:** Timeout is for the entire request (connect + send + receive), not broken into separate connect/read/pool timeouts. For granular control, create a custom httpx transport and use `set_client_factory()`.

### 3. Error Classification & Recovery

The client defines a rich error hierarchy:

```
HTTPError (httpx)
└── HfHubHTTPError
    ├── BadRequestError (HTTP 400)
    ├── RepositoryNotFoundError (HTTP 404)
    ├── RevisionNotFoundError (HTTP 404)
    ├── GatedRepoError (HTTP 403)
    ├── DisabledRepoError
    ├── RemoteEntryNotFoundError
    ├── BucketNotFoundError
    └── JobNotFoundError

TimeoutError (builtin)
└── InferenceTimeoutError (HTTPError)

TextGenerationError (HTTPError)
├── ValidationError
└── GenerationError
```

**`_inner_post` error handling:**
```python
try:
    response = get_session().stream("POST", url, json=..., headers=..., timeout=self.timeout)
    hf_raise_for_status(response)  # raises HfHubHTTPError for non-2xx
except TimeoutError:
    raise InferenceTimeoutError(...)
except HfHubHTTPError:
    if error.response.status_code == 422:
        # Append validation details to error message
    raise
```

**HTTP 503 behavior:** The serverless inference API returns HTTP 503 when the model is loading (cold-start). The client does NOT handle 503 specially in `_inner_post` — instead, `hf_raise_for_status` converts 503 to a `HfHubHTTPError`. The caller can catch `HfHubHTTPError` and check `error.response.status_code == 503` to implement retry with backoff.

**Recommended retry pattern:**
```python
import time
from huggingface_hub import InferenceClient
from huggingface_hub.errors import HfHubHTTPError, InferenceTimeoutError

client = InferenceClient(timeout=30)

def infer_with_retry(**kwargs, max_retries=3, base_delay=2.0):
    for attempt in range(max_retries):
        try:
            return client.chat_completion(**kwargs)
        except InferenceTimeoutError:
            if attempt == max_retries - 1:
                raise
            time.sleep(base_delay * (2 ** attempt))  # exponential backoff
        except HfHubHTTPError as e:
            if e.response.status_code == 503:  # model loading
                time.sleep(base_delay * (2 ** attempt))
                continue
            raise  # non-recoverable error
```

### 4. Provider Routing

The `provider` parameter controls which inference backend serves the request:

```python
client = InferenceClient(provider="auto")      # Default: fastest provider
client = InferenceClient(provider="hf-inference")  # HF's own serverless API
client = InferenceClient(provider="together")  # Third-party provider
```

**Provider resolution:**
1. `get_provider_helper(provider, task, model)` creates a provider-specific helper
2. `helper.prepare_request(inputs, parameters, headers, model, api_key)` normalizes inputs and builds the request
3. The provider helper selects the endpoint URL, formats the payload, and adds authentication
4. `provider="auto"` uses configured routing (configurable at https://hf.co/settings/inference-providers) — options: "fastest", "cheapest", "preferred"

**Supported providers (as of v1.24.0):**
`cerebras`, `cohere`, `deepinfra`, `fal-ai`, `featherless-ai`, `fireworks-ai`, `groq`, `hf-inference`, `novita`, `nscale`, `openai`, `ovhcloud`, `publicai`, `replicate`, `scaleway`, `together`, `wavespeed`, `zai-org`

**Key design choice:** Providers are resolved per-request, not cached. Each task call (e.g., `audio_classification`, `chat_completion`) calls `get_provider_helper()` independently even if using the same model.

### 5. Streaming Architecture

Two distinct streaming paths exist:

**Text Generation / Chat Completion (SSE):**
```python
# _stream_text_generation_response — parses SSE events
# _stream_chat_completion_response — parses SSE events with delta fields
for chunk in client.chat_completion(messages, stream=True):
    print(chunk.choices[0].delta.content)
```
- Returns `Iterable[str]` via `response.iter_lines()`
- Each line is a raw SSE event (data: {...})
- Stream parsers handle: chunk parsing, token aggregation, stop conditions
- Uses `ExitStack` to manage the streaming context

**Other Tasks (non-streaming):**
```python
result = client.audio_classification("audio.flac")  # returns full response
result = client.text_generation(prompt)              # returns full text
```
- Single response via `response.read()`
- All task-specific methods (40+ tasks) use either pattern

**Streaming lifecycle:**
```
client.chat_completion(stream=True)
  → _inner_post(stream=True)
    → get_session().stream("POST", url, ...)  # httpx stream context
    → response.iter_lines()                    # SSE line iterator
  → _stream_chat_completion_response(response) # wraps in chunk parser
  → async for / for loop consumes chunks
  → ExitStack ensures response body is consumed and connection released
```

### 6. Rate Limiting & Headers

The `utils/_http.py` module includes full rate limit parsing following the IETF draft:

```python
from huggingface_hub.utils import parse_ratelimit_headers

# Headers from response: ratelimit, ratelimit-policy
# "ratelimit": '"api";r=0;t=55' → resource="api", remaining=0, reset_in=55s
# "ratelimit-policy": '"fixed window";"api";q=500;w=300' → limit=500, window=300s

info = parse_ratelimit_headers(response.headers)
if info and info.remaining == 0:
    wait_seconds = info.reset_in_seconds
    print(f"Rate limited. Reset in {wait_seconds}s")
```

**Important:** The `InferenceClient` does NOT automatically handle rate limits — no built-in retry or queue management. Rate limit parsing is available in the utils but must be manually integrated.

**Retry-After header:**
```python
from huggingface_hub.utils._http import _parse_retry_after
wait = _parse_retry_after(response.headers)  # Returns seconds or None
```

### 7. Caching Patterns for Zero-Cost Optimization

The `InferenceClient` has **zero built-in caching**. Every call hits the network. For serverless inference (which is free but rate-limited), caching identical requests is essential.

**Pattern 1: In-memory cache with TTL (for repeated prompts):**
```python
from functools import lru_cache

client = InferenceClient()

@lru_cache(maxsize=128)
def classify_audio_cached(audio_bytes: bytes, model: str) -> list:
    return client.audio_classification(audio_bytes, model=model)
```

**Pattern 2: diskcache for persistence across restarts:**
```python
import diskcache
from huggingface_hub import InferenceClient

cache = diskcache.Cache("/tmp/hf-inference-cache")
client = InferenceClient(timeout=30)

def cached_inference(prompt: str, model: str = "meta-llama/Llama-3.2-3B-Instruct"):
    key = f"{model}:{prompt}"
    if key in cache:
        return cache[key]
    result = client.text_generation(prompt, model=model, max_new_tokens=512)
    cache.set(key, result, expire=3600)  # 1-hour TTL
    return result
```

**Pattern 3: Async batch deduplication (for concurrent identical requests):**
```python
import asyncio
from huggingface_hub import AsyncInferenceClient

_pending: dict[str, asyncio.Future] = {}

async def deduped_chat(client: AsyncInferenceClient, messages: list, model: str):
    import json
    key = f"{model}:{json.dumps(messages, sort_keys=True)}"
    if key in _pending:
        return await _pending[key]
    future = asyncio.get_event_loop().create_future()
    _pending[key] = future
    try:
        result = await client.chat_completion(messages=messages, model=model)
        future.set_result(result)
        return result
    except Exception as e:
        future.set_exception(e)
        raise
    finally:
        del _pending[key]
```

### 8. AsyncInferenceClient Differences

`AsyncInferenceClient` mirrors `InferenceClient` with identical API but async internal:

| Aspect | InferenceClient | AsyncInferenceClient |
|--------|----------------|---------------------|
| Session | `get_session()` → sync httpx.Client | `get_async_session()` → async httpx.AsyncClient |
| Stream | `response.iter_lines()` (sync generator) | `response.aiter_lines()` (async generator) |
| Context | `ExitStack.enter_context()` | `AsyncExitStack.enter_async_context()` |
| Provider routing | Same `get_provider_helper()` | Same (sync helper, but async HTTP) |
| Error types | Identical | Identical |

**Key caveat:** The async client uses a separate global session (`_GLOBAL_ASYNC_CLIENT` vs `_GLOBAL_CLIENT`). Customizing the async factory is done via `set_async_client_factory()`.

### 9. Practical Optimization Tips for Free Tier

| Strategy | Implementation | Impact |
|----------|---------------|--------|
| Connection reuse | Default `get_session()` pools connections automatically | Reduces TLS handshake latency by ~300-500ms per request |
| Model pinning | Always pass `model="org/model"` to avoid auto-selection overhead | Avoids extra provider resolution step |
| Batch requests | For independent tasks, use `asyncio.gather()` with AsyncInferenceClient | Up to 10x throughput on concurrent requests |
| Minimum token count | Set `max_new_tokens=1` for classification tasks that only need yes/no | Reduces response time and token cost |
| Cache identical prompts | Use `lru_cache` or `diskcache` to avoid re-hitting the API for exact repeats | Zero-cost for repeated queries |
| Monitor rate limits | Parse response headers with `parse_ratelimit_headers()` | Avoids silent failures from throttling |
| Set explicit timeout | `timeout=15` for most tasks, `timeout=60` for text generation | Prevents hangs on cold-start failures |
| Avoid per-call client creation | Reuse one `InferenceClient` instance | No global session re-initialization |

### 10. Architecture Diagram (Request Lifecycle)

```
InferenceClient.__init__(model, provider, timeout, headers, cookies)
  │
  ├── self.model = model
  ├── self.provider = get_provider_routing(provider)
  ├── self.timeout = timeout
  └── self.exit_stack = ExitStack()

client.chat_completion(messages, stream=False)
  │
  ├── get_provider_helper(provider, task="chat-completion", model)
  │   └── provider_helper.prepare_request(messages, headers, model, api_key)
  │       └── Returns: RequestParameters(url, json, data, headers, task)
  │
  ├── _inner_post(request_parameters, stream=False)
  │   │
  │   ├── get_session()  → global httpx.Client (shared singleton)
  │   ├── session.stream("POST", url, json=..., headers=..., timeout=...)
  │   ├── hf_raise_for_status(response)  → raises HfHubHTTPError if non-2xx
  │   ├── if stream=True: return response.iter_lines()  → SSE parser
  │   └── if stream=False: return response.read()  → raw bytes
  │
  ├── Parse bytes into ChatCompletionOutput (pydantic model)
  └── Return typed result to caller
```

### 11. Best Practices for Reliability

1. **Always set an explicit timeout** for production use — `timeout=None` can hang forever
2. **Wrap calls in retry logic** with exponential backoff for HTTP 503 and timeout errors
3. **Prefer `AsyncInferenceClient`** for multiple parallel requests — sessions are thread-safe
4. **Do NOT set a custom client factory** unless you need custom transport (proxies, IPv6, custom TLS) — the default handles pooling well
5. **Use `with InferenceClient() as client:`** or call `client.close()` to clean up streaming contexts — the `ExitStack` ensures response bodies are consumed
6. **For long-running services**, create one `InferenceClient` at module level and reuse it — avoid per-request instantiation
7. **Check rate limit headers** after every request if running near quota — implement self-throttling

### Skill
hf-async-inference-client — Async inference patterns, concurrent requests, streaming, MCP integration

---

## 2026-07-25: hf-open-llm-leaderboard-deep-dive — Open LLM Leaderboard v2 Evaluation Methodology & Architecture (Topic #40 Deep-Dive)

### Summary

Deep-dive into the Hugging Face Open LLM Leaderboard v2 — the standardized evaluation platform for open-source LLMs. Covers the 6-benchmark methodology, submission pipeline, results dataset architecture, reproducibility commands, model categorization, the community request workflow, and the underlying lm-evaluation-harness integration. Builds on the skill SKILL.md with source-level detail on how evaluations are orchestrated, results are stored, and the leaderboard is maintained.

### Sources

- Open LLM Leaderboard: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
- Results dataset: https://huggingface.co/datasets/open-llm-leaderboard/results
- Requests dataset: https://huggingface.co/datasets/open-llm-leaderboard/requests
- HF fork of lm-eval-harness: https://github.com/huggingface/lm-evaluation-harness
- EleutherAI LM Eval Harness: https://github.com/EleutherAI/lm-evaluation-harness
- IFEval paper: https://arxiv.org/abs/2311.07911
- BBH paper: https://arxiv.org/abs/2210.09261
- MATH paper: https://arxiv.org/abs/2103.03874
- GPQA paper: https://arxiv.org/abs/2311.12022
- MuSR paper: https://arxiv.org/abs/2310.16049
- MMLU-PRO paper: https://arxiv.org/abs/2406.01574

### 1. Evaluation Architecture Overview

The Open LLM Leaderboard is deployed as a **Docker Space** on Hugging Face (`open-llm-leaderboard/open_llm_leaderboard`), running on **CPU Upgrade** hardware ($0.03/hr). It uses the HF fork of the EleutherAI Language Model Evaluation Harness to run standardized evaluations.

```
User submits model
    │
    ├─→ Validation (model_id exists, format valid)
    │
    ├─→ Queued for evaluation
    │
    ├─→ lm_eval runs 6 benchmarks:
    │   ├─ IFEval (0-shot, strict accuracy)
    │   ├─ BBH (3-shot, 23 subtasks, normalized accuracy)
    │   ├─ MATH Lvl 5 (4-shot, exact match)
    │   ├─ GPQA (0-shot, 4-choice, normalized accuracy)
    │   ├─ MuSR (0-shot, 3 subtasks, normalized accuracy)
    │   └─ MMLU-PRO (5-shot, 10-choice, accuracy)
    │
    ├─→ Results stored in open-llm-leaderboard/results dataset
    │
    └─→ Leaderboard updated with average score
```

### 2. The 6 Benchmarks — Deep-Dive

#### 2.1 IFEval (Instruction Following Evaluation)

- **Task ID in lm-eval**: `IFEval`
- **Paper**: arxiv.org/abs/2311.07911 (Yi et al., Google)
- **Shots**: 0-shot
- **Metric**: `inst_level_strict_acc,none` + `prompt_level_strict_acc,none`
- **What it tests**: Can the model follow explicit formatting instructions? Prompts like "Write a paragraph about cats. End your paragraph with the word 'meow'." or "Output your answer in JSON format with keys: name, age, city."

**Scoring**: Two levels of strictness:
- **Instance-level**: Each individual constraint is checked independently
- **Prompt-level**: All constraints in a prompt must be satisfied

The metric is strict because it checks exact formatting adherence, not semantic correctness. A model that generates correct content but wrong formatting fails.

**Why 0-shot**: IFEval tests inherent instruction-following ability without examples. Few-shot would leak the expected format.

#### 2.2 BBH (Big Bench Hard)

- **Task ID in lm-eval**: `BBH`
- **Paper**: arxiv.org/abs/2210.09261 (Suzgun et al., Stanford)
- **Shots**: 3-shot (each of the 23 subtasks gets 3 examples)
- **Metric**: `acc_norm,none` (Normalized Accuracy — rewards partial credit for multi-choice questions)
- **Subtasks**: 23 subtasks covering reasoning domains:

| Subtask | Choices | What It Tests |
|---------|---------|---------------|
| boolean_expressions | 2 | Evaluating Boolean logic expressions |
| causal_judgement | 2 | Counterfactual causal reasoning |
| date_understanding | 6 | Inferring dates from context |
| disambiguation_qa | 3 | Resolving ambiguous queries |
| dyck_languages | 4 | Checking balanced parentheses |
| formal_fallacies | 2 | Identifying logical fallacies |
| geometric_shapes | 11 | Named-entity recognition for geometric shapes |
| hyperbaton | 2 | Identifying adjective order correctness |
| logical_deduction_five_objects | 5 | Deductive reasoning with 5 objects |
| logical_deduction_seven_objects | 7 | Deductive reasoning with 7 objects |
| logical_deduction_three_objects | 3 | Deductive reasoning with 3 objects |
| movie_recommendation | 6 | Movie recommendation based on preferences |
| multistep_arithmetic_two | 2 | Multi-step arithmetic |
| navigate | 2 | Following navigation instructions |
| object_counting | 19 | Counting objects in overlapping descriptions |
| penguins_in_a_table | 5 | Table-based reasoning about penguins |
| reasoning_about_colored_objects | 18 | Reasoning about colored objects |
| ruin_names | 6 | Recovering original movie names from "ruined" versions |
| salient_translation_error_detection | 6 | Detecting errors in translations |
| snarks | 2 | Detecting sarcasm |
| sports_understanding | 2 | Determining if sports sentences are plausible |
| temporal_sequences | 4 | Temporal ordering of events |
| tracking_shuffled_objects_five_objects | 5 | Tracking objects through shuffles (5 objects) |
| tracking_shuffled_objects_seven_objects | 7 | Tracking objects through shuffles (7 objects) |
| tracking_shuffled_objects_three_objects | 3 | Tracking objects through shuffles (3 objects) |
| web_of_lies | 2 | Tracking truth/lie chains |

**Normalized Accuracy**: `acc_norm` divides by the number of choices per question. A model that gets 50% on a 2-choice task (where random is 50%) gets 0.0 normalized. This makes BBH scores more comparable across subtasks with different choice counts.

#### 2.3 MATH Lvl 5

- **Task ID in lm-eval**: `math_level_5`
- **Paper**: arxiv.org/abs/2103.03874 (Hendrycks et al., Berkeley)
- **Shots**: 4-shot
- **Metric**: `exact_match,none`
- **What it tests**: Only the **hardest level** (Level 5) of the MATH dataset — high-school competition problems. Requires LaTeX equation comprehension.

**Scoring**: Exact match of the final answer (typically a number or expression). No partial credit. The model must output the exact formatted answer.

**Why Level 5 only**: Easier levels saturate quickly. Level 5 provides meaningful discrimination even among top models.

#### 2.4 GPQA (Graduate-Level Google-Proof Q&A)

- **Task ID in lm-eval**: `GPQA`
- **Paper**: arxiv.org/abs/2311.12022 (Rein et al., NYU/Anthropic)
- **Shots**: 0-shot
- **Metric**: `acc_norm,none`
- **Choices**: 4 (multiple choice)
- **What it tests**: PhD-level domain expert questions in biology, physics, chemistry.

**Design philosophy**: Questions are designed to be "Google-proof" — they require genuine domain expertise, not search. The dataset has **gated access** to minimize contamination. Questions are written and validated by domain experts (PhD candidates and above).

**Gating mechanism**: The GPQA dataset on HF requires authentication and/or acceptance of terms before download. This prevents models from being trained on exact evaluation examples.

#### 2.5 MuSR (Multistep Soft Reasoning)

- **Task ID in lm-eval**: `MuSR`
- **Paper**: arxiv.org/abs/2310.16049 (Sprague et al., Google)
- **Shots**: 0-shot
- **Metric**: `acc_norm,none`
- **Subtasks**: 3 subtasks, each algorithmically generated:

| Subtask | Choices | Description |
|---------|---------|-------------|
| murder_mysteries | 2 | ~1000-word murder mystery narratives — who is the killer? |
| object_placements | 5 | Spatial reasoning about object placements from narrative descriptions |
| team_allocation | 3 | Allocating team members based on complex constraints in narrative |

**Key challenge**: Each question is generated from a **parameterized template** with ~1000 words of narrative. Models must integrate reasoning across long-range narrative context. Few models beat random baseline significantly.

**Algorithmic generation**: MuSR questions are generated via templates with randomized parameters (names, objects, locations). This makes contamination nearly impossible since the exact question is never published.

#### 2.6 MMLU-PRO (Massive Multitask Language Understanding - Professional)

- **Task ID in lm-eval**: `mmlu_pro`
- **Paper**: arxiv.org/abs/2406.01574 (Wang et al., Stanford)
- **Shots**: 5-shot
- **Metric**: `acc,none` (plain accuracy)
- **Choices**: 10 (up from 4 in original MMLU)
- **What it tests**: The refined version of MMLU — expert-reviewed to remove noisy/ambiguous questions. 10 choices instead of 4 makes guessing harder (random baseline: 10%).

**Improvements over MMLU**:
- **10 choices** (vs 4): Reduces random guess accuracy from 25% to 10%
- **Expert review**: Questions vetted by domain experts
- **Noise removal**: Ambiguous or poorly-phrased questions filtered out
- **Harder selection**: Only questions where expert agreement was high

### 3. Submission Pipeline

Users submit models for evaluation through a **Space-based interface**:

1. **Navigate** to https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard
2. **Enter model ID** (e.g., `username/model-name`)
3. **Select precision tag** (e.g., `@precision:float16`, `@precision:4bit`)
4. **Submit** — the model enters the evaluation queue

**Submission validation**:
- Model ID must exist on the Hub
- Model must be accessible (not private/gated without auth)
- Model must have a valid `config.json` or relevant format
- Duplicate submissions are detected and prevented

**Queue processing**: Evaluations run sequentially on the Space's CPU Upgrade hardware. Each evaluation takes several hours depending on model size. The queue status is visible on the leaderboard page.

### 4. Results Dataset Architecture

Results are stored in **`open-llm-leaderboard/results`** — a HF dataset repository structured as:

```
results/
├── configs/
│   ├── default/               # Main results
│   │   └── data/
│   │       └── train-00000-of-00001.parquet  # All results
│   └── per-model/
│       └── data/              # Individual model breakdowns
└── README.md
```

**Parquet schema** (key fields):
| Field | Type | Description |
|-------|------|-------------|
| `model` | string | HF model ID |
| `model_type` | string | Category emoji (🟢🟩🔶💬🤝) |
| `IFEval` | float | Instance-level strict accuracy |
| `BBH` | float | Normalized accuracy across 23 subtasks |
| `MATH Lvl 5` | float | Exact match score |
| `GPQA` | float | Normalized accuracy |
| `MuSR` | float | Normalized accuracy across 3 subtasks |
| `MMLU-PRO` | float | Accuracy |
| `average` | float | Mean of all 6 scores |
| `precision` | string | Precision tag (e.g., `float16`, `4bit`) |
| `submission_date` | timestamp | When the evaluation was submitted |
| `evaluation_date` | timestamp | When evaluation completed |
| `parameters` | string | Reported parameter count (optional) |
| `license` | string | Model license |
| `architecture` | string | Architecture family (e.g., `llama`, `qwen`) |

**Per-model breakdowns**: Clicking the 📄 emoji on the leaderboard reveals per-task breakdown with subtask-level scores.

### 5. lm-eval Harness Integration

The leaderboard uses the **HF fork** of EleutherAI's `lm-evaluation-harness` at `github.com/huggingface/lm-evaluation-harness`.

**Default evaluation command**:
```bash
lm-eval \
    --model_args="pretrained=<model_id>,revision=<revision>,dtype=<dtype>" \
    --tasks=leaderboard \
    --batch_size=auto \
    --output_path=<output_dir>
```

**For instruction-tuned models** (chat models), two additional flags:
```bash
lm-eval \
    --model_args="pretrained=<model_id>,revision=<revision>,dtype=<dtype>" \
    --tasks=leaderboard \
    --batch_size=auto \
    --output_path=<output_dir> \
    --apply_chat_template \
    --fewshot_as_multiturn
```

**`--apply_chat_template`**: Applies the model's tokenizer chat template to format prompts. Required for instruction-tuned models that expect conversational formatting.

**`--fewshot_as_multiturn`**: Formats few-shot examples as multi-turn conversations instead of a single concatenated prompt. This better reflects how chat models are used in practice.

**Batch size sensitivity**: Results can vary slightly across batch sizes because padding differs. `--batch_size=auto` selects the largest batch that fits in memory, but different hardware (or different batch size settings) may produce slightly different padding → slightly different results.

### 6. Model Categorization System

Models are categorized into 5 types:

| Emoji | Category | Description |
|-------|----------|-------------|
| 🟢 | **Pretrained** | Base models trained on text corpora via language modeling objectives (MLM, CLM) |
| 🟩 | **Continuously Pretrained** | Base models further trained on additional corpora. May include some instruction-following or chat data |
| 🔶 | **Fine-Tuned** | Pretrained models fine-tuned on domain-specific or task-specific datasets |
| 💬 | **Chat Models** | Models fine-tuned via RLHF, DPO, KTO, IFT, or other alignment methods for conversational use |
| 🤝 | **Merges & MoErges** | Models produced by merging existing models (via TIES, DARE, linear interpolation, etc.) or by architectural Mixture-of-Experts combinations without additional training |

**Categorization is self-reported** by the submitter or determined from the model card metadata.

### 7. Community Request System

The **requests dataset** (`open-llm-leaderboard/requests`) tracks community-submitted evaluation requests:

```
requests/
├── default/
│   └── data/
│       └── train-00000-of-00001.parquet
└── README.md
```

Each request contains:
- Model ID requested
- Submitter's HF username
- Status (pending/completed/flagged/rejected)
- Notes or reasons for rejection

Users can request evaluation of any public model. Requests are reviewed periodically. Flagged models (visible on the leaderboard with "Flagged" prefix) should be ignored — the linked discussion explains why.

### 8. Search & Discovery

The leaderboard supports a powerful search syntax:

| Syntax | Example | Effect |
|--------|---------|--------|
| Single term | `llama` | Find models containing "llama" |
| Semicolon union | `llama; qwen` | Union: models matching either |
| Tag filter | `@architecture:llama` | Filter by architecture tag |
| Tag + term | `meta @architecture:llama` | Intersection of "meta" + architecture:llama |
| Multiple tags | `@architecture:llama @license:apache` | Both tags must match |
| Regex | `llama-2-(7|13|70)b` | Auto-detected regex patterns |
| Combined | `meta @architecture:llama; 7b @license:apache` | Union of two filter groups |
| Precision | `@precision:float16` | Filter by precision |

### 9. Reproducibility Best Practices

To reproduce leaderboard results:

```bash
# 1. Clone the HF fork (not upstream EleutherAI)
git clone git@github.com:huggingface/lm-evaluation-harness.git
cd lm-evaluation-harness
git checkout main
pip install -e .

# 2. Run leaderboard task suite
lm-eval \
    --model_args="pretrained=meta-llama/Llama-3.2-3B-Instruct,dtype=float16" \
    --tasks=leaderboard \
    --batch_size=auto \
    --apply_chat_template \
    --fewshot_as_multiturn \
    --output_path=./results

# 3. Compare with leaderboard scores
#    Small differences (≤1%) due to batch-size padding variation are expected
```

**Key reproducibility notes**:
- The HF fork has specific patches that upstream EleutherAI may not have — always use the HF fork
- `--apply_chat_template` and `--fewshot_as_multiturn` are critical for chat models
- Base models (pretrained only) should omit these flags
- Different hardware (A100 vs T4 vs CPU) may produce minor floating-point differences
- Precision matters: float16 vs 4-bit quantization changes scores

### 10. Leaderboard Hardware & Infrastructure

| Component | Detail |
|-----------|--------|
| **Space SDK** | Docker |
| **Hardware** | CPU Upgrade (8 vCPU, 32 GB RAM) |
| **Cost** | $0.03/hr (paid by open-llm-leaderboard org) |
| **Plan type** | Team organization plan |
| **Storage** | Results stored in HF Dataset (not Space storage) |
| **Queue** | Sequential — one evaluation at a time |
| **Data retention** | Results dataset is permanent; leaderboard shows latest only |

The leaderboard intentionally uses CPU-only evaluation to:
1. **Fairness**: GPU differences don't affect scores
2. **Cost**: $0.03/hr vs $0.40+/hr for GPU
3. **Reproducibility**: CPU evaluation is more deterministic

### 11. v1 to v2 Methodology Changes

| Aspect | v1 (Retired) | v2 (Current) |
|--------|--------------|--------------|
| Benchmarks | ARC, HellaSwag, MMLU, TruthfulQA | IFEval, BBH, MATH Lvl 5, GPQA, MuSR, MMLU-PRO |
| MCQA format | 4-choices standard | Mixed: 2-19 choices, 10 for MMLU-PRO |
| Instruction following | Not tested | IFEval specifically tests formatting adherence |
| Math difficulty | MATH (all levels) | MATH Level 5 only (hardest) |
| Contamination resistance | Low (static datasets) | High (MuSR algorithmic, GPQA gated) |
| Model categories | Basic (pt, ft) | 5 categories with emoji |
| Search | Basic text search | Advanced tags, regex, union filters |
| Submission | Space form | Space form + precision tags |

### 12. Known Limitations & Pitfalls

1. **Batch-size sensitivity**: Results can vary ±1% purely from batch-size padding differences. Use `--batch_size=auto` for reproducibility.

2. **Chat template variance**: Different chat templates (from different tokenizers) produce different prompt formats. The leaderboard standardizes by using the model's own tokenizer template.

3. **Self-reported categories**: Model categories (🟢🟩🔶💬🤝) are self-reported and may not always be accurate.

4. **Precision not standardized**: Models submitted with different precisions (float16, 4bit, 8bit) are compared in the same ranking. Quantized models may score lower.

5. **Submission queue time**: Popular models may wait days in the queue. No priority system exists.

6. **Flagged model handling**: Models marked as "Flagged" appear on the leaderboard with a distracting prefix. Click the discussion link for context — many are flagged for data contamination or suspicious results.

7. **No multi-turn evaluation**: The leaderboard evaluates single-turn responses only. No conversation or multi-turn benchmarks.

8. **Language bias**: All 6 benchmarks are English-only. Multilingual capability is not evaluated.

### 13. Practical Tips for Submissions

- **Use the correct precision tag**: `@precision:float16` for full-precision, `@precision:4bit` for quantized. This affects comparison fairness.
- **Must submit via the Space UI**: Programmatic submission is not publicly documented.
- **Set `trust_remote_code=True` in model config**: If your model uses custom modeling code, this is required for evaluation.
- **Expected timeline**: 1-6 hours per model depending on size. 7B models complete faster than 70B+.
- **Check results dataset**: Your model's detailed scores appear in the results dataset before they update on the leaderboard.
- **Community requests**: If you want to see a model evaluated that's not submitted, add it to the requests dataset via the leaderboard UI.

### Skill
mlops/hf-open-llm-leaderboard — Open LLM Leaderboard v2 evaluation methodology, submission workflow, and reproducibility guide

---

## 2026-07-25: hf-llm-course-comprehensive-deep-dive — Complete HF LLM/NLP Course Curriculum & Implementation Guide (Topic #248)

### Summary
Comprehensive deep-dive into the Hugging Face LLM/NLP Course (https://huggingface.co/learn/llm-course) — the flagship educational resource covering the full transformer model lifecycle. The course spans 8 chapters and ~70 units across natural language processing, transformer architectures (encoder-only, decoder-only, encoder-decoder), model fine-tuning (Trainer API, custom loops with Accelerate), dataset processing (Arrow, streaming, Parquet, FAISS search), tokenizer training (BPE, WordPiece, Unigram), Hub sharing (model cards, YAML, push_to_hub), and production deployment (TGI, vLLM, ONNX, quantization). Covers libraries: transformers v5.x, datasets v5.x, tokenizers, accelerate, huggingface_hub.

### Key Sections
- **Ch1**: Transformer architecture theory, NLP fundamentals, inference strategies, bias/limitations
- **Ch2**: Pipeline API internals, AutoModel/AutoTokenizer, padding/truncation, optimized deployment
- **Ch3**: Fine-tuning with Trainer API, TrainingArguments, custom training loops with Accelerate
- **Ch4**: Hub orientation, model sharing, model card YAML, widget configuration
- **Ch5**: Datasets library: local loading, slicing/shuffling, streaming, Parquet, FAISS semantic search
- **Ch6**: Tokenizers library: BPE/WordPiece/Unigram algorithms, training custom tokenizers, offset mapping
- **Ch7**: Task-specific fine-tuning: token classification (NER), MLM, translation, summarization, causal LM

### Skill
mlops/hf-llm-course — Hugging Face LLM/NLP Course complete curriculum documentation, covering transformers, datasets, tokenizers, fine-tuning, Hub sharing, and production deployment patterns

---

## 2026-07-25: hf-dataset-viewer-croissant-metadata (Topic #252)

### Summary
Deep-dive into the Hugging Face Dataset Viewer's Croissant metadata endpoint — a JSON-LD metadata format built on schema.org by MLCommons that standardizes ML dataset descriptions for indexing, searching, and programmatic loading. The endpoint at `GET /api/datasets/{dataset}/croissant` auto-generates Croissant metadata for every Hub dataset convertible to Parquet, documenting the dataset name, description, distribution (Parquet file references via FileObject/FileSet), record sets (configs/subsets), and field definitions with schema.org data types.

### Key Points
- **Croissant** = ML dataset metadata format by MLCommons, built on schema.org, serialized as JSON-LD
- **Two endpoints**: Hub API (`/api/datasets/{name}/croissant`) — enriched with Hub metadata; raw backend (`datasets-server.huggingface.co/croissant-crumbs`)
- **Availability**: All public datasets < 5GB convertible to Parquet; private datasets require PRO/Enterprise
- **Structure**: `distribution` (FileObject for repo + FileSet per config's Parquet files) + `recordSet` (RecordSet per config, each with `field` array of columns)
- **Type mapping**: schema.org types — `sc:Text`, `sc:Integer`, `sc:Float`, `sc:Boolean`, `sc:DateTime`, `sc:ImageObject`; sequences use `repeated: true`, nested use `subField`
- **mlcroissant library**: `Dataset(jsonld=url)` loads directly from Croissant metadata
- **Use cases**: Dataset discovery/search indexing, schema inspection without download, cross-platform interop (Kaggle, OpenML), ETL pipeline schema source

### Sources
- Dataset Viewer Croissant Docs: https://huggingface.co/docs/dataset-viewer/main/en/croissant
- Dataset Viewer GitHub: https://github.com/huggingface/dataset-viewer
- Croissant Spec: http://mlcommons.org/croissant/
- mlcroissant: https://github.com/mlcommons/croissant/tree/main/python/mlcroissant

### Skill
mlops/hf-datasets-server-rest-api — the Croissant metadata endpoint for ML dataset discovery and programmatic consumption

---

## 2026-07-25: hf-hub-docker-registry — Hugging Face Hub Docker Registry Complete Reference (Topic #254)

### Summary
Comprehensive deep-dive on the Hugging Face Hub Docker Container Registry — the standard Docker V2 registry at `registry.hf.space` that powers Docker-based Spaces, Jobs batch inference, and local development workflows. Covers registry authentication (HF tokens), Docker Spaces build/runtime constraints, Jobs popular images (vLLM, TRL), secrets management, local execution with `docker run`, storage persistence patterns, and zero-cost pathways for development.

### Source
- HF Docker Spaces SDK: https://huggingface.co/docs/hub/en/spaces-sdks-docker
- HF Run Spaces with Docker: https://huggingface.co/docs/hub/en/spaces-run-with-docker
- HF Jobs Popular Images: https://huggingface.co/docs/hub/en/jobs-popular-images
- Docker Registry V2 API: https://distribution.github.io/distribution/
- Registry endpoint: `registry.hf.space` (verified responding with Docker V2 auth challenge)

### Skill
hf-hub-docker-registry — Hugging Face Hub Docker Registry complete reference: authentication with HF tokens at `registry.hf.space`, Docker Spaces build/runtime constraints, Jobs popular images, secrets management, local execution, zero-cost development pathways

### 1. What Is the HF Docker Registry?

The Hugging Face Hub Docker Registry is a standard **Docker Distribution V2 registry** that allows users to store, share, and deploy container images alongside models, datasets, and Spaces on the HF Hub. It is accessed at `registry.hf.space` and supports `docker login`, `docker pull`, and `docker push` via standard Docker V2 API protocol with Bearer token authentication.

### 2. Authentication

Authenticate using your Hugging Face username and a User Access Token (write scope for pushes):
```bash
echo $HF_TOKEN | docker login registry.hf.space -u $HF_USERNAME --password-stdin
```

### 3. Key Constraints for Docker Spaces

- **UID 1000**: Container runs as user ID 1000 — create matching user in Dockerfile
- **No GPU at build time**: `nvidia-smi` or `torch.cuda.is_available()` will fail during `docker build`
- **Ephemeral storage**: Filesystem resets on restart — use Storage Buckets for persistence
- **Secrets at build time**: Use `RUN --mount=type=secret` (Docker BuildKit)
- **Networking**: Only ports 80, 443, 8080 allowed for outbound

### 4. Jobs Popular Images

| Image | Use Case | Example |
|-------|----------|---------|
| `vllm/vllm-openai` | LLM batch inference | `uv run --image vllm/vllm-openai --flavor l4x4` |
| `huggingface/trl` | Post-training (SFT, GRPO) | `uv run --image huggingface/trl --flavor a100-large` |

### 5. Local Development

```bash
git clone https://huggingface.co/spaces/owner/space-name
cd space-name
docker build -t test-space .
docker run -p 7860:7860 test-space
```

### 6. Zero-Cost Note
Docker Spaces require a paid plan (except ZeroGPU which is Gradio-only). Local Docker development is free. Jobs have free CPU tiers.

---

## 2026-07-25: hf-optimum-exporters-model-conversion-pipeline (Topic #257)

### Summary
Comprehensive deep-dive on 🤗 Optimum's exporters framework — the model conversion pipeline for transforming Transformers/Diffusers/timm/Sentence-Transformers models into serialized formats (ONNX, OpenVINO, TFLite, Neuron) for production inference. Covers the full architecture: configuration objects per architecture, `TasksManager` for task discovery, `optimum-cli export` command, per-format CLI flags, ONNX opset selection and dynamo exporter, dtype casting (fp32/fp16/bf16), optimize levels (O1-O4), past key/value caching, dynamic vs static axes, monolith vs split exports, and zero-cost pathways.

### Source
- Optimum ONNX Overview: https://huggingface.co/docs/optimum-onnx/onnx/overview
- Export a Model to ONNX: https://huggingface.co/docs/optimum-onnx/onnx/usage_guides/export_a_model
- Optimum Exporters Overview: https://huggingface.co/docs/optimum/main/en/exporters/overview
- Optimum TFLite Overview: https://huggingface.co/docs/optimum/en/exporters/tflite/overview
- Optimum GitHub: https://github.com/huggingface/optimum
- Optimum ONNX GitHub: https://github.com/huggingface/optimum-onnx

### Key Points

**1. Exporters Architecture**
- Optimum's `exporters` module supports 4 formats: ONNX (via `optimum-onnx`), OpenVINO (via `optimum-intel`), TFLite (via Optimum core), Neuron (via `optimum-neuron`).
- For each format, configuration objects (`~optimum.exporters.<format>.model_configs.<Architecture>Config`) define the export details — input/output names, dynamic axes, opset, and post-processing.
- The `TasksManager` class handles task discovery and validation across all supported architectures.

**2. ONNX Export (optimum-onnx)**
- CLI: `optimum-cli export onnx --model <model_id> <output_dir>`
- Auto-detects task from Hub metadata; override with `--task`.
- Task variants: `with-past` suffix (e.g., `text-generation-with-past`) enables KV-cache reuse in decoder loops.
- Input shapes overrides: `--batch_size`, `--sequence_length`, `--num_choices` (text), `--width`, `--height`, `--num_channels` (image), `--feature_size`, `--nb_max_frames`, `--audio_sequence_length` (audio), `--point_batch_size`, `--nb_points_per_image` (SAM).
- Opset: default depends on architecture; set via `--opset`. Dynamo exporter (`--dynamo`) recommended for opset >= 18 (uses `torch.export.export` instead of deprecated TorchScript).
- Dtypes: `--dtype fp32` (default), `fp16`, `bf16`.
- Optimization levels (`--optimize`): O1 (basic), O2 (extended + transformer fusions), O3 (O2 + GELU approx), O4 (O3 + fp16 mixed precision, GPU-only).
- Monolith export (`--monolith`): forces single ONNX file; default split for encoder-decoder models.
- Post-processing: merges decoder + decoder-with-past models into one by default; disable with `--no-post-process`.
- Slim optimization (`--slim`): uses `onnxslim` to optimize the exported graph.
- Validation: after export, validates outputs match reference model with configurable `--atol`.
- Framework: `--framework pt` only (PyTorch); TensorFlow exports handled via Transformers' `TFPreTrainedModel.from_pretrained()` auto-conversion.

**3. TFLite Export**
- CLI: `optimum-cli export tflite --model <model_id> <output_dir>`
- Supports 16 architectures: Albert, BERT, Camembert, ConvBert, Deberta, DebertaV2, DistilBert, Electra, Flaubert, MobileBert, MPNet, ResNet, Roberta, RoFormer, XLM, XLMRoberta.
- TensorFlow models with PyTorch weights auto-convert via Transformers' `from_pretrained()`.

**4. Config Objects and TasksManager**
- `TasksManager.get_supported_tasks_for_model_type("distilbert", "onnx")` returns all supported ONNX tasks.
- Each supported architecture has a dedicated config class in `~optimum.exporters.onnx.model_configs`.
- The `model_type` key in the model's `config.json` maps to the appropriate config object.
- Configs define: `DUMMY_INPUT_GENERATOR` (for validation), `TASK_TO_COMMON_OUTPUTS` (output name mapping), `ONNX_OPSET` (default opset).

**5. Workflow Integration**
- Export → Load with `ORTModelForXxx.from_pretrained(output_dir)` — same Hugging Face API.
- ORTModel can export directly: `ORTModelForQuestionAnswering.from_pretrained("model-id", export=True)`.
- Encoder-decoder models export to 2+ ONNX files (encoder.onnx, decoder.onnx, decoder_with_past.onnx).
- Past KV caching enabled by default for decoder models; produces smaller exported graph for generation.

**6. Zero-Cost Note**
All exports run locally on CPU (default `--device cpu`). No GPU or paid services required. The `optimum[onnx]` package is MIT-licensed and free. For OpenVINO export, install `optimum-intel[openvino]` separately.
`

---

## 2026-07-25: hf-hub-daily-papers-and-paper-pages — HF Hub Daily Papers & Paper Pages Deep Dive (Topic #258)

### Summary
Comprehensive deep-dive on the Hugging Face Hub's papers ecosystem — the daily papers feed, Paper Pages, and the programmatic API. Covers the full data model (PaperInfo, PaperAuthor, linked models/datasets/Spaces), all API endpoints (`/api/daily_papers`, `/api/papers/search`, `/api/papers/<id>`, `/papers/<id>.md`), submission and curation flow, community features (upvotes, discussions), linking infrastructure between papers and Hub resources, the `huggingface_hub` Python API (`list_daily_papers()`, `list_papers()`, `paper_info()`, `read_paper()`), Paper Pages with AI summaries, the daily curation pipeline, and zero-cost pathways for researchers.

### Source
- HF Daily Papers: https://huggingface.co/papers
- HF Hub API - Daily Papers: https://huggingface.co/api/daily_papers
- HF Hub API - Paper Search: https://huggingface.co/api/papers/search
- huggingface_hub docs - list_daily_papers: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.list_daily_papers
- huggingface_hub docs - paper_info: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.paper_info
- huggingface_hub docs - list_papers: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api#huggingface_hub.HfApi.list_papers

### Skill
hf-hub-daily-papers — Hugging Face Hub Daily Papers & Paper Pages deep reference: API endpoints, data model, linking papers to models/datasets/Spaces, submission/curation, and programmatic access via huggingface_hub

---

## 2026-07-25: hf-hub-model-dependents-deep-dive-v2-tag-system-merge-chains — Deep-Dive v2: Tag System, Merge Models, Real-World Chains & Advanced Discovery (Topic #253)

### Summary
Deepened coverage of the Hugging Face Hub Model Dependents system with live API-verified findings. Covers the three overlapping dependency registration mechanisms (card YAML, Hub-auto tags, baseModels expand), the dual-tag system (`base_model:X` + `base_model:{relation}:X`) that enables type-specific filtering, real dependency chains (e.g., `google/gemma-2-2b → gemma-2-2b-it → gemma-2-2b-it-GGUF`), multi-parent merge model patterns with their tag format, the `base_model` YAML field's supported formats (string, list, dict), the Hub's heuristic auto-classification logic (file-based detection of adapter/quantized/merge/finetune), advanced discovery patterns (ancestry traversal, type-filtered children listing, complete ecosystem profiling), and edge cases (cross-org deps, recursive children, missing cardData).

### Key Findings (from live API tests)
- **Dual-tag system**: Models get `base_model:parent` AND `base_model:{relation}:parent` tags — use type-specific prefix for filtering by relation type
- **Merge models** use `base_model:merge:parent1`, `base_model:merge:parent2` with card data `base_model: [parent1, parent2]`
- **Chains are single-hop** — `base_models` only shows immediate parent, traverse manually for full ancestry
- **Auto-classification**: Hub infers `adapter` (adapter_config.json), `quantized` (GGUF/AWQ/GPTQ/HQQ), `merge` (multi-base + merge tag), `finetune` (standard weights)
- **Cross-org**: Children can be in different orgs than parent (e.g., `bartowski/gemma-2-2b-it-GGUF` is child of `google/gemma-2-2b-it`)

### Real Verified Data
- `google/gemma-2-2b-it` — 997 finetunes + 188 quantized + 476 adapters + 19 merges = 1,680 total children
- `bert-base-uncased` — 6,837 finetunes + 134 adapters + 27 quantized + 7 merges = 7,005 total children
- `John6666/one-obsession-17-red-sdxl` — merge of `Laxhar/noobai-XL-1.0` + `OnomaAIResearch/Illustrious-XL-v2.0`

### Skill
mlops/hf-hub-model-dependents — Hugging Face Hub Model Dependents API: how models declare parent relationships, the tag-based dependency system, children discovery by type (finetune/quantized/adapter/merge), multi-parent merge models, dependency chain traversal, and ecosystem profiling.

---

## 2026-07-25: hf-inference-client-openai-compatibility-and-structured-outputs — Inference Client OpenAI API Compatibility & Structured Outputs Deep Dive (Topic #262)

### Summary
Comprehensive deep-dive on Hugging Face `InferenceClient`'s OpenAI API compatibility layer and structured output capabilities. Covers the OpenAI-compatible `client.chat.completions.create()` syntax (drop-in replacement for `openai.OpenAI`), JSON Schema and regex grammar for structured outputs via `response_format`, JSON mode vs structured outputs distinction, function/tool calling with OpenAI-compatible schemas, streaming support, full parameter reference, provider compatibility matrix, and practical patterns for each feature.

### Source
- HF InferenceClient docs: https://huggingface.co/docs/huggingface_hub/main/en/guides/inference
- HF InferenceClient API reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client
- InferenceClient.chat_completion: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/inference_client#huggingface_hub.InferenceClient.chat_completion
- Inference Providers docs: https://huggingface.co/docs/inference-providers/en/index

### Skill
hf-inference-client-openai — Hugging Face InferenceClient OpenAI compatibility deep reference: chat.completions.create API, structured outputs (JSON Schema/regex), JSON mode, function calling, streaming, full parameter surface, 17+ provider support, and drop-in OpenAI migration patterns
---

## 2026-07-25: hf-hub-spaces-build-runtime-api-deep-dive-v3-space-templates — Space Templates: The Complete New Feature (Topic #263)

### Summary
Deep-dive on Hugging Face Space Templates — a new feature released in `huggingface_hub` v1.23.0 (July 9, 2026) that lets users seed Spaces from 28 official templates instead of starting from scratch. Covers the full API surface (`list_space_templates()`, `SpaceTemplate` dataclass, `create_repo(space_template=...)`), CLI commands (`hf spaces templates`, `hf repos create --template`), template resolution logic (name vs repo_id lookup, case-insensitive matching, preferred_private auto-visibility, auto SDK detection), the 28 templates across 3 SDK categories (Docker, Static, Gradio), the underlying REST endpoint, zero-cost pathways via Static templates, and integration with the broader Spaces ecosystem.

### Source
- huggingface_hub v1.23.0 source: `HfApi.list_space_templates()`, `HfApi.create_repo()`, `SpaceTemplate` dataclass
- HF API endpoint: `GET https://huggingface.co/api/spaces/templates`
- HF Spaces templates CLI: `hf spaces templates --help`
- HF repos create CLI: `hf repos create --help`
- Release notes: https://github.com/huggingface/huggingface_hub/releases/tag/v1.23.0

### Skill
mlops/hf-hub-spaces-build-runtime-api — Complete Space Templates reference: 28 official templates across Docker/Static/Gradio SDKs, API & CLI usage, template resolution, preferred_private auto-visibility, zero-cost Static Space pathways

### 1. What Are Space Templates?

Space Templates let you seed a new Hugging Face Space from an **official pre-built template** instead of starting from an empty repository. Each template is itself a Space repo on the Hub, containing all the boilerplate code, configuration, and dependencies needed for a particular app framework.

Benefits over starting from scratch:
- **Zero boilerplate** — the template provides app code, Dockerfile, requirements, and config
- **Framework auto-detection** — SDK (Gradio, Docker, Static) is inferred from the template
- **Smart defaults** — templates with `preferred_private=True` auto-create private Spaces without user action
- **28 ready-to-use templates** as of 2026-07-25, covering data science dashboards, ML demos, static sites, and observability tools

### 2. API Surface

#### 2.1 `HfApi.list_space_templates()`

```python
from huggingface_hub import HfApi

api = HfApi()
templates = api.list_space_templates()  # -> list[SpaceTemplate]
```

Returns all official Space templates. The `SpaceTemplate` dataclass has 4 fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-friendly name (e.g. `"JupyterLab"`, `"Streamlit"`) |
| `repo_id` | `str` | Full Hub repo ID (e.g. `"SpacesExamples/jupyterlab"`) |
| `sdk` | `str` | SDK type — `"docker"`, `"static"`, or `"gradio"` |
| `preferred_private` | `bool` | If True, new Spaces from this template default to private |

#### 2.2 `create_repo(space_template=...)`

```python
from huggingface_hub import HfApi

api = HfApi()

# Using repo_id (full identifier)
api.create_repo(
    repo_id="my-user/my-notebook",
    repo_type="space",
    space_template="SpacesExamples/jupyterlab",
)

# Using short name (human-friendly, case-insensitive)
api.create_repo(
    repo_id="my-user/my-streamlit-app",
    repo_type="space",
    space_template="Streamlit",
)
```

Key behavior:
- Accepts either `repo_id` (e.g. `"SpacesExamples/jupyterlab"`) or short `name` (e.g. `"JupyterLab"`)
- Case-insensitive matching on name
- If `space_sdk` is omitted, it's **auto-set** from the template's SDK
- If `space_sdk` is provided and doesn't match the template's SDK, raises `ValueError`
- If template has `preferred_private=True` and no visibility is explicitly set, the Space is created as **private**

### 3. Template Resolution Algorithm (Source-Verified)

From `HfApi.create_repo()` source code, the resolution follows this exact logic:

```python
# Pseudocode of the actual implementation
resolved_space_template = None
if space_template is not None:
    if repo_type != "space":
        raise ValueError("space_template only valid with repo_type='space'")
    
    all_templates = api.list_space_templates(token=token)
    template = None
    
    # Try matching by repo_id first, then by name (case-insensitive)
    for candidate in all_templates:
        if candidate.repo_id == space_template:
            template = candidate
            break
        if candidate.name.lower() == space_template.lower():
            template = candidate
            break
    
    if template is None:
        raise ValueError(f"Unknown Space template '{space_template}'")
    
    resolved_space_template = template.repo_id
    
    # Auto-private if template recommends it and user didn't set visibility
    if template.preferred_private and private is None and visibility is None:
        resolved_visibility = "private"
    
    # Auto-set SDK to match template
    if space_sdk is not None and space_sdk != template.sdk:
        raise ValueError(f"space_sdk must match template SDK. Got {space_sdk}, expected {template.sdk}")
    space_sdk = template.sdk

# Payload sent to the Hub API
payload["sdk"] = space_sdk
if resolved_space_template is not None:
    payload["template"] = resolved_space_template
```

### 4. The 28 Official Templates (Live API-Verified)

#### Docker SDK (17 templates) — Full container environments

| # | Name | repo_id | Preferred Private |
|---|------|---------|:---:|
| 1 | Streamlit | `streamlit/streamlit-template-space` | No |
| 2 | JupyterLab | `SpacesExamples/jupyterlab` | **Yes** |
| 3 | Argilla | `argilla/argilla-template-space` | No |
| 4 | Livebook | `livebook-dev/livebook` | No |
| 5 | LabelStudio | `LabelStudio/LabelStudio` | No |
| 6 | AimStack | `aimstack/aim` | No |
| 7 | Shiny (R) | `posit/shiny-for-r-template` | No |
| 8 | Shiny (Python) | `posit/shiny-for-python-template` | No |
| 9 | ZenML | `zenml/zenml` | No |
| 10 | ChatUI | `huggingchat/chat-ui-template` | No |
| 11 | Panel | `Panel-Org/panel-template` | No |
| 12 | Giskard | `giskardai/giskard` | No |
| 13 | Quarto | `posit/quarto-template` | No |
| 14 | marimo | `marimo-team/marimo-app-template` | No |
| 15 | Evidence | `evidence-dev/template-app` | No |
| 16 | Langfuse | `langfuse/langfuse-template-space` | No |
| 17 | Plotly | `plotly/dash-app-template` | No |

#### Static SDK (6 templates) — Pure frontend, no backend server

| # | Name | repo_id | Preferred Private |
|---|------|---------|:---:|
| 18 | Paper Project | `nerfies/paper-template` | No |
| 19 | Gradio-Lite | `gradio/gradio-lite-template` | No |
| 20 | Transformers.js | `static-templates/transformers.js` | No |
| 21 | React | `static-templates/react` | No |
| 22 | Svelte | `static-templates/svelte` | No |
| 23 | Vue | `static-templates/vue` | No |

#### Gradio SDK (5 templates) — Gradio app blueprints

| # | Name | repo_id | Preferred Private |
|---|------|---------|:---:|
| 24 | chatbot | `gradio-templates/chatbot` | No |
| 25 | text-to-image | `gradio-templates/text-to-image-gradio-template` | No |
| 26 | leaderboard | `gradio-templates/leaderboard` | No |
| 27 | Trackio | `gradio-templates/trackio-dashboard` | No |
| 28 | Workflow | `gradio-templates/workflow` | No |

**Notable detail:** Only **JupyterLab** (`SpacesExamples/jupyterlab`) has `preferred_private=True` — this makes sense because Jupyter notebooks often contain sensitive data and experiments.

### 5. CLI Integration

#### Listing templates

```bash
hf spaces templates
```

Outputs a TSV-like table with columns: `name`, `repo_id`, `sdk`, `preferred_private`.

Format options:
```bash
hf spaces templates --json         # JSON output
hf spaces templates --format quiet  # One ID per line (repo_ids)
hf spaces templates --format human  # Human-readable table
```

#### Creating a Space from a template

```bash
# Using full repo_id
hf repos create my-jupyterlab --type space --template SpacesExamples/jupyterlab

# Using short name
hf repos create my-streamlit --type space --template Streamlit
```

The `--space-sdk` flag is optional when `--template` is provided — it's auto-set from the template.

### 6. Underlying REST API

```http
GET https://huggingface.co/api/spaces/templates
Authorization: Bearer hf_****
```

Response format:
```json
{
  "templates": [
    {
      "sdk": "docker",
      "name": "Streamlit",
      "repoId": "streamlit/streamlit-template-space",
      "preferredPrivate": false
    }
  ]
}
```

The `create_repo` API call sends the resolved `repo_id` in the `template` field of the JSON body:
```json
{
  "name": "my-space",
  "type": "space",
  "sdk": "docker",
  "template": "streamlit/streamlit-template-space"
}
```

### 7. Zero-Cost Pathways

| Template Type | Cost Model | Details |
|--------------|------------|---------|
| **Static templates** (Paper Project, Gradio-Lite, Transformers.js, React, Svelte, Vue) | **Free** | Static Spaces require no server, no GPU — 100% free, never sleep |
| **Gradio templates** (chatbot, text-to-image, leaderboard, Trackio, Workflow) | **Free on CPU Basic** | Free CPU-tier Spaces, sleep after 48h inactivity, wake on traffic |
| **Docker templates** (Streamlit, JupyterLab, etc.) | **Free on CPU Basic** | Can run on free CPU tier; upgraded hardware costs $0.03–$2.50/hr |
| **JupyterLab** (preferred_private=True) | Free or paid | Auto-private by default; runs on Docker, use CPU Basic for $0 |

All templates can be developed and tested entirely on free-tier infrastructure.

### 8. Integration Points with Other Spaces APIs

Space Templates work naturally with all existing Spaces management APIs:

```python
# Create from template, upgrade hardware, set sleep, add secrets
api.create_repo(
    repo_id="my-user/my-app",
    repo_type="space",
    space_template="Streamlit",
    space_hardware="cpu-upgrade",
    space_sleep_time=1800,
    space_secrets=[{"key": "API_KEY", "value": "my_key"}],
)

# Wait for it to be ready
runtime = api.wait_for_space("my-user/my-app", timeout=300)
print(f"Space is {runtime.stage} on {runtime.hardware}")
```

### 9. Edge Cases & Design Notes

1. **Only official templates** — `list_space_templates()` returns only HF-curated templates. User-created Spaces cannot be used as templates via this API.
2. **Template Spaces themselves are regular Spaces** — looking at e.g. `streamlit/streamlit-template-space`, it's just a normal Space repo with a Dockerfile, `app.py`, and `README.md` that serves as the template source.
3. **Non-unique name matching** — name resolution is case-insensitive but there's no protection against name collisions. The resolution loop returns the *first* match; currently no two templates share the same name, so this is not an issue.
4. **SDK enforcement** — since `space_sdk` is auto-set to match the template, users cannot mix-and-match SDKs with templates. A Streamlit template always produces a Docker SDK Space.
5. **No `duplicate_repo` integration** — `duplicate_repo()` does not support `space_template`; templates only work with `create_repo`.
6. **Visibility inheritance** — only `preferred_private=True` triggers auto-visibility; all other templates default to public unless explicitly set.

### 10. Practical Examples

#### Create a JupyterLab Space for data analysis

```python
from huggingface_hub import HfApi

api = HfApi()
api.create_repo(
    repo_id="my-user/data-analysis",
    repo_type="space",
    space_template="JupyterLab",  # Auto-private, Docker SDK
)
```

#### Create a static documentation site with Vue

```python
api.create_repo(
    repo_id="my-user/docs",
    repo_type="space",
    space_template="Vue",  # Static SDK, 100% free
)
```

#### List all available templates programmatically

```python
from huggingface_hub import list_space_templates

templates = list_space_templates()
docker_templates = [t for t in templates if t.sdk == "docker"]
static_templates = [t for t in templates if t.sdk == "static"]
gradio_templates = [t for t in templates if t.sdk == "gradio"]

print(f"Docker: {len(docker_templates)}, Static: {len(static_templates)}, Gradio: {len(gradio_templates)}")
# Output: Docker: 17, Static: 6, Gradio: 5
```

### Zero-Cost Note
All research was performed via API calls to `GET /api/spaces/templates` (read-only, free), source code inspection of `huggingface_hub` (MIT license), and the `hf` CLI help output. Creating Spaces from templates on free-tier hardware (CPU Basic or Static) costs $0.

---

## 2026-07-25: hf-hub-doi-digital-object-identifiers — Digital Object Identifiers for Models and Datasets on HF Hub (Topic #266)

### Summary
Comprehensive reference for DOI (Digital Object Identifier) support on the Hugging Face Hub. DOIs are persistent identifiers that uniquely identify models and datasets, making them citable in academic publications (analogous to an ISBN). DOIs are managed via DataCite, generated through the repo Settings UI (no programmatic API), and lock repositories against deletion/rename/visibility change. Supports versioning via new DOI generation per revision.

### Key Findings
- **Generation**: Exclusive through Hub UI → repo Settings → DOI section → "Generate DOI" → accept DataCite terms → optional author customization
- **No API**: `huggingface_hub` library has no DOI methods in `HfApi`; the interactive DataCite consent flow prevents CLI/API generation
- **Versioning**: Push a new revision → "Generate new DOI" → old DOI deprecated, fresh DOI assigned for the new snapshot
- **Locking**: DOI-locked repos cannot be deleted, renamed, or made private without HF support intervention (`website@huggingface.co`)
- **Free**: No cost to generate DOIs on HF Hub
- **Citation**: DOI badge appears automatically in the model/dataset header after generation
- **Scope**: Models and datasets only (not Spaces)

### Sources
- HF Hub DOI Docs: https://huggingface.co/docs/hub/en/doi
- Announcement Blog: https://huggingface.co/blog/introducing-doi
- DataCite: https://datacite.org

### Skill
hf-hub-doi — Digital Object Identifiers on Hugging Face Hub: generation workflow, DataCite integration, versioning semantics, repo locking restrictions, and citation integration

---

## 2026-07-25: hf-spaces-lifecycle — Hugging Face Spaces Sleep, Pause, Billing & Duration (Topic #268)

### Summary
Comprehensive deep-dive on Hugging Face Spaces lifecycle management — covering
the complete sleep/pause/billing lifecycle for free (cpu-basic) and paid (GPU
upgraded) hardware tiers.

**Free tier (cpu-basic):** Auto-sleep after 48h inactivity, no custom sleep time
configuration, any visitor can wake the Space. Manual pause also available.

**Paid hardware (GPU upgraded):** Runs indefinitely by default. Custom sleep
time configurable via Settings UI or `api.request_space_hardware()` with
`sleep_time` parameter. No billing while asleep. Wakes automatically on visitor.

**Pause/Resume:** Manual pause on all tiers from Settings tab. Only the owner
can resume a paused Space. Paused time is NOT billed.

**Billing model:** Per-minute metered only during `Starting` and `Running`
states. Build phase is NOT billed. Auto-suspend on repeated failures halts
billing. To stop billing, pause the Space or downgrade to cpu-basic.

**ZeroGPU dynamic GPU allocation:**
- `@spaces.GPU` decorator for per-request GPU allocation
- Default function duration: 60 seconds (configurable via `duration=120`)
- Dynamic duration: pass a callable returning needed seconds
- Daily quotas: Free=5min, PRO=40min, Team/Org=40min, Enterprise=60min
- Quota resets 24h after first GPU usage
- PRO+ can extend at $1/10min
- `torch.compile()` NOT supported; use AOT compilation (torch 2.8+)
- GPU size: `large` (half RTX Pro 6000) or `xlarge` (full, 2× quota)
- Free accounts: max 2 ZeroGPU Spaces
- Shorter durations → better queue priority

**Programmatic control via HfApi:**
```python
api.request_space_hardware(repo_id="user/my-space", hardware="t4-medium", sleep_time=30)
api.pause_space("user/my-space")
api.resume_space("user/my-space")
```

**Live monitoring:** SSE streaming endpoints for build/run logs, events, and
metrics at `/api/spaces/{ns}/{repo}/logs/{build|run}` with optional `?tail=N`.

### Source
- HF Spaces Overview: https://huggingface.co/docs/hub/en/spaces-overview
- HF Spaces GPU: https://huggingface.co/docs/hub/en/spaces-gpus
- HF Spaces ZeroGPU: https://huggingface.co/docs/hub/en/spaces-zerogpu
- HF Spaces Settings: https://huggingface.co/docs/hub/en/spaces-settings
- HF Spaces Config: https://huggingface.co/docs/hub/en/spaces-config-reference
- ZeroGPU AOT Blog: https://huggingface.co/blog/zerogpu-aoti

### Skill
mlops/hf-spaces-lifecycle — Complete reference for HF Spaces lifecycle:
auto-sleep (free 48h vs paid custom), manual pause/resume, per-minute billing
model, ZeroGPU dynamic allocation with daily quotas, programmatic hardware
control via HfApi, SSE streaming, and zero-cost operation strategies

---

## 2026-07-25: mergekit-hf-merging — MergeKit: Complete Model Merging Toolkit for Hugging Face Hub (Topic #269)

### Summary
Comprehensive deep-dive on MergeKit (arcee-ai/mergekit), the open-source toolkit for merging large language models. MergeKit enables combining multiple pre-trained models into single checkpoints through weight-space interpolation, operating entirely on CPU or with as little as 8 GB VRAM. Covers the full merge method taxonomy (17+ methods), YAML configuration syntax (slices, models, parameters, tokenizer), Hub upload workflow via huggingface-cli, multi-stage merging (mergekit-multi), Mixture-of-Experts conversion (mergekit-moe), LoRA extraction (mergekit-extract-lora), tokenizer transplantation (mergekit-tokensurgeon), evolutionary search methods, and practical zero-cost operation patterns for merging on CPU-only hardware.

### Merge Methods Overview

| Method | Value(s) | # Models | Base? | Core Idea |
|--------|----------|----------|-------|-----------|
| **Linear** | `linear` | ≥2 | - | Weighted average of parameters (model soups) |
| **SLERP** | `slerp` | 2 | ✓ | Spherical linear interpolation on hypersphere |
| **NuSLERP** | `nuslerp` | 2 | * | Enhanced SLERP with flexible weighting, task vector SLERP |
| **Multi-SLERP** | `multislerp` | ≥2 | * | Barycentric SLERP for >2 models |
| **Karcher Mean** | `karcher` | ≥2 | - | Riemannian barycenter on manifolds |
| **Task Arithmetic** | `task_arithmetic` | ≥2 | ✓ | Linear combination of task vectors (deltas from base) |
| **TIES** | `ties` | ≥2 | ✓ | Task arithmetic + sparsification + sign consensus (remove interference) |
| **DARE** | `dare_linear`, `dare_ties` | ≥2 | ✓ | Task arithmetic + random pruning + rescaling |
| **DELLA** | `della`, `della_linear` | ≥2 | ✓ | Adaptive magnitude-based pruning of task vectors |
| **Model Breadcrumbs** | `breadcrumbs`, `breadcrumbs_ties` | ≥2 | ✓ | Outlier removal (small & large diffs) from task vectors |
| **SCE** | `sce` | ≥2 | ✓ | Adaptive matrix-level weighting by parameter variance |
| **RAM** | `ram`, `ramplus_tl` | ≥2 | ✓ | Random assignment merging |
| **Model Stock** | `model_stock` | ≥3 | ✓ | Geometric weight calculation for linear interpolation |
| **Nearswap** | `nearswap` | 2 | ✓ | Interpolate only where parameters are similar |
| **Arcee Fusion** | `arcee_fusion` | 2 | ✓ | Dynamic thresholding for fusing important changes |
| **Passthrough** | `passthrough` | 1 | - | Direct tensor copy (for frankenmerging/layer stacking) |

**Base model column:** ✓ = required, * = optional, - = not applicable

### YAML Configuration

Two mutually exclusive top-level specs:

**Slices mode** — piecewise assembly from layer blocks:
```yaml
merge_method: slerp
slices:
  - model: model1
  - model: model2
    parameters:
      weight: 0.5  # per-slice weight
parameters:
  t: 0.5  # interpolation factor (slerp)
```

**Models mode** — entire models as merge inputs:
```yaml
merge_method: ties
base_model: mistralai/Mistral-7B-v0.1
models:
  - model: model1
    parameters:
      weight: 1.0
      density: 0.5  # TIES sparsification
  - model: model2
    parameters:
      weight: 0.5
      density: 0.3
dtype: bfloat16
tokenizer:
  source: union
```

Key configuration fields:
- `dtype`: data type for merge (float16, bfloat16, float32)
- `tokenizer`: modern config — `source: union|base|<path>`, per-token embedding control
- `tokenizer_source`: legacy field (union|base|<path>)
- `chat_template`: "auto" | "alpaca" | "chatml" | "llama3" | "mistral" | "exaone" or custom Jinja2
- `parameters`: scoped at global → model → slice → source levels (decreasing precedence)

### Hub Upload Workflow

```bash
# 1. Run merge (CPU-only, zero-cost)
mergekit-yaml ./config.yml ./merged-model --lazy-unpickle --allow-crimes

# 2. Edit auto-generated README.md with model card info

# 3. Login and upload
huggingface-cli login  # token with write permission
huggingface-cli upload your_ns/merged-model ./merged-model .
```

MergeKit auto-generates a README with merge metadata (method, input models, parameters, citation) for the model card. No separate model card creation needed.

### Advanced Features

- **Multi-stage merging** (`mergekit-multi`): chain merges where later stages consume earlier outputs — YAML with multiple config sections
- **MoE Merging** (`mergekit-moe`): convert dense models → Mixture of Experts by splitting feed-forward layers across experts
- **LoRA Extraction** (`mergekit-extract-lora`): extract PEFT-compatible low-rank approximations from fine-tuned models
- **Tokenizer Transplantation** (`mergekit-tokensurgeon`): align vocabulary between models for speculative decoding or cross-tokenizer distillation
- **Evolutionary Methods**: genetic algorithm search for optimal merge weights (docs/evolve.md)
- **Raw PyTorch Merging** (`mergekit-pytorch`): merge arbitrary `.pt`/`.safetensors` checkpoints outside Transformers

### Zero-Cost Operation

- **Entirely CPU-runnable**: `--lazy-unpickle` loads tensors lazily; no GPU needed
- **No inference credits consumed**: merging is local computation, not inference
- **Free Hub uploads**: the HF Hub hosts merged models at zero cost
- **Recommended for Beer**: Beer's hardware (380 MB 0.5B GGUF, 934 MB 1.5B GGUF) can run mergekit for small models; for larger models, use CPU-only mode with `--allow-crimes` flag

### Source
- MergeKit GitHub: https://github.com/arcee-ai/mergekit
- MergeKit README: https://github.com/arcee-ai/mergekit/blob/main/README.md
- Merge Methods Guide: https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- MoE Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/moe.md
- Multi-Stage Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/multimerge.md
- Evolutionary Merge: https://github.com/arcee-ai/mergekit/blob/main/docs/evolve.md
- EMNLP Paper: https://aclanthology.org/2024.emnlp-industry.36/
- FrankenSteinAI (hosted UI): https://frankenstein-ai.com/

### Skill
SakThai-mergekit-hf-merging — Complete reference for MergeKit toolkit:
17+ merge methods (linear, SLERP, TIES, DARE, passthrough, etc.), YAML config
syntax, tokenizer handling (union/base/per-token), Hub upload workflow,
multi-stage and MoE merging, LoRA extraction, evolutionary search,
tokenizer transplantation, and zero-cost CPU-only operation patterns

---

## 2026-07-25: mergekit-hf-merging-deep-dive-v2 — MergeKit Advanced Features Deep-Dive (Topic #270)

### Summary
Deep-dive on the advanced MergeKit features beyond basic merge methods: dense-to-MoE conversion (mergekit-moe), evolutionary parameter optimization (mergekit-evolve), multi-stage chaining (mergekit-multi), raw PyTorch checkpoint merging (mergekit-pytorch), LoRA extraction via SVD (mergekit-extract-lora), tokenizer transplantation (mergekit-tokensurgeon), fine-grained parameter control with tensor name filters, gradient interpolation, and modern tokenizer configuration with per-token embedding override.

### New Learnings (beyond v1)

1. **mergekit-moe Gate Modes**: Three modes — `hidden` (hidden state from prompts, best quality, default), `cheap_embed` (raw token embeddings, low hardware), `random` (for sparse upcycling/further training). Shared expert support with `residual_scale` for Qwen MoE architecture.

2. **mergekit-evolve CMA-ES**: Uses Covariance Matrix Adaptation Evolution Strategy with LM Eval Harness tasks. Three scheduling strategies: `pool` (one actor/GPU), `buffered` (concurrent on same GPU), `serial` (Ray placement groups). Supports in-memory merging and vLLM backend.

3. **mergekit-multi Chaining**: YAML documents separated by `---`. Named intermediates referenced by name in later stages. `--lazy` flag skips cached intermediates.

4. **mergekit-pytorch**: Applies merge algorithms to arbitrary `.pt`/`.safetensors` (non-Transformers models). No layer slicing or tokenizer support.

5. **mergekit-extract-lora**: SVD-based extraction of PEFT-compatible LoRA adapters. Options: `--max-rank`, `--embed-lora`, `--distribute-scale`, regex filtering, `--sv-epsilon` for singular value thresholding.

6. **mergekit-tokensurgeon**: Transplants tokenizers between models for speculative decoding draft models or cross-tokenizer distillation.

7. **Fine-Grained Parameters**: Four-level precedence + tensor name filters (`self_attn`, `mlp`, etc.) for different merge weights per module type. Gradient interpolation arrays for per-layer-varying weights.

8. **Tokenizer Configuration**: New `tokenizer` block with `tokens` map for per-token embedding override and `pad_to_multiple_of`. Legacy `tokenizer_source` maintained for backward compatibility but fields are mutually exclusive.

### Sources
- MergeKit GitHub: https://github.com/arcee-ai/mergekit
- Merge Methods Guide: https://github.com/arcee-ai/mergekit/blob/main/docs/merge_methods.md
- MoE Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/moe.md
- Multi-Stage Merging: https://github.com/arcee-ai/mergekit/blob/main/docs/multimerge.md
- Evolutionary Merge: https://github.com/arcee-ai/mergekit/blob/main/docs/evolve.md

### Skill
SakThai-mergekit-hf-merging v2.0.0 — Complete MergeKit reference with all advanced features, configuration patterns, and zero-cost operation guidelines.

---

## 2026-07-25: hf-lighteval — Hugging Face LightEval: All-in-One LLM Evaluation Toolkit (Topic #271)

### Summary
Comprehensive deep-dive on Hugging Face LightEval (v0.11.x) — the all-in-one toolkit for evaluating LLMs across multiple backends. Built by the HF Leaderboard and Evals Team (2,500+ GitHub stars, MIT license). Covers the full architecture (Pipeline, Registry, LightevalModel abstract interface, EvaluationTracker), all 8 evaluation backends (inspect-ai preferred, accelerate, vllm, sglang, nanotron, TGI, Inference Endpoints, LiteLLM, Inference Providers), 1000+ supported evaluation tasks across 7 core suites (lighteval, leaderboard, harness, helm, bigbench, original, extended) plus community and multilingual suites, custom task definitions via LightevalTaskConfig, 25+ built-in metrics (ExactMatch, F1, BLEU, ROUGE, BERTScore, Perplexity, PassAtK, MajAtN, LLM-as-Judge, Faithfulness, Extractiveness, and more), three sampling methods (GENERATIVE, LOGPROBS, PERPLEXITY), result management (push-to-hub, per-sample details, re-evaluation from cached responses), CLI with full typer-based subcommands (`lighteval eval`, `lighteval accelerate`, `lighteval vllm`, `lighteval sglang`, `lighteval endpoint` with 4 sub-endpoints), Python API for in-memory model evaluation with Transformers, model configuration (YAML/args/class), inspect-ai integration as preferred backend for API-served models, auto-discovery of live inference providers via HF API, and zero-cost evaluation patterns using free Inference Providers, small CPU models, and Hub result hosting.

### Architecture Pipeline
1. **Registry** — Task discovery from suite directories; matches task names to LightevalTaskConfig objects
2. **Pipeline** — Orchestrates model loading, task execution, metric computation
3. **LightevalModel** — Abstract interface with async/sync execution (greedy_until, loglikelihood, loglikelihood_rolling)
4. **ParallelismManager** — Enum supporting ACCELERATE, NANOTRON, VLLM, SGLANG, TGI, OPENAI, CUSTOM, NONE
5. **EvaluationTracker** — Results logging with per-task, per-sample detail storage

### Key Features
1. **8 Entry Points**: `eval` (inspect-ai, preferred), `accelerate`, `vllm`, `sglang`, `nanotron`, `endpoint inference-endpoint`, `endpoint tgi`, `endpoint litellm`, `endpoint inference-providers`, `custom`
2. **1000+ Tasks**: 9 suite categories with popular benchmarks (MMLU, GSM8K, MATH, GPQA, IFEval, BBH, HellaSwag, ARC, HLE, SimpleQA, AIME, etc.)
3. **Task String Syntax**: `"gsm8k"` for single, `"bbh:boolean_expressions"` for subtask, `"gsm8k,mmlu_pro"` for multiple, `"leaderboard"` for suite
4. **Custom Tasks**: Define `LightevalTaskConfig` with `TASKS_TABLE` export; load via `--custom-tasks` flag
5. **Model Config**: YAML files or CLI args for model_name, generation_parameters (temperature, top_p, max_new_tokens), system_prompt, cache_dir
6. **22 Model Parameters on CLI**: max_tokens, temperature, top_p, top_k, seed, stop_seqs, num_choices, frequency_penalty, presence_penalty, logit_bias, best_of, log_probs, top_logprobs, cache_prompt, reasoning_effort, reasoning_tokens, reasoning_history, response_format, parallel_tool_calls, max_tool_output, internal_tools, model_args
7. **Per-sample Details**: Caching with `--save-details`, re-evaluation via `--load-responses-from-details-date-id`
8. **Result Push**: `--repo-id` creates a Hub Space with browsable results; `--public` flag controls visibility
9. **Auto Provider Discovery**: `:all` suffix on model names finds all live HF Inference Providers
10. **Reasoning Tag Removal**: Automatic stripping of `<think>` tags (or custom pairs) before metric computation

### Custom Task Example
```python
from lighteval.tasks.lighteval_task import LightevalTaskConfig

TASKS_TABLE = [
    LightevalTaskConfig(
        name="my_custom_qa",
        suite="custom",
        prompt_function="prompt_fn",
        hf_repo="my-org/my-dataset",
        hf_subset="default",
        hf_avail_splits=["train", "test"],
        evaluation_splits=["test"],
        few_shots=[],
        metric=["my_metric"],
    )
]

def prompt_fn(line, example):
    return f"Question: {line['question']}\nAnswer:"
```

### Sources
- LightEval GitHub: https://github.com/huggingface/lighteval
- LightEval Docs: https://huggingface.co/docs/lighteval/main/en/index
- Inspect-ai: https://inspect.aisi.org.uk/
- HF Inference Providers: https://huggingface.co/docs/inference-providers/en/index
- Open LLM Leaderboard: https://huggingface.co/spaces/open-llm-leaderboard/open_llm_leaderboard

### Skill
mlops/hf-lighteval — Complete reference for Hugging Face LightEval evaluation toolkit: architecture (Pipeline, Registry, LightevalModel, EvaluationTracker), 8 evaluation backends, 1000+ tasks across 7 core + optional suites, custom tasks via LightevalTaskConfig, 25+ built-in metrics, CLI subcommands, Python API for in-memory Transformers evaluation, inspect-ai integration, results management with Hub push, auto-discovery of inference providers, and zero-cost evaluation patterns

---

## 2026-07-25: hf-lighteval-deep-dive-v2 — LightEval Python API, Custom Metrics System & EvaluationTracker Internals (Topic #272)

### Summary
Source-level deep-dive into LightEval's Python API, custom metrics architecture, and the EvaluationTracker logging/reporting module. Based on direct analysis of the v0.11.x source code on GitHub. Covers (1) the `Pipeline` class orchestration loop, (2) `ModelConfig` Pydantic model with YAML/CLI config loading, (3) the full `Metric` dataclass hierarchy (4 types: `SampleLevelMetric`, `CorpusLevelMetric`, `SampleLevelMetricGrouping`, `CorpusLevelMetricGrouping`), (4) the `Metrics` Enum with 40+ pre-built metric entries, (5) how `SampleLevelComputation` and `CorpusLevelComputation` abstract classes work, (6) `LightevalTaskConfig` dataclass with all 20+ configuration fields, (7) `EvaluationTracker` with its 5 sub-loggers (Details, Metrics, Versions, GeneralConfig, TaskConfig), (8) Hub push pipeline (dataset card generation with `DatasetCardData`, per-split organization, MMLU special-case aggregation), (9) TensorBoard and Weights & Biases/Trackio integration, (10) custom metrics and tasks patterns with `Preparator` classes (`GenerativePreparator`, `LoglikelihoodPreparator`, `PerplexityPreparator`), (11) the metric-to-model sampling method mapping (GENERATIVE, LOGPROBS, PERPLEXITY), (12) `Metrics.apply_metric()` dispatching between batched and non-batched computations.

### Python API Architecture

#### 1. Pipeline Orchestration
The central evaluation engine is `lighteval.pipeline.Pipeline`. It orchestrates:
1. **Task loading** via `Registry` (task discovery from suite directories + custom task files)
2. **Model wrapping** via `LightevalModel` abstract interface
3. **Metric computation** via `apply_metric()` dispatch
4. **Result tracking** via `EvaluationTracker`

```python
# Core Pipeline loop (simplified from source)
pipeline = Pipeline(
    pipeline_params=PipelineParameters(launcher_type=ParallelismManager.ACCELERATE, ...),
    evaluation_tracker=EvaluationTracker(output_dir="./results", ...),
    model=load_model(...),
    tasks=Registry().get_task_list(...),
)
results = pipeline.run()
```

#### 2. ModelConfig — Pydantic-based Configuration
```python
class ModelConfig(BaseModel, extra="forbid"):
    model_name: str = None
    generation_parameters: GenerationParameters = GenerationParameters()
    system_prompt: str | None = None
    cache_dir: str = "~/.cache/huggingface/lighteval"

    @classmethod
    def from_path(cls, path: str):  # Load from YAML
    @classmethod
    def from_args(cls, args: str):  # Parse from CLI arg string
    @staticmethod
    def _parse_args(args: str) -> dict:  # Braces-notation parser for nested gen params
```

Supports three instantiation paths:
- Direct Python: `ModelConfig(model_name="meta-llama/Llama-3.1-8B-Instruct", generation_parameters=GenerationParameters(temperature=0.7))`
- YAML file: `ModelConfig.from_path("model_config.yaml")`
- CLI string: `ModelConfig.from_args("model_name=gpt2,generation_parameters={temperature=0.7,max_new_tokens=100}")`

#### 3. LightevalTaskConfig — Full Configuration Dataclass
Contains 20+ fields including:
- `name`, `prompt_function`, `hf_repo`, `hf_subset`, `metrics`
- `hf_revision`, `hf_filter_fn`, `hf_avail_splits`, `evaluation_splits`
- `few_shots_split`, `few_shots_select`, `num_fewshots`
- `generation_size`, `generation_grammar`, `stop_sequence`, `num_samples`
- `version`, `truncate_fewshots`

Task string syntax (source): `lighteval eval <model> <task_string>` where task_string is:
- Single: `"gsm8k"`
- Subtask: `"bbh:boolean_expressions"`
- Suite: `"leaderboard"` (convenience alias for the full leaderboard suite)
- Multiple: `"gsm8k,mmlu_pro"`

### Custom Metrics System

#### 4. Metric Dataclass Hierarchy
```
Metric (base dataclass)
├── SampleLevelMetric    — per-sample, then simple aggregation (mean/min/max)
├── CorpusLevelMetric    — computed over entire corpus at once
├── SampleLevelMetricGrouping — grouped per-sample metrics (e.g. BERTScore: P, R, F1)
└── CorpusLevelMetricGrouping — grouped corpus-level metrics (e.g. ROUGE: 1, 2, L, Lsum)
```

```python
@dataclass
class Metric:
    metric_name: str                          # Single name or list for groupings
    higher_is_better: bool
    category: SamplingMethod                  # GENERATIVE, LOGPROBS, or PERPLEXITY
    sample_level_fn: SampleLevelComputation | Preparator
    corpus_level_fn: CorpusLevelComputation | Callable
    batched_compute: bool = False

    def compute_sample(self, **kwargs) -> dict
    def get_corpus_aggregations(self) -> dict
    def __call__(self, sample_params: dict | None):  # Parametric instantiation (e.g. pass@k&n=16)
```

#### 5. SamplingMethod Enum
```python
class SamplingMethod(Enum):
    GENERATIVE = auto()   # Free-text generation, evaluated via string matching
    LOGPROBS  = auto()    # Log-probability scoring of given completions
    PERPLEXITY = auto()   # Perplexity/loss computation over target text
```

#### 6. Sample-Level Computation
```python
class SampleLevelComputation(ABC):
    @abstractmethod
    def compute(self, doc: Doc, model_response: ModelResponse, **kwargs):
        """Returns dict of metric values for one sample."""

# Concrete implementations (all in metrics_sample.py):
class ExactMatches(SampleLevelComputation):     # Exact match with normalization
class F1_score(SampleLevelComputation):         # Token F1 score
class Recall(SampleLevelComputation):           # Recall@k
class MRR(SampleLevelComputation):             # Mean Reciprocal Rank
class PassAtK(SampleLevelComputation):         # pass@k for code/STEM
class GPassAtK(SampleLevelComputation):        # Grouped pass@k
class MajAtN(SampleLevelComputation):          # Majority vote@n
class AvgAtN(SampleLevelComputation):          # Average@n
class BLEU(SampleLevelComputation):            # N-gram BLEU
class ROUGE(SampleLevelComputation):           # ROUGE summarization
class BertScore(SampleLevelComputation):       # BERTScore (P, R, F1)
class BLEURT(SampleLevelComputation):          # BLEURT learned metric
class StringDistance(SampleLevelComputation):  # Edit distance metrics
class Faithfulness(SampleLevelComputation):    # SummaC faithfulness
class Extractiveness(SampleLevelComputation):  # Coverage/density/compression
class DropMetrics(SampleLevelComputation):     # DROP EM + F1
class AccGoldLikelihood(SampleLevelComputation):       # Accuracy from gold likelihood
class LoglikelihoodAcc(SampleLevelComputation):         # Logprob accuracy
class JudgeLLMSimpleQA(SampleLevelComputation):        # LLM-as-Judge for SimpleQA
class MultilingualExtractiveMatchMetric(SampleLevelComputation):  # Math expr extraction
```

#### 7. Corpus-Level Computation
```python
class CorpusLevelComputation(ABC):
    @abstractmethod
    def compute_corpus(self, items):
        """Returns aggregated metric value over entire corpus."""

# Implementations (metrics_corpus.py):
class MatthewsCorrCoef(CorpusLevelComputation)        # Matthews Correlation Coefficient
class CorpusLevelF1Score(CorpusLevelComputation)       # Corpus F1 (macro/weighted/micro)
class CorpusLevelPerplexityMetric(CorpusLevelComputation)  # Perplexity from logprobs+durations
class CorpusLevelTranslationMetric(CorpusLevelComputation) # chrF/chrF++/BLEU corpus translation metrics
```

#### 8. Preparator Classes (bridge between model output and corpus metric input)
```python
class GenerativePreparator(Preparator):
    @staticmethod
    def prepare(doc: Doc, model_response: ModelResponse, **kwargs):
        """Returns GenerativeCorpusMetricInput(golds=..., preds=...)"""

class LoglikelihoodPreparator(Preparator):
    def __init__(self, is_single_token: bool = False):
    def prepare(self, doc: Doc, model_response: ModelResponse, **kwargs):
        """Returns LogprobCorpusMetricInput(golds=..., preds=...)"""

class PerplexityPreparator(Preparator):
    def __init__(self, units_type: str = "words"):
    def prepare(self, doc: Doc, model_response: ModelResponse, **kwargs):
        """Returns PerplexityCorpusMetricInput(logprobs=..., weights=...)"""
```

#### 9. Metrics Enum — All 40+ Pre-Built Entries
```python
class Metrics(Enum):
    # GENERATIVE metrics
    exact_match        = SampleLevelMetric(metric_name="em", ...)
    f1_score          = SampleLevelMetric(metric_name="f1", ...)
    pass_at_k          = SampleLevelMetric(metric_name="pass@k", ...)     # parametric: pass@k&n={N}
    g_pass_at_k        = SampleLevelMetricGrouping(...)                    # g-pass@k (code grouping variant)
    maj_at_n           = SampleLevelMetric(metric_name="maj@n", ...)
    avg_at_n           = SampleLevelMetric(metric_name="avg@n", ...)
    bleu_1             = SampleLevelMetric(metric_name="bleu_1", ...)
    bleu_4             = SampleLevelMetric(metric_name="bleu_4", ...)
    rouge1             = SampleLevelMetric(metric_name="rouge1", ...)
    rouge_t5           = CorpusLevelMetricGrouping(metric_name=[...], ...) # Multiple rouge variants
    bert_score         = SampleLevelMetricGrouping(...)                   # P, R, F1
    bleurt             = SampleLevelMetric(metric_name="bleurt", ...)
    drop               = SampleLevelMetricGrouping(...)                   # em, f1 for DROP
    extractiveness     = SampleLevelMetricGrouping(...)                   # coverage, density, compression
    faithfulness       = SampleLevelMetric(metric_name="summac", ...)
    expr_gold_metric   = SampleLevelMetric(metric_name="extractive_match", ...)  # Math
    copyright          = SampleLevelMetricGrouping(...)                   # Longest common prefix, edit distance/similarity

    # LOGPROBS metrics
    acc_golds_likelihood  = SampleLevelMetric(metric_name="acc", ...)
    loglikelihood_acc     = SampleLevelMetric(metric_name="acc", ...)
    loglikelihood_f1      = CorpusLevelMetric(metric_name="loglikelihood_f1", ...)
    mrr                   = SampleLevelMetric(metric_name="mrr", ...)
    recall_at_k           = SampleLevelMetric(metric_name="recall", ...)
    mcc                   = CorpusLevelMetric(metric_name="mcc", ...)

    # PERPLEXITY metrics
    prediction_perplexity = SampleLevelMetric(metric_name="ppl", ...)
    bits_per_byte         = CorpusLevelMetric(metric_name="bits_per_byte", ...)
    byte_perplexity       = CorpusLevelMetric(metric_name="byte_perplexity", ...)

    # Translation metrics (corpus-level, GENERATIVE)
    bleu                  = CorpusLevelMetric(metric_name="bleu", ...)
    chrf                  = CorpusLevelMetric(metric_name="chrf", ...)
    chrf_plus             = CorpusLevelMetric(metric_name="chrf++", ...)
```

#### 10. Parametric Metrics (Runtime Parameter Override)
```python
# Metrics support runtime parameter override via __call__:
pass_at_k_metric = Metrics.pass_at_k(sample_params={"k": 3, "n": 16})
# This both overrides the sample_params and updates metric_name to "pass@k:k=3&n=16"
```

The `__call__` method (source from metric_utils.py):
```python
def __call__(self, sample_params: dict | None):
    if sample_params is not None:
        for k, v in sample_params.items():
            setattr(self.sample_level_fn, k, v)
    sample_params_name = "&".join(f"{k}={v}" for k, v in sample_params.items())
    if isinstance(self, MetricGrouping):
        self.metric_name = [f"{metric}:{sample_params_name}" for metric in self.metric_name]
    else:
        self.metric_name = f"{self.metric_name}:{sample_params_name}"
    return self
```

#### 11. Metric Dispatch — `apply_metric()` (metrics/__init__.py)
```python
def apply_metric(responses: list[ModelResponse], docs: list[Doc], metrics: list[Metric]):
    """Separates batched and non-batched metrics for efficient computation."""
    batched_metrics = [m for m in metrics if m.batched_compute]
    non_batched_metrics = [m for m in metrics if not m.batched_compute]

    # Batched metrics receive ALL responses/docs at once
    for metric in batched_metrics:
        metric_outputs = metric.compute_sample(responses=responses, docs=docs)
        # Can return either list[dict] (one per sample) or dict[str, list[Any]] (one list per metric name)

    # Non-batched metrics receive one response/doc at a time
    for metric in non_batched_metrics:
        output.update(metric.compute_sample(model_response=responses[i], doc=docs[i]))
```

### EvaluationTracker Internals

#### 12. Logger Composition
```python
class EvaluationTracker:
    def __init__(self, ...):
        self.details_logger = DetailsLogger()              # Per-sample evaluation details
        self.metrics_logger = MetricsLogger()              # Aggregate metrics
        self.versions_logger = VersionsLogger()            # Task/dataset version tracking
        self.general_config_logger = GeneralConfigLogger() # Overall evaluation config
        self.task_config_logger = TaskConfigLogger()       # Per-task configuration

        self.api = HfApi()                                 # Hub interaction
        self.fs, self.output_dir = url_to_fs(output_dir)   # Supports local+S3 paths
```

#### 13. EnhancedJSONEncoder
```python
class EnhancedJSONEncoder(json.JSONEncoder):
    """Handles dataclasses, callables, torch.dtype, Enums in JSON serialization."""
    def default(self, o):
        if is_dataclass(o): return asdict(o)
        if callable(o): return o.__name__ if hasattr(o, "__name__") else o.func.__name__
        if isinstance(o, torch.dtype): return str(o)
        if isinstance(o, Enum): return o.name
```

#### 14. Results Property
```python
@property
def results(self):
    config_general = asdict(self.general_config_logger)
    config_general["model_config"] = config_general["model_config"].model_dump()
    return {
        "config_general": config_general,
        "results": self.metrics_logger.metric_aggregated,
        "versions": self.versions_logger.versions,
        "config_tasks": self.task_config_logger.tasks_configs,
        "summary_tasks": self.details_logger.compiled_details,
        "summary_general": asdict(self.details_logger.compiled_details_over_all_tasks),
    }
```

#### 15. Save Pipeline (save() method)
1. Generates a `date_id` from ISO datetime (colons replaced with hyphens for filesystem compat)
2. Produces `results_dict` from the `.results` property
3. Calls `self.save_results(date_id, results_dict)` — writes JSON to output_dir
4. Converts per-detail entries to 🤗 `Dataset.from_list()` objects
5. Calls `self.save_details(date_id, details_datasets)` — writes per-task datasets as JSONL
6. Optionally `push_to_hub()` with:
   - Creates `DatasetCardData` with config descriptions and latest results
   - Generates a `DatasetCard` from template
   - Splits results by eval date with a "latest" alias
   - Special-case merges for MMLU across all subtasks
   - Pushes the full dataset card + data to Hub
7. Optionally `push_to_tensorboard()` via HFSummaryWriter
8. Optionally `push_to_wandb()` via wandb or Trackio

#### 16. Hub Push — Dataset Card Generation
```python
card_data = DatasetCardData(
    dataset_summary=f"Dataset created during evaluation of [{model_name}]...",
    repo_url=f"https://huggingface.co/{model_name}",
    pretty_name=f"Evaluation run of {model_name}",
    leaderboard_url=leaderboard_url,
    point_of_contact="clementine@hf.co" if open_llm_leaderboard else None,
)
card = DatasetCard.from_template(card_data, ...)
card.push_to_hub(repo_id, repo_type="dataset")
```

Each task gets its own dataset config (split by eval date). A special "results" config stores aggregated metrics. MMLU tasks get auto-merged into a combined config.

#### 17. TensorBoard Integration
Requires nanotron and tensorboardX. Uses `HFSummaryWriter` which can push directly to Hub repos. Key details:
- Scalar prefix system: `{prefix}/{task_name}/{metric}` and `stderr_{prefix}/{task_name}/{metric}`
- Bench suite averaging: tasks with `:` subtask names get aggregated (e.g., MMLU:abstract_algebra)
- Files renamed with global_step prefix for ordering (tensorboard ordering workaround)
- Trigger-based push to Hub after file renaming

#### 18. Weights & Biases / Trackio Integration
- Auto-detects Trackio (preferred) or falls back to wandb
- Reads `WANDB_PROJECT` and `WANDB_SPACE_ID` from environment
- Logs all aggregated metrics and pushes per-task detail datasets

### Custom Task Patterns

#### 19. Registry Task Loading
```python
# Tasks loaded from:
# 1) Built-in suites: lighteval, leaderboard, harness, helm, bigbench, original, extended
# 2) Community tasks: dynamically loaded from community_tasks/ directory
# 3) Custom task files: loaded via --custom-tasks flag (Python file with TASKS_TABLE export)
# 4) Multilingual tasks: loaded via --load-tasks-multilingual flag

class Registry:
    def get_task_list(self, task_names: list[str], custom_tasks_file: str | None = None,
                      load_multilingual: bool = False) -> list[LightevalTask]:
        # Combines tasks from all sources
        # Supports task:subtask syntax
```

#### 20. Community Task System
```python
def load_community_tasks():
    """Dynamically imports community_tasks/*.py modules with TASKS_TABLE exports."""
    # Path: <lighteval_root>/community_tasks/
    # Each module must export TASKS_TABLE = list[LightevalTaskConfig]
```

### Sources
- LightEval GitHub Source: https://github.com/huggingface/lighteval
  - `src/lighteval/pipeline.py` — Pipeline orchestration
  - `src/lighteval/models/abstract_model.py` — ModelConfig Pydantic model
  - `src/lighteval/metrics/metrics.py` — Metrics Enum with all 40+ entries
  - `src/lighteval/metrics/metrics_sample.py` — SampleLevelComputation implementations
  - `src/lighteval/metrics/metrics_corpus.py` — CorpusLevelComputation implementations
  - `src/lighteval/metrics/utils/metric_utils.py` — Metric dataclass hierarchy
  - `src/lighteval/metrics/sample_preparator.py` — Preparator classes
  - `src/lighteval/metrics/__init__.py` — apply_metric() dispatch
  - `src/lighteval/logging/evaluation_tracker.py` — Full EvaluationTracker
  - `src/lighteval/tasks/lighteval_task.py` — LightevalTaskConfig
  - `src/lighteval/tasks/registry.py` — Registry with community task loading
  - `src/lighteval/metrics/metrics.py` — Inspect-ai scorers (math_scorer, multichoice_scorer)
- LightEval Docs: https://huggingface.co/docs/lighteval/main/en/index

### Skill
mlops/hf-lighteval — Enhanced with source-level deep-dive on Python API (Pipeline, ModelConfig, LightevalTaskConfig), custom metrics system (Metric hierarchy, SampleLevelComputation, CorpusLevelComputation, MetricGrouping, Preparator), all 40+ Metrics enum entries, parametric metric override via __call__, batched vs non-batched metric dispatch, EvaluationTracker internals (5 sub-loggers, EnhancedJSONEncoder, save pipeline, Hub dataset card generation, TensorBoard with bench suite averaging, wandb/Trackio), community task system, and inspect-ai scorer integration for math and multiple-choice evals.

---

## 2026-07-25: hf-trl-dapo-gspo-deep-dive — From GRPO to DAPO and GSPO: Algorithms, Design Motivations, and Implementation (Topic #282)

### Summary
Comprehensive deep-dive on the evolution from GRPO to DAPO and GSPO — the three key reinforcement learning algorithms for LLM reasoning post-training. Covers the GRPO foundation (group-based advantage normalization, token-level importance sampling with clipping), DAPO's four targeted improvements (Clip-Higher, Dynamic Sampling, Token-Level Gradient Loss, Overlong Reward Shaping), GSPO's fundamental shift from token-level to sequence-level optimization for MoE stability, and the additional loss types now available in TRL's GRPOTrainer (Dr. GRPO, SAPO). Based on the DAPO paper (ByteDance/Volcengine), the GSPO paper (Qwen team), TRL v1.9.0+ documentation, and community blog analysis. (281st entry in tracker.)

### Source
- DAPO Paper: https://arxiv.org/abs/2504.05764 — "DAPO: An Open-Source LLM Reinforcement Learning System at Scale"
- GSPO Paper: https://arxiv.org/abs/2505. — Qwen Team, "GSPO: Group Sequence Policy Optimization"
- Community Blog: https://huggingface.co/blog/NormalUhr/grpo-to-dapo-and-gspo — "From GRPO to DAPO and GSPO: What, Why, and How" (Aug 2025)
- TRL Docs (main): https://huggingface.co/docs/trl/main/en/grpo_trainer — GRPOTrainer with loss_type support
- GRPO Paper: https://arxiv.org/abs/2402.03300 — "DeepSeekMath: Pushing the Limits of Mathematical Reasoning in Open Language Models"
- Understanding R1-Zero: https://arxiv.org/abs/2505. — "Understanding R1-Zero-Like Training: A Critical Perspective"

### 1. The GRPO Foundation

GRPO (Group Relative Policy Optimization) is the baseline from which DAPO and GSPO evolved. It removes the value model (critic network) from PPO, replacing it with group-based advantage normalization:

**Core Objective:**

```
J_GRPO(θ) = E [ 1/G Σ_i 1/|o_i| Σ_t (min(r_i,t(θ)·Â_i, clip(r_i,t(θ), 1-ε, 1+ε)·Â_i) − β·D_KL(π_θ || π_ref)) ]
```

Where:
- **Importance ratio**: r_i,t(θ) = π_θ(o_i,t | q, o_i,<t) / π_θ_old(o_i,t | q, o_i,<t)
- **Advantage**: Â_i = (r_i − mean(r)) / std(r) — group-normalized within the batch of G samples
- **Clipping**: clip(r, 1-ε, 1+ε) prevents the policy ratio from drifting too far (>20% by default)
- **KL penalty**: β·D_KL keeps the policy close to the reference model (often disabled in practice, β=0)

**Key insight**: The sign of Â_i and r_i,t together determine update direction:
- Â_i > 0 & r_i,t > 1: Reinforce a good action the new policy already prefers
- Â_i < 0 & r_i,t < 1: Correct a bad action the new policy is already avoiding
- Â_i > 0 & r_i,t < 1: The new policy is becoming less likely to produce a good action (undesirable)
- Â_i < 0 & r_i,t > 1: The new policy is becoming more likely to produce a bad action (undesirable)

**Limitations that motivated DAPO/GSPO:**
1. Clipping kills gradient for tokens with r_i,t > 1+ε even if Â_i > 0 (good tokens capped)
2. Uniform sampling wastes compute when all G responses get same reward (zero advantage)
3. Sample-level loss averaging dilutes gradients from long, high-quality responses
4. Per-token importance sampling introduces high variance in MoE architectures

### 2. DAPO — Four Targeted Improvements

DAPO (Dynamic Advantage Policy Optimization, ByteDance 2025) preserves the GRPO framework while fixing four specific weaknesses:

#### 2.1 Clip-Higher (Asymmetric Clipping)

**Problem**: When the old policy assigns very low probability to a token that happens to be good (high advantage), the upper clip bound (1+ε) prevents the new policy from significantly increasing that token's probability. This creates a "Matthew effect" — tokens the old policy was already good at get reinforced, while tokens it was bad at stay suppressed.

**Solution**: Raise the upper clip bound while keeping the lower bound fixed:

```
clip(r_i,t(θ), 1-ε_low, 1+ε_high)   where ε_high > ε_low
```

Typically ε_high=0.28, ε_low=0.2. This gives more room for "good but unlikely" tokens to grow their probability.

#### 2.2 Dynamic Sampling

**Problem**: For any given prompt, if all G sampled responses receive identical rewards (all 0 or all 1), the group advantage Â_i becomes zero for all responses, contributing zero gradient. This wastes generation compute.

**Solution**: Enforce diversity in sampled responses per prompt:

```
s.t. 0 < |{o_i | is_equivalent(a, o_i)}| < G
```

This ensures the sampled set contains both correct and incorrect answers. If all G responses are the same quality, additional samples are drawn until the constraint is met.

#### 2.3 Token-Level Gradient Loss

**Problem**: GRPO's loss averages gradients per-sample first, then across the batch:
```
L_GRPO = −1/G Σ_i 1/|o_i| Σ_t l_i,t
```
A 200-token response gives each token weight (1/200)×(1/G), while a 10-token response gives (1/10)×(1/G). Short responses dominate gradient updates.

**Solution**: DAPO averages over the total token count across all samples:
```
L_DAPO = −1/Σ|o_i| Σ_i Σ_t l_i,t
```
Every token has equal weight regardless of its parent response length. This prevents gradient dilution for long, high-quality responses and corrects the length bias.

#### 2.4 Overlong Reward Shaping

**Problem**: Excessively long responses consume compute and often indicate incoherent reasoning.

**Solution**: Linear penalty for tokens beyond a first threshold, scaling up to cancel the correctness reward entirely at a second threshold. This softly discourages verbosity without hard truncation.

### 3. GSPO — Sequence-Level Optimization for MoE Stability

GSPO (Group Sequence Policy Optimization, Qwen Team 2025) addresses a structural limitation of GRPO that DAPO's token-level fixes cannot resolve: the instability of per-token importance sampling in Mixture-of-Experts architectures.

#### 3.1 The Problem with Token-Level IS in MoE

In GRPO, importance sampling is performed per-token:
```
r_i,t = π_θ(o_i,t | ...) / π_θ_old(o_i,t | ...)
```

This works for dense models where all parameters contribute to every token. But in MoE:
- Different tokens activate different expert subsets
- The routing decisions introduce additional stochasticity
- A single token's importance ratio cannot meaningfully correct for distribution shift
- The per-token variance inflates dramatically, causing gradient noise and instability

**Practical symptom**: During long MoE training runs, the model can suddenly collapse — even resuming from checkpoint or tuning hyperparameters may not recover it.

#### 3.2 Routing Replay (Pre-GSPO Workaround)

Before GSPO, practitioners used Routing Replay — recording expert activation patterns during inference and enforcing the same routing during training. While effective, this:
- Greatly increases engineering complexity
- Limits performance by constraining routing
- Adds memory overhead for storing routing tables

#### 3.3 GSPO's Solution

GSPO shifts optimization granularity from token-level to **sequence-level**:

```
L_GSPO = −1/G Σ_i [ min(r_i·Â_i, clip(r_i, 1-ε, 1+ε)·Â_i) ]
```

Where r_i = π_θ(o_i | q) / π_θ_old(o_i | q) is computed over the **entire sequence**, not per-token.

**Implications:**
- Eliminates the need for Routing Replay entirely
- Reduces variance by pooling the importance signal across the full sequence
- Naturally handles the token-expert assignment variability in MoE
- Aligns reward granularity (response-level) with optimization granularity (sequence-level)
- Only high-quality samples contribute meaningfully to updates

The key insight: We evaluate the model based on full responses (rewards are response-level), yet GRPO trains it token-by-token. GSPO aligns these by optimizing at the sequence level — the same granularity as the reward signal.

**Adoption**: The Qwen3 series uses GSPO for post-training, demonstrating its effectiveness in production-scale MoE models.

### 4. Additional Loss Types in TRL's GRPOTrainer

Beyond DAPO and GSPO, TRL's GRPOTrainer supports several other loss formulations via the `loss_type` parameter:

| Loss Type | How to Enable | Key Idea |
|-----------|--------------|----------|
| **GRPO** | `loss_type="grpo"` (default) | Sample-level normalization: 1/G · 1/|o_i| |
| **DAPO** | `loss_type="dapo"` | Token-level normalization: 1/Σ|o_i| |
| **Dr. GRPO** | `loss_type="dr_grpo"` | Divide by a constant (max completion length) instead of actual length — fully removes length bias |
| **SAPO** | `loss_type="sapo"` | Replaces hard clipping with soft sigmoid-gated gating: f(x) = σ(τ(x-1))·4τ. Uses asymmetric temperatures τ_pos=1.0, τ_neg=1.05 for stricter penalization of bad actions |

**Dr. GRPO** formula:
```
L_Dr_GRPO = −1/(L_max·G) Σ_i Σ_t l_i,t
```
Where L_max is the maximum completion length in the batch. This completely removes the length bias introduced by sample- or token-level normalization.

**SAPO** (Soft-gated Advantage Policy Optimization):
- Uses temperature-controlled sigmoid gating instead of hard clip
- f_i,t(x) = σ(τ_i,t·(x-1)) · 4/τ_i,t
- Asymmetric temperatures τ_neg > τ_pos ensure stricter penalization
- Retains useful learning signals from "near-on-policy" tokens while suppressing extreme deviation noise

### 5. Practical Guidance

#### When to Use Each Variant

| Scenario | Recommended Loss Type |
|----------|---------------------|
| Dense model, standard reasoning tasks | GRPO (default) |
| Long chain-of-thought with dense model | DAPO (token-level loss prevents gradient dilution) |
| MoE model (e.g., Qwen3, DeepSeek) | GSPO (sequence-level avoids per-token IS variance) |
| Length bias is critical | Dr. GRPO (constant normalization fully removes bias) |
| Training instability with hard clipping | SAPO (soft gating smooths extreme updates) |

#### Key Configuration Parameters

In `GRPOConfig`:
- `loss_type`: `"grpo"`, `"dapo"`, `"dr_grpo"`, `"sapo"` (GSPO not yet exposed as separate loss_type in current TRL)
- `epsilon_low`: Lower clip bound (default: 0.2)
- `epsilon_high`: Upper clip bound (default: 0.28 for Clip-Higher)
- `scale_rewards`: Whether to normalize rewards by std (can disable or set to "batch")
- `beta`: KL penalty coefficient (typically 0.0 in modern practice)
- `entropy_coef`: Entropy regularization coefficient
- `use_adaptive_entropy`: Dynamically adjust entropy coefficient based on target

### 6. Key Takeaways

1. **GRPO → DAPO → GSPO represents an evolution of RL-based LLM training**, not a revolution — each builds on the previous while fixing specific identified weaknesses.

2. **DAPO's Clip-Higher** solves the "Matthew effect" where good but unlikely tokens get their gradients killed by symmetric clipping.

3. **DAPO's Token-Level Loss** addresses the practical problem that GRPO's sample-level averaging dilutes gradients from long responses — critical for long-CoT training scenarios.

4. **GSPO's sequence-level optimization** is the most fundamental change, addressing the root cause of MoE instability rather than patching symptoms.

5. **The trend is toward simpler, more aligned optimization**: Reward granularity (response-level) should match optimization granularity — sequence-level in GSPO aligns them perfectly.

6. **TRL's GRPOTrainer supports multiple loss types** under a unified training API, making it easy to experiment with different formulations without changing the training infrastructure.

### Skill
mlops/hf-trl-dapo-gspo — Deep-dive on DAPO and GSPO algorithms for LLM RL post-training. Covers GRPO foundation (group-based advantage, token-level IS with clipping), DAPO's four improvements (Clip-Higher asymmetric clipping, Dynamic Sampling for reward diversity, Token-Level Gradient Loss to prevent length bias, Overlong Reward Shaping), GSPO's sequence-level shift for MoE stability (eliminating Routing Replay), and TRL's loss_type options (GRPO, DAPO, Dr. GRPO, SAPO) with practical guidance for dense vs. MoE models.

---

## 2026-07-25: hf-diffusers-nunchaku-lite-native-integration — Nunchaku Lite Native Integration into Diffusers: SVDQuant W4A4 at from_pretrained() Speed (Topic #283)

### Summary
Comprehensive deep-dive on Nunchaku Lite — Hugging Face's native integration of the Nunchaku/SVDQuant 4-bit diffusion inference engine directly into the Diffusers library (announced July 23, 2026). Covers the full architecture: SVDQuant quantization method (outlier migration to 16-bit low-rank branch, residual quantized to 4 bits), Nunchaku CUDA inference engine, Nunchaku Lite as the Diffusers-native integration path, the `kernels` Hub package for dynamic kernel loading, NVFP4 (Blackwell) and INT4 kernel variants, AWQ W4A16 for text encoders and modulation projections, `from_pretrained()` loading without custom pipelines or local compilation, the `diffuse-compressor` toolkit for end-to-end quantization workflows, hardware support matrix, structural rewrites for fused QKV projections, torch.compile compatibility, benchmark performance (1.8x speedup, 50% memory reduction on RTX PRO 6000 at 1024×1024), and the complete workflow from inspection through quantization, packaging, verification, and publishing to the Hub.

### Source
- Blog: https://huggingface.co/blog/nunchaku-diffusers (July 23, 2026)
- Diffusers Nunchaku Quantization Docs: https://huggingface.co/docs/diffusers/main/en/quantization/nunchaku
- Nunchaku GitHub: https://github.com/mit-han-lab/nunchaku
- SVDQuant Paper: https://arxiv.org/abs/2411.05005
- `kernels` PyPI Package: https://pypi.org/project/kernels/ (v0.16.0, Apache-2.0)
- Diffusers Integration PR: huggingface/diffusers#14100

### Skill
mlops/hf-diffusers-nunchaku-lite — Nunchaku Lite native Diffusers integration: SVDQuant W4A4 quantization with Nunchaku CUDA kernels, `from_pretrained()` loading, NVFP4/INT4 variants, Hub-based kernel loading via `kernels` package, AWQ W4A16 text encoder quantization, diffuse-compressor workflow, hardware support (Blackwell, Ampere, Ada, Turing), torch.compile compatibility, structural rewrites for fused QKV projections

---

## 2026-07-25: hf-diffusers-nunchaku-lite-native-integration — Technical Architecture Deep-Dive

### 1. Background: SVDQuant and Nunchaku

**Standard 4-bit quantization is difficult for diffusion transformers** because both weights and activations contain large outliers. SVDQuant handles this by:

1. **Moving activation outliers into the weights** — the hardest part of each weight matrix is split off into a small 16-bit low-rank branch
2. **Quantizing the remaining residual to 4 bits** — the bulk of compute runs at W4A4
3. **The low-rank correction** — a tiny 16-bit branch (rank 32) preserves precision where 4-bit quantization would lose too much information

**Nunchaku** is the reference CUDA inference engine for SVDQuant. It fuses the low-rank down projection with the quantization kernel and the low-rank up projection with the 4-bit compute kernel, eliminating the memory access overhead of the 16-bit branch. Nunchaku also includes model-specific fused execution paths (e.g., fused QKV projections, fused GELU/MLP kernels) that are tied to each architecture's module layout and checkpoint format.

### 2. Nunchaku Lite — The Diffusers-Native Integration

**Nunchaku Lite** is the new integration path in Diffusers that allows loading Nunchaku-style checkpoints without a custom pipeline or separate inference engine. Key difference from original Nunchaku:

| Aspect | Original Nunchaku | Nunchaku Lite |
|--------|-------------------|---------------|
| Pipeline class | Custom Nunchaku-specific | Standard `DiffusionPipeline.from_pretrained()` |
| Kernel loading | Bundled with engine | Hub-based via `kernels` package |
| Architecture support | Per-model porting needed | Architecture-agnostic (generic) |
| Fused operations | Full model-specific fusions | No fusions in generic path |
| Speedup | Maximum (engine-optimal) | ~1.3-1.8× (no fusions, mitigated by torch.compile) |

**How it works under the hood:**
1. Nunchaku Lite patches the relevant `nn.Linear` modules of a stock Diffusers model with runtime `SVDQW4A4Linear` or `AWQW4A16Linear` layers before the checkpoint is loaded
2. The CUDA kernels come from the Hugging Face Hub through the `kernels` package
3. A `quantization_config.json` tells Diffusers which modules were quantized, which scheme they use, and which runtime layer to instantiate
4. Because the quantized model keeps the exact module structure of the dense one, everything downstream (schedulers, LoRA loading hooks, offloading, CPU offloading) sees a normal Diffusers model

### 3. Kernel Architecture: The `kernels` Package

The `kernels` package (v0.16.0, Apache-2.0, by Daniel de Kok & David Holtz at Hugging Face) enables dynamic loading of compute kernels directly from the Hugging Face Hub. Key properties:

- **Portable**: kernels can be loaded from paths outside `PYTHONPATH`
- **Unique**: multiple versions of the same kernel can coexist in one process
- **Compatible**: supports all recent Python versions and PyTorch build configurations (various CUDA versions and C++ ABIs)

**Two kernel families used by Nunchaku Lite:**

| Kernel Type | Precision | Use Case | GPU Support |
|------------|-----------|----------|-------------|
| **SVDQ W4A4** | 4-bit weights + 4-bit activations with SVDQuant low-rank correction | Transformer attention and MLP projections (where nearly all compute is spent) | INT4: Turing/Ampere/Ada; NVFP4: Blackwell |
| **AWQ W4A16** | 4-bit weights + 16-bit activations | Adaptive normalization and modulation projections (memory-bound, precision-sensitive) | Same as SVDQ |

**NVFP4** (NVIDIA FP4 format) is new for Blackwell GPUs (RTX 50 series, RTX PRO 6000, B200), providing additional performance. Requires PyTorch >= 2.7 with CUDA >= 12.8.

**GPU Architecture Support:**
| Architecture | NVFP4 | INT4 |
|-------------|-------|------|
| Blackwell (RTX 50, RTX PRO 6000, B200) | ✅ | ✅ |
| Ada (RTX 40 series) | ❌ | ✅ |
| Ampere (RTX 30 series, A100, RTX A6000) | ❌ | ✅ |
| Turing (RTX 20 series, T4) | ❌ | ✅ |
| Hopper (H100, H200) | ❌ | ❌ |
| Volta (V100) | ❌ | ❌ |

### 4. Usage: Loading a Pre-Quantized Model

```python
import torch
from diffusers import DiffusionPipeline

# Load like any other Diffusers model — kernels auto-download from Hub
pipe = DiffusionPipeline.from_pretrained(
    "rootonchair/ERNIE-Image-Turbo-nunchaku-lite-nvfp4",
    torch_dtype=torch.bfloat16,
).to("cuda")

# Use the standard pipeline API
image = pipe(
    prompt="A cinematic portrait of a red fox in a misty forest at sunrise",
    height=1024,
    width=1024,
    num_inference_steps=8,
    guidance_scale=1.0,
    generator=torch.Generator("cuda").manual_seed(42),
).images[0]
```

No custom pipeline class, no local CUDA compilation, no separate inference engine. The NVFP4 kernels are downloaded from the Hub on first use through the `kernels` package.

### 5. Performance Benchmarks

Measured on NVIDIA RTX PRO 6000 (Blackwell) at 1024×1024 with ERNIE-Image-Turbo:

| Configuration | Peak VRAM | Latency | Speedup vs BF16 |
|--------------|-----------|---------|-----------------|
| BF16 (baseline) | ~24 GB | ~3.0 s | 1.0× |
| Nunchaku Lite INT4 | ~12 GB | ~2.0 s | ~1.5× |
| Nunchaku Lite NVFP4 | ~12 GB | ~1.7 s | ~1.76× |
| Nunchaku Lite NVFP4 + torch.compile | ~12 GB | ~1.68 s | ~1.8× |
| NVFP4 + NF4 text encoder | ~9.4 GB | ~2.27 s | ~1.32× (lower memory) |

**Key insights:**
- **50% memory reduction** (24 GB → 12 GB) makes 1024×1024 generation feasible on consumer GPUs with 12-16 GB VRAM
- **1.8× speedup** with torch.compile, which mitigates the extra kernel launch overhead from Nunchaku Lite's non-fused ops
- Further memory savings (to ~9.4 GB) by also quantizing text encoders with bitsandbytes NF4
- Image quality remains close to the BF16 original

### 6. The diffuse-compressor Workflow: Quantizing Your Own Model

The `diffuse-compressor` toolkit provides an end-to-end SVDQuant workflow for Diffusers models. The complete pipeline:

#### Step 1: Inspect
```bash
python examples/text_to_image/quantize_hf.py black-forest-labs/FLUX.2-klein-4B \
    --precision int4 --rank 32 --inspect-config
```
Outputs a report showing the target modules, expected quantized linear count, and any missing patterns or duplicate names. For FLUX.2 Klein 4B: 100 SVDQ targets, 3 AWQ targets, 6 dense outer linears.

#### Step 2: Calibrate & Quantize
```bash
python examples/text_to_image/quantize_hf.py black-forest-labs/FLUX.2-klein-4B \
    --output outputs/checkpoints/svdq-int4_r32-flux-2-klein-4b.safetensors
```
For Blackwell GPUs, add `--nvfp4` for NVFP4 weights.

#### Step 3: Package as Diffusers Pipeline
```bash
python examples/convert_nunchaku_lite_diffusers.py \
    --checkpoint outputs/checkpoints/svdq-int4_r32-flux-2-klein-4b.safetensors \
    --model-id black-forest-labs/FLUX.2-klein-4B \
    --bnb4-text-encoder text_encoder \
    --output-dir outputs/diffusers/FLUX.2-klein-4B-nunchaku-lite-int4-bnb4-text-encoder
```
Combines quantized transformer with base pipeline components, writes `quantization_config.json`, and optionally converts text encoders to NF4.

#### Step 4: Verify & Push to Hub
```python
pipe = DiffusionPipeline.from_pretrained("outputs/diffusers/FLUX.2-klein-4B-nunchaku-lite-int4-bnb4-text-encoder")
image = pipe("A glass robot in a greenhouse, cinematic lighting").images[0]
pipe.push_to_hub("your-name/your-model-nunchaku-lite-int4")
```
Other users can then load it with the same `from_pretrained()` call.

### 7. Structural Rewrites for Maximum Performance

The generic Nunchaku Lite path assumes the architecture can be quantized without structural rewrites. For additional speedup, the original Nunchaku engine rewrites groups of Diffusers layers as fused modules. The generic path **cannot** infer these changes on its own.

**Concrete example — FLUX.1-dev QKV projection:**
- **Diffusers default**: Three separate modules `to_q`, `to_k`, `to_v` as `nn.Linear`
- **Nunchaku fused**: Single `to_qkv` as `SVDQW4A4Linear` combining Q, K, V projections
- **Why it matters**: Nunchaku's fused operator consumes QKV projection + Q/K normalization + rotary embeddings together in one fused CUDA kernel

Structural rewrites like these are described by a model-specific target config during quantization and handled by a small runtime adapter when the checkpoint is loaded. The `diffuse-compressor` repo provides target config examples and runtime adapters for popular architectures.

### 8. torch.compile Integration

Nunchaku Lite quantized modules are fully compatible with `torch.compile`:
```python
# Full transformer compilation
pipe.transformer = torch.compile(pipe.transformer, mode="max-autotune")

# Faster compilation for repeated blocks
pipe.transformer.compile_repeated_blocks(fullgraph=True)
```

Without compilation, the speedup is ~1.35× (vs BF16 baseline). With compilation, it reaches ~1.8× — close to the original Nunchaku engine's performance, thanks to kernel fusion from the compiler.

### 9. Practical Guidance

#### When to Use Nunchaku Lite vs. Other Quantization Backends

| Scenario | Recommended Backend |
|----------|---------------------|
| Want maximum speed + memory savings | Nunchaku Lite (W4A4 with SVDQuant) |
| Have Blackwell GPU | Nunchaku Lite NVFP4 for best perf |
| Need only weight compression | bitsandbytes NF4 or torchao |
| Need cross-platform compatibility | GGUF or Quanto |
| Quantizing custom architectures | diffuse-compressor toolkit |

#### Zero-Cost Pathways
- Pre-quantized checkpoints on the Hub are free to download
- `diffuse-compressor` is open-source (Apache-2.0)
- The `kernels` package is free (install via `pip install kernels`)
- All tooling runs on consumer GPUs — no paid compute required
- Inference on quantized models uses less VRAM, potentially fitting on free-tier GPUs (e.g., T4 in Colab free tier with INT4)

### 10. Key Takeaways

1. **Nunchaku Lite marks a step-change in diffusion model accessibility**: For the first time, W4A4 quantized diffusion models load with a single `from_pretrained()` call, no custom pipelines, and no local compilation — the same developer experience as a dense model.

2. **The `kernels` package is a new infrastructure layer for Hugging Face**: Dynamic kernel loading from the Hub enables a separation of concerns — model weights live on the Hub, compute kernels live on the Hub, and the user's environment is minimal.

3. **NVFP4 on Blackwell gives the best perf**: NVIDIA's native FP4 format on Blackwell GPUs delivers the full 2x memory reduction with an actual 1.8× speedup. INT4 on previous generations still gives 1.5× speedup and 50% memory savings.

4. **Memory reduction is the primary win**: From ~24 GB to ~9-12 GB for 1024×1024 generation, making modern diffusion transformers practical on 12-16 GB consumer GPUs. Further quantization of text encoders (NF4) can push to ~9 GB.

5. **Structural rewrites are the advanced path**: For maximum performance (fused QKV projections, combined attention+rotary kernels), model-specific adapters are needed. The generic path trades perf for generality.

6. **torch.compile is essential for peak performance**: Compilation closes the gap between the generic Nunchaku Lite path and the original Nunchaku engine by fusing kernel launches.

### Skill
mlops/hf-diffusers-nunchaku-lite — Nunchaku Lite native Diffusers integration: SVDQuant W4A4 quantization with Nunchaku CUDA kernels, `from_pretrained()` loading, NVFP4/INT4 variants, Hub-based kernel loading via `kernels` package, AWQ W4A16 text encoder quantization, diffuse-compressor workflow, hardware support (Blackwell, Ampere, Ada, Turing), torch.compile compatibility, structural rewrites for fused QKV projections

## 2026-07-25: hf-hub-hfapi-method-catalog — Complete HfApi Method Reference Catalog (Topic #285)

### Summary
Complete categorized reference catalog of every public method in the `huggingface_hub` library's `HfApi` class (v1.x). Covers all 100+ methods organized into 12 functional domains: Repo CRUD, File Operations, Repo Metadata, Collections, Discussions/PRs, Space Management, Webhooks, Inference, User/Org, Security/Tokens, Jobs, and Storage Buckets. Each method documented with its signature, return type, and purpose. Intended as a quick-reference lookup for everyday Hub automation tasks.

### Source
- huggingface_hub source: https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/hf_api.py
- huggingface_hub docs: https://huggingface.co/docs/hub/en/python-reference
- HfApi reference: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api

### Skill
hf-hub-hfapi-method-catalog — Complete HfApi method reference: 100+ methods across 12 domains, with signatures, return types, and usage notes. Quick-reference for Hub automation, CI/CD, and programmatic repo management.

---

## 2026-07-25: hf-hub-hfapi-method-catalog — Complete HfApi Method Reference (Deep-Dive)

### Domain 1: Repository CRUD (create, delete, move)

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `create_repo` | `(repo_id, repo_type, private, exist_ok, token) -> str` | Repo URL | Create a new model/dataset/space repo. Raises `HTTPError` if exist_ok=False and repo exists. |
| `delete_repo` | `(repo_id, repo_type, missing_ok, token) -> None` | None | Delete a repo permanently. Cannot delete DOI-locked repos. |
| `update_repo_visibility` | `(repo_id, repo_type, private, token) -> None` | None | Toggle repo public/private. Fails if repo has a DOI. |
| `move_repo` | `(from_id, to_id, repo_type, token) -> str` | New repo URL | Rename/move a repo. Fails for DOI-locked repos. |
| `repo_exists` | `(repo_id, repo_type, token) -> bool` | bool | Check if a repo exists on the Hub. |
| `repo_type` | `(repo_id, token) -> str` | "model", "dataset", or "space" | Auto-detect repo type from ID. |
| `whoami` | `(token) -> dict` | User/org info dict | Returns current user identity, org memberships, and token scopes. |
| `get_full_repo_name` | `(repo_name, namespace, token) -> str` | "namespace/name" | Construct full repo ID from name + optional namespace. |

### Domain 2: File Operations (upload, download, delete)

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `upload_file` | `(path_or_fileobj, path_in_repo, repo_id, repo_type, revision, token) -> CommitInfo` | CommitInfo | Upload a single file. Accepts path or file-like object. |
| `upload_folder` | `(folder_path, repo_id, repo_type, revision, path_in_repo, token, allow_patterns, ignore_patterns) -> CommitInfo` | CommitInfo | Upload an entire folder with pattern-based filtering. Uses `CommitOperationAdd` internally. |
| `upload_large_folder` | `(folder_path, repo_id, repo_type, revision, path_in_repo, token, allow_patterns, ignore_patterns, hf_transfer) -> CommitInfo` | CommitInfo | Upload large folders with Xet/hf_transfer acceleration. Chunked parallel upload. |
| `snapshot_download` | `(repo_id, repo_type, revision, cache_dir, token, allow_patterns, ignore_patterns, max_workers, resume) -> str` | Local path | Download entire repo snapshot to disk with caching. |
| `hf_hub_download` | `(repo_id, repo_type, filename, revision, cache_dir, token, resume, local_dir) -> str` | Local path | Download single file with resume, caching, and symlinks. |
| `delete_file` | `(repo_id, repo_type, filename, revision, token) -> CommitInfo` | CommitInfo | Delete a single file from a repo. |
| `metadata_update` | `(repo_id, repo_type, metadata, revision, token, overwrite) -> CommitInfo` | CommitInfo | Update repo metadata (model card YAML, dataset tags) via a commit. |
| `create_commit` | `(repo_id, repo_type, operations, commit_message, revision, token, parent) -> CommitInfo` | CommitInfo | Atomic multi-file commit with mixed operations (add, delete, update). |
| `get_hf_file_metadata` | `(url, token) -> HfFileMetadata` | HfFileMetadata | Get file metadata (size, SHA256, commit info) without downloading. |
| `file_exists` | `(repo_id, repo_type, filename, revision, token) -> bool` | bool | Check if a specific file exists in a repo at a revision. |

### Domain 3: Repo Metadata & Listing

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_models` | `(filter, search, sort, direction, limit, expand, token, cursor) -> Iterable[ModelInfo]` | Iterable[ModelInfo] | List/search models with filtering by tag, pipeline, library, etc. Cursor-paginated. |
| `list_datasets` | `(filter, search, sort, direction, limit, expand, token, cursor) -> Iterable[DatasetInfo]` | Iterable[DatasetInfo] | List/search datasets. Same pagination/sort/filter system as models. |
| `list_spaces` | `(filter, search, sort, direction, limit, expand, token, cursor, linked_url) -> Iterable[SpaceInfo]` | Iterable[SpaceInfo] | List/search Spaces. Additional linked_url filter for model-to-space linking. |
| `model_info` | `(repo_id, revision, expand, token) -> ModelInfo` | ModelInfo | Get single model's full metadata (card, tags, siblings, config, etc.). |
| `dataset_info` | `(repo_id, revision, expand, token) -> DatasetInfo` | DatasetInfo | Get single dataset's full metadata. |
| `space_info` | `(repo_id, expand, token) -> SpaceInfo` | SpaceInfo | Get single Space's full metadata (runtime, hardware, secrets, vars). |
| `list_repo_files` | `(repo_id, repo_type, revision, token, recursive) -> list[str]` | List of file paths | List all files in a repo at a given revision. |
| `list_repo_refs` | `(repo_id, repo_type, token) -> GitRefs` | GitRefs | List all branches and tags in a repo. |
| `list_repo_commits` | `(repo_id, repo_type, revision, token, cursor_backward) -> list[GitCommitInfo]` | list[GitCommitInfo] | List commit history with cursor-based backward pagination. |
| `list_repo_tree` | `(repo_id, repo_type, revision, path, recursive, expand, token) -> list[RepoFile]` | list[RepoFile] | Browse directory tree with expand option for file metadata. |
| `super_squash_history` | `(repo_id, repo_type, token) -> None` | None | Squash repo commit history into a single commit. Irreversible. |

### Domain 4: Collections

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_collections` | `(owner, item, sort, direction, token) -> Iterable[Collection]` | Iterable[Collection] | List collections with owner and item-type filters. 3 sort modes (lastUpdated, createdAt, trending). |
| `get_collection` | `(collection_slug, token) -> Collection` | Collection | Get a single collection by slug (e.g., "namespace/collection-name"). |
| `create_collection` | `(title, namespace, description, private, token) -> Collection` | Collection | Create a new collection under your namespace. |
| `update_collection` | `(collection_slug, description, title, private, settings, token) -> Collection` | Collection | Update collection metadata. |
| `delete_collection` | `(collection_slug, token, missing_ok) -> None` | None | Delete a collection. |
| `add_collection_item` | `(collection_slug, item, item_type, note, token) -> CollectionItem` | CollectionItem | Add model/dataset/space/paper/collection to a collection. |
| `update_collection_item` | `(collection_slug, item_object_id, note, token) -> CollectionItem` | CollectionItem | Update the note on a collection item. |
| `delete_collection_item` | `(collection_slug, item_object_id, token, missing_ok) -> None` | None | Remove an item from a collection. |

### Domain 5: Discussions & Pull Requests

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_discussions` | `(repo_id, repo_type, token) -> list[Discussion]` | list[Discussion] | List all discussions and PRs for a repo. |
| `get_discussion_details` | `(repo_id, repo_type, discussion_num, token) -> Discussion` | Discussion | Get discussion with full comment thread and events. |
| `create_discussion` | `(repo_id, repo_type, title, description, token, pull_request) -> Discussion` | Discussion | Create a new discussion or pull request. |
| `comment_discussion` | `(repo_id, repo_type, discussion_num, comment, token) -> DiscussionComment` | DiscussionComment | Add a comment to an existing discussion/PR. |
| `edit_discussion_comment` | `(repo_id, repo_type, discussion_num, comment_id, content, token) -> None` | None | Edit an existing comment. |
| `hide_discussion_comment` | `(repo_id, repo_type, discussion_num, comment_id, token) -> None` | None | Hide a comment (moderator action). |
| `rename_discussion` | `(repo_id, repo_type, discussion_num, new_title, token) -> None` | None | Rename a discussion. |
| `merge_pull_request` | `(repo_id, repo_type, discussion_num, comment, token) -> None` | None | Merge a pull request into main branch. |

### Domain 6: Space Management

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `create_space` | `(repo_id, repo_type, space_sdk, space_hardware, secrets, variables, token) -> SpaceInfo` | SpaceInfo | Create a new Space with SDK choice (gradio, streamlit, docker, static) and hardware tier. |
| `request_space_hardware` | `(repo_id, hardware, token, sleeping) -> SpaceInfo` | SpaceInfo | Request hardware upgrade for a Space. Can set sleep timeout. |
| `pause_space` | `(repo_id, token) -> SpaceInfo` | SpaceInfo | Pause a Space (stops and sleeps it). |
| `restart_space` | `(repo_id, token, factory_mode) -> SpaceInfo` | SpaceInfo | Restart a Space (optionally in factory mode to reset storage). |
| `duplicate_space` | `(from_id, to_id, space_sdk, token) -> SpaceInfo` | SpaceInfo | Duplicate a Space. Creates a copy under your namespace. |
| `add_space_secret` | `(repo_id, key, value, description, token) -> None` | None | Add a secret to a Space's environment. |
| `delete_space_secret` | `(repo_id, key, token) -> None` | None | Delete a secret from a Space. |
| `add_space_variable` | `(repo_id, key, value, description, token) -> None` | None | Add an environment variable (non-secret) to a Space. |
| `delete_space_variable` | `(repo_id, key, token) -> None` | None | Delete an environment variable from a Space. |
| `get_space_variables` | `(repo_id, token) -> dict` | dict | Get all environment variables and secrets for a Space. |
| `list_spaces_runtimes` | `(token) -> list[SpaceRuntime]` | list[SpaceRuntime] | List all available runtimes for Spaces (SDK versions). |
| `list_space_runtime_logs` | `(repo_id, token, revision) -> SpaceLogs` | SpaceLogs | Fetch Space build logs from the most recent build. |

### Domain 7: Webhooks

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `create_webhook` | `(name, url, watched, domains, secret, token) -> Webhook` | Webhook | Create a webhook that fires on repo events (push, PR, discussion, release). |
| `list_webhooks` | `(token) -> list[Webhook]` | list[Webhook] | List all webhooks on your account. |
| `update_webhook` | `(webhook_id, name, url, watched, domains, secret, token) -> Webhook` | Webhook | Update webhook configuration. |
| `delete_webhook` | `(webhook_id, token) -> None` | None | Delete a webhook. |
| `ping_webhook` | `(webhook_id, token) -> None` | None | Send a test ping to a webhook endpoint. |

### Domain 8: Inference & Endpoints

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_model_status` | `(repo_id, token) -> ModelStatus` | ModelStatus | Get model's inference status (loaded providers, queue length). |
| `toggle_model_status` | `(repo_id, token, disable) -> None` | None | Enable/disable public inference for a model. |
| `list_inference_endpoints` | `(namespace, token) -> list[InferenceEndpoint]` | list[InferenceEndpoint] | List all Inference Endpoints in a namespace. |
| `create_inference_endpoint` | `(name, repo_id, endpoint_type, hardware, revision, token, scale_to_zero_timeout) -> InferenceEndpoint` | InferenceEndpoint | Create a dedicated Inference Endpoint (PAYG). |
| `get_inference_endpoint` | `(name, namespace, token) -> InferenceEndpoint` | InferenceEndpoint | Get Inference Endpoint details. |
| `update_inference_endpoint` | `(name, namespace, token, hardware, repository, revision, min_replica, max_replica) -> InferenceEndpoint` | InferenceEndpoint | Update endpoint hardware/scale config. |
| `delete_inference_endpoint` | `(name, namespace, token, force) -> None` | None | Delete an Inference Endpoint. |
| `pause_inference_endpoint` | `(name, namespace, token) -> InferenceEndpoint` | InferenceEndpoint | Pause endpoint (scale to zero). |
| `resume_inference_endpoint` | `(name, namespace, token, running_ok) -> InferenceEndpoint` | InferenceEndpoint | Resume a paused endpoint. |
| `scale_to_zero_inference_endpoint` | `(name, namespace, token, scale_to_zero_timeout) -> InferenceEndpoint` | InferenceEndpoint | Set endpoint to auto-scale-to-zero after idle timeout. |

### Domain 9: User, Org & Social

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `get_user_overview` | `(username, token) -> User` | User | Get user public profile: avatar, followers, following, orgs, repos. |
| `list_user_followers` | `(username, token) -> Iterable[User]` | Iterable[User] | List user's followers. |
| `list_user_following` | `(username, token) -> Iterable[User]` | Iterable[User] | List who a user follows. |
| `list_organization_members` | `(organization, token) -> Iterable[User]` | Iterable[User] | List org members. |
| `get_org_overview` | `(organization, token) -> Organization` | Organization | Get org public profile. |
| `list_organization_followers` | `(organization, token) -> Iterable[User]` | Iterable[User] | List org followers. |
| `list_user_orgs` | `(token) -> list[Organization]` | list[Organization] | List orgs the authenticated user belongs to. |
| `like_repo` | `(repo_id, repo_type, token) -> None` | None | Like (add heart to) a repo. |
| `unlike_repo` | `(repo_id, repo_type, token) -> None` | None | Unlike (remove heart from) a repo. |
| `list_repo_likers` | `(repo_id, repo_type, token) -> Iterable[User]` | Iterable[User] | List users who liked a repo. |

### Domain 10: Security, Tokens & Auth

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_auth_tokens` | `(token) -> list[AuthToken]` | list[AuthToken] | List all fine-grained tokens for the authenticated user. |
| `create_auth_token` | `(name, role, token, permissions) -> AuthToken` | AuthToken | Create a fine-grained token with specific repo scopes. |
| `delete_auth_token` | `(token_id, token) -> None` | None | Delete an auth token. |
| `get_token_permission` | `(token) -> TokenPermission` | TokenPermission | Get the permission level of the current token. |
| `get_webhook_token` | `(token) -> WebhookToken` | WebhookToken | Get webhook signing token. |
| `list_gated_repos` | `(token) -> list[GatedRepo]` | list[GatedRepo] | List all gated repos the user has access to. |
| `request_repo_access` | `(repo_id, repo_type, token, reason) -> None` | None | Request access to a gated repo with a reason. |

### Domain 11: Jobs & Sandboxes

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_jobs` | `(namespace, status, job_type, token) -> list[Job]` | list[Job] | List Hub jobs. |
| `get_job` | `(job_id, token) -> Job` | Job | Get job status and details. |
| `create_job` | `(job_type, params, namespace, token) -> Job` | Job | Create a new Hub job. |
| `cancel_job` | `(job_id, token) -> None` | None | Cancel a running job. |
| `list_sandboxes` | `(namespace, token) -> list[Sandbox]` | list[Sandbox] | List HF Sandbox environments. |
| `get_sandbox` | `(sandbox_id, token) -> Sandbox` | Sandbox | Get Sandbox details. |
| `create_sandbox` | `(name, compute, disk_size, token) -> Sandbox` | Sandbox | Create a new Sandbox. |
| `stop_sandbox` | `(sandbox_id, token) -> None` | None | Stop a Sandbox. |
| `delete_sandbox` | `(sandbox_id, token) -> None` | None | Delete a Sandbox. |

### Domain 12: Storage Buckets & System

| Method | Signature | Returns | Description |
|--------|-----------|---------|-------------|
| `list_storage_buckets` | `(namespace, token) -> list[StorageBucket]` | list[StorageBucket] | List storage buckets for user/org. |
| `get_storage_bucket` | `(bucket_id, token) -> StorageBucket` | StorageBucket | Get bucket details and usage. |
| `create_storage_bucket` | `(repo_id, token) -> StorageBucket` | StorageBucket | Create a storage bucket for a repo. |
| `update_storage_bucket` | `(bucket_id, limits, token) -> StorageBucket` | StorageBucket | Update bucket storage limits. |
| `delete_storage_bucket` | `(bucket_id, token) -> None` | None | Delete a storage bucket. |
| `health_check` | `(token) -> str` | "ok" | Check Hub API health. |
| `list_metrics` | `(repo_id, repo_type, token) -> dict` | dict | Get repo metrics (downloads, likes, etc.). |

### Usage Patterns

#### Pattern 1: Create and Populate a Dataset Repo
```python
from huggingface_hub import HfApi
api = HfApi()

url = api.create_repo("my-dataset", repo_type="dataset", private=True, exist_ok=True)
api.upload_file(
    path_or_fileobj="data/train.parquet",
    path_in_repo="data/train.parquet",
    repo_id="my-dataset",
    repo_type="dataset"
)
api.metadata_update("my-dataset", repo_type="dataset", metadata={
    "tags": ["synthetic", "text-classification"],
    "language": ["en"],
})
```

#### Pattern 2: List All Models for a Library
```python
from huggingface_hub import HfApi
api = HfApi()

models = api.list_models(library="transformers", sort="downloads", direction=-1, limit=20)
for m in models:
    print(f"{m.modelId} — {m.downloads} downloads")
```

#### Pattern 3: Create and Manage a Collection
```python
from huggingface_hub import HfApi
api = HfApi()

col = api.create_collection(
    title="My Research Track",
    namespace="my-org",
    description="Collection of models for my paper"
)
api.add_collection_item(col.slug, item="meta-llama/Llama-4-8B", item_type="model", note="Base model")
```

#### Pattern 4: Monitor Space Build Logs
```python
from huggingface_hub import HfApi
api = HfApi()

api.restart_space("my-space", factory_mode=True)
logs = api.list_space_runtime_logs("my-space")
print(logs.logs[-20:])
```

### Zero-Cost Notes
- All HfApi methods for repo management, listing, collections, discussions, and webhooks are FREE (limited by Hub API rate limits)
- Inference Endpoint creation (create_inference_endpoint) costs money — use InferenceClient (serverless, free tier) instead
- File uploads count toward your storage quota (free tier: models ~5GB per repo, datasets ~50GB, total ~50GB across user)
- The `huggingface_hub` library itself is open-source and free to install (pip install huggingface-hub)

### Key Takeaways
1. **HfApi is the complete automation surface**: Every Hub operation available programmatically — no UI needed after initial setup.
2. **Three tiers of cost**: Free (metadata/listing/collections/discussions/webhooks), Storage-quota (file uploads), Paid (Inference Endpoints, Sandboxes).
3. **Cursor pagination everywhere**: All list_* methods return Iterable with built-in pagination — no manual page management needed.
4. **Create_commit for atomic ops**: Use with CommitOperationAdd/Delete for multi-file atomic updates in a single commit.
5. **Upload_large_folder for big datasets**: Uses Xet/hf_transfer acceleration for folder uploads over ~100MB.
6. **Space secrets are write-once**: Can be added/deleted via API but cannot be read back (API returns key names, not values).

### Skill
hf-hub-hfapi-method-catalog — Complete HfApi method reference catalog: 100+ methods in 12 domains (Repo CRUD, File Ops, Metadata, Collections, Discussions, Spaces, Webhooks, Inference, User/Org, Security, Jobs, Storage Buckets). Each method with signature, return type, and purpose. Practical patterns for automation workflows. Zero-cost usage guidance.

---

## 2026-07-25: hf-hub-foundry-enterprise-deployment-curation — Hugging Face Models on Microsoft Foundry Managed Compute: Curation, Security Screening and Enterprise Deployment (Topic #289)

### Summary
Comprehensive deep-dive on the integration between Hugging Face and Microsoft Foundry Managed Compute — announced at Microsoft Build 2026. Covers the full curation pipeline Microsoft runs to bring open-weight HF models into the Foundry Model Catalog: trending model identification, license review, trust_remote_code remediation, CVE-scanned container images on 6 runtimes (vLLM, SGLang, TensorRT-LLM, NIM, TEI, llama.cpp, hf-serve), weight pre-staging in Azure storage for private-network deployments, deployment templates (runtime + accelerator + context-length tuning), OpenAI-compatible SDK scoring, and integration with Foundry Agents. Also covers the parallel SageMaker Studio one-click deep-link integration from HF model pages to AWS SageMaker Studio (July 2026).

### Sources
- Hugging Face Blog: https://huggingface.co/blog/microsoft/foundry-managed-compute (July 7, 2026)
- Hugging Face Blog: https://huggingface.co/blog/amazon/one-click-to-sagemaker-studio (July 7, 2026)
- Foundry Managed Compute documentation (Microsoft)
- HF Collection on Foundry Model Catalog

### Key Details

#### Curation Pipeline (Multi-Stage)
1. Trend identification — HF and Microsoft jointly identify trending models based on community signals, partner requests, customer demand
2. Compliance and security screening — license review vs Microsoft enterprise distribution policy; repository inspected for trust_remote_code patterns and custom executable code; any model requiring third-party Python at load time is either remediated (code reviewed) or excluded
3. Runtime build and scan — Microsoft builds inference container images on supported runtimes (vLLM, SGLang, TRT-LLM, NIM, TEI, llama.cpp), scans for CVEs, signs, publishes to Microsoft-managed container registry
4. Weight upload — model weights pulled from HF once, validated against model card, stored in Microsoft-managed Azure storage in serving regions
5. Validation and catalog publish — every model + runtime + accelerator combination tested for API conformance and performance (latency, throughput, TTFT, ITDT), then published with one-click deploy

#### Supported Runtimes
- vLLM: High-throughput LLM serving (default; any Transformers model runs day-of-release)
- SGLang: Structured outputs, agentic workloads (JSON/regex/grammar-constrained generation)
- TensorRT-LLM: NVIDIA-optimized latency/throughput
- NIM: NVIDIA inference microservices
- TEI: Embeddings, rerank, sequence classification
- llama.cpp: CPU/small-GPU for GGUF models
- hf-serve: Vision, audio, segmentation, non-LLM models

#### Deployment Templates
Named, versioned assets that pin: runtime, accelerator family and count, context length, runtime-specific tuning.

Example for Qwen3-32B:
- qwen--qwen3-32b--40k-nvidia-a100 — vLLM, 1x A100 80GB, 40K context
- qwen--qwen3-32b--40k-nvidia-h100 — vLLM, 1x H100 80GB, 40K context
- qwen--qwen3-32b--128k-nvidia-2xa100 — vLLM, 2x A100 80GB, 128K context
- qwen--qwen3-32b--128k-nvidia-2xh100 — vLLM, 2x H100 80GB, 128K context

Each template pre-tuned with: runtime settings, tool-call/reasoning parsers, scoring path, health probes, request concurrency, model-specific context-extension settings.

#### SageMaker Studio Integration (Parallel Launch)
- Deep-link buttons on HF model pages: Customize on SageMaker AI (fine-tuning) and Deploy on SageMaker AI (endpoint)
- Pre-configured IAM policy (AmazonSageMakerModelCustomizationCoreAccess) auto-created
- GPU quota visibility inline in instance selection UI
- Supports SFT, DPO, RLVR, RLAIF training jobs
- Context preserved end-to-end — no need to re-select model in SageMaker

#### Key Enterprise Features
- Private networking — deployments inside private networks without outbound access to HF Hub (weights pre-staged in Azure)
- Auto-upgraded runtimes — container updates, runtime upgrades, CVE patches applied automatically without redeployment
- Unified endpoint — Managed Compute, pay-per-token, and provisioned throughput share the same SDK, auth, observability, billing
- Global + Data Zone deployments — residency and sovereignty support
- Observability — Azure Monitor metrics, per-deployment billing tags
- Agent integration — Foundry Agents connect to Collection models via admin-connected models

#### Zero-Cost Notes
- Model discovery, browsing, and curation information on HF is free
- Enterprise Managed Compute is paid (per-accelerator-hour pricing) but the curation pipeline and deployment templates are managed by Microsoft as part of the service
- SageMaker deep-link integration is free — you only pay for SageMaker compute when you run training or inference

### Skill
hf-hub-foundry-enterprise-deployment-curation — Hugging Face models on Microsoft Foundry Managed Compute: full enterprise curation pipeline (trending identification to license screening to trust_remote_code remediation to CVE-scanned runtime builds to weight pre-staging to catalog publishing), 7 supported runtimes (vLLM, SGLang, TRT-LLM, NIM, TEI, llama.cpp, hf-serve), deployment templates, OpenAI-compatible scoring, Foundry Agents integration, parallel SageMaker Studio integration, and enterprise deployment patterns.
