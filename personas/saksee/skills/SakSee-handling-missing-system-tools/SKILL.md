---
name: SakSee-handling-missing-system-tools
description: "Handle situations where common system tools like lsof, netstat, or gh are not available, and use alternative methods to accomplish the same tasks."
version: 1.0.0
author: SakSee
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [system, tools, troubleshooting, lsof, netstat, gh]
---

# Handling Missing System Tools

## Overview

This skill covers techniques for handling situations where common system tools are not available, and using alternative methods to accomplish the same tasks. This is particularly important in constrained environments where certain tools may not be installed.

## When to Use

- When a command like `lsof`, `netstat`, or `gh` is not found
- When working in a constrained environment with limited tool availability
- When needing to accomplish tasks that typically require specific tools but those tools are not available

## Prerequisites

- Basic understanding of Unix/Linux command line
- Familiarity with alternative methods for common tasks
- Knowledge of process management commands

## Quick Reference

| Missing Tool | Alternative Commands | Purpose |
|--------------|---------------------|---------|
| `lsof` | `ps aux`, `pgrep`, `netstat` | Process and port investigation |
| `netstat` | `ss`, `cat /proc/net/tcp` | Network connection information |
| `gh` | `curl` with GitHub API, `git` commands | GitHub operations |

## Examples from July 7, 2026 Session

In a recent session, both `lsof` and `netstat` were unavailable. The following alternative approaches were used successfully:

1. **Process Investigation**: Used `ps aux | grep sakthai` to find running processes
2. **Port Checking**: Used `curl -I http://localhost:3001/` to verify server accessibility
3. **Process Details**: Used `ps -p <pid> -o pid,ppid,cmd` to get process information

## Procedure

### 1. Handling Missing lsof

When `lsof` is not available for checking port usage:

```bash
# Alternative to lsof for checking port usage
netstat -tulpn | grep :<port>

# Check process information directly
ps aux | grep <process_name>

# Get detailed information about a specific process
ps -p <pid> -o pid,ppid,cmd

# Check for processes by pattern
pgrep -f "<pattern>"
```

### 2. Handling Missing netstat

When `netstat` is not available:

```bash
# Use ss instead of netstat
ss -tulpn | grep :<port>

# Check network connections directly from /proc
cat /proc/net/tcp | grep <port_hex>

# Use ps to check network-related processes
ps aux | grep -E "(nc|socat|ssh|nginx|apache)"
```

### 3. Handling Missing gh CLI

When `gh` CLI is not available for GitHub operations:

```bash
# Use curl with GitHub API directly
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/<owner>/<repo>

# Use git commands for basic operations
git remote -v
git branch -vv
git status

# For more complex operations, use Composio tools when available
```

### 4. General Approach for Missing Tools

1. **Identify the purpose** of the missing tool
2. **Find alternative commands** that can accomplish the same purpose
3. **Use built-in system information** from /proc, /sys, etc.
4. **Leverage available tools** like ps, grep, cat, etc.
5. **Use Composio or other MCP tools** when available for complex operations

## Pitfalls

- **Assuming tools are always available.** Always have alternative methods ready.
- **Not documenting workarounds.** When you find a working alternative, document it for future use.
- **Overlooking built-in system information.** Many systems have detailed information available in /proc, /sys, and other standard locations.
- **Relying too heavily on specific tools.** Develop skills with multiple approaches to common tasks.
- **Not verifying results.** When using alternative methods, verify that the results are equivalent to what the standard tool would provide.

## Verification

To verify that you've successfully worked around a missing tool:

1. Confirm that the alternative method provides the same information
2. Cross-check results with multiple approaches when possible
3. Document the workaround for future reference (see `references/missing-tools-workarounds.md` for examples)
4. Test the alternative method on a known case to ensure accuracy

See `references/missing-tools-workarounds.md` for specific examples and detailed workarounds for common missing tools.