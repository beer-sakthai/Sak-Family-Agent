# Built-in MCP servers

Four MCP servers ship **in code**, not in any `mcp.json`. They are defined by
factory functions in [`personas/sakthai/mcp/servers.py`](../personas/sakthai/mcp/servers.py)
and registered in `BUILTIN_SERVER_FACTORIES`, so they travel with the package
and need no per-user configuration file. This page is their reference: what each
one is, which persona loads which, how they are resolved and gated at startup,
and the one behavior that surprises people — the agent loads a different set
than `sakthai mcp list` shows by default.

For *external* servers you configure yourself in `~/.sakthai/mcp.json`, see
[`plugins.md`](plugins.md). For the transports and namespacing rules that apply
to every server (built-in or not), see [`plugins.md`](plugins.md) and
[`mcp-support-matrix.md`](mcp-support-matrix.md).

## The four servers

| Server | Transport | Endpoint / command | Credential (env) |
|---|---|---|---|
| `genkit` | stdio | `npx -y genkit@1.44.0 mcp` | — (opt-in; see the gate below) |
| `google_dev_knowledge` | streamable-http | `https://developerknowledge.googleapis.com/mcp`, header `x-goog-api-key` | `GOOGLE_API_KEY` or `GEMINI_API_KEY` |
| `figma` | streamable-http | `https://mcp.figma.com/mcp`, headers `Authorization: Bearer` + `X-Figma-Token` | `FIGMA_ACCESS_TOKEN` or `FIGMA_TOKEN` |
| `huggingface` | streamable-http | `https://huggingface.co/mcp?login&gradio=none`, header `Authorization: Bearer` | `HF_TOKEN` |

Two details that look like mistakes and are not:

- **`genkit` is pinned to an exact version** (`genkit@1.44.0`). A bare
  `npx -y genkit` runs whatever npm published most recently, on every launch,
  with no review — the supply-chain hole that `_PINNED_NPM_SPEC` in
  `tests/test_persona_security_config.py` exists to forbid. Bump it like any
  other dependency, never unpin it.
- **`figma` sends the token under two headers** (`Authorization` *and*
  `X-Figma-Token`). Both ride the same request to the same host, so the exposure
  is identical, while `X-Figma-Token` is Figma's own API convention. Dropping
  either risks breaking the integration to save nothing — leave both unless you
  have confirmed which the endpoint reads.

`google_dev_knowledge` additionally contributes a set of domain-scoped search
tools (`create_scoped_google_dev_tools`), scoped to `GOOGLE_DEV_DOMAINS`
(`developer.chrome.com`, `web.dev`, `developers.google.com`, `antigravity.google`,
`adk.dev`), alongside the raw tools the remote server advertises.

## Per-persona loadout

`PERSONA_DEFAULT_MCP_SERVERS` decides which built-ins a persona loads. A persona
not in the map — or no persona at all — loads **all four**.

| Persona | Built-ins |
|---|---|
| SakThai | `huggingface` |
| SakSee | `figma`, `google_dev_knowledge` |
| SakJules | `genkit`, `google_dev_knowledge` |
| SakKing | `genkit`, `google_dev_knowledge` |
| SakSit | `huggingface`, `figma` |
| SakTan | `genkit` |

## How they are resolved and loaded

`get_builtin_mcp_servers(persona)` returns the persona's loadout (or all four).
`load_server_specs(persona, include_builtins=...)` then places the built-ins at
**tier 0 — the lowest precedence** — so a server of the same name defined in
`~/.sakthai/mcp.json`, a persona config, or `SAKTHAI_MCP_CONFIG` overrides the
built-in. Built-ins are included only when `include_builtins=True` is passed or
`SAKTHAI_ENABLE_BUILTIN_MCP=1` is set.

At startup `connect_servers` ([`manager.py`](../personas/sakthai/mcp/manager.py))
walks each resolved spec and **fails soft** — any server that does not pass a
gate is logged and skipped, and the agent loop continues with the rest. The
gates, in order:

1. **Validation** — `MCPServerValidator` rejects an unsafe spec (a dangerous
   argv, a non-HTTPS URL, and under `strict` security level an unapproved name).
   See [`mcp-threat-model.md`](mcp-threat-model.md).
2. **Remote credential gate** — for `figma`, `huggingface` and
   `google_dev_knowledge`, `RemoteMCPClient.is_configured()` returns false when
   the token env var is unset, so a tokenless persona is skipped **before any
   network I/O**. It never dials the endpoint.
3. **`npx`/`node`/`npm` on PATH** — a stdio server whose command is missing from
   PATH is skipped.
4. **The `genkit` environment gate** — `genkit` is skipped unless one of
   `SAKTHAI_ENABLE_GENKIT`, `GENKIT_ENV`, `GENKIT_PROJECT_ID`, or
   `FIREBASE_PROJECT_ID` is set. It is the one built-in that is opt-in even when
   its binary is available, because `npx genkit mcp` is a developer tool, not
   something to spawn on every run.

## The surprising bit: `sakthai run` loads more than `sakthai mcp list` shows

`sakthai run` and `sakthai chat` pass `include_builtins=True` **unconditionally**
— every agent run gets the persona's built-ins. But the three inspection
commands, `sakthai mcp list`, `mcp ping`, and `mcp tools`, default to
`--no-builtins`. So the inspector shows a *different, smaller* set than the agent
actually loads, unless you ask for them:

```bash
sakthai mcp list --builtins                 # include built-ins for the current persona
sakthai mcp list --builtins --persona sakjules   # …for a specific persona's loadout
```

This is deliberate — the inspection commands report your *configured* servers by
default — but it means "it's not in `mcp list`" is not evidence that the agent
isn't loading it. Use `--builtins` (or `SAKTHAI_ENABLE_BUILTIN_MCP=1`) to see the
set the agent sees. Remote servers still skip without their token, and `genkit`
still skips without its env gate, so an empty or partial list is expected when
credentials are absent.

## Security posture

Because these servers are defined in Python rather than in a JSON manifest, they
were once invisible to the review invariants that guard the manifest files. Since
the reconciliation in #2062 they are folded into the same four checks in
`tests/test_persona_security_config.py`, which now cover every server the
repository ships, whichever source defined it:

- every remote URL is HTTPS;
- every host is on the reviewed `_ALLOWED_MCP_HOSTS` allowlist;
- every `npx` spec is pinned to an exact version;
- no header carries a literal credential (the token comes from `os.getenv` at
  construction, so an unset env var yields no header at all).

See [`mcp-threat-model.md`](mcp-threat-model.md) for the attack flows these
checks close.
