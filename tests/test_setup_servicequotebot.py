"""Tests for the ServiceQuoteBot customer bootstrap script."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Mark all tests in this file as TDD
pytestmark = pytest.mark.tdd


def test_setup_script_exists_and_is_importable() -> None:
    """Verify that the setup script exists and can be imported without errors."""
    try:
        import scripts.setup_servicequotebot  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Could not import scripts.setup_servicequotebot: {e}")


def test_build_customer_bundle_writes_env_and_service_files(tmp_path: Path) -> None:
    """Test that build_customer_bundle creates the correct .env and service files."""
    from scripts.setup_servicequotebot import build_customer_bundle

    repo_root = tmp_path / "Sak-Family-Agent"
    target_dir = tmp_path / "customer_bundle"
    price_book_path = repo_root / "data" / "price-book.md"

    # Create dummy infra file for the script to copy
    infra_dir = repo_root / "infra" / "servicequotebot" / "systemd"
    infra_dir.mkdir(parents=True, exist_ok=True)
    service_template_path = infra_dir / "servicequotebot.service"
    service_template_path.write_text(
        "[Unit]\nDescription=ServiceQuoteBot\n\n[Service]\nExecStart=\n"
    )

    result = build_customer_bundle(
        target_dir=target_dir,
        repo_root=repo_root,
        anthropic_api_key="sk-test-anthropic",
        telegram_bot_token="12345:telegram-token",
        telegram_allowed_user_ids=[98765],
        price_book=price_book_path,
    )

    assert result.env_file.exists()
    assert result.service_file.exists()
    assert result.ingest_command

    env_content = result.env_file.read_text()
    assert 'ANTHROPIC_API_KEY="sk-test-anthropic"' in env_content
    assert 'TELEGRAM_BOT_TOKEN="12345:telegram-token"' in env_content
    assert 'TELEGRAM_ALLOWED_USER_IDS="98765"' in env_content
    assert f'SAKTHAI_HOME="{target_dir / ".sakthai-servicequotebot"}"' in env_content

    service_content = result.service_file.read_text()
    assert service_content.startswith("[Unit]")

    assert result.service_file.parent == target_dir / "systemd"


@patch("scripts.setup_servicequotebot.build_customer_bundle")
@patch("scripts.setup_servicequotebot.run_ingest")
def test_main_cli_flow(
    mock_run_ingest, mock_build_bundle, tmp_path: Path, capsys
) -> None:
    """Test the main function CLI argument parsing and flow."""
    from scripts.setup_servicequotebot import BundleResult, main

    target_dir = tmp_path / "customer_bundle"
    repo_root = tmp_path / "repo"
    price_book = repo_root / "price.md"

    mock_build_bundle.return_value = BundleResult(
        env_file=target_dir / "servicequotebot.env",
        service_file=target_dir / "systemd" / "servicequotebot.service",
        ingest_command=["ingest", "command"],
    )

    sys.argv = [
        "setup_servicequotebot.py",
        "--repo-root",
        str(repo_root),
        "--target-dir",
        str(target_dir),
        "--price-book",
        str(price_book),
        "--anthropic-api-key",
        "key1",
        "--telegram-bot-token",
        "token1",
        "--telegram-allowed-user-ids",
        "123,456",
        "--run-ingest",
    ]

    main()

    mock_build_bundle.assert_called_once()
    mock_run_ingest.assert_called_once_with(["ingest", "command"])

    captured = capsys.readouterr()
    assert "ServiceQuoteBot bundle created at" in captured.out
    assert "Ingesting price book..." in captured.out