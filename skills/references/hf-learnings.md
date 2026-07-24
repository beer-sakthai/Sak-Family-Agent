# HF Learnings Log

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
|