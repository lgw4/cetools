import pytest

from cetools.engine.rolls import RandomRolls, ScriptedRolls
from cetools.engine.ships import build_ship, dump_design, loads_design
from cetools.engine.ships.generator import generate_ship
from cetools.engine.ships.tables import HULLS

# --- ScriptedRolls pins a known component selection to an exact Ship ---


def test_scripted_rolls_all_defaults_yields_exact_ship():
    ship = generate_ship(ScriptedRolls())

    assert ship.hull_tons == 100
    assert ship.jump_rating == 2
    assert ship.maneuver_rating == 2
    assert ship.power_rating == 2
    assert ship.assumed_jump_distance == 2
    assert ship.jump_fuel == pytest.approx(20.0)
    assert ship.power_fuel == pytest.approx(2.0)
    assert ship.tonnage_used == pytest.approx(48.0)
    assert ship.cargo_tons == pytest.approx(52.0)
    assert ship.hull_points == 2
    assert ship.structure_points == 2
    assert ship.hardpoints == 1
    assert ship.hardpoints_used == 0
    assert ship.build_weeks == HULLS[100].build_weeks

    crew = ship.crew
    assert crew.pilot == 1
    assert crew.navigator == 1
    assert crew.engineers == 1
    assert crew.gunners == 0
    assert crew.screen_operators == 0
    assert crew.medic == 0
    assert crew.stewards == 0


# --- SC-004: reproducibility ---


def test_random_rolls_seeded_reproducible():
    a = generate_ship(RandomRolls.seeded(42))
    b = generate_ship(RandomRolls.seeded(42))
    assert a == b


def test_random_rolls_different_seeds_can_differ():
    a = generate_ship(RandomRolls.seeded(1))
    b = generate_ship(RandomRolls.seeded(2))
    assert a != b


# --- SC-003: a sweep of many seeds never raises ---


def test_many_seeds_all_produce_ships():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed))
        assert ship.cargo_tons >= 0


# --- FR-018: hull_size is honoured ---


def test_hull_size_is_honoured():
    for seed in range(20):
        ship = generate_ship(RandomRolls.seeded(seed), hull_size=400)
        assert ship.hull_tons == 400


def test_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        generate_ship(RandomRolls.seeded(1), hull_size=150)


# --- SC-008: generated ships round-trip losslessly ---


def test_generated_ships_round_trip():
    for seed in range(20):
        ship = generate_ship(RandomRolls.seeded(seed))
        assert build_ship(loads_design(dump_design(ship.design))) == ship


def test_default_rolls_is_random_rolls():
    # No explicit `rolls` argument still produces a valid ship (defaults to RandomRolls()).
    ship = generate_ship()
    assert ship.cargo_tons >= 0
