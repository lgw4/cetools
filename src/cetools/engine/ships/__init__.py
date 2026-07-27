"""Public surface for the ship-design domain."""

from cetools.engine.ships.builder import build_ship
from cetools.engine.ships.description import render_description
from cetools.engine.ships.design import dump_design, load_design, loads_design
from cetools.engine.ships.generator import (
    UNCONSTRAINED,
    DesignConstraints,
    GenerationResult,
    TonnageLedger,
    UnmetConstraint,
    generate_ship,
    validate_hull_tons,
)
from cetools.engine.ships.models import (
    AmmoFit,
    ArmorFit,
    ArmorType,
    BayFit,
    ComputerFit,
    Configuration,
    Crew,
    FittingFit,
    HullClass,
    LineItem,
    ScreenFit,
    Ship,
    ShipDesign,
    SoftwareFit,
    TurretFit,
)
from cetools.engine.ships.names import (
    SHIP_NAMES,
    BasisKind,
    ShipName,
    Tradition,
    generate_ship_name,
)

__all__ = [
    "AmmoFit",
    "ArmorFit",
    "ArmorType",
    "BasisKind",
    "BayFit",
    "ComputerFit",
    "Configuration",
    "Crew",
    "DesignConstraints",
    "FittingFit",
    "GenerationResult",
    "HullClass",
    "LineItem",
    "SHIP_NAMES",
    "ScreenFit",
    "Ship",
    "ShipDesign",
    "ShipName",
    "SoftwareFit",
    "Tradition",
    "TonnageLedger",
    "TurretFit",
    "UNCONSTRAINED",
    "UnmetConstraint",
    "build_ship",
    "dump_design",
    "generate_ship",
    "generate_ship_name",
    "load_design",
    "loads_design",
    "render_description",
    "validate_hull_tons",
]
