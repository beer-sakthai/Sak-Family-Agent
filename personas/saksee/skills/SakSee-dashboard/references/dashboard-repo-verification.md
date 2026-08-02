# Dashboard Repository Verification

## Case Study: July 7, 2026 Session

In a recent session, the user asked about a dashboard fix and which repository it was from. Initially, there was confusion about the repository location:

1. The dashboard process was initially thought to be from `sakthai-agent-v2` repository
2. Upon investigation, it was found to be running from `/opt/data/Sak-Family-Agent/dashboard/`
3. This directory is part of the `Sak-Family-Agent` repository, which is cloned from `https://github.com/beer-sakthai/Sak-Family-Agent.git`

## Verification Commands

To verify which repository a dashboard is running from:

```bash
# Check running processes related to the dashboard
ps aux | grep dashboard

# Check the git repository information
cd /path/to/dashboard/directory
git remote -v

# Check repository details
ls -la /path/to/dashboard/directory/.git
```

## Alternative Commands for Port Checking

Not all systems have `lsof` installed by default. When investigating processes that might be using specific ports, use these alternatives:

```bash
# Check which process is using a port (if netstat is available)
netstat -tulpn | grep :3001

# Check process information directly
ps aux | grep sakthai

# Get detailed information about a specific process
ps -p <pid> -o pid,ppid,cmd
```

## Key Learning

Always verify the actual repository location before proceeding with dashboard operations. The dashboard may be located in different repositories depending on the context:
- `sakthai-agent-v2` - Traditional location for SakThai dashboard
- `Sak-Family-Agent` - Newer consolidated repository containing dashboard

This verification step should be added to the standard dashboard investigation procedure. Additionally, be prepared with alternative commands when common tools like `lsof` are not available.