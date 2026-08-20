---
name: SakThai-hf-hub-github-actions
author: SakThai
license: MIT
description: Hugging Face Hub GitHub Actions integration — sync repos, Trusted Publishers (OIDC keyless auth), hub-sync action parameters, Spaces CI/CD, and custom workflow patterns
category: mlops
version: 1.0.0
---

# HF Hub GitHub Actions & Trusted Publishers

Trigger when: user asks about syncing GitHub repos to HF Hub, CI/CD for models/datasets/Spaces, Trusted Publishers, OIDC keyless publishing, `hub-sync` action, or automating Hub updates from GitHub Actions.

## Overview

Two complementary mechanisms for pushing content from GitHub Actions to the Hugging Face Hub:

1. **`huggingface/hub-sync` action** — simple file mirroring with an `HF_TOKEN` secret
2. **Trusted Publishers** — OIDC-based keyless auth; no token to store or rotate

Both support syncing **Models**, **Datasets**, and **Spaces**.

---

## 1. Basic GitHub Actions Sync (hub-sync)

### Setup

1. Create a Hugging Face [access token](https://huggingface.co/settings/tokens) with **write** permission to the target repo. Use a fine-grained token scoped to only that repo for better security.
2. Add the token as a GitHub secret called `HF_TOKEN` in your repo settings.
3. Add a workflow file (e.g., `.github/workflows/sync-to-hub.yml`).

### Basic Usage

```yaml
name: Sync to Hugging Face Hub
on:
  push:
    branches: [main]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: huggingface/hub-sync@v0.1.0
        with:
          github_repo_id: ${{ github.repository }}
          huggingface_repo_id: username/repo-name
          hf_token: ${{ secrets.HF_TOKEN }}
```

### Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `github_repo_id` | ✅ | — | GitHub repo (`${{ github.repository }}`) |
| `huggingface_repo_id` | ✅ | — | Target repo on Hub (`username/repo-name`) |
| `hf_token` | ✅ | — | HF access token |
| `repo_type` | ❌ | `space` | `model`, `dataset`, or `space` |
| `space_sdk` | ❌ | `gradio` | For Spaces: `gradio`, `streamlit`, `docker`, `static` |
| `private` | ❌ | `false` | Create the repo as private |
| `subdirectory` | ❌ | — | Sync a subdirectory (useful for monorepos) |

**Notes:**
- Mirrors files using the HF CLI — not git-to-git sync
- Automatically excludes `.github/` directories
- Mirrors deletions (files removed from GitHub are removed from Hub)
- For Spaces: respects file size limits and LFS handling

---

## 2. Trusted Publishers (OIDC Keyless Auth)

Trusted Publishers eliminate the need to store an `HF_TOKEN` secret. Your CI job proves its identity using a short-lived OIDC token, and gets a short-lived HF token in exchange.

### Comparison

| Aspect | `HF_TOKEN` Secret | Trusted Publisher |
|--------|------------------|-------------------|
| Secret storage | Required | Nothing to store |
| Rotation | Manual | Automatic, every run |
| Lifetime | Until revoked | ≤60 minutes |
| Scope | User-defined | Per-repo or per-user |

### How It Works

1. Your CI provider mints an OIDC ID token describing the job (repo, branch, workflow)
2. Your workflow presents it to `https://huggingface.co/oauth/token`
3. Hub checks the token's signature and claims against configured publishers
4. Returns a short-lived (60 min) HF token

### Setup: GitHub Actions

1. **On the Hub**: Go to target repo → Settings → Trusted Publishers → Add publisher
   - Provider: GitHub Actions
   - Repository: `owner/repo` (must match exactly)
   - Optionally pin to a workflow file or branch

2. **In your workflow**: No `HF_TOKEN` needed. The `huggingface_hub` CLI (≥0.26.0) detects the provider automatically:

```yaml
name: Publish to Hub (keyless)
on:
  push:
    branches: [main]

permissions:
  id-token: write  # needed for OIDC

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install huggingface_hub
      - run: huggingface-cli upload my-org/my-model . --repo-type model
        env:
          HF_OIDC_RESOURCE: my-org/my-model
```

### Multi-Repo Publishing

Publishing to several repos in one run? Set `HF_OIDC_RESOURCE` per step:

```yaml
- run: huggingface-cli upload my-org/my-model . --repo-type model
  env:
    HF_OIDC_RESOURCE: my-org/my-model
- run: huggingface-cli upload my-org/my-dataset . --repo-type dataset
  env:
    HF_OIDC_RESOURCE: my-org/my-dataset
```

### User-Scoped Publishers (for gated repos)

For accessing gated repos from CI (read-only), configure a publisher on your **account**:

Settings → Authentication → CI/CD Access → Add publisher

Then use your username as the resource:

```yaml
env:
  HF_OIDC_RESOURCE: your-username
```

The resulting token:
- Can read gated repos you have access to
- Uses your account's rate limits
- Cannot write anything
- Cannot read your private repos

### Other CI Providers

| Provider | ID Token Source | Audience |
|----------|----------------|----------|
| GitLab CI | `id_tokens: { HF_ID_TOKEN: { aud: https://huggingface.co } }` | `$HF_ID_TOKEN` |
| CircleCI | `$CIRCLE_OIDC_TOKEN_V2` | Set audience in project settings |
| Bitbucket | `$BITBUCKET_STEP_OIDC_TOKEN` | `oidc: true` on step |

---

## 3. Advanced Patterns

### Sync a Subdirectory (Monorepo)

```yaml
- uses: huggingface/hub-sync@v0.1.0
  with:
    github_repo_id: ${{ github.repository }}
    huggingface_repo_id: username/my-space
    hf_token: ${{ secrets.HF_TOKEN }}
    subdirectory: spaces/my-space
    repo_type: space
    space_sdk: gradio
```

### Custom Upload with Python

For build steps or custom logic:

```yaml
- run: |
    pip install huggingface_hub
    python -c "
    from huggingface_hub import HfApi
    api = HfApi(token='${{ secrets.HF_TOKEN }}')
    api.upload_folder(
        folder_path='dist/',
        repo_id='username/my-model',
        repo_type='model',
    )
    "
```

### Trigger on Release

```yaml
on:
  release:
    types: [published]
```

### Scheduled Sync

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # daily at 6 AM UTC
```

---

## 4. Trusted Publishers API Reference

**Endpoint:** `POST https://huggingface.co/oauth/token`

**Request:**
```json
{
  "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
  "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
  "subject_token": "<OIDC_JWT>",
  "resource": "namespace/repo-name"
}
```

**Success Response:** Standard OAuth token response with `access_token`, `token_type`, `expires_in`.

**Error Response:** `400 Bad Request` with OAuth-style body:
- `invalid_request` — missing/malformed parameter
- `invalid_grant` — repo/user not found; no matching publisher; claims don't match

**Security Model:**
- Tokens expire after 60 minutes from exchange (not from workflow start)
- No refresh token — long jobs should re-exchange
- Repo tokens are repo-scoped (can't touch other repos)
- Pushes attributed to a synthetic system user
- Claims matched exactly (no regex or prefix matching)
- Adding/removing a publisher is audit-logged

---

## Pitfalls

- **`id-token: write`** permission is required for OIDC in GitHub Actions — without it, the token exchange fails silently
- **Claims are matched exactly** — if your workflow file is `.github/workflows/publish.yml`, configure it exactly that way
- **Trusted Publishers are per-repo** — each repo you push to needs its own publisher config (or use user-scoped for read-only)
- **60-minute token expiry** — long training jobs must re-exchange mid-run
- **`hub-sync` mirrors deletions** — files removed from GitHub are removed from Hub; use `subdirectory` to limit scope
- **`hub-sync` is not git-to-git** — it uses HF CLI under the hood, not git operations
