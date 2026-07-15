"""World, System, and Subsector domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from cetools.engine.worlds.profile import render_profile
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
