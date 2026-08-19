---
name: SakThai-hf-spaces-secrets-management-deep-dive
description: "Comprehensive reference for managing secrets and environment variables in Hugging\
  \ Face Spaces \u2014 covering the conceptual difference between secrets vs variables,\
  \ full Python API (add/get/delete), the REST API endpoints, Docker buildtime vs\
  \ runtime beh"
---

# Spaces Secrets & Variables Management — Complete Deep Dive

## Core Concepts

Hugging Face Spaces provides two mechanisms for injecting configuration into your app without hardcoding:

| Feature | Variables | Secrets |
|---------|-----------|---------|
| **Purpose** | Non-sensitive config | Sensitive credentials |
| **Value readable back?** | Yes | **No** (write-once) |
| **Visible in settings?** | Yes | Masked (never shown) |
| **Duplicated to forks?** | Yes | **No** |
| **Injected as** | Env var at runtime | Env var at runtime |
| **Access in code** | `os.getenv("KEY")` | `os.getenv("KEY")` |

**Key rule of thumb:** Use variables for `MODEL_REPO_ID`, `API_BASE_URL`, `LOG_LEVEL`. Use secrets for `HF_TOKEN`, `OPENAI_API_KEY`, database passwords, or anything you wouldn't paste in a public chat.

### How they reach your app

Both secrets and variables are injected as **environment variables** into the Space container at runtime. In your app code, access them identically:

```python
import os
hf_token = os.getenv("HF_TOKEN")
model_repo = os.getenv("MODEL_REPO_ID")
```

The difference is entirely in the **Hub's own storage and UI** — not in how your app consumes them.

---

## Full Python API (`huggingface_hub` v1.24.0+)

All operations live on `HfApi`:

```python
from huggingface_hub import HfApi
api = HfApi(token="your_token")  # or rely on logged-in token
```

### 1. `get_space_secrets(repo_id, *, token=None)`

**`GET /api/spaces/{repo_id}/secrets`**

Returns `dict[str, SpaceSecret]` — keyed by secret name.

```python
secrets = api.get_space_secrets("username/my-space")
# {'HF_TOKEN': SpaceSecret(key='HF_TOKEN', description='...', updated_at=datetime(...))}
```

**Important:** Values are **never** returned. Only key, description, and last update time are readable.

### 2. `add_space_secret(repo_id, key, value, *, description=None, token=None)`

**`POST /api/spaces/{repo_id}/secrets`**

Creates a new secret or updates the value of an existing one.

```python
api.add_space_secret(
    repo_id="username/my-space",
    key="OPENAI_API_KEY",
    value="sk-...",
    description="OpenAI API key for chat completion",
)
```

**Returns `None`.**

### 3. `delete_space_secret(repo_id, key, *, token=None)`

**`DELETE /api/spaces/{repo_id}/secrets`**

Removes a secret from the Space.

```python
api.delete_space_secret("username/my-space", "DEPRECATED_KEY")
```

**Returns `None`.**

### 4. `get_space_variables(repo_id, *, token=None)`

**`GET /api/spaces/{repo_id}/variables`**

Returns `dict[str, SpaceVariable]` — keyed by variable name.

```python
variables = api.get_space_variables("username/my-space")
# {'MODEL_REPO_ID': SpaceVariable(key='MODEL_REPO_ID', value='beer/model-name', description='...', updated_at=datetime(...))}
```

**Unlike secrets, variable VALUES are readable.**

### 5. `add_space_variable(repo_id, key, value, *, description=None, token=None)`

**`POST /api/spaces/{repo_id}/variables`**

Creates or updates a variable.

```python
api.add_space_variable(
    repo_id="username/my-space",
    key="MODEL_REPO_ID",
    value="beer/my-model",
    description="Default model for inference",
)
```

**Returns `dict[str, SpaceVariable]`** — the updated variable dictionary.

### 6. `delete_space_variable(repo_id, key, *, token=None)`

**`DELETE /api/spaces/{repo_id}/variables`**

Removes a variable.

```python
api.delete_space_variable("username/my-space", "OBSOLETE_VAR")
```

**Returns `dict[str, SpaceVariable]`** — the remaining variable dictionary.

---

## Data Classes

```python
@dataclass
class SpaceSecret:
    key: str
    description: str | None
    updated_at: datetime | None  # None if never updated

@dataclass
class SpaceVariable:
    key: str
    value: str
    description: str | None
    updated_at: datetime | None
```

Both constructors take `(key, values_dict)` internally — you typically don't instantiate these yourself.

---

## Setting Secrets/Variables at Space Creation

When creating a Space with `create_repo()`, you can pass initial secrets and variables:

```python
api.create_repo(
    repo_id="username/my-new-space",
    repo_type="space",
    space_sdk="gradio",
    space_secrets=[
        {"key": "HF_TOKEN", "value": "hf_...", "description": "My HF token"},
    ],
    space_variables=[
        {"key": "MODEL_REPO_ID", "value": "beer/my-model", "description": "Default model"},
    ],
)
```

---

## Docker Spaces: Buildtime vs Runtime

Docker Spaces handle variables and secrets differently at build vs run time:

### Variables (Docker)

| Phase | Access Method |
|-------|--------------|
| **Buildtime** | `ARG` in Dockerfile + `--build-arg` |
| **Runtime** | `ENV` / `os.getenv()` |

**Buildtime example (Dockerfile):**
```dockerfile
ARG MODEL_REPO_NAME
FROM python:latest
# ... use ARG during build
RUN predict.py $MODEL_REPO_NAME
```

### Secrets (Docker)

For security, secrets are **not** available as build args by default. To use a secret during build:

```dockerfile
# In Dockerfile:
RUN --mount=type=secret,id=MY_SECRET \
    cat /run/secrets/MY_SECRET
```

Then the secret value is mounted as a file at `/run/secrets/{id}` during the build step.

At **runtime**, both secrets and variables are injected as plain environment variables — `os.getenv()` works for both.

---

## The Secrets Scanner

Hugging Face runs an automated **Secrets Scanner** on all Spaces. If it detects hardcoded secrets (API keys, tokens, passwords) in your source code or commit history, the Space owner receives a notification.

**This is why you should always use the Secrets API instead of hardcoding** — the scanner will warn you, and exposed credentials in git history are a security risk that requires rotating the key.

### Best Practices

1. **Never hardcode** tokens/keys in your app files
2. **Use the Python API** (`add_space_secret`) for deployment automation
3. **Set secrets at Space creation** via `create_repo(space_secrets=[...])` for CI/CD pipelines
4. **Use variables for config, secrets for credentials** — respect the access model
5. **Rotate secrets periodically** via `add_space_secret()` (same method updates if key exists)
6. **Read secrets lazily** — use `os.getenv("KEY")` with fallbacks for local development

---

## REST API Endpoints (Direct Access)

If you're not using the Python library, the REST API is:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/spaces/{repo_id}/secrets` | List secrets (no values) |
| `POST` | `/api/spaces/{repo_id}/secrets` | Add/update secret |
| `DELETE` | `/api/spaces/{repo_id}/secrets` | Delete secret |
| `GET` | `/api/spaces/{repo_id}/variables` | List variables (with values) |
| `POST` | `/api/spaces/{repo_id}/variables` | Add/update variable |
| `DELETE` | `/api/spaces/{repo_id}/variables` | Delete variable |

All require authentication via `Authorization: Bearer {token}` header.

---

## Zero-Cost Patterns for Beer

Since every operation must be free:

1. **All API operations on free-tier Spaces are free** — manage secrets programmatically via the API at no cost.
2. **Use variables for model/config references** — they survive forks and are visible, making duplicated Spaces immediately functional.
3. **Use secrets for HF tokens** — a common pattern is `api.add_space_secret("username/my-space", "HF_TOKEN", hf_token)` to allow your Space to download gated models.
4. **Automate via cron job** — a nightly script can rotate secrets or sync variables across your Space fleet.
5. **No storage cost** — secrets and variables are metadata, not stored in the Space's disk quota.
