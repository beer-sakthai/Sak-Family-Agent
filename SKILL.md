---
name: automated-vulnerability-patching
category: software-development
description: A 5-step pipeline for automatically finding, patching, and testing code vulnerabilities.
version: 1.0.0
author: Gemini Code Assist
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [vulnerability-management, patching, code-evolution, self-healing, devsecops, ai-patching]
    related_skills: [systematic-debugging, test-driven-development, github-pull-request]
---

# Automated Vulnerability Patching

## Vision: An Intelligent Digital Immune System

The goal of this skill is to create an "intelligent digital immune system" for the agent's codebase. When a vulnerability is detected, this automated pipeline is triggered to find, fix, test, and propose a patch, turning a reactive, hours-long human task into an automated process that takes seconds.

This process is a specialized form of code evolution, focused on security and stability. It is the primary mechanism for creating a self-healing codebase.

## When to Use

This pipeline should be triggered automatically or manually when a specific, reproducible bug is identified by a tool.

- **Automatic Trigger:** A CI/CD pipeline hook detects a `pytest` failure, a static analysis warning (e.g., from `ruff` or `bandit`), or a sanitizer error.
- **Manual Trigger:** An agent or human developer, after using the `systematic-debugging` skill to confirm a bug's existence, can invoke this skill to attempt an automated fix.

**Core Prerequisite:** A detailed error report, such as a stack trace or a static analysis finding with a file and line number, must be available.

## The 5-Step Automated Patching Pipeline

This pipeline must be followed sequentially. Each step is a gate for the next.

---

### 1. Find Vulnerabilities

The process begins when a tool detects a bug and provides actionable information.

**Action:**

1. Capture the output from the triggering tool (e.g., `pytest`, a linter, or a memory sanitizer).
2. Preserve all critical information, especially the **stack trace**, error message, file path, and line number. This information is the "symptom" that the rest of the pipeline will cure.

**Example Trigger:**

```
E   uninitialized_value_error: The variable 'user_id' can be uninitialized at this point.
E   File "/app/src/handlers.py", line 52, in process_request
```

---

### 2. Isolate and Reproduce

Before attempting a fix, create a failing test case that reliably reproduces the bug. This is the most critical step for ensuring the final patch is correct.

**Action:**

1. Analyze the stack trace and error report to pinpoint the exact file and lines of code that need fixing.
2. Use the `test-driven-development` skill to write a new, minimal test case that specifically targets the identified bug.
3. Run `pytest` on just this new test. It **must fail** with the expected error. This failing test becomes the "regression test" for the fix.

**Goal:** Create a single, fast-running test that proves the bug exists.

---

### 3. Generate Fixes with LLM

With a reproducible failure case, use a Large Language Model (LLM) to generate potential code patches.

**Action:**

1. Construct a detailed prompt for a powerful code-generation LLM (e.g., Claude 3 Opus, Gemini 1.5 Pro).
2. The prompt **must** include:
    - The isolated, problematic source code.
    - The full stack trace or error report from Step 1.
    - The exact location of the error (file and line number).
    - The failing test case created in Step 2.
    - A clear instruction: "Generate a code patch to fix this bug so the provided test case passes."
3. Generate one or more candidate patches from the LLM's response.

---

### 4. Test the Fixes

This is the automated validation gate. Each candidate patch is automatically applied and rigorously tested.

**Action:**

1. For each generated patch:
    a. Create a temporary copy of the codebase.
    b. Apply the patch to the relevant file.
    c. Run the specific failing test created in Step 2. If it does not pass, discard the patch immediately.
    d. If the specific test passes, run the **entire test suite** (`pytest tests/`). This is crucial for catching regressions (i.e., fixes that break other parts of the code).
2. Any patch that causes new test failures is an AI "hallucination" or an incorrect fix and must be discarded.

**Success Criteria:** A patch is considered successful only if the new test passes AND all existing tests continue to pass.

---

### 5. Surface for Human Review

After automatically filtering out all bad solutions, surface the successful, fully-tested fixes for a final human review. **Never commit directly to the main branch.**

**Action:**

1. For each successful patch:
    a. Create a new Git branch from the main branch (e.g., `fix/auto-patch-123`).
    b. Commit the code change to this branch.
    c. Use the `github-pull-request` skill to automatically create a pull request.
2. The pull request description **must** be populated with the full context:
    - The original bug report/stack trace.
    - A link to the failing test case.
    - The test results (showing all tests passed).
    - The exact code change (diff).
3. Assign the pull request to the appropriate human developer for final review and approval.

## Integration with Other Skills

- **`systematic-debugging`**: Use this skill to find and confirm bugs. Once the root cause is understood and reproducible, this `automated-vulnerability-patching` skill can be used to generate the fix.
- **`test-driven-development`**: This is a core dependency for Step 2 (Isolate and Reproduce). A failing test is non-negotiable.
- **`github-pull-request`**: This is the final step of the pipeline, ensuring all automated changes are subject to human oversight.
