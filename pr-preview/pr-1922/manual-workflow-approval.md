# Manual Workflow Approval Guide

**Status:** Adopted  
**Action:** [`trstringer/manual-approval`](https://github.com/trstringer/manual-approval)  
**Pinned Commit SHA:** `fa642940caf8412403569b28b2db4a1df08a83a3` (`# v1.13.1`)  
**Scope:** GitHub Actions workflows requiring human-in-the-loop verification

---

## 1. Overview and Household Alignment

In the House of Sak ecosystem, irreversible operations—such as publishing models/datasets to Hugging Face Hub, spending money ($0.00 spend invariant), publishing releases, or applying high-privilege configuration changes—must not run fully autonomously without Beer's explicit approval.

The `trstringer/manual-approval` action implements this human-in-the-loop safety boundary in GitHub Actions:
1. It pauses workflow execution at the approval step.
2. It opens a dedicated GitHub issue assigned to authorized approvers (`beer-sakthai`).
3. It polls the issue status until an authorized user comments `approved` (or closes the issue to reject/cancel).
4. Upon approval, the workflow resumes downstream sensitive steps.

---

## 2. Standard Installation Snippet

In accordance with OpenSSF Scorecard supply-chain security standards and repository invariants, third-party actions **must be pinned by immutable commit SHA** rather than floating tags.

### Step-level snippet:

```yaml
- name: Manual Workflow Approval
  uses: trstringer/manual-approval@fa642940caf8412403569b28b2db4a1df08a83a3 # v1.13.1
  with:
    secret: ${{ github.token }}
    approvers: beer-sakthai
    minimum-approvals: 1
    issue-title: "Manual Approval Required: ${{ github.workflow }} #${{ github.run_number }}"
    issue-body: "Approval requested by @${{ github.actor }} for run ${{ github.run_id }}."
```

---

## 3. Security, Token Permissions & Network Egress

### 3.1 Permissions Mapping
The action creates and manages issues, requiring `issues: write` at the job or workflow level:

```yaml
permissions:
  contents: read
  issues: write
```

Scalar permission declarations (such as `permissions: write-all`) are rejected by repository linting (`scripts/lint_workflow_permissions.py`). Always use explicit mapping form.

### 3.2 StepSecurity Harden-Runner
Every job executing third-party actions must first harden the runner against network exfiltration and tampering:

```yaml
- name: Harden the runner
  uses: step-security/harden-runner@1d88384fd173af6ecb012dfd0264a306b711241a # v2.22.4
  with:
    use-policy-store: true
    api-key: ${{ secrets.STEP_SECURITY_API_KEY }}
```

---

## 4. Workflows Implementing Manual Approval

1. **[`manual.yml`](../.github/workflows/manual.yml)**:
   - Includes an optional `require_approval: true/false` dispatch input.
   - When set to `true`, halts at the `approval-gate` job before executing the downstream `greet` job.

2. **[`reusable-manual-approval-gate.yml`](../.github/workflows/reusable-manual-approval-gate.yml)**:
   - A modular `workflow_call` workflow that other workflows can invoke as a reusable gating job.

### Example Caller Pattern:

```yaml
jobs:
  preflight:
    runs-on: ubuntu-latest
    steps: [...]

  gate:
    needs: [preflight]
    uses: ./.github/workflows/reusable-manual-approval-gate.yml
    with:
      gate_name: "Hugging Face Model Card Publication"
      approvers: "beer-sakthai"
      timeout_minutes: 60

  publish:
    needs: [gate]
    runs-on: ubuntu-latest
    steps: [...]
```
