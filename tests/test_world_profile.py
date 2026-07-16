from cetools.engine.pseudohex import from_pseudohex
from cetools.engine.worlds.models import System, TravelZone, World
from cetools.engine.worlds.profile import render_data_line, render_profile


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


# --- Full world-data line (Phase 4 / US2, research.md D5) ---


def _line_world(**overrides):
    fields = dict(
        name="Veltura",
        size=8,
        atmosphere=6,
        hydrographics=7,
        population=10,
        government=9,
        law_level=12,
        starport="A",
        tech_level=15,
        population_modifier=9,
        trade_codes=("Ag", "Ni"),
        travel_zone=TravelZone.AMBER,
    )
    fields.update(overrides)
    return World(**fields)


def _system(**overrides):
    fields = dict(
        world=_line_world(),
        hex="0102",
        planetoid_belts=2,
        gas_giants=3,
        naval_base=True,
        scout_base=False,
        pirate_base=False,
        allegiance="Na",
    )
    fields.update(overrides)
    return System(**fields)


def test_data_line_full_example():
    assert render_data_line(_system()) == "Veltura  0102  A867A9C-F  N  Ag Ni  A  923  Na"


def test_data_line_blank_hex_when_none():
    line = render_data_line(_system(hex=None))
    assert line == "Veltura    A867A9C-F  N  Ag Ni  A  923  Na"


def test_data_line_includes_hex_when_present():
    line = render_data_line(_system(hex="0102"))
    assert "0102" in line


def test_data_line_blank_trade_codes_when_none():
    line = render_data_line(_system(world=_line_world(trade_codes=())))
    assert line == "Veltura  0102  A867A9C-F  N    A  923  Na"


def test_data_line_green_travel_zone_renders_a_space():
    line = render_data_line(_system(world=_line_world(travel_zone=TravelZone.GREEN)))
    assert line == "Veltura  0102  A867A9C-F  N  Ag Ni     923  Na"


def test_data_line_no_bases_renders_blank_base_code():
    line = render_data_line(_system(naval_base=False))
    assert line == "Veltura  0102  A867A9C-F     Ag Ni  A  923  Na"


def test_unspecified_allegiance_defaults_to_and_renders_na():
    # FR-017
    system = _system()
    assert system.allegiance == "Na"
    assert render_data_line(system).endswith("Na")


def test_population_modifier_ten_system_renders_pbg_slot_as_a():
    # I1
    system = _system(world=_line_world(population_modifier=10), planetoid_belts=1, gas_giants=0)
    assert system.pbg == "A10"
    assert render_data_line(system) == "Veltura  0102  A867A9C-F  N  Ag Ni  A  A10  Na"


def test_system_data_line_property_delegates_to_render_data_line():
    system = _system()
    assert system.data_line == render_data_line(system)
