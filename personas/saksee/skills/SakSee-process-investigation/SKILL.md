---
name: SakSee-process-investigation
description: "Investigate and manage system processes for debugging, monitoring, and verification purposes."
---

# Process Investigation

Investigate and manage system processes for debugging, monitoring, and verification purposes. This skill covers techniques for identifying running processes, understanding their origins, and verifying their status.

## When to Use

- User asks about running services or processes
- Need to verify if a service is running
- Investigating system resource usage
- Debugging process-related issues
- Verifying which repository or codebase a process is running from

## Prerequisites

- Basic understanding of Unix/Linux process management
- Familiarity with terminal commands

## Quick Reference

| Command | Action |
|---------|--------|
| `ps aux | grep <process>` | Find processes by name |
| `pgrep -f "<pattern>"` | Find process IDs by pattern |
| `lsof -i :<port>` | Check which process is using a port |
| `ps -p <pid> -o pid,ppid,cmd` | Get details about a specific process |

## Procedure

### 1. Finding Running Processes

To find processes related to a specific service or application:

```bash
# Search for processes by name
ps aux | grep sakthai

# Find process IDs by pattern
pgrep -f "sakthai dashboard"

# Show all processes with specific keywords
ps aux | grep -E "(dashboard|sakthai)"
```

### 2. Getting Process Details

Once you have a process ID, get more information:

```bash
# Get detailed information about a specific process
ps -p 12345 -o pid,ppid,cmd --no-headers

# Show full command line for a process
ps -p 12345 -o pid,cmd,args

# Show process with parent-child relationships
ps -ef | grep 12345
```

### 3. Checking Port Usage

To verify which process is using a specific port:

```bash
# Check which process is using a port (Linux)
lsof -i :3001

# Alternative using netstat (if available)
netstat -tulpn | grep :3001

# Check multiple ports
lsof -i :3001,:3002
```

### 4. Verifying Repository Origins

To determine which repository or codebase a process is running from:

```bash
# Check the working directory of a process
ps -p <pid> -o pid,cmd

# If the command shows a path, navigate to that directory and check git info
cd /path/to/process/directory
git remote -v
ls -la .git

# Check the full process tree
ps -ef | grep <process_name>
```

## Pitfalls

- **Process ID changes**: Process IDs can change between system restarts or process restarts
- **Multiple instances**: There may be multiple instances of the same process running
- **Permissions**: Some process information may not be accessible without appropriate permissions
- **Missing tools**: Not all systems have `lsof` or `netstat` installed by default
- **Repository confusion**: Processes may be running from different repositories than expected; always verify the actual location

## Verification

To verify that you've correctly identified a process:

1. Confirm the process is running with `ps aux | grep <process>`
2. Check that it's listening on the expected port with `lsof -i :<port>`
3. Verify the repository or codebase location with `ps -p <pid> -o cmd` and checking the git remote
4. Confirm functionality by accessing the service if applicable
5. Check references like `references/sakthai-agent-v2-investigation.md` for specific examples of repository structure investigations
6. See `references/food-penguin-limited-investigation.md` for an example of investigating a complex dashboard repository

See `references/process-investigation-examples.md` for specific examples and common scenarios.