---
name: run-hermes-agents
description: Run, restart, drive, smoke-test, and verify the Hermes Telegram-agent fleet — the 4 gateway systemd --user services (SakKing/default, Saksee, Saksit, SakThai). Use when asked to start/restart the bots, check the fleet is up, verify the agents are healthy, debug a gateway that won't run, or confirm provider/MCP auth after a config change or laptop reset.
---

The **Hermes fleet** is 4 Telegram bots running as systemd **user** services
(`hermes-gateway` = SakKing/default, `-saksee`, `-saksit`, `-sakthai`), each a
profile under `~/.hermes/` driven by the `hermes` CLI. There is no headless way
to do a real Telegram round-trip, so you **drive the fleet through its
management surface**: the smoke driver at
`.claude/skills/run-hermes-agents/driver.sh` checks all 4 services are active,
provider auth resolves, MCP servers connect, and repo config is sane.

All paths below are relative to `infra/hermes-agents/` (the config unit). The
fleet itself runs from `~/.hermes/` (the live runtime); config is deployed there
from this repo.

## Prerequisites

Everything is already installed on the host — **no `apt-get` needed**:

- `hermes` CLI on PATH (`~/.local/bin/hermes`; venv at `~/.hermes/hermes-agent/venv`)
- `python3` (for `doctor.py`), `systemctl --user`, `journalctl --user`
- A systemd **user** session (this works in the WSL2 container — see Gotchas)

```bash
command -v hermes            # -> /home/beerthai/.local/bin/hermes
hermes --version
```

## Run (agent path) — the smoke driver

This is the primary path. It exits non-zero only if a gateway is **down** or
`doctor.py` fails; `nous` being logged out and post-restart MCP retries are
reported as **WARN**, not failures.

```bash
./.claude/skills/run-hermes-agents/driver.sh
# -> per-section [PASS]/[WARN]/[FAIL] lines, then "OK: fleet up and serving"
```

What it drives (all against the live fleet):

| surface | check |
|---|---|
| gateways | `systemctl --user is-active` + `NRestarts` for all 4 (hard FAIL if not active) |
| provider auth | `hermes auth status {huggingface,copilot,nous}` + `hermes auth list` |
| MCP health | `journalctl --user -u <gw>` grep for mcp fail/error lines (last 5 min) |
| repo config | `python3 doctor.py` overall_health |
| CLI | `hermes status` exit code |

Override the binary with `HERMES_BIN=/path/to/hermes ./.claude/skills/run-hermes-agents/driver.sh`.

## Start / restart the fleet

Services are installed + enabled; they come up on login. To restart (e.g. after
deploying config, or to pick up changed `Environment=` lines):

```bash
systemctl --user daemon-reload     # only after editing unit files
systemctl --user restart hermes-gateway hermes-gateway-saksee hermes-gateway-saksit hermes-gateway-sakthai
```

All four return to `active` within ~1–2s. Re-run the driver to confirm.

### Individual checks

```bash
systemctl --user is-active hermes-gateway-saksee            # -> active
hermes auth status nous                                     # provider login state
hermes auth list                                            # pooled credentials
hermes status                                               # env, API keys, model/provider
journalctl --user -u hermes-gateway-sakthai --since "5 minutes ago" --no-pager | grep -i mcp
```

## Deploy config (separate skill)

Applying changed `config.yaml` / `SOUL.md` / `cron/jobs.json` / `*.service`
from this repo to `~/.hermes/` is handled by the sibling **`hermes-deploy`**
skill (`./deploy.py`, which rewrites `/home/sakthai` → `$HOME`). This skill is
about running/verifying the result, not deploying it.

## Run (human path)

The bots are already live as services — to actually use them, message them on
Telegram (SakKing/default, `@saksee_bot`, `@saksit_agent_bot`, `@sakthai_v1_bot`).
There is no useful foreground/CLI chat for verification headless (see Gotchas:
`hermes -z`).

## Gotchas

- **`systemctl --user` DOES work in this container.** The sibling `hermes-deploy`
  skill claims "the agent sandbox cannot run `systemctl --user` (no `/run/user`)"
  — that is **false here**: `is-active`, `show`, `daemon-reload`, `restart`, and
  `journalctl --user` all work. The driver depends on this.
- **`hermes -z "<prompt>"` (one-shot agent) silently exits 2 headless.** Zero
  output, even with `--cli --yolo --ignore-rules`, explicit `--provider`+`-m`,
  and stdin from `/dev/null`. Do **not** try to drive the agent loop one-shot to
  verify the fleet — use the gateway + a real Telegram message, or the
  management surface this driver uses.
- **`nous` logged out is expected and non-fatal.** The bots serve on
  **HuggingFace** (`model.provider: huggingface`); nous is only the model for the
  `cron-fleet-selfheal` cron job. The driver WARNs, doesn't FAIL. Recover nous
  with the **interactive** `env -u HERMES_HOME hermes auth add nous` (device-code
  + browser approval; `env -u HERMES_HOME` forces it to write the shared
  `~/.hermes/auth.json`).
- **MCP error lines spike right after a restart.** Each gateway re-attempts every
  MCP server on boot; failures (3 retries) land in the journal window. The
  `github` MCP currently returns **401 Unauthorized** (the Copilot PAT) on all
  profiles — a single MCP server can fail without taking the gateway down. WARN,
  not FAIL.
- **All 4 share one `~/.hermes/auth.json` for nous but run with different
  `HERMES_HOME`** (default = `~/.hermes`, others = `~/.hermes/profiles/<name>`).
  This previously broke nous refresh-token coordination → fleet-wide revocation;
  fixed by `HERMES_SHARED_AUTH_DIR=~/.hermes/shared` on all 4 units. Confirm it's
  in the running env: `tr '\0' '\n' </proc/$(systemctl --user show hermes-gateway-saksee -p MainPID --value)/environ | grep HERMES_SHARED_AUTH_DIR`.
- **Each bot needs its own `TELEGRAM_BOT_TOKEN`** in its profile `.env` (two bots
  sharing one token → Telegram 409, both go silent).

## Troubleshooting

- **driver shows `[FAIL] <gw> is 'failed'`** → `journalctl --user -u <gw> --since "5 minutes ago" --no-pager | tail -40` for the crash; common causes are a malformed profile `config.yaml` or a missing `.env` var.
- **`No access token found for Nous Portal login`** (cron job / nous calls) → expected when nous is logged out; recover with `env -u HERMES_HOME hermes auth add nous`, then `systemctl --user restart` the gateways.
- **`hermes auth status nous` still logged-out right after `hermes auth add nous`** → the interactive device-code flow wasn't completed (browser approval). Re-run and finish the approval; confirm with `hermes auth list` showing a nous credential.
- **github MCP `401 Unauthorized` in journal** → the `GITHUB_TOKEN` PAT is expired/insufficient for `api.githubcopilot.com/mcp`; rotate it in the profile `.env`. Non-blocking for the gateway.
