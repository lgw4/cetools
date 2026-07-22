import pytest

from cetools.engine.rolls import (
    MAX_ROLL_ATTEMPTS,
    RandomRolls,
    RollName,
    ScriptedRolls,
    bounded_retry,
)


class FixedRandom:
    """A random source whose dice always land on the same face."""

    def __init__(self, face: int, index: int = 0):
        self._face = face
        self._index = index

    def randint(self, low: int, high: int) -> int:
        return self._face

    def randrange(self, stop: int) -> int:
        return self._index % stop


def _random(face: int, index: int = 0) -> RandomRolls:
    return RandomRolls(FixedRandom(face, index))


# --- check: the 2D6 + DM >= target rule ---
# These moved out of tests/test_generator.py, where they tested the private
# generator._check. The rule lives on the seam now, and is tested here once.


def test_check_succeeds_when_roll_plus_modifier_meets_target() -> None:
    # 2D6 = 3+3 = 6, dm=0 -> 6 >= target 6
    assert _random(3).check(0, 6, RollName.SURVIVAL) is True


def test_check_fails_when_roll_plus_modifier_below_target() -> None:
    # 2D6 = 2+2 = 4, dm=0 -> 4 < target 6
    assert _random(2).check(0, 6, RollName.SURVIVAL) is False


def test_check_applies_the_dice_modifier() -> None:
    # 2D6 = 2+2 = 4, dm=+2 -> 6 >= target 6. Without the modifier, 4 < 6 fails.
    assert _random(2).check(2, 6, RollName.QUALIFICATION) is True


def test_check_applies_a_negative_dice_modifier() -> None:
    # 2D6 = 4+4 = 8, dm=-2 -> 6 < target 7
    assert _random(4).check(-2, 7, RollName.COMMISSION) is False


def test_two_d6_sums_two_dice() -> None:
    assert _random(5).two_d6(RollName.AGING) == 10


def test_d6_draws_a_single_die() -> None:
    assert _random(5).d6(RollName.MISHAP) == 5


def test_random_rolls_stay_in_range() -> None:
    rolls = RandomRolls()
    assert all(1 <= rolls.d6(RollName.MISHAP) <= 6 for _ in range(200))
    assert all(2 <= rolls.two_d6(RollName.AGING) <= 12 for _ in range(200))
    assert all(rolls.choose(("A", "B", "C"), RollName.CAREER) in "ABC" for _ in range(200))


def test_random_choose_can_reach_every_item() -> None:
    rolls = RandomRolls()
    items = tuple(range(8))
    seen = {rolls.choose(items, RollName.CAREER) for _ in range(400)}
    assert seen == set(items)


def test_choose_rejects_an_empty_sequence() -> None:
    with pytest.raises(ValueError, match="empty"):
        RandomRolls().choose((), RollName.CAREER)


# --- ScriptedRolls ---


def test_scripted_check_returns_the_scripted_outcome_ignoring_arithmetic() -> None:
    # A scripted check supplies the outcome, not the dice: an impossible target
    # still passes, because the arithmetic is the seam's job, tested above.
    rolls = ScriptedRolls(checks={RollName.SURVIVAL: True})
    assert rolls.check(-99, 99, RollName.SURVIVAL) is True


def test_scripted_scalar_means_always() -> None:
    rolls = ScriptedRolls(d6={RollName.MISHAP: 4})
    assert [rolls.d6(RollName.MISHAP) for _ in range(3)] == [4, 4, 4]


def test_scripted_list_is_consumed_in_order() -> None:
    rolls = ScriptedRolls(checks={RollName.SURVIVAL: [True, False]}, default_check=True)
    assert rolls.check(0, 0, RollName.SURVIVAL) is True
    assert rolls.check(0, 0, RollName.SURVIVAL) is False


def test_scripted_list_falls_back_to_the_default_when_exhausted() -> None:
    rolls = ScriptedRolls(checks={RollName.SURVIVAL: [False]}, default_check=True)
    assert rolls.check(0, 0, RollName.SURVIVAL) is False
    assert rolls.check(0, 0, RollName.SURVIVAL) is True


def test_unscripted_rolls_take_the_per_verb_default() -> None:
    rolls = ScriptedRolls(default_check=False, default_two_d6=9, default_d6=6, default_choice=2)
    assert rolls.check(0, 0, RollName.COMMISSION) is False
    assert rolls.two_d6(RollName.AGING) == 9
    assert rolls.d6(RollName.MISHAP) == 6
    assert rolls.choose(("A", "B", "C"), RollName.CAREER) == "C"


def test_scripted_rolls_are_addressed_independently_by_name() -> None:
    # The point of the seam: scripting SURVIVAL says nothing about ADVANCEMENT,
    # and neither is disturbed by how many other rolls the engine makes.
    rolls = ScriptedRolls(
        checks={RollName.SURVIVAL: False, RollName.ADVANCEMENT: True},
        default_check=False,
    )
    assert rolls.check(0, 0, RollName.ADVANCEMENT) is True
    assert rolls.check(0, 0, RollName.SURVIVAL) is False
    assert rolls.check(0, 0, RollName.QUALIFICATION) is False


def test_scripted_choice_is_a_zero_based_index() -> None:
    rolls = ScriptedRolls(choices={RollName.CAREER: 1})
    assert rolls.choose(("A", "B", "C"), RollName.CAREER) == "B"


def test_scripted_choice_accepts_a_negative_index() -> None:
    rolls = ScriptedRolls(choices={RollName.FIRST_NAME: -1})
    assert rolls.choose(("A", "B", "C"), RollName.FIRST_NAME) == "C"


def test_scripted_keys_must_be_roll_names() -> None:
    # A bare string is the typo class of bug the RollName enum exists to kill.
    with pytest.raises(TypeError, match="RollName"):
        ScriptedRolls(checks={"survival": False})


def test_roll_names_are_unique() -> None:
    values = [member.value for member in RollName]
    assert len(values) == len(set(values))


def test_bounded_retry_returns_the_first_accepted_candidate() -> None:
    produced = iter([1, 2, 3, 4])
    assert bounded_retry(lambda: next(produced), lambda n: n >= 3) == 3


def test_bounded_retry_returns_none_when_nothing_is_accepted() -> None:
    assert bounded_retry(lambda: 0, lambda n: n > 0) is None


def test_bounded_retry_stops_producing_once_accepted() -> None:
    calls = 0

    def produce() -> int:
        nonlocal calls
        calls += 1
        return calls

    assert bounded_retry(produce, lambda n: n == 2) == 2
    assert calls == 2


def test_bounded_retry_honors_a_custom_attempt_budget() -> None:
    calls = 0

    def produce() -> int:
        nonlocal calls
        calls += 1
        return 0

    assert bounded_retry(produce, lambda n: n > 0, attempts=3) is None
    assert calls == 3


def test_bounded_retry_defaults_to_max_roll_attempts() -> None:
    calls = 0

    def produce() -> int:
        nonlocal calls
        calls += 1
        return 0

    assert bounded_retry(produce, lambda n: n > 0) is None
    assert calls == MAX_ROLL_ATTEMPTS


def test_seeded_rolls_are_reproducible() -> None:
    a = RandomRolls.seeded(42)
    b = RandomRolls.seeded(42)
    a_seq = [a.two_d6(RollName.CHARACTERISTIC) for _ in range(20)]
    b_seq = [b.two_d6(RollName.CHARACTERISTIC) for _ in range(20)]
    assert a_seq == b_seq


def test_different_seeds_produce_different_streams() -> None:
    a = RandomRolls.seeded(1)
    b = RandomRolls.seeded(2)
    a_seq = [a.two_d6(RollName.CHARACTERISTIC) for _ in range(20)]
    b_seq = [b.two_d6(RollName.CHARACTERISTIC) for _ in range(20)]
    assert a_seq != b_seq


def test_seeded_none_is_an_unseeded_working_adapter() -> None:
    rolls = RandomRolls.seeded(None)
    assert isinstance(rolls, RandomRolls)
    assert all(2 <= rolls.two_d6(RollName.CHARACTERISTIC) <= 12 for _ in range(20))
