# StepSecurity Integration Guide — House of Sak (`beer-sakthai`)

This document details the configuration and operations for StepSecurity CI/CD security, Model Context Protocol (MCP) tooling, and Dev Machine Guard telemetry within the **House of Sak** ecosystem.

---

## 1. Overview & Tenant Identity

The repository is integrated with StepSecurity for runtime supply-chain protection and CI/CD security:

- **Customer / Tenant ID**: `beer-sakthai`
- **API Endpoint**: `https://agent.api.stepsecurity.io`
- **OIDC Audience**: `beer-sakthai.api.stepsecurity.io`
- **MCP Server Endpoint**: `https://agent.api.stepsecurity.io/v1/mcp?customer=beer-sakthai`

---

## 2. Model Context Protocol (MCP) Server Integration

The StepSecurity MCP server exposes StepSecurity platform APIs directly to AI coding assistants and autonomous agents (specifically **SakJules**, the Master of Automation & CI/CD, and **SakKing**, the Lead Orchestrator).

### Configuration Files

1. **Workspace Root** (`.mcp.json`):
   ```json
   {
     "mcpServers": {
       "stepsecurity": {
         "url": "https://agent.api.stepsecurity.io/v1/mcp?customer=beer-sakthai",
         "headers": {
           "Authorization": "Bearer ${STEP_SECURITY_API_KEY}"
         }
       }
     }
   }
   ```

2. **Persona Configurations**:
   - `personas/sakjules/config/mcp.json`
   - `personas/sakking/config/mcp.json`

### Supported Agent Capabilities

With this integration, agents can query:
- **Incident Exposure Checks**: `check_incident_exposure`, `check_npm_package_exposure`, `check_pypi_package_exposure`, `check_ioc_in_baseline`.
- **Workflow Run Investigation**: `list_outbound_calls_in_run`, `get_run_process_events`, `get_run_file_events`, `list_run_detections`.
- **Actions Security Posture**: `get_actions_security_summary`, `get_harden_runner_coverage`, `list_recent_workflow_runs`.
- **Dev Machine Guard Inventory**: `list_dev_machines`, `list_ai_coding_agents`, `list_mcp_servers`.

---

## 3. GitHub Actions Keyless OIDC Authentication

StepSecurity supports keyless authentication via OpenID Connect (OIDC), exchanging the GitHub workflow OIDC token for a short-lived StepSecurity API token.

### Reusable Workflow

The repository provides [`.github/workflows/reusable-stepsecurity-token.yml`](../.github/workflows/reusable-stepsecurity-token.yml):

```yaml
jobs:
  get-token:
    uses: beer-sakthai/Sak-Family-Agent/.github/workflows/reusable-stepsecurity-token.yml@main
    with:
      customer: 'beer-sakthai'
      audience: 'beer-sakthai.api.stepsecurity.io'
    permissions:
      contents: read
      id-token: write

  use-token:
    needs: get-token
    runs-on: ubuntu-latest
    steps:
      - name: Call StepSecurity API with Minted Token
        run: |
          curl -H "Authorization: Bearer ${{ needs.get-token.outputs.token }}" \
               https://agent.api.stepsecurity.io/v1/beer-sakthai/summary
```

### In-Job Token Minting (Script Pattern)

Workflows requiring immediate token minting in a step use `actions/github-script`:

```yaml
permissions:
  id-token: write
  contents: read

steps:
  - name: Mint StepSecurity API token
    id: ss
    uses: actions/github-script@3a2844b7e9c422d3c10d287c895573f7108da1b3 # v9.0.0
    env:
      CUSTOMER: 'beer-sakthai'
      AUDIENCE: 'beer-sakthai.api.stepsecurity.io'
    with:
      script: |
        const audience = process.env.AUDIENCE;
        const customer = process.env.CUSTOMER;
        const token = await core.getIDToken(audience);
        const res = await fetch(`https://agent.api.stepsecurity.io/v1/${customer}/oidc/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ github_oidc_token: token })
        });
        if (!res.ok) {
          core.setFailed(`Exchange failed: ${res.status}`);
          return;
        }
        const data = await res.json();
        core.setSecret(data.token);
        core.setOutput('token', data.token);
```

---

## 4. Dev Machine Guard Linux Loader

The verified StepSecurity Device Agent loader is maintained at [`scripts/stepsecurity-loader-linux-beer-sakthai.sh`](../scripts/stepsecurity-loader-linux-beer-sakthai.sh).

### Features
- Verifies binary integrity using SHA-256 and Ed25519 SSH signature verification via `ssh-keygen -Y verify`.
- Installs `stepsecurity-dev-machine-guard` under `$HOME/.stepsecurity/bin`.
- Supports environment variable overrides for customer ID, endpoint, and API key (`STEP_SECURITY_CUSTOMER_ID`, `STEP_SECURITY_API_ENDPOINT`, `STEP_SECURITY_API_KEY`).

### Execution Commands

```bash
# 1. Inspect options and help
bash scripts/stepsecurity-loader-linux-beer-sakthai.sh help

# 2. Run one-off telemetry collection and reporting
bash scripts/stepsecurity-loader-linux-beer-sakthai.sh send-telemetry

# 3. Full installation with scheduled systemd user service & timer (15-min interval)
bash scripts/stepsecurity-loader-linux-beer-sakthai.sh install

# 4. Uninstall agent and remove user services
bash scripts/stepsecurity-loader-linux-beer-sakthai.sh uninstall
```
