# Research Notes — HF Storage Buckets (2026-07-30)

Source pages consulted for skill creation, with key excerpts preserved.

## 1. [Storage Buckets Overview](https://huggingface.co/docs/hub/en/storage-buckets)
- Buckets vs Repositories comparison table (versioning, types, use cases, dedup)
- Creating buckets: UI at `/new-bucket`, CLI `hf buckets create`, Python `create_bucket()`
- Browsing: `hf buckets list` with `-h`, `-R`, `--tree` flags
- File ops: `cp`, `sync`, `rm` (permanent), server-side `cp` between repos and buckets
- Pre-warming & CDN caching for multi-region workloads
- Use cases: checkpoints, data pipelines, agentic storage, rolling backups, model-bucket links
- Pricing: free tier + per-TB billing, dedup-based for Enterprise

## 2. [Access Patterns](https://huggingface.co/docs/hub/en/storage-buckets-access)
Five access methods table with best-for column:
| Method | Best for | Details |
|--------|----------|---------|
| hf-mount | Mount as local FS | NFS/FUSE, lazy fetch |
| Volume mounts | HF Jobs & Spaces | Platform-managed, same as hf-mount |
| hf:// paths (fsspec) | Python data tools | HfFileSystem — pandas, DuckDB, etc. |
| CLI sync | Batch transfers | rsync-like |
| S3 API | Existing S3 tooling | AWS CLI, boto3, s5cmd via `s3.hf.co` |

hf-mount: `brew install hf-mount` then `hf-mount start bucket <ns>/<name> /mnt/data`. Lazy fetch. Buckets RW, repos RO.

Volume mounts: `hf jobs run -v hf://buckets/ns/name:/data python:3.12 script.py`. Local dirs also supported.

HfFileSystem: fsspec-compatible, `hffs.open()`, `hffs.ls()`, `hffs.cp()`, `hffs.rm()`, `hffs.glob()`.

## 3. [Bucket Integrations](https://huggingface.co/docs/hub/en/storage-buckets-integrations)
- pandas: `pd.read_parquet("hf://buckets/u/b/data.parquet")`
- Dask: `dd.read_parquet("hf://buckets/u/b/data.parquet")`
- Daft: Xet-accelerated with `IOConfig(hf=HuggingFaceConfig(token=get_token()))`
- PyArrow: `pq.read_table("hf://buckets/u/b/data.parquet")`
- PySpark: `spark.read.format("huggingface").option("data_files",'["data.parquet"]').load("buckets/u/b")`
- Datasets: `load_dataset("buckets/u/b", data_files=["data.parquet"])`
- Inspect AI: `export INSPECT_LOG_DIR=hf://buckets/u/b/eval-logs`
- SkyPilot: `file_mounts: { /checkpoints: { source: hf://buckets/u/b, store: hf, mode: MOUNT } }`
- Filesystem ops via `hffs`: open/cp/rm/ls/glob
- OpenDAL: similar interface for Rust, Java, Go, JS
- Coming soon: Polars, DuckDB native, webdataset

## 4. [S3 Compatibility](https://huggingface.co/docs/hub/en/storage-buckets-s3)
- Endpoint: `https://s3.hf.co/<namespace>`
- Credentials: Generate from token dropdown at `/settings/tokens`
- Required config: `region=us-east-1`, `addressing_style=path`, checksum `when_required`
- Two addressing strategies: namespace in endpoint URL (recommended) or namespace as bucket name
- DuckDB via S3: `CREATE SECRET hf (TYPE s3, ... URL_STYLE 'path')`
- rclone: `type=s3, provider=Other, force_path_style=true, list_version=2`
- DVC: `dvc remote add -d hf-bucket s3://bucket/dvc-store`
- Limitations: V1 list, no ACLs/tagging/versioning/lifecycle, CopyObject same-namespace only
- Client detection: aws-cli/botocore get proxied; others get 302 redirect to CDN

## 5. [Bucket Security](https://huggingface.co/docs/hub/en/storage-buckets-security)
- AES-256 at rest, TLS in transit
- RBAC via Resource Groups
- Audit Logs for all bucket operations
- US and EU data residency
- SOC 2 Type 2, GDPR compliant

## 6. [Python API: Buckets Guide](https://huggingface.co/docs/huggingface_hub/guides/buckets)
- `create_bucket(name, private, exist_ok, region)` -> `BucketUrl` with `.bucket_id`, `.uri.to_uri()`
- `bucket_info(name)` -> `BucketInfo(id, private, created_at, size, file_count, ...)`
- `delete_bucket(name)` — must be empty
- `move_bucket(src, dst)` — rename across namespaces
- `batch_bucket_files(namespace, add=[...], delete=[...])` — add+delete in one call
- `download_bucket_files(namespace, files=[...])` — batch download
- `sync_bucket(src, dst)` — rsync-like, supports `--delete`, `--filter`, `--plan`/`--apply`
- `HfApi.bucket_exists(name)`, `list_buckets(namespace)`, `iter_buckets()`
