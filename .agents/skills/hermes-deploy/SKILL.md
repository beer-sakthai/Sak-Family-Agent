---
name: hermes-deploy
description: >
  Deploy Hermes agent configuration files from the sakthai-hermes-agents repo
  to the live ~/.hermes environment, translating /home/sakthai → /home/beerthai.
  Use this skill whenever config.yaml, SOUL.md, cron/jobs.json, or systemd service
  files are modified and need to be applied to the live Hermes runtime.
---

## When to use

Any time config files (`config.yaml`, `SOUL.md`, `cron/jobs.json`) or systemd
service files in the repo are modified and need to be applied to the live runtime.

## Deploy command

```bash
cd ~/sakthai-hermes-agents
./deploy.py
```

## What deploy.py does

1. Copies `default/{config.yaml,SOUL.md}` → `~/.hermes/`
2. Copies `shared/agents-roster.md` → `~/.hermes/shared/`
3. For each profile in `profiles/`: copies `config.yaml`, `SOUL.md`, `cron/jobs.json`
4. Creates/refreshes `AGENTS.md` symlink → `../../shared/agents-roster.md`
5. Copies all `systemd/*.service` files → `~/.config/systemd/user/`
6. Replaces all `/home/sakthai` occurrences with `$HOME` in destination files
7. Backs up any overwritten file as `<file>.bak`

## After deploy — required host terminal commands

The agent sandbox cannot run `systemctl --user` (no `/run/user`). Always give
the user these commands to run in their host terminal:

```bash
systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service hermes-gateway-saksee.service \
  hermes-gateway-sakthai.service hermes-gateway-saksit.service
```

## Path translation note

The repo was originally authored with `/home/sakthai` paths. The live host is
`/home/beerthai`. `deploy.py` handles this automatically. Never hardcode either
path in new config edits — use `${HOME}` where possible, or rely on deploy.py.

## Repo → live path map

| Repo path | Live path |
|-----------|-----------|
| `default/config.yaml` | `~/.hermes/config.yaml` |
| `default/SOUL.md` | `~/.hermes/SOUL.md` |
| `shared/agents-roster.md` | `~/.hermes/shared/agents-roster.md` |
| `profiles/<name>/config.yaml` | `~/.hermes/profiles/<name>/config.yaml` |
| `profiles/<name>/SOUL.md` | `~/.hermes/profiles/<name>/SOUL.md` |
| `profiles/<name>/cron/jobs.json` | `~/.hermes/profiles/<name>/cron/jobs.json` |
| `systemd/*.service` | `~/.config/systemd/user/*.service` |
