"""A client for the MCP Registry, and the supply-chain check it enables.

Before this there was no registry of any kind: no index, no ``.well-known``, no
search, no install-by-name. External servers were configured by hand-editing
six ``mcp.json`` files, and the only supply-chain control was an exact ``npx``
version pin enforced by ``tests/test_persona_security_config.py``. A pin stops
a *new* release running unreviewed. It does nothing about the release you
already pinned turning out to be malicious.

That is what this closes. Every entry the registry serves carries a status
under ``_meta["io.modelcontextprotocol.registry/official"]``:

``active``
    Normal.
``deprecated``
    The publisher has retired it.
``deleted``
    Removed under the registry's moderation policy — spam, malware, or
    otherwise. The registry runs OSV checks on publish and sweeps daily.

Incremental syncs return deleted entries too, precisely so a downstream
consumer learns about them. :func:`check_configured_servers` is the payoff:
``sakthai doctor`` can tell you that a server sitting in your manifest has
since been pulled upstream.

**Aggregators and subregistries.** The registry documentation expects
downstream consumers to copy the catalog on a regular but infrequent basis
(it suggests hourly) and add value — ratings, scanning, curation. One that also
implements the registry's own OpenAPI surface is a *subregistry*, and a client
can point at it unchanged. ``SAKTHAI_MCP_REGISTRY_URL`` is that pointer: aim it
at a private subregistry and the family discovers only what that subregistry
publishes. See ``docs/mcp-registry.md``.

Nothing here runs automatically. Sync is an explicit command, because reaching
the network during an agent run is exactly the property the test suite and the
sandbox defaults work to avoid.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .. import config

logger = logging.getLogger(__name__)

#: The API version this client speaks. The registry froze ``v0.1`` on
#: 2025-10-24, so the path is stable enough to hardcode; a subregistry
#: implementing the same spec serves the same path.
API_VERSION = "v0.1"

#: Where the registry puts its own metadata on each entry. Reverse-DNS with a
#: mandatory prefix, and prefixes whose second label is ``modelcontextprotocol``
#: are reserved for the specification — an aggregator adding its own fields
#: uses its own namespace, e.g. ``io.github.beer-sakthai/...``.
OFFICIAL_META_KEY = "io.modelcontextprotocol.registry/official"

#: Entries per page. The registry's own guidance is to page rather than ask for
#: everything at once.
DEFAULT_PAGE_SIZE = 100

#: Stop after this many pages. A registry that keeps handing back cursors would
#: otherwise loop forever.
MAX_PAGES = 200

STATUS_ACTIVE = "active"
STATUS_DEPRECATED = "deprecated"
STATUS_DELETED = "deleted"

#: Statuses that should stop a configured server from being used.
PROBLEM_STATUSES = frozenset({STATUS_DEPRECATED, STATUS_DELETED})


class RegistryError(RuntimeError):
    """The registry could not be reached, or answered with something unusable."""


@dataclass(frozen=True)
class RegistryServer:
    """One server as the registry describes it."""

    name: str
    description: str = ""
    version: str = ""
    status: str = STATUS_ACTIVE
    published_at: str = ""
    is_latest: bool = True
    #: Installable artifacts: ``registryType`` is npm / pypi / oci / nuget /
    #: cargo / mcpb, with the identifier and version alongside.
    packages: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    #: Remote endpoints, each with a ``type`` of ``streamable-http`` or ``sse``.
    remotes: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    website_url: str = ""
    repository_url: str = ""

    @property
    def is_problem(self) -> bool:
        """Whether this entry's status should stop it being used."""
        return self.status in PROBLEM_STATUSES

    def to_json(self) -> dict[str, Any]:
        """The cache-line form. Flat on purpose: the cache is ours, not theirs."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status,
            "publishedAt": self.published_at,
            "isLatest": self.is_latest,
            "packages": list(self.packages),
            "remotes": list(self.remotes),
            "websiteUrl": self.website_url,
            "repositoryUrl": self.repository_url,
        }

    @classmethod
    def from_cache(cls, row: dict[str, Any]) -> RegistryServer:
        return cls(
            name=str(row.get("name", "")),
            description=str(row.get("description", "")),
            version=str(row.get("version", "")),
            status=str(row.get("status", STATUS_ACTIVE)),
            published_at=str(row.get("publishedAt", "")),
            is_latest=bool(row.get("isLatest", True)),
            packages=tuple(row.get("packages") or ()),
            remotes=tuple(row.get("remotes") or ()),
            website_url=str(row.get("websiteUrl", "")),
            repository_url=str(row.get("repositoryUrl", "")),
        )


def parse_entry(entry: Any) -> RegistryServer | None:
    """One listing entry, or None if it is not usable.

    The registry nests the server under a ``server`` key with ``_meta`` as its
    *sibling*, not inside it — a shape that is easy to get wrong and silently
    lose every status with. A nameless entry is dropped: the name is the key
    everything else joins on.
    """
    if not isinstance(entry, dict):
        return None
    server = entry.get("server")
    if not isinstance(server, dict):
        return None
    name = server.get("name")
    if not isinstance(name, str) or not name:
        return None

    meta = entry.get("_meta")
    official = meta.get(OFFICIAL_META_KEY) if isinstance(meta, dict) else None
    official = official if isinstance(official, dict) else {}

    repository = server.get("repository")
    repository_url = ""
    if isinstance(repository, dict):
        repository_url = str(repository.get("url") or "")

    return RegistryServer(
        name=name,
        description=str(server.get("description") or ""),
        version=str(server.get("version") or ""),
        status=str(official.get("status") or STATUS_ACTIVE),
        published_at=str(official.get("publishedAt") or ""),
        is_latest=bool(official.get("isLatest", True)),
        packages=tuple(p for p in (server.get("packages") or []) if isinstance(p, dict)),
        remotes=tuple(r for r in (server.get("remotes") or []) if isinstance(r, dict)),
        website_url=str(server.get("websiteUrl") or ""),
        repository_url=repository_url,
    )


#: A function that GETs a URL with query params and returns the decoded JSON.
#: Injected so the sync logic is testable without a network or a mocked client.
Fetcher = Callable[[str, dict[str, Any]], dict[str, Any]]


def _httpx_fetcher(timeout: float) -> Fetcher:
    def fetch(url: str, params: dict[str, Any]) -> dict[str, Any]:
        import httpx

        try:
            response = httpx.get(
                url,
                params=params,
                timeout=timeout,
                follow_redirects=True,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            body = response.json()
        except Exception as exc:  # noqa: BLE001 — every failure is the same to us
            raise RegistryError(f"registry request to {url} failed: {exc}") from exc
        if not isinstance(body, dict):
            raise RegistryError(f"registry at {url} returned a non-object body")
        return body

    return fetch


def iter_servers(
    *,
    base_url: str | None = None,
    updated_since: str | None = None,
    page_size: int = DEFAULT_PAGE_SIZE,
    fetcher: Fetcher | None = None,
    timeout: float = 30.0,
) -> Iterator[RegistryServer]:
    """Every server the registry lists, following cursors.

    ``updated_since`` is an RFC 3339 timestamp; with it the registry returns
    only what changed, **including entries that became deleted**, which is how
    a moderation removal propagates downstream.

    The cursor is held across every page of one run rather than re-derived, and
    a repeated cursor stops the walk — the same guard the tool-list pagination
    needs, for the same reason.
    """
    url = f"{(base_url or config.mcp_registry_url()).rstrip('/')}/{API_VERSION}/servers"
    fetch = fetcher or _httpx_fetcher(timeout)
    cursor: str | None = None
    seen_cursors: set[str] = set()

    for _ in range(MAX_PAGES):
        params: dict[str, Any] = {"limit": page_size}
        if cursor:
            params["cursor"] = cursor
        if updated_since:
            params["updated_since"] = updated_since

        body = fetch(url, params)
        entries = body.get("servers")
        if isinstance(entries, list):
            for entry in entries:
                parsed = parse_entry(entry)
                if parsed is not None:
                    yield parsed

        metadata = body.get("metadata")
        next_cursor = metadata.get("nextCursor") if isinstance(metadata, dict) else None
        if not isinstance(next_cursor, str) or not next_cursor:
            return
        if next_cursor in seen_cursors:
            logger.warning("registry repeated cursor %r; stopping", next_cursor)
            return
        seen_cursors.add(next_cursor)
        cursor = next_cursor
    else:
        logger.warning("registry paginated past %d pages; truncating", MAX_PAGES)


def write_cache(servers: Iterable[RegistryServer], path: Path | None = None) -> int:
    """Replace the local cache with ``servers``. Returns how many were written.

    Written whole rather than merged: a full sync is the only way to learn that
    an entry *disappeared* rather than changed, and the file is small enough
    that incremental merging would buy nothing but a chance to corrupt it.
    """
    target = path or config.registry_cache_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    tmp = target.with_suffix(target.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        for server in servers:
            handle.write(json.dumps(server.to_json(), ensure_ascii=False) + "\n")
            count += 1
    tmp.replace(target)  # atomic, so a failed sync cannot leave a half file
    return count


def read_cache(path: Path | None = None) -> list[RegistryServer]:
    """The cached listing, or an empty list when there is none.

    A malformed line is skipped rather than fatal: the cache is a convenience,
    and refusing to answer at all because one row is bad would be worse than
    answering from the rest.
    """
    source = path or config.registry_cache_path()
    if not source.is_file():
        return []
    out: list[RegistryServer] = []
    try:
        text = source.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("could not read registry cache %s: %s", source, exc)
        return []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("skipping malformed registry cache line in %s", source)
            continue
        if isinstance(row, dict):
            out.append(RegistryServer.from_cache(row))
    return out


def sync(
    *,
    base_url: str | None = None,
    updated_since: str | None = None,
    path: Path | None = None,
    fetcher: Fetcher | None = None,
    timeout: float = 30.0,
) -> int:
    """Fetch the registry and replace the local cache. Returns the count."""
    servers = list(
        iter_servers(
            base_url=base_url,
            updated_since=updated_since,
            fetcher=fetcher,
            timeout=timeout,
        )
    )
    return write_cache(servers, path)


def search(
    query: str,
    *,
    servers: list[RegistryServer] | None = None,
    limit: int = 20,
    include_problems: bool = False,
) -> list[RegistryServer]:
    """Cached entries whose name or description contains ``query``.

    Deprecated and deleted entries are excluded unless asked for: the point of
    search is to find something to install, and offering a withdrawn server as
    a candidate is the opposite of what this module is for.
    """
    rows = servers if servers is not None else read_cache()
    needle = query.strip().lower()
    hits = [
        s
        for s in rows
        if (include_problems or not s.is_problem)
        and (not needle or needle in s.name.lower() or needle in s.description.lower())
    ]
    hits.sort(key=lambda s: s.name)
    return hits[:limit] if limit > 0 else hits


def check_configured_servers(
    configured_names: Iterable[str],
    *,
    servers: list[RegistryServer] | None = None,
) -> list[tuple[str, RegistryServer]]:
    """Configured servers the registry marks deprecated or deleted.

    Returns ``(configured_name, entry)`` pairs. This is the supply-chain check
    an exact version pin cannot perform: the pin stops an unreviewed *new*
    release, while this catches the release you already pinned being withdrawn.

    Matching is by exact registry name, then by the last path segment of one.
    Local names are chosen by whoever wrote the manifest and need not match the
    registry's namespaced ``io.github.owner/repo`` form, so a bare ``playwright``
    is still matched against ``io.github.microsoft/playwright``. A near-miss is
    reported rather than ignored; a false positive here costs a glance, a false
    negative costs the warning entirely.
    """
    rows = servers if servers is not None else read_cache()
    problems = {s.name: s for s in rows if s.is_problem}
    by_tail: dict[str, RegistryServer] = {}
    for full_name, entry in problems.items():
        by_tail.setdefault(full_name.rsplit("/", 1)[-1].lower(), entry)

    found: list[tuple[str, RegistryServer]] = []
    for name in configured_names:
        match = problems.get(name) or by_tail.get(name.lower())
        if match is not None:
            found.append((name, match))
    return found
