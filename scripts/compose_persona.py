#!/usr/bin/env python3
"""Compose a persona's full skill tree from the shared library + its overlay.

After the monorepo consolidation, the four persona skill libraries
(``personas/{sakthai,sakking,saksee,saksit}``) no longer each carry a full copy
of the ~446 skill files they share. Instead the identical files live once under
``personas/shared/skills/`` and each persona keeps only the files that are unique
to it or that differ from the shared version (its *overlay*).

This script reconstitutes the full, runnable skill tree for a persona by laying
the shared library down first and then copying the persona's overlay on top
(**overlay wins** on any path collision — the same "later wins" precedence the
agent's tool registry uses). The composed tree is byte-for-byte identical to the
persona's pre-consolidation ``skills/`` directory.

Usage::

    # Materialise sakthai's full skill tree into a directory
    python scripts/compose_persona.py sakthai --out /tmp/sakthai-skills

    # Verify a composed tree matches an expected snapshot (exit 1 on mismatch)
    python scripts/compose_persona.py sakthai --out /tmp/out --check /path/to/expected
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PERSONAS_DIR = REPO_ROOT / "personas"
PERSONAS = ("sakthai", "sakking", "saksee", "saksit")


def _copy_tree(src: Path, dst: Path) -> None:
    """Copy every file under ``src`` into ``dst`` (overwriting), preserving layout."""
    for path in src.rglob("*"):
        if path.is_file():
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def compose(persona: str, out: Path) -> Path:
    """Materialise ``persona``'s full skill tree into ``out`` and return it."""
    if persona not in PERSONAS:
        raise SystemExit(f"unknown persona {persona!r}; choose from {', '.join(PERSONAS)}")
    shared = PERSONAS_DIR / "shared" / "skills"
    overlay = PERSONAS_DIR / persona / "skills"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    if shared.is_dir():
        _copy_tree(shared, out)
    if overlay.is_dir():
        _copy_tree(overlay, out)  # overlay wins
    return out


def _diff(a: Path, b: Path) -> list[str]:
    """Return a list of human-readable differences between trees ``a`` and ``b``."""
    diffs: list[str] = []

    def walk(cmp: filecmp.dircmp[str], prefix: str = "") -> None:
        for name in cmp.left_only:
            diffs.append(f"only in expected: {prefix}{name}")
        for name in cmp.right_only:
            diffs.append(f"only in composed: {prefix}{name}")
        for name in cmp.diff_files:
            diffs.append(f"content differs: {prefix}{name}")
        for name, sub in cmp.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    walk(filecmp.dircmp(str(a), str(b)))
    return diffs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("persona", choices=PERSONAS, help="which persona to compose")
    parser.add_argument("--out", type=Path, required=True, help="output directory")
    parser.add_argument(
        "--check",
        type=Path,
        default=None,
        metavar="EXPECTED",
        help="diff the composed tree against EXPECTED; exit 1 on any mismatch",
    )
    args = parser.parse_args(argv)

    out = compose(args.persona, args.out)
    print(f"composed {args.persona} -> {out} ({sum(1 for _ in out.rglob('*') if _.is_file())} files)")

    if args.check is not None:
        diffs = _diff(args.check, out)
        if diffs:
            print(f"MISMATCH ({len(diffs)}):", file=sys.stderr)
            for d in diffs[:50]:
                print(f"  {d}", file=sys.stderr)
            return 1
        print(f"OK: composed {args.persona} matches {args.check} byte-for-byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
