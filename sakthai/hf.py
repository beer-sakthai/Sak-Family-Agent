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
    target = sakthai_home() / "hf" / repo_id
    return str(_hub().snapshot_download(repo_id, local_dir=str(target)))
