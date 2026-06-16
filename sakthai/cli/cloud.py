"""Commands for the cloud (Google ADK / Vertex AI) runtime stub."""

from __future__ import annotations

from pathlib import Path

import click

from ..cloud import build_adk_agent, cloud_status, render_manifest, resolve_cloud_spec
from ..cloud.runtime import CloudRuntimeError

_OK = "[+]"
_WARN = "[!]"


@click.group()
def cloud() -> None:
    """Inspect and scaffold the cloud (ADK/Vertex) deployment skeleton."""


@cloud.command("status")
def cloud_status_cmd() -> None:
    """Report cloud-deployment readiness (no network calls)."""
    status = cloud_status()
    click.echo(click.style("\n── SakThai Cloud Status ──", bold=True))

    def line(label: str, ok: bool, detail: str) -> None:
        mark = click.style(_OK, fg="green") if ok else click.style(_WARN, fg="yellow")
        click.echo(f"  {mark} {label:<14}: {detail}")

    line(
        "ADK extra",
        status["adk_installed"],
        "installed" if status["adk_installed"] else 'missing — pip install -e ".[cloud]"',
    )
    line("Project", status["project"] is not None, status["project"] or "set GOOGLE_CLOUD_PROJECT")
    line(
        "Credential",
        status["credential"],
        "resolved" if status["credential"] else "set GEMINI_API_KEY or enable Vertex",
    )
    click.echo(f"      location  : {status['location']}")
    click.echo(f"      model     : {status['model']}")
    click.echo(f"      vertex    : {status['use_vertex']}")

    click.echo()
    if status["ready"]:
        click.echo(
            click.style("  ✓ Ready to scaffold/deploy a cloud agent.", fg="green", bold=True)
        )
    else:
        click.echo(
            click.style("  ✗ Not deploy-ready — this is a roadmap stub.", fg="yellow", bold=True)
        )
    click.echo()


@cloud.command("manifest")
def cloud_manifest_cmd() -> None:
    """Print the deployment manifest for the resolved spec."""
    click.echo(render_manifest(resolve_cloud_spec()))


@cloud.command("scaffold")
@click.argument("target", type=click.Path(file_okay=False, path_type=Path), default="cloud-deploy")
@click.option("--force", is_flag=True, help="Overwrite an existing manifest.")
def cloud_scaffold_cmd(target: Path, force: bool) -> None:
    """Write a deployment manifest into TARGET dir (default: ./cloud-deploy)."""
    target.mkdir(parents=True, exist_ok=True)
    manifest_path = target / "manifest.yaml"
    if manifest_path.exists() and not force:
        raise click.ClickException(f"{manifest_path} exists — pass --force to overwrite.")
    manifest_path.write_text(render_manifest(resolve_cloud_spec()), encoding="utf-8")
    click.echo(f"{_OK} wrote {manifest_path}")


@cloud.command("build")
def cloud_build_cmd() -> None:
    """Try to build the ADK agent (requires the `cloud` extra)."""
    try:
        agent = build_adk_agent()
    except CloudRuntimeError as exc:
        raise click.ClickException(str(exc)) from exc
    click.echo(f"{_OK} built cloud agent: {getattr(agent, 'name', '<agent>')}")
