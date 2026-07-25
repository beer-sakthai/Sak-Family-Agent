# A2A Message Bus — Agent-to-Agent Communication

A lightweight HTTP message bus for family agents to send and receive messages. Runs on port 3005.

## Endpoints

| Method | Path | Body | Description |
|--------|------|------|-------------|
| POST | `/send` | `{"from":"sakthai","to":"saksee","type":"message","content":"..."}` | Send a message |
| POST | `/inbox` | `{"agent":"saksee"}` | Get last 20 messages for an agent |
| POST | `/status` | — | List all agents with messages |

### Send a message

```bash
curl -X POST http://localhost:3005/send \
  -H "Content-Type: application/json" \
  -d '{"from":"sakthai","to":"saksee","content":"Hello from SakThai!"}'
```

### Read inbox

```bash
curl -X POST http://localhost:3005/inbox \
  -H "Content-Type: application/json" \
  -d '{"agent":"saksee"}'
```

## How agents discover messages

Each agent's cron or session startup checks `/inbox` for its name or `"to":"all"`. The A2A bus keeps the last 100 messages in a JSON file at `/opt/data/profiles/sakthai/cache/a2a_messages.json`.

## The bus itself

The A2A bus runs as a background process on the host machine (not inside any agent's session). It's accessible at `http://localhost:3005` from any Hermes process on the same machine.

## See also

- `sak-family-handoff` — the formal delegation protocol
- The running bus at `/opt/data/profiles/sakthai/a2a-bus.py`
