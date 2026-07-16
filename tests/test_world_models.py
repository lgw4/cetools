import pytest

from cetools.engine.worlds.models import System, World


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


def test_profile_renders_srd_order_with_hyphen_before_tl():
    assert _world().profile == "A867A9C-F"


def test_head_count_is_modifier_times_ten_to_the_population():
    world = _world(population=3, population_modifier=5)
    assert world.head_count == 5000


def test_head_count_is_zero_for_an_uninhabited_world():
    world = _world(population=0, population_modifier=0, government=0, law_level=0, tech_level=0)
    assert world.head_count == 0


@pytest.mark.parametrize(
    "field,value",
    [
        ("size", -1),
        ("size", 11),
        ("atmosphere", -1),
        ("atmosphere", 16),
        ("hydrographics", -1),
        ("hydrographics", 11),
        ("population", -1),
        ("population", 11),
        ("government", -1),
        ("government", 16),
        ("law_level", -1),
        ("tech_level", -1),
    ],
)
def test_out_of_range_field_raises(field, value):
    with pytest.raises(ValueError):
        _world(**{field: value})


def test_invalid_starport_raises():
    with pytest.raises(ValueError, match="starport"):
        _world(starport="Z")


def test_size_zero_requires_atmosphere_zero():
    with pytest.raises(ValueError):
        _world(size=0, atmosphere=1, hydrographics=0)


def test_size_zero_requires_hydrographics_zero():
    with pytest.raises(ValueError):
        _world(size=0, atmosphere=0, hydrographics=1)


def test_size_one_requires_hydrographics_zero():
    with pytest.raises(ValueError):
        _world(size=1, hydrographics=1)


def test_population_zero_requires_government_zero():
    with pytest.raises(ValueError):
        _world(population=0, government=1, law_level=0, tech_level=0, population_modifier=0)


def test_population_zero_requires_law_level_zero():
    with pytest.raises(ValueError):
        _world(population=0, government=0, law_level=1, tech_level=0, population_modifier=0)


def test_population_zero_requires_tech_level_zero():
    with pytest.raises(ValueError):
        _world(population=0, government=0, law_level=0, tech_level=1, population_modifier=0)


def test_population_modifier_must_be_at_least_one_when_inhabited():
    with pytest.raises(ValueError):
        _world(population_modifier=0)


def test_population_modifier_must_be_at_most_ten():
    with pytest.raises(ValueError):
        _world(population_modifier=11)


def test_population_modifier_must_be_zero_when_uninhabited():
    with pytest.raises(ValueError):
        _world(
            population=0,
            government=0,
            law_level=0,
            tech_level=0,
            population_modifier=1,
        )


def test_tech_level_below_the_mandated_minimum_raises():
    # Atmosphere <= 3 mandates TL >= 7 (Appendix C2); TL 6 is one short.
    with pytest.raises(ValueError, match="tech_level"):
        _world(atmosphere=2, tech_level=6)


def test_tech_level_at_the_mandated_minimum_is_valid():
    _world(atmosphere=2, tech_level=7)


def test_tech_level_minimum_does_not_apply_to_an_uninhabited_world():
    # Population 0 forces TL to 0, overriding any mandated minimum (FR-009).
    _world(
        population=0,
        atmosphere=2,
        government=0,
        law_level=0,
        tech_level=0,
        population_modifier=0,
    )


# --- System (Phase 4 / US2) ---


def _system(**overrides):
    fields = dict(
        world=_world(),
        hex=None,
        planetoid_belts=1,
        gas_giants=1,
        naval_base=False,
        scout_base=False,
        pirate_base=False,
        allegiance="Na",
    )
    fields.update(overrides)
    return System(**fields)


def test_base_code_naval_and_scout_is_a():
    assert _system(naval_base=True, scout_base=True).base_code == "A"


def test_base_code_naval_only_is_n():
    assert _system(naval_base=True).base_code == "N"


def test_base_code_scout_only_is_s():
    assert _system(scout_base=True).base_code == "S"


def test_base_code_scout_and_pirate_is_g():
    system = _system(world=_world(starport="C"), scout_base=True, pirate_base=True)
    assert system.base_code == "G"


def test_base_code_pirate_only_is_p():
    system = _system(world=_world(starport="C"), pirate_base=True)
    assert system.base_code == "P"


def test_base_code_none_is_blank():
    assert _system().base_code == " "


def test_pbg_renders_each_slot_via_pseudohex():
    system = _system(world=_world(population_modifier=10), planetoid_belts=1, gas_giants=0)
    assert system.pbg == "A10"


def test_pbg_all_single_digit_slots():
    system = _system(world=_world(population_modifier=5), planetoid_belts=3, gas_giants=4)
    assert system.pbg == "534"


def test_negative_planetoid_belts_raises():
    with pytest.raises(ValueError):
        _system(planetoid_belts=-1)


def test_negative_gas_giants_raises():
    with pytest.raises(ValueError):
        _system(gas_giants=-1)


def test_size_zero_requires_at_least_one_belt():
    with pytest.raises(ValueError):
        _system(world=_world(size=0, atmosphere=0, hydrographics=0), planetoid_belts=0)


def test_size_zero_with_a_belt_is_valid():
    _system(world=_world(size=0, atmosphere=0, hydrographics=0), planetoid_belts=1)


def test_naval_base_requires_starport_a_or_b():
    with pytest.raises(ValueError):
        _system(world=_world(starport="C"), naval_base=True)


def test_naval_base_allowed_on_starport_b():
    _system(world=_world(starport="B"), naval_base=True)


def test_scout_base_never_present_on_starport_e():
    with pytest.raises(ValueError):
        _system(world=_world(starport="E"), scout_base=True)


def test_scout_base_never_present_on_starport_x():
    with pytest.raises(ValueError):
        _system(world=_world(starport="X"), scout_base=True)


def test_pirate_base_never_present_with_starport_a():
    with pytest.raises(ValueError):
        _system(world=_world(starport="A"), pirate_base=True)


def test_pirate_base_never_present_with_a_naval_base():
    with pytest.raises(ValueError):
        _system(world=_world(starport="B"), naval_base=True, pirate_base=True)


def test_pirate_base_allowed_without_naval_base_or_starport_a():
    _system(world=_world(starport="C"), pirate_base=True)
