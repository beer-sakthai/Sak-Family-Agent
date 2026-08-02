---
name: SakThai-hf-pull-requests-discussions
description: ">   Complete reference on Hugging Face Hub Pull Requests and Discussions API —   covering the full lifecycle: creating discussions and PRs, listing, filtering,   commenting, editing, hiding, status changes, merging, renaming, and the git   ref model "
---

# HF Hub Pull Requests & Discussions API

## What This Covers

All aspects of the Hugging Face Hub's PR and Discussion system:

| Topic | Description |
|-------|-------------|
| **Architecture** | PR storage model (custom git refs), no-forks model |
| **Python SDK** | Full `HfApi` method reference with signatures |
| **CLI** | `huggingface-cli discussions` commands |
| **Lifecycle** | Create → comment → edit → merge/close → delete ref |
| **Filtering** | By type (PR vs discussion), status (open/closed), author |
| **Draft Mode** | Programmatic PRs start as draft, publish to open |
| **Git Workflow** | Fetch PR refs locally, push changes, merge |

## Related References

- `hf-learnings.md` in this directory
- Hub docs: https://huggingface.co/docs/hub/en/repositories-pull-requests-discussions
- Python API: `huggingface_hub.HfApi` methods
