# Sak-Family MCP Gateway & Microsoft 365 Copilot Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `services/sak-mcp-gateway` as a secure, production-grade bridge enabling Microsoft 365 Copilot (Declarative Agent with MCP plugin schema v2.4) and Work IQ to interact with the House of Sak ecosystem under strict Entra ID JWT authorization, while enforcing an unbreachable boundary around the agents' shared memory (`~/.sakthai/memory.db`).

**Architecture:**
- **Inbound Leg (M365 Copilot -> Sak Gateway)**: Microsoft 365 Copilot calls a secure HTTPS `/mcp` endpoint backed by FastAPI, authenticated via Microsoft Entra ID bearer tokens (`OAuthPluginVault`). Starter tools (`sak_health_status`, `sak_family_catalog`) return read-only status and domain catalogs without touching SQLite memory stores directly.
- **Outbound Leg (Sak Family -> Work IQ)**: Python Work IQ MCP client communicates with the Microsoft Work IQ MCP server over Streamable HTTP with delegated user tokens, strictly filtered by a read-only tool allowlist.
- **Container Deployment**: Docker Compose with Caddy reverse proxy, rootless Python 3.12 container, read-only root filesystem, dropped Linux capabilities, and `no-new-privileges`.
- **M365 App Package**: Teams app manifest v1.17, Declarative Agent v1.0, and `ai-plugin.json` schema v2.4 (`RemoteMCPServer`), bundled via `package_app.py`.

**Tech Stack:** Python 3.12, FastAPI, Uvicorn, PyJWT, Cryptography, HTTPX, Docker Compose, Caddy, Pytest.

**Security & Privacy Invariants:**
- Zero financial cost ($0.00 USD).
- Never access `~/.sakthai/memory.db` without an approved knowledge adapter.
- No hardcoded secrets, tenant IDs, or bearer tokens in code or manifests.
- Work IQ client blocks any mutating tools (`create`, `update`, `delete`, `send`).
- All code formatted and linted with Ruff, strictly typed, and verified with Bandit and Pytest.

---

### Task 1: M365 Copilot Package Source & Packaging Utility

**Files:**
- Create: `services/sak-mcp-gateway/microsoft365/manifest.json`
- Create: `services/sak-mcp-gateway/microsoft365/declarativeAgent.json`
- Create: `services/sak-mcp-gateway/microsoft365/ai-plugin.json`
- Create: `services/sak-mcp-gateway/microsoft365/package_app.py`
- Create: `services/sak-mcp-gateway/microsoft365/assets/color.png`
- Create: `services/sak-mcp-gateway/microsoft365/assets/outline.png`
- Test: `python services/sak-mcp-gateway/microsoft365/package_app.py --dry-run`

- [ ] **Step 1: Create plugin manifest schemas and declarative agent definitions**
- [ ] **Step 2: Generate placeholder SVG/PNG app icons**
- [ ] **Step 3: Implement `package_app.py` packaging script**
- [ ] **Step 4: Test manifest validation and zip packaging**

---

### Task 2: Core Gateway & Work IQ Client Implementation

**Files:**
- Create: `services/sak-mcp-gateway/pyproject.toml`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/__init__.py`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/config.py`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/auth.py`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/tools.py`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/gateway.py`
- Create: `services/sak-mcp-gateway/src/sak_mcp_gateway/work_iq_client.py`
- Test: `uv run pytest services/sak-mcp-gateway/tests/`

- [ ] **Step 1: Define `pyproject.toml` and package configuration**
- [ ] **Step 2: Implement Entra ID JWT verification in `auth.py`**
- [ ] **Step 3: Implement read-only starter tools in `tools.py`**
- [ ] **Step 4: Implement FastAPI `/mcp` and `/health` server in `gateway.py`**
- [ ] **Step 5: Implement Work IQ MCP client with tool allowlist in `work_iq_client.py`**

---

### Task 3: Hardened Container & Deployment Infrastructure

**Files:**
- Create: `services/sak-mcp-gateway/Dockerfile`
- Create: `services/sak-mcp-gateway/docker-compose.yml`
- Create: `services/sak-mcp-gateway/Caddyfile`
- Create: `services/sak-mcp-gateway/.env.example`
- Create: `services/sak-mcp-gateway/README.md`
- Test: `docker compose -f services/sak-mcp-gateway/docker-compose.yml config`

- [ ] **Step 1: Author hardened rootless Dockerfile**
- [ ] **Step 2: Configure Docker Compose and Caddy reverse proxy**
- [ ] **Step 3: Author `.env.example` and service documentation in `README.md`**
- [ ] **Step 4: Validate docker-compose syntax**

---

### Task 4: Unit Test Suite & Quality Verification

**Files:**
- Create: `services/sak-mcp-gateway/tests/test_auth.py`
- Create: `services/sak-mcp-gateway/tests/test_tools.py`
- Create: `services/sak-mcp-gateway/tests/test_gateway.py`
- Create: `services/sak-mcp-gateway/tests/test_work_iq_client.py`
- Create: `services/sak-mcp-gateway/tests/test_packaging.py`
- Test: `uv run pytest services/sak-mcp-gateway/tests/ -v`
- Test: `make lint`
- Test: `uv run bandit -c pyproject.toml -r services/sak-mcp-gateway/src -q`

- [ ] **Step 1: Write comprehensive unit test suite**
- [ ] **Step 2: Run pytest suite and verify 100% pass**
- [ ] **Step 3: Run linter and security checks**
- [ ] **Step 4: Update PLAN.md Section 21**
