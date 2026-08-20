---
name: SakKing-environment-audit
description: "Audit filesystem structure and file contents systematically."
version: 0.1.0
author: Hermes
metadata:
  hermes:
    tags: [Environment, Audit, System, Diagnostics]
---

# Environment Audit
This skill provides a systematic procedure for auditing the local filesystem environment, from the root directory to individual files, using only Hermes tools. It avoids manual guesswork and ensures you have a clear, evidence-based understanding of the current workspace state.

## When to Use
- When you need to understand the structure of a directory or the contents of files within it.
- When you are unsure about the location or purpose of specific files in your environment.
- When Beer asks for a status check or an inventory of the current workspace.

## How to Run
Invoke the audit through the `search_files` and `read_file` tools. Use `search_files` for discovery and `read_file` for content inspection.

## Procedure
1. **Audit Root Directory**: Use `search_files` to list top-level contents of the current environment.
   `search_files(pattern='*', path='/opt/data', target='files')`
2. **Explore Subdirectories**: Repeat the discovery process for subdirectories as needed.
   `search_files(pattern='*', path='/opt/data/<subdir>', target='files')`
3. **Inspect File Contents**: Read specific files discovered during the audit.
   `read_file(path='/opt/data/<filename>')`
4. **Identify Dependencies**: Check for manifest files (e.g., `requirements.txt`, `package.json`, `config.yaml`) to understand the environment's requirements.

## Pitfalls
- **Large Directories**: Searching very large directories can be slow or return truncated results; use specific `file_glob` patterns to narrow the scope.
- **Hidden Files**: `search_files` may need specific glob patterns to include hidden files (e.g., `.*`).

## Verification
Run a directory audit of the root to ensure the workspace is accessible:
`search_files(pattern='*', path='/opt/data', target='files')`
