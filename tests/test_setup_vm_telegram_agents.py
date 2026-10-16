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
