"""generate_ship(rolls=None, *, hull_size=None, small_craft=False) -> Ship.

Selects rules-legal components through the `Rolls` seam, reading the same
`tables.py` data `build_ship` validates against, and assembles a `ShipDesign`
that is legal by construction: tonnage is tracked against a running budget so
no candidate is ever chosen that would over-allocate the hull. Ends by calling
`build_ship`, so a generated ship can never be rules-illegal (FR-016, SC-003).

`small_craft=True` selects under the small-craft ruleset (research.md Part K):
a 10-95 ton hull, a cockpit instead of a bridge, no jump drive, and turret
weapons constrained to the power plant's energy-weapon cap. Maneuver and power
drive codes are chosen together, since a small hull's tight tonnage budget
means the choice must be filtered for affordability up front rather than
corrected after the fact (unlike the starship path's looser margins).

Bays and screens (research.md Part H, FR-020) are only ever offered on the
standard-hull path, and only among kinds that fit the hardpoints and tonnage
still free after turrets are chosen—never on small craft, which forbid bays
outright.
"""

from __future__ import annotations

import math

from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.ships.builder import BAY_FIRE_CONTROL_TONS, build_ship
from cetools.engine.ships.models import (
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    FittingFit,
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


def _select_hull_tons(rolls: Rolls, hull_size: int | None) -> int:
    if hull_size is not None:
        if hull_size not in HULLS:
            raise ValueError(
                f"{hull_size} tons is not a tabulated hull size; valid: {sorted(HULLS)}"
            )
        return hull_size
    return rolls.choose(sorted(HULLS), RollName.SHIP_HULL_SIZE)


def _select_configuration(rolls: Rolls) -> Configuration:
    return rolls.choose(list(Configuration), RollName.SHIP_CONFIGURATION)


def _codes_valid_for_hull(hull_tons: int) -> list[str]:
    return sorted(code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings)


def _fit_jump_drive(hull_tons: int, drawn_code: str, budget: float) -> str:
    """The lightest jump drive affording the highest rating `budget` buys,
    never rated above `drawn_code`, per contracts/jump-drive-fit.md.

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


def _select_armor(rolls: Rolls, hull_tons: int, remaining: float) -> tuple[ArmorFit | None, float]:
    fit = rolls.choose(_ARMOR_CHOICES, RollName.SHIP_ARMOR)
    if fit is None:
        return None, remaining
    tons = max(1.0, hull_tons * 0.05) * (fit.percent // 5)
    if tons > remaining:
        return None, remaining
    return fit, remaining - tons


def _select_computer(rolls: Rolls) -> ComputerFit | None:
    return rolls.choose(_COMPUTER_PROFILES, RollName.SHIP_COMPUTER)


def _select_electronics(rolls: Rolls, remaining: float) -> tuple[str | None, float]:
    name = rolls.choose(_ELECTRONICS_CHOICES, RollName.SHIP_ELECTRONICS)
    if name == "standard":
        return None, remaining
    tons = ELECTRONICS[name].tons
    if tons > remaining:
        return None, remaining
    return name, remaining - tons


def _select_staterooms(rolls: Rolls, remaining: float) -> tuple[int, float]:
    count = rolls.d6(RollName.SHIP_STATEROOMS) - 1
    stateroom_tons = QUARTERS["stateroom"].tons
    affordable = int(remaining // stateroom_tons) if stateroom_tons else 0
    count = max(0, min(count, affordable))
    return count, remaining - stateroom_tons * count


def _select_fitting(rolls: Rolls, remaining: float) -> tuple[FittingFit | None, float]:
    kind = rolls.choose(_FITTING_CHOICES, RollName.SHIP_FITTING)
    if kind is None:
        return None, remaining
    tons = FITTINGS[kind].tons
    if tons > remaining:
        return None, remaining
    return FittingFit(kind=kind), remaining - tons


def _select_turrets(
    rolls: Rolls, hull_tons: int, remaining: float
) -> tuple[tuple[TurretFit, ...], float]:
    hardpoints = hull_tons // 100
    turret_count = max(0, min(hardpoints, rolls.d6(RollName.SHIP_TURRET_COUNT) - 1))

    turrets: list[TurretFit] = []
    for _ in range(turret_count):
        mount_name = rolls.choose(_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)
        mount = TURRET_MOUNTS[mount_name]
        if mount.tons > remaining:
            continue
        weapon = rolls.choose(_TURRET_WEAPONS, RollName.SHIP_WEAPON)
        turrets.append(TurretFit(mount=mount_name, weapons=(weapon,) * mount.weapon_slots))
        remaining -= mount.tons
        if len(turrets) >= hardpoints:
            break

    return tuple(turrets), remaining


def _select_bay(
    rolls: Rolls, hardpoints_remaining: int, remaining: float
) -> tuple[BayFit | None, int, float]:
    """Pick a bay only among kinds that fit both the remaining hardpoints and
    tonnage (50 t plus fire control), so a chosen bay never needs correction."""
    if hardpoints_remaining <= 0:
        return None, hardpoints_remaining, remaining
    candidates: tuple[str | None, ...] = (None,) + tuple(
        kind for kind, row in BAYS.items() if row.tons + BAY_FIRE_CONTROL_TONS <= remaining
    )
    kind = rolls.choose(candidates, RollName.SHIP_BAY)
    if kind is None:
        return None, hardpoints_remaining, remaining
    tons = BAYS[kind].tons + BAY_FIRE_CONTROL_TONS
    return BayFit(kind=kind), hardpoints_remaining - 1, remaining - tons


def _select_screen(rolls: Rolls, remaining: float) -> tuple[ScreenFit | None, float]:
    candidates: tuple[str | None, ...] = (None,) + tuple(
        kind for kind, row in SCREENS.items() if row.tons <= remaining
    )
    kind = rolls.choose(candidates, RollName.SHIP_SCREEN)
    if kind is None:
        return None, remaining
    return ScreenFit(kind=kind), remaining - SCREENS[kind].tons


def _select_small_craft_hull_tons(rolls: Rolls, hull_size: int | None) -> int:
    if hull_size is not None:
        if hull_size not in SMALL_CRAFT_HULLS:
            raise ValueError(
                f"{hull_size} tons is not a tabulated small-craft hull size; "
                f"valid: {sorted(SMALL_CRAFT_HULLS)}"
            )
        return hull_size
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


def _select_cockpit(rolls: Rolls, remaining: float) -> str:
    candidates = [name for name, row in COCKPITS.items() if row.tons <= remaining]
    return rolls.choose(candidates, RollName.SHIP_COCKPIT)


def _select_small_craft_turret(
    rolls: Rolls, remaining: float, energy_cap: int
) -> tuple[tuple[TurretFit, ...], float]:
    if rolls.d6(RollName.SHIP_TURRET_COUNT) <= 3:
        return (), remaining
    mount_name = rolls.choose(_SMALL_CRAFT_TURRET_MOUNTS, RollName.SHIP_TURRET_MOUNT)
    mount = TURRET_MOUNTS[mount_name]
    if mount.tons > remaining:
        return (), remaining
    weapon_choices = _TURRET_WEAPONS if energy_cap > 0 else _NON_ENERGY_TURRET_WEAPONS
    weapon = rolls.choose(weapon_choices, RollName.SHIP_WEAPON)
    return (TurretFit(mount=mount_name, weapons=(weapon,)),), remaining - mount.tons


def _generate_small_craft(rolls: Rolls, hull_size: int | None) -> Ship:
    hull_tons = _select_small_craft_hull_tons(rolls, hull_size)
    configuration = _select_configuration(rolls)
    maneuver_code, power_code = _select_small_craft_drives(rolls, hull_tons)
    maneuver_letter, power_letter = maneuver_code[1:], power_code[1:]

    maneuver_tons = DRIVE_COSTS[maneuver_letter].maneuver_tons
    power_tons = DRIVE_COSTS[power_letter].power_tons
    power_fuel_tons = _small_craft_power_fuel(power_tons)

    remaining = hull_tons - (maneuver_tons + power_tons + power_fuel_tons)
    cockpit = _select_cockpit(rolls, remaining)
    remaining -= COCKPITS[cockpit].tons

    armor, remaining = _select_armor(rolls, hull_tons, remaining)
    computer = _select_computer(rolls)
    electronics, remaining = _select_electronics(rolls, remaining)
    staterooms, remaining = _select_staterooms(rolls, remaining)
    fitting, remaining = _select_fitting(rolls, remaining)

    energy_cap = SMALL_CRAFT_ENERGY_CAPS[power_letter]
    turrets, remaining = _select_small_craft_turret(rolls, remaining, energy_cap)

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
    hull_size: int | None = None,
    small_craft: bool = False,
) -> Ship:
    """A random, rules-legal ship, selected via `rolls` and validated by `build_ship`.

    `rolls` defaults to `RandomRolls()`; pass `RandomRolls.seeded(seed)` for
    reproducibility (FR-017). `hull_size` constrains generation to a tabulated
    hull size while staying legal (FR-018); when `None`, one is chosen.
    `small_craft` generates under the 10-95 ton small-craft ruleset (FR-019).

    `generate_ship_name` is drawn last on both paths, after every component
    decision (FR-010a). `RandomRolls` wraps one `random.Random` stream, so a
    draw inserted anywhere else would shift every later draw and change the
    hull, drives and armament a seed produces—naming would stop being purely
    additive. `specs/012-ship-names/baseline/designs.json` pins 100 pre-feature
    designs and fails loudly, naming the seed, if a future edit ever moves the
    name draw off the end of a path (see `engine/ships/names.py`'s docstring).
    """
    rolls = rolls or RandomRolls()

    if small_craft:
        return _generate_small_craft(rolls, hull_size)

    hull_tons = _select_hull_tons(rolls, hull_size)
    configuration = _select_configuration(rolls)
    jump_code, maneuver_code, power_code = _select_drive_codes(rolls, hull_tons)

    maneuver_tons = DRIVE_COSTS[maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[power_code].power_tons
    power_fuel_tons = (power_tons // 3) * _STANDARD_POWER_WEEKS
    bridge_tons = _bridge_tons(hull_tons)

    budget = hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)
    jump_code = _fit_jump_drive(hull_tons, jump_code, budget)
    jump_rating = DRIVE_PERFORMANCE[jump_code][hull_tons]

    remaining = max(0.0, budget - DRIVE_COSTS[jump_code].jump_tons)

    max_jump_distance = math.floor(remaining / (0.1 * hull_tons))
    jump_distance = max(0, min(jump_rating, max_jump_distance))
    remaining -= 0.1 * hull_tons * jump_distance

    armor, remaining = _select_armor(rolls, hull_tons, remaining)
    computer = _select_computer(rolls)
    electronics, remaining = _select_electronics(rolls, remaining)
    staterooms, remaining = _select_staterooms(rolls, remaining)
    fitting, remaining = _select_fitting(rolls, remaining)
    turrets, remaining = _select_turrets(rolls, hull_tons, remaining)

    hardpoints_remaining = hull_tons // 100 - len(turrets)
    bay, hardpoints_remaining, remaining = _select_bay(rolls, hardpoints_remaining, remaining)
    screen, remaining = _select_screen(rolls, remaining)

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
    return build_ship(design)
