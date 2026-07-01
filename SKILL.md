---
name: subprocess
description: "A guide to using Python's built-in subprocess module to spawn new processes, connect to their I/O pipes, and obtain their return codes."
version: 1.0.0
author: Gemini
license: MIT
tags: [subprocess, shell, command, process, python, built-in]
category: system
---

# Running External Commands with `subprocess`

## Overview

Guidelines for using Python's built-in `subprocess` module to run external commands. The modern and recommended approach is to use the `subprocess.run()` function.

## Sandbox runtime — read first

Your shell runs in a **Modal sandbox** (`nikolaik/python-nodejs:python3.11-nodejs20`). This environment has Python 3.11.

- **Security**: Running external commands can be dangerous. Always treat input from external sources with caution. The agent's built-in `run_command` tool is disabled by default and must be enabled with `SAKTHAI_SHELL_ALLOW=1` for this reason. When using `subprocess` directly, you are responsible for security.
- **Ephemeral Filesystem**: Any scripts or data you create should be saved under `/tmp`.

## Installation

The `subprocess` module is part of Python's standard library. **No installation is needed.**

## Basic Usage

The `subprocess.run()` function is the recommended way to run external commands for most use cases.

### 1. Running a Simple Command

By default, `subprocess.run()` waits for the command to complete and returns a `CompletedProcess` object. For security and correctness, it is critical to pass command arguments as a list (when `shell=False`).

```python
import subprocess

# Arguments are passed as a list of strings
result = subprocess.run(['ls', '-l', '/tmp'])

print(f"Return Code: {result.returncode}")
```

### 2. Capturing Output

To capture the command's output (stdout and stderr), use `capture_output=True`. To get the output as a string instead of bytes, use `text=True`.

```python
import subprocess

result = subprocess.run(
    ['echo', 'hello from subprocess'],
    capture_output=True,
    text=True
)

print(f"STDOUT: {result.stdout.strip()}")
```

### 3. Error Handling

If the command returns a non-zero exit code (indicating an error), `subprocess.run()` will not raise an exception by default. To make it raise a `CalledProcessError`, use `check=True`.

```python
import subprocess

try:
    # This command will fail
    subprocess.run(['ls', '/nonexistent-directory'], check=True, capture_output=True)
except subprocess.CalledProcessError as e:
    print(f"Command failed with return code {e.returncode}")
    print(f"STDERR: {e.stderr}")
```

## Hello-World Example

Create `hello_subprocess.py` to list files in `/tmp`.

```python
# /tmp/hello_subprocess.py
import subprocess

try:
    # 1. Define the command and arguments as a list
    command = ['ls', '-la', '/tmp']
    print(f"Running command: {' '.join(command)}")

    # 2. Run the command, capturing output and checking for errors
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=30  # Add a timeout for safety
    )

    # 3. Print the standard output
    print("\n--- STDOUT ---")
    print(result.stdout)

except FileNotFoundError:
    print("Error: The 'ls' command was not found in the system's PATH.")
except subprocess.CalledProcessError as e:
    print(f"\nCommand failed with exit code {e.returncode}:")
    print(e.stderr)
except subprocess.TimeoutExpired:
    print("\nError: The command timed out.")
except Exception as e:
    print(f"\nAn unexpected error occurred: {e}")
```

Run with `python /tmp/hello_subprocess.py`.

## Pitfalls & Fixes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FileNotFoundError: [Errno 2] No such file or directory` | The command you are trying to run does not exist or is not in the system's `PATH`. | Verify the command is installed and spelled correctly. Use the full path to the executable if it's not in the `PATH`. |
| `subprocess.CalledProcessError` | The command returned a non-zero exit code, and you used `check=True`. | This is expected behavior for error handling. Inspect the `.returncode`, `.stdout`, and `.stderr` attributes of the exception object to debug why the command failed. |
| Command injection vulnerabilities | Using `shell=True` with untrusted input. This is a major security risk. | **Avoid `shell=True`**. Pass arguments as a list of strings. If you absolutely must use shell features, use `shlex.quote()` to escape arguments. |
| Process hangs indefinitely | The subprocess is waiting for input or is taking a very long time to complete. | Always use the `timeout` parameter in `subprocess.run()` to prevent your script from hanging. |
| `TypeError: a bytes-like object is required, not 'str'` | You are trying to provide string input to a process's stdin without `text=True`, or you are reading stdout/stderr as strings without `text=True`. | Always use `text=True` (or `encoding='utf-8'`) when you want to work with standard I/O as strings. |
