# Process Investigation Examples - SakSee Session July 7, 2026

## Case: Dashboard Process Investigation

In this session, we investigated a dashboard process that was running on the system. Here's what we discovered:

### Initial Investigation
1. We found a process related to sakthai dashboard with PID 32117
2. We attempted to check port usage with `lsof` but found the command was not installed
3. We used alternative methods to investigate the process

### Commands Used
```bash
# Check for sakthai processes
ps aux | grep sakthai

# Check for dashboard processes specifically
ps aux | grep dashboard

# Try to check port usage (failed due to missing lsof)
lsof -i :3001,:3002 -P -n

# Get detailed process information
ps -p 32117 -o pid,ppid,cmd --no-headers
```

### Key Findings
1. The dashboard was running as part of the Sak-Family-Agent repository, not sakthai-agent-v2 as initially assumed
2. The dashboard directory was located at `/opt/data/Sak-Family-Agent/dashboard/`
3. The repository was cloned from `https://github.com/beer-sakthai/Sak-Family-Agent.git`

### Lessons Learned
- Always verify repository locations when investigating processes
- Not all systems have `lsof` installed; have alternative methods ready
- Process investigation often requires multiple approaches to get complete information
- Repository consolidation can lead to confusion about where processes are running from

### Best Practices for Future Investigations
1. Check the actual command line of the process to determine its origin
2. Verify git remote information to confirm repository location
3. Have alternative commands ready when common tools like `lsof` are not available
4. Document findings to help with future investigations of similar processes