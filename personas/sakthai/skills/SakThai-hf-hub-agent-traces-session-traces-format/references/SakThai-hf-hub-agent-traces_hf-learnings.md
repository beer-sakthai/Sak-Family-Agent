# HF Learnings: hf-hub-agent-traces-deep-dive-v2

**Date:** 2026-07-25
**Topic:** Deep-dive v2 — the `huggingface_hub` harness detection internals, the Hub API registry, and the complete agent trace ecosystem from the client implementation side.

## Summary

This deep-dive goes beyond the public docs to cover the actual Python client implementation that detects which agent harness is running (`huggingface_hub.utils._detect_agent`), the live `{ENDPOINT}/api/agent-harnesses` registry served by the Hub, the caching and fallback system, and the complete list of 25 registered harnesses as of July 2026 with their detection strategies.

---

## 1. Harness Detection: The Client-Side Implementation

The public HF docs describe the harness registry as a TypeScript file in `@huggingface/tasks`. **The actual implementation is now a server-side API consumed by the Python client.**

### 1.1 Entry Point: `detect_agent()`

File: `huggingface_hub/utils/_detect_agent.py` (204 lines)

```python
def detect_agent() -> Optional[str]:
    """Return the id of the detected AI agent harness or `None`."""
```

The function:
1. Loads the registry (from cache or Hub API)
2. Iterates through each harness, checking custom `envVars` first
3. Falls back to matching `standardEnvVars` (`AI_AGENT` and `AGENT`) against harness IDs
4. If a standard var is set but matches nothing known, returns `"unknown"`
5. Returns `None` when no agent is detected at all

### 1.2 Two-Step Match Strategy

**Step 1 — Custom env vars per harness:**
For each harness, if it defines `envVars`, those are checked first. The `_env_vars_match()` function supports two patterns:
- `"*"` — the variable is set to any non-empty value
- `"<exact_value>"` — the variable must equal this exact string

```python
def _env_vars_match(env_vars: dict[str, str]) -> bool:
    for var, pattern in env_vars.items():
        value = os.environ.get(var)
        if not value:
            continue
        if pattern == "*":
            return True
        if value == pattern:
            return True
    return False
```

**Step 2 — Standard universal vars:**
`AI_AGENT` and `AGENT` are treated as a universal standard — any agent can set its harness id here. If the value matches a registered harness id (case-insensitive), that harness is returned.

### 1.3 Registry Loading: 3-Tier Fallback

```python
def _load_registry() -> Registry:
```

1. **Fresh cache** — reads `~/.cache/huggingface/.agent_harnesses.json` if modified within the last 24 hours
2. **Hub fetch** — hits `{ENDPOINT}/api/agent-harnesses` with a 3-second timeout; persists result to cache
3. **Stale cache** — if fetch fails, reuses any cached copy regardless of age
4. **Empty fallback** — if nothing is available, returns `{"standardEnvVars": [], "harnesses": {}}` (no detection)

Critical design properties:
- **Best-effort only:** Timeout is 3 seconds. Any exception is swallowed. Detection must never make a process fail.
- **No hardcoded list:** The client ships with zero built-in harnesses. Everything comes from the API.
- **Graceful degradation:** Offline or unreachable Hub → empty registry → `detect_agent()` returns `None`
- **In-process cache:** The loaded registry is cached in a module-level `_registry` variable so repeated calls don't re-read the file

### 1.4 The `is_agent()` Convenience

```python
def is_agent() -> bool:
    return detect_agent() is not None
```

Simple boolean wrapper used by other parts of `huggingface_hub` to adjust behaviour when running inside an agent (e.g., modifying the user-agent header).

### 1.5 Cache File Location

Defined in `huggingface_hub/constants.py`:
```python
AGENT_HARNESSES_PATH = os.path.join(HF_HOME, ".agent_harnesses.json")
```
Typically resolves to `~/.cache/huggingface/.agent_harnesses.json`.

**TTL:** 24 hours (`_REGISTRY_TTL_SECONDS = 24 * 3600`)

---

## 2. The Live Registry: 25 Registered Harnesses

Fetched from `https://huggingface.co/api/agent-harnesses`. The registry has two top-level sections:

### 2.1 Standard Env Vars

```json
"standardEnvVars": ["AI_AGENT", "AGENT"]
```

Any agent can set `AI_AGENT=my-harness-id` or `AGENT=my-harness-id` and be recognized immediately — no registration needed for basic attribution.

### 2.2 Complete Harness List (2026-07-25)

| Harness ID | Pretty Label | Env Vars Detected | Notes |
|---|---|---|---|
| `antigravity` | Antigravity | `ANTIGRAVITY_AGENT` | Google's Gemini-based agentic dev platform |
| `augment-cli` | Augment CLI | `AUGMENT_AGENT` | Auggie from Augment Code |
| `cline` | Cline | `CLINE_ACTIVE` | Open-source VS Code coding agent |
| `cowork` | Cowork | `CLAUDE_CODE_IS_COWORK` | Anthropic's autonomous knowledge work agent on top of Claude Code |
| `claude-code` | Claude Code | `CLAUDECODE`, `CLAUDE_CODE` | Anthropic's terminal agentic coding tool |
| `codex` | Codex | `CODEX_SANDBOX`, `CODEX_CI`, `CODEX_THREAD_ID` | OpenAI's lightweight terminal coding agent |
| `crush` | Crush | `CRUSH` | Charm's open-source terminal agent |
| `gemini-cli` | Gemini CLI | `GEMINI_CLI` | Google's Gemini-powered terminal agent |
| `github-copilot` | GitHub Copilot | `COPILOT_MODEL`, `COPILOT_ALLOW_ALL`, `COPILOT_GITHUB_TOKEN` | GitHub's AI coding assistant |
| `goose` | Goose | `GOOSE_TERMINAL` | Open-source extensible agent (Block/Agentic AI Foundation) |
| `hermes-agent` | Hermes Agent | `HERMES_SESSION_ID` | Nous Research's self-improving multi-provider agent |
| `hi` | hi | (none — matched by standard vars only) | Rust terminal coding agent from Pipe Network |
| `kilo-code` | Kilo Code | `KILOCODE_FEATURE` | Open-source VS Code/JetBrains/terminal agent |
| `kiro` | Kiro | `AGENT_CONTEXT_OUT` | AWS's agentic IDE for spec-driven development |
| `openclaw` | OpenClaw | `OPENCLAW_SHELL` | Self-hosted personal AI assistant |
| `opencode` | opencode | `OPENCODE_CLIENT` | Open-source terminal coding agent |
| `pi` | Pi | `PI_CODING_AGENT` | Minimal self-extensible terminal agent |
| `replit` | Replit | `REPL_ID` | Cloud dev environment with AI agent |
| `trae` | Trae | `TRAE_AI_SHELL_ID` | ByteDance's AI-powered IDE |
| `vtcode` | VTCode | `VTCODE=1` (exact match) | Rust coding agent with sandboxing |
| `warp` | Warp | `TERM_PROGRAM=WarpTerminal` (exact match) | AI-powered terminal |
| `zed` | Zed | `ZED_TERM` | High-performance code editor with AI panel |
| `cursor-cli` | Cursor CLI | `CURSOR_AGENT` | Cursor's CLI coding agent |
| `cursor` | Cursor | `CURSOR_TRACE_ID` | AI-powered code editor |
| `devin` | Devin | (none — standard vars only) | Autonomous AI software engineer from Cognition |

**Key pattern observations:**
- 22 of 25 harnesses use custom env var detection (with `"*"` wildcard pattern)
- 2 harnesses (`vtcode`, `warp`) use exact value matching
- 2 harnesses (`hi`, `devin`) have no custom env vars — they rely on `AI_AGENT`/`AGENT` standard vars
- Codex has the most env vars (3): `CODEX_SANDBOX`, `CODEX_CI`, `CODEX_THREAD_ID`
- The `envVars` field is optional — when absent, only standard var matching applies

### 2.3 Harness Info Schema

```typescript
interface HarnessInfo {
  prettyLabel?: string;    // Display name in UI
  repoUrl?: string;        // Source code repository
  docsUrl?: string;        // Documentation URL
  description?: string;    // One-line description
  envVars?: Record<string, string>;  // Env var name -> match pattern
}
```

The `envVars` patterns:
- `"*"` — Match if env var is set to any non-empty value (most common)
- `"exact_string"` — Match if env var equals this exactly (e.g., `"WarpTerminal"`, `"1"`)

---

## 3. How the Registry Differs from Earlier Documentation

| Old Docs (TypeScript file) | Current Implementation (Hub API) |
|---|---|
| Harnesses defined in `@huggingface/tasks` TypeScript file | Served from `{ENDPOINT}/api/agent-harnesses` |
| User-agent-based attribution | Environment variable detection |
| Manual PR to add harness | API is updated server-side |
| Registry shipped with client | Registry fetched live, cached 24h |
| PR-based rendering per harness | Server-side icon/label rendering |

The client-side detection code was added to `huggingface_hub` in 2026 (copyright 2026 in the source). This replaced the older PR-based TypeScript approach.

---

## 4. The `hf skills add` Connection

When the `hf` CLI runs inside a detected agent, `detect_agent()` identifies which harness is active. The CLI uses this to:
- Attribute Hub API traffic to the correct harness via the user-agent header
- Customize certain CLI behaviours (e.g., `hf skills add` installs the right skill set for the active agent)
- Enable agent-specific onboarding flows

The agent skills themselves are distinct from harness detection: skills provide task-specific guidance to agents, while harness detection identifies *which* agent is running.

---

## 5. Practical Implications for Custom Harness Builders

To register a new harness today:

1. **Short-term (instant):** Set `AI_AGENT=my-harness-id` in your agent's environment. The `huggingface_hub` client will detect it. The Hub trace viewer will attribute your sessions to `my-harness-id` but without a branded icon/label.

2. **Full registration:** Open an issue or PR to add your harness to the server-side registry at `@huggingface/tasks`. Once merged:
   - Your env var pattern is added as a custom detection rule
   - A `prettyLabel`, icon, and description are assigned
   - Your sessions render with branding in the trace viewer
   - Traffic from your harness appears in the monthly agent usage dataset

3. **Detection criteria for registration:**
   - Choose a unique env var your agent sets **reliably** in every session
   - Prefer `"*"` pattern (any non-empty value) unless you need exact match
   - Provide `prettyLabel`, repo URL, docs URL, and a one-line description

---

## 6. Architecture Diagram

```
Agent process (Claude Code, Codex, Pi, ...)
        │
        │ Sets env vars (CLAUDECODE, CODEX_SANDBOX, PI_CODING_AGENT, ...)
        │
        ▼
huggingface_hub client
        │
        ├─ detect_agent()
        │    ├─ _get_registry()
        │    │    ├─ Cache fresh? (24h TTL) → Return cached
        │    │    ├─ Fetch from /api/agent-harnesses → Cache & return
        │    │    └─ Hub unreachable? → Use stale cache → Empty
        │    │
        │    ├─ Match custom envVars per harness
        │    ├─ Match standard vars (AI_AGENT, AGENT)
        │    └─ Return harness_id | "unknown" | None
        │
        ├─ Sends harness_id in User-Agent on all Hub API calls
        └─ Enables agent-specific Hub features (skills, traces, etc.)
                │
                ▼
        Hub trace viewer renders STS-format .jsonl
        with branded icon & label per harness_id
```

---

## 7. Key Code Snippets for Implementation Reference

### Registering your harness in a Python agent

```python
import os

# Simplest approach — set the standard env var
os.environ["AI_AGENT"] = "my-custom-agent"

# The hf CLI and huggingface_hub will now detect your agent
```

### Reading the registry directly

```python
from huggingface_hub.utils._detect_agent import _fetch_registry

registry = _fetch_registry()
if registry:
    print(f"Standard vars: {registry['standardEnvVars']}")
    for hid, info in registry['harnesses'].items():
        print(f"  {hid}: {info.get('prettyLabel')}")
```

### Checking if running inside an agent (Python)

```python
from huggingface_hub.utils._detect_agent import is_agent, detect_agent

if is_agent():
    harness = detect_agent()
    print(f"Running inside: {harness}")
```

---

## 8. Key Differences from Existing Coverage v1

| Aspect | v1 Coverage | v2 Deep-Dive |
|---|---|---|
| Harness detection | Mentioned as TypeScript file + PR | Full client implementation (`_detect_agent.py`) |
| Registry source | `@huggingface/tasks` on GitHub | `{ENDPOINT}/api/agent-harnesses` with caching |
| Caching mechanism | Not covered | 24h TTL, 3-tier fallback, in-process cache |
| Env var patterns | Not covered | `"*"` wildcard and exact match documented |
| Known harnesses | Only `llama.app` mentioned | All 25 harnesses with their exact detection env vars |
| `detect_agent()` | Not covered | Full source code analysis |
| Registration path | "open a PR" | Two-tier: instant via env var, branded via registry |
| Agent identification | User-agent based | Env var based with two-step matching |

---

## References

- Source: `huggingface_hub/utils/_detect_agent.py` (2026 copyright)
- Source: `huggingface_hub/constants.py` (AGENT_HARNESSES_PATH)
- Live registry: `https://huggingface.co/api/agent-harnesses`
- Cached at: `~/.cache/huggingface/.agent_harnesses.json` (24h TTL)
- HF Hub Docs: [Agent Traces](https://huggingface.co/docs/hub/en/agent-traces)
- HF Hub Docs: [Session Traces Format](https://huggingface.co/docs/hub/en/session-traces-format)
- HF Hub Docs: [Agents Overview](https://huggingface.co/docs/hub/en/agents-overview)
- Public Trace Example: [TeichAI/DeepSeek-v4-Pro-Agent](https://huggingface.co/datasets/TeichAI/DeepSeek-v4-Pro-Agent)
