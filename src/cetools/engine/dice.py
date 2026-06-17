import random
from typing import Protocol


class DiceRoller(Protocol):
    def roll(self, sides: int, count: int = 1) -> int:
        """Return the sum of `count` dice, each with `sides` faces."""
        ...


class RandomDiceRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return sum(random.randint(1, sides) for _ in range(count))
