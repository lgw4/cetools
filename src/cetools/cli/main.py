import typer

from cetools.cli import character

app = typer.Typer()
app.add_typer(character.app, name="character")


@app.callback()
def main() -> None:
    """Cepheus Engine character generation tools."""
