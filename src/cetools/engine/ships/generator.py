"""generate_ship(rolls=None, *, hull_size=None, small_craft=False) -> Ship.

Selects rules-legal components through the `Rolls` seam, reading the same
`tables.py` data `build_ship` validates against, and assembles a `ShipDesign`
that is legal by construction: tonnage is tracked against a running budget so
no candidate is ever chosen that would over-allocate the hull. Ends by calling
`build_ship`, so a generated ship can never be rules-illegal (FR-016, SC-003).

`small_craft=True` is not yet implemented (its ruleset lands with the builder
support added in User Story 3); passing it raises `NotImplementedError`.
"""

from __future__ import annotations

import math

from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.ships.builder import build_ship
from cetools.engine.ships.models import (
    ArmorFit,
    ArmorType,
    ComputerFit,
    Configuration,
    FittingFit,
    Ship,
    ShipDesign,
    SoftwareFit,
    TurretFit,
)
from cetools.engine.ships.tables import (
    BRIDGE_SIZES,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    QUARTERS,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_STANDARD_POWER_WEEKS = 2

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
    """
    if small_craft:
        raise NotImplementedError("small-craft generation is not yet implemented")

    rolls = rolls or RandomRolls()

    hull_tons = _select_hull_tons(rolls, hull_size)
    configuration = _select_configuration(rolls)
    jump_code, maneuver_code, power_code = _select_drive_codes(rolls, hull_tons)

    jump_rating = DRIVE_PERFORMANCE[jump_code][hull_tons]
    jump_tons = DRIVE_COSTS[jump_code].jump_tons
    maneuver_tons = DRIVE_COSTS[maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[power_code].power_tons
    power_fuel_tons = (power_tons // 3) * _STANDARD_POWER_WEEKS
    bridge_tons = _bridge_tons(hull_tons)

    remaining = max(
        0.0,
        hull_tons - (jump_tons + maneuver_tons + power_tons + bridge_tons + power_fuel_tons),
    )

    max_jump_distance = math.floor(remaining / (0.1 * hull_tons))
    jump_distance = max(0, min(jump_rating, max_jump_distance))
    remaining -= 0.1 * hull_tons * jump_distance

    armor, remaining = _select_armor(rolls, hull_tons, remaining)
    computer = _select_computer(rolls)
    electronics, remaining = _select_electronics(rolls, remaining)
    staterooms, remaining = _select_staterooms(rolls, remaining)
    fitting, remaining = _select_fitting(rolls, remaining)
    turrets, remaining = _select_turrets(rolls, hull_tons, remaining)

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
    )
    return build_ship(design)
