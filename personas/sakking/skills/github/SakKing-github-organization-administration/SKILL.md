---
name: SakKing-github-organization-administration
description: "GitHub organization admin: manage org/team roles, audit logs, policies, secrets, and billing."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, organization, admin, team, roles, audit, logs, security, policies, secrets, billing]
    related_skills: [SakKing-github-repo-management, github-repo-roles]
---

# GitHub Organization Administration

## Provided Actions

| Action | Tool | Notes |
|-------|------|-------|
| Add/Remove team members | GitHub web interface | Composio doesn't have a tool for managing membership |
| Manage team roles | GitHub web interface | Same reason- no Composio tool |
| Audit logs | GitHub web interface | Use the Audit Log section |
| Security policies | GitHub web interface | Settings > Security |
| Manage secrets | GitHub web interface | Settings > Secrets and variables |

## Note on Organization Access

YOU do not have access to the `beer-sakthai` organization's settings via the Composio API. All organization-level administration must be done through the GitHub web interface or its API documentation. The Composio tools are limited to repository-level file and code operations