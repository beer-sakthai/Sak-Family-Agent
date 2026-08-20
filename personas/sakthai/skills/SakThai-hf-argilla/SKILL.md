---
name: SakThai-hf-argilla
description: "Argilla \u2014 open-source data annotation and collaboration platform for building\
  \ high-quality AI datasets. Deep integration with Hugging Face Hub for deployment,\
  \ authentication, and dataset import/export."
---

# Argilla — Data Annotation & Curation for AI Datasets

**Skill:** Using Argilla (v2.8.x) for data annotation, curation, and collaboration — deployed on HF Spaces, managed via Python SDK, and integrated with the Hugging Face Hub ecosystem.

## Overview

Argilla is a **free, open-source, self-hosted collaboration tool** for AI engineers and domain experts to build high-quality datasets. Created by the same team behind **Distilabel**, it focuses on collecting human feedback for NLP, LLM, and multimodal AI projects.

- **GitHub:** [argilla-io/argilla](https://github.com/argilla-io/argilla) — 5.1k stars, 496 forks (v2.8.0)
- **Docs:** https://docs.argilla.io/latest/
- **License:** Apache 2.0
- **Stack:** Python SDK + FastAPI server + Vue.js UI

### Key Differentiators

| Feature | Argilla | Alternatives |
|---------|---------|--------------|
| **HF Native** | Deploy on Spaces, login with HF OAuth, import/export to Hub | Separate infra |
| **Programmatic SDK** | Full Python API (`rg` module) | Web-only tools |
| **Semantic Search** | Vector fields for similarity-based record navigation | Basic filters only |
| **Flexible Schema** | Custom fields, questions, metadata per dataset | Fixed schemas |
| **Open Source** | Apache 2.0, self-hosted | SaaS-only options |

## Deployment

### Option A: Hugging Face Spaces (Recommended, Zero-Cost)

1. Go to https://huggingface.co/new-space
2. Use the **Argilla Docker Space** template
3. **Required secrets:**
   - `HF_TOKEN` — HF access token (write permissions for dataset export)
   - `ARGILLA_AUTH_SECRET_KEY` — random secret for session signing
4. **Optional secrets:**
   - `USERNAME` / `PASSWORD` — basic auth (omit for HF OAuth login)
   - `OAUTH2_HF_ENABLED=true` — enables HF OAuth (default with template)
5. Set **persistent storage** to `SMALL` (free) — **critical** to avoid data loss on restart
6. The Space boots as a Docker container running FastAPI + Vue.js UI

**URL pattern:** `https://{username}-argilla.hf.space`

### Option B: Docker (Local / Self-Hosted)

```bash
docker run -d \
  --name argilla \
  -p 6900:6900 \
  -e ARGILLA_AUTH_SECRET_KEY=your-secret-key \
  -e HF_TOKEN=your-hf-token \
  -v argilla-data:/data \
  argilla/argilla-server:latest
```

## Core Concepts

### Python SDK (`argilla` package)

```bash
pip install argilla
```

Import convention: `import argilla as rg`

### 1. Client (`rg.Argilla`)

The entry point — connects to an Argilla server.

```python
import argilla as rg

# Connect to a local/remote Argilla server
client = rg.Argilla(
    api_url="https://your-argilla-space.hf.space",
    api_key="argilla-api-key-from-my-settings"  # or use HF_TOKEN
)

# Or with HF OAuth directly
client = rg.Argilla(
    api_url="https://your-argilla-space.hf.space",
    api_key="hf_your_token"  # HF token works when OAuth is configured
)
```

**Key attributes:**
- `client.workspaces` — list/manage workspaces
- `client.datasets` — list/manage datasets
- `client.users` — list/manage users
- `client.webhooks` — list/manage webhooks

### 2. Workspace (`rg.Workspace`)

Logical grouping of datasets and users.

```python
# Create
workspace = client.workspaces.create(name="my-project")

# List
for ws in client.workspaces:
    print(ws.name, ws.id)

# Add user to workspace
user = client.users.create(username="annotator1", password="...")
workspace.add_user(user.id)
```

### 3. User (`rg.User`)

Annotation team members. Supports role-based access.

```python
user = client.users.create(
    username="annotator1",
    password="secure-password",  # not needed if using HF OAuth
    role="annotator",           # "admin" | "owner" | "annotator"
)
```

**Roles:**
| Role | Can create datasets | Can annotate | Can manage users |
|------|:---:|:---:|:---:|
| `owner` | ✅ | ✅ | ✅ |
| `admin` | ✅ | ✅ | ✅ |
| `annotator` | ❌ | ✅ | ❌ |

### 4. Dataset (`rg.Dataset`)

The core entity. Defined by a `Settings` object that describes the annotation schema.

```python
settings = rg.Settings(
    fields=[
        rg.TextField(name="text", title="Input Text"),
        rg.TextField(name="context", title="Context"),
    ],
    questions=[
        rg.LabelQuestion(
            name="sentiment",
            title="Sentiment",
            labels=["positive", "negative", "neutral"],
        ),
        rg.TextQuestion(
            name="explanation",
            title="Why did you choose this label?",
            use_markdown=True,
        ),
    ],
    metadata=[
        rg.TermsMetadataProperty(name="source"),
        rg.FloatMetadataProperty(name="confidence", min=0.0, max=1.0),
    ],
    vectors=[
        rg.VectorField(name="embedding", dimensions=768),
    ],
)

dataset = rg.Dataset(
    name="sentiment-annotations",
    workspace=workspace,
    settings=settings,
)
dataset = dataset.create()
```

**Field types:**
| Field | Purpose | Options |
|-------|---------|---------|
| `rg.TextField` | Show text to annotators | `name`, `title`, `use_markdown`, `required` |
| `rg.ImageField` | Show image to annotators | `name`, `title` |

**Question types:**
| Question | Type | Example |
|----------|------|---------|
| `rg.LabelQuestion` | Single-label classification | Sentiment, topic |
| `rg.MultiLabelQuestion` | Multi-label classification | Tags, categories |
| `rg.TextQuestion` | Free-text response | Explanation, summary |
| `rg.SpanQuestion` | Span/token labeling | NER entities |
| `rg.RankingQuestion` | Rank items | Preference ordering |
| `rg.RatingQuestion` | Star/numeric rating | 1-5 scale |

**Metadata property types:** `TermsMetadataProperty` (categorical), `FloatMetadataProperty` (numeric), `IntegerMetadataProperty` (int)

### 5. Record (`rg.Record`)

A single data item to annotate.

```python
import argilla as rg

record = rg.Record(
    fields={"text": "This movie was amazing!", "context": "Review by user123"},
    metadata={"source": "imdb", "confidence": 0.95},
    vectors={"embedding": [0.1, 0.2, ...]},  # 768-dim vector
    # Pre-existing suggestions (optional):
    suggestions=[
        rg.Suggestion(
            question_name="sentiment",
            value="positive",
            agent="initial-model-v1",
            type="model",  # "model" | "human" | "ai_suggestion"
        )
    ],
    # Existing responses (when importing already-annotated data):
    responses=[
        rg.Response(
            question_name="sentiment",
            value="positive",
            user_id=user.id,
        )
    ],
)

# Add records in bulk
dataset.records.log([record1, record2, record3])
```

**Record fields:**
| Field | Description |
|-------|-------------|
| `fields` | Data shown to annotators (matches `Settings.fields`) |
| `metadata` | Filterable metadata (matches `Settings.metadata`) |
| `vectors` | Embedding vectors for semantic search |
| `suggestions` | Pre-annotations / model predictions for review |
| `responses` | Ground-truth annotations from users |
| `external_id` | Your own ID for cross-referencing |

### 6. Query (`rg.Query`)

Filter and search records programmatically.

```python
from argilla import Query

# Simple filter
query = Query(filter="source == 'imdb'")

# Semantic search with vector
query = Query(
    vector=("embedding", [0.1, 0.2, ...]),
)

# Combined
query = Query(
    filter="sentiment.responses == 'positive'",
    vector=("embedding", [0.1, 0.2, ...]),
)

results = dataset.records(query)
for record in results:
    print(record.fields["text"], record.metadata)
```

## Annotation Workflow

### Complete Pipeline

```python
import argilla as rg

# 1. Connect
client = rg.Argilla(api_url="...", api_key="...")

# 2. Get or create workspace
ws = client.workspaces("my-project")

# 3. Define settings
settings = rg.Settings(
    fields=[rg.TextField(name="text", use_markdown=True)],
    questions=[rg.LabelQuestion(name="sentiment", labels=["pos", "neg", "neu"])],
)

# 4. Create dataset
ds = rg.Dataset(name="reviews", workspace=ws, settings=settings).create()

# 5. Add records
records = [
    rg.Record(fields={"text": t}) for t in ["Great!", "Terrible.", "OK."]
]
ds.records.log(records)

# 6. (Annotators work in the UI at this point)

# 7. Export annotated data
ds = client.datasets("reviews")  # refresh to get latest
for record in ds.records(with_responses=True):
    responses = record.responses  # list of Response objects
    # responses[0].value for each question
```

### Export to Hugging Face Hub

```python
# Export full dataset with annotations to HF Hub
ds.to_hub(
    repo_id="username/my-annotated-dataset",
    with_responses=True,     # include annotations
    with_suggestions=True,   # include model suggestions
    with_vectors=False,      # embeddings are large; skip unless needed
)

# Import from HF Hub
ds = rg.Dataset.from_hub("username/my-annotated-dataset")
ds = ds.create()
```

## HF Integration Deep Dive

### Authentication Flow

1. **Space deploys Argilla** with `OAUTH2_HF_ENABLED=true`
2. **Users sign in** with "Sign in with Hugging Face" button
3. **Argilla verifies** via HF OAuth — the Space owner is the first admin
4. **API key** generated per user at My Settings page
5. **Python SDK** uses either `api_key` or `HF_TOKEN` for auth

### Dataset Import/Export

```python
# Export: Argilla → HF Hub
dataset.to_hub(
    repo_id="org/my-dataset",
    repo_type="dataset",
    with_responses=True,
)

# Import: HF Hub → Argilla
external = rg.Dataset.from_hub("org/my-dataset")
local = external.create()  # creates in current workspace
```

The export preserves:
- Field values
- Question responses + user attribution
- Suggestions + agent metadata
- Metadata filters
- Vector embeddings (optional)

### Integration with Distilabel

Argilla and Distilabel are sibling projects by the same team:

- **Distilabel**: Generate synthetic datasets using LLMs (the *generation* side)
- **Argilla**: Curate, annotate, and review datasets with humans (the *curation* side)

Typical pipeline: **Generate with Distilabel → Curate with Argilla → Export to HF Hub → Fine-tune with TRL/PEFT**

## Advanced Features

### Webhooks

Respond to server events programmatically.

```python
webhook = client.webhooks.create(
    url="https://your-api.example.com/argilla-events",
    events=["dataset.updated", "record.created", "response.created"],
    enabled=True,
)
```

Events: `dataset.created`, `dataset.updated`, `dataset.deleted`, `record.created`, `record.updated`, `response.created`, `response.updated`, `user.created`, etc.

### Vector Search

Enable annotators to find similar records.

```python
settings = rg.Settings(
    # ...
    vectors=[rg.VectorField(name="sentence_embedding", dimensions=384)],
)

record = rg.Record(
    fields={"text": "example"},
    vectors={"sentence_embedding": [0.1, 0.2, ...]},  # from sentence-transformers
)
```

In the UI, annotators can search by semantic similarity instead of pagination.

### Custom Layouts

Control how fields are displayed to annotators.

```python
from argilla import Settings, TextField, LabelQuestion

settings = rg.Settings(
    fields=[
        TextField(name="question"),
        TextField(name="answer", use_markdown=True),
    ],
    questions=[
        LabelQuestion(name="relevance", labels=["relevant", "irrelevant"]),
        TextQuestion(name="notes", use_markdown=True),
    ],
    layout=[
        # Row 1: side by side
        rg.layout.HorizontalLayout(
            [rg.layout.Field("question"), rg.layout.Field("answer")]
        ),
        # Row 2: stacked
        rg.layout.VerticalLayout(
            [rg.layout.Question("relevance")],
            [rg.layout.Question("notes")],
        ),
    ],
)
```

## Use Cases

| Use Case | Argilla Workflow |
|----------|------------------|
| **RLHF / DPO** | Collect preference rankings with `RankingQuestion`, export to HF, train with TRL |
| **RAG Evaluation** | Show Q+A pairs with context, label relevance/faithfulness |
| **NER / Token Class.** | `SpanQuestion` for entity labeling |
| **Sentiment Analysis** | `LabelQuestion` + bulk model suggestions for pre-annotation |
| **Image Preference** | `ImageField` + `RankingQuestion` for comparing generations |
| **Safety / Moderation** | Custom questions, metadata filters for edge case bucketing |

## Pitfalls

- **Persistent storage is mandatory** for production — without it, data is lost on Space restart. Always set to at least `SMALL` on HF Spaces.
- **`dataset.to_hub()` exports the schema and records** but does NOT export workspace structure, user accounts, or webhook configs. Those are server-specific.
- **Vector fields increase storage significantly** — a 768-dim float32 vector per record adds ~3KB per record. Use `with_vectors=False` when exporting unless you need semantic search downstream.
- **API key ≠ HF token** — the Argilla API key is a separate credential generated per-user in the UI. HF token works as an API key only when HF OAuth is enabled.
- **Dataset schema is immutable** — once created, you cannot change fields or question types. Delete and recreate with new `Settings` if the schema needs changes.
- **Large exports may timeout** on free HF Spaces (CPU-only). For datasets with 100k+ records, use Docker deployment or batch exports.
- **The `argilla` package requires Python 3.9+** — compatible with most modern environments.

## Reference

- **Docs:** https://docs.argilla.io/latest/
- **GitHub:** https://github.com/argilla-io/argilla
- **Python SDK API:** https://docs.argilla.io/latest/reference/python/
- **Distilabel:** https://distilabel.argilla.io/ (sibling project for synthetic data generation)
- **HF Spaces Template:** https://huggingface.co/new-space (select Argilla Docker template)
- **License:** Apache 2.0
