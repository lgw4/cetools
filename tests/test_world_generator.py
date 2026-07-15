import random

from cetools.engine.rolls import RandomRolls, RollName, ScriptedRolls
from cetools.engine.worlds.generator import generate_world


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
