---
name: sakthai-security-red-teaming
category: security
description: Audit system inputs, API sandboxes, and file capabilities to identify security vulnerabilities.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - security
    related_skills:
      - sakthai-security-hardening
      - sakthai-security-privacy
---

# sakthai-security-red-teaming

Proactively evaluate boundaries, API wrappers, and execution shells for vulnerabilities:

1. **Input Sanitization**: Check code for SQL injection, command injection, and unescaped inputs passed to subprocesses.
2. **Sandbox Validation**: Ensure commands or file operations adhere strictly to configured sandbox paths and permissions. Reject any unsanctioned shell escapes.
3. **Dependency Scans**: Run vulnerability auditing tools (e.g. `bandit`, `snyk`) and verify that dependencies are up to date and secure.
