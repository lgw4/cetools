import pytest

from cetools.engine.models import (
    Benefit,
    Character,
    GenerationFailure,
    MishapOutcome,
    boost,
    characteristic_modifier,
)
from cetools.engine.pseudohex import encode_upp

MODIFIER_TABLE = [
    (0, -2),
    (1, -2),
    (2, -2),
    (3, -1),
    (4, -1),
    (5, -1),
    (6, 0),
    (7, 0),
    (8, 0),
    (9, 1),
    (10, 1),
    (11, 1),
    (12, 2),
    (13, 2),
    (14, 2),
    (15, 3),
    (16, 3),
    (17, 3),
    (18, 4),
    (19, 4),
    (20, 4),
    (21, 5),
    (22, 5),
    (23, 5),
    (24, 6),
    (25, 6),
    (26, 6),
    (27, 7),
    (28, 7),
    (29, 7),
    (30, 8),
    (31, 8),
    (32, 8),
    (33, 9),
]


def test_characteristic_modifier_all_bands() -> None:
    for score, expected_mod in MODIFIER_TABLE:
        result = characteristic_modifier(score)
        assert (
            result == expected_mod
        ), f"characteristic_modifier({score}) expected {expected_mod}, got {result}"


def test_characteristic_modifier_above_33() -> None:
    assert characteristic_modifier(34) == 9
    assert characteristic_modifier(100) == 9


def test_characteristic_modifier_floor_is_minus_2() -> None:
    assert characteristic_modifier(0) == -2
    assert characteristic_modifier(2) == -2


def test_encode_upp_produces_6_char_string() -> None:
    scores = {
        "Strength": 7,
        "Dexterity": 10,
        "Endurance": 6,
        "Intelligence": 11,
        "Education": 8,
        "Social Standing": 5,
    }
    upp = encode_upp(scores)
    assert len(upp) == 6
    assert upp == "7A6B85"


def test_generation_failure_exit_code_is_1() -> None:
    failure = GenerationFailure(reason="test")
    assert failure.exit_code == 1


def test_generation_failure_stores_reason() -> None:
    failure = GenerationFailure(reason="Navy enlistment failed")
    assert failure.reason == "Navy enlistment failed"


# T002 — Character.drafted field
def test_character_drafted_defaults_to_false() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
    )
    assert char.drafted is False
    assert isinstance(char.drafted, bool)


def test_character_drafted_can_be_set_true() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        drafted=True,
    )
    assert char.drafted is True


# T002 — Character.name field
def test_character_name_field_is_stored() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        name="Jane Doe",
    )
    assert char.name == "Jane Doe"


def test_benefit_cash_requires_cash_amount() -> None:
    with pytest.raises(ValueError, match="cash_amount"):
        Benefit(kind="cash")


def test_benefit_material_requires_material_name() -> None:
    with pytest.raises(ValueError, match="material_name"):
        Benefit(kind="material")


def test_benefit_cash_with_amount_is_valid() -> None:
    benefit = Benefit(kind="cash", cash_amount=5000)
    assert benefit.cash_amount == 5000


def test_benefit_material_with_name_is_valid() -> None:
    benefit = Benefit(kind="material", material_name="Blade")
    assert benefit.material_name == "Blade"


# T002 — MishapOutcome dataclass
def test_mishap_outcome_stores_all_fields() -> None:
    outcome = MishapOutcome(
        roll=1,
        discharge_type="none",
        imprisoned=False,
        injury_reductions={"Strength": 3},
        injury_crisis=False,
    )
    assert outcome.roll == 1
    assert outcome.discharge_type == "none"
    assert outcome.imprisoned is False
    assert outcome.injury_reductions == {"Strength": 3}
    assert outcome.injury_crisis is False


# T002 — Character.mishap / Character.debt fields
def test_character_mishap_and_debt_default() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
    )
    assert char.mishap is None
    assert char.debt == 0


def test_character_mishap_and_debt_can_be_set() -> None:
    outcome = MishapOutcome(
        roll=3,
        discharge_type="honorable",
        imprisoned=False,
        injury_reductions={},
        injury_crisis=False,
    )
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        mishap=outcome,
        debt=15000,
    )
    assert char.mishap is outcome
    assert char.debt == 15000


def test_benefit_material_quantity_defaults_none() -> None:
    b = Benefit(kind="material", material_name="Weapon")
    assert b.material_quantity is None


def test_benefit_carries_material_quantity() -> None:
    b = Benefit(kind="material", material_name="Ship Shares", material_quantity=4)
    assert b.material_quantity == 4


def test_character_psionics_default_to_non_psionic() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
    )
    assert char.psi_strength == 0
    assert char.talents == {}


def test_character_psionics_can_be_set() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career="Scout",
        rank=0,
        rank_title="Scout",
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        psi_strength=6,
        talents={"Telepathy": 0},
    )
    assert char.psi_strength == 6
    assert char.talents == {"Telepathy": 0}


# --- boost: the "+1 X" rule ---
# Shared by Skills and Training entries and by material benefits, so it lives
# with the other characteristics rules rather than in either caller.


def test_boost_applies_a_stat_boost() -> None:
    assert boost({"Strength": 7}, "+1 Str")["Strength"] == 8


def test_boost_returns_none_for_a_plain_skill_name() -> None:
    assert boost({"Strength": 7}, "Melee Combat") is None


def test_boost_recognises_an_unknown_abbreviation_without_applying_it() -> None:
    # Still a boost, so it is never granted as a skill named "+1 Xyz" — it just
    # has nothing to apply.
    assert boost({"Strength": 7}, "+1 Xyz") == {"Strength": 7}


def test_boost_caps_a_characteristic_at_33() -> None:
    assert boost({"Strength": 33}, "+1 Str")["Strength"] == 33


def test_boost_does_not_mutate_its_argument() -> None:
    characteristics = {"Strength": 7}
    boost(characteristics, "+1 Str")
    assert characteristics == {"Strength": 7}
