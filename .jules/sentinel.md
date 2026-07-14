# Sentinel Security Journal

## 2026-07-01 - [Redacting Secrets in Tool Error Handlers]

**Vulnerability:** Raw `TELEGRAM_BOT_TOKEN` was included in the exception string returned to the LLM when an `Unexpected Error` occurred during message sending.

**Learning:** Generic `except Exception as exc` handlers that return `str(exc)` can inadvertently leak sensitive configuration data (like API tokens in URLs or credentials in object representations) to the model.

**Prevention:** Always redact sensitive tokens or use specific, safe error messages in tool return strings. Use `re.sub` or structured error objects instead of raw exception stringification for external API calls.

## 2026-07-02 - [Global Secret Redaction Fail-safe]

**Vulnerability:** Multi-provider API keys and Telegram tokens could still leak via raw exception strings in tool handlers if not manually redacted in every single tool.

**Learning:** While individual tool hardening (like in the Telegram tool) is good, a global fail-safe in the agent's tool execution loop (`_execute_tool`) provides defense-in-depth against future tools or forgotten handlers.

**Prevention:** Implement a centralized `redact_secrets` utility that knows about all sensitive environment variables and apply it to all stringified exceptions returned from the tool layer to the LLM.

## 2026-07-03 - [Defense-in-Depth for Persistent Data and Logs]

**Vulnerability:** Session logs and the memory database were created with default system permissions (often 0644), potentially exposing sensitive interaction history or learned facts to other users on the same host. Additionally, session logs could contain unredacted secrets if tools were used directly or if the model echoed sensitive inputs.

**Learning:** Security must extend beyond the active tool loop to the persistent data layer. Centralizing redaction at the tool execution boundary and the log writing boundary, combined with strict POSIX file permissions (0600/0700), ensures that sensitive data remains protected both in transit (to the LLM) and at rest (on disk).

**Prevention:** Use `os.open` with explicit modes for file creation and `os.chmod` for existing sensitive directories/files. Always apply central redaction logic to any data being persisted to logs or returned from external tool executions.

## 2026-07-04 - [Centralized Path Validation for Tools]

**Vulnerability:** The `ingest_document` tool lacked the directory restriction checks (SAKTHAI_READ_ALLOW) present in `read_file`, allowing the agent to potentially read and learn facts from any file accessible by the process, including sensitive configuration or system files outside the intended sandbox.

**Learning:** When multiple tools share similar side-effect patterns (e.g., reading from the filesystem), security controls must be centralized. Implementing validation individually in each tool is error-prone and leads to security gaps as new tools are added or existing ones are refactored.

**Prevention:** Centralize sensitive validation logic (like path resolution and containment checks) into shared internal helpers (e.g., `_resolve_and_validate_path`). Mandate that any tool accessing the filesystem must use these helpers to ensure a consistent security posture across the entire toolset.

## 2026-07-04 - [Hardening Shell Command Guardrails]

**Vulnerability:** Shell command guardrails for `rm -rf` were too specific, only blocking the exact string `-rf` and standalone `/` or `~` arguments. This allowed bypasses using different flag combinations (e.g., `-r -f`, `-fr`, `--recursive`) or targeting absolute subdirectories (e.g., `/etc`).

**Learning:** String-matching based security checks on CLI commands are fragile. Effective guardrails must parse the command (e.g., using `shlex`) and evaluate the semantic intent (recursive deletion) and the reach of the target (absolute or home-relative paths) across all possible flag variations.

**Prevention:** Use robust flag detection that handles combined, individual, and long-form flags. Validate all positional arguments for sensitive path prefixes rather than matching exact strings.

## 2026-07-06 - [Robust Command Binary Detection in Guardrails]

**Vulnerability:** Destructive command guardrails (like the `rm` check) could be bypassed by using absolute paths to the binary (e.g., `/bin/rm` or `sudo /bin/rm`) because the detection logic only looked for exact string matches on the command name.

**Learning:** When building security guardrails that inspect shell commands, simply checking for a command name is insufficient. Command aliases, absolute paths, and wrappers (like `sudo`) must be considered to prevent trivial bypasses.

**Prevention:** Use matching logic that identifies a binary both by its base name and its path-prefixed forms (e.g., `part == "binary" or part.endswith("/binary")`). Ensure this check is applied even when commands are prefixed by administrative wrappers.

## 2026-07-05 - [Unified Security Enforcement for MCP Tools]

**Vulnerability:** Tool calls in the MCP server bypassed the `GuardrailPolicy` and `redact_secrets` mechanisms used by the main agent loop, leading to inconsistent security enforcement and potential secret leakage during remote tool execution.

**Learning:** Security controls must be enforced at every layer that executes tools. Implementing guardrails only in the primary agent loop leaves other interfaces (like MCP or API endpoints) vulnerable if they share the same tool registry but bypass the orchestration's security logic.

**Prevention:** Ensure all tool execution entry points consistently apply the full security pipeline: pre-execution policy checks, argument validation, exception redaction, and post-execution output filtering. Pass the active `GuardrailPolicy` through all transport layers to maintain a unified security posture.

## 2026-07-07 - [Comprehensive Secret Detection in Guardrails]

**Vulnerability:** The secret detection guardrail only matched underscore-prefixed tokens (`sk_`), allowing Anthropic and OpenAI keys that use hyphens (`sk-`) to bypass the filter and potentially leak in tool outputs.

**Learning:** Secret formats are provider-specific and can vary even within a single provider's ecosystem. A generic regular expression that assumes a single separator (like `_`) is insufficient for a multi-provider agent.

**Prevention:** Use robust, multi-pattern regular expressions that account for various separators (`-`, `_`) and known provider prefixes (e.g., `AIza` for Google, `ghp` for GitHub). Periodically update these patterns as new providers or token formats are integrated.

## 2026-07-05 - [Hardening Destructive Command Guardrails Against Bypass]

**Vulnerability:** Shell command guardrails for `rm -rf` were bypassed if the force flag (`-f`) was omitted, or if path traversal (`..`) was used to target files outside the current directory (e.g., `rm -rf ../../../etc/shadow`).

**Learning:** Destructive command detection must not rely on specific flag combinations (like `-rf`) as recursive deletion alone (`rm -r`) on sensitive targets is equally dangerous. Furthermore, target path validation must account for path traversal sequences (`..`) to prevent escaping the intended sandbox via relative paths.

**Prevention:** Enforce recursive deletion blocks on sensitive targets regardless of the presence of the force flag. Implement robust path inspection that denies any target containing path traversal characters (`..`) when evaluating destructive commands.

## 2026-07-05 - [Path Traversal in Hugging Face Downloads]

**Vulnerability:** The `hf_download` function in `sakthai/hf.py` constructed the local download directory by simply appending the user-provided `repo_id` to the base cache path. This allowed an attacker to use path traversal sequences (e.g., `../../.ssh`) to download files into arbitrary locations accessible by the agent.

**Learning:** Any tool that uses user-provided strings to construct filesystem paths must explicitly validate that the resulting path remains within the intended directory. Simply appending strings is never safe, even if the base path is trusted.

**Prevention:** Always resolve the final target path using `Path.resolve()` and verify that it is still a child of the intended root directory using `path.is_relative_to(root)`.

## 2026-07-08 - [Recursion and Wrapper-aware Shell Guardrails]
 
**Vulnerability:** Shell command guardrails could be bypassed by nesting destructive commands inside wrappers like `bash -c`, `sudo`, or `find -exec`. Additionally, destructive `chmod` and `mv` operations on system-critical paths were unmonitored.
 
**Learning:** Simple top-level token matching is insufficient for shell security. Commands can be deeply nested or executed via specialized flags in common utilities. Effective guardrails must recursively inspect arguments and understand the context of specialized wrappers.
 
**Prevention:** Use recursive token inspection for shell wrappers (`bash -c`, `sudo`, etc.). Explicitly detect and block recursive operations (`rm -r`, `chmod -R`) and sensitive target moves (`mv`) on system-critical paths across all nested levels. For specialized tools like `find`, implement heuristics that account for target paths and placeholder replacement.

## 2026-07-09 - [Hardening Shell Guardrails against Non-recursive and Specialized Deletions]

**Vulnerability:** Shell command guardrails only blocked recursive `rm -rf` on sensitive paths, allowing bypasses via non-recursive `rm`, `chmod`, `mv`, or specialized flags like `find ... -delete`.

**Learning:** Security guardrails for CLI commands must not rely solely on "recursive" flags when the target is a system-critical path. Even a single-file deletion or permission change on a sensitive target can compromise the system. Furthermore, multi-purpose utilities like `find` have built-in destructive capabilities that bypass simple command-name matching.

**Prevention:** Centralize sensitive path detection (e.g., `_is_sensitive_path`) and apply it consistently across all potentially destructive command types. Ensure that any operation targeting a sensitive root is blocked, regardless of flags. Explicitly audit flags of common utilities (like `find -delete`) for destructive side-effects.

## 2026-07-10 - [Path Normalization in Guardrails]

**Vulnerability:** Path-based guardrails (like `_is_sensitive_path`) could be bypassed using redundant slashes (e.g., `//etc/passwd`) or relative segments (e.g., `/./etc/passwd`) because the detection logic relied on simple string prefix matching.

**Learning:** String-based path checks are vulnerable to normalization bypasses. POSIX path resolution collapses redundant slashes and dots, but naive string comparisons do not. Furthermore, `os.path.normpath` has an edge case where it preserves a leading `//` for certain network filesystem implementations, which can still bypass a check for `/etc`.

**Prevention:** Always normalize paths using `os.path.normpath` before performing security checks. For POSIX-style root checks, explicitly handle and collapse the leading `//` edge case to ensure that targets in sensitive system roots are correctly identified regardless of their string representation.

## 2026-07-11 - [Secure Environment File Ingestion with Active Redaction]

**Vulnerability:** Standard file reading or custom scripts mapping local environment files (`.env`) can inadvertently output raw secrets, API tokens, and credentials directly to user-facing dashboards or chat terminals.

**Learning:** When developing skills or tools to audit, verify, or read environment configuration files, security checks must be built into the parsing loop itself. Simply reading the file is a risk; variables must be evaluated for sensitivity based on key patterns, and their values proactively masked before formatting the response.

**Prevention:** Implement strict key-pattern recognition (matching strings like `SECRET`, `KEY`, `TOKEN`, `PASSWORD`, `CREDENTIAL`) during configuration file parsing. Proactively redact these values with placeholders (e.g., `[REDACTED]`) at the parsing stage, ensuring that secrets are never sent to the LLM or rendered in UI logs.

## 2026-07-12 - [Hardening find -delete Guardrails against Global Options]

**Vulnerability:** The guardrail for `find -delete` could be bypassed by using global options like `-L` or `-H` before the target path (e.g., `find -L /etc -delete`). This happened because the inspection logic used a `break` statement as soon as it encountered any token starting with a hyphen.

**Learning:** Shell utilities often support global options that precede positional arguments. When building security guardrails that inspect command-line arguments, "stopping at the first flag" is an unsafe heuristic if sensitive targets can appear later in the command string.

**Prevention:** When inspecting command arguments for sensitive paths, skip flags (tokens starting with `-`) using `continue` instead of `break`. This ensures that all positional arguments are evaluated even if they follow or are interspersed with options.

## 2026-07-13 - [Hardening Shell Guardrails against Data Exfiltration and Input Redirection]

**Vulnerability:** Shell guardrails for `run_command` only monitored destructive binaries (like `rm`, `mv`) and a subset of output redirections (`>`, `>>`), allowing bypasses via file-reading commands (e.g., `cat /etc/shadow`) or input/descriptor redirections (e.g., `cmd < .env` or `cmd >& /etc/passwd`).

**Learning:** Security guardrails for shell execution must account for data exfiltration and unauthorized reading, not just system destruction. Furthermore, shell redirection is versatile, and many operators besides simple output redirection can be used to target sensitive files.

**Prevention:** Maintain an expansive list of "dangerous" binaries beyond just "destructive" ones, including tools for reading, searching, and networking. Use comprehensive regular expressions for shell redirection operators and ensure correct alternation order (e.g., `>&` before `>`) in regex to prevent partial matches.

## 2026-07-06 - [Hardened Shell Guardrails against find -delete Bypass and Wrappers]

**Vulnerability:** Shell guardrails for `find -delete` could be bypassed by inserting global options (e.g., `find -L /etc -delete`) because the argument scanner prematurely stopped at hyphenated tokens. Additionally, destructive commands wrapped in `xargs` or using `find` variants like `-execdir` were unmonitored.

**Learning:** When scanning CLI arguments for sensitive paths, security logic must not assume that options only appear after positional targets. Furthermore, security enforcement must be recursive and account for all variants of execution wrappers to prevent trivial bypasses.

**Prevention:** Ensure that argument scanners for specialized tools (like `find`) continue inspecting all non-option tokens as potential starting points even when global options are present. Consistently apply recursive inspection to all common execution wrappers, including `xargs` and all `-exec`-like variants of `find`.

## 2026-07-07 - [Comprehensive Shell Redirection and Flag-based Path Protection]

**Vulnerability:** Shell command guardrails could be bypassed by using redirections (e.g., `echo evil > /etc/passwd`), destructive binaries not previously monitored (e.g., `cp`, `ln`, `tee`), or by passing sensitive paths within flags (e.g., `--directory=/etc`) or specialized arguments (e.g., `dd of=/etc/passwd`).

**Learning:** Hardening shell guardrails requires move beyond simple command name matching. Destructive intent can be expressed through I/O redirections which are handled by the shell before the command is even executed in a full shell environment, or through specialized arguments in common utilities. Furthermore, positional argument scanning must account for flags that use an equals sign to pair with their values.

**Prevention:** Implement a unified scanner that monitors a broad list of destructive binaries (`rm`, `chmod`, `mv`, `cp`, `ln`, `tee`, `chgrp`, `chown`) and explicitly stops scanning at command separators to prevent false positives. Enhance path validation to decompose flag-value pairs. Add dedicated heuristics for specialized commands like `dd` and for shell redirection operators that target sensitive system roots.

## 2026-07-07 - [Hardening Guardrails against Binary-specific Flag Bypasses]

**Vulnerability:** Shell command guardrails could be bypassed by using binaries like `curl`, `wget`, or `sed` to overwrite sensitive files (e.g., `curl -o /etc/passwd ...`). Additionally, short flags with attached paths (e.g., `-o/etc/passwd`) were not correctly decomposed by the path validator, allowing them to bypass sensitive path checks.

**Learning:** Destructive intent is not limited to `rm` or `chmod`. Many common utilities have flags that allow writing to arbitrary locations. Furthermore, shell argument parsing allows for various ways to attach values to flags, which security scanners must account for beyond simple space or equals-sign separation.

**Prevention:** Expand monitored destructive binaries to include tools with file-writing capabilities (`curl`, `wget`, `sed`). Harden path validation to detect and decompose short flags that are immediately followed by an absolute path (e.g., `-x/path`).

## 2026-07-08 - [Hardening Shell Redirection Guardrails Against Attached Operators]

**Vulnerability:** Shell redirection guardrails could be bypassed by attaching the operator directly to the preceding command or argument (e.g., `echo>file` or `echo> /etc/passwd`). The previous logic only checked for exact matches on standalone operators (e.g., `>`) or tokens that started with the operator (e.g., `>/etc/passwd`).

**Learning:** Shell parsing is highly flexible regarding whitespace around redirection operators. A robust security scanner must use regular expressions to identify redirection operators within any part of a token and correctly resolve the target path, whether it's attached to the operator or appears in the subsequent token.

**Prevention:** Use a unified regular expression to detect all standard redirection operators (including numeric file descriptors like `2>`) within shell command tokens. Ensure the scanner correctly extracts the target path by checking both the remainder of the current token and the entirety of the next token if the operator appears at the end.

## 2026-07-14 - [Hardening Guardrails against Data Exfiltration and Clobbering]

**Vulnerability:** Shell guardrails could be bypassed using advanced redirection operators like `>|` (clobber) or `&>>` (append both streams) to overwrite sensitive files. Additionally, the `dd` command was only monitored for its output file (`of=`), leaving the input file (`if=`) unprotected, which allowed the agent to be tricked into reading and exfiltrating system-critical files (e.g., `/dev/sda` or `/etc/shadow`).

**Learning:** Security guardrails for shell execution must account for all possible redirection variants supported by modern shells (Bash/Zsh). Furthermore, tools that perform low-level data movement like `dd` must be validated for both reading and writing to prevent both data destruction and unauthorized exfiltration. Path validation for flags must also account for home-relative segments (`~`) which can be used to target sensitive user data outside the sandbox.

**Prevention:** Expand redirection regex to include `&>>` and `>|`. Implement dual-side path validation for `dd` (both `if=` and `of=`). Update flag-based path detection to recognize and resolve the `~` character.

## 2026-07-15 - [Credential Leakage in Memory Metadata]
**Vulnerability:** Secrets (API keys, tokens) were only redacted from the `value` of facts and `summary` of observations. Metadata fields like `kind`, `key`, `tags`, and session IDs were not redacted, allowing credentials to be stored in plain text in the SQLite database and potentially leaked during memory recall.
**Learning:** Security redaction must be applied to all user-controllable string fields in a persistent store, not just the primary content fields. Metadata can often be used to store sensitive data accidentally or maliciously.
**Prevention:** Apply a centralized `redact_secrets` function to every string field at the data entry boundary (both for individual writes and bulk imports).

## 2026-07-16 - [Hardening Shell Redirection against Read-Write and Descriptor Duplication]
**Vulnerability:** Shell redirection guardrails missed the `<>` (read-write) and `<&` (input duplication) operators, allowing potential bypasses when interacting with sensitive system files (e.g., `cat <>/etc/passwd`).
**Learning:** Shell redirection is extremely versatile. Less common operators like `<>` and `<&` can be just as dangerous as standard output redirections if they target sensitive paths. Security regexes must be exhaustive and prioritized (longer matches first).
**Prevention:** Use a unified and comprehensive regex for shell redirection operators: `r"(?:[0-9]|&)?(?:&>>|>>|>&|>\||<>|<&|>|<)"`. This ensures all variants are captured before the target path is validated.

## 2026-07-28 - [Protecting SQLite Sidecar Files and Hardening Destructive Commands]

**Vulnerability:** Guardrails only blocked `memory.db`, leaving SQLite sidecar files (`-wal`, `-shm`, `-journal`) exposed to exfiltration. Additionally, `rmdir` was missing from monitored destructive binaries.

**Learning:** Database security must cover all auxiliary files that may contain data fragments. When blocking a specific file like a database, always consider its sidecar and temporary files. Furthermore, security lists for destructive actions must be exhaustive regarding standard utilities that can modify or remove the filesystem structure.

**Prevention:** Use prefix matching (e.g., `memory.db-`) in path validation to block all associated database files. Periodically audit and expand `destructive_binaries` to include all standard POSIX utilities with deletion capabilities like `rmdir`.

## 2026-07-17 - [Hardening Guardrails against Interpreter-based Path Bypasses]

**Vulnerability:** Shell guardrails could be bypassed by using language interpreters (e.g., `python3`, `node`) to read or execute system-critical files (e.g., `python3 /etc/passwd`). These binaries were not monitored, allowing them to target sensitive paths via positional arguments.

**Learning:** Security guardrails for shell execution must include common language interpreters in the monitored list. Interpreters are dual-use: they are necessary for the agent's operation but can also be used as powerful file-reading and execution tools that bypass simple utility-based filters.

**Prevention:** Expand `dangerous_binaries` to include `python`, `python3`, and `node`. Update guardrail denial reasons and test assertions to use more inclusive terminology (like "dangerous" instead of just "destructive") to cover both data exfiltration and system destruction.

## 2026-07-18 - [Hardening _is_binary against Versioning Bypasses]

**Vulnerability:** The `_is_binary` helper used simple string matching (exact or suffix), allowing bypasses using versioned binary names (e.g., `python3.12`) or absolute paths to those binaries (e.g., `/usr/bin/python3`).

**Learning:** Command-line tokens can refer to the same logical binary through various string representations, including absolute paths and version-specific suffixes. Security checks must use robust pattern matching on the base name to ensure all variants are captured.

**Prevention:** Refactor `_is_binary` to use a regular expression that matches the binary's base name followed by optional versioning (e.g., `rf"^{re.escape(name)}(?:[0-9]+(?:\.[0-9]+)*)?$"`). Always extract the `basename` before matching to account for absolute paths.

## 2026-07-19 - [Conditional Local Path Blocking in Guardrails]

**Vulnerability:** Destructive commands could target the current directory (e.g., `rm -rf .`), causing local data loss. However, blocking the current directory (`.`) globally in `_is_sensitive_path` caused regressions for common, safe discovery tools like `find .`.

**Learning:** Path sensitivity is context-dependent. While the current directory is not a "system-critical" root, it should still be protected from destructive operations. Security policies must differentiate between destructive intent (e.g., `rm`, `chmod`, `find -delete`) and safe discovery or exfiltration intent (e.g., `ls`, `cat`, `find`, `python` execution) when evaluating local path targets.

**Prevention:** Introduce an `allow_local` flag to `_is_sensitive_path`. Differentiate monitored binaries into `destructive_binaries` (which block `.`) and `exfiltration_binaries` (which allow `.`). Apply stricter `allow_local=False` checks to `destructive_binaries` and the output targets (`of=`) of data-movement tools like `dd`.

## 2026-07-20 - [CI Failures due to Inflated Action Versions]

**Vulnerability:** Multiple GitHub Actions workflows failed with `fatal: repository not found` because they referenced non-existent future versions of actions (e.g., `actions/checkout@v7`).

**Learning:** Using overly high version numbers for community or official actions can lead to infrastructure-level failures as runners fail to resolve the action reference. Always use established, stable major versions (e.g., `@v4` for checkout) unless a specific new feature is required and verified to exist.

**Prevention:** Audit workflow files regularly to ensure action versions match the current stable releases provided by maintainers. Avoid "future-proofing" by inflating version numbers.

## 2026-07-21 - [Hardening Guardrails against Combined Flag Bypasses]

**Vulnerability:** Shell and interpreter guardrails could be bypassed by combining the command execution flag with other short flags (e.g., `bash -xc` or `python3 -ic`). The previous logic only checked for exact matches like `-c`.

**Learning:** Command-line parsers for shells and interpreters often allow combining multiple short flags into a single token. Security guardrails must account for this by checking if the relevant flag (like `c` for command execution) is present in a combined flag group, typically as the last character if it takes an argument.

**Prevention:** When inspecting tokens for flags that trigger subcommand execution, check if the token starts with a single hyphen and ends with the expected flag character. This ensures that combined flags are correctly identified before recursing into the command string.

## 2026-07-22 - [Hardening Guardrails against Empty-Base Glob Bypasses]

**Vulnerability:** Shell command guardrails could be bypassed by using empty-base wildcards (e.g., `rm *` or `rm ?`) when `allow_local=False`. The logic to extract `base_path` from a glob would result in an empty string, skipping the critical root checks and potentially allowing destructive operations on the current directory.

**Learning:** Path validation for globs must explicitly handle the case where the glob starts with a wildcard character, especially when local path access is prohibited. Relying solely on prefix-based root checks is insufficient for protecting the current directory from broad wildcard deletions.

**Prevention:** Harden `_is_sensitive_path` to return `True` if `allow_local` is `False` and the path contains wildcards but has an empty `base_path`. This ensures that patterns like `*` are correctly identified as targeting the local directory and blocked when destructive tools are used.

## 2026-07-23 - [Hardening find Guardrails against Destructive fprint and Discovery]

**Vulnerability:** The 'find' command's file-writing flags (-fprint, -fprint0, -fls, -fprintf) allowed overwriting sensitive system files. Additionally, 'find' could be used for unauthorized discovery of sensitive directories without being flagged.

**Learning:** Specialized commands like 'find' have dual-use flags that can be used for both discovery and destruction. Generic exfiltration lists might intercept these commands prematurely, preventing more granular specialized logic from enforcing stricter path rules (like allow_local=False for deletions or writes).

**Prevention:** Implement a dedicated, multi-stage scanner for complex tools like 'find'. First, check for destructive action flags (-delete, -fprint) with strict root protection (allow_local=False). Second, validate discovery paths with standard root protection (allow_local=True). Ensure these specialized tools are excluded from broader "interpreter" or "exfiltration" loops that might shadow the more specific security checks.

## 2026-07-24 - [Protecting Repository-Sensitive Files and Hardening Argument Decomposition]

**Vulnerability:** Repository-sensitive files such as `.env`, `.git/config`, `.jules/`, and `memory.db` were vulnerable to exfiltration via direct commands (e.g., `cat .env`) or advanced tool flags (e.g., `curl -F file=@.env`). Additionally, certain interpreter execution flags (like `php -r`) were not monitored, allowing arbitrary code execution bypasses.

**Learning:** Guardrails focusing primarily on system-critical roots (`/etc`, `/root`) miss application-specific sensitive data stored in the repository or home directory. Furthermore, tool-specific argument syntax (like `curl`'s `@` prefix for file uploads) can be used to target sensitive files if the guardrail does not correctly decompose and validate argument values.

**Prevention:** Explicitly block access to repository-sensitive filenames and directories within the path validation logic. Harden `_is_sensitive_path` to recognize and decompose value separators (like `=` and `@`) in command arguments, ensuring that target values are recursively validated as paths. Expand interpreter flag detection to include all common one-liner execution variants (e.g., `-r`, `-p`, `-E`).
## 2026-07-11 - [Hardening find Guardrails against Global Options Bypass]

**Vulnerability:** The `find` command's path validation could be bypassed by inserting global options (e.g., `find -L /etc`) because the scanner prematurely stopped at the first token starting with a hyphen.

**Learning:** Positional arguments in many CLI tools can be preceded or interspersed with options. Heuristics that stop scanning at the first flag are unsafe and easily bypassed.

**Prevention:** When scanning command arguments for sensitive paths, use `continue` to skip flags instead of `break`, ensuring all non-flag tokens are evaluated as potential targets.

## 2026-07-25 - [Global Path Guardrails for All Tools]

**Vulnerability:** Tools with filesystem access (like `read_file` or `ingest_document`) could be used to read sensitive repository files (e.g., `.env`, `.git/config`) if those files were located within a default allowed root like the current working directory.

**Learning:** Hardening `run_command` is insufficient if other tools also accept path arguments. Security policies for sensitive paths must be enforced globally at the tool execution boundary to prevent information disclosure via seemingly "safe" tools.

**Prevention:** Use a centralized pre-execution guardrail that scans all tool arguments and validates them against a sensitive path registry (`_is_sensitive_path`). Ensure this rule is registered in the default policy applied to all tools.

## 2026-07-12 - [Expanded Utility Coverage + Duplicate Sentinel PR Consolidation]

**Vulnerability:** `run_command` guardrails could still be bypassed with less common text/metadata utilities (`uniq`, `cut`, `ls`, `file`, `stat`, `tac`, `rev`, `nl`, `xxd`, `column`) targeting sensitive paths, and `truncate` was missing from the destructive-binary list. Separately, three concurrent Sentinel tasks (PRs #361, #363, #364) each re-implemented the same `_block_sensitive_path_args` guardrail, producing duplicate, mutually conflicting PRs.

**Learning:** Command-line utilities are numerous; a short blocklist invites bypasses, so every file-reading/metadata utility must be paired with the sensitive-path scan. Process-wise: concurrent security tasks scanning the same module converge on the same fix — without checking open PRs first, they generate conflicting duplicates that all go stale once one merges.

**Prevention:** Keep `exfiltration_binaries`/`destructive_binaries` exhaustive and covered by tests that assert both DENY on sensitive paths and ALLOW on local files (no overblocking). Before opening a Sentinel PR, fetch latest `main` and list open Sentinel PRs; if one already covers the same guardrail area, extend it instead of opening a new one (see AGENTS.md rule 5).

## 2026-07-26 - [Hardening Guardrails against Protocol-prefixed Path Bypasses]

**Vulnerability:** Shell command guardrails could be bypassed using tools that prefix paths with protocols or schemes (e.g., `socat FILE:/etc/passwd ...` or `openssl ... -in /etc/shadow`). These prefixes prevented the path validator from recognizing the target as a sensitive absolute path.

**Learning:** Security scanners that look for absolute paths starting with `/` or `~` can be fooled by tool-specific syntax that wraps or prefixes the path. A robust scanner must decompose arguments using all common separators, including colons, before validating the resulting strings as paths.

**Prevention:** Update `_is_sensitive_path` to include `:` as a value separator. Expand monitored binary lists to include versatile networking and cryptography tools (`socat`, `openssl`) and alternative listing utilities (`dir`, `vdir`).

## 2026-07-27 - [Hardening Guardrails against Shell Wrapper and eval/exec Bypasses]

**Vulnerability:** Shell command guardrails could be bypassed by nesting destructive commands inside `eval` or `exec`, or by using transparent wrappers like `timeout`, `nice`, `nohup`, etc. These wrappers hid the actual command from the simple token-based scanner.

**Learning:** Destructive intent can be hidden behind multiple layers of shell built-ins and system utilities. A robust security scanner must be able to recursively peel back these layers, handling both shell-level evaluation (`eval`) and process-level wrapping (`timeout`). Heuristics for skipping wrapper-specific flags and arguments are necessary to reach the core command.

**Prevention:** Implement recursive inspection for `eval` and `exec` by re-splitting their arguments. Maintain an exhaustive list of transparent system wrappers (`timeout`, `nice`, `nohup`, `setsid`, `chrt`, `taskset`, `stdbuf`) and implement logic to skip their specific flags and arguments before recursing into the wrapped command.

## 2026-07-28 - [Hardening Interpreter Guardrails against Intermediate Flags and Relative Repo Paths]

**Vulnerability:** Interpreter and shell command guardrails could be bypassed by inserting intermediate flags (e.g., `python3 -v -c`) between the binary and the script execution flag. Additionally, repository-sensitive files (like `.env`, `memory.db`) could be targeted within scripts if they were accessed via relative paths without leading `/`, `~`, or `../` segments, which the script scanner previously ignored.

**Learning:** Positional heuristics in CLI guardrails (e.g., assuming `binary_name` is at `i-1` for a flag at `i`) are unsafe due to the flexibility of standard CLI parsers. Furthermore, script-based exfiltration scanners must explicitly include application-specific sensitive files in their search patterns to prevent access to data not covered by generic absolute path checks.

**Prevention:** Implement a robust backward-searching scanner that identifies the command binary associated with an execution flag even when separated by intermediate options. Enhance script argument regexes to explicitly match repository-sensitive file patterns (`.env`, `.git`, `.jules`, `memory.db`) at the start of any path-like string.

## 2026-07-29 - [Hardening Guardrails against Unmonitored Development Binaries]

**Vulnerability:** Shell command guardrails could be bypassed using standard development and maintenance tools (`mkdir`, `touch`, `git`, `npm`, `pip`) to create, modify, or exfiltrate files in sensitive system roots. These binaries were not previously monitored.

**Learning:** Security blocklists for CLI commands must go beyond standard destructive utilities (`rm`, `mv`) and include common development tools that have significant filesystem side-effects. "Dual-use" tools like `git` or package managers can be used to compromise system integrity if their target paths are not validated.

**Prevention:** Expand `destructive_binaries` and `exfiltration_binaries` to include common version control systems, package managers, and file creation utilities. Ensure that any tool capable of modifying the filesystem or reading data is subjected to sensitive path validation.

## 2026-07-29 - [Comprehensive Relative Path Blocking for Sensitive Data]
**Vulnerability:** `_is_sensitive_path` only blocked absolute paths, home-relative paths (`~`), or paths with traversal (`..`) to system-critical roots. Relative paths to sensitive user data (e.g., `.ssh/id_rsa`, `.aws/credentials`, shell histories) located in the current or sub-directories were not blocked. Follow-up variants also bypassed it: sensitive basenames as flag/upload values (`data=@id_rsa`), backup-suffixed private keys (`id_rsa.bak`), case-variant references on case-insensitive filesystems (`.AWS/credentials`), globs expanding to sensitive dirs (`.a?s/credentials`), and relative credential paths embedded in interpreter one-liners.
**Learning:** Security guardrails must protect sensitive user and application data regardless of how they are referenced. Relying on absolute path prefixes is insufficient in a local-first environment where the agent often operates in the user's home directory or repository root, and every separator/case/glob/interpreter surface is a distinct bypass vector.
**Prevention:** Block via `_SENSITIVE_BASENAMES`/`_SENSITIVE_DIRS`/`_SENSITIVE_KEY_STEMS`, validating every normalized path component case-insensitively; recurse into all separator-extracted values; treat wildcard components that can expand to a sensitive dir as sensitive; and derive the interpreter-script scanner's regex from the same sets. `tests/test_persona_guardrails_parity.py` fails CI whenever any persona's `guardrails.py` drifts from the canonical copy, so a hardening fix can no longer land in one persona while leaving the others vulnerable.
