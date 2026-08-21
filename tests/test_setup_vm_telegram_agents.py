from __future__ import annotations

import importlib.util
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
        image_name="ghcr.io/example/sak-family-agent@sha256:" + "0" * 64,
    )

    assert bundle.common_env_file.read_text(encoding="utf-8") == (
        "IMAGE_NAME=ghcr.io/example/sak-family-agent@sha256:" + "0" * 64 + "\n"
        "OPENAI_BASE_URL=https://example.azure.com/openai/v1\n"
        "OPENAI_API_KEY=sk-test\n"
        "SAKTHAI_PROVIDER=openai\n"
    )
    sakking_env = bundle.env_files["sakking"].read_text(encoding="utf-8")
    assert "TELEGRAM_BOT_TOKEN=sakking-token" in sakking_env
    assert "TELEGRAM_ALLOWED_USER_IDS=123,456" in sakking_env
    assert "SAKTHAI_MODEL=model-router" in sakking_env
    assert bundle.service_file.exists()


def test_generated_env_never_sets_what_the_systemd_unit_owns(tmp_path: Path) -> None:
    """The three variables the unit derives from %i must not appear in any env file.

    systemd applies ``EnvironmentFile=`` *after* ``Environment=``, so a value
    written here silently overrides the unit. That is not hypothetical: this
    generator used to write ``SAKTHAI_HOME`` into all six agent env files from a
    single ``--shared-sakthai-home`` flag, giving every persona the *same*
    memory database and merging their facts and cycle-stage state.
    """
    bundle = build_vm_bundle(
        repo_root=Path(__file__).resolve().parents[1],
        target_dir=tmp_path / "vm-bundle",
        openai_base_url="https://example.azure.com/openai/v1",
        openai_api_key="sk-test",
        telegram_bot_tokens={agent: f"{agent}-token" for agent in SCRIPT_MODULE.AGENTS},
        telegram_allowed_user_ids=[123],
    )

    unit_owned = ("SAKTHAI_HOME", "SAKTHAI_PERSONA", "SAKTHAI_SYSTEM_PROMPT_FILE")
    for agent, env_file in bundle.env_files.items():
        text = env_file.read_text(encoding="utf-8")
        for key in unit_owned:
            assert f"{key}=" not in text, (
                f"{agent}.env sets {key}, which the systemd unit derives from %i. "
                "EnvironmentFile is applied after Environment=, so this wins."
            )


def test_every_agent_gets_its_own_model(tmp_path: Path) -> None:
    """Per-agent models must survive; they were flattened to gpt-4o-mini once."""
    bundle = build_vm_bundle(
        repo_root=Path(__file__).resolve().parents[1],
        target_dir=tmp_path / "vm-bundle",
        openai_base_url="https://example.azure.com/openai/v1",
        openai_api_key="sk-test",
        telegram_bot_tokens={agent: f"{agent}-token" for agent in SCRIPT_MODULE.AGENTS},
        telegram_allowed_user_ids=[123],
    )

    models = {
        agent: next(
            line.split("=", 1)[1]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("SAKTHAI_MODEL=")
        )
        for agent, path in bundle.env_files.items()
    }
    assert models["sakking"] == "model-router"
    assert models["saksee"] == "gpt-5.4-mini"
    assert models["saksit"] == "Phi-4-mini-reasoning"

    import sys

    if sys.platform != "win32":
        assert (bundle.config_dir.stat().st_mode & 0o777) == 0o700
        assert (bundle.common_env_file.stat().st_mode & 0o777) == 0o600
        for env_file in bundle.env_files.values():
            assert (env_file.stat().st_mode & 0o777) == 0o600
