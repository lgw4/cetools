from cetools.engine.names import FIRST_NAMES, LAST_NAMES, generate_name
from conftest import ConstantRoller, SequenceRoller


class _RecordingRoller:
    """Records every (sides, count) call it receives, returning values in sequence."""

    def __init__(self, values: list[int]) -> None:
        self._values = list(values)
        self.calls: list[tuple[int, int]] = []

    def roll(self, sides: int, count: int = 1) -> int:
        self.calls.append((sides, count))
        return self._values[len(self.calls) - 1]


def test_first_names_is_tuple_with_at_least_ten_entries() -> None:
    assert isinstance(FIRST_NAMES, tuple)
    assert all(isinstance(entry, str) for entry in FIRST_NAMES)
    assert len(FIRST_NAMES) >= 10


def test_last_names_is_tuple_with_at_least_ten_entries() -> None:
    assert isinstance(LAST_NAMES, tuple)
    assert all(isinstance(entry, str) for entry in LAST_NAMES)
    assert len(LAST_NAMES) >= 10


def test_generate_name_returns_two_space_separated_non_empty_words() -> None:
    result = generate_name(ConstantRoller(1))
    words = result.split(" ")
    assert len(words) == 2
    assert all(word for word in words)


def test_generate_name_combines_independently_drawn_first_and_last_names() -> None:
    # SequenceRoller([3, 7]): first draw = 3 -> FIRST_NAMES[2]; second draw = 7 -> LAST_NAMES[6]
    roller = SequenceRoller([3, 7])
    result = generate_name(roller)
    assert result == f"{FIRST_NAMES[2]} {LAST_NAMES[6]}"


def test_generate_name_makes_two_independent_rolls_sized_to_each_table() -> None:
    roller = _RecordingRoller([1, 1])
    generate_name(roller)
    assert len(roller.calls) == 2
    assert roller.calls[0][0] == len(FIRST_NAMES)
    assert roller.calls[1][0] == len(LAST_NAMES)
