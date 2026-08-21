#!/usr/bin/env python3
"""Create Hermes-free VM deployment files for the six Sak Family Telegram bots."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

AGENTS = {
    # Models preserved from infra/vm-agents/sakthai-agent-run.sh, the Key Vault
    # entry point this deployment retired. That script carried per-agent models
    # which this table had flattened to gpt-4o-mini for all six.
    "sakking": {"model": "model-router", "skills": ""},
    "sakthai": {"model": "gpt-4o-mini", "skills": ""},
    "saksee": {"model": "gpt-5.4-mini", "skills": "playwright"},
    "saksit": {"model": "Phi-4-mini-reasoning", "skills": ""},
    "saktan": {"model": "gpt-4o-mini", "skills": ""},
    "sakjules": {"model": "gpt-4o-mini", "skills": ""},
}


@dataclass(frozen=True)
class VmDeployment:
    repo_root: Path
    target_dir: Path
    config_dir: Path
    systemd_dir: Path
    env_files: dict[str, Path]
    common_env_file: Path
    service_file: Path


def parse_user_ids(raw: str) -> list[int]:
    return [int(value) for value in raw.replace(",", " ").split()]


DEFAULT_IMAGE_NAME = "ghcr.io/beer-sakthai/sak-family-agent:latest"


def _render_common_env(
    *, openai_base_url: str, openai_api_key: str, image_name: str
) -> str:
    return (
        f"IMAGE_NAME={image_name}\n"
        f"OPENAI_BASE_URL={openai_base_url}\n"
        f"OPENAI_API_KEY={openai_api_key}\n"
        "SAKTHAI_PROVIDER=openai\n"
    )


def _render_agent_env(
    *,
    agent: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
) -> str:
    """Render one agent's env file.

    SAKTHAI_HOME, SAKTHAI_PERSONA and SAKTHAI_SYSTEM_PROMPT_FILE are
    deliberately absent: the systemd unit derives all three from the instance
    name (%i). systemd applies EnvironmentFile *after* Environment=, so writing
    them here would override the unit.

    This is also a bug fix. The previous version wrote
    ``SAKTHAI_HOME={shared_sakthai_home}`` — the *same* value for every agent,
    taken from a single ``--shared-sakthai-home`` flag whose documented value
    was ``~/.sakthai``. All six personas therefore shared one memory database,
    silently merging their facts and cycle-stage state, which is precisely what
    the env templates warn against.
    """
    spec = AGENTS[agent]
    lines = [
        f"TELEGRAM_BOT_TOKEN={telegram_bot_token}",
        "TELEGRAM_ALLOWED_USER_IDS="
        + ",".join(str(user_id) for user_id in telegram_allowed_user_ids),
        f"SAKTHAI_MODEL={spec['model']}",
        f"SAKTHAI_WITH_SKILLS={spec['skills']}",
        "SAKTHAI_FAST=1",
    ]
    return "\n".join(lines) + "\n"


def build_vm_bundle(
    *,
    repo_root: Path,
    target_dir: Path,
    openai_base_url: str,
    openai_api_key: str,
    telegram_bot_tokens: dict[str, str],
    telegram_allowed_user_ids: list[int],
    image_name: str = DEFAULT_IMAGE_NAME,
) -> VmDeployment:
    repo_root = repo_root.resolve()
    target_dir = target_dir.resolve()
    config_dir = target_dir / "config"
    systemd_dir = target_dir / "systemd"
    import os

    config_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(config_dir, 0o700)
    except OSError:
        pass
    systemd_dir.mkdir(parents=True, exist_ok=True)

    common_env_file = config_dir / "common.env"
    common_env_file.write_text(
        _render_common_env(
            openai_base_url=openai_base_url,
            openai_api_key=openai_api_key,
            image_name=image_name,
        ),
        encoding="utf-8",
    )
    try:
        os.chmod(common_env_file, 0o600)
    except OSError:
        pass

    env_files: dict[str, Path] = {}
    for agent in AGENTS:
        env_file = config_dir / f"{agent}.env"
        env_file.write_text(
            _render_agent_env(
                agent=agent,
                telegram_bot_token=telegram_bot_tokens[agent],
                telegram_allowed_user_ids=telegram_allowed_user_ids,
            ),
            encoding="utf-8",
        )
        try:
            os.chmod(env_file, 0o600)
        except OSError:
            pass
        env_files[agent] = env_file

    service_src = (
        repo_root / "infra" / "vm-agents" / "systemd" / "sakthai-telegram@.service"
    )
    service_file = systemd_dir / "sakthai-telegram@.service"
    shutil.copy2(service_src, service_file)

    return VmDeployment(
        repo_root=repo_root,
        target_dir=target_dir,
        config_dir=config_dir,
        systemd_dir=systemd_dir,
        env_files=env_files,
        common_env_file=common_env_file,
        service_file=service_file,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--openai-base-url", required=True)
    parser.add_argument("--openai-api-key", required=True)
    parser.add_argument("--telegram-allowed-user-ids", required=True)
    # `--shared-sakthai-home` was removed deliberately: it wrote one
    # SAKTHAI_HOME into all six agent env files, merging every persona's memory
    # into a single database. The systemd unit now derives a per-persona shard
    # from the instance name instead.
    parser.add_argument(
        "--image-name",
        default=DEFAULT_IMAGE_NAME,
        help="Published image the systemd unit pulls; pin to a digest for production.",
    )
    for agent in AGENTS:
        parser.add_argument(f"--{agent}-telegram-bot-token", required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    tokens = {agent: getattr(args, f"{agent}_telegram_bot_token") for agent in AGENTS}
    bundle = build_vm_bundle(
        repo_root=args.repo_root,
        target_dir=args.target_dir,
        openai_base_url=args.openai_base_url,
        openai_api_key=args.openai_api_key,
        telegram_bot_tokens=tokens,
        telegram_allowed_user_ids=parse_user_ids(args.telegram_allowed_user_ids),
        image_name=args.image_name,
    )
    print(f"Wrote common env: {bundle.common_env_file}")
    for agent, env_file in bundle.env_files.items():
        print(f"Wrote {agent} env: {env_file}")
    print(f"Wrote systemd unit: {bundle.service_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())