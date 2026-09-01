"""Unit tests for ServiceQuoteBot client manager and onboarding engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from sakthai.client import (
    ClientConfig,
    generate_client_env,
    generate_docker_compose,
    generate_systemd_service,
    get_clients_base_dir,
    list_clients,
    load_client,
    onboard_client,
    save_client,
)


def test_client_config_slugify_and_validation() -> None:
    cfg = ClientConfig(
        client_id="Acme Plumbing & Heating!",
        company_name="Acme Plumbing",
        currency="USD",
        telegram_bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11",
        telegram_allowed_user_ids=(12345, 67890),
    )
    assert cfg.client_id == "acme-plumbing-heating"
    assert cfg.company_name == "Acme Plumbing"
    assert cfg.currency == "USD"
    assert cfg.telegram_allowed_user_ids == (12345, 67890)

    # Empty validation
    with pytest.raises(ValueError, match="company_name cannot be empty"):
        ClientConfig(client_id="valid-id", company_name="   ")


def test_client_config_serialization() -> None:
    cfg = ClientConfig(
        client_id="test-client",
        company_name="Test Co",
        currency="EUR",
        telegram_bot_token="secret_token_12345678",
        telegram_allowed_user_ids=(111, 222),
    )
    data = cfg.to_dict()
    assert data["client_id"] == "test-client"
    assert data["company_name"] == "Test Co"
    assert data["currency"] == "EUR"
    assert data["telegram_allowed_user_ids"] == [111, 222]

    restored = ClientConfig.from_dict(data)
    assert restored.client_id == cfg.client_id
    assert restored.company_name == cfg.company_name
    assert restored.telegram_allowed_user_ids == (111, 222)


def test_client_config_mask_sensitive() -> None:
    cfg = ClientConfig(
        client_id="test-client",
        company_name="Test Co",
        telegram_bot_token="1234567890abcdef",
    )
    masked = cfg.mask_sensitive()
    assert masked["telegram_bot_token"] == "1234...cdef"


def test_clients_base_dir_follows_sakthai_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SAKTHAI_HOME scopes the clients dir, like every other sakthai path.

    This used to resolve from Path.home() directly, so a persona running with
    its own SAKTHAI_HOME still shared one global ~/.sakthai/clients with the
    other five.
    """
    monkeypatch.delenv("SAKTHAI_CLIENTS_DIR", raising=False)
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path / "persona-home"))

    assert get_clients_base_dir() == tmp_path / "persona-home" / "clients"


def test_clients_dir_override_beats_sakthai_home(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An explicit SAKTHAI_CLIENTS_DIR still wins over SAKTHAI_HOME."""
    monkeypatch.setenv("SAKTHAI_HOME", str(tmp_path / "ignored"))
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path / "explicit"))

    assert get_clients_base_dir() == tmp_path / "explicit"


def test_client_save_load_list(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))
    assert get_clients_base_dir() == tmp_path

    cfg1 = ClientConfig(client_id="client-one", company_name="Company One")
    cfg2 = ClientConfig(client_id="client-two", company_name="Company Two")

    save_client(cfg1)
    save_client(cfg2)

    loaded1 = load_client("client-one")
    assert loaded1.company_name == "Company One"

    all_clients = list_clients()
    assert len(all_clients) == 2
    ids = {c.client_id for c in all_clients}
    assert "client-one" in ids
    assert "client-two" in ids


def test_load_nonexistent_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(tmp_path))
    with pytest.raises(FileNotFoundError, match="not found"):
        load_client("nonexistent")


def test_generate_client_assets(tmp_path: Path) -> None:
    client_dir = tmp_path / "client-test"
    client_dir.mkdir(parents=True)

    cfg = ClientConfig(
        client_id="client-test",
        company_name="Test Biz",
        currency="GBP",
        telegram_bot_token="test-bot-token",
        telegram_allowed_user_ids=(999,),
        port=9090,
    )

    env_file = generate_client_env(cfg, client_dir)
    assert env_file.is_file()
    env_content = env_file.read_text()
    assert "CLIENT_ID=client-test" in env_content
    assert "COMPANY_NAME=Test Biz" in env_content
    assert "CURRENCY=GBP" in env_content
    assert "PORT=9090" in env_content

    svc_file = generate_systemd_service(cfg, client_dir, repo_root=tmp_path)
    assert svc_file.is_file()
    svc_content = svc_file.read_text()
    assert "Description=ServiceQuoteBot Gateway (Test Biz)" in svc_content
    assert f"WorkingDirectory={tmp_path.resolve()}" in svc_content

    compose_file = generate_docker_compose(cfg, client_dir, repo_root=tmp_path)
    assert compose_file.is_file()
    compose_content = compose_file.read_text()
    assert "servicequotebot-client-test:" in compose_content
    assert '"9090:9090"' in compose_content


def test_onboard_client_with_price_book(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    clients_dir = tmp_path / "clients"
    monkeypatch.setenv("SAKTHAI_CLIENTS_DIR", str(clients_dir))

    price_book = tmp_path / "prices.md"
    price_book.write_text(
        "# Services\n- Oil Change: $50\n- Brake Inspection: $80\n- Tire Rotation: $30\n",
        encoding="utf-8",
    )

    cfg = ClientConfig(
        client_id="auto-shop",
        company_name="Quick Auto",
        price_book_path=str(price_book),
        currency="USD",
    )

    result = onboard_client(cfg, repo_root=tmp_path)
    assert result.success is True
    assert result.client_id == "auto-shop"
    assert result.ingested_facts_count == 3
    assert Path(result.memory_db).is_file()
    assert Path(result.env_file).is_file()
    assert Path(result.config_file).is_file()
