"""Automated Social Asset Bundler for publishing packages."""

from __future__ import annotations

import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sakthai.config import sakthai_home


@dataclass
class SocialAssetBundle:
    slug: str
    bundle_dir: Path
    post_path: Path
    prompts_path: Path
    metadata_path: Path
    zip_path: Path
    total_files: int


def sanitize_bundle_slug(slug: str) -> str:
    """Sanitize string into a filesystem-safe slug."""
    clean = re.sub(r"[^a-zA-Z0-9_\-]", "_", slug)
    clean = re.sub(r"_+", "_", clean).strip("_-")
    return clean or "social_bundle"


def create_social_asset_bundle(
    slug: str,
    content: str,
    prompts: dict[str, Any] | list[Any],
    metadata: dict[str, Any],
    output_dir: Path | None = None,
    extra_files: dict[str, str | bytes] | None = None,
) -> SocialAssetBundle:
    """Package staged copy, multimodal prompts, and metadata into a structured bundle folder and zip."""
    safe_slug = sanitize_bundle_slug(slug)
    base_dir = output_dir or (sakthai_home() / "reports" / "bundles")
    bundle_dir = base_dir / safe_slug
    bundle_dir.mkdir(parents=True, exist_ok=True)

    post_path = bundle_dir / "post.md"
    prompts_path = bundle_dir / "prompts.json"
    metadata_path = bundle_dir / "metadata.json"
    zip_path = bundle_dir / "package.zip"

    post_path.write_text(content, encoding="utf-8")
    prompts_path.write_text(json.dumps(prompts, indent=2, sort_keys=True), encoding="utf-8")

    meta_copy = dict(metadata)
    meta_copy.setdefault("bundle_slug", safe_slug)
    metadata_path.write_text(json.dumps(meta_copy, indent=2, sort_keys=True), encoding="utf-8")

    files_to_zip: list[tuple[str, Path]] = [
        ("post.md", post_path),
        ("prompts.json", prompts_path),
        ("metadata.json", metadata_path),
    ]

    if extra_files:
        for fname, fcontent in extra_files.items():
            fpath = bundle_dir / fname
            if isinstance(fcontent, bytes):
                fpath.write_bytes(fcontent)
            else:
                fpath.write_text(fcontent, encoding="utf-8")
            files_to_zip.append((fname, fpath))

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for arcname, fpath in files_to_zip:
            zf.write(fpath, arcname=arcname)

    return SocialAssetBundle(
        slug=safe_slug,
        bundle_dir=bundle_dir,
        post_path=post_path,
        prompts_path=prompts_path,
        metadata_path=metadata_path,
        zip_path=zip_path,
        total_files=len(files_to_zip) + 1,
    )
