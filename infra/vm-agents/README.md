# VM Telegram Agents

This directory holds the Hermes-free VM deployment assets for the six Sak Family
Telegram bots.

## Runtime model

Each agent runs the in-repo Telegram gateway:

```bash
python -m sakthai.telegram.bot
```

The bot reads its runtime identity from environment variables:

- `TELEGRAM_BOT_TOKEN` and `TELEGRAM_ALLOWED_USER_IDS`
- `SAKTHAI_PROVIDER` and `SAKTHAI_MODEL`
- `SAKTHAI_SYSTEM_PROMPT_FILE` pointing at the agent's `SOUL.md`
- `SAKTHAI_WITH_SKILLS` for extra shared or persona skills
- `SAKTHAI_FAST` and `SAKTHAI_STATELESS` when a lightweight launch is desired

Shared VM settings live in `~/.config/sak-family-agents/common.env` so every bot
can reuse the same model endpoint and API key.

## Suggested layout on the VM

```text
~/.config/sak-family-agents/
  common.env
  sakking.env
  sakthai.env
  saksee.env
  saksit.env
  saktan.env
  sakjules.env
```

Each env file should set the bot token, allowed user IDs, model endpoint, and
persona file for one agent. Use the same `SAKTHAI_HOME` only when the agents
should share memory; otherwise give each agent its own home directory.

The repository also includes example env templates under
`infra/vm-agents/env-templates/` and a bundle helper at
`scripts/setup_vm_telegram_agents.py`.

## Bundle helper

```bash
python scripts/setup_vm_telegram_agents.py \
  --repo-root /home/beerthai/Sak-Family-Agent \
  --target-dir /tmp/sak-family-vm-bundle \
  --openai-base-url https://sakthai-resource.openai.azure.com/openai/v1 \
  --openai-api-key "$OPENAI_API_KEY" \
  --telegram-allowed-user-ids "123456789" \
  --shared-sakthai-home /home/beerthai/.sakthai \
  --sakking-telegram-bot-token "$SAKKING_TOKEN" \
  --sakthai-telegram-bot-token "$SAKTHAI_TOKEN" \
  --saksee-telegram-bot-token "$SAKSEE_TOKEN" \
  --saksit-telegram-bot-token "$SAKSIT_TOKEN" \
  --saktan-telegram-bot-token "$SAKTAN_TOKEN" \
  --sakjules-telegram-bot-token "$SAKJULES_TOKEN"
```

## Systemd

Install [`systemd/sakthai-telegram@.service`](systemd/sakthai-telegram@.service)
as a user unit, then enable one instance per env file:

```bash
systemctl --user daemon-reload
systemctl --user enable --now sakthai-telegram@sakking.service
systemctl --user enable --now sakthai-telegram@sakthai.service
```

Repeat for the remaining agents. The instance name maps to the matching env
file, so `sakthai-telegram@saksee.service` loads `~/.config/sak-family-agents/saksee.env`.
