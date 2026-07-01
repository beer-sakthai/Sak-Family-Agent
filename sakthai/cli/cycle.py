"""Commands for the 6-stage Dream → Growth cycle."""

from __future__ import annotations

import click

from ..cycle import STAGES, Stage, advance_stage, get_current_stage, set_stage, stage_info
from ..memory.store import MemoryStore


@click.group()
def cycle() -> None:
    """Track and advance the 6-stage Dream → Growth cycle."""


@cycle.command("status")
def cycle_status() -> None:
    """Show the current stage and its guidance."""
    with MemoryStore() as store:
        stage = get_current_stage(store)
    info = stage_info(stage)
    click.echo(f"Stage {info.number}/6  [{stage.value.upper()}]  {info.goal}")
    click.echo(f"  guidance : {info.guidance}")
    click.echo(f"  commands : {', '.join(info.commands)}")


@cycle.command("next")
def cycle_next() -> None:
    """Advance to the next stage."""
    with MemoryStore() as store:
        upcoming = advance_stage(store)
    info = stage_info(upcoming)
    click.echo(f"→ Stage {info.number}/6  [{upcoming.value.upper()}]  {info.goal}")


@cycle.command("set")
@click.argument("stage_name", metavar="STAGE")
@click.option("-f", "--force", is_flag=True, help="Allow skipping forward over stages.")
def cycle_set(stage_name: str, force: bool) -> None:
    """Jump to a specific STAGE (dream, hope, care, joy, trust, growth).

    Going back to an earlier stage or advancing by exactly one is always
    allowed; skipping *forward* over stages requires --force. Use
    `sakthai cycle next` for the normal sequential flow.
    """
    try:
        stage = Stage(stage_name.lower())
    except ValueError:
        valid = ", ".join(s.value for s in Stage)
        raise click.ClickException(
            f"Unknown stage '{stage_name}'. Valid: {valid}"
        ) from None
    with MemoryStore() as store:
        current = get_current_stage(store)
        skipped = stage_info(stage).number - stage_info(current).number - 1
        if skipped > 0 and not force:
            raise click.ClickException(
                f"Refusing to skip from {current.value.upper()} to {stage.value.upper()} "
                f"({skipped} stage(s) skipped). Use `sakthai cycle next` to advance one "
                "stage, or pass --force to jump."
            )
        set_stage(store, stage)
    info = stage_info(stage)
    click.echo(f"Set to Stage {info.number}/6  [{stage.value.upper()}]  {info.goal}")


@cycle.command("list")
def cycle_list() -> None:
    """List all six stages, marking the current one."""
    with MemoryStore() as store:
        current = get_current_stage(store)
    for info in STAGES:
        marker = "▶" if info.stage == current else " "
        click.echo(
            f"  {marker} {info.number}. {info.stage.value.upper():<8}  {info.goal}"
        )
