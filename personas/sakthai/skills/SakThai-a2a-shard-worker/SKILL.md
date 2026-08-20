---
name: SakThai-a2a-shard-worker
description: Claim and process A2A task shards from the bus.
version: 0.1.0
author: Hermes
platforms: [linux]
metadata:
  hermes:
    tags: [A2A, Task Worker, Shard Processing]
---

# Sak A2A Shard Worker

Process task shards distributed via the A2A message bus. Checks the bus inbox for `task_available` messages, claims the shard, processes the input, and submits the result back.

## When to Use

- Running as a cron job that checks the A2A bus periodically.
- Manually processing a shard that was assigned to you.
- Testing the A2A task pipeline end-to-end.

## How It Works

1. **Check inbox** at `POST http://localhost:3005/inbox` for messages with `type: "task_available"` addressed to your agent name.
2. **Claim the shard** at `POST http://localhost:3005/task/claim` to lock it so no other agent takes it.
3. **Process** the shard's `input` — run analysis, generate content, compute results.
4. **Submit result** at `POST http://localhost:3005/task/complete` with the output.

## Procedure

### 1. Check Inbox

```bash
curl -s -X POST http://localhost:3005/inbox \
  -H "Content-Type: application/json" \
  -d '{"agent":"<your-agent-name>"}'
```

This returns messages with `type: "task_available"`. Each has:
- `content.task_id` — the task identifier
- `content.shard_id` — which shard this is (0, 1, 2, ...)
- `content.total_shards` — how many shards total
- `content.input` — the data to process
- `content.description` — what the task is about

### 2. Claim the Shard

```bash
curl -s -X POST http://localhost:3005/task/claim \
  -H "Content-Type: application/json" \
  -d '{"task_id":"<task_id>","shard_id":<shard_id>,"agent":"<your-agent-name>"}'
```

Response includes the full `input` if claim succeeds. If it returns `"status":"error"`, another agent already claimed it — skip to the next message.

### 3. Process and Submit

Process the input according to the task description. Then submit:

```bash
curl -s -X POST http://localhost:3005/task/complete \
  -H "Content-Type: application/json" \
  -d '{"task_id":"<task_id>","shard_id":<shard_id>,"from":"<your-agent-name>","result":"<your output>"}'
```

The result is a string. For complex outputs, serialize as JSON.

### 4. Full Worker Sequence

Self-contained prompt for a cron job:

```
Check the A2A bus at http://localhost:3005 for task_available messages addressed to <your_name>.
For each one, call /task/claim to claim it, then process the input carefully,
then call /task/complete to submit your result. Report what you found and did.
```

## Agent Names

| Agent | Bus Name |
|-------|----------|
| SakKing | `sakking` |
| SakThai | `sakthai` |
| SakSee | `saksee` |
| SakSit | `saksit` |

## Pitfalls

- **Already claimed**: If `/task/claim` returns `"status":"error"`, the shard was taken. Move to the next message.
- **Bus down**: Check `/health` first. The bus auto-stores messages — nothing lost if you poll again later.
- **One shard per cycle**: Process one shard per cron tick. If there are N shards, they get spread across N cron cycles between all workers.
- **Result format**: The `result` field is a string. For structured data, use `json.dumps()`.
- **Stale messages**: Messages persist even after processing. Use the `since` timestamp to avoid re-processing old ones.

## Verification

```
curl -s -X POST http://localhost:3005/inbox -H "Content-Type: application/json" -d '{"agent":"<your_name>"}'
```
