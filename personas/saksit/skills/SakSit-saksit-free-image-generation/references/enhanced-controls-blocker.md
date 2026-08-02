# Composio Enhanced Controls — Gemini Image Gen Blocker

> Error encountered 2026-07-23 while trying GEMINI_GENERATE_IMAGE via Composio.

## The Error

```
Helper Function Error:Bad Request Error:run_composio_tool:
{'message': 'Enhanced Controls is not supported for this session because
your client (e.g. Claude Web, ChatGPT) does not support elicitation.
Please go to https://dashboard.composio.dev/org/connect/settings and
disable enhanced controls to continue.',
 'code': 4300, 'slug': 'ToolRouterV2_BadRequest', 'status': 400}
```

## Symptoms

| Symptom | Where it appears |
|---------|-----------------|
| "No response to elicitation prompt within the allowed time" | `COMPOSIO_MULTI_EXECUTE_TOOL` (timed out — masks the real error) |
| Clear 400 error with code 4300 | `COMPOSIO_REMOTE_WORKBENCH` via run_composio_tool() |

## Root Cause

Composio **Enhanced Controls** is ON in the workspace/organization settings. This feature requires "elicitation" (user-in-the-loop confirmation) for sensitive tools like image generation. When the client (Hermes agent, Claude Code, etc.) cannot provide interactive elicitation, the tool refuses to execute.

## Fix

1. Visit https://dashboard.composio.dev/org/connect/settings
2. Locate the **Enhanced Controls** toggle
3. Turn it **OFF**
4. Retry GEMINI_GENERATE_IMAGE

## What does NOT fix it

- Changing safety_settings on the Gemini prompt
- Using a different Gemini model
- Using the workbench instead of multi-execute
- Setting longer timeouts
- DATABRICKS_SETTINGS_ENHANCED_SECURITY_MONITORING_UPDATE (unrelated — Databricks only)

## Impact

All Gemini tools may be affected, not just image generation. Disabling Enhanced Controls is the only solution.
