from typing import Optional

import typer

from cetools.engine.generator import draft_character
from cetools.engine.models import Character
from cetools.formatter import format_character

app = typer.Typer()


@app.command()
def generate(career: Optional[str] = typer.Option(None, "--career")) -> None:
    """Generate a character."""
    if career is None:
        result = draft_character()
    else:
        typer.echo(
            f"Unknown career '{career}'. Valid careers: navy, scout",
            err=True,
        )
        raise typer.Exit(1)

    if isinstance(result, Character):
        typer.echo(format_character(result))
    else:
        typer.echo(result.reason, err=True)
        raise typer.Exit(code=result.exit_code)
