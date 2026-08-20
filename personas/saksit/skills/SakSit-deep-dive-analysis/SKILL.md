---
name: SakSit-deep-dive-analysis
description: "Analyze plans, code, or docs comprehensively."
version: 0.1.0
author: Hermes
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Research, Analysis, Documentation, Codebase, Architecture]
category: research
---

# Deep Dive Analysis

Analyze a PLAN.md, project directory, or documentation comprehensively — uncover what's built vs planned, trace references, assess implementation state, and present a structured report. Does NOT produce code changes; produces understanding.

## When to Use

- User asks "what's inside X?" and the answer needs depth, not a file listing
- User drops a PLAN.md or README and wants to know what's real vs aspirational
- A project has multiple layers (plan → sub-plans → code → test results) and you need to connect them
- Before starting work on a feature, to understand the full landscape
- User says "deep dive" or "tell me everything about X"

## Prerequisites

- `read_file` access to the target directory or file
- `search_files` for directory structure and cross-references
- `terminal` for checking build state, run artifacts, or git history
- No external credentials needed — works on local filesystem

## How to Run

```bash
# Start with the entry point
deep_dive(path: str) — read the main file/directory, follow references, assess state, report
```

Invoke through `execute_code` or step through manually with `read_file` + `search_files` + `terminal`.

## Quick Reference

| Step | Hermes Tool | What to Get |
|------|-------------|-------------|
| 1. Entry | `read_file` | Main PLAN.md, README, or directory listing |
| 2. Structure | `search_files` | All files, sub-plans, key components |
| 3. References | `read_file` | Follow links to sub-docs, related plans |
| 4. State | `terminal` | Build artifacts, test outputs, run history |
| 5. Reality check | `search_files` + `read_file` | What's actually implemented vs planned |
| 6. Synthesize | — | Structured report with findings |

## Procedure

### 1. Read the Entry Point

Start with whatever the user pointed at — a PLAN.md, a directory, a README:

```python
# Read the main plan
plan = read_file(path)["content"]
```

Extract:
- The **purpose** (what is this thing trying to do?)
- The **structure** (tables of contents, sub-directories, linked docs)
- The **status markers** (✅ done, [x] done, 🚧 wip, ❌ blocked)

### 2. Map the Directory Structure

Use `search_files` with `target="files"` to get a complete inventory:

```python
# Get all files recursively
files = search_files(pattern="*", path=dir_path, target="files")

# Or filter for specific types
md_files = search_files(pattern="*.md", path=dir_path, target="files")
py_files = search_files(pattern="*.py", path=dir_path, target="files")
```

Note:
- Files that exist → implemented or scaffolded
- Files referenced in PLAN.md that don't exist → not yet built
- Output directories with run artifacts → has been exercised

### 3. Trace All References

PLAN.md files often link to sub-plans. Follow every path:

```python
# For each linked doc, read it
for sub_plan in ["product/PLAN.md", "personas/*/PLAN.md"]:
    read_file(sub_plan)
```

Cross-reference what the plan *says* against what files *exist* on disk.

### 4. Check Implementation State

Read source files, not just docs:

```python
# Check if the Python package/scripts actually exist
search_files("evolution/skills/evolve_skill.py", target="files")

# Check previous run outputs
terminal("ls output/")

# Check test results
terminal("ls tests/")
```

Key signals:
- **Empty directory** → scaffold, not built
- **Has `__init__.py` but no `.py` files** → package structure, no logic
- **Has actual code + tests + run output** → fully implemented
- **Previous run artifacts with FAILED** → been tried but hit issues

### 5. Build the Reality Map

Create a side-by-side comparison of planned vs actual:

```
| Plan Says | On Disk | Status |
|-----------|---------|--------|
| evolution/core/dataset_builder.py | ✅ exists | Implemented |
| Evolution of tool descriptions | ❌ no code | Planned only |
| Phase 1 validation report | ✅ reports/phase1_validation_report.pdf | Done |
```

### 6. Synthesize the Report

Present findings in a structured format covering:

1. **Purpose** — what this system/project is for
2. **Architecture** — key components and how they connect
3. **Status** — what's built vs what's planned (table)
4. **Previous Results** — any run artifacts, test outputs, failures
5. **Constraints** — dependencies, required APIs/keys, limits
6. **Next Steps** — what would be actionable from here

## References

- **`references/plan-vs-reality.md`** — checklist and probes for cross-referencing plan claims against actual filesystem state. Use when a PLAN.md says something is built and you need to verify it really is.
- **`references/plan-inventory-audit.md`** — estate-wide audit: find ALL PLAN.md files across the filesystem, categorize canonical vs stale, verify content and cross-references, produce a priority-ordered fix list with a durable saved report the user can recount from.

## Pitfalls

- **Plans are aspirational.** A well-written PLAN.md ≠ implemented code. Always check disk before reporting a feature exists.
- **Previous failures don't mean broken pipeline.** `evolved_FAILED.md` means constraint validation caught a bad variant — that's the guardrail working, not a bug.
- **Don't stop at the first file.** Plans link to sub-plans. Follow every reference before reporting completeness.
- **Empty `__init__.py` files** mean "package declared, nothing implemented." Don't count them as code.
- **README bias.** Omissions in a README don't mean the feature is missing. Always cross-check against the actual code.

## Verification

After a deep dive, you should be able to answer:
- What's the purpose of this project/system?
- What's fully built vs partially built vs planned only?
- What previous runs/attempts exist and what happened?
- What are the key constraints (deps, keys, limits)?
- What's the single next actionable step?
