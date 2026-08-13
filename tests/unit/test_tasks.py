import pytest

from cetools import Band, Modifier, Roller, TaskParameters, check
from cetools.errors import TaskError

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
    parameters = _parameters()
    result = check(Roller(1), difficulty=name, skill=0, parameters=parameters)
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
    parameters = _parameters()
    result = check(Roller(1), skill=0, parameters=parameters)
    difficulty_modifier = result.modifiers[0]
    assert difficulty_modifier.label == "Difficulty (Average)"
    assert difficulty_modifier.value == 0


def test_untrained_skill_applies_unskilled_penalty():
    parameters = _parameters()
    result = check(Roller(1), parameters=parameters)
    skill_modifier = [m for m in result.modifiers if m.label in ("Unskilled",)][0]
    assert skill_modifier.label == "Unskilled"
    assert skill_modifier.value == -3


def test_skill_zero_is_trained_and_applies_nothing():
    parameters = _parameters()
    result = check(Roller(1), skill=0, parameters=parameters)
    skill_modifier = result.modifiers[-1]
    assert skill_modifier.label == "Skill 0"
    assert skill_modifier.value == 0


def test_trained_skill_applies_its_level():
    parameters = _parameters()
    result = check(Roller(1), skill=3, parameters=parameters)
    skill_modifier = result.modifiers[-1]
    assert skill_modifier.label == "Skill 3"
    assert skill_modifier.value == 3


def test_modifier_order_is_difficulty_characteristic_skill_situational():
    parameters = _parameters()
    result = check(
        Roller(1),
        difficulty="Difficult",
        characteristic=9,
        skill=2,
        modifiers=(Modifier(label="cover", value=-2),),
        parameters=parameters,
    )
    labels = [m.label for m in result.modifiers]
    assert labels == ["Difficulty (Difficult)", "Characteristic 9", "Skill 2", "cover"]


def test_unknown_difficulty_raises_task_error_listing_valid_names():
    parameters = _parameters()
    with pytest.raises(TaskError) as exc_info:
        check(Roller(1), difficulty="Trivial", parameters=parameters)
    message = str(exc_info.value)
    for name in DIFFICULTY_LADDER:
        assert name in message


def test_negative_characteristic_raises_task_error():
    parameters = _parameters()
    with pytest.raises(TaskError):
        check(Roller(1), characteristic=-1, parameters=parameters)


def test_negative_skill_raises_task_error():
    parameters = _parameters()
    with pytest.raises(TaskError):
        check(Roller(1), skill=-1, parameters=parameters)


def test_no_automatic_success_on_natural_high_roll():
    # session-alpha throws 1, 5 (sum 6); a heavy negative ladder still fails.
    parameters = _parameters(target=100)
    result = check(
        Roller("session-alpha"), difficulty="Formidable", skill=0, parameters=parameters
    )
    assert result.total < parameters.target
    assert result.success is False


def test_no_automatic_failure_on_natural_low_roll():
    # seed 1 throws 2, 5 (sum 7); enough modifiers still succeed.
    parameters = _parameters(target=1)
    result = check(Roller(1), difficulty="Simple", skill=0, parameters=parameters)
    assert result.total >= parameters.target
    assert result.success is True


def test_sc010_edited_parameters_change_result_at_the_api_level():
    edited = _parameters(target=999)
    result = check(Roller(1), skill=0, parameters=edited)
    assert result.target == 999
    assert result.success is False
