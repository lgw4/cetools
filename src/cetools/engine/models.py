from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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


@dataclass
class Skill:
    name: str
    level: int


@dataclass
class Benefit:
    kind: Literal["cash", "material"]
    cash_amount: int | None = None
    material_name: str | None = None


@dataclass
class Term:
    number: int
    survived: bool
    commissioned: bool
    promoted: bool
    rank_at_end: int
    skills_gained: list[str] = field(default_factory=list)


@dataclass
class Character:
    characteristics: dict[str, int]
    upp: str
    age: int
    career: str
    rank: int
    rank_title: str
    terms_served: int
    skills: dict[str, int]
    benefits: list[Benefit]
    pension: int | None
    terms: list[Term]
    drafted: bool = False


@dataclass
class GenerationFailure:
    reason: str
    exit_code: int = 1
