from __future__ import annotations

import importlib.util
import os
import re
import stat
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "setup_vm_telegram_agents.py"
SCRIPT_SPEC = importlib.util.spec_from_file_location("setup_vm_telegram_agents", SCRIPT_PATH)
assert SCRIPT_SPEC is not None and SCRIPT_SPEC.loader is not None
SCRIPT_MODULE = importlib.util.module_from_spec(SCRIPT_SPEC)
sys.modules[SCRIPT_SPEC.name] = SCRIPT_MODULE
SCRIPT_SPEC.loader.exec_module(SCRIPT_MODULE)

build_vm_bundle = SCRIPT_MODULE.build_vm_bundle
parse_user_ids = SCRIPT_MODULE.parse_user_ids


def test_parse_user_ids_accepts_commas_and_spaces() -> None:
    assert parse_user_ids("123, 456 789") == [123, 456, 789]


def test_build_vm_bundle_writes_common_and_agent_env_files(tmp_path: Path) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    bundle = build_vm_bundle(
        repo_root=repo_root,
        target_dir=tmp_path / "vm-bundle",
        openai_base_url="https://example.azure.com/openai/v1",
        openai_api_key="sk-test",
        telegram_bot_tokens={agent: f"{agent}-token" for agent in SCRIPT_MODULE.AGENTS},
        telegram_allowed_user_ids=[123, 456],
        shared_sakthai_home=tmp_path / "state" / "sakthai",
    )

    assert bundle.common_env_file.read_text(encoding="utf-8") == (
        "OPENAI_BASE_URL=https://example.azure.com/openai/v1\n"
        "OPENAI_API_KEY=sk-test\n"
        "SAKTHAI_PROVIDER=openai\n"
    )
    sakking_env = bundle.env_files["sakking"].read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=sakking-token" in sakking_env
    assert "TELEGRAM_ALLOWED_USER_IDS=123,456" in sakking_env
    assert "SAKTHAI_SYSTEM_PROMPT_FILE=" in sakking_env
    assert bundle.service_file.exists()


def _bundle(tmp_path: Path) -> object:
    return build_vm_bundle(
        repo_root=Path(__file__).resolve().parents[1],
        target_dir=tmp_path / "vm-bundle",
        openai_base_url="https://example.azure.com/openai/v1",
        openai_api_key="sk-test",
        telegram_bot_tokens={agent: f"{agent}-token" for agent in SCRIPT_MODULE.AGENTS},
        telegram_allowed_user_ids=[123],
        shared_sakthai_home=tmp_path / "state" / "sakthai",
    )


def test_env_files_holding_secrets_are_owner_only(tmp_path: Path) -> None:
    """The env files carry the API key and bot tokens, so only the owner may read them."""
    old_umask = os.umask(0o022)  # the common default, which leaves new files 0644
    try:
        bundle = _bundle(tmp_path)
    finally:
        os.umask(old_umask)

    assert stat.S_IMODE(bundle.config_dir.stat().st_mode) == 0o700
    for env_file in (bundle.common_env_file, *bundle.env_files.values()):
        assert stat.S_IMODE(env_file.stat().st_mode) == 0o600, env_file.name


def test_rerun_tightens_a_world_readable_env_file(tmp_path: Path) -> None:
    config_dir = tmp_path / "vm-bundle" / "config"
    config_dir.mkdir(parents=True)
    stale = config_dir / "common.env"
    stale.write_text("OPENAI_API_KEY=old\n", encoding="utf-8")
    stale.chmod(0o644)

    _bundle(tmp_path)

    assert stat.S_IMODE(stale.stat().st_mode) == 0o600
    assert "OPENAI_API_KEY=sk-test" in stale.read_text(encoding="utf-8")


def test_secret_prefers_flag_then_environment_then_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    prompts: list[str] = []
    monkeypatch.setattr(SCRIPT_MODULE.getpass, "getpass", lambda p: prompts.append(p) or "typed")
    monkeypatch.setenv("SAKKING_TELEGRAM_BOT_TOKEN", "from-env")

    assert SCRIPT_MODULE._secret("from-flag", "SAKKING_TELEGRAM_BOT_TOKEN", "x") == "from-flag"
    assert SCRIPT_MODULE._secret(None, "SAKKING_TELEGRAM_BOT_TOKEN", "x") == "from-env"
    monkeypatch.delenv("SAKKING_TELEGRAM_BOT_TOKEN")
    assert SCRIPT_MODULE._secret(None, "SAKKING_TELEGRAM_BOT_TOKEN", "SakKing token") == "typed"
    assert prompts == ["SakKing token: "]


def _no_terminal(_prompt: str) -> str:
    raise EOFError


@pytest.mark.parametrize("prompt_answer", [lambda _p: "", _no_terminal], ids=["empty", "no-tty"])
def test_missing_secret_exits_cleanly(monkeypatch: pytest.MonkeyPatch, prompt_answer) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(SCRIPT_MODULE.getpass, "getpass", prompt_answer)
    with pytest.raises(SystemExit, match="OpenAI API key"):
        SCRIPT_MODULE._secret(None, "OPENAI_API_KEY", "OpenAI API key")


def test_parser_does_not_require_secrets_on_the_command_line() -> None:
    """Secrets passed as flags show up in `ps` and shell history; none is required."""
    args = SCRIPT_MODULE._build_parser().parse_args(
        [
            "--repo-root",
            ".",
            "--target-dir",
            "out",
            "--openai-base-url",
            "https://example.com/v1",
            "--telegram-allowed-user-ids",
            "123",
            "--shared-sakthai-home",
            "home",
        ]
    )
    assert args.openai_api_key is None
    assert all(
        getattr(args, f"{agent}_telegram_bot_token") is None for agent in SCRIPT_MODULE.AGENTS
    )


def _deployed_skill_settings() -> list[tuple[str, str, str]]:
    """(source, persona, skill) for every SAKTHAI_WITH_SKILLS a VM deployment sets."""
    repo_root = Path(__file__).resolve().parents[1]
    found = [
        ("setup_vm_telegram_agents.py", persona, skill)
        for persona, spec in SCRIPT_MODULE.AGENTS.items()
        for skill in spec["skills"].replace(",", " ").split()
    ]
    templates = repo_root / "infra" / "vm-agents" / "env-templates"
    for template in sorted(templates.glob("sak*.env.example")):
        persona = template.name.removesuffix(".env.example")
        for line in template.read_text(encoding="utf-8").splitlines():
            if line.startswith("SAKTHAI_WITH_SKILLS="):
                for skill in line.split("=", 1)[1].replace(",", " ").split():
                    found.append((template.name, persona, skill))
    launcher = (repo_root / "infra" / "vm-agents" / "sakthai-agent-run.sh").read_text(
        encoding="utf-8"
    )
    for persona, block in re.findall(r"^(sak\w+)\)(.*?);;", launcher, re.M | re.S):
        for value in re.findall(r"SAKTHAI_WITH_SKILLS=(\S*)", block):
            for skill in value.replace(",", " ").split():
                found.append(("sakthai-agent-run.sh", persona, skill))
    return found


def test_every_deployed_with_skills_name_resolves() -> None:
    """A skill name the VM passes must exist for that persona, or it is silently skipped.

    SakSee ran with SAKTHAI_WITH_SKILLS=playwright, a name no skill root has; the
    real skill is SakSee-playwright.
    """
    from sakthai.skills import collect_skills, default_skill_roots

    settings = _deployed_skill_settings()
    assert settings, "no SAKTHAI_WITH_SKILLS setting found"
    missing = [
        (source, persona, skill)
        for source, persona, skill in settings
        if skill not in {s.name for s in collect_skills(*default_skill_roots(persona))}
    ]
    assert not missing, f"unresolved skill names: {missing}"
