import click
def _ok() -> str:
    return str(click.style('+', fg='green'))
from typing import Any
def _ok() -> str:
    return f"{click.style('+', fg='green')}"
