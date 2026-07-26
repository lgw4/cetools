"""SRD Chapter 8 "Ship Design and Construction" tables, encoded as data.

Small-craft tables (``SMALL_CRAFT_HULLS``, ``COCKPITS``, ``SMALL_CRAFT_ENERGY_CAPS``,
``SMALL_CRAFT_DRIVE_PERFORMANCE``) mirror the starship tables under their own
ruleset (SRD "Small Craft Design"). Bay/screen tables (``BAYS``, ``SCREENS``)
hold the 50-ton weapon bays and defensive screens from the SRD's "Bays" and
"Screens" sections.

Tables keyed by an enum's *value* (a lowercase string, e.g. ``"standard"`` for
``Configuration.STANDARD``) rather than by the enum itself, so this module has no
dependency on ``models.py``: ``models.py`` reads these tables, not the reverse.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HullRow:
    """One row of the Ship Hull by Displacement table."""

    code: str
    cost: float
    build_weeks: int


@dataclass(frozen=True)
class DriveRow:
    """One row of the Drive Costs table: tonnage/cost for J-Drive, M-Drive, P-Plant."""

    jump_tons: int
    jump_cost: float
    maneuver_tons: int
    maneuver_cost: float
    power_tons: int
    power_cost: float


@dataclass(frozen=True)
class ArmorRow:
    """One row of the Ship Armor by Type table.

    ``name`` is the SRD's prose spelling, printed by the description's
    configuration sentence (FR-030); ``tl`` is the table's own TL column, read
    by the tech-level derivation (FR-028a).
    """

    name: str
    protection_per_5_percent: int
    cost_percent_per_5_percent: int
    tl: int


@dataclass(frozen=True)
class ArmorOptionRow:
    """One row of the Ship Armor Options table: MCr surcharge per armored ton.

    ``name`` is the SRD noun phrase the configuration sentence prints, article
    included ("a stealth coating"); ``tl`` comes from the SRD section's prose,
    which is the only place it appears.
    """

    name: str
    cost_per_ton: float
    tl: int


@dataclass(frozen=True)
class ComputerRow:
    """One row of the Ship Computer Models table.

    The description names a computer by its model *number* ("a computer Model
    3/fib"), so this row needs no display name; ``tl`` feeds the ship's derived
    tech level (FR-028a).
    """

    tl: int
    rating: int
    cost: float


@dataclass(frozen=True)
class SoftwareRow:
    """One row of the Ship Software table.

    Rating and MCr cost both scale linearly with the software's chosen ``level``
    (weapons controlled, Jn governed, repair attempts, DM-1 stacks, …), so a
    `SoftwareFit(name, level)` costs `rating_per_level * level` rating and
    `cost_per_level * level` MCr.
    """

    rating_per_level: float
    cost_per_level: float


@dataclass(frozen=True)
class ElectronicsRow:
    """One row of the Ship Electronics table.

    ``dm`` is the package's sensor dice modifier, printed with an explicit sign
    by the sensors sentence -- including ``DM+0`` for Basic Military (FR-009,
    FR-030a).
    """

    name: str
    tons: float
    cost: float
    tl: int
    dm: int


@dataclass(frozen=True)
class QuartersRow:
    """One row covering staterooms / low berths / emergency low berths."""

    tons: float
    cost: float


@dataclass(frozen=True)
class FittingRow:
    """One row of the Additional Ship Components tables.

    ``tons``/``cost`` are ``None`` for a *vehicle-sized* fitting—one whose size
    comes from the design rather than the table (the vehicle hangar, sized from
    `FittingFit.vehicle_tons`). Such a row instead sets
    ``tons_per_vehicle_ton``/``cost_per_vehicle_ton``, and those two columns are
    what mark it vehicle-sized: `models.py` requires a ``vehicle_tons`` for any
    row that sets them, and the builder's fitting step multiplies through them,
    so a second SRD vehicle-sized fitting stays a data-only edit (SC-006).

    ``name`` carries its indefinite article ("an armory", "fuel scoops") and
    ``plural`` does not, because the special-features sentence mixes countable
    and mass nouns. ``counted_in_tons`` marks a fitting the
    SRD measures rather than counts ("two tons of luxuries"), and
    ``unrefined_fuel_per_ton`` its daily throughput, set only on the fuel
    processor: two data columns driving two generic renderer branches rather
    than a per-kind branch (FR-017, FR-031). The SRD tabulates no TL for any of
    these components, so there is no ``tl`` column.
    """

    name: str
    plural: str
    tons: float | None
    cost: float | None
    forbidden_on_distributed: bool = False
    hull_structure_bonus: int = 0
    tons_per_vehicle_ton: float | None = None
    cost_per_vehicle_ton: float | None = None
    counted_in_tons: bool = False
    unrefined_fuel_per_ton: float | None = None


@dataclass(frozen=True)
class MountRow:
    """One row of the Turret Displacement and Cost table.

    ``tl`` is ``None`` for the fixed mounting alone, whose TL cell the SRD
    prints as "-": it contributes nothing to a ship's derived tech level, the
    same treatment as an untabulated category, expressed per row (FR-028a).
    """

    name: str
    plural: str
    tons: float
    cost: float
    weapon_slots: int
    tl: int | None


@dataclass(frozen=True)
class WeaponRow:
    """One row of the Turret Weapons table.

    ``name``/``plural`` are the *armament clause's* spelling, not the catalog's:
    the SRD examples write "armed with missiles", never "armed with missile
    racks". The same singular spells the ammunition sentence's
    "the missile turrets".
    """

    name: str
    plural: str
    cost: float
    tl: int
    energy: bool = False


@dataclass(frozen=True)
class AmmoRow:
    """One row of the Ammunition table: rounds per ton and cost per round.

    ``kind`` and ``type`` mirror `AmmoFit`'s two selectors, so `models.py`
    derives the legal ammo kinds—and the types legal for each kind—from this
    table rather than from a hardcoded duplicate of its keys (SC-006).
    ``type`` is ``None`` for a kind the SRD prices as a single item.

    ``weapon`` is the ``TURRET_WEAPONS`` key this ammunition feeds, so the
    ammunition sentence can name its weapon from data rather than from the
    renderer knowing that missiles go in missile racks (FR-031).
    """

    name: str
    plural: str
    kind: str
    rounds_per_ton: int
    cost_per_round: float
    tl: int
    weapon: str
    type: str | None = None


@dataclass(frozen=True)
class BayRow:
    """One row of the Weapon Bays table: fixed 50 t plus SRD cost.

    Each bay also costs +1 t of fire control (a builder-applied rule, not part
    of this row—see ``builder.BAY_FIRE_CONTROL_TONS``) and consumes one
    hardpoint, same as a turret.
    """

    name: str
    plural: str
    tons: float
    cost: float
    tl: int


@dataclass(frozen=True)
class ScreenRow:
    """One row of the Defensive Screens table: fixed 50 t plus SRD cost."""

    name: str
    plural: str
    tons: float
    cost: float
    tl: int


@dataclass(frozen=True)
class ConfigurationRow:
    """One row of the Ship Configuration table: display name and cost modifier.

    ``name`` is lower case because the starship examples print "The hull is
    standard"; only the small-craft examples capitalise.
    """

    name: str
    cost_modifier: float


@dataclass(frozen=True)
class CrewPositionRow:
    """One position of the Ship Crew Requirements table.

    ``field`` names the `models.Crew` count attribute this position reads, so
    the crew sentence's breakdown is driven by the table rather than by a
    hardcoded list in the renderer.
    """

    field: str
    name: str
    plural: str


@dataclass(frozen=True)
class CockpitRow:
    """One row of the Small Craft Cockpit table: tonnage only.

    Cost is not fixed per cockpit: it scales with the ship, MCr 0.1 per 20 tons
    of hull (research Part K), the same way bridge cost scales with hull tons.

    Seating is deliberately **not** a column. The SRD names its cockpits "1-man"
    and "2-man", but its minimum-crew rules (research Part I) are a separate,
    ship-wide calculation the source page never reconciles with cockpit
    capacity, so no builder step caps crew against seats—doing so would invent
    a rule the SRD does not state (FR-002). A `1_man`-cockpit fighter reporting
    a multi-person minimum crew is expected, not a defect.
    """

    tons: float


HULLS: dict[int, HullRow] = {
    100: HullRow(code="1", cost=2, build_weeks=36),
    200: HullRow(code="2", cost=8, build_weeks=44),
    300: HullRow(code="3", cost=12, build_weeks=52),
    400: HullRow(code="4", cost=16, build_weeks=60),
    500: HullRow(code="5", cost=32, build_weeks=68),
    600: HullRow(code="6", cost=48, build_weeks=76),
    700: HullRow(code="7", cost=64, build_weeks=84),
    800: HullRow(code="8", cost=80, build_weeks=92),
    900: HullRow(code="9", cost=90, build_weeks=100),
    1000: HullRow(code="A", cost=100, build_weeks=108),
    1200: HullRow(code="C", cost=120, build_weeks=124),
    1400: HullRow(code="E", cost=140, build_weeks=140),
    1600: HullRow(code="G", cost=160, build_weeks=156),
    1800: HullRow(code="J", cost=180, build_weeks=172),
    2000: HullRow(code="L", cost=200, build_weeks=188),
    3000: HullRow(code="M", cost=300, build_weeks=268),
    4000: HullRow(code="N", cost=400, build_weeks=348),
    5000: HullRow(code="P", cost=500, build_weeks=428),
}
"""Standard-hull tons -> (code, cost MCr, build weeks). Sparse above 1,000 t."""

CONFIGURATIONS: dict[str, ConfigurationRow] = {
    "distributed": ConfigurationRow(name="distributed", cost_modifier=0.9),
    "standard": ConfigurationRow(name="standard", cost_modifier=1.0),
    "streamlined": ConfigurationRow(name="streamlined", cost_modifier=1.1),
}
"""Ship Configuration display name and hull-cost modifier, keyed by
``Configuration.value``. `Configuration.cost_modifier` reads
``cost_modifier`` here, so the x0.9/x1.0/x1.1 arithmetic is unchanged."""

CREW_POSITIONS: tuple[CrewPositionRow, ...] = (
    CrewPositionRow(field="pilot", name="pilot", plural="pilots"),
    CrewPositionRow(field="navigator", name="navigator", plural="navigators"),
    CrewPositionRow(field="engineers", name="engineer", plural="engineers"),
    CrewPositionRow(field="gunners", name="gunner", plural="gunners"),
    CrewPositionRow(field="screen_operators", name="screen operator", plural="screen operators"),
    CrewPositionRow(field="medic", name="medic", plural="medics"),
    CrewPositionRow(field="stewards", name="steward", plural="stewards"),
)
"""The crew positions cetools derives, in the order FR-018's breakdown prints
them. The single source of both the spelling and the order; a position whose
count is zero is omitted from the sentence.

The SRD's fuller list (commanding officer, marines, scientists, flight crew) is
referee-discretion staffing that cetools leaves out of scope, and this module
invents none of it."""

DRIVE_COSTS: dict[str, DriveRow] = {
    "A": DriveRow(
        jump_tons=10, jump_cost=10, maneuver_tons=2, maneuver_cost=4, power_tons=4, power_cost=8
    ),
    "B": DriveRow(
        jump_tons=15, jump_cost=20, maneuver_tons=3, maneuver_cost=8, power_tons=7, power_cost=16
    ),
    "C": DriveRow(
        jump_tons=20, jump_cost=30, maneuver_tons=5, maneuver_cost=12, power_tons=10, power_cost=24
    ),
    "D": DriveRow(
        jump_tons=25, jump_cost=40, maneuver_tons=7, maneuver_cost=16, power_tons=13, power_cost=32
    ),
    "E": DriveRow(
        jump_tons=30, jump_cost=50, maneuver_tons=9, maneuver_cost=20, power_tons=16, power_cost=40
    ),
    "F": DriveRow(
        jump_tons=35,
        jump_cost=60,
        maneuver_tons=11,
        maneuver_cost=24,
        power_tons=19,
        power_cost=48,
    ),
    "G": DriveRow(
        jump_tons=40,
        jump_cost=70,
        maneuver_tons=13,
        maneuver_cost=28,
        power_tons=22,
        power_cost=56,
    ),
    "H": DriveRow(
        jump_tons=45,
        jump_cost=80,
        maneuver_tons=15,
        maneuver_cost=32,
        power_tons=25,
        power_cost=64,
    ),
    "J": DriveRow(
        jump_tons=50,
        jump_cost=90,
        maneuver_tons=17,
        maneuver_cost=36,
        power_tons=28,
        power_cost=72,
    ),
    "K": DriveRow(
        jump_tons=55,
        jump_cost=100,
        maneuver_tons=19,
        maneuver_cost=40,
        power_tons=31,
        power_cost=80,
    ),
    "L": DriveRow(
        jump_tons=60,
        jump_cost=110,
        maneuver_tons=21,
        maneuver_cost=44,
        power_tons=34,
        power_cost=88,
    ),
    "M": DriveRow(
        jump_tons=65,
        jump_cost=120,
        maneuver_tons=23,
        maneuver_cost=48,
        power_tons=37,
        power_cost=96,
    ),
    "N": DriveRow(
        jump_tons=70,
        jump_cost=130,
        maneuver_tons=25,
        maneuver_cost=52,
        power_tons=40,
        power_cost=104,
    ),
    "P": DriveRow(
        jump_tons=75,
        jump_cost=140,
        maneuver_tons=27,
        maneuver_cost=56,
        power_tons=43,
        power_cost=112,
    ),
    "Q": DriveRow(
        jump_tons=80,
        jump_cost=150,
        maneuver_tons=29,
        maneuver_cost=60,
        power_tons=46,
        power_cost=120,
    ),
    "R": DriveRow(
        jump_tons=85,
        jump_cost=160,
        maneuver_tons=31,
        maneuver_cost=64,
        power_tons=49,
        power_cost=128,
    ),
    "S": DriveRow(
        jump_tons=90,
        jump_cost=170,
        maneuver_tons=33,
        maneuver_cost=68,
        power_tons=52,
        power_cost=136,
    ),
    "T": DriveRow(
        jump_tons=95,
        jump_cost=180,
        maneuver_tons=35,
        maneuver_cost=72,
        power_tons=55,
        power_cost=144,
    ),
    "U": DriveRow(
        jump_tons=100,
        jump_cost=190,
        maneuver_tons=37,
        maneuver_cost=76,
        power_tons=58,
        power_cost=152,
    ),
    "V": DriveRow(
        jump_tons=105,
        jump_cost=200,
        maneuver_tons=39,
        maneuver_cost=80,
        power_tons=61,
        power_cost=160,
    ),
    "W": DriveRow(
        jump_tons=110,
        jump_cost=210,
        maneuver_tons=41,
        maneuver_cost=84,
        power_tons=64,
        power_cost=168,
    ),
    "X": DriveRow(
        jump_tons=115,
        jump_cost=220,
        maneuver_tons=43,
        maneuver_cost=88,
        power_tons=67,
        power_cost=176,
    ),
    "Y": DriveRow(
        jump_tons=120,
        jump_cost=230,
        maneuver_tons=45,
        maneuver_cost=92,
        power_tons=70,
        power_cost=182,
    ),
    "Z": DriveRow(
        jump_tons=125,
        jump_cost=240,
        maneuver_tons=47,
        maneuver_cost=96,
        power_tons=73,
        power_cost=192,
    ),
}
"""Drive code (A-Z, skipping I and O) -> J-Drive/M-Drive/P-Plant tonnage and MCr cost."""

DRIVE_PERFORMANCE: dict[str, dict[int, int]] = {
    "A": {100: 2, 200: 1},
    "B": {100: 4, 200: 2, 300: 1, 400: 1},
    "C": {100: 6, 200: 3, 300: 2, 400: 1, 500: 1, 600: 1},
    "D": {200: 4, 300: 2, 400: 2, 500: 1, 600: 1, 700: 1, 800: 1},
    "E": {200: 5, 300: 3, 400: 2, 500: 2, 600: 1, 700: 1, 800: 1, 900: 1, 1000: 1},
    "F": {200: 6, 300: 4, 400: 3, 500: 2, 600: 2, 700: 1, 800: 1, 900: 1, 1000: 1, 1200: 1},
    "G": {300: 4, 400: 3, 500: 2, 600: 2, 700: 2, 800: 2, 900: 1, 1000: 1, 1200: 1, 1400: 1},
    "H": {
        300: 5,
        400: 4,
        500: 3,
        600: 2,
        700: 2,
        800: 2,
        900: 2,
        1000: 2,
        1200: 1,
        1400: 1,
        1600: 1,
    },
    "J": {
        300: 6,
        400: 4,
        500: 3,
        600: 3,
        700: 2,
        800: 2,
        900: 2,
        1000: 2,
        1200: 2,
        1400: 1,
        1600: 1,
        1800: 1,
    },
    "K": {
        400: 5,
        500: 4,
        600: 3,
        700: 3,
        800: 3,
        900: 2,
        1000: 2,
        1200: 2,
        1400: 2,
        1600: 1,
        1800: 1,
        2000: 1,
    },
    "L": {
        400: 5,
        500: 4,
        600: 3,
        700: 3,
        800: 3,
        900: 3,
        1000: 3,
        1200: 2,
        1400: 2,
        1600: 2,
        1800: 1,
        2000: 1,
    },
    "M": {
        400: 6,
        500: 4,
        600: 4,
        700: 3,
        800: 3,
        900: 3,
        1000: 3,
        1200: 3,
        1400: 2,
        1600: 2,
        1800: 2,
        2000: 1,
    },
    "N": {
        400: 6,
        500: 5,
        600: 4,
        700: 4,
        800: 4,
        900: 3,
        1000: 3,
        1200: 3,
        1400: 3,
        1600: 2,
        1800: 2,
        2000: 2,
    },
    "P": {
        500: 5,
        600: 4,
        700: 4,
        800: 4,
        900: 4,
        1000: 4,
        1200: 3,
        1400: 3,
        1600: 3,
        1800: 2,
        2000: 2,
    },
    "Q": {
        500: 6,
        600: 5,
        700: 4,
        800: 4,
        900: 4,
        1000: 4,
        1200: 4,
        1400: 3,
        1600: 3,
        1800: 3,
        2000: 2,
        3000: 1,
    },
    "R": {
        500: 6,
        600: 5,
        700: 5,
        800: 5,
        900: 4,
        1000: 4,
        1200: 4,
        1400: 4,
        1600: 3,
        1800: 3,
        2000: 3,
        3000: 1,
    },
    "S": {
        500: 6,
        600: 5,
        700: 5,
        800: 5,
        900: 5,
        1000: 5,
        1200: 4,
        1400: 4,
        1600: 4,
        1800: 3,
        2000: 3,
        3000: 1,
    },
    "T": {
        600: 6,
        700: 5,
        800: 5,
        900: 5,
        1000: 5,
        1200: 5,
        1400: 4,
        1600: 4,
        1800: 4,
        2000: 3,
        3000: 2,
    },
    "U": {
        600: 6,
        700: 6,
        800: 5,
        900: 5,
        1000: 5,
        1200: 5,
        1400: 4,
        1600: 4,
        1800: 4,
        2000: 4,
        3000: 2,
    },
    "V": {
        600: 6,
        700: 6,
        800: 6,
        900: 5,
        1000: 5,
        1200: 5,
        1400: 5,
        1600: 4,
        1800: 4,
        2000: 4,
        3000: 2,
        4000: 1,
    },
    "W": {
        700: 6,
        800: 6,
        900: 6,
        1000: 5,
        1200: 5,
        1400: 5,
        1600: 4,
        1800: 4,
        2000: 4,
        3000: 3,
        4000: 1,
        5000: 1,
    },
    "X": {
        700: 6,
        800: 6,
        900: 6,
        1000: 6,
        1200: 5,
        1400: 5,
        1600: 5,
        1800: 4,
        2000: 4,
        3000: 3,
        4000: 1,
        5000: 1,
    },
    "Y": {
        700: 6,
        800: 6,
        900: 6,
        1000: 6,
        1200: 5,
        1400: 5,
        1600: 5,
        1800: 4,
        2000: 4,
        3000: 3,
        4000: 2,
        5000: 1,
    },
    "Z": {
        700: 6,
        800: 6,
        900: 6,
        1000: 6,
        1200: 6,
        1400: 5,
        1600: 5,
        1800: 5,
        2000: 4,
        3000: 4,
        4000: 2,
        5000: 2,
    },
}
"""Drive code -> {hull tons -> rating}. Governs jump rating, maneuver-G and power
rating alike; a hull tons missing from a code's inner dict means that code cannot
be installed on that hull."""

ARMOR: dict[str, ArmorRow] = {
    "titanium_steel": ArmorRow(
        name="Titanium Steel", protection_per_5_percent=2, cost_percent_per_5_percent=5, tl=7
    ),
    "crystaliron": ArmorRow(
        name="Crystaliron", protection_per_5_percent=4, cost_percent_per_5_percent=20, tl=10
    ),
    "bonded_superdense": ArmorRow(
        name="Bonded Superdense", protection_per_5_percent=6, cost_percent_per_5_percent=50, tl=14
    ),
}
"""Armor type -> display name, protection, cost per 5% of hull tonnage and TL,
keyed by ``ArmorType.value``."""

ARMOR_OPTIONS: dict[str, ArmorOptionRow] = {
    "reflec": ArmorOptionRow(name="a reflec coating", cost_per_ton=0.1, tl=10),
    "self_sealing": ArmorOptionRow(name="a self-sealing hull", cost_per_ton=0.01, tl=9),
    "stealth": ArmorOptionRow(name="a stealth coating", cost_per_ton=0.1, tl=11),
}
"""Armor option -> SRD noun phrase, MCr surcharge per armored ton, and TL
(research Parts D and F). The single source for which options exist (`ArmorFit`
validates against these keys), what they cost (the builder's armor step reads
``cost_per_ton``) and how they are spelled, so adding an SRD option stays a
data-only edit (SC-006)."""

BRIDGE_SIZES: tuple[tuple[int | None, int], ...] = (
    (200, 10),
    (1000, 20),
    (2000, 40),
    (None, 60),
)
"""Ordered ``(max_tons, bridge_tons)`` steps; ``None`` max_tons means "no upper bound"."""

COMPUTERS: dict[int, ComputerRow] = {
    1: ComputerRow(tl=7, rating=5, cost=0.03),
    2: ComputerRow(tl=9, rating=10, cost=0.16),
    3: ComputerRow(tl=11, rating=15, cost=2),
    4: ComputerRow(tl=12, rating=20, cost=5),
    5: ComputerRow(tl=13, rating=25, cost=10),
    6: ComputerRow(tl=14, rating=30, cost=20),
    7: ComputerRow(tl=15, rating=35, cost=30),
}
"""Computer model number -> (TL, rating, cost MCr)."""

SOFTWARE: dict[str, SoftwareRow] = {
    "fire_control": SoftwareRow(rating_per_level=5, cost_per_level=2),
    "jump_control": SoftwareRow(rating_per_level=5, cost_per_level=0.1),
    "jump_course_tape": SoftwareRow(rating_per_level=1, cost_per_level=0.001),
    "evade": SoftwareRow(rating_per_level=5, cost_per_level=1),
    "auto_repair": SoftwareRow(rating_per_level=10, cost_per_level=5),
}
"""Software name -> rating cost and MCr cost per level (weapon, Jn, DM-1 stack, …)."""

ELECTRONICS: dict[str, ElectronicsRow] = {
    "standard": ElectronicsRow(name="Standard", tons=0, cost=0, tl=8, dm=-4),
    "basic_civilian": ElectronicsRow(name="Basic Civilian", tons=1, cost=0.05, tl=9, dm=-2),
    "basic_military": ElectronicsRow(name="Basic Military", tons=2, cost=1, tl=10, dm=0),
    "advanced": ElectronicsRow(name="Advanced", tons=3, cost=2, tl=11, dm=1),
    "very_advanced": ElectronicsRow(name="Very Advanced", tons=5, cost=4, tl=12, dm=2),
}
"""Electronics package -> (display name, tons, cost MCr, TL, sensor DM).
``standard`` is included in the bridge or cockpit, so every ship carries it and
the derived tech level has a floor of 8 (research Part D)."""

QUARTERS: dict[str, QuartersRow] = {
    "stateroom": QuartersRow(tons=4, cost=0.5),
    "low_berth": QuartersRow(tons=0.5, cost=0.05),
    "emergency_low_berth": QuartersRow(tons=1, cost=0.1),
}
"""Crew-accommodation kind -> (tons, cost MCr) per berth."""

FITTINGS: dict[str, FittingRow] = {
    "armory": FittingRow(name="an armory", plural="armories", tons=2, cost=0.5),
    "detention_cell": FittingRow(
        name="a detention cell", plural="detention cells", tons=2, cost=0.25
    ),
    "fuel_scoops": FittingRow(
        name="fuel scoops", plural="fuel scoops", tons=0, cost=1, forbidden_on_distributed=True
    ),
    "fuel_processor": FittingRow(
        name="a fuel processor",
        plural="fuel processors",
        tons=1,
        cost=0.05,
        counted_in_tons=True,
        unrefined_fuel_per_ton=20.0,
    ),
    "laboratory": FittingRow(name="a laboratory", plural="laboratories", tons=4, cost=1),
    "library": FittingRow(name="a library", plural="libraries", tons=4, cost=4),
    "luxuries": FittingRow(
        name="luxuries", plural="luxuries", tons=1, cost=0.1, counted_in_tons=True
    ),
    "vault": FittingRow(name="a vault", plural="vaults", tons=12, cost=6, hull_structure_bonus=4),
    "vehicle_hangar": FittingRow(
        name="a small craft hangar",
        plural="small craft hangars",
        tons=None,
        cost=None,
        tons_per_vehicle_ton=1.3,
        cost_per_vehicle_ton=0.2,
    ),
}
"""Fitting name -> (tons, cost MCr) per unit of ``FittingFit.quantity``.

``vehicle_hangar``'s tons/cost are ``None`` because it is vehicle-sized: its
figures come from ``FittingFit.vehicle_tons`` scaled by the row's
``tons_per_vehicle_ton``/``cost_per_vehicle_ton`` (hangar tons = vehicle tons
x1.3, cost = MCr0.2/ton, research Part G)."""

TURRET_MOUNTS: dict[str, MountRow] = {
    "single": MountRow(
        name="single turret", plural="single turrets", tons=1, cost=0.2, weapon_slots=1, tl=7
    ),
    "double": MountRow(
        name="double turret", plural="double turrets", tons=1, cost=0.5, weapon_slots=2, tl=8
    ),
    "triple": MountRow(
        name="triple turret", plural="triple turrets", tons=1, cost=1, weapon_slots=3, tl=9
    ),
    "pop_up": MountRow(
        name="pop-up turret", plural="pop-up turrets", tons=2, cost=1, weapon_slots=1, tl=10
    ),
    "fixed": MountRow(
        name="fixed mounting", plural="fixed mountings", tons=0, cost=0.1, weapon_slots=1, tl=None
    ),
}
"""Mount type -> (tons, cost MCr, weapon slots).

The SRD presents pop-up and fixed as *qualities* layered on a single/double/triple
mount (+2 t and +MCr1 for pop-up; half cost for fixed), but ``TurretFit.mount`` is
one flat choice among five (design-schema.md), so each is modelled here as its own
single-weapon-slot mount: pop-up at its literal SRD tons/cost, fixed at 0 t (the
SRD's fixed mounting occupies no separate tonnage) and half of a single turret's
cost."""

TURRET_WEAPONS: dict[str, WeaponRow] = {
    "missile_rack": WeaponRow(name="missile", plural="missiles", cost=0.75, tl=6),
    "pulse_laser": WeaponRow(
        name="pulse laser", plural="pulse lasers", cost=0.5, tl=7, energy=True
    ),
    "sandcaster": WeaponRow(name="sandcaster", plural="sandcasters", cost=0.25, tl=7),
    "particle_beam": WeaponRow(
        name="particle beam", plural="particle beams", cost=4, tl=8, energy=True
    ),
}
"""Turret weapon -> (armament-clause spelling, cost MCr, TL, whether it counts
against a small craft's energy-weapon cap). The SRD page's Turret Weapons table
lists exactly these four; a "beam laser" is named in the surrounding prose but
never priced, so it is omitted rather than guessed."""

AMMO: dict[str, AmmoRow] = {
    "sand_barrels": AmmoRow(
        name="canister",
        plural="canisters",
        kind="sand_barrels",
        rounds_per_ton=20,
        cost_per_round=10_000 / 20 / 1_000_000,
        tl=5,
        weapon="sandcaster",
    ),
    "missile_standard": AmmoRow(
        name="standard missile",
        plural="standard missiles",
        kind="missile",
        type="standard",
        rounds_per_ton=12,
        cost_per_round=1_250 / 1_000_000,
        tl=6,
        weapon="missile_rack",
    ),
    "missile_smart": AmmoRow(
        name="smart missile",
        plural="smart missiles",
        kind="missile",
        type="smart",
        rounds_per_ton=12,
        cost_per_round=2_500 / 1_000_000,
        tl=8,
        weapon="missile_rack",
    ),
    "missile_nuclear": AmmoRow(
        name="nuclear missile",
        plural="nuclear missiles",
        kind="missile",
        type="nuclear",
        rounds_per_ton=12,
        cost_per_round=3_750 / 1_000_000,
        tl=6,
        weapon="missile_rack",
    ),
}
"""Ammunition entry -> (display name, kind, type, rounds per ton, MCr cost per
round, TL, the turret weapon it feeds). Sand barrels: 20/ton, Cr10,000 per ton
(Cr500/barrel), called "canisters" in Chapter 9 (research Part E). Missiles:
12/ton regardless of type, priced per missile (standard Cr1,250, smart Cr2,500,
nuclear Cr3,750). The dict key is descriptive only—`models.py` and `builder.py`
both match an `AmmoFit` on the row's ``kind``/``type`` columns, never on the
key's spelling."""

BAYS: dict[str, BayRow] = {
    "missile_bank": BayRow(name="missile bay", plural="missile bays", tons=50, cost=12, tl=6),
    "particle": BayRow(
        name="particle beam bay", plural="particle beam bays", tons=50, cost=20, tl=8
    ),
    "meson": BayRow(name="meson gun bay", plural="meson gun bays", tons=50, cost=50, tl=11),
    "fusion": BayRow(name="fusion gun bay", plural="fusion gun bays", tons=50, cost=8, tl=12),
}
"""Weapon-bay kind -> (display name, 50 t, cost MCr, TL), research Parts D and
H. Forbidden on small craft."""

SCREENS: dict[str, ScreenRow] = {
    "meson_screen": ScreenRow(
        name="meson screen", plural="meson screens", tons=50, cost=60, tl=12
    ),
    "nuclear_damper": ScreenRow(
        name="nuclear damper", plural="nuclear dampers", tons=50, cost=50, tl=12
    ),
}
"""Defensive-screen kind -> (display name, 50 t, cost MCr, TL), research Parts D
and H."""

SMALL_CRAFT_HULLS: dict[int, HullRow] = {
    10: HullRow(code="s1", cost=1.1, build_weeks=28),
    15: HullRow(code="s2", cost=1.15, build_weeks=29),
    20: HullRow(code="s3", cost=1.2, build_weeks=29),
    25: HullRow(code="s4", cost=1.25, build_weeks=30),
    30: HullRow(code="s5", cost=1.3, build_weeks=30),
    35: HullRow(code="s6", cost=1.35, build_weeks=30),
    40: HullRow(code="s7", cost=1.4, build_weeks=31),
    45: HullRow(code="s8", cost=1.45, build_weeks=31),
    50: HullRow(code="s9", cost=1.5, build_weeks=32),
    55: HullRow(code="sA", cost=1.55, build_weeks=32),
    60: HullRow(code="sB", cost=1.6, build_weeks=32),
    65: HullRow(code="sC", cost=1.65, build_weeks=33),
    70: HullRow(code="sD", cost=1.7, build_weeks=33),
    75: HullRow(code="sE", cost=1.75, build_weeks=34),
    80: HullRow(code="sF", cost=1.8, build_weeks=34),
    85: HullRow(code="sG", cost=1.85, build_weeks=34),
    90: HullRow(code="sH", cost=1.9, build_weeks=35),
    95: HullRow(code="sJ", cost=1.95, build_weeks=35),
}
"""Small-craft tons (10-95, 5-ton steps) -> (code, cost MCr, build weeks)."""

COCKPITS: dict[str, CockpitRow] = {
    "1_man": CockpitRow(tons=1.5),
    "2_man": CockpitRow(tons=3.0),
}
"""Small-craft cockpit name -> tonnage (research Part K). The SRD's two cockpits
only; the larger "control cabin" variants are out of this feature's scope."""

SMALL_CRAFT_ENERGY_CAPS: dict[str, int] = {
    **{code: 0 for code in "ABCDEF"},
    **{code: 1 for code in "GHJK"},
    **{code: 2 for code in "LMNPQR"},
    **{code: 3 for code in "STUVWXYZ"},
}
"""Drive-code letter (unprefixed) -> max lasers/particle weapons a small craft's
power plant allows (research Part K: sA-sF 0, sG-sK 1, sL-sR 2, sS-sZ 3)."""

SMALL_CRAFT_DRIVE_PERFORMANCE: dict[str, dict[int, int]] = {
    "A": {10: 2, 15: 1, 20: 1},
    "B": {10: 4, 15: 2, 20: 2, 25: 1, 30: 1, 35: 1, 40: 1},
    "C": {10: 6, 15: 4, 20: 3, 25: 2, 30: 2, 35: 1, 40: 1, 45: 1, 50: 1, 55: 1, 60: 1},
    "D": {
        15: 5,
        20: 4,
        25: 3,
        30: 2,
        35: 2,
        40: 2,
        45: 1,
        50: 1,
        55: 1,
        60: 1,
        65: 1,
        70: 1,
        75: 1,
        80: 1,
    },
    "E": {
        15: 6,
        20: 5,
        25: 4,
        30: 3,
        35: 2,
        40: 2,
        45: 2,
        50: 2,
        55: 1,
        60: 1,
        65: 1,
        70: 1,
        75: 1,
        80: 1,
        85: 1,
        90: 1,
        95: 1,
    },
    "F": {
        20: 6,
        25: 4,
        30: 4,
        35: 3,
        40: 3,
        45: 2,
        50: 2,
        55: 2,
        60: 2,
        65: 1,
        70: 1,
        75: 1,
        80: 1,
        85: 1,
        90: 1,
        95: 1,
    },
    "G": {
        25: 5,
        30: 4,
        35: 4,
        40: 3,
        45: 3,
        50: 2,
        55: 2,
        60: 2,
        65: 2,
        70: 2,
        75: 1,
        80: 1,
        85: 1,
        90: 1,
        95: 1,
    },
    "H": {
        25: 6,
        30: 5,
        35: 4,
        40: 4,
        45: 3,
        50: 3,
        55: 2,
        60: 2,
        65: 2,
        70: 2,
        75: 2,
        80: 2,
        85: 1,
        90: 1,
        95: 1,
    },
    "J": {
        30: 6,
        35: 5,
        40: 4,
        45: 4,
        50: 3,
        55: 3,
        60: 3,
        65: 2,
        70: 2,
        75: 2,
        80: 2,
        85: 2,
        90: 2,
        95: 1,
    },
    "K": {
        30: 6,
        35: 5,
        40: 5,
        45: 4,
        50: 4,
        55: 3,
        60: 3,
        65: 3,
        70: 2,
        75: 2,
        80: 2,
        85: 2,
        90: 2,
        95: 2,
    },
    "L": {
        35: 6,
        40: 6,
        45: 5,
        50: 4,
        55: 4,
        60: 4,
        65: 3,
        70: 3,
        75: 3,
        80: 3,
        85: 2,
        90: 2,
        95: 2,
    },
    "M": {45: 6, 50: 5, 55: 5, 60: 4, 65: 4, 70: 4, 75: 3, 80: 3, 85: 3, 90: 3, 95: 2},
    "N": {50: 6, 55: 5, 60: 5, 65: 4, 70: 4, 75: 4, 80: 4, 85: 3, 90: 3, 95: 3},
    "P": {55: 6, 60: 6, 65: 5, 70: 5, 75: 4, 80: 4, 85: 4, 90: 4, 95: 3},
    "Q": {60: 6, 65: 6, 70: 5, 75: 5, 80: 5, 85: 4, 90: 4, 95: 4},
    "R": {65: 6, 70: 6, 75: 5, 80: 5, 85: 5, 90: 4, 95: 4},
    "S": {70: 6, 75: 6, 80: 6, 85: 5, 90: 5, 95: 5},
    "T": {75: 6, 80: 6, 85: 6, 90: 5, 95: 5},
    "U": {85: 6, 90: 6, 95: 5},
    "V": {90: 6, 95: 6},
    "W": {95: 6},
}
"""Small-craft "Drive Performance by Hull Volume" table, keyed by the drive-code
letter without its "s" prefix (research Part K). A separate matrix from
``DRIVE_PERFORMANCE``: small-craft hull tons (10-95) never appear in the starship
matrix, and the same code letter performs differently at small-craft scale. Codes
sX-sZ price and cap energy weapons (``SMALL_CRAFT_ENERGY_CAPS``) but have no
tabulated performance on any small-craft hull."""
