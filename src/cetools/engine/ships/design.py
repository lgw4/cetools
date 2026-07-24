"""TOML design-file I/O (contracts/design-schema.md).

`loads_design`/`load_design` parse *shape* only: malformed TOML, unknown keys,
wrong types, and unknown enum strings raise `ValueError`. They never check SRD
*rules* (FR-015)—that is `build_ship`'s job. `dump_design` is the matching
writer: `loads_design(dump_design(d)) == d` for every well-formed `d`.
"""

from __future__ import annotations

import os
import tomllib

from cetools.engine.ships.models import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    FittingFit,
    HullClass,
    ScreenFit,
    ShipDesign,
    SoftwareFit,
    TurretFit,
)

_TOP_LEVEL_KEYS = {
    "name",
    "hull_tons",
    "configuration",
    "standard_design",
    "drives",
    "bridge",
    "computer",
    "electronics",
    "quarters",
    "armor",
    "fittings",
    "turrets",
    "bays",
    "screens",
    "passengers",
}


def _require_table(value, path: str) -> dict:
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be a table, got {type(value).__name__}")
    return value


def _require_str(value, path: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string, got {type(value).__name__}")
    return value


def _require_int(value, path: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{path} must be an integer, got {type(value).__name__}")
    return value


def _require_bool(value, path: str) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{path} must be a boolean, got {type(value).__name__}")
    return value


def _parse_enum(enum_cls, value, path: str):
    if not isinstance(value, str):
        raise ValueError(f"{path} must be a string, got {type(value).__name__}")
    try:
        return enum_cls(value)
    except ValueError:
        valid = ", ".join(member.value for member in enum_cls)
        raise ValueError(f"unknown {path} {value!r}; valid: {valid}") from None


def _reject_unknown(keys, allowed: set[str], path: str) -> None:
    unknown = set(keys) - allowed
    if unknown:
        raise ValueError(f"unknown key(s) in {path}: {sorted(unknown)}")


def _parse_drives(data: dict, kwargs: dict) -> None:
    drives = _require_table(data.get("drives", {}), "[drives]")
    _reject_unknown(
        drives, {"jump", "maneuver", "power", "jump_distance", "power_weeks"}, "[drives]"
    )
    if "jump" in drives:
        kwargs["jump_code"] = _require_str(drives["jump"], "drives.jump")
    if "maneuver" in drives:
        kwargs["maneuver_code"] = _require_str(drives["maneuver"], "drives.maneuver")
    if "power" in drives:
        kwargs["power_code"] = _require_str(drives["power"], "drives.power")
    if "jump_distance" in drives:
        kwargs["jump_distance"] = _require_int(drives["jump_distance"], "drives.jump_distance")
    if "power_weeks" in drives:
        kwargs["power_weeks"] = _require_int(drives["power_weeks"], "drives.power_weeks")


def _parse_bridge(data: dict, kwargs: dict) -> None:
    bridge = _require_table(data.get("bridge", {}), "[bridge]")
    _reject_unknown(bridge, {"present", "cockpit"}, "[bridge]")
    if "cockpit" in bridge:
        kwargs["cockpit"] = _require_str(bridge["cockpit"], "bridge.cockpit")
        kwargs["bridge"] = False
    elif "present" in bridge:
        kwargs["bridge"] = _require_bool(bridge["present"], "bridge.present")


def _parse_software(entries, path: str) -> tuple[SoftwareFit, ...]:
    software = []
    for entry in entries:
        _require_table(entry, path)
        _reject_unknown(entry, {"name", "level"}, path)
        if "name" not in entry:
            raise ValueError(f"{path} entry requires 'name'")
        if "level" not in entry:
            raise ValueError(f"{path} entry requires 'level'")
        name = _require_str(entry["name"], f"{path}.name")
        level = _require_int(entry["level"], f"{path}.level")
        software.append(SoftwareFit(name=name, level=level))
    return tuple(software)


def _parse_computer(data: dict, kwargs: dict) -> None:
    if "computer" not in data:
        return
    computer = _require_table(data["computer"], "[computer]")
    _reject_unknown(computer, {"model", "jump_control", "hardened", "software"}, "[computer]")
    if "model" not in computer:
        raise ValueError("[computer] requires 'model'")
    model = _require_int(computer["model"], "computer.model")
    jump_control = _require_bool(computer.get("jump_control", False), "computer.jump_control")
    hardened = _require_bool(computer.get("hardened", False), "computer.hardened")
    software = _parse_software(computer.get("software", []), "computer.software[]")
    kwargs["computer"] = ComputerFit(
        model=model, jump_control=jump_control, hardened=hardened, software=software
    )


def _parse_quarters(data: dict, kwargs: dict) -> None:
    quarters = _require_table(data.get("quarters", {}), "[quarters]")
    _reject_unknown(quarters, {"staterooms", "low_berths", "emergency_low_berths"}, "[quarters]")
    if "staterooms" in quarters:
        kwargs["staterooms"] = _require_int(quarters["staterooms"], "quarters.staterooms")
    if "low_berths" in quarters:
        kwargs["low_berths"] = _require_int(quarters["low_berths"], "quarters.low_berths")
    if "emergency_low_berths" in quarters:
        kwargs["emergency_low_berths"] = _require_int(
            quarters["emergency_low_berths"], "quarters.emergency_low_berths"
        )


def _parse_armor(data: dict) -> tuple[ArmorFit, ...]:
    fits = []
    for entry in data.get("armor", []):
        _require_table(entry, "[[armor]]")
        _reject_unknown(entry, {"type", "percent", "options"}, "[[armor]]")
        if "type" not in entry:
            raise ValueError("[[armor]] entry requires 'type'")
        if "percent" not in entry:
            raise ValueError("[[armor]] entry requires 'percent'")
        armor_type = _parse_enum(ArmorType, entry["type"], "armor.type")
        percent = _require_int(entry["percent"], "armor.percent")
        options = tuple(entry.get("options", ()))
        fits.append(ArmorFit(type=armor_type, percent=percent, options=options))
    return tuple(fits)


def _parse_fittings(data: dict) -> tuple[FittingFit, ...]:
    fits = []
    for entry in data.get("fittings", []):
        _require_table(entry, "[[fittings]]")
        _reject_unknown(entry, {"kind", "quantity", "vehicle_tons"}, "[[fittings]]")
        if "kind" not in entry:
            raise ValueError("[[fittings]] entry requires 'kind'")
        kind = _require_str(entry["kind"], "fittings.kind")
        quantity = _require_int(entry.get("quantity", 1), "fittings.quantity")
        vehicle_tons = entry.get("vehicle_tons")
        if vehicle_tons is not None:
            vehicle_tons = _require_int(vehicle_tons, "fittings.vehicle_tons")
        fits.append(FittingFit(kind=kind, quantity=quantity, vehicle_tons=vehicle_tons))
    return tuple(fits)


def _parse_ammo(entries, path: str) -> tuple[AmmoFit, ...]:
    ammo = []
    for entry in entries:
        _require_table(entry, path)
        _reject_unknown(entry, {"kind", "count", "type"}, path)
        if "kind" not in entry:
            raise ValueError(f"{path} entry requires 'kind'")
        if "count" not in entry:
            raise ValueError(f"{path} entry requires 'count'")
        kind = _require_str(entry["kind"], f"{path}.kind")
        count = _require_int(entry["count"], f"{path}.count")
        ammo_type = entry.get("type")
        if ammo_type is not None:
            ammo_type = _require_str(ammo_type, f"{path}.type")
        ammo.append(AmmoFit(kind=kind, count=count, type=ammo_type))
    return tuple(ammo)


def _parse_turrets(data: dict) -> tuple[TurretFit, ...]:
    turrets = []
    for entry in data.get("turrets", []):
        _require_table(entry, "[[turrets]]")
        _reject_unknown(entry, {"mount", "weapons", "ammo"}, "[[turrets]]")
        if "mount" not in entry:
            raise ValueError("[[turrets]] entry requires 'mount'")
        mount = _require_str(entry["mount"], "turrets.mount")
        weapons = tuple(entry.get("weapons", ()))
        ammo = _parse_ammo(entry.get("ammo", []), "turrets.ammo[]")
        turrets.append(TurretFit(mount=mount, weapons=weapons, ammo=ammo))
    return tuple(turrets)


def _parse_bays(data: dict) -> tuple[BayFit, ...]:
    bays = []
    for entry in data.get("bays", []):
        _require_table(entry, "[[bays]]")
        _reject_unknown(entry, {"kind"}, "[[bays]]")
        if "kind" not in entry:
            raise ValueError("[[bays]] entry requires 'kind'")
        bays.append(BayFit(kind=_require_str(entry["kind"], "bays.kind")))
    return tuple(bays)


def _parse_screens(data: dict) -> tuple[ScreenFit, ...]:
    screens = []
    for entry in data.get("screens", []):
        _require_table(entry, "[[screens]]")
        _reject_unknown(entry, {"kind"}, "[[screens]]")
        if "kind" not in entry:
            raise ValueError("[[screens]] entry requires 'kind'")
        screens.append(ScreenFit(kind=_require_str(entry["kind"], "screens.kind")))
    return tuple(screens)


def _parse_passengers(data: dict, kwargs: dict) -> None:
    passengers = _require_table(data.get("passengers", {}), "[passengers]")
    _reject_unknown(passengers, {"high", "middle"}, "[passengers]")
    if "high" in passengers:
        kwargs["passengers_high"] = _require_int(passengers["high"], "passengers.high")
    if "middle" in passengers:
        kwargs["passengers_middle"] = _require_int(passengers["middle"], "passengers.middle")


def loads_design(text: str) -> ShipDesign:
    """Parse TOML *text* into a well-formed `ShipDesign` (shape only, FR-015)."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise ValueError(f"malformed TOML: {exc}") from exc

    _reject_unknown(data, _TOP_LEVEL_KEYS, "design")

    if "hull_tons" not in data:
        raise ValueError("missing required key 'hull_tons'")

    kwargs: dict = {"hull_tons": _require_int(data["hull_tons"], "hull_tons")}

    if "name" in data:
        kwargs["name"] = _require_str(data["name"], "name")
    if "standard_design" in data:
        kwargs["standard_design"] = _require_bool(data["standard_design"], "standard_design")
    if "configuration" in data:
        kwargs["configuration"] = _parse_enum(
            Configuration, data["configuration"], "configuration"
        )

    _parse_drives(data, kwargs)
    _parse_bridge(data, kwargs)
    _parse_computer(data, kwargs)

    if "electronics" in data:
        kwargs["electronics"] = _require_str(data["electronics"], "electronics")

    _parse_quarters(data, kwargs)
    kwargs["armor"] = _parse_armor(data)
    kwargs["fittings"] = _parse_fittings(data)
    kwargs["turrets"] = _parse_turrets(data)
    kwargs["bays"] = _parse_bays(data)
    kwargs["screens"] = _parse_screens(data)
    _parse_passengers(data, kwargs)

    return ShipDesign(**kwargs)


def load_design(path: str | os.PathLike) -> ShipDesign:
    """Read the design file at `path` and parse it with `loads_design`.

    `path` is always a filesystem path, never TOML text (mirrors
    `json.load`/`json.loads`). Raises `OSError` if the file cannot be read.
    """
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return loads_design(text)


def _toml_str(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _dump_software(software: tuple[SoftwareFit, ...]) -> str:
    entries = ", ".join(
        f"{{ name = {_toml_str(fit.name)}, level = {fit.level} }}" for fit in software
    )
    return f"[{entries}]"


def _dump_ammo(ammo: tuple[AmmoFit, ...]) -> str:
    entries = []
    for fit in ammo:
        if fit.type is not None:
            entries.append(
                f"{{ kind = {_toml_str(fit.kind)}, type = {_toml_str(fit.type)}, "
                f"count = {fit.count} }}"
            )
        else:
            entries.append(f"{{ kind = {_toml_str(fit.kind)}, count = {fit.count} }}")
    return f"[{', '.join(entries)}]"


def dump_design(design: ShipDesign) -> str:
    """Serialize `design` to builder-compatible TOML (canonical key order, FR-023).

    `loads_design(dump_design(d)) == d` for any well-formed `d` (SC-008).
    """
    lines: list[str] = []

    if design.name is not None:
        lines.append(f"name = {_toml_str(design.name)}")
    lines.append(f"hull_tons = {design.hull_tons}")
    if design.configuration is not Configuration.STANDARD:
        lines.append(f"configuration = {_toml_str(design.configuration.value)}")
    if design.standard_design:
        lines.append("standard_design = true")
    if design.electronics is not None:
        lines.append(f"electronics = {_toml_str(design.electronics)}")

    drives_lines = []
    if design.jump_code is not None:
        drives_lines.append(f"jump = {_toml_str(design.jump_code)}")
    if design.maneuver_code is not None:
        drives_lines.append(f"maneuver = {_toml_str(design.maneuver_code)}")
    if design.power_code is not None:
        drives_lines.append(f"power = {_toml_str(design.power_code)}")
    if design.jump_distance is not None:
        drives_lines.append(f"jump_distance = {design.jump_distance}")
    default_weeks = 2 if design.hull_class is HullClass.STARSHIP else 1
    if design.power_weeks != default_weeks:
        drives_lines.append(f"power_weeks = {design.power_weeks}")
    if drives_lines:
        lines.append("")
        lines.append("[drives]")
        lines.extend(drives_lines)

    bridge_lines = []
    if design.cockpit is not None:
        bridge_lines.append(f"cockpit = {_toml_str(design.cockpit)}")
    elif not design.bridge:
        bridge_lines.append("present = false")
    if bridge_lines:
        lines.append("")
        lines.append("[bridge]")
        lines.extend(bridge_lines)

    if design.computer is not None:
        lines.append("")
        lines.append("[computer]")
        lines.append(f"model = {design.computer.model}")
        if design.computer.jump_control:
            lines.append("jump_control = true")
        if design.computer.hardened:
            lines.append("hardened = true")
        if design.computer.software:
            lines.append(f"software = {_dump_software(design.computer.software)}")

    quarters_lines = []
    if design.staterooms:
        quarters_lines.append(f"staterooms = {design.staterooms}")
    if design.low_berths:
        quarters_lines.append(f"low_berths = {design.low_berths}")
    if design.emergency_low_berths:
        quarters_lines.append(f"emergency_low_berths = {design.emergency_low_berths}")
    if quarters_lines:
        lines.append("")
        lines.append("[quarters]")
        lines.extend(quarters_lines)

    for fit in design.armor:
        lines.append("")
        lines.append("[[armor]]")
        lines.append(f"type = {_toml_str(fit.type.value)}")
        lines.append(f"percent = {fit.percent}")
        if fit.options:
            lines.append(f"options = [{', '.join(_toml_str(o) for o in fit.options)}]")

    for fit in design.fittings:
        lines.append("")
        lines.append("[[fittings]]")
        lines.append(f"kind = {_toml_str(fit.kind)}")
        if fit.quantity != 1:
            lines.append(f"quantity = {fit.quantity}")
        if fit.vehicle_tons is not None:
            lines.append(f"vehicle_tons = {fit.vehicle_tons}")

    for turret in design.turrets:
        lines.append("")
        lines.append("[[turrets]]")
        lines.append(f"mount = {_toml_str(turret.mount)}")
        lines.append(f"weapons = [{', '.join(_toml_str(w) for w in turret.weapons)}]")
        if turret.ammo:
            lines.append(f"ammo = {_dump_ammo(turret.ammo)}")

    for bay in design.bays:
        lines.append("")
        lines.append("[[bays]]")
        lines.append(f"kind = {_toml_str(bay.kind)}")

    for screen in design.screens:
        lines.append("")
        lines.append("[[screens]]")
        lines.append(f"kind = {_toml_str(screen.kind)}")

    if design.passengers_high or design.passengers_middle:
        lines.append("")
        lines.append("[passengers]")
        if design.passengers_high:
            lines.append(f"high = {design.passengers_high}")
        if design.passengers_middle:
            lines.append(f"middle = {design.passengers_middle}")

    return "\n".join(lines) + "\n"
