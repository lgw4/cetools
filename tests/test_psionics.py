from cetools.engine.psionics import roll_psionics
from conftest import SequenceRoller


def test_psi_strength_is_two_d6_minus_terms() -> None:
    # First 2D6 roll (9) minus 3 terms = 6.
    psi, _ = roll_psionics(terms_served=3, roller=SequenceRoller([9], default=2))
    assert psi == 6


def test_psi_strength_floors_at_zero_and_skips_training() -> None:
    # 7 - 10 = -3, floored to 0. The high follow-up values (12) must never be
    # consumed, proving no talent checks are attempted when Psi < 1.
    psi, talents = roll_psionics(terms_served=10, roller=SequenceRoller([7, 12, 12, 12, 12, 12]))
    assert psi == 0
    assert talents == {}


def test_training_order_and_cumulative_penalty() -> None:
    # Psi roll 7, terms 0 -> Psi 7 (PsiDM 0). Then five talent checks each roll 8:
    #   Telepathy(+4, attempt 0): 8+4-0=12 >= 8  -> learned
    #   Clairvoyance(+3, attempt 1): 8+3-1=10 >= 8 -> learned
    #   Telekinesis(+2, attempt 2): 8+2-2=8 >= 8   -> learned
    #   Awareness(+1, attempt 3): 8+1-3=6 < 8      -> not learned
    #   Teleportation(+0, attempt 4): 8+0-4=4 < 8  -> not learned
    psi, talents = roll_psionics(terms_served=0, roller=SequenceRoller([7, 8, 8, 8, 8, 8]))
    assert psi == 7
    assert talents == {"Telepathy": 0, "Clairvoyance": 0, "Telekinesis": 0}


def test_learned_talents_are_level_zero() -> None:
    _, talents = roll_psionics(terms_served=0, roller=SequenceRoller([7, 8, 8, 8, 8, 8]))
    assert all(level == 0 for level in talents.values())
