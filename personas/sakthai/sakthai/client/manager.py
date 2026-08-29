"""Client workspace manager and provisioning engine for ServiceQuoteBot."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from .. import config
from ..learn.ingest import ingest_document
from ..memory.store import MemoryStore
from .models import ClientConfig, OnboardResult, _slugify

logger = logging.getLogger(__name__)


def get_clients_base_dir() -> Path:
    """Return the root directory where all provisioned client workspaces live."""
    p = config.clients_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_client_dir(client_id: str) -> Path:
    """Return the dedicated workspace path for a specific client."""
    slug = _slugify(client_id)
    return get_clients_base_dir() / slug


def list_clients() -> list[ClientConfig]:
    """Scan the clients directory and return all discovered client configurations."""
    base = get_clients_base_dir()
    clients: list[ClientConfig] = []
    if not base.exists():
        return clients

    for item in sorted(base.iterdir()):
        if item.is_dir():
            cfg_file = item / "client.json"
            if cfg_file.is_file():
                try:
                    data = json.loads(cfg_file.read_text(encoding="utf-8"))
                    clients.append(ClientConfig.from_dict(data))
                except Exception as exc:  # noqa: BLE001
                    logger.warning("Failed to load client config %s: %s", cfg_file, exc)
    return clients


def load_client(client_id: str) -> ClientConfig:
    """Load the ClientConfig for a given client ID."""
    client_dir = get_client_dir(client_id)
    cfg_file = client_dir / "client.json"
    if not cfg_file.is_file():
        raise FileNotFoundError(f"Client '{client_id}' not found at {cfg_file}")

    data = json.loads(cfg_file.read_text(encoding="utf-8"))
    return ClientConfig.from_dict(data)


def save_client(config: ClientConfig) -> Path:
    """Persist client configuration to client.json."""
    client_dir = get_client_dir(config.client_id)
    client_dir.mkdir(parents=True, exist_ok=True)
    cfg_file = client_dir / "client.json"
    cfg_file.write_text(
        json.dumps(config.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return cfg_file


def generate_client_env(config: ClientConfig, client_dir: Path) -> Path:
    """Write an isolated .env file for the customer deployment."""
    env_file = client_dir / "client.env"
    allowed_ids_str = ",".join(str(uid) for uid in config.telegram_allowed_user_ids)

    lines = [
        "# Auto-generated ServiceQuoteBot customer environment",
        f"CLIENT_ID={config.client_id}",
        f"COMPANY_NAME={config.company_name}",
        f"CURRENCY={config.currency}",
        f"SAKTHAI_HOME={client_dir}",
        f"TELEGRAM_BOT_TOKEN={config.telegram_bot_token}",
        f"TELEGRAM_ALLOWED_USER_IDS={allowed_ids_str}",
        f"SAKTHAI_DEFAULT_MODEL={config.model}",
        f"SAKTHAI_DEFAULT_PROVIDER={config.provider}",
        f"PORT={config.port}",
    ]
    env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return env_file


def generate_systemd_service(
    config: ClientConfig,
    client_dir: Path,
    repo_root: Path | None = None,
) -> Path:
    """Generate a portable systemd user service for this client."""
    svc_dir = client_dir / "systemd"
    svc_dir.mkdir(parents=True, exist_ok=True)
    svc_file = svc_dir / f"servicequotebot-{config.client_id}.service"

    working_dir = repo_root.resolve() if repo_root else Path.cwd().resolve()
    python_bin = working_dir / ".venv" / "bin" / "python"
    exec_start = (
        f"{python_bin} -m sakthai.telegram.bot"
        if python_bin.is_file()
        else "/usr/bin/python3 -m sakthai.telegram.bot"
    )

    content = f"""[Unit]
Description=ServiceQuoteBot Gateway ({config.company_name})
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory={working_dir}
ExecStart={exec_start}
Environment=SAKTHAI_HOME={client_dir}
EnvironmentFile={client_dir / "client.env"}
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""
    svc_file.write_text(content, encoding="utf-8")
    return svc_file


def generate_docker_compose(
    config: ClientConfig,
    client_dir: Path,
    repo_root: Path | None = None,
) -> Path:
    """Generate a client-specific docker-compose.yml file."""
    compose_file = client_dir / "docker-compose.yml"
    working_dir = repo_root.resolve() if repo_root else Path.cwd().resolve()

    content = f"""version: '3.8'

services:
  servicequotebot-{config.client_id}:
    build:
      context: {working_dir}
      dockerfile: infra/servicequotebot/docker/Dockerfile
    container_name: servicequotebot-{config.client_id}
    restart: unless-stopped
    env_file:
      - {client_dir / "client.env"}
    environment:
      - SAKTHAI_HOME=/app/data
    volumes:
      - {client_dir / "data"}:/app/data
      - {client_dir / "logs"}:/app/logs
    ports:
      - "{config.port}:{config.port}"
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
"""
    compose_file.write_text(content, encoding="utf-8")
    return compose_file


def ingest_client_price_book(
    client_id: str,
    price_book_path: Path | str,
    store: MemoryStore | None = None,
) -> int:
    """Ingest pricing document into the client's memory store."""
    path = Path(price_book_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Price book file not found: {path}")

    client_dir = get_client_dir(client_id)
    target_db = client_dir / "data" / "memory.db"
    target_db.parent.mkdir(parents=True, exist_ok=True)

    target_store = store or MemoryStore(target_db)
    fact_ids = ingest_document(path, store=target_store)
    logger.info("Ingested %d facts from %s for client %s", len(fact_ids), path, client_id)
    return len(fact_ids)


def onboard_client(
    config: ClientConfig,
    repo_root: Path | None = None,
) -> OnboardResult:
    """Execute complete onboarding pipeline for a new client."""
    client_dir = get_client_dir(config.client_id)
    client_dir.mkdir(parents=True, exist_ok=True)
    (client_dir / "data").mkdir(parents=True, exist_ok=True)
    (client_dir / "logs").mkdir(parents=True, exist_ok=True)

    # 1. Save config
    cfg_file = save_client(config)

    # 2. Write client.env
    env_file = generate_client_env(config, client_dir)

    # 3. Ingest price book if provided
    ingested_count = 0
    if config.price_book_path:
        pb_path = Path(config.price_book_path)
        if pb_path.is_file():
            ingested_count = ingest_client_price_book(config.client_id, pb_path)
        else:
            logger.warning("Price book %s specified but not found on filesystem", pb_path)

    # 4. Generate deployment assets
    svc_file = generate_systemd_service(config, client_dir, repo_root=repo_root)
    compose_file = generate_docker_compose(config, client_dir, repo_root=repo_root)

    return OnboardResult(
        client_id=config.client_id,
        workspace_dir=str(client_dir),
        env_file=str(env_file),
        memory_db=str(client_dir / "data" / "memory.db"),
        ingested_facts_count=ingested_count,
        config_file=str(cfg_file),
        service_file=str(svc_file),
        compose_file=str(compose_file),
        success=True,
    )
