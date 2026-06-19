import click
def _ok() -> str:
    return str(click.style('+', fg='green'))
