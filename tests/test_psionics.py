from cetools.engine.psionics import roll_psionics
from cetools.engine.rolls import RollName, ScriptedRolls


def test_psi_strength_is_two_d6_minus_terms() -> None:
    # The gate passes, so the Psi roll (9) applies: 9 - 3 terms = 6.
    rolls = ScriptedRolls(
        checks={RollName.PSI_GATE: True},
        two_d6={RollName.PSI_STRENGTH: 9},
    )
    psi, _ = roll_psionics(terms_served=3, rolls=rolls)
    assert psi == 6


def test_psi_strength_floors_at_zero_and_skips_training() -> None:
    # The gate passes and the Psi roll is 7, but 7 - 10 terms floors to 0. Talent
    # checks are scripted to succeed, so an empty talent dict proves none were
    # attempted: training is skipped entirely when Psi < 1.
    rolls = ScriptedRolls(
        checks={RollName.PSI_GATE: True, RollName.PSI_TALENT: True},
        two_d6={RollName.PSI_STRENGTH: 7},
    )
    psi, talents = roll_psionics(terms_served=10, rolls=rolls)
    assert psi == 0
    assert talents == {}


def test_training_order_and_cumulative_penalty() -> None:
    # Talents are attempted highest-DM-first, so the scripted outcomes land in
    # that order: Telepathy, Clairvoyance and Telekinesis pass; Awareness and
    # Teleportation fail, as the cumulative per-attempt penalty eventually will.
    # The mapping of outcome to talent name is what this test pins down.
    rolls = ScriptedRolls(
        checks={
            RollName.PSI_GATE: True,
            RollName.PSI_TALENT: [True, True, True, False, False],
        },
        two_d6={RollName.PSI_STRENGTH: 7},
    )
    psi, talents = roll_psionics(terms_served=0, rolls=rolls)
    assert psi == 7
    assert talents == {"Telepathy": 0, "Clairvoyance": 0, "Telekinesis": 0}


def test_learned_talents_are_level_zero() -> None:
    # The gate passes, Psi is 7, and the first three talent checks succeed;
    # every talent that is learned comes back at level 0.
    rolls = ScriptedRolls(
        checks={
            RollName.PSI_GATE: True,
            RollName.PSI_TALENT: [True, True, True, False, False],
        },
        two_d6={RollName.PSI_STRENGTH: 7},
    )
    _, talents = roll_psionics(terms_served=0, rolls=rolls)
    assert all(level == 0 for level in talents.values())


def test_eligibility_gate_failure_skips_all_rolls() -> None:
    # The gate fails, so nothing downstream runs. The Psi roll is scripted high
    # (12) and every talent check would succeed; Psi 0 and no talents prove the
    # gate short-circuits before either is reached.
    rolls = ScriptedRolls(
        checks={RollName.PSI_GATE: False, RollName.PSI_TALENT: True},
        two_d6={RollName.PSI_STRENGTH: 12},
    )
    psi, talents = roll_psionics(terms_served=0, rolls=rolls)
    assert psi == 0
    assert talents == {}


def test_eligibility_gate_boundary_eleven_passes() -> None:
    # Minimal pair with test_eligibility_gate_boundary_ten_fails: same terms (3)
    # and same Psi roll (12); the gate passes, so the Psi roll applies: 12 - 3 = 9.
    rolls = ScriptedRolls(
        checks={RollName.PSI_GATE: True},
        two_d6={RollName.PSI_STRENGTH: 12},
    )
    psi, _ = roll_psionics(terms_served=3, rolls=rolls)
    assert psi == 9


def test_eligibility_gate_boundary_ten_fails() -> None:
    # The gate fails even though the Psi roll (12) would otherwise give a high Psi.
    rolls = ScriptedRolls(
        checks={RollName.PSI_GATE: False},
        two_d6={RollName.PSI_STRENGTH: 12},
    )
    psi, talents = roll_psionics(terms_served=3, rolls=rolls)
    assert psi == 0
    assert talents == {}
