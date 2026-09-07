---
name: SakJules-SakThai-hf-hub-model-hub-mixin-integration
description: ">   Complete reference for integrating any ML framework with the Hugging Face Hub   using ModelHubMixin — covering the mixin lifecycle, PyTorchModelHubMixin for   instant integration, helper functions for framework-specific workflows, model   card ge"
---

# HF Hub ModelHubMixin: Integrating Custom Frameworks with the Hub

## What It Is

`ModelHubMixin` is a class in `huggingface_hub` (v1.24.0, 834 lines in `hub_mixin.py`) that lets **any** ML framework integrate with the Hugging Face Hub via multiple inheritance. Instead of manually implementing `push_to_hub()`, `from_pretrained()`, repo creation, commits, PRs, and model cards, you write just two private methods — `_save_pretrained()` and `_from_pretrained()` — and the Mixin handles everything else.

Two approaches exist: the **helper approach** (standalone functions like `push_to_hub_fastai()` / `from_pretrained_fastai()`) and the **class inheritance approach** (`ModelHubMixin`). This reference covers both, with source-level detail from `hub_mixin.py`.

## Approach Comparison

| Feature | Helper Approach | Class Inheritance (ModelHubMixin) |
|---------|----------------|----------------------------------|
| Implementation | Two standalone functions | Two private methods on your class |
| Repo creation | Manual via `HfApi.create_repo()` | Automatic |
| Config serialization | Manual | Automatic via `__init__` inspection |
| Model card generation | Manual via `ModelCard` | Automatic via template |
| Download/upload params | Must re-implement all params | Inherited (token, revision, cache_dir, etc.) |
| Download stats | Manual tracking | Automatic |
| Maintenance burden | High — must update when HF API changes | Low — upstream handles it |
| Flexibility | Maximum — full control | Controlled — within mixin contract |
| Best for | Simple integrations, one-off scripts | Libraries wanting permanent HF integration |

## 1. Helper Approach (`push_to_hub_*` / `from_pretrained_*`)

### `from_pretrained` pattern

```python
from huggingface_hub import hf_hub_download

def from_pretrained(model_id: str) -> MyModelClass:
    # Download model from Hub
    cached_model = hf_hub_download(
        repo_id=model_id,
        filename="model.safetensors",
        library_name="my-library",
        library_version=get_my_library_version(),
    )
    # Load model from downloaded file
    return load_model(cached_model)
```

### `push_to_hub` pattern

```python
from huggingface_hub import HfApi
from tempfile import TemporaryDirectory
from pathlib import Path

def push_to_hub(model: MyModelClass, repo_name: str) -> str:
    api = HfApi()
    # Create repo if not existing
    repo_id = api.create_repo(repo_name, exist_ok=True).repo_id

    # Save all files in temp dir and push in single commit
    with TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        save_model(model, tmpdir / "model.safetensors")
        # Generate model card
        card = generate_model_card(model)
        (tmpdir / "README.md").write_text(card)
        # Push to hub
        return api.upload_folder(repo_id=repo_id, folder_path=tmpdir)
```

### Limitations of helpers

Users expect all these `from_pretrained` params: `token`, `revision`, `cache_dir`, `force_download`, `local_files_only`, `proxies`. And all these `push_to_hub` params: `commit_message`, `private`, `create_pr`, `branch`, `allow_patterns`, `ignore_patterns`. Supporting them all means duplicating parameter handling from `huggingface_hub`. When a new parameter is added upstream, you must update your library. **Class inheritance solves this.**

## 2. Class Inheritance — ModelHubMixin (Source Architecture)

### Source file: `huggingface_hub/hub_mixin.py` (834 lines, v1.24.0)

### Core classes

- **`MixinInfo`** (`@dataclass`, line 110–116): stores `model_card_template`, `model_card_data`, `docs_url`, `paper_url`, `repo_url` — the metadata for model card generation.
- **`ModelHubMixin`** (line 133): the base mixin class with 3 public + 2 private methods.
- **`PyTorchModelHubMixin(ModelHubMixin)`** (line 740): concrete implementation for PyTorch models — saves/loads safetensors.

### ModelHubMixin — Public API

| Method | Signature | Description |
|--------|-----------|-------------|
| `save_pretrained()` | `(self, save_directory, *, config, repo_id, push_to_hub, model_card_kwargs, **push_to_hub_kwargs) -> str | None` | Save weights locally + optionally push |
| `from_pretrained()` | `(cls, pretrained_model_name_or_path, *, force_download, token, cache_dir, local_files_only, revision, **model_kwargs) -> T` | Class method — download + instantiate |
| `push_to_hub()` | `(self, repo_id, *, config, commit_message, private, token, branch, create_pr, allow_patterns, ignore_patterns, delete_patterns, model_card_kwargs) -> str` | Push to Hub (creates repo if needed) |
| `generate_model_card()` | `(self, *args, **kwargs) -> ModelCard` | Auto-generate model card from template + metadata |

### ModelHubMixin — Private (Overrideable) API

| Method | Signature | What You Implement |
|--------|-----------|--------------------|
| `_save_pretrained()` | `(self, save_directory: Path) -> None` | Serialize model to `save_directory` |
| `_from_pretrained()` | `(cls, *, model_id, revision, cache_dir, force_download, local_files_only, token, **model_kwargs) -> T` | Download + load model |

### Key internal mechanisms

**`__init_subclass__()` (line 196):** Called once when your class is defined (not per-instance). It:
1. Inspects `__init__` signature to build `_hub_mixin_init_parameters` dict and `_hub_mixin_jsonable_default_values`
2. Checks if `_from_pretrained` accepts a `config` kwarg (sets `_hub_mixin_inject_config`)
3. Stores model card metadata (`MixinInfo`) — inherits from parent if not overridden
4. Appends `"model_hub_mixin"` tag automatically
5. Handles custom `coders` — encoder/decoder pairs for types that aren't JSON-serializable by default (dataclasses, OmegaConf, argparse.Namespace, etc.)

**`__new__()` (line 291):** Called per-instance. Handles config propagation:
1. If `self._hub_mixin_config` already set, skip
2. If `config` passed as dataclass, set it directly
3. Otherwise, build config from `__init__` default values + passed values

**`save_pretrained()` (line 383):** Complete lifecycle:
1. Creates `save_directory`
2. Removes existing `config.json` (avoids stale configs)
3. Calls `self._save_pretrained(save_directory)` — your serialization logic
4. Serializes config as `config.json` (if not already written by `_save_pretrained`)
5. Generates model card as `README.md` (if not already written)
6. Optionally calls `push_to_hub()` if `push_to_hub=True`

**`from_pretrained()` (line 464):** Load lifecycle:
1. Checks if `pretrained_model_name_or_path` is a local directory — if so, looks for `config.json` locally
2. If remote, calls `hf_hub_download()` for `config.json`
3. Reads and decodes config — handles custom types via `_decode_arg()`
4. Populates `model_kwargs` from config values (matching `__init__` parameter names)
5. If `_from_pretrained` accepts `config`, passes it as kwarg
6. Calls `cls._from_pretrained(**model_kwargs)`
7. Stores config on instance via `_hub_mixin_config`

**`push_to_hub()` (line 621):** Upload lifecycle:
1. Creates or gets repo via `HfApi.create_repo(exist_ok=True)`
2. Creates a temporary directory via `SoftTemporaryDirectory`
3. Calls `self.save_pretrained(tmp_path)` — serializes model + config + model card
4. Uploads entire folder via `api.upload_folder()`

**Config handling:** The Mixin automatically saves/reloads `__init__` parameters as `config.json`. It handles:
- `@dataclass` configs — converted to dict via `asdict()`
- Custom types — uses `coders` dict for encode/decode
- Simple optional types — `Optional[MyType]` is unwrapped
- `VAR_KEYWORD` (`**kwargs`) — config keys are forwarded into kwargs

### Model card generation (`generate_model_card()`, line 691)

```python
def generate_model_card(self, *args, **kwargs) -> ModelCard:
    card = ModelCard.from_template(
        card_data=self._hub_mixin_info.model_card_data,
        template_str=self._hub_mixin_info.model_card_template,
        repo_url=self._hub_mixin_info.repo_url,
        paper_url=self._hub_mixin_info.paper_url,
        docs_url=self._hub_mixin_info.docs_url,
        **kwargs,
    )
    return card
```

Default template (stored as `DEFAULT_MODEL_CARD` string constant):
```markdown
---
{{ card_data }}
---

This model has been pushed to the Hub using the [PytorchModelHubMixin](...):
- Code: {{ repo_url | default("[More Information Needed]", true) }}
- Paper: {{ paper_url | default("[More Information Needed]", true) }}
- Docs: {{ docs_url | default("[More Information Needed]", true) }}
```

## 3. PyTorchModelHubMixin — Concrete Implementation

### Usage

```python
import torch
import torch.nn as nn
from huggingface_hub import PyTorchModelHubMixin

class MyModel(
    nn.Module,
    PyTorchModelHubMixin,          # multiple inheritance
    library_name="my-library",
    tags=["text-generation"],
    repo_url="https://github.com/...",
    docs_url="https://...",
):
    def __init__(self, hidden_size: int = 512, vocab_size: int = 30000):
        super().__init__()
        self.param = nn.Parameter(torch.rand(hidden_size, vocab_size))
        self.linear = nn.Linear(4, vocab_size)

    def forward(self, x):
        return self.linear(x + self.param)

# Save locally
model = MyModel(hidden_size=256)
model.save_pretrained("my-awesome-model")

# Push to Hub
model.push_to_hub("my-awesome-model")

# Load from Hub
reloaded = MyModel.from_pretrained("username/my-awesome-model")
```

### How `_save_pretrained` works (line 755)

```python
def _save_pretrained(self, save_directory: Path) -> None:
    model_to_save = self.module if hasattr(self, "module") else self
    save_model_as_safetensor(model_to_save, str(save_directory / SAFETENSORS_SINGLE_FILE))
```

Saves model weights as `model.safetensors` (not `.bin`). Uses `self.module` if wrapped in `DataParallel/DDP`.

### How `_from_pretrained` works (line 761)

1. Instantiates model via `cls(**model_kwargs)` — config values are forwarded automatically
2. For local dir: loads `model.safetensors` from directory
3. For remote: tries `model.safetensors` first, falls back to `pytorch_model.bin` if safetensors not found
4. Loads weights via `safetensors.torch.load_model()` (or `torch.load()` for pickle fallback)
5. Calls `model.eval()` — model is in eval mode by default

### Key: `map_location` and `strict` parameters

`_from_pretrained` accepts two extra `model_kwargs` that PyTorch users expect:
- `map_location="cpu"` (default) — controls device placement. Safetensors >=0.4.3 supports loading directly to GPU
- `strict=False` — whether to raise on mismatched state_dict keys

### Safetensors version behavior (line 812)

```python
# safetensors >= 0.4.3: direct device loading
if version.parse(safetensors.__version__) >= version.parse("0.4.3"):
    safetensors.torch.load_model(model, model_file, strict=strict, device=map_location)
else:
    load_model_as_safetensor(model, model_file, strict=strict)
    if map_location != "cpu":
        model.to(map_location)  # slower: load on CPU then copy
```

## 4. Metadata & Model Card Customization

### Class-level metadata attributes

Pass these as keyword arguments in the class definition (not in `__init__`):

| Attribute | Type | Purpose |
|-----------|------|---------|
| `repo_url` | `str` | Source code repository link |
| `paper_url` | `str` | Research paper link |
| `docs_url` | `str` | Documentation link |
| `model_card_template` | `str` | Jinja2 template for model card (default: `DEFAULT_MODEL_CARD`) |
| `language` | `str \| list[str]` | Language(s) the model supports |
| `library_name` | `str` | Your library name (e.g., `"transformers"`, `"diffusers"`) |
| `license` | `str` | SPDX license identifier (e.g., `"apache-2.0"`, `"mit"`) |
| `license_name` | `str` | Custom license name (only if `license="other"`) |
| `license_link` | `str` | URL to custom license |
| `pipeline_tag` | `str` | HF pipeline tag (e.g., `"text-classification"`) |
| `tags` | `list[str]` | Free-form tags for discoverability |
| `coders` | `dict[Type, tuple]` | Encode/decode pairs for custom config types |

### Custom model card template example

```python
MODEL_CARD_TEMPLATE = """---
{{ card_data }}
---
# {{ library_name | default("MyModel") }}

This model is part of MyCoolLibrary.
- **Paper:** {{ paper_url | default("N/A") }}
- **Code:** {{ repo_url | default("N/A") }}

## Usage
```python
from my_cool_library import MyCoolModel
model = MyCoolModel.from_pretrained("{{ repo_id }}")
```
"""

class MyCoolModel(
    nn.Module,
    PyTorchModelHubMixin,
    library_name="my-cool-library",
    model_card_template=MODEL_CARD_TEMPLATE,
    tags=["computer-vision", "image-classification"],
):
    ...
```

## 5. Custom Coders for Complex Config Types

When `__init__` parameters have types that aren't JSON-serializable, define custom encoders/decoders:

```python
from dataclasses import dataclass

@dataclass
class ModelConfig:
    hidden_size: int = 512
    num_layers: int = 6

class MyModel(
    nn.Module,
    PyTorchModelHubMixin,
    library_name="my-library",
    coders={
        ModelConfig: (
            lambda cfg: asdict(cfg),         # encoder: dataclass -> dict
            lambda data: ModelConfig(**data), # decoder: dict -> dataclass
        ),
    },
):
    def __init__(self, config: ModelConfig, vocab_size: int = 30000):
        super().__init__()
        self.config = config
        ...
```

Note: `@dataclass` types are handled automatically — `coders` is only needed for custom types like `argparse.Namespace`, `OmegaConf`, or third-party config objects.

## 6. Best Practices

### For library maintainers
1. **Prefer class inheritance** — it's more maintainable and gives users the full HF API surface for free
2. **Use safetensors** — `PyTorchModelHubMixin` already does; for other frameworks, use `.safetensors` format
3. **Set `library_name`** — makes all your models searchable on the Hub
4. **Always implement both `_save_pretrained` and `_from_pretrained`** — neither is optional
5. **Accept extra `**model_kwargs`** in `_from_pretrained` — lets users pass framework-specific options like `map_location`
6. **Handle local and remote paths** — `from_pretrained` should accept both a directory path and a model ID

### For users
1. **Use `save_pretrained` for local backups** — saves model, config, and model card
2. **`push_to_hub` accepts all `upload_folder` params** — use `allow_patterns`/`ignore_patterns` to filter files
3. **Config is automatically serialized** — no need to manually save `config.json`
4. **Model card is auto-generated** — but you can override by writing `README.md` in `save_pretrained()`

### Known behaviors
- `model.eval()` is called automatically on `from_pretrained` — call `model.train()` if needed
- Config is NOT serialized if `_save_pretrained` already writes `config.json` — the mixin skips overwriting
- Downloaded files respect HF caching — shared cache with `transformers`, `datasets`, etc.
- `from_pretrained` with a local path loads config from `<path>/config.json` — no download needed

## Sources

- Source code: `huggingface_hub/hub_mixin.py` (834 lines, v1.24.0) — full ModelHubMixin + PyTorchModelHubMixin implementation
- Official docs: https://huggingface.co/docs/huggingface_hub/en/guides/integrations
- Package reference: https://huggingface.co/docs/huggingface_hub/en/package_reference/mixins
- FastAI integration: `huggingface_hub/fastai_utils.py` — `push_to_hub_fastai()`, `from_pretrained_fastai()`
- GitHub: https://github.com/huggingface/huggingface_hub
