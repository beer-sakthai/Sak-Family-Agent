"""Unit tests for the Runtime Gateway configuration resolver."""

from __future__ import annotations

import pytest

from sakthai.gateway.config import GatewayConfig, resolve_gateway_config


def test_gateway_config_defaults() -> None:
    cfg = GatewayConfig()
    assert cfg.host == "127.0.0.1"
    assert cfg.port == 8080
    assert cfg.bearer_token is None
    assert cfg.cors_origin is None
    assert cfg.request_timeout == 60.0
    assert cfg.rate_limit_per_minute == 120
    assert cfg.default_persona == "sakthai"


def test_resolve_gateway_config_explicit() -> None:
    cfg = resolve_gateway_config(
        host="0.0.0.0",
        port=9090,
        bearer_token="secret-token-123",
        cors_origin="http://localhost:3000",
        request_timeout=30.0,
        rate_limit_per_minute=200,
        default_persona="saksee",
    )
    assert cfg.host == "0.0.0.0"
    assert cfg.port == 9090
    assert cfg.bearer_token == "secret-token-123"
    assert cfg.cors_origin == "http://localhost:3000"
    assert cfg.request_timeout == 30.0
    assert cfg.rate_limit_per_minute == 200
    assert cfg.default_persona == "saksee"


def test_resolve_gateway_config_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAKTHAI_GATEWAY_HOST", "10.0.0.1")
    monkeypatch.setenv("SAKTHAI_GATEWAY_PORT", "8888")
    monkeypatch.setenv("SAKTHAI_GATEWAY_BEARER_TOKEN", "tok-from-env")
    monkeypatch.setenv("SAKTHAI_GATEWAY_CORS_ORIGIN", "https://sakthai.app")
    monkeypatch.setenv("SAKTHAI_GATEWAY_TIMEOUT", "45.0")
    monkeypatch.setenv("SAKTHAI_GATEWAY_DEFAULT_PERSONA", "sakjules")

    cfg = resolve_gateway_config()
    assert cfg.host == "10.0.0.1"
    assert cfg.port == 8888
    assert cfg.bearer_token == "tok-from-env"
    assert cfg.cors_origin == "https://sakthai.app"
    assert cfg.request_timeout == 45.0
    assert cfg.default_persona == "sakjules"


def test_resolve_gateway_config_memorystore_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_GATEWAY_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("SAKTHAI_GATEWAY_TOKEN", raising=False)

    class DummyFact:
        value = "db-stored-token"

    class DummyStore:
        def __enter__(self) -> DummyStore:
            return self

        def __exit__(self, *args: object) -> None:
            pass

        def get_fact_by_key(self, kind: str, key: str) -> DummyFact | None:
            if kind == "web_auth" and key == "bearer_token":
                return DummyFact()
            return None

    monkeypatch.setattr("sakthai.memory.store.MemoryStore", DummyStore)

    cfg = resolve_gateway_config()
    assert cfg.bearer_token == "db-stored-token"


def test_create_gateway_server() -> None:
    from sakthai.gateway import create_gateway_server

    server = create_gateway_server(host="127.0.0.1", port=0, default_persona="sakjules")
    assert server.host == "127.0.0.1"
    assert server.config.default_persona == "sakjules"


def test_resolve_gateway_config_memorystore_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SAKTHAI_GATEWAY_BEARER_TOKEN", raising=False)
    monkeypatch.delenv("SAKTHAI_GATEWAY_TOKEN", raising=False)

    def failing_store():
        raise RuntimeError("Store failure")

    monkeypatch.setattr("sakthai.memory.store.MemoryStore", failing_store)
    cfg = resolve_gateway_config()
    assert cfg.bearer_token is None
