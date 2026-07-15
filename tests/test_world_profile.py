from cetools.engine.pseudohex import from_pseudohex
from cetools.engine.worlds.models import World
from cetools.engine.worlds.profile import render_profile


def _world(**overrides):
    fields = dict(
        name="Testworld",
        size=8,
        atmosphere=6,
        hydrographics=7,
        population=10,
        government=9,
        law_level=12,
        starport="A",
        tech_level=15,
        population_modifier=9,
    )
    fields.update(overrides)
    return World(**fields)


def test_render_profile_matches_the_classic_example():
    assert render_profile(_world()) == "A867A9C-F"


def test_render_profile_uses_pseudohex_for_values_above_nine():
    world = _world(population=10, government=11, law_level=13, tech_level=14)
    assert render_profile(world) == "A867ABD-E"


def test_render_profile_uses_the_literal_starport_letter():
    world = _world(starport="X")
    assert render_profile(world).startswith("X")


def test_render_profile_hyphen_precedes_tech_level():
    profile = render_profile(_world())
    assert profile[-2] == "-"
    assert profile.count("-") == 1


def test_world_profile_property_delegates_to_render_profile():
    world = _world()
    assert world.profile == render_profile(world)


def test_render_profile_round_trips_via_pseudohex():
    world = _world()
    profile = render_profile(world)
    starport, rest = profile[0], profile[1:]
    digits, tech_level_char = rest.split("-")
    assert starport == world.starport
    assert [from_pseudohex(char) for char in digits] == [
        world.size,
        world.atmosphere,
        world.hydrographics,
        world.population,
        world.government,
        world.law_level,
    ]
    assert from_pseudohex(tech_level_char) == world.tech_level
