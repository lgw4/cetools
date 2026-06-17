from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


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


@dataclass
class GenerationFailure:
    reason: str
    exit_code: int = 1
