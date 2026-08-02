# Persona Domain Match Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a chat message clearly fits one Sak Family persona's domain, re-theme that reply's panel with that persona's existing color/avatar and add a "best matched" chip — without that persona actually answering.

**Architecture:** A new pure function `match_persona()` keyword-scores the user's message against a small domain table (4 personas, excluding SakThai and SakTan) and returns the best match or `None`. The result flows one level deep: `run_chat`'s turn loop computes it once per turn and passes it into the existing `ReplyStream` renderer, which already owns all persona-colored panel rendering.

**Tech Stack:** Python 3.11+, Rich (`Panel`, `Text`, `Live`), pytest.

## Global Constraints

- Threshold for a match is **2 or more** keyword hits (spec section 1) — confirmed with the user, do not change to 1.
- Matching is plain lowercase substring scoring — no regex, no external dependencies (spec section 1, "Out of scope").
- SakThai always generates the reply text in every case; this feature only changes panel theming/labeling (spec section 2).
- No other persona's `SOUL.md`/config/memory is loaded (spec "Out of scope") — only `theme.py`'s existing color/avatar/label tables are reused.
- SakTan is excluded from `PERSONA_DOMAINS` (spec "Context").
- Full existing test suite (`pytest tests/ -q`) and `ruff check sakthai tests` / `mypy sakthai` must stay green after each task — this repo's CI (fixed in an earlier session) actually enforces these now.

---

### Task 1: `match_persona()` domain-matching module

**Files:**
- Create: `sakthai/agent/persona_match.py`
- Test: `tests/test_persona_match.py`

**Interfaces:**
- Produces: `PERSONA_DOMAINS: dict[str, tuple[str, tuple[str, ...]]]` (persona_key → (domain_label, keywords)), `MATCH_THRESHOLD: int = 2`, `match_persona(message: str) -> tuple[str, str] | None`. Task 3 imports `match_persona` by this exact name and signature.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_persona_match.py`:

```python
"""Tests for sakthai.agent.persona_match — keyword-based domain matching."""

from __future__ import annotations

from sakthai.agent.persona_match import PERSONA_DOMAINS, match_persona


def test_match_persona_returns_none_for_an_ordinary_message() -> None:
    assert match_persona("What's the weather like today?") is None


def test_match_persona_requires_at_least_two_keyword_hits() -> None:
    # "deploy" alone is one hit — below the threshold.
    assert match_persona("Can you deploy this for me?") is None


def test_match_persona_matches_sakjules_on_cicd_language() -> None:
    result = match_persona("The github actions pipeline keeps failing on deploy")
    assert result == ("sakjules", "CI/CD & automation")


def test_match_persona_matches_saksee_on_browser_automation_language() -> None:
    result = match_persona("Can you scrape this website and grab the url list?")
    assert result == ("saksee", "web & browser automation")


def test_match_persona_matches_saksit_on_social_media_language() -> None:
    result = match_persona("Write a post caption for instagram about our launch")
    assert result == ("saksit", "social & storytelling")


def test_match_persona_matches_sakking_on_task_language() -> None:
    result = match_persona("Remind me to schedule this task for tomorrow")
    assert result == ("sakking", "general tasks")


def test_persona_domains_excludes_sakthai_and_saktan() -> None:
    assert "sakthai" not in PERSONA_DOMAINS
    assert "saktan" not in PERSONA_DOMAINS
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_persona_match.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'sakthai.agent.persona_match'`

- [ ] **Step 3: Write the implementation**

Create `sakthai/agent/persona_match.py`:

```python
"""Keyword-based domain matching for the chat CLI.

Labels a reply with whichever Sak Family persona's domain best fits the
user's message — SakThai always generates the reply text; this only
affects how the reply panel is themed and labeled. See
docs/superpowers/specs/2026-07-25-persona-domain-match-design.md.
"""

from __future__ import annotations

MATCH_THRESHOLD = 2

PERSONA_DOMAINS: dict[str, tuple[str, tuple[str, ...]]] = {
    "sakking": (
        "general tasks",
        ("remind", "schedule", "task", "todo", "run this", "execute"),
    ),
    "saksee": (
        "web & browser automation",
        ("browser", "scrape", "website", "web page", "url", "automate the web"),
    ),
    "saksit": (
        "social & storytelling",
        ("social media", "instagram", "tweet", "caption", "story", "write a post"),
    ),
    "sakjules": (
        "CI/CD & automation",
        ("deploy", "ci/cd", "pipeline", "github actions", "workflow", "build fails"),
    ),
}


def match_persona(message: str) -> tuple[str, str] | None:
    """Score ``message`` against each persona's keywords (case-insensitive
    substring counts). Returns ``(persona_key, domain_label)`` for the
    highest scorer at or above :data:`MATCH_THRESHOLD`, or ``None`` if
    nothing clears it.
    """
    lowered = message.lower()
    best_persona: str | None = None
    best_domain = ""
    best_score = 0
    for persona, (domain, keywords) in PERSONA_DOMAINS.items():
        score = sum(1 for keyword in keywords if keyword in lowered)
        if score > best_score:
            best_score = score
            best_persona = persona
            best_domain = domain
    if best_persona is not None and best_score >= MATCH_THRESHOLD:
        return best_persona, best_domain
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_persona_match.py -v`
Expected: PASS (7 tests)

- [ ] **Step 5: Lint and type-check**

Run: `uv run ruff check sakthai tests && uv run mypy sakthai`
Expected: no errors

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/persona_match.py tests/test_persona_match.py
git commit -m "feat: add keyword-based persona domain matching"
```

---

### Task 2: Themed panel + chip in `ReplyStream`

**Files:**
- Modify: `sakthai/agent/chat.py:178-255` (the `ReplyStream` class and `make_token_renderer`)
- Test: `tests/test_chat.py` (append new tests near the existing `ReplyStream` tests at line ~117)

**Interfaces:**
- Consumes: `match_persona`'s return type `tuple[str, str] | None` (Task 1) — this task only accepts it as a parameter, does not call `match_persona` itself.
- Produces: `ReplyStream.__init__(console, persona, *, matched=None)` and `make_token_renderer(console, persona, *, matched=None)` — Task 3 calls `make_token_renderer` with a `matched` keyword argument.

- [ ] **Step 1: Write the failing tests**

Add to `tests/test_chat.py`, directly after `test_reply_stream_streams_inside_a_panel_in_a_terminal` (around line 127):

```python
def test_reply_stream_uses_matched_personas_theme_when_provided() -> None:
    console = Console(file=io.StringIO(), force_terminal=True, width=80)
    stream = chat_agent.make_token_renderer(
        console, "sakthai", matched=("sakjules", "CI/CD & automation")
    )
    stream("Hello")
    stream.close()
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "SakJules" in output
    assert "SakThai" not in output


def test_reply_stream_shows_a_matched_chip_on_the_final_panel() -> None:
    console = Console(file=io.StringIO(), force_terminal=True, width=80)
    stream = chat_agent.make_token_renderer(
        console, "sakthai", matched=("sakjules", "CI/CD & automation")
    )
    stream("Hello")
    stream.close()
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "best matched" in output
    assert "CI/CD & automation" in output


def test_reply_stream_without_a_match_keeps_todays_behavior() -> None:
    console = Console(file=io.StringIO(), force_terminal=True, width=80)
    stream = chat_agent.make_token_renderer(console, "sakthai")
    stream("Hello")
    stream.close()
    output = console.file.getvalue()  # type: ignore[union-attr]
    assert "SakThai" in output
    assert "best matched" not in output
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k "matched" -v`
Expected: FAIL with `TypeError: make_token_renderer() got an unexpected keyword argument 'matched'`

- [ ] **Step 3: Write the implementation**

In `sakthai/agent/chat.py`, add `chip` to the existing `from .ui import (...)` block (line 38-50) — insert alphabetically:

```python
from .ui import (
    chip,
    help_panel,
    input_frame_bottom,
    input_frame_top,
    memory_panel,
    persona_avatar,
    rainbow_rule,
    rainbow_sweep_line,
    skills_panel,
    status_bar,
    tools_panel,
    welcome_panel,
)
```

Replace `ReplyStream.__init__` (lines 178-186):

```python
    def __init__(
        self, console: Console, persona: str, *, matched: tuple[str, str] | None = None
    ) -> None:
        self._console = console
        display_persona = matched[0] if matched else persona
        self._label = PERSONA_LABELS.get(display_persona, display_persona)
        self._color = PERSONA_COLORS.get(display_persona, "white")
        self._avatar = persona_avatar(display_persona)
        self._match_domain = matched[1] if matched else None
        self._parts: list[str] = []
        self._live: Live | None = None
        self._started = False
```

Replace `_panel` (lines 208-222):

```python
    def _panel(self, body: RenderableType, *, streaming: bool = False) -> Panel:
        color = self._color
        title = f"[{color}]{self._avatar}[/{color}] [bold {color}]{self._label}[/bold {color}]"
        subtitle: RenderableType
        if streaming:
            subtitle = "[dim]▌ streaming…[/dim]"
        elif self._match_domain:
            subtitle = chip(
                f"best matched: {self._label} · {self._match_domain}",
                accent=self._color,
                glyph=self._avatar,
            )
        else:
            subtitle = f"[dim]{time.strftime('%H:%M')}[/dim]"
        return Panel(
            body,
            box=box.ROUNDED,
            title=title,
            title_align="left",
            subtitle=subtitle,
            subtitle_align="right",
            border_style=color,
        )
```

Replace `make_token_renderer` (lines 253-255):

```python
def make_token_renderer(
    console: Console, persona: str, *, matched: tuple[str, str] | None = None
) -> ReplyStream:
    """Build the ``on_token`` callback for ``run_agent`` that renders a reply."""
    return ReplyStream(console, persona, matched=matched)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -k "matched or reply_stream or token_renderer" -v`
Expected: PASS (all reply-stream and new matched tests green)

- [ ] **Step 5: Run the full test suite, lint, and type-check**

Run: `uv run pytest tests/ -q && uv run ruff check sakthai tests && uv run mypy sakthai`
Expected: all pass — this confirms the `matched=None` default didn't change any existing (non-matched) rendering.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/chat.py tests/test_chat.py
git commit -m "feat: theme reply panel and add chip for a matched persona"
```

---

### Task 3: Wire matching into the chat turn loop

**Files:**
- Modify: `sakthai/agent/chat.py:436-438` (inside `run_chat`)
- Test: `tests/test_chat.py` (append near the other `run_chat` integration tests, after `test_run_chat_threads_history_across_turns` around line 401)

**Interfaces:**
- Consumes: `match_persona` (Task 1, `sakthai.agent.persona_match`), `make_token_renderer(..., matched=...)` (Task 2).

- [ ] **Step 1: Write the failing tests**

**Correction:** an earlier version of this task tried to assert on rendered
console output, but `fake_run_agent` below never calls `on_token` — and
`ReplyStream.close()` renders `Text("")` (no panel at all) when no tokens
ever arrived (`sakthai/agent/chat.py`, `close()`: `Markdown("".join(self._parts))`
only happens `if self._parts`, otherwise it's blank). So no amount of
correct wiring could make "best matched" appear in captured output this
way — the test itself was unable to pass. Test the wiring directly instead:
monkeypatch `make_token_renderer` to capture the `matched` argument
`run_chat` passes it, which is exactly what this task is responsible for
(Task 2's own tests already cover that `ReplyStream` renders the chip
correctly given a `matched` value — this task only needs to prove
`run_chat` computes and forwards the right value).

Add to `tests/test_chat.py`:

```python
def test_run_chat_passes_the_matched_persona_to_the_token_renderer(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    captured: dict[str, Any] = {}

    def fake_make_token_renderer(
        console: Console, persona: str, *, matched: tuple[str, str] | None = None
    ) -> chat_agent.ReplyStream:
        captured["matched"] = matched
        return chat_agent.ReplyStream(console, persona, matched=matched)

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        return AgentResult(text="done", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    monkeypatch.setattr(chat_agent, "make_token_renderer", fake_make_token_renderer)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="claude-opus-4-8",
        provider="anthropic",
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["deploy the github actions pipeline", None]),
    )
    assert captured["matched"] == ("sakjules", "CI/CD & automation")


def test_run_chat_passes_no_match_for_an_ordinary_message(
    monkeypatch: pytest.MonkeyPatch, store: MemoryStore
) -> None:
    captured: dict[str, Any] = {}

    def fake_make_token_renderer(
        console: Console, persona: str, *, matched: tuple[str, str] | None = None
    ) -> chat_agent.ReplyStream:
        captured["matched"] = matched
        return chat_agent.ReplyStream(console, persona, matched=matched)

    def fake_run_agent(task: str, **kwargs: Any) -> AgentResult:
        return AgentResult(text="done", iterations=1, stop_reason="end_turn", messages=[])

    monkeypatch.setattr(chat_agent, "run_agent", fake_run_agent)
    monkeypatch.setattr(chat_agent, "make_token_renderer", fake_make_token_renderer)
    chat_agent.run_chat(
        persona="sakthai",
        soul_text="",
        tools=(),
        model="claude-opus-4-8",
        provider="anthropic",
        caveman=None,
        with_skills=(),
        store=store,
        console=_console(),
        read_input=_make_scripted_input(["what's the weather?", None]),
    )
    assert captured["matched"] is None
```

Both reuse the existing `_console()` helper (line 59) and `_make_scripted_input`
helper already defined in `tests/test_chat.py` — no new imports needed
beyond what the file already has (`Any` from `typing` is already imported).

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chat.py -k "passes_the_matched_persona or passes_no_match" -v`
Expected: `test_run_chat_passes_the_matched_persona_to_the_token_renderer` FAILs with
`AssertionError: assert None == ('sakjules', 'CI/CD & automation')` — before Step 3,
`run_chat` still calls `make_token_renderer(console, persona)` with no `matched` kwarg,
so the fake's default (`matched=None`) is what gets captured.
`test_run_chat_passes_no_match_for_an_ordinary_message` PASSes even before Step 3 (both
sides are `None`) — that's expected and fine; Step 4 re-confirms it stays passing after
the real wiring is in place, which is the test that actually matters for that case.

- [ ] **Step 3: Write the implementation**

In `sakthai/agent/chat.py`, add the import (near the other local imports at the top, alphabetically after `.loop`):

```python
from .loop import AgentError, run_agent
from .persona_match import match_persona
```

In `run_chat`, replace lines 437-438:

```python
        render_user_turn(console, user_text)
        reply = make_token_renderer(console, persona)
```

with:

```python
        render_user_turn(console, user_text)
        matched = match_persona(user_text)
        reply = make_token_renderer(console, persona, matched=matched)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chat.py -v`
Expected: PASS (full file, including the two new integration tests)

- [ ] **Step 5: Run the full suite, lint, and type-check**

Run: `uv run pytest tests/ -q && uv run ruff check sakthai tests && uv run ruff format --check sakthai tests && uv run mypy sakthai && uv run bandit -c pyproject.toml -r sakthai`
Expected: all pass. This is the same command set CI runs — confirms the feature is fully integrated and nothing regressed.

- [ ] **Step 6: Commit**

```bash
git add sakthai/agent/chat.py tests/test_chat.py
git commit -m "feat: match user messages to a persona domain each chat turn"
```

---

## Self-Review Notes

- **Spec coverage:** Section 1 (matcher) → Task 1. Section 2 (UI integration) → Tasks 2–3. Section 3 (testing) → a test file/additions in every task. "Out of scope" items (no other persona's SOUL.md, no SakTan, no LLM/embedding classification) are respected — nothing in this plan touches `personas/`, loads `SOUL.md`, or adds a dependency.
- **Placeholder scan:** none — every step has complete, exact code.
- **Type consistency:** `tuple[str, str] | None` is the return type of `match_persona` (Task 1) and the exact parameter type of `matched` in `ReplyStream.__init__`/`make_token_renderer` (Task 2) and the exact variable type assigned in `run_chat` (Task 3) — verified consistent across all three tasks.
