import click
def test() -> str:
    val: str = click.style('test', fg='green')
    return val
