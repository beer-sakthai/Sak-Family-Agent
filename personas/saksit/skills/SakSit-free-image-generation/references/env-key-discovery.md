# Env Key Discovery (Jul25 session)

## Where keys actually live

The `auth.json` file in the profile stores credential metadata with **sealed
secret fingerprints** — the actual key values are NOT readable from auth.json.
To get a usable API key, read `.env` files directly.

## Key locations

| File | Contents |
|------|----------|
| `/opt/data/profiles/saksit/.env` | SakSit profile secrets |
| `/opt/data/profiles/saksee/.env` | SakSee profile secrets (same keys) |
| `/opt/data/profiles/sakthai/.env` | SakThai profile secrets |
| `/opt/data/.env` | Root env file (shared) |

## Keys found in this env (Jul25)

| Key | Value prefix | Status |
|-----|-------------|--------|
| `GOOGLE_API_KEY` | `AQ.Ab8RN6...` | Works but free quota exhausted |
| `OPENROUTER_API_KEY` | `sk-or-...` | Only 82 tokens credit left |
| `MCP_COMPOSIO_API_KEY` | `ck_-tCxV...` | Composio MCP works |
| `HF_TOKEN` | `hf_sgt...` | Quota exhausted (403) |
| `OPENCODE_GO_API_KEY` | `sk-bri...` | For opencode-go provider only |

## How to read

```bash
grep GOOGLE_API_KEY /opt/data/profiles/saksit/.env
grep OPENROUTER_API_KEY /opt/data/profiles/saksit/.env
grep MCP_COMPOSIO_API_KEY /opt/data/profiles/saksit/.env
```
