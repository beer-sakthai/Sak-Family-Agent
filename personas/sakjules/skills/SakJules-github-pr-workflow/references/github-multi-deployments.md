# GitHub Multi Deployments (`maxgfr/github-multi-deployments`) Reference

> **Persona Domain:** SakJules · Master of Automation & CI/CD  
> **Source Action:** [`maxgfr/github-multi-deployments`](https://github.com/marketplace/actions/github-multi-deployments)  
> **Pinned SHA:** `ed720d528c8e44c33cca444d1b5375a866ec724c` (`v1.8.11`)

---

## 1. Overview & Purpose

`maxgfr/github-multi-deployments` is a TypeScript-based GitHub Action built as a performant, resilient evolution of `bobheadxi/deployments`. It manages the entire lifecycle of GitHub Deployments and deployment statuses for both single and multiple environments within a single workflow step.

In the House of Sak automation ecosystem, this action provides:
1. **Multi-target deployment updates** — Updating staging, production, or multi-cloud endpoints in a single atomic workflow step.
2. **Ephemeral PR preview environment tracking** — Creating transient environments per pull request (`pr-<number>`) and automatically deactivating them upon PR merge or close.
3. **Robust rate-limit resilience** — Automatic pagination for repositories with high deployment volumes and exponential backoff retry on 429/5xx errors without duplicate deployment creation.

---

## 2. Token & Permission Requirements

| Step | Required Token | Required Scopes / Permissions |
| :--- | :--- | :--- |
| `start` | `GITHUB_TOKEN` | `deployments: write`, `contents: read` |
| `finish` | `GITHUB_TOKEN` | `deployments: write`, `contents: read` |
| `deactivate-env` | `GITHUB_TOKEN` | `deployments: write` |
| `get-env` | `GITHUB_TOKEN` | `deployments: read` |
| `delete-env` | Personal Access Token (PAT) | `repo` scope (GitHub REST API limitation) |

> **Security Note:** In House of Sak workflows, `GITHUB_TOKEN` is always preferred for `start`, `finish`, and `deactivate-env`. Personal Access Tokens are restricted and never checked into source control.

---

## 3. Workflow Steps & Parameters

### Step Types (`step:`)
- **`start`**: Registers a new deployment in GitHub with status `in_progress` (or `pending`).
- **`finish`**: Updates an existing deployment with conclusion status (`success`, `failure`, `inactive`, etc.) and attaches public `env_url`.
- **`deactivate-env`**: Marks previous deployments for the specified environment as inactive.
- **`delete-env`**: Permanently deletes an environment (requires PAT).
- **`get-env`**: Fetches environment deployment details for a specific git ref.

### Core Inputs

| Input | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `token` | string | `${{ github.token }}` | GitHub token with deployment write permissions. |
| `step` | string | `start` | Lifecycle step to execute. |
| `env` | string / JSON array | — | Environment name (`"production"`) or list (`'["staging", "production"]'`). |
| `env_url` | string / JSON array | — | Public URL(s) for the deployment (`finish` only). |
| `deployment_id` | string / JSON array | — | Deployment ID(s) to finalize (`finish` only). |
| `status` | string | `success` | Status: `success`, `failure`, `cancelled`, `error`, `inactive`. |
| `auto_inactive` | boolean | `false` | Instructs GitHub to auto-deactivate previous deployments. |
| `transient_environment` | boolean | `true` | Marks environment as temporary (set `false` for permanent prod). |
| `production_environment` | boolean | `false` | Designates production status in GitHub UI. |
| `dry_run` | boolean | `false` | Simulates execution without calling GitHub REST API. |

---

## 4. House of Sak Integration Architecture

### A. Reusable Deployment Workflow (`.github/workflows/reusable-deployment.yml`)
The centralized reusable deployment workflow supports multi-target recording with automatic engine fallback:

```yaml
- name: Manage Multi Deployments
  uses: maxgfr/github-multi-deployments@ed720d528c8e44c33cca444d1b5375a866ec724c # v1.8.11
  with:
    step: ${{ inputs.step }}
    token: ${{ secrets.GITHUB_TOKEN }}
    env: ${{ inputs.environment }}
    env_url: ${{ inputs.environment_url }}
    deployment_id: ${{ inputs.deployment_id }}
    status: ${{ inputs.status }}
```

### B. Ephemeral PR Preview Deployment (`.github/workflows/reusable-pr-deploy.yml`)
Tracks container preview environments throughout the pull request lifecycle:

1. **On PR Open/Synchronize:**
   - Registers deployment for `pr-${{ github.event.number }}` with `transient_environment: 'true'`.
   - Provisions isolated preview container via `hngprojects/pr-deploy`.
   - Records final status and links to `https://pr-<number>.preview.houseofsak.app`.
2. **On PR Close / Merge:**
   - Invokes `step: deactivate-env` to mark the preview environment as inactive cleanly.

---

## 5. Security & Invariant Standards

1. **Immutable Commit Pinning:** Always pin `maxgfr/github-multi-deployments` to its 40-character commit SHA (`ed720d528c8e44c33cca444d1b5375a866ec724c`).
2. **StepSecurity Harden-Runner:** Precede all deployment steps with `step-security/harden-runner` in `audit` mode.
3. **Explicit Permissions:** Scope `deployments: write` and `contents: read` at the job level. Never use root-level `write-all`.
4. **Always Finalize:** Always attach `if: always()` to the `finish` step so failed or cancelled workflows properly update the GitHub deployment state to `failure` rather than hanging in `in_progress`.
