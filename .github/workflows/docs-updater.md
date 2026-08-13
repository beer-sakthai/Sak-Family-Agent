---
on:
  schedule: weekly

permissions:
  contents: read
  pull-requests: read

safe-outputs:
  create-pull-request:
    branch: docs/automation
    title-prefix: "[docs] "
    draft: true
---

# Documentation Updater

Review code and documentation changes from the last seven days.

Identify outdated setup steps, missing option descriptions, and examples that no longer match current behavior. Update the relevant documentation files and open a draft pull request describing the changes and any areas that still require human review.