import pytest

from cetools.engine.dice import LegacyDiceRolls, as_rolls
from cetools.engine.rolls import RollName, Rolls
from conftest import ConstantRoller, SequenceRoller


def _rolls(roller) -> Rolls:
    return LegacyDiceRolls(roller)


# --- check: the 2D6 + DM >= target rule ---
# These three moved out of tests/test_generator.py, where they tested the
# private generator._check. The rule now lives on the seam.


def test_check_succeeds_when_roll_plus_modifier_meets_target() -> None:
    # ConstantRoller(6): 2D6=6, dm=0 -> 6 >= target 6
    assert _rolls(ConstantRoller(6)).check(0, 6, RollName.SURVIVAL) is True


def test_check_fails_when_roll_plus_modifier_below_target() -> None:
    # ConstantRoller(5): 2D6=5, dm=0 -> 5 < target 6
    assert _rolls(ConstantRoller(5)).check(0, 6, RollName.SURVIVAL) is False


def test_check_applies_dice_modifier() -> None:
    # ConstantRoller(4): 2D6=4, dm=+2 -> 6 >= target 6.
    # Without the modifier, 4 < 6 would fail.
    assert _rolls(ConstantRoller(4)).check(2, 6, RollName.QUALIFICATION) is True


def test_check_accepts_a_negative_dice_modifier() -> None:
    # 2D6=8, dm=-2 -> 6 < target 7
    assert _rolls(ConstantRoller(8)).check(-2, 7, RollName.COMMISSION) is False


# --- dice ---


def test_two_d6_draws_a_two_dice_roll() -> None:
    # The shim must ask for two dice, not one: SmartRoller-style distinction.
    assert _rolls(ConstantRoller(9)).two_d6(RollName.AGING) == 9


def test_d6_draws_a_single_die() -> None:
    assert _rolls(ConstantRoller(4)).d6(RollName.MISHAP) == 4


# --- choose ---


def test_choose_returns_the_item_at_the_rolled_position() -> None:
    # roll(3) -> 2, so the second item.
    assert _rolls(ConstantRoller(2)).choose(("A", "B", "C"), RollName.CAREER) == "B"


def test_choose_wraps_a_roll_beyond_the_list() -> None:
    # A degenerate roller can return a value larger than the list; wrap rather
    # than raise, matching the modulo the generator applied before the seam.
    assert _rolls(ConstantRoller(7)).choose(("A", "B", "C"), RollName.CAREER) == "A"


def test_choose_consumes_one_roll_per_call() -> None:
    rolls = _rolls(SequenceRoller([1, 3]))
    items = ("A", "B", "C")
    assert rolls.choose(items, RollName.CAREER) == "A"
    assert rolls.choose(items, RollName.CAREER) == "C"


def test_choose_rejects_an_empty_sequence() -> None:
    with pytest.raises(ValueError, match="empty"):
        _rolls(ConstantRoller(1)).choose((), RollName.CAREER)


# --- roll names ---


def test_roll_names_are_unique() -> None:
    values = [member.value for member in RollName]
    assert len(values) == len(set(values))


# --- coercion (temporary, dies with phase B) ---


def test_as_rolls_wraps_a_bare_dice_roller() -> None:
    assert isinstance(as_rolls(ConstantRoller(3)), LegacyDiceRolls)


def test_as_rolls_passes_a_rolls_through_unchanged() -> None:
    rolls = _rolls(ConstantRoller(3))
    assert as_rolls(rolls) is rolls


def test_as_rolls_defaults_to_a_random_source() -> None:
    rolls = as_rolls(None)
    assert 2 <= rolls.two_d6(RollName.CHARACTERISTIC) <= 12
