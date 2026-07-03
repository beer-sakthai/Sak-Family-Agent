---
name: asset-monitor
description: "Monitors a list of public URLs from a file and sends a Telegram alert on failure."
author: SakThai
version: 1.0.0
created: 2026-06-22
updated: 2026-06-22
---

# Public Asset Monitor

This skill provides a simple, robust way to monitor the availability of a list of public web assets (like Hugging Face models, datasets, or any public URL). If any asset becomes unavailable, it sends an alert to a specified Telegram chat.

It reuses the verified, no-auth logic from the `mlops-hf-train-manual-upload` skill.

## ✅ When to Use

- You need to continuously verify that public-facing models, datasets, or API endpoints are live.
- You want to set up a cron job to run this check and be alerted automatically on failure.

## ⚙️ Configuration

First, create a configuration file that lists the URLs you want to monitor.

**File path**: `/home/sakthai/config/asset_monitor_urls.txt`

**Format**: One URL per line.

```
https://huggingface.co/datasets/Nanthasit/hf-training-composio-tools-50
https://huggingface.co/models/Nanthasit/sakthai-context-0.5b-tools
https://google.com/this-will-fail-404
```

## 🚀 Workflow

The main script orchestrates the monitoring and alerting.

**Script path**: `/home/sakthai/skills/monitoring/asset-monitor/scripts/run_asset_monitor.py`

This script will:

1. Read the URLs from the configuration file.
2. Execute the `verify_hf_upload.py` script, passing the URLs to it.
3. If the verification script fails (i.e., exits with a non-zero status code), it will construct an error message.
4. It will then use the `telegram` tool to send the error message to the specified chat ID.

### How to Run

To run the monitor, use the `terminal` tool. You must provide your Telegram Chat ID as an environment variable.

```bash
TELEGRAM_CHAT_ID="your_chat_id" python3 /home/sakthai/skills/monitoring/asset-monitor/scripts/run_asset_monitor.py
```

If all URLs are accessible, the script will print a success message and exit silently.

If a failure occurs, you will receive a Telegram message like:

> 🚨 Asset Monitor Failure!
> The following assets may be down:
>
> - <https://google.com/this-will-fail-404>

## 🚨 Pitfalls

- Ensure the `TELEGRAM_CHAT_ID` environment variable is set correctly.
- The `telegram` tool must be available and configured in your environment.
- The URL list file must exist at the specified path.
