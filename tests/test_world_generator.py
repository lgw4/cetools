import random

from cetools.engine.rolls import RandomRolls, RollName, ScriptedRolls
from cetools.engine.worlds.generator import generate_system, generate_world
from cetools.engine.worlds.models import TravelZone


def _rolls(**kwargs) -> ScriptedRolls:
    return ScriptedRolls(**kwargs)


# --- Size ---


def test_size_is_two_d6_minus_two():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 9})
    assert generate_world(rolls, name="X").size == 7


# --- Atmosphere ---


def test_atmosphere_is_two_d6_minus_seven_plus_size():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 9, RollName.WORLD_ATMOSPHERE: 8})
    world = generate_world(rolls, name="X")
    assert world.size == 7
    assert world.atmosphere == 8  # 8-7+7


def test_atmosphere_forced_to_zero_when_size_zero():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 2, RollName.WORLD_ATMOSPHERE: 12})
    world = generate_world(rolls, name="X")
    assert world.size == 0
    assert world.atmosphere == 0


def test_atmosphere_caps_at_fifteen():
    # Scripted values exceed what real dice could ever produce, exercising the clamp
    # defensively.
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 12, RollName.WORLD_ATMOSPHERE: 20})
    world = generate_world(rolls, name="X")
    assert world.size == 10
    assert world.atmosphere == 15


# --- Hydrographics ---


def test_hydrographics_is_two_d6_minus_seven_plus_size():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_HYDROGRAPHICS: 8,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.hydrographics == 8  # 8-7+7, atmosphere 7 carries no hydro DM


def test_hydrographics_forced_to_zero_for_size_zero():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 2, RollName.WORLD_HYDROGRAPHICS: 12})
    world = generate_world(rolls, name="X")
    assert world.size == 0
    assert world.hydrographics == 0


def test_hydrographics_forced_to_zero_for_size_one():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 3, RollName.WORLD_HYDROGRAPHICS: 12})
    world = generate_world(rolls, name="X")
    assert world.size == 1
    assert world.hydrographics == 0


def test_hydrographics_dm_for_low_atmosphere():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 0,
            RollName.WORLD_HYDROGRAPHICS: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.atmosphere == 0  # 0-7+7
    assert world.hydrographics == 5  # 9-7+7-4


def test_hydrographics_clamps_to_range():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 12,
            RollName.WORLD_ATMOSPHERE: 2,
            RollName.WORLD_HYDROGRAPHICS: 12,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.hydrographics == 10  # 12-7+10=15, clamped to 10


# --- Population ---


def test_population_is_two_d6_minus_two_with_no_dms():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.size == 7
    assert world.atmosphere == 7
    assert world.population == 7  # 9-2


def test_population_small_size_dm():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 4,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.size == 2
    assert world.population == 6  # 9-2-1 (size <= 2)


def test_population_high_atmosphere_dm():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 10,
            RollName.WORLD_POPULATION: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.atmosphere == 10
    assert world.population == 5  # 9-2-2 (atmosphere >= A)


def test_population_clamps_to_ten():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 20,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 10  # 20-2=18, clamped


# --- Government / Law Level ---


def test_government_is_two_d6_minus_seven_plus_population():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
            RollName.WORLD_GOVERNMENT: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 7
    assert world.government == 9  # 9-7+7


def test_law_level_is_two_d6_minus_seven_plus_government():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
            RollName.WORLD_GOVERNMENT: 9,
            RollName.WORLD_LAW_LEVEL: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.government == 9
    assert world.law_level == 11  # 9-7+9


def test_government_law_and_tech_level_zero_when_population_zero():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 2,
            RollName.WORLD_GOVERNMENT: 12,
            RollName.WORLD_LAW_LEVEL: 12,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 0
    assert world.government == 0
    assert world.law_level == 0
    assert world.tech_level == 0


# --- Starport ---


def test_starport_lookup_uses_population_dm():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
            RollName.WORLD_STARPORT: 9,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 7
    assert world.starport == "B"  # 9-7+7=9 -> B


def test_starport_clamps_to_the_table_ends():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 2,
            RollName.WORLD_STARPORT: 2,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 0
    assert world.starport == "X"  # 2-7+0=-5, clamped to 2 -> X


# --- Technology Level ---


def test_tech_level_sums_dms_and_applies_a_minimum():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 4,  # size = 2
            RollName.WORLD_ATMOSPHERE: 7,  # atmosphere = 2
            RollName.WORLD_HYDROGRAPHICS: 7,  # hydrographics = 2
            RollName.WORLD_POPULATION: 9,  # population = 6
            RollName.WORLD_GOVERNMENT: 9,  # government = 8
            RollName.WORLD_LAW_LEVEL: 9,  # law_level = 10
            RollName.WORLD_STARPORT: 9,  # starport roll 8 -> C
        },
        d6={RollName.WORLD_TECH_LEVEL: 1},
    )
    world = generate_world(rolls, name="X")
    assert world.size == 2
    assert world.atmosphere == 2
    assert world.hydrographics == 2
    assert world.population == 6
    assert world.government == 8
    assert world.law_level == 10
    assert world.starport == "C"
    # DM sum: starport C(+2) + size 2(+1) + atmosphere 2(+1) = 4; 1D6=1 -> 5, raised to the
    # Atmosphere<=3 minimum of 7.
    assert world.tech_level == 7


def test_tech_level_dm_includes_the_hydrographics_zero_entry():
    # An earlier SRD summary omitted this; Appendix C1 confirms hydrographics 0 grants +1.
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 3,  # size = 1 (forces hydrographics to 0)
            RollName.WORLD_ATMOSPHERE: 12,  # atmosphere = 12-7+1 = 6
            RollName.WORLD_POPULATION: 9,
            RollName.WORLD_GOVERNMENT: 9,
            RollName.WORLD_LAW_LEVEL: 9,
            RollName.WORLD_STARPORT: 9,
        },
        d6={RollName.WORLD_TECH_LEVEL: 1},
    )
    world = generate_world(rolls, name="X")
    assert world.size == 1
    assert world.hydrographics == 0
    assert world.atmosphere == 6
    assert world.population == 9  # 9-2-1(size<=2)+3(atmo==6)
    assert world.starport == "A"  # 9-7+9=11, clamped to 11 -> A
    # DM sum: starport A(+6) + size 1(+2) + hydrographics 0(+1) + population 9(+1) = 10;
    # 1D6=1 -> 11 (already above the hydro-0/pop>=6 minimum of 4).
    assert world.tech_level == 11


def test_tech_level_floors_at_zero():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,  # size = 7
            RollName.WORLD_ATMOSPHERE: 6,  # atmosphere = 6 (no TL-minimum trigger)
            RollName.WORLD_POPULATION: 9,  # population = 9-2+3(atmo==6) = 10
            RollName.WORLD_STARPORT: -1,  # roll -1-7+10=2 -> X (-4 DM)
        },
        d6={RollName.WORLD_TECH_LEVEL: 1},
    )
    world = generate_world(rolls, name="X")
    assert world.atmosphere == 6
    assert world.population == 10
    assert world.starport == "X"
    # DM sum: starport X(-4) + population 10(+2) = -2; 1D6=1 -> -1, floored to 0 (no
    # applicable TL minimum at this atmosphere/hydrographics/population combination).
    assert world.tech_level == 0


# --- Population Modifier / head_count ---


def test_population_modifier_is_two_d6_minus_two_minimum_one():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
            RollName.POPULATION_MODIFIER: 3,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population_modifier == 1  # 3-2=1


def test_population_modifier_zero_when_uninhabited():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 2,
            RollName.POPULATION_MODIFIER: 12,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 0
    assert world.population_modifier == 0


# --- Naming ---


def test_generate_world_uses_the_given_name_verbatim():
    world = generate_world(ScriptedRolls(), name="Terra")
    assert world.name == "Terra"


def test_generate_world_generates_a_name_when_none_given():
    world = generate_world(ScriptedRolls())
    assert world.name


def test_generate_world_defaults_to_random_rolls():
    world = generate_world()
    assert world.name


# --- Statistical bounds (SC-001, SC-002) ---


def test_statistical_bounds_over_many_unseeded_worlds():
    rolls = RandomRolls(random.Random(0))
    for _ in range(2000):
        world = generate_world(rolls)
        assert 0 <= world.size <= 10
        assert 0 <= world.atmosphere <= 15
        assert 0 <= world.hydrographics <= 10
        assert 0 <= world.population <= 10
        assert 0 <= world.government <= 15
        assert world.law_level >= 0
        assert world.tech_level >= 0
        assert world.starport in "ABCDEX"
        if world.size == 0:
            assert world.atmosphere == 0
            assert world.hydrographics == 0
        if world.size <= 1:
            assert world.hydrographics == 0
        if world.population == 0:
            assert world.government == 0
            assert world.law_level == 0
            assert world.tech_level == 0
            assert world.population_modifier == 0
        else:
            assert 1 <= world.population_modifier <= 10


# --- Determinism (FR-022, SC-005) ---


def test_generate_world_is_deterministic_given_the_same_seed():
    world_a = generate_world(RandomRolls(random.Random(42)))
    world_b = generate_world(RandomRolls(random.Random(42)))
    assert world_a == world_b


# --- Trade codes (Appendix C3, SC-003) ---


def test_generate_world_assigns_multiple_matching_trade_codes():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,  # size = 7
            RollName.WORLD_ATMOSPHERE: 7,  # atmosphere = 7
            RollName.WORLD_HYDROGRAPHICS: 6,  # hydrographics = 6
            RollName.WORLD_POPULATION: 8,  # population = 6
            RollName.WORLD_GOVERNMENT: 7,  # government = 6
            RollName.WORLD_LAW_LEVEL: 7,  # law_level = 6
            RollName.WORLD_STARPORT: 8,  # starport = C
        },
        d6={RollName.WORLD_TECH_LEVEL: 3},  # tech_level = 5
    )
    world = generate_world(rolls, name="X")
    assert (world.atmosphere, world.hydrographics, world.population, world.tech_level) == (
        7,
        6,
        6,
        5,
    )
    assert world.trade_codes == ("Ag", "Lt", "Ni")


def test_generate_world_assigns_no_trade_codes_when_nothing_matches():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,  # size = 7
            RollName.WORLD_ATMOSPHERE: 2,  # atmosphere = 2
            RollName.WORLD_HYDROGRAPHICS: 5,  # hydrographics = 5
            RollName.WORLD_POPULATION: 9,  # population = 7
            RollName.WORLD_GOVERNMENT: 7,  # government = 7
            RollName.WORLD_LAW_LEVEL: 6,  # law_level = 6
            RollName.WORLD_STARPORT: 9,  # starport roll 9-7+7=9 -> B
        },
        d6={RollName.WORLD_TECH_LEVEL: 3},  # DM 4(B)+1(atmo2)+2(gov7)=7, +3=10
    )
    world = generate_world(rolls, name="X")
    assert (world.atmosphere, world.hydrographics, world.population, world.tech_level) == (
        2,
        5,
        7,
        10,
    )
    assert world.trade_codes == ()


def test_generate_world_trade_codes_match_the_table_generically():
    # Every generated world's trade_codes exactly matches recomputing the C3 table
    # against its own final UWP values (guards against drift between the generator's
    # matcher and the table it reads).
    from cetools.engine.worlds.tables import TRADE_CODES, matches_conditions

    rolls = RandomRolls(random.Random(3))
    for _ in range(500):
        world = generate_world(rolls)
        values = {
            "size": world.size,
            "atmosphere": world.atmosphere,
            "hydrographics": world.hydrographics,
            "population": world.population,
            "government": world.government,
            "law_level": world.law_level,
            "tech_level": world.tech_level,
        }
        expected = tuple(
            rule["code"] for rule in TRADE_CODES if matches_conditions(rule["conditions"], values)
        )
        assert world.trade_codes == expected


# --- Travel zone (Amber rule, FR-016) ---


def test_travel_zone_amber_for_high_atmosphere():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 12, RollName.WORLD_ATMOSPHERE: 20})
    world = generate_world(rolls, name="X")
    assert world.atmosphere == 15
    assert world.travel_zone == TravelZone.AMBER


def test_travel_zone_amber_for_government_zero():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 2,
            RollName.WORLD_GOVERNMENT: 12,
            RollName.WORLD_LAW_LEVEL: 12,
        }
    )
    world = generate_world(rolls, name="X")
    assert world.population == 0
    assert world.government == 0
    assert world.travel_zone == TravelZone.AMBER


def test_travel_zone_amber_for_government_seven():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,  # size = 7
            RollName.WORLD_ATMOSPHERE: 2,  # atmosphere = 2
            RollName.WORLD_HYDROGRAPHICS: 5,  # hydrographics = 5
            RollName.WORLD_POPULATION: 9,  # population = 7
            RollName.WORLD_GOVERNMENT: 7,  # government = 7
        },
    )
    world = generate_world(rolls, name="X")
    assert world.government == 7
    assert world.travel_zone == TravelZone.AMBER


def test_travel_zone_green_when_no_amber_condition_matches():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,  # size = 7
            RollName.WORLD_ATMOSPHERE: 7,  # atmosphere = 7
            RollName.WORLD_HYDROGRAPHICS: 7,  # hydrographics = 7
            RollName.WORLD_POPULATION: 9,  # population = 7
            RollName.WORLD_GOVERNMENT: 8,  # government = 8
            RollName.WORLD_LAW_LEVEL: 7,  # law_level = 8
        }
    )
    world = generate_world(rolls, name="X")
    assert (world.atmosphere, world.government, world.law_level) == (7, 8, 8)
    assert world.travel_zone == TravelZone.GREEN


def test_travel_zone_red_overrides_amber():
    rolls = _rolls(two_d6={RollName.WORLD_SIZE: 12, RollName.WORLD_ATMOSPHERE: 20})
    world = generate_world(rolls, name="X", travel_zone_red=True)
    assert world.atmosphere == 15  # would be Amber by rule
    assert world.travel_zone == TravelZone.RED


def test_travel_zone_red_override_on_an_otherwise_green_world():
    world = generate_world(ScriptedRolls(), name="X", travel_zone_red=True)
    assert world.travel_zone == TravelZone.RED


# --- generate_system: hex, allegiance, travel zone passthrough ---


def test_generate_system_stamps_the_given_hex():
    system = generate_system(ScriptedRolls(), name="X", hex="0102")
    assert system.hex == "0102"


def test_generate_system_hex_defaults_to_none():
    system = generate_system(ScriptedRolls(), name="X")
    assert system.hex is None


def test_generate_system_allegiance_defaults_to_na():
    system = generate_system(ScriptedRolls(), name="X")
    assert system.allegiance == "Na"


def test_generate_system_uses_the_given_allegiance():
    system = generate_system(ScriptedRolls(), name="X", allegiance="ImDs")
    assert system.allegiance == "ImDs"


def test_generate_system_travel_zone_red_override():
    system = generate_system(ScriptedRolls(), name="X", travel_zone_red=True)
    assert system.world.travel_zone == TravelZone.RED


def test_generate_system_world_carries_population_modifier():
    rolls = _rolls(
        two_d6={
            RollName.WORLD_SIZE: 9,
            RollName.WORLD_ATMOSPHERE: 7,
            RollName.WORLD_POPULATION: 9,
            RollName.POPULATION_MODIFIER: 3,
        }
    )
    system = generate_system(rolls, name="X")
    assert system.world.population_modifier == 1  # 3-2=1


# --- Planetoid belts ---


def test_belt_presence_and_count():
    rolls = _rolls(
        checks={RollName.PLANETOID_BELT_PRESENCE: True},
        d6={RollName.PLANETOID_BELT_COUNT: 5},
    )
    system = generate_system(rolls, name="X")
    assert system.planetoid_belts == 2  # 5-3


def test_no_belt_when_presence_check_fails_and_size_nonzero():
    rolls = _rolls(checks={RollName.PLANETOID_BELT_PRESENCE: False})
    system = generate_system(rolls, name="X")
    assert system.world.size != 0
    assert system.planetoid_belts == 0


def test_belt_guaranteed_when_size_zero_even_if_presence_check_fails():
    rolls = _rolls(
        two_d6={RollName.WORLD_SIZE: 2},
        checks={RollName.PLANETOID_BELT_PRESENCE: False},
        d6={RollName.PLANETOID_BELT_COUNT: 4},
    )
    system = generate_system(rolls, name="X")
    assert system.world.size == 0
    assert system.planetoid_belts == 1  # 4-3


def test_belt_count_minimum_one():
    rolls = _rolls(
        checks={RollName.PLANETOID_BELT_PRESENCE: True},
        d6={RollName.PLANETOID_BELT_COUNT: 1},
    )
    system = generate_system(rolls, name="X")
    assert system.planetoid_belts == 1  # max(1, 1-3)


# --- Gas giants ---


def test_gas_giant_presence_and_count():
    rolls = _rolls(
        checks={RollName.GAS_GIANT_PRESENCE: True},
        d6={RollName.GAS_GIANT_COUNT: 5},
    )
    system = generate_system(rolls, name="X")
    assert system.gas_giants == 3  # 5-2


def test_no_gas_giant_when_presence_check_fails():
    rolls = _rolls(checks={RollName.GAS_GIANT_PRESENCE: False})
    system = generate_system(rolls, name="X")
    assert system.gas_giants == 0


def test_gas_giant_count_minimum_one():
    rolls = _rolls(
        checks={RollName.GAS_GIANT_PRESENCE: True},
        d6={RollName.GAS_GIANT_COUNT: 1},
    )
    system = generate_system(rolls, name="X")
    assert system.gas_giants == 1  # max(1, 1-2)


# --- Bases: naval, scout, pirate (with exclusions) ---


def test_naval_base_present_when_check_passes_on_starport_a():
    rolls = _rolls(
        two_d6={RollName.WORLD_STARPORT: 12},  # roll-7+6(default pop)=11 -> A
        checks={RollName.NAVAL_BASE: True},
    )
    system = generate_system(rolls, name="X")
    assert system.world.starport == "A"
    assert system.naval_base is True


def test_naval_base_absent_on_non_ab_starport_even_if_check_passes():
    rolls = _rolls(checks={RollName.NAVAL_BASE: True})
    system = generate_system(rolls, name="X")
    assert system.world.starport not in ("A", "B")
    assert system.naval_base is False


class _ScoutDMSpy:
    """Wraps a Rolls adapter, recording the dm passed to the SCOUT_BASE check."""

    def __init__(self, inner):
        self._inner = inner
        self.scout_dm = None

    def check(self, dm, target, name):
        if name is RollName.SCOUT_BASE:
            self.scout_dm = dm
        return self._inner.check(dm, target, name)

    def two_d6(self, name):
        return self._inner.two_d6(name)

    def d6(self, name):
        return self._inner.d6(name)

    def choose(self, items, name):
        return self._inner.choose(items, name)


def _scout_dm_for_starport_roll(starport_roll):
    rolls = _ScoutDMSpy(_rolls(two_d6={RollName.WORLD_STARPORT: starport_roll}))
    generate_system(rolls, name="X")
    return rolls.scout_dm


def test_scout_base_dm_is_minus_three_for_starport_a():
    assert _scout_dm_for_starport_roll(12) == -3  # roll-7+6=11 -> A


def test_scout_base_dm_is_minus_two_for_starport_b():
    assert _scout_dm_for_starport_roll(11) == -2  # roll-7+6=10 -> B


def test_scout_base_dm_is_minus_one_for_starport_c():
    assert _scout_dm_for_starport_roll(9) == -1  # roll-7+6=8 -> C


def test_scout_base_dm_is_zero_for_starport_d():
    assert _scout_dm_for_starport_roll(7) == 0  # roll-7+6=6 -> D


def test_scout_base_never_present_on_starport_e_or_x():
    rolls = _rolls(
        two_d6={RollName.WORLD_STARPORT: -3},  # roll-7+6=-4, clamped to 2 -> X
        checks={RollName.SCOUT_BASE: True},
    )
    system = generate_system(rolls, name="X")
    assert system.world.starport == "X"
    assert system.scout_base is False


def test_pirate_base_present_when_no_naval_and_not_starport_a():
    rolls = _rolls(
        two_d6={RollName.WORLD_STARPORT: 7},  # -> D
        checks={RollName.PIRATE_BASE: True, RollName.NAVAL_BASE: False},
    )
    system = generate_system(rolls, name="X")
    assert system.world.starport == "D"
    assert system.pirate_base is True


def test_pirate_base_absent_on_starport_a_even_if_check_passes():
    rolls = _rolls(
        two_d6={RollName.WORLD_STARPORT: 12},  # -> A
        checks={RollName.PIRATE_BASE: True, RollName.NAVAL_BASE: False},
    )
    system = generate_system(rolls, name="X")
    assert system.world.starport == "A"
    assert system.pirate_base is False


def test_pirate_base_absent_when_naval_base_present():
    rolls = _rolls(
        two_d6={RollName.WORLD_STARPORT: 11},  # -> B
        checks={RollName.PIRATE_BASE: True, RollName.NAVAL_BASE: True},
    )
    system = generate_system(rolls, name="X")
    assert system.world.starport == "B"
    assert system.naval_base is True
    assert system.pirate_base is False


# --- Statistical bounds (SC-004) ---


def test_statistical_bounds_over_many_unseeded_systems():
    rolls = RandomRolls(random.Random(1))
    total = 10000
    belt_present = 0
    gas_giant_present = 0
    ab_starports = 0
    naval_present_given_ab = 0

    for _ in range(total):
        system = generate_system(rolls)
        if system.planetoid_belts > 0:
            belt_present += 1
        if system.gas_giants > 0:
            gas_giant_present += 1
        if system.world.starport in ("A", "B"):
            ab_starports += 1
            if system.naval_base:
                naval_present_given_ab += 1
        if system.naval_base:
            assert system.world.starport in ("A", "B")
        if system.scout_base:
            assert system.world.starport not in ("E", "X")
        if system.pirate_base:
            assert system.world.starport != "A"
            assert not system.naval_base
        if system.world.size == 0:
            assert system.planetoid_belts >= 1

    assert abs(belt_present / total * 100 - 92) <= 2
    assert abs(gas_giant_present / total * 100 - 83) <= 2
    assert abs(naval_present_given_ab / ab_starports * 100 - 42) <= 2


# --- Determinism (FR-022, SC-005) ---


def test_generate_system_is_deterministic_given_the_same_seed():
    system_a = generate_system(RandomRolls(random.Random(99)))
    system_b = generate_system(RandomRolls(random.Random(99)))
    assert system_a == system_b


def test_generate_system_defaults_to_random_rolls():
    system = generate_system()
    assert system.world.name
