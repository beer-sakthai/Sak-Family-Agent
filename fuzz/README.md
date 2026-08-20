# Fuzz harnesses

Coverage-guided fuzzing over the parsing boundaries that take attacker-shaped
input: git URLs handed to a `git` subprocess, guardrail decisions about tool
calls, and the JSON-RPC requests the MCP stdio server reads from another
process's stdout.

Each harness asserts a *security* invariant, not just "does not crash" — a
guardrail that raises on a malformed path is a bug, but a guardrail that
returns `ALLOW` for a path it should refuse is the bug worth fuzzing for.

## Running

Atheris is not a project dependency: it needs a matching clang toolchain and is
not installed by `uv sync --all-extras`. Install it into the fuzzing
environment explicitly:

```bash
uv sync --all-extras --group fuzz     # or: pip install atheris
python fuzz/fuzz_giturl.py            # runs until it finds something, Ctrl-C to stop
python fuzz/fuzz_guardrails.py -runs=100000
python fuzz/fuzz_mcp_server.py -atheris_runs=100000
```

Anything after the script name is passed through to libFuzzer, so `-runs=N`,
`-max_total_time=N`, `-dict=…` and a corpus directory argument all work.

## Running the invariants without Atheris

Every harness keeps its invariant in a plain `exercise(data: bytes)` function
that imports nothing from Atheris. `tests/test_fuzz_harnesses.py` calls those
directly over a seed corpus, so the harness bodies are checked by the normal
`pytest` run and cannot rot silently between fuzzing campaigns. That is the
reason for the `try: import atheris` guard at the top of each file — the module
must import cleanly whether or not Atheris is present.

## Adding a harness

1. `import atheris` at the top, guarded, exactly as the existing files do.
2. Put the invariant in `exercise(data: bytes) -> None`, taking raw bytes and
   decoding them itself, so it behaves identically with and without Atheris.
3. Add the module and a few seed inputs to `tests/test_fuzz_harnesses.py`.

Keep the `import atheris` line: Scorecard's Fuzzing check detects Python
fuzzing by matching that literal text against `*.py` files
(`checks/raw/fuzzing.go`), and it is what closes alert #15463.
