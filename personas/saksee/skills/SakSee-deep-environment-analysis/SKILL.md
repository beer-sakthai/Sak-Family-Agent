---
name: SakSee-deep-environment-analysis
description: Perform deep research and analysis of environment files with systematic investigation
  and diagnostic capabilities.
...
---

# Deep Environment Analysis

Perform deep research and systematic analysis of environment files with advanced diagnostic capabilities. This skill combines methodical investigation techniques with diagnostic tools to understand complex system states and file structures.

## When to Use
- When investigating complex system configurations or environment files
- When trying to understand why a process is behaving unexpectedly
- When performing root cause analysis of system issues
- When documenting detailed findings from environment exploration
- When creating comprehensive analysis reports for technical documentation
- When needing to diagnose file-based issues in complex systems

## Prerequisites
- Basic understanding of Unix/Linux file systems
- Familiarity with terminal commands and shell scripting
- Access to the target environment for investigation
- Python 3.x installed for analysis scripts
- Git for version control of analysis findings

## How to Run
Invoke through the `terminal` tool with appropriate commands for file investigation, or use `execute_code` for Python-based analysis. Use `delegate_task` for complex multi-step investigations.

## Quick Reference
- `find /path -name "*pattern*" -type f` - Find files matching a pattern
- `ls -la /path` - List directory contents with details
- `file /path/to/file` - Determine file type
- `stat /path/to/file` - Get detailed file information
- `grep -r "pattern" /path` - Search for patterns recursively
- `python3 analysis_script.py` - Run Python analysis scripts

## Procedure

1. **Initial Environment Assessment**
   - Use `terminal` to run `find /opt/data -type f -name "*analysis*" 2>/dev/null` to locate existing analysis files
   - Check for plan files with `find /opt/data -name "*plan*" -type f 2>/dev/null`
   - Document findings in a structured format

2. **Systematic File Investigation**
   - Use `search_files` to locate relevant files by content patterns
   - Use `read_file` to examine file contents with line numbers
   - Create directory structure maps with `terminal(command="find /path -type d")`
   - Identify file types with `terminal(command="file /path/to/file")`

3. **Deep Diagnostic Analysis**
   - For Python-based analysis, use `execute_code` with hermes_tools
   - Create analysis scripts that can process multiple files systematically
   - Use pattern matching to identify common structures or issues
   - Generate structured reports from findings

4. **Claude Code Integration (When Available)**
   - If Claude Code CLI is installed:
     - Use `terminal(command="claude -p 'Analyze this configuration file' --allowedTools 'Read' < file.txt")` for deep file analysis
     - Leverage print mode for non-interactive analysis
     - Use structured JSON output for programmatic processing

5. **Repository Structure Investigation**
   - Apply repository-structure-investigation skill techniques
   - Check for integrated components vs. standalone repositories
   - Verify repository origins with `git remote -v`
   - Look for skill directories that might contain drivers

6. **Process Investigation**
   - Apply process-investigation skill techniques
   - Find running processes with `ps aux | grep process_name`
   - Check port usage with `lsof -i :port`
   - Verify process origins and repository locations

7. **Documentation and Reporting**
   - Create structured analysis reports using markdown templates
   - Document findings with specific file paths and line numbers
   - Include diagnostic output and analysis results
   - Save reports to version control for future reference

## Pitfalls
- Assuming all repositories are standalone when they may be integrated components
- Not checking for local modifications to files that may not be committed
- Missing tools like `lsof` or `netstat` that are needed for process investigation
- Not documenting findings in a structured, reproducible way
- Overlooking environment variables that may affect behavior
- Failing to verify repository origins when investigating processes
- Not using systematic debugging approaches when issues are complex
- Ignoring git status that may show local changes not yet pushed

## Verification
Run `find /opt/data -name "*analysis*" -type f` to verify analysis files are properly located, and `python3 -c "import json; print('Python analysis tools available')"` to verify Python environment is ready for analysis scripts.
