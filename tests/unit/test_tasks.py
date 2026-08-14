from types import MappingProxyType

import pytest

from cetools import Band, Modifier, Roller, TaskParameters, check
from cetools.errors import RulesDataError, TaskError
from cetools.provenance import Provenance
from cetools.registries import BenefitRegistry, CharacteristicRegistry, SkillRegistry
from cetools.rules import RulesData

DIFFICULTY_LADDER = {
    "Simple": 6,
    "Easy": 4,
    "Routine": 2,
    "Average": 0,
    "Difficult": -2,
    "Very Difficult": -4,
    "Formidable": -6,
}

CHARACTERISTIC_BANDS = (
    Band(minimum=0, maximum=2, dm=-2),
    Band(minimum=3, maximum=5, dm=-1),
    Band(minimum=6, maximum=8, dm=0),
    Band(minimum=9, maximum=11, dm=1),
    Band(minimum=12, maximum=14, dm=2),
    Band(minimum=15, maximum=17, dm=3),
    Band(minimum=18, maximum=20, dm=4),
    Band(minimum=21, maximum=23, dm=5),
    Band(minimum=24, maximum=26, dm=6),
    Band(minimum=27, maximum=29, dm=7),
    Band(minimum=30, maximum=32, dm=8),
    Band(minimum=33, maximum=None, dm=9),
)

_EMPTY_PROVENANCE = Provenance(version="test", files=(), ignored=())


def _parameters(**overrides):
    fields = dict(
        roll="2d6",
        target=8,
        unskilled_dm=-3,
        difficulty_dms=DIFFICULTY_LADDER,
        characteristic_bands=CHARACTERISTIC_BANDS,
    )
    fields.update(overrides)
    return TaskParameters(**fields)


def _rules(**overrides):
    """A synthetic `RulesData` wrapping `_parameters(**overrides)`, for tests
    that exercise `check`'s task-resolution logic without a data set on disk
    (contracts/library-api.md).
    """
    return RulesData(
        task_parameters=_parameters(**overrides),
        characteristics=CharacteristicRegistry(names=MappingProxyType({})),
        skills=SkillRegistry(skills=MappingProxyType({})),
        benefits=BenefitRegistry(items=()),
        careers=MappingProxyType({}),
        provenance=_EMPTY_PROVENANCE,
    )


@pytest.mark.parametrize(
    "name,expected_total",
    [
        ("Simple", 13),
        ("Easy", 11),
        ("Routine", 9),
        ("Average", 7),
        ("Difficult", 5),
        ("Very Difficult", 3),
        ("Formidable", 1),
    ],
)
def test_difficulty_ladder_steps_by_two_with_fixed_dice_and_target(name, expected_total):
    result = check(Roller(1), difficulty=name, skill=0, rules=_rules())
    assert result.faces == (2, 5)
    assert result.dice_total == 7
    assert result.target == 8
    assert result.total == expected_total


@pytest.mark.parametrize(
    "score,expected_dm",
    [
        # Both bounds of every one of the twelve bands, so the list walks the
        # whole table rather than its ends (SC-003). A boundary comparison that
        # slipped by one anywhere in the middle of the curve now fails here.
        (0, -2),
        (2, -2),
        (3, -1),
        (5, -1),
        (6, 0),
        (8, 0),
        (9, 1),
        (11, 1),
        (12, 2),
        (14, 2),
        (15, 3),
        (17, 3),
        (18, 4),
        (20, 4),
        (21, 5),
        (23, 5),
        (24, 6),
        (26, 6),
        (27, 7),
        (29, 7),
        (30, 8),
        (32, 8),
        (33, 9),
        (99, 9),
        (4000, 9),
    ],
)
def test_characteristic_bands_including_unbounded_top(score, expected_dm):
    parameters = _parameters()
    assert parameters.characteristic_dm(score) == expected_dm


def test_default_difficulty_is_the_sole_zero_modifier_rung_by_value():
    parameters = _parameters()
    assert parameters.default_difficulty() == "Average"


def test_check_with_no_difficulty_uses_default_difficulty():
    result = check(Roller(1), skill=0, rules=_rules())
    difficulty_modifier = result.modifiers[0]
    assert difficulty_modifier.label == "Difficulty (Average)"
    assert difficulty_modifier.value == 0


def test_untrained_skill_applies_unskilled_penalty():
    result = check(Roller(1), rules=_rules())
    skill_modifier = [m for m in result.modifiers if m.label in ("Unskilled",)][0]
    assert skill_modifier.label == "Unskilled"
    assert skill_modifier.value == -3


def test_skill_zero_is_trained_and_applies_nothing():
    result = check(Roller(1), skill=0, rules=_rules())
    skill_modifier = result.modifiers[-1]
    assert skill_modifier.label == "Skill 0"
    assert skill_modifier.value == 0


def test_trained_skill_applies_its_level():
    result = check(Roller(1), skill=3, rules=_rules())
    skill_modifier = result.modifiers[-1]
    assert skill_modifier.label == "Skill 3"
    assert skill_modifier.value == 3


def test_modifier_order_is_difficulty_characteristic_skill_situational():
    result = check(
        Roller(1),
        difficulty="Difficult",
        characteristic=9,
        skill=2,
        modifiers=(Modifier(label="cover", value=-2),),
        rules=_rules(),
    )
    labels = [m.label for m in result.modifiers]
    assert labels == ["Difficulty (Difficult)", "Characteristic 9", "Skill 2", "cover"]


def test_unknown_difficulty_raises_task_error_listing_valid_names():
    with pytest.raises(TaskError) as exc_info:
        check(Roller(1), difficulty="Trivial", rules=_rules())
    message = str(exc_info.value)
    for name in DIFFICULTY_LADDER:
        assert name in message


def test_negative_characteristic_raises_task_error():
    with pytest.raises(TaskError):
        check(Roller(1), characteristic=-1, rules=_rules())


def test_negative_skill_raises_task_error():
    with pytest.raises(TaskError):
        check(Roller(1), skill=-1, rules=_rules())


def test_no_automatic_success_on_natural_high_roll():
    # session-alpha throws 1, 5 (sum 6); a heavy negative ladder still fails.
    rules = _rules(target=100)
    result = check(Roller("session-alpha"), difficulty="Formidable", skill=0, rules=rules)
    assert result.total < rules.task_parameters.target
    assert result.success is False


def test_no_automatic_failure_on_natural_low_roll():
    # seed 1 throws 2, 5 (sum 7); enough modifiers still succeed.
    rules = _rules(target=1)
    result = check(Roller(1), difficulty="Simple", skill=0, rules=rules)
    assert result.total >= rules.task_parameters.target
    assert result.success is True


def test_sc010_edited_parameters_change_result_at_the_api_level():
    result = check(Roller(1), skill=0, rules=_rules(target=999))
    assert result.target == 999
    assert result.success is False


def test_check_rejects_a_task_roll_that_is_not_a_count_and_sides_throw():
    # The loader guards this, but a synthetic `rules=` bypasses the loader
    # entirely and is the documented way a house-rule consumer supplies its
    # own table, so `check` owes the same typed failure rather than a bare
    # TypeError (FR-029).
    with pytest.raises(RulesDataError, match="task.roll"):
        check(Roller(1), rules=_rules(roll="d66"))


def test_check_rejects_a_task_roll_that_is_not_dice_notation():
    with pytest.raises(RulesDataError, match="task.roll"):
        check(Roller(1), rules=_rules(roll="not dice notation"))


def test_characteristic_score_in_no_band_raises_rules_data_error():
    # FR-015: because the table is editable under FR-022, a score falling outside
    # every band in the data then in force is a rules-data error, never a silent
    # zero. Gap detection is deliberately deferred to lookup time, which makes
    # this raise the only thing between a holed table and a wrong answer.
    gapped = _parameters(
        characteristic_bands=(
            Band(minimum=0, maximum=2, dm=-2),
            Band(minimum=6, maximum=8, dm=0),
            Band(minimum=9, maximum=None, dm=1),
        )
    )
    with pytest.raises(RulesDataError, match="no characteristic band covers score 4"):
        gapped.characteristic_dm(4)


def test_check_with_a_score_in_no_band_raises_rules_data_error():
    rules = _rules(
        characteristic_bands=(
            Band(minimum=0, maximum=2, dm=-2),
            Band(minimum=6, maximum=8, dm=0),
            Band(minimum=9, maximum=None, dm=1),
        )
    )
    with pytest.raises(RulesDataError, match="no characteristic band covers score 4"):
        check(Roller(1), characteristic=4, skill=0, rules=rules)


# --- FR-018: `dice_total` is `sum(faces)`, and a house-ruled roll modifier
# --- is itemized like every other applied modifier rather than folded in


def test_house_ruled_roll_modifier_is_itemized_and_dice_total_stays_sum_of_faces():
    result = check(Roller(1), difficulty="Average", skill=0, rules=_rules(roll="2d6+1"))
    assert result.faces == (2, 5)
    assert result.dice_total == 7
    assert result.modifiers[0] == Modifier(label="Roll (2d6+1)", value=1)
    assert result.total == 8


def test_house_ruled_negative_roll_modifier_is_itemized():
    result = check(Roller(1), difficulty="Average", skill=0, rules=_rules(roll="2d6-2"))
    assert result.dice_total == 7
    assert result.modifiers[0] == Modifier(label="Roll (2d6-2)", value=-2)
    assert result.total == 5


def test_roll_without_a_modifier_adds_no_roll_row():
    result = check(Roller(1), difficulty="Average", skill=0, rules=_rules(roll="2d6"))
    assert [m.label for m in result.modifiers] == ["Difficulty (Average)", "Skill 0"]


def test_check_result_carries_the_rules_provenance():
    rules = _rules()
    result = check(Roller(1), skill=0, rules=rules)
    assert result.provenance is rules.provenance
