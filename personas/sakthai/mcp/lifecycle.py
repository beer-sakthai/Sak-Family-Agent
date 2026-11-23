"""Feature lifecycle and deprecation for this package's MCP surface.

Nothing in the repository had any deprecation machinery: no
``DeprecationWarning``, no ``warnings.warn``, no sunset dates, no feature flags.
The single precedent is model-name deprecation in
``agent/providers/gemini_provider.py`` — a legacy-to-modern map plus a
``logger.warning`` that substitutes silently. This generalises that, because an
MCP surface has configuration *other people wrote* pointing at it, and quietly
changing what a name means is how you break someone else's manifest.

The model is the specification's own (SEP-2596): a feature is **Active**,
**Deprecated**, or **Removed**, a deprecation runs for at least twelve months
before removal, and the set of deprecated features is published rather than
left in release notes. ``docs/mcp-deprecations.md`` is generated from
:data:`FEATURE_STATES` by ``scripts/gen_mcp_docs.py``, and a test fails if the
two disagree.

Deprecating something here does **not** change behavior. It records the
intent, warns the operator once, and names the replacement and the earliest
date the behavior may be withdrawn.
"""

from __future__ import annotations

import datetime as _dt
import logging
import warnings
from dataclasses import dataclass
from enum import StrEnum

logger = logging.getLogger(__name__)

#: Minimum notice between deprecating a feature and removing it, per SEP-2596.
#: Checked by a test against every entry's ``removal_not_before``.
MIN_DEPRECATION_DAYS = 365


class FeatureState(StrEnum):
    """Where a feature sits in its lifecycle."""

    ACTIVE = "active"
    DEPRECATED = "deprecated"
    REMOVED = "removed"


@dataclass(frozen=True)
class Feature:
    """One entry in the deprecation registry.

    ``deprecated_since`` and ``removal_not_before`` are ISO dates. The gap
    between them is the notice period, and a test asserts it is at least
    :data:`MIN_DEPRECATION_DAYS` — the point of writing the dates down rather
    than carrying them in someone's head.
    """

    id: str
    state: FeatureState
    summary: str
    #: Why it is going away, in a sentence an operator can act on.
    rationale: str = ""
    replacement: str = ""
    deprecated_since: str = ""
    removal_not_before: str = ""

    @property
    def notice_days(self) -> int | None:
        """Days of notice given, or None when either date is absent."""
        if not self.deprecated_since or not self.removal_not_before:
            return None
        start = _dt.date.fromisoformat(self.deprecated_since)
        end = _dt.date.fromisoformat(self.removal_not_before)
        return (end - start).days


#: The registry. Add an entry in the same change that deprecates something.
FEATURE_STATES: tuple[Feature, ...] = (
    Feature(
        id='transport: "sse"',
        state=FeatureState.DEPRECATED,
        summary=('The `"sse"` value for an MCP server\'s `type`/`transport` key in `mcp.json`.'),
        rationale=(
            "It never named an SSE transport. `RemoteMCPClient` POSTs JSON-RPC "
            "and accepts either a JSON or an SSE-framed reply — that is "
            "Streamable HTTP. There is no GET stream, which is what an SSE "
            "transport would be. Every remote entry in the six shipped persona "
            'manifests omits `type` entirely and so was labeled `"sse"` by '
            "default, making the misnomer universal and invisible. Keeping the "
            "name would leave operators configuring a transport that does not "
            "exist. The HTTP+SSE transport itself is separately deprecated "
            "upstream, in spec revision 2026-07-28 (SEP-2596)."
        ),
        replacement='transport: "streamable-http"',
        deprecated_since="2026-11-23",
        removal_not_before="2027-11-23",
    ),
    Feature(
        id="protocol: 2024-11-05",
        state=FeatureState.ACTIVE,
        summary="The first MCP protocol revision, still accepted by the server.",
        rationale=(
            "Four revisions behind, but hosts do pin it and negotiation makes "
            "supporting it nearly free. Kept Active deliberately: there is no "
            "plan to drop it, and listing it here is so that intent is on the "
            "record rather than inferred from the version table."
        ),
        replacement="protocol: 2025-11-25",
    ),
    Feature(
        id="SAKTHAI_MCP_ENV_PASSTHROUGH=all",
        state=FeatureState.ACTIVE,
        summary=(
            "Hands a spawned MCP server the entire parent environment instead "
            "of the 14-name allowlist."
        ),
        rationale=(
            "An escape hatch for a server that needs a variable the allowlist "
            "omits, and it hands over every API key the process holds. Active "
            "because there is no finer-grained alternative yet; a spec `env` "
            "block is the targeted replacement and already works per-server."
        ),
        replacement="a per-server env block in mcp.json",
    ),
    Feature(
        id='_meta["ui/resourceUri"]',
        state=FeatureState.DEPRECATED,
        summary="The flat spelling of the MCP Apps tool-to-UI link.",
        rationale=(
            "The MCP Apps extension (SEP-1865) carries both a nested "
            "`_meta.ui.resourceUri` and this flat form, and states the flat one "
            "will be removed before the extension reaches GA. This package "
            "emits the nested form; the entry exists so that a host still "
            "reading the flat key is not surprised by its absence."
        ),
        replacement="_meta.ui.resourceUri",
        deprecated_since="2026-11-23",
        removal_not_before="2027-11-23",
    ),
)

_BY_ID = {feature.id: feature for feature in FEATURE_STATES}

#: Feature ids already warned about, so a warning fires once per process rather
#: than once per server spec parsed.
_WARNED: set[str] = set()


def get_feature(feature_id: str) -> Feature | None:
    """The registry entry for ``feature_id``, if there is one."""
    return _BY_ID.get(feature_id)


def deprecated_features() -> tuple[Feature, ...]:
    """Every entry not currently Active, for the generated documentation."""
    return tuple(f for f in FEATURE_STATES if f.state is not FeatureState.ACTIVE)


def warn_deprecated(feature_id: str, *, context: str = "") -> None:
    """Warn once that a deprecated feature was used.

    Emits a ``DeprecationWarning`` for anyone running with warnings visible,
    and a ``logger.warning`` for the far more common case of a CLI run where
    they are not — the gemini-provider precedent, which logs rather than warns,
    for exactly that reason. Both carry the replacement and the earliest
    removal date, so the message is actionable without opening the docs.

    An unknown ``feature_id`` is a programming error and raises: a typo would
    otherwise silently never warn.
    """
    feature = _BY_ID.get(feature_id)
    if feature is None:
        raise KeyError(f"no such feature in the deprecation registry: {feature_id!r}")
    if feature.state is FeatureState.ACTIVE:
        return
    if feature_id in _WARNED:
        return
    _WARNED.add(feature_id)

    parts = [f"{feature.id} is deprecated"]
    if feature.replacement:
        parts.append(f"use {feature.replacement} instead")
    if feature.removal_not_before:
        parts.append(f"it may be removed on or after {feature.removal_not_before}")
    message = "; ".join(parts) + "."
    if context:
        message = f"{message} ({context})"

    warnings.warn(message, DeprecationWarning, stacklevel=3)
    logger.warning("%s", message)


def _reset_warned_for_tests() -> None:
    """Clear the once-per-process warning memo. For tests only."""
    _WARNED.clear()
