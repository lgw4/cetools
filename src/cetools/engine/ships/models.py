"""Ship-design domain models.

Two record families: `ShipDesign` (declarative input, mirrors the TOML schema) and
`Ship` (computed output, carries its originating `ShipDesign`). Every validator
below checks *shape*, never SRD *rules*: a design that is well-formed but
rules-illegal (e.g. a small craft with a jump drive) constructs cleanly here and is
rejected only by `build_ship`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from cetools.engine.ships.tables import (
    AMMO,
    ARMOR_OPTIONS,
    BAYS,
    COCKPITS,
    COMPUTERS,
    CONFIGURATIONS,
    ELECTRONICS,
    FITTINGS,
    SCREENS,
    SOFTWARE,
    TURRET_MOUNTS,
    TURRET_WEAPONS,
)


def _ammo_kinds() -> set[str]:
    """Every ammunition kind `AMMO` prices. Derived, never restated: a new SRD
    ammunition row must be a data-only edit."""
    return {row.kind for row in AMMO.values()}


def _ammo_types_for(kind: str) -> set[str]:
    """The types `AMMO` prices separately for `kind` (empty when the SRD prices
    the kind as a single item, as it does sand barrels)."""
    return {row.type for row in AMMO.values() if row.kind == kind and row.type is not None}


def _typed_ammo_kinds() -> set[str]:
    """The ammunition kinds that take a `type` at all."""
    return {row.kind for row in AMMO.values() if row.type is not None}


def _vehicle_sized_fittings() -> set[str]:
    """Fittings sized from `FittingFit.vehicle_tons` rather than from a fixed
    table tonnage—identified by the row's per-vehicle-ton columns, not by name."""
    return {kind for kind, row in FITTINGS.items() if row.tons_per_vehicle_ton is not None}


class Configuration(Enum):
    """A ship's hull shape (SRD "Ship Configuration")."""

    DISTRIBUTED = "distributed"
    STANDARD = "standard"
    STREAMLINED = "streamlined"

    @property
    def cost_modifier(self) -> float:
        """The hull-cost multiplier: x0.9 / x1.0 / x1.1."""
        return CONFIGURATIONS[self.value].cost_modifier

    def includes(self, kind: str) -> bool:
        """Whether a hull of this shape carries `kind` already.

        Streamlining "includes fuel scoops" (SRD "Ship Configuration"), which
        the x1.1 hull surcharge has already paid for, so fitting them again buys
        a second set of something the ship has. Nothing else is included by any
        shape today.

        Asked here rather than at the builder and the renderer separately, so
        that what a shape provides is stated once and both readers agree by
        construction. It reports redundancy, never illegality: what a shape may
        not carry is `FittingRow.forbidden_on_distributed`, which is the
        builder's to refuse.
        """
        return self is Configuration.STREAMLINED and FITTINGS[kind].included_on_streamlined


class ArmorType(Enum):
    """A ship-armor material (SRD "Ship Armor")."""

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
    of 5 is an SRD *rule*, checked by `build_ship`'s armor step, not here."""
    if fit.percent <= 0:
        raise ValueError(f"armor percent must be positive, got {fit.percent}")
    unknown = set(fit.options) - set(ARMOR_OPTIONS)
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
    vehicle_sized = _vehicle_sized_fittings()
    if fit.kind in vehicle_sized:
        if fit.vehicle_tons is None or fit.vehicle_tons <= 0:
            raise ValueError(f"{fit.kind} requires a positive vehicle_tons")
    elif fit.vehicle_tons is not None:
        raise ValueError(
            f"vehicle_tons is only meaningful for {', '.join(sorted(vehicle_sized))}, "
            f"not {fit.kind!r}"
        )


@dataclass(frozen=True)
class FittingFit:
    """One additional-component installation (armory, vault, hangar, ...)."""

    kind: str
    quantity: int = 1
    vehicle_tons: int | None = None

    def __post_init__(self) -> None:
        _validate_fitting_fit(self)


def _validate_ammo_fit(fit: AmmoFit) -> None:
    kinds = _ammo_kinds()
    if fit.kind not in kinds:
        raise ValueError(f"unknown ammo kind {fit.kind!r}; known: {sorted(kinds)}")
    if fit.count <= 0:
        raise ValueError(f"ammo count must be positive, got {fit.count}")
    types = _ammo_types_for(fit.kind)
    if types:
        if fit.type not in types:
            raise ValueError(f"unknown {fit.kind} type {fit.type!r}; known: {sorted(types)}")
    elif fit.type is not None:
        typed = sorted(_typed_ammo_kinds())
        raise ValueError(f"type is only meaningful for {', '.join(typed)} ammo, not {fit.kind!r}")


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
    if fit.kind not in BAYS:
        raise ValueError(f"unknown bay kind {fit.kind!r}; known: {sorted(BAYS)}")


@dataclass(frozen=True)
class BayFit:
    """One 50-ton weapon bay (starship only)."""

    kind: str

    def __post_init__(self) -> None:
        _validate_bay_fit(self)


def _validate_screen_fit(fit: ScreenFit) -> None:
    if fit.kind not in SCREENS:
        raise ValueError(f"unknown screen kind {fit.kind!r}; known: {sorted(SCREENS)}")


@dataclass(frozen=True)
class ScreenFit:
    """One defensive screen (meson screen or nuclear damper)."""

    kind: str

    def __post_init__(self) -> None:
        _validate_screen_fit(self)


# --- Input record ---


_TRAILING_PUNCTUATION = ".!?…,;:"
"""Punctuation an authored `purpose` must not end with. The renderer closes the
first sentence itself, so an authored period orphans one ("... is a
fast trader..") and an authored comma dangles one, which is disallowed."""


def _validate_author_prose(value: str, field: str) -> None:
    """Reject a shape the description's one unwrapped paragraph cannot carry.

    `name` and `purpose` are interpolated verbatim into the heading and the
    first sentence, so a line break inside either would split the paragraph in
    two, and stray or doubled whitespace would render as the space
    before a period, or the doubled space, which is disallowed. Validation
    rather than normalization: the value is author prose that appears in the
    output as written, and every other check here reports rather than rewrites.
    """
    if value != value.strip():
        raise ValueError(f"{field} must not have leading or trailing whitespace: {value!r}")
    if "  " in value or any(char.isspace() and char != " " for char in value):
        raise ValueError(f"{field} must be one line with single spaces between words: {value!r}")


def _validate_ship_design(design: ShipDesign) -> None:
    if design.hull_tons <= 0:
        raise ValueError(f"hull_tons must be positive, got {design.hull_tons}")

    for code_field in ("jump_code", "maneuver_code", "power_code"):
        code = getattr(design, code_field)
        if code is not None and not _is_drive_code(code):
            raise ValueError(f"{code_field} {code!r} is not an SRD drive code letter")

    if design.jump_distance is not None and design.jump_distance < 0:
        raise ValueError(f"jump_distance must be >= 0, got {design.jump_distance}")

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

    if design.name is not None:
        if not isinstance(design.name, str):
            raise ValueError(f"name must be a string, got {type(design.name).__name__}")
        # A blank name is *no* name: the description falls back to its
        # placeholder rather than rendering a heading that trails off.
        if design.name.strip():
            _validate_author_prose(design.name, "name")

    if design.purpose is not None:
        if not isinstance(design.purpose, str):
            raise ValueError(f"purpose must be a string, got {type(design.purpose).__name__}")
        if not design.purpose.strip():
            raise ValueError("purpose must not be empty")
        _validate_author_prose(design.purpose, "purpose")
        if design.purpose[-1] in _TRAILING_PUNCTUATION:
            raise ValueError(
                "purpose must not end with punctuation; the renderer supplies the "
                f"sentence's own: {design.purpose!r}"
            )

    # Shape only. An explicit tech level is a statement about the yard
    # that built the ship, never compared against the value `build_ship`
    # derives from the fitted components, and never clamped to it.
    if design.tech_level is not None:
        if isinstance(design.tech_level, bool) or not isinstance(design.tech_level, int):
            raise ValueError(
                f"tech_level must be an integer, got {type(design.tech_level).__name__}"
            )
        if design.tech_level < 0:
            raise ValueError(f"tech_level must be >= 0, got {design.tech_level}")


_DRIVE_CODES = frozenset("ABCDEFGHJKLMNPQRSTUVWXYZ")


def _is_drive_code(code: str) -> bool:
    """Whether `code` is a letter in the SRD drive-code sequence.

    Small-craft codes carry an `s` prefix (`sA`-`sZ`, SRD "Small Craft Drives") over the
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
    purpose: str | None = None
    """The clause completing "the <name> is ..." in the description's first
    sentence. Author-supplied prose, rendered verbatim and carrying no
    trailing period; cetools never generates one."""
    tech_level: int | None = None
    """The designer's override for the heading's tech level.
    `build_ship` uses it as given; when it is `None` the tech level is derived
    from the fitted components."""

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
    """The SRD minimum crew breakdown (SRD "Ship Crew")."""

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
    """One costed, tonnage-consuming component of a built ship.

    `discountable` defaults to `True`; the builder sets it `False` on jump
    fuel, power-plant fuel, and ammunition, which the SRD never discounts.
    This is an explicit flag rather than a name-suffix check, so a
    future SRD entry whose name happens to end in "fuel" or "ammo" is not
    silently exempted from the 10% standard-design discount.
    """

    name: str
    tons: float
    cost: float
    discountable: bool = True

    def __post_init__(self) -> None:
        _validate_line_item(self)


def _validate_ship(ship: Ship) -> None:
    if ship.hull_tons <= 0:
        raise ValueError(f"hull_tons must be positive, got {ship.hull_tons}")
    if ship.cargo_tons < 0:
        raise ValueError(f"cargo_tons must be >= 0, got {ship.cargo_tons}")
    for name in (
        "tech_level",
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
    """The computed ship: produced by `build_ship(design)` and `generate_ship(...)`.

    Carries its originating `design` so a ship round-trips losslessly.
    Carries no rendering method: `ships/description.py`'s
    `render_description(ship)` is the sole reader, so `models.py` never imports
    `description.py`.
    """

    design: ShipDesign
    tech_level: int
    """`design.tech_level` when the designer supplied one, otherwise the highest
    tech level among the fitted components. Always an `int`, never
    `None`: every ship carries the Standard electronics package included in its
    bridge or cockpit, so the derived value floors at `ELECTRONICS["standard"].tl`."""
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
