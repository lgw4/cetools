from collections.abc import Sequence
from typing import TypeVar

from cetools.engine.names import FIRST_NAMES, LAST_NAMES, generate_name
from cetools.engine.rolls import RollName, ScriptedRolls

T = TypeVar("T")


class _RecordingRolls(ScriptedRolls):
    """Records the size and name of every `choose` the engine asks for."""

    def __init__(self) -> None:
        super().__init__()
        self.calls: list[tuple[int, RollName]] = []

    def choose(self, items: Sequence[T], name: RollName) -> T:
        self.calls.append((len(items), name))
        return super().choose(items, name)


def test_first_names_is_tuple_with_at_least_ten_entries() -> None:
    assert isinstance(FIRST_NAMES, tuple)
    assert all(isinstance(entry, str) for entry in FIRST_NAMES)
    assert len(FIRST_NAMES) >= 10


def test_last_names_is_tuple_with_at_least_ten_entries() -> None:
    assert isinstance(LAST_NAMES, tuple)
    assert all(isinstance(entry, str) for entry in LAST_NAMES)
    assert len(LAST_NAMES) >= 10


def test_generate_name_returns_two_space_separated_non_empty_words() -> None:
    # Nothing scripted: both picks take the default index (0).
    result = generate_name(ScriptedRolls())
    words = result.split(" ")
    assert len(words) == 2
    assert all(word for word in words)


def test_generate_name_combines_independently_drawn_first_and_last_names() -> None:
    # The two picks are drawn independently: index 2 of FIRST_NAMES, index 6 of
    # LAST_NAMES.
    rolls = ScriptedRolls(choices={RollName.FIRST_NAME: 2, RollName.LAST_NAME: 6})
    result = generate_name(rolls)
    assert result == f"{FIRST_NAMES[2]} {LAST_NAMES[6]}"


def test_generate_name_makes_two_independent_rolls_sized_to_each_table() -> None:
    rolls = _RecordingRolls()
    generate_name(rolls)
    assert len(rolls.calls) == 2
    assert rolls.calls[0][0] == len(FIRST_NAMES)
    assert rolls.calls[1][0] == len(LAST_NAMES)
