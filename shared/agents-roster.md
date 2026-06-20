# Agent Roster — Hermes, Saksee, SakThai & SakSit

This environment runs **four sibling Telegram agents**, all owned by Beer
(`beer-sakthai`). This file is shared by all of them so each agent knows the
others exist. You are one of these four — your own name is defined in your SOUL.md.

> Note: profile *names* are internal and no longer match identities (history):
> the `default` profile hosts **Hermes**, the `hermesagent` profile hosts
> **SakThai**, the `sakthai` profile hosts **Saksee**. (The newest, `saksit`,
> does match: it hosts **SakSit**.) Identity is whatever each profile's SOUL.md
> says — trust the handle→identity mapping below.

## Hermes — `@sakthai_agent_v2_bot`
- Runtime: Hermes gateway, **default profile** (`HERMES_HOME=/home/sakthai/.hermes`).
- Model: **Nous free** — `stepfun/step-3.7-flash:free`.
- systemd service: `hermes-gateway.service`.

## Saksee — `@saksee_bot`
- Runtime: Hermes gateway, **sakthai profile** (`HERMES_HOME=/home/sakthai/.hermes/profiles/sakthai`).
- Model: **Ollama Cloud** — `kimi-k2.7-code`, with **Nous free fallback** on rate-limit.
- systemd service: `hermes-gateway-sakthai.service`.

## SakThai — `@sakthai_v1_bot`
- Runtime: Hermes gateway, **hermesagent profile** (`HERMES_HOME=/home/sakthai/.hermes/profiles/hermesagent`).
- Model: **Ollama Cloud** — `kimi-k2.7-code`, with **Nous free fallback** on rate-limit.
- systemd service: `hermes-gateway-hermesagent.service`.

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
- "Hermes" is both the framework we all run on AND the name of one of the three
  agents (`@sakthai_agent_v2_bot`); SakThai and Saksee are not that agent.
