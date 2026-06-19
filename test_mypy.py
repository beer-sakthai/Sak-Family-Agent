import click
from typing import Any
def _ok() -> str:
    return f"{click.style('+', fg='green')}"
