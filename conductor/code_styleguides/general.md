# General Code Styleguide & Invariants

## 1. Python Style Guidelines
- Use modern Python 3.11+ type annotations (`from __future__ import annotations`, `str | None`, `tuple[str, ...]`).
- Use standard dataclasses or Pydantic models for domain data transfer objects.
- All exceptions raised in public APIs must inherit from standard exceptions or `AgentError`.
- Keep functions small and focused on a single responsibility.

## 2. Next.js / React 19 Style Guidelines
- Use React 19 hooks and Next.js 15 App Router architecture.
- In `useEffect` hooks, ensure state updates occur inside async continuation closures or event callbacks to comply with React Compiler rules.
- Follow Tailwind CSS utility classes with dark theme palette `#0f172a` / `#1e293b`.

## 3. SQLite Invariants
- Always use WAL mode (`PRAGMA journal_mode=WAL;`).
- Use parameterized queries `?` exclusively to prevent SQL injection.
- Ensure all connection resources are closed cleanly via context managers.
