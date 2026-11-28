"""Asynchronous template staging and offline metadata caching for content generation."""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any, cast

import httpx

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
            val = json.loads(target.read_text(encoding="utf-8"))
            if isinstance(val, dict):
                return cast(dict[str, Any], val)
            return None
        except Exception:
            return None

    def save_staged_draft(self, slug: str, content: str) -> Path:
        """Save a staged draft to disk."""
        safe_name = self._safe_slug(slug)
        target = self.drafts_dir / f"{safe_name}.md"
        target.write_text(content, encoding="utf-8")
        return target

    def hydrate_with_live_hub(
        self,
        template: str,
        repo_id: str,
        repo_type: str = "model",
        variables: dict[str, Any] | None = None,
        timeout: float = 10.0,
        ttl_seconds: int = 3600,
    ) -> str:
        """Hydrate template with live Hugging Face Hub metadata, merged with user variables."""
        vars_dict: dict[str, Any] = dict(variables or {})
        vars_dict["REPO_ID"] = repo_id

        meta = fetch_live_hub_metadata(
            repo_id=repo_id,
            repo_type=repo_type,
            timeout=timeout,
            ttl_seconds=ttl_seconds,
            cache_dir=self.metadata_dir,
        )

        if meta:
            if "downloads" in meta:
                vars_dict.setdefault("DOWNLOADS", meta["downloads"])
                vars_dict.setdefault("DOWNLOAD_COUNT", meta["downloads"])
            if "likes" in meta:
                vars_dict.setdefault("LIKES", meta["likes"])
                vars_dict.setdefault("STARS", meta["likes"])
            if "sha" in meta:
                vars_dict.setdefault("COMMIT_SHA", meta["sha"])
                vars_dict.setdefault("HUB_COMMIT", meta["sha"])

        return self.stage_template(template, vars_dict)


def fetch_live_hub_metadata(
    repo_id: str,
    repo_type: str = "model",
    timeout: float = 10.0,
    ttl_seconds: int = 3600,
    cache_dir: Path | None = None,
    hf_token: str | None = None,
) -> dict[str, Any] | None:
    """Fetch live metadata for a model or dataset from the Hugging Face Hub API with TTL caching."""
    target_dir = cache_dir or (sakthai_home() / "cache" / "stager" / "hub_metadata")
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", repo_id).strip("_")
    cache_file = target_dir / f"{safe_slug}.json"

    now = time.time()
    cached_data: dict[str, Any] | None = None
    if cache_file.is_file():
        try:
            raw = json.loads(cache_file.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                cached_data = cast(dict[str, Any], raw)
                cached_at = float(cached_data.get("cached_at", 0))
                if (now - cached_at) < ttl_seconds:
                    return cached_data
        except Exception:
            cached_data = None

    token = hf_token or os.environ.get("HF_TOKEN")
    headers: dict[str, str] = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    api_path = "models" if repo_type == "model" else "datasets"
    url = f"https://huggingface.co/api/{api_path}/{repo_id}"

    try:
        resp = httpx.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            payload = resp.json()
            if isinstance(payload, dict):
                res = cast(dict[str, Any], payload)
                res["cached_at"] = now
                cache_file.write_text(json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
                return res
        elif resp.status_code == 404:
            return None
    except Exception as exc:
        _ = exc

    return cached_data
