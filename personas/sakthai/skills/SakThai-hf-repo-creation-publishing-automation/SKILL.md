---
name: SakThai-hf-repo-creation-publishing-automation
description: "Complete reference for programmatic repository lifecycle management on Hugging Face\
  \ Hub \u2014 creation, configuration, file operations, metadata, CI/CD publishing\
  \ automation"
---

# HF Repo Creation & Publishing Automation

Trigger when: user asks about creating repos on Hugging Face Hub, publishing models/datasets/Spaces programmatically, automating uploads in CI/CD, or managing repo lifecycle (create, delete, move, duplicate, squash history).

## Key Areas

- **Repository CRUD**: create_repo, delete_repo, duplicate_repo, move_repo, super_squash_history
- **Repo metadata**: repo_info, repo_exists, update_repo_settings, list_repo_files, list_repo_commits
- **File operations**: upload_file, upload_folder, create_commit, CommitOperationAdd/Delete/Copy
- **CLI equivalents**: `hf repos create`, `hf repos delete`, `hf repos duplicate`, `hf repos move`, `hf repos settings`, `hf repos cp`
- **CI/CD automation**: headless publishing, GitHub Actions with HF_TOKEN, commit patterns, optimistic locking
- **Repo types**: models, datasets, Spaces (with SDK, hardware, secrets, volumes)

See `references/hf-learnings.md` for the complete deep-dive reference.
