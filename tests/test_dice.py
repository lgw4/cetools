from cetools.engine.dice import DiceRoller, RandomDiceRoller
from conftest import ConstantRoller


def test_stub_roller_satisfies_protocol() -> None:
    roller: DiceRoller = ConstantRoller(4)
    assert roller.roll(6) == 4


def test_random_roller_1d6_in_range() -> None:
    roller = RandomDiceRoller()
    for _ in range(50):
        result = roller.roll(6)
        assert 1 <= result <= 6, f"Expected 1–6, got {result}"


def test_random_roller_2d6_in_range() -> None:
    roller = RandomDiceRoller()
    for _ in range(50):
        result = roller.roll(6, count=2)
        assert 2 <= result <= 12, f"Expected 2–12, got {result}"


def test_stub_roller_returns_controlled_value() -> None:
    roller = ConstantRoller(9)
    assert roller.roll(6, count=2) == 9
    assert roller.roll(6) == 9
    assert roller.roll(8, count=3) == 9
