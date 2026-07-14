import random
from collections.abc import Sequence
from typing import Protocol, TypeVar

from cetools.engine.rolls import RollName, Rolls

T = TypeVar("T")


class DiceRoller(Protocol):
    def roll(self, sides: int, count: int = 1) -> int:
        """Return the sum of `count` dice, each with `sides` faces."""
        ...


class RandomDiceRoller:
    def roll(self, sides: int, count: int = 1) -> int:
        return sum(random.randint(1, sides) for _ in range(count))


class LegacyDiceRolls:
    """Satisfies `Rolls` over the old low-level `DiceRoller`.

    Temporary. It consumes dice in exactly the same order and arity as the engine
    did before the seam existed, so the die sequences the current tests script by
    hand still line up. That is what lets the engine move onto `Rolls` without
    touching those tests — a green suite is then proof the rules did not move.

    Deleted once the tests script rolls by name (`ScriptedRolls`), along with
    `DiceRoller`, `RandomDiceRoller`, `as_rolls`, and this module.
    """

    def __init__(self, roller: DiceRoller) -> None:
        self._roller = roller

    def check(self, dm: int, target: int, name: RollName) -> bool:
        return self._roller.roll(6, count=2) + dm >= target

    def two_d6(self, name: RollName) -> int:
        return self._roller.roll(6, count=2)

    def d6(self, name: RollName) -> int:
        return self._roller.roll(6)

    def choose(self, items: Sequence[T], name: RollName) -> T:
        if not items:
            raise ValueError(f"cannot choose from an empty sequence (roll '{name}')")
        return items[(self._roller.roll(len(items)) - 1) % len(items)]


def as_rolls(source: "DiceRoller | Rolls | None") -> Rolls:
    """Coerce a roller, a `Rolls`, or nothing into a `Rolls`.

    Temporary, and the reason the existing tests can keep passing a `DiceRoller`
    into engine functions that now speak `Rolls`. Dies with `LegacyDiceRolls`.
    """
    if source is None:
        return LegacyDiceRolls(RandomDiceRoller())
    if hasattr(source, "check"):
        return source  # type: ignore[return-value]
    return LegacyDiceRolls(source)  # type: ignore[arg-type]
