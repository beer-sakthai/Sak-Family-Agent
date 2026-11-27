# ModelHubMixin Metadata Customization & Complex Config Coders

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
