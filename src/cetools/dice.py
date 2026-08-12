import random
import re
from dataclasses import dataclass

from cetools.errors import DiceError
from cetools.seeds import resolve_seed

_NOTATION = re.compile(
    r"^\s*(?P<count>\d+)?\s*[dD]\s*(?P<sides>\d+)\s*" r"(?:(?P<sign>[+-])\s*(?P<mod>\d+))?\s*$"
)


class Roller:
    """The only source of randomness in the library.

    Constructed from a seed and passed explicitly to everything that needs
    a die. Two `Roller` instances never share state, so neither can consume
    the other's sequence (FR-008).
    """

    def __init__(self, seed: int | str | None = None) -> None:
        self.seed = resolve_seed(seed)
        self._rng = random.Random(self.seed)

    def die(self, sides: int) -> int:
        if not isinstance(sides, int) or sides < 1:
            raise DiceError(f"sides must be an integer of at least 1, got {sides!r}")
        bits = (sides - 1).bit_length()
        while True:
            n = self._rng.getrandbits(bits)
            if n < sides:
                return n + 1

    def dice(self, count: int, sides: int) -> tuple[int, ...]:
        if not isinstance(count, int) or count < 1:
            raise DiceError(f"count must be an integer of at least 1, got {count!r}")
        return tuple(self.die(sides) for _ in range(count))


@dataclass(frozen=True, slots=True)
class ThrowResult:
    """The result of a dice throw: `throw`, `throw_dice`, or `d66`."""

    notation: str
    faces: tuple[int, ...]
    modifier: int
    total: int
    seed: int


def parse_notation(notation: str) -> tuple[int, int, int] | None:
    """Parse dice notation into `(count, sides, modifier)`.

    Raises `DiceError` for anything the grammar does not match, and for a
    count or side count below 1.
    """
    match = _NOTATION.match(notation)
    if match is None:
        raise DiceError(f"invalid dice notation: {notation!r}")
    count = int(match.group("count") or 1)
    sides = int(match.group("sides"))
    if count < 1:
        raise DiceError(f"count must be at least 1, got {count}")
    if sides < 1:
        raise DiceError(f"sides must be at least 1, got {sides}")
    modifier = int(match.group("mod") or 0)
    if match.group("sign") == "-":
        modifier = -modifier
    return count, sides, modifier


def throw_dice(roller: Roller, count: int, sides: int, modifier: int = 0) -> ThrowResult:
    faces = roller.dice(count, sides)
    sign = "+" if modifier >= 0 else "-"
    notation = f"{count}d{sides}" + (f"{sign}{abs(modifier)}" if modifier else "")
    return ThrowResult(
        notation=notation,
        faces=faces,
        modifier=modifier,
        total=sum(faces) + modifier,
        seed=roller.seed,
    )


def throw(roller: Roller, notation: str) -> ThrowResult:
    count, sides, modifier = parse_notation(notation)
    return throw_dice(roller, count, sides, modifier)
