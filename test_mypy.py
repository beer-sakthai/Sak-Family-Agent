import click


def _ok() -> str:
    return f"{click.style('+', fg='green')}"
