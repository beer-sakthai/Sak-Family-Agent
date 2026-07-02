# ServiceQuoteBot Deployment Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a customer deployment package for ServiceQuoteBot with repeatable setup, a systemd service template, and a repo-local deployment guide.

**Architecture:** Keep the runtime simple and Linux-first. The bot already runs in-process via `sakthai.telegram.bot`, so deployment should wrap that entry point with a small systemd unit, a setup script that assembles a customer-specific `.env` and memory directory, and a short guide that explains how to ingest the customer price book before starting the service. Keep the deployment assets separate from the core runtime so they can be reused for future customer installs.

**Tech Stack:** Python 3.11+, `systemd` user services, `uv`/virtualenv-compatible Python entry point, Markdown docs, `pytest`, `ruff`.

---

### Task 1: Define the deployment contract

**Files:**
- Create: `docs/servicequotebot/deployment.md`
- Modify: `product/todo.md`

- [ ] **Step 1: Write the deployment guide**

Document the deployment flow end to end:
- where the repo should live on the customer host
- which environment variables the bot needs (`ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_ALLOWED_USER_IDS`, `SAKTHAI_HOME`)
- how the price book gets ingested into the persistent memory DB before first launch
- how to start and verify the service with `systemctl --user`

- [ ] **Step 2: Update the tracker**

Mark the `Deployment Plan` checklist item complete only after the deployment guide exists and matches the implementation.

- [ ] **Step 3: Verify the doc is specific**

Run:

```bash
sed -n '1,220p' docs/servicequotebot/deployment.md
```

Expected:
- the guide names the exact entry point (`python -m sakthai.telegram.bot`)
- the guide names the service file path and the setup script path
- the guide shows one concrete example command for price-book ingestion

- [ ] **Step 4: Commit**

```bash
git add docs/servicequotebot/deployment.md product/todo.md
git commit -m "docs: add servicequotebot deployment guide"
```

### Task 2: Add a systemd service template

**Files:**
- Create: `infra/servicequotebot/systemd/servicequotebot.service`

- [ ] **Step 1: Write the service file**

Use a user-service template that:
- runs `python -m sakthai.telegram.bot`
- points `WorkingDirectory` at the deployed repo root
- exports `SAKTHAI_HOME`, `ANTHROPIC_API_KEY`, `TELEGRAM_BOT_TOKEN`, and `TELEGRAM_ALLOWED_USER_IDS`
- restarts automatically on failure

Example:

```ini
[Unit]
Description=ServiceQuoteBot Telegram Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/apps/Sak-Family-Agent
ExecStart=%h/apps/Sak-Family-Agent/.venv/bin/python -m sakthai.telegram.bot
Environment=SAKTHAI_HOME=%h/.sakthai-servicequotebot
EnvironmentFile=%h/.config/servicequotebot/servicequotebot.env
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

- [ ] **Step 2: Verify the unit is portable**

Confirm the unit only uses customer-local paths and does not reference the Hermes deployment tree.

- [ ] **Step 3: Commit**

```bash
git add infra/servicequotebot/systemd/servicequotebot.service
git commit -m "infra: add servicequotebot systemd unit"
```

### Task 3: Add the customer bootstrap script

**Files:**
- Create: `scripts/setup_servicequotebot.py`
- Create: `tests/test_setup_servicequotebot.py`

- [ ] **Step 1: Write the failing tests**

Test these behaviors:
- the script writes a customer env file with the requested Telegram and Anthropic credentials
- the script writes the selected `SAKTHAI_HOME`
- the script prepares an ingest command for the supplied price book path
- the script points at the service template from `infra/servicequotebot/systemd/servicequotebot.service`

Example test outline:

```python
def test_setup_writes_env_and_service(tmp_path, monkeypatch):
    from scripts.setup_servicequotebot import build_customer_bundle

    result = build_customer_bundle(
        target_dir=tmp_path,
        repo_root=Path("/repo"),
        anthropic_api_key="sk-test",
        telegram_bot_token="123:abc",
        telegram_allowed_user_ids=[123],
        price_book=Path("/inputs/price-book.md"),
    )

    assert result.env_file.read_text() == ...
    assert result.service_file.read_text().startswith("[Unit]")
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run:

```bash
uv run pytest tests/test_setup_servicequotebot.py -q
```

Expected:
- import or function errors until the script exists

- [ ] **Step 3: Implement the script**

Implement a small standard-library CLI that:
- accepts `--repo-root`, `--target-dir`, `--price-book`, `--anthropic-api-key`, `--telegram-bot-token`, and `--telegram-allowed-user-ids`
- creates the target directories
- writes a `.env` or `servicequotebot.env` file
- copies the systemd template into the customer bundle
- optionally runs `sakthai ingest_document` against the supplied price book after the environment is prepared

- [ ] **Step 4: Run the tests and confirm they pass**

Run:

```bash
uv run pytest tests/test_setup_servicequotebot.py -q
```

Expected:
- tests pass and the generated env/service content matches the deployment contract

- [ ] **Step 5: Commit**

```bash
git add scripts/setup_servicequotebot.py tests/test_setup_servicequotebot.py
git commit -m "feat: add servicequotebot setup script"
```

### Task 4: Validate the full deployment story

**Files:**
- Modify: `product/todo.md`
- Possibly modify: `docs/servicequotebot/deployment.md`, `infra/servicequotebot/systemd/servicequotebot.service`, `scripts/setup_servicequotebot.py`

- [ ] **Step 1: Run the repo checks**

Run:

```bash
uv run ruff check .
uv run ruff format --check .
uv run pytest tests/ -q -m "not integration"
```

- [ ] **Step 2: Update the tracker**

Mark `Deployment Plan` complete in `product/todo.md`.

- [ ] **Step 3: Commit**

```bash
git add product/todo.md docs/servicequotebot/deployment.md infra/servicequotebot/systemd/servicequotebot.service scripts/setup_servicequotebot.py tests/test_setup_servicequotebot.py
git commit -m "docs: finish servicequotebot deployment plan"
```

### Coverage Check

- `docs/servicequotebot/deployment.md` covers the customer deployment flow requested in the tracker.
- `infra/servicequotebot/systemd/servicequotebot.service` satisfies the “systemd service file or Dockerfile” requirement.
- `scripts/setup_servicequotebot.py` satisfies the automated setup requirement for a new client.
- `tests/test_setup_servicequotebot.py` covers the new script behavior before it is committed.
- `product/todo.md` is the only active tracker and will be checked off only after the artifacts exist and verify cleanly.
