"""Ship-design domain models.

Two record families: `ShipDesign` (declarative input, mirrors the TOML schema) and
`Ship` (computed output, carries its originating `ShipDesign`). Every validator
below checks *shape*, never SRD *rules*: a design that is well-formed but
rules-illegal (e.g. a small craft with a jump drive) constructs cleanly here and is
rejected only by `build_ship` (FR-015; see data-model.md "Validation—shape only").
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cetools.engine.ships.tables import (
    COCKPITS,
    COMPUTERS,
    CONFIG_MODIFIERS,
    ELECTRONICS,
    FITTINGS,
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)

_ARMOR_OPTIONS = frozenset({"reflec", "self_sealing", "stealth"})
_AMMO_KINDS = frozenset({"sand_barrels", "missile"})
_MISSILE_TYPES = frozenset({"standard", "smart", "nuclear"})
_BAY_KINDS = frozenset({"missile_bank", "particle", "meson", "fusion"})
_SCREEN_KINDS = frozenset({"meson_screen", "nuclear_damper"})


class Configuration(Enum):
    """A ship's hull shape (research.md Part B)."""

    DISTRIBUTED = "distributed"
    STANDARD = "standard"
    STREAMLINED = "streamlined"

    @property
    def cost_modifier(self) -> float:
        """The hull-cost multiplier: x0.9 / x1.0 / x1.1."""
        return CONFIG_MODIFIERS[self.value]


class ArmorType(Enum):
    """A ship-armor material (research.md Part F)."""

    TITANIUM_STEEL = "titanium_steel"
    CRYSTALIRON = "crystaliron"
    BONDED_SUPERDENSE = "bonded_superdense"


class HullClass(Enum):
    """Which ruleset a hull builds under: bridge vs cockpit, jump-capable or not."""

    STARSHIP = "starship"
    SMALL_CRAFT = "small_craft"


# --- Component fits ---


def _validate_armor_fit(fit: ArmorFit) -> None:
    """Shape only: `percent` must be a positive integer. Whether it is a multiple
    of 5 is an SRD *rule*, checked by `build_ship`'s armor step, not here
    (FR-015; data-model.md "Builder-enforced constraints" #2)."""
    if fit.percent <= 0:
        raise ValueError(f"armor percent must be positive, got {fit.percent}")
    unknown = set(fit.options) - _ARMOR_OPTIONS
    if unknown:
        raise ValueError(f"unknown armor option(s): {sorted(unknown)}")
    if len(fit.options) != len(set(fit.options)):
        raise ValueError(f"armor options must not repeat, got {fit.options}")


@dataclass(frozen=True)
class ArmorFit:
    """One armor layer: a type, a percent of hull tonnage, and once-only options."""

    type: ArmorType
    percent: int
    options: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_armor_fit(self)


def _validate_software_fit(fit: SoftwareFit) -> None:
    if fit.name not in SOFTWARE:
        raise ValueError(f"unknown software {fit.name!r}; known: {sorted(SOFTWARE)}")
    if fit.level <= 0:
        raise ValueError(f"software level must be positive, got {fit.level}")


@dataclass(frozen=True)
class SoftwareFit:
    """One installed software package at a chosen level (weapons, Jn, DM-1 stacks, ...)."""

    name: str
    level: int

    def __post_init__(self) -> None:
        _validate_software_fit(self)


def _validate_computer_fit(fit: ComputerFit) -> None:
    if fit.model not in COMPUTERS:
        raise ValueError(f"unknown computer model {fit.model}; known: {sorted(COMPUTERS)}")


@dataclass(frozen=True)
class ComputerFit:
    """The ship's computer: model, options, and installed software."""

    model: int
    jump_control: bool = False
    hardened: bool = False
    software: tuple[SoftwareFit, ...] = ()

    def __post_init__(self) -> None:
        _validate_computer_fit(self)


def _validate_fitting_fit(fit: FittingFit) -> None:
    if fit.kind not in FITTINGS:
        raise ValueError(f"unknown fitting {fit.kind!r}; known: {sorted(FITTINGS)}")
    if fit.quantity <= 0:
        raise ValueError(f"fitting quantity must be positive, got {fit.quantity}")
    if fit.kind == "vehicle_hangar":
        if fit.vehicle_tons is None or fit.vehicle_tons <= 0:
            raise ValueError("vehicle_hangar requires a positive vehicle_tons")
    elif fit.vehicle_tons is not None:
        raise ValueError(f"vehicle_tons is only meaningful for vehicle_hangar, not {fit.kind!r}")


@dataclass(frozen=True)
class FittingFit:
    """One additional-component installation (armory, vault, hangar, ...)."""

    kind: str
    quantity: int = 1
    vehicle_tons: int | None = None

    def __post_init__(self) -> None:
        _validate_fitting_fit(self)


def _validate_ammo_fit(fit: AmmoFit) -> None:
    if fit.kind not in _AMMO_KINDS:
        raise ValueError(f"unknown ammo kind {fit.kind!r}; known: {sorted(_AMMO_KINDS)}")
    if fit.count <= 0:
        raise ValueError(f"ammo count must be positive, got {fit.count}")
    if fit.kind == "missile":
        if fit.type not in _MISSILE_TYPES:
            raise ValueError(f"unknown missile type {fit.type!r}; known: {sorted(_MISSILE_TYPES)}")
    elif fit.type is not None:
        raise ValueError(f"type is only meaningful for missile ammo, not {fit.kind!r}")


@dataclass(frozen=True)
class AmmoFit:
    """Sand barrels or missiles loaded for a turret weapon."""

    kind: str
    count: int
    type: str | None = None

    def __post_init__(self) -> None:
        _validate_ammo_fit(self)


def _validate_turret_fit(fit: TurretFit) -> None:
    if fit.mount not in TURRET_MOUNTS:
        raise ValueError(f"unknown turret mount {fit.mount!r}; known: {sorted(TURRET_MOUNTS)}")
    unknown = set(fit.weapons) - set(TURRET_WEAPONS)
    if unknown:
        raise ValueError(f"unknown turret weapon(s): {sorted(unknown)}")
    if not fit.weapons:
        raise ValueError("a turret must carry at least one weapon")
    slots = TURRET_MOUNTS[fit.mount].weapon_slots
    if len(fit.weapons) > slots:
        raise ValueError(
            f"{fit.mount} mount holds at most {slots} weapon(s), got {len(fit.weapons)}"
        )


@dataclass(frozen=True)
class TurretFit:
    """One turret: its mount, the weapons it carries, and any loaded ammunition."""

    mount: str
    weapons: tuple[str, ...]
    ammo: tuple[AmmoFit, ...] = ()

    def __post_init__(self) -> None:
        _validate_turret_fit(self)


def _validate_bay_fit(fit: BayFit) -> None:
    if fit.kind not in _BAY_KINDS:
        raise ValueError(f"unknown bay kind {fit.kind!r}; known: {sorted(_BAY_KINDS)}")


@dataclass(frozen=True)
class BayFit:
    """One 50-ton weapon bay (starship only; FR-020)."""

    kind: str

    def __post_init__(self) -> None:
        _validate_bay_fit(self)


def _validate_screen_fit(fit: ScreenFit) -> None:
    if fit.kind not in _SCREEN_KINDS:
        raise ValueError(f"unknown screen kind {fit.kind!r}; known: {sorted(_SCREEN_KINDS)}")


@dataclass(frozen=True)
class ScreenFit:
    """One defensive screen (meson screen or nuclear damper)."""

    kind: str

    def __post_init__(self) -> None:
        _validate_screen_fit(self)


# --- Input record ---


def _validate_ship_design(design: ShipDesign) -> None:
    if design.hull_tons <= 0:
        raise ValueError(f"hull_tons must be positive, got {design.hull_tons}")

    for code_field in ("jump_code", "maneuver_code", "power_code"):
        code = getattr(design, code_field)
        if code is not None and not _is_drive_code(code):
            raise ValueError(f"{code_field} {code!r} is not an SRD drive code letter")

    if design.jump_distance is not None and design.jump_distance < 0:
        raise ValueError(f"jump_distance must be >= 0, got {design.jump_distance}")

    minimum_weeks = 2 if design.hull_class is HullClass.STARSHIP else 1
    if design.power_weeks < minimum_weeks:
        raise ValueError(
            f"power_weeks must be >= {minimum_weeks} for a {design.hull_class.value}, "
            f"got {design.power_weeks}"
        )

    has_cockpit = design.cockpit is not None
    if has_cockpit == design.bridge:
        raise ValueError("exactly one of bridge or cockpit must be set")
    if has_cockpit and design.cockpit not in COCKPITS:
        raise ValueError(f"unknown cockpit {design.cockpit!r}; known: {sorted(COCKPITS)}")

    if design.electronics is not None and design.electronics not in ELECTRONICS:
        raise ValueError(f"unknown electronics package {design.electronics!r}")

    for name in ("staterooms", "low_berths", "emergency_low_berths"):
        value = getattr(design, name)
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")

    for name in ("passengers_high", "passengers_middle"):
        value = getattr(design, name)
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")


_DRIVE_CODES = frozenset("ABCDEFGHJKLMNPQRSTUVWXYZ")


def _is_drive_code(code: str) -> bool:
    """Whether `code` is a letter in the SRD drive-code sequence.

    Small-craft codes carry an `s` prefix (`sA`-`sZ`, research.md Part K) over the
    same A-Z-skip-I/O sequence as starship codes; both are accepted here since
    `ShipDesign` is shared between the two rulesets and this check is shape-only —
    whether a code is *tabulated for this hull* is the builder's job.
    """
    letters = code[1:] if code.startswith("s") else code
    return letters in _DRIVE_CODES


@dataclass(frozen=True)
class ShipDesign:
    """The declarative build order: produced by `load_design` or the generator,
    consumed by `build_ship`."""

    hull_tons: int
    configuration: Configuration = Configuration.STANDARD
    hull_class: HullClass | None = None
    jump_code: str | None = None
    maneuver_code: str | None = None
    power_code: str | None = None
    jump_distance: int | None = None
    power_weeks: int | None = None
    armor: tuple[ArmorFit, ...] = ()
    bridge: bool = True
    cockpit: str | None = None
    computer: ComputerFit | None = None
    electronics: str | None = None
    staterooms: int = 0
    low_berths: int = 0
    emergency_low_berths: int = 0
    fittings: tuple[FittingFit, ...] = ()
    turrets: tuple[TurretFit, ...] = ()
    bays: tuple[BayFit, ...] = ()
    screens: tuple[ScreenFit, ...] = ()
    passengers_high: int = 0
    passengers_middle: int = 0
    standard_design: bool = False
    name: str | None = None

    def __post_init__(self) -> None:
        if self.hull_class is None:
            object.__setattr__(
                self,
                "hull_class",
                HullClass.STARSHIP if self.hull_tons >= 100 else HullClass.SMALL_CRAFT,
            )
        if self.power_weeks is None:
            minimum = 2 if self.hull_class is HullClass.STARSHIP else 1
            object.__setattr__(self, "power_weeks", minimum)
        _validate_ship_design(self)


# --- Output records ---


def _validate_crew(crew: Crew) -> None:
    for name in (
        "pilot",
        "navigator",
        "engineers",
        "gunners",
        "screen_operators",
        "medic",
        "stewards",
    ):
        value = getattr(crew, name)
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")


@dataclass(frozen=True)
class Crew:
    """The SRD minimum crew breakdown (research.md Part I)."""

    pilot: int
    navigator: int
    engineers: int
    gunners: int
    screen_operators: int
    medic: int
    stewards: int

    def __post_init__(self) -> None:
        _validate_crew(self)

    @property
    def total(self) -> int:
        return (
            self.pilot
            + self.navigator
            + self.engineers
            + self.gunners
            + self.screen_operators
            + self.medic
            + self.stewards
        )


def _validate_line_item(item: LineItem) -> None:
    if item.tons < 0:
        raise ValueError(f"tons must be >= 0, got {item.tons}")
    if item.cost < 0:
        raise ValueError(f"cost must be >= 0, got {item.cost}")


@dataclass(frozen=True)
class LineItem:
    """One costed, tonnage-consuming component on the ship sheet."""

    name: str
    tons: float
    cost: float

    def __post_init__(self) -> None:
        _validate_line_item(self)


def _validate_ship(ship: Ship) -> None:
    if ship.hull_tons <= 0:
        raise ValueError(f"hull_tons must be positive, got {ship.hull_tons}")
    if ship.cargo_tons < 0:
        raise ValueError(f"cargo_tons must be >= 0, got {ship.cargo_tons}")
    for name in (
        "jump_rating",
        "maneuver_rating",
        "power_rating",
        "jump_fuel",
        "power_fuel",
        "tonnage_used",
        "hull_points",
        "structure_points",
        "hardpoints",
        "hardpoints_used",
        "total_cost",
        "build_weeks",
        "assumed_jump_distance",
        "armor_protection",
    ):
        value = getattr(ship, name)
        if value < 0:
            raise ValueError(f"{name} must be >= 0, got {value}")


@dataclass(frozen=True)
class Ship:
    """The computed sheet: produced by `build_ship(design)` and `generate_ship(...)`.

    Carries its originating `design` so a ship round-trips losslessly (SC-008).
    Carries no rendering method: `ships/sheet.py`'s `render_sheet(ship)` is the
    sole reader, so `models.py` never imports `sheet.py`.
    """

    design: ShipDesign
    hull_tons: int
    configuration: Configuration
    jump_rating: int
    maneuver_rating: int
    power_rating: int
    jump_fuel: float
    assumed_jump_distance: int
    power_fuel: float
    tonnage_used: float
    cargo_tons: float
    hull_points: int
    structure_points: int
    armor_protection: int
    hardpoints: int
    hardpoints_used: int
    crew: Crew
    total_cost: float
    build_weeks: int
    line_items: tuple[LineItem, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _validate_ship(self)
