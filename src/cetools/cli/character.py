import difflib
from typing import Annotated

import typer

from cetools.engine.careers import CAREER_REGISTRY
from cetools.engine.generator import DRAFT, RANDOM, generate
from cetools.engine.models import Character
from cetools.formatter import format_characters

app = typer.Typer()

_CANONICAL_CAREERS = ", ".join(
    c.name for c in sorted(CAREER_REGISTRY.values(), key=lambda c: c.name)
)


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
        original = career
        normalized = career.strip().lower().replace("-", " ")
        if normalized not in CAREER_REGISTRY:
            matches = difflib.get_close_matches(
                normalized, CAREER_REGISTRY.keys(), n=1, cutoff=0.6
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
        resolved_career = CAREER_REGISTRY[normalized]

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
