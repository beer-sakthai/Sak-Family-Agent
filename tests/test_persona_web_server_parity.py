"""Guard against web-server drift across the persona snapshots.

``web/server.py`` carries the web API's bearer-token auth, and like
``agent/guardrails.py`` it is copied into each persona's ``sakthai`` tree. The
suite only imports the canonical copy, so a security fix that lands there
alone would leave the other copies vulnerable with nothing to notice. This
test fails CI the moment any copy diverges from
``personas/sakthai/sakthai/web/server.py``.

SakJules and SakTan reach ``personas/shared/sakthai`` through a symlink, so
they cover the shared copy; SakKing, SakSee and SakSit each shadow it with a
real file of their own.
"""

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS = ["sakjules", "saktan", "sakking", "saksee", "saksit"]
SERVER_REL = Path("sakthai") / "web" / "server.py"


class TestPersonaWebServerParity(unittest.TestCase):
    def test_all_persona_web_servers_are_identical(self):
        canonical = (REPO_ROOT / "personas" / "sakthai" / SERVER_REL).read_bytes()
        for persona in PERSONAS:
            with self.subTest(persona=persona):
                copy_path = REPO_ROOT / "personas" / persona / SERVER_REL
                self.assertTrue(copy_path.is_file(), f"missing {copy_path}")
                self.assertEqual(
                    copy_path.read_bytes(),
                    canonical,
                    f"personas/{persona}/{SERVER_REL} has drifted from the "
                    "canonical copy. Sync it (cp from personas/sakthai/) so "
                    "auth fixes reach every persona.",
                )


if __name__ == "__main__":
    unittest.main()
