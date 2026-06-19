# Code Review Request: Remove Unused Import in sakthai/cli/memory.py

The `memory_deduplicate` function had a local import of `Fact` and `Observation`, but these were already imported at the module level in `sakthai/cli/memory.py`. I have removed the redundant local import.

- File: `sakthai/cli/memory.py`
- Line: 386 (removed)

Verified with:
- `uv run ruff check sakthai/cli/memory.py`
- `uv run pytest tests/test_cli.py -k deduplicate`
