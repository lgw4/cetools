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
from dataclasses import dataclass

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
)

_STANDARD_POWER_WEEKS = 2
_SMALL_CRAFT_POWER_WEEKS = 1
_MIN_COCKPIT_TONS = min(row.tons for row in COCKPITS.values())


@dataclass(frozen=True)
class DesignConstraints:
    """What a referee pinned; everything left unset is rolled.

    One value rather than a keyword per field, because the constrainable surface
    is the whole of roll parity and a signature cannot carry it. Prompting is a
    thin layer over this record, so a library caller reaches the same capability
    without a conversation.

    `hull_class` has no unset state: every ship builds under one ruleset or the
    other, and the generator has always defaulted to starship.
    """

    hull_class: HullClass = HullClass.STARSHIP
    hull_tons: int | None = None


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


def _select_hull_tons(rolls: Rolls, pinned_tons: int | None) -> int:
    if pinned_tons is not None:
        validate_hull_tons(HullClass.STARSHIP, pinned_tons)
        return pinned_tons
    return rolls.choose(sorted(HULLS), RollName.SHIP_HULL_SIZE)


def _select_configuration(rolls: Rolls) -> Configuration:
    return rolls.choose(list(Configuration), RollName.SHIP_CONFIGURATION)


def _codes_valid_for_hull(hull_tons: int) -> list[str]:
    return sorted(code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings)


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


def _select_drive_codes(rolls: Rolls, hull_tons: int) -> tuple[str, str, str]:
    valid = _codes_valid_for_hull(hull_tons)
    jump_code = rolls.choose(valid, RollName.SHIP_JUMP_CODE)
    maneuver_code = rolls.choose(valid, RollName.SHIP_MANEUVER_CODE)
    required = max(
        DRIVE_PERFORMANCE[jump_code][hull_tons],
        DRIVE_PERFORMANCE[maneuver_code][hull_tons],
    )
    power_candidates = [c for c in valid if DRIVE_PERFORMANCE[c][hull_tons] >= required]
    power_code = rolls.choose(power_candidates, RollName.SHIP_POWER_CODE)
    return jump_code, maneuver_code, power_code


def _bridge_tons(hull_tons: int) -> int:
    for max_tons, bridge_tons in BRIDGE_SIZES:
        if max_tons is None or hull_tons <= max_tons:
            return bridge_tons
    raise AssertionError("BRIDGE_SIZES must end with an unbounded (None, tons) step")


def _select_armor(rolls: Rolls, hull_tons: int, ledger: TonnageLedger) -> ArmorFit | None:
    fit = rolls.choose(_ARMOR_CHOICES, RollName.SHIP_ARMOR)
    if fit is None:
        return None
    tons = max(1.0, hull_tons * 0.05) * (fit.percent // 5)
    if not ledger.affords(tons):
        return None
    ledger.spend(tons)
    return fit


def _select_computer(rolls: Rolls) -> ComputerFit | None:
    return rolls.choose(_COMPUTER_PROFILES, RollName.SHIP_COMPUTER)


def _select_electronics(rolls: Rolls, ledger: TonnageLedger) -> str | None:
    name = rolls.choose(_ELECTRONICS_CHOICES, RollName.SHIP_ELECTRONICS)
    if name == "standard":
        return None
    tons = ELECTRONICS[name].tons
    if not ledger.affords(tons):
        return None
    ledger.spend(tons)
    return name


def _select_staterooms(rolls: Rolls, ledger: TonnageLedger) -> int:
    count = rolls.d6(RollName.SHIP_STATEROOMS) - 1
    stateroom_tons = QUARTERS["stateroom"].tons
    affordable = int(ledger.remaining // stateroom_tons) if stateroom_tons else 0
    count = max(0, min(count, affordable))
    ledger.spend(stateroom_tons * count)
    return count


def _select_fitting(rolls: Rolls, ledger: TonnageLedger) -> FittingFit | None:
    kind = rolls.choose(_FITTING_CHOICES, RollName.SHIP_FITTING)
    if kind is None:
        return None
    tons = FITTINGS[kind].tons
    if not ledger.affords(tons):
        return None
    ledger.spend(tons)
    return FittingFit(kind=kind)


def _select_turrets(rolls: Rolls, hull_tons: int, ledger: TonnageLedger) -> tuple[TurretFit, ...]:
    hardpoints = hull_tons // 100
    turret_count = max(0, min(hardpoints, rolls.d6(RollName.SHIP_TURRET_COUNT) - 1))

    turrets: list[TurretFit] = []
    for _ in range(turret_count):
        mount_name = rolls.choose(_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)
        mount = TURRET_MOUNTS[mount_name]
        if not ledger.affords(mount.tons):
            continue
        weapon = rolls.choose(_TURRET_WEAPONS, RollName.SHIP_WEAPON)
        turrets.append(TurretFit(mount=mount_name, weapons=(weapon,) * mount.weapon_slots))
        ledger.spend(mount.tons)
        if len(turrets) >= hardpoints:
            break

    return tuple(turrets)


def _select_bay(
    rolls: Rolls, hardpoints_remaining: int, ledger: TonnageLedger
) -> tuple[BayFit | None, int]:
    """Pick a bay only among kinds that fit both the remaining hardpoints and
    tonnage (50 t plus fire control), so a chosen bay never needs correction."""
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


def _select_screen(rolls: Rolls, ledger: TonnageLedger) -> ScreenFit | None:
    candidates: tuple[str | None, ...] = (None,) + tuple(
        kind for kind, row in SCREENS.items() if ledger.affords(row.tons)
    )
    kind = rolls.choose(candidates, RollName.SHIP_SCREEN)
    if kind is None:
        return None
    ledger.spend(SCREENS[kind].tons)
    return ScreenFit(kind=kind)


def _select_small_craft_hull_tons(rolls: Rolls, pinned_tons: int | None) -> int:
    if pinned_tons is not None:
        validate_hull_tons(HullClass.SMALL_CRAFT, pinned_tons)
        return pinned_tons
    return rolls.choose(sorted(SMALL_CRAFT_HULLS), RollName.SHIP_HULL_SIZE)


def _small_craft_power_fuel(power_tons: float) -> float:
    return math.floor(power_tons / 3 * 10) / 10


def _select_small_craft_drives(rolls: Rolls, hull_tons: int) -> tuple[str, str]:
    """Pick maneuver+power codes that fit the hull, reserving room for at least
    the smallest cockpit so `_select_cockpit` always has a legal candidate."""
    valid = sorted(
        c for c, ratings in SMALL_CRAFT_DRIVE_PERFORMANCE.items() if hull_tons in ratings
    )

    def power_options(maneuver_letter: str) -> list[str]:
        maneuver_tons = DRIVE_COSTS[maneuver_letter].maneuver_tons
        maneuver_rating = SMALL_CRAFT_DRIVE_PERFORMANCE[maneuver_letter][hull_tons]
        options = []
        for power_letter in valid:
            if SMALL_CRAFT_DRIVE_PERFORMANCE[power_letter][hull_tons] < maneuver_rating:
                continue
            power_tons = DRIVE_COSTS[power_letter].power_tons
            power_fuel = _small_craft_power_fuel(power_tons)
            if maneuver_tons + power_tons + power_fuel + _MIN_COCKPIT_TONS <= hull_tons:
                options.append(power_letter)
        return options

    maneuver_candidates = [c for c in valid if power_options(c)]
    if not maneuver_candidates:
        raise ValueError(f"no small-craft drive combination fits a {hull_tons}-ton hull")
    maneuver_letter = rolls.choose(maneuver_candidates, RollName.SHIP_MANEUVER_CODE)
    power_letter = rolls.choose(power_options(maneuver_letter), RollName.SHIP_POWER_CODE)
    return f"s{maneuver_letter}", f"s{power_letter}"


def _select_cockpit(rolls: Rolls, ledger: TonnageLedger) -> str:
    candidates = [name for name, row in COCKPITS.items() if ledger.affords(row.tons)]
    cockpit = rolls.choose(candidates, RollName.SHIP_COCKPIT)
    ledger.spend(COCKPITS[cockpit].tons)
    return cockpit


def _select_small_craft_turret(
    rolls: Rolls, ledger: TonnageLedger, energy_cap: int
) -> tuple[TurretFit, ...]:
    if rolls.d6(RollName.SHIP_TURRET_COUNT) <= 3:
        return ()
    mount_name = rolls.choose(_SMALL_CRAFT_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)
    mount = TURRET_MOUNTS[mount_name]
    if not ledger.affords(mount.tons):
        return ()
    weapon_choices = _TURRET_WEAPONS if energy_cap > 0 else _NON_ENERGY_TURRET_WEAPONS
    weapon = rolls.choose(weapon_choices, RollName.SHIP_WEAPON)
    ledger.spend(mount.tons)
    return (TurretFit(mount=mount_name, weapons=(weapon,)),)


def _generate_small_craft(rolls: Rolls, constraints: DesignConstraints) -> Ship:
    hull_tons = _select_small_craft_hull_tons(rolls, constraints.hull_tons)
    configuration = _select_configuration(rolls)
    maneuver_code, power_code = _select_small_craft_drives(rolls, hull_tons)
    maneuver_letter, power_letter = maneuver_code[1:], power_code[1:]

    maneuver_tons = DRIVE_COSTS[maneuver_letter].maneuver_tons
    power_tons = DRIVE_COSTS[power_letter].power_tons
    power_fuel_tons = _small_craft_power_fuel(power_tons)

    ledger = TonnageLedger(hull_tons - (maneuver_tons + power_tons + power_fuel_tons))
    cockpit = _select_cockpit(rolls, ledger)

    armor = _select_armor(rolls, hull_tons, ledger)
    computer = _select_computer(rolls)
    electronics = _select_electronics(rolls, ledger)
    staterooms = _select_staterooms(rolls, ledger)
    fitting = _select_fitting(rolls, ledger)

    energy_cap = SMALL_CRAFT_ENERGY_CAPS[power_letter]
    turrets = _select_small_craft_turret(rolls, ledger, energy_cap)

    name = generate_ship_name(rolls)

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
        name=name,
    )
    return build_ship(design)


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
        return GenerationResult(ship=_generate_small_craft(rolls, constraints))

    hull_tons = _select_hull_tons(rolls, constraints.hull_tons)
    configuration = _select_configuration(rolls)
    jump_code, maneuver_code, power_code = _select_drive_codes(rolls, hull_tons)

    maneuver_tons = DRIVE_COSTS[maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[power_code].power_tons
    power_fuel_tons = (power_tons // 3) * _STANDARD_POWER_WEEKS
    bridge_tons = _bridge_tons(hull_tons)

    budget = hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)
    jump_code = _fit_jump_drive(hull_tons, jump_code, budget)
    jump_rating = DRIVE_PERFORMANCE[jump_code][hull_tons]

    ledger = TonnageLedger(max(0.0, budget - DRIVE_COSTS[jump_code].jump_tons))

    max_jump_distance = math.floor(ledger.remaining / (0.1 * hull_tons))
    jump_distance = max(0, min(jump_rating, max_jump_distance))
    ledger.spend(0.1 * hull_tons * jump_distance)

    armor = _select_armor(rolls, hull_tons, ledger)
    computer = _select_computer(rolls)
    electronics = _select_electronics(rolls, ledger)
    staterooms = _select_staterooms(rolls, ledger)
    fitting = _select_fitting(rolls, ledger)
    turrets = _select_turrets(rolls, hull_tons, ledger)

    hardpoints_remaining = hull_tons // 100 - len(turrets)
    bay, hardpoints_remaining = _select_bay(rolls, hardpoints_remaining, ledger)
    screen = _select_screen(rolls, ledger)

    name = generate_ship_name(rolls)

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
    )
    return GenerationResult(ship=build_ship(design))
