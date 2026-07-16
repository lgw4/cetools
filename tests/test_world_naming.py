import random

from cetools.engine.rolls import RandomRolls, ScriptedRolls
from cetools.engine.worlds.naming import generate_world_name


def test_generate_world_name_is_non_empty_title_cased_and_pronounceable():
    name = generate_world_name(ScriptedRolls())
    assert name
    assert name.isalpha()
    assert name == name.capitalize()


def test_generate_world_name_is_deterministic_under_a_seeded_rolls():
    name_a = generate_world_name(RandomRolls(random.Random(7)))
    name_b = generate_world_name(RandomRolls(random.Random(7)))
    assert name_a == name_b


def test_generate_world_name_defaults_to_random_rolls():
    assert generate_world_name()


def test_generate_world_name_yields_at_least_ten_thousand_distinct_names():
    rolls = RandomRolls(random.Random(1))
    names = {generate_world_name(rolls) for _ in range(60000)}
    assert len(names) >= 10000
