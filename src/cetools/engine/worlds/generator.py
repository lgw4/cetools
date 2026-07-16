"""Generation rules for worlds, systems, and subsectors."""

from __future__ import annotations

from cetools.engine.rolls import RandomRolls, RollName, Rolls
from cetools.engine.worlds.models import System, TravelZone, World
from cetools.engine.worlds.naming import generate_world_name
from cetools.engine.worlds.tables import (
    HYDRO_DM_BY_ATMOSPHERE,
    POPULATION_DMS,
    STARPORT_BY_ROLL,
    TL_DM_BY_VALUE,
    TL_MINIMUMS,
    TRADE_CODES,
    matches_conditions,
)

_SCOUT_DM_BY_STARPORT = {"A": -3, "B": -2, "C": -1}


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


def _match_trade_codes(
    size: int,
    atmosphere: int,
    hydrographics: int,
    population: int,
    government: int,
    law_level: int,
    tech_level: int,
) -> tuple[str, ...]:
    values = {
        "size": size,
        "atmosphere": atmosphere,
        "hydrographics": hydrographics,
        "population": population,
        "government": government,
        "law_level": law_level,
        "tech_level": tech_level,
    }
    return tuple(
        rule["code"] for rule in TRADE_CODES if matches_conditions(rule["conditions"], values)
    )


def _is_amber(atmosphere: int, government: int, law_level: int) -> bool:
    return atmosphere >= 10 or government in (0, 7, 10) or law_level == 0 or law_level >= 9


def generate_world(
    rolls: Rolls | None = None,
    *,
    name: str | None = None,
    travel_zone_red: bool = False,
) -> World:
    """A whole world: the classic UWP, generated in SRD order.

    `rolls` defaults to `RandomRolls()`; pass `RandomRolls(random.Random(seed))` for
    reproducibility (FR-022). `name` defaults to a generated one via
    `generate_world_name`; the caller may override it verbatim. `travel_zone_red` is
    a caller override (referee discretion); Amber is still assigned by rule when
    applicable but is superseded by an explicit RED.
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
    trade_codes = _match_trade_codes(
        size, atmosphere, hydrographics, population, government, law_level, tech_level
    )
    if travel_zone_red:
        travel_zone = TravelZone.RED
    elif _is_amber(atmosphere, government, law_level):
        travel_zone = TravelZone.AMBER
    else:
        travel_zone = TravelZone.GREEN

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
        trade_codes=trade_codes,
        travel_zone=travel_zone,
    )


def _roll_planetoid_belts(rolls: Rolls, size: int) -> int:
    present = rolls.check(0, 4, RollName.PLANETOID_BELT_PRESENCE) or size == 0
    count = max(1, rolls.d6(RollName.PLANETOID_BELT_COUNT) - 3)
    return count if present else 0


def _roll_gas_giants(rolls: Rolls) -> int:
    present = rolls.check(0, 5, RollName.GAS_GIANT_PRESENCE)
    count = max(1, rolls.d6(RollName.GAS_GIANT_COUNT) - 2)
    return count if present else 0


def _roll_bases(rolls: Rolls, starport: str) -> tuple[bool, bool, bool]:
    naval_roll = rolls.check(0, 8, RollName.NAVAL_BASE)
    naval_base = starport in ("A", "B") and naval_roll

    scout_dm = _SCOUT_DM_BY_STARPORT.get(starport, 0)
    scout_roll = rolls.check(scout_dm, 7, RollName.SCOUT_BASE)
    scout_base = starport not in ("E", "X") and scout_roll

    pirate_roll = rolls.check(0, 12, RollName.PIRATE_BASE)
    pirate_base = starport != "A" and not naval_base and pirate_roll

    return naval_base, scout_base, pirate_base


def generate_system(
    rolls: Rolls | None = None,
    *,
    name: str | None = None,
    hex: str | None = None,
    allegiance: str = "Na",
    travel_zone_red: bool = False,
) -> System:
    """A world plus its stellar surroundings: belts, gas giants, and bases.

    `hex` optionally stamps a `"CCRR"` subsector coordinate. Other parameters
    forward to `generate_world`.
    """
    rolls = rolls or RandomRolls()

    world = generate_world(rolls, name=name, travel_zone_red=travel_zone_red)
    planetoid_belts = _roll_planetoid_belts(rolls, world.size)
    gas_giants = _roll_gas_giants(rolls)
    naval_base, scout_base, pirate_base = _roll_bases(rolls, world.starport)

    return System(
        world=world,
        hex=hex,
        planetoid_belts=planetoid_belts,
        gas_giants=gas_giants,
        naval_base=naval_base,
        scout_base=scout_base,
        pirate_base=pirate_base,
        allegiance=allegiance,
    )
