import random
import sys
from collections.abc import Callable, Iterable
from dataclasses import fields
from functools import partial
from pathlib import Path
from typing import Annotated

import typer

from cetools.cli import prompts
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
    GenerationResult,
    HullClass,
    ScreenFit,
    Ship,
    TurretPin,
    UnmetConstraint,
    bay_kinds,
    build_ship,
    computer_models,
    dump_design,
    electronics_packages,
    fitting_kinds,
    generate_ship,
    load_design,
    power_floor,
    render_description,
    screen_kinds,
    small_craft_maneuver_ratings,
    small_craft_power_ratings,
    turret_mounts,
    turret_weapons,
    validate_hull_tons,
    validate_rating,
    validate_small_craft_weapon,
    validate_turret_count,
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


def _spelled(values: Iterable) -> list[str]:
    """`prompts.spell` mapped over a set of words—the default rendering for
    `_closed_set`. A numeric set is rendered with `prompts.numbers` instead,
    which collapses runs rather than mapping per value."""
    return [prompts.spell(value) for value in values]


def _closed_set(
    question: str,
    values: Iterable,
    render: Callable[[Iterable], Iterable[str]] = _spelled,
    *,
    none: bool = False,
    note: str = "",
) -> tuple[str, list[str]]:
    """Compose a closed-set question, and hand back its values as displayed.

    Returns the question text with the value list composed in, and that same
    list, so a reader's own refusal can name exactly what the prompt named
    instead of spelling its own (FR-016). `none=True` appends the literal
    `none` last, per FR-002's ordering.
    """
    displayed = list(render(values))
    if none:
        displayed = displayed + [_NONE]
    return prompts.offer(question, displayed, note=note), displayed


def _read_hull_class(known: list[str], answer: str) -> HullClass:
    """Which ruleset the ship builds under, spelled either way a referee might."""
    try:
        return HullClass(prompts.key(answer))
    except ValueError:
        raise ValueError(
            f"{answer} is not a known hull class; known: {', '.join(known)}"
        ) from None


def _read_maneuver_rating(hull_class: HullClass, hull_tons: int | None, answer: str) -> int:
    """A manoeuvre rating, narrowed to what a small craft can actually carry.

    The drive table tabulates ratings this hull could reach in isolation, but a
    craft also needs a plant and a cockpit. Refusing here keeps the power prompt
    that follows from having no acceptable answer at all.
    """
    rating = _read_rating(hull_class, hull_tons, Drive.MANEUVER, None, answer)

    if hull_class is HullClass.SMALL_CRAFT and hull_tons is not None:
        carryable = small_craft_maneuver_ratings(hull_tons)
        if rating not in carryable:
            raise ValueError(
                f"a {hull_tons}-ton small craft cannot carry a {rating}-G drive and a "
                f"power plant beside it; available: {list(carryable)}"
            )
    return rating


def _read_power_rating(
    hull_class: HullClass,
    hull_tons: int | None,
    floor: int | None,
    maneuver_rating: int | None,
    answer: str,
) -> int:
    """A power plant rating, narrowed on the small-craft path.

    There the pair is chosen jointly, so a manoeuvre drive already pinned rules
    out plants too weak to power it or too heavy to sit beside it. Offering a
    rating generation would then have to decline would be promising more than
    the hull can give.
    """
    rating = _read_rating(hull_class, hull_tons, Drive.POWER, floor, answer)

    if hull_class is HullClass.SMALL_CRAFT and hull_tons is not None and maneuver_rating:
        offered = small_craft_power_ratings(hull_tons, maneuver_rating)
        if rating not in offered:
            raise ValueError(
                f"power rating {rating} is not available beside a {maneuver_rating}-G "
                f"drive on a {hull_tons}-ton hull; available: {list(offered)}"
            )
    return rating


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


def _read_armor(known: list[str], answer: str) -> ArmorFit | Absent:
    """One armour layer from `<type> <percent>`, or `ABSENT` from `none`.

    Any SRD type may be pinned, including ones generation would never roll. The
    multiple-of-5 rule is *not* checked here: it lives in `build_ship` and is
    deliberately not duplicated outward, so it surfaces at assembly.

    The type may be more than one word (`bonded superdense`), so the **last**
    whitespace-separated token is taken as the percent and everything before
    it as the type, rather than requiring exactly two tokens.
    """
    if prompts.key(answer) == _NONE:
        return ABSENT

    parts = answer.split()
    if len(parts) < 2:
        raise ValueError(f'give an armor type and a percent, like "crystaliron 10"; got {answer}')

    *type_words, percent_text = parts
    name = prompts.key(" ".join(type_words))
    try:
        kind = ArmorType(name)
    except ValueError:
        raise ValueError(f"{name} is not a known armor type; known: {', '.join(known)}") from None
    try:
        percent = int(percent_text.removesuffix("%"))  # a referee may well type "10%"
    except ValueError:
        raise ValueError(f"{percent_text} is not a percent of the hull") from None

    return ArmorFit(type=kind, percent=percent)  # rejects a non-positive percent


def _read_configuration(known: list[str], answer: str) -> Configuration:
    try:
        return Configuration(prompts.key(answer))
    except ValueError:
        raise ValueError(
            f"{answer} is not a known configuration; known: {', '.join(known)}"
        ) from None


def _read_computer(known: list[str], answer: str) -> ComputerFit | Absent:
    """The computer as a bare model number; `ComputerFit` rules on the model.

    Software, hardening and jump control are out of scope for the wizard and
    remain reachable through hand-authored TOML (#41, Out of Scope).
    """
    if prompts.key(answer) == _NONE:
        return ABSENT
    try:
        model = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a computer model") from None
    if model not in computer_models():
        raise ValueError(f"unknown computer model {model}; known: {', '.join(known)}")
    return ComputerFit(model=model)


def _read_electronics(known: list[str], answer: str) -> str | Absent:
    stored = prompts.key(answer)
    if stored == _NONE:
        return ABSENT
    if stored not in electronics_packages():
        raise ValueError(f"unknown electronics package {stored!r}; known: {', '.join(known)}")
    return stored


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


def _read_fitting(known: list[str], answer: str) -> FittingFit | Absent:
    """A fitting kind; `FittingFit` rules on whether it is one.

    Quantity and vehicle tonnage are deliberately not askable (#41, Out of
    Scope). A vehicle-sized fitting is a real fitting the tables recognise, so
    it still reaches `FittingFit`'s own refusal for a missing `vehicle_tons`,
    unchanged from today (AS 1.7). The prompt's own refusal, in the displayed
    spelling, is reserved for a kind nothing recognises at all—found by
    probing whether a tonnage would have let the same kind through.
    """
    stored = prompts.key(answer)
    if stored == _NONE:
        return ABSENT
    try:
        return FittingFit(kind=stored)
    except ValueError as exc:
        try:
            FittingFit(kind=stored, vehicle_tons=1)
        except ValueError:
            raise ValueError(f"unknown fitting {stored!r}; known: {', '.join(known)}") from None
        raise exc


def _read_bay(known: list[str], answer: str) -> BayFit | Absent:
    stored = prompts.key(answer)
    if stored == _NONE:
        return ABSENT
    if stored not in bay_kinds():
        raise ValueError(f"unknown bay kind {stored!r}; known: {', '.join(known)}")
    return BayFit(kind=stored)


def _read_screen(known: list[str], answer: str) -> ScreenFit | Absent:
    stored = prompts.key(answer)
    if stored == _NONE:
        return ABSENT
    if stored not in screen_kinds():
        raise ValueError(f"unknown screen kind {stored!r}; known: {', '.join(known)}")
    return ScreenFit(kind=stored)


def _read_turret_mount(known: list[str], answer: str) -> str:
    stored = prompts.key(answer)
    if stored not in turret_mounts():
        raise ValueError(f"unknown turret mount {stored!r}; known: {', '.join(known)}")
    return stored


def _read_turret_weapon(known: list[str], answer: str) -> str:
    stored = prompts.key(answer)
    if stored not in turret_weapons():
        raise ValueError(f"unknown turret weapon {stored!r}; known: {', '.join(known)}")
    return stored


def _read_small_craft_weapon(
    hull_tons: int, power_rating: int, mount: str | None, answer: str
) -> str:
    """A small craft's weapon, checked against the plant that has to run it.

    The mount is known by now—it is asked first—and it decides how many of the
    weapon the turret carries, which is what the plant's allowance is counted
    against.
    """
    validate_small_craft_weapon(hull_tons, power_rating, answer.lower(), mount)
    return answer.lower()


def _read_turret_count(hull_class: HullClass, hull_tons: int | None, answer: str) -> int:
    """How many turrets to fit, where `none` is the deliberate unarmed ship.

    A count above the hull's hardpoints is refused here when the hull is
    settled, which it is by this point unless the referee left it to the dice.
    """
    if answer.lower() == _NONE:
        return 0
    try:
        count = int(answer)
    except ValueError:
        raise ValueError(f"{answer} is not a number of turrets") from None
    if count < 0:
        raise ValueError(f"turrets cannot be negative, got {count}")
    if hull_tons is not None:
        validate_turret_count(hull_class, hull_tons, count)
    return count


def _ask_turrets(
    hull_class: HullClass, hull_tons: int | None, power_rating: int | None
) -> tuple[TurretPin, ...] | None:
    """The turret count, then each turret's mount and weapon in turn.

    The one repeating structure in the session. Answering the count opens the
    inner questions; pressing Enter through them leaves that turret to chance,
    which is how a count-only answer works without a mode of its own.

    On a small craft the weapon is capped by the power plant, so the plant's
    rating is needed here. It is only known if the referee pinned it; otherwise
    the cap is applied when the weapon is drawn, as it always has been.
    """
    count = _ask_until_understood("Turrets", partial(_read_turret_count, hull_class, hull_tons))
    if count is None:
        return None

    capped = (
        hull_class is HullClass.SMALL_CRAFT and hull_tons is not None and power_rating is not None
    )

    pins = []
    for ordinal in range(1, count + 1):
        mount_question, mount_known = _closed_set(f"Turret {ordinal} mount", turret_mounts())
        mount = _ask_until_understood(mount_question, partial(_read_turret_mount, mount_known))

        if capped:
            weapon = _ask_until_understood(
                f"Turret {ordinal} weapon",
                partial(_read_small_craft_weapon, hull_tons, power_rating, mount),
            )
        else:
            weapon_question, weapon_known = _closed_set(
                f"Turret {ordinal} weapon", turret_weapons()
            )
            weapon = _ask_until_understood(
                weapon_question, partial(_read_turret_weapon, weapon_known)
            )
        pins.append(TurretPin(mount=mount, weapon=weapon))
    return tuple(pins)


def _read_name(answer: str) -> str | Absent:
    """The ship's name, taken as written. `none` pins a ship with no name of its
    own, which is a different answer from letting the catalogue supply one.

    The shape rules `ShipDesign` applies to author prose—one line, single
    spaces—are not repeated here. They live with the record that renders them,
    and surface at assembly.
    """
    return ABSENT if answer.lower() == _NONE else answer


def _read_purpose(answer: str) -> str | None:
    """The ship's purpose, which is never rolled: `none` and Enter agree here."""
    return None if answer.lower() == _NONE else answer


def _ask_constraints(
    hull_class: HullClass | None,
    hull: int | None,
    keep: DesignConstraints | None = None,
    revise: frozenset[str] = frozenset(),
) -> DesignConstraints:
    """Walk the referee through what they can pin, in SRD build order.

    A value a flag already supplied pre-answers its question and that question
    is not asked, so flags and prompts never ask the same thing twice.

    Hull class comes first because it governs the rest: it decides which hull
    tonnages are tabulated, and which questions are worth asking at all. A small
    craft carries no jump drive and no weapon bay, so a referee designing a
    launch is never asked about either.

    Passing `keep` walks the same order again but asks only the fields named in
    `revise`, taking every other answer from the session just held. A referee
    who has answered fourteen questions should not answer them all again over
    the one that did not fit.
    """

    def answered[T](field: str, ask: Callable[[], T]) -> T:
        """One question's answer: asked, or carried over from last time."""
        if keep is not None and field not in revise:
            return getattr(keep, field)
        return ask()

    def ask_closed[T](
        question: str,
        values: Iterable,
        read: Callable[[list[str], str], T],
        *,
        render: Callable[[Iterable], Iterable[str]] = _spelled,
        none: bool = False,
        note: str = "",
        default_label: str = _ROLL,
    ) -> T | None:
        """Compose a closed-set question with `_closed_set` and ask it."""
        text, known = _closed_set(question, values, render, none=none, note=note)
        return _ask_until_understood(text, partial(read, known), default_label=default_label)

    # Tonnage is tabulated per ruleset, so a revised hull class takes the
    # tonnage with it however the referee answered it: carrying a 200-ton
    # starship hull into a small-craft session buys a certain refusal, and
    # spends one of the five attempts on it.
    carried_hull_tons = keep is not None and not {"hull_tons", "hull_class"} & revise
    if keep is not None and "hull_class" not in revise:
        hull_class = keep.hull_class

    if hull_class is None:
        hull_class = (
            ask_closed(
                "Hull class",
                [ruleset.value for ruleset in HullClass],
                _read_hull_class,
                default_label=HullClass.STARSHIP.value,
            )
            or HullClass.STARSHIP
        )
    small_craft = hull_class is HullClass.SMALL_CRAFT

    if keep is not None:
        # The flag pre-answered the first round only. Afterwards the session's
        # own answer stands, so a revised tonnage is not overwritten by it.
        hull = None

    if carried_hull_tons:
        # Carried whole, `None` included: a hull the dice chose last time was an
        # answer too, and asking again would be re-asking an unimplicated question.
        hull_tons = keep.hull_tons  # type: ignore[union-attr]
    else:
        if hull is not None:
            try:
                validate_hull_tons(hull_class, hull)
            except ValueError as exc:
                # `--hull` pre-answers the question, but only with an answer this
                # ruleset accepts. The referee chose the class a moment ago, so
                # the flag is the stale half: say so and ask.
                typer.echo(str(exc), err=True)
                hull = None

        hull_tons = (
            hull
            if hull is not None
            else _ask_until_understood("Hull tonnage", partial(_read_hull_tons, hull_class))
        )

    def ask_rating(question: str, drive: Drive, floor: int | None = None) -> int | None:
        return _ask_until_understood(
            question, partial(_read_rating, hull_class, hull_tons, drive, floor)
        )

    configuration = answered(
        "configuration",
        lambda: ask_closed(
            "Configuration", [shape.value for shape in Configuration], _read_configuration
        ),
    )

    jump_rating = (
        None
        if small_craft
        else answered("jump_rating", lambda: ask_rating("Jump rating", Drive.JUMP))
    )
    maneuver_rating = answered(
        "maneuver_rating",
        lambda: _ask_until_understood(
            "Maneuver rating", partial(_read_maneuver_rating, hull_class, hull_tons)
        ),
    )

    floor = power_floor(hull_class, jump_rating, maneuver_rating)
    power_question = (
        "Power plant rating" if floor is None else f"Power plant rating (at least {floor})"
    )
    power_rating = answered(
        "power_rating",
        lambda: _ask_until_understood(
            power_question,
            partial(_read_power_rating, hull_class, hull_tons, floor, maneuver_rating),
        ),
    )

    armor = answered(
        "armor",
        lambda: ask_closed(
            "Armor",
            [kind.value for kind in ArmorType],
            _read_armor,
            note=", each with a percent, or none",
        ),
    )
    computer = answered(
        "computer",
        lambda: ask_closed(
            "Computer model", computer_models(), _read_computer, render=prompts.numbers, none=True
        ),
    )
    electronics = answered(
        "electronics",
        lambda: ask_closed("Electronics", electronics_packages(), _read_electronics, none=True),
    )
    staterooms = answered(
        "staterooms",
        lambda: _ask_until_understood(
            prompts.offer("Staterooms", [], note="a count, or none"), _read_staterooms
        ),
    )
    fitting = answered(
        "fitting", lambda: ask_closed("Fitting", fitting_kinds(), _read_fitting, none=True)
    )
    turrets = answered("turrets", lambda: _ask_turrets(hull_class, hull_tons, power_rating))
    bay = (
        None
        if small_craft
        else answered("bay", lambda: ask_closed("Weapon bay", bay_kinds(), _read_bay, none=True))
    )
    screen = answered(
        "screen",
        # A screen is never rolled onto a small craft, so Enter there pins
        # absence. Labelling it `[roll]` would promise a draw generation does
        # not make—the one field whose default did something other than it said.
        lambda: ask_closed(
            "Screen",
            screen_kinds(),
            _read_screen,
            none=True,
            default_label=_NONE if small_craft else _ROLL,
        ),
    )
    name = answered(
        "name",
        lambda: _ask_until_understood(
            prompts.offer("Name", [], note="any text, or none"), _read_name
        ),
    )
    purpose = answered(
        "purpose",
        lambda: _ask_until_understood("Purpose", _read_purpose, default_label=_NONE),
    )

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
        turrets=turrets,
        bay=bay,
        screen=screen,
        name=name,
        purpose=purpose,
    )


_MAX_ATTEMPTS = 5
"""How many ships a session may try before it settles for what it has.

A referee who answers the same way each time would otherwise revise forever.
The cap is generous enough that no honest revision reaches it and small enough
that a mistaken one ends. Four revisions, then the fifth ship stands.
"""

_REVISABLE = tuple(field.name for field in fields(DesignConstraints))


def _read_fields(answer: str) -> frozenset[str]:
    """The answers a referee named, space-separated, checked against the record."""
    named = answer.replace(",", " ").split()
    unknown = [field for field in named if field not in _REVISABLE]
    if unknown:
        raise ValueError(f"no such answer: {' '.join(unknown)}; known: {list(_REVISABLE)}")
    return frozenset(named)


def _ask_which_to_revise() -> frozenset[str]:
    """Which answers to put back to the referee after a refusal.

    An unmet constraint names its own field, so nothing has to be guessed there.
    A rules refusal is a sentence: `build_ship` is the sole authority on those
    rules and does not carry a field alongside them, and reading fields out of
    its prose guesses wrongly more often than not—"a distributed hull cannot
    mount fuel scoops" is about the configuration and the fitting, and mentions
    neither by name. So the referee is asked, having just been told the reason.
    """
    return _ask_until_understood(
        "Revise which answers", _read_fields, default_label="all"
    ) or frozenset(_REVISABLE)


def _read_verdict(answer: str) -> bool:
    """Whether the referee asked to revise. Anything else is a typo, not consent."""
    if answer.lower() in {"revise", "r"}:
        return True
    if answer.lower() in {"accept", "a"}:
        return False
    raise ValueError(f"answer accept or revise; got {answer}")


def _ask_to_revise() -> bool:
    """Whether the referee wants another go. Accepting is the default, because
    a degraded ship is still a ship and the session has already cost them."""
    return bool(_ask_until_understood("Accept this ship or revise", _read_verdict, "accept"))


def _report_unmet(unmet: tuple[UnmetConstraint, ...]) -> None:
    """Say plainly which answers the tonnage could not honour.

    On stderr and never on stdout, so a degraded ship still pipes; and without
    an error exit, because a ship really was produced. A referee who is handed
    a lesser ship in silence would believe they got what they asked for, which
    is the whole reason the record exists.
    """
    if not unmet:
        return

    typer.echo(f"could not honour {len(unmet)} constraint(s):", err=True)
    for entry in unmet:
        typer.echo(
            f"  {entry.field}: asked {entry.asked}, got {entry.got} ({entry.reason})", err=True
        )


def _generate(seed: int, constraints: DesignConstraints) -> GenerationResult:
    """Generate, turning a refusal into the exit code it has always had."""
    try:
        return generate_ship(RandomRolls.seeded(seed), constraints=constraints)
    except ValueError as exc:
        typer.echo(str(exc), err=True)
        raise typer.Exit(1)


def _run_session(seed: int, hull_class: HullClass | None, hull: int | None) -> Ship:
    """Ask, generate, and offer the referee the ship or another go.

    Three outcomes at assembly, and this is where the middle two are handled.
    *Met* hands back the ship. *Unmet* reports the shortfalls and asks; the
    referee can take the degraded ship or revise the answers the report names.
    *Illegal* has no ship to offer at all, so it goes straight back to the
    answers its refusal points at rather than costing the session.
    """
    constraints = _ask_constraints(hull_class, hull)

    for attempt in range(_MAX_ATTEMPTS):
        last = attempt == _MAX_ATTEMPTS - 1

        try:
            result = generate_ship(RandomRolls.seeded(seed), constraints=constraints)
        except ValueError as exc:
            typer.echo(str(exc), err=True)
            if last:
                typer.echo("revised enough; these answers still do not build", err=True)
                raise typer.Exit(1)
            implicated = _ask_which_to_revise()
        else:
            if not result.unmet:
                return result.ship
            _report_unmet(result.unmet)
            if not _ask_to_revise():
                return result.ship
            if last:
                typer.echo("revised enough; taking the ship as it stands", err=True)
                return result.ship
            implicated = frozenset(entry.field for entry in result.unmet)

        constraints = _ask_constraints(hull_class, hull, constraints, implicated)

    raise AssertionError("every attempt returns or revises")


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

    if not interactive:
        result = _generate(seed, DesignConstraints(hull_class=hull_class, hull_tons=hull))
        _report_unmet(result.unmet)
        ship = result.ship
    else:
        # `--small-craft` pre-answers the hull class; without it the session asks.
        ship = _run_session(seed, hull_class if small_craft else None, hull)

    output = dump_design(ship.design) if toml else render_description(ship)

    if out is not None:
        out.write_text(output, encoding="utf-8")
    else:
        typer.echo(output)
