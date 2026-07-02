---
name: find-duplicate-code
description: "Analyzes a codebase to find duplicated code and suggests refactoring opportunities."
version: 1.0.0
author: Gemini Code Assist
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [refactoring, code-quality, duplication, static-analysis, python]
    related_skills: [run-command, read-file, systematic-debugging]
---

# Find and Suggest Refactoring for Duplicated Code

This skill identifies duplicated code blocks within a project and provides actionable refactoring suggestions to improve code quality and maintainability.

**Core principle:** Don't Repeat Yourself (DRY). Duplicated code increases maintenance overhead and the risk of bugs. This skill automates the detection and provides intelligent solutions.

## When to Use

Trigger this skill when a user wants to improve their codebase by reducing duplication.

- "Check my project for duplicate code."
- "Are there any refactoring opportunities in the `sakthai/` directory?"
- "/find-duplicate-code"

## The Process

### Phase 1 — Run Duplication Analysis

1. **Identify Target:** Determine the target directory for analysis. If the user doesn't specify one, assume the current project root.

2. **Run Code Duplication Tool:** Use the `run_command` tool to execute a copy-paste detector (CPD) tool. `pmd cpd` is a good candidate as it's language-agnostic and produces parsable output.

    ```bash
    # Hypothetical command. The agent may need to install pmd first.
    run_command "pmd cpd --minimum-tokens 75 --files path/to/project --language python --format xml"
    ```

    If a suitable tool is not available, inform the user and stop. The agent should parse the XML output to extract the file paths, line numbers, and code fragments for each duplicated block.

### Phase 2 — Launch the Refactoring Suggester Sub-agent

Delegate the creative work of suggesting refactors to a specialized sub-agent, providing it with the structured data from the CPD tool.

**Refactoring Suggester Agent Goal**
> You are an expert software engineer with a keen eye for clean code and effective refactoring. You have been given a report of duplicated code blocks. Your task is to provide clear, actionable suggestions to eliminate the duplication.
>
> For each set of duplicated code blocks:
>
> 1. **Analyze the Duplication:**
>     - Is the code identical, or are there minor differences (e.g., variable names, literal values)?
>     - What is the purpose of the duplicated code?
>
> 2. **Propose a Refactoring Strategy:**
>     - **Extract Function:** If the code is identical, suggest extracting it into a new, single function.
>     - **Parameterize Function:** If the code is slightly different, suggest extracting it into a function that accepts parameters for the differing parts.
>     - **Suggest Location:** If the duplication is within a single file, suggest a private helper function. If it's across multiple files, recommend creating or using a shared `utils.py` module.
>
> 3. **Provide Concrete Code Examples:**
>     - Show the proposed new function.
>     - Show how the original locations should be modified to call the new function.
>
> 4. **Structure the Report:** Group your suggestions by the duplicated block, making it easy for the user to understand the issue and the proposed solution.

### Phase 3 — Report to User

Present the suggestions from the sub-agent in a clear and helpful format.

**Example Output:**
> I've analyzed the codebase for duplicated code and found a few opportunities for refactoring.
>
> ### Duplication found in `sakthai/agent/providers/anthropic_provider.py` and `sakthai/agent/providers/gemini_provider.py`
>
> **Issue:** The logic for handling API request retries appears in both provider files.
>
> **Suggestion:** Extract this logic into a shared utility function.
>
> **Proposed New Function (in a new `sakthai/agent/providers/utils.py`):**
>
> ```python
> from tenacity import retry, stop_after_attempt, wait_exponential
> 
> @retry(wait=wait_exponential(multiplier=1, min=4, max=10), stop=stop_after_attempt(3))
> def make_request_with_retry(*args, **kwargs):
>     # ... implementation of the request logic ...
>     return response
> ```
>
> **Refactored Code:**
> Both `anthropic_provider.py` and `gemini_provider.py` would then be updated to import and call this function, removing the duplicated `@retry` decorator and logic from each.

## Pitfalls

- **Tool Availability:** The success of this skill depends on the availability of a command-line tool for detecting code duplication. The agent should be able to handle the case where no such tool is installed.
- **Near-Duplicates:** Simple CPD tools might miss duplications that have minor variations. The sub-agent's prompt should encourage it to look for these "near-misses" if the tool provides enough context.
- **Trivial Duplication:** The duplication tool should be configured with a reasonable minimum token count to avoid flagging trivial cases like common imports or boilerplate.
