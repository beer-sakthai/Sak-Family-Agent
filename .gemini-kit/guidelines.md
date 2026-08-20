# Development Guidelines: Sak-Family-Agent

## 1. Code Style & Typing
- **Python**: Strict type annotations (`from __future__ import annotations`), dataclasses/Pydantic models, no untyped `Any` in public APIs.
- **TypeScript**: Strict mode enabled (`noImplicitAny`, `strictNullChecks`), React 19 compiler compliance (state updates in effect continuations).
- **Control Character Rejection**: File path operations must reject control characters (`ord(c) < 32 or ord(c) == 127`).

## 2. Testing Invariants
- **Hermetic Tests**: Unit tests must never initiate real network requests or mutate user home directories outside temporary sandboxes (`tmp_path`).
- **AST Compilation**: All Python files in the workspace must parse cleanly to AST (`tests/test_repo_parses.py`).
- **Package Parity**: Ensure byte/function parity between `personas/sakthai/sakthai/` and `personas/shared/sakthai/`.

## 3. Git Commit Conventions
Follow Conventional Commits format:
- `feat(component): add new capability`
- `fix(component): resolve issue`
- `test(component): add test coverage`
- `docs(component): update documentation`
- `refactor(component): code structure cleanup`
