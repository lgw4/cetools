"""build_ship(design) -> Ship: deterministic allocation, costing, validation.

Follows the SRD build order ("Ship Design Checklist") exactly: hull, armor, maneuver
drive, jump drive, power plant, fuel, bridge, computer/software, electronics,
quarters, fittings, turrets, bays, screens, cargo, crew, cost, build time.
Every SRD rule check lives here, in that order, so a design that violates
several reports the first violation in build order (FR-015, SC-005).
`ShipDesign.__post_init__` already guarantees the record is well-formed; this
module only ever rejects *rules* violations.

`HullClass.SMALL_CRAFT` designs (10-95 tons) follow the same build order under
a distinct ruleset (SRD "Small Craft Design"): a cockpit instead of a bridge, no
jump drive, power-plant fuel rounded to 0.1 ton with a one-week floor, exactly
one hardpoint, and an energy-weapon cap keyed by the power plant's code.
"""

from __future__ import annotations

import math

from cetools.engine.ships.models import Configuration, Crew, HullClass, LineItem, Ship, ShipDesign
from cetools.engine.ships.tables import (
    AMMO,
    ARMOR,
    ARMOR_OPTIONS,
    BAYS,
    BRIDGE_SIZES,
    COCKPITS,
    COMPUTERS,
    CONFIGURATIONS,
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
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_COCKPIT_COST_PER_20_TONS = 0.1
BAY_FIRE_CONTROL_TONS = 1.0
"""Fire control a weapon bay needs beyond its own 50 t (research Part H). Not
tabulated data—applied uniformly to every bay kind—so it lives here rather
than in `tables.BAYS`, and `generator.py` imports it for the same allocation."""

JUMP_CONTROL_RATING_BONUS = 5
"""The jump-control computer option's "+5 jump rating" (SRD "Ship Computer Options"):
raises the effective computer rating available for installed software by 5,
letting a jump-control computer run 5 more points of software than its bare
model rating allows. Not tabulated data (it modifies a `COMPUTERS` row rather
than being one), so it lives here rather than in `tables.py`."""


def _drive_letter(code: str) -> str:
    """The bare A-Z drive letter a small-craft "s"-prefixed code shares with
    ``DRIVE_COSTS`` (research Part K: component tonnage/cost is unified across
    both rulesets; only performance is looked up from a separate table)."""
    return code[1:] if code.startswith("s") else code


def _drive_rating(code: str, hull_tons: int, hull_class: HullClass) -> int:
    table = (
        SMALL_CRAFT_DRIVE_PERFORMANCE if hull_class is HullClass.SMALL_CRAFT else DRIVE_PERFORMANCE
    )
    rating = table.get(_drive_letter(code), {}).get(hull_tons)
    if rating is None:
        raise ValueError(f"drive code {code} is not available on a {hull_tons}-ton hull")
    return rating


def _build_hull(design: ShipDesign, items: list[LineItem]):
    table = HULLS if design.hull_class is HullClass.STARSHIP else SMALL_CRAFT_HULLS
    row = table.get(design.hull_tons)
    if row is None:
        raise ValueError(f"{design.hull_tons} tons is not a tabulated hull size")
    items.append(
        LineItem(name="hull", tons=0.0, cost=row.cost * design.configuration.cost_modifier)
    )
    return row


def _build_armor(
    design: ShipDesign, items: list[LineItem], hull_tons: int, base_hull_cost: float
) -> int:
    total_protection = 0
    for fit in design.armor:
        if fit.percent % 5 != 0:
            raise ValueError("armor must be added in 5% increments (min 1 ton)")
        row = ARMOR[fit.type.value]
        increments = fit.percent // 5
        # The SRD's own armor-by-type table states "minimum
        # 1 ton" per 5% increment, so a hull whose 5% is under 1 ton still costs
        # a full ton per increment rather than being rejected.
        tons_per_increment = max(1.0, hull_tons * 0.05)
        tons = tons_per_increment * increments
        cost = base_hull_cost * (row.cost_percent_per_5_percent / 100) * increments
        for option in fit.options:
            cost += ARMOR_OPTIONS[option].cost_per_ton * tons
        items.append(LineItem(name=f"{fit.type.value} armor", tons=tons, cost=cost))
        total_protection += row.protection_per_5_percent * increments
    return total_protection


def _build_maneuver(design: ShipDesign, items: list[LineItem], hull_tons: int) -> int:
    if design.maneuver_code is None:
        return 0
    row = DRIVE_COSTS[_drive_letter(design.maneuver_code)]
    rating = _drive_rating(design.maneuver_code, hull_tons, design.hull_class)
    items.append(
        LineItem(
            name=f"maneuver drive {design.maneuver_code}",
            tons=row.maneuver_tons,
            cost=row.maneuver_cost,
        )
    )
    return rating


def _build_jump(design: ShipDesign, items: list[LineItem], hull_tons: int) -> int:
    if design.hull_class is HullClass.SMALL_CRAFT and design.jump_code is not None:
        raise ValueError("small craft cannot mount a jump drive")
    if design.hull_class is HullClass.STARSHIP and design.jump_code is None:
        raise ValueError("starship requires a jump drive")
    if design.jump_code is None:
        return 0
    row = DRIVE_COSTS[_drive_letter(design.jump_code)]
    rating = _drive_rating(design.jump_code, hull_tons, design.hull_class)
    items.append(
        LineItem(name=f"jump drive {design.jump_code}", tons=row.jump_tons, cost=row.jump_cost)
    )
    return rating


def _build_power(
    design: ShipDesign, items: list[LineItem], hull_tons: int, required_rating: int
) -> tuple[int, int]:
    if design.power_code is None:
        raise ValueError("powered craft requires a power plant")
    row = DRIVE_COSTS[_drive_letter(design.power_code)]
    rating = _drive_rating(design.power_code, hull_tons, design.hull_class)
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


def _build_bridge_or_cockpit(design: ShipDesign, items: list[LineItem], hull_tons: int) -> None:
    if design.hull_class is HullClass.SMALL_CRAFT and design.bridge:
        raise ValueError("small craft requires a cockpit, not a bridge")
    if design.hull_class is HullClass.STARSHIP and design.cockpit is not None:
        raise ValueError("a starship requires a bridge, not a cockpit")
    if design.cockpit is not None:
        row = COCKPITS[design.cockpit]
        cost = hull_tons / 20 * _COCKPIT_COST_PER_20_TONS
        items.append(LineItem(name=f"{design.cockpit} cockpit", tons=row.tons, cost=cost))
    else:
        items.append(
            LineItem(name="bridge", tons=_bridge_tons(hull_tons), cost=hull_tons / 100 * 0.5)
        )


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

    effective_rating = row.rating + JUMP_CONTROL_RATING_BONUS if fit.jump_control else row.rating
    if total_rating > effective_rating:
        raise ValueError(
            f"software rating {total_rating:g} exceeds computer rating {effective_rating:g}"
        )


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
        if row.forbidden_on_distributed and design.configuration is Configuration.DISTRIBUTED:
            raise ValueError(f"a distributed hull cannot mount {fit.kind.replace('_', ' ')}")
        if row.tons_per_vehicle_ton is not None:
            tons = fit.vehicle_tons * row.tons_per_vehicle_ton * fit.quantity
            cost = fit.vehicle_tons * row.cost_per_vehicle_ton * fit.quantity
        else:
            tons = row.tons * fit.quantity
            cost = row.cost * fit.quantity
        items.append(LineItem(name=fit.kind, tons=tons, cost=cost))
        bonus += row.hull_structure_bonus * fit.quantity
    return bonus


def _ammo_row(ammo):
    """The `AMMO` row for one `AmmoFit`, matched on the row's ``kind``/``type``
    columns rather than on a key spelling, so a new SRD ammunition entry is a
    data-only edit (SC-006). `AmmoFit`'s own validation guarantees a match."""
    return next(row for row in AMMO.values() if row.kind == ammo.kind and row.type == ammo.type)


def _build_turrets(design: ShipDesign, items: list[LineItem]) -> int:
    for turret in design.turrets:
        mount = TURRET_MOUNTS[turret.mount]
        weapon_cost = sum(TURRET_WEAPONS[weapon].cost for weapon in turret.weapons)
        items.append(
            LineItem(name=f"{turret.mount} turret", tons=mount.tons, cost=mount.cost + weapon_cost)
        )
        for ammo in turret.ammo:
            row = _ammo_row(ammo)
            items.append(
                LineItem(
                    name=f"{ammo.kind} ammo" if ammo.type is None else f"{ammo.type} missile ammo",
                    tons=ammo.count / row.rounds_per_ton,
                    cost=ammo.count * row.cost_per_round,
                    discountable=False,
                )
            )
    return len(design.turrets)


def _build_bays(design: ShipDesign, items: list[LineItem]) -> int:
    for bay in design.bays:
        row = BAYS[bay.kind]
        items.append(LineItem(name=f"{bay.kind} bay", tons=row.tons, cost=row.cost))
        items.append(
            LineItem(name=f"{bay.kind} bay fire control", tons=BAY_FIRE_CONTROL_TONS, cost=0.0)
        )
    return len(design.bays)


def _build_screens(design: ShipDesign, items: list[LineItem]) -> None:
    for screen in design.screens:
        row = SCREENS[screen.kind]
        items.append(LineItem(name=f"{screen.kind} screen", tons=row.tons, cost=row.cost))


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


def _fitted_rows(design: ShipDesign):
    """Every table row the design actually fits, in build order.

    Ship *software* is the one deliberate omission: the SRD's TL column for it
    is a per-level floor ("9+", "10+"), not a value for the row, so FR-028a's
    enumeration does not name it.
    """
    # `_build_hull` has already rejected an untabulated hull size by the time
    # this runs, so the lookup cannot miss.
    hulls = HULLS if design.hull_class is HullClass.STARSHIP else SMALL_CRAFT_HULLS
    yield hulls[design.hull_tons]
    yield CONFIGURATIONS[design.configuration.value]

    for fit in design.armor:
        yield ARMOR[fit.type.value]
        for option in fit.options:
            yield ARMOR_OPTIONS[option]

    for code in (design.maneuver_code, design.jump_code, design.power_code):
        if code is not None:
            yield DRIVE_COSTS[_drive_letter(code)]

    if design.cockpit is not None:
        yield COCKPITS[design.cockpit]

    if design.computer is not None:
        yield COMPUTERS[design.computer.model]

    # A design that buys no package still carries the Standard suite included
    # in its bridge or cockpit, which is why the derived value has a floor of 8
    # and `Ship.tech_level` is never absent (FR-028c).
    yield ELECTRONICS[design.electronics or "standard"]

    for field_name, kind in (
        ("staterooms", "stateroom"),
        ("low_berths", "low_berth"),
        ("emergency_low_berths", "emergency_low_berth"),
    ):
        if getattr(design, field_name) > 0:
            yield QUARTERS[kind]

    for fitting in design.fittings:
        yield FITTINGS[fitting.kind]

    for turret in design.turrets:
        yield TURRET_MOUNTS[turret.mount]
        for weapon in turret.weapons:
            yield TURRET_WEAPONS[weapon]
        for ammo in turret.ammo:
            yield _ammo_row(ammo)

    for bay in design.bays:
        yield BAYS[bay.kind]

    for screen in design.screens:
        yield SCREENS[screen.kind]


def _derive_tech_level(design: ShipDesign) -> int:
    """The highest tech level among the fitted components' rows (FR-028).

    Reads ``tl`` off whatever row is fitted rather than consulting a list of
    "categories that have a tech level", so adding a ``tl`` to an SRD row
    widens the derivation with no change here (SC-007). A row carrying no
    ``tl`` column contributes nothing—the SRD tabulates none for hulls,
    configurations, drives, cockpits, quarters or fittings—and so does an
    individual ``tl`` of ``None``, which is the fixed mounting's "-" cell.
    """
    levels = [row.tl for row in _fitted_rows(design) if getattr(row, "tl", None) is not None]
    return max(levels, default=ELECTRONICS["standard"].tl)


def _total_cost(items: list[LineItem], *, discount: bool) -> float:
    """Sum every `LineItem`'s cost, applying the 10% standard-design discount
    (research Part J) to every discountable item; fuel and ammunition are
    marked `discountable=False` and are never discounted."""
    exempt = sum(item.cost for item in items if not item.discountable)
    discountable = sum(item.cost for item in items if item.discountable)
    if discount:
        discountable *= 0.9
    return discountable + exempt


def build_ship(design: ShipDesign) -> Ship:
    """The single validation authority for SRD ship-design rules (FR-015).

    Pure and deterministic: the same `design` always yields an equal `Ship`.
    Raises `ValueError` naming the first violated rule in SRD build order.
    """
    items: list[LineItem] = []
    hull_tons = design.hull_tons

    hull_row = _build_hull(design, items)
    armor_protection = _build_armor(design, items, hull_tons, hull_row.cost)

    maneuver_rating = _build_maneuver(design, items, hull_tons)
    jump_rating = _build_jump(design, items, hull_tons)
    power_rating, power_tons = _build_power(
        design, items, hull_tons, max(jump_rating, maneuver_rating)
    )

    jump_distance = design.jump_distance if design.jump_distance is not None else jump_rating
    jump_fuel = 0.1 * hull_tons * jump_distance
    minimum_weeks = 2 if design.hull_class is HullClass.STARSHIP else 1
    if design.power_weeks < minimum_weeks:
        raise ValueError(
            f"power_weeks must be >= {minimum_weeks} for a {design.hull_class.value}, "
            f"got {design.power_weeks}"
        )
    if design.hull_class is HullClass.SMALL_CRAFT:
        power_fuel_per_week = math.floor(power_tons / 3 * 10) / 10
    else:
        power_fuel_per_week = power_tons // 3
    power_fuel = power_fuel_per_week * design.power_weeks
    items.append(LineItem(name="jump fuel", tons=jump_fuel, cost=0.0, discountable=False))
    items.append(LineItem(name="power plant fuel", tons=power_fuel, cost=0.0, discountable=False))

    _build_bridge_or_cockpit(design, items, hull_tons)

    _build_computer(design, items)
    _build_electronics(design, items)
    _build_quarters(design, items)
    hull_structure_bonus = _build_fittings(design, items)

    hardpoints_used = _build_turrets(design, items)
    hardpoints_used += _build_bays(design, items)
    _build_screens(design, items)
    hardpoints = 1 if design.hull_class is HullClass.SMALL_CRAFT else hull_tons // 100
    if hardpoints_used > hardpoints:
        raise ValueError(
            f"{hardpoints_used} weapon systems exceed {hardpoints} hardpoints (1 per 100 tons)"
        )

    if design.hull_class is HullClass.SMALL_CRAFT and design.bays:
        raise ValueError("small craft cannot mount a weapon bay")

    if design.hull_class is HullClass.SMALL_CRAFT:
        energy_weapon_count = sum(
            1
            for turret in design.turrets
            for weapon in turret.weapons
            if TURRET_WEAPONS[weapon].energy
        )
        energy_cap = SMALL_CRAFT_ENERGY_CAPS[_drive_letter(design.power_code)]
        if energy_weapon_count > energy_cap:
            raise ValueError(
                f"power plant code {design.power_code} allows at most {energy_cap} energy weapons"
            )

    tonnage_used = sum(item.tons for item in items)
    cargo_tons = hull_tons - tonnage_used
    if cargo_tons < 0:
        raise ValueError(f"components use {tonnage_used:g} tons, hull holds {hull_tons}")

    maneuver_tons = (
        DRIVE_COSTS[_drive_letter(design.maneuver_code)].maneuver_tons
        if design.maneuver_code
        else 0
    )
    jump_tons = DRIVE_COSTS[_drive_letter(design.jump_code)].jump_tons if design.jump_code else 0
    crew = _build_crew(design, maneuver_tons + jump_tons + power_tons, hardpoints_used)

    total_cost = _total_cost(items, discount=design.standard_design)

    return Ship(
        design=design,
        tech_level=(
            design.tech_level if design.tech_level is not None else _derive_tech_level(design)
        ),
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
        armor_protection=armor_protection,
        hardpoints=hardpoints,
        hardpoints_used=hardpoints_used,
        crew=crew,
        total_cost=total_cost,
        build_weeks=hull_row.build_weeks,
        line_items=tuple(items),
    )
