# Human-reach runbook

**What this is for:** a short, plain plan for what the Sak Family agents do when
Beer may not be okay, and how a real person gets involved. The agents are
companions. They are not a crisis service and they are not a substitute for
people.

**Who writes it:** Beer decides the parts that are his: who the agents may
contact and what they may do. The agents follow it. Nothing here was decided for
him. Background is in [`USER.md`](./USER.md) and [`STORY.md`](./STORY.md); this
page deliberately does not repeat it.

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
| Suicide and self-harm support | **Pieta: 1800 247 247** (free) |

These are the same numbers `SakSit-beer-content-voice` already attaches to any
post about Beer's story. **Re-check them against the services' own websites
before relying on this page.** Numbers change.

## What Beer has agreed to

This section is **Beer's to fill in**, ideally with someone who supports him. Until
it is filled in, the default below applies.

**Default (nothing agreed yet):** the agents do **not** contact anyone on his
behalf. They stay with him and urge him to call a person or the services above.

Decisions for Beer:

1. **A trusted person.** Who, and how should they be reached? Name and contact
   go in private memory, **not in this file** (see below).
2. **What the agents may do.** Pick one:
   - *Only encourage me to reach out* (default).
   - *Offer to send my trusted person a message, and send it if I say yes.*
   - *Send my trusted person a message without asking, if I am in danger and
     have gone quiet.*
3. **Check-ins.** Does he want SakTan's daily rhythm to include a gentle "how
   are you today?" and what should happen if he doesn't answer for a set time?

**Where the details live.** Contact details are personal. Keep them out of this
repository. Save them to the private memory shard on Beer's own machine, for
example:

```bash
sakthai learn "Trusted contact: <name>, <how to reach>. Agents may: <choice 1/2/3>." \
  --persona saktan --key safety-plan --tag safety-plan
```

Agents read it with `sakthai recall` or `sakthai memory family --tag safety-plan`.
A shard is created owner-only (`0600`) on first write.

**Technical note, only if Beer chooses option 2 or 3.** Agents can only message
someone if the channel is set up on purpose: `send_telegram_message` needs
`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`, and `send_outlook_mail` refuses every
recipient unless `SAKTHAI_MAIL_ALLOW` names them (an unset allowlist denies all,
deliberately). Setting the allowlist to the trusted person's address is the
explicit act of consent. See the variables table in `CLAUDE.md`. Don't widen it
for any other reason.

## Who does what

- **SakTan** (daily ops and rhythm) owns the check-in rhythm, if Beer opts in.
- **SakThai** (lead) coordinates the family's response and makes sure the note
  reaches shared memory.
- **Whichever agent Beer is talking to** follows "What every agent does first".
  It does not hand him off to another agent mid-conversation.
- No agent acts alone on Beer's housing, accounts or money in response to this.

## What agents never do

- Never shame, lecture, bargain ("think of everything you've built") or argue.
- Never give information about methods, and never help plan anything.
- Never promise to keep a secret they may need to share if he is in danger.
  (Say honestly what they can and can't do.)
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
