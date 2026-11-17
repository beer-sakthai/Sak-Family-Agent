# Pull Request Preview Deployment Guide

**Status:** Adopted  
**Action:** [`rossjrw/pr-preview-action`](https://github.com/rossjrw/pr-preview-action)  
**Pinned Commit SHA:** `873417d2df72380da1f3978378fb58560bcde976` (`# v1.8.2`)  
**Workflow:** [`.github/workflows/pr-preview.yml`](../.github/workflows/pr-preview.yml)  
**Scope:** Pull request previews for documentation and static dashboard assets

---

## 1. Overview

The Pull Request Preview workflow automatically deploys branch previews for changes affecting repository documentation and dashboard views (such as [`docs/index.html`](index.html)).

When a pull request touches documentation:
1. It deploys the preview assets from `./docs` into the `gh-pages` branch under `pr-preview/pr-<number>/`.
2. It comments on the pull request with a live preview link.
3. When the pull request is updated with new commits, it synchronizes the preview.
4. When the pull request is merged or closed, it automatically deletes the preview deployment.

---

## 2. Standard Installation Snippet

In accordance with OpenSSF Scorecard supply chain security invariants, all actions must be pinned to full 40-character commit SHAs:

```yaml
- name: Deploy Pull Request Preview
  uses: rossjrw/pr-preview-action@873417d2df72380da1f3978378fb58560bcde976 # v1.8.2
  with:
    source-dir: ./docs
    preview-branch: gh-pages
    umbrella-dir: pr-preview
    action: auto
```

---

## 3. Permissions & Security Configuration

### 3.1 Token Permissions
The preview action requires:
- `contents: write`: To commit and push preview artifacts to the `gh-pages` branch.
- `pull-requests: write`: To post and update the preview status comment on the PR.

```yaml
permissions:
  contents: write
  pull-requests: write
```

### 3.2 StepSecurity Harden-Runner
Every runner instance must execute Harden-Runner before invoking third-party actions:

```yaml
- name: Harden the runner
  uses: step-security/harden-runner@1d88384fd173af6ecb012dfd0264a306b711241a # v2.22.4
  with:
    use-policy-store: true
    api-key: ${{ secrets.STEP_SECURITY_API_KEY }}
```

---

## 4. Lifecycle Behavior

| PR Event | Action Behavior | Outcome |
|---|---|---|
| **opened / reopened** | Deploys `./docs` to `gh-pages/pr-preview/pr-<id>` | Adds preview comment on PR with live URL |
| **synchronize** | Updates existing preview folder | Overwrites preview deployment with latest commits |
| **closed** | Cleans up `gh-pages/pr-preview/pr-<id>` | Deletes preview files and marks PR comment closed |
