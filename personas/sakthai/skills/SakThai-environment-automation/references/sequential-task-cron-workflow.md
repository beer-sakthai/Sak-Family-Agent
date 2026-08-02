# Sequential Multi-Task Processing with Healing Crons

## Signal

User says something like "all start one by one after finishing one task start next one, send cronjob to send their ok." This means:

1. Treat all listed tasks as a strict FIFO queue
2. Execute one at a time, in order
3. Verify each task completes before starting the next
4. After ALL tasks are done, set up healing/status crons for each
5. Report final status

## Workflow

### Phase 1: Queue Setup
```python
todo(todos=[
    {"id": "task1", "content": "description", "status": "in_progress"},
    {"id": "task2", "content": "description", "status": "pending"},
    ...
])
```

### Phase 2: Execute Sequentially
For each task:
1. Mark as `in_progress`
2. Execute
3. Verify (test, curl, check output)
4. Mark as `completed`
5. Report to user

### Phase 3: Healing Crons
After all tasks complete, create a watchdog/healer script:
```bash
# status-checker.sh — checks all tasks' deliverables
#!/bin/bash
# Check each deliverable
curl -s -o /dev/null -w "%{http_code}" "http://localhost:3003/"  # RAG server
curl -s -o /dev/null -w "%{http_code}" "http://localhost:3005/status"  # A2A bus
...
```

Then create cron via:
```python
cronjob(action='create', no_agent=True, schedule='2m', script='status-checker.sh')
```

## Pitfalls

- **Do not parallelise.** FIFO means finish N before touching N+1. Parallel execution wastes user's attention.
- **Verification step is mandatory.** Running a command is not the same as confirming it worked. Test each deliverable before declaring done.
- **Crons should be `no_agent=True`** — simple shell scripts, no LLM cost per tick.
- **Report progress after each task** — user wants to see completion not wait until the end.
