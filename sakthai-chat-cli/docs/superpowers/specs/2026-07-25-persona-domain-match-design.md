# Persona domain match — design spec

Date: 2026-07-25

## Context

`sakthai-chat-cli` is the standalone extraction of SakThai from the
`Sak-Family-Agent` monorepo — only SakThai's own persona data (`SOUL.md`,
config, skills) is present here. The chat UI's theme module
(`sakthai/agent/theme.py`) already carries colors, gradients, and avatar
glyphs for all six Sak Family personas (SakKing, SakThai, SakSee, SakSit,
SakTan, SakJules), unused by anything outside the welcome banner today.

Beer wants replies to visually signal which family member's domain a
question best fits — e.g. a CI/CD question gets framed with SakJules'
red/⚙️ theme — even though SakThai is the only persona actually present
here and remains the one generating every reply. This is a labeling/framing
feature, not a multi-agent handoff: no other persona's identity, memory, or
SOUL.md is invoked.

SakTan is excluded from the domain table: its persona files are currently
missing from `Sak-Family-Agent` (an in-progress, unconfirmed removal
discovered during an unrelated cleanup session), and the current
`Sak-Family-Agent/README.md` family-role table no longer lists it either.

## Goal

When a user's message clearly matches one family member's domain, theme
that reply's panel with the matched persona's color/avatar and add a small
label naming the match. When nothing matches clearly, render exactly as
today (SakThai's own cyan theme, no label).

## Design

### 1. Matching module — `sakthai/agent/persona_match.py`

```python
# persona_key: (domain_label, strong_keywords, weak_keywords)
PERSONA_DOMAINS: dict[str, tuple[str, tuple[str, ...], tuple[str, ...]]] = {
    "sakking":  ("general tasks", (), ("remind", "schedule", "task", "todo", "run this", "execute")),
    "saksee":   ("web & browser automation", ("automate the web",), ("browser", "scrape", "website", "web page", "url")),
    "saksit":   ("social & storytelling", ("social media", "instagram"), ("tweet", "caption", "story", "write a post")),
    "sakjules": ("CI/CD & automation", ("ci/cd", "github actions"), ("deploy", "pipeline", "workflow", "build fails")),
}

def match_persona(message: str) -> tuple[str, str] | None:
    """Case-insensitive keyword scoring against PERSONA_DOMAINS: a strong
    keyword hit is worth 2 points, a weak keyword hit 1 point. Returns
    (persona_key, domain_label) for the highest scorer at or above the
    2-point threshold, or None if no persona clears it — caller falls
    back to SakThai's own theme, unlabeled."""
```

**Revised post-review:** the original version scored every keyword equally
and required 2+ raw hits regardless of specificity — which meant an
unambiguous single phrase like "repair our CI/CD" never matched at all
(one hit on `"ci/cd"`, below the flat threshold), contradicting the
motivating example for this feature. Splitting keywords into a strong tier
(worth `STRONG_WEIGHT = 2`, clears the threshold alone) and a weak tier
(worth `WEAK_WEIGHT = 1`, still needs two combined) fixes this while
keeping the original safeguard for single common/ambiguous words (`"task"`,
`"story"`) that shouldn't trigger a label by themselves.

- Pure function, no I/O, no external dependencies — deterministic and free.
- SakThai has no table entry: it is the implicit default, not a "match."
- A single strong-keyword hit, or two weak-keyword hits (any combination,
  including a strong hit plus a weak hit), clears the 2-point threshold.
  A single weak-keyword hit alone never does.
- Domain keywords are plain lowercase substrings, matched against the
  lowercased message — no regex, no stemming, easy to hand-edit later.
  This is deliberately not word-boundary-aware: a short keyword can match
  inside an unrelated longer word (`"story"` inside `"history"`, `"url"`
  inside `"curl"`). The 2-hit threshold makes an accidental double-hit
  unlikely but not impossible — accepted tradeoff for staying regex-free;
  revisit if false-positive labels turn out to be a real problem in use.

### 2. UI integration — `sakthai/agent/chat.py`

**Correction (post-review):** an earlier version of this section named
`sakthai/cli/chat.py` + `sakthai/agent/ui.py` as the integration points,
written before the actual reply-rendering code had been located. The real
integration point, confirmed during planning and implementation, is the
`ReplyStream` class and `make_token_renderer()` factory in
`sakthai/agent/chat.py` — `cli/chat.py` only wires up the `chat` Click
command, and `ui.py` has no reply-panel-specific rendering function at all.

- In `run_chat`'s turn loop (`sakthai/agent/chat.py`), immediately before
  building the token renderer for a reply, call `match_persona(user_text)`.
- Pass the result (persona key + domain label, or `None`) as a new
  `matched` keyword argument into `make_token_renderer`/`ReplyStream`.
- `ReplyStream`'s color/avatar/label — previously always derived from the
  `persona` argument it was constructed with — become conditional: use the
  matched persona's entries from the existing `theme.py` tables when
  `matched` is present, the constructor's own `persona` argument otherwise
  (so a session started with `--persona saksee` still shows SakSee on
  unmatched turns, not SakThai — the fallback is "no match," not "hardcoded
  to SakThai"). No new color/avatar data is added; this only wires up
  tables that already exist for all six personas.
- When matched, add a `chip()` (the existing pill-shaped metadata token
  already used for tool traces) to the panel's header row:
  `<avatar> best matched: <Label> · <domain>`, e.g.
  `⚙️ best matched: SakJules · CI/CD & automation`.
- SakThai continues to generate the reply text in every case. This feature
  changes only the panel's visual framing and an informational label — not
  who answers.

### 3. Testing

- New `tests/test_persona_match.py`:
  - One clear-hit example message per persona in `PERSONA_DOMAINS`,
    asserting the correct `(persona_key, domain_label)` match.
  - One ordinary/ambiguous message asserting `None` (falls back to
    SakThai).
  - One message with exactly 1 keyword hit asserting `None` (confirms the
    2+ threshold is enforced, not just documented).
- Extend existing `tests/test_ui.py`:
  - Reply panel renders with the matched persona's color/avatar/chip when
    a match is passed.
  - Reply panel renders with SakThai's own theme and no chip when no match
    is passed (regression guard for the default path).
- No changes expected to `tests/test_chat.py`'s existing REPL-flow tests
  beyond confirming the new call site is a no-op on the default (no-match)
  path — full existing suite must still pass.

## Out of scope

- Any other persona actually answering, or loading any other persona's
  `SOUL.md`/config/memory — this repo only contains SakThai's.
- SakTan, pending resolution of its incomplete removal from
  `Sak-Family-Agent`.
- LLM- or embedding-based classification — keyword scoring only, per
  Beer's cost-conscious/free-by-default preference.
