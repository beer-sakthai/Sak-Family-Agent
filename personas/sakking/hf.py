"""Hugging Face Hub operations: model info and downloads into the SakThai cache.

huggingface_hub is imported lazily so the package (and test suite) works
without it installed; the CLI surfaces a clear install hint instead.
"""

from __future__ import annotations

from typing import Any

import click

from .config import sakthai_home


def _hub() -> Any:
    try:
        import huggingface_hub
    except ImportError as e:
        raise click.ClickException(
            "huggingface_hub is not installed. Install it with:\n    pip install huggingface_hub"
        ) from e
    return huggingface_hub


def hf_info(repo_id: str) -> str:
    info = _hub().model_info(repo_id)
    lines = [
        f"id:        {info.id}",
        f"downloads: {info.downloads}",
        f"likes:     {info.likes}",
        f"tags:      {', '.join(info.tags or [])}",
    ]
    return "\n".join(lines)


def hf_download(repo_id: str) -> str:
    """Download a model snapshot into the SakThai cache, protected against traversal."""
    root = (sakthai_home() / "hf").resolve()
    target = (root / repo_id).resolve()

    if not target.is_relative_to(root):
        raise ValueError(f"Invalid repo_id {repo_id!r}: path traversal detected.")

    return str(_hub().snapshot_download(repo_id, local_dir=str(target)))


class TripleGateError(PermissionError):
    """Raised when a Hugging Face Hub write operation violates the Triple Gate safety contract."""


def _is_charge_sufficient(current_charge: Any) -> bool:
    """Check if charge meets or exceeds 50% (Active level)."""
    if current_charge is None:
        return True
    if isinstance(current_charge, (int, float)):
        return current_charge >= 50.0
    val = str(current_charge).lower().strip()
    if val.endswith("%"):
        try:
            return float(val[:-1]) >= 50.0
        except ValueError:
            pass
    if val in ("chargelevel.active", "active", "chargelevel.critical", "critical"):
        return True
    return val not in ("chargelevel.low", "low", "chargelevel.none", "none")


def assert_hf_write_allowed(
    store: Any | None = None,
    target_repo: str | None = None,
    current_charge: Any = "active",
) -> bool:
    """Enforce SakThai's Triple Gate on all Hugging Face Hub write operations.

    Gate 1: SakThai Charge >= 50% (Active level).
    Gate 2: No active 'deputy-chain' emergency tag in family memory.
    Gate 3: Explicit 'hub-approved' tag from Beer in family memory.

    Raises:
        TripleGateError: If any of the three safety gates are violated.
    Returns:
        True if all three gates pass.
    """
    # Gate 1: Charge >= 50%
    if not _is_charge_sufficient(current_charge):
        raise TripleGateError(
            f"Gate 1 violation: SakThai Charge ({current_charge}) is below 50% minimum threshold. "
            "Hub writes require Charge >= 50% (Active level)."
        )

    # If no store is provided, gates 2 & 3 cannot be verified
    if store is None:
        raise TripleGateError(
            "Gate 2 & 3 violation: No MemoryStore provided to verify active tags."
        )

    # Gate 2: No active 'deputy-chain' emergency tag
    deputy_facts = store.search_by_tag("deputy-chain", limit=10)
    if deputy_facts:
        raise TripleGateError(
            f"Gate 2 violation: Detected active deputy-chain emergency tag ({len(deputy_facts)} facts). "
            "Hub writes are strictly suspended while emergency deputy chain routing is active."
        )

    # Gate 3: Explicit 'hub-approved' tag from Beer
    approved_facts = store.search_by_tag("hub-approved", limit=20)
    if not approved_facts:
        raise TripleGateError(
            "Gate 3 violation: Missing verified 'hub-approved' tag from Beer in family memory. "
            "All Hub writes require explicit pre-approval logged with --tag hub-approved."
        )

    return True


def triple_gate_hub_write(func: Any) -> Any:
    """Decorator enforcing the Triple Gate on Hugging Face Hub write functions/tools."""
    import functools

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        store = kwargs.get("store")
        target_repo = kwargs.get("target_repo") or kwargs.get("repo_id")
        current_charge = kwargs.get("current_charge", "active")

        # Also inspect args if not in kwargs
        if store is None:
            for a in args:
                if hasattr(a, "search_by_tag"):
                    store = a
                    break

        assert_hf_write_allowed(store=store, target_repo=target_repo, current_charge=current_charge)
        return func(*args, **kwargs)

    return wrapper
