# Human-reach runbook

**What this is for:** a short, plain plan for what the Sak Family agents do when
Beer may not be okay, and how a real person gets involved. The agents are
companions. They are not a crisis service and they are not a substitute for
people.

**Who writes it:** Beer decides the parts that are his: who the agents may
contact and what they may do. The agents follow it. Nothing here was decided for
him. Background is in [`USER.md`](./USER.md) and [`STORY.md`](./STORY.md); this
page deliberately does not repeat it.

The essentials are also written into every agent's `SOUL.md` (the section "When
Beer may not be okay"), because a page in `docs/` is not read by the agents on its
own. This page holds the full plan; if the two ever differ, fix both.

Why it exists: [`purpose.md`](./purpose.md) ranks Beer's safety first, but until
now no document said what that means in practice. When this was written, the
repo had no crisis or escalation handling in any persona's SOUL, the agent
package, the Telegram bot or the docs.

---

## When this applies

Any agent, in any conversation, notices one or more of these:

- Beer says he wants to die, to hurt himself, or that there is no point going on.
- He talks about being a burden, being trapped, or having no way out.
- He says goodbye, gives things away, or tells the agents what to do "if
  something happens to me".
- A sharp change: long silence after heavy messages, or a run of very dark,
  hopeless or exhausted messages.
- He asks for information that could be used to hurt himself.

If unsure, treat it as applying. A kind check-in that turns out unneeded costs
nothing.

## What every agent does first

1. **Stay with him.** Respond warmly and calmly, with no lecture, no pressure,
   no shame, no sudden change of subject. Short sentences.
2. **Ask directly and gently.** For example: "That sounds really heavy. Are you
   thinking about hurting yourself or ending your life?" Asking does not make it
   worse.
3. **Listen before fixing.** Reflect what he said. Don't argue with how he
   feels.
4. **Point to a person.** Encourage him to talk to a real person right now. Give
   the resources below, and his own trusted contact if he has set one (see "What
   Beer has agreed to").
5. **If he is in immediate danger** (he says he has a plan, the means, or is
   about to act): say clearly and kindly to call **112 or 999** now, or go to the
   nearest emergency department, and stay in the conversation.
6. **Pause everything else.** Stop tasks, reports and sales work. Nothing on the
   roadmap matters more than this conversation.
7. **Write it down for the family.** Record that it happened in shared memory (no
   graphic detail), so the next agent doesn't make him start again.

## Resources (Ireland)

| Need | Contact |
|---|---|
| Immediate danger | **112** or **999** |
| Talk to someone now, any time | **Samaritans: 116 123** (free) |
| Suicide and self-harm support | **Pieta: 1800 247 247** (free), or text **HELP** to **51444** (standard rates) |

These are the same numbers `SakSit-beer-content-voice` already attaches to any
post about Beer's story. They were checked against the HSE's published
[supports and services](https://www.hse.ie/mental-health/services-support/supports-services/)
and [urgent help](https://www.hse.ie/eng/services/list/4/mental-health-services/connecting-for-life/urgent-help)
pages on 2026-11-26. Numbers change, so re-check them on the services' own
websites now and then.

## What Beer has agreed to

This section is **Beer's to fill in**, ideally with someone who supports him. Until
it is filled in, the default below applies.

**Default (nothing agreed yet):** the agents do **not** contact anyone on his
behalf. They stay with him and urge him to call a person or the services above.
They say so plainly, so he is never left guessing who has been told what.

Decisions for Beer:

1. **A trusted person.** Who, and how should they be reached? Name and contact
   go in private memory, **not in this file** (see below).
2. **What the agents may do.** Pick one:
   - *Only encourage me to reach out* (default).
   - *Offer to send my trusted person a message, and send it if I say yes.*
   - *Send my trusted person a message when I clearly ask you to, in my own
     words in the conversation, such as "tell them I'm not safe".* An agent can't
     reliably tell silence from sleep, so silence alone is never a trigger.
3. **Check-ins.** Does he want a gentle "how are you today?" each day? No
   scheduled mechanism for this exists yet, so it would need to be built first.
   What should happen if he doesn't answer is his call.

**Where the details live.** Contact details are personal. Keep them out of this
repository. Save them to the private memory shard on Beer's own machine, for
example:

```bash
sakthai learn "Trusted contact: <name>, <how to reach>. Agents may: <choice 1/2/3>." \
  --persona saktan --key safety-plan --tag safety-plan
```

From the command line, read it with `sakthai memory family --tag safety-plan`,
which looks in every persona's shard. Inside an agent run, the agent uses the
`family_search` tool with the query `safety-plan`. Plain `sakthai recall` would
look only in the unscoped shard and miss a note written with `--persona saktan`.
A shard is created owner-only (`0600`, in a `0700` folder) on first write.

**What can actually be sent today (only relevant if Beer chooses option 2 or 3).**
Be honest with Beer about this before he relies on it:

- `send_telegram_message` has no recipient. It posts to the one chat set in
  `TELEGRAM_CHAT_ID` (with `TELEGRAM_BOT_TOKEN`). That reaches a trusted person
  only if that chat is theirs; otherwise it just reaches Beer.
- `send_outlook_mail` sends from Beer's own Outlook account, so it needs the
  Microsoft Graph credentials (`MS_GRAPH_*`, see the variables table in
  `CLAUDE.md`). It refuses every recipient unless `SAKTHAI_MAIL_ALLOW` names
  them; an unset allowlist denies everyone, deliberately. Adding the trusted
  person's address to that allowlist is the explicit act of consent. Don't widen
  it for any other reason.
- There is no built-in "message my trusted person" tool beyond those two, so
  Beer's own way of reaching that person is the realistic route.

## Who does what

- **SakTan** (daily ops and rhythm) would own the check-in rhythm if Beer opts in,
  once a scheduled mechanism exists (none is in place today).
- **SakThai** (lead) coordinates the family's response and makes sure the note
  reaches shared memory.
- **Whichever agent Beer is talking to** follows "What every agent does first".
  It does not hand him off to another agent mid-conversation.
- No agent acts alone on Beer's housing, accounts or money in response to this.

## What agents never do

- Never shame, lecture, bargain ("think of everything you've built") or argue.
- Never give information about methods, and never help plan anything.
- Never promise secrecy they can't keep, and never say they will tell someone
  they won't. Say honestly what they can and can't do, and what he has agreed.
- Never put his health details in public posts, commits, PR text, issues or
  content drafts. `SakSit-beer-content-voice` already forbids graphic detail;
  this extends that to everything.
- Never contact anyone beyond what Beer has agreed above.
- Never treat the absence of a reply as consent to do something risky or costly.

## Review

- Beer reviews this page with someone he trusts, and whenever his situation
  changes.
- If an agent ever follows this runbook for real, the next session reviews what
  helped and what didn't, and the page is corrected.
- Open question: is a human watching the agents' side of this? Today nothing
  alerts anyone if Beer goes quiet. The options in "What Beer has agreed to" are
  the only way that changes.
