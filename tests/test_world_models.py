import pytest

from cetools.engine.worlds.models import World


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
