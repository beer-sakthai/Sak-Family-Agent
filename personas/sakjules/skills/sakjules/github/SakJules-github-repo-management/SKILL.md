---
name: SakJules-github-repo-management
description: "GitHub repo management: invite, protect, archive, restrict push, rename, delete, transfer ownership, and settings."
version: 1.0.0
platforms: [lnux, macos, windows]
metadata:
  hermes:
    tags: [github, repo, management, ownership, protect, archive, rename, delete, invite, settings]
    related_skills: [github-repo-roles, github-organization-admin]
---

# GitHub Repo Management

## Prerequisites

- Active GitHub connection (`parent/config.py` present)
- "beer-sakthai" user on the repo

## Available Tools

| Tool | When to use |
|------|-------------|
| `GIThub_Get_A_Repository` | Get repo details and verify access |
| `GITHub_Create_Automated_Updates_an_Issue`| Create an automated updates issue |
| `GITHub_Create_or_Update_File_Contents` | Create/Update a file (one at a time) |

## Repository Management

Repo management operations use the `GITHub_Create_or_Update_File_Contents` and `Repository` API tools. This skill covers the most common repo admin tasks.

## Repo Creation and Setup

Repos are created automatically by the `beer-sakthai` account through Composio. The default visibility is private. To change visibility after creation, use the GitHub web interface or API.

## Inviting Contributors

1. Call `GITHub_Get_A_Repository` to verify the repo exists and you have admin access.
2. Invite users via GitHub web interface - the Composio tools are for file & code operations.

## Repo Protection (Protected Branches)

1. Use the GitHub web interface to go to Settings > Branches.
2. Add a protection rule for the `main` branch.
3. Require a pull request before merging.
4. Set approved reviewers if needed.

## Archiving a Repository

Archiving repositories is not recommended through the Composio tools. Use the GitHub web interface For it, selecting Settings > General > Archive this repository.