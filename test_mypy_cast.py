import click
from typing import cast
def test() -> str:
    return cast(str, click.style('test', fg='green'))
