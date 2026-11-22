#!/usr/bin/env python3
"""Sync the canonical package code from ``personas/sakthai`` to the five copies.

Only ``personas/sakthai/`` is installed and run (see ``pyproject.toml``), but the
other five personas each carry a full copy of the package tree. A change to the
canonical code must be mirrored into those copies or they drift silently; ADR-0001
(``docs/adr/ADR-0001-persona-package-duplication.md``) records the decision to
guard that drift with ``tests/test_persona_package_parity.py`` and to make this
mirroring a one-command operation.

This script is that command. It copies every canonical ``.py`` file that the
parity test checks into each persona, and removes any parity-surface ``.py`` a
persona has that the canonical tree no longer has, so the result is byte-identical
on exactly the files the test compares.

Deliberately NOT touched (genuinely per-persona — see the exclusion set, which is
kept identical to the parity test's): each persona's ``SOUL.md``, ``skills/``,
``config/``, ``evolution/`` (its own self-evolution subproject) and its
non-runtime ``tests/`` copy.

Usage::

    python scripts/sync_personas.py            # copy canonical -> the five
    python scripts/sync_personas.py --check     # report drift, change nothing (exit 1 on drift)
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "sakthai"
COPIES = ("sakking", "saksee", "saksit", "sakjules", "saktan")

# Top-level directories under a persona that are legitimately per-persona and so
# are NOT part of the package-code parity surface. Keep this set identical to the
# one in tests/test_persona_package_parity.py.
PER_PERSONA_DIRS = frozenset({"skills", "config", "evolution", "tests"})


def _is_parity_py(rel: Path) -> bool:
    """True if a package-root-relative ``.py`` path is on the parity surface."""
    if rel.suffix != ".py":
        return False
    if "__pycache__" in rel.parts:
        return False
    return rel.parts[0] not in PER_PERSONA_DIRS


def parity_files(package_root: Path) -> set[Path]:
    """Package-root-relative ``.py`` paths on the parity surface under a persona."""
    return {
        p.relative_to(package_root)
        for p in package_root.rglob("*.py")
        if _is_parity_py(p.relative_to(package_root))
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="report drift without changing anything; exit 1 if any copy differs",
    )
    args = parser.parse_args()

    canonical_root = REPO_ROOT / "personas" / CANONICAL
    canonical_files = parity_files(canonical_root)

    drift = 0
    for persona in COPIES:
        persona_root = REPO_ROOT / "personas" / persona
        persona_files = parity_files(persona_root)

        # Files to copy from canonical (missing or differing in the persona).
        for rel in sorted(canonical_files):
            src = canonical_root / rel
            dst = persona_root / rel
            if dst.is_file() and dst.read_bytes() == src.read_bytes():
                continue
            drift += 1
            action = "would update" if args.check else "update"
            print(f"[{action}] personas/{persona}/{rel}")
            if not args.check:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)

        # Parity-surface files the persona has but canonical no longer does.
        for rel in sorted(persona_files - canonical_files):
            drift += 1
            action = "would remove" if args.check else "remove"
            print(f"[{action}] personas/{persona}/{rel} (not in canonical)")
            if not args.check:
                (persona_root / rel).unlink()

    if args.check:
        if drift:
            print(f"\n{drift} file(s) differ from canonical personas/{CANONICAL}/.")
            print("Run `make sync-personas` to mirror the canonical package code.")
            return 1
        print(f"All five persona copies match canonical personas/{CANONICAL}/.")
        return 0

    if drift:
        print(f"\nSynced {drift} file(s) from canonical personas/{CANONICAL}/.")
    else:
        print(f"Nothing to sync; copies already match personas/{CANONICAL}/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
