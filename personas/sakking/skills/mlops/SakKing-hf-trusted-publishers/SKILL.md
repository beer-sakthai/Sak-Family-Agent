---
name: SakKing-hf-trusted-publishers
description: "Hugging Face Trusted Publishers: OIDC-based CI/CD authentication that exchanges short-lived CI tokens for temporary Hub access tokens, enabling keyless publishing from GitHub Actions, GitLab CI, CircleCI, Bitbucket, and other providers."
version: 1.0.0
author: SakThai
license: MIT
tags: [huggingface, ci-cd, oidc, trusted-publishers, github-actions, gitlab, authentication]
platforms: [linux, macos, windows]
---

# Hugging Face Trusted Publishers

Push to the Hub from CI **without storing a long-lived `HF_TOKEN` secret**.

Trusted Publishers use **OpenID Connect (OIDC)** to prove a CI job's identity, then exchange that proof for a short-lived Hugging Face token (valid ~60 minutes) via RFC 8693 token exchange.

## Core Concept

| | Personal Access Token | Trusted Publisher |
|---|---|---|
| **Lifetime** | Until revoked | 1 hour |
| **Storage** | CI secret | Nothing to store |
| **Rotation** | Manual | Automatic every run |
| **Blast radius** | Valid until revoked | At most ~1 hour, repo-scoped |

## Two Flavors

### 1. Repo Publisher (write access)
- Configured on a repo's **Settings → Trusted Publishers**.
- Returns a token with **write access to that single repo** only.
- Use it to publish model checkpoints, datasets, Spaces, or kernels from CI.

### 2. User Publisher (read gated repos)
- Configured on your **account Authentication settings → CI/CD Access**.
- Returns a **read-only** token with the `gated-repos` scope.
- Use it to download gated models or datasets from CI jobs.

## Supported CI Providers

| Provider | Issuer | How to get the ID token |
|---|---|---|
| **GitHub Actions** | `https://token.actions.githubusercontent.com` | Set `permissions: id-token: write`, then call the metadata endpoint with `audience=https://huggingface.co`. |
| **GitLab CI** | `https://gitlab.com` (or self-hosted) | Declare `id_tokens: { HF_ID_TOKEN: { aud: https://huggingface.co } }`. |
| **CircleCI** | `https://oidc.circleci.com/org/<org-UUID>` | Use `$CIRCLE_OIDC_TOKEN_V2`. |
| **Bitbucket Pipelines** | `https://api.bitbucket.org/2.0/workspaces/<workspace>/pipelines-config/identity/oidc` | Set `oidc: true` on the step; read `$BITBUCKET_STEP_OIDC_TOKEN`. |

Any OIDC-compliant provider (AWS, GCP, Buildkite, custom IdP) works — you only need to mint the ID token and pass it through.

## Hub-Side Configuration

1. Navigate to the target repo (or your account settings for user publishers).
2. Open **Trusted Publishers**.
3. Add a publisher:
   - **Provider**: select your CI provider.
   - **Claims** (all must match exactly for the exchange to succeed):
     - `repository` (e.g. `acme/awesome-model-training`)
     - `branch` (optional, e.g. `main`)
     - `workflow` (optional, e.g. `publish.yml`)
4. Save.

> [!TIP]
> `repository` alone scopes to a GitHub repo. Add `branch` and/or `workflow` to further restrict the publisher.

## GitHub Actions Example (Auto-Exchange)

With `huggingface_hub>=1.19.0`, the `hf` CLI auto-detects GitHub Actions and performs the exchange. Set `HF_OIDC_RESOURCE` to the target repo or your username.

```yaml
name: Publish to Hugging Face
on:
  push:
    branches: [main]

jobs:
  publish:
    runs-on: ubuntu-latest
    permissions:
      id-token: write   # required to request an OIDC token
      contents: read

    steps:
      - uses: actions/checkout@v4

      - name: Install hf CLI
        run: |
          curl -LsSf https://hf.co/cli/install.sh | bash
          echo "$HOME/.local/bin" >> "$GITHUB_PATH"

      - name: Upload checkpoint
        env:
          HF_OIDC_RESOURCE: acme/awesome-model
        run: hf upload acme/awesome-model ./checkpoint . --commit-message "Publish from ${GITHUB_SHA::7}"
```

> [!TIP]
> Publishing to several repos in one run (e.g. a model **and** a dataset)? Set `HF_OIDC_RESOURCE` per step so each token is scoped to the repo that step pushes to.

## Other CI Providers (Manual Exchange)

On GitLab, CircleCI, Bitbucket, or custom OIDC providers, mint the ID token yourself and pass it via `HF_OIDC_ID_TOKEN`. The exchange call is identical.

```yaml
# GitLab CI
publish:
  id_tokens:
    HF_ID_TOKEN:
      aud: https://huggingface.co
  script:
    - curl -LsSf https://hf.co/cli/install.sh | bash
    - export PATH="$HOME/.local/bin:$PATH"
    - HF_OIDC_ID_TOKEN="$HF_ID_TOKEN" HF_OIDC_RESOURCE="acme/awesome-model" hf upload acme/awesome-model ./checkpoint .
```

```bash
# CircleCI
HF_OIDC_ID_TOKEN="$CIRCLE_OIDC_TOKEN_V2" HF_OIDC_RESOURCE="acme/awesome-model" hf upload acme/awesome-model ./checkpoint .
```

## How It Works

1. Your CI provider mints a short-lived **OIDC ID token** describing the job (repo, branch, workflow, …).
2. Your workflow `POST`s that token to `https://huggingface.co/oauth/token`, along with a `resource` (the repo or username).
3. The Hub validates the token's signature and claims against your configured publishers, and returns a Hugging Face token.

```
┌──────────┐  1. mint ID token   ┌──────────┐  2. exchange   ┌────────────┐
│ CI job   │ ─────────────────▶  │ CI OIDC  │ ──────────────▶│ huggingface│
│          │                     │ issuer   │                │  /oauth/   │
│          │ ◀──────────────────────────────────────────────│  token     │
└──────────┘        3. short-lived HF token (valid 1 h)      └────────────┘
```

## Exchange API Reference (Raw)

**Endpoint:** `POST https://huggingface.co/oauth/token`  
**Content-Type:** `application/json`

No client authentication is needed — the OIDC ID token authenticates the request.

| Field | Required | Value |
|---|---|---|
| `grant_type` | Yes | `urn:ietf:params:oauth:grant-type:token-exchange` |
| `subject_token_type` | Yes | `urn:ietf:params:oauth:token-type:id_token` |
| `subject_token` | Yes | The raw OIDC ID token (JWT). Its `aud` claim **must** be `https://huggingface.co`. |
| `resource` | Yes | A Hub repo (`namespace/name`, `datasets/namespace/name`, `spaces/namespace/name`, `kernels/namespace/name`) or a Hub **username** (no slash) for a user-scoped token. |

**Success response:**
```json
{
  "access_token": "hf_jwt_…",
  "token_type": "bearer",
  "expires_in": 3600,
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token"
}
```

**Common errors:**
- `invalid_request`: Missing/malformed parameter or bad `resource` format.
- `invalid_grant`: Repo/user not found; no publisher matches this issuer; claims don't match; signature or audience check failed; account locked.

When the `hf` CLI fails, it surfaces the `error` code along with a `(Request ID: …)`. Include that Request ID when reporting issues.

## Security Model

- **Short-lived:** 60 minutes from the moment of exchange. No refresh token — long jobs should re-exchange.
- **Repo-scoped:** A token for `acme/awesome-model` cannot touch `acme/anything-else`. Pushes are attributed to a synthetic `[OIDC]` system user.
- **User-scoped tokens are read-only:** Only `gated-repos` scope. Cannot write, read private repos, or manage the account.
- **Claims are matched exactly:** No regex, no prefix matching. `repository`, `branch`, and `workflow` are literal.
- **Audit logging:** Adding or removing a publisher is logged; successful exchanges show last-used time.

## hub-sync GitHub Action

The official [`huggingface/hub-sync`](https://github.com/marketplace/actions/sync-github-to-hugging-face-hub) action mirrors GitHub files to the Hub using the `hf` CLI (not a git-to-git sync).

```yaml
- uses: huggingface/hub-sync@v0.1.0
  with:
    github_repo_id: ${{ github.repository }}
    huggingface_repo_id: username/repo-name
    hf_token: ${{ secrets.HF_TOKEN }}
```

Key parameters:

| Parameter | Required | Default | Description |
|---|---|---|---|
| `github_repo_id` | Yes | — | `${{ github.repository }}` |
| `huggingface_repo_id` | Yes | — | Target repo on the Hub |
| `hf_token` | Yes | — | HF access token (or leave empty for Trusted Publishers if the CLI handles it) |
| `repo_type` | No | `space` | `space`, `model`, or `dataset` |
| `space_sdk` | No | `gradio` | `gradio`, `streamlit`, `docker`, `static` |
| `private` | No | `false` | Whether to create the repo as private |
| `subdirectory` | No | `.` | Sync a specific subdirectory (monorepos) |

> [!NOTE]
> `hub-sync` automatically excludes `.github/` and `.git/` and mirrors deletions. For files >10 MB in Spaces, ensure Git-LFS is tracked in your GitHub repo before syncing.

## Common Pitfalls

1. **Forgot `id-token: write` permission** — GitHub Actions will not emit an OIDC token without this permission at the job level.
2. **Audience mismatch** — The OIDC token's `aud` claim must be exactly `https://huggingface.co`. If your CI provider cannot set the audience, the exchange will fail with `invalid_grant`.
3. **Claims are exact** — Typos in `repository`, `branch`, or `workflow` on the Hub settings page will silently reject valid CI runs.
4. **Long jobs exceed 60 minutes** — There is no refresh token; split the job or re-exchange manually inside long-running steps.
5. **Private repos with hub-sync** — Set `private: true` when syncing to a private Hub repo for the first time, or create the repo manually beforehand.

## When to Use What

- **GitHub Actions + short-lived tokens only**: Use Trusted Publishers. No `HF_TOKEN` secret needed.
- **GitHub Actions + need full API access (e.g. create repos, manage discussions)**: Use a fine-grained token stored as a secret.
- **Non-GitHub CI (GitLab, CircleCI, Bitbucket)**: Use Trusted Publishers; mint the ID token natively or via a helper, pass `HF_OIDC_ID_TOKEN` + `HF_OIDC_RESOURCE`.
- **One-off scripts from a developer laptop**: Use a standard PAT or fine-grained user token.

## Layout

```
SKILL.md
references/
  related-skills.md   # Sibling skill boundary matrix
```

## References

- **Hub docs**: https://huggingface.co/docs/hub/en/trusted-publishers
- **Hub docs (GitHub Actions)**: https://huggingface.co/docs/hub/en/repositories-github-actions
- **Hub docs (Spaces + GitHub Actions)**: https://huggingface.co/docs/hub/en/spaces-github-actions
- **OAuth RFC 8693**: https://www.rfc-editor.org/rfc/rfc8693.html
- **`huggingface_hub` CLI / SDK**: `huggingface_hub>=1.19.0` includes the OIDC exchange in the `hf` CLI.
