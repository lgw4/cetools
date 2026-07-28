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
    BayFit,
    ComputerFit,
    Configuration,
    DesignConstraints,
    Drive,
    FittingFit,
    HullClass,
    ScreenFit,
    build_ship,
    dump_design,
    generate_ship,
    load_design,
    power_floor,
    render_description,
    validate_electronics,
    validate_hull_tons,
    validate_rating,
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


def _ask_until_understood[T](
    question: str, interpret: Callable[[str], T], default_label: str = _ROLL
) -> T | None:
    """Ask `question` until `interpret` accepts the answer, and return what it made.

    Generic in what `interpret` returns, so each field keeps its own type on the
    way to `DesignConstraints`—a three-state field must not arrive as `object`.

    Enter returns `None`, leaving the field to the dice. An answer `interpret`
    rejects is reported by the reason it raised and asked again, so a typo costs
    a line rather than the session.

    `default_label` is what Enter is advertised to do. Every field rolls except
    `purpose`, which is never rolled at all, so promising a roll there would be
    a lie the referee only discovers in the output.
    """
    while True:
        answer = _ask(question, default_label)
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


def _read_rating(
    hull_class: HullClass, hull_tons: int | None, drive: Drive, floor: int | None, answer: str
) -> int:
    """One drive rating, checked against the hull as far as it is known.

    When the referee left the hull to the dice, `hull_tons` is `None` and the
    check widens to every hull of the class: a rating no hull could deliver is
    still caught, one this hull cannot is not. That narrower case surfaces at
    assembly instead.
    """
    try:
        rating = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a drive rating") from None

    if floor is not None and rating < floor:
        raise ValueError(f"power plant rating {rating} is below the {floor} its drives require")
    validate_rating(hull_class, hull_tons, drive, rating)
    return rating


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


def _read_configuration(answer: str) -> Configuration:
    try:
        return Configuration(answer.lower())
    except ValueError:
        known = sorted(shape.value for shape in Configuration)
        raise ValueError(f"{answer} is not a known configuration; known: {known}") from None


def _read_computer(answer: str) -> ComputerFit | Absent:
    """The computer as a bare model number; `ComputerFit` rules on the model.

    Software, hardening and jump control are out of scope for the wizard and
    remain reachable through hand-authored TOML (#41, Out of Scope).
    """
    if answer.lower() == _NONE:
        return ABSENT
    try:
        model = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a computer model") from None
    return ComputerFit(model=model)


def _read_electronics(answer: str) -> str | Absent:
    if answer.lower() == _NONE:
        return ABSENT
    validate_electronics(answer.lower())
    return answer.lower()


def _read_staterooms(answer: str) -> int:
    """A count, where `none` is the deliberate zero rather than an absent answer."""
    if answer.lower() == _NONE:
        return 0
    try:
        count = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a number of staterooms") from None
    if count < 0:
        raise ValueError(f"staterooms cannot be negative, got {count}")
    return count


def _read_fitting(answer: str) -> FittingFit | Absent:
    """A fitting kind; `FittingFit` rules on whether it is one.

    Quantity and vehicle tonnage are deliberately not askable (#41, Out of
    Scope), so a vehicle-sized fitting is refused here by the record that needs
    them and stays reachable through hand-authored TOML.
    """
    if answer.lower() == _NONE:
        return ABSENT
    return FittingFit(kind=answer.lower())


def _read_bay(answer: str) -> BayFit | Absent:
    return ABSENT if answer.lower() == _NONE else BayFit(kind=answer.lower())


def _read_screen(answer: str) -> ScreenFit | Absent:
    return ABSENT if answer.lower() == _NONE else ScreenFit(kind=answer.lower())


def _read_name(answer: str) -> str | Absent:
    """The ship's name, taken as written. `none` pins a ship with no name of its
    own, which is a different answer from letting the catalogue supply one.

    The shape rules `ShipDesign` applies to author prose—one line, single
    spaces—are not repeated here. They live with the record that renders them,
    and surface at assembly (ADR-0001).
    """
    return ABSENT if answer.lower() == _NONE else answer


def _read_purpose(answer: str) -> str | None:
    """The ship's purpose, which is never rolled: `none` and Enter agree here."""
    return None if answer.lower() == _NONE else answer


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

    def ask_rating(question: str, drive: Drive, floor: int | None = None) -> int | None:
        return _ask_until_understood(
            question, partial(_read_rating, hull_class, hull_tons, drive, floor)
        )

    configuration = _ask_until_understood("Configuration", _read_configuration)

    jump_rating = (
        None
        if hull_class is HullClass.SMALL_CRAFT
        else ask_rating("Jump rating", Drive.JUMP)  # small craft carry no jump drive
    )
    maneuver_rating = ask_rating("Maneuver rating", Drive.MANEUVER)

    floor = power_floor(hull_class, jump_rating, maneuver_rating)
    power_question = (
        "Power plant rating" if floor is None else f"Power plant rating (at least {floor})"
    )
    power_rating = ask_rating(power_question, Drive.POWER, floor)

    armor = _ask_until_understood("Armor", _read_armor)
    computer = _ask_until_understood("Computer model", _read_computer)
    electronics = _ask_until_understood("Electronics", _read_electronics)
    staterooms = _ask_until_understood("Staterooms", _read_staterooms)
    fitting = _ask_until_understood("Fitting", _read_fitting)
    bay = _ask_until_understood("Weapon bay", _read_bay)
    screen = _ask_until_understood("Screen", _read_screen)
    name = _ask_until_understood("Name", _read_name)
    purpose = _ask_until_understood("Purpose", _read_purpose, default_label=_NONE)

    return DesignConstraints(
        hull_class=hull_class,
        hull_tons=hull_tons,
        configuration=configuration,
        jump_rating=jump_rating,
        maneuver_rating=maneuver_rating,
        power_rating=power_rating,
        armor=armor,
        computer=computer,
        electronics=electronics,
        staterooms=staterooms,
        fitting=fitting,
        bay=bay,
        screen=screen,
        name=name,
        purpose=purpose,
    )


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
