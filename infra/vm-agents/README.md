# VM Agent Deployment (Hermes-Free)

This directory contains assets for deploying the six Sak Family Telegram agents on a Linux VM without the Hermes runtime. The deployment uses `systemd` user services, with one service instance per agent, managed by a single templated unit file.

## Architecture

The goal is a clean, repeatable, and robust deployment that is independent of the Hermes framework.

- **`systemd` User Services**: Each agent runs as its own `systemd` service under the user account (`systemctl --user`). This allows the agents to start on user login and be managed without root privileges.
- **Templated Service Unit**: A single file, `systemd/sakthai-telegram@.service`, serves as a template for all six agents. When you enable `sakthai-telegram@sakking.service`, `systemd` automatically substitutes `%i` with `sakking`.
- **Per-Agent Configuration**: The templated service loads a common environment file (`common.env`) for shared settings (like the model API base URL) and an agent-specific file (`<agent_name>.env`) for unique settings like the Telegram bot token. This keeps secrets and configurations cleanly separated.
- **Bootstrap Script**: The `scripts/setup_vm_telegram_agents.py` script is a command-line helper that gathers all necessary credentials and generates the complete set of `.env` files and a copy of the `systemd` unit, creating a self-contained deployment bundle.

## Deployment Flow

Follow these steps on the target VM to deploy the agents.

### Prerequisites

- A Linux VM with `systemd`.
- The `Sak-Family-Agent` repository cloned, typically to `~/Sak-Family-Agent`.
- Python 3.11+ and `uv` installed.
- A Python virtual environment created and dependencies installed (`uv sync`).
- API keys and Telegram bot tokens for all six agents.

### Step 1: Generate the Deployment Bundle

Run the `setup_vm_telegram_agents.py` script to create a directory containing all necessary configuration files. This script prompts for all required tokens and paths.

**Example Command:**

```bash
# Ensure you are in the repository root
# Replace placeholders with your actual credentials and paths

python scripts/setup_vm_telegram_agents.py \
  --repo-root ~/Sak-Family-Agent \
  --target-dir ~/sak-family-agents-deployment \
  --openai-base-url "https://api.openai.com/v1" \
  --openai-api-key "sk-..." \
  --telegram-allowed-user-ids "123456789" \
  --shared-sakthai-home ~/.sakthai \
  --sakking-telegram-bot-token "..." \
  --sakthai-telegram-bot-token "..." \
  --saksee-telegram-bot-token "..." \
  --saksit-telegram-bot-token "..." \
  --saktan-telegram-bot-token "..." \
  --sakjules-telegram-bot-token "..."
```

This command will create a `~/sak-family-agents-deployment` directory with the following structure:

```
sak-family-agents-deployment/
├── config/
│   ├── common.env
│   ├── sakking.env
│   ├── sakthai.env
│   ├── saksee.env
│   ├── saksit.env
│   ├── saktan.env
│   └── sakjules.env
└── systemd/
    └── sakthai-telegram@.service
```

### Step 2: Install Configuration and Service Files

Copy the generated files to the standard locations for user-level configuration and `systemd` units.

```bash
# Create destination directories if they don't exist
mkdir -p ~/.config/sak-family-agents
mkdir -p ~/.config/systemd/user

# Copy the environment files
cp ~/sak-family-agents-deployment/config/*.env ~/.config/sak-family-agents/

# Copy the systemd service file
cp ~/sak-family-agents-deployment/systemd/sakthai-telegram@.service ~/.config/systemd/user/
```

### Step 3: Enable and Start the Agent Services

Reload the `systemd` user daemon to make it aware of the new service file. Then, enable and start a service for each agent.

```bash
# Reload the systemd user daemon
systemctl --user daemon-reload

# Enable and start each agent service
systemctl --user enable --now sakthai-telegram@sakking.service
systemctl --user enable --now sakthai-telegram@sakthai.service
systemctl --user enable --now sakthai-telegram@saksee.service
systemctl --user enable --now sakthai-telegram@saksit.service
systemctl --user enable --now sakthai-telegram@saktan.service
systemctl --user enable --now sakthai-telegram@sakjules.service
```

The `enable --now` command both starts the service immediately and ensures it starts automatically on future logins.

### Step 4: Verify the Services

An automated script is provided to check the status of all six agent services. Run it from the repository root:

```bash
python scripts/verify_vm_telegram_agents.py
```

This script will report if each service is active and show the last few log entries for each.

For more detailed manual checks, you can use the following commands:

```bash
# Check the status of a specific agent
systemctl --user status sakthai-telegram@sakking.service

# List all running agent units
systemctl --user list-units "sakthai-telegram@*.service"

# Tail the logs for a specific agent
journalctl --user -u sakthai-telegram@saktan.service -f
```

At this point, all six agents should be running and responsive on Telegram.
