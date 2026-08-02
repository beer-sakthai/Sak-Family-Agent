# Plan vs Reality — Cross-Referencing Guide

A PLAN.md tells you what the author *intends* or *aspired* to build. The filesystem tells you what actually exists. Never report a feature as "implemented" based on a PLAN.md entry alone.

## Checklist

When a PLAN.md says something exists or is planned:

| Plan Says | Check On Disk | What It Means |
|-----------|---------------|---------------|
| "Phase 1 implemented" | Source files exist with logic? | ✅ Really done |
| "Phase 1 implemented" | Only `__init__.py` stubs | Scaffolded, not built |
| "Phase 1 implemented" | Nothing found | Not started despite plan |
| "Will use X technology" | `pyproject.toml` has deps? | Check if X is wired or just mentioned |
| "Has tests" | `tests/` dir with `test_*.py` files? | Verify test content |
| Previous run claimed | `output/` or `runs/` dirs | Check for artifacts |

## Signals From This Session (SakKing Self-Evolution)

- PLAN.md described a 4-phase pipeline as future work
- Disk showed: full `evolution/` Python package, tests, `evolve_agent.sh`, `pyproject.toml`, **and** a previous run attempt in `output/github-auth/evolved_FAILED.md`
- Verdict: **Phase 1 fully built, had been run, failed at constraint validation (guardrail worked)**

## Common Pitfalls

- **Empty `__init__.py`** means "intended to have code here" — not "has code here"
- **PLAN.md status boards** use mixed notation (✅ vs [x]) — check all rows, not just the first
- **README bias** — README may claim features that have no corresponding implementation
- **Persona-specific plans** may be identical copies of a generic template (SakSit's self-evolution plan was a copy of SakKing's — not actually tailored)
- **Duplicate checkouts** (e.g. `repo-push/`, `profiles/saksit/sak-family-agent/`) contain stale PLAN.md copies that will mismatch the canonical repo

## Quick Probe Commands

```python
# Check if source files are real (not just __init__ stubs)
search_files("def ", path="evolution/", file_glob="*.py")

# Check output/run artifacts
terminal("ls output/ 2>/dev/null || echo 'no outputs'")

# Check test coverage
terminal("ls tests/ 2>/dev/null || echo 'no tests'")

# Check for previous failed/successful runs
search_files("*FAILED*", target="files") or search_files("*SUCCESS*", target="files")
```
