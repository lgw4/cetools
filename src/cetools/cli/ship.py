import random
import sys
from pathlib import Path
from typing import Annotated

import typer

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import (
    DesignConstraints,
    HullClass,
    build_ship,
    dump_design,
    generate_ship,
    load_design,
    render_description,
    validate_hull_tons,
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


_ROLL = "roll"
"""What pressing Enter at a prompt does, shown as the default at every prompt."""


def _ask(question: str, default_label: str) -> str:
    """Ask `question` on stderr, showing its default, and read one answer.

    Written out by hand rather than delegated to `typer.prompt` because nothing
    the wizard says may reach stdout: `--interactive` composes with `--toml` and
    `--out`, so stdout has to stay a design a pipe can read.
    """
    typer.echo(f"{question} [{default_label}]: ", nl=False, err=True)
    line = sys.stdin.readline()
    if not line:  # end of input: no answer is coming, and none can be assumed
        typer.echo("", err=True)
        raise typer.Abort()
    return line.strip()


def _ask_hull_tons(hull_class: HullClass) -> int | None:
    """The referee's hull tonnage, or `None` to leave it to the dice.

    An untabulated answer is rejected here and asked again, so a typo costs one
    line rather than the session. Only tabulation is checked: `build_ship`
    remains the sole authority on rules legality.
    """
    while True:
        answer = _ask("Hull tonnage", _ROLL)
        if not answer:
            return None
        try:
            tons = int(answer)
        except ValueError:
            typer.echo(f"{answer} is not a number of tons", err=True)
            continue
        try:
            validate_hull_tons(hull_class, tons)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            continue
        return tons


def _ask_constraints(hull_class: HullClass, hull: int | None) -> DesignConstraints:
    """Walk the referee through what they can pin, in SRD build order.

    A value a flag already supplied pre-answers its question and that question
    is not asked, so flags and prompts never ask the same thing twice.
    """
    hull_tons = hull if hull is not None else _ask_hull_tons(hull_class)
    return DesignConstraints(hull_class=hull_class, hull_tons=hull_tons)


@app.command("generate")
def generate(
    hull: Annotated[
        int | None, typer.Option("--hull", help="Constrain to a tabulated hull size.")
    ] = None,
    small_craft: Annotated[
        bool, typer.Option("--small-craft", help="Generate a 10-95 ton small craft.")
    ] = False,
    interactive: Annotated[
        bool,
        typer.Option("--interactive", "-i", help="Answer prompts to pin what you care about."),
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

    hull_class = HullClass.SMALL_CRAFT if small_craft else HullClass.STARSHIP

    if interactive:
        constraints = _ask_constraints(hull_class, hull)
    else:
        constraints = DesignConstraints(hull_class=hull_class, hull_tons=hull)

    try:
        result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)

    ship = result.ship

    output = dump_design(ship.design) if toml else render_description(ship)

    if out is not None:
        out.write_text(output, encoding="utf-8")
    else:
        typer.echo(output)
