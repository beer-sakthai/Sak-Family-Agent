"""Asynchronous template staging and offline metadata caching for content generation."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import sakthai_home

_VAR_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
_PENDING_PATTERN = re.compile(r"\[PENDING VERIFICATION:\s*([A-Z0-9_]+)\]")


class ContentTemplateStager:
    """Manages asynchronous template hydration and offline Hub/metrics caching."""

    def __init__(self, cache_dir: Path | None = None) -> None:
        self.cache_dir = cache_dir or (sakthai_home() / "cache" / "stager")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.cache_dir / "hub_metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.drafts_dir = self.cache_dir / "staged_drafts"
        self.drafts_dir.mkdir(parents=True, exist_ok=True)

    def stage_template(self, template: str, variables: dict[str, Any] | None = None) -> str:
        """Hydrate a template with known variables, marking unsupplied ones as pending."""
        vars_dict = variables or {}

        def replace_match(match: re.Match[str]) -> str:
            var_name = match.group(1)
            if var_name in vars_dict and vars_dict[var_name] is not None:
                return str(vars_dict[var_name])
            return f"[PENDING VERIFICATION: {var_name}]"

        return _VAR_PATTERN.sub(replace_match, template)

    def detect_unresolved_placeholders(self, content: str) -> list[str]:
        """Detect any unresolved variables or pending verification tags."""
        unresolved: set[str] = set()
        for m in _VAR_PATTERN.finditer(content):
            unresolved.add(m.group(1))
        for m in _PENDING_PATTERN.finditer(content):
            unresolved.add(m.group(1))
        return sorted(unresolved)

    def _safe_slug(self, key: str) -> str:
        return re.sub(r"[^a-zA-Z0-9_\-]", "_", key).strip("_")

    def save_cached_hub_metadata(self, repo_id: str, data: dict[str, Any]) -> Path:
        """Cache metadata for an external Hub repository to support offline drafting."""
        slug = self._safe_slug(repo_id)
        target = self.metadata_dir / f"{slug}.json"
        target.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
        return target

    def get_cached_hub_metadata(self, repo_id: str) -> dict[str, Any] | None:
        """Retrieve cached metadata for an external Hub repository."""
        slug = self._safe_slug(repo_id)
        target = self.metadata_dir / f"{slug}.json"
        if not target.is_file():
            return None
        try:
            return json.loads(target.read_text(encoding="utf-8"))
        except Exception:
            return None

    def save_staged_draft(self, slug: str, content: str) -> Path:
        """Save a staged draft to disk."""
        safe_name = self._safe_slug(slug)
        target = self.drafts_dir / f"{safe_name}.md"
        target.write_text(content, encoding="utf-8")
        return target
