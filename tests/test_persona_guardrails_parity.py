"""Guard against security-code drift across the six persona package copies.

Each persona under ``personas/`` exposes a ``sakthai`` package. The wiring is
not uniform (see CLAUDE.md):

* ``sakthai``            — the canonical, installed package (a real directory)
* ``sakjules``/``saktan`` — symlinks to ``personas/shared/sakthai``
* ``sakking``/``saksee``/``saksit`` — real directories holding a *partial* copy
  that shadows the shared one, created when security fixes were synced into
  what used to be a symlink path

Security hardening applied to the canonical copy must reach every persona,
otherwise a fixed vulnerability silently survives in an unsynced copy. This
module enforces two separate invariants:

1. :class:`TestPersonaSecurityFileParity` — every persona copy of a
   security-critical file is byte-identical to the canonical one.
2. :class:`TestShadowInventory` — the set of files shadowed into the partial
   persona directories is exactly the set we expect. A *new* shadow file
   appearing is the drift vector this repo has actually hit before, so it must
   fail loudly rather than be silently inherited.
"""

import unittest
from pathlib import Path

from sakthai.config import PERSONA_NAMES

REPO_ROOT = Path(__file__).resolve().parents[1]
PERSONAS_DIR = REPO_ROOT / "personas"
CANONICAL_PKG = PERSONAS_DIR / "sakthai" / "sakthai"

# Files carrying security-critical logic that MUST be identical everywhere.
#
# ``agent/guardrails.py`` is the tool-call policy. ``web/server.py`` holds the
# bearer-token authentication for the HTTP API — it is shadowed into the same
# three partial persona directories as guardrails.py and was previously
# unguarded, so a web-auth fix synced to only some personas would have shipped
# undetected.
SECURITY_SYNCED_FILES = (
    Path("agent") / "guardrails.py",
    Path("web") / "server.py",
)

# Shadow files that are known, accepted, stale snapshots rather than synced
# security code. Per CLAUDE.md these still register a `dashboard` command the
# real CLI no longer has; they are not live code and are deliberately NOT held
# to byte-parity. They are enumerated here so the inventory test below can tell
# "known stale file" apart from "someone just shadowed a new file".
KNOWN_STALE_SHADOWS: dict[str, set[str]] = {
    "saksee": {"cli/__init__.py", "cli/system.py"},
    "saksit": {"cli/__init__.py", "cli/system.py"},
}


def _persona_pkg(persona: str) -> Path:
    return PERSONAS_DIR / persona / "sakthai"


class TestPersonaSecurityFileParity(unittest.TestCase):
    def test_persona_list_is_complete(self):
        """The parity sweep must cover every persona the package knows about.

        This test previously hard-coded five persona names and omitted
        ``saktan``. That was survivable only because saktan is a symlink; the
        three personas that are now real shadow directories were symlinks too,
        until security syncs converted them. Deriving the list from
        ``config.PERSONA_NAMES`` removes the chance of a persona being added
        without being guarded.
        """
        self.assertEqual(len(PERSONA_NAMES), 6, f"expected six personas, got {PERSONA_NAMES}")
        for persona in PERSONA_NAMES:
            with self.subTest(persona=persona):
                self.assertTrue(
                    _persona_pkg(persona).is_dir(),
                    f"personas/{persona}/sakthai is missing",
                )

    def test_security_files_are_identical_across_personas(self):
        for rel in SECURITY_SYNCED_FILES:
            canonical_path = CANONICAL_PKG / rel
            self.assertTrue(canonical_path.is_file(), f"missing canonical {canonical_path}")
            canonical = canonical_path.read_bytes()

            for persona in PERSONA_NAMES:
                copy_path = _persona_pkg(persona) / rel
                with self.subTest(persona=persona, file=str(rel)):
                    self.assertTrue(copy_path.is_file(), f"missing {copy_path}")
                    self.assertEqual(
                        copy_path.read_bytes(),
                        canonical,
                        f"personas/{persona}/sakthai/{rel} has drifted from the "
                        "canonical copy. Security fixes must be synced to every "
                        "persona (cp from personas/sakthai/sakthai/).",
                    )

    def test_shared_copy_of_security_files_matches(self):
        """``personas/shared/sakthai`` is what the symlinked personas resolve to.

        Checked directly as well as through the symlinks, so the failure message
        points at the file that actually needs editing.
        """
        shared = PERSONAS_DIR / "shared" / "sakthai"
        for rel in SECURITY_SYNCED_FILES:
            with self.subTest(file=str(rel)):
                shared_path = shared / rel
                self.assertTrue(shared_path.is_file(), f"missing {shared_path}")
                self.assertEqual(
                    shared_path.read_bytes(),
                    (CANONICAL_PKG / rel).read_bytes(),
                    f"personas/shared/sakthai/{rel} has drifted from the canonical copy.",
                )

    def test_sakthai_chat_cli_guardrails_matches(self):
        """``sakthai-chat-cli/sakthai/agent/guardrails.py`` must match canonical guardrails.py."""
        cli_guardrails = REPO_ROOT / "sakthai-chat-cli" / "sakthai" / "agent" / "guardrails.py"
        canonical_guardrails = CANONICAL_PKG / "agent" / "guardrails.py"
        self.assertTrue(cli_guardrails.is_file(), f"missing {cli_guardrails}")
        self.assertEqual(
            cli_guardrails.read_bytes(),
            canonical_guardrails.read_bytes(),
            "sakthai-chat-cli/sakthai/agent/guardrails.py has drifted from the canonical copy.",
        )


class TestSecurityPropertiesArePresent(unittest.TestCase):
    """Assert security properties *exist*, not merely that copies agree.

    Parity is necessary but not sufficient. On 2026-08-18 a commit reverted the
    ``do_HEAD`` authentication gate in **all five** persona copies of
    ``web/server.py`` at once, and deleted the regression tests in
    ``tests/test_web_auth.py`` in the same diff. Every parity assertion above
    still passed, because the copies remained byte-identical to each other --
    uniformly reverted. Nothing in the suite noticed.

    These checks close that blind spot: they pin the presence of the property
    itself, in a file that four successive reverts have left alone. They are
    deliberately coarse (a substring, not a behavioural test) so they stay cheap
    and stable; the behavioural coverage lives in ``tests/test_web_auth.py``.
    """

    def _server_copies(self):
        """Yield (label, path) for every persona copy of web/server.py."""
        rel = Path("web") / "server.py"
        yield "canonical", CANONICAL_PKG / rel
        yield "shared", PERSONAS_DIR / "shared" / "sakthai" / rel
        for persona in PERSONA_NAMES:
            candidate = PERSONAS_DIR / persona / "sakthai" / rel
            if candidate.is_file():
                yield persona, candidate

    def test_head_requests_are_gated_in_every_web_server_copy(self):
        """``SimpleHTTPRequestHandler`` supplies its own ``do_HEAD``.

        Inheriting it unchanged serves HEAD straight out of ``send_head()``,
        skipping the bearer-token check and the static-root containment check
        that ``do_GET`` performs. An explicit ``do_HEAD`` must therefore exist
        in every copy.
        """
        for label, path in self._server_copies():
            with self.subTest(copy=label):
                source = path.read_text(encoding="utf-8")
                self.assertIn(
                    "def do_HEAD",
                    source,
                    f"{path} has no explicit do_HEAD, so it inherits "
                    "SimpleHTTPRequestHandler's, which bypasses authentication.",
                )

    def test_serve_api_script_gates_head_and_redacts_the_token(self):
        """``scripts/serve_api.py`` is a second, standalone copy of the server.

        It is outside the package (ruff and mypy skip ``scripts/``), so nothing
        else in the suite covers it, yet it serves the same API on port 3002.
        """
        source = (REPO_ROOT / "scripts" / "serve_api.py").read_text(encoding="utf-8")
        self.assertIn(
            "def do_HEAD",
            source,
            "scripts/serve_api.py inherits SimpleHTTPRequestHandler.do_HEAD, "
            "which bypasses its bearer-token check.",
        )
        self.assertIn(
            "_redact_query_token",
            source,
            "scripts/serve_api.py logs the request line, which carries any "
            "?token= credential; it must redact it before logging.",
        )


class TestShadowInventory(unittest.TestCase):
    """Pin which files the partial persona directories shadow.

    A shadow file takes precedence over the shared package for that persona, so
    every one of them is a place security fixes can fail to land. Adding one
    must be a deliberate, reviewed act.
    """

    def _shadowed_files(self, persona: str) -> set[str]:
        pkg = _persona_pkg(persona)
        if pkg.is_symlink():
            # Symlinked personas shadow nothing — they *are* the shared copy.
            return set()
        return {
            p.relative_to(pkg).as_posix()
            for p in pkg.rglob("*.py")
            # rglob would follow the `sakthai~origin_main` symlink that sits
            # alongside the partial directory; only count real files under it.
            if not any(part.endswith("~origin_main") for part in p.relative_to(pkg).parts)
        }

    def test_shadow_inventory_is_expected(self):
        expected_security = {rel.as_posix() for rel in SECURITY_SYNCED_FILES}

        for persona in PERSONA_NAMES:
            if persona == "sakthai":
                continue  # the canonical package shadows nothing
            with self.subTest(persona=persona):
                actual = self._shadowed_files(persona)
                allowed = expected_security | KNOWN_STALE_SHADOWS.get(persona, set())
                unexpected = actual - allowed
                self.assertEqual(
                    unexpected,
                    set(),
                    f"personas/{persona}/sakthai shadows unexpected file(s): "
                    f"{sorted(unexpected)}. A shadowing copy overrides the shared "
                    "package for this persona, so it is a place security fixes can "
                    "fail to land. Either add it to SECURITY_SYNCED_FILES (and keep "
                    "it byte-identical), or to KNOWN_STALE_SHADOWS if it is an "
                    "accepted stale snapshot.",
                )

    def test_known_stale_shadows_still_exist(self):
        """Keep KNOWN_STALE_SHADOWS honest.

        If one of these files is deleted (the real fix), this test fails and the
        allowlist entry must be dropped — so the exemption cannot outlive it.
        """
        for persona, rels in KNOWN_STALE_SHADOWS.items():
            for rel in rels:
                with self.subTest(persona=persona, file=rel):
                    self.assertTrue(
                        (_persona_pkg(persona) / rel).is_file(),
                        f"personas/{persona}/sakthai/{rel} no longer exists — "
                        "remove it from KNOWN_STALE_SHADOWS.",
                    )


if __name__ == "__main__":
    unittest.main()
