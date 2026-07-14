from typing import Annotated

import typer

from cetools.engine.careers import CAREERS, UnknownCareer, resolve
from cetools.engine.generator import DRAFT, RANDOM, generate
from cetools.engine.models import Character
from cetools.formatter import format_characters

app = typer.Typer()

_CANONICAL_CAREERS = ", ".join(career.name for career in CAREERS)


@app.command("generate")
def generate_characters(
    career: Annotated[
        str | None,
        typer.Option("--career", help=f"Career to generate. Valid careers: {_CANONICAL_CAREERS}"),
    ] = None,
    random: Annotated[
        bool,
        typer.Option("--random", help="Draw each career uniformly at random from all careers."),
    ] = False,
    count: Annotated[
        int,
        typer.Option("--count", "-n", min=1, help="Number of characters to generate."),
    ] = 1,
) -> None:
    """Generate one or more characters."""
    if career is not None and random:
        typer.echo("Options --career and --random are mutually exclusive.", err=True)
        raise typer.Exit(1)

    resolved_career = None
    if career is not None:
        resolved_career = resolve(career)
        if isinstance(resolved_career, UnknownCareer):
            if resolved_career.suggestion is not None:
                hint = f"Did you mean: {resolved_career.suggestion.name}?"
            else:
                hint = f"Valid careers: {_CANONICAL_CAREERS}"
            typer.echo(f"Unknown career '{resolved_career.spec}'. {hint}", err=True)
            raise typer.Exit(1)

    assignment = resolved_career or (RANDOM if random else DRAFT)

    characters: list[Character] = []
    failures = 0
    failure_exit_code = 1
    for _ in range(count):
        result = generate(assignment)

        if isinstance(result, Character):
            characters.append(result)
        else:
            typer.echo(result.reason, err=True)
            failures += 1
            failure_exit_code = result.exit_code

    if characters:
        typer.echo(format_characters(characters))
    if failures:
        raise typer.Exit(failure_exit_code)
