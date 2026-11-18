# ServiceQuoteBot Deployment Guide

ServiceQuoteBot runs the Telegram bot entry point in-process:

```bash
python -m sakthai.telegram.bot
```

The deployment shape is intentionally simple:

- the repository lives on the customer host
- a user-level `systemd` service keeps the bot running
- a small setup script writes the customer env file, copies the systemd unit,
  and ingests the first price book into persistent memory

## Prerequisites

- Python 3.11 or newer
- the Sak-Family-Agent repository cloned on the host
- a Telegram bot token
- an Anthropic API key for the model used by `sakthai run`
- the customer price book in Markdown, CSV, or plain text

## Files

- Systemd unit template: [`infra/servicequotebot/systemd/servicequotebot.service`](/home/beerthai/Sak-Family-Agent/infra/servicequotebot/systemd/servicequotebot.service)
- Bootstrap script: [`scripts/setup_servicequotebot.py`](/home/beerthai/Sak-Family-Agent/scripts/setup_servicequotebot.py)

## Setup flow

- Create a bundle for the customer:

```bash
python scripts/setup_servicequotebot.py \
  --repo-root /opt/Sak-Family-Agent \
  --target-dir /etc/servicequotebot/acme-plumbing \
  --price-book /srv/customer/acme-plumbing/price-book.md \
  --anthropic-api-key sk-ant-... \
  --telegram-bot-token 123456:ABCDEF... \
  --telegram-allowed-user-ids 123456789,987654321
```

- Install the generated env file and service unit:

```bash
install -Dm600 \
  /etc/servicequotebot/acme-plumbing/config/servicequotebot.env \
  ~/.config/servicequotebot/servicequotebot.env
install -Dm644 \
  /etc/servicequotebot/acme-plumbing/systemd/servicequotebot.service \
  ~/.config/systemd/user/servicequotebot.service
systemctl --user daemon-reload
systemctl --user enable --now servicequotebot.service
```

- Verify the service:

```bash
systemctl --user status servicequotebot.service
journalctl --user -u servicequotebot.service -f
```

## What the setup script prepares

- a customer-specific `servicequotebot.env` file with the Telegram and
  Anthropic credentials
- a persistent `SAKTHAI_HOME` directory for that customer
- a copied price book stored in the customer bundle
- a pre-seeded memory database created by ingesting the supplied price book
- a customer-specific systemd unit that points at the repository root and
  launches the Telegram bot entry point

## Rollout notes

- Keep one bundle per customer.
- Update the price book by rerunning the setup script with the new source
  file, then restart the user service.
- If the repository moves, regenerate the service unit so `WorkingDirectory`
  and `ExecStart` point at the new path.
