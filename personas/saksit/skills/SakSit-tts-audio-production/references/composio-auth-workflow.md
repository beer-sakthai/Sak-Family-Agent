# Composio ElevenLabs Auth Workflow

Troubleshooting guide for ElevenLabs connection issues in Composio.

---

## The Two Error States

### "Elicitation is unavailable for this session. Approve this tool in the Composio dashboard."

**Root cause:** The OAuth connection was created but the tool-specific permissions weren't granted during the auth flow. The connection shows as "ACTIVE" in `COMPOSIO_MANAGE_CONNECTIONS`, but individual tools can't be called.

**Fix:** Create a new connection with `action='add'`:
1. `COMPOSIO_MANAGE_CONNECTIONS(action='add', name='elevenlabs', alias='fresh-alias')`
2. Share the returned `redirect_url` as a clickable link: `🔗 [Connect ElevenLabs]({url})`
3. Tell the user to open the link and authenticate ElevenLabs in their browser
4. `COMPOSIO_WAIT_FOR_CONNECTIONS(toolkits=['elevenlabs'])` — waits until ACTIVE
5. Test with `ELEVENLABS_GET_VOICES`

### "No response to elicitation prompt within the allowed time."

**Root cause:** Same as above, but the auth session expired or was never completed. The redirect URL expires in ~10 minutes.

**Fix:** Same as above — generate a fresh auth link. Do NOT reuse old links.

---

## Auth Flow Script

```
Step 1: COMPOSIO_MANAGE_CONNECTIONS
         action='add', name='elevenlabs', alias='elevenlabs-<purpose>'
         → returns redirect_url

Step 2: Present link to user
         "🔗 [Connect ElevenLabs]({redirect_url}) (expires in ~10 min)"

Step 3: COMPOSIO_WAIT_FOR_CONNECTIONS
         toolkits=['elevenlabs']
         → waits until ACTIVE

Step 4: Test the connection
         Run ELEVENLABS_GET_VOICES or ELEVENLABS_GET_MODELS
         If it works, all ElevenLabs tools are available
```

---

## Session Management

When working with ElevenLabs tools in Composio:

1. **Use the same `session_id`** across all calls within a workflow (COMPOSIO_SEARCH_TOOLS → COMPOSIO_MULTI_EXECUTE_TOOL → etc.)
2. If you hit an elicitation error, you may need to **start a new session** with `generate_id: true` after reconnecting
3. The session ID from the original `COMPOSIO_SEARCH_TOOLS` call should be passed as `session_id` in all subsequent meta tool calls

---

## Active Accounts

Beer has one active default ElevenLabs connection:
- `elevenlabs_dedan-shower` (default, active)
- Multiple "initiated" accounts may exist from failed auth attempts — these can be ignored or removed

---

## Built-in TTS Config (Alternative Path)

If Beer provides his ElevenLabs API key directly, the Hermes built-in `text_to_speech` tool can be configured:

```yaml
# config.yaml
tts:
  provider: elevenlabs
  voice: "JBFqnCBsd6RMkjVDRZzb"
```

Plus `ELEVENLABS_API_KEY` in `.env`.

Until he provides the key, always use the Composio ELEVENLABS_TEXT_TO_SPEECH tool.
