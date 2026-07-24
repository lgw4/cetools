"""build_ship(design) -> Ship: deterministic allocation, costing, validation.

Follows the SRD build order (research.md Part A) exactly: hull, armor, maneuver
drive, jump drive, power plant, fuel, bridge, computer/software, electronics,
quarters, fittings, turrets, cargo, crew, cost, build time. Every SRD rule
check lives here, in that order, so a design that violates several reports the
first violation in build order (FR-015, SC-005). `ShipDesign.__post_init__`
already guarantees the record is well-formed; this module only ever rejects
*rules* violations.

Ammunition (`TurretFit.ammo`) is accepted and carried on the design for the
sheet and round-trip, but is not tabulated in `tables.py` (the SRD ammunition
price list is not part of this feature's research digest), so it adds no
tonnage or cost here.
"""

from __future__ import annotations

import math

from cetools.engine.ships.models import Configuration, Crew, HullClass, LineItem, Ship, ShipDesign
from cetools.engine.ships.tables import (
    ARMOR,
    BRIDGE_SIZES,
    COMPUTERS,
    DRIVE_COSTS,
    DRIVE_PERFORMANCE,
    ELECTRONICS,
    FITTINGS,
    HULLS,
    QUARTERS,
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_ARMOR_OPTION_COST_PER_TON = {"reflec": 0.1, "self_sealing": 0.01, "stealth": 0.1}


def _drive_rating(code: str, hull_tons: int) -> int:
    rating = DRIVE_PERFORMANCE[code].get(hull_tons)
    if rating is None:
        raise ValueError(f"drive code {code} is not available on a {hull_tons}-ton hull")
    return rating


def _build_hull(design: ShipDesign, items: list[LineItem]):
    row = HULLS.get(design.hull_tons)
    if row is None:
        raise ValueError(f"{design.hull_tons} tons is not a tabulated hull size")
    items.append(
        LineItem(name="hull", tons=0.0, cost=row.cost * design.configuration.cost_modifier)
    )
    return row


def _build_armor(
    design: ShipDesign, items: list[LineItem], hull_tons: int, base_hull_cost: float
) -> None:
    for fit in design.armor:
        row = ARMOR[fit.type.value]
        increments = fit.percent // 5
        tons_per_increment = max(1.0, hull_tons * 0.05)
        tons = tons_per_increment * increments
        cost = base_hull_cost * (row.cost_percent_per_5_percent / 100) * increments
        for option in fit.options:
            cost += _ARMOR_OPTION_COST_PER_TON[option] * tons
        items.append(LineItem(name=f"{fit.type.value} armor", tons=tons, cost=cost))


def _build_maneuver(design: ShipDesign, items: list[LineItem], hull_tons: int) -> int:
    if design.maneuver_code is None:
        return 0
    row = DRIVE_COSTS[design.maneuver_code]
    rating = _drive_rating(design.maneuver_code, hull_tons)
    items.append(
        LineItem(
            name=f"maneuver drive {design.maneuver_code}",
            tons=row.maneuver_tons,
            cost=row.maneuver_cost,
        )
    )
    return rating


def _build_jump(design: ShipDesign, items: list[LineItem], hull_tons: int) -> int:
    if design.hull_class is HullClass.STARSHIP and design.jump_code is None:
        raise ValueError("starship requires a jump drive")
    if design.jump_code is None:
        return 0
    row = DRIVE_COSTS[design.jump_code]
    rating = _drive_rating(design.jump_code, hull_tons)
    items.append(
        LineItem(name=f"jump drive {design.jump_code}", tons=row.jump_tons, cost=row.jump_cost)
    )
    return rating


def _build_power(
    design: ShipDesign, items: list[LineItem], hull_tons: int, required_rating: int
) -> tuple[int, int]:
    if design.power_code is None:
        raise ValueError("powered craft requires a power plant")
    row = DRIVE_COSTS[design.power_code]
    rating = _drive_rating(design.power_code, hull_tons)
    if rating < required_rating:
        raise ValueError(
            f"power plant rating {rating} below required {required_rating} "
            "(higher of jump/maneuver)"
        )
    items.append(
        LineItem(name=f"power plant {design.power_code}", tons=row.power_tons, cost=row.power_cost)
    )
    return rating, row.power_tons


def _bridge_tons(hull_tons: int) -> int:
    for max_tons, bridge_tons in BRIDGE_SIZES:
        if max_tons is None or hull_tons <= max_tons:
            return bridge_tons
    raise AssertionError("BRIDGE_SIZES must end with an unbounded (None, tons) step")


def _build_computer(design: ShipDesign, items: list[LineItem]) -> None:
    if design.computer is None:
        return
    fit = design.computer
    row = COMPUTERS[fit.model]
    if fit.jump_control and fit.hardened:
        multiplier = 2.0
    elif fit.jump_control or fit.hardened:
        multiplier = 1.5
    else:
        multiplier = 1.0
    items.append(
        LineItem(name=f"computer model/{fit.model}", tons=0.0, cost=row.cost * multiplier)
    )

    total_rating = 0.0
    for software in fit.software:
        srow = SOFTWARE[software.name]
        rating = srow.rating_per_level * software.level
        cost = srow.cost_per_level * software.level
        total_rating += rating
        items.append(LineItem(name=f"{software.name} software", tons=0.0, cost=cost))

    if total_rating > row.rating:
        raise ValueError(f"software rating {total_rating:g} exceeds computer rating {row.rating}")


def _build_electronics(design: ShipDesign, items: list[LineItem]) -> None:
    if design.electronics is None:
        return
    row = ELECTRONICS[design.electronics]
    items.append(LineItem(name=f"electronics: {design.electronics}", tons=row.tons, cost=row.cost))


def _build_quarters(design: ShipDesign, items: list[LineItem]) -> None:
    for field_name, kind in (
        ("staterooms", "stateroom"),
        ("low_berths", "low_berth"),
        ("emergency_low_berths", "emergency_low_berth"),
    ):
        count = getattr(design, field_name)
        if count <= 0:
            continue
        row = QUARTERS[kind]
        items.append(LineItem(name=kind, tons=row.tons * count, cost=row.cost * count))


def _build_fittings(design: ShipDesign, items: list[LineItem]) -> int:
    bonus = 0
    for fit in design.fittings:
        row = FITTINGS[fit.kind]
        if fit.kind == "fuel_scoops" and design.configuration is Configuration.DISTRIBUTED:
            raise ValueError("a distributed hull cannot mount fuel scoops")
        if fit.kind == "vehicle_hangar":
            tons = fit.vehicle_tons * 1.3 * fit.quantity
            cost = fit.vehicle_tons * 0.2 * fit.quantity
        else:
            tons = row.tons * fit.quantity
            cost = row.cost * fit.quantity
        items.append(LineItem(name=fit.kind, tons=tons, cost=cost))
        bonus += row.hull_structure_bonus * fit.quantity
    return bonus


def _build_turrets(design: ShipDesign, items: list[LineItem]) -> int:
    for turret in design.turrets:
        mount = TURRET_MOUNTS[turret.mount]
        weapon_cost = sum(TURRET_WEAPONS[weapon].cost for weapon in turret.weapons)
        items.append(
            LineItem(name=f"{turret.mount} turret", tons=mount.tons, cost=mount.cost + weapon_cost)
        )
    return len(design.turrets)


def _build_crew(design: ShipDesign, drive_tons: float, hardpoints_used: int) -> Crew:
    has_jump_control_software = design.computer is not None and any(
        software.name == "jump_control" for software in design.computer.software
    )
    pilot = 1
    navigator = 0 if has_jump_control_software else 1
    engineers = math.ceil(drive_tons / 35) if drive_tons > 0 else 0
    gunners = hardpoints_used
    screen_operators = len(design.screens)

    passengers = design.passengers_high + design.passengers_middle
    stewards = 0
    medic = 0
    if passengers > 0:
        stewards = math.ceil(design.passengers_high / 4) + math.ceil(design.passengers_middle / 10)
        crew_so_far = pilot + navigator + engineers + gunners + screen_operators + stewards
        medic = math.ceil((crew_so_far + passengers) / 120)

    return Crew(
        pilot=pilot,
        navigator=navigator,
        engineers=engineers,
        gunners=gunners,
        screen_operators=screen_operators,
        medic=medic,
        stewards=stewards,
    )


def build_ship(design: ShipDesign) -> Ship:
    """The single validation authority for SRD ship-design rules (FR-015).

    Pure and deterministic: the same `design` always yields an equal `Ship`.
    Raises `ValueError` naming the first violated rule in SRD build order.
    """
    items: list[LineItem] = []
    hull_tons = design.hull_tons

    hull_row = _build_hull(design, items)
    _build_armor(design, items, hull_tons, hull_row.cost)

    maneuver_rating = _build_maneuver(design, items, hull_tons)
    jump_rating = _build_jump(design, items, hull_tons)
    power_rating, power_tons = _build_power(
        design, items, hull_tons, max(jump_rating, maneuver_rating)
    )

    jump_distance = design.jump_distance if design.jump_distance is not None else jump_rating
    jump_fuel = 0.1 * hull_tons * jump_distance
    power_fuel = (power_tons // 3) * design.power_weeks
    items.append(LineItem(name="jump fuel", tons=jump_fuel, cost=0.0))
    items.append(LineItem(name="power plant fuel", tons=power_fuel, cost=0.0))

    items.append(LineItem(name="bridge", tons=_bridge_tons(hull_tons), cost=hull_tons / 100 * 0.5))

    _build_computer(design, items)
    _build_electronics(design, items)
    _build_quarters(design, items)
    hull_structure_bonus = _build_fittings(design, items)

    hardpoints_used = _build_turrets(design, items)
    hardpoints = hull_tons // 100
    if hardpoints_used > hardpoints:
        raise ValueError(
            f"{hardpoints_used} weapon systems exceed {hardpoints} hardpoints (1 per 100 tons)"
        )

    tonnage_used = sum(item.tons for item in items)
    cargo_tons = hull_tons - tonnage_used
    if cargo_tons < 0:
        raise ValueError(f"components use {tonnage_used:g} tons, hull holds {hull_tons}")

    maneuver_tons = DRIVE_COSTS[design.maneuver_code].maneuver_tons if design.maneuver_code else 0
    jump_tons = DRIVE_COSTS[design.jump_code].jump_tons if design.jump_code else 0
    crew = _build_crew(design, maneuver_tons + jump_tons + power_tons, hardpoints_used)

    total_cost = sum(item.cost for item in items)
    if design.standard_design:
        total_cost *= 0.9

    return Ship(
        design=design,
        hull_tons=hull_tons,
        configuration=design.configuration,
        jump_rating=jump_rating,
        maneuver_rating=maneuver_rating,
        power_rating=power_rating,
        jump_fuel=jump_fuel,
        assumed_jump_distance=jump_distance,
        power_fuel=power_fuel,
        tonnage_used=tonnage_used,
        cargo_tons=cargo_tons,
        hull_points=hull_tons // 50 + hull_structure_bonus,
        structure_points=math.ceil(hull_tons / 50) + hull_structure_bonus,
        hardpoints=hardpoints,
        hardpoints_used=hardpoints_used,
        crew=crew,
        total_cost=total_cost,
        build_weeks=hull_row.build_weeks,
        line_items=tuple(items),
    )
