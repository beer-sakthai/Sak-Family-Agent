---
name: sakthai-coding-tdd
category: coding
description: Apply Test-Driven Development (TDD) principles to design and verify correct codebase features.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
    related_skills:
      - sakthai-coding-debugging
      - sakthai-devops-ci
---

# sakthai-coding-tdd

Write tests to define behavior before implementation, verifying both happy and error paths:

1. **Red-Green-Refactor**: Write a failing unit test first to capture the expectation, implement the minimum code to make the test pass, then refactor.
2. **Isolation**: Mock external dependencies and network requests to ensure tests are fast, deterministic, and hermetic.
3. **End-to-End Testing**: For web UI or complex integration paths, use Playwright or similar E2E frameworks, asserting on user-facing elements and accessibility tags rather than fragile class selectors.
