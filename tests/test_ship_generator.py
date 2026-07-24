import time

import pytest

from cetools.engine.rolls import RandomRolls, ScriptedRolls
from cetools.engine.ships import build_ship, dump_design, load_design, loads_design
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


# --- US3: small craft (research.md Part K) ---


def test_small_craft_yields_a_10_to_95_ton_ship_with_no_jump_drive():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed), small_craft=True)
        assert 10 <= ship.hull_tons <= 95
        assert ship.jump_rating == 0
        assert ship.jump_fuel == pytest.approx(0.0)
        assert ship.cargo_tons >= 0


def test_small_craft_reproducible_from_a_seed():
    a = generate_ship(RandomRolls.seeded(42), small_craft=True)
    b = generate_ship(RandomRolls.seeded(42), small_craft=True)
    assert a == b


def test_small_craft_hull_size_is_honoured():
    for tons in (10, 40, 95):
        for seed in range(10):
            ship = generate_ship(RandomRolls.seeded(seed), hull_size=tons, small_craft=True)
            assert ship.hull_tons == tons


def test_small_craft_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated small-craft hull size"):
        generate_ship(RandomRolls.seeded(1), hull_size=100, small_craft=True)


def test_small_craft_round_trips_losslessly():
    for seed in range(50):
        ship = generate_ship(RandomRolls.seeded(seed), small_craft=True)
        assert build_ship(loads_design(dump_design(ship.design))) == ship


# --- US4: bays and screens (research.md Part H) ---


def test_generated_bays_never_exceed_hardpoints_or_free_tonnage():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed))
        assert ship.hardpoints_used <= ship.hardpoints
        assert ship.cargo_tons >= 0


def test_generated_ships_never_carry_a_bay_on_small_craft():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed), small_craft=True)
        assert ship.design.bays == ()


def test_a_bay_is_reachable_for_a_large_enough_hull():
    # Sweep enough seeds on a hull with ample hardpoints and tonnage that at
    # least one draw selects a bay (bay selection is randomized, not forced).
    assert any(
        generate_ship(RandomRolls.seeded(seed), hull_size=2000).design.bays for seed in range(300)
    )


def test_a_screen_is_reachable_for_a_large_enough_hull():
    assert any(
        generate_ship(RandomRolls.seeded(seed), hull_size=2000).design.screens
        for seed in range(300)
    )


# --- SC-007: a single build or generation is effectively instant ---


def test_a_single_build_completes_in_under_a_tenth_of_a_second():
    design = load_design("specs/010-starship-generator/examples/free-trader.toml")
    build_ship(design)  # warm up imports before timing

    start = time.perf_counter()
    build_ship(design)
    assert time.perf_counter() - start < 0.1


def test_a_single_generation_completes_in_under_a_tenth_of_a_second():
    generate_ship(RandomRolls.seeded(1))  # warm up imports before timing

    start = time.perf_counter()
    generate_ship(RandomRolls.seeded(2))
    assert time.perf_counter() - start < 0.1
