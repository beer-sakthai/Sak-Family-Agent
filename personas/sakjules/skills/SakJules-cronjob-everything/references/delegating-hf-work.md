# Delegating Cron Work to Subagents

Use `delegate_task` to parallelize HF batch operations (max 3 concurrent):

```python
delegate_task(tasks=[
    {"goal": "Improve card for Nanthasit/sakthai-context-1.5b-v2",
     "context": "Add download badge, usage examples, YAML metadata. Use HF_TOKEN."},
    {"goal": "Health check Nanthasit/sakthai-coder-1.5b",
     "context": "Verify README, cross-links, download stats."},
])
```

## When to Delegate for HF Cron Work

- Improving multiple model/dataset cards simultaneously
- Running parallel health checks across repos
- Batch card updates across 10+ repos while monitoring results
- Scanning trending models while uploading eval results

## Constraints

- Max 3 concurrent subagents
- No nested delegation (subagents cannot delegate further)
- Each subagent gets its own terminal + HF_TOKEN
- Pass FULL context — subagents have no conversation history
- Results return asynchronously as new messages

## Auth

- Primary: `HF_TOKEN` env var (passed to subagents automatically)
- Backup: Composio HF OAuth connection (active, expires 2026-08-30)
