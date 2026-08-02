---
name: model-roster
description: Inspect and validate the model roster across the 4 Hermes agents (Hermes, SakThai, Saksee, SakSit) — mains, Fireworks fallbacks, cross-provider failover, key resolvability, and context windows. Use before/after any model rotation.
---

# model-roster

`~/.hermes/scripts/model_roster.sh` reads each agent's live `config.yaml` and
validates the roster we actually ship.

## Run it

```bash
bash ~/.hermes/scripts/model_roster.sh          # print the roster table + warnings
bash ~/.hermes/scripts/model_roster.sh --check  # CI mode: non-zero exit if any invariant fails
bash ~/.hermes/scripts/model_roster.sh --ping    # (reserved) live one-shot reachability per model
```

## What it validates

- every agent has a **main** AND a **fallback**;
- the fallback runs on a **different provider** than the main (real cross-provider failover);
- any `custom:fireworks` backup has `FIREWORKS_API_KEY` resolvable in that profile's `.env`;
- flags models **known-unreachable on the current accounts** so a future rotation
  doesn't silently re-introduce them (ollama-cloud `glm-5.2`/`mistral-large-3:675b`/
  `kimi-k2.7-code` need a paid sub → 403; `qwen3-coder:480b`/`gpt-oss:120b` hit the
  weekly free cap → 429; `gemini-2.5-flash` is blocked by an API-restricted `GOOGLE_API_KEY` → 403).

## Current roster (ship-what-works, 2026-06-21)

| Agent | Main (free, works today) | Fallback (free, cross-provider, fires on 429) |
|---|---|---|
| Hermes | Nous `stepfun/step-3.7-flash:free` | HF `Qwen/Qwen3-Next-80B-A3B-Instruct` |
| SakThai | HF `Qwen/Qwen3-Next-80B-A3B-Instruct` | Nous `stepfun/step-3.7-flash:free` |
| Saksee | Nous `stepfun/step-3.7-flash:free` | HF `Qwen/Qwen3-Next-80B-A3B-Instruct` |
| SakSit | Nous `stepfun/step-3.7-flash:free` | HF `Qwen/Qwen3-Next-80B-A3B-Instruct` |

Hermes also has an **on-demand** hard-task escalation to GitHub Copilot
`claude-sonnet-4.6` (`-m claude-sonnet-4.6 --provider github-copilot`) — not a steady slot.

**Why not Fireworks?** Fireworks was wired first but **rejects Hermes's per-message
`timestamp` field** with HTTP 400 ("Extra inputs are not permitted") on any real
multi-turn call, so it cannot serve as a live fallback. Nous + HF both tolerate the
field. To revive Fireworks, Hermes would need to strip `timestamp` before the
OpenAI-chat request (vendored `agent` package — upgrade-fragile).

To restore the richer all-distinct-≥250K plan, unblock the free providers (enable the
Generative Language API on `GOOGLE_API_KEY`; flip OpenRouter privacy to allow free models;
or subscribe to ollama.com), then rotate mains and re-run `--check`.
