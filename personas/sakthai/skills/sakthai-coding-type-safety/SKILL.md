---
name: sakthai-coding-type-safety
category: coding
description: Write strict-clean Python that passes sakthai-agent-v2's `mypy --strict` gate over `sakthai/`. Use when annotating signatures, modeling optionals, using generics/protocols, or narrowing types.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - coding
      - python
      - typing
      - mypy
      - type-safety
    related_skills:
      - sakthai-coding-uv
      - sakthai-coding-testing
      - sakthai-coding-skill-authoring
---

# sakthai-coding-type-safety

`sakthai-agent-v2` runs **`mypy` in `strict` mode over `sakthai/`** (only
`sakthai.dashboard.app` is loosened — it's Streamlit glue over untyped libs).
`warn_unused_ignores` and `warn_return_any` are on. New code must be
strict-clean; treat type errors as build failures, not warnings.

## When to use this skill

- Adding or fixing type annotations anywhere under `sakthai/`
- Modeling "might not exist" with `| None` and narrowing it
- Writing reusable generics or structural interfaces (Protocols)
- Resolving a `mypy --strict` failure
- Deciding when a `# type: ignore` is justified (rarely)

## The strict-mode baseline

Run the exact gate locally:

```bash
uv run mypy sakthai
```

Strict mode means, in practice:

- **Every function gets annotated params and a return type** — including `-> None`.
  An unannotated `def` is an error under strict.
- **No implicit `Any`.** Returning `Any` from a typed function warns
  (`warn_return_any`). Annotate or cast deliberately.
- **No untyped calls bleeding in.** Wrap untyped third-party surfaces at a thin
  boundary and type your side of it.

## Core patterns

### Annotate all signatures (target ≥3.11 syntax)

```python
def add_fact(self, value: str, *, kind: str | None = None,
             key: str | None = None, tags: list[str] | None = None) -> int:
    ...
```

Use modern syntax: `X | None` (not `Optional[X]`), `list[str]` /
`dict[str, int]` (not `List`/`Dict`). ruff's `UP` rules enforce this here.

### Make "might not exist" explicit, then narrow

```python
fact = store.get_fact_by_key("pref", "theme")  # -> Fact | None
if fact is None:
    raise KeyError("pref/theme")
print(fact.value)   # mypy now knows fact is Fact, not Fact | None
```

Narrow with `is None` / `isinstance` / early-return guards. Don't reach into a
`| None` value before narrowing — strict mode rejects it.

### Protocols for structural interfaces

Prefer a `Protocol` over inheritance when you only need "has these methods" —
this is how v2 keeps the store/client injectable for tests without a base class:

```python
from typing import Protocol

class SupportsRender(Protocol):
    def render_prompt_block(self) -> str: ...

def build_prompt(store: SupportsRender) -> str:
    return store.render_prompt_block()
```

### Generics that preserve type information

```python
from typing import TypeVar

T = TypeVar("T")

def first_or(items: list[T], default: T) -> T:
    return items[0] if items else default
```

### TypedDict / dataclasses for structured records

The store models rows as dataclasses (`Fact`, `Observation`). Prefer a dataclass
or `TypedDict` over a bare `dict[str, Any]` so fields are checked, not guessed.

## When `# type: ignore` is acceptable

Almost never in `sakthai/`. Because `warn_unused_ignores` is on, a stale ignore
is itself an error. If you must, scope it to the exact code and explain:

```python
result = untyped_lib.call()  # type: ignore[no-untyped-call]  # lib ships no stubs
```

Prefer `ignore_missing_imports` (already set globally) over per-line ignores for
missing third-party stubs.

## Common pitfalls

1. **Don't widen to `Any` to silence mypy.** It hides the bug and trips
   `warn_return_any`. Model the real type or narrow.
2. **Don't add `Optional`/`List`/`Dict` imports** — use builtin generics and
   `|`; ruff `UP` will flag the old forms.
3. **Don't type `dashboard/app.py` strictly** — it's deliberately loosened. Don't
   "fix" it.
4. **Don't leave a stale `# type: ignore`** — it fails the build under
   `warn_unused_ignores`. Remove it once the underlying issue is gone.
5. **Don't annotate `library/` or `scripts/`** to mypy's taste — mypy only covers
   `sakthai/`; those trees are intentionally out of scope.
