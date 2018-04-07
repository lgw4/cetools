from typing import (Dict, List, Optional, Type)

import attr


@attr.s(auto_attribs=True)
class Skill:
    name: str
    rank: Optional[int]


@attr.s(auto_attribs=True, frozen=True)
class Rank:
    name: str
    skill: Optional[Skill]


@attr.s(auto_attribs=True)
class Character:
    name: str
    strength: int
    dexterity: int
    endurance: int
    intelligence: int
    education: int
    social_standing: int
    psionic_strength: Optional[int]
    careers: Dict[str, int]
    skills: Dict[str, int]


@attr.s(auto_attribs=True, frozen=True)
class Career:
    name: str
    qualifications: Dict[str, int]
    survival: Dict[str, int]
    commission: Dict[str, int]
    advancement: Dict[str, int]
    re_enlistment: int
    ranks_and_skills: List[Rank]
    benefits: List[str]
    cash: List[int]
    personal_development: List[Skill]
    service_skills: List[Skill]
    specialist_skills: List[Skill]
    advanced_education: List[Skill]


navy = Career(
    name="Navy",
    qualifications={"INT": 6},
    survival={"INT": 5},
    commission={"SOC": 7},
    advancement={"EDU": 6},
    re_enlistment=5,
    ranks_and_skills=[
        Rank(name="Starman", skill=Skill(name="Zero-G", rank=1)),
        Rank(name="Midshipman", skill=None),
        Rank(name="Lieutenant", skill=None),
        Rank(name="Lt. Commander", skill=Skill(name="Tactics", rank=1)),
        Rank(name="Commander", skill=None),
        Rank(name="Captain", skill=None),
        Rank(name="Commodore", skill=None),
    ],
    benefits=[
        "Low Passage",
        "EDU",
        "Weapon",
        "Mid Passage",
        "SOC",
        "High Passage",
        "Explorers' Society",
    ],
    cash=[1_000, 5_000, 10_000, 10_000, 20_000, 50_000, 50_000],
    personal_development=[
        Skill(name="STR", rank=1),
        Skill(name="DEX", rank=1),
        Skill(name="END", rank=1),
        Skill(name="INT", rank=1),
        Skill(name="EDU", rank=1),
        Skill(name="Melee Combat", rank=None),
    ],
    service_skills=[
        Skill(name="Comms", rank=None),
        Skill(name="Engineering", rank=None),
        Skill(name="Gun Combat", rank=None),
        Skill(name="Gunnery", rank=None),
        Skill(name="Melee Combat", rank=None),
        Skill(name="Vehicle", rank=None),
    ],
    specialist_skills=[
        Skill(name="Gravitics", rank=None),
        Skill(name="Jack o'Trades", rank=None),
        Skill(name="Melee Combat", rank=None),
        Skill(name="Navigation", rank=None),
        Skill(name="Leadership", rank=None),
        Skill(name="Piloting", rank=None),
    ],
    advanced_education=[
        Skill(name="Advocate", rank=None),
        Skill(name="Computer", rank=None),
        Skill(name="Engineering", rank=None),
        Skill(name="Medicine", rank=None),
        Skill(name="Navigation", rank=None),
        Skill(name="Tactics", rank=None),
    ],
)
