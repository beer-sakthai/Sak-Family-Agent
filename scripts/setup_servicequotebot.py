#!/usr/bin/env python3
"""Bundle a customer-specific ServiceQuoteBot deployment."""

from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path

from sakthai.learn.ingest import ingest_document
from sakthai.memory.store import MemoryStore

SERVICE_TEMPLATE = Path("infra/servicequotebot/systemd/servicequotebot.service")


@dataclass(frozen=True)
class CustomerDeployment:
    repo_root: Path
    target_dir: Path
    config_dir: Path
    systemd_dir: Path
    state_dir: Path
    env_file: Path
    service_file: Path
    price_book_copy: Path
    memory_db: Path
    ingested_fact_ids: list[int]


def parse_user_ids(raw: str) -> list[int]:
    cleaned = raw.replace(",", " ").split()
    return [int(value) for value in cleaned]


def _render_env_file(
    *,
    anthropic_api_key: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
    sakthai_home: Path,
) -> str:
    lines = [
        f"ANTHROPIC_API_KEY={anthropic_api_key}",
        f"TELEGRAM_BOT_TOKEN={telegram_bot_token}",
        "TELEGRAM_ALLOWED_USER_IDS="
        + ",".join(str(user_id) for user_id in telegram_allowed_user_ids),
        f"SAKTHAI_HOME={sakthai_home}",
    ]
    return "\n".join(lines) + "\n"


def _render_service_file(repo_root: Path, env_file: Path, sakthai_home: Path) -> str:
    template = (repo_root / SERVICE_TEMPLATE).read_text(encoding="utf-8")
    return (
        template.replace("__REPO_ROOT__", str(repo_root))
        .replace("__ENV_FILE__", str(env_file))
        .replace("__SAKTHAI_HOME__", str(sakthai_home))
    )


def build_customer_bundle(
    *,
    repo_root: Path,
    target_dir: Path,
    price_book: Path,
    anthropic_api_key: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
) -> CustomerDeployment:
    repo_root = repo_root.resolve()
    target_dir = target_dir.resolve()
    config_dir = target_dir / "config"
    systemd_dir = target_dir / "systemd"
    state_dir = target_dir / "state" / "sakthai"
    inputs_dir = target_dir / "inputs"
    price_book_copy = inputs_dir / price_book.name
    env_file = config_dir / "servicequotebot.env"
    service_file = systemd_dir / "servicequotebot.service"
    memory_db = state_dir / "memory.db"

    config_dir.mkdir(parents=True, exist_ok=True)
    systemd_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)
    inputs_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(price_book, price_book_copy)
    env_file.write_text(
        _render_env_file(
            anthropic_api_key=anthropic_api_key,
            telegram_bot_token=telegram_bot_token,
            telegram_allowed_user_ids=telegram_allowed_user_ids,
            sakthai_home=state_dir,
        ),
        encoding="utf-8",
    )
    service_file.write_text(
        _render_service_file(repo_root, env_file, state_dir),
        encoding="utf-8",
    )

    ingested_fact_ids: list[int] = []
    with MemoryStore(memory_db) as store:
        ingested_fact_ids.extend(ingest_document(price_book_copy, store=store))

    return CustomerDeployment(
        repo_root=repo_root,
        target_dir=target_dir,
        config_dir=config_dir,
        systemd_dir=systemd_dir,
        state_dir=state_dir,
        env_file=env_file,
        service_file=service_file,
        price_book_copy=price_book_copy,
        memory_db=memory_db,
        ingested_fact_ids=ingested_fact_ids,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--target-dir", type=Path, required=True)
    parser.add_argument("--price-book", type=Path, required=True)
    parser.add_argument("--anthropic-api-key", required=True)
    parser.add_argument("--telegram-bot-token", required=True)
    parser.add_argument("--telegram-allowed-user-ids", required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    bundle = build_customer_bundle(
        repo_root=args.repo_root,
        target_dir=args.target_dir,
        price_book=args.price_book,
        anthropic_api_key=args.anthropic_api_key,
        telegram_bot_token=args.telegram_bot_token,
        telegram_allowed_user_ids=parse_user_ids(args.telegram_allowed_user_ids),
    )
    print(f"Wrote env file: {bundle.env_file}")
    print(f"Wrote systemd unit: {bundle.service_file}")
    print(f"Copied price book: {bundle.price_book_copy}")
    print(f"Seeded memory DB: {bundle.memory_db}")
    print(f"Ingested facts: {len(bundle.ingested_fact_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
