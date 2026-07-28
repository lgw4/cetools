"""generate_ship(rolls=None, *, constraints=DesignConstraints()) -> GenerationResult.

Selects rules-legal components through the `Rolls` seam, reading the same
`tables.py` data `build_ship` validates against, and assembles a `ShipDesign`
that is legal by construction: tonnage is tracked against a running budget so
no candidate is ever chosen that would over-allocate the hull. Ends by calling
`build_ship`, so a generated ship can never be rules-illegal (FR-016, SC-003).

Everything a referee pins arrives on one `DesignConstraints` value rather than
as a keyword per field, so the interactive wizard in `cli/ship.py` is a thin
layer over the same seam a library caller uses.

`HullClass.SMALL_CRAFT` selects under the small-craft ruleset (SRD "Small Craft
Design"): a 10-95 ton hull, a cockpit instead of a bridge, no jump drive, and
turret weapons constrained to the power plant's energy-weapon cap. Maneuver and
power drive codes are chosen together, since a small hull's tight tonnage budget
means the choice must be filtered for affordability up front rather than
corrected after the fact (unlike the starship path's looser margins).

Bays and screens (SRD "Bays" and "Screens", FR-020) are only ever offered on the
standard-hull path, and only among kinds that fit the hardpoints and tonnage
still free after turrets are chosen—never on small craft, which forbid bays
outright.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from operator import attrgetter

from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.ships.builder import BAY_FIRE_CONTROL_TONS, build_ship
from cetools.engine.ships.models import (
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    FittingFit,
    HullClass,
    ScreenFit,
    Ship,
    ShipDesign,
    SoftwareFit,
    TurretFit,
)
from cetools.engine.ships.names import generate_ship_name
from cetools.engine.ships.tables import (
    BAYS,
    BRIDGE_SIZES,
    COCKPITS,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    QUARTERS,
    SCREENS,
    SMALL_CRAFT_DRIVE_PERFORMANCE,
    SMALL_CRAFT_ENERGY_CAPS,
    SMALL_CRAFT_HULLS,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
    DriveRow,
)

_STANDARD_POWER_WEEKS = 2
_SMALL_CRAFT_POWER_WEEKS = 1
_MIN_COCKPIT_TONS = min(row.tons for row in COCKPITS.values())


class Absent(Enum):
    """The type of `ABSENT`, which is the only member worth naming."""

    TOKEN = "absent"


ABSENT = Absent.TOKEN
"""Pins a component's absence: the referee said *no armour*, not nothing at all.

An optional-component field is three-state, and a plain `X | None` cannot carry
it: `None` already means "unset, roll it", so reusing it for "do not fit one"
silently turns a deliberate answer into a random one. That confusion is the
whole reason the `none` keyword exists at the prompt, so the value it produces
has to be distinguishable from an unanswered question (FR, ADR-0001).

An `Enum` of one member rather than a bare `object()`, so it is a *type* an
annotation can name and a reader can follow.
"""


@dataclass(frozen=True)
class TurretPin:
    """What a referee pinned about one turret; each half answers on its own.

    Not a `TurretFit`, because a fit is a finished turret: it knows its mount
    and carries a weapon in every slot the mount holds. A pin may name a weapon
    while leaving the mount to chance, which is exactly the answer a referee
    gives when they care about the beam lasers and not the housing.

    A tuple of these *is* the turret count, so `()` pins an unarmed ship and a
    tuple of empty pins asks for that many turrets with everything else rolled.
    """

    mount: str | None = None
    weapon: str | None = None


@dataclass(frozen=True)
class DesignConstraints:
    """What a referee pinned; everything left unset is rolled.

    One value rather than a keyword per field, because the constrainable surface
    is the whole of roll parity and a signature cannot carry it. Prompting is a
    thin layer over this record, so a library caller reaches the same capability
    without a conversation.

    `hull_class` has no unset state: every ship builds under one ruleset or the
    other, and the generator has always defaulted to starship. Nor is it
    three-state: a ship with no hull class is not a ship. Optional *components*
    are three-state—unset rolls, a value pins, `ABSENT` pins absence.
    """

    hull_class: HullClass = HullClass.STARSHIP
    hull_tons: int | None = None
    configuration: Configuration | None = None
    jump_rating: int | None = None
    maneuver_rating: int | None = None
    power_rating: int | None = None
    armor: ArmorFit | Absent | None = None
    computer: ComputerFit | Absent | None = None
    electronics: str | Absent | None = None
    staterooms: int | None = None
    fitting: FittingFit | Absent | None = None
    turrets: tuple[TurretPin, ...] | None = None
    bay: BayFit | Absent | None = None
    screen: ScreenFit | Absent | None = None
    name: str | Absent | None = None
    purpose: str | None = None
    """Never rolled: cetools does not invent a ship's purpose, so unset means the
    design carries none rather than a random one."""


UNCONSTRAINED = DesignConstraints()
"""Roll everything—the behaviour `generate_ship` had before it took constraints."""


@dataclass(frozen=True)
class UnmetConstraint:
    """A pinned value the tonnage budget could not accommodate.

    Carries the reason as well as the values, because "why" is only knowable
    where the shortfall is detected: once a design is assembled, the tonnage that
    was free at the moment of the decision is gone.

    A *rolled* value that will not fit is declined silently and produces none of
    these—it was a preference, not a promise. See
    `docs/adr/0001-constrained-ship-generation.md`.
    """

    field: str
    asked: str
    got: str
    reason: str


def _tons(value: float) -> str:
    """Tonnage for a reason string: whole numbers plain, fractions as they are.

    Not `prose.tons`, which spells whole numbers as words for the description; a
    shortfall is read as a number standing beside another number.
    """
    return f"{value:g}"


class TonnageLedger:
    """The running tonnage budget the selection steps spend against.

    Replaces a `remaining` float threaded by hand from step to step. The steps
    hold the ledger and spend from it, so a step that has to decline a component
    can record *why* without every step's return type growing a third value.

    Mutable by design, unlike the frozen records elsewhere in this package: it is
    an accumulator, and the accumulation is the point.
    """

    def __init__(self, tons: float) -> None:
        self._remaining = tons
        self._declined: list[UnmetConstraint] = []

    @property
    def remaining(self) -> float:
        """The tonnage not yet allocated."""
        return self._remaining

    @property
    def declined(self) -> tuple[UnmetConstraint, ...]:
        """Every pinned value recorded as unaffordable, in the order recorded."""
        return tuple(self._declined)

    def affords(self, tons: float) -> bool:
        """Whether `tons` still fits. Steps ask before they spend."""
        return tons <= self._remaining

    def spend(self, tons: float) -> None:
        """Allocate `tons`. Callers check `affords` first; nothing here enforces
        it, so that this remains arithmetic and never a new failure mode."""
        self._remaining -= tons

    def decline(self, field: str, asked: str, got: str, reason: str) -> None:
        """Record that `field` could not have `asked`, what it got instead, and why."""
        self._declined.append(UnmetConstraint(field=field, asked=asked, got=got, reason=reason))

    def decline_unaffordable(self, field: str, asked: str, cost: float) -> None:
        """Record that `asked` needed `cost` tons the budget could not cover.

        The commonest shortfall by far, and the arithmetic behind it is the
        ledger's own, so the sentence is composed here once rather than at every
        step that has to say it.
        """
        self.decline(field, asked, "none", f"needs {_tons(cost)}t, {_tons(self._remaining)}t free")


@dataclass(frozen=True)
class GenerationResult:
    """What generation produced, and what it could not honour.

    Generation never fails on tonnage: a pinned value that will not fit is
    declined and recorded here, so a caller always gets a ship and can ask
    separately whether it is the ship that was asked for.
    """

    ship: Ship
    unmet: tuple[UnmetConstraint, ...] = ()


_ARMOR_CHOICES: tuple[ArmorFit | None, ...] = (
    None,
    ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=5),
    ArmorFit(type=ArmorType.TITANIUM_STEEL, percent=10),
    ArmorFit(type=ArmorType.CRYSTALIRON, percent=5),
)

_COMPUTER_PROFILES: tuple[ComputerFit | None, ...] = (
    None,
    ComputerFit(model=1),
    ComputerFit(model=2),
    ComputerFit(model=2, software=(SoftwareFit(name="jump_control", level=1),)),
    ComputerFit(model=3, software=(SoftwareFit(name="fire_control", level=1),)),
)

_ELECTRONICS_CHOICES: tuple[str, ...] = tuple(ELECTRONICS)

_FITTING_CHOICES: tuple[str | None, ...] = (
    None,
    "armory",
    "laboratory",
    "library",
    "luxuries",
    "fuel_processor",
    "detention_cell",
)

_TURRET_MOUNTS: tuple[str, ...] = tuple(sorted(TURRET_MOUNTS))
_TURRET_WEAPONS: tuple[str, ...] = tuple(sorted(TURRET_WEAPONS))
_NON_ENERGY_TURRET_WEAPONS: tuple[str, ...] = tuple(
    w for w in _TURRET_WEAPONS if not TURRET_WEAPONS[w].energy
)
_SMALL_CRAFT_TURRET_MOUNTS: tuple[str, ...] = tuple(
    sorted(name for name, row in TURRET_MOUNTS.items() if row.weapon_slots == 1)
)
"""Small craft get one hardpoint and one weapon; restricting to single-slot
mounts keeps a turret's energy-weapon contribution at 0 or 1, so it can be
checked directly against the power plant's cap without summing per-slot."""


def validate_hull_tons(hull_class: HullClass, tons: int) -> None:
    """Raise `ValueError` unless `tons` is a tabulated hull size for `hull_class`.

    Tabulation is the whole of it: `build_ship` remains the sole authority on
    rules legality. This is exposed because the same sentence has to serve two
    moments—the wizard rejecting an answer where it was typed, and generation
    rejecting a pin from a library caller who never saw a prompt—and a referee
    who is told two different things about one mistake is being told one of them
    wrongly.
    """
    if hull_class is HullClass.SMALL_CRAFT:
        if tons not in SMALL_CRAFT_HULLS:
            raise ValueError(
                f"{tons} tons is not a tabulated small-craft hull size; "
                f"valid: {sorted(SMALL_CRAFT_HULLS)}"
            )
    elif tons not in HULLS:
        raise ValueError(f"{tons} tons is not a tabulated hull size; valid: {sorted(HULLS)}")


def _validate_key(name: str, table: Mapping[str, object], what: str) -> None:
    """Raise `ValueError` unless `name` is a key of `table`.

    Every value a referee can pin by name earns the same sentence, whether they
    typed it at a prompt or a library caller passed it in a value. Component-fit
    records make this check for themselves; these are the fields that arrive as
    bare table keys with no record to rule on them.
    """
    if name not in table:
        raise ValueError(f"unknown {what} {name!r}; known: {sorted(table)}")


def validate_electronics(name: str) -> None:
    """Raise `ValueError` unless `name` is a tabulated electronics package."""
    _validate_key(name, ELECTRONICS, "electronics package")


def validate_turret_mount(name: str) -> None:
    """Raise `ValueError` unless `name` is a tabulated turret mount."""
    _validate_key(name, TURRET_MOUNTS, "turret mount")


def validate_turret_weapon(name: str) -> None:
    """Raise `ValueError` unless `name` is a tabulated turret weapon."""
    _validate_key(name, TURRET_WEAPONS, "turret weapon")


def _hardpoints_for(hull_class: HullClass, hull_tons: int) -> int:
    """How many turrets this hull can mount.

    A starship gets one hardpoint per 100 tons; a small craft gets exactly one
    however small it is, which is why the ruleset has to be named here—counting
    a 40-ton launch by the starship rule would give it none at all.
    """
    if hull_class is HullClass.SMALL_CRAFT:
        return 1
    return hull_tons // 100


def validate_turret_count(hull_class: HullClass, hull_tons: int, count: int) -> None:
    """Raise `ValueError` unless this hull has hardpoints for `count` turrets.

    Knowable at the point of input, unlike affordability: hardpoints follow from
    the hull alone, which is settled before turrets are ever asked about.
    """
    hardpoints = _hardpoints_for(hull_class, hull_tons)
    if count > hardpoints:
        raise ValueError(
            f"a {hull_tons}-ton {hull_class.value.replace('_', ' ')} has "
            f"{hardpoints} hardpoint(s), so it cannot mount {count}"
        )


def _select_hull_tons(rolls: Rolls, pinned_tons: int | None) -> int:
    if pinned_tons is not None:
        validate_hull_tons(HullClass.STARSHIP, pinned_tons)
        return pinned_tons
    return rolls.choose(sorted(HULLS), RollName.SHIP_HULL_SIZE)


def _select_name(rolls: Rolls, pinned: str | Absent | None) -> str:
    """The ship's name, drawn last on both paths so naming stays purely additive.

    `ABSENT` pins a ship that carries no name of its own, which the description
    renderer already understands: a blank name renders as an unnamed ship. That
    is a different answer from leaving the field to the catalogue.
    """
    if pinned is ABSENT:
        return ""
    if isinstance(pinned, str):
        return pinned
    return generate_ship_name(rolls)


def _select_configuration(rolls: Rolls, pinned: Configuration | None) -> Configuration:
    if pinned is not None:
        return pinned
    return rolls.choose(list(Configuration), RollName.SHIP_CONFIGURATION)


def _codes_valid_for_hull(hull_tons: int) -> list[str]:
    return sorted(code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings)


class Drive(Enum):
    """One of the three drives a design fits.

    Exists because a rating means nothing without saying which drive delivers
    it: the same letter weighs three different amounts, and the performance
    tables are read the same way for all three. Naming the drive keeps one
    validator and one resolver serving all of them.
    """

    JUMP = "jump"
    MANEUVER = "maneuver"
    POWER = "power"


_DRIVE_TONS: dict[Drive, Callable[[DriveRow], float]] = {
    Drive.JUMP: attrgetter("jump_tons"),
    Drive.MANEUVER: attrgetter("maneuver_tons"),
    Drive.POWER: attrgetter("power_tons"),
}


def _ratings_table(hull_class: HullClass) -> dict[str, dict[int, int]]:
    return (
        SMALL_CRAFT_DRIVE_PERFORMANCE if hull_class is HullClass.SMALL_CRAFT else DRIVE_PERFORMANCE
    )


def available_ratings(hull_class: HullClass, hull_tons: int | None) -> tuple[int, ...]:
    """Every rating some drive can deliver on `hull_tons`, ascending.

    `hull_tons` of `None` widens the answer to every hull of the class, which is
    what the wizard can offer when the referee left the hull to the dice: it can
    still catch a rating no hull could ever deliver, just not one this hull
    cannot.
    """
    table = _ratings_table(hull_class)
    if hull_tons is None:
        return tuple(sorted({rating for ratings in table.values() for rating in ratings.values()}))
    return tuple(
        sorted({ratings[hull_tons] for ratings in table.values() if hull_tons in ratings})
    )


def validate_rating(
    hull_class: HullClass, hull_tons: int | None, drive: Drive, rating: int
) -> None:
    """Raise `ValueError` unless `drive` can deliver `rating` on this hull.

    Shared by the wizard and the selection steps for the same reason
    `validate_hull_tons` is: one mistake earns one sentence, whether the referee
    typed it at a prompt or a library caller passed it in a value.
    """
    if drive is Drive.JUMP and hull_class is HullClass.SMALL_CRAFT:
        raise ValueError("small craft carry no jump drive, so no jump rating can be pinned")

    available = available_ratings(hull_class, hull_tons)
    if rating not in available:
        where = (
            f"a {hull_tons}-ton hull" if hull_tons is not None else f"any {hull_class.value} hull"
        )
        raise ValueError(
            f"{drive.value} rating {rating} is not tabulated for {where}; "
            f"available: {list(available)}"
        )


def power_floor(
    hull_class: HullClass, jump_rating: int | None, maneuver_rating: int | None
) -> int | None:
    """The rating a power plant must at least match, as far as it is yet known.

    The SRD rule is `build_ship`'s to enforce; this states it early so a prompt
    can show the floor and refuse an answer beneath it. Only pinned ratings
    count: a drive left to the dice has no rating yet, and a floor guessed from
    a drive that has not been chosen would be a lie. A small craft carries no
    jump drive, so its manoeuvre drive alone sets the floor.
    """
    if hull_class is HullClass.SMALL_CRAFT:
        return maneuver_rating
    pinned = [rating for rating in (jump_rating, maneuver_rating) if rating is not None]
    return max(pinned) if pinned else None


def _lightest_code_at(
    candidates: Iterable[str], hull_class: HullClass, hull_tons: int, drive: Drive, rating: int
) -> str | None:
    """The lightest of `candidates` delivering `rating` on this hull, or `None`.

    The same rule `_fit_jump_drive` already applies to a drawn drive, applied to
    a pinned one: tonnage not spent on the drive flows on to fuel and fittings
    (FR-004).
    """
    table = _ratings_table(hull_class)
    tons_of = _DRIVE_TONS[drive]
    at_rating = [code for code in candidates if table[code].get(hull_tons) == rating]
    if not at_rating:
        return None
    return min(at_rating, key=lambda code: tons_of(DRIVE_COSTS[code]))


def _fit_jump_drive(hull_tons: int, drawn_code: str, budget: float) -> str:
    """The lightest jump drive affording the highest rating `budget` buys,
    never rated above `drawn_code`.

    Total: `drawn_code` is itself legal for `hull_tons`, so a candidate always
    exists at every rating up to its own—step 4 never has to look further.
    """
    ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]
    legal = [
        c for c in _codes_valid_for_hull(hull_tons) if DRIVE_PERFORMANCE[c][hull_tons] <= ceiling
    ]

    lightest_by_rating: dict[int, str] = {}
    for rating in sorted({DRIVE_PERFORMANCE[c][hull_tons] for c in legal}):
        lightest_by_rating[rating] = min(
            (c for c in legal if DRIVE_PERFORMANCE[c][hull_tons] == rating),
            key=lambda c: DRIVE_COSTS[c].jump_tons,
        )

    for rating in sorted(lightest_by_rating, reverse=True):
        code = lightest_by_rating[rating]
        if DRIVE_COSTS[code].jump_tons + 0.1 * hull_tons * rating <= budget:
            return code
    return lightest_by_rating[min(lightest_by_rating)]


def _select_drive_codes(
    rolls: Rolls, hull_tons: int, constraints: DesignConstraints
) -> tuple[str, str, str]:
    """Jump, manoeuvre and power codes, drawn in that order unless pinned.

    A pinned rating resolves without a draw, so the codes left to chance shift
    down the roll stream. That is the documented cost of pinning consuming no
    dice (ADR-0001): two runs on one seed diverge below the first pin.

    A pinned power rating is *not* floored at the drives it must support. The
    prompt states the floor and rejects an answer below it, and `build_ship`
    rejects the design outright—duplicating the rule here would make it a third
    authority on a rule the builder already owns.
    """
    valid = _codes_valid_for_hull(hull_tons)

    def pinned_or_drawn(
        drive: Drive, rating: int | None, roll: RollName, candidates: list[str]
    ) -> str:
        if rating is None:
            return rolls.choose(candidates, roll)
        validate_rating(HullClass.STARSHIP, hull_tons, drive, rating)
        code = _lightest_code_at(candidates, HullClass.STARSHIP, hull_tons, drive, rating)
        if code is None:
            raise AssertionError(
                f"{drive.value} rating {rating} passed validation for a {hull_tons}-ton hull "
                "but no code delivers it; the validator and the tables disagree"
            )
        return code

    jump_code = pinned_or_drawn(
        Drive.JUMP, constraints.jump_rating, RollName.SHIP_JUMP_CODE, valid
    )
    maneuver_code = pinned_or_drawn(
        Drive.MANEUVER, constraints.maneuver_rating, RollName.SHIP_MANEUVER_CODE, valid
    )

    required = max(
        DRIVE_PERFORMANCE[jump_code][hull_tons],
        DRIVE_PERFORMANCE[maneuver_code][hull_tons],
    )
    power_code = pinned_or_drawn(
        Drive.POWER,
        constraints.power_rating,
        RollName.SHIP_POWER_CODE,
        # A pinned plant resolves against every code the hull takes, not only
        # those clearing `required`: a referee is allowed to ask for one too
        # small, and `build_ship` is the authority that refuses it.
        (
            valid
            if constraints.power_rating is not None
            else [c for c in valid if DRIVE_PERFORMANCE[c][hull_tons] >= required]
        ),
    )
    return jump_code, maneuver_code, power_code


def _bridge_tons(hull_tons: int) -> int:
    for max_tons, bridge_tons in BRIDGE_SIZES:
        if max_tons is None or hull_tons <= max_tons:
            return bridge_tons
    raise AssertionError("BRIDGE_SIZES must end with an unbounded (None, tons) step")


def _pin_or_draw[T](
    pinned: T | Absent | None,
    ledger: TonnageLedger,
    field: str,
    tons: Callable[[T], float],
    asked: Callable[[T], str],
    draw: Callable[[], T | None],
) -> T | None:
    """One optional component, resolved from the referee's answer or the dice.

    The three states in one place, because every optional component answers them
    identically: `ABSENT` fits nothing and draws nothing, a pinned value is
    installed if the budget covers it and recorded as unmet if it does not, and
    an unset field falls through to `draw`.

    A pinned value's tonnage is the only thing checked here. Whether it is
    *legal* was settled when the referee's answer became a component-fit record,
    which validates its own kind against the SRD tables (FR-015).
    """
    if pinned is ABSENT:
        return None

    if pinned is not None:
        cost = tons(pinned)
        if ledger.affords(cost):
            ledger.spend(cost)
            return pinned
        ledger.decline_unaffordable(field, asked(pinned), cost)
        return None

    return draw()


def _armor_tons(hull_tons: int, fit: ArmorFit) -> float:
    return max(1.0, hull_tons * 0.05) * (fit.percent // 5)


def _install_armor(fit: ArmorFit, hull_tons: int, ledger: TonnageLedger) -> bool:
    """Spend the tonnage `fit` costs, or report that the budget cannot cover it."""
    tons = _armor_tons(hull_tons, fit)
    if not ledger.affords(tons):
        return False
    ledger.spend(tons)
    return True


def _select_armor(
    rolls: Rolls,
    hull_tons: int,
    ledger: TonnageLedger,
    pinned: ArmorFit | Absent | None,
) -> ArmorFit | None:
    """The armour to fit: the referee's answer if they gave one, else a draw.

    A pinned layer is validated by `build_ship` alone, so any SRD type may be
    pinned even though `_ARMOR_CHOICES` would never roll it: that list keeps
    *rolled* output plausible and was never a limit on intent (ADR-0001).
    """

    def draw() -> ArmorFit | None:
        fit = rolls.choose(_ARMOR_CHOICES, RollName.SHIP_ARMOR)
        if fit is None:
            return None
        return fit if _install_armor(fit, hull_tons, ledger) else None

    return _pin_or_draw(
        pinned,
        ledger,
        "armor",
        tons=lambda fit: _armor_tons(hull_tons, fit),
        asked=lambda fit: f"{fit.type.value} {fit.percent}%",
        draw=draw,
    )


def _select_computer(rolls: Rolls, pinned: ComputerFit | Absent | None) -> ComputerFit | None:
    """The computer costs no tonnage, so a pin is never declined—only fitted."""
    if pinned is ABSENT:
        return None
    if isinstance(pinned, ComputerFit):
        return pinned
    return rolls.choose(_COMPUTER_PROFILES, RollName.SHIP_COMPUTER)


def _select_electronics(
    rolls: Rolls, ledger: TonnageLedger, pinned: str | Absent | None
) -> str | None:
    """The sensor package, as a table key. `None` is the Standard package every
    ship carries, which is what `ABSENT` pins and what a declined draw leaves."""

    def draw() -> str | None:
        name = rolls.choose(_ELECTRONICS_CHOICES, RollName.SHIP_ELECTRONICS)
        if name == "standard":
            return None
        tons = ELECTRONICS[name].tons
        if not ledger.affords(tons):
            return None
        ledger.spend(tons)
        return name

    if isinstance(pinned, str):
        validate_electronics(pinned)

    return _pin_or_draw(
        pinned,
        ledger,
        "electronics",
        tons=lambda name: ELECTRONICS[name].tons,
        asked=str,
        draw=draw,
    )


def _select_staterooms(rolls: Rolls, ledger: TonnageLedger, pinned: int | None) -> int:
    """How many staterooms to fit.

    Two-state, not three: a stateroom count of zero *is* the pinned absence, and
    `None` still means roll. A count the budget cannot cover is clamped like a
    drawn one, since the referee asked for rooms rather than for a specific ship.
    """
    stateroom_tons = QUARTERS["stateroom"].tons
    if pinned is not None:
        affordable = int(ledger.remaining // stateroom_tons) if stateroom_tons else 0
        count = max(0, min(pinned, affordable))
        if count < pinned:
            ledger.decline(
                "staterooms",
                str(pinned),
                str(count),
                f"needs {_tons(stateroom_tons * pinned)}t, {_tons(ledger.remaining)}t free",
            )
        ledger.spend(stateroom_tons * count)
        return count

    count = rolls.d6(RollName.SHIP_STATEROOMS) - 1
    stateroom_tons = QUARTERS["stateroom"].tons
    affordable = int(ledger.remaining // stateroom_tons) if stateroom_tons else 0
    count = max(0, min(count, affordable))
    ledger.spend(stateroom_tons * count)
    return count


def _fitting_tons(fit: FittingFit) -> float:
    """What one fitting costs, mirroring the builder's own fittings step.

    A vehicle-sized fitting (a hangar, a launch tube) is priced by the vehicle it
    holds rather than by a fixed tonnage, so its table row carries no `tons` at
    all. The generator would never roll one, but a referee may pin one.
    """
    row = FITTINGS[fit.kind]
    if row.tons_per_vehicle_ton is not None:
        return fit.vehicle_tons * row.tons_per_vehicle_ton * fit.quantity
    return row.tons * fit.quantity


def _select_fitting(
    rolls: Rolls, ledger: TonnageLedger, pinned: FittingFit | Absent | None
) -> FittingFit | None:
    def draw() -> FittingFit | None:
        kind = rolls.choose(_FITTING_CHOICES, RollName.SHIP_FITTING)
        if kind is None:
            return None
        tons = FITTINGS[kind].tons
        if not ledger.affords(tons):
            return None
        ledger.spend(tons)
        return FittingFit(kind=kind)

    return _pin_or_draw(
        pinned,
        ledger,
        "fitting",
        tons=_fitting_tons,
        asked=lambda fit: fit.kind,
        draw=draw,
    )


def _fit_turret(
    rolls: Rolls, ledger: TonnageLedger, pinned: TurretPin, ordinal: int, promised: bool
) -> TurretFit | None:
    """One turret, taking the referee's answer for either half and drawing the rest.

    Returns `None` when the mount will not fit, which is how a turret has always
    been dropped. The weapon is drawn only once a mount is secured, so a dropped
    turret costs no weapon draw and the draw sequence is unchanged from before
    turrets could be pinned.

    `promised` comes from the caller because only it knows whether this turret
    was asked for at all: a count-only answer pins neither half, so the pin
    itself cannot say. The tonnage the shortfall is measured in is only known
    here, once a mount has been settled on.
    """
    if pinned.mount is not None:
        validate_turret_mount(pinned.mount)
        mount_name = pinned.mount
    else:
        mount_name = rolls.choose(_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)

    mount = TURRET_MOUNTS[mount_name]
    if not ledger.affords(mount.tons):
        # Only a *pinned* turret is a promise. A drawn one that will not fit has
        # always been dropped in silence, and still is.
        if promised:
            ledger.decline_unaffordable("turrets", _turret_asked(ordinal, pinned), mount.tons)
        return None

    if pinned.weapon is not None:
        validate_turret_weapon(pinned.weapon)
        weapon = pinned.weapon
    else:
        weapon = rolls.choose(_TURRET_WEAPONS, RollName.SHIP_WEAPON)

    ledger.spend(mount.tons)
    return TurretFit(mount=mount_name, weapons=(weapon,) * mount.weapon_slots)


def _turret_asked(ordinal: int, pin: TurretPin) -> str:
    """What the referee asked for on one turret, as they put it.

    A count-only answer pins neither half, so the record says which turret went
    unfitted rather than naming parts nobody chose.
    """
    wanted = " ".join(part for part in (pin.mount, pin.weapon) if part is not None)
    return f"turret {ordinal} ({wanted})" if wanted else f"turret {ordinal}"


def _select_turrets(
    rolls: Rolls,
    hull_tons: int,
    ledger: TonnageLedger,
    pinned: tuple[TurretPin, ...] | None,
) -> tuple[TurretFit, ...]:
    """The ship's turrets: how many, and what each one is.

    A pinned tuple carries both answers at once—its length is the count, and
    each entry is what the referee said about that turret. `()` is an unarmed
    ship, which is an answer rather than an unanswered question.
    """
    hardpoints = _hardpoints_for(HullClass.STARSHIP, hull_tons)

    if pinned is not None:
        validate_turret_count(HullClass.STARSHIP, hull_tons, len(pinned))
        wanted: tuple[TurretPin, ...] = pinned
    else:
        drawn = max(0, min(hardpoints, rolls.d6(RollName.SHIP_TURRET_COUNT) - 1))
        wanted = (TurretPin(),) * drawn

    turrets: list[TurretFit] = []
    for ordinal, pin in enumerate(wanted, 1):
        turret = _fit_turret(rolls, ledger, pin, ordinal, promised=pinned is not None)
        if turret is None:
            continue
        turrets.append(turret)
        if len(turrets) >= hardpoints:
            break

    return tuple(turrets)


def _select_bay(
    rolls: Rolls,
    hardpoints_remaining: int,
    ledger: TonnageLedger,
    pinned: BayFit | Absent | None,
) -> tuple[BayFit | None, int]:
    """Pick a bay only among kinds that fit both the remaining hardpoints and
    tonnage (50 t plus fire control), so a chosen bay never needs correction.

    A pin faces the same hardpoint check as a draw: with none left there is
    nowhere to mount it, which is a shortfall the referee should hear about
    rather than a budget that would not stretch.
    """
    if pinned is ABSENT:
        return None, hardpoints_remaining

    if isinstance(pinned, BayFit):
        if hardpoints_remaining <= 0:
            ledger.decline("bay", pinned.kind, "none", "no hardpoint left to mount it")
            return None, hardpoints_remaining
        tons = BAYS[pinned.kind].tons + BAY_FIRE_CONTROL_TONS
        if not ledger.affords(tons):
            ledger.decline_unaffordable("bay", pinned.kind, tons)
            return None, hardpoints_remaining
        ledger.spend(tons)
        return pinned, hardpoints_remaining - 1

    if hardpoints_remaining <= 0:
        return None, hardpoints_remaining
    candidates: tuple[str | None, ...] = (None,) + tuple(
        kind for kind, row in BAYS.items() if ledger.affords(row.tons + BAY_FIRE_CONTROL_TONS)
    )
    kind = rolls.choose(candidates, RollName.SHIP_BAY)
    if kind is None:
        return None, hardpoints_remaining
    ledger.spend(BAYS[kind].tons + BAY_FIRE_CONTROL_TONS)
    return BayFit(kind=kind), hardpoints_remaining - 1


def _select_screen(
    rolls: Rolls, ledger: TonnageLedger, pinned: ScreenFit | Absent | None
) -> ScreenFit | None:
    def draw() -> ScreenFit | None:
        candidates: tuple[str | None, ...] = (None,) + tuple(
            kind for kind, row in SCREENS.items() if ledger.affords(row.tons)
        )
        kind = rolls.choose(candidates, RollName.SHIP_SCREEN)
        if kind is None:
            return None
        ledger.spend(SCREENS[kind].tons)
        return ScreenFit(kind=kind)

    return _pin_or_draw(
        pinned,
        ledger,
        "screen",
        tons=lambda fit: SCREENS[fit.kind].tons,
        asked=lambda fit: fit.kind,
        draw=draw,
    )


def _select_small_craft_hull_tons(rolls: Rolls, pinned_tons: int | None) -> int:
    if pinned_tons is not None:
        validate_hull_tons(HullClass.SMALL_CRAFT, pinned_tons)
        return pinned_tons
    return rolls.choose(sorted(SMALL_CRAFT_HULLS), RollName.SHIP_HULL_SIZE)


def _small_craft_power_fuel(power_tons: float) -> float:
    return math.floor(power_tons / 3 * 10) / 10


def _small_craft_codes_for(hull_tons: int) -> list[str]:
    return sorted(
        code for code, ratings in SMALL_CRAFT_DRIVE_PERFORMANCE.items() if hull_tons in ratings
    )


def _small_craft_power_codes(hull_tons: int, maneuver_letter: str) -> list[str]:
    """The power plants a craft with this manoeuvre drive can still carry.

    Two rules at once: a plant may not be rated below the drive it powers, and
    the pair must leave room for at least the smallest cockpit. The small-craft
    budget is tight enough that both have to be applied before choosing rather
    than corrected afterwards.
    """
    maneuver_tons = DRIVE_COSTS[maneuver_letter].maneuver_tons
    maneuver_rating = SMALL_CRAFT_DRIVE_PERFORMANCE[maneuver_letter][hull_tons]

    options = []
    for power_letter in _small_craft_codes_for(hull_tons):
        if SMALL_CRAFT_DRIVE_PERFORMANCE[power_letter][hull_tons] < maneuver_rating:
            continue
        power_tons = DRIVE_COSTS[power_letter].power_tons
        power_fuel = _small_craft_power_fuel(power_tons)
        if maneuver_tons + power_tons + power_fuel + _MIN_COCKPIT_TONS <= hull_tons:
            options.append(power_letter)
    return options


def small_craft_maneuver_ratings(hull_tons: int) -> tuple[int, ...]:
    """Every manoeuvre rating a small craft of this tonnage can actually carry.

    Narrower than what the drive table tabulates for the hull: a rating whose
    every drive leaves no room for a plant and a cockpit beside it is not one
    this craft can have. The wizard offers these so a referee is refused at the
    manoeuvre prompt rather than at the power prompt that follows it, where
    every answer would be wrong through no fault of their own.
    """
    return tuple(
        sorted(
            {
                SMALL_CRAFT_DRIVE_PERFORMANCE[code][hull_tons]
                for code in _small_craft_codes_for(hull_tons)
                if _small_craft_power_codes(hull_tons, code)
            }
        )
    )


def small_craft_power_ratings(hull_tons: int, maneuver_rating: int) -> tuple[int, ...]:
    """Every power plant rating a small craft at this manoeuvre rating can carry.

    The wizard offers these rather than the ratings the hull can deliver at
    large, because on this path the pair is chosen jointly: a manoeuvre drive
    already fitted rules out plants that are too weak to power it or too heavy
    to sit beside it. Exposed so the prompt and the selection step agree on what
    is possible instead of the prompt promising more than generation can give.
    """
    ratings: set[int] = set()
    for maneuver_letter in _small_craft_codes_for(hull_tons):
        if SMALL_CRAFT_DRIVE_PERFORMANCE[maneuver_letter][hull_tons] != maneuver_rating:
            continue
        for power_letter in _small_craft_power_codes(hull_tons, maneuver_letter):
            ratings.add(SMALL_CRAFT_DRIVE_PERFORMANCE[power_letter][hull_tons])
    return tuple(sorted(ratings))


def _energy_allowance(hull_tons: int, power_rating: int) -> int:
    """How many energy weapons the lightest plant at this rating can run."""
    code = _lightest_code_at(
        _small_craft_codes_for(hull_tons),
        HullClass.SMALL_CRAFT,
        hull_tons,
        Drive.POWER,
        power_rating,
    )
    return SMALL_CRAFT_ENERGY_CAPS[code] if code is not None else 0


def _exceeds_energy_allowance(allowance: int, weapon: str, mount: str | None) -> bool:
    """Whether a turret of this mount, filled with this weapon, outruns the plant.

    A mount carries the same weapon in every slot it has, so a triple mount asks
    three times what a single one does. The builder counts installed energy
    weapons against the cap; this counts the same way, because counting
    differently is how a prompt comes to accept what assembly then refuses.
    """
    if not TURRET_WEAPONS[weapon].energy:
        return False
    slots = TURRET_MOUNTS[mount].weapon_slots if mount is not None else 1
    return slots > allowance


def validate_small_craft_weapon(
    hull_tons: int, power_rating: int, weapon: str, mount: str | None = None
) -> None:
    """Raise `ValueError` if this craft's plant cannot run `weapon`.

    A small craft's armament is capped by its power plant (SRD "Small Craft
    Design"), so an energy weapon needs an allowance to spare. Only checkable
    once the plant is known, which on this path means once the referee has
    pinned its rating; when they have not, the same rule is applied at the point
    of selection instead.
    """
    validate_turret_weapon(weapon)
    if mount is not None:
        validate_turret_mount(mount)

    allowance = _energy_allowance(hull_tons, power_rating)
    if _exceeds_energy_allowance(allowance, weapon, mount):
        mounted = f"{weapon} in a {mount}" if mount is not None else weapon
        raise ValueError(
            f"a small craft's power plant at rating {power_rating} runs "
            f"{allowance} energy weapon(s), so it cannot mount {mounted}"
        )


def _pin_small_craft_drive(
    candidates: list[str],
    hull_tons: int,
    drive: Drive,
    rating: int,
    ledger: TonnageLedger,
) -> str:
    """The lightest of `candidates` delivering `rating`, degrading if none does.

    `candidates` is already filtered for what fits, so an empty result at the
    asked-for rating means the rating is tabulated for this hull but no drive
    delivering it leaves room for the rest of the craft. That is a tonnage
    shortfall, so it degrades and is recorded rather than refused: the referee
    gets the best rating the hull can actually carry, and is told it is not the
    one they asked for. The starship jump drive has always behaved this way.
    """
    validate_rating(HullClass.SMALL_CRAFT, hull_tons, drive, rating)
    code = _lightest_code_at(candidates, HullClass.SMALL_CRAFT, hull_tons, drive, rating)
    if code is not None:
        return code

    affordable = {SMALL_CRAFT_DRIVE_PERFORMANCE[c][hull_tons] for c in candidates}
    below = [candidate for candidate in affordable if candidate < rating]
    got = max(below) if below else min(affordable)
    ledger.decline(
        f"{drive.value}_rating",
        str(rating),
        str(got),
        f"no {drive.value} drive delivering {rating} fits a {hull_tons}-ton hull",
    )
    fallback = _lightest_code_at(candidates, HullClass.SMALL_CRAFT, hull_tons, drive, got)
    if fallback is None:
        raise AssertionError(f"{got} came from {candidates} but no code delivers it")
    return fallback


def _select_small_craft_drives(
    rolls: Rolls, hull_tons: int, constraints: DesignConstraints, ledger: TonnageLedger
) -> tuple[str, str]:
    """Pick maneuver+power codes that fit the hull, reserving room for at least
    the smallest cockpit so `_select_cockpit` always has a legal candidate.

    Takes the ledger only to record a degraded pin. Nothing is spent here: the
    drives are priced against the hull directly, and what they cost is taken off
    the budget by the caller once both are known.

    A pinned rating narrows the same candidate list rather than bypassing it, so
    the affordability filtering still holds. The power plant's floor needs no
    separate check here: `_small_craft_power_codes` already drops anything rated
    below the manoeuvre drive, so a power rating pinned beneath it finds none.
    """
    valid = _small_craft_codes_for(hull_tons)
    maneuver_candidates = [c for c in valid if _small_craft_power_codes(hull_tons, c)]
    if not maneuver_candidates:
        raise ValueError(f"no small-craft drive combination fits a {hull_tons}-ton hull")

    if constraints.maneuver_rating is not None:
        maneuver_letter = _pin_small_craft_drive(
            maneuver_candidates, hull_tons, Drive.MANEUVER, constraints.maneuver_rating, ledger
        )
    else:
        maneuver_letter = rolls.choose(maneuver_candidates, RollName.SHIP_MANEUVER_CODE)

    options = _small_craft_power_codes(hull_tons, maneuver_letter)
    if constraints.power_rating is not None:
        power_letter = _pin_small_craft_drive(
            options, hull_tons, Drive.POWER, constraints.power_rating, ledger
        )
    else:
        power_letter = rolls.choose(options, RollName.SHIP_POWER_CODE)

    return f"s{maneuver_letter}", f"s{power_letter}"


def _select_cockpit(rolls: Rolls, ledger: TonnageLedger) -> str:
    candidates = [name for name, row in COCKPITS.items() if ledger.affords(row.tons)]
    cockpit = rolls.choose(candidates, RollName.SHIP_COCKPIT)
    ledger.spend(COCKPITS[cockpit].tons)
    return cockpit


def _select_small_craft_turret(
    rolls: Rolls,
    hull_tons: int,
    ledger: TonnageLedger,
    energy_cap: int,
    pinned: tuple[TurretPin, ...] | None,
) -> tuple[TurretFit, ...]:
    """The one turret a small craft may carry, drawn or pinned.

    A separate path from the starship one because the craft has a single
    hardpoint and its power plant caps energy weapons. A pin is honoured here
    just the same: an answer the referee gave must not be quietly dropped for
    having been given on the smaller ruleset.
    """
    if pinned is not None:
        validate_turret_count(HullClass.SMALL_CRAFT, hull_tons, len(pinned))
        if not pinned:
            return ()
        pin = pinned[0]
    else:
        if rolls.d6(RollName.SHIP_TURRET_COUNT) <= 3:
            return ()
        pin = TurretPin()

    if pin.mount is not None:
        validate_turret_mount(pin.mount)
        mount_name = pin.mount
    else:
        mount_name = rolls.choose(_SMALL_CRAFT_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)

    mount = TURRET_MOUNTS[mount_name]
    if not ledger.affords(mount.tons):
        if pinned is not None:
            ledger.decline_unaffordable("turrets", _turret_asked(1, pin), mount.tons)
        return ()

    if pin.weapon is not None:
        validate_turret_weapon(pin.weapon)
        if _exceeds_energy_allowance(energy_cap, pin.weapon, mount_name):
            # The plant this craft ended up with cannot run the weapon asked for.
            # `build_ship` would refuse the design outright and cost the session
            # a ship; declining the turret leaves a craft, and says why.
            ledger.decline(
                "turrets",
                _turret_asked(1, pin),
                "none",
                f"the power plant runs {energy_cap} energy weapon(s)",
            )
            return ()
        weapon = pin.weapon
    else:
        weapon_choices = _TURRET_WEAPONS if energy_cap > 0 else _NON_ENERGY_TURRET_WEAPONS
        weapon = rolls.choose(weapon_choices, RollName.SHIP_WEAPON)

    ledger.spend(mount.tons)
    return (TurretFit(mount=mount_name, weapons=(weapon,) * mount.weapon_slots),)


def _generate_small_craft(rolls: Rolls, constraints: DesignConstraints) -> GenerationResult:
    hull_tons = _select_small_craft_hull_tons(rolls, constraints.hull_tons)
    if constraints.jump_rating is not None:
        validate_rating(HullClass.SMALL_CRAFT, hull_tons, Drive.JUMP, constraints.jump_rating)
    if isinstance(constraints.bay, BayFit):
        raise ValueError("small craft carry no weapon bays, so no bay can be pinned")
    configuration = _select_configuration(rolls, constraints.configuration)
    ledger = TonnageLedger(hull_tons)
    maneuver_code, power_code = _select_small_craft_drives(rolls, hull_tons, constraints, ledger)
    maneuver_letter, power_letter = maneuver_code[1:], power_code[1:]

    maneuver_tons = DRIVE_COSTS[maneuver_letter].maneuver_tons
    power_tons = DRIVE_COSTS[power_letter].power_tons
    power_fuel_tons = _small_craft_power_fuel(power_tons)

    ledger.spend(maneuver_tons + power_tons + power_fuel_tons)
    cockpit = _select_cockpit(rolls, ledger)

    armor = _select_armor(rolls, hull_tons, ledger, constraints.armor)
    computer = _select_computer(rolls, constraints.computer)
    electronics = _select_electronics(rolls, ledger, constraints.electronics)
    staterooms = _select_staterooms(rolls, ledger, constraints.staterooms)
    fitting = _select_fitting(rolls, ledger, constraints.fitting)

    energy_cap = SMALL_CRAFT_ENERGY_CAPS[power_letter]
    turrets = _select_small_craft_turret(rolls, hull_tons, ledger, energy_cap, constraints.turrets)

    # A screen is never *rolled* onto a small craft, but the rules permit one,
    # so a pinned screen is fitted rather than silently dropped. Passing ABSENT
    # for an unset field keeps this path drawing exactly what it always drew.
    screen = _select_screen(rolls, ledger, constraints.screen or ABSENT)

    name = _select_name(rolls, constraints.name)

    design = ShipDesign(
        hull_tons=hull_tons,
        configuration=configuration,
        maneuver_code=maneuver_code,
        power_code=power_code,
        power_weeks=_SMALL_CRAFT_POWER_WEEKS,
        bridge=False,
        cockpit=cockpit,
        armor=(armor,) if armor is not None else (),
        computer=computer,
        electronics=electronics,
        staterooms=staterooms,
        fittings=(fitting,) if fitting is not None else (),
        turrets=turrets,
        screens=(screen,) if screen is not None else (),
        name=name,
        purpose=constraints.purpose,
    )
    return GenerationResult(ship=build_ship(design), unmet=ledger.declined)


def generate_ship(
    rolls: Rolls | None = None,
    *,
    constraints: DesignConstraints = UNCONSTRAINED,
) -> GenerationResult:
    """A random, rules-legal ship, selected via `rolls` and validated by `build_ship`.

    Returns a `GenerationResult`, not a bare `Ship`: generation never fails on
    tonnage, so the caller needs somewhere to learn that a pinned value could not
    be honoured. Reach for `.ship` when you do not care.

    `rolls` defaults to `RandomRolls()`; pass `RandomRolls.seeded(seed)` for
    reproducibility (FR-017). `constraints` carries what the referee pinned:
    `hull_tons` constrains generation to a tabulated hull size while staying
    legal (FR-018), and `hull_class` selects the 10-95 ton small-craft ruleset
    (FR-019). Left at its default, nothing is pinned and every value is rolled.

    A pinned value consumes no dice, so the unconstrained draw sequence is
    byte-identical to the one `tests/data/baseline/designs.json` pins.

    `generate_ship_name` is drawn last on both paths, after every component
    decision (FR-010a). `RandomRolls` wraps one `random.Random` stream, so a
    draw inserted anywhere else would shift every later draw and change the
    hull, drives and armament a seed produces—naming would stop being purely
    additive.
    `test_sc008_ship_name_is_the_final_draw_and_is_drawn_exactly_once_on_both_paths`
    in `tests/test_ship_generator.py` asserts this directly, and
    `tests/data/baseline/designs.json` re-pins a
    seed-to-ship anchor for future features, failing loudly, naming the seed,
    if a future edit ever moves the name draw off the end of a path (see
    `engine/ships/names.py`'s docstring).
    """
    rolls = rolls or RandomRolls()

    if constraints.hull_class is HullClass.SMALL_CRAFT:
        return _generate_small_craft(rolls, constraints)

    hull_tons = _select_hull_tons(rolls, constraints.hull_tons)
    configuration = _select_configuration(rolls, constraints.configuration)
    jump_code, maneuver_code, power_code = _select_drive_codes(rolls, hull_tons, constraints)

    maneuver_tons = DRIVE_COSTS[maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[power_code].power_tons
    power_fuel_tons = (power_tons // 3) * _STANDARD_POWER_WEEKS
    bridge_tons = _bridge_tons(hull_tons)

    budget = hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)
    jump_code = _fit_jump_drive(hull_tons, jump_code, budget)
    jump_rating = DRIVE_PERFORMANCE[jump_code][hull_tons]

    ledger = TonnageLedger(max(0.0, budget - DRIVE_COSTS[jump_code].jump_tons))
    if constraints.jump_rating is not None and jump_rating < constraints.jump_rating:
        ledger.decline(
            "jump_rating",
            f"Jump-{constraints.jump_rating}",
            f"Jump-{jump_rating}",
            f"fuelling Jump-{constraints.jump_rating} needs "
            f"{0.1 * hull_tons * constraints.jump_rating}t of fuel the hull cannot spare",
        )

    max_jump_distance = math.floor(ledger.remaining / (0.1 * hull_tons))
    jump_distance = max(0, min(jump_rating, max_jump_distance))
    ledger.spend(0.1 * hull_tons * jump_distance)

    armor = _select_armor(rolls, hull_tons, ledger, constraints.armor)
    computer = _select_computer(rolls, constraints.computer)
    electronics = _select_electronics(rolls, ledger, constraints.electronics)
    staterooms = _select_staterooms(rolls, ledger, constraints.staterooms)
    fitting = _select_fitting(rolls, ledger, constraints.fitting)
    turrets = _select_turrets(rolls, hull_tons, ledger, constraints.turrets)

    hardpoints_remaining = _hardpoints_for(HullClass.STARSHIP, hull_tons) - len(turrets)
    bay, hardpoints_remaining = _select_bay(rolls, hardpoints_remaining, ledger, constraints.bay)
    screen = _select_screen(rolls, ledger, constraints.screen)

    name = _select_name(rolls, constraints.name)

    design = ShipDesign(
        hull_tons=hull_tons,
        configuration=configuration,
        jump_code=jump_code,
        maneuver_code=maneuver_code,
        power_code=power_code,
        jump_distance=jump_distance,
        armor=(armor,) if armor is not None else (),
        computer=computer,
        electronics=electronics,
        staterooms=staterooms,
        fittings=(fitting,) if fitting is not None else (),
        turrets=turrets,
        bays=(bay,) if bay is not None else (),
        screens=(screen,) if screen is not None else (),
        name=name,
        purpose=constraints.purpose,
    )
    return GenerationResult(ship=build_ship(design), unmet=ledger.declined)
