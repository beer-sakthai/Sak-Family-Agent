"""Pin the divergence between the shared package copy and the canonical one.

``personas/shared/sakthai`` is not documentation — it is the code **SakJules and
SakTan actually execute**, because ``personas/sakjules/sakthai`` and
``personas/saktan/sakthai`` are symlinks to it (see CLAUDE.md).

Nothing tests it. ``[tool.coverage.run] source = ["sakthai"]`` resolves to the
*installed* package, which is ``personas/sakthai/sakthai``; the shared tree is
never imported by the suite, so its coverage is not low, it is **absent**. The
existing :mod:`tests.test_persona_guardrails_parity` closes part of this by
pinning two security-critical files byte-identical across every persona
(``agent/guardrails.py``, ``web/server.py``) — but only those two. Everything
else in the shared tree may drift arbitrarily and silently.

At the time this module was written the drift was already substantial: 11 files
totalling roughly 3,800 lines differ from the canonical copy, including
``agent/loop.py``, ``agent/tools.py``, ``config.py`` and ``auth.py`` — the core
of the agent. That is a known, tracked gap (CLAUDE.md calls reconciling the two
copies "not yet done"), and this module does **not** try to fix it: reconciling
3,800 lines of behaviour is a separate, reviewed piece of work.

What it fixes is the part that is cheap and matters most — the drift being
*invisible*. This is an inventory guard, in the same spirit as
``TestShadowInventory``:

* :class:`TestSharedDivergenceInventory` — the set of files that differ is
  exactly the set declared below. A **new** divergence fails CI, so the gap can
  be paid down but never silently grown.
* :class:`TestCanonicalOnlyInventory` — the set of modules that exist only in
  the canonical copy is exactly as declared, so shipping a new subsystem becomes
  an explicit decision about whether the symlinked personas get it too.
* :class:`TestAllowlistsStayHonest` — a declared exemption that no longer
  applies fails, so entries cannot outlive the drift they describe.

The 56 files not named below are asserted identical by construction: if one of
them drifts it moves into the diverged set and
:meth:`TestSharedDivergenceInventory.test_no_new_divergence` fails.
"""

import hashlib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"
CANONICAL_PKG = PERSONAS_DIR / "sakthai" / "sakthai"
SHARED_PKG = PERSONAS_DIR / "shared" / "sakthai"

# Personas whose `sakthai` package IS the shared copy, via symlink. Named here
# so the failure messages can say whose runtime is affected rather than talking
# about an abstract directory.
SYMLINKED_PERSONAS = ("sakjules", "saktan")

# Files that differ between the shared copy and the canonical one, each mapped
# to why. Every entry is live code SakJules and SakTan run untested.
#
# This is a debt register, not an approval list. Removing an entry (by syncing
# the file) is always the preferred direction; `test_declared_divergences_still_
# differ` fails if an entry is stale, which is what forces the register to
# shrink as the reconciliation lands.
# All files between personas/shared/sakthai and personas/sakthai/sakthai are now 100%
# synchronized in byte-parity. This register enforces zero ongoing drift.
KNOWN_DIVERGENCES: dict[str, str] = {}

# All canonical subsystems (including hardened guardrails, defense-in-depth, and selfheal)
# are now synchronized to the shared copy so symlinked personas have full feature parity.
CANONICAL_ONLY: dict[str, str] = {}

_SYNC_HINT = (
    "personas/shared/sakthai is what {personas} execute at runtime (their "
    "`sakthai` directory is a symlink to it), and no test imports it. Either "
    "sync the file from personas/sakthai/sakthai/, or declare it in "
    "KNOWN_DIVERGENCES with the reason it is intentionally forked."
).format(personas=" and ".join(SYMLINKED_PERSONAS))


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _python_files(base: Path) -> dict[str, str]:
    """Map every real ``.py`` under ``base`` to its content digest.

    Skips ``__pycache__`` (build output) and anything under a ``~origin_main``
    symlink, which ``rglob`` would otherwise follow back into the shared tree —
    the same guard :class:`TestShadowInventory` applies.
    """
    out: dict[str, str] = {}
    for path in base.rglob("*.py"):
        rel = path.relative_to(base)
        if "__pycache__" in rel.parts:
            continue
        if any(part.endswith("~origin_main") for part in rel.parts):
            continue
        out[rel.as_posix()] = _digest(path)
    return out


class _InventoryTestCase(unittest.TestCase):
    """Shared setup: both trees hashed once per test class."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.canonical = _python_files(CANONICAL_PKG)
        cls.shared = _python_files(SHARED_PKG)
        common = cls.canonical.keys() & cls.shared.keys()
        cls.diverged = {rel for rel in common if cls.canonical[rel] != cls.shared[rel]}
        cls.identical = {rel for rel in common if cls.canonical[rel] == cls.shared[rel]}
        cls.canonical_only = cls.canonical.keys() - cls.shared.keys()
        cls.shared_only = cls.shared.keys() - cls.canonical.keys()


class TestSharedPackageIsReal(_InventoryTestCase):
    def test_shared_package_exists(self):
        self.assertTrue(SHARED_PKG.is_dir(), f"missing {SHARED_PKG}")
        self.assertTrue(self.shared, "shared package contains no Python files")

    def test_symlinked_personas_resolve_to_shared(self):
        """Pin *why* this module exists: these personas run the shared copy.

        If a persona stops being a symlink (the drift vector that created the
        three partial shadow directories), this fails and the new arrangement
        has to be looked at deliberately.
        """
        for persona in SYMLINKED_PERSONAS:
            with self.subTest(persona=persona):
                pkg = PERSONAS_DIR / persona / "sakthai"
                self.assertTrue(
                    pkg.is_symlink(), f"personas/{persona}/sakthai is no longer a symlink"
                )
                self.assertEqual(
                    pkg.resolve(),
                    SHARED_PKG.resolve(),
                    f"personas/{persona}/sakthai no longer points at personas/shared/sakthai",
                )


class TestSharedDivergenceInventory(_InventoryTestCase):
    def test_no_new_divergence(self):
        """The set of drifted files must not grow.

        Any file not in KNOWN_DIVERGENCES is required to be byte-identical.
        """
        unexpected = self.diverged - set(KNOWN_DIVERGENCES)
        self.assertEqual(
            sorted(unexpected),
            [],
            f"personas/shared/sakthai has newly drifted from the canonical copy in "
            f"{sorted(unexpected)}. {_SYNC_HINT}",
        )

    def test_no_files_missing_from_shared(self):
        """A canonical module absent from the shared copy must be declared.

        Otherwise SakJules and SakTan get an ``ImportError`` at runtime for a
        module the rest of the package assumes exists.
        """
        undeclared = self.canonical_only - set(CANONICAL_ONLY)
        self.assertEqual(
            sorted(undeclared),
            [],
            f"{sorted(undeclared)} exist only in personas/sakthai/sakthai. If the "
            f"symlinked personas ({', '.join(SYMLINKED_PERSONAS)}) are meant to have "
            "them, copy them into personas/shared/sakthai; if not, declare them in "
            "CANONICAL_ONLY.",
        )

    def test_shared_has_no_orphan_modules(self):
        """The shared copy must not carry modules the canonical one dropped.

        A file surviving only here is code nothing tests, nothing type-checks
        (mypy covers only the canonical package) and nothing lints.
        """
        self.assertEqual(
            sorted(self.shared_only),
            [],
            f"{sorted(self.shared_only)} exist only in personas/shared/sakthai — "
            "orphaned code outside every quality gate. Delete it, or promote it "
            "to the canonical package.",
        )

    def test_majority_of_package_is_still_in_sync(self):
        """A canary on the overall shape of the drift.

        Not a precise threshold — it exists so that a bulk divergence (someone
        regenerating the shared tree from an old revision, say) trips a test
        even if each individual file were somehow declared.
        """
        self.assertGreater(
            len(self.identical),
            len(self.diverged),
            f"only {len(self.identical)} shared files still match canonical vs "
            f"{len(self.diverged)} drifted — the shared copy has diverged wholesale.",
        )


class TestCanonicalOnlyInventory(_InventoryTestCase):
    def test_declared_canonical_only_files_exist(self):
        for rel in sorted(CANONICAL_ONLY):
            with self.subTest(file=rel):
                self.assertIn(
                    rel,
                    self.canonical,
                    f"{rel} is declared in CANONICAL_ONLY but no longer exists in "
                    "the canonical package — remove the entry.",
                )

    def test_declared_canonical_only_files_absent_from_shared(self):
        """If a declared-canonical-only file got synced, drop the entry."""
        for rel in sorted(CANONICAL_ONLY):
            with self.subTest(file=rel):
                self.assertNotIn(
                    rel,
                    self.shared,
                    f"{rel} now exists in personas/shared/sakthai — remove it from "
                    "CANONICAL_ONLY so it is held to parity like everything else.",
                )


class TestAllowlistsStayHonest(_InventoryTestCase):
    """Exemptions must not outlive the condition they describe."""

    def test_declared_divergences_still_differ(self):
        """A synced file must be removed from KNOWN_DIVERGENCES.

        This is what makes the register shrink: once the reconciliation lands
        for a file, the stale entry fails CI until it is deleted, so the
        allowlist cannot quietly re-authorise future drift in that file.
        """
        for rel in sorted(KNOWN_DIVERGENCES):
            with self.subTest(file=rel):
                self.assertIn(
                    rel,
                    self.canonical,
                    f"{rel} is declared in KNOWN_DIVERGENCES but is gone from the "
                    "canonical package — remove the entry.",
                )
                self.assertIn(
                    rel,
                    self.shared,
                    f"{rel} is declared in KNOWN_DIVERGENCES but is gone from the "
                    "shared package — remove the entry.",
                )
                self.assertIn(
                    rel,
                    self.diverged,
                    f"{rel} is declared in KNOWN_DIVERGENCES but now matches the "
                    "canonical copy. Remove it from the register so the file is "
                    "held to parity from here on.",
                )

    def test_every_divergence_has_a_stated_reason(self):
        for rel, reason in sorted(KNOWN_DIVERGENCES.items()):
            with self.subTest(file=rel):
                self.assertTrue(
                    reason.strip(),
                    f"KNOWN_DIVERGENCES[{rel!r}] must say why the fork is intentional.",
                )

    def test_registers_do_not_overlap(self):
        """A file cannot be both 'diverged' and 'canonical-only'."""
        overlap = set(KNOWN_DIVERGENCES) & set(CANONICAL_ONLY)
        self.assertEqual(sorted(overlap), [], f"{sorted(overlap)} declared in both registers")


if __name__ == "__main__":
    unittest.main()
