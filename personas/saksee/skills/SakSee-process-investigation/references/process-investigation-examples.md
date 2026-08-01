# Process Investigation Examples

## Case Study: July 7, 2026 Session

In a recent session, the user asked about a dashboard fix and wanted to know which repository it was from. Here's how we investigated:

### Initial Investigation

```bash
# Check for running dashboard processes
ps aux | grep dashboard

# Output showed:
# hermes        12  0.1  1.7 567244 138300 ?       Sl   Jul06   1:19 /opt/hermes/.venv/bin/python3 /opt/hermes/.venv/bin/hermes dashboard --host 0.0.0.0 --port 4860 --no-open --skip-build
# root         979  0.0  0.7 23781304 60372 pts/2  Sl+  Jul06   0:00 node /opt/data/Sak-Family-Agent/dashboard/node_modules/.bin/vite --host
# hermes     32751  0.0  0.0   3888  2080 ?        S    02:30   0:00 grep dashboard
```

### Repository Verification

We then checked the repository information:

```bash
# Check the git repository information
cd /opt/data/Sak-Family-Agent && git remote -v

# Output showed:
# origin	https://github.com/beer-sakthai/Sak-Family-Agent.git (fetch)
# origin	https://github.com/beer-sakthai/Sak-Family-Agent.git (push)
```

### Dashboard Directory Verification

We also checked the dashboard directory specifically:

```bash
# Check the dashboard directory
ls -la /opt/data/Sak-Family-Agent/dashboard/

# Output showed the dashboard is part of the Sak-Family-Agent repository
```

### Key Learning

The dashboard was running from the `Sak-Family-Agent` repository rather than the initially assumed `sakthai-agent-v2` repository. This highlights the importance of:

1. Always verifying the actual repository location before proceeding with operations
2. Checking process details to understand the exact path and repository
3. Not making assumptions about repository locations based on process names

## Common Patterns

### Finding Process by Name

```bash
# Generic pattern for finding processes
ps aux | grep <service_name>

# Example for finding all sakthai-related processes
ps aux | grep sakthai
```

### Checking Port Usage

```bash
# Check which process is using a specific port
lsof -i :<port_number>

# If lsof is not available, try netstat
netstat -tulpn | grep :<port_number>
```

### Getting Process Details

```bash
# Get detailed information about a specific process
ps -p <pid> -o pid,ppid,cmd --no-headers

# Show full command line for a process
ps -p <pid> -o pid,cmd,args
```

### Repository Verification

```bash
# Navigate to the process directory and check git info
cd /path/to/process/directory
git remote -v
ls -la .git
```