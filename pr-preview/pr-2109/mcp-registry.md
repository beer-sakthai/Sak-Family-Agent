# MCP registry aggregators

How this package discovers published MCP servers, how it could publish its own,
and why the registry's status field is the most useful thing in it.

## The shape of the ecosystem

```
   registry.modelcontextprotocol.io          the official registry
   (metadata only — it hosts nothing)        source of record
                   │
                   │  downstream copies, "on a regular but infrequent
                   │  basis (e.g. once per hour)"
                   ▼
   ┌───────────────────────────────┐
   │ aggregators                   │  add ratings, security scanning,
   │  marketplaces, directories    │  install counts, curation
   └───────────────────────────────┘
                   │
                   │  an aggregator that ALSO implements the registry's
                   │  own OpenAPI surface is a SUBREGISTRY
                   ▼
   ┌───────────────────────────────┐
   │ subregistries                 │  public: client-specific marketplaces
   │  (same API, different data)   │  private: an org's curated allow-list
   └───────────────────────────────┘
                   │
                   ▼
            sakthai mcp registry sync
```

The distinction that matters: an **aggregator** consumes the registry and
presents it however it likes. A **subregistry** consumes it and re-serves it
through the *same* API, so any client — this one included — can be pointed at
it with a URL change and nothing else.

That is the whole curation story. `SAKTHAI_MCP_REGISTRY_URL` aims this client
at a subregistry, and the family then discovers exactly what that subregistry
publishes.

## What the client does

```bash
sakthai mcp registry sync              # fetch and cache the catalog
sakthai mcp registry sync --since 2026-11-01T00:00:00Z   # only what changed
sakthai mcp registry search qdrant     # search the cache
sakthai mcp registry check             # audit configured servers, exit 1 on a problem
```

Implementation: [`personas/sakthai/mcp/registry.py`](../personas/sakthai/mcp/registry.py).

- `GET {base}/v0.1/servers` with `limit`, `cursor` and `updated_since`.
  Pagination is cursor-based: the response carries `metadata.nextCursor`, and
  the client follows it to the end, stopping on a repeated cursor or a page
  budget.
- The cache is `~/.sakthai/registry/servers.jsonl`, written whole and
  atomically. Whole rather than merged, because a full sync is the only way to
  learn an entry *disappeared*; atomically, so a failed sync cannot leave half
  a file.
- Nothing syncs automatically. It is an explicit command. Reaching the network
  during an agent run is precisely the property the test suite and the sandbox
  defaults work to preserve.

### The entry shape, and the easy mistake

The registry nests the server under a `server` key with `_meta` as its
**sibling**, not inside it:

```json
{
  "servers": [
    {
      "server": { "name": "io.modelcontextprotocol/filesystem",
                  "description": "…", "version": "1.0.2" },
      "_meta": { "io.modelcontextprotocol.registry/official":
                 { "status": "active", "publishedAt": "…", "isLatest": true } }
    }
  ],
  "metadata": { "count": 10, "nextCursor": "com.example/my-server:1.0.0" }
}
```

Reading `_meta` from inside `server` parses without error and silently loses
every status — which is the one field worth having. `parse_entry` handles the
real shape and `tests/test_mcp_registry.py` pins it.

`_meta` keys are reverse-DNS with a mandatory prefix. Any prefix whose second
label is `modelcontextprotocol` or `mcp` is reserved for the specification, so
`io.modelcontextprotocol.registry/official` is theirs; an aggregator adding
fields of its own uses its own namespace.

## Why this is a security feature, not a convenience

The family's manifests pin every `npx` server to an exact version, enforced by
`tests/test_persona_security_config.py`:

```json
"playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@0.0.83"] }
```

A pin answers one question: *will a new release run without review?* No.

It does not answer the other: *is the release I pinned still safe?* A package
can be found to be malicious after you pin it. The pin then guarantees you keep
running the bad version.

The registry answers that one. Every entry carries a status:

| Status | Meaning |
|---|---|
| `active` | Normal. |
| `deprecated` | The publisher has retired it. |
| `deleted` | Removed under the registry's moderation policy — spam, malware, illegal content. The registry runs OSV checks on publish and sweeps daily. |

Incremental `updated_since` syncs return deleted entries *precisely so*
downstream consumers learn about them. So:

```console
$ sakthai mcp registry check
1 configured server(s) withdrawn upstream:
  • backdoor matches io.github.evil/backdoor — deleted
$ echo $?
1
```

Non-zero, so it gates a deploy. `sakthai doctor` reports the same thing in its
own section, and stays quiet when there is no cache — syncing is a choice, and
nagging about an unused feature is noise.

**Name matching is deliberately loose.** Local names in `mcp.json` are whatever
the operator wrote and need not match the registry's namespaced
`io.github.owner/repo` form, so a bare `backdoor` is still matched against
`io.github.evil/backdoor` by its last path segment. A false positive costs a
glance; a false negative costs the warning entirely.

**What it is not.** The registry is a preview index, not a vetted list.
`active` means nobody has reported it, not that anyone has reviewed it. This
narrows the window on a known-bad package; it does not vouch for an unknown
one. The version pin, the `spec.tools` allowlist and
`SAKTHAI_MCP_SECURITY_LEVEL=strict` all still do their own jobs.

## Publishing this server

[`server.json`](../server.json) is the manifest, naming
`io.github.beer-sakthai/sak-family-agent` with a `pypi` package and a `stdio`
transport.

**Committing it publishes nothing.** The registry does not accept publications
by pull request or by finding a file in a repository. Publication goes through
the `mcp-publisher` CLI, and the `io.github.<owner>/…` namespace is proved by
either logging in as that GitHub user or running the publish from a GitHub
Action on one of their repositories (OIDC). A domain-based namespace
(`me.example/…`) is proved by a DNS or HTTP challenge instead.

So publishing is a deliberate act, requiring credentials this repository does
not hold. The manifest is committed so that act is a single command rather than
a reconstruction job.

## Running a private subregistry

Supported upstream — the registry ships a container image and takes its own
PostgreSQL — and almost certainly more than this family needs. The useful half
is available without it: point `SAKTHAI_MCP_REGISTRY_URL` at any service
implementing the same API, or simply curate the synced cache and
`SAKTHAI_APPROVED_MCP` by hand.

The remaining duplication worth fixing is closer to home: the three remote docs
servers are copy-pasted verbatim into all six persona manifests with no
inheritance, because `personas/shared/config/` has no `mcp.json`. A shared base
plus per-persona overlays is tracked in [`mcp-roadmap.md`](mcp-roadmap.md).
