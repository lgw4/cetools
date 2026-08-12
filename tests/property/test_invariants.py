from hypothesis import given
from hypothesis import strategies as st

from cetools.dice import Roller, throw_dice

seeds = st.one_of(st.integers(min_value=0, max_value=2**64 - 1), st.text(min_size=1, max_size=20))
counts = st.integers(min_value=1, max_value=20)
sides = st.integers(min_value=1, max_value=100)
modifiers = st.integers(min_value=-10, max_value=10)


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_throw_faces_are_within_range_and_correct_count(seed, count, sides_, modifier):
    result = throw_dice(Roller(seed), count, sides_, modifier)
    assert len(result.faces) == count
    assert all(1 <= face <= sides_ for face in result.faces)


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_throw_total_equals_sum_of_faces_plus_modifier(seed, count, sides_, modifier):
    result = throw_dice(Roller(seed), count, sides_, modifier)
    assert result.total == sum(result.faces) + modifier


@given(seed=seeds, count=counts, sides_=sides, modifier=modifiers)
def test_same_seed_and_arguments_yield_equal_result(seed, count, sides_, modifier):
    first = throw_dice(Roller(seed), count, sides_, modifier)
    second = throw_dice(Roller(seed), count, sides_, modifier)
    assert first == second
