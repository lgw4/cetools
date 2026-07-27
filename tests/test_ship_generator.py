import json
import math
import time

import pytest

from cetools.engine.rolls import RandomRolls, RollName, Rolls, ScriptedRolls
from cetools.engine.ships import (
    SHIP_NAMES,
    UNCONSTRAINED,
    DesignConstraints,
    GenerationResult,
    HullClass,
    Ship,
    ShipDesign,
    build_ship,
    dump_design,
    load_design,
    loads_design,
)
from cetools.engine.ships.generator import TonnageLedger, generate_ship
from cetools.engine.ships.tables import DRIVE_COSTS, DRIVE_PERFORMANCE, HULLS

_SMALL_CRAFT = DesignConstraints(hull_class=HullClass.SMALL_CRAFT)
_CATALOGUE_NAMES = {entry.name for entry in SHIP_NAMES}
_PRE_CHANGE_SWEEP_PATH = "tests/data/baseline/pre_change_sweep.json"
_POST_CHANGE_BASELINE_PATH = "tests/data/baseline/designs.json"

# --- TonnageLedger: the budget the selection steps spend against ---


def test_ledger_starts_with_the_tonnage_it_was_given():
    assert TonnageLedger(42.5).remaining == pytest.approx(42.5)


def test_ledger_spending_reduces_what_remains():
    ledger = TonnageLedger(100.0)
    ledger.spend(30.0)
    ledger.spend(0.5)
    assert ledger.remaining == pytest.approx(69.5)


def test_ledger_affords_exactly_what_remains():
    """The boundary is inclusive: a component costing every remaining ton fits.

    The threaded-float code this replaced declined only when `tons > remaining`,
    so an exact fit was affordable. Flipping this to exclusive would silently
    drop components that used to be installed.
    """
    ledger = TonnageLedger(10.0)
    assert ledger.affords(10.0)
    assert not ledger.affords(10.1)


def test_ledger_affords_nothing_once_overspent():
    ledger = TonnageLedger(1.0)
    ledger.spend(1.0)
    assert ledger.affords(0.0)
    assert not ledger.affords(0.1)


def test_ledger_records_nothing_until_something_is_declined():
    assert TonnageLedger(100.0).declined == ()


def test_ledger_records_declines_in_order_with_their_reasons():
    ledger = TonnageLedger(5.0)
    ledger.decline("armor", "crystaliron 10%", "none", "needs 20.0t, 5.0t free")
    ledger.decline("bay", "particle", "none", "needs 51.0t, 5.0t free")

    assert [d.field for d in ledger.declined] == ["armor", "bay"]
    assert ledger.declined[0].asked == "crystaliron 10%"
    assert ledger.declined[0].reason == "needs 20.0t, 5.0t free"


def test_ledger_declined_is_a_snapshot_not_a_live_view():
    ledger = TonnageLedger(5.0)
    before = ledger.declined
    ledger.decline("screen", "meson", "none", "needs 50.0t, 5.0t free")
    assert before == ()
    assert len(ledger.declined) == 1


def test_ledger_declining_does_not_move_the_budget():
    """Recording a decline is bookkeeping, not an allocation."""
    ledger = TonnageLedger(5.0)
    ledger.decline("armor", "crystaliron 10%", "none", "needs 20.0t, 5.0t free")
    assert ledger.remaining == pytest.approx(5.0)


# --- GenerationResult: what generation produced, and what it could not honour ---


def test_generate_ship_returns_a_result_carrying_the_ship():
    result = generate_ship(ScriptedRolls())

    assert isinstance(result, GenerationResult)
    assert isinstance(result.ship, Ship)
    assert result.ship.hull_tons == 100


def test_unconstrained_generation_reports_nothing_unmet():
    """Nothing is pinned, so nothing can go unhonoured: a rolled value that will
    not fit is a preference declined silently, never an unmet constraint."""
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)).unmet == ()
        assert generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).unmet == ()


def test_result_equality_still_distinguishes_seeds():
    """The result record is compared, not just the ship it carries, so seeded
    reproducibility assertions keep their meaning after the return type change."""
    assert generate_ship(RandomRolls.seeded(42)) == generate_ship(RandomRolls.seeded(42))
    assert generate_ship(RandomRolls.seeded(1)) != generate_ship(RandomRolls.seeded(2))


# --- DesignConstraints: the referee's answers, carried as a value ---


def test_unconstrained_is_the_default_and_pins_nothing():
    """Constraints are optional, and their absence is `UNCONSTRAINED`.

    Every pin below is measured against this: the same seed with nothing pinned
    must still produce the ship it produced before constraints existed, which is
    what `tests/data/baseline/designs.json` holds.
    """
    for seed in range(20):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(
            RandomRolls.seeded(seed), constraints=UNCONSTRAINED
        )


def test_constraints_carry_the_hull_class_the_ruleset_branches_on():
    starship = generate_ship(RandomRolls.seeded(7)).ship
    small_craft = generate_ship(RandomRolls.seeded(7), constraints=_SMALL_CRAFT).ship

    assert starship.design.hull_class is HullClass.STARSHIP
    assert small_craft.design.hull_class is HullClass.SMALL_CRAFT


# --- ScriptedRolls pins a known component selection to an exact Ship ---


def test_scripted_rolls_all_defaults_yields_exact_ship():
    ship = generate_ship(ScriptedRolls()).ship

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
    a = generate_ship(RandomRolls.seeded(42)).ship
    b = generate_ship(RandomRolls.seeded(42)).ship
    assert a == b


def test_random_rolls_different_seeds_can_differ():
    a = generate_ship(RandomRolls.seeded(1)).ship
    b = generate_ship(RandomRolls.seeded(2)).ship
    assert a != b


# --- SC-003: a sweep of many seeds never raises ---


def test_many_seeds_all_produce_ships():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.cargo_tons >= 0


# --- FR-018: a pinned hull tonnage is honoured ---


def test_hull_size_is_honoured():
    for seed in range(20):
        ship = generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400)
        ).ship
        assert ship.hull_tons == 400


def test_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated hull size"):
        generate_ship(RandomRolls.seeded(1), constraints=DesignConstraints(hull_tons=150))


# --- SC-008: generated ships round-trip losslessly ---


def test_generated_ships_round_trip():
    for seed in range(20):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert build_ship(loads_design(dump_design(ship.design))) == ship


def test_default_rolls_is_random_rolls():
    # No explicit `rolls` argument still produces a valid ship (defaults to RandomRolls()).
    ship = generate_ship().ship
    assert ship.cargo_tons >= 0


# --- US1: every generated ship is named (FR-001, FR-002) ---


def test_generated_starship_carries_a_catalogue_name():
    ship = generate_ship(RandomRolls.seeded(42)).ship
    assert ship.design.name in _CATALOGUE_NAMES


def test_generated_small_craft_carries_a_catalogue_name():
    ship = generate_ship(RandomRolls.seeded(7), constraints=_SMALL_CRAFT).ship
    assert ship.design.name in _CATALOGUE_NAMES


# --- T018 (US2): naming is reproducible by seed, not forced across seeds (FR-010, SC-002) ---


def test_generated_ship_name_is_reproducible_from_a_seed():
    a = generate_ship(RandomRolls.seeded(42)).ship
    b = generate_ship(RandomRolls.seeded(42)).ship
    assert a == b
    assert a.design.name == b.design.name


def test_generated_ship_names_across_seeds_are_not_forced_to_match():
    names = {generate_ship(RandomRolls.seeded(seed)).ship.design.name for seed in range(20)}
    assert len(names) > 1


# --- T025 (US3): generated batches read as varied (SC-003) ---
# Pinned seed set 0-19 so this check cannot flake.


def test_generated_ships_over_a_pinned_seed_set_are_mostly_distinct():
    names = [generate_ship(RandomRolls.seeded(seed)).ship.design.name for seed in range(20)]
    assert len(set(names)) >= 17


# --- US3: small craft (SRD "Small Craft Design") ---


def test_small_craft_yields_a_10_to_95_ton_ship_with_no_jump_drive():
    for seed in range(200):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert 10 <= ship.hull_tons <= 95
        assert ship.jump_rating == 0
        assert ship.jump_fuel == pytest.approx(0.0)
        assert ship.cargo_tons >= 0


def test_small_craft_reproducible_from_a_seed():
    a = generate_ship(RandomRolls.seeded(42), constraints=_SMALL_CRAFT).ship
    b = generate_ship(RandomRolls.seeded(42), constraints=_SMALL_CRAFT).ship
    assert a == b


def test_small_craft_hull_size_is_honoured():
    for tons in (10, 40, 95):
        for seed in range(10):
            ship = generate_ship(
                RandomRolls.seeded(seed),
                constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=tons),
            ).ship
            assert ship.hull_tons == tons


def test_small_craft_unknown_hull_size_raises():
    with pytest.raises(ValueError, match="not a tabulated small-craft hull size"):
        generate_ship(
            RandomRolls.seeded(1),
            constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=100),
        )


def test_small_craft_round_trips_losslessly():
    for seed in range(50):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert build_ship(loads_design(dump_design(ship.design))) == ship


# --- US4: bays and screens (SRD "Bays", "Screens") ---


def test_generated_bays_never_exceed_hardpoints_or_free_tonnage():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.hardpoints_used <= ship.hardpoints
        assert ship.cargo_tons >= 0


def test_generated_ships_never_carry_a_bay_on_small_craft():
    for seed in range(300):
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert ship.design.bays == ()


def test_a_bay_is_reachable_for_a_large_enough_hull():
    # Sweep enough seeds on a hull with ample hardpoints and tonnage that at
    # least one draw selects a bay (bay selection is randomized, not forced).
    assert any(
        generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=2000)
        ).ship.design.bays
        for seed in range(300)
    )


def test_a_screen_is_reachable_for_a_large_enough_hull():
    assert any(
        generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=2000)
        ).ship.design.screens
        for seed in range(300)
    )


# --- Phase 2 Foundational: `_fit_jump_drive` ---
# T006: contract tests C1-C4/C8, driven by four worked examples.
# These were written before `_fit_jump_drive` existed and confirmed red against
# the AttributeError it raised then; the implementation followed, and they have
# passed since.

_FIT_WORKED_EXAMPLES = (
    (400, "C", 200, "B"),
    (700, "Z", 600, "U"),
    (700, "Z", 400, "N"),
    (100, "C", 72, "B"),
)


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_matches_the_contracts_worked_examples(
    hull_tons, drawn_code, budget, expected
):
    from cetools.engine.ships.generator import _fit_jump_drive

    assert _fit_jump_drive(hull_tons, drawn_code, budget) == expected


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c1_result_is_legal_for_the_hull(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert hull_tons in DRIVE_PERFORMANCE[result]


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c2_rating_is_never_raised(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert DRIVE_PERFORMANCE[result][hull_tons] <= DRIVE_PERFORMANCE[drawn_code][hull_tons]


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c3_result_is_the_unique_lightest_at_its_rating(
    hull_tons, drawn_code, budget, expected
):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    result_rating = DRIVE_PERFORMANCE[result][hull_tons]
    result_tons = DRIVE_COSTS[result].jump_tons
    for code, ratings in DRIVE_PERFORMANCE.items():
        if hull_tons in ratings and ratings[hull_tons] == result_rating:
            assert DRIVE_COSTS[code].jump_tons >= result_tons


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c4_highest_affordable_rating_wins(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]
    affordable_ratings = [
        ratings[hull_tons]
        for code, ratings in DRIVE_PERFORMANCE.items()
        if hull_tons in ratings
        and ratings[hull_tons] <= ceiling
        and DRIVE_COSTS[code].jump_tons + 0.1 * hull_tons * ratings[hull_tons] <= budget
    ]
    result_rating = DRIVE_PERFORMANCE[result][hull_tons]
    if affordable_ratings:
        assert result_rating == max(affordable_ratings)
        assert DRIVE_COSTS[result].jump_tons + 0.1 * hull_tons * result_rating <= budget
    else:
        assert result_rating == min(
            ratings[hull_tons]
            for code, ratings in DRIVE_PERFORMANCE.items()
            if hull_tons in ratings
        )


@pytest.mark.parametrize("hull_tons,drawn_code,budget,expected", _FIT_WORKED_EXAMPLES)
def test_fit_jump_drive_c8_is_idempotent(hull_tons, drawn_code, budget, expected):
    from cetools.engine.ships.generator import _fit_jump_drive

    result = _fit_jump_drive(hull_tons, drawn_code, budget)
    assert _fit_jump_drive(hull_tons, result, budget) == result


def test_fit_jump_drive_legality_and_ceiling_hold_over_every_hull_and_legal_drawn_code():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        for drawn_code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            result = _fit_jump_drive(hull_tons, drawn_code, 10_000.0)
            assert hull_tons in DRIVE_PERFORMANCE[result]
            assert DRIVE_PERFORMANCE[result][hull_tons] <= ratings[hull_tons]


# T038: C3 and C4 swept over every hull, every legal drawn code and a spread of
# budgets, matching the coverage C1/C2 (above) and C5/C6 (below) already have.
# Postconditions C1-C8 are the acceptance criteria for this function's tests;
# C3 and C4 alone were still example-driven.

_FIT_SWEEP_BUDGETS = (0.0, 1.0, 5.0, 20.0, 55.0, 72.0, 100.0, 200.0, 400.0, 600.0, 10_000.0)


def test_fit_jump_drive_c3_is_the_lightest_at_its_rating_over_every_hull_and_budget():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        for drawn_code in legal:
            for budget in _FIT_SWEEP_BUDGETS:
                result = _fit_jump_drive(hull_tons, drawn_code, budget)
                result_rating = DRIVE_PERFORMANCE[result][hull_tons]
                result_tons = DRIVE_COSTS[result].jump_tons
                for code in legal:
                    if DRIVE_PERFORMANCE[code][hull_tons] == result_rating:
                        assert DRIVE_COSTS[code].jump_tons >= result_tons


def test_fit_jump_drive_c4_highest_affordable_rating_wins_over_every_hull_and_budget():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        lowest_rating = min(DRIVE_PERFORMANCE[code][hull_tons] for code in legal)
        for drawn_code in legal:
            ceiling = DRIVE_PERFORMANCE[drawn_code][hull_tons]
            for budget in _FIT_SWEEP_BUDGETS:
                result = _fit_jump_drive(hull_tons, drawn_code, budget)
                result_rating = DRIVE_PERFORMANCE[result][hull_tons]
                affordable = [
                    DRIVE_PERFORMANCE[code][hull_tons]
                    for code in legal
                    if DRIVE_PERFORMANCE[code][hull_tons] <= ceiling
                    and DRIVE_COSTS[code].jump_tons
                    + 0.1 * hull_tons * DRIVE_PERFORMANCE[code][hull_tons]
                    <= budget
                ]
                if affordable:
                    assert result_rating == max(affordable)
                    assert (
                        DRIVE_COSTS[result].jump_tons + 0.1 * hull_tons * result_rating <= budget
                    )
                else:
                    assert result_rating == lowest_rating


# T007: the FR-014 starved-hull fallback (contract C5, C6), tested against the
# helper directly since no seed can reach it through `generate_ship`.


def test_fit_jump_drive_c5_starved_hull_falls_back_to_the_lowest_rated_legal_drive():
    from cetools.engine.ships.generator import _fit_jump_drive

    assert _fit_jump_drive(100, "A", 5.0) == "A"


def test_fit_jump_drive_c5_zero_budget_falls_back_to_the_lightest_lowest_rated_drive():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        drawn_code = max(legal, key=lambda code: DRIVE_PERFORMANCE[code][hull_tons])

        result = _fit_jump_drive(hull_tons, drawn_code, 0.0)

        lowest_rating = min(DRIVE_PERFORMANCE[code][hull_tons] for code in legal)
        lightest_at_lowest = min(
            (code for code in legal if DRIVE_PERFORMANCE[code][hull_tons] == lowest_rating),
            key=lambda code: DRIVE_COSTS[code].jump_tons,
        )
        assert result == lightest_at_lowest


def test_fit_jump_drive_c6_never_raises_for_any_input_satisfying_the_preconditions():
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        for drawn_code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            for budget in (0.0, 1.0, 50.0, 10_000.0):
                _fit_jump_drive(hull_tons, drawn_code, budget)


# --- Phase 3, User Story 1: every generated starship can make at least one
# jump (FR-001..FR-006, SC-001, SC-002, SC-003, SC-007). T010-T013 were written
# and confirmed red before T014 reordered `generate_ship`'s allocation.


def _fr014_budget_tons(ship) -> float:
    """Recompute the mandatory-systems tonnage budget from a *finished* ship's
    own hull, maneuver drive and power plant (FR-014), so the FR-014
    classification below depends on nothing internal to the generator."""
    from cetools.engine.ships.generator import _bridge_tons

    maneuver_tons = DRIVE_COSTS[ship.design.maneuver_code].maneuver_tons
    power_tons = DRIVE_COSTS[ship.design.power_code].power_tons
    power_fuel_tons = (power_tons // 3) * 2
    bridge_tons = _bridge_tons(ship.hull_tons)
    return ship.hull_tons - (maneuver_tons + power_tons + bridge_tons + power_fuel_tons)


def _is_fr014_starved_hull_ship(ship) -> bool:
    """A ship is an FR-014 ship exactly when its jump fuel falls short of one
    complete jump at its installed rating *and* no drive legal for its hull
    could have been fuelled for one complete jump within its own tonnage
    budget (FR-014) — both halves recomputable from the finished
    ship rather than from generator internals."""
    if ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating:
        return False
    budget = _fr014_budget_tons(ship)
    legal = [c for c, ratings in DRIVE_PERFORMANCE.items() if ship.hull_tons in ratings]
    return not any(
        DRIVE_COSTS[c].jump_tons + 0.1 * ship.hull_tons * DRIVE_PERFORMANCE[c][ship.hull_tons]
        <= budget
        for c in legal
    )


def test_sc001_sc002_every_generated_starship_carries_fuel_for_one_full_jump():
    starved = 0
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        if _is_fr014_starved_hull_ship(ship):
            starved += 1
            continue
        assert ship.jump_fuel >= 0.1 * ship.hull_tons * ship.jump_rating
        assert ship.assumed_jump_distance == ship.jump_rating
    assert starved == 0


def test_us1_as1_a_100_ton_hull_with_maneuver_a_and_power_c_mounts_jump_b_at_jump_4():
    # Overview scenario / contracts worked example 4: 100/C/72 -> B (Jump-4).
    # 72 tons remain for the jump drive once the 10-ton bridge, 2-ton maneuver
    # drive, 10-ton power plant and 6 tons of power-plant fuel are deducted.
    from cetools.engine.ships.generator import _codes_valid_for_hull

    hull_tons = 100
    valid = _codes_valid_for_hull(hull_tons)
    jump_index = valid.index("C")
    maneuver_index = valid.index("A")
    required = max(DRIVE_PERFORMANCE["C"][hull_tons], DRIVE_PERFORMANCE["A"][hull_tons])
    power_candidates = [c for c in valid if DRIVE_PERFORMANCE[c][hull_tons] >= required]
    power_index = power_candidates.index("C")

    rolls = ScriptedRolls(
        choices={
            RollName.SHIP_JUMP_CODE: jump_index,
            RollName.SHIP_MANEUVER_CODE: maneuver_index,
            RollName.SHIP_POWER_CODE: power_index,
        }
    )
    ship = generate_ship(rolls, constraints=DesignConstraints(hull_tons=hull_tons)).ship

    assert ship.design.jump_code == "B"
    assert ship.jump_rating == 4
    assert ship.assumed_jump_distance == 4
    assert ship.jump_fuel == pytest.approx(40.0)


def test_sc007_ships_already_fully_fuelled_before_the_change_keep_their_rating():
    with open(_PRE_CHANGE_SWEEP_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)["standard"]

    checked = 0
    for seed_text, before in baseline.items():
        if before["assumed_jump_distance"] != before["jump_rating"]:
            continue
        seed = int(seed_text)
        ship = generate_ship(RandomRolls.seeded(seed)).ship

        assert ship.hull_tons == before["hull_tons"]
        assert ship.jump_rating == before["jump_rating"]
        assert ship.design.maneuver_code == before["maneuver_code"]
        assert ship.design.power_code == before["power_code"]
        if ship.design.jump_code != before["jump_code"]:
            before_tons = DRIVE_COSTS[before["jump_code"]].jump_tons
            after_tons = DRIVE_COSTS[ship.design.jump_code].jump_tons
            assert after_tons < before_tons
        checked += 1
    assert checked > 0


def test_sc003_allocated_tonnage_never_overruns_the_hull():
    # FR-013's other half — "passes exactly the same validation a
    # caller-supplied design must pass" — needs no separate assertion here:
    # `generate_ship` returns `build_ship(design)`, so a sweep that completes
    # without raising has already run every generated design through the
    # sole validation authority.
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        assert ship.cargo_tons >= 0
        assert ship.tonnage_used <= ship.hull_tons


# --- Phase 5, User Story 3: determinism, small craft and authored designs
# stay predictable (FR-009..FR-012, SC-005, SC-006, SC-008, SC-009).


def test_sc006_generation_is_deterministic_on_every_path():
    for seed in range(2000):
        assert generate_ship(RandomRolls.seeded(seed)) == generate_ship(RandomRolls.seeded(seed))
        assert generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT) == generate_ship(
            RandomRolls.seeded(seed), constraints=_SMALL_CRAFT
        )
        assert generate_ship(
            RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400)
        ) == generate_ship(RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=400))


def test_sc005_small_craft_output_is_unchanged_from_before_the_change():
    with open(_PRE_CHANGE_SWEEP_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)["small_craft"]

    for seed_text, expected_toml in baseline.items():
        seed = int(seed_text)
        ship = generate_ship(RandomRolls.seeded(seed), constraints=_SMALL_CRAFT).ship
        assert dump_design(ship.design) == expected_toml


def test_sc009_hull_size_is_always_honoured():
    for hull_tons in sorted(HULLS):
        for seed in range(10):
            ship = generate_ship(
                RandomRolls.seeded(seed), constraints=DesignConstraints(hull_tons=hull_tons)
            ).ship
            assert ship.hull_tons == hull_tons


class RecordingRolls:
    """Wraps another `Rolls` and records every `RollName` drawn, in order.

    Serves one test (SC-008's draw-order guard) and no production caller, so
    it lives here rather than in `engine/rolls.py`."""

    def __init__(self, wrapped: Rolls) -> None:
        self._wrapped = wrapped
        self.drawn: list[RollName] = []

    def check(self, dm: int, target: int, name: RollName) -> bool:
        self.drawn.append(name)
        return self._wrapped.check(dm, target, name)

    def two_d6(self, name: RollName) -> int:
        self.drawn.append(name)
        return self._wrapped.two_d6(name)

    def d6(self, name: RollName) -> int:
        self.drawn.append(name)
        return self._wrapped.d6(name)

    def choose(self, items, name: RollName):
        self.drawn.append(name)
        return self._wrapped.choose(items, name)


def test_sc008_ship_name_is_the_final_draw_and_is_drawn_exactly_once_on_both_paths():
    for seed in range(50):
        for hull_class in HullClass:
            recorder = RecordingRolls(RandomRolls.seeded(seed))
            generate_ship(recorder, constraints=DesignConstraints(hull_class=hull_class))
            assert recorder.drawn[-1] == RollName.SHIP_NAME
            assert recorder.drawn.count(RollName.SHIP_NAME) == 1


def test_a_pinned_hull_tonnage_draws_no_dice_on_either_path():
    """Pinning spends an answer, not a roll (ADR-0001).

    `RecordingRolls` is the only way to see this: the ship alone cannot say
    whether the hull was drawn and discarded or never drawn at all, and the
    difference is exactly what keeps the pinned baseline meaningful.
    """
    for seed in range(20):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder, constraints=DesignConstraints(hull_tons=400))
        assert RollName.SHIP_HULL_SIZE not in recorder.drawn

        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(
            recorder,
            constraints=DesignConstraints(hull_class=HullClass.SMALL_CRAFT, hull_tons=40),
        )
        assert RollName.SHIP_HULL_SIZE not in recorder.drawn


def test_an_unpinned_hull_tonnage_is_drawn_exactly_once_on_either_path():
    """The other half: without a pin the draw is still made, so the test above
    cannot pass by the roll having been removed altogether."""
    for hull_class in HullClass:
        recorder = RecordingRolls(RandomRolls.seeded(3))
        generate_ship(recorder, constraints=DesignConstraints(hull_class=hull_class))
        assert recorder.drawn.count(RollName.SHIP_HULL_SIZE) == 1


def test_sc008_drive_codes_are_drawn_jump_then_maneuver_then_power():
    for seed in range(50):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder)
        jump_at = recorder.drawn.index(RollName.SHIP_JUMP_CODE)
        maneuver_at = recorder.drawn.index(RollName.SHIP_MANEUVER_CODE)
        power_at = recorder.drawn.index(RollName.SHIP_POWER_CODE)
        assert jump_at < maneuver_at < power_at

    for seed in range(50):
        recorder = RecordingRolls(RandomRolls.seeded(seed))
        generate_ship(recorder, constraints=_SMALL_CRAFT)
        assert RollName.SHIP_JUMP_CODE not in recorder.drawn
        maneuver_at = recorder.drawn.index(RollName.SHIP_MANEUVER_CODE)
        power_at = recorder.drawn.index(RollName.SHIP_POWER_CODE)
        assert maneuver_at < power_at


def test_sc008_re_pinned_baseline_pins_seeded_designs_for_future_features():
    # A blunt regression net for *future* features, not this one — the data
    # was generated from this feature's own post-change generator (T027).
    with open(_POST_CHANGE_BASELINE_PATH, encoding="utf-8") as handle:
        baseline = json.load(handle)

    for key, expected_toml in baseline.items():
        path, seed_text = key.split(":")
        seed = int(seed_text)
        ship = generate_ship(
            RandomRolls.seeded(seed),
            constraints=_SMALL_CRAFT if path == "small_craft" else UNCONSTRAINED,
        ).ship
        assert dump_design(ship.design) == expected_toml, f"{key}: moved off the pinned baseline"


# --- Phase 7 Convergence: pins for properties that already held but were
# asserted nowhere in the suite. Neither test drove a source change.


def _lightest_code_at(hull_tons: int, rating: int) -> str:
    return min(
        (code for code, ratings in DRIVE_PERFORMANCE.items() if ratings.get(hull_tons) == rating),
        key=lambda code: DRIVE_COSTS[code].jump_tons,
    )


def test_g4_every_generated_starship_mounts_the_lightest_drive_at_its_rating():
    """T036, FR-004 and contract G4.

    FR-004 is a standing rule applied to every generated starship, but nothing
    asserted it at the `generate_ship` level:
    `test_sc007_ships_already_fully_fuelled_before_the_change_keep_their_rating`
    checks only that a *changed* letter is strictly lighter, and the C3 tests
    cover `_fit_jump_drive` rather than the wiring. Before this test, a
    regression reinstating a heavier same-rating drive passed `uv run pytest`
    and the pre-push gate, caught only by the manual survey script.
    """
    starved = 0
    for seed in range(2000):
        ship = generate_ship(RandomRolls.seeded(seed)).ship
        # G4 binds even on an FR-014 ship: the fallback defers to FR-004 for
        # the choice among drives sharing the lowest rating, so this is
        # asserted before the starved-hull classification, not after it.
        assert ship.design.jump_code == _lightest_code_at(ship.hull_tons, ship.jump_rating)
        if _is_fr014_starved_hull_ship(ship):
            starved += 1
    assert starved == 0


def test_fr003_affordability_and_the_generators_fuel_arithmetic_agree_at_the_boundary():
    """T037, "a property to pin, not one to assume".

    `_fit_jump_drive` admits a rating when `jump_tons + 0.1 * hull * rating`
    fits the budget; `generate_ship` then decides how many jumps the leftover
    tonnage actually buys with `math.floor(remaining / (0.1 * hull))`. The two
    must agree at the tightest budget the first accepts, or the search could
    select a rating the allocation then refuses to fund. They do for every hull
    and rating in the current tables, but the agreement rests on floating-point
    behaviour rather than on anything the SRD guarantees.
    """
    for hull_tons in HULLS:
        for code, ratings in DRIVE_PERFORMANCE.items():
            if hull_tons not in ratings:
                continue
            rating = ratings[hull_tons]
            jump_tons = DRIVE_COSTS[code].jump_tons
            budget = jump_tons + 0.1 * hull_tons * rating  # exactly affordable
            remaining = max(0.0, budget - jump_tons)
            assert math.floor(remaining / (0.1 * hull_tons)) >= rating


# --- Phase 8 Convergence: FR-014's FR-013 clause ---


def test_fr014_a_starved_hull_design_still_builds_within_its_hull():
    """T040, FR-014's "MUST still satisfy FR-013" clause and contract G5.

    For a starved hull the contract drops every guarantee but G4 and G5, and
    G5 — the design still fits — was asserted nowhere: the C5 and C6 tests
    check only which *letter* `_fit_jump_drive` returns, never that a design
    built around that letter fits its hull.

    A *genuinely* starved hull cannot be reached, and not merely through
    `generate_ship`: the fallback drive is the lowest-rated legal one, and on
    every tabulated hull the mandatory systems leave room to fuel it for a full
    jump (reconfirmed here — 0 of 18 hulls fall short). So
    there is no configuration of real tables under which FR-014's fuel shortfall
    occurs, and a test that merely rebuilt the fallback allocation would quietly
    assert an ordinary fully-fuelled ship.

    What is pinned instead is the *shape* FR-014 permits: the fallback drive
    carrying "whatever fuel fits", swept across every jump distance from 0 (the
    degenerate zero-jump ship FR-014 explicitly allows) up to its full rating.
    Every one of those designs must build and fit inside its hull.
    """
    from cetools.engine.ships.generator import _fit_jump_drive

    for hull_tons in HULLS:
        legal = [code for code, ratings in DRIVE_PERFORMANCE.items() if hull_tons in ratings]
        top = max(legal, key=lambda code: DRIVE_PERFORMANCE[code][hull_tons])
        fallback = _fit_jump_drive(hull_tons, top, 0.0)
        rating = DRIVE_PERFORMANCE[fallback][hull_tons]

        # The heaviest power plant the drive's rating floor admits, so the
        # mandatory systems take as much of the hull as the rules allow.
        maneuver = min(legal, key=lambda code: DRIVE_COSTS[code].maneuver_tons)
        required = max(rating, DRIVE_PERFORMANCE[maneuver][hull_tons])
        power = max(
            (code for code in legal if DRIVE_PERFORMANCE[code][hull_tons] >= required),
            key=lambda code: DRIVE_COSTS[code].power_tons,
        )

        for distance in range(0, rating + 1):
            ship = build_ship(
                ShipDesign(
                    hull_tons=hull_tons,
                    jump_code=fallback,
                    maneuver_code=maneuver,
                    power_code=power,
                    jump_distance=distance,
                    power_weeks=2,
                )
            )

            assert ship.tonnage_used <= ship.hull_tons  # FR-013 / G5
            assert ship.cargo_tons >= 0
            assert ship.assumed_jump_distance == distance  # never silently corrected
            assert ship.jump_fuel == pytest.approx(0.1 * hull_tons * distance)


# --- SC-007: a single build or generation is effectively instant ---


def test_a_single_build_completes_in_under_a_tenth_of_a_second():
    design = load_design("tests/data/ships/free-trader.toml")
    build_ship(design)  # warm up imports before timing

    start = time.perf_counter()
    build_ship(design)
    assert time.perf_counter() - start < 0.1


def test_a_single_generation_completes_in_under_a_tenth_of_a_second():
    generate_ship(RandomRolls.seeded(1))  # warm up imports before timing

    start = time.perf_counter()
    generate_ship(RandomRolls.seeded(2))
    assert time.perf_counter() - start < 0.1
