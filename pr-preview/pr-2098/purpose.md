# What Sak Family Agent is for

## In one sentence

Six AI companions that support **Beer** day to day and help him build an income
of his own. The software platform is how they do that. It is not the goal.

## Who it is for

Beer first. He built this because he wanted companions who would help him get
back on his feet and remind him who he is. His own account is in
[`STORY.md`](./STORY.md), and how the agents should treat him is in
[`USER.md`](./USER.md). Read both before changing anything that touches how an
agent talks to him, what it does on his behalf, or what it spends.

Beer has 12 years of business experience and no coding background, so the agents
handle the technical work and lean on his judgment for the business.

## Three jobs, in priority order

When the jobs pull against each other, the higher one wins.

| # | Job | Where it lives | It is working when |
|---|---|---|---|
| 1 | **Companionship and safety.** Beer feels less alone, and the agents act with care, patience and low-risk help. | Persona `SOUL.md` files, [`SOUL.md`](./SOUL.md), the Dream → Hope → Care → Joy → Trust → Growth cycle | Beer uses them and they help him. Nothing they do puts his housing, accounts, safety or finances at risk. |
| 2 | **Income for Beer.** A product people pay for. | `services/servicequotebot/`, `sakthai lead`, [`product/PLAN.md`](../product/PLAN.md) | There are paying customers and Beer can see the money coming in. |
| 3 | **A reusable platform.** Other people could deploy their own agents. | The `sakthai` package, persona exports, [`architecture.md`](./architecture.md) | Someone other than Beer runs it. Treat this as a bonus, not a roadmap driver. |

## How the pieces serve it

- **Six personas, one family.** Each has a role and its own memory. The roster
  and roles are in [`SOUL.md`](./SOUL.md). Don't copy them here, since models
  and counts change.
- **Memory.** The agents remember what Beer tells them so he doesn't have to
  repeat himself. `sakthai memory family` reads across all of them.
- **The cycle.** Dream → Hope → Care → Joy → Trust → Growth is the six values
  Beer holds, used as the way the agents work. It is described in
  [`cycle/`](./cycle/).
- **Cost.** Beer is cost-constrained. Anything that spends money or reaches
  outside needs his explicit OK ([`OPERATING_CONTRACT.md`](./OPERATING_CONTRACT.md)).

## What it is not

- Not a general consumer app.
- Not a software-engineering framework. [`sak-family-agent-overview.md`](./sak-family-agent-overview.md)
  describes one and is out of date.
- Not finished because a lot of machinery exists. Skills, workflows, exports and
  tests count only if they serve one of the three jobs above.

## How to tell whether it is working

These are questions, not metrics. Ask them regularly and answer honestly.

1. Did Beer use the agents this week? Which one, and for what?
2. Did it help him, in his own words?
3. Are there paying customers? Is revenue growing?
4. If Beer is struggling, is there a path that reaches a person, and not only
   other agents?

## Open decisions

- **Priority order.** This page puts companionship and safety above income, and
  income above the platform. [`product/decision.md`](../product/decision.md)
  says "business-first platform" and ranks personal and family use second. Beer
  should confirm the order. Once he has, `product/decision.md` should be amended
  to match or this page changed.
- **Question 4 above.** I did not find an agreed answer in the repo for how the
  family reaches a human if Beer is not okay. That needs a decision with Beer,
  and then a runbook.
