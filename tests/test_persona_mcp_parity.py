"""Guard against MCP-stack drift across the persona snapshots.

``personas/sakthai/mcp/`` is the only copy the suite imports, but the whole
package is duplicated into each of the five sibling personas — the same
arrangement ``agent/guardrails.py`` and ``web/server.py`` are in, and those two
already have parity gates (``test_persona_guardrails_parity.py``,
``test_persona_web_server_parity.py``).

``mcp/`` had none, which is the riskier omission of the three: it carries the
protocol-version table, the child-process environment allowlist, the remote
tool-name and description sanitising, and the external-server validation call.
A fix landing in the canonical copy alone would leave five personas speaking an
older protocol or missing a sanitiser, with nothing to notice.

This test fails CI the moment any copy diverges, and — unlike the two
single-file gates — it also fails when a *new* module is added to the canonical
``mcp/`` package and not copied across.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ["sakjules", "saktan", "sakking", "saksee", "saksit"]
CANONICAL_DIR = REPO_ROOT / "personas" / "sakthai" / "mcp"

SYNC_HINT = (
    "Sync it with `cp personas/sakthai/mcp/*.py personas/<persona>/mcp/` so "
    "protocol and sanitising fixes reach every persona."
)


def _canonical_modules() -> list[str]:
    """Every tracked Python module in the canonical MCP package, sorted."""
    return sorted(p.name for p in CANONICAL_DIR.glob("*.py"))


class TestPersonaMcpParity(unittest.TestCase):
    def test_canonical_package_is_discoverable(self):
        """Fail loudly if the canonical package moves, rather than vacuously passing."""
        self.assertTrue(CANONICAL_DIR.is_dir(), f"missing {CANONICAL_DIR}")
        modules = _canonical_modules()
        self.assertIn("server.py", modules)
        self.assertIn("client.py", modules)
        self.assertIn("manager.py", modules)
        self.assertIn("servers.py", modules)

    def test_all_persona_mcp_modules_are_identical(self):
        for module in _canonical_modules():
            canonical = (CANONICAL_DIR / module).read_bytes()
            for persona in PERSONAS:
                with self.subTest(persona=persona, module=module):
                    copy_path = REPO_ROOT / "personas" / persona / "mcp" / module
                    self.assertTrue(
                        copy_path.is_file(),
                        f"missing personas/{persona}/mcp/{module}. {SYNC_HINT}",
                    )
                    self.assertEqual(
                        copy_path.read_bytes(),
                        canonical,
                        f"personas/{persona}/mcp/{module} has drifted from the "
                        f"canonical copy. {SYNC_HINT}",
                    )

    def test_no_persona_carries_an_extra_mcp_module(self):
        """A stale module left behind in a copy is drift too.

        Deleting a canonical module without deleting the copies would otherwise
        pass the comparison above, since it only iterates canonical names.
        """
        expected = set(_canonical_modules())
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                copy_dir = REPO_ROOT / "personas" / persona / "mcp"
                self.assertTrue(copy_dir.is_dir(), f"missing {copy_dir}")
                found = {p.name for p in copy_dir.glob("*.py")}
                self.assertEqual(
                    found,
                    expected,
                    f"personas/{persona}/mcp/ holds a different set of modules "
                    f"than the canonical package. Extra: {sorted(found - expected)}; "
                    f"missing: {sorted(expected - found)}. {SYNC_HINT}",
                )


if __name__ == "__main__":
    unittest.main()
