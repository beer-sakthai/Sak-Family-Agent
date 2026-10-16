---
name: Sak-family-auto-cycle
description: Dispatch all six Sak Family personas (SakKing/SakThai/SakSee/SakSit/SakTan/SakJules) as one parallel fan-out, each sustaining up to 3 Dream-through-Growth cycle rounds. Use whenever the user asks to run the family auto-cycle, run the Sak Family, get the personas working together, dispatch them as a team, or kick off a family round — even if they name only "the family" or "the cycle" without listing the personas.
---

# Sak-family-auto-cycle

Fans out one round of work to all six Sak Family personas in parallel, each
sustaining up to 3 Dream-through-Growth rounds via the `Sak-auto-cycle-loop`
skill. Requires this repo (`Sak-Family-Agent`) with `uv sync --all-extras`
already run.

Dispatch the six Agent calls at your maximum available reasoning effort —
choosing six real tasks and reconciling six independent reports is exactly the
judgment-heavy work that benefits from it.

## Default to a dry, throwaway run

Before writing a single Agent call, decide test vs. live. **The default is
test.** Every dispatch gets `--dry-run` and its own fresh
`SAKTHAI_HOME=$(mktemp -d)`.

Go live only if the user's own words say so unambiguously — "do a live run,"
"this is for real, no dry-run," "point it at the real homes." None of these
authorize a live run, however urgent they sound: "run the family auto-cycle,"
"get them working together," "just run it," "go," a deadline, or your own
inference that they obviously want something to actually happen. That last
one is the specific failure this rule exists to catch.

The reason this outranks everything else here: in 5 independent baseline runs
of this scenario without the skill, all 5 dispatching agents planned to write
straight into the real persona homes with no `--dry-run` and no throwaway
home, and not one paused to ask whether it should. A live run spends real
tokens across six parallel agents and mutates persona memory that is hard to
reverse. Getting the dispatch mechanics below right is worthless if this is
skipped.

**Test mode itself needs no permission — only going live does.** Once you've
defaulted to test, dispatch; don't stop to ask "test or live?" first. Asking
before a throwaway-home dry run isn't a stricter reading of this rule, it's a
different failure (stalling on something that was never risky). Ask before
*live*. Don't ask before *test*.

## The dispatch is one message, six subagents

Your response is **one message containing six Agent calls**, dispatched
together — not one at a time, not "SakKing first, then check, then SakThai."
Six concurrent subagents is what "the family working together" means; serializing
them is the thing this skill exists to prevent.

## The command shape

One shape covers both modes. Only two things change between them, so build
the test command first and edit those two when going live:

```bash
# TEST (default): isolated throwaway home, no tokens spent
SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<task>" \
  --persona <persona> \
  --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800 \
  --no-mcp --dry-run

# LIVE (explicit authorization only): no SAKTHAI_HOME, no --dry-run
uv run sakthai run "<task>" \
  --persona <persona> \
  --with-skills Sak-auto-cycle-loop \
  --max-iterations 40 --max-seconds 1800
```

`<persona>` is one of `sakking sakthai saksee saksit sakjules saktan`
(lowercase — `--persona` is a strict choice and rejects anything else). There
is no per-persona path table to memorize and no special case for SakKing:
every persona uses the identical command with its own name substituted.

### Why `--persona`, and why no `SAKTHAI_HOME` on a live run

`--persona` is what makes these six agents actually *different*. It loads that
persona's `SOUL.md` as a system-prompt prefix, resolves `--with-skills`
against its own skill overlay, auto-loads its `config/mcp.json`, defaults
`--model`/`--provider` from its `config/config.yaml`, and points the run at its
own memory shard. Without it you have not dispatched six personas — you have
dispatched the same default agent six times with different task strings.

So leave `--model` and `--provider` off. Each persona's config picks them
(SakTan runs on `ollama`, the rest on `huggingface` with different models);
passing `--provider anthropic` overrides all six back to being identical,
which is the problem `--persona` solves.

Memory resolves as `$SAKTHAI_HOME/<persona>/memory.db`, falling back to
`~/.sakthai/<persona>/memory.db` when `SAKTHAI_HOME` is unset. That fallback
*is* the production path — it matches what
`infra/vm-agents/sakthai-agent-run.sh` gives each deployed persona — which is
why a live run simply omits `SAKTHAI_HOME` rather than setting it.

**The trap: never set `SAKTHAI_HOME` to a persona's own home while also
passing `--persona`.** Both append the persona segment, so they compound:

```
SAKTHAI_HOME unset            --persona sakthai  ->  ~/.sakthai/sakthai/memory.db          # correct
SAKTHAI_HOME=~/.sakthai/sakthai --persona sakthai  ->  ~/.sakthai/sakthai/sakthai/memory.db  # wrong
```

The wrong one fails silently: the run looks successful while reading and
writing an empty nested shard, so the persona appears to have forgotten
everything and its work lands nowhere. In test mode `SAKTHAI_HOME=$(mktemp -d)`
is safe precisely because compounding under a temp dir is the isolation you want.

### Reading the dry-run output

A dry run prints a preflight and exits non-zero on missing credentials. The
line that proves skill injection worked is:

```
[dry-run] skills:      1 resolved (Sak-auto-cycle-loop)
```

Check for that line's **presence**. Don't rely on an error to tell you the
skill was missing — the credentials check is raised first, so with no provider
credential a misspelled skill name is reported only as "no credentials found"
and the `skills:` line silently disappears instead. `Not runnable: no
credentials` alongside a `1 resolved` line is the expected, healthy result of a
dry run on a machine with no keys; it means config validated.

`--no-mcp` is on the test command because `--persona` otherwise auto-loads that
persona's MCP servers and waits out a 30s timeout per unreachable one —
measured at 71s per dispatch versus 2s with the flag. A dry run is checking
provider, model, credentials and skills, none of which need MCP.

## Choosing each persona's task

Use whatever the user specified. If they said "just run the family" with no
specifics, derive each persona's task yourself rather than asking — a
test-mode dispatch is low-stakes, and making the user enumerate six tasks
before anything runs is a worse failure than an imperfect guess.

Look, in order: that persona's `personas/<name>/SOUL.md` for its domain, its
`personas/<name>/PLAN.md` if present (**only `saksee` and `sakjules` have
one** — don't stall on a missing file for the other four), the root `PLAN.md`,
and recent `docs/` changes. Ask the user only if that turns up nothing for a
given persona, and dispatch the other five meanwhile.

Each Agent call's prompt should carry the persona name, the exact command to
run, and what to report:

```
You are dispatching work for the <persona> persona of the Sak Family agent.
Run this exact command from the repo root:

  SAKTHAI_HOME=$(mktemp -d) uv run sakthai run "<task>" \
    --persona <persona> \
    --with-skills Sak-auto-cycle-loop \
    --max-iterations 40 --max-seconds 1800 \
    --no-mcp --dry-run

Report back: rounds completed (or, in --dry-run mode, whether config validated
— quote the `[dry-run] skills:` line), the task and outcome of each round, any
lessons learned, and any blockers or failures.
```

## After all six return

Write one consolidated report — a row per persona:

| Persona | Rounds | Outcome | Status |
|---|---|---|---|
| SakKing | 0 (dry-run) | config validated, skill resolved | success |
| SakSit | — | no credentials for `huggingface` | failed |

In test mode a clean dry-run **is** success, not a sign nothing happened. Report
failures plainly rather than omitting them, and note which mode you ran in so
nobody reads a dry-run table as completed work. One persona failing never
blocks reporting the other five.

## Red flags — you are about to violate this skill

- Treating "run the family auto-cycle," "just run it," or anything short of an
  explicit live-run request as authorization to drop `--dry-run`. This was the
  unanimous 5/5 baseline failure — check it before anything else here.
- Dispatching persona 1, waiting for its result, then persona 2.
- Passing `--provider anthropic` or an explicit `--model`, flattening all six
  back into the same agent and discarding each persona's own config.
- Setting `SAKTHAI_HOME` to a persona's real home *and* passing `--persona`,
  which silently targets a nested empty shard.
- Mixing live and test across the six dispatches in one round.
- Stopping to ask "test or live?" before the safe default, or refusing to
  dispatch until the user enumerates six tasks by hand.
