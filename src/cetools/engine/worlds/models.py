"""World, System, and Subsector domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cetools.engine.pseudohex import to_pseudohex
from cetools.engine.worlds.profile import render_data_line, render_profile
from cetools.engine.worlds.tables import TL_MINIMUMS, matches_conditions

_VALID_STARPORTS = frozenset("ABCDEX")


class TravelZone(Enum):
    """A system's safety classification (research.md Part A step 14)."""

    GREEN = " "
    AMBER = "A"
    RED = "R"


def _tech_level_minimum(atmosphere: int, hydrographics: int, population: int) -> int:
    values = {"atmosphere": atmosphere, "hydrographics": hydrographics, "population": population}
    applicable = [
        rule["min"] for rule in TL_MINIMUMS if matches_conditions(rule["conditions"], values)
    ]
    return max(applicable, default=0)


def _validate_world(world: World) -> None:
    if not 0 <= world.size <= 10:
        raise ValueError(f"size must be 0-10, got {world.size}")
    if not 0 <= world.atmosphere <= 15:
        raise ValueError(f"atmosphere must be 0-15, got {world.atmosphere}")
    if not 0 <= world.hydrographics <= 10:
        raise ValueError(f"hydrographics must be 0-10, got {world.hydrographics}")
    if not 0 <= world.population <= 10:
        raise ValueError(f"population must be 0-10, got {world.population}")
    if not 0 <= world.government <= 15:
        raise ValueError(f"government must be 0-15, got {world.government}")
    if world.law_level < 0:
        raise ValueError(f"law_level must be >= 0, got {world.law_level}")
    if world.tech_level < 0:
        raise ValueError(f"tech_level must be >= 0, got {world.tech_level}")
    if world.starport not in _VALID_STARPORTS:
        raise ValueError(f"starport must be one of A B C D E X, got {world.starport!r}")

    if world.size == 0 and (world.atmosphere != 0 or world.hydrographics != 0):
        raise ValueError("size 0 requires atmosphere 0 and hydrographics 0")
    if world.size <= 1 and world.hydrographics != 0:
        raise ValueError("size 0 or 1 requires hydrographics 0")

    if world.population == 0:
        if world.government != 0 or world.law_level != 0 or world.tech_level != 0:
            raise ValueError("population 0 requires government, law_level, and tech_level 0")
        if world.population_modifier != 0:
            raise ValueError("population 0 requires population_modifier 0")
    else:
        if not 1 <= world.population_modifier <= 10:
            raise ValueError(
                f"population_modifier must be 1-10 when inhabited, got"
                f" {world.population_modifier}"
            )
        minimum = _tech_level_minimum(world.atmosphere, world.hydrographics, world.population)
        if world.tech_level < minimum:
            raise ValueError(
                f"tech_level must be >= mandated minimum {minimum}, got {world.tech_level}"
            )


@dataclass(frozen=True)
class World:
    """The primary world of a system. Produced by `generate_world`."""

    name: str
    size: int
    atmosphere: int
    hydrographics: int
    population: int
    government: int
    law_level: int
    starport: str
    tech_level: int
    population_modifier: int
    trade_codes: tuple[str, ...] = ()
    travel_zone: TravelZone = TravelZone.GREEN

    def __post_init__(self) -> None:
        _validate_world(self)

    @property
    def profile(self) -> str:
        """The classic UWP string, e.g. `A867A9C-F`."""
        return render_profile(self)

    @property
    def head_count(self) -> int:
        """The specific population: `population_modifier * 10**population`."""
        return self.population_modifier * (10**self.population)


def _validate_system(system: System) -> None:
    if system.planetoid_belts < 0:
        raise ValueError(f"planetoid_belts must be >= 0, got {system.planetoid_belts}")
    if system.gas_giants < 0:
        raise ValueError(f"gas_giants must be >= 0, got {system.gas_giants}")
    if system.world.size == 0 and system.planetoid_belts < 1:
        raise ValueError("size 0 requires at least one planetoid belt")
    if system.naval_base and system.world.starport not in ("A", "B"):
        raise ValueError("naval base requires starport A or B")
    if system.scout_base and system.world.starport in ("E", "X"):
        raise ValueError("scout base is never present on starport E or X")
    if system.pirate_base and (system.world.starport == "A" or system.naval_base):
        raise ValueError("pirate base is never present with starport A or a naval base")


@dataclass(frozen=True)
class System:
    """A world plus its stellar surroundings. Produced by `generate_system`."""

    world: World
    hex: str | None = None
    planetoid_belts: int = 0
    gas_giants: int = 0
    naval_base: bool = False
    scout_base: bool = False
    pirate_base: bool = False
    allegiance: str = "Na"

    def __post_init__(self) -> None:
        _validate_system(self)

    @property
    def base_code(self) -> str:
        """`A`/`N`/`S`/`G`/`P`, or a blank space when no base is present."""
        if self.naval_base and self.scout_base:
            return "A"
        if self.naval_base:
            return "N"
        if self.scout_base and self.pirate_base:
            return "G"
        if self.scout_base:
            return "S"
        if self.pirate_base:
            return "P"
        return " "

    @property
    def pbg(self) -> str:
        """Population Modifier, planetoid belts, gas giants, each pseudo-hex encoded."""
        return "".join(
            to_pseudohex(value)
            for value in (self.world.population_modifier, self.planetoid_belts, self.gas_giants)
        )

    @property
    def data_line(self) -> str:
        """The full world-data line (research.md D5)."""
        return render_data_line(self)
