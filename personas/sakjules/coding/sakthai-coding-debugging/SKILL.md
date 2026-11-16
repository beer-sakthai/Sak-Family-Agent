---
name: sakthai-coding-debugging
category: coding
description: Debug runtime behavior systematically using breakpoints, log inspection, and isolated reproduction scripts.
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
      - sakthai-coding-conventions
      - sakthai-coding-tdd
---

# sakthai-coding-debugging

Apply a disciplined, systematic debugging process to isolate and fix errors:

1. **Reproduction**: Create a minimal, self-contained reproduction script in the `scratch/` directory.
2. **Inspection**: Inspect raw error logs, traceback frames, and environment variables. Use native debugger tools (e.g. `debugpy`, Node inspect) or run print statements at boundary layers rather than guessing.
3. **Surgical Fixes**: Locate the root cause, apply a focused correction, and run targeted tests to confirm behavior before modifying surrounding code.
