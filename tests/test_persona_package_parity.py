"""Guard against package-code drift across the six persona snapshots.

Only ``personas/sakthai/`` is installed and run, but each other persona under
``personas/`` carries a full copy of the ``sakthai`` package. A change to the
canonical code must be mirrored into every copy or the copies drift silently.

``tests/test_persona_structure_parity.py`` already byte-compares a hard-coded
list of 15 core subpackages, but that list misses the top-level package modules
(``auth.py``, ``config.py``, ``skills.py`` ...) and ``scripts/``, and a newly
added subpackage would not be covered until someone remembers to extend the list.
This test closes that gap by walking the **whole** canonical package tree and
asserting byte-identity for every ``.py`` on the parity surface, so a new module
or subpackage is covered automatically.

ADR-0001 (``docs/adr/ADR-0001-persona-package-duplication.md``) records why this
exists; ``scripts/sync_personas.py`` (``make sync-personas``) mirrors the
canonical code into the copies when a legitimate change makes this test fail.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANONICAL = "sakthai"
COPIES = ("sakking", "saksee", "saksit", "sakjules", "saktan")

# Top-level directories under a persona that are legitimately per-persona and so
# are NOT part of the package-code parity surface:
#   skills/     - each persona's own skill overlay
#   config/     - each persona's own model/provider/mcp config
#   evolution/  - each persona's own self-evolution subproject (really differs)
#   tests/      - a non-runtime per-persona copy; the real suite is repo-root tests/
# Keep this set identical to the one in scripts/sync_personas.py.
PER_PERSONA_DIRS = frozenset({"skills", "config", "evolution", "tests"})


def _parity_files(package_root: Path) -> set[Path]:
    """Package-root-relative ``.py`` paths on the parity surface under a persona."""
    out: set[Path] = set()
    for p in package_root.rglob("*.py"):
        rel = p.relative_to(package_root)
        if "__pycache__" in rel.parts:
            continue
        if rel.parts[0] in PER_PERSONA_DIRS:
            continue
        out.add(rel)
    return out


class TestPersonaPackageParity(unittest.TestCase):
    def setUp(self) -> None:
        self.canonical_root = REPO_ROOT / "personas" / CANONICAL
        self.canonical_files = _parity_files(self.canonical_root)

    def test_parity_surface_is_non_trivial(self) -> None:
        # A regression in the walk (wrong root, over-broad exclusions) would make
        # every other assertion vacuously pass; anchor it to a real floor.
        self.assertGreater(
            len(self.canonical_files),
            100,
            "parity surface collapsed; check the walk and PER_PERSONA_DIRS",
        )
        # The gap this test exists to close: top-level modules the subpackage
        # parity test does not cover.
        self.assertIn(Path("config.py"), self.canonical_files)
        self.assertIn(Path("skills.py"), self.canonical_files)

    def test_every_canonical_py_is_byte_identical_in_each_copy(self) -> None:
        for persona in COPIES:
            persona_root = REPO_ROOT / "personas" / persona
            for rel in sorted(self.canonical_files):
                with self.subTest(persona=persona, file=str(rel)):
                    copy_path = persona_root / rel
                    self.assertTrue(
                        copy_path.is_file(),
                        f"personas/{persona}/{rel} is missing. Run `make sync-personas`.",
                    )
                    self.assertEqual(
                        copy_path.read_bytes(),
                        (self.canonical_root / rel).read_bytes(),
                        f"personas/{persona}/{rel} has drifted from canonical "
                        f"personas/{CANONICAL}/{rel}. Run `make sync-personas`.",
                    )

    def test_no_copy_has_extra_package_py_absent_from_canonical(self) -> None:
        for persona in COPIES:
            with self.subTest(persona=persona):
                persona_root = REPO_ROOT / "personas" / persona
                extra = _parity_files(persona_root) - self.canonical_files
                self.assertEqual(
                    extra,
                    set(),
                    f"personas/{persona} has package .py files not in canonical "
                    f"personas/{CANONICAL}/: {sorted(map(str, extra))}. "
                    "Run `make sync-personas`.",
                )


if __name__ == "__main__":
    unittest.main()
