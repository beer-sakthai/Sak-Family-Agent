# HF Learnings — GitHub Actions & Trusted Publishers Deep Dive

## 2026-07-26: hf-hub-github-actions-trusted-publishers — GitHub Actions Integration, hub-sync Action, OIDC Keyless Publishing (Topic #402)

### Summary
Comprehensive deep-dive into Hugging Face Hub's GitHub Actions integration covering the `huggingface/hub-sync` action parameters and behavior, Trusted Publishers (OIDC-based keyless auth) architecture including token exchange flow, security model, multi-provider support (GitHub, GitLab, CircleCI, Bitbucket), and advanced patterns for CI/CD pipelines.

### Sources
- https://huggingface.co/docs/hub/en/repositories-github-actions
- https://huggingface.co/docs/hub/en/trusted-publishers
- https://github.com/huggingface/hub-sync (action repo)
- https://huggingface.co/docs/huggingface_hub/en/guides/upload

---

### Key Findings

#### 1. hub-sync Action Internals

The `huggingface/hub-sync@v0.1.0` action uses the HF CLI under the hood — it is **not** a git-to-git sync. It copies files from the GitHub checkout to the Hub repo using `huggingface-cli upload`.

**Behavior:**
- Automatically excludes `.github/` directories from the sync
- **Mirrors deletions** — files removed from the GitHub repo are also removed from the Hub repo
- Creates the target repo automatically if it doesn't exist (controlled by `private` parameter)
- For Spaces: respects the `space_sdk` parameter to set up the right SDK scaffolding

**Limitations:**
- Monorepo support requires the `subdirectory` parameter — there's no git-filter-tree equivalent
- LFS files in Spaces have size limits (same as direct upload — 50GB for Docker, 5GB for others)
- No built-in conflict resolution — the last push wins

#### 2. Trusted Publishers OIDC Flow

The OIDC token exchange follows **RFC 8693** (OAuth 2.0 Token Exchange):

```
┌─────────────┐     OIDC ID Token      ┌──────────────┐
│  CI Runner   │ ──────────────────────→ │  hf.co/oauth/ │
│  (GitHub,    │    + resource claim     │  token       │
│   GitLab,…)  │ ←──────────────────────│              │
│              │   Short-lived HF Token  │              │
└─────────────┘                         └──────────────┘
```

| Step | Detail |
|------|--------|
| 1 | CI provider mints OIDC JWT describing the job |
| 2 | Workflow presents JWT + `resource` (repo_id or username) |
| 3 | Hub validates signature, checks claims against configured publishers |
| 4 | Returns `access_token`, `token_type: Bearer`, `expires_in: 3600` |

**Token lifetime:** Exactly 60 minutes from exchange time — not from workflow start time. For long-running jobs, the token must be re-exchanged mid-run.

#### 3. Two Flavors of Publishers

| Flavor | Configured On | Scope | Use Case |
|--------|---------------|-------|----------|
| **Repo publisher** | Repo → Settings → Trusted Publishers | Write access to that one repo | Publishing models, datasets, Spaces from CI |
| **User publisher** | Account → Authentication → CI/CD Access | Read-only, gated-repos scope | Downloading gated models from CI, using account rate limits |

**User publisher limitations:** Cannot write anything, cannot read your private repos. Token attribution shows the synthetic system user with a reference to the originating issuer and subject.

#### 4. Multi-Provider OIDC Support

| Provider | ID Token Retrieval | Audience |
|----------|-------------------|----------|
| GitHub Actions | `permissions: id-token: write` → metadata endpoint | `https://huggingface.co` |
| GitLab CI | `id_tokens: { HF_ID_TOKEN: { aud: https://huggingface.co } }` | Set in YAML |
| CircleCI | `$CIRCLE_OIDC_TOKEN_V2` | Set in project settings |
| Bitbucket Pipelines | `$BITBUCKET_STEP_OIDC_TOKEN` | `oidc: true` on step |
| Any OIDC provider | Mint your own JWT → `HF_OIDC_ID_TOKEN` | `https://huggingface.co` |

The CLI (`huggingface_hub>=0.26.0`) detects GitHub Actions natively. For other providers, pass the ID token via `HF_OIDC_ID_TOKEN` environment variable.

#### 5. Token Exchange API Details

```
POST https://huggingface.co/oauth/token
Content-Type: application/json

{
  "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
  "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
  "subject_token": "<raw JWT>",
  "resource": "namespace/repo-name"  // or just "username" for user-scoped
}
```

**Error codes:**
- `invalid_request` (400) — missing/malformed parameter, or bad `resource` format
- `invalid_grant` (400) — repo/user not found; no matching publisher; claims don't match; signature failure; account locked

Hub returns a `request_id` in error responses for traceability.

#### 6. Security Model

- **Exact claim matching** — no regex, no prefix matching. The configured repo, workflow file, and branch must match exactly
- **Short-lived tokens** — 60 minutes, no refresh token
- **Repo-scoped** — cannot touch other repos
- **Audit logs** — adding/removing a publisher is logged; successful exchanges update "last used" timestamp
- **No client authentication** — the OIDC ID token itself authenticates the request
- **System user attribution** — pushes are attributed to a synthetic user, not the publisher's account

#### 7. Practical Patterns

**Monorepo pattern:** Use `subdirectory` parameter on `hub-sync` to sync only a specific subfolder:

```yaml
- uses: huggingface/hub-sync@v0.1.0
  with:
    subdirectory: spaces/my-demo
    repo_type: space
    space_sdk: gradio
```

**Multi-repo publish:** Set `HF_OIDC_RESOURCE` per step for different repos:

```yaml
- run: huggingface-cli upload my-org/model . --repo-type model
  env:
    HF_OIDC_RESOURCE: my-org/model
- run: huggingface-cli upload my-org/dataset . --repo-type dataset
  env:
    HF_OIDC_RESOURCE: my-org/dataset
```

**Gated repo access from CI:** Use user-scoped publisher + `HF_OIDC_RESOURCE=your-username`, then any `huggingface-cli download` call uses the exchanged token automatically.

#### 8. Comparison: hub-sync vs Custom Upload

| Aspect | hub-sync Action | Custom Python/CLI |
|--------|----------------|-------------------|
| Setup | 5 lines in workflow | More verbose |
| File mirroring | Automatic (incl. deletions) | Manual |
| Monorepo | `subdirectory` param | Any path logic |
| Build steps | Separate job/step | Full flexibility |
| LFS handling | Automatic for Spaces | Manual |
| Deletion sync | ✅ Yes | ❌ No |

### Resources
- GitHub Actions docs: https://huggingface.co/docs/hub/en/repositories-github-actions
- Trusted Publishers docs: https://huggingface.co/docs/hub/en/trusted-publishers
- hub-sync action: https://github.com/huggingface/hub-sync
- HF CLI upload: https://huggingface.co/docs/huggingface_hub/en/guides/upload
- OIDC token exchange (RFC 8693): https://datatracker.ietf.org/doc/html/rfc8693
