"""Number, list and article primitives for the ship description.

Pure functions over numbers and strings. This module imports nothing from
``models.py``, ``tables.py`` or any other ships module, and knows nothing about
ships: that is the seam that makes the SRD's number and grammar rules testable
without building one.

Three numeric helpers occupy deliberately disjoint domains:

``count``
    counts of *things* -- crew, staterooms, hardpoints, turrets, jumps, weeks.
    Words up to ten, digits above.
``tons``
    tonnage stated in running prose. The count rule when the value is whole,
    digits when it is fractional, because the SRD writes "two tons allocated to
    fire control" but "1.3 tons".
``number`` / ``money``
    measured and rated values -- hull points, Jump rating, sensor DM, armour
    protection, MCr cost. Digits at every magnitude; ``money`` adds thousands
    separators.

Rendering a slot with the wrong helper is therefore visible in the output
rather than silent.
"""

from __future__ import annotations

from collections.abc import Sequence

_WORDS: tuple[str, ...] = (
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
)
"""The SRD's spelled counts. Above ten it prints digits."""

_DECIMAL_PLACES = 6
"""Fixed precision for `number` and `money`, stripped of trailing zeros
afterwards -- never `:g`, which caps at six *significant* figures (rendering
MCr2,768.145 as 2768.14) and switches to scientific notation above 1e6. Six
places sits below the smallest figure the SRD prices (a standard missile at
MCr0.00125) and above any float-accumulation artefact."""

_VOWELS = frozenset("aeiouAEIOU")


def count(n: int) -> str:
    """A count of things: a word up to ten, digits above."""
    if 0 <= n < len(_WORDS):
        return _WORDS[n]
    return str(n)


def tons(value: float) -> str:
    """Tonnage in running prose: the `count` rule when whole, digits when
    fractional."""
    if float(value).is_integer():
        return count(int(value))
    return number(value)


def _split(value: float) -> tuple[str, str]:
    """The integer and trailing-zero-stripped fractional parts of `value`,
    formatted at fixed precision."""
    integer, _, fraction = f"{value:.{_DECIMAL_PLACES}f}".partition(".")
    return integer, fraction.rstrip("0")


def number(value: float) -> str:
    """A measured or rated value: digits at every magnitude, trailing zeros
    stripped, no dangling decimal point, no scientific notation, no thousands
    separator."""
    integer, fraction = _split(value)
    return f"{integer}.{fraction}" if fraction else integer


def money(value: float) -> str:
    """An MCr figure: `number` plus thousands separators on the integer part.
    "MCr2,768.145", "MCr29.772", "MCr597.87"."""
    integer, fraction = _split(value)
    grouped = f"{int(integer):,}"
    return f"{grouped}.{fraction}" if fraction else grouped


def signed(n: int) -> str:
    """A dice modifier, always with an explicit sign: "+1", "-2", "+0"."""
    return f"{n:+d}"


def plural(n: float, singular: str, plural: str) -> str:  # noqa: A002 - matches the data column
    """`singular` at exactly one, `plural` otherwise.

    Both spellings come from the caller -- in practice a data row's ``name`` and
    ``plural`` columns -- never from a suffix rule, because the SRD's own
    plurals are irregular ("armory" -> "armories").

    ``n`` is a `float` because the description agrees a noun with a tonnage as
    well as with a count: fuel tankage, cargo capacity and hangar capacity all
    read `float` fields off the `Ship`. A whole float takes the singular the way
    the matching `int` does, since ``1.0 == 1``.
    """
    return singular if n == 1 else plural


def join(items: Sequence[str]) -> str:
    """ "a", "a and b", "a, b and c" -- commas and a final "and", no serial
    comma."""
    items = list(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} and {items[-1]}"


def article(word: str) -> str:
    """ "an" before a leading vowel letter, else "a"."""
    return "an" if word[:1] in _VOWELS else "a"


def tonnage_article(value: int) -> str:
    """The hull sentence's article: "an" when the tonnage's leading digit is 8,
    else "a" -- "Using an 800-ton hull", "Using a 200-ton hull".

    Eight is the only leading digit whose spoken form begins with a vowel among
    the SRD's 18 starship and 18 small-craft hull sizes.
    """
    return "an" if str(value).lstrip("-")[:1] == "8" else "a"
