# Sak Family auto-cycle — consolidated report

**Mode: TEST (dry-run).** All six personas ran with `--dry-run` and their own
fresh `SAKTHAI_HOME=$(mktemp -d)`. No real memory shard under `~/.sakthai/` was
read or written, and no model tokens were spent. Read the table below as *config
validation*, not as completed cycle work.

Live mode was not used, because nothing in the request authorized it — "run the
sak family auto-cycle" is exactly the phrasing that does not. Say the word (e.g.
"do a live run, no dry-run") and I'll re-dispatch the same six against the real
persona homes.

All six went out **in one message, as one parallel fan-out** — not serialized.

---

## Results

| Persona | Rounds | Outcome | Status |
|---|---|---|---|
| SakKing | 0 (dry-run) | config validated — `huggingface` / `Qwen/Qwen3-Coder-30B-A3B-Instruct`, 18 tools, skill resolved; halted at credentials | success (dry-run) |
| SakThai | 0 (dry-run) | config validated — `huggingface` / `gemini-3.1-flash-lite`, 18 tools, skill resolved; halted at credentials | success (dry-run) |
| SakSee | 0 (dry-run) | config validated — `huggingface` / `gemini-3.1-flash-lite`, 18 tools, skill resolved; halted at credentials | success (dry-run) |
| SakSit | 0 (dry-run) | config validated — `huggingface` / `DeepSeek-V4-Flash`, 18 tools, skill resolved; halted at credentials | success (dry-run) |
| SakTan | 0 (dry-run) | config validated — `ollama` → resolved `openai` / `sakthai`, 18 tools, skill resolved; halted at credentials | success (dry-run) |
| SakJules | 0 (dry-run) | config validated — `huggingface` / `gemini-2.5-flash-lite`, 18 tools, skill resolved; halted at credentials | success (dry-run) |

Six of six clean. Every dispatch printed the line that proves skill injection
worked:

```
[dry-run] skills:      1 resolved (Sak-auto-cycle-loop)
```

and then exited non-zero on `Not runnable: no credentials found for provider
'huggingface'` (`'openai'` for SakTan). On a machine with no provider keys — and
this one has none: no `HF_TOKEN`, no `OLLAMA_HOST`, no `.env`, no CLI OAuth cache
— that pair *is* the healthy result. Config validated; the run stopped exactly
where it should.

---

## What each persona was pointed at

Tasks were derived rather than requested, from each `SOUL.md`, the two persona
`PLAN.md` files that exist (SakSee and SakJules), and the root `PLAN.md`.

- **SakKing** — re-derive the shared-vs-canonical package divergence
  (`diff -rq personas/shared/sakthai personas/sakthai/sakthai`) and report which
  entries in CLAUDE.md's list have gone stale.
- **SakThai** — inventory Phase 1 of `docs/hf-cards-improvement-plan.md`, the
  HF Ecosystem row still marked in-progress and awaiting approval to start.
- **SakSee** — its own PLAN Phase 1: Playwright Chromium / Comet executable audit
  and the local GGUF + vision model health check.
- **SakSit** — audit `docs/capabilities.md` against the real 18 tools and CLI
  surface (the 2026-08-28 freshness audit found it listing 8 tools and a
  `sakthai dashboard` view removed in v2).
- **SakTan** — assemble the family daily briefing from the open PLAN items and
  verify the `cron-watchdog-self-heal` sub-skill still names a live schedule.
- **SakJules** — the root PLAN's one open "Not done": wiring
  `--cov-fail-under=96` into `ci.yml` so the floor actually gates the build.

---

## Configuration confirmed by the fan-out

Worth keeping, since it is what the dry run actually bought:

1. **All six personas resolve `Sak-auto-cycle-loop`.** It lives in
   `personas/shared/skills/`, and every persona's overlay reaches it. No persona
   is missing the loop skill.
2. **The six are genuinely distinct.** Five different provider/model pairs came
   back from six personas' own `config/config.yaml` — SakTan alone on `ollama`,
   SakKing on the Qwen coder model, SakSit on DeepSeek, the rest on Gemini-class
   HF models. That is `--persona` doing its job; no `--model` or `--provider` was
   passed, which would have flattened all six into the same agent.
3. **18 built-in tools** registered on every dispatch, consistent across personas.
4. **`--no-mcp` kept it fast.** Without it, `--persona` auto-loads each persona's
   MCP servers and waits out a 30s timeout per unreachable one (~71s per dispatch
   versus ~2s). Nothing a dry run checks needs MCP.

## The one blocker

**No provider credentials on this machine.** Not a failure of any persona — it is
the single thing standing between this dry run and a real cycle. A live run needs
at minimum `HF_TOKEN` (five personas) and a reachable Ollama for SakTan. Nothing
else in the six preflights was unhealthy.

## Next step

Set `HF_TOKEN` (and start Ollama if SakTan should run locally), then say
explicitly that you want a live run. I'll re-dispatch the identical six commands
with `SAKTHAI_HOME` and `--dry-run` dropped, so each persona writes to its own
production shard at `~/.sakthai/<persona>/memory.db` — the same path
`infra/vm-agents/sakthai-agent-run.sh` gives each deployed persona.
