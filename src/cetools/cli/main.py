import typer

from cetools.cli import character, world

app = typer.Typer()
app.add_typer(character.app, name="character")
app.add_typer(world.app, name="world")


@app.callback()
def main() -> None:
    """Cepheus Engine character and world generation tools."""
