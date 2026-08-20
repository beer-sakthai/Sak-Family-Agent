# Microsoft 365 Copilot Studio Provider Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `copilotstudio` as a sixth `sakthai run`/`chat` provider, backed by a Microsoft 365 Copilot Studio agent called through the Bot Framework Connector API.

**Architecture:** New `agent/providers/copilotstudio_provider.py` module implementing `call_copilotstudio(...)` with the same external shape as `call_openai_compat`. Auth goes through a new `resolve_copilotstudio_credentials()` in `auth.py` (Entra client-credentials via `msal`, scoped to `https://api.botframework.com/.default`), wired into `providers/__init__.py`'s `build_client`/`detect_provider` exactly like the other five providers. New config in `config.py`, new env vars in `.env.example`/`CLAUDE.md`.

**Tech Stack:** Python 3.11+, `httpx` (already a dependency, reused for the Connector API calls), `msal` (new dependency), `pytest` + `httpx.MockTransport` for wire-contract tests.

## Global Constraints

- Spec source of truth: `docs/superpowers/specs/2026-08-05-m365-copilot-studio-provider-design.md`.
- Edit only `personas/sakthai/sakthai/` (the canonical, installed copy) for logic changes — `config.py` and `agent/providers/__init__.py` are already known-diverged from `personas/shared/sakthai/` per `Sak-Family-Agent/CLAUDE.md`, so editing only the canonical copy is consistent with existing practice.
- The **new** `copilotstudio_provider.py` module must be mirrored byte-for-byte into `personas/shared/sakthai/agent/providers/` — unlike `config.py`/`__init__.py`, the other provider implementation files (`anthropic_provider.py`, `openai_provider.py`, `gemini_provider.py`, `base.py`) are IDENTICAL between the two copies today (confirmed via `sakthai-skills-validate`'s drift check), so a brand-new provider file should keep that parity rather than starting diverged.
- `mypy --strict` covers the whole `sakthai/` package with no per-module exceptions — all new code must be strict-clean.
- Tests are hermetic: no real network calls, no real credentials. Mock `msal` and `httpx` at the boundary.
- No module hardcodes a path or secret name — everything new goes through `config.py`.
- Never write the real `MS365_COPILOT_*` values (the Application ID shared earlier in chat, or any secret) into any file this plan touches. Only variable *names* appear in `.env.example`/`CLAUDE.md`.
- Windows-side git note: `git commit` against this repo hangs indefinitely when run over the `\\wsl.localhost\Ubuntu\...` UNC path — use `wsl.exe -d Ubuntu -- git -C /home/beern/Sak-Family-Agent commit ...` for every commit step below. `git status`/`add`/`diff` are fine over UNC.

---

### Task 1: Add the `msal` dependency

**Files:**
- Modify: `pyproject.toml:12-22` (the `dependencies` list)

**Interfaces:**
- Produces: `msal` importable at runtime for Task 3.

- [ ] **Step 1: Add the dependency**

Edit the `dependencies` array in `pyproject.toml`:

```toml
dependencies = [
    "click>=8.4.2,<9.0",
    "pyyaml>=6.0,<7.0",
    "anthropic>=0.120.2,<1.0",
    "httpx>=0.20.0",
    "google-genai>=2.14.0",
    "tenacity>=8.0,<10.0",
    "python-telegram-bot==22.8",
    "rich>=15.0.0,<16.0",
    "prompt-toolkit>=3.0.53,<4.0",
    "msal>=1.28.0,<2.0",
]
```

- [ ] **Step 2: Sync the environment**

Run (via native WSL, not the UNC path, to avoid the same class of slowness seen with git):

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv sync --all-extras"
```

Expected: completes without error; `msal` appears in `uv.lock`.

- [ ] **Step 3: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add pyproject.toml uv.lock && git commit -m 'build: add msal dependency for Copilot Studio provider'"
```

---

### Task 2: `config.py` accessors

**Files:**
- Modify: `personas/sakthai/sakthai/config.py` (add near `gateway_base_url`/`huggingface_api_base`, around line 265)
- Test: `tests/test_config_reports.py` (add a new test function; follow the existing style in that file for env-var-backed accessors)

**Interfaces:**
- Produces: `ms365_copilot_tenant_id() -> str | None`, `ms365_copilot_client_id() -> str | None`, `ms365_copilot_client_secret() -> str | None`, `ms365_copilot_bot_id() -> str | None`, `ms365_copilot_service_url() -> str` — all consumed by Task 3.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_config_reports.py`:

```python
def test_ms365_copilot_accessors_read_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MS365_COPILOT_TENANT_ID", "tenant-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_ID", "client-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("MS365_COPILOT_BOT_ID", "bot-1")

    assert config.ms365_copilot_tenant_id() == "tenant-1"
    assert config.ms365_copilot_client_id() == "client-1"
    assert config.ms365_copilot_client_secret() == "secret-1"
    assert config.ms365_copilot_bot_id() == "bot-1"


def test_ms365_copilot_accessors_default_to_none(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in (
        "MS365_COPILOT_TENANT_ID",
        "MS365_COPILOT_CLIENT_ID",
        "MS365_COPILOT_CLIENT_SECRET",
        "MS365_COPILOT_BOT_ID",
    ):
        monkeypatch.delenv(var, raising=False)

    assert config.ms365_copilot_tenant_id() is None
    assert config.ms365_copilot_client_id() is None
    assert config.ms365_copilot_client_secret() is None
    assert config.ms365_copilot_bot_id() is None


def test_ms365_copilot_service_url_default_and_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MS365_COPILOT_SERVICE_URL", raising=False)
    assert config.ms365_copilot_service_url() == "https://smba.trafficmanager.net/teams"

    monkeypatch.setenv("MS365_COPILOT_SERVICE_URL", "https://custom.example.com/api/")
    assert config.ms365_copilot_service_url() == "https://custom.example.com/api"
```

(Check the top of `tests/test_config_reports.py` for how `config` is imported — match that import style rather than adding a new one.)

- [ ] **Step 2: Run tests to verify they fail**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_config_reports.py -k ms365_copilot -v"
```

Expected: FAIL with `AttributeError: module 'sakthai.config' has no attribute 'ms365_copilot_tenant_id'` (and similarly for the others).

- [ ] **Step 3: Implement the accessors**

Add to `personas/sakthai/sakthai/config.py`, near `gateway_base_url`/`huggingface_api_base`:

```python
def ms365_copilot_tenant_id() -> str | None:
    """Return the Entra tenant ID for the Microsoft 365 Copilot Studio provider."""
    return os.environ.get("MS365_COPILOT_TENANT_ID")


def ms365_copilot_client_id() -> str | None:
    """Return the Entra app (client) ID for the Microsoft 365 Copilot Studio provider."""
    return os.environ.get("MS365_COPILOT_CLIENT_ID")


def ms365_copilot_client_secret() -> str | None:
    """Return the Entra app client secret for the Microsoft 365 Copilot Studio provider."""
    return os.environ.get("MS365_COPILOT_CLIENT_SECRET")


def ms365_copilot_bot_id() -> str | None:
    """Return the target Copilot Studio agent's Bot Framework App ID.

    This is the conversation *recipient* — distinct from
    ``ms365_copilot_client_id()``, which identifies the calling Entra app.
    """
    return os.environ.get("MS365_COPILOT_BOT_ID")


def ms365_copilot_service_url() -> str:
    """Return the Bot Framework Connector service URL.

    Defaults to the global Connector endpoint; honors
    ``MS365_COPILOT_SERVICE_URL`` for a region-pinned or sovereign-cloud
    deployment.
    """
    return os.environ.get(
        "MS365_COPILOT_SERVICE_URL", "https://smba.trafficmanager.net/teams"
    ).rstrip("/")
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_config_reports.py -k ms365_copilot -v"
```

Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add personas/sakthai/sakthai/config.py tests/test_config_reports.py && git commit -m 'feat(config): add MS365 Copilot Studio config accessors'"
```

---

### Task 3: `auth.py` credential resolution

**Files:**
- Modify: `personas/sakthai/sakthai/auth.py` (add near `resolve_huggingface_credentials`/`openai_credential_source`)
- Test: `tests/test_auth.py` (add new test functions; follow existing style — see how `resolve_gateway_credentials`/`resolve_huggingface_credentials` are tested there for the mocking pattern used with `monkeypatch`)

**Interfaces:**
- Consumes: `ms365_copilot_tenant_id()`, `ms365_copilot_client_id()`, `ms365_copilot_client_secret()`, `ms365_copilot_bot_id()`, `ms365_copilot_service_url()` from Task 2.
- Produces: `ms365_copilot_credential_source() -> str | None`, `resolve_copilotstudio_credentials() -> tuple[str, str]` (returns `(service_url, bearer_token)`) — both consumed by Task 6.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_auth.py`:

```python
def test_ms365_copilot_credential_source_none_when_incomplete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in (
        "MS365_COPILOT_TENANT_ID",
        "MS365_COPILOT_CLIENT_ID",
        "MS365_COPILOT_CLIENT_SECRET",
        "MS365_COPILOT_BOT_ID",
    ):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("MS365_COPILOT_TENANT_ID", "tenant-1")
    # client_id, client_secret, bot_id still unset.

    assert auth.ms365_copilot_credential_source() is None


def test_ms365_copilot_credential_source_present_when_complete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("MS365_COPILOT_TENANT_ID", "tenant-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_ID", "client-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_SECRET", "secret-1")
    monkeypatch.setenv("MS365_COPILOT_BOT_ID", "bot-1")

    assert auth.ms365_copilot_credential_source() == "ms365_copilot_client_credentials"


def test_resolve_copilotstudio_credentials_raises_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for var in ("MS365_COPILOT_TENANT_ID", "MS365_COPILOT_CLIENT_ID", "MS365_COPILOT_CLIENT_SECRET"):
        monkeypatch.delenv(var, raising=False)

    with pytest.raises(auth.AuthError, match="Microsoft 365 Copilot Studio"):
        auth.resolve_copilotstudio_credentials()


def test_resolve_copilotstudio_credentials_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MS365_COPILOT_TENANT_ID", "tenant-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_ID", "client-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_SECRET", "secret-1")
    monkeypatch.delenv("MS365_COPILOT_SERVICE_URL", raising=False)

    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {"access_token": "tok-abc"}
    monkeypatch.setattr(
        "msal.ConfidentialClientApplication", MagicMock(return_value=fake_app)
    )

    service_url, token = auth.resolve_copilotstudio_credentials()

    assert service_url == "https://smba.trafficmanager.net/teams"
    assert token == "tok-abc"
    fake_app.acquire_token_for_client.assert_called_once_with(
        scopes=["https://api.botframework.com/.default"]
    )


def test_resolve_copilotstudio_credentials_token_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MS365_COPILOT_TENANT_ID", "tenant-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_ID", "client-1")
    monkeypatch.setenv("MS365_COPILOT_CLIENT_SECRET", "secret-1")

    fake_app = MagicMock()
    fake_app.acquire_token_for_client.return_value = {
        "error": "invalid_client",
        "error_description": "bad secret",
    }
    monkeypatch.setattr(
        "msal.ConfidentialClientApplication", MagicMock(return_value=fake_app)
    )

    with pytest.raises(auth.AuthError, match="token acquisition failed"):
        auth.resolve_copilotstudio_credentials()
```

(Check the top of `tests/test_auth.py` for its existing `import auth` / `from unittest.mock import MagicMock` style and match it — do not add a second, differently-named import.)

- [ ] **Step 2: Run tests to verify they fail**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_auth.py -k ms365_copilot -v"
```

Expected: FAIL — `AttributeError: module 'sakthai.auth' has no attribute 'ms365_copilot_credential_source'`.

- [ ] **Step 3: Implement**

Add to `personas/sakthai/sakthai/auth.py`, near `resolve_huggingface_credentials`:

```python
def ms365_copilot_credential_source() -> str | None:
    """Return a short label for the active M365 Copilot Studio credential set, or None."""
    from .config import (
        ms365_copilot_bot_id,
        ms365_copilot_client_id,
        ms365_copilot_client_secret,
        ms365_copilot_tenant_id,
    )

    if (
        ms365_copilot_tenant_id()
        and ms365_copilot_client_id()
        and ms365_copilot_client_secret()
        and ms365_copilot_bot_id()
    ):
        return "ms365_copilot_client_credentials"
    return None


def resolve_copilotstudio_credentials() -> tuple[str, str]:
    """Resolve the Bot Framework Connector service URL and a bearer token.

    Raises :class:`AuthError` when ``MS365_COPILOT_TENANT_ID``,
    ``MS365_COPILOT_CLIENT_ID``, or ``MS365_COPILOT_CLIENT_SECRET`` is
    missing, or when Entra client-credentials token acquisition fails.

    Returns:
        (service_url, bearer_token)
    """
    from .config import (
        ms365_copilot_client_id,
        ms365_copilot_client_secret,
        ms365_copilot_service_url,
        ms365_copilot_tenant_id,
    )

    tenant_id = ms365_copilot_tenant_id()
    client_id = ms365_copilot_client_id()
    client_secret = ms365_copilot_client_secret()
    if not (tenant_id and client_id and client_secret):
        raise AuthError(
            "No Microsoft 365 Copilot Studio credentials found. Set "
            "MS365_COPILOT_TENANT_ID, MS365_COPILOT_CLIENT_ID, and "
            "MS365_COPILOT_CLIENT_SECRET to authenticate via Entra app "
            "client credentials."
        )

    import msal

    app = msal.ConfidentialClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(
        scopes=["https://api.botframework.com/.default"]
    )
    access_token = result.get("access_token")
    if not access_token:
        detail = result.get("error_description", result.get("error", "unknown error"))
        raise AuthError(f"Microsoft 365 Copilot Studio token acquisition failed: {detail}")

    return ms365_copilot_service_url(), access_token
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_auth.py -k ms365_copilot -v"
```

Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add personas/sakthai/sakthai/auth.py tests/test_auth.py && git commit -m 'feat(auth): resolve MS365 Copilot Studio credentials via msal'"
```

---

### Task 4: `copilotstudio_provider.py` — wire-contract tests (written first, red)

**Files:**
- Test: `tests/test_providers_copilotstudio.py` (new — mirrors the `httpx.MockTransport` pattern in `tests/test_provider_contracts.py`)

**Interfaces:**
- Consumes (not yet implemented — this is the failing-test step): `call_copilotstudio(client, model, system, tools, messages, iteration, bot_id, on_token=None) -> Response` from `sakthai.agent.providers.copilotstudio_provider`.
- Produces: the test file Task 5 must satisfy.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_providers_copilotstudio.py`:

```python
"""Wire-contract tests for the Microsoft 365 Copilot Studio provider.

Follows the pattern in test_provider_contracts.py: a real httpx.Client
backed by httpx.MockTransport, so the genuine request/response cycle
(including the multi-step conversation-start / send / poll flow and the
shared retry policy) is exercised, not just response parsing.
"""

from __future__ import annotations

from typing import Any

import httpx
import pytest

import sakthai.agent.providers.base as base
from sakthai.agent.providers.base import AgentError
from sakthai.agent.providers.copilotstudio_provider import call_copilotstudio
from sakthai.agent.tools import Tool


@pytest.fixture(autouse=True)
def _no_retry_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(base, "RETRY_WAIT_MULTIPLIER", 0.0)
    monkeypatch.setattr(base, "RETRY_WAIT_MAX", 0.0)


@pytest.fixture(autouse=True)
def _no_poll_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
    """Zero the poll interval so the short-poll loop doesn't actually sleep."""
    import sakthai.agent.providers.copilotstudio_provider as mod

    monkeypatch.setattr(mod, "POLL_INTERVAL_SECONDS", 0.0)
    monkeypatch.setattr(mod, "POLL_TIMEOUT_SECONDS", 1.0)


def _tool(name: str = "learn") -> Tool:
    return Tool(
        name=name,
        description=f"{name} tool",
        input_schema={"type": "object", "properties": {}},
        handler=lambda args, store: "ok",
    )


def _client(handler: Any) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test.local")


def _run(client: httpx.Client, **overrides: Any) -> Any:
    kwargs: dict[str, Any] = {
        "client": client,
        "model": "copilotstudio",
        "system": "you are helpful",
        "tools": (),
        "messages": [{"role": "user", "content": "hello"}],
        "iteration": 0,
        "bot_id": "bot-123",
    }
    kwargs.update(overrides)
    return call_copilotstudio(**kwargs)


def test_happy_path_maps_bot_reply_to_response() -> None:
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(f"{request.method} {request.url.path}")
        if request.url.path == "/v3/conversations" and request.method == "POST":
            return httpx.Response(201, json={"id": "conv-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "POST":
            return httpx.Response(200, json={"id": "activity-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "watermark": "1",
                    "activities": [
                        {"type": "message", "from": {"id": "bot-123"}, "text": "hi there"}
                    ],
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    with _client(handler) as client:
        resp = _run(client)

    assert calls[0] == "POST /v3/conversations"
    assert calls[1] == "POST /v3/conversations/conv-1/activities"
    assert calls[2] == "GET /v3/conversations/conv-1/activities"
    assert resp.stop_reason == "end_turn"
    assert resp.content[0].text == "hi there"


def test_poll_ignores_echoed_user_activity_then_finds_bot_reply() -> None:
    """The first poll only sees the echoed user message; the bot reply comes later."""
    poll_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/conversations" and request.method == "POST":
            return httpx.Response(201, json={"id": "conv-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "POST":
            return httpx.Response(200, json={"id": "activity-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "GET":
            poll_count["n"] += 1
            if poll_count["n"] == 1:
                return httpx.Response(
                    200,
                    json={
                        "watermark": "0",
                        "activities": [{"type": "message", "from": {"id": "user"}, "text": "hello"}],
                    },
                )
            return httpx.Response(
                200,
                json={
                    "watermark": "1",
                    "activities": [
                        {"type": "message", "from": {"id": "bot-123"}, "text": "second try works"}
                    ],
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    with _client(handler) as client:
        resp = _run(client)

    assert poll_count["n"] == 2
    assert resp.content[0].text == "second try works"


def test_poll_timeout_surfaces_as_agent_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/conversations" and request.method == "POST":
            return httpx.Response(201, json={"id": "conv-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "POST":
            return httpx.Response(200, json={"id": "activity-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "GET":
            # Bot never replies.
            return httpx.Response(200, json={"watermark": "0", "activities": []})
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    with _client(handler) as client, pytest.raises(AgentError, match="did not reply"):
        _run(client)


def test_conversation_start_500_is_retried_then_raises() -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/conversations":
            calls["n"] += 1
            return httpx.Response(500, json={"error": "boom"})
        raise AssertionError("should not reach activities endpoint")

    with _client(handler) as client, pytest.raises(AgentError, match="Copilot Studio"):
        _run(client)

    assert calls["n"] == base.RETRY_ATTEMPTS


def test_tools_are_not_forwarded_but_do_not_error() -> None:
    """Copilot Studio has no tool-calling wire format; extra tools are silently unused."""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v3/conversations" and request.method == "POST":
            return httpx.Response(201, json={"id": "conv-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "POST":
            import json as _json

            body = _json.loads(request.content)
            assert "tools" not in body
            return httpx.Response(200, json={"id": "activity-1"})
        if request.url.path == "/v3/conversations/conv-1/activities" and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "watermark": "1",
                    "activities": [{"type": "message", "from": {"id": "bot-123"}, "text": "ok"}],
                },
            )
        raise AssertionError(f"unexpected request: {request.method} {request.url}")

    with _client(handler) as client:
        resp = _run(client, tools=(_tool("learn"),))

    assert resp.content[0].text == "ok"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_providers_copilotstudio.py -v"
```

Expected: FAIL — `ModuleNotFoundError: No module named 'sakthai.agent.providers.copilotstudio_provider'`.

- [ ] **Step 3: Commit the failing tests**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add tests/test_providers_copilotstudio.py && git commit -m 'test(providers): add failing wire-contract tests for Copilot Studio'"
```

---

### Task 5: `copilotstudio_provider.py` — implementation (green)

**Files:**
- Create: `personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py`

**Interfaces:**
- Consumes: `AgentError`, `Block`, `Response`, `with_retry`, `logger` from `.base` (Task-independent, already exist).
- Produces: `call_copilotstudio(client, model, system, tools, messages, iteration, bot_id, on_token=None) -> Response`, plus module-level `POLL_INTERVAL_SECONDS`/`POLL_TIMEOUT_SECONDS` constants — consumed by Task 4's tests and Task 6's wiring.

- [ ] **Step 1: Implement**

Create `personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py`:

```python
"""Microsoft 365 Copilot Studio provider backend (Bot Framework Connector API).

Unlike the other providers, Copilot Studio has no single-request
chat-completions endpoint: a conversation must be started, the prompt sent
as an Activity, and the reply retrieved by short-polling. This module hides
that protocol behind the same ``call_*(client, model, system, tools,
messages, iteration, ...) -> Response`` shape every other provider exposes,
so ``agent/loop.py`` does not need to know this provider works differently.

Copilot Studio agents have no wire-level tool-calling format analogous to
OpenAI/Anthropic function calling — ``tools`` is accepted for interface
parity but never sent. A Copilot Studio provider response therefore never
carries ``stop_reason == "tool_use"``; any tool behavior comes from the
agent's own Copilot Studio topics/actions, invisible to this client.
"""

from __future__ import annotations

import time
import uuid
from typing import Any

import httpx

from ..tools import Tool
from ..usage import extract_usage
from .base import AgentError, Block, Response, block_field, logger, with_retry

POLL_INTERVAL_SECONDS = 0.5
POLL_TIMEOUT_SECONDS = 30.0


def _flatten_prompt(system: str, messages: list[dict[str, Any]]) -> str:
    """Collapse the message history into a single text turn.

    Copilot Studio conversations are managed server-side per agent
    invocation (this provider opens a fresh conversation every call, per
    the design's statelessness decision), so there is no multi-turn wire
    format to preserve here — only the latest user-visible text matters.
    """
    parts: list[str] = []
    for msg in messages:
        content = msg.get("content")
        if isinstance(content, str):
            parts.append(content)
        elif isinstance(content, list):
            for block in content:
                text = block_field(block, "text")
                if text:
                    parts.append(text)
    return "\n".join(parts) or system


def _start_conversation(client: httpx.Client) -> str:
    resp = client.post("/v3/conversations", json={})
    resp.raise_for_status()
    conversation_id = resp.json().get("id")
    if not conversation_id:
        raise AgentError("Copilot Studio did not return a conversation id.")
    return str(conversation_id)


def _send_activity(client: httpx.Client, conversation_id: str, text: str, bot_id: str) -> None:
    resp = client.post(
        f"/v3/conversations/{conversation_id}/activities",
        json={
            "type": "message",
            "from": {"id": "sakthai-agent"},
            "recipient": {"id": bot_id},
            "text": text,
        },
    )
    resp.raise_for_status()


def _poll_for_reply(client: httpx.Client, conversation_id: str, bot_id: str) -> str:
    deadline = time.monotonic() + POLL_TIMEOUT_SECONDS
    watermark = ""
    while time.monotonic() < deadline:
        resp = client.get(
            f"/v3/conversations/{conversation_id}/activities",
            params={"watermark": watermark} if watermark else None,
        )
        resp.raise_for_status()
        data = resp.json()
        watermark = str(data.get("watermark", watermark))
        for activity in data.get("activities", []):
            if activity.get("type") != "message":
                continue
            from_id = (activity.get("from") or {}).get("id")
            if from_id == bot_id and activity.get("text"):
                return str(activity["text"])
        if POLL_INTERVAL_SECONDS:
            time.sleep(POLL_INTERVAL_SECONDS)
    raise AgentError(
        f"Copilot Studio agent did not reply within {POLL_TIMEOUT_SECONDS}s "
        f"(conversation {conversation_id})."
    )


def _run_conversation(client: httpx.Client, text: str, bot_id: str) -> str:
    conversation_id = _start_conversation(client)
    _send_activity(client, conversation_id, text, bot_id)
    return _poll_for_reply(client, conversation_id, bot_id)


def call_copilotstudio(
    client: httpx.Client,
    model: str,
    system: str,
    tools: tuple[Tool, ...],
    messages: list[dict[str, Any]],
    iteration: int,
    bot_id: str,
    on_token: Any = None,
) -> Response:
    """Send one turn to a Copilot Studio agent, normalised to :class:`Response`.

    ``model`` and ``on_token`` are accepted for interface parity with the
    other providers but unused: Copilot Studio has no model selector, and
    the Connector API's polling model has no incremental-token stream to
    forward.
    """
    del model, on_token  # interface parity only; see docstring
    text = _flatten_prompt(system, messages)

    try:
        reply_text = with_retry(_run_conversation, client, text, bot_id)
    except AgentError:
        raise
    except Exception as exc:
        logger.error("Copilot Studio API call failed: %s", exc)
        raise AgentError(f"Copilot Studio API call failed: {exc}") from exc

    return Response(
        stop_reason="end_turn",
        content=[Block("text", text=reply_text)],
        usage=extract_usage({}),
    )
```

- [ ] **Step 2: Run tests to verify they pass**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_providers_copilotstudio.py -v"
```

Expected: PASS (5 passed). If `test_conversation_start_500_is_retried_then_raises` fails because `with_retry` doesn't retry a whole multi-call function the way it retries a single request, adjust `_run_conversation`'s call site so `with_retry` wraps only `_start_conversation` (the first network call) — re-run until green, since the exact retry granularity is the one piece of this module not pinned down by the design doc.

- [ ] **Step 3: Type-check**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run mypy personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py"
```

Expected: no errors (strict mode). Fix any `Any`-propagation issues before continuing.

- [ ] **Step 4: Lint**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run ruff check personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py tests/test_providers_copilotstudio.py && uv run ruff format --check personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py tests/test_providers_copilotstudio.py"
```

Expected: clean. Run the same command without `--check` to auto-fix formatting if it isn't.

- [ ] **Step 5: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py && git commit -m 'feat(providers): implement Copilot Studio provider'"
```

---

### Task 6: Wire into `providers/__init__.py`

**Files:**
- Modify: `personas/sakthai/sakthai/agent/providers/__init__.py`
- Test: `tests/test_providers_detect.py` (extend the existing `test_detect_provider_scenarios` parametrize table, plus a new `build_client` test)

**Interfaces:**
- Consumes: `call_copilotstudio` (Task 5), `ms365_copilot_credential_source`/`resolve_copilotstudio_credentials` (Task 3), `ms365_copilot_bot_id` (Task 2).
- Produces: `detect_provider(...)` returns `"copilotstudio"` when appropriate; `build_client("copilotstudio", None)` returns a configured `httpx.Client`.

- [ ] **Step 1: Write the failing tests**

Add a new case to the `test_detect_provider_scenarios` parametrize list in `tests/test_providers_detect.py`:

```python
        (None, "claude-3", {}, {"ms365_copilot": True}, "copilotstudio"),
        (None, "copilotstudio/my-agent", {}, {}, "copilotstudio"),
```

Find where the `creds` fixture dict is translated into monkeypatched credential-source functions further down in the same test (it patches things like `gateway_credential_source`/`huggingface_credential_source` based on the `creds` dict keys) and add an `"ms365_copilot"` entry following the exact same pattern used for `"huggingface"`.

Then add a standalone test to the same file:

```python
def test_build_client_copilotstudio_uses_resolved_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    from sakthai.agent.providers import __init__ as providers_pkg  # noqa: F401
    import sakthai.auth as auth_mod

    monkeypatch.setattr(
        auth_mod, "resolve_copilotstudio_credentials", lambda: ("http://cs.test", "tok-xyz")
    )

    client = build_client("copilotstudio", None)

    assert isinstance(client, httpx.Client)
    assert str(client.base_url) == "http://cs.test/"
    assert client.headers["authorization"] == "Bearer tok-xyz"
```

(Match whatever concrete import style the rest of `test_providers_detect.py` already uses for patching `auth` — some of the existing tests patch through `sakthai.agent.providers` re-exports rather than `sakthai.auth` directly; use the same approach as the neighboring `_build_*_client` tests, if any exist in this file, for consistency. If none exist yet for the other providers, patch `sakthai.auth.resolve_copilotstudio_credentials` directly as shown above.)

- [ ] **Step 2: Run tests to verify they fail**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_providers_detect.py -v"
```

Expected: FAIL — the new parametrize cases return `"anthropic"` (fallback) instead of `"copilotstudio"`, and `test_build_client_copilotstudio_uses_resolved_credentials` fails with `AgentError` (default-fallback client tries to build an Anthropic client instead).

- [ ] **Step 3: Implement the wiring**

In `personas/sakthai/sakthai/agent/providers/__init__.py`:

Add to the `from ...auth import (...)` block (alphabetical, matching existing style):

```python
from ...auth import (
    AuthError,
    anthropic_credential_source,
    gateway_credential_source,
    huggingface_credential_source,
    local_credential_source,
    ms365_copilot_credential_source,
    openai_credential_source,
    resolve_anthropic_client,
    resolve_local_credentials,
    resolve_ollama_credentials,
)
```

Add the import and `__all__` entry:

```python
from .copilotstudio_provider import call_copilotstudio
```

```python
__all__ = [
    "AgentError",
    "Block",
    "Response",
    "block_field",
    "build_client",
    "call_anthropic",
    "call_copilotstudio",
    "call_gemini",
    "call_openai_compat",
    "detect_provider",
    "find_tool_name_by_id",
    "is_retryable",
    "to_gemini_contents",
    "to_openai_messages",
    "with_retry",
]
```

Add a model-name hint to `_detect_from_model_name`, before the `OPENAI_COMPAT_KEYWORDS` check (mirroring the `gateway`/`local/` prefix checks):

```python
    if model_lower.startswith("copilotstudio"):
        return "copilotstudio"
```

Add a credential check to `_detect_from_credentials`, after the `huggingface_credential_source()` check:

```python
    if ms365_copilot_credential_source() is not None:
        return "copilotstudio"
```

Add a client builder, near `_build_huggingface_client`:

```python
def _build_copilotstudio_client() -> Any:
    """Build a client for the Microsoft 365 Copilot Studio Bot Framework Connector."""
    from ...auth import resolve_copilotstudio_credentials

    try:
        api_base, token = resolve_copilotstudio_credentials()
    except AuthError as exc:
        raise AgentError(str(exc)) from exc

    return _openai_compat_client(api_base, token)
```

Add a branch in `build_client`:

```python
    if provider == "copilotstudio":
        return _build_copilotstudio_client()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/test_providers_detect.py tests/test_providers_copilotstudio.py -v"
```

Expected: all PASS.

- [ ] **Step 5: Full local suite, type-check, lint**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/ -q && uv run mypy personas/sakthai/sakthai && uv run ruff check personas/sakthai/sakthai tests && uv run ruff format --check personas/sakthai/sakthai tests"
```

Expected: green across the board. Coverage floor is 96% — a new provider module fully covered by Task 4/5's tests should not drop it, but check the coverage report if `pytest` is run with `--cov` in CI config and fix any gap before moving on.

- [ ] **Step 6: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add personas/sakthai/sakthai/agent/providers/__init__.py tests/test_providers_detect.py && git commit -m 'feat(providers): wire copilotstudio into detect_provider/build_client'"
```

---

### Task 7: Docs and `.env.example`

**Files:**
- Modify: `.env.example` (append after the `SAKTHAI_MCP_TIMEOUT` block)
- Modify: `Sak-Family-Agent/CLAUDE.md` (the "Key environment variables" table, and the `--provider`/`-p` flag description under "Runtime entry points")

**Interfaces:**
- None — documentation only, no code interface.

- [ ] **Step 1: Update `.env.example`**

Append to `.env.example`:

```
# Optional: Microsoft 365 Copilot Studio provider (--provider copilotstudio).
# All four of TENANT_ID/CLIENT_ID/CLIENT_SECRET/BOT_ID are required together.
# MS365_COPILOT_TENANT_ID=
# MS365_COPILOT_CLIENT_ID=
# MS365_COPILOT_CLIENT_SECRET=
# MS365_COPILOT_BOT_ID=

# Optional: override the Bot Framework Connector service URL (region/sovereign
# cloud deployments). Default: https://smba.trafficmanager.net/teams
# MS365_COPILOT_SERVICE_URL=
```

- [ ] **Step 2: Update `CLAUDE.md`**

In the "Key environment variables" table, add five rows following the existing table format (`| Variable | Purpose |`):

```
| `MS365_COPILOT_TENANT_ID` | Entra tenant ID for the `copilotstudio` provider |
| `MS365_COPILOT_CLIENT_ID` | Entra app (client) ID for the `copilotstudio` provider |
| `MS365_COPILOT_CLIENT_SECRET` | Entra app client secret for the `copilotstudio` provider |
| `MS365_COPILOT_BOT_ID` | Target Copilot Studio agent's Bot Framework App ID |
| `MS365_COPILOT_SERVICE_URL` | Bot Framework Connector service URL (default: `https://smba.trafficmanager.net/teams`) |
```

Under "Runtime entry points" → CLI → `run "<task>"`, update the `--provider`/`-p` flag description to include the new value:

```
`--provider`/`-p` (anthropic/google/openai/ollama/gateway/huggingface/copilotstudio),
```

- [ ] **Step 3: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add .env.example CLAUDE.md && git commit -m 'docs: document MS365 Copilot Studio provider env vars'"
```

---

### Task 8: Mirror the new provider file into `personas/shared/sakthai/` and re-validate drift

**Files:**
- Create: `personas/shared/sakthai/agent/providers/copilotstudio_provider.py` (identical copy of the canonical file from Task 5)
- Do NOT modify `personas/shared/sakthai/config.py` or `personas/shared/sakthai/agent/providers/__init__.py` — those stay diverged from the canonical copy, consistent with the existing, already-known divergence documented in `CLAUDE.md` and confirmed by `sakthai-skills-validate` earlier this session.

**Interfaces:**
- None — this task keeps the five non-SakThai personas' shared package in parity with the new provider *module* (matching how `anthropic_provider.py`/`openai_provider.py`/`gemini_provider.py`/`base.py` are already identical across both copies), without attempting to reconcile the pre-existing `config.py`/`__init__.py` divergence, which is out of scope for this plan.

- [ ] **Step 1: Copy the file**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && cp personas/sakthai/sakthai/agent/providers/copilotstudio_provider.py personas/shared/sakthai/agent/providers/copilotstudio_provider.py"
```

- [ ] **Step 2: Re-run the drift check**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && python .claude/skills/sakthai-skills-validate/scripts/diff_trees.py --left personas/sakthai/sakthai --right personas/shared/sakthai"
```

Expected: `agent/providers/copilotstudio_provider.py` reports `IDENTICAL`. `config.py` and `agent/providers/__init__.py` still report `DIVERGES` — that's expected and pre-existing; do not attempt to reconcile them as part of this task. No *new* `UNKNOWN` divergences should appear beyond what this plan intentionally introduced (`config.py`/`__init__.py`, both already on the known list).

Note from earlier this session: `python -m sakthai.cli.skills validate --naming` produced no output after 3+ minutes on both attempts (exit 0, no visible result) even with a warm `.venv` — this looks like a separate, pre-existing issue with that specific command, unrelated to this plan. If it recurs here, don't block on it; it's out of scope for this task (file it as a follow-up instead).

- [ ] **Step 3: Commit**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && git add personas/shared/sakthai/agent/providers/copilotstudio_provider.py && git commit -m 'feat(providers): mirror Copilot Studio provider into shared persona tree'"
```

---

### Task 9: Final full verification

**Files:** none (verification only).

- [ ] **Step 1: Full suite**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run pytest tests/ -q"
```

Expected: all tests pass, including every test added in Tasks 2–6.

- [ ] **Step 2: Lint, format, type-check, security scan**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && uv run ruff check personas/sakthai/sakthai tests && uv run ruff format --check personas/sakthai/sakthai tests && uv run mypy personas/sakthai/sakthai && uv run bandit -c pyproject.toml -r personas/sakthai/sakthai"
```

Expected: all clean — this mirrors the exact CI sequence from `CLAUDE.md`.

- [ ] **Step 3: Manual acceptance check (cannot be automated — needs your real tenant)**

```bash
wsl.exe -d Ubuntu -- bash -c "cd /home/beern/Sak-Family-Agent && export MS365_COPILOT_TENANT_ID=... MS365_COPILOT_CLIENT_ID=... MS365_COPILOT_CLIENT_SECRET=... MS365_COPILOT_BOT_ID=... && uv run sakthai run --provider copilotstudio --dry-run 'hello'"
```

Then drop `--dry-run` and try a real prompt once the dry-run validates config. This is the acceptance step flagged as out-of-scope-for-automated-tests in the design doc — do this with your real Entra app credentials, not committed anywhere.

- [ ] **Step 4: Update `PLAN.md`**

Per this repo's "Workflow: Plan First" convention in `CLAUDE.md`: mark this feature's entry in `PLAN.md` `[ ]` → `[x] 2026-08-05` once Step 3 confirms it works against the real tenant. Use a targeted replacement of just that line, then re-read `PLAN.md` to confirm the surrounding content is intact, per `CLAUDE.md`'s `PLAN.md` safety rule.
