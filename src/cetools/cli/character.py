import typer

from cetools.engine.careers import CAREER_REGISTRY
from cetools.engine.generator import draft_character, generate_career_character
from cetools.engine.models import Character
from cetools.formatter import format_character

app = typer.Typer()


@app.command()
def generate(career: str | None = typer.Option(None, "--career")) -> None:
    """Generate a character."""
    if career is None:
        result = draft_character()
    else:
        original = career
        normalized = career.strip().lower()
        if normalized not in CAREER_REGISTRY:
            valid = ", ".join(sorted(CAREER_REGISTRY))
            typer.echo(
                f"Unknown career '{original}'. Valid careers: {valid}",
                err=True,
            )
            raise typer.Exit(1)
        result = generate_career_character(CAREER_REGISTRY[normalized])

    if isinstance(result, Character):
        typer.echo(format_character(result))
    else:
        typer.echo(result.reason, err=True)
        raise typer.Exit(code=result.exit_code)
