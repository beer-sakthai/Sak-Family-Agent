# Sak Family auto-cycle — guardrail parity review

**Mode: TEST (dry run).** All six personas were dispatched with `--dry-run` and
their own throwaway `SAKTHAI_HOME=$(mktemp -d)`. **No persona memory was
written, no model tokens were spent, and no cycle rounds were executed.** Your
request — "kick off the family cycle to review the guardrail parity issue" — is
not the explicit live-run authorization the skill requires, so the safe default
applied. Read the table below as *config validated*, not as completed work.

Dispatch was **one message containing six concurrent Agent calls**, not a
serial chain.

## Results

| Persona | Rounds | Outcome | Status |
|---|---|---|---|
| SakThai | 0 (dry-run) | config validated · `huggingface` / `gemini-3.1-flash-lite` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no credentials | success |
| SakKing | 0 (dry-run) | config validated · `huggingface` / `Qwen/Qwen3-Coder-30B-A3B-Instruct` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no credentials | success |
| SakSee | 0 (dry-run) | config validated · `huggingface` / `gemini-3.1-flash-lite` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no credentials | success |
| SakSit | 0 (dry-run) | config validated · `huggingface` / `DeepSeek-V4-Flash` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no credentials | success |
| SakJules | 0 (dry-run) | config validated · `huggingface` / `gemini-2.5-flash-lite` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no credentials | success |
| SakTan | 0 (dry-run) | config validated · `ollama` / `sakthai` · `1 resolved (Sak-auto-cycle-loop)` · not runnable: no reachable Ollama endpoint at `127.0.0.1:11434` | success (with note) |

Every dispatch printed the line that proves skill injection worked:

```
[dry-run] skills:      1 resolved (Sak-auto-cycle-loop)
```

`Not runnable: no credentials` alongside that line is the **expected, healthy**
dry-run result on a machine with no provider keys — this box has none set
(`ANTHROPIC_API_KEY`, `HF_TOKEN`, `GEMINI_API_KEY`, `OPENAI_API_KEY` all unset,
no `.env`, no `ollama` binary). Six for six resolved their own persona config,
their own model and provider, and their own skill overlay, which is what the
dry run exists to confirm.

## What the review found about the parity issue itself

This came from pre-dispatch reconnaissance in the repo, and is real regardless
of the dry-run mode:

**The parity test is currently green — and that is the misleading part.** All
six `personas/<name>/sakthai/agent/guardrails.py` copies are byte-identical
(md5 `0f08fd1d…`, 1434 lines). There is no live drift to fix. The issue is the
*mechanism*, and it has three gaps:

1. **The test checks five personas, not six.**
   `tests/test_persona_guardrails_parity.py` hard-codes
   `PERSONAS = ["sakthai", "sakjules", "sakking", "saksee", "saksit"]`.
   **`saktan` is absent.** Drift in SakTan's guardrails copy is invisible to CI
   today. The test's own docstring says "each persona under `personas/`", and
   its failure message says "all six personas" — the code does five.

2. **It checks one file.** Only `agent/guardrails.py` is compared. The
   redaction sets in `config.py`, plus `guardrails_hardened.py` and
   `security_hardening.py`, are copied per persona with no parity guard — and
   `web/server.py`, which carries the bearer-token enforcement and the
   loopback-bind refusal, is one of the shadowing files in SakKing's, SakSee's
   and SakSit's partial real directories, also unguarded.

3. **The enforcement path is itself suspect.** The documented finding that
   `ci.yml`'s test step reports `conclusion: success` even when pytest prints a
   failure line and exits 1 locally means a parity failure's ability to block a
   PR should be verified, not assumed.

Supporting context: `personas/sakthai/sakthai/` and `personas/shared/sakthai/`
have genuinely diverged across roughly a dozen files (`config.py`, `auth.py`,
`skills.py`, `agent/chat.py`, `agent/loop.py`, `agent/tools.py`, `cli/*`,
`web/server.py`, and several subpackages present in only one copy). Copy-based
synchronization guarded by a single-file test is the shape of the problem.

## Recommended next steps

1. Add `saktan` to `PERSONAS` in `tests/test_persona_guardrails_parity.py` —
   the smallest change that closes the largest hole.
2. Widen the compared file set to `config.py`, `agent/guardrails_hardened.py`,
   `agent/security_hardening.py` and `web/server.py`, over whichever personas
   actually carry a real copy of each.
3. Confirm that a parity failure genuinely fails the `ci.yml` job, given the
   known success-reporting weakness.
4. Decide the longer-term shape: keep copy-plus-parity-test, or move to one
   source of truth with generated persona copies. This is the decision SakThai
   was dispatched to make and could not, because the run was a dry run.

## To actually run this

Say so explicitly — e.g. *"do a live run of the family cycle on the guardrail
parity issue"* — and I will re-dispatch the same six tasks with `SAKTHAI_HOME`
and `--dry-run` removed, writing to each persona's real shard at
`~/.sakthai/<persona>/memory.db`. Note that a live run needs provider
credentials, which are not present on this machine: five personas need
`HF_TOKEN` and SakTan needs a reachable Ollama at `127.0.0.1:11434`.
