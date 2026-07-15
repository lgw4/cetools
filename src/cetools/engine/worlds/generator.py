"""Generation rules for worlds, systems, and subsectors."""

from __future__ import annotations

from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.worlds.models import World
from cetools.engine.worlds.naming import generate_world_name
from cetools.engine.worlds.tables import (
    HYDRO_DM_BY_ATMOSPHERE,
    POPULATION_DMS,
    STARPORT_BY_ROLL,
    TL_DM_BY_VALUE,
    TL_MINIMUMS,
    matches_conditions,
)


def _roll_size(rolls: Rolls) -> int:
    return max(0, min(10, rolls.two_d6(RollName.WORLD_SIZE) - 2))


def _roll_atmosphere(rolls: Rolls, size: int) -> int:
    value = rolls.two_d6(RollName.WORLD_ATMOSPHERE) - 7 + size
    if size == 0:
        return 0
    return max(0, min(15, value))


def _roll_hydrographics(rolls: Rolls, size: int, atmosphere: int) -> int:
    value = rolls.two_d6(RollName.WORLD_HYDROGRAPHICS) - 7 + size
    value += HYDRO_DM_BY_ATMOSPHERE.get(atmosphere, 0)
    if size <= 1:
        return 0
    return max(0, min(10, value))


def _roll_population(rolls: Rolls, size: int, atmosphere: int, hydrographics: int) -> int:
    value = rolls.two_d6(RollName.WORLD_POPULATION) - 2
    values = {"size": size, "atmosphere": atmosphere, "hydrographics": hydrographics}
    for rule in POPULATION_DMS:
        if matches_conditions(rule["conditions"], values):
            value += rule["dm"]
    return max(0, min(10, value))


def _roll_government(rolls: Rolls, population: int) -> int:
    value = rolls.two_d6(RollName.WORLD_GOVERNMENT) - 7 + population
    if population == 0:
        return 0
    return max(0, min(15, value))


def _roll_law_level(rolls: Rolls, government: int) -> int:
    value = rolls.two_d6(RollName.WORLD_LAW_LEVEL) - 7 + government
    if government == 0:
        return 0
    return max(0, value)


def _roll_starport(rolls: Rolls, population: int) -> str:
    roll = rolls.two_d6(RollName.WORLD_STARPORT) - 7 + population
    clamped = max(2, min(11, roll))
    return STARPORT_BY_ROLL[clamped]


def _roll_tech_level(
    rolls: Rolls,
    starport: str,
    size: int,
    atmosphere: int,
    hydrographics: int,
    population: int,
    government: int,
) -> int:
    dm = (
        TL_DM_BY_VALUE["starport"].get(starport, 0)
        + TL_DM_BY_VALUE["size"].get(size, 0)
        + TL_DM_BY_VALUE["atmosphere"].get(atmosphere, 0)
        + TL_DM_BY_VALUE["hydrographics"].get(hydrographics, 0)
        + TL_DM_BY_VALUE["population"].get(population, 0)
        + TL_DM_BY_VALUE["government"].get(government, 0)
    )
    tech_level = max(0, rolls.d6(RollName.WORLD_TECH_LEVEL) + dm)

    values = {"atmosphere": atmosphere, "hydrographics": hydrographics, "population": population}
    for rule in TL_MINIMUMS:
        if matches_conditions(rule["conditions"], values):
            tech_level = max(tech_level, rule["min"])

    if population == 0:
        return 0
    return tech_level


def _roll_population_modifier(rolls: Rolls, population: int) -> int:
    value = rolls.two_d6(RollName.POPULATION_MODIFIER) - 2
    if population == 0:
        return 0
    return max(1, value)


def generate_world(rolls: Rolls | None = None, *, name: str | None = None) -> World:
    """A whole world: the classic UWP, generated in SRD order.

    `rolls` defaults to `RandomRolls()`; pass `RandomRolls(random.Random(seed))` for
    reproducibility (FR-022). `name` defaults to a generated one via
    `generate_world_name`; the caller may override it verbatim.
    """
    rolls = rolls or RandomRolls()

    size = _roll_size(rolls)
    atmosphere = _roll_atmosphere(rolls, size)
    hydrographics = _roll_hydrographics(rolls, size, atmosphere)
    population = _roll_population(rolls, size, atmosphere, hydrographics)
    government = _roll_government(rolls, population)
    law_level = _roll_law_level(rolls, government)
    starport = _roll_starport(rolls, population)
    tech_level = _roll_tech_level(
        rolls, starport, size, atmosphere, hydrographics, population, government
    )
    population_modifier = _roll_population_modifier(rolls, population)

    return World(
        name=name if name is not None else generate_world_name(rolls),
        size=size,
        atmosphere=atmosphere,
        hydrographics=hydrographics,
        population=population,
        government=government,
        law_level=law_level,
        starport=starport,
        tech_level=tech_level,
        population_modifier=population_modifier,
    )
