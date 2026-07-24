import typer

from cetools.cli import character, ship, world

app = typer.Typer()
app.add_typer(character.app, name="character")
app.add_typer(world.app, name="world")
app.add_typer(ship.app, name="ship")


@app.callback()
def main() -> None:
    """Cepheus Engine character, world, and ship generation tools."""
