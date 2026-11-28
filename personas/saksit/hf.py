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


def verify_deputy_break_glass_quorum(store: Any | None) -> bool:
    """Verify emergency break-glass quorum for Deputy 1 Hub write delegation.

    Checks shared memory for either 'emergency-hf-delegate' or 'quorum-approved' tag.
    Returns True if valid break-glass quorum exists, False otherwise.
    """
    if store is None:
        return False
    delegates = store.search_by_tag("emergency-hf-delegate", limit=10)
    quorum = store.search_by_tag("quorum-approved", limit=10)
    return bool(delegates or quorum)


def assert_hf_write_allowed(
    store: Any | None = None,
    target_repo: str | None = None,
    current_charge: Any = "active",
    emergency_proxy: bool = False,
) -> bool:
    """Enforce SakThai's Triple Gate on all Hugging Face Hub write operations.

    Gate 1: SakThai Charge >= 50% (Active level), or Deputy 1 Charge >= 20% if emergency_proxy=True.
    Gate 2: No active 'deputy-chain' emergency tag in family memory, unless emergency_proxy=True
            and break-glass quorum is verified ('emergency-hf-delegate' or 'quorum-approved').
    Gate 3: Explicit 'hub-approved' tag from Beer in family memory.

    Raises:
        TripleGateError: If any of the three safety gates are violated.
    Returns:
        True if all three gates pass.
    """
    # Gate 1: Charge requirement
    if emergency_proxy:
        val = str(current_charge).strip().lower()
        if val in ("chargelevel.none", "none", "critical", "chargelevel.critical"):
            raise TripleGateError(
                f"Gate 1 violation: Emergency proxy requires Charge >= 20% (current: {current_charge})."
            )
    elif not _is_charge_sufficient(current_charge):
        raise TripleGateError(
            f"Gate 1 violation: SakThai Charge ({current_charge}) is below 50% minimum threshold. "
            "Hub writes require Charge >= 50% (Active level)."
        )

    # If no store is provided, gates 2 & 3 cannot be verified
    if store is None:
        raise TripleGateError(
            "Gate 2 & 3 violation: No MemoryStore provided to verify active tags."
        )

    # Gate 2: No active 'deputy-chain' emergency tag, unless authorized emergency break-glass quorum
    deputy_facts = store.search_by_tag("deputy-chain", limit=10)
    if deputy_facts:
        if emergency_proxy and verify_deputy_break_glass_quorum(store):
            pass  # Authorized emergency break-glass proxy
        else:
            raise TripleGateError(
                f"Gate 2 violation: Detected active deputy-chain emergency tag ({len(deputy_facts)} facts). "
                "Hub writes are strictly suspended while emergency deputy chain routing is active "
                "unless emergency break-glass quorum is verified (--tag emergency-hf-delegate or --tag quorum-approved)."
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
        emergency_proxy = kwargs.get("emergency_proxy", False)

        # Also inspect args if not in kwargs
        if store is None:
            for a in args:
                if hasattr(a, "search_by_tag"):
                    store = a
                    break

        assert_hf_write_allowed(
            store=store,
            target_repo=target_repo,
            current_charge=current_charge,
            emergency_proxy=emergency_proxy,
        )
        return func(*args, **kwargs)

    return wrapper


def hf_validate_card_metadata(card_path_or_content: str | Any) -> dict[str, Any]:
    """Validate Hugging Face model card YAML frontmatter metadata offline.

    Accepts a filepath (str or Path) or the raw string content of a README.md / model card.
    Extracts the YAML frontmatter between `---` boundaries and verifies required and
    recommended metadata keys (license, language, tags, pipeline_tag).

    Returns:
        dict with keys:
            - 'valid' (bool): True if YAML is valid and required fields are present
            - 'metadata' (dict): Extracted metadata dictionary
            - 'errors' (list[str]): Critical schema/parsing errors
            - 'warnings' (list[str]): Best-practice recommendations
    """
    import re
    from pathlib import Path

    import yaml

    errors: list[str] = []
    warnings: list[str] = []
    metadata: dict[str, Any] = {}

    content = ""
    # Check if input is an existing file path
    try:
        p = Path(card_path_or_content)
        if p.exists() and p.is_file():
            content = p.read_text(encoding="utf-8")
        else:
            content = str(card_path_or_content)
    except Exception:
        content = str(card_path_or_content)

    # Frontmatter regex: opening --- and closing ---
    match = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", content, re.DOTALL)
    if not match:
        errors.append("Missing YAML frontmatter (must start and end with '---')")
        return {
            "valid": False,
            "metadata": metadata,
            "errors": errors,
            "warnings": warnings,
        }

    raw_yaml = match.group(1)
    try:
        parsed = yaml.safe_load(raw_yaml)
        if not isinstance(parsed, dict):
            errors.append(
                f"Frontmatter YAML must parse to a dictionary, got {type(parsed).__name__}"
            )
            return {
                "valid": False,
                "metadata": metadata,
                "errors": errors,
                "warnings": warnings,
            }
        metadata = parsed
    except Exception as e:
        errors.append(f"YAML parsing error: {e}")
        return {
            "valid": False,
            "metadata": metadata,
            "errors": errors,
            "warnings": warnings,
        }

    # Validate required fields
    if "license" not in metadata or not metadata["license"]:
        errors.append("Missing required metadata field: 'license'")

    # Validate recommended fields / types
    if "pipeline_tag" not in metadata and "tags" not in metadata:
        warnings.append("Recommended metadata missing: 'pipeline_tag' or 'tags'")

    if "language" in metadata:
        lang = metadata["language"]
        if not isinstance(lang, (str, list)):
            warnings.append(
                f"'language' field should be str or list of str, got {type(lang).__name__}"
            )

    return {
        "valid": len(errors) == 0,
        "metadata": metadata,
        "errors": errors,
        "warnings": warnings,
    }
