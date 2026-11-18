# Google Colab CLI & MCP Integration

## Overview
This document outlines the Google Colab integration into the SakThai / Antigravity development environment, providing both headless VM orchestration and interactive browser-connected notebook execution.

---

## Architecture & Tooling

### 1. `colab` CLI (`google-colab-cli` v0.8.0)
- **Executable**: `/home/sak/.local/bin/colab`
- **Capabilities**:
  - Provision billable or free Colab VMs with accelerators (`--gpu T4`, `L4`, `A100`, `H100` or `--tpu v5e1`, `v6e1`).
  - Ephemeral single-command execution: `colab run --gpu T4 script.py`.
  - Stateful session execution: `colab exec -s <session> -f <script.py>`.
  - File sync: `colab upload`, `colab download`, `colab ls`.
  - Keyring storage configured via `keyrings.alt.file.PlaintextKeyring` for seamless CLI token persistence in WSL/headless environments.

### 2. Official Colab MCP Server (`googlecolab/colab-mcp` v1.0.1)
- **Executable**: `/home/sak/.local/bin/colab-mcp`
- **Type**: Stdio MCP Server.
- **Capabilities**:
  - Connects to active browser Colab sessions (`open_colab_browser_connection`).
  - Dynamically exposes live cell execution, notebook reading, editing, and error inspection to the AI agent.

### 3. Colab CLI MCP Server (`colab-cli-mcp` v0.1.0)
- **Executable**: `/home/sak/.local/bin/colab-cli-mcp`
- **Type**: Stdio MCP Server (42 tools).
- **Capabilities**:
  - Complete programmatic execution of Colab VMs: `colab_new`, `colab_stop`, `colab_restart_kernel`.
  - Script & Job execution: `colab_run`, `colab_exec`, `colab_job_start`, `colab_job_status`.
  - Notebook manipulation: `colab_notebook_create`, `colab_notebook_run_cell`, `colab_notebook_run_all`.
  - Drive-aware operations: `colab_drive_status`, `colab_drive_project_dir`.

---

## Antigravity CLI (`agy`) Configuration

1. **Plugin Package**:
   - Location: `/home/sak/.gemini/config/plugins/google-colab` (installed globally) and mirrored at `/home/sak/.agents/plugins/google-colab`.
   - Included Skills: `colab-operator`, `colab-drive-notebooks`.
   - Included MCP Servers: `colab-mcp`, `colab-cli-mcp`.

2. **Registered MCP Servers**:
   - `colab-mcp`: `stdio` $\rightarrow$ `/home/sak/.local/bin/colab-mcp`
   - `colab-cli-mcp`: `stdio` $\rightarrow$ `/home/sak/.local/bin/colab-cli-mcp`

---

## Authentication Instructions

- **Headless / Agent execution (ADC)**:
  ```bash
  gcloud auth application-default login \
    --scopes=openid,https://www.googleapis.com/auth/cloud-platform,https://www.googleapis.com/auth/userinfo.email,https://www.googleapis.com/auth/colaboratory
  ```
- **Interactive OAuth flow**:
  ```bash
  colab whoami
  ```
  Follow the generated URL, authorize with Google, and paste back the verification code.
