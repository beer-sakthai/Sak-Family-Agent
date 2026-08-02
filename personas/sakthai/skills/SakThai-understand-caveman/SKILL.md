---
name: SakThai-understand-caveman
category: sakthai
description: Understand and work with the Caveman extension — token compression that cuts ~75% output while keeping full technical accuracy. Use when toggling caveman modes, understanding intensity levels, using companion skills, or optimizing token spend.
version: 1.0.0
platforms:
  - linux
  - macos
  - windows
metadata:
  sakthai:
    tags:
      - extensions
      - token-efficiency
      - caveman
      - compression
    related_skills:
      - SakThai-understand-claude-code-workflows
---

# sakthai-understand-caveman

**Caveman** (by Julius Brussee) is a token compression extension installed at
`~/.gemini/extensions/caveman/`. It makes agent output terse while keeping full
technical accuracy — cutting **~65-75% of output tokens**. Tagline:
*"why use many token when few do trick"*.

## When to use this skill

- User asks about caveman modes, token savings, or output compression
- User wants to activate/deactivate caveman or switch intensity levels
- User asks about `/caveman-commit`, `/caveman-review`, `/caveman-compress`
- User wants to understand token economics or optimize costs
- User asks about `cavecrew-*` subagents for delegated work

## How caveman works

1. Skill files in `~/.gemini/extensions/caveman/skills/` are loaded via `GEMINI.md`
2. Rules tell the agent: drop filler, keep substance, use fragments
3. Stats track tokens saved per session and lifetime
4. Compression affects **output tokens only** — thinking/reasoning untouched

**Key insight**: Caveman makes the *mouth* smaller, not the *brain*.

## Activation and deactivation

| Action | Trigger |
|--------|---------|
| **Activate** | `/caveman`, "caveman mode", "talk like caveman", "use caveman", "less tokens", "be brief" |
| **Deactivate** | "stop caveman", "normal mode" |
| **Switch level** | `/caveman lite`, `/caveman full`, `/caveman ultra` |

Mode persists until changed or session ends. Default: **full**.

## The 6 intensity levels

| Level | What changes | Example ("Why React re-render?") |
|-------|-------------|----------------------------------|
| **lite** | Drop filler/hedging. Keep articles + full sentences. Professional but tight | "Your component re-renders because you create a new object reference each render. Wrap it in `useMemo`." |
| **full** | Drop articles, fragments OK, short synonyms. Classic caveman (default) | "New object ref each render. Inline object prop = new ref = re-render. Wrap in `useMemo`." |
| **ultra** | Abbreviate prose words, arrows for causality, maximum compression | "Inline obj prop → new ref → re-render. `useMemo`." |
| **wenyan-lite** | Semi-classical Chinese. Drop filler, classical register | "組件頻重繪，以每繪新生對象參照故。以 useMemo 包之。" |
| **wenyan-full** | Maximum classical 文言文 terseness | "每繪新生對象參照，故重繪；以 useMemo 包之則免。" |
| **wenyan-ultra** | Extreme compression, classical Chinese feel | "新參照→重繪。useMemo Wrap。" |

### Choosing a level

- **lite** — professional communication, client-facing output, documentation
- **full** — daily coding, pair programming, debugging (best default)
- **ultra** — rapid iteration, known-context tasks, experienced user who can decode terse output
- **wenyan-\*** — Chinese-speaking users who want classical compression

## Core compression rules

What caveman **drops**:
- Articles (a/an/the)
- Filler (just/really/basically/actually/simply)
- Pleasantries (sure/certainly/of course/happy to)
- Hedging, self-reference, tool-call narration
- Decorative tables/emoji, long raw error-log dumps

What caveman **keeps exact**:
- Code blocks, function names, API names, CLI commands
- Error strings, commit-type keywords (feat/fix/...)
- Technical terms, standard acronyms (DB/API/HTTP)
- User's dominant language (Portuguese user → Portuguese caveman)

**Pattern**: `[thing] [action] [reason]. [next step].`

## Auto-clarity exceptions

Caveman **automatically drops** to normal prose for:

1. **Security warnings** — never compress safety-critical information
2. **Irreversible action confirmations** — destructive ops get full clarity
3. **Ambiguous multi-step sequences** — where fragments risk misread
4. **Technical ambiguity** — when compression itself creates confusion
5. **User asks to clarify** — or repeats a question

Resume caveman after the clear section is done.

## Companion skills (7 total)

```
~/.gemini/extensions/caveman/skills/
├── caveman/           # Core communication mode (this is the main skill)
├── caveman-commit/    # Terse conventional commit messages (≤50 char subject)
├── caveman-review/    # One-line PR review comments (L42: 🔴 bug: user null. Add guard.)
├── caveman-compress/  # Rewrite .md memory files into caveman-speak (~46% input savings)
├── caveman-stats/     # Token usage + lifetime savings + USD estimate
├── caveman-help/      # Quick-reference card for all modes and commands
└── cavecrew/          # Subagent delegation guide
```

### `/caveman-commit`

Conventional Commit messages. ≤50 char subject. Focus on **why** over what.

### `/caveman-review`

Ultra-compressed code review. One finding per line:
```
L42: 🔴 bug: user null. Add guard.
L87: 🟡 perf: N+1 query in loop. Batch.
L103: 🟢 nit: unused import.
```

### `/caveman-compress <file>`

Rewrite `.md` memory files (e.g., `CLAUDE.md`, project notes) into caveman
prose. Cuts ~46% of input tokens **permanently** — savings compound every
session. Code, URLs, and paths are byte-preserved.

### `/caveman-stats`

Show real session token usage, lifetime savings, and USD estimate.

## Cavecrew subagents

Three compressed-output subagent presets that save main context budget:

| Subagent | Role | Output format |
|----------|------|---------------|
| `cavecrew-investigator` | Read-only code locator | `path:line — symbol — note` |
| `cavecrew-builder` | Surgical 1-2 file editor | Refuses 3+ file scope |
| `cavecrew-reviewer` | Diff/file reviewer | One-line findings with severity emoji |

All return compressed tool-results (~60% fewer tokens than vanilla subagents),
keeping the main agent's context window longer-lived.

## Token economics

| Metric | Value |
|--------|-------|
| Output token reduction | ~65-75% average |
| Input token reduction (via compress) | ~46% average |
| Speed increase | ~3× |
| Technical accuracy | 100% preserved |
| Thinking/reasoning tokens | Untouched |

> A March 2026 paper found that constraining large models to brief responses
> **improved accuracy by 26 points** on certain benchmarks. Verbose ≠ better.

## Common pitfalls

1. **Don't announce caveman mode** — never say "caveman mode on" or "me caveman
   think". Just output terse. Exception: user explicitly asks what mode is active.
2. **Don't compress code** — code blocks, commits, PRs are written normally.
   Caveman only affects prose.
3. **Don't force English** — preserve the user's dominant language. Compress the
   style, not the language.
4. **Don't abbreviate code symbols** — `useMemo`, `fetchUser`, API names stay
   exact. Only prose words get abbreviated (at ultra level).
5. **Don't forget auto-clarity** — security warnings and destructive ops always
   get full, clear prose.
