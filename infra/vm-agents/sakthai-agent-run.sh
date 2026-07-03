#!/usr/bin/env bash
# Entry point for sakthai-telegram@<agent>.service. Fetches secrets from Azure
# Key Vault via the VM's managed identity (IMDS) at process start instead of
# reading them from a static env file, so no secret ever needs to be pushed
# to the VM out of band (e.g. through `az vm run-command`, which persists
# script/parameter content in Azure's run-command history).
set -euo pipefail
AGENT="$1"
VAULT="kv-beernant505684507543"
REPO="$HOME/Sak-Family-Agent"

get_secret() {
  local secret_name="$1"
  local kv_token
  kv_token=$(curl -s -H "Metadata:true" "http://169.254.169.254/metadata/identity/oauth2/token?resource=https://vault.azure.net&api-version=2018-02-01" | python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])")
  curl -s -H "Authorization: Bearer $kv_token" "https://$VAULT.vault.azure.net/secrets/$secret_name?api-version=7.4" | python3 -c "import json,sys; print(json.load(sys.stdin)['value'])"
}

export OPENAI_API_KEY="$(get_secret sakthai-openai-key)"
export TELEGRAM_BOT_TOKEN="$(get_secret telegram-$AGENT)"
export OPENAI_BASE_URL=https://sakthai-resource.openai.azure.com/openai/v1
export SAKTHAI_PROVIDER=openai
export TELEGRAM_ALLOWED_USER_IDS=8618306046
export SAKTHAI_WITH_SKILLS=
export SAKTHAI_FAST=1
export SAKTHAI_HOME="$HOME/.sakthai/$AGENT"
export SAKTHAI_SYSTEM_PROMPT_FILE="$REPO/personas/$AGENT/SOUL.md"

case "$AGENT" in
  sakking) export SAKTHAI_MODEL=model-router ;;
  sakthai) export SAKTHAI_MODEL=gpt-4o-mini ;;
  saksit)  export SAKTHAI_MODEL=Kimi-K2.5 ;;
  saktan)  export SAKTHAI_MODEL=gpt-4o-mini ;;
  *) echo "unknown agent $AGENT" >&2; exit 1 ;;
esac

exec "$REPO/.venv/bin/python" -m sakthai.telegram.bot
