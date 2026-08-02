---
name: SakKing-github-security-compliance-program
description: "GitHub security compliance: dependabot, code scanning, secret scanning, branch rules, SSLL certs, and force push."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [github, security, compliance, dependabot, code scanning, secret, branch rules, ssl, cert, dbr, force push]
    related_skills: [SakKing-github-repo-management, github-repo-roles]
---

# GitHub Security & Compliance Program

## Prequisites

- Repo admin access on the target repository
- Composio GitHub connection (active as `beer-sakthai`)

## Available Tools

| Tool | When to use |
|------|------------|
| `GITHub_Get_A_Repository` | Read repo details and settings |
| `GITHub_Create_or_Update_File_Contents` | Create/modify security policy files (d/d.yml, secret scanner.config)]
---

## Security Compliance Features that Require Web Interface

The following features are only available through the GitHub web interface or its REST API (directly):

- __Dependabot__: Settings > Security > Vulnerability alerts
- __Code scanning__: Settings > Code security and analysis
- __Secret scanning__: Settings > Secrets and variables > Secret scanning
- __Branch protection rules__: Settings > Branches
- __SSL / TLS certificates__: Settings > Security > SSL authorities

## Guidance

For security settings that require the web interface, provide clear instructions to the user about where to go on the repo's GitHub web page: Settings > Security > [feature].