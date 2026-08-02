---
name: SakThai-hf-hub-repo-settings
author: SakThai
license: MIT
title: HF Hub Repo Settings, Visibility & Tags Management
category: mlops
tags: [hub, repo-settings, visibility, gated, tags, collections, api]
description: Manage repository settings, visibility, gated access, tags, and metadata on the Hugging Face Hub through the huggingface_hub Python API.
version: 1.0.0
---

# HF Hub Repo Settings, Visibility & Tags Management

Manage repository settings, visibility, gated access, tags, and metadata on the Hugging Face Hub through the `huggingface_hub` Python API.

## Overview

The Hugging Face Hub provides a comprehensive REST API and Python library for managing repository settings beyond just uploading files. This skill covers:

- **Visibility management**: public, private, protected (Spaces only)
- **Gated access**: auto, manual, disabled
- **Tag management**: creating, deleting, and discovering tags
- **Collection metadata**: updating title, description, theme, privacy
- **Reading settings back**: using `repo_info` with `expand` parameter

## Key APIs

### `update_repo_settings`
The primary API for changing repo visibility and gated access status.

### `create_tag` / `delete_tag`
Git-style tagging for commits on the Hub.

### `get_model_tags` / `get_dataset_tags`
Discover valid tags for classification.

### `update_collection_metadata`
Modify collection appearance and access settings.

### `repo_info` with `expand`
Read comprehensive repo metadata including settings.

## Author

- **author**: SakThai
- **license**: MIT
