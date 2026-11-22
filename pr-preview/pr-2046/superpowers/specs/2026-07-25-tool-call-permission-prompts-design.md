# Tool-call permission prompts — design spec

Date: 2026-07-25

## Context

Second of three subsystems in the tool-call-transparency breakdown (see
`docs/superpowers/specs/2026-07-25-tool-call-live-state-design.md` for the
first, "live running state," which has an approved plan not yet built).
This one: require explicit approve/deny before a risky tool actually runs.

Scoped tools, per Beer's confirmation: `run_command` (shell execution),
`send_telegram_message` (external communication), `run_agent_loop` (spawns
a nested agent loop), and `forget` (destructively deletes memory). All four
are defined in `sakthai/agent/tools.py`.

**Existing extension point, and why this doesn't reuse it:** the agent loop
already has a pre-execution deny mechanism — `GuardrailPolicy.check_pre_execution`
(`sakthai/agent/guardrails.py:352-373`), used today to enforce
`SAKTHAI_SHELL_ALLOW` for `run_command`
(`_block_run_command_if_not_allowed`, `guardrails.py:47-54`). Its rules are
`PreGuardrailRule = Callable[[Tool, dict, MemoryStore], GuardrailResult]` —
deliberately pure, synchronous, I/O-free functions, so the whole guardrail
system stays testable without a console. An interactive approve/deny prompt
is inherently I/O. Bolting that onto a guardrail rule would break the
purity every other rule relies on and complicate testing all of them. This
spec adds a **parallel** gate instead — same shape and spirit as the
existing `notify`/`on_event` injectable-callback convention already used
throughout `sakthai/agent/loop.py`, not a replacement for guardrails. Both
gates run: guardrails first (cheap, no user interruption needed for things
that are going to be blocked anyway regardless of the answer), confirmation
second, only for tools that pass guardrails and are flagged as needing it.

## Goal

Before `run_command`, `send_telegram_message`, `run_agent_loop`, or
`forget` executes in the interactive `sakthai chat` REPL, the user sees the
tool name and arguments and must explicitly approve. Denying feeds the
model a clear "user denied" result instead of running the tool. `sakthai
run` and the MCP server are unaffected — no prompt, same behavior as today.

## Design

### 1. Tool metadata — `sakthai/agent/tools.py`

Add one field to the `Tool` dataclass (`tools.py:37-41`):

```python
@dataclass
class Tool:
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[[dict[str, Any], MemoryStore], str]
    requires_confirmation: bool = False
```

Set `requires_confirmation=True` on the four `Tool(...)` definitions for
`run_command`, `send_telegram_message`, `run_agent_loop`, and `forget`
(`tools.py:448-517`); leave the default `False` everywhere else. This
mirrors how `Tool` already carries per-tool metadata (`name`,
`description`) rather than maintaining a separate hardcoded name list
elsewhere — and means a plugin tool (CLAUDE.md documents "external plugins
may deliberately shadow built-ins") can declare itself as needing
confirmation too, which a hardcoded set couldn't support.

### 2. The gate — `sakthai/agent/loop.py`

Add one parameter to `_execute_tool_with_guardrails` (`loop.py:218-244`),
inserted after the existing pre-execution guardrail check and before
`_execute_tool` runs:

```python
def _execute_tool_with_guardrails(
    tool: Tool,
    args: dict[str, Any],
    store: MemoryStore,
    policy: GuardrailPolicy,
    on_confirm: Callable[[str, dict[str, Any]], bool] | None = None,
) -> tuple[str, bool]:
    pre_check_result = policy.check_pre_execution(tool, args, store)
    if pre_check_result.action == GuardrailAction.DENY:
        return (
            pre_check_result.reason
            or f"Tool '{tool.name}' was denied by a pre-execution guardrail.",
            True,
        )

    final_args = pre_check_result.modified_args or args

    if tool.requires_confirmation and on_confirm is not None:
        if not on_confirm(tool.name, final_args):
            return f"Tool '{tool.name}' was denied by the user.", True

    output, is_error = _execute_tool(tool, final_args, store)
    # ...unchanged post-execution guardrail check below
```

`on_confirm` threads through the same call chain `notify` already does —
`run_agent` → `_dispatch_tool_calls` → `_process_tool_uses` →
`_execute_tool_with_guardrails` — each function gaining one parameter of
type `Callable[[str, dict[str, Any]], bool] | None = None`, defaulting to
`None` at every level. `run_agent`'s public signature gains
`on_confirm: Callable[[str, dict[str, Any]], bool] | None = None`.
`on_confirm(tool_name, args) -> bool` intentionally mirrors `on_event`'s
`(str, dict[str, Any])` shape rather than passing the full `Tool` object —
keeps the callback's interface minimal and consistent with the existing
convention, and callers that only need name/args don't need to import
`Tool`.

Because the default is `None` everywhere, `sakthai run`
(`sakthai/cli/agent.py`) and the MCP server (`sakthai/mcp/server.py`) are
unaffected with zero changes — they simply never pass `on_confirm`, so
`tool.requires_confirmation and on_confirm is not None` is always `False`
for them, identical to today's behavior.

### 3. The interactive prompt — `sakthai/agent/chat.py` + `sakthai/cli/chat.py`

`run_chat` (`sakthai/agent/chat.py`) gains one new parameter, following the
exact same injection pattern its existing `read_input` parameter already
uses:

```python
confirm_tool: Callable[[str, dict[str, Any]], bool] | None = None,
```

passed straight through to `run_agent(..., on_confirm=confirm_tool)`
alongside the existing `on_event`/`on_token` wiring.

The real interactive implementation lives in `sakthai/cli/chat.py`,
alongside the existing `_make_read_input` factory (`cli/chat.py:86-107`),
following the same pattern:

```python
def _make_confirm_tool(persona: str) -> Callable[[str, dict[str, Any]], bool]:
    accent = theme.PERSONA_ACCENTS.get(persona, "cyan")

    def _confirm(name: str, args: dict[str, Any]) -> bool:
        console = Console()
        console.print(
            f"[bold {accent}]⚠ {name}[/bold {accent}] wants to run with: [dim]{args}[/dim]"
        )
        answer = console.input("[bold]Allow this? [y/N] [/bold]").strip().lower()
        return answer in ("y", "yes")

    return _confirm
```

Wired into the `chat()` command (`cli/chat.py:170-180`) alongside the
existing `read_input=_make_read_input(...)` argument:
`confirm_tool=_make_confirm_tool(persona)`.

Default-to-deny: any input other than exactly `y`/`yes` (including empty
Enter) denies. `run_chat`'s own tests inject a fake `confirm_tool`
(`lambda name, args: True/False`) rather than driving a real console
prompt — same pattern the existing `read_input=_make_scripted_input([...])`
tests already use.

## Out of scope

- `sakthai run` and the MCP server prompting interactively — architecturally
  they run unattended; no design is needed since `on_confirm=None` already
  means "no gate" for them.
- Remembering a user's choice ("always allow `run_command`" for the rest of
  the session) — YAGNI for this pass; every flagged call prompts.
- Per-tool custom prompt copy (e.g. a `run_command`-specific warning showing
  the exact shell command distinctly from a generic `send_telegram_message`
  warning) — the generic `name` + `args` display is enough for a first cut,
  consistent with how the live-running-state design also kept its running
  line generic rather than per-tool.
- Live running state (subsystem #1) and expandable output (subsystem #3) —
  separate specs.

## Testing

- `tests/test_agent_loop.py`: a test that a `requires_confirmation=True`
  tool with `on_confirm` returning `False` produces an `is_error=True`
  result containing "denied by the user" and never calls the tool's
  handler (assert via a fake `Tool` with a handler that raises if called,
  or a call-counting handler). A parallel test with `on_confirm` returning
  `True` confirms the tool executes normally. A third test confirms a
  `requires_confirmation=True` tool with `on_confirm=None` (the default)
  executes normally with no gate — this is the critical backward-compat
  case for `sakthai run`/MCP.
- `tests/test_agent_loop.py`: a test that a tool denied by
  `GuardrailPolicy.check_pre_execution` never reaches `on_confirm` at all
  (guardrails run first) — inject a spy `on_confirm` that raises if called,
  paired with a guardrail-denying policy.
- `tests/test_chat.py`: `run_chat` forwards a given `confirm_tool` through
  to `run_agent` as `on_confirm` — same monkeypatch-and-capture approach
  used for the persona-domain-match feature's Task 3 (capture the kwarg
  `run_agent` is called with, rather than trying to observe it through
  rendered console output).
- A CLI-level test for `_make_confirm_tool`'s real prompt behavior (`y`,
  `yes`, `n`, empty input, mixed case) using a monkeypatched
  `Console.input`.
