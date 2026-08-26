#!/usr/bin/env python3
"""Generate the dashboard's TypeScript types from ``sakthai.web.contracts``.

``personas/sakthai/sakthai/web/contracts.py`` is the single definition of every
payload the web API returns. This script renders it to
``apps/sak_agent_dashboard/src/lib/contracts.generated.ts`` so the Next.js app
and the Python server cannot drift apart. CI regenerates and runs
``git diff --exit-code``, so a stale committed file fails the build.

Usage::

    python scripts/gen_dashboard_types.py           # write the file
    python scripts/gen_dashboard_types.py --check   # exit 1 if it would change

Output is deterministic: emission order comes from ``contracts.__all__`` and the
banner carries no timestamp, so regenerating an unchanged contract is a no-op.

Unsupported annotations raise rather than emitting a plausible-but-wrong TS
type — a loud failure here is much cheaper than a silent mismatch at runtime.
"""

from __future__ import annotations

import argparse
import json
import sys
import types
import typing
from pathlib import Path
from typing import Any, Literal, TypeVar, Union, get_args, get_origin

REPO_ROOT = Path(__file__).resolve().parents[1]

# There is no root-level `sakthai/` package; the installed one lives here.
sys.path.insert(0, str(REPO_ROOT / "personas" / "sakthai"))

from sakthai.web import contracts  # noqa: E402

OUTPUT_PATH = (
    REPO_ROOT / "apps" / "sak_agent_dashboard" / "src" / "lib" / "contracts.generated.ts"
)

_BANNER = """\
// ---------------------------------------------------------------------------
// DO NOT EDIT. Generated from personas/sakthai/sakthai/web/contracts.py by
// scripts/gen_dashboard_types.py. Run that script to regenerate; CI fails if
// this file is out of sync with the Python contract.
// ---------------------------------------------------------------------------
"""

_PRIMITIVES: dict[Any, str] = {
    str: "string",
    bool: "boolean",
    int: "number",
    float: "number",
    type(None): "null",
    object: "unknown",
}


class UnsupportedAnnotation(TypeError):
    """Raised for an annotation the generator refuses to guess at."""


def _alias_names() -> dict[Any, str]:
    """Map each exported ``Literal`` alias object back to its exported name.

    Lets a field annotated ``DataSource`` emit ``DataSource`` rather than
    re-inlining ``"local" | "api" | "demo"`` at every use site.
    """
    aliases: dict[Any, str] = {}
    for name in contracts.__all__:
        obj = getattr(contracts, name)
        if get_origin(obj) is Literal:
            aliases[obj] = name
    return aliases


def render_type(annotation: Any, aliases: dict[Any, str] | None = None) -> str:
    """Render one Python annotation as a TypeScript type expression."""
    if aliases and annotation in aliases:
        return aliases[annotation]

    # `bool` is a subclass of `int`, so identity lookup (not issubclass) matters.
    if annotation in _PRIMITIVES:
        return _PRIMITIVES[annotation]

    if isinstance(annotation, TypeVar):
        return annotation.__name__

    if typing.is_typeddict(annotation):
        return str(annotation.__name__)

    origin = get_origin(annotation)
    args = get_args(annotation)

    if origin is Literal:
        return " | ".join(json.dumps(arg) for arg in args)

    if origin is list:
        inner = render_type(args[0], aliases)
        # `A | null` must be parenthesised before `[]` binds.
        return f"({inner})[]" if " | " in inner else f"{inner}[]"

    if origin is dict:
        key, value = args
        if key is not str:
            raise UnsupportedAnnotation(f"dict keys must be str, got {key!r}")
        return f"Record<string, {render_type(value, aliases)}>"

    # `X | None` under `from __future__ import annotations` resolves to
    # typing.Union; a bare `X | Y` at runtime is types.UnionType.
    if origin is Union or isinstance(annotation, types.UnionType):
        return " | ".join(render_type(arg, aliases) for arg in args)

    raise UnsupportedAnnotation(
        f"{annotation!r} is not in the contract's supported type vocabulary; "
        "extend render_type() deliberately rather than widening it by accident."
    )


def render_interface(name: str, cls: Any, aliases: dict[Any, str]) -> str:
    """Render one TypedDict as an exported TS interface."""
    params = getattr(cls, "__parameters__", ())
    generics = ""
    if params:
        generics = "<" + ", ".join(f"{p.__name__} = unknown" for p in params) + ">"

    hints = typing.get_type_hints(cls)
    lines = [f"export interface {name}{generics} {{"]
    for field, annotation in hints.items():
        lines.append(f"  {field}: {render_type(annotation, aliases)};")
    lines.append("}")
    return "\n".join(lines)


def render_member(name: str, obj: Any, aliases: dict[Any, str]) -> str:
    """Render one exported member of the contracts module."""
    if isinstance(obj, str):
        return f"export const {name} = {json.dumps(obj)};"
    if typing.is_typeddict(obj):
        return render_interface(name, obj, aliases)
    if get_origin(obj) is Literal:
        # Render the alias's own declaration from its args, not via the alias
        # map, or it would emit `export type DataSource = DataSource;`.
        return f"export type {name} = {render_type(obj)};"
    raise UnsupportedAnnotation(
        f"contracts.{name} is a {type(obj)!r}; the generator emits string "
        "constants, Literal aliases, and TypedDicts only."
    )


def generate() -> str:
    """Render the whole contracts module as a TypeScript source file."""
    aliases = _alias_names()
    blocks = [
        render_member(name, getattr(contracts, name), aliases) for name in contracts.__all__
    ]
    return _BANNER + "\n" + "\n\n".join(blocks) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 1 if the committed file differs, without writing it",
    )
    args = parser.parse_args(argv)

    rendered = generate()

    if args.check:
        current = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""
        if current != rendered:
            print(f"{OUTPUT_PATH.relative_to(REPO_ROOT)} is stale; run this script.")
            return 1
        print(f"{OUTPUT_PATH.relative_to(REPO_ROOT)} is up to date.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
