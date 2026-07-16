import random
from typing import Annotated

import typer

from cetools.engine.rolls import RandomRolls
from cetools.engine.worlds import Density, generate_subsector, generate_system

app = typer.Typer()

_DENSITIES = {density.name.lower(): density for density in Density}


@app.command("generate")
def generate_worlds(
    name: Annotated[
        str | None,
        typer.Option("--name", help="Override the generated world name (single world only)."),
    ] = None,
    count: Annotated[
        int,
        typer.Option("--count", "-n", min=1, help="Number of systems to generate."),
    ] = 1,
    allegiance: Annotated[
        str,
        typer.Option("--allegiance", help="Allegiance stamped on each system."),
    ] = "Na",
    seed: Annotated[
        int | None,
        typer.Option("--seed", help="Seed for reproducible output."),
    ] = None,
) -> None:
    """Generate one or more fully-described systems."""
    if name is not None and count > 1:
        typer.echo("--name applies only to a single world (use --count 1).", err=True)
        raise typer.Exit(1)

    rolls = RandomRolls(random.Random(seed)) if seed is not None else RandomRolls()

    for _ in range(count):
        system = generate_system(rolls, name=name, allegiance=allegiance)
        typer.echo(system.data_line)


@app.command("subsector")
def generate_subsector_command(
    density: Annotated[
        str,
        typer.Option("--density", help="World-presence density: rift, sparse, standard, dense."),
    ] = "standard",
    seed: Annotated[
        int | None,
        typer.Option("--seed", help="Seed for reproducible output."),
    ] = None,
) -> None:
    """Generate an 8x10 subsector of systems."""
    resolved_density = _DENSITIES.get(density.lower())
    if resolved_density is None:
        valid = ", ".join(_DENSITIES)
        typer.echo(f"Unknown density {density!r}. Valid choices: {valid}.", err=True)
        raise typer.Exit(1)

    rolls = RandomRolls(random.Random(seed)) if seed is not None else RandomRolls()

    subsector = generate_subsector(rolls, density=resolved_density)
    for system in sorted(subsector.systems, key=lambda system: system.hex):
        typer.echo(system.data_line)
