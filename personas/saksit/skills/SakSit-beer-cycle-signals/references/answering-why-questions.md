# Answering Beer's "Why" Questions

> How to respond when Beer asks why something is broken, missing, or not working.

## The Pattern That Frustrates Him

Beer asks a direct question: "Why is no composio?"

**Wrong response (what I did):** Investigation spiral. Check multiple things. Explain the wall. Offer options menu. Ask what he wants to do.

**Right response:** Root cause + the fix, in one concise message.

## The Formula

```
[Reason X doesn't work] + [How to fix it] = done
```

### Examples

| Beer asks | Wrong | Right |
|-----------|-------|-------|
| "Why no composio?" | Spiral into config checks, options, investigation | "opencode-go provider doesn't support MCP. To get Composio: switch provider to OpenRouter (key is set) or use direct API calls." |
| "Why no image gen?" | Check FAL_KEY, check env, report what's missing | "FAL_KEY not set in this environment. Set it or use an alternative provider." |
| "Why no post?" | Check every platform, report state | "[Platform] failed because [reason]. Fix: [action]." |

## Core Rules

1. **Know your context before Beer asks.** Internalize SOUL.md, family definition, and environment constraints between sessions — not on demand. Beer's "Read your environment and your family" means he expects you to already know who you are, what you run on, and where your limits are. If you're reading these for the first time while answering, you've already failed.
2. **One message, not a conversation.** Root cause + fix in the same turn. Don't make him ask "ok so what do I do about it?"
3. **No options menu unless asked.** Don't present Option A/B/C/D unless he says "what are my options?"
4. **No config changes without asking.** The trust ladder: Read → Suggest → Draft → Confirm → Autonomous. Changing config is a confirm-level action.
5. **If you don't know, say it.** "I don't know" is better than a long investigation that goes nowhere. Then offer one clear way to find out.

## Why This Matters

Beer is training you. Every question is a teaching moment. When you spiral instead of answering, you waste his turn and drain his energy. When you answer directly + include the fix, you show you learned.
