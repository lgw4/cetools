from cetools.engine.models import STAT_NAMES

_TO_CHAR = (
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "A",
    "B",
    "C",
    "D",
    "E",
    "F",
    "G",
    "H",
    "J",
    "K",
    "L",
    "M",
    "N",
    "P",
    "Q",
    "R",
    "S",
    "T",
    "U",
    "V",
    "W",
    "X",
    "Y",
    "Z",
)

_FROM_CHAR = {c: i for i, c in enumerate(_TO_CHAR)}


def to_pseudohex(value: int) -> str:
    if value < 0 or value > 33:
        raise ValueError(f"Value {value} out of pseudo-hex range 0–33")
    return _TO_CHAR[value]


def from_pseudohex(char: str) -> int:
    if char not in _FROM_CHAR:
        raise ValueError(f"Invalid pseudo-hex character: {char!r}")
    return _FROM_CHAR[char]


def encode_upp(scores: dict[str, int]) -> str:
    return "".join(to_pseudohex(scores[stat]) for stat in STAT_NAMES)
