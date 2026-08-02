# HF Learnings Log

## 2026-07-25: hf-hub-repocard-system-source-deep-dive — RepoCard/ModelCard/DatasetCard/SpaceCard Python API (Topic #237)

### Summary
Source code deep-dive on the Hugging Face Hub's RepoCard system in `huggingface_hub v1.24.0`. Covers the full object hierarchy from `RepoCard` base class through `ModelCard`, `DatasetCard`, and `SpaceCard` subclasses, the `CardData` metadata classes, the YAML frontmatter parsing engine (`REGEX_YAML_BLOCK`), the Jinja2 template system for card generation, evaluation result formatting with `EvalResult`, and the `metadata_update()` / `metadata_eval_result()` convenience functions. Everything verified from source at `/opt/data/.venv/lib/python3.13/site-packages/huggingface_hub/`.

### Key Findings

#### 1. Architecture — Two-Layer System
```
RepoCard (repocard.py)
├── card_data_class → CardData subclass
├── default_template_path → Jinja2 template path
├── repo_type → "model" | "dataset" | "space"
├── content → full Markdown with YAML frontmatter
│   ├── self.data → CardData instance (parsed from YAML)
│   └── self.text → Markdown body (everything after YAML)
│
├── ModelCard(RepoCard)  → ModelCardData  → "model"
├── DatasetCard(RepoCard) → DatasetCardData → "dataset"
└── SpaceCard(RepoCard)  → SpaceCardData  → "space"
```

**Critical insight:** The card's `content` property dynamically reconstructs the full file from `self.data.to_yaml()` + `self.text`. This means modifying `self.data` automatically propagates to `content` with no manual sync needed.

#### 2. YAML Frontmatter Parsing
```python
# Regex maintained in sync with Hub server (moon-landing ViewMarkdown.ts)
REGEX_YAML_BLOCK = re.compile(r"^(\s*---[\r\n]+)([\S\s]*?)([\r\n]+---(\r\n|\n|$))")
```
The parser:
- Matches `---` delimiters at the start of file (or with leading whitespace)
- Captures the YAML block content between markers
- Falls back to empty metadata if no YAML block found (with warning)
- Raises `ValueError` if YAML block doesn't parse to a dict
- Preserves original key order via `_original_order` list for round-trip fidelity

#### 3. CardData — Dict-Like Metadata Container
`CardData` is NOT a dict subclass — it stores data in `self.__dict__` and implements:
- `to_dict()` — deep-copies `__dict__`, calls `_to_dict()` for subclass alterations, filters `None` values
- `to_yaml(line_break, original_order)` — optional key reordering, dumps to YAML with `yaml_dump()`
- Dict protocol: `__getitem__`, `__setitem__`, `__contains__`, `__len__`, `get(key, default)`, `pop(key, default)`
- `kwargs` passthrough: Unknown keyword args are stored in `__dict__` without validation — the system is extensible

**ModelCardData specifics:**
- `model-index` auto-generation from `eval_results` — `_to_dict()` converts `EvalResult` list to the model-index format
- `model_name` defaults from `eval_results` if provided
- Validates `eval_results` through `_validate_eval_results()` in `__init__`
- Parses legacy `model-index` kwarg back into `EvalResult` objects via `model_index_to_eval_results()`

**DatasetCardData specifics:**
- Transforms `train_eval_index` to `train-eval-index` in YAML output via `_to_dict()`
- Validated fields: `annotations_creators`, `language_creators`, `multilinguality`, `size_categories`, `source_datasets`, `task_categories`, `task_ids`

**SpaceCardData specifics:**
- `tags` field deduplicated via `_to_unique_list()`
- Configuration reference: https://huggingface.co/docs/hub/spaces-config-reference

#### 4. EvalResult Dataclass — Structured Evaluation Results
```python
@dataclass
class EvalResult:
    task_type: str           # e.g., "image-classification"
    dataset_type: str        # e.g., "common_voice"
    dataset_name: str        # e.g., "Common Voice (French)"
    metric_type: str         # e.g., "wer"
    metric_value: Any        # e.g., 0.9 or "20.0 ± 1.2"
    # Optional fields:
    task_name: str | None = None
    dataset_config: str | None = None
    dataset_split: str | None = None
    dataset_revision: str | None = None
    dataset_args: dict | None = None
    metric_name: str | None = None
    metric_config: str | None = None
    metric_args: dict | None = None
    verified: bool | None = None
    verify_token: str | None = None
    source_name: str | None = None
    source_url: str | None = None
```
Key features:
- `unique_identifier` property — tuple of (task_type, dataset_type, dataset_config, dataset_split, dataset_revision)
- `is_equal_except_value(other)` — semantic comparison ignoring the actual metric value (useful for detecting changes)
- Validates that `source_name` requires `source_url`

#### 5. Template System (Jinja2)
Default template for models: `huggingface_hub/templates/modelcard_template.md`
Default template for datasets: `huggingface_hub/templates/datasetcard_template.md`

The template receives:
- `card_data` — the YAML block rendered by `CardData.to_yaml()` (inserted inside `---` markers)
- All kwargs passed to `from_template()` — these override card_data keys if duplicate

Template sections include: Model Details, Uses, Bias/Risks, How to Get Started, Training Details, Environmental Impact, Technical Specs, Model Card Authors, Citation. Most fields default to "[More Information Needed]" via Jinja's `default()` filter.

#### 6. Validation and Push Pipeline
```
push_to_hub()
├── validate(repo_type) → POST /api/validate-yaml
│   ├── 200 → OK
│   └── 400 → raise ValueError(response.text)
├── SoftTemporaryDirectory()
│   ├── write card to README.md
│   └── upload_file() → commit to Hub
└── return commit URL
```

Validation is server-side: the Hub's `/api/validate-yaml` endpoint checks the YAML against the card schema. This means offline validation is not supported — you must be online to push.

The upload uses `upload_file()` (not `upload_large_file()` or commit API) because cards are small files.

#### 7. Convenience Functions
- `metadata_update(repo_id, metadata, repo_type, overwrite, ...)` — Loads existing README.md, merges metadata dict, re-uploads. `overwrite=True` allows field overwrites; `overwrite=False` (default) errors on existing fields.
- `metadata_load(local_path)` — Reads local file, extracts YAML block, returns dict (or None)
- `metadata_save(local_path, data)` — Saves metadata dict back to local file, preserving line endings
- `metadata_eval_result(...)` — Creates a complete `model-index` dict for direct use with `metadata_update()`

#### 8. Line Ending Detection
`_detect_line_ending()` counts CR/LF/CRLF occurrences and returns the dominant format. Implementation mirrors Hub server logic. Used by `save()` and `metadata_save()` to avoid unnecessary diffs.

### Practical Usage Patterns

**Creating a model card from scratch:**
```python
from huggingface_hub import ModelCard, ModelCardData

card_data = ModelCardData(
    language='en',
    license='apache-2.0',
    library_name='transformers',
    tags=['text-classification', 'bert'],
    pipeline_tag='text-classification',
)
card = ModelCard.from_template(
    card_data,
    model_description='A fine-tuned BERT model for sentiment analysis',
    model_id='my-org/my-model',
)
card.push_to_hub('my-org/my-model')
```

**Loading and updating an existing card:**
```python
from huggingface_hub import RepoCard

card = RepoCard.load('my-org/my-model')
card.data.language = 'fr,en'
card.data.tags.append('multilingual')
card.push_to_hub('my-org/my-model')
```

**Adding evaluation results:**
```python
from huggingface_hub import ModelCardData, EvalResult

card_data = ModelCardData(
    model_name='my-bert-model',
    eval_results=[
        EvalResult(
            task_type='text-classification',
            dataset_type='imdb',
            dataset_name='IMDB',
            metric_type='accuracy',
            metric_value=0.94,
        ),
    ],
)
```

**Quick metadata update without full card:**
```python
from huggingface_hub import metadata_update

metadata_update(
    'my-org/my-model',
    {'language': 'en', 'license': 'mit'},
    overwrite=True,
)
```

### Source Files
- `huggingface_hub/repocard.py` (835 lines) — RepoCard, ModelCard, DatasetCard, SpaceCard, metadata_load/save/update/eval_result
- `huggingface_hub/repocard_data.py` (775 lines) — CardData, ModelCardData, DatasetCardData, SpaceCardData, EvalResult, model_index conversions
- `huggingface_hub/templates/modelcard_template.md` (200 lines) — Default Jinja2 model card template
- `huggingface_hub/templates/datasetcard_template.md` — Default Jinja2 dataset card template

### Skill
mlops/hf-hub-repocard-system — Full RepoCard/ModelCard/DatasetCard/SpaceCard API
