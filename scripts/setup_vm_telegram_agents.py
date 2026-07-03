#!/usr/bin/env python3
"""Create Hermes-free VM deployment files for the six Sak Family Telegram bots."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

AGENTS = {
    "sakking": {
        "model": "gpt-4o-mini",
        "persona": "personas/sakking/SOUL.md",
        "skills": "",
    },
    "sakthai": {
        "model": "gpt-4o-mini",
        "persona": "personas/sakthai/SOUL.md",
        "skills": "",
    },
    "saksee": {
        "model": "gpt-5.4-mini",
        "persona": "personas/saksee/SOUL.md",
        "skills": "playwright",
    },
    "saksit": {
        "model": "kimi-k2.7-code",
        "persona": "personas/saksit/SOUL.md",
        "skills": "",
    },
    "saktan": {
        "model": "gpt-4o-mini",
        "persona": "personas/saktan/SOUL.md",
        "skills": "",
    },
    "sakjules": {
        "model": "gpt-4o-mini",
        "persona": "personas/sakjules/SOUL.md",
        "skills": "",
    },
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


def _render_common_env(*, openai_base_url: str, openai_api_key: str) -> str:
    return (
        f"OPENAI_BASE_URL={openai_base_url}\n"
        f"OPENAI_API_KEY={openai_api_key}\n"
        "SAKTHAI_PROVIDER=openai\n"
    )


def _render_agent_env(
    *,
    repo_root: Path,
    agent: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
    sakthai_home: Path,
) -> str:
    spec = AGENTS[agent]
    lines = [
        f"TELEGRAM_BOT_TOKEN={telegram_bot_token}",
        "TELEGRAM_ALLOWED_USER_IDS=" + ",".join(str(user_id) for user_id in telegram_allowed_user_ids),
        f"SAKTHAI_MODEL={spec['model']}",
        f"SAKTHAI_SYSTEM_PROMPT_FILE={repo_root / spec['persona']}",
        f"SAKTHAI_WITH_SKILLS={spec['skills']}",
        "SAKTHAI_FAST=1",
        f"SAKTHAI_HOME={sakthai_home}",
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
    shared_sakthai_home: Path,
) -> VmDeployment:
    repo_root = repo_root.resolve()
    target_dir = target_dir.resolve()
    config_dir = target_dir / "config"
    systemd_dir = target_dir / "systemd"
    config_dir.mkdir(parents=True, exist_ok=True)
    systemd_dir.mkdir(parents=True, exist_ok=True)

    common_env_file = config_dir / "common.env"
    common_env_file.write_text(
        _render_common_env(openai_base_url=openai_base_url, openai_api_key=openai_api_key),
        encoding="utf-8",
    )

    env_files: dict[str, Path] = {}
    for agent in AGENTS:
        env_file = config_dir / f"{agent}.env"
        env_file.write_text(
            _render_agent_env(
                repo_root=repo_root,
                agent=agent,
                telegram_bot_token=telegram_bot_tokens[agent],
                telegram_allowed_user_ids=telegram_allowed_user_ids,
                sakthai_home=shared_sakthai_home,
            ),
            encoding="utf-8",
        )
        env_files[agent] = env_file

    service_src = repo_root / "infra" / "vm-agents" / "systemd" / "sakthai-telegram@.service"
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
    parser.add_argument("--shared-sakthai-home", type=Path, required=True)
    for agent in AGENTS:
        parser.add_argument(f"--{agent}-telegram-bot-token", required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    tokens = {
        agent: getattr(args, f"{agent}_telegram_bot_token") for agent in AGENTS
    }
    bundle = build_vm_bundle(
        repo_root=args.repo_root,
        target_dir=args.target_dir,
        openai_base_url=args.openai_base_url,
        openai_api_key=args.openai_api_key,
        telegram_bot_tokens=tokens,
        telegram_allowed_user_ids=parse_user_ids(args.telegram_allowed_user_ids),
        shared_sakthai_home=args.shared_sakthai_home,
    )
    print(f"Wrote common env: {bundle.common_env_file}")
    for agent, env_file in bundle.env_files.items():
        print(f"Wrote {agent} env: {env_file}")
    print(f"Wrote systemd unit: {bundle.service_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
