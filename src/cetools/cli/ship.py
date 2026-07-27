import random
import sys
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Annotated

import typer

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships import (
    ABSENT,
    Absent,
    ArmorFit,
    ArmorType,
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


_NONE = "none"
"""Typed at a prompt, pins a component's *absence*—a different answer from Enter."""


def _ask_until_understood[T](question: str, interpret: Callable[[str], T]) -> T | None:
    """Ask `question` until `interpret` accepts the answer, and return what it made.

    Generic in what `interpret` returns, so each field keeps its own type on the
    way to `DesignConstraints`—a three-state field must not arrive as `object`.

    Enter returns `None`, leaving the field to the dice. An answer `interpret`
    rejects is reported by the reason it raised and asked again, so a typo costs
    a line rather than the session.
    """
    while True:
        answer = _ask(question, _ROLL)
        if not answer:
            return None
        try:
            return interpret(answer)
        except ValueError as exc:
            typer.echo(str(exc), err=True)


def _read_hull_tons(hull_class: HullClass, answer: str) -> int:
    try:
        tons = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a number of tons") from None
    validate_hull_tons(hull_class, tons)  # tabulation only; build_ship owns the rules
    return tons


def _read_armor(answer: str) -> ArmorFit | Absent:
    """One armour layer from `<type> <percent>`, or `ABSENT` from `none`.

    Any SRD type may be pinned, including ones generation would never roll. The
    multiple-of-5 rule is *not* checked here: it lives in `build_ship` and is
    deliberately not duplicated outward, so it surfaces at assembly (ADR-0001).
    """
    if answer.lower() == _NONE:
        return ABSENT

    parts = answer.split()
    if len(parts) != 2:
        raise ValueError(f'give an armor type and a percent, like "crystaliron 10"; got {answer}')

    name, percent_text = parts
    try:
        kind = ArmorType(name.lower())
    except ValueError:
        known = sorted(known_type.value for known_type in ArmorType)
        raise ValueError(f"{name} is not a known armor type; known: {known}") from None
    try:
        percent = int(percent_text.removesuffix("%"))  # a referee may well type "10%"
    except ValueError:
        raise ValueError(f"{percent_text} is not a percent of the hull") from None

    return ArmorFit(type=kind, percent=percent)  # rejects a non-positive percent


def _ask_constraints(hull_class: HullClass, hull: int | None) -> DesignConstraints:
    """Walk the referee through what they can pin, in SRD build order.

    A value a flag already supplied pre-answers its question and that question
    is not asked, so flags and prompts never ask the same thing twice.
    """
    hull_tons = (
        hull
        if hull is not None
        else _ask_until_understood("Hull tonnage", partial(_read_hull_tons, hull_class))
    )
    armor = _ask_until_understood("Armor", _read_armor)
    return DesignConstraints(hull_class=hull_class, hull_tons=hull_tons, armor=armor)


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
