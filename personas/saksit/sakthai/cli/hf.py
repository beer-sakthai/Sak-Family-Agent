"""Hugging Face CLI commands: info and download."""

from __future__ import annotations

import click

from ..hf import hf_download, hf_info


@click.group("hf")
def hf_cmd() -> None:
    """Hugging Face Hub operations."""


@hf_cmd.command("info")
@click.argument("repo_id")
def hf_info_cmd(repo_id: str) -> None:
    """Show HF model info for REPO_ID."""
    click.echo(hf_info(repo_id))


@hf_cmd.command("download")
@click.argument("repo_id")
def hf_download_cmd(repo_id: str) -> None:
    """Download HF model REPO_ID into local SakThai cache."""
    click.echo(hf_download(repo_id))
