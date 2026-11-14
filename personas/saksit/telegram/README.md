# SakThai Telegram Bot

This bot runs the agent loop in-process and is the runtime entry point used by
the VM services.

## Required environment

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_ALLOWED_USER_IDS`
- `SAKTHAI_PROVIDER`
- `SAKTHAI_MODEL`
- `SAKTHAI_SYSTEM_PROMPT_FILE` or `SAKTHAI_SYSTEM_PROMPT`

Optional launch controls:

- `SAKTHAI_FAST=1`
- `SAKTHAI_STATELESS=1`
- `SAKTHAI_WITH_SKILLS=skill-a,skill-b`

## Run

From the repository root:

```bash
python -m sakthai.telegram.bot
```

## Telegram commands

- `/start` opens the bot.
- `/workflows` lists workflow skills.
- `/workflow <name>` runs one workflow skill through the agent loop.
- Plain text messages go straight to the agent.

## Persona setup

For Hermes-free deployments, point `SAKTHAI_SYSTEM_PROMPT_FILE` at the agent's
`SOUL.md` file. The bot prepends that persona block before the shared runtime
prompt, so one code path can serve SakKing, SakThai, SakSee, SakSit, SakTan,
and SakJules.
