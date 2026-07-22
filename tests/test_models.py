from cetools.engine.careers.scout import SCOUT_CAREER
from cetools.engine.models import (
    Benefit,
    Cash,
    Character,
    GenerationFailure,
    Item,
    MishapOutcome,
    Shares,
    StatBoost,
    apply_stat_boost,
    characteristic_modifier,
    parse_stat_boost,
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


# T002—Character.drafted field
def test_character_drafted_defaults_to_false() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career=SCOUT_CAREER,
        rank=0,
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
        career=SCOUT_CAREER,
        rank=0,
        terms_served=1,
        name="Jane Doe",
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        drafted=True,
    )
    assert char.drafted is True


# T002—Character.name field
def test_character_name_field_is_stored() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career=SCOUT_CAREER,
        rank=0,
        terms_served=1,
        skills={},
        benefits=[],
        pension=None,
        terms=[],
        name="Jane Doe",
    )
    assert char.name == "Jane Doe"


# The old Benefit had a `kind` and three optional fields, so it needed
# __post_init__ to reject "cash with no amount" and "material with no name". Each
# variant now carries exactly its own fields: those states are unconstructable, so
# the tests that asserted their ValueErrors are gone rather than weakened.


def test_cash_carries_an_amount() -> None:
    assert Cash(amount=5000).amount == 5000


def test_item_carries_a_name() -> None:
    assert Item(name="Blade").name == "Blade"


# T002—MishapOutcome dataclass
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


# T002—Character.mishap / Character.debt fields
def test_character_mishap_and_debt_default() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career=SCOUT_CAREER,
        rank=0,
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
        career=SCOUT_CAREER,
        rank=0,
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


def test_shares_carry_a_quantity() -> None:
    assert Shares(quantity=4).quantity == 4


def test_a_benefit_is_one_of_the_four_variants() -> None:
    # Ship shares used to be told apart from other material benefits by
    # `material_quantity is not None`—a sentinel. Now each benefit simply is
    # what it is.
    for benefit in (Cash(1000), StatBoost("Edu"), Item("Weapon"), Shares(4)):
        assert isinstance(benefit, Benefit)


def test_character_psionics_default_to_non_psionic() -> None:
    char = Character(
        characteristics={},
        upp="000000",
        age=18,
        career=SCOUT_CAREER,
        rank=0,
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
        career=SCOUT_CAREER,
        rank=0,
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


# --- the "+1 X" notation: parsed in one place, applied in one place ---
# Career skill tables and material benefit tables both use it, so both come
# through here and neither knows what the prefix means.


def test_parse_reads_a_stat_boost_entry() -> None:
    assert parse_stat_boost("+1 Str") == StatBoost(label="Str")


def test_parse_returns_none_for_a_plain_skill_name() -> None:
    assert parse_stat_boost("Melee Combat") is None


def test_parse_accepts_an_unknown_abbreviation() -> None:
    # Still a boost, so it is never granted as a skill named "+1 Xyz"—it just
    # has nothing to apply.
    assert parse_stat_boost("+1 Xyz") == StatBoost(label="Xyz")


def test_apply_boosts_the_characteristic() -> None:
    assert apply_stat_boost({"Strength": 7}, StatBoost("Str"))["Strength"] == 8


def test_apply_ignores_an_unknown_abbreviation() -> None:
    assert apply_stat_boost({"Strength": 7}, StatBoost("Xyz")) == {"Strength": 7}


def test_apply_caps_a_characteristic_at_33() -> None:
    assert apply_stat_boost({"Strength": 33}, StatBoost("Str"))["Strength"] == 33


def test_apply_does_not_mutate_its_argument() -> None:
    characteristics = {"Strength": 7}
    apply_stat_boost(characteristics, StatBoost("Str"))
    assert characteristics == {"Strength": 7}
