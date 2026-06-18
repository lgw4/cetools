import difflib
from typing import Annotated

import typer

from cetools.engine.careers import CAREER_REGISTRY
from cetools.engine.generator import draft_character, generate_career_character
from cetools.engine.models import Character
from cetools.formatter import format_character

app = typer.Typer()

_CANONICAL_CAREERS = ", ".join(
    c.name for c in sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
)


@app.command()
def generate(
    career: Annotated[
        str | None,
        typer.Option("--career", help=f"Career to generate. Valid careers: {_CANONICAL_CAREERS}"),
    ] = None,
) -> None:
    """Generate a character."""
    if career is None:
        result = draft_character()
    else:
        original = career
        normalized = career.strip().lower().replace("-", " ")
        if normalized not in CAREER_REGISTRY:
            matches = difflib.get_close_matches(
                normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.4
            )
            if matches:
                canonical = CAREER_REGISTRY[matches[0]].name
                typer.echo(
                    f"Unknown career '{original}'. Did you mean: {canonical}?",
                    err=True,
                )
            else:
                typer.echo(
                    f"Unknown career '{original}'. Valid careers: {_CANONICAL_CAREERS}",
                    err=True,
                )
            raise typer.Exit(1)
        result = generate_career_character(CAREER_REGISTRY[normalized])

    if isinstance(result, Character):
        typer.echo(format_character(result))
    else:
        typer.echo(result.reason, err=True)
        raise typer.Exit(code=result.exit_code)
