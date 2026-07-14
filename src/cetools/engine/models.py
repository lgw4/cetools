from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Literal

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


MAX_CHARACTERISTIC = 33


def boost(characteristics: dict[str, int], entry: str) -> dict[str, int] | None:
    """New characteristics if `entry` is a "+1 X" boost, else None.

    Both Skills and Training entries and material benefits use the same "+1 X"
    notation, so both go through here. An unknown abbreviation is still a boost —
    it just has nothing to apply — which keeps a typo in a career table from being
    silently granted as a skill named "+1 Xyz".
    """
    if not entry.startswith("+1 "):
        return None
    stat = STAT_ABBREV.get(entry[3:])
    if stat is None:
        return dict(characteristics)
    boosted = dict(characteristics)
    boosted[stat] = min(MAX_CHARACTERISTIC, boosted.get(stat, 0) + 1)
    return boosted


@dataclass
class Benefit:
    kind: Literal["cash", "material"]
    cash_amount: int | None = None
    material_name: str | None = None
    material_quantity: int | None = None

    def __post_init__(self) -> None:
        if self.kind == "cash" and self.cash_amount is None:
            raise ValueError("Benefit: kind 'cash' requires cash_amount")
        if self.kind == "material" and self.material_name is None:
            raise ValueError("Benefit: kind 'material' requires material_name")


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
