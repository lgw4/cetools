from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

from cetools.engine.rolls import RollName, Rolls

if TYPE_CHECKING:  # careers.base imports this module, so only import it for types
    from cetools.engine.careers.base import Career

STAT_NAMES: tuple[str, ...] = (
    "Strength",
    "Dexterity",
    "Endurance",
    "Intelligence",
    "Education",
    "Social Standing",
)

STAT_ABBREV: dict[str, str] = {
    "Str": "Strength",
    "Dex": "Dexterity",
    "End": "Endurance",
    "Int": "Intelligence",
    "Edu": "Education",
    "Soc": "Social Standing",
}


def characteristic_modifier(score: int) -> int:
    if score <= 2:
        return -2
    if score <= 5:
        return -1
    if score <= 8:
        return 0
    if score <= 11:
        return 1
    if score <= 14:
        return 2
    if score <= 17:
        return 3
    if score <= 20:
        return 4
    if score <= 23:
        return 5
    if score <= 26:
        return 6
    if score <= 29:
        return 7
    if score <= 32:
        return 8
    return 9


def characteristic_check(
    rolls: Rolls,
    characteristics: dict[str, int],
    stat: str,
    target: int,
    name: RollName,
) -> bool:
    """A check against a characteristic: 2D6 + its DM >= target.

    Qualification, survival, commission and advancement are all this. The seam
    knows about chance and not about characteristics, so the DM lookup happens
    here—in the module that owns the DM rule—rather than in each caller.
    """
    return rolls.check(characteristic_modifier(characteristics[stat]), target, name)


MAX_CHARACTERISTIC = 33

_BOOST_PREFIX = "+1 "


@dataclass(frozen=True)
class Cash:
    """Cash drawn at muster-out."""

    amount: int


@dataclass(frozen=True)
class StatBoost:
    """A "+1 X" entry, by the abbreviation it is written with (e.g. "Edu").

    Always one level: no career table says "+2 X". Two boosts of the same stat are
    two of these, and summing them for display is the formatter's business.
    """

    label: str


@dataclass(frozen=True)
class Item:
    """A material benefit that is a thing: a Weapon, a High Passage, a ship."""

    name: str


@dataclass(frozen=True)
class Shares:
    """Ship shares, whose count is rolled when the benefit is granted."""

    quantity: int


Benefit = Cash | StatBoost | Item | Shares
"""What a character leaves a career with. Each variant carries exactly what it is,
so there is nothing to validate and no way to build a benefit that means nothing."""


def parse_stat_boost(entry: str) -> StatBoost | None:
    """The StatBoost `entry` denotes, or None if it is not a "+1 X" entry.

    Career skill tables and material benefit tables both use this notation, so
    both come through here and neither knows what the prefix means. An unknown
    abbreviation is still a boost—it just has nothing to apply—which keeps a
    typo in a career table from being granted as a skill named "+1 Xyz".
    """
    if not entry.startswith(_BOOST_PREFIX):
        return None
    return StatBoost(label=entry.removeprefix(_BOOST_PREFIX))


def apply_stat_boost(characteristics: dict[str, int], boost: StatBoost) -> dict[str, int]:
    """The characteristics after the boost. An unknown abbreviation changes nothing."""
    stat = STAT_ABBREV.get(boost.label)
    if stat is None:
        return dict(characteristics)
    boosted = dict(characteristics)
    boosted[stat] = min(MAX_CHARACTERISTIC, boosted.get(stat, 0) + 1)
    return boosted


@dataclass
class Term:
    number: int
    survived: bool
    commissioned: bool
    promoted: bool
    rank_at_end: int
    skills_gained: list[str] = field(default_factory=list)


@dataclass
class MishapOutcome:
    roll: int
    discharge_type: Literal["honorable", "dishonorable", "medical", "none"]
    imprisoned: bool
    injury_reductions: dict[str, int]
    injury_crisis: bool


@dataclass
class Character:
    characteristics: dict[str, int]
    upp: str
    age: int
    career: Career
    rank: int
    terms_served: int
    name: str
    skills: dict[str, int]
    benefits: list[Benefit]
    pension: int | None
    terms: list[Term]
    drafted: bool = False
    mishap: MishapOutcome | None = None
    debt: int = 0
    psi_strength: int = 0
    talents: dict[str, int] = field(default_factory=dict)

    @property
    def rank_title(self) -> str:
        """The character's title at their current rank.

        Derived, not stored: the career knows it, and a character carries its
        career.
        """
        return self.career.ranks[self.rank].title


@dataclass
class GenerationFailure:
    reason: str
    exit_code: int = 1
