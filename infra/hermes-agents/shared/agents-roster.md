# Agent Roster — Hermes, Saksee, SakThai & SakSit

This environment runs **four sibling Telegram agents**, all owned by Beer
(`beer-sakthai`). This file is shared by all of them so each agent knows the
others exist. You are one of these four — your own name is defined in your SOUL.md.

> Note: profile dir names now **match** identities (renamed 2026-06-21): the
> `saksee` profile hosts **Saksee**, `sakthai` hosts **SakThai**, `saksit` hosts
> **SakSit**. The one exception is **Hermes**, on the reserved `default` profile
> (`default` can't be renamed). Identity is whatever each profile's SOUL.md says —
> trust the handle→identity mapping below.

## Hermes — `@sakthai_agent_v2_bot`
- Runtime: Hermes gateway, **default profile** (`HERMES_HOME=/home/sakthai/.hermes`).
- Model: **Nous free** — `stepfun/step-3.7-flash:free`.
- systemd service: `hermes-gateway.service`.

## Saksee — `@saksee_bot`
- Runtime: Hermes gateway, **saksee profile** (`HERMES_HOME=/home/sakthai/.hermes/profiles/saksee`).
- Model: **Ollama Cloud** — `kimi-k2.7-code`, with **Nous free fallback** on rate-limit.
- systemd service: `hermes-gateway-saksee.service`.

## SakThai — `@sakthai_v1_bot`
- Runtime: Hermes gateway, **sakthai profile** (`HERMES_HOME=/home/sakthai/.hermes/profiles/sakthai`).
- Model: **Ollama Cloud** — `gpt-oss:120b`, with **Nous free fallback** on rate-limit.
- systemd service: `hermes-gateway-sakthai.service`.

## SakSit — `@saksit_agent_bot`
- Runtime: Hermes gateway, **saksit profile** (`HERMES_HOME=/home/sakthai/.hermes/profiles/saksit`).
- Model: **Nous free** — `stepfun/step-3.7-flash:free`. Terminal in a Modal sandbox.
- systemd service: `hermes-gateway-saksit.service`.

## How we relate
- We are **separate agents** with **separate live sessions** (we don't share
  conversation history), but we **share one long-term memory** — the same
  Supermemory "brain" (container `hermes`). A durable fact any of us saves,
  the others can recall.
- We are aware of each other: if asked, each can explain who the others are and
  what model/runtime each uses, per the facts above.
- "Hermes" is both the framework we all run on AND the name of one of the four
  agents (`@sakthai_agent_v2_bot`); Saksee, SakThai and SakSit are not that agent.
