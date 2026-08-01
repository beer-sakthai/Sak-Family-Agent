# Missing Tools Workarounds - Additional Examples

## lsof Missing - July 7, 2026 Session

In a recent session, we encountered a system where `lsof` was not installed. This is a common scenario in minimal or containerized environments.

### Alternative Commands Used

When `lsof -i :3001,:3002 -P -n` failed with "lsof: command not found", we used alternative approaches:

```bash
# Check for processes directly
ps aux | grep sakthai

# Get detailed process information
ps -p <pid> -o pid,ppid,cmd --no-headers

# Check for dashboard processes specifically
ps aux | grep dashboard
```

### Key Learning

1. **Not all systems have lsof installed** - especially minimal or containerized environments
2. **Alternative approaches work well** - process investigation can be done with ps and pgrep
3. **Repository verification is crucial** - checking git remote information helps confirm repository locations

### Best Practices for Future Cases

1. Always have alternative methods ready when common tools are not available
2. Document successful workarounds for future reference
3. Use process-based investigation methods when port-checking tools are missing
4. Verify repository locations through multiple methods (process commands, git remotes, directory structure)