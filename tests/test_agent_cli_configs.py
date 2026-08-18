"""Invariants for the external coding-agent harness configs.

Claude Code reads ``CLAUDE.md`` + ``.claude/``. Two other agent CLIs are now
configured against this monorepo:

* **Gemini CLI** — ``GEMINI.md`` (context file) + ``.gemini/settings.json``
* **OpenCode** — ``opencode.json``

Neither file is executed by the ``sakthai`` package, so nothing else in the
suite would notice them rotting. Three things can rot, and all three have a
precedent in this repo:

1. **A pointer stops resolving.** Both configs deliberately *reference*
   ``AGENTS.md`` / ``CLAUDE.md`` / ``SOUL.md`` rather than restating them, so a
   moved or renamed file silently empties an agent's instructions.
2. **The duplicated model table drifts.** ``opencode.json`` has to spell out
   each persona's model because OpenCode cannot read this repo's YAML. A model
   rotation in ``personas/<name>/config/config.yaml`` must reach it.
3. **A persona is added and forgotten.** The persona list comes from
   ``config.PERSONA_NAMES``, the same source ``test_persona_guardrails_parity``
   derives from, so a seventh persona fails here until it is wired up.
"""

import json
import re
import unittest
from pathlib import Path

from sakthai.config import PERSONA_NAMES, persona_model_defaults

REPO_ROOT = Path(__file__).resolve().parents[1]
GEMINI_CONTEXT = REPO_ROOT / "GEMINI.md"
GEMINI_SETTINGS = REPO_ROOT / ".gemini" / "settings.json"
OPENCODE_CONFIG = REPO_ROOT / "opencode.json"

# ``{file:./relative/path}`` — OpenCode's file-reference syntax for `prompt`.
_FILE_REF_RE = re.compile(r"^\{file:(?P<path>[^}]+)\}$")
# ``@./relative/path.md`` at the start of a line — Gemini CLI's import syntax.
_IMPORT_RE = re.compile(r"^@(?P<path>\./\S+)\s*$", re.MULTILINE)

# The stdio command both harnesses use for this repo's own MCP server. Kept
# identical on purpose: the two CLIs must see the same tool list the agent loop
# has, because `mcp/server.py` reuses BUILTIN_TOOLS directly.
SAKTHAI_MCP_COMMAND = ["uv", "run", "--project", ".", "sakthai", "mcp"]


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class TestFilesExist(unittest.TestCase):
    """The three config files are present and parse."""

    def test_gemini_context_file_exists(self) -> None:
        self.assertTrue(GEMINI_CONTEXT.is_file(), f"missing {GEMINI_CONTEXT}")

    def test_gemini_settings_is_valid_json(self) -> None:
        self.assertTrue(GEMINI_SETTINGS.is_file(), f"missing {GEMINI_SETTINGS}")
        self.assertIsInstance(_load_json(GEMINI_SETTINGS), dict)

    def test_opencode_config_is_valid_json(self) -> None:
        self.assertTrue(OPENCODE_CONFIG.is_file(), f"missing {OPENCODE_CONFIG}")
        self.assertIsInstance(_load_json(OPENCODE_CONFIG), dict)


class TestInstructionPointersResolve(unittest.TestCase):
    """Every referenced instruction file exists.

    This is the failure mode that matters most: a dangling pointer does not
    error at runtime, it just means the agent runs with no house rules.
    """

    def test_gemini_imports_resolve(self) -> None:
        text = GEMINI_CONTEXT.read_text(encoding="utf-8")
        imports = _IMPORT_RE.findall(text)
        self.assertTrue(imports, "GEMINI.md imports no instruction files")
        for rel in imports:
            with self.subTest(imported=rel):
                self.assertTrue(
                    (REPO_ROOT / rel).is_file(),
                    f"GEMINI.md imports {rel}, which does not exist",
                )

    def test_gemini_imports_cover_the_shared_instructions(self) -> None:
        text = GEMINI_CONTEXT.read_text(encoding="utf-8")
        imported = {Path(rel).name for rel in _IMPORT_RE.findall(text)}
        self.assertIn("AGENTS.md", imported)
        self.assertIn("CLAUDE.md", imported)

    def test_gemini_context_filename_points_at_a_real_file(self) -> None:
        context = _load_json(GEMINI_SETTINGS).get("context", {})
        names = context.get("fileName")
        self.assertTrue(names, "context.fileName is unset")
        if isinstance(names, str):
            names = [names]
        for name in names:
            with self.subTest(context_file=name):
                self.assertTrue((REPO_ROOT / name).is_file(), f"{name} does not exist")

    def test_opencode_instructions_resolve(self) -> None:
        instructions = _load_json(OPENCODE_CONFIG).get("instructions", [])
        self.assertTrue(instructions, "opencode.json declares no instruction files")
        for rel in instructions:
            with self.subTest(instruction=rel):
                self.assertTrue(
                    (REPO_ROOT / rel).is_file(),
                    f"opencode.json lists {rel}, which does not exist",
                )

    def test_opencode_instructions_cover_the_shared_instructions(self) -> None:
        instructions = {Path(p).name for p in _load_json(OPENCODE_CONFIG)["instructions"]}
        self.assertIn("AGENTS.md", instructions)
        self.assertIn("CLAUDE.md", instructions)

    def test_opencode_agent_prompts_resolve(self) -> None:
        agents = _load_json(OPENCODE_CONFIG).get("agent", {})
        self.assertTrue(agents, "opencode.json defines no agents")
        for name, spec in agents.items():
            prompt = spec.get("prompt")
            if prompt is None:
                continue
            with self.subTest(agent=name):
                match = _FILE_REF_RE.match(prompt)
                self.assertIsNotNone(
                    match, f"agent {name!r} prompt is not a {{file:...}} reference"
                )
                assert match is not None  # narrowed for mypy; asserted above
                self.assertTrue(
                    (REPO_ROOT / match.group("path")).is_file(),
                    f"agent {name!r} prompt points at a missing file",
                )


class TestPersonaCoverage(unittest.TestCase):
    """Every persona is an OpenCode agent, wired to its own SOUL and model."""

    def setUp(self) -> None:
        self.agents = _load_json(OPENCODE_CONFIG)["agent"]

    def test_every_persona_has_an_agent(self) -> None:
        missing = sorted(set(PERSONA_NAMES) - set(self.agents))
        self.assertEqual(
            missing,
            [],
            f"personas with no opencode.json agent: {missing}. "
            "Add one (prompt = that persona's SOUL.md, model from its config.yaml).",
        )

    def test_persona_agents_use_their_own_soul(self) -> None:
        for persona in PERSONA_NAMES:
            with self.subTest(persona=persona):
                prompt = self.agents[persona]["prompt"]
                match = _FILE_REF_RE.match(prompt)
                assert match is not None  # shape verified in TestInstructionPointersResolve
                self.assertEqual(
                    Path(match.group("path")).as_posix(),
                    f"personas/{persona}/SOUL.md",
                    f"agent {persona!r} does not use its own SOUL.md",
                )

    def test_persona_agent_models_match_config_yaml(self) -> None:
        """The duplicated model table must track ``config/config.yaml``.

        OpenCode cannot read this repo's YAML, so the model is spelled out in
        ``opencode.json``. That copy is only safe while something fails when it
        drifts — this is that something.
        """
        for persona in PERSONA_NAMES:
            provider, model = persona_model_defaults(persona)
            if provider is None or model is None:
                continue
            with self.subTest(persona=persona):
                self.assertEqual(
                    self.agents[persona]["model"],
                    f"{provider}/{model}",
                    f"opencode.json model for {persona!r} is stale; "
                    f"personas/{persona}/config/config.yaml says {provider}/{model}",
                )

    def test_agent_modes_are_valid(self) -> None:
        for name, spec in self.agents.items():
            mode = spec.get("mode")
            if mode is None:
                continue
            with self.subTest(agent=name):
                self.assertIn(mode, ("primary", "subagent", "all"))


class TestProvidersAreDeclared(unittest.TestCase):
    """Non-default providers referenced by an agent must be configured."""

    def test_agent_model_providers_are_known(self) -> None:
        config = _load_json(OPENCODE_CONFIG)
        declared = set(config.get("provider", {}))
        for name, spec in config["agent"].items():
            model = spec.get("model")
            if model is None:
                continue
            provider = model.split("/", 1)[0]
            with self.subTest(agent=name):
                self.assertIn(
                    provider,
                    declared,
                    f"agent {name!r} uses provider {provider!r}, "
                    "which opencode.json does not configure",
                )

    def test_ollama_uses_ipv4_loopback(self) -> None:
        """``localhost`` breaks on hosts that resolve it to IPv6 first.

        ``providers/openai_provider.py`` connects to 127.0.0.1 for exactly this
        reason; the OpenCode provider must not reintroduce the bug.
        """
        options = _load_json(OPENCODE_CONFIG)["provider"]["ollama"]["options"]
        self.assertIn("127.0.0.1", options["baseURL"])
        self.assertNotIn("localhost", options["baseURL"])


class TestSharedMcpServer(unittest.TestCase):
    """Both harnesses launch this repo's own MCP server the same way."""

    def test_gemini_registers_the_sakthai_server(self) -> None:
        servers = _load_json(GEMINI_SETTINGS).get("mcpServers", {})
        self.assertIn("sakthai", servers)
        spec = servers["sakthai"]
        self.assertEqual([spec["command"], *spec["args"]], SAKTHAI_MCP_COMMAND)

    def test_opencode_registers_the_sakthai_server(self) -> None:
        servers = _load_json(OPENCODE_CONFIG).get("mcp", {})
        self.assertIn("sakthai", servers)
        spec = servers["sakthai"]
        self.assertEqual(spec["type"], "local")
        self.assertEqual(spec["command"], SAKTHAI_MCP_COMMAND)
        self.assertTrue(spec.get("enabled", True))


class TestSecurityPosture(unittest.TestCase):
    """The harness configs must not quietly widen the repo's defaults."""

    def test_gemini_does_not_default_to_yolo(self) -> None:
        general = _load_json(GEMINI_SETTINGS).get("general", {})
        self.assertNotEqual(
            general.get("defaultApprovalMode"),
            "yolo",
            "the committed project setting must not auto-approve every action; "
            "pass --yolo per session instead",
        )

    def test_gemini_respects_gitignore(self) -> None:
        """`.env` is gitignored — the agent must not read it as project context."""
        filtering = _load_json(GEMINI_SETTINGS)["context"]["fileFiltering"]
        self.assertTrue(filtering.get("respectGitIgnore"))

    def test_opencode_gates_bash(self) -> None:
        permission = _load_json(OPENCODE_CONFIG).get("permission", {})
        self.assertIn(
            permission.get("bash"),
            ("ask", "deny"),
            "shell must stay gated, matching the run_command / SAKTHAI_SHELL_ALLOW default",
        )

    def test_guardrail_reviewer_cannot_edit(self) -> None:
        agent = _load_json(OPENCODE_CONFIG)["agent"]["guardrail-review"]
        self.assertEqual(agent["mode"], "subagent")
        self.assertEqual(agent["permission"]["edit"], "deny")


if __name__ == "__main__":
    unittest.main()
