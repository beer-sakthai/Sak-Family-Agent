# HF Learnings — MLCommons Croissant Metadata on Hugging Face Hub

> **author:** SakThai  
> **license:** MIT  

## 2026-07-25: hf-croissant-metadata-and-hub-integration-deep-dive — Croissant 🥐 Metadata Format & HF Hub Integration (Topic #387)

### Summary

Comprehensive deep-dive into **Croissant** 🥐 — the MLCommons standard metadata format for describing ML datasets — and its deep integration with the Hugging Face Hub. Croissant is built on schema.org and JSON-LD, providing a rich, machine-readable description of datasets including distribution (files), structure (record sets, fields), and ML-specific semantics (splits, data types, transformations).

The Hugging Face Hub automatically generates Croissant metadata for every compatible dataset (primarily Parquet-based) and exposes it via the `/api/datasets/{repo}/croissant` endpoint. The `mlcroissant` Python library (v1.1.0, 878★ on GitHub) enables creating, validating, and consuming Croissant metadata across ML frameworks (TFDS, PyTorch, JAX).

**Key insight:** Croissant is the bridge between dataset metadata and ML tooling — it turns static dataset descriptions into actionable, framework-agnostic data pipelines. HF's auto-generation for Parquet datasets means every Parquet dataset on the Hub already has Croissant metadata without any manual effort from the uploader.

---

### 1. What Is Croissant?

Croissant is a **high-level metadata format for ML datasets** that layers four dimensions of description on top of schema.org/Dataset:

| Layer | Description | Croissant Concept |
|-------|-------------|-------------------|
| 📦 **Resources** | Where files live and how to access them | `FileObject`, `FileSet` |
| 🏗️ **Structure** | Columns, types, shapes, splits | `RecordSet`, `Field`, `Split` |
| 🧠 **Semantics** | ML-specific meaning (e.g., image vs label) | `dataType`, `sc:Text`, `cr:UInt16` |
| 🔄 **Transformations** | How raw files become ML-ready tensors | `transform`, `regex`, `jsonPath` |

Croissant is an **open standard** developed by MLCommons (the same organization behind MLPerf benchmarks), with contributions from Google, Hugging Face, Meta, and others. The specification is at `http://mlcommons.org/croissant/1.1`.

**Repository:** https://github.com/mlcommons/croissant — 878★, 20+ contributors  
**Python library:** `mlcroissant` v1.1.0 on PyPI — `pip install mlcroissant`

---

### 2. What Croissant Looks Like (JSON-LD)

Croissant is expressed as **JSON-LD** (JSON for Linked Data). Every Croissant document has four major sections:

#### 2.1 `@context` — Vocabulary Mapping

Defines the JSON-LD context, mapping shorthand terms to full URLs:

```json
{
  "@context": {
    "@language": "en",
    "@vocab": "https://schema.org/",
    "cr": "http://mlcommons.org/croissant/",
    "dct": "http://purl.org/dc/terms/",
    "sc": "https://schema.org/",
    "fileObject": "cr:fileObject",
    "fileSet": "cr:fileSet",
    "recordSet": "cr:recordSet",
    "dataType": {"@id": "cr:dataType", "@type": "@vocab"},
    "field": "cr:field",
    "transform": "cr:transform",
    "regex": "cr:regex",
    "source": "cr:source",
    "data": {"@id": "cr:data", "@type": "@json"}
  }
}
```

HF uses **38 context entries** covering schema.org types, Croissant types, Dublin Core terms, and custom transformation operations.

#### 2.2 `distribution` — File Descriptions

Describes the dataset's files using two types:

- **`cr:FileObject`** — A single file or data source (e.g., a git repository)
- **`cr:FileSet`** — A pattern-based set of files (e.g., all Parquet files in a directory)

```json
{
  "distribution": [
    {
      "@type": "cr:FileObject",
      "@id": "repo",
      "name": "repo",
      "description": "The Hugging Face git repository.",
      "contentUrl": "https://huggingface.co/datasets/anisoleai/fineweb-tokenized/tree/refs%2Fconvert%2Fparquet",
      "encodingFormat": "git+https",
      "sha256": "https://github.com/mlcommons/croissant/issues/80"
    },
    {
      "@type": "cr:FileSet",
      "@id": "parquet-files-for-config-default",
      "containedIn": {"@id": "repo"},
      "encodingFormat": "application/x-parquet",
      "includes": "default/*/*.parquet"
    }
  ]
}
```

Key properties of `FileSet`:
| Property | Description |
|----------|-------------|
| `@id` | Unique identifier |
| `containedIn` | Reference to parent FileObject |
| `encodingFormat` | MIME type (e.g., `application/x-parquet`) |
| `includes` | Glob pattern for matching files |
| `excludes` | Optional exclusion pattern |

#### 2.3 `recordSet` — Data Structure Definition

The heart of Croissant. Defines how data is organized into records and fields:

```json
{
  "recordSet": [
    {
      "@type": "cr:RecordSet",
      "@id": "default_splits",
      "name": "default_splits",
      "description": "Splits for the default config.",
      "dataType": "cr:Split",
      "key": {"@id": "default_splits/split_name"},
      "field": [
        {
          "@type": "cr:Field",
          "@id": "default_splits/split_name",
          "dataType": "sc:Text"
        }
      ],
      "data": [
        {"default_splits/split_name": "train"}
      ]
    },
    {
      "@type": "cr:RecordSet",
      "@id": "default",
      "description": "example/dataset - 'default' subset",
      "field": [
        {
          "@type": "cr:Field",
          "@id": "default/split",
          "dataType": "sc:Text",
          "source": {
            "fileSet": {"@id": "parquet-files-for-config-default"},
            "extract": {"fileProperty": "fullpath"},
            "transform": {"regex": "default/(?:partial-)?(train)/.+parquet$"}
          },
          "references": {"field": {"@id": "default_splits/split_name"}}
        },
        {
          "@type": "cr:Field",
          "@id": "default/token_ids",
          "dataType": "cr:UInt16",
          "source": {
            "fileSet": {"@id": "parquet-files-for-config-default"},
            "extract": {"column": "token_ids"}
          }
        }
      ]
    }
  ]
}
```

**Key RecordSet features:**

| Feature | Description |
|---------|-------------|
| `Split` RecordSet | Defines available splits (train/val/test) — data is inline |
| `key` | Identifies the field that defines split membership |
| `source.fileSet` | Links a field to files in the distribution |
| `source.extract.column` | Maps a Parquet column to a Croissant field |
| `source.extract.fileProperty` | Extracts metadata from file path (e.g., `fullpath`) |
| `transform.regex` | Applies regex to extract values from file paths |
| `references.field` | Cross-references between record sets (split → data) |

#### 2.4 Top-Level Dataset Metadata

```json
{
  "@type": "sc:Dataset",
  "conformsTo": "http://mlcommons.org/croissant/1.1",
  "name": "fineweb-tokenized",
  "description": "FineWeb Tokenized — 4 trillion tokens...",
  "alternateName": ["anisoleai/fineweb-tokenized", "FineWeb Tokenized (AnisoleAI)"],
  "creator": {
    "@type": "Person",
    "name": "AnisoleAI",
    "url": "https://huggingface.co/anisoleai"
  },
  "keywords": ["text-generation", "English", "parquet", "Croissant"],
  "license": "https://choosealicense.com/licenses/odc-by/",
  "url": "https://huggingface.co/datasets/anisoleai/fineweb-tokenized"
}
```

---

### 3. Croissant Data Types

Croissant defines a rich set of data types, mapped from both schema.org and Croissant-specific types:

| Croissant Type | schema.org Mapping | Description |
|----------------|-------------------|-------------|
| `sc:Text` | `https://schema.org/Text` | String/unicode data |
| `sc:Integer` | `https://schema.org/Integer` | 64-bit integer |
| `sc:Float` | `https://schema.org/Float` | 64-bit float |
| `sc:Boolean` | `https://schema.org/Boolean` | True/false |
| `sc:Date` | `https://schema.org/Date` | ISO-8601 date |
| `sc:DateTime` | `https://schema.org/DateTime` | ISO-8601 datetime |
| `cr:UInt8` | — | Unsigned 8-bit integer |
| `cr:UInt16` | — | Unsigned 16-bit integer (used for token IDs) |
| `cr:UInt32` | — | Unsigned 32-bit integer |
| `cr:UInt64` | — | Unsigned 64-bit integer |
| `cr:Float16` | — | 16-bit float (half precision) |
| `cr:Float32` | — | 32-bit float |
| `cr:Float64` | — | 64-bit float (same as sc:Float) |
| `cr:Split` | — | Dataset split indicator |

HF's Croissant generation uses `cr:UInt16` for token IDs (as seen in FineWeb Tokenized), `sc:Text` for string columns, and `cr:Split` for the split definition record set.

---

### 4. Hugging Face Hub Croissant Integration

#### 4.1 The Croissant API Endpoint

Every dataset on HF has an auto-generated Croissant metadata endpoint:

```
GET https://huggingface.co/api/datasets/{namespace}/{repo}/croissant
```

**Returns:** JSON-LD Croissant metadata (Content-Type: `application/ld+json`)

**Examples:**
- `GET /api/datasets/anisoleai/fineweb-tokenized/croissant` — Large dataset with Parquet shards
- `GET /api/datasets/huggingface/documentation-images/croissant` — Image dataset

**Authentication:** Required for gated datasets. Use your HF token.

The endpoint returns a **404** for datasets that don't have Croissant-compatible metadata (non-Parquet datasets, datasets without configs).

#### 4.2 Auto-Generation for Parquet Datasets

HF Hub **automatically generates** Croissant metadata for datasets that:
1. Have at least one Parquet-based config
2. Are uploaded via the HF Datasets library or Parquet conversion pipeline

The auto-generation creates:
- A `repo` FileObject pointing to the git repository
- A `FileSet` per dataset config with Parquet file glob patterns (e.g., `default/*/*.parquet`)
- A `Split` RecordSet defining available splits (train/test/validation)
- A data RecordSet with fields mapped to Parquet columns
- Regex-based split extraction from file paths (e.g., `default/(?:partial-)?(train)/.+parquet$`)

**No manual action needed** — any dataset uploaded through HF Datasets with Parquet format automatically gets Croissant metadata.

#### 4.3 The `mlcroissant` Hub Tag

Datasets with Croissant metadata get the `mlcroissant` tag automatically. You can search for them:

```
https://huggingface.co/datasets?tag=mlcroissant&sort=trending
```

Example from the API response:
```json
{
  "id": "anisoleai/fineweb-tokenized",
  "tags": [..., "mlcroissant", ...]
}
```

The tag enables filtering and discovery of Croissant-compatible datasets.

#### 4.4 Auto-Generated Croissant Structure for HF Datasets

Analyzing real Croissant responses from HF datasets reveals a consistent structure:

| Component | Always Present? | Description |
|-----------|----------------|-------------|
| `@context` | ✅ | 38 key vocabulary mappings |
| `distribution[0]` (FileObject) | ✅ | Git repo reference |
| `distribution[1]` (FileSet) | ✅ | Parquet file glob pattern |
| `recordSet[0]` (Split RecordSet) | ✅ | Split definitions with inline data |
| `recordSet[1]` (Data RecordSet) | ✅ | Actual data fields with column mappings |
| `conformsTo` | ✅ | `http://mlcommons.org/croissant/1.1` |
| `sc:Dataset @type` | ✅ | Top-level type declaration |
| `creator` | ✅ | From HF dataset author metadata |
| `keywords` | ✅ | Tags/annotations from HF dataset card |
| `license` | ✅ | SPDX or URL from HF license field |

**For multi-config datasets:** Each config gets its own FileSet and RecordSet entries.

---

### 5. The `mlcroissant` Python Library

The official Python library for working with Croissant metadata:

```bash
pip install mlcroissant
```

#### 5.1 Loading and Inspecting Croissant Metadata

```python
import mlcroissant as mlc

# Load Croissant from HF endpoint
url = "https://huggingface.co/api/datasets/anisoleai/fineweb-tokenized/croissant"
dataset = mlc.Dataset(url)

# Inspect metadata
metadata = dataset.metadata.to_json()
print(f"Dataset: {metadata['name']}")
print(f"Description: {metadata['description']}")
print(f"License: {metadata.get('license')}")
print(f"Creator: {metadata['creator']['name']}")
```

#### 5.2 Iterating Through Records

```python
# Iterate over a RecordSet
for record in dataset.records(record_set="default"):
    print(record)
```

#### 5.3 Using with TensorFlow Datasets

```python
import tensorflow_datasets as tfds

# Build a TFDS dataset from Croissant
url = "https://huggingface.co/api/datasets/zalando-datasets/fashion_mnist/croissant"
builder = tfds.core.dataset_builders.CroissantBuilder(
    jsonld=url,
    record_set_ids=["fashion_mnist"],
    file_format='array_record',
)
builder.download_and_prepare()

# Use in training
train, test = builder.as_data_source(split=['default[:80%]', 'default[80%:]'])
for batch in train:
    print(batch)
```

#### 5.4 Creating Custom Croissant Metadata

```python
from mlcroissant import Croissant

croissant = Croissant()
# Build distribution, record sets, fields programmatically
# or from a structured Python dictionary
croissant.add_file_set(
    id="my-files",
    encoding_format="application/x-parquet",
    includes="data/*.parquet",
    contained_in="my-repo"
)
croissant.add_record_set(
    id="my-data",
    fields=[
        {"@id": "my-data/input", "dataType": "sc:Text"},
        {"@id": "my-data/label", "dataType": "sc:Integer"}
    ]
)
```

#### 5.5 Validating Croissant Metadata

The library validates against the Croissant schema:

```python
try:
    dataset = mlc.Dataset(croissant_url)
    print(f"Valid Croissant: {dataset.metadata.to_json()['name']}")
except mlc.ValidationError as e:
    print(f"Invalid: {e}")
```

---

### 6. Integration with ML Frameworks

Croissant enables framework-agnostic dataset loading:

| Framework | Integration | Status |
|-----------|-------------|--------|
| **TensorFlow Datasets** | `CroissantBuilder` — native builder | ✅ Stable |
| **Hugging Face Datasets** | Croissant metadata auto-generated for Parquet datasets | ✅ Automatic |
| **PyTorch** | Can consume via `mlcroissant` library | ✅ Via records iteration |
| **JAX** | Can consume via `mlcroissant` + TensorFlow Datasets | ✅ Via TFDS bridge |
| **Ragged** | CroissantBuilder supports array_record format | ✅ Stable |

The key workflow:
```
HF Dataset (Parquet) → HF Auto-Croissant → mlcroissant → TFDS/PyTorch/JAX
```

---

### 7. Real-World Examples

#### 7.1 FineWeb Tokenized (anisoleai/fineweb-tokenized)

- **Size:** 4 trillion tokens across Parquet shards
- **Croissant:** 2 FileSets (repo + Parquet files), 2 RecordSets (split + data)
- **Fields:** `token_ids` (cr:UInt16), `split` (sc:Text with regex extraction)
- **License:** ODC-BY
- **Pattern:** Regex-based split extraction from file paths — `default/(?:partial-)?(train)/.+parquet$`

This is a template pattern for large-scale Parquet datasets: split membership is inferred from file paths, and data columns are directly mapped from Parquet columns.

#### 7.2 Documentation Images (huggingface/documentation-images)

- **Size:** Small (<1K images), imagefolder format
- **Croissant:** 2 FileSets, 2 RecordSets
- **Pattern:** Image datasets use the same Parquet-based Croissant structure even though the source is imagefolder (HF converts to Parquet intermediary)

#### 7.3 Fashion MNIST (zalando-datasets/fashion_mnist)

- **Classic benchmark** used in TFDS CroissantBuilder documentation
- **Pattern:** Demonstrates the TFDS → Croissant → HF bridge

---

### 8. Croissant v1.1 Key Features

| Feature | Description | HF Support |
|---------|-------------|------------|
| `conformsTo` | Version declaration | ✅ v1.1 |
| `cr:Split` RecordSet | Split definitions with inline data | ✅ |
| `cr:FileObject` | Single file description | ✅ (repo reference) |
| `cr:FileSet` | Pattern-based file sets | ✅ (Parquet glob patterns) |
| `regex` transform | Extract values from file paths | ✅ (for split inference) |
| `fileProperty` extract | Extract file metadata | ✅ (fullpath) |
| `column` extract | Map Parquet columns to fields | ✅ |
| `references` | Cross-record set references | ✅ (split → data) |
| `cr:UInt*` types | Unsigned integer support | ✅ (UInt16 for tokens) |
| `cr:Float*` types | Floating point support | ✅ |
| `isLiveDataset` | Dataset updates over time | In development |

---

### 9. Practical Patterns

#### Pattern 1: Access Croissant via HF API

```bash
# Get Croissant metadata for any public Parquet dataset
curl https://huggingface.co/api/datasets/anisoleai/fineweb-tokenized/croissant | python3 -m json.tool

# Check if a dataset has Croissant
# Look for "mlcroissant" in the tags array
curl https://huggingface.co/api/datasets/anisoleai/fineweb-tokenized | python3 -c "
import sys,json; d=json.load(sys.stdin)
print('Has Croissant:', 'mlcroissant' in [t.lower() for t in d.get('tags',[])])
"
```

#### Pattern 2: Use Croissant for Dataset Discovery

Query datasets with Croissant metadata via the search API:

```python
import requests

resp = requests.get("https://huggingface.co/api/datasets", params={
    "search": "parquet",
    "sort": "downloads",
    "direction": -1,
    "full": "true"
})
datasets = resp.json()
croissant_datasets = [d for d in datasets if has_croissant_tag(d)]
```

#### Pattern 3: Build ML Pipelines from Croissant

```python
# The ultimate value of Croissant: framework-agnostic data loading
import mlcroissant as mlc

# 1. Define the dataset once
url = "https://huggingface.co/api/datasets/.../croissant"

# 2. Load with any supported framework
ds = mlc.Dataset(url)

# 3. Access metadata (always available)
metadata = ds.metadata.to_json()
num_fields = len(ds.metadata.record_sets[0].fields)

# 4. Iterate records (framework-neutral)
for record in ds.records(record_set="default"):
    inputs, labels = preprocess(record)
```

#### Pattern 4: Zero-Cost Metadata Extraction

Croissant metadata is **free** — no GPU, no API credits, no compute. Use it to extract dataset structure information programmatically:

```python
import requests

def get_dataset_fields(repo_id):
    """Extract field names and types from a dataset's Croissant metadata."""
    url = f"https://huggingface.co/api/datasets/{repo_id}/croissant"
    resp = requests.get(url)
    resp.raise_for_status()
    croissant = resp.json()
    
    fields = []
    for rs in croissant.get("recordSet", []):
        for field in rs.get("field", []):
            fields.append({
                "id": field["@id"],
                "type": field["dataType"],
                "record_set": rs["@id"]
            })
    return fields

# Example
fields = get_dataset_fields("anisoleai/fineweb-tokenized")
for f in fields:
    print(f"{f['id']}: {f['type']}")
# Output:
# default_splits/split_name: sc:Text
# default/split: sc:Text
# default/token_ids: cr:UInt16
```

---

### 10. Key Insights

1. **Croissant is a universal metadata layer** — It sits between raw data files and ML frameworks, enabling any framework to consume any Croissant-enabled dataset without custom format parsing.

2. **HF auto-generates Croissant for free** — Every Parquet dataset on the Hub already has Croissant metadata via the `/api/datasets/{repo}/croissant` endpoint. No manual work needed by dataset creators.

3. **The structure is consistent** — HF's Croissant always has: repo FileObject → Parquet FileSet → Split RecordSet → Data RecordSet with column mapping. This consistency makes tooling trivial.

4. **Regex-based split inference** — Rather than encoding splits in the data, HF infers them from file paths (e.g., `default/train/part-0001.parquet`). This is an elegant zero-overhead approach.

5. **Croissant v1.1 is stable** — The `conformsTo` field confirms v1.1, which is also the version of `mlcroissant` on PyPI. The spec is production-ready.

6. **Discovery via mlcroissant tag** — Tag-based search makes it easy to find Croissant-compatible datasets on the Hub.

7. **Tooling ecosystem is growing** — TFDS has native `CroissantBuilder`, and the `mlcroissant` library enables PyTorch/JAX consumption. Expect broader framework integration over time.

8. **Zero-cost advantage** — Croissant metadata extraction costs nothing (no compute, no API credits). This is a perfect fit for Beer's zero-cost-first constraint.

---

### Sources

- https://huggingface.co/api/datasets/anisoleai/fineweb-tokenized/croissant — Real Croissant metadata from HF (primary source, verified by API call)
- https://huggingface.co/api/datasets/huggingface/documentation-images/croissant — Second example Croissant metadata
- https://github.com/mlcommons/croissant — MLCommons Croissant repository (878★, specification + Python library)
- https://pypi.org/project/mlcroissant/ — `mlcroissant` v1.1.0 Python package
- https://mlcommons.org/working-groups/data/croissant/ — MLCommons Croissant working group
- https://huggingface.co/docs/hub/en/datasets — HF Hub datasets documentation (general reference)
- https://schema.org/Dataset — schema.org Dataset vocabulary
- https://doi.org/10.1145/3650203.3663326 — "Croissant: A Metadata Format for ML-Ready Datasets" (companion paper)
