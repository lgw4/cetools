import json

from cetools.dice import ThrowResult
from cetools.render import as_dict, as_json, as_text
from cetools.tasks import CheckResult, Modifier


def test_as_text_throw_with_modifier_matches_contract_example():
    result = ThrowResult(
        notation="2d6+1",
        faces=(1, 5),
        modifier=1,
        total=7,
        seed=14333185781139156525,
    )
    assert as_text(result) == (
        "2d6+1 = 7\n"
        "  Dice:     1, 5 (sum 6)\n"
        "  Modifier: +1\n"
        "  Seed:     14333185781139156525\n"
    )


def test_as_text_throw_without_modifier_omits_sum_and_modifier_line():
    result = ThrowResult(
        notation="1d6",
        faces=(1,),
        modifier=0,
        total=1,
        seed=14333185781139156525,
    )
    assert as_text(result) == ("1d6 = 1\n" "  Dice: 1\n" "  Seed: 14333185781139156525\n")


def test_as_text_throw_negative_modifier_is_signed():
    result = ThrowResult(
        notation="2d6-1",
        faces=(1, 5),
        modifier=-1,
        total=5,
        seed=1,
    )
    text = as_text(result)
    assert "Modifier: -1" in text


def test_as_text_throw_ends_with_trailing_newline():
    result = ThrowResult(
        notation="1d6",
        faces=(1,),
        modifier=0,
        total=1,
        seed=1,
    )
    assert as_text(result).endswith("\n")
    assert not as_text(result).endswith("\n\n")


def test_as_text_check_matches_contract_difficult_example():
    result = CheckResult(
        faces=(1, 5),
        dice_total=6,
        modifiers=(
            Modifier(label="Difficulty (Difficult)", value=-2),
            Modifier(label="Characteristic 9", value=1),
            Modifier(label="Skill 2", value=2),
            Modifier(label="cover", value=-2),
        ),
        total=5,
        target=8,
        success=False,
        seed=14333185781139156525,
    )
    assert as_text(result) == (
        "Check: FAILURE\n"
        "  Dice:  1, 5 (sum 6)\n"
        "  Modifiers:\n"
        "    Difficulty (Difficult) -2\n"
        "    Characteristic 9       +1\n"
        "    Skill 2                +2\n"
        "    cover                  -2\n"
        "  Total: 5 vs target 8\n"
        "  Seed:  14333185781139156525\n"
    )


def test_as_text_check_success_header():
    result = CheckResult(
        faces=(6, 6),
        dice_total=12,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=12,
        target=8,
        success=True,
        seed=1,
    )
    assert as_text(result).startswith("Check: SUCCESS\n")


def test_as_text_check_modifier_values_are_signed_including_zero():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(
            Modifier(label="Difficulty (Average)", value=0),
            Modifier(label="Unskilled", value=-3),
        ),
        total=4,
        target=8,
        success=False,
        seed=1,
    )
    text = as_text(result)
    assert "Difficulty (Average) +0" in text
    assert "Unskilled            -3" in text


def test_as_text_check_dice_line_always_carries_sum():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
    )
    assert "Dice:  2, 5 (sum 7)" in as_text(result)


def test_as_text_check_ends_with_trailing_newline():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
    )
    text = as_text(result)
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_as_dict_throw_matches_json_contract_shape():
    result = ThrowResult(
        notation="2d6+1",
        faces=(1, 5),
        modifier=1,
        total=7,
        seed=14333185781139156525,
    )
    assert as_dict(result) == {
        "kind": "roll",
        "notation": "2d6+1",
        "faces": [1, 5],
        "modifier": 1,
        "total": 7,
        "seed": "14333185781139156525",
    }


def test_as_dict_check_matches_json_contract_shape():
    result = CheckResult(
        faces=(1, 5),
        dice_total=6,
        modifiers=(
            Modifier(label="Difficulty (Difficult)", value=-2),
            Modifier(label="cover", value=-2),
        ),
        total=1,
        target=8,
        success=False,
        seed=14333185781139156525,
    )
    assert as_dict(result) == {
        "kind": "check",
        "faces": [1, 5],
        "dice_total": 6,
        "modifiers": [
            {"label": "Difficulty (Difficult)", "value": -2},
            {"label": "cover", "value": -2},
        ],
        "total": 1,
        "target": 8,
        "success": False,
        "seed": "14333185781139156525",
    }


def test_as_json_throw_uses_indent_two_and_unescaped_unicode():
    result = ThrowResult(notation="1d6", faces=(1,), modifier=0, total=1, seed=1)
    text = as_json(result)
    assert text == json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"


def test_as_json_check_uses_indent_two_and_unescaped_unicode():
    result = CheckResult(
        faces=(2, 5),
        dice_total=7,
        modifiers=(Modifier(label="Difficulty (Average)", value=0),),
        total=7,
        target=8,
        success=False,
        seed=1,
    )
    text = as_json(result)
    assert text == json.dumps(as_dict(result), indent=2, ensure_ascii=False) + "\n"


def test_as_json_ends_with_trailing_newline():
    result = ThrowResult(notation="1d6", faces=(1,), modifier=0, total=1, seed=1)
    assert as_json(result).endswith("\n")
    assert json.loads(as_json(result)) == as_dict(result)
