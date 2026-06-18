import typer

from cetools.engine.careers.navy import NAVY_CAREER
from cetools.engine.generator import generate_character
from cetools.engine.models import Character
from cetools.formatter import format_character

app = typer.Typer()


@app.command()
def generate() -> None:
    """Generate a Navy character."""
    result = generate_character(NAVY_CAREER)
    if isinstance(result, Character):
        typer.echo(format_character(result))
    else:
        typer.echo(result.reason, err=True)
        raise typer.Exit(code=result.exit_code)
