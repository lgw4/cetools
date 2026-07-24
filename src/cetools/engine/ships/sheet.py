"""render_sheet(ship) -> human-readable ship sheet (FR-022).

A pure function of the `Ship` alone: it renders nothing the `Ship` does not
carry, notably not a generator seed (the CLI reports that separately on
stderr). Total for any valid `Ship` and deterministic (byte-identical for
equal ships, SC-004).
"""

from __future__ import annotations

from cetools.engine.ships.models import Ship


def _format_turret(turret) -> str:
    text = f"{turret.mount} turret [{', '.join(turret.weapons)}]"
    if turret.ammo:
        ammo_strs = [
            (
                f"{ammo.kind} ammo x{ammo.count}"
                if ammo.type is None
                else f"{ammo.type} missile ammo x{ammo.count}"
            )
            for ammo in turret.ammo
        ]
        text += f" (ammo: {', '.join(ammo_strs)})"
    return text


def render_sheet(ship: Ship) -> str:
    design = ship.design
    lines = [design.name if design.name is not None else "Unnamed Ship"]

    lines.append(f"Hull: {ship.hull_tons} tons, {ship.configuration.value} configuration")

    week_word = "week" if design.power_weeks == 1 else "weeks"
    is_small_craft = design.cockpit is not None
    if is_small_craft:
        lines.append(f"Maneuver-{ship.maneuver_rating} Power-{ship.power_rating}")
        lines.append(f"Fuel: {ship.power_fuel:g}t power plant ({design.power_weeks} {week_word})")
    else:
        lines.append(
            f"Jump-{ship.jump_rating} Maneuver-{ship.maneuver_rating} Power-{ship.power_rating}"
        )
        lines.append(
            f"Fuel: {ship.jump_fuel:g}t jump (assumes range {ship.assumed_jump_distance}), "
            f"{ship.power_fuel:g}t power plant ({design.power_weeks} {week_word})"
        )

    bridge_item = next(
        (
            item
            for item in ship.line_items
            if item.name == "bridge" or item.name.endswith("cockpit")
        ),
        None,
    )
    if bridge_item is not None:
        if is_small_craft:
            lines.append(f"Cockpit: {design.cockpit} ({bridge_item.tons:g}t)")
        else:
            lines.append(f"Bridge: {bridge_item.tons:g}t")

    if design.computer is not None:
        computer = design.computer
        options = []
        if computer.jump_control:
            options.append("jump-control")
        if computer.hardened:
            options.append("hardened")
        suffix = f" ({', '.join(options)})" if options else ""
        lines.append(f"Computer: Model/{computer.model}{suffix}")
        for software in computer.software:
            lines.append(f"  Software: {software.name} (level {software.level})")

    if design.electronics is not None:
        lines.append(f"Electronics: {design.electronics}")

    crew = ship.crew
    lines.append(
        "Crew: "
        f"pilot {crew.pilot}, navigator {crew.navigator}, engineers {crew.engineers}, "
        f"gunners {crew.gunners}, screen operators {crew.screen_operators}, "
        f"medic {crew.medic}, stewards {crew.stewards} (total {crew.total})"
    )

    if design.staterooms or design.low_berths or design.emergency_low_berths:
        lines.append(
            "Quarters: "
            f"{design.staterooms} staterooms, {design.low_berths} low berths, "
            f"{design.emergency_low_berths} emergency low berths"
        )

    if design.fittings:
        fitting_strs = ", ".join(f"{fit.kind} x{fit.quantity}" for fit in design.fittings)
        lines.append(f"Fittings: {fitting_strs}")

    if design.armor:
        armor_strs = ", ".join(f"{fit.type.value} {fit.percent}%" for fit in design.armor)
        lines.append(f"Armor: {armor_strs}")

    if design.turrets or design.bays or design.screens:
        armament_strs = [_format_turret(turret) for turret in design.turrets]
        armament_strs += [f"{bay.kind} bay" for bay in design.bays]
        armament_strs += [f"{screen.kind} screen" for screen in design.screens]
        lines.append(f"Armaments: {'; '.join(armament_strs)}")

    lines.append(
        f"Tonnage: {ship.tonnage_used:g} used, {ship.cargo_tons:g} cargo, "
        f"hardpoints {ship.hardpoints_used}/{ship.hardpoints}"
    )
    lines.append(f"Hull points: {ship.hull_points}, Structure points: {ship.structure_points}")
    lines.append(f"Cost: MCr{ship.total_cost:g}, Build time: {ship.build_weeks} weeks")

    return "\n".join(lines)
