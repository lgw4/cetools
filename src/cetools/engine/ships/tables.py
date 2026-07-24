"""SRD Chapter 8 "Ship Design and Construction" tables, encoded as data.

Every table here carries only the starship (100-5,000 ton) rules the Foundational
phase and User Story 1 need. Small-craft tables (``SMALL_CRAFT_HULLS``,
``COCKPITS``, ``SMALL_CRAFT_ENERGY_CAPS``) and bay/screen tables (``BAYS``,
``SCREENS``) are added in their own story phases.

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
    """One row of the Ship Armor by Type table."""

    protection_per_5_percent: int
    cost_percent_per_5_percent: int
    min_tl: int


@dataclass(frozen=True)
class ComputerRow:
    """One row of the Ship Computer Models table."""

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
    """One row of the Ship Electronics table."""

    tons: float
    cost: float


@dataclass(frozen=True)
class QuartersRow:
    """One row covering staterooms / low berths / emergency low berths."""

    tons: float
    cost: float


@dataclass(frozen=True)
class FittingRow:
    """One row of the Additional Ship Components tables.

    ``tons``/``cost`` are ``None`` for a fitting whose size is computed from the
    design rather than fixed (the vehicle hangar, sized from ``vehicle_tons``).
    """

    tons: float | None
    cost: float | None
    forbidden_on_distributed: bool = False
    hull_structure_bonus: int = 0


@dataclass(frozen=True)
class MountRow:
    """One row of the Turret Displacement and Cost table."""

    tons: float
    cost: float
    weapon_slots: int


@dataclass(frozen=True)
class WeaponRow:
    """One row of the Turret Weapons table."""

    cost: float
    energy: bool = False


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

CONFIG_MODIFIERS: dict[str, float] = {
    "distributed": 0.9,
    "standard": 1.0,
    "streamlined": 1.1,
}
"""Ship Configuration hull-cost modifier, keyed by ``Configuration.value``."""

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
    "titanium_steel": ArmorRow(protection_per_5_percent=2, cost_percent_per_5_percent=5, min_tl=7),
    "crystaliron": ArmorRow(protection_per_5_percent=4, cost_percent_per_5_percent=20, min_tl=10),
    "bonded_superdense": ArmorRow(
        protection_per_5_percent=6, cost_percent_per_5_percent=50, min_tl=14
    ),
}
"""Armor type -> protection and cost per 5% of hull tonnage, keyed by ``ArmorType.value``."""

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
    "standard": ElectronicsRow(tons=0, cost=0),
    "basic_civilian": ElectronicsRow(tons=1, cost=0.05),
    "basic_military": ElectronicsRow(tons=2, cost=1),
    "advanced": ElectronicsRow(tons=3, cost=2),
    "very_advanced": ElectronicsRow(tons=5, cost=4),
}
"""Electronics package -> (tons, cost MCr). ``standard`` is included in the bridge."""

QUARTERS: dict[str, QuartersRow] = {
    "stateroom": QuartersRow(tons=4, cost=0.5),
    "low_berth": QuartersRow(tons=0.5, cost=0.05),
    "emergency_low_berth": QuartersRow(tons=1, cost=0.1),
}
"""Crew-accommodation kind -> (tons, cost MCr) per berth."""

FITTINGS: dict[str, FittingRow] = {
    "armory": FittingRow(tons=2, cost=0.5),
    "detention_cell": FittingRow(tons=2, cost=0.25),
    "fuel_scoops": FittingRow(tons=0, cost=1, forbidden_on_distributed=True),
    "fuel_processor": FittingRow(tons=1, cost=0.05),
    "laboratory": FittingRow(tons=4, cost=1),
    "library": FittingRow(tons=4, cost=4),
    "luxuries": FittingRow(tons=1, cost=0.1),
    "vault": FittingRow(tons=12, cost=6, hull_structure_bonus=4),
    "vehicle_hangar": FittingRow(tons=None, cost=None),
}
"""Fitting name -> (tons, cost MCr) per unit of ``FittingFit.quantity``.

``vehicle_hangar``'s tons/cost are ``None``: its size comes from
``FittingFit.vehicle_tons`` (hangar tons = vehicle tons x1.3, cost = MCr0.2/ton)."""

TURRET_MOUNTS: dict[str, MountRow] = {
    "single": MountRow(tons=1, cost=0.2, weapon_slots=1),
    "double": MountRow(tons=1, cost=0.5, weapon_slots=2),
    "triple": MountRow(tons=1, cost=1, weapon_slots=3),
    "pop_up": MountRow(tons=2, cost=1, weapon_slots=1),
    "fixed": MountRow(tons=1, cost=0.1, weapon_slots=1),
}
"""Mount type -> (tons, cost MCr, weapon slots).

The SRD presents pop-up and fixed as *qualities* layered on a single/double/triple
mount (+2 t and +MCr1 for pop-up; half cost for fixed), but ``TurretFit.mount`` is
one flat choice among five (design-schema.md), so each is modelled here as its own
single-weapon-slot mount: pop-up at its literal SRD tons/cost, fixed at half of a
single turret's cost."""

TURRET_WEAPONS: dict[str, WeaponRow] = {
    "missile_rack": WeaponRow(cost=0.75),
    "pulse_laser": WeaponRow(cost=0.5, energy=True),
    "sandcaster": WeaponRow(cost=0.25),
    "particle_beam": WeaponRow(cost=4, energy=True),
}
"""Turret weapon -> (cost MCr, whether it counts against a small craft's energy-weapon
cap). The SRD page's Turret Weapons table lists exactly these four; a "beam laser" is
named in the surrounding prose but never priced, so it is omitted rather than guessed."""
