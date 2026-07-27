import random
from pathlib import Path
from typing import Annotated

import typer

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import (
    build_ship,
    dump_design,
    generate_ship,
    load_design,
    render_description,
)

app = typer.Typer()

_SEED_UPPER_BOUND = 2**32


@app.command("build")
def build(
    file: Annotated[Path, typer.Argument(help="Path to a TOML ship design file.")],
    toml: Annotated[
        bool, typer.Option("--toml", help="Emit round-trippable TOML instead of a description.")
    ] = False,
    out: Annotated[
        Path | None, typer.Option("--out", help="Write output to a file instead of stdout.")
    ] = None,
) -> None:
    """Build a ship from a TOML design file and print its description."""
    if out is not None and not toml:
        typer.echo("--out requires --toml", err=True)
        raise typer.Exit(1)

    try:
        design = load_design(file)
        ship = build_ship(design)
    except OSError:
        typer.echo(f"cannot read design file: {file}", err=True)
        raise typer.Exit(1)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    output = dump_design(ship.design) if toml else render_description(ship)

    if out is not None:
        out.write_text(output, encoding="utf-8")
    else:
        typer.echo(output)


@app.command("generate")
def generate(
    hull: Annotated[
        int | None, typer.Option("--hull", help="Constrain to a tabulated hull size.")
    ] = None,
    small_craft: Annotated[
        bool, typer.Option("--small-craft", help="Generate a 10-95 ton small craft.")
    ] = False,
    toml: Annotated[
        bool, typer.Option("--toml", help="Emit round-trippable TOML instead of a description.")
    ] = False,
    out: Annotated[
        Path | None, typer.Option("--out", help="Write output to a file instead of stdout.")
    ] = None,
    seed: Annotated[
        int | None, typer.Option("--seed", help="Seed for reproducible output.")
    ] = None,
) -> None:
    """Randomly generate a rules-legal ship and print its description."""
    if out is not None and not toml:
        typer.echo("--out requires --toml", err=True)
        raise typer.Exit(1)

    if seed is None:
        seed = random.randrange(_SEED_UPPER_BOUND)
        typer.echo(f"seed: {seed}", err=True)

    try:
        result = generate_ship(RandomRolls.seeded(seed), hull_size=hull, small_craft=small_craft)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    ship = result.ship

    output = dump_design(ship.design) if toml else render_description(ship)

    if out is not None:
        out.write_text(output, encoding="utf-8")
    else:
        typer.echo(output)
