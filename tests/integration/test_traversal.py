"""T073 (SC-005, FR-026 through FR-028): a deterministic walk per career.

`generate_character` picks a career at random from those in force, so
proving each of the twenty-four is individually reachable — not merely that
the packaged set parses — means driving one career's own service directly
through the same primitives `_Walk.run` composes: `_qualify`,
`basic_training`, `_grant_rank_bonus`, `run_term_loop`, `muster_out_service`
(the same primitives `TestTitlePersistenceAcrossCareers` and
`TestQuantifiedBenefitDraw` already drive directly in test_generator.py),
skipping only `enter_career`'s random selection.
"""

import pytest

from cetools.dice import Roller
from cetools.generator import _Walk
from cetools.rules import load_rules

RULES = load_rules()
_SEED_LIMIT = 1000
_QUALIFYING_SCORE = 9  # a +1 DM on every throw, without guaranteeing success


def _walk_one_service(career):
    """The first seed under `_SEED_LIMIT` that qualifies into `career` and
    musters out with at least one benefit roll actually taken — a mishap
    can forfeit every roll a service would otherwise earn (FR-020), which
    this walk is not what T073 means to exercise, so such a seed is
    skipped in favor of the next.
    """
    for seed in range(_SEED_LIMIT):
        walk = _Walk(Roller(seed), RULES)
        walk.characteristics = {code: _QUALIFYING_SCORE for code in RULES.characteristics.names}
        if not walk._qualify(career, 0):
            continue
        walk.basic_training(career, is_first_career=True)
        entry_ladder = walk._entry_ladder(career)
        walk._grant_rank_bonus(career.name, 1, entry_ladder, 0)
        terms, ladder, rank, commissioned, ended, benefit_rolls, forfeit_all = walk.run_term_loop(
            career, "selected"
        )
        rolls_taken = walk.muster_out_service(
            career, terms, ladder, rank, benefit_rolls, forfeit_all
        )
        if rolls_taken < 1:
            continue
        return walk, terms, rolls_taken
    raise AssertionError(
        f"no seed under {_SEED_LIMIT} qualifies into {career.name} "
        "and completes a service with a benefit roll taken"
    )


@pytest.mark.parametrize("basename", sorted(RULES.careers))
def test_a_deterministic_walk_reaches_every_career(basename):
    career = RULES.careers[basename]
    walk, terms, rolls_taken = _walk_one_service(career)

    # Qualifies into the career, and completes at least one term.
    qualification_step = next(s for s in walk.history if s.kind == "qualification")
    assert qualification_step.throw.success
    assert terms >= 1

    # Exercises the career's own service skill table: the first-career
    # branch of `basic_training` grants every one of its rows.
    basic_training_step = next(s for s in walk.history if s.kind == "basic-training")
    assert len(basic_training_step.effects) == len(career.tables["service"].entries)

    # Exercises the rank ladder: entering a career grants its entry
    # ladder's rank 0 unconditionally (FR-007a), recorded as its own step.
    assert any(s.kind == "rank-bonus" for s in walk.history)

    # Musters out with cash and/or material benefits drawn from the
    # career's own tables (FR-026 through FR-028): at least one roll was
    # actually taken, and it left the walk holding funds, a material
    # benefit, or a characteristic adjustment from that roll.
    assert rolls_taken >= 1
    assert (
        walk.funds > 0
        or walk.benefits
        or any(
            s.kind == "benefit" and any(e.kind == "characteristic" for e in s.effects)
            for s in walk.history
        )
    )
