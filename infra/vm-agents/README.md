# VM Agent Deployment

Assets for deploying the six Sak Family Telegram agents on a Linux VM as
`systemd` **user** services, one service instance per agent, from a single
templated unit file. All six run the same container image; the instance name
selects the persona.

## How it fits together

- **One image, six instances.** `Dockerfile` at the repository root builds
  `ghcr.io/beer-sakthai/sak-family-agent`, published by
  [`.github/workflows/publish-image.yml`](../../.github/workflows/publish-image.yml).
  Nothing persona-specific is baked in: the unit passes `SAKTHAI_PERSONA`,
  `SAKTHAI_HOME` and `SAKTHAI_SYSTEM_PROMPT_FILE`, all derived from the instance
  name (`%i`).
- **Templated user unit.** `systemd/sakthai-telegram@.service` is the template.
  Enabling `sakthai-telegram@sakking.service` substitutes `%i` with `sakking`.
- **Per-agent memory.** Each persona writes to its own shard at
  `~/.sakthai/<persona>/memory.db` on the host, mounted into the container at
  `/data/.sakthai`. **Never point two personas at one `SAKTHAI_HOME`** — it
  silently merges their facts and cycle-stage state.
- **Config split by blast radius.** `common.env` holds what every agent shares
  (image reference, provider credentials, allowed Telegram user IDs);
  `<agent>.env` holds that agent's own bot token and model.

## Prerequisites

- A Linux VM with `systemd` and **Docker**.
- The VM user in the `docker` group (`sudo usermod -aG docker $USER`, then log
  out and back in) — the unit runs `docker` without `sudo`.
- `loginctl enable-linger $USER` — without it, user services stop at logout and
  the agents die when you close your SSH session.
- Read access to the GHCR package (see Step 1).
- A Telegram bot token for each of the six agents.

Note there is **no** requirement to clone the repository or build a virtualenv
on the VM. The agents run from the published image; the repo is only needed on
whatever machine generates the config bundle.

## Step 1 — Authenticate to GHCR

The image is published to GitHub Container Registry. Authenticate once with a
personal access token carrying `read:packages`:

```bash
echo "$GHCR_TOKEN" | docker login ghcr.io -u <your-github-username> --password-stdin
```

Confirm the image pulls before going further — this is the step that failed
silently for every previous version of this deployment:

```bash
docker pull ghcr.io/beer-sakthai/sak-family-agent:latest
```

## Step 2 — Generate the config bundle

```bash
python scripts/setup_vm_telegram_agents.py \
  --repo-root ~/Sak-Family-Agent \
  --target-dir ~/sak-family-agents-deployment \
  --openai-base-url "https://sakthai-resource.openai.azure.com/openai/v1" \
  --openai-api-key "sk-..." \
  --telegram-allowed-user-ids "123456789" \
  --image-name "ghcr.io/beer-sakthai/sak-family-agent@sha256:<digest>" \
  --sakking-telegram-bot-token "..." \
  --sakthai-telegram-bot-token "..." \
  --saksee-telegram-bot-token "..." \
  --saksit-telegram-bot-token "..." \
  --saktan-telegram-bot-token "..." \
  --sakjules-telegram-bot-token "..."
```

`--image-name` defaults to `:latest`, but **pin it to a digest in production**.
The publish workflow prints the digest to pin at the end of every run. A moving
tag means `ExecStartPre=docker pull` can change what runs on the next restart
with no change on your side.

Produces:

```
sak-family-agents-deployment/
├── config/          common.env + one <agent>.env per persona (mode 0600)
└── systemd/         sakthai-telegram@.service
```

## Step 3 — Install config and unit

```bash
mkdir -p ~/.config/sak-family-agents ~/.config/systemd/user
cp ~/sak-family-agents-deployment/config/*.env ~/.config/sak-family-agents/
cp ~/sak-family-agents-deployment/systemd/sakthai-telegram@.service ~/.config/systemd/user/
```

## Step 4 — Enable and start

```bash
systemctl --user daemon-reload
for agent in sakking sakthai saksee saksit saktan sakjules; do
  systemctl --user enable --now "sakthai-telegram@${agent}.service"
done
```

## Step 5 — Verify

```bash
python scripts/verify_vm_telegram_agents.py
```

Manual checks:

```bash
systemctl --user status sakthai-telegram@sakking.service
systemctl --user list-units "sakthai-telegram@*.service"
journalctl --user -u sakthai-telegram@saktan.service -f
```

A persona's shard file only appears on first write, so a freshly started agent
that has answered nothing yet has no `memory.db`. That is expected, not a fault.

## Troubleshooting

| Symptom | Cause |
|---|---|
| Unit restarts every 10s, `docker pull` fails | Not logged in to GHCR, or the image reference is wrong. Run the Step 1 pull by hand. |
| Agents die when you log out | `loginctl enable-linger $USER` was not run. |
| `permission denied … docker.sock` | The VM user is not in the `docker` group, or has not re-logged in since being added. |
| Bot answers but remembers nothing across restarts | The `~/.sakthai` mount is not writable by the container user. The image runs as UID 1000; if the VM account is not 1000, rebuild with `--build-arg UID=$(id -u)`. |
| Two personas returning each other's facts | Two units share a `SAKTHAI_HOME`. The unit derives it from `%i`; check no `<agent>.env` overrides it — `EnvironmentFile` is applied *after* `Environment=` and wins. |

## Secrets

Tokens currently live in `~/.config/sak-family-agents/*.env`, mode `0600`.

A previous iteration fetched them at start-up from Azure Key Vault using the
VM's managed identity, which is genuinely better — no secret ever has to be
pushed to the VM out of band, and `az vm run-command` persists script and
parameter content in Azure's run-command history. That script
(`sakthai-agent-run.sh`) was retired here because nothing invoked it: the unit's
`ExecStart` ran Docker instead, so the file described a deployment that was not
happening while claiming in its own docstring to be the entry point. Restoring
Key Vault as an `ExecStartPre` that writes the env file is the intended
follow-up; git history has the original.
