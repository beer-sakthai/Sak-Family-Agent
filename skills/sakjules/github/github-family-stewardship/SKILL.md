---
name: github-family-stewardship
description: "GitHub family stewardship management: repo inventory, support rotation, archiving, labels, and family-agent coordination."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, family, stewardship, inventory, repo, archive, rotation, labels, coordination]
    related_skills: [github-repo-management, github-organization-admin, github-repo-roles]
---

# GitHub Family Stewardship

This skill covers managing the GitHub infrastructure for the Sak Family of Agents: repo inventory, support rotation, archiving, labeling, and agent coordination.

## Preequisites

- Active GitHub connection (`beer-sakthai`)\n- Read the `references/repo-inventory.md` for the full list of family repos
---

## Available Tools

| Tool | When to use |
|------|-------------|
| `GITHub_Get_A_Repository` | Read repo details, verify access |
| `GITube_Create_or_Update_File_Contents` | Create/update files (policies, docs, configs) |
| `GITHub_List_Check_Runs_for_A_Ref` | CI status checks |

## Repo Inventory

The full list of family repos is in `references/repo-inventory.md`. This is a living document that should be updated as repos are added or removed.

## Support Rotation

When a support repo is no longer needed:
1. Check the repo inventory to see what older projects use it
2. Update those projects to new repos or remove dependencies
3. Archive the repo (GitHub web interface only)
4. Remove from the inventory

## Agent Coordination

Each agent has a dedicated repo (or set of repos) under the bbeer-sakthai` organization. When a task involves another agent's repo, ask the user for permission or refer to the agent directly.