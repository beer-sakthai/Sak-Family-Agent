# Sakthai-Agent-v2 Investigation - July 7, 2026

## Key Finding

The sakthai-agent-v2 is not a separate repository located at `/home/sakthai/sakthai-agent-v2` as previously assumed, but rather a component of the Sak-Family-Agent repository.

## Actual Location

- Main package: `/opt/data/Sak-Family-Agent/personas/sakthai/sakthai/`
- Skill for running it: `/opt/data/Sak-Family-Agent/.claude/skills/run-sakthai-agent-v2/`

## Investigation Commands Used

```bash
# Check for sakthai directories
find /opt/data -type d -name "*sakthai*" 2>/dev/null

# Check the skill directory
ls -la /opt/data/Sak-Family-Agent/.claude/skills/ | grep sakthai

# Check the actual package location
ls -la /opt/data/Sak-Family-Agent/personas/sakthai/sakthai/
```

## Key Learning Points

1. **Repository Structure**: The sakthai-agent-v2 is integrated into the Sak-Family-Agent repository rather than being a standalone repository.

2. **Package Location**: The actual sakthai package is located at `personas/sakthai/sakthai/` within the Sak-Family-Agent repository, not at a root-level `sakthai/` directory.

3. **Running Sakthai**: The correct way to run sakthai-agent-v2 is using the skill at `.claude/skills/run-sakthai-agent-v2/` within the Sak-Family-Agent repository.

4. **Setup Process**: Use `uv sync --all-extras` from the Sak-Family-Agent repository root rather than navigating to a separate sakthai-agent-v2 directory.

## Best Practices for Future Investigations

1. Always verify repository locations when investigating processes
2. Check skill directories and documentation for the most up-to-date information
3. Look for integration patterns where tools might be components of larger repositories
4. Use find commands to locate directories when expected paths don't exist