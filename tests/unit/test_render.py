from cetools.dice import ThrowResult
from cetools.render import as_text


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
