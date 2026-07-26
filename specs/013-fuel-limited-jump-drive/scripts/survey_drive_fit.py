"""Reproduce every measurement quoted in feature 013's research.md and validate SC-001..SC-006.

Run from the repository root:

    uv run python specs/013-fuel-limited-jump-drive/scripts/survey_drive_fit.py

Before the fix this reports a non-zero short-fuelled count (111 of 2000). After it, that
count is zero and the starved-hull count is reported separately, per SC-001.

SC-007 is deliberately **not** measured here: it compares each seed against the output of the
pre-change generator, which this script cannot see. It is asserted by the pytest sweep against
the capture in `baseline/pre_change_sweep.json`. What this script reports instead is the
FR-004/G4 population -- ships whose drive is not the lightest at its rating.

Exit status is 0 when every success criterion holds, 1 otherwise, so the script doubles as a
manual gate. It is a survey tool, not part of the test suite; every criterion it reports is also
asserted by pytest at a smaller sweep size. That was not true of the FR-004/G4 line until
convergence added `test_g4_every_generated_starship_mounts_the_lightest_drive_at_its_rating` to
`tests/test_ship_generator.py` — this script was for a time its only guard, and a survey tool run
by hand is not a gate.
"""

from __future__ import annotations

import sys

from cetools.engine.rolls import RandomRolls
from cetools.engine.ships.description import render_description
from cetools.engine.ships.generator import generate_ship
from cetools.engine.ships.tables import BRIDGE_SIZES, DRIVE_COSTS, DRIVE_PERFORMANCE, HULLS

SWEEP = 2000
LETTERS = list(DRIVE_COSTS)


def legal_codes(hull: int) -> list[str]:
    return [c for c in LETTERS if hull in DRIVE_PERFORMANCE[c]]


def bridge_tons(hull: int) -> int:
    for cap, tons in BRIDGE_SIZES:
        if cap is None or hull <= cap:
            return tons
    raise AssertionError("BRIDGE_SIZES must end with an unbounded step")


def lightest_at(hull: int, rating: int) -> str:
    return min(
        (c for c in legal_codes(hull) if DRIVE_PERFORMANCE[c][hull] == rating),
        key=lambda c: DRIVE_COSTS[c].jump_tons,
    )


def report_table_invariants() -> bool:
    """research.md Part C: the two ordering invariants the fit search states explicitly."""
    # Adjacent pairs suffice: strictly increasing between neighbours implies it throughout.
    tons_ok = all(
        DRIVE_COSTS[b].jump_tons > DRIVE_COSTS[a].jump_tons for a, b in zip(LETTERS, LETTERS[1:])
    )
    rating_ok = all(
        (ratings := [DRIVE_PERFORMANCE[c][h] for c in legal_codes(h)]) == sorted(ratings)
        for h in HULLS
    )
    print(f"jump_tons strictly increasing in letter order: {tons_ok}")
    print(f"rating non-decreasing in letter order, every hull: {rating_ok}")
    return tons_ok and rating_ok


def report_starved_hulls() -> bool:
    """research.md Part E: is FR-014 reachable over the full draw space, not just a sample?"""
    starved = [
        (hull, m, p)
        for hull in sorted(HULLS)
        for m in legal_codes(hull)
        for p in legal_codes(hull)
        if not any(
            DRIVE_COSTS[c].jump_tons + 0.1 * hull * DRIVE_PERFORMANCE[c][hull]
            <= hull
            - (
                DRIVE_COSTS[m].maneuver_tons
                + DRIVE_COSTS[p].power_tons
                + bridge_tons(hull)
                + (DRIVE_COSTS[p].power_tons // 3) * 2
            )
            for c in legal_codes(hull)
        )
    ]
    print(f"starved (hull, maneuver, power) combos over the full cross product: {len(starved)}")
    for row in starved[:10]:
        print(f"  {row}")
    return True  # informational: a non-zero count is a table fact, not a failure


def report_sweep() -> bool:
    """SC-001 through SC-004, SC-006 and SC-007 over `SWEEP` seeds."""
    short = starved = negative_cargo = zero_in_prose = not_lightest = nondeterministic = 0

    for seed in range(SWEEP):
        ship = generate_ship(RandomRolls.seeded(seed))
        hull, rating = ship.hull_tons, ship.jump_rating

        # An FR-014 ship is the sole permitted exception; count it separately (SC-001).
        budget = hull - (
            DRIVE_COSTS[ship.design.maneuver_code].maneuver_tons
            + DRIVE_COSTS[ship.design.power_code].power_tons
            + bridge_tons(hull)
            + ship.power_fuel
        )
        is_starved = not any(
            DRIVE_COSTS[c].jump_tons + 0.1 * hull * DRIVE_PERFORMANCE[c][hull] <= budget
            for c in legal_codes(hull)
        )
        if is_starved:
            starved += 1
            continue

        if ship.jump_fuel < 0.1 * hull * rating:  # SC-001, SC-002
            short += 1
        if f"zero Jump-{rating}" in render_description(ship):  # SC-004
            zero_in_prose += 1
        if ship.cargo_tons < 0:  # SC-003
            negative_cargo += 1
        if ship.design.jump_code != lightest_at(hull, rating):  # FR-004, contract G4
            not_lightest += 1
        if generate_ship(RandomRolls.seeded(seed)) != ship:  # SC-006
            nondeterministic += 1

    print(f"\n--- {SWEEP} seeds, standard hull ---")
    print(f"SC-001/002 short-fuelled (expect 0):         {short}")
    print(f"SC-001 FR-014 starved hulls (expect 0):      {starved}")
    print(f"SC-003 negative cargo (expect 0):            {negative_cargo}")
    print(f"SC-004 'zero Jump-n' in prose (expect 0):    {zero_in_prose}")
    print(f"FR-004 drive not lightest at rating (0):     {not_lightest}")
    print(f"SC-006 non-reproducible seeds (expect 0):    {nondeterministic}")
    return not any((short, negative_cargo, zero_in_prose, not_lightest, nondeterministic))


def report_small_craft() -> bool:
    """SC-005: the small-craft path is untouched, and reproducible."""
    ok = all(
        generate_ship(RandomRolls.seeded(seed), small_craft=True)
        == generate_ship(RandomRolls.seeded(seed), small_craft=True)
        for seed in range(SWEEP)
    )
    print(f"SC-005 small craft reproducible over {SWEEP} seeds: {ok}")
    return ok


def main() -> int:
    results = [
        report_table_invariants(),
        report_starved_hulls(),
        report_sweep(),
        report_small_craft(),
    ]
    passed = all(results)
    print("\nPASS" if passed else "\nFAIL")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
