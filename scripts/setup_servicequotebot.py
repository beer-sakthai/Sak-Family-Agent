#!/usr/bin/env python3
"""Bundle a customer-specific ServiceQuoteBot deployment."""

from __future__ import annotations

import argparse
import subprocess
import shutil
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BundleResult:
    """Result of building a customer bundle."""

    env_file: Path
    service_file: Path
    ingest_command: list[str]


def _render_env_file(
    *,
    anthropic_api_key: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
    target_dir: Path,
) -> str:
    """Render the content of the .env file."""
    sakthai_home = target_dir / ".sakthai-servicequotebot"
    lines = [
        f'ANTHROPIC_API_KEY="{anthropic_api_key}"',
        f'TELEGRAM_BOT_TOKEN="{telegram_bot_token}"',
        f'TELEGRAM_ALLOWED_USER_IDS="{",".join(map(str, telegram_allowed_user_ids))}"',
        f'SAKTHAI_HOME="{sakthai_home}"',
    ]
    return "\n".join(lines) + "\n"


def _render_service_file(*, repo_root: Path, env_file: Path, sakthai_home: Path) -> str:
    """Render the content of the systemd service file."""
    template_path = (
        repo_root / "infra" / "servicequotebot" / "systemd" / "servicequotebot.service"
    )
    template = template_path.read_text(encoding="utf-8")
    return template.replace(
        "WorkingDirectory=__REPO_ROOT__", f"WorkingDirectory={repo_root}"
    ).replace(
        "EnvironmentFile=__ENV_FILE__", f"EnvironmentFile={env_file}"
    ).replace(f"SAKTHAI_HOME=__SAKTHAI_HOME__", f"SAKTHAI_HOME={sakthai_home}")


def build_customer_bundle(
    *,
    target_dir: Path,
    repo_root: Path,
    anthropic_api_key: str,
    telegram_bot_token: str,
    telegram_allowed_user_ids: list[int],
    price_book: Path,
) -> BundleResult:
    """Create the customer deployment bundle."""
    # Resolve paths to be absolute for the service file
    repo_root = repo_root.resolve()
    target_dir = target_dir.resolve()
    price_book = price_book.resolve()

    systemd_dir = target_dir / "systemd"
    systemd_dir.mkdir(parents=True, exist_ok=True)

    sakthai_home = target_dir / ".sakthai-servicequotebot"
    env_file = target_dir / "servicequotebot.env"
    env_content = _render_env_file(
        anthropic_api_key=anthropic_api_key,
        telegram_bot_token=telegram_bot_token,
        telegram_allowed_user_ids=telegram_allowed_user_ids,
        target_dir=target_dir,  # This determines sakthai_home
    )
    env_file.write_text(env_content, encoding="utf-8")

    service_file = systemd_dir / "servicequotebot.service"
    service_content = _render_service_file(
        repo_root=repo_root, env_file=env_file, sakthai_home=sakthai_home
    )
    # The template in infra/ has placeholders that need to be replaced.
    service_file.write_text(service_content, encoding="utf-8")

    ingest_command = [
        "uv",
        "run",
        "sakthai",
        "ingest-document",
        str(price_book),
    ]

    return BundleResult(
        env_file=env_file,
        service_file=service_file,
        ingest_command=ingest_command,
    )


def run_ingest(command: list[str]) -> None:
    """Run the ingestion command."""
    subprocess.run(command, check=True)


def _parse_user_ids(raw_ids: str) -> list[int]:
    """Parse a comma-separated string of user IDs into a list of ints."""
    return [int(uid.strip()) for uid in raw_ids.split(",") if uid.strip()]


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True, help="Path to the repository root.")
    parser.add_argument("--target-dir", type=Path, required=True, help="Directory to create the bundle in.")
    parser.add_argument("--price-book", type=Path, required=True, help="Path to the price book markdown file.")
    parser.add_argument("--anthropic-api-key", required=True, help="Anthropic API key.")
    parser.add_argument("--telegram-bot-token", required=True, help="Telegram bot token.")
    parser.add_argument("--telegram-allowed-user-ids", required=True, help="Comma-separated list of allowed Telegram user IDs.")
    parser.add_argument("--run-ingest", action="store_true", help="Run the price book ingestion after creating the bundle.")
    return parser


def main() -> None:
    """Main entry point for the CLI."""
    args = _build_parser().parse_args()

    user_ids = _parse_user_ids(args.telegram_allowed_user_ids)

    bundle = build_customer_bundle(
        target_dir=args.target_dir,
        repo_root=args.repo_root,
        anthropic_api_key=args.anthropic_api_key,
        telegram_bot_token=args.telegram_bot_token,
        telegram_allowed_user_ids=user_ids,
        price_book=args.price_book,
    )

    print(f"ServiceQuoteBot bundle created at: {args.target_dir}")
    print(f"  - Environment file: {bundle.env_file}")
    print(f"  - Systemd service file: {bundle.service_file}")

    if args.run_ingest:
        print("\nIngesting price book...")
        try:
            run_ingest(bundle.ingest_command)
            print("Ingestion complete.")
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            print(f"Error during ingestion: {e}")
            raise SystemExit(1) from e


if __name__ == "__main__":
    main()
