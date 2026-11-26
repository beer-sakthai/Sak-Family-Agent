---
on:
  schedule: daily

permissions:
  contents: read
  copilot-requests: write
  issues: read
  pull-requests: read

safe-outputs:
  create-pull-request:
    title-prefix: "[code-simplifier] "
    draft: true
  threat-detection: false
  report-failure-as-issue: false
  noop:
---

# Code Simplifier

Review production code changed in the last 24 hours. Look for one clear opportunity to remove needless branching, duplication, dead local abstractions, or confusing naming while preserving behavior and public interfaces exactly.

Make only a focused change with a measurable readability or maintainability benefit. Run the repository's formatter, tests, linter, and build. Open a draft pull request describing why the result is simpler and which checks passed. When no worthwhile simplification exists, explicitly call the `noop` tool with a concise message explaining why no simplification was needed.
