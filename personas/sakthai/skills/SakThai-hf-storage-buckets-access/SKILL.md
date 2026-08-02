---
name: SakThai-hf-storage-buckets-access
author: SakThai
license: MIT
description: Complete reference for HF Storage Bucket access patterns and data integrations — five access methods (hf-mount, volume mounts, hf:// fsspec, CLI sync, S3 API), Python data tool integrations (pandas, DuckDB, Dask, Daft, PyArrow, PySpark, Datasets, Inspect AI, SkyPilot), S3 gateway configuration (AWS CLI, boto3, rclone, DVC), file management, security, and use cases.
version: 1.0.0
metadata:
  hermes:
    tags: [hf-hub, storage-buckets, data-integration, s3-compatibility]
    related_skills: [SakThai-hf-hub-storage-management, SakThai-hf-hub-storage-limits]
category: hf-hub
---

# HF Hub Storage Buckets — Access Patterns & Data Integration

Authoritative reference for Hugging Face Storage Buckets — S3-like mutable object storage on the Hub, powered by the Xet backend. Files overwrite in place; no Git history. This skill covers how to create, access, integrate, and manage buckets.

## Quickstart

```bash
hf buckets create my-bucket --private            # create
hf buckets sync ./data hf://buckets/u/data       # sync up
hf buckets sync hf://buckets/u/data ./data       # sync down
```

```python
from huggingface_hub import create_bucket
create_bucket("my-bucket", private=True)
```

## Five Access Methods

| Method | Best for | Details |
|--------|----------|---------|
| **hf-mount** | Mount as local FS | NFS/FUSE, lazy fetch |
| **Volume mounts** | HF Jobs & Spaces | Platform-managed |
| **hf:// paths (fsspec)** | Python tools | HfFileSystem |
| **CLI sync** | Batch transfers | rsync-like |
| **S3 API** | Existing S3 tooling | Gateway at s3.hf.co |

### hf-mount
```bash
brew install hf-mount
hf-mount start bucket username/my-bucket /mnt/data
```
Once mounted, any tool reads/writes the bucket as a local directory. Buckets are RW, repos are RO.

### Volume mounts in Jobs
```bash
hf jobs run -v hf://buckets/username/my-bucket:/data python:3.12 python script.py
```

### hf:// paths via HfFileSystem
```python
from huggingface_hub import hffs
with hffs.open("buckets/u/my-bucket/data.txt") as f: content = f.read()
files = hffs.ls("buckets/u/my-bucket")
hffs.cp("buckets/u/my-bucket/a.txt", "buckets/u/my-bucket/b.txt")
text_files = hffs.glob("buckets/u/my-bucket/*.txt")
```

### CLI sync
```bash
hf buckets sync ./data hf://buckets/username/my-bucket/data     # upload
hf buckets sync hf://buckets/username/my-bucket/data ./data     # download
hf buckets sync ./data hf://buckets/u/data --delete             # mirror
hf buckets sync ./data hf://buckets/u/data --dry-run            # preview
```
Supports `--include`, `--exclude`, `--plan`/`--apply` workflows.

## Data Integrations

All use `hf://buckets/` paths via HfFileSystem (fsspec).

**pandas:** `pd.read_parquet("hf://buckets/u/my-bucket/data.parquet")`

**DuckDB (Python):**
```python
duckdb.register_filesystem(HfFileSystem())
duckdb.sql("SELECT * FROM 'hf://buckets/u/my-bucket/data.parquet'")
```

**Dask:** `dd.read_parquet("hf://buckets/u/my-bucket/data.parquet")`

**Daft (Xet-accelerated):**
```python
io_config = IOConfig(hf=HuggingFaceConfig(token=get_token()))
daft.read_parquet("hf://buckets/u/my-bucket/data.parquet", io_config=io_config)
```

**PyArrow:** `pq.read_table("hf://buckets/u/my-bucket/data.parquet")`

**PySpark** (with `pyspark_huggingface`):
```python
spark.read.format("huggingface").option("data_files",'["data.parquet"]').load("buckets/u/my-bucket")
```

**🤗 Datasets:** `load_dataset("buckets/u/my-bucket", data_files=["data.parquet"])`

**Inspect AI:**
```bash
export INSPECT_LOG_DIR=hf://buckets/username/my-bucket/eval-logs
inspect eval popularity.py --model openai/gpt-4
```

**SkyPilot** (multi-cloud):
```yaml
file_mounts:
  /checkpoints:
    source: hf://buckets/username/qwen-sft
    store: hf
    mode: MOUNT
```
Launch: `sky launch qwen-sft.yaml` (requires `pip install "skypilot[huggingface]"`)

## S3-Compatible Gateway

Endpoint: `https://s3.hf.co/<namespace>`

Generate S3 creds at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) (token dropdown → Generate S3 credentials).

### AWS CLI
```ini
[profile hf]
region = us-east-1
endpoint_url = https://s3.hf.co/<namespace>
s3 = addressing_style=path
request_checksum_calculation = when_required
response_checksum_validation = when_required
```

### boto3
```python
s3 = boto3.client("s3", endpoint_url="https://s3.hf.co/ns",
    config=Config(region_name="us-east-1", s3={"addressing_style": "path"}))
s3.upload_file("model.safetensors", "my-bucket", "models/model.safetensors")
```

### rclone (migrate S3 to HF)
```ini
[hf]
type = s3; provider = Other; endpoint = https://s3.hf.co/<namespace>
force_path_style = true; list_version = 2; upload_cutoff = 2G; chunk_size = 2G
```
Copy: `rclone copy aws:source-bucket hf:target-bucket --progress`

### DVC
```bash
dvc remote add -d hf-bucket s3://my-bucket/dvc-store
dvc remote modify hf-bucket endpointurl https://s3.hf.co/ns
```

### DuckDB (S3 API)
```sql
CREATE SECRET hf (TYPE s3, KEY_ID 'HFAK...', SECRET '...',
    ENDPOINT 's3.hf.co/ns', URL_STYLE 'path', REGION 'us-east-1');
SELECT * FROM read_parquet('s3://my-bucket/data.parquet');
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `hf buckets create <name>` | Create bucket |
| `hf buckets list <name>` | List contents |
| `hf buckets cp <src> <dst>` | Copy files (local↔bucket, bucket↔repo) |
| `hf buckets sync <src> <dst>` | Sync directories |
| `hf buckets rm <path>` | Remove files (permanent — no recovery) |
| `hf buckets info <name>` | Bucket metadata |
| `hf sync <src> <dst>` | Alias for `hf buckets sync` |

## Use Cases

- **Training checkpoints:** `hf sync ./checkpoints hf://buckets/u/training-run/ckpt`
- **Data pipelines:** Stage raw data → process → promote final artifact to Dataset repo
- **Agentic storage:** Scratch space for tool outputs, traces, working memory
- **Rolling backups:** `hf sync ./daily hf://buckets/u/backups/latest --delete`
- **Model-bucket links:** Add `buckets: [my-org/my-bucket]` to model card YAML

## Security & Compliance

| Feature | Details |
|---------|---------|
| Encryption | AES-256 at rest, TLS in transit |
| Access | SSO, RBAC (Resource Groups), scoped tokens |
| Audit | All bucket ops in org Audit Logs |
| Residency | US and EU regions; CDN pre-warming |
| Compliance | SOC 2 Type 2, GDPR |

## S3 API Limitations

- `ListObjectsV1` not supported — use V2
- No ACLs, bucket policies, tagging, versioning, or lifecycle rules
- `CopyObject` works only within a single namespace
- Multipart uploads auto-expire after 7 days
- `If-Match`/`If-None-Match` on `PutObject` only, not `GetObject`
- Object keys: no `//`, `../`, `./`, `\\`, null bytes

## References

- See `references/hf-docs-research.md` for raw research notes from all 6 source pages
- [Storage Buckets (Hub Docs)](https://huggingface.co/docs/hub/en/storage-buckets)
- [Access Patterns](https://huggingface.co/docs/hub/en/storage-buckets-access)
- [Bucket Integrations](https://huggingface.co/docs/hub/en/storage-buckets-integrations)
- [S3 Compatibility](https://huggingface.co/docs/hub/en/storage-buckets-s3)
- [Bucket Security](https://huggingface.co/docs/hub/en/storage-buckets-security)
- [Python API: Buckets Guide](https://huggingface.co/docs/huggingface_hub/guides/buckets)
- [hf-mount](https://github.com/huggingface/hf-mount)
- [SkyPilot + HF Storage](https://huggingface.co/blog/skypilot-hf-storage)
