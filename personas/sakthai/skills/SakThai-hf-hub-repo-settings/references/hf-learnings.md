# HF Hub Repo Settings, Visibility & Tags Management

**Source**: `huggingface_hub` v1.24.0 source code + Hub REST API
**Author**: SakThai
**License**: MIT
**Date**: 2026-07-25

---

## 1. Repository Settings — `update_repo_settings`

The primary method to change repo visibility and gated access status.

### Signature

```python
def update_repo_settings(
    self,
    repo_id: str,
    *,
    gated: Literal["auto", "manual", False] | None = None,
    private: bool | None = None,
    visibility: Literal["public", "private", "protected"] | None = None,
    token: str | bool | None = None,
    repo_type: str | None = None,
) -> None:
```

### Parameters

| Parameter | Values | Description |
|-----------|--------|-------------|
| `gated` | `"auto"` | Gated — access requests auto-approved or denied based on predefined criteria |
| `gated` | `"manual"` | Gated — access requests require manual approval |
| `gated` | `False` | Not gated — anyone can access |
| `private` | `True` | Makes repo private |
| `private` | `False` | Makes repo public |
| `visibility` | `"public"` | Public repo |
| `visibility` | `"private"` | Private repo |
| `visibility` | `"protected"` | Protected (Spaces only) |

> **Note**: `private` and `visibility` are mutually exclusive — passing both raises `ValueError`.

### REST API Endpoint

```
PUT https://huggingface.co/api/{repo_type}s/{repo_id}/settings
```

With JSON payload:
```json
{
  "gated": "auto",
  "visibility": "private"
}
```

### Internal Resolution Logic

The `_resolve_repo_visibility` helper handles the `private`/`visibility` mapping:
- `private=True` → `"private"`
- `private=False` → `"public"`
- `visibility="protected"` → only valid for Spaces; raises `ValueError` otherwise

### Usage Examples

```python
from huggingface_hub import HfApi

api = HfApi()

# Make repo private
api.update_repo_settings("beer-sakthai/my-model", private=True)

# Remove gated access
api.update_repo_settings("beer-sakthai/gated-model", gated=False)

# Enable manual gated access
api.update_repo_settings("beer-sakthai/research-model", gated="manual")

# Protected Space
api.update_repo_settings("beer-sakthai/my-space", visibility="protected", repo_type="space")
```

### Error Handling

| Error | Cause |
|-------|-------|
| `ValueError` | Invalid gated value (not "auto", "manual", or False) |
| `ValueError` | Invalid repo_type |
| `ValueError` | Protected visibility on non-Space repo |
| `HfHubHTTPError` | API failure (auth, not found, etc.) |
| `RepositoryNotFoundError` | Repo doesn't exist or private + no access |

---

## 2. Tag Management — `create_tag` & `delete_tag`

Git-style tagging for Hub repository commits.

### `create_tag`

```python
def create_tag(
    repo_id: str,
    *,
    tag: str,
    tag_message: str | None = None,
    revision: str | None = None,
    token: bool | str | None = None,
    repo_type: str | None = None,
    exist_ok: bool = False,
) -> None:
```

- **`tag`**: Name of the tag to create (e.g. `"v1.0.0"`)
- **`tag_message`**: Optional annotation/description
- **`revision`**: Commit SHA, branch name, or tag to point to (defaults to HEAD)
- **`exist_ok`**: If `True`, suppresses error when tag already exists

### `delete_tag`

```python
def delete_tag(
    repo_id: str,
    *,
    tag: str,
    token: bool | str | None = None,
    repo_type: str | None = None,
) -> None:
```

### Usage Examples

```python
# Create a release tag
api.create_tag("beer-sakthai/my-model", tag="v2.0.0", tag_message="Major refactor release")

# Tag a specific commit
api.create_tag("beer-sakthai/dataset-v1", tag="release-1.0",
              revision="abc123def456", repo_type="dataset")

# Delete a tag
api.delete_tag("beer-sakthai/my-model", tag="v1.0.0-rc1")

# Idempotent creation
api.create_tag("beer-sakthai/my-model", tag="v1.0.0", exist_ok=True)
```

### Tag Use Cases

- **Release management**: Tag specific SHAs as versioned releases
- **Checkpointing**: Mark important training milestones
- **Dataset versions**: Tag dataset revisions for reproducibility

---

## 3. Tag Discovery — `get_model_tags` & `get_dataset_tags`

Retrieve the complete hierarchy of valid tags for classification on the Hub.

### API Endpoints

- Models: `GET https://huggingface.co/api/models-tags-by-type`
- Datasets: `GET https://huggingface.co/api/datasets-tags-by-type`

### Return Value

Returns a nested dict with categories and available tags. Structure example:

```python
{
  "library": ["transformers", "diffusers", "sentence-transformers", ...],
  "language": ["en", "fr", "de", "ja", ...],
  "license": ["mit", "apache-2.0", "cc-by-4.0", ...],
  "pipeline_tag": ["text-classification", "image-classification", ...],
  "dataset_tasks": ["text-classification", "question-answering", ...],
  "other": [...]
}
```

### Usage

```python
# Get all valid model tags
model_tags = api.get_model_tags()
for category, tags in model_tags.items():
    print(f"{category}: {len(tags)} tags available")

# Get dataset tags
dataset_tags = api.get_dataset_tags()
```

### Practical Use

- **Validation**: Ensure tags used in model cards are valid
- **Discovery**: Find available categories for repo classification
- **Automation**: Programmatically determine available pipeline tags

---

## 4. Reading Settings Back — `repo_info` with `expand`

The `repo_info` method returns a `ModelInfo`, `DatasetInfo`, or `SpaceInfo` dataclass with settings information.

### Signature

```python
def repo_info(
    repo_id: str,
    *,
    revision: str | None = None,
    repo_type: str | None = None,
    timeout: float | None = None,
    files_metadata: bool = False,
    expand: ExpandModelProperty_T | None = None,
    token: bool | str | None = None,
) -> ModelInfo | DatasetInfo | SpaceInfo:
```

### Available Expand Parameters (Models)

| Expand Property | Description |
|----------------|-------------|
| `gated` | Gated access status |
| `private` | Privacy status |
| `cardData` | Full model card metadata |
| `tags` | All tags assigned |
| `pipeline_tag` | Primary pipeline tag |
| `library_name` | Library used |
| `siblings` | File listing |
| `downloads` | Download count |
| `downloadsAllTime` | All-time downloads |
| `likes` | Like count |
| `createdAt` | Creation timestamp |
| `lastModified` | Last modification |
| `sha` | HEAD commit SHA |
| `safetensors` | SafeTensors metadata |
| `config` | Model config |
| `widgetData` | Widget examples |
| `spaces` | Spaces using this model |
| `evalResults` | Evaluation results |
| `baseModels` | Base models |
| `inferenceProviderMapping` | Inference providers |
| `trendingScore` | Trending score |
| `usedStorage` | Storage used |
| `resourceGroup` | Resource group |
| `inference` | Inference status |
| `gguf` | GGUF metadata |

### Usage Examples

```python
# Get model's gated status
model_info = api.repo_info("beer-sakthai/model", expand="gated")
print(f"Gated: {model_info.gated}, Private: {model_info.private}")

# Full metadata including card data and tags
info = api.repo_info("beer-sakthai/model", expand=["cardData", "tags", "gated"])
print(f"Pipeline: {info.pipeline_tag}")
print(f"Tags: {info.tags}")
print(f"Card data: {info.card_data.to_dict() if info.card_data else {}}")

# File listing
info = api.repo_info("beer-sakthai/model", files_metadata=True)
for sibling in info.siblings:
    print(f"{sibling.rfilename}: {sibling.size} bytes")
```

### Settings-Related Fields by Repo Type

**ModelInfo**: `gated`, `private`, `tags`, `card_data`, `pipeline_tag`, `library_name`

**DatasetInfo**: `gated`, `private`, `tags`, `card_data`

**SpaceInfo**: `gated`, `private`, `tags`, `sdk`

---

## 5. Collection Metadata — `update_collection_metadata`

Modify collection appearance, access, and organization settings.

### Signature

```python
def update_collection_metadata(
    self,
    collection_slug: str,
    *,
    title: str | None = None,
    description: str | None = None,
    position: int | None = None,
    private: bool | None = None,
    theme: str | None = None,
    token: bool | str | None = None,
) -> Collection:
```

### Parameters

| Parameter | Description |
|-----------|-------------|
| `title` | New collection title |
| `description` | New description |
| `position` | Position in user's collection list |
| `private` | Privacy toggle |
| `theme` | Visual theme (e.g. `"pink"`, `"blue"`, `"green"`) |

### REST API

```
PATCH https://huggingface.co/api/collections/{collection_slug}
```

### Usage

```python
from huggingface_hub import update_collection_metadata

collection = update_collection_metadata(
    collection_slug="beer-sakthai/sakthai-model-family-64f9a55bb3115b4f513ec026",
    title="SakThai Model Family",
    description="All models, datasets and Spaces for the SakThai household",
    private=False,
    theme="pink",
)
print(f"Updated: {collection.slug}")
```

---

## 6. Best Practices & Patterns

### Visibility Management Flow

```python
def ensure_repo_visibility(repo_id: str, repo_type: str = "model", desired: str = "public"):
    """Ensure a repo has the desired visibility setting."""
    info = api.repo_info(repo_id, repo_type=repo_type, expand="private")
    
    current = "private" if info.private else "public"
    if current != desired:
        api.update_repo_settings(repo_id, visibility=desired, repo_type=repo_type)
        print(f"Changed {repo_id} visibility: {current} -> {desired}")
    else:
        print(f"{repo_id} already {desired}")
```

### Gated Access Automation

```python
def set_gated_access(repo_id: str, mode: Literal["auto", "manual", False]):
    """Set gated access for a repo with validation."""
    # First check current state
    info = api.repo_info(repo_id, expand="gated")
    if info.gated == mode:
        print(f"Already in {mode} mode")
        return
    api.update_repo_settings(repo_id, gated=mode)
    print(f"Gated mode set to: {mode}")
```

### Tag Management for Releases

```python
def create_release_tag(repo_id: str, version: str, commit_sha: str | None = None):
    """Create a versioned release tag."""
    tag_name = f"v{version}"
    api.create_tag(
        repo_id,
        tag=tag_name,
        tag_message=f"Release {version}",
        revision=commit_sha,
        exist_ok=True,
    )
    print(f"Created tag {tag_name}")
```

---

## 7. Key Summary

| API Method | REST Method | Endpoint | Purpose |
|------------|-------------|----------|---------|
| `update_repo_settings` | PUT | `/api/{type}s/{id}/settings` | Change visibility, gated |
| `create_tag` | (Hub API) | commit tagging | Tag a commit |
| `delete_tag` | (Hub API) | commit tagging | Remove a tag |
| `get_model_tags` | GET | `/api/models-tags-by-type` | Valid model tags |
| `get_dataset_tags` | GET | `/api/datasets-tags-by-type` | Valid dataset tags |
| `repo_info` | GET | `/api/{type}s/{id}` | Read repo metadata |
| `update_collection_metadata` | PATCH | `/api/collections/{slug}` | Update collection |

---

## References

- Source: `huggingface_hub.hf_api.HfApi` (`~/.venv-sakthai/lib/python3.14/site-packages/huggingface_hub/hf_api.py`)
- Hub API docs: https://huggingface.co/docs/hub/en/api
- huggingface_hub docs: https://huggingface.co/docs/huggingface_hub/main/en/package_reference/hf_api
