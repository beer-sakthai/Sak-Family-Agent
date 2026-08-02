# HF Learnings — ModelCard Python API: Programmatic Card Creation & Management

## 2026-07-24: hf-model-card-yaml-widgets — ModelCard Python API Deep Dive (Topic #29 — Deepened)

### Summary
Deep-dive into the `huggingface_hub` **ModelCard** Python API — the programmatic interface for creating, loading, validating, and pushing model cards to the Hub. Covers the `ModelCard` and `ModelCardData` classes, `EvalResult` for evaluation metadata, template-based card generation, the YAML validation endpoint, multi-repo card types (DatasetCard, SpaceCard), and practical zero-cost patterns for automating card creation in CI/CD pipelines. Source analysis based on `huggingface_hub` v1.x source at `src/huggingface_hub/repocard.py` and `repocard_data.py`.

### Core Class Hierarchy

```
RepoCard (base)
├── ModelCard     — for model repos (repo_type="model")
├── DatasetCard   — for dataset repos (repo_type="dataset")
└── SpaceCard     — for Space repos (repo_type="space")
```

All share the same API from `RepoCard`. Subclasses differ only in the default `repo_type` and the `card_data_class` they instantiate:

| Class | `repo_type` default | `card_data_class` |
|-------|-------------------|-------------------|
| `RepoCard` | `"model"` | `CardData` |
| `ModelCard` | `"model"` | `ModelCardData` |
| `DatasetCard` | `"dataset"` | `DatasetCardData` |
| `SpaceCard` | `"space"` | `SpaceCardData` |

### ModelCard API Reference

#### 1. Creating a Card: `ModelCard(content)`

```python
from huggingface_hub import ModelCard

# From raw markdown string with YAML front-matter
card = ModelCard("""---
language: en
license: mit
pipeline_tag: text-classification
---

# My Model

This is a great model for text classification.
""")

print(card.data.to_dict())
# {'language': 'en', 'license': 'mit', 'pipeline_tag': 'text-classification'}
print(card.text)
# '\n# My Model\n\nThis is a great model for text classification.\n'
```

The parser splits the content at the YAML `---` delimiters. If no YAML block is found, it logs a warning and creates an empty `ModelCardData`.

**Constructor params:**
- `content` (`str`) — Raw markdown with optional YAML front-matter
- `ignore_metadata_errors` (`bool`, default `False`) — If True, silently skip malformed YAML

#### 2. Loading from the Hub: `ModelCard.load(repo_id)`

```python
from huggingface_hub import ModelCard

# Load from Hub repo (public model)
card = ModelCard.load("nateraw/food")
print(card.data.tags)  # ['generated_from_trainer', 'image-classification', 'pytorch']

# Load from local file
card = ModelCard.load("./path/to/README.md")

# Load with custom repo type
from huggingface_hub import DatasetCard
ds_card = DatasetCard.load("beans", repo_type="dataset")
```

**How it works internally:**
- If `repo_id_or_path` is a local path → reads the file directly
- If it's a repo ID → calls `hf_hub_download(repo_id, "README.md", repo_type=...)` to download from Hub
- Supports token-based auth for gated repos

**Params:**
- `repo_id_or_path` (`str | Path`) — Hub repo ID or local file path
- `repo_type` (`str | None`) — `"model"`, `"dataset"`, `"space"`, or `None` (uses class default)
- `token` (`str | None`) — HF token for gated/private repos
- `ignore_metadata_errors` (`bool`, default `False`)

#### 3. Template-Based Creation: `ModelCard.from_template(card_data, ...)`

The most powerful way to create professional model cards programmatically. Uses Jinja2 templating with a default template from the huggingface_hub package.

```python
from huggingface_hub import ModelCard, ModelCardData, EvalResult

# Build metadata
card_data = ModelCardData(
    language="en",
    license="mit",
    library_name="transformers",
    tags=["text-classification", "bert", "custom"],
    datasets=["imdb"],
    metrics=["accuracy"],
    model_name="my-bert-classifier",
    pipeline_tag="text-classification",
)

# Generate card from default template
card = ModelCard.from_template(
    card_data,
    model_description="A BERT model fine-tuned on IMDB for sentiment analysis.",
    model_name="My BERT Classifier",
)

print(card)  # Full markdown with YAML header + template body
```

**With evaluation results:**

```python
card_data = ModelCardData(
    language="en",
    tags=["image-classification", "resnet"],
    eval_results=[
        EvalResult(
            task_type="image-classification",
            dataset_type="beans",
            dataset_name="Beans Dataset",
            metric_type="accuracy",
            metric_value=0.95,
            task_name="Image Classification",
            dataset_config="default",
            dataset_split="test",
            dataset_revision="main",
            metric_name="Accuracy",
            verified=True,
            source_name="PapersWithCode",
            source_url="https://paperswithcode.com/...",
        ),
    ],
    model_name="my-beans-classifier",
)

card = ModelCard.from_template(card_data)
```

**Using a custom template:**

```python
card = ModelCard.from_template(
    card_data=card_data,
    template_path="./my-custom-template.md",  # Local Jinja2 template
    template_kwarg1="value1",
    template_kwarg2="value2",
)

# Or from a raw template string
card = ModelCard.from_template(
    card_data=card_data,
    template_str="""---
{{ card_data }}
---
{{ model_description }}
""",
    model_description="Custom description",
)
```

**How it works:**
1. Loads the template (default from `huggingface_hub/templates/modelcard_template.md`, or custom)
2. Renders it with Jinja2, passing `card_data` as the `card_data` variable
3. The `card_data` variable auto-renders the YAML block via its `__str__` method (which calls `to_yaml()`)

**Template variables available:**
- `card_data` — The `ModelCardData` instance (auto-converts to YAML via `str()`)
- Any `**template_kwargs` you pass (e.g., `model_description`, `model_name`)

#### 4. The `ModelCardData` Class

All metadata fields for the YAML front-matter.

```python
from huggingface_hub import ModelCardData

data = ModelCardData(
    # Standard fields
    language="en, th",                    # ISO 639-1/2/3 code(s)
    license="mit",                         # Standard license slug
    library_name="transformers",          # Framework
    tags=["text-generation", "llama"],    # Discoverability tags
    pipeline_tag="text-generation",       # Task type (must match /api/tasks taxonomy)
    datasets=["user/my-dataset"],         # Training dataset ID(s)
    metrics=["accuracy"],                 # Metric names
    model_name="My Model",                # Display name for leaderboards

    # Extended license (for non-standard licenses)
    license_name="My Custom License",
    license_link="https://example.com/license",

    # Base model (for fine-tunes/adapters)
    base_model="meta-llama/Llama-3.1-8B",  # str or list[str]

    # Evaluation results
    eval_results=[EvalResult(...)],

    # Any other custom YAML keys
    extra_field="value",                   # Captured by **kwargs
    my_custom_list=[1, 2, 3],
)
```

**All constructor parameters** (keyword-only):

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_model` | `str \| list[str] \| None` | `None` | Base model ID(s) for fine-tunes |
| `datasets` | `str \| list[str] \| None` | `None` | Dataset ID(s) used for training |
| `eval_results` | `list[EvalResult] \| None` | `None` | Evaluation results for leaderboards |
| `language` | `str \| list[str] \| None` | `None` | ISO language code(s) |
| `library_name` | `str \| None` | `None` | Framework/library name |
| `license` | `str \| None` | `None` | Standard license slug |
| `license_name` | `str \| None` | `None` | Custom license name (use with `license_link`) |
| `license_link` | `str \| None` | `None` | Custom license URL (use with `license_name`) |
| `metrics` | `list[str] \| None` | `None` | Metric names for evaluation |
| `model_name` | `str \| None` | `None` | Model display name for leaderboards |
| `pipeline_tag` | `str \| None` | `None` | Task type from `/api/tasks` taxonomy |
| `tags` | `list[str] \| None` | `None` | Discoverability tags |
| `ignore_metadata_errors` | `bool` | `False` | Silently skip invalid metadata |
| `**kwargs` | any | — | Any extra YAML keys (passed through) |

**Methods:**

| Method | Signature | Description |
|--------|-----------|-------------|
| `to_dict()` | `() -> dict` | Returns all data as a plain dict (keys in original order) |
| `to_yaml()` | `(line_break=None, original_order=None) -> str` | Renders as YAML string. Pass `original_order=list(...)` to preserve key order |
| `get(key, default)` | `(str, Any) -> Any` | Dict-style access |
| `pop(key, default)` | `(str, Any) -> Any` | Dict-style pop |

**Key behavior:** `ModelCardData` inherits from `CardData`, which stores original key ordering. The `to_yaml()` output always preserves insertion order. Extra `**kwargs` are stored as-is and round-tripped faithfully.

#### 5. `EvalResult` Dataclass

Structured evaluation results for leaderboard integration.

```python
from huggingface_hub import EvalResult

result = EvalResult(
    task_type="image-classification",      # Required: task name
    dataset_type="beans",                    # Required: dataset ID
    dataset_name="Beans Dataset",            # Required: human-readable name
    metric_type="accuracy",                  # Required: metric name
    metric_value=0.95,                       # Required: metric value

    # Optional fields
    task_name="Image Classification",        # Human-readable task name
    dataset_config="default",                # Dataset configuration
    dataset_split="test",                    # Dataset split
    dataset_revision="main",                 # Dataset revision/SHA
    dataset_args={},                         # Dataset loading kwargs
    metric_name="Accuracy",                  # Human-readable metric name
    metric_config="default",                 # Metric configuration
    metric_args={},                          # Metric kwargs
    verified=True,                           # Whether result is verified
    verify_token="hf_...",                   # Verification token
    source_name="PapersWithCode",            # Source of the evaluation
    source_url="https://...",                # URL to the source
)
```

**Required fields:** `task_type`, `dataset_type`, `dataset_name`, `metric_type`, `metric_value`
**All other fields are optional.**

#### 6. Pushing to the Hub: `push_to_hub()`

```python
from huggingface_hub import ModelCard, ModelCardData

card = ModelCard.from_template(
    ModelCardData(language="en", license="mit", tags=["test"]),
    model_description="A test model card.",
)

# Push README.md to a repo
card.push_to_hub(
    repo_id="username/my-model",
    token="hf_...",                      # Optional: falls back to saved token
    repo_type="model",                   # Optional: defaults to "model"
    commit_message="Update model card",  # Optional
    commit_description="Adds metadata and description",
    revision="main",                     # Optional: branch
    create_pr=False,                     # Optional: create PR instead of direct push
    parent_commit=None,                  # Optional: specific parent SHA
)
```

**Important:** If `create_pr=True`, the card is committed to a new branch and a PR is created. If `parent_commit` is set and `create_pr=False`, the push will fail if the branch has diverged — this prevents accidental overwrites.

#### 7. Saving Locally: `save()`

```python
card.save("./README.md")  # Writes to file
```

#### 8. Validating YAML: `validate()`

```python
# Validates against Hub's YAML validation API
card.validate(repo_type="model")

# Returns None on success, raises ValueError on failure
# Internally calls: POST https://huggingface.co/api/validate-yaml
```

The validation endpoint checks:
- YAML syntax correctness
- Valid pipeline_tag values
- Valid license identifiers
- Allowed tags and metadata structure

**What happens on failure:**
```python
try:
    card.validate()
except ValueError as e:
    print(f"Validation errors: {e}")
    # Response body contains human-readable error messages
```

#### 9. Content Property

The `content` property is the core parsing engine:

```python
card = ModelCard("---\nlanguage: en\n---\n\n# Body")
card.content  # The full original content string

# Setting content re-parses it
card.content = "---\nlicense: mit\n---\n\n# New body"
card.data.to_dict()  # {'license': 'mit'}
card.text  # '\n# New body\n'

# Access raw parts
card.text   # Markdown body (everything after YAML block)
card.data   # ModelCardData instance
```

The content setter:
1. Searches for the YAML block via regex (`^---\n(.*?)\n---`)
2. Parses YAML with `yaml.safe_load()`
3. If YAML is not a dict, raises `ValueError`
4. If no YAML block found, creates empty `ModelCardData` with a warning
5. Preserves original key order for round-trip fidelity

#### 10. `str()` Representation

```python
card = ModelCard.from_template(
    ModelCardData(language="en", license="mit"),
    model_description="Test",
)
print(str(card))
# ---
# language: en
# license: mit
# ---
#
# # Model Card
#
# ...
```

The `__str__` method reconstructs the full markdown with YAML header + body. This is what gets pushed to the Hub or saved to file.

### Practical Zero-Cost Patterns

#### Pattern 1: Automated Card Generation in CI

```python
"""generate_model_card.py — Run after training completes."""
import sys
from huggingface_hub import ModelCard, ModelCardData, HfApi

def generate_card(
    model_id: str,
    model_name: str,
    task: str,
    language: str,
    license: str,
    base_model: str | None = None,
    dataset: str | None = None,
    accuracy: float | None = None,
) -> ModelCard:
    data = ModelCardData(
        language=language,
        license=license,
        library_name="transformers",
        tags=[task, model_name.lower().replace(" ", "-")],
        pipeline_tag=task,
        datasets=[dataset] if dataset else None,
        metrics=["accuracy"] if accuracy else None,
        model_name=model_name,
        base_model=base_model,
    )

    if accuracy is not None and dataset:
        data.eval_results = [
            EvalResult(
                task_type=task,
                dataset_type=dataset,
                dataset_name=dataset.split("/")[-1].replace("-", " ").title(),
                metric_type="accuracy",
                metric_value=accuracy,
            )
        ]

    return ModelCard.from_template(
        data,
        model_description=f"{model_name} is fine-tuned for {task}.",
        model_name=model_name,
    )

if __name__ == "__main__":
    card = generate_card(
        model_id="user/my-model",
        model_name="My Fine-tuned Model",
        task="text-classification",
        language="en",
        license="mit",
        base_model="bert-base-uncased",
        dataset="imdb",
        accuracy=0.92,
    )
    card.validate()
    card.push_to_hub("user/my-model")
```

#### Pattern 2: Read, Modify, and Update an Existing Card

```python
from huggingface_hub import ModelCard

# 1. Load the current card
card = ModelCard.load("user/my-model")

# 2. Modify metadata
card.data.tags = list(set(card.data.tags + ["new-tag", "updated"]))
card.data.language = "en, fr"

# 3. Update body — append a new section
card.text += "\n## Usage\n\nRun with `pipeline('text-classification')`.\n"

# 4. Validate and push
card.validate()
card.push_to_hub("user/my-model", commit_message="Update card metadata and usage")
```

**Key detail:** Setting `card.text` preserves the YAML header. Setting `card.content` re-parses everything from scratch.

#### Pattern 3: Dataset Card for Dataset Repos

```python
from huggingface_hub import DatasetCard, DatasetCardData

card_data = DatasetCardData(
    language=["en"],
    license="mit",
    annotations_creators=["crowdsourced"],
    language_creators=["found"],
    multilinguality=["monolingual"],
    pretty_name="My Dataset",
    size_categories=["10K<n<100K"],
    source_datasets=["original"],
    task_categories=["text-classification"],
)

card = DatasetCard.from_template(
    card_data,
    dataset_summary="A dataset for text classification.",
    dataset_description="Detailed description...",
)
card.push_to_hub("user/my-dataset", repo_type="dataset")
```

#### Pattern 4: Batch Card Validation

```python
from huggingface_hub import ModelCard
import concurrent.futures

def validate_card(repo_id: str) -> tuple[str, bool, str]:
    try:
        card = ModelCard.load(repo_id)
        card.validate()
        return (repo_id, True, "OK")
    except Exception as e:
        return (repo_id, False, str(e))

# Batch validate multiple model cards
repos = ["user/model-a", "user/model-b", "user/model-c"]
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(validate_card, repos))

for repo, ok, msg in results:
    status = "✅" if ok else "❌"
    print(f"{status} {repo}: {msg}")
```

#### Pattern 5: Extract Card Data from Any Public Model

```python
from huggingface_hub import ModelCard

def analyze_model_card(repo_id: str) -> dict:
    """Extract structured metadata from any public model card."""
    card = ModelCard.load(repo_id)
    data = card.data.to_dict()
    return {
        "repo_id": repo_id,
        "pipeline_tag": data.get("pipeline_tag", "unknown"),
        "license": data.get("license", "unknown"),
        "languages": data.get("language", []),
        "tags": data.get("tags", []),
        "datasets": data.get("datasets", []),
        "base_model": data.get("base_model"),
        "has_eval_results": len(data.get("eval_results", [])) > 0,
        "model_name": data.get("model_name"),
        "body_preview": card.text[:200] + "..." if len(card.text) > 200 else card.text,
    }

# Usage
info = analyze_model_card("meta-llama/Llama-3.2-1B-Instruct")
print(f"Task: {info['pipeline_tag']}, License: {info['license']}")
```

### Card Content YAML Structure

The YAML block that `ModelCardData` produces follows the HF Hub schema:

```yaml
---
language:                     # ISO code(s): "en", ["en", "fr"]
license:                      # Standard slug: "mit", "apache-2.0", "llama3.1"
library_name:                 # Framework: "transformers", "diffusers", "sentence-transformers"
tags:                         # List: ["text-generation", "pytorch", "custom_code"]
pipeline_tag:                 # Task from /api/tasks: "text-generation", "image-classification"
datasets:                     # Dataset ID(s): ["user/dataset1"]
metrics:                      # Metric names: ["accuracy", "f1"]
model_name:                   # Display name for leaderboards
base_model:                   # str or list[str] — parent model ID(s)
model-index:                  # Generated from eval_results — leaderboard entries
  - name: My Model
    results:
      - task:
          type: image-classification
          name: Image Classification
        dataset:
          type: beans
          name: Beans Dataset
          config: default
          split: test
          revision: main
        metrics:
          - type: accuracy
            value: 0.95
            name: Accuracy
            verified: true
license_name:                 # Custom license name (non-standard)
license_link:                 # Custom license URL (non-standard)
extra_field: value            # Any custom keys pass through
---
```

### `model-index` Generation

When `eval_results` are provided, `ModelCardData.to_dict()` generates a `model-index` structure automatically. Each `EvalResult` becomes an entry under the model name configured via `model_name`.

```python
data = ModelCardData(
    model_name="My Model",
    eval_results=[
        EvalResult(
            task_type="image-classification",
            dataset_type="beans",
            dataset_name="Beans",
            metric_type="accuracy",
            metric_value=0.95,
            task_name="Image Classification",
            dataset_config="default",
            dataset_split="test",
            metric_name="Accuracy",
            verified=True,
        ),
    ],
)

print(data.to_dict()["model-index"])
# [{'name': 'My Model', 'results': [{'task': {'type': 'image-classification', 'name': 'Image Classification'}, 'dataset': {'type': 'beans', 'name': 'Beans', 'config': 'default', 'split': 'test'}, 'metrics': [{'type': 'accuracy', 'value': 0.95, 'name': 'Accuracy', 'verified': True}]}]}]
```

This is the format required by the Hub's leaderboard integration at paperswithcode.com.

### Validation: `POST /api/validate-yaml`

The Hub provides a server-side YAML validation endpoint:

```
POST https://huggingface.co/api/validate-yaml
Content-Type: application/json

{
  "repoType": "model",       # "model" | "dataset" | "space"
  "content": "---\nlanguage: en\nlicense: mit\n---\n\n# Body"
}

Response 200:
{"errors": [], "warnings": []}

Response 400:
{"errors": ["Invalid pipeline_tag 'text-gen'"], "warnings": []}
```

> **⚠️ `config` field trap:** The `config` field under each `metrics` entry in `model-index` must be a **plain string**, not a nested object. The validation API (`POST /api/validate-yaml` and push-time validation) will reject with `"model-index[0].results[0].metrics[1].config" must be a string` if you pass an object like `{scale: 1-5}`. Use a short descriptor string instead: `config: mos-scale-1-5`.

This is called internally by `card.validate()` and `card.push_to_hub()`. You can also call it directly:

```python
import requests

response = requests.post(
    "https://huggingface.co/api/validate-yaml",
    json={"repoType": "model", "content": str(card)},
)
if response.status_code == 200:
    result = response.json()
    if result["errors"]:
        print(f"Errors: {result['errors']}")
    if result["warnings"]:
        print(f"Warnings: {result['warnings']}")
```

### Internal Architecture

**File locations in huggingface_hub source:**

| File | Contains |
|------|----------|
| `src/huggingface_hub/repocard.py` | `RepoCard`, `ModelCard`, `DatasetCard`, `SpaceCard` classes |
| `src/huggingface_hub/repocard_data.py` | `CardData`, `ModelCardData`, `DatasetCardData`, `SpaceCardData`, `EvalResult` |
| `src/huggingface_hub/templates/modelcard_template.md` | Default Jinja2 template |
| `src/huggingface_hub/templates/datasetcard_template.md` | Default dataset card template |

**Parsing pipeline:**
1. Regex `REGEX_YAML_BLOCK = re.compile(r"^---\n(.*?\n)---\n?", re.DOTALL)` matches YAML block
2. Group 2 (`match.group(2)`) is parsed by `yaml.safe_load()`
3. If valid dict → instantiate `card_data_class` with the dict as `**kwargs`
4. If None/empty → create empty `CardData()`
5. Text part = everything after the closing `---`

**Push pipeline:**
1. Validate (calls API)
2. Call `api.upload_file()` with path = `"README.md"` and content = `str(self)`
3. Returns the commit URL

### Key Takeaways

1. **`ModelCard.from_template()` is the recommended way** to create production cards — it generates well-structured cards with all required sections from the default Jinja2 template.

2. **`ModelCard.load()` works cross-repo-type** — use `DatasetCard.load()` or `SpaceCard.load()` for non-model repos, or pass `repo_type` explicitly.

3. **`EvalResult` feeds the PapersWithCode leaderboard** — include it for any model with benchmark results to get automatic leaderboard entries.

4. **Validation is server-side** — `validate()` calls the Hub API. It's automatically called before `push_to_hub()`.

5. **Extra kwargs pass through faithfully** — any YAML keys not in the standard schema are preserved and round-tripped. This includes HF-specific fields like `extra_gated_prompt`, `extra_gated_fields`, `co2_eq_emissions`, etc.

6. **`ModelCardData` preserves key order** — the `original_order` parameter in `to_yaml()` lets you control YAML key ordering for readability.

7. **All card operations are free** — no inference credits, no API costs. Only standard Hub API rate limits apply.

### References

- **Source code:** `src/huggingface_hub/repocard.py` — https://github.com/huggingface/huggingface_hub/blob/main/src/huggingface_hub/repocard.py
- **Card data models:** `src/huggingface_hub/repocard_data.py`
- **Default template:** `src/huggingface_hub/templates/modelcard_template.md`
- **Validation API:** `POST https://huggingface.co/api/validate-yaml`
- **License reference:** https://huggingface.co/docs/hub/repositories-licenses
- **Tasks taxonomy:** https://huggingface.co/api/tasks

### Skill
mlops/hf-model-card-yaml-widgets — references/hf-learnings.md

---
