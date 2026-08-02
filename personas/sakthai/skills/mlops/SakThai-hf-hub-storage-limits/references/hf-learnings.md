# HF Learnings — Storage Buckets S3 Compatibility Deep-Dive

**Topic:** hf-hub-storage-buckets-s3-compatibility-deep-dive
**Date:** 2026-07-25
**Author:** SakThai
**License:** MIT
**Sources:**
- Official docs: https://huggingface.co/docs/hub/en/storage-buckets-s3
- Buckets overview: https://huggingface.co/docs/hub/en/storage-buckets
- Bucket access patterns: https://huggingface.co/docs/hub/en/storage-buckets-access
- Bucket integrations: https://huggingface.co/docs/hub/en/storage-buckets-integrations
- Hugging Face Blog (Storage Buckets announcement): https://huggingface.co/blog

---

## Summary

Storage Buckets support an **S3-compatible API gateway** at `https://s3.hf.co/<namespace>`, enabling existing S3 tooling — AWS CLI, boto3, s5cmd, rclone, DuckDB (httpfs), DVC — to interact with Hub buckets without changing code. This deep-dive covers credential generation, client configuration, addressing modes, limitations vs real S3, and real-world integration recipes for each tool.

---

## 1. Architecture: The Gateway

The S3 API is implemented as a **reverse-proxy gateway** that translates AWS S3 API calls into Hugging Face Bucket operations.

```
S3 client → https://s3.hf.co/<namespace> → HF Buckets API
```

Key characteristics:
- **Single-region** currently (us-east-1) — the gateway is not multi-region, but downloads are accelerated via CDN
- **Path-style addressing only** — virtual-hosted style (bucket.s3.hf.co) is NOT supported
- **No authentication delegation** — uses AWS-style access keys derived from HF User Access Tokens
- **Only works with Storage Buckets** — cannot access models, datasets, or Spaces through the S3 gateway
- **S3 credentials are derived, not stored** — generated on-demand from an HF token, only shown once

### Gateway Behavior for Downloads

The gateway implements an intelligent redirect strategy for GetObject:

| Client | Behavior | Why |
|--------|----------|-----|
| `aws-cli`, `botocore` (boto3), `aws-sdk-rust` | Gateway proxies data through itself | These clients don't follow 302 redirects from S3 endpoints |
| `rclone`, `s5cmd`, `curl`, AWS Go SDK, others | Receives HTTP 302 → follows to CDN | Faster, gateway stays out of data path |

This means for most non-AWS tools, downloads bypass the gateway entirely after the initial redirect, going directly to the nearest CDN edge.

---

## 2. Credential Generation

S3 credentials are **derived from a Hugging Face User Access Token** — there is no separate S3 signup or IAM.

### Steps

1. Go to https://huggingface.co/settings/tokens
2. Create a new token (or use existing one)
3. Open the token's dropdown menu → **Generate S3 credentials**
4. Copy the generated:
   - **Access Key ID** (prefixed `HFAK...`)
   - **Secret Access Key** (shown once only)

### Permission Model

- S3 credentials **inherit the permissions** of the underlying HF token
- Fine-grained tokens → scope them to only the namespaces and buckets you need
- Read token → read-only S3 access; Write token → read + write S3 access
- No additional IAM-like policy system — HF token scoping IS the authorization model

### Security Properties

| Property | Detail |
|----------|--------|
| Secret visibility | Shown once at generation; if lost, revoke and regenerate |
| Scope | Bound to the parent token's permissions |
| Rotation | Regenerate from the parent token at any time |
| No secondary auth | You can't create new keys from S3 credentials — Hub tokens are the auth root |

---

## 3. Client Configuration

### Required Settings

All clients MUST configure these for the gateway to work:

| Setting | Value | Reason |
|---------|-------|--------|
| `endpoint_url` | `https://s3.hf.co/<namespace>` | Gateway, scoped to your username or org |
| `region` | `us-east-1` | Gateway is currently single-region |
| `addressing_style` | `path` | Buckets addressed as path segments, not subdomains |
| `request_checksum_calculation` | `when_required` | Prevents trailing CRC32 checksums (aws-chunked) not parsed by gateway |
| `response_checksum_validation` | `when_required` | Same reason — prevents expecting checksums in responses |

### Optional Performance Settings

| Setting | Recommended Value | Effect |
|---------|------------------|--------|
| `s3.multipart_threshold` | `2GB` | Fewer multipart parts for large uploads |
| `s3.multipart_chunksize` | `2GB` | Same — 2GB max parts reduce overhead |

### AWS CLI Profile Example

```ini
# ~/.aws/config
[profile hf]
region = us-east-1
endpoint_url = https://s3.hf.co/your-username
s3 =
    addressing_style = path
    multipart_threshold = 2GB
    multipart_chunksize = 2GB
request_checksum_calculation = when_required
response_checksum_validation = when_required

# ~/.aws/credentials
[hf]
aws_access_key_id = HFAKxxxxxxxxxx
aws_secret_access_key = xxxxxxxxxxxxxxxxxx
```

Usage:
```bash
aws --profile hf s3 ls
aws --profile hf s3 mb s3://my-bucket
aws --profile hf s3 cp ./model.safetensors s3://my-bucket/models/model.safetensors
```

---

## 4. Addressing Buckets

The namespace/bucket hierarchy introduces a mismatch with standard S3 clients. Two workaround strategies:

### Strategy 1: Namespace in Endpoint URL (Recommended)

Scope the endpoint URL to your namespace, so the client sees only the bare bucket name:

```bash
aws --endpoint-url https://s3.hf.co/my-org s3api get-object \
  --bucket my-bucket --key some/object.txt ./object.txt
```

**Pros:** Clean, works with most commands, most intuitive.
**Cons:** Cannot copy between namespaces (e.g., personal → org) in a single command.

### Strategy 2: Namespace as Bucket Name

Treat the namespace as the bucket and prepend the HF bucket name to the object key:

```bash
aws --endpoint-url https://s3.hf.co s3api get-object \
  --bucket my-org --key my-bucket/some/object.txt ./object.txt
```

**Pros:** Works for object-level ops (upload, download).
**Cons:** Fails for bucket-level ops (create/delete buckets).

---

## 5. Limitations vs AWS S3

| Feature | AWS S3 | HF Storage Buckets S3 Gateway |
|---------|--------|-------------------------------|
| **Region** | Multi-region | Single-region (us-east-1) |
| **Addressing** | Virtual-hosted + path | Path-only |
| **ListObjectsV1** | ✅ | ❌ — use V2 |
| **Delimiter** | Any character | `/` only |
| **ACLs** | ✅ | ❌ |
| **Bucket policies** | ✅ | ❌ |
| **Object tagging** | ✅ | ❌ |
| **Versioning** | ✅ | ❌ |
| **Lifecycle rules** | ✅ | ❌ |
| **SSE (server-side encryption)** | ✅ | ❌ (headers accepted, ignored) |
| **Object metadata** | Arbitrary `x-amz-meta-*` | Only `Content-Type` supported |
| **Cross-namespace CopyObject** | ✅ (any buckets) | ❌ (same namespace only) |
| **UploadPartCopy** | ✅ | ❌ |
| **Conditional requests (GetObject)** | ✅ (If-Match, If-None-Match) | ❌ (honored for PutObject/CopyObject only) |
| **Storage class** | Multiple classes | Always `STANDARD` |
| **Multipart upload expiry** | Configurable | 7 days (auto-cleanup) |

### Object Key Restrictions

Keys must NOT:
- Start or end with `/`
- Contain consecutive `//`
- Contain `../` sequences
- Start with `./`
- End with `..`
- Contain `\` (backslash) or `\0` (null byte)

---

## 6. Tool Integration Recipes

### 6.1 boto3 (Python)

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    endpoint_url="https://s3.hf.co/your-username",
    aws_access_key_id="HFAK...",
    aws_secret_access_key="...",
    config=Config(
        region_name="us-east-1",
        s3={"addressing_style": "path"},
        request_checksum_calculation="when_required",
        response_checksum_validation="when_required",
    ),
)

# Upload
s3.upload_file("model.safetensors", "my-bucket", "models/model.safetensors")

# Download
s3.download_file("my-bucket", "models/model.safetensors", "model.safetensors")

# List
response = s3.list_objects_v2(Bucket="my-bucket", Prefix="models/")
for obj in response.get("Contents", []):
    print(obj["Key"])

# Delete
s3.delete_object(Bucket="my-bucket", Key="old/temp.bin")
```

### 6.2 DuckDB (Parquet Querying via httpfs)

```sql
INSTALL httpfs;
LOAD httpfs;

CREATE SECRET hf (
    TYPE s3,
    KEY_ID 'HFAK...',
    SECRET '...',
    ENDPOINT 's3.hf.co/your-username',
    URL_STYLE 'path',
    REGION 'us-east-1'
);

-- Read Parquet directly from bucket
SELECT * FROM read_parquet('s3://my-bucket/data.parquet');

-- Write results back
COPY (
    SELECT count(*) as total, date_trunc('day', timestamp) as day
    FROM read_parquet('s3://my-bucket/logs/*.parquet')
    GROUP BY day
) TO 's3://my-bucket/analytics/daily_counts.parquet' (FORMAT PARQUET);
```

> **Critical:** `URL_STYLE 'path'` is REQUIRED. Without it, DuckDB uses virtual-hosted style and fails with "Could not resolve hostname."

### 6.3 rclone (Bidirectional Sync)

```ini
# ~/.config/rclone/rclone.conf

# Source: existing AWS S3 bucket
[aws]
type = s3
provider = AWS
access_key_id = AKIA...
secret_access_key = ...
region = us-east-1

# Destination: Hugging Face Storage Bucket
[hf]
type = s3
provider = Other
endpoint = https://s3.hf.co/your-username
access_key_id = HFAK...
secret_access_key = ...
region = us-east-1
force_path_style = true
list_version = 2
upload_cutoff = 2G
chunk_size = 2G
```

Usage:
```bash
# One-way copy (incremental)
rclone copy aws:my-source-bucket hf:my-bucket --progress

# Two-way sync (make destination an exact mirror)
rclone sync aws:my-source-bucket hf:my-bucket --progress

# High-concurrency import
rclone copy aws:my-source-bucket hf:my-bucket --transfers 16 --checkers 16 --progress

# Verify
rclone check aws:my-source-bucket hf:my-bucket
```

**Why each setting matters:**
- `force_path_style = true` → path-style addressing (required)
- `list_version = 2` → forces ListObjectsV2 (V1 not supported)
- `upload_cutoff = 2G, chunk_size = 2G` → fewer multipart parts

### 6.4 DVC (Data Version Control)

```bash
# Install with S3 support
pip install 'dvc[s3]'

# Add remote
dvc remote add -d hf-bucket s3://my-bucket/dvc-store
dvc remote modify hf-bucket endpointurl https://s3.hf.co/your-username
dvc remote modify hf-bucket region us-east-1

# Set credentials (locally, out of git)
dvc remote modify hf-bucket --local access_key_id HFAK...
dvc remote modify hf-bucket --local secret_access_key ...

# Or via environment
export AWS_ACCESS_KEY_ID=HFAK...
export AWS_SECRET_ACCESS_KEY=...

# Usage
dvc add data/
git add data.dvc .gitignore .dvc/config && git commit -m "Track data with DVC"
dvc push                                   # uploads to bucket
dvc pull                                   # downloads on fresh clone
```

> **Note:** Use your namespace in `endpointurl` and the bare bucket name in `s3://` URL.

### 6.5 s5cmd (Fast Parallel Transfers)

```bash
# Configure via environment
export AWS_ACCESS_KEY_ID=HFAK...
export AWS_SECRET_ACCESS_KEY=...
export AWS_ENDPOINT_URL=https://s3.hf.co/your-username
export AWS_REGION=us-east-1

# Upload directory (uses concurrency)
s5cmd cp --show-progress ./local-data/* s3://my-bucket/data/

# Download
s5cmd cp s3://my-bucket/models/model.safetensors .

# Sync
s5cmd sync ./data/ s3://my-bucket/data/

# List
s5cmd ls s3://my-bucket/
```

### 6.6 curl (Raw HTTP)

```bash
# List buckets
curl -H "Authorization: AWS4-HMAC-SHA256 Credential=HFAK.../..." \
  "https://s3.hf.co/your-username/"

# Get object (follows 302 redirect automatically with -L)
curl -L -H "Authorization: AWS4-HMAC-SHA256 Credential=HFAK.../..." \
  "https://s3.hf.co/your-username/my-bucket/object.txt"

# Put object
curl -X PUT -T file.bin \
  -H "Authorization: AWS4-HMAC-SHA256 Credential=HFAK.../..." \
  "https://s3.hf.co/your-username/my-bucket/file.bin"
```

> Note: curl receives a 302 redirect for GetObject and follows it with `-L`. For PutObject, data goes through the gateway.

---

## 7. Practical Zero-Cost Patterns

| Pattern | Tool | Cost |
|---------|------|------|
| Upload checkpoints from training | boto3, aws CLI | Free (HF storage quota) |
| Query log Parquet files | DuckDB | Free (compute is local) |
| Sync from AWS S3 (free tier) → HF | rclone | Source egress may apply |
| DVC data store for ML projects | DVC + boto3 | Free (HF storage quota) |
| Agent scratch space via S3 API | boto3, s5cmd | Free (HF storage quota) |

### Key Insights for Zero-Cost Usage

1. **No egress on reads** — unlike AWS S3, reading data from HF Storage Buckets onto GPU instances is free, regardless of cloud vendor
2. **No versioning overhead** — files overwrite in place, so you don't pay for deleted versions
3. **No super-squash needed** — Storage Buckets aren't Git repos, so no history to clean
4. **Server-side copy is free** — copying between HF repos/buckets avoids download/re-upload
5. **Free tier quota** — check https://huggingface.co/settings/billing for current limits

---

## 8. Security Considerations

| Concern | Mitigation |
|---------|-----------|
| S3 credential secret shown once | Regenerate from parent token if lost |
| Token scoping | Use fine-grained tokens scoped to specific namespaces/buckets |
| No IAM policies | HF token permissions ARE the access control |
| Cross-namespace restriction | Server-side copy limited to same namespace — good isolation property |
| Single-region gateway | CDN caches at edge for fast reads; writes go through us-east-1 |
| Object metadata not stored | No risk of accidentally exposing metadata that shouldn't be there |

---

## Key Takeaways

1. **The S3 gateway is an adapter, not a reimplementation** — it provides enough S3 compatibility to use existing tools, but intentionally omits features that don't map to HF Bucket semantics (versioning, ACLs, policies, lifecycle).

2. **Client configuration is the hardest part** — once you get the five required settings right (endpoint_url, region, path addressing, checksum settings), everything else works like standard S3.

3. **Namespace addressing is the main UX friction** — the namespace/bucket hierarchy doesn't map cleanly to S3's flat bucket namespace. Use Strategy 1 (namespace in endpoint URL) for 90% of use cases.

4. **Checksum settings are critical for modern clients** — AWS CLI ≥ 2.23 and recent boto3 send trailing CRC32 checksums by default that the gateway doesn't parse. Set `request_checksum_calculation = when_required`.

5. **Tool coverage is excellent** — boto3, DuckDB, rclone, DVC, s5cmd, and curl all work. The only tool that notably doesn't work without a workaround is older software that only supports ListObjectsV1.

### Skill
hf-hub-storage-buckets-s3-compatibility — Hugging Face Storage Buckets S3-Compatible API deep reference: credential generation via HF tokens, client configuration (AWS CLI, boto3, DuckDB httpfs, rclone, DVC, s5cmd, curl), addressing strategies, limitations vs AWS S3, security model, and zero-cost integration patterns.
