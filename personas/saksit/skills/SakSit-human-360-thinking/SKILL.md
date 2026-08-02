---
name: SakSit-human-360-thinking
category: core
description: Analyze problems from every human perspective with clarity.
version: 0.1.0
author: Hermes
tags: [Thinking, Reasoning, Perspective, Analysis, Decision-Making]
---

# 360° Human Perspective Thinking

A structured thinking framework built on four pillars: **Listen**, **Receive**, **Organise**, **Think Clearly** — applied from a full 360° view of everyone involved. Use it when a problem is tangled, emotions are high, stakeholders disagree, or linear analysis misses the human dimension.

This is not a brainstorming technique. It is a **discipline**: slow down, take in the full landscape of human experience around a decision, then organise it until clarity emerges. Works for strategy, conflict resolution, product design, content creation, and any decision with human consequences.

## When to Use

- A problem has multiple stakeholders with competing needs
- You or the user feel stuck, rushed, or reactive about a decision
- You need to understand why someone acted a certain way
- Content or messaging must land with empathy and accuracy
- You're analysing a conflict or failure and need the full picture
- User says "think about this from all angles" or "what would make sense to everyone involved"
- Before writing anything that will be read by real people

## Prerequisites

- No tools required. This is a thinking discipline applied through conversation, reasoning, and writing.
- Optionally use `delegate_task` to parallelise research on different stakeholder perspectives when the landscape is large.

## How to Run

Apply the four pillars in sequence. Each pillar has a clear output that feeds the next. Work through them with the user or silently in your own reasoning when the user asks for analysis.

## Quick Reference

| Pillar | Goal | Key Question | Output |
|--------|------|-------------|--------|
| **Listen** | Absorb fully before acting | What is actually being said and felt? | Raw signal — no filter |
| **Receive** | Drop preconceptions | What would I see if I had no agenda? | Frame shift |
| **Organise** | Structure the landscape | What's really going on here? | Mapped territory |
| **Think Clearly** | Act from the full picture | What makes sense for everyone? | Decision or insight |

## Procedure

### Phase 1: Listen

**Goal:** Receive the full signal before forming any response. Not "listening to reply" — listening to understand.

Steps:
1. **Suspend the answer.** Do not draft a response, solution, or rebuttal in your head while the other person speaks. If you catch yourself doing it, stop and return to pure receiving.
2. **Capture literal content.** What was actually said? Distinguish between data (facts, events, numbers) and interpretation (meaning, spin, assumption).
3. **Capture emotional content.** What feeling carries the words? Fear, frustration, hope, exhaustion? Name the emotion plainly — "this sounds like it comes from exhaustion, not disagreement."
4. **Capture what is NOT said.** Silence, avoidance, hesitancy, changed topic — what might be missing? Ask yourself: "If the speaker could say one more thing without consequence, what would it be?"
5. **Paraphrase back.** Before Phase 2, verify: "Let me check I heard you right. You said X, and what I'm picking up underneath is Y. Is that accurate?"

**Output:** A neutral, unfiltered summary of what was communicated — content, emotion, and omission.

### Phase 2: Receive

**Goal:** Drop your own frame and genuinely try on every other perspective present in the situation. You cannot think clearly from 360° if you skipped this step.

Steps:
1. **Inventory every stakeholder.** List every person, group, or role affected by this situation — including yourself, including silent parties, including people who aren't in the room but will feel the outcome.
2. **Adopt each frame one at a time.** For each stakeholder, answer:
   - What do they actually want? (Not what you think they *should* want.)
   - What do they fear losing?
   - What information do they have that others don't?
   - What do they not see that others see?
3. **Test your own frame.** What assumption are you holding that, if proven wrong, would change your whole view? Write it explicitly.
4. **Do not judge.** A perspective can be "wrong" from your view and still be *real*. You are mapping the territory, not deciding who is right.
5. **Loop back if new perspectives emerge.** Receiving often reveals you didn't listen well enough. Go back to Phase 1.

**Output:** A full stakeholder map — each perspective written in that person's voice, not yours.

### Phase 3: Organise

**Goal:** Turn the now-expanded landscape into a structured model you can reason with.

Steps:
1. **Cluster perspectives** by pattern:
   - Who shares the same core concern?
   - Where do perspectives directly conflict? (Mark these as tension points.)
   - Where do perspectives complement each other?
2. **Find the shared ground.** What does *everyone* agree on? Even in conflict, there is usually 1-2 things no one disputes. Start there.
3. **Identify the real tension.** Often the surface conflict is not the true one. Example: two stakeholders arguing about budget are actually arguing about safety vs. ambition. Name the underlying axis.
4. **Rank by consequence.** Not all perspectives carry equal weight. Which stakeholder's outcome has the most downstream effect? Weight accordingly — but record it, don't discard.
5. **Map possible paths.** For each tension point, what are the possible resolutions? Include options that don't fully satisfy anyone — those maps honestly.

**Output:** A structured landscape: shared ground, tension points, weighted perspectives, and possible resolution paths.

### Phase 4: Think Clearly

**Goal:** From the full 360° map, arrive at a clear, defensible course of action — or a clear articulation of why clarity isn't possible yet.

Steps:
1. **State the decision to be made.** In one sentence. If you can't, you haven't organised enough. Go back to Phase 3.
2. **Evaluate each path against each stakeholder's core need.** A tool: draw a simple impact table.

```
| Path | Stakeholder A | Stakeholder B | Stakeholder C |
|------|--------------|--------------|--------------|
| Path 1 | Satisfies | Harms | Neutral |
| Path 2 | Neutral | Satisfies | Harms |
| Path 3 | Partial | Partial | Partial |
```

3. **Apply the test of humanity.** If you enacted this path, could you look every affected person in the eye and explain why? If not, the path is incomplete or wrong.
4. **Check for blind spots.** Look back at Phase 2 — did you skip a stakeholder? Did you smooth over a tension to get to an answer faster?
5. **Recommend with reasoning.** Present the recommendation not as "this is right" but as "given the full landscape, this path best honours the shared constraints." Include what you are deprioritising and why.
6. **If clarity is impossible:** state unambiguously what information is missing, what would change the picture, and what the cost of waiting is.

**Output:** A clear, defensible recommendation — or a clear statement of what's needed to reach one.

## 360° Perspective Prompts (quick reference)

Use these prompts during Phase 2 when you need to shift frames:

- **User / Creator:** What outcome serves the person who asked for this?
- **Audience / Reader:** How will someone on the receiving side actually experience this?
- **Competitor / Counterpart:** What would they say is the real problem here?
- **Future self (6 months from now):** What would past-me regret not considering?
- **Silent party:** Who is affected but never asked? (Customer support, the next person maintaining this, the person who has to say no.)
- **Adversary:** If someone wanted to argue against my position, what would their best case be?
- **Outsider:** Someone from a completely different industry or culture — what would they notice that we've normalised?

## Reference: Applied Example

See `references/live-application-beer-content-strategy.md` for a worked example — the framework applied to Beer's content strategy decision. Contains full stakeholder map, tension analysis, path evaluation table, and resulting recommendation.

## Pitfalls

- **Skipping Phase 1.** The most common failure: you start organising (Phase 3) before you've truly listened. If the output feels thin, you probably skipped listening or receiving.
- **Confusing "Receive" with "Agree."** Receiving a perspective does not mean endorsing it. You can accurately map a view you find wrong. The map is not the judgement.
- **Over-organising too early.** Structure is useful but premature structure locks you into one frame. Let the listening and receiving expand the landscape before you impose order.
- **False consensus.** People nodding in agreement is not the same as shared understanding. Test: "Let me say back what I think we've agreed on — does that match your understanding?"
- **Analysis paralysis.** The 360° view can feel endless. Use a timer or a page limit: "I will spend exactly 15 minutes on receiving before I move to organise." Clarity is the goal, not completeness.
- **Using the framework to justify your existing position.** If the output is always the same, you're not really doing it. Look for conclusions that *surprise* you.

## Verification

After applying the framework, check:

1. Can you name at least 3 distinct stakeholder perspectives that shaped your conclusion?
2. Is there a perspective in your final recommendation that did NOT match your initial assumption?
3. Could you explain your decision to someone who disagrees, in terms that person would recognise as fair?

If yes to all three, the 360° framework has done its work.
