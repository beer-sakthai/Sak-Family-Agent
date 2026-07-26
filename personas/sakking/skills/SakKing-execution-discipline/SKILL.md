---
name: SakKing-execution-discipline
version: 1.4.0
description: >
  Class-level execution discipline for bounded, evidence-first action.
  Apply whenever the next step is uncertain, a fix is unconfirmed, or the
  user explicitly asks the agent to stop guessing. Governs the boundary
  between reasoning and execution: if no clear cure is supported by real
  evidence, the agent must state that, summarize what is known, and offer
  the next verification step instead of acting.
triggers:
  - insufficient evidence
  - unclear failure cause
  - stop vs act decision
  - speculative execution
  - no clear cure
  - user says don't guess
  - unresolved tooling mismatch
  - avoid guessing
---

# Execution Discipline

This skill enforces the execution boundary between **reasoning** and
**acting**. It exists because guessing is not free: it consumes turns,
pollutes context, and can produce misleading “fixes” that harden into
false constraints.

## Principle

**If no clear cure is supported by real evidence, say so and stop.**
Action is only justified when at least one actionable hypothesis is
grounded in authoritative evidence.

## When this applies

- A tool/network/environment failure has no clear cause from the
  current diagnostic data.
- Known facts are conflicting or incomplete.
- A proposed fix relies on analogy or pattern-matching rather than
  explicitly authoritative sources (docs, reproducible artifacts,
  direct inspection).
- The user explicitly asks the agent to stop guessing.
- A workspace has known unresolved mismatches (for example,
  `pip` pointing to a different Python than the editor/lint chain).

## Required behavior

1. **State the boundary.**
   Say plainly whether the current evidence is sufficient to act.
2. **Summarize knowns and missing pieces.**
   One or two bullets each. Keep it tight.
3. **Propose a single verification step.**
   The smallest action that would resolve the ambiguity, if the user
   wants it.
4. **Do not execute speculative commands.**
   Especially avoid retry loops, blind `pip install` attempts, or
   publishing proposed fixes with unverified causes.
5. **Verify display-layer evidence with byte-level probe before
   every content-modifying action.**
   If a patch, write, sed, or any content modification is motivated
   by a perceived issue detected through `read_file`, `grep`,
   `cat`, or `search_files`, the evidence is **insufficient**
   until confirmed by a byte-level probe. The display layer can
   transform placeholder tokens (`<token>`→`***`, `$GITHUB_TOKEN`→`***`),
   hide backticks (consumed as markdown formatting), or redact
   content for security — all of which create false positives.

   **Required pre-patch verification:**
   ```bash
   od -A x -t x1z <file> | grep <expected-hex-pattern>
   # OR for a specific line:
   sed -n '<LINE>p' <file> | od -A x -t x1z
   ```
   A reusable script `scripts/verify-file-bytes.py` automates this check
   — see it for examples and full usage.

   When the file is under version control, compare against the
   committed object to detect display-layer redaction:
   ```python
   import subprocess
   old = subprocess.run(['git','show','HEAD:<path>'], capture_output=True).stdout
   with open('<path>','rb') as f: new = f.read()
   # compare old and new byte-by-byte
   ```

   Do not skip this step even when the issue looks "obvious" —
   the confirmation-bias trap is strongest when you already
   believe you see the problem (see `references/execution-patterns.md`
   for the full 2026-07-26 session case).

## Expected output shape

> What failed / why it is unclear / what is missing / one concrete
> next check if the user wants to continue.

## Pitfalls

- “Let’s just try X” without a hypothesis tied to evidence.
- Re-running the same probe hoping for a different result.
- Publishing a fix plan that names causes you cannot confirm.
- Continuing to act after stating you do not know.
- Acting on an environment state you have not verified in this session.
- **Trusting display-layer tools (read_file, grep) as byte-level evidence.** When the question is "does this file contain the exact characters I expect," read_file's LINE_NUM| prefix formatting and markdown rendering can obscure backticks, pipes, and whitespace. `read_file` showing a clean file does not prove the file is clean — use byte-level probes for verification. **Do NOT trust `repr()` or `cat -A` either** — the conversation display layer can transform terminal output, replacing placeholders like `***` with `***`. The only fully reliable verification is comparing raw hex or bytes against a known-authoritative source (e.g., git object for the committed version). Acting on display-layer output alone is acting on insufficient evidence.

  **`read_file` doubles backslash characters in its display output.** A line containing `$'\n\r'` (bash ANSI-C quoting for newline+carriage return, single backslash before each letter) displays as `$'\\n\\r'` (double backslash). This is a separate display-layer transformation from token redaction — backslashes are escaped for safe markdown rendering. If you use the displayed double-backslash text as `old_string` in `patch`, the match will fail because the file has a single backslash while your pattern has a double one. Always verify backslash-heavy lines with `od -A x -t x1z`: `5c 6e` = one backslash + 'n' (correct for ANSI-C quoting), `5c 5c 6e` = two backslashes + 'n' (display artifact). Confirmed in the 2026-07-26 skill audit session: `read_file` showed `$'\\n\\r'` for a line whose actual bytes were `5c 6e 5c 72` (one backslash each).

  **Which byte-level probe to use:**

  - **`od -c`** — fast, no Python dependency, shows each byte as a printable character or escape. Good for most checks. Limitation: it escapes backslash bytes as `\\`, making `\n` (one backslash + n) vs `\\n` (two backslashes + n) hard to distinguish since both appear as backslash-escape sequences in the output.

  - **`od -A x -t x1z`** — hex dump format. Each byte is two hex digits. `\n` = `5c 6e`, `\\n` = `5c 5c 6e`. Unambiguous even for backslash-heavy content (bash `$'\n\r'` ANSI-C quoting, sed `\(` groups, Python regex `\s`). Prefer this when the content contains backslash sequences.

  - **`git show HEAD:` + Python comparison** — the only fully authoritative source. Compare raw bytes of the current file against the committed version when you need to confirm a patch landed or detect display-layer redaction.

  **Real case (2026-07-26):** A `patch` call that should have written `$'\n\r'` (bash ANSI-C quoting for newline + carriage return) instead wrote `$'\\n\\r'` (literal backslash-n-backslash-r). `read_file` showed both versions identically. `od -c` showed `\ n \ r` vs `\ \ n \ \ r` — a one-space difference easy to miss. Only the hex dump (`5c 6e` vs `5c 5c 6e`) made the double-backslash unambiguous. See `references/execution-patterns.md` for the full verification workflow.

## Relation to reasoning and debugging skills

This skill is the execution boundary for reasoning frameworks such as
structured reasoning skills and debugging workflows like
`systematic-debugging`. Those skills define how to analyze; this skill
defines when not to act.

## Session evidence

For real cases and pattern examples, see `references/execution-patterns.md`.
